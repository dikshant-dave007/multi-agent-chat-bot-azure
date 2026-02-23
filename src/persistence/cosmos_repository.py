"""
Cosmos DB repository for task persistence.

This module provides CRUD operations and query capabilities for
tasks stored in Azure Cosmos DB.
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import List, Optional

from azure.cosmos import CosmosClient, DatabaseProxy, ContainerProxy, PartitionKey
from azure.cosmos.exceptions import CosmosHttpResponseError, CosmosResourceNotFoundError
from azure.identity import DefaultAzureCredential

from src.core.config import get_settings
from src.core.exceptions import (
    DatabaseConnectionError,
    DatabaseOperationError,
    RecordNotFoundError,
    ConcurrencyError,
)
from src.core.logging_config import LoggerMixin
from src.persistence.models import TaskRecord, TaskStatus, AuditLog


class CosmosDBRepository(LoggerMixin):
    """
    Repository for task persistence in Cosmos DB.

    This class provides thread-safe, retry-enabled access to Cosmos DB
    with proper error handling and logging.
    
    Note: Azure Cosmos SDK is synchronous, so we use ThreadPoolExecutor
    to make it work with async FastAPI.
    """

    def __init__(self):
        """Initialize Cosmos DB repository."""
        self.settings = get_settings()
        self._client: Optional[CosmosClient] = None
        self._database: Optional[DatabaseProxy] = None
        self._container: Optional[ContainerProxy] = None
        self._executor = ThreadPoolExecutor(max_workers=10)

    async def _run_in_executor(self, func, *args, **kwargs):
        """Run a synchronous function in the thread pool executor."""
        loop = asyncio.get_event_loop()
        if kwargs:
            func = partial(func, **kwargs)
        return await loop.run_in_executor(self._executor, func, *args)

    async def initialize(self) -> None:
        """
        Initialize Cosmos DB connection.

        Raises:
            DatabaseConnectionError: If connection fails
        """
        try:
            self.logger.info("initializing_cosmos_db_connection")

            cosmos_settings = self.settings.cosmos_db

            # Determine authentication method
            if cosmos_settings.key:
                # Use key authentication
                self.logger.debug("using_key_authentication")
                self._client = CosmosClient(cosmos_settings.endpoint, cosmos_settings.key)
            else:
                # Use managed identity
                self.logger.debug("using_managed_identity_authentication")
                credential = DefaultAzureCredential()
                self._client = CosmosClient(cosmos_settings.endpoint, credential)

            # Get database
            self._database = self._client.get_database_client(cosmos_settings.database_name)

            # Get or create container
            try:
                self._container = self._database.get_container_client(cosmos_settings.container_name)
                # Verify container exists (synchronous call, no await)
                await self._run_in_executor(self._container.read)
                
            except CosmosResourceNotFoundError:
                self.logger.info("container_not_found_creating", container=cosmos_settings.container_name)
                # Create container (synchronous call)
                self._container = await self._run_in_executor(
                    self._database.create_container,
                    id=cosmos_settings.container_name,
                    partition_key=PartitionKey(path="/id"),
                )

            self.logger.info(
                "cosmos_db_initialized",
                database=cosmos_settings.database_name,
                container=cosmos_settings.container_name,
            )

        except Exception as e:
            self.logger.error("cosmos_db_initialization_failed", error=str(e), exc_info=True)
            raise DatabaseConnectionError(
                message="Failed to initialize Cosmos DB connection",
                details={"error": str(e)},
            ) from e

    async def create_task(self, task: TaskRecord) -> TaskRecord:
        """
        Create a new task record.

        Args:
            task: Task record to create

        Returns:
            TaskRecord: Created task record

        Raises:
            DatabaseOperationError: If creation fails
        """
        try:
            self.logger.info("creating_task", task_id=task.id)

            doc = task.to_cosmos_dict()
            created_doc = await self._run_in_executor(
                self._container.create_item,
                body=doc
            )

            created_task = TaskRecord.from_cosmos_dict(created_doc)

            self.logger.info("task_created", task_id=created_task.id)
            return created_task

        except CosmosHttpResponseError as e:
            self.logger.error("task_creation_failed", task_id=task.id, error=str(e), exc_info=True)
            raise DatabaseOperationError(
                message=f"Failed to create task: {task.id}",
                details={"task_id": task.id, "error": str(e)},
            ) from e

    async def get_task(self, task_id: str) -> TaskRecord:
        """
        Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            TaskRecord: Task record

        Raises:
            RecordNotFoundError: If task not found
            DatabaseOperationError: If retrieval fails
        """
        try:
            self.logger.debug("getting_task", task_id=task_id)

            doc = await self._run_in_executor(
                self._container.read_item,
                item=task_id,
                partition_key=task_id
            )
            task = TaskRecord.from_cosmos_dict(doc)

            self.logger.debug("task_retrieved", task_id=task_id)
            return task

        except CosmosResourceNotFoundError:
            self.logger.warning("task_not_found", task_id=task_id)
            raise RecordNotFoundError(
                message=f"Task not found: {task_id}",
                details={"task_id": task_id},
            )
        except Exception as e:
            self.logger.error("task_retrieval_failed", task_id=task_id, error=str(e), exc_info=True)
            raise DatabaseOperationError(
                message=f"Failed to retrieve task: {task_id}",
                details={"task_id": task_id, "error": str(e)},
            ) from e

    async def update_task(self, task: TaskRecord) -> TaskRecord:
        """
        Update existing task record.

        Args:
            task: Task record to update

        Returns:
            TaskRecord: Updated task record

        Raises:
            RecordNotFoundError: If task not found
            ConcurrencyError: If concurrent modification detected
            DatabaseOperationError: If update fails
        """
        try:
            self.logger.info("updating_task", task_id=task.id, status=task.status)

            doc = task.to_cosmos_dict()

            # Prepare replace_item call with etag for optimistic concurrency control
            replace_kwargs = {
                "item": task.id,
                "body": doc,
            }
            
            if task._etag:
                replace_kwargs["if_match"] = task._etag

            updated_doc = await self._run_in_executor(
                self._container.replace_item,
                **replace_kwargs
            )

            updated_task = TaskRecord.from_cosmos_dict(updated_doc)

            self.logger.info("task_updated", task_id=updated_task.id, status=updated_task.status)
            return updated_task

        except CosmosResourceNotFoundError:
            self.logger.warning("task_not_found_for_update", task_id=task.id)
            raise RecordNotFoundError(
                message=f"Task not found for update: {task.id}",
                details={"task_id": task.id},
            )
        except CosmosHttpResponseError as e:
            if e.status_code == 412:  # Precondition Failed
                self.logger.warning("concurrent_modification_detected", task_id=task.id)
                raise ConcurrencyError(resource_id=task.id, resource_type="task")
            else:
                self.logger.error("task_update_failed", task_id=task.id, error=str(e), exc_info=True)
                raise DatabaseOperationError(
                    message=f"Failed to update task: {task.id}",
                    details={"task_id": task.id, "error": str(e)},
                ) from e

    async def delete_task(self, task_id: str) -> None:
        """
        Delete task by ID.

        Args:
            task_id: Task ID

        Raises:
            RecordNotFoundError: If task not found
            DatabaseOperationError: If deletion fails
        """
        try:
            self.logger.info("deleting_task", task_id=task_id)

            await self._run_in_executor(
                self._container.delete_item,
                item=task_id,
                partition_key=task_id
            )

            self.logger.info("task_deleted", task_id=task_id)

        except CosmosResourceNotFoundError:
            self.logger.warning("task_not_found_for_deletion", task_id=task_id)
            raise RecordNotFoundError(
                message=f"Task not found for deletion: {task_id}",
                details={"task_id": task_id},
            )
        except Exception as e:
            self.logger.error("task_deletion_failed", task_id=task_id, error=str(e), exc_info=True)
            raise DatabaseOperationError(
                message=f"Failed to delete task: {task_id}",
                details={"task_id": task_id, "error": str(e)},
            ) from e

    def _query_tasks_sync(
        self,
        status: Optional[TaskStatus],
        limit: int,
        continuation_token: Optional[str],
    ) -> tuple[List[dict], Optional[str]]:
        """
        Synchronous helper for querying tasks.
        
        Returns:
            tuple: (List of task dicts, next continuation token)
        """
        # Build query
        if status:
            query = "SELECT * FROM c WHERE c.status = @status ORDER BY c.created_at DESC"
            parameters = [{"name": "@status", "value": status.value}]
        else:
            query = "SELECT * FROM c ORDER BY c.created_at DESC"
            parameters = None

        # Execute query with cross-partition enabled
        items = self._container.query_items(
            query=query,
            parameters=parameters,
            max_item_count=limit,
            continuation=continuation_token,
            enable_cross_partition_query=True,
        )

        tasks = []
        next_token = None

        # Get first page only
        for page in items.by_page():
            for doc in page:
                tasks.append(doc)
            # Get continuation token from pager's current status
            next_token = items.continuation_token if hasattr(items, 'continuation_token') else None
            break  # Only get first page

        return tasks, next_token

    async def query_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 100,
        continuation_token: Optional[str] = None,
    ) -> tuple[List[TaskRecord], Optional[str]]:
        """
        Query tasks with optional filters.

        Args:
            status: Optional status filter
            limit: Maximum number of results
            continuation_token: Token for pagination

        Returns:
            tuple: (List of tasks, next continuation token)

        Raises:
            DatabaseOperationError: If query fails
        """
        try:
            self.logger.debug("querying_tasks", status=status, limit=limit)

            # Run synchronous query in executor
            task_dicts, next_token = await self._run_in_executor(
                self._query_tasks_sync,
                status,
                limit,
                continuation_token
            )

            # Convert to TaskRecord objects
            tasks = [TaskRecord.from_cosmos_dict(doc) for doc in task_dicts]

            self.logger.debug("tasks_queried", count=len(tasks), has_more=bool(next_token))
            return tasks, next_token

        except Exception as e:
            self.logger.error("task_query_failed", error=str(e), exc_info=True)
            raise DatabaseOperationError(
                message="Failed to query tasks",
                details={"error": str(e), "status": status},
            ) from e

    async def create_audit_log(self, log: AuditLog) -> None:
        """
        Create audit log entry.

        Args:
            log: Audit log entry

        Raises:
            DatabaseOperationError: If creation fails
        """
        try:
            self.logger.debug("creating_audit_log", event_type=log.event_type)

            doc = log.model_dump()
            await self._run_in_executor(
                self._container.create_item,
                body=doc
            )

            self.logger.debug("audit_log_created", log_id=log.id)

        except Exception as e:
            # Log but don't raise - audit logging should not break main flow
            self.logger.error("audit_log_creation_failed", error=str(e), exc_info=True)

    async def close(self) -> None:
        """Close Cosmos DB connection and thread pool."""
        if self._client:
            # Cosmos client doesn't need explicit closing
            self._client = None
        
        if self._executor:
            self._executor.shutdown(wait=True)
            self.logger.info("cosmos_db_connection_closed")


# Global repository instance
_repository: Optional[CosmosDBRepository] = None


async def get_repository() -> CosmosDBRepository:
    """
    Get the global repository instance.

    Returns:
        CosmosDBRepository: Repository instance
    """
    global _repository
    if _repository is None:
        _repository = CosmosDBRepository()
        await _repository.initialize()
    return _repository
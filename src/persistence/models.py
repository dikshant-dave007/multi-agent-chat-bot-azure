"""
Data models for persistence layer.

This module defines the data models used throughout the application
for tasks, agents, and execution state.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "PENDING"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"


class TaskPriority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentType(str, Enum):
    """Agent types."""

    PLANNER = "planner"
    EXECUTOR = "executor"
    VALIDATOR = "validator"
    OBSERVER = "observer"


class AgentExecutionStatus(str, Enum):
    """Agent execution status."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class AgentExecution(BaseModel):
    """Record of agent execution."""

    execution_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: str
    agent_type: AgentType
    status: AgentExecutionStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = Field(default_factory=dict)
    token_usage: Dict[str, int] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExecutionPlan(BaseModel):
    """Execution plan created by planner agent."""

    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    dependencies: Dict[str, List[str]] = Field(default_factory=dict)
    estimated_duration_seconds: Optional[int] = None
    required_agents: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ValidationResult(BaseModel):
    """Validation result from validator agent."""

    validation_id: str = Field(default_factory=lambda: str(uuid4()))
    is_valid: bool
    confidence_score: float = Field(ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TaskRecord(BaseModel):
    """
    Task record stored in Cosmos DB.

    This is the primary data model for task storage and retrieval.
    """

    # Required fields
    id: str = Field(default_factory=lambda: f"task_{uuid4()}")
    task_description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Execution details
    correlation_id: Optional[str] = None
    agent_executions: List[AgentExecution] = Field(default_factory=list)
    execution_plan: Union[ExecutionPlan, Dict[str, Any], None] = None
    validation_result: Union[ValidationResult, Dict[str, Any], None] = None

    # Results
    result: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = Field(default_factory=dict)

    # Metrics
    duration_ms: Optional[int] = None
    retry_count: int = 0
    total_token_usage: Dict[str, int] = Field(default_factory=dict)

    # Context and metadata
    context: Dict[str, Any] = Field(default_factory=dict)
    callback_url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Cosmos DB fields
    _etag: Optional[str] = None
    _ts: Optional[int] = None

    class Config:
        """Pydantic configuration."""

        json_encoders = {datetime: lambda v: v.isoformat()}

    def to_cosmos_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for Cosmos DB storage.

        Returns:
            dict: Document for Cosmos DB
        """
        # Use model_dump with mode='json' to properly serialize datetime objects
        doc = self.model_dump(mode='json', exclude_none=False)
        
        # Ensure id is present for Cosmos DB
        doc["id"] = self.id
        
        return doc

    @classmethod
    def from_cosmos_dict(cls, doc: Dict[str, Any]) -> "TaskRecord":
        """
        Create TaskRecord from Cosmos DB document.

        Args:
            doc: Cosmos DB document

        Returns:
            TaskRecord: Task record instance
        """
        # Parse datetime strings back to datetime objects
        datetime_fields = ['created_at', 'updated_at', 'started_at', 'completed_at']
        
        for field in datetime_fields:
            if field in doc and doc[field] is not None and isinstance(doc[field], str):
                doc[field] = datetime.fromisoformat(doc[field].replace('Z', '+00:00'))
        
        # Parse agent_executions datetime fields
        if 'agent_executions' in doc:
            for execution in doc['agent_executions']:
                for field in ['started_at', 'completed_at']:
                    if field in execution and execution[field] is not None and isinstance(execution[field], str):
                        execution[field] = datetime.fromisoformat(execution[field].replace('Z', '+00:00'))
        
        # Convert execution_plan dict to ExecutionPlan object if needed
        if 'execution_plan' in doc and doc['execution_plan'] is not None and isinstance(doc['execution_plan'], dict):
            doc['execution_plan'] = ExecutionPlan(**doc['execution_plan'])
        
        # Convert validation_result dict to ValidationResult object if needed
        if 'validation_result' in doc and doc['validation_result'] is not None and isinstance(doc['validation_result'], dict):
            doc['validation_result'] = ValidationResult(**doc['validation_result'])
        
        return cls(**doc)

    def update_status(self, status: TaskStatus) -> None:
        """
        Update task status and timestamp.

        Args:
            status: New task status
        """
        self.status = status
        self.updated_at = datetime.utcnow()

        if status == TaskStatus.EXECUTING and self.started_at is None:
            self.started_at = datetime.utcnow()
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT]:
            self.completed_at = datetime.utcnow()
            if self.started_at:
                self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)

    def add_agent_execution(self, execution: AgentExecution) -> None:
        """
        Add agent execution record.

        Args:
            execution: Agent execution record
        """
        self.agent_executions.append(execution)
        self.updated_at = datetime.utcnow()

        # Aggregate token usage
        if execution.token_usage:
            for key, value in execution.token_usage.items():
                self.total_token_usage[key] = self.total_token_usage.get(key, 0) + value

    def is_terminal_state(self) -> bool:
        """
        Check if task is in terminal state.

        Returns:
            bool: True if task is in terminal state
        """
        return self.status in [
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        ]

    def can_retry(self, max_retries: int = 3) -> bool:
        """
        Check if task can be retried.

        Args:
            max_retries: Maximum number of retries allowed

        Returns:
            bool: True if task can be retried
        """
        return self.status == TaskStatus.FAILED and self.retry_count < max_retries


class AgentMemory(BaseModel):
    """
    Agent memory for maintaining context across executions.
    """

    agent_name: str
    memory_type: str  # short_term, long_term, episodic, semantic
    entries: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditLog(BaseModel):
    """
    Audit log entry for tracking system events.
    """

    id: str = Field(default_factory=lambda: f"audit_{uuid4()}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: str
    actor: str  # User, agent, or system component
    resource_type: str
    resource_id: str
    action: str
    status: str  # success, failure, partial
    details: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None

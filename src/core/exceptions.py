"""
Custom exception classes for the multi-agent automation engine.

This module defines a hierarchy of exceptions that provide clear error
semantics throughout the application stack.
"""

from typing import Any, Dict, Optional


class MultiAgentEngineException(Exception):
    """Base exception for all multi-agent engine errors."""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# Configuration and Setup Errors


class ConfigurationError(MultiAgentEngineException):
    """Raised when there's a configuration problem."""

    pass


class InitializationError(MultiAgentEngineException):
    """Raised when component initialization fails."""

    pass


# Task and Orchestration Errors


class TaskError(MultiAgentEngineException):
    """Base class for task-related errors."""

    pass


class TaskNotFoundError(TaskError):
    """Raised when a task cannot be found."""

    def __init__(self, task_id: str):
        super().__init__(
            message=f"Task not found: {task_id}",
            error_code="TASK_NOT_FOUND",
            details={"task_id": task_id},
        )


class TaskValidationError(TaskError):
    """Raised when task input validation fails."""

    pass


class TaskExecutionError(TaskError):
    """Raised when task execution fails."""

    pass


class TaskTimeoutError(TaskError):
    """Raised when task execution exceeds timeout."""

    def __init__(self, task_id: str, timeout_seconds: int):
        super().__init__(
            message=f"Task {task_id} exceeded timeout of {timeout_seconds} seconds",
            error_code="TASK_TIMEOUT",
            details={"task_id": task_id, "timeout_seconds": timeout_seconds},
        )


class TaskCancelledException(TaskError):
    """Raised when a task is cancelled."""

    def __init__(self, task_id: str):
        super().__init__(
            message=f"Task was cancelled: {task_id}",
            error_code="TASK_CANCELLED",
            details={"task_id": task_id},
        )


# Agent Errors


class AgentError(MultiAgentEngineException):
    """Base class for agent-related errors."""

    pass


class AgentNotFoundError(AgentError):
    """Raised when an agent cannot be found."""

    def __init__(self, agent_name: str):
        super().__init__(
            message=f"Agent not found: {agent_name}",
            error_code="AGENT_NOT_FOUND",
            details={"agent_name": agent_name},
        )


class AgentExecutionError(AgentError):
    """Raised when agent execution fails."""

    pass


class AgentTimeoutError(AgentError):
    """Raised when agent execution exceeds timeout."""

    pass


# LLM and Semantic Kernel Errors


class LLMError(MultiAgentEngineException):
    """Base class for LLM-related errors."""

    pass


class LLMRateLimitError(LLMError):
    """Raised when LLM rate limit is exceeded."""

    def __init__(self, retry_after_seconds: Optional[int] = None):
        details = {}
        if retry_after_seconds:
            details["retry_after_seconds"] = retry_after_seconds
        super().__init__(
            message="LLM rate limit exceeded",
            error_code="LLM_RATE_LIMIT",
            details=details,
        )


class LLMServiceError(LLMError):
    """Raised when LLM service returns an error."""

    pass


class LLMResponseError(LLMError):
    """Raised when LLM response cannot be parsed or is invalid."""

    pass


# Persistence Errors


class PersistenceError(MultiAgentEngineException):
    """Base class for persistence-related errors."""

    pass


class DatabaseConnectionError(PersistenceError):
    """Raised when database connection fails."""

    pass


class DatabaseOperationError(PersistenceError):
    """Raised when a database operation fails."""

    pass


class RecordNotFoundError(PersistenceError):
    """Raised when a record is not found in database."""

    pass


class ConcurrencyError(PersistenceError):
    """Raised when a concurrent modification is detected."""

    def __init__(self, resource_id: str, resource_type: str):
        super().__init__(
            message=f"Concurrent modification detected for {resource_type}: {resource_id}",
            error_code="CONCURRENCY_ERROR",
            details={"resource_id": resource_id, "resource_type": resource_type},
        )


# Authentication and Authorization Errors


class AuthenticationError(MultiAgentEngineException):
    """Raised when authentication fails."""

    pass


class AuthorizationError(MultiAgentEngineException):
    """Raised when user lacks required permissions."""

    def __init__(self, resource: str, action: str):
        super().__init__(
            message=f"Not authorized to {action} on {resource}",
            error_code="AUTHORIZATION_ERROR",
            details={"resource": resource, "action": action},
        )


# Validation Errors


class ValidationError(MultiAgentEngineException):
    """Raised when data validation fails."""

    pass


# External Service Errors


class ExternalServiceError(MultiAgentEngineException):
    """Base class for external service errors."""

    pass


class AzureServiceError(ExternalServiceError):
    """Raised when an Azure service returns an error."""

    pass


class KeyVaultError(AzureServiceError):
    """Raised when Key Vault operation fails."""

    pass


# Retry and Circuit Breaker Errors


class RetryExhaustedError(MultiAgentEngineException):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, operation: str, attempts: int):
        super().__init__(
            message=f"Retry exhausted for {operation} after {attempts} attempts",
            error_code="RETRY_EXHAUSTED",
            details={"operation": operation, "attempts": attempts},
        )


class CircuitBreakerOpenError(MultiAgentEngineException):
    """Raised when circuit breaker is open."""

    def __init__(self, service: str):
        super().__init__(
            message=f"Circuit breaker open for {service}",
            error_code="CIRCUIT_BREAKER_OPEN",
            details={"service": service},
        )

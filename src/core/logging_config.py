"""
Simplified logging configuration for Azure App Service deployment.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from structlog.types import EventDict, Processor


def setup_logging() -> None:
    """
    Configure simple console logging for Azure App Service.
    Azure automatically captures stdout/stderr to Log Stream.
    """
    # Simple console-only processors
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.dev.ConsoleRenderer(),
    ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging - console only
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    # Suppress noisy loggers
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (typically __name__)

    Returns:
        BoundLogger: Configured logger instance
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class.
    """

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        """Get logger for this class."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


def bind_correlation_id(correlation_id: str) -> None:
    """
    Bind correlation ID to context for all subsequent log messages.

    Args:
        correlation_id: Correlation ID to bind
    """
    structlog.contextvars.bind_contextvars(correlation_id=correlation_id)


def bind_task_id(task_id: str) -> None:
    """
    Bind task ID to context for all subsequent log messages.

    Args:
        task_id: Task ID to bind
    """
    structlog.contextvars.bind_contextvars(task_id=task_id)


def bind_agent_name(agent_name: str) -> None:
    """
    Bind agent name to context for all subsequent log messages.

    Args:
        agent_name: Agent name to bind
    """
    structlog.contextvars.bind_contextvars(agent_name=agent_name)


def clear_contextvars() -> None:
    """Clear all context variables."""
    structlog.contextvars.clear_contextvars()


def log_function_call(func_name: str, **kwargs: Any) -> None:
    """
    Log a function call with parameters.

    Args:
        func_name: Function name
        **kwargs: Function parameters to log
    """
    logger = get_logger("function_call")
    logger.debug("function_called", function=func_name, parameters=kwargs)


def log_function_result(func_name: str, result: Any, duration_ms: float) -> None:
    """
    Log a function result.

    Args:
        func_name: Function name
        result: Function result
        duration_ms: Execution duration in milliseconds
    """
    logger = get_logger("function_result")
    logger.debug(
        "function_completed",
        function=func_name,
        duration_ms=duration_ms,
        result_type=type(result).__name__,
    )


def log_exception(exc: Exception, context: Dict[str, Any]) -> None:
    """
    Log an exception with context.

    Args:
        exc: Exception to log
        context: Additional context information
    """
    logger = get_logger("exception")
    logger.error(
        "exception_occurred",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        **context,
        exc_info=True,
    )
    
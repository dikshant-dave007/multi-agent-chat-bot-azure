"""
Pydantic models for API requests and responses.

This module defines all request and response schemas for the FastAPI endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.persistence.models import TaskStatus, TaskPriority


# Request Models


class TaskSubmitRequest(BaseModel):
    """Request model for task submission."""

    task_description: str = Field(..., description="Description of the task to execute", min_length=10)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context for task")
    callback_url: Optional[str] = Field(None, description="URL to call when task completes")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task_description": "Analyze sales data for Q4 2024 and generate a comprehensive report",
                    "priority": "high",
                    "context": {
                        "department": "sales",
                        "quarter": "Q4",
                        "year": 2024
                    },
                    "callback_url": "https://example.com/webhook/tasks"
                }
            ]
        }
    }


class TaskCancelRequest(BaseModel):
    """Request model for task cancellation."""

    reason: Optional[str] = Field(None, description="Reason for cancellation")


# LangGraph Multi-Agent Models


class MultiAgentRequest(BaseModel):
    """Request model for multi-agent processing."""

    query: str = Field(..., description="User query or request", min_length=1)
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for tracking")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "Can you research the latest developments in AI?",
                    "conversation_id": "conv_123",
                    "context": {"user_id": "user_456"}
                },
                {
                    "query": "Hello! How are you?",
                }
            ]
        }
    }


class AgentMessage(BaseModel):
    """Message structure for agent communication."""

    role: str = Field(..., description="Message role: user, assistant, or system")
    content: str = Field(..., description="Message content")
    agent: Optional[str] = Field(None, description="Which agent generated this message")


class MultiAgentResponse(BaseModel):
    """Response model for multi-agent processing."""

    success: bool = Field(..., description="Whether processing was successful")
    conversation_id: str = Field(..., description="Conversation ID for tracking")
    user_query: str = Field(..., description="Original user query")
    intent: Optional[str] = Field(None, description="Detected intent: greeting, research, facility, database, celebration")
    agent: Optional[str] = Field(None, description="Agent that handled the request")
    response: Optional[str] = Field(None, description="Final response from the agent")
    messages: List[AgentMessage] = Field(default_factory=list, description="Conversation history")
    timestamp: datetime = Field(..., description="Processing timestamp")
    error: Optional[str] = Field(None, description="Error message if processing failed")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "conversation_id": "conv_123",
                    "user_query": "What are the latest AI trends?",
                    "intent": "research",
                    "agent": "ResearcherAgent",
                    "response": "The latest AI trends include...",
                    "messages": [
                        {
                            "role": "user",
                            "content": "What are the latest AI trends?",
                            "agent": None
                        },
                        {
                            "role": "assistant",
                            "content": "The latest AI trends include...",
                            "agent": "ResearcherAgent"
                        }
                    ],
                    "timestamp": "2024-01-15T10:00:00Z"
                }
            ]
        }
    }


# Response Models


class AgentExecutionResponse(BaseModel):
    """Response model for agent execution."""

    execution_id: str
    agent_name: str
    agent_type: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    error_message: Optional[str] = None


class ValidationResponse(BaseModel):
    """Response model for validation results."""

    is_valid: bool
    confidence_score: float
    issues: List[str]
    recommendations: List[str]


class TaskResponse(BaseModel):
    """Response model for task information."""

    task_id: str
    task_description: str
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    result: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    retry_count: int = 0
    agent_executions: List[AgentExecutionResponse] = Field(default_factory=list)
    validation_result: Optional[ValidationResponse] = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "task_id": "task_123e4567-e89b-12d3-a456-426614174000",
                    "task_description": "Analyze sales data",
                    "status": "COMPLETED",
                    "priority": "high",
                    "created_at": "2024-01-15T10:00:00Z",
                    "updated_at": "2024-01-15T10:05:00Z",
                    "started_at": "2024-01-15T10:00:05Z",
                    "completed_at": "2024-01-15T10:05:00Z",
                    "duration_ms": 295000,
                    "result": {
                        "summary": "Q4 sales increased by 15%",
                        "details": {}
                    },
                    "retry_count": 0
                }
            ]
        }
    }


class TaskSubmitResponse(BaseModel):
    """Response model for task submission."""

    task_id: str
    status: TaskStatus
    created_at: datetime
    estimated_duration_seconds: Optional[int] = None
    message: str = "Task submitted successfully"


class TaskListResponse(BaseModel):
    """Response model for task list."""

    tasks: List[TaskResponse]
    total_count: int
    continuation_token: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current timestamp")
    dependencies: Dict[str, str] = Field(..., description="Status of dependencies")


class MetricsResponse(BaseModel):
    """Response model for system metrics."""

    tasks_completed_total: int
    tasks_failed_total: int
    tasks_active: int
    avg_execution_time_ms: float
    success_rate: float
    agent_metrics: Dict[str, Dict[str, Any]]


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": "TASK_NOT_FOUND",
                    "message": "Task not found: task_123",
                    "details": {"task_id": "task_123"},
                    "timestamp": "2024-01-15T10:00:00Z"
                }
            ]
        }
    }



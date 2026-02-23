"""
FastAPI main application.

This module defines the FastAPI application with all routes,
middleware, error handlers, and lifecycle management.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, Dict
from uuid import uuid4
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.models.schemas import (
    ErrorResponse,
    MultiAgentRequest,
    MultiAgentResponse,
    AgentMessage,
)
from src.core.config import get_settings
from src.core.exceptions import (
    MultiAgentEngineException,
    TaskNotFoundError,

)
from src.core.logging_config import (
    setup_logging,
    get_logger,
    bind_correlation_id,
    clear_contextvars,

)

from src.persistence.cosmos_repository import get_repository
from src.persistence.models import TaskRecord, TaskStatus, TaskPriority

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown.

    Args:
        app: FastAPI application
    """
    # Startup
    logger.info("Application starting up...")
    logger.info("Initializing application with lifespan management")
    
    settings = get_settings()
    logger.info(f"📋 Loaded configuration: environment={settings.environment}, debug={settings.debug}")

    # Initialize database connection
    try:
        logger.info("Initializing database connection...")
        repository = await get_repository()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}", 
                    error=str(e), 
                    exc_info=True)
        raise

    logger.info(f"✅ Application started successfully in {settings.environment} environment")

    yield

    # Shutdown
    logger.info("Application shutting down...")
    logger.info("Application stopped")


# Create FastAPI application
app = FastAPI(
    title="Multi-Agent Custom Automation Engine",
    description="AI-driven multi-agent orchestration system for task automation",
    version="1.0.0",
    lifespan=lifespan,
)

# Get settings
settings = get_settings()
logger.info(f"🌐 API Configuration: host={settings.api.host}, port={settings.api.port}")
logger.info(f"🔗 CORS Origins: {settings.api.cors_origins}")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logger.info("✅ CORS middleware configured")


# Middleware for correlation ID
@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Add correlation ID to each request."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid4()))
    bind_correlation_id(correlation_id)
    
    logger.debug(f"Incoming request: {request.method} {request.url.path}",
                correlation_id=correlation_id,
                client_host=request.client.host if request.client else "unknown")

    try:
        response = await call_next(request)
        
        # Add correlation ID to response
        response.headers["X-Correlation-ID"] = correlation_id
        
        logger.debug(f"Response sent: status={response.status_code}",
                    correlation_id=correlation_id,
                    content_length=response.headers.get('content-length', 'unknown'))
        
    except Exception as e:
        logger.error(f"Request processing failed: {str(e)}",
                    correlation_id=correlation_id,
                    error=str(e),
                    exc_info=True)
        raise
    finally:
        # Clear context after request
        clear_contextvars()
        logger.debug(f"🧹 Cleared context variables for correlation_id={correlation_id}")

    return response


# Global exception handler
@app.exception_handler(MultiAgentEngineException)
async def engine_exception_handler(request: Request, exc: MultiAgentEngineException):
    """Handle custom engine exceptions."""
    logger.error(f"Engine exception: {exc.error_code} - {exc.message}",
                error_code=exc.error_code,
                message=exc.message,
                details=exc.details,
                path=request.url.path,
                method=request.method)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=ErrorResponse(
            error=exc.error_code,
            message=exc.message,
            details=exc.details,
        ).model_dump(mode='json'),
    )


@app.exception_handler(TaskNotFoundError)
async def task_not_found_handler(request: Request, exc: TaskNotFoundError):
    """Handle task not found exceptions."""
    logger.warning(f"🔍 Task not found: {exc.message}",
                  task_id=exc.details.get('task_id', 'unknown'),
                  path=request.url.path,
                  method=request.method)

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            error=exc.error_code,
            message=exc.message,
            details=exc.details,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.critical(f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
                   error_type=type(exc).__name__,
                   error=str(exc),
                   path=request.url.path,
                   method=request.method,
                   exc_info=True)

    error_response = ErrorResponse(
        error="INTERNAL_SERVER_ERROR",
        message="An internal error occurred",
        details={"error_type": type(exc).__name__},
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json'),
    )


# API Routes

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    logger.info("🌐 Root endpoint accessed")
    return {
        "message": "Multi-Agent Custom Automation Engine API",
        "version": "1.0.0",
        "docs": "/docs",
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "FastAPI Multi-Agent Chat Bot",
        "timestamp": datetime.now().isoformat()
    }


@app.post("/api/v1/multi_agent_process", response_model=MultiAgentResponse, tags=["Multi-Agent"])
async def multi_agent_process(request: MultiAgentRequest) -> MultiAgentResponse:
    """
    Process a user query through the multi-agent LangGraph system.

    This endpoint routes the user query to the appropriate agent:
    - Greeting Agent: For user greetings
    - Researcher Agent: For research and information requests
    - Database Agent: For database queries
    - Email Agent: For writing professional emails

    Args:
        request: MultiAgentRequest containing the user query

    Returns:
        MultiAgentResponse: Response from the appropriate agent
    """
    from src.orchestration.semantic_kernel_orchestrator import get_semantic_kernel_orchestrator
    
    logger.info(f"🤖 Multi-agent request received: {request.query[:100]}...")
    
    try:
        # Get the Semantic Kernel orchestrator
        orchestrator = get_semantic_kernel_orchestrator()
        
        # Process the request
        result = await orchestrator.process_request(
            user_query=request.query,
            conversation_id=request.conversation_id
        )
        
        if result["success"]:
            logger.info(
                f"✅ Multi-agent request processed successfully",
                conversation_id=result["conversation_id"],
                intent=result.get("intent"),
                agent=result.get("agent")
            )
            
            # Convert messages to proper format
            messages = [
                AgentMessage(
                    role=msg.get("role"),
                    content=msg.get("content"),
                    agent=msg.get("agent")
                )
                for msg in result.get("messages", [])
            ]
            
            return MultiAgentResponse(
                success=True,
                conversation_id=result["conversation_id"],
                user_query=result["user_query"],
                intent=result.get("intent"),
                agent=result.get("agent"),
                response=result.get("response"),
                messages=messages,
                timestamp=result["timestamp"]
            )
        else:
            logger.error(
                f"❌ Multi-agent request failed",
                conversation_id=result["conversation_id"],
                error=result.get("error")
            )
            
            return MultiAgentResponse(
                success=False,
                conversation_id=result["conversation_id"],
                user_query=result["user_query"],
                error=result.get("error"),
                timestamp=result["timestamp"]
            )
    
    except Exception as e:
        logger.error(f"❌ Multi-agent processing failed: {str(e)}", 
                    error=str(e),
                    exc_info=True)
        
        from datetime import datetime
        return MultiAgentResponse(
            success=False,
            conversation_id=request.conversation_id or str(uuid4()),
            user_query=request.query,
            error=str(e),
            timestamp=datetime.utcnow().isoformat()
        )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("🎬 Starting FastAPI application directly...")
    logger.info(f"Server will run on {settings.api.host}:{settings.api.port}")
    logger.info(f"Debug mode: {settings.debug}")
    
    uvicorn.run(
        "src.api.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.debug,
    )
"""
FastAPI application for LLM inference system.
Provides REST API endpoints for queued text generation.
"""
import time
import logging
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, Response
from celery.result import AsyncResult
import redis

from app.config import settings, logger
from app.models import (
    GenerateRequest,
    TaskResponse,
    ResultResponse,
    ErrorResponse,
    StatusResponse,
    HealthResponse,
    TaskMetrics
)
from app.auth import verify_api_key
from app.celery_app import celery_app
from app.tasks.inference import generate_text, health_check

# Optional enhancements
from app.streaming import stream_task_progress
from app.rate_limit import RateLimitMiddleware
from app.metrics import (
    PrometheusMiddleware,
    record_task_submitted,
    record_task_completed,
    update_system_metrics,
    get_metrics,
    CONTENT_TYPE_LATEST
)

# Initialize FastAPI app
app = FastAPI(
    title="LLM Inference System",
    description="Queue-based LLM inference API with comprehensive logging and monitoring",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware (60 requests per minute per API key)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    burst_size=10
)

# Add Prometheus metrics middleware
app.add_middleware(PrometheusMiddleware)

# Redis client for health checks
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    decode_responses=True
)


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "LLM Inference System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint.
    Verifies Redis connection and worker status.
    """
    # Check Redis connection
    try:
        redis_client.ping()
        redis_connected = True
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        redis_connected = False
    
    # Check if worker is available and model is loaded
    model_loaded = False
    try:
        # Send health check task with short timeout
        result = health_check.apply_async()
        worker_response = result.get(timeout=5)
        model_loaded = worker_response.get("model_loaded", False)
    except Exception as e:
        logger.warning(f"Worker health check failed: {str(e)}")
    
    # Update Prometheus metrics
    update_system_metrics(redis_connected, model_loaded)
    
    return HealthResponse(
        status="healthy" if redis_connected else "degraded",
        redis_connected=redis_connected,
        model_loaded=model_loaded,
        version="1.0.0"
    )


@app.post("/generate", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate(
    request: GenerateRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Submit a text generation request.
    
    The request is queued for processing and returns immediately with a task_id.
    Use the task_id to check status or retrieve results.
    
    Args:
        request: Generation request with prompt and parameters
        api_key: API key for authentication
        
    Returns:
        TaskResponse with task_id and status
        
    Raises:
        HTTPException: If request validation fails
    """
    try:
        # Record enqueue time for metrics
        enqueue_time = time.time()
        
        logger.info(f"Received generation request from user: {request.user_id or 'anonymous'}")
        logger.info(f"Prompt length: {len(request.prompt)} characters")
        
        # Submit task to Celery
        task = generate_text.apply_async(
            kwargs={
                "prompt": request.prompt,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "enqueue_time": enqueue_time
            }
        )
        
        logger.info(f"Task queued with ID: {task.id}")
        
        # Record metrics
        record_task_submitted(request.user_id or "anonymous")
        
        return TaskResponse(
            status="queued",
            task_id=task.id,
            message="Your request is being processed. Use the task_id to check status."
        )
        
    except Exception as e:
        logger.error(f"Failed to queue task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to queue request: {str(e)}"
        )


@app.get("/status/{task_id}", response_model=StatusResponse)
async def get_status(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Check the status of a task.
    
    Args:
        task_id: Unique task identifier
        api_key: API key for authentication
        
    Returns:
        StatusResponse with current task status
        
    Raises:
        HTTPException: If task_id is invalid
    """
    try:
        # Get task result
        result = AsyncResult(task_id, app=celery_app)
        
        # Map Celery states to our status
        if result.state == "PENDING":
            task_status = "queued"
            message = "Task is waiting in queue"
        elif result.state == "STARTED":
            task_status = "processing"
            message = "Task is currently being processed"
        elif result.state == "SUCCESS":
            task_status = "completed"
            message = "Task completed successfully"
        elif result.state == "FAILURE":
            task_status = "failed"
            message = "Task failed during processing"
        else:
            task_status = result.state.lower()
            message = f"Task state: {result.state}"
        
        return StatusResponse(
            status=task_status,
            task_id=task_id,
            message=message
        )
        
    except Exception as e:
        logger.error(f"Failed to get status for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve task status: {str(e)}"
        )


@app.get("/result/{task_id}")
async def get_result(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Retrieve the result of a completed task.
    
    Args:
        task_id: Unique task identifier
        api_key: API key for authentication
        
    Returns:
        ResultResponse if successful, ErrorResponse if failed, or status if still processing
        
    Raises:
        HTTPException: If task not found or other errors
    """
    try:
        # Get task result
        result = AsyncResult(task_id, app=celery_app)
        
        # Check if task is ready
        if not result.ready():
            # Task still processing or queued
            if result.state == "PENDING":
                return JSONResponse(
                    status_code=status.HTTP_202_ACCEPTED,
                    content={
                        "status": "queued",
                        "task_id": task_id,
                        "message": "Task is still in queue"
                    }
                )
            elif result.state == "STARTED":
                return JSONResponse(
                    status_code=status.HTTP_202_ACCEPTED,
                    content={
                        "status": "processing",
                        "task_id": task_id,
                        "message": "Task is currently being processed"
                    }
                )
            else:
                return JSONResponse(
                    status_code=status.HTTP_202_ACCEPTED,
                    content={
                        "status": result.state.lower(),
                        "task_id": task_id,
                        "message": f"Task state: {result.state}"
                    }
                )
        
        # Task is ready, get the result
        task_result = result.get()
        
        # Check if task succeeded or failed
        if task_result.get("status") == "completed":
            # Success - return result with metrics
            metrics_data = task_result.get("metrics", {})
            
            return ResultResponse(
                status="completed",
                task_id=task_id,
                result=task_result.get("result", ""),
                metrics=TaskMetrics(**metrics_data) if metrics_data else None
            )
        else:
            # Error - return error response
            return ErrorResponse(
                status="error",
                task_id=task_id,
                error_message=task_result.get("error_message", "Unknown error"),
                error_type=task_result.get("error_type")
            )
        
    except Exception as e:
        logger.error(f"Failed to get result for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve task result: {str(e)}"
        )


@app.get("/stream/{task_id}")
async def stream_result(
    task_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Stream task progress and result using Server-Sent Events (SSE).
    
    This endpoint provides real-time updates as the task progresses.
    Useful for showing live status in web applications.
    
    Args:
        task_id: Unique task identifier
        api_key: API key for authentication
        
    Returns:
        StreamingResponse with SSE events
        
    Example:
        ```javascript
        const eventSource = new EventSource('/stream/task-id-here');
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log(data.status, data.message);
        };
        ```
    """
    return StreamingResponse(
        stream_task_progress(task_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus text format for scraping.
    
    Metrics include:
    - HTTP request counts and durations
    - Task submission and completion counts
    - Task timing histograms
    - Token generation metrics
    - System status gauges
    
    Returns:
        Prometheus metrics in text format
    """
    return Response(
        content=get_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom exception handler for HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Custom exception handler for unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.fastapi_host,
        port=settings.fastapi_port,
        reload=True
    )

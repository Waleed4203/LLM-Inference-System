"""
Prometheus metrics for monitoring and observability.
Tracks API requests, task processing, and system performance.
"""
import time
import logging
from typing import Callable
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Task metrics
tasks_submitted_total = Counter(
    'tasks_submitted_total',
    'Total tasks submitted',
    ['user']
)

tasks_completed_total = Counter(
    'tasks_completed_total',
    'Total tasks completed',
    ['status']
)

task_queue_wait_seconds = Histogram(
    'task_queue_wait_seconds',
    'Task queue wait time in seconds'
)

task_processing_seconds = Histogram(
    'task_processing_seconds',
    'Task processing time in seconds'
)

task_total_seconds = Histogram(
    'task_total_seconds',
    'Task total time in seconds'
)

# Token metrics
tokens_generated_total = Counter(
    'tokens_generated_total',
    'Total tokens generated'
)

tokens_per_second = Histogram(
    'tokens_per_second',
    'Token generation speed'
)

# System metrics
active_tasks = Gauge(
    'active_tasks',
    'Number of active tasks'
)

redis_connected = Gauge(
    'redis_connected',
    'Redis connection status (1=connected, 0=disconnected)'
)

model_loaded = Gauge(
    'model_loaded',
    'Model loaded status (1=loaded, 0=not loaded)'
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for Prometheus metrics collection.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Collect metrics for each request.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
            
        Returns:
            HTTP response
        """
        # Skip metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)
        
        # Record request
        method = request.method
        endpoint = request.url.path
        
        # Time the request
        start_time = time.time()
        
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as e:
            status = 500
            raise
        finally:
            # Record metrics
            duration = time.time() - start_time
            
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
        
        return response


def record_task_submitted(user_id: str = "anonymous"):
    """Record task submission."""
    tasks_submitted_total.labels(user=user_id).inc()
    active_tasks.inc()


def record_task_completed(
    status: str,
    queue_wait_time: float,
    processing_time: float,
    total_time: float,
    completion_tokens: int = 0,
    tokens_per_sec: float = 0.0
):
    """
    Record task completion metrics.
    
    Args:
        status: Task status (success/error)
        queue_wait_time: Queue wait time in seconds
        processing_time: Processing time in seconds
        total_time: Total time in seconds
        completion_tokens: Number of tokens generated
        tokens_per_sec: Token generation speed
    """
    tasks_completed_total.labels(status=status).inc()
    active_tasks.dec()
    
    task_queue_wait_seconds.observe(queue_wait_time)
    task_processing_seconds.observe(processing_time)
    task_total_seconds.observe(total_time)
    
    if completion_tokens > 0:
        tokens_generated_total.inc(completion_tokens)
    
    if tokens_per_sec > 0:
        tokens_per_second.observe(tokens_per_sec)


def update_system_metrics(redis_status: bool, model_status: bool):
    """
    Update system status metrics.
    
    Args:
        redis_status: Redis connection status
        model_status: Model loaded status
    """
    redis_connected.set(1 if redis_status else 0)
    model_loaded.set(1 if model_status else 0)


def get_metrics() -> str:
    """
    Get Prometheus metrics in text format.
    
    Returns:
        Metrics in Prometheus text format
    """
    return generate_latest().decode('utf-8')

"""
Celery application configuration for distributed task queue.
"""
from celery import Celery
from app.config import settings

# Initialize Celery app
celery_app = Celery(
    "llm_inference",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.inference"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution
    task_track_started=True,
    task_time_limit=settings.task_time_limit,
    task_soft_time_limit=settings.task_time_limit - 10,
    
    # Result backend
    result_expires=3600,  # Results expire after 1 hour
    result_extended=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Only fetch one task at a time
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks (prevent memory leaks)
    
    # Retry settings
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,
)

# Optional: Configure task routes
celery_app.conf.task_routes = {
    "app.tasks.inference.*": {"queue": "inference"},
}

if __name__ == "__main__":
    celery_app.start()

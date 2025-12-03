"""
Pydantic models for request/response validation.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request model for text generation."""
    prompt: str = Field(..., min_length=1, max_length=10000, description="Input prompt for generation")
    max_tokens: Optional[int] = Field(default=512, ge=1, le=2048, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: Optional[float] = Field(default=0.9, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    user_id: Optional[str] = Field(default=None, description="Optional user identifier")


class TaskResponse(BaseModel):
    """Response model for queued tasks."""
    status: str = Field(..., description="Task status: 'queued'")
    task_id: str = Field(..., description="Unique task identifier")
    message: str = Field(..., description="Human-readable message")


class TaskMetrics(BaseModel):
    """Performance metrics for completed tasks."""
    queue_wait_time: float = Field(..., description="Time spent waiting in queue (seconds)")
    processing_time: float = Field(..., description="Time spent processing (seconds)")
    total_time: float = Field(..., description="Total time from submission to completion (seconds)")
    prompt_tokens: Optional[int] = Field(default=None, description="Number of tokens in prompt")
    completion_tokens: Optional[int] = Field(default=None, description="Number of tokens in completion")
    tokens_per_second: Optional[float] = Field(default=None, description="Generation speed")


class ResultResponse(BaseModel):
    """Response model for completed tasks."""
    status: str = Field(..., description="Task status: 'completed'")
    task_id: str = Field(..., description="Unique task identifier")
    result: str = Field(..., description="Generated text")
    metrics: Optional[TaskMetrics] = Field(default=None, description="Performance metrics")


class ErrorResponse(BaseModel):
    """Response model for failed tasks."""
    status: str = Field(default="error", description="Task status: 'error'")
    task_id: str = Field(..., description="Unique task identifier")
    error_message: str = Field(..., description="Error description")
    error_type: Optional[str] = Field(default=None, description="Exception type")


class StatusResponse(BaseModel):
    """Response model for task status checks."""
    status: str = Field(..., description="Task status: 'queued', 'processing', 'completed', 'failed'")
    task_id: str = Field(..., description="Unique task identifier")
    message: Optional[str] = Field(default=None, description="Additional information")
    progress: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Task progress (0-1)")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(default="healthy", description="Service status")
    redis_connected: bool = Field(..., description="Redis connection status")
    model_loaded: bool = Field(default=False, description="Whether model is loaded in worker")
    version: str = Field(default="1.0.0", description="API version")

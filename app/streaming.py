"""
Streaming utilities for real-time token generation.
Supports Server-Sent Events (SSE) for streaming responses.
"""
import asyncio
import json
import logging
from typing import AsyncGenerator, Optional
from celery.result import AsyncResult
from app.celery_app import celery_app

logger = logging.getLogger(__name__)


async def stream_task_progress(task_id: str, poll_interval: float = 0.5) -> AsyncGenerator[str, None]:
    """
    Stream task progress and result using Server-Sent Events.
    
    Args:
        task_id: Celery task ID
        poll_interval: Seconds between status checks
        
    Yields:
        SSE formatted messages with task status and progress
    """
    result = AsyncResult(task_id, app=celery_app)
    
    # Send initial status
    yield f"data: {json.dumps({'status': 'queued', 'message': 'Task queued'})}\n\n"
    
    while True:
        # Check task state
        if result.state == "PENDING":
            yield f"data: {json.dumps({'status': 'queued', 'message': 'Waiting in queue'})}\n\n"
        
        elif result.state == "STARTED":
            yield f"data: {json.dumps({'status': 'processing', 'message': 'Processing request'})}\n\n"
        
        elif result.state == "SUCCESS":
            # Task completed - send final result
            task_result = result.get()
            
            if task_result.get("status") == "completed":
                # Send completion event
                yield f"data: {json.dumps({'status': 'completed', 'result': task_result.get('result'), 'metrics': task_result.get('metrics')})}\n\n"
            else:
                # Send error event
                yield f"data: {json.dumps({'status': 'error', 'error_message': task_result.get('error_message'), 'error_type': task_result.get('error_type')})}\n\n"
            
            # Send done signal
            yield "data: [DONE]\n\n"
            break
        
        elif result.state == "FAILURE":
            # Task failed
            yield f"data: {json.dumps({'status': 'error', 'error_message': 'Task failed', 'error_type': 'TaskFailure'})}\n\n"
            yield "data: [DONE]\n\n"
            break
        
        else:
            # Unknown state
            yield f"data: {json.dumps({'status': result.state.lower(), 'message': f'Task state: {result.state}'})}\n\n"
        
        # Wait before next check
        await asyncio.sleep(poll_interval)


async def stream_tokens(task_id: str) -> AsyncGenerator[str, None]:
    """
    Stream generated tokens in real-time (if model supports streaming).
    
    Note: This is a placeholder for future implementation.
    Current implementation streams the final result when complete.
    
    Args:
        task_id: Celery task ID
        
    Yields:
        SSE formatted messages with generated tokens
    """
    # For now, use progress streaming
    # Future: Implement actual token-by-token streaming with model.generate(streamer=...)
    async for event in stream_task_progress(task_id):
        yield event

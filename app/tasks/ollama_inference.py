"""
Celery tasks for Ollama LLM inference.
"""
import time
import logging
import traceback
import requests
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from app.celery_app import celery_app
from app.config import settings

logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Raised when Ollama API fails."""
    pass


def log_request_metrics(
    task_id: str,
    status: str,
    enqueue_time: float,
    start_time: float,
    end_time: float,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    error_message: Optional[str] = None
):
    """Log request metrics to llm_requests.log."""
    log_dir = Path(settings.log_dir)
    log_file = log_dir / "llm_requests.log"
    
    queue_wait = start_time - enqueue_time
    processing_time = end_time - start_time
    total_time = end_time - enqueue_time
    
    timestamp = datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
    
    log_parts = [
        f"[{timestamp}]",
        f"task_id={task_id}",
        f"backend=ollama",
        f"model={settings.ollama_model}",
        f"status={status}",
    ]
    
    if prompt_tokens is not None:
        log_parts.append(f"prompt_tokens={prompt_tokens}")
    
    if completion_tokens is not None:
        log_parts.append(f"completion_tokens={completion_tokens}")
        if processing_time > 0:
            tokens_per_sec = completion_tokens / processing_time
            log_parts.append(f"tokens_per_sec={tokens_per_sec:.2f}")
    
    log_parts.extend([
        f"queue_wait={queue_wait:.2f}s",
        f"processing_time={processing_time:.2f}s",
        f"total_time={total_time:.2f}s",
    ])
    
    if error_message:
        log_parts.append(f"error_message=\"{error_message}\"")
    
    log_entry = " ".join(log_parts) + "\n"
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    logger.info(f"Request metrics logged: {task_id} - {status}")


def log_error_traceback(task_id: str, error: Exception):
    """Log detailed error traceback to errors.log."""
    log_dir = Path(settings.log_dir)
    error_log = log_dir / "errors.log"
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    error_entry = (
        f"\n{'='*80}\n"
        f"[{timestamp}] ERROR - Task {task_id} failed (Ollama)\n"
        f"Error Type: {type(error).__name__}\n"
        f"Error Message: {str(error)}\n"
        f"\nTraceback:\n"
        f"{traceback.format_exc()}\n"
        f"{'='*80}\n"
    )
    
    with open(error_log, "a", encoding="utf-8") as f:
        f.write(error_entry)
    
    logger.error(f"Error traceback logged for task {task_id}")


def call_ollama_api(
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.9
) -> Dict[str, Any]:
    """
    Call Ollama API to generate text.
    
    Args:
        prompt: Input text prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        top_p: Nucleus sampling parameter
        
    Returns:
        Dict with response and token counts
        
    Raises:
        OllamaError: If API call fails
    """
    url = f"{settings.ollama_base_url}/api/generate"
    
    payload = {
        "model": settings.ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
        }
    }
    
    try:
        logger.info(f"Calling Ollama API: {url}")
        logger.info(f"Model: {settings.ollama_model}")
        
        response = requests.post(url, json=payload, timeout=settings.task_time_limit)
        response.raise_for_status()
        
        data = response.json()
        
        # Handle thinking models (like qwen3) that return response in 'thinking' field
        response_text = data.get("response", "")
        if not response_text and data.get("thinking"):
            response_text = data.get("thinking", "")
        
        return {
            "response": response_text,
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
            "total_duration": data.get("total_duration", 0) / 1e9,  # Convert to seconds
        }
        
    except requests.exceptions.Timeout:
        raise OllamaError(f"Ollama API timeout after {settings.task_time_limit}s")
    except requests.exceptions.ConnectionError:
        raise OllamaError(f"Cannot connect to Ollama at {settings.ollama_base_url}. Is Ollama running?")
    except requests.exceptions.HTTPError as e:
        raise OllamaError(f"Ollama API error: {e.response.status_code} - {e.response.text}")
    except Exception as e:
        raise OllamaError(f"Ollama API call failed: {str(e)}")


@celery_app.task(bind=True, name="app.tasks.ollama_inference.generate_text_ollama")
def generate_text_ollama(
    self: Task,
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.9,
    enqueue_time: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generate text using Ollama.
    
    Args:
        prompt: Input text prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        top_p: Nucleus sampling parameter
        enqueue_time: When the task was enqueued (for metrics)
        
    Returns:
        Dict with status, result, and metrics
    """
    task_id = self.request.id
    start_time = time.time()
    
    if enqueue_time is None:
        enqueue_time = start_time
    
    logger.info(f"Starting Ollama task {task_id}")
    logger.info(f"Prompt length: {len(prompt)} characters")
    
    try:
        # Call Ollama API
        result = call_ollama_api(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
        )
        
        end_time = time.time()
        
        # Calculate metrics
        queue_wait_time = start_time - enqueue_time
        processing_time = end_time - start_time
        total_time = end_time - enqueue_time
        
        prompt_tokens = result["prompt_tokens"]
        completion_tokens = result["completion_tokens"]
        tokens_per_second = completion_tokens / processing_time if processing_time > 0 else 0
        
        logger.info(f"Task {task_id} completed successfully")
        logger.info(f"Generated {completion_tokens} tokens in {processing_time:.2f}s ({tokens_per_second:.2f} tokens/s)")
        
        # Log metrics
        log_request_metrics(
            task_id=task_id,
            status="success",
            enqueue_time=enqueue_time,
            start_time=start_time,
            end_time=end_time,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )
        
        return {
            "status": "completed",
            "task_id": task_id,
            "result": result["response"],
            "metrics": {
                "queue_wait_time": queue_wait_time,
                "processing_time": processing_time,
                "total_time": total_time,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "tokens_per_second": tokens_per_second
            }
        }
        
    except SoftTimeLimitExceeded:
        end_time = time.time()
        error_msg = f"Task exceeded time limit of {settings.task_time_limit}s"
        
        logger.error(f"Task {task_id} timed out")
        
        log_request_metrics(
            task_id=task_id,
            status="error",
            enqueue_time=enqueue_time,
            start_time=start_time,
            end_time=end_time,
            error_message=error_msg
        )
        
        return {
            "status": "error",
            "task_id": task_id,
            "error_message": error_msg,
            "error_type": "TimeoutError"
        }
        
    except OllamaError as e:
        end_time = time.time()
        error_msg = str(e)
        
        logger.error(f"Task {task_id} failed: {error_msg}")
        
        log_error_traceback(task_id, e)
        log_request_metrics(
            task_id=task_id,
            status="error",
            enqueue_time=enqueue_time,
            start_time=start_time,
            end_time=end_time,
            error_message=error_msg
        )
        
        return {
            "status": "error",
            "task_id": task_id,
            "error_message": error_msg,
            "error_type": "OllamaError"
        }
        
    except Exception as e:
        end_time = time.time()
        error_msg = str(e)
        error_type = type(e).__name__
        
        logger.error(f"Task {task_id} failed with {error_type}: {error_msg}")
        
        log_error_traceback(task_id, e)
        log_request_metrics(
            task_id=task_id,
            status="error",
            enqueue_time=enqueue_time,
            start_time=start_time,
            end_time=end_time,
            error_message=error_msg
        )
        
        return {
            "status": "error",
            "task_id": task_id,
            "error_message": error_msg,
            "error_type": error_type
        }


@celery_app.task(name="app.tasks.ollama_inference.health_check_ollama")
def health_check_ollama() -> Dict[str, Any]:
    """
    Health check for Ollama connection.
    
    Returns:
        Dict with health status
    """
    try:
        url = f"{settings.ollama_base_url}/api/tags"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        models = response.json().get("models", [])
        model_names = [m.get("name") for m in models]
        
        return {
            "status": "healthy",
            "ollama_connected": True,
            "available_models": model_names,
            "configured_model": settings.ollama_model,
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "ollama_connected": False,
            "error": str(e),
            "timestamp": time.time()
        }

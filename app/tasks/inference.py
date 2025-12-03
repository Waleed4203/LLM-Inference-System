"""
Celery tasks for LLM inference with comprehensive logging and error handling.
"""
import time
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded

from app.celery_app import celery_app
from app.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Global model and tokenizer (loaded once per worker)
_model = None
_tokenizer = None
_model_loaded = False


class ModelLoadError(Exception):
    """Raised when model fails to load."""
    pass


def get_model_and_tokenizer():
    """
    Load and cache the LLM model and tokenizer.
    This is called once per worker process at startup.
    
    Returns:
        Tuple of (model, tokenizer)
        
    Raises:
        ModelLoadError: If model fails to load
    """
    global _model, _tokenizer, _model_loaded
    
    if _model_loaded and _model is not None and _tokenizer is not None:
        return _model, _tokenizer
    
    try:
        logger.info(f"Loading model: {settings.model_name}")
        logger.info(f"Device: {settings.model_device}")
        
        # Determine device
        if settings.model_device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA requested but not available, falling back to CPU")
            device = "cpu"
        else:
            device = settings.model_device
        
        # Load tokenizer
        logger.info("Loading tokenizer...")
        _tokenizer = AutoTokenizer.from_pretrained(
            settings.model_name,
            trust_remote_code=True
        )
        
        # Ensure tokenizer has pad token
        if _tokenizer.pad_token is None:
            _tokenizer.pad_token = _tokenizer.eos_token
        
        # Load model
        logger.info("Loading model...")
        load_kwargs = {
            "pretrained_model_name_or_path": settings.model_name,
            "trust_remote_code": True,
        }
        
        # Configure device and quantization
        if device == "cuda":
            if settings.use_quantization:
                logger.info("Using 4-bit quantization")
                load_kwargs["device_map"] = "auto"
                load_kwargs["load_in_4bit"] = True
            else:
                load_kwargs["device_map"] = "auto"
                load_kwargs["torch_dtype"] = torch.float16
        else:
            load_kwargs["device_map"] = "cpu"
        
        _model = AutoModelForCausalLM.from_pretrained(**load_kwargs)
        
        # Set to eval mode
        _model.eval()
        
        _model_loaded = True
        logger.info(f"Model loaded successfully on {device}")
        
        # Log GPU memory if using CUDA
        if device == "cuda":
            memory_allocated = torch.cuda.memory_allocated() / 1024**3
            memory_reserved = torch.cuda.memory_reserved() / 1024**3
            logger.info(f"GPU Memory - Allocated: {memory_allocated:.2f}GB, Reserved: {memory_reserved:.2f}GB")
        
        return _model, _tokenizer
        
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        logger.error(traceback.format_exc())
        raise ModelLoadError(f"Failed to load model: {str(e)}")


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
    """
    Log request metrics to llm_requests.log in human-readable format.
    
    Args:
        task_id: Unique task identifier
        status: 'success' or 'error'
        enqueue_time: When task was enqueued
        start_time: When processing started
        end_time: When processing ended
        prompt_tokens: Number of input tokens
        completion_tokens: Number of output tokens
        error_message: Error message if failed
    """
    log_dir = Path(settings.log_dir)
    log_file = log_dir / "llm_requests.log"
    
    # Calculate metrics
    queue_wait = start_time - enqueue_time
    processing_time = end_time - start_time
    total_time = end_time - enqueue_time
    
    # Format timestamp
    timestamp = datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
    
    # Build log entry
    log_parts = [
        f"[{timestamp}]",
        f"task_id={task_id}",
        f"status={status}",
    ]
    
    if prompt_tokens is not None:
        log_parts.append(f"prompt_tokens={prompt_tokens}")
    
    if completion_tokens is not None:
        log_parts.append(f"completion_tokens={completion_tokens}")
        
        # Calculate tokens per second
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
    
    # Write to log file
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)
    
    logger.info(f"Request metrics logged: {task_id} - {status}")


def log_error_traceback(task_id: str, error: Exception):
    """
    Log detailed error traceback to errors.log.
    
    Args:
        task_id: Unique task identifier
        error: Exception that occurred
    """
    log_dir = Path(settings.log_dir)
    error_log = log_dir / "errors.log"
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    error_entry = (
        f"\n{'='*80}\n"
        f"[{timestamp}] ERROR - Task {task_id} failed\n"
        f"Error Type: {type(error).__name__}\n"
        f"Error Message: {str(error)}\n"
        f"\nTraceback:\n"
        f"{traceback.format_exc()}\n"
        f"{'='*80}\n"
    )
    
    with open(error_log, "a", encoding="utf-8") as f:
        f.write(error_entry)
    
    logger.error(f"Error traceback logged for task {task_id}")


@celery_app.task(bind=True, name="app.tasks.inference.generate_text")
def generate_text(
    self: Task,
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.9,
    enqueue_time: Optional[float] = None
) -> Dict[str, Any]:
    """
    Generate text using the LLM model.
    
    This task:
    1. Loads the model (if not already loaded)
    2. Generates text from the prompt
    3. Logs comprehensive metrics
    4. Handles errors gracefully
    
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
    
    # Use current time if enqueue_time not provided
    if enqueue_time is None:
        enqueue_time = start_time
    
    logger.info(f"Starting task {task_id}")
    logger.info(f"Prompt length: {len(prompt)} characters")
    
    try:
        # Load model and tokenizer
        try:
            model, tokenizer = get_model_and_tokenizer()
        except ModelLoadError as e:
            end_time = time.time()
            error_msg = f"Model loading failed: {str(e)}"
            
            # Log error
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
                "error_type": "ModelLoadError"
            }
        
        # Tokenize input
        logger.info("Tokenizing input...")
        inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
        
        # Move to device
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        prompt_tokens = inputs["input_ids"].shape[1]
        logger.info(f"Prompt tokens: {prompt_tokens}")
        
        # Generate text
        logger.info("Generating text...")
        generation_start = time.time()
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        
        generation_end = time.time()
        logger.info(f"Generation completed in {generation_end - generation_start:.2f}s")
        
        # Decode output
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Remove the prompt from output (only return generated part)
        if generated_text.startswith(prompt):
            result_text = generated_text[len(prompt):].strip()
        else:
            result_text = generated_text
        
        completion_tokens = outputs.shape[1] - prompt_tokens
        
        end_time = time.time()
        
        # Calculate metrics
        queue_wait_time = start_time - enqueue_time
        processing_time = end_time - start_time
        total_time = end_time - enqueue_time
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
            "result": result_text,
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
        
        # Log timeout
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
        
    except Exception as e:
        end_time = time.time()
        error_msg = str(e)
        error_type = type(e).__name__
        
        logger.error(f"Task {task_id} failed with {error_type}: {error_msg}")
        
        # Log error with full traceback
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


@celery_app.task(name="app.tasks.inference.health_check")
def health_check() -> Dict[str, Any]:
    """
    Health check task to verify worker is running and model is loaded.
    
    Returns:
        Dict with health status
    """
    global _model_loaded
    
    return {
        "status": "healthy",
        "model_loaded": _model_loaded,
        "timestamp": time.time()
    }

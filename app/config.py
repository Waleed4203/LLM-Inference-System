"""
Configuration management for LLM Inference System.
Loads settings from environment variables with sensible defaults.
"""
import os
import logging
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Redis Configuration
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL from components."""
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    # API Configuration
    api_keys: str = Field(default="dev-key-12345", env="API_KEYS")
    fastapi_host: str = Field(default="0.0.0.0", env="FASTAPI_HOST")
    fastapi_port: int = Field(default=8000, env="FASTAPI_PORT")
    
    @property
    def api_keys_list(self) -> List[str]:
        """Parse comma-separated API keys."""
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]
    
    # Model Configuration
    model_name: str = Field(default="gpt2", env="MODEL_NAME")
    model_device: str = Field(default="cuda", env="MODEL_DEVICE")
    use_quantization: bool = Field(default=False, env="USE_QUANTIZATION")
    max_new_tokens: int = Field(default=512, env="MAX_NEW_TOKENS")
    temperature: float = Field(default=0.7, env="TEMPERATURE")
    
    # Task Configuration
    task_time_limit: int = Field(default=120, env="TASK_TIME_LIMIT")
    celery_concurrency: int = Field(default=1, env="CELERY_CONCURRENCY")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_dir: str = Field(default="logs", env="LOG_DIR")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()


def setup_logging():
    """Configure logging for the application."""
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "app.log"),
            logging.StreamHandler()
        ]
    )
    
    # Configure specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("celery").setLevel(logging.INFO)
    
    return logging.getLogger(__name__)


# Initialize logging
logger = setup_logging()

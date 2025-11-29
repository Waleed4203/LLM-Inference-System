"""
Rate limiting middleware for API endpoints.
Implements token bucket algorithm for request throttling.
"""
import time
import logging
from typing import Dict, Tuple
from collections import defaultdict
from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter.
    
    Allows burst traffic while maintaining average rate limit.
    """
    
    def __init__(self, requests_per_minute: int = 60, burst_size: int = 10):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_minute: Maximum requests per minute
            burst_size: Maximum burst size (tokens in bucket)
        """
        self.rate = requests_per_minute / 60.0  # Requests per second
        self.burst_size = burst_size
        self.buckets: Dict[str, Tuple[float, float]] = defaultdict(lambda: (burst_size, time.time()))
    
    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed for given key.
        
        Args:
            key: Identifier (e.g., API key or IP address)
            
        Returns:
            True if request is allowed, False otherwise
        """
        tokens, last_update = self.buckets[key]
        now = time.time()
        
        # Add tokens based on time elapsed
        elapsed = now - last_update
        tokens = min(self.burst_size, tokens + elapsed * self.rate)
        
        if tokens >= 1.0:
            # Allow request and consume token
            self.buckets[key] = (tokens - 1.0, now)
            return True
        else:
            # Rate limit exceeded
            self.buckets[key] = (tokens, now)
            return False
    
    def get_retry_after(self, key: str) -> float:
        """
        Get seconds until next request is allowed.
        
        Args:
            key: Identifier
            
        Returns:
            Seconds to wait
        """
        tokens, _ = self.buckets[key]
        if tokens >= 1.0:
            return 0.0
        return (1.0 - tokens) / self.rate


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    """
    
    def __init__(self, app, requests_per_minute: int = 60, burst_size: int = 10):
        """
        Initialize middleware.
        
        Args:
            app: FastAPI application
            requests_per_minute: Rate limit per API key
            burst_size: Burst size
        """
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute, burst_size)
        self.requests_per_minute = requests_per_minute
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request with rate limiting.
        
        Args:
            request: HTTP request
            call_next: Next middleware/handler
            
        Returns:
            HTTP response
            
        Raises:
            HTTPException: If rate limit exceeded
        """
        # Skip rate limiting for health check and docs
        if request.url.path in ["/", "/health", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get API key from header
        api_key = request.headers.get("X-API-Key", "anonymous")
        
        # Check rate limit
        if not self.limiter.is_allowed(api_key):
            retry_after = self.limiter.get_retry_after(api_key)
            
            logger.warning(f"Rate limit exceeded for key: {api_key[:8]}...")
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute.",
                headers={"Retry-After": str(int(retry_after) + 1)}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        
        return response

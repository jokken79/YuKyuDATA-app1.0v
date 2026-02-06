import time
import logging
import os
from typing import Dict, List, Optional, Callable
from abc import ABC, abstractmethod
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

class RateLimitStorage(ABC):
    @abstractmethod
    def check_limit(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int, int]:
        """Returns (is_allowed, remaining, reset_time)"""
        pass

class InMemoryStorage(RateLimitStorage):
    def __init__(self):
        self.requests: Dict[str, List[float]] = {}

    def check_limit(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int, int]:
        now = time.time()
        
        # Initialize or clean up old requests
        if key not in self.requests:
            self.requests[key] = []
        
        self.requests[key] = [t for t in self.requests[key] if now - t < window_seconds]
        
        if len(self.requests[key]) >= max_requests:
            reset_time = int(min(self.requests[key]) + window_seconds) if self.requests[key] else int(now + window_seconds)
            return False, 0, reset_time
            
        self.requests[key].append(now)
        remaining = max_requests - len(self.requests[key])
        reset_time = int(now + window_seconds)
        
        return True, remaining, reset_time

class RedisStorage(RateLimitStorage):
    """Placeholder for Redis implementation"""
    def __init__(self, redis_client):
        self.redis = redis_client

    def check_limit(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int, int]:
        # Typical Redis implementation using LUA script or INCR/EXPIRE
        # For now, this is a blueprint for the user
        pass

class AdvancedRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced Rate Limiting Middleware
    - Redis-ready storage abstraction
    - Custom limits per route type
    - Detailed X-RateLimit headers
    """
    def __init__(
        self, 
        app: ASGIApp, 
        storage: Optional[RateLimitStorage] = None,
        default_limit: int = 100,
        default_window: int = 60,
        exclude_paths: List[str] = None
    ):
        super().__init__(app)
        self.storage = storage or InMemoryStorage()
        self.default_limit = default_limit
        self.default_window = default_window
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/redoc", "/favicon.ico"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # Skip in testing
        if os.environ.get("TESTING") == "true":
            return await call_next(request)

        # Identify client (IP or API Key/User if authenticated)
        # Using IP as fallback
        client_id = request.client.host if request.client else "unknown"
        
        # Route-specific limits (can be expanded)
        limit = self.default_limit
        window = self.default_window
        
        if "/api/auth/" in request.url.path:
            limit = 10 # Strict login limits
            window = 60
        elif "/api/admin/" in request.url.path:
            limit = 50
        
        key = f"rl:{client_id}:{request.url.path}" # Per-path limiting
        # Or just per-client: key = f"rl:{client_id}"
        
        allowed, remaining, reset = self.storage.check_limit(key, limit, window)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded: {key}")
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Too many requests. Please slow down.",
                    "details": {
                        "limit": limit,
                        "reset_at_unix": reset,
                        "retry_after_seconds": max(0, reset - int(time.time()))
                    }
                },
                headers={
                    "Retry-After": str(max(0, reset - int(time.time()))),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset)
                }
            )

        response = await call_next(request)
        
        # Add rate limit info to headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset)
        
        return response

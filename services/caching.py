"""
Caching Module for YuKyuDATA
Simple in-memory caching with configurable TTL

Features:
- Decorator-based caching
- TTL (time-to-live) support
- Cache invalidation
- Statistics tracking
"""

from functools import wraps
from time import time
from typing import Optional, Callable, Any, Dict
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class SimpleCache:
    """Simple in-memory cache with TTL support"""

    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache

        Args:
            default_ttl: Default time-to-live in seconds
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None if expired/missing
        """
        if key not in self.cache:
            self.misses += 1
            return None

        entry = self.cache[key]

        # Check if expired
        if entry['expires_at'] < time():
            del self.cache[key]
            self.misses += 1
            return None

        self.hits += 1
        return entry['value']

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        ttl = ttl or self.default_ttl
        self.cache[key] = {
            'value': value,
            'expires_at': time() + ttl,
            'created_at': time()
        }

    def delete(self, key: str):
        """Delete key from cache"""
        if key in self.cache:
            del self.cache[key]

    def clear(self):
        """Clear entire cache"""
        self.cache.clear()
        logger.info("Cache cleared")

    def invalidate_pattern(self, pattern: str):
        """
        Invalidate all keys matching pattern

        Args:
            pattern: Pattern to match (simple wildcard: '*' matches anything)
        """
        keys_to_delete = []

        for key in self.cache.keys():
            # Simple pattern matching
            if pattern.replace('*', '') in key:
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del self.cache[key]

        logger.info(f"Invalidated {len(keys_to_delete)} cache keys matching: {pattern}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            'hits': self.hits,
            'misses': self.misses,
            'total_requests': total,
            'hit_rate': f"{hit_rate:.1f}%",
            'cached_items': len(self.cache),
            'memory_usage_approx': sum(len(str(v['value'])) for v in self.cache.values())
        }


# Global cache instance
_cache = SimpleCache(default_ttl=300)


def cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from arguments

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key
    """
    # Create a unique key from args and kwargs
    key_data = json.dumps(
        {
            'args': [str(arg) for arg in args],
            'kwargs': {k: str(v) for k, v in kwargs.items()}
        },
        sort_keys=True,
        default=str
    )
    return hashlib.md5(key_data.encode()).hexdigest()


def cached(ttl: Optional[int] = None, cache_instance: Optional[SimpleCache] = None):
    """
    Decorator for caching function results

    Args:
        ttl: Time-to-live in seconds
        cache_instance: Cache instance to use (default: global cache)

    Usage:
        @cached(ttl=300)
        def get_employee(emp_id: int):
            # Expensive operation
            return database.get_employee(emp_id)
    """
    cache = cache_instance or _cache

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{func.__module__}.{func.__name__}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {key}")
                return cached_value

            # Execute function
            logger.debug(f"Cache MISS: {key}")
            result = func(*args, **kwargs)

            # Store in cache
            cache.set(key, result, ttl)

            return result

        # Add cache control methods to wrapper
        wrapper.cache_clear = lambda: cache.delete(
            f"{func.__module__}.{func.__name__}:*"
        )
        wrapper.cache_info = lambda: cache.get_stats()

        return wrapper

    return decorator


# NOTE: cache_result decorator removed (2026-01) - never used in codebase
# Use @cached(ttl=...) decorator instead which auto-generates keys

def clear_cache():
    """Clear global cache"""
    _cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """Get global cache statistics"""
    return _cache.get_stats()


def invalidate_cache_pattern(pattern: str):
    """Invalidate cache keys matching pattern"""
    _cache.invalidate_pattern(pattern)


# Cache invalidation helpers
def invalidate_employee_cache(emp_id: Optional[int] = None):
    """Invalidate employee-related caches"""
    if emp_id:
        invalidate_cache_pattern(f"employee:{emp_id}")
    else:
        invalidate_cache_pattern("employee:*")


# NOTE: invalidate_genzai_cache, invalidate_ukeoi_cache, invalidate_stats_cache removed (2026-01)
# These were defined but never called. Use invalidate_cache_pattern("genzai:*") etc directly if needed.

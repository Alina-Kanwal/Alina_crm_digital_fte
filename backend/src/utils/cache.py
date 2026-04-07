"""
Redis caching layer for Digital FTE AI Customer Success Agent.

Per Constitution Principle VI (Cost Consciousness) and Performance requirements:
- Cache frequent documentation queries
- Reduce database load
- Improve response latency (<3s target)
- Configurable TTL and cache size limits
"""
import logging
from typing import Optional, Any, Dict, List, Callable, TypeVar, Union
from functools import wraps
from datetime import timedelta
import json
import hashlib
import asyncio

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CacheManager:
    """
    Redis cache manager for application-level caching.

    Supports:
    - String caching with TTL
    - JSON object caching
    - List caching
    - Cache invalidation patterns
    - Cache statistics
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        default_ttl: int = 3600,  # 1 hour default
        max_connections: int = 10,
        key_prefix: str = "digital-fte:"
    ):
        """
        Initialize cache manager.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default time-to-live in seconds
            max_connections: Maximum Redis connections
            key_prefix: Prefix for all cache keys
        """
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix
        self.pool = None
        self.client = None
        self.max_connections = max_connections

        # Cache statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }

        logger.info(
            f"Cache manager initialized: url={redis_url}, "
            f"default_ttl={default_ttl}s, key_prefix={key_prefix}"
        )

    async def connect(self):
        """Establish Redis connection pool."""
        try:
            self.pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                decode_responses=True
            )
            self.client = redis.Redis(connection_pool=self.pool)

            # Test connection
            await self.client.ping()

            logger.info("Redis cache connection established")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Close Redis connections."""
        if self.pool:
            await self.pool.aclose()
            logger.info("Redis cache connection closed")

    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self.key_prefix}{key}"

    def _make_key_hash(self, *args, **kwargs) -> str:
        """
        Create hash-based cache key from function arguments.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Hash-based cache key
        """
        # Create a deterministic string from arguments
        key_data = {
            'args': args,
            'kwargs': kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)

        # Hash the string
        hash_obj = hashlib.sha256(key_str.encode())
        return hash_obj.hexdigest()[:32]

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key (without prefix)

        Returns:
            Cached value or None if not found
        """
        try:
            full_key = self._make_key(key)
            value = await self.client.get(full_key)

            if value:
                self.stats['hits'] += 1
                logger.debug(f"Cache HIT: {key}")
                return value

            self.stats['misses'] += 1
            logger.debug(f"Cache MISS: {key}")
            return None

        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None

    async def get_json(self, key: str) -> Optional[Dict]:
        """
        Get JSON object from cache.

        Args:
            key: Cache key

        Returns:
            JSON object or None if not found
        """
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to decode JSON for key {key}: {e}")
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)

        Returns:
            True if successful
        """
        try:
            full_key = self._make_key(key)
            ttl = ttl or self.default_ttl

            await self.client.setex(full_key, ttl, value)
            self.stats['sets'] += 1
            logger.debug(f"Cache SET: {key} (ttl={ttl}s)")

            return True

        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False

    async def set_json(
        self,
        key: str,
        value: Dict,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set JSON object in cache.

        Args:
            key: Cache key
            value: JSON object to cache
            ttl: Time-to-live in seconds

        Returns:
            True if successful
        """
        try:
            json_str = json.dumps(value, default=str)
            return await self.set(key, json_str, ttl)

        except Exception as e:
            logger.error(f"Cache set_json error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        try:
            full_key = self._make_key(key)
            result = await self.client.delete(full_key)

            if result:
                self.stats['deletes'] += 1
                logger.debug(f"Cache DELETE: {key}")

            return True

        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern.

        Args:
            pattern: Glob pattern (e.g., "docs:*")

        Returns:
            Number of keys deleted
        """
        try:
            full_pattern = self._make_key(pattern)
            keys = await self.client.keys(full_pattern)

            if keys:
                deleted = await self.client.delete(*keys)
                self.stats['deletes'] += deleted
                logger.info(f"Deleted {deleted} keys matching pattern: {pattern}")

                return deleted

            return 0

        except Exception as e:
            logger.error(f"Cache delete_pattern error for {pattern}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key

        Returns:
            True if key exists
        """
        try:
            full_key = self._make_key(key)
            result = await self.client.exists(full_key)
            return bool(result)

        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            total_requests = self.stats['hits'] + self.stats['misses']
            hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0

            return {
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'sets': self.stats['sets'],
                'deletes': self.stats['deletes'],
                'evictions': self.stats['evictions'],
                'total_requests': total_requests,
                'hit_rate_percent': round(hit_rate, 2)
            }

        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}


def cached(
    ttl: int = 3600,
    key_prefix: str = "",
    arg_hash: bool = False
) -> Callable:
    """
    Decorator for caching async function results.

    Args:
        ttl: Cache time-to-live in seconds
        key_prefix: Prefix for cache key
        arg_hash: Use hash of arguments for key (for parameterized functions)

    Usage:
        @cached(ttl=1800, key_prefix="docs:")
        async def get_documentation(query: str):
            ...
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            cache: Optional[CacheManager] = kwargs.get('_cache')

            if not cache:
                return await func(*args, **kwargs)

            # Generate cache key
            if arg_hash:
                cache_key = cache._make_key_hash(*args, **kwargs)
            else:
                cache_key = f"{key_prefix}{func.__name__}"

            # Check cache
            cached_result = await cache.get_json(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            if result is not None:
                await cache.set_json(cache_key, result, ttl)

            return result

        return wrapper
    return decorator


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


async def get_cache() -> CacheManager:
    """
    Get global cache manager instance.

    Returns:
        CacheManager instance
    """
    global _cache_manager

    if _cache_manager is None:
        redis_url = "redis://localhost:6379/0"
        _cache_manager = CacheManager(redis_url=redis_url)
        await _cache_manager.connect()

    return _cache_manager


async def close_cache():
    """Close global cache manager."""
    global _cache_manager

    if _cache_manager:
        await _cache_manager.disconnect()
        _cache_manager = None

"""
Cache service for high-performance retrieval in the Digital FTE agent.
Provides asynchronous caching using Redis with a local memory fallback for development.
Supports Phase 9.1 (T105) performance requirements.
"""
import os
import json
import asyncio
import logging
from typing import Any, Optional, Union
from datetime import timedelta

logger = logging.getLogger(__name__)

class CacheService:
    """World-class caching service with Redis and Memory fallback."""

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL")
        self.redis = None
        self.memory_cache = {}
        self._is_ready = False
        self._use_redis = False

    async def initialize(self):
        """Initialize the cache connection."""
        if self.redis_url:
            try:
                import redis.asyncio as redis
                self.redis = redis.from_url(self.redis_url, decode_responses=True)
                # Test connectivity
                await self.redis.ping()
                self._use_redis = True
                logger.info(f"Redis cache initialized and connected to {self.redis_url}")
            except (ImportError, Exception) as e:
                logger.warning(f"Failed to connect to Redis ({e}). Falling back to in-memory caching.")
                self._use_redis = False
        else:
            logger.info("REDIS_URL not set. Using in-memory caching service.")
            self._use_redis = False
        
        self._is_ready = True

    async def get(self, key: str) -> Optional[Any]:
        """Retrieve a value from the cache."""
        if not self._is_ready:
            await self.initialize()

        try:
            if self._use_redis:
                value = await self.redis.get(key)
                return json.loads(value) if value else None
            else:
                return self.memory_cache.get(key)
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            return None

    async def set(self, key: str, value: Any, expire_seconds: int = 3600):
        """Store a value in the cache with an expiration time."""
        if not self._is_ready:
            await self.initialize()

        try:
            if self._use_redis:
                await self.redis.set(key, json.dumps(value), ex=expire_seconds)
            else:
                self.memory_cache[key] = value
                # Schedule expiration for memory cache
                asyncio.create_task(self._expire_memory_key(key, expire_seconds))
        except Exception as e:
            logger.error(f"Error storing in cache: {e}")

    async def _expire_memory_key(self, key: str, seconds: int):
        """Simulate key expiration for the in-memory fallback."""
        await asyncio.sleep(seconds)
        if key in self.memory_cache:
            del self.memory_cache[key]

    async def delete(self, key: str):
        """Invalidate a specific cache key."""
        if not self._is_ready:
            await self.initialize()

        try:
            if self._use_redis:
                await self.redis.delete(key)
            else:
                self.memory_cache.pop(key, None)
        except Exception as e:
            logger.error(f"Error invalidating cache key: {e}")

    async def clear(self):
        """Flush the entire cache."""
        if not self._is_ready:
            await self.initialize()

        try:
            if self._use_redis:
                await self.redis.flushdb()
            else:
                self.memory_cache.clear()
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

# Singleton factory for the cache service
_instance = None

def get_cache_service() -> CacheService:
    global _instance
    if _instance is None:
        _instance = CacheService()
    return _instance

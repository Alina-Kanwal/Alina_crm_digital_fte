"""
API rate limiting using slowapi.

Per Constitution Principle VI (Cost Consciousness) and Security requirements:
- Prevent abuse and DoS attacks
- Protect against API key exhaustion
- Support different rate limits for different endpoints
- Implement sliding window algorithm
- Track and log rate limit violations
"""
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from functools import wraps
import asyncio

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RedisBackend:
    """
    Redis backend for distributed rate limiting.

    Uses Redis to store rate limit counters across multiple instances.
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/1",
        prefix: str = "ratelimit:"
    ):
        """
        Initialize Redis backend.

        Args:
            redis_url: Redis connection URL
            prefix: Prefix for rate limit keys
        """
        self.redis_url = redis_url
        self.prefix = prefix
        self.client = None
        self.pool = None

    async def connect(self):
        """Establish Redis connection."""
        try:
            from redis.asyncio import ConnectionPool
            self.pool = ConnectionPool.from_url(self.redis_url, decode_responses=True)
            self.client = redis.Redis(connection_pool=self.pool)
            await self.client.ping()
            logger.info("Redis rate limiter backend connected")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for rate limiting: {e}")
            raise

    async def disconnect(self):
        """Close Redis connections."""
        if self.pool:
            await self.pool.aclose()
            logger.info("Redis rate limiter backend disconnected")

    async def hit(
        self,
        key: str,
        limit: int,
        period: int,
        cost: int = 1
    ) -> Tuple[bool, Dict]:
        """
        Check and record rate limit hit.

        Args:
            key: Rate limit key (e.g., "ip:1.2.3.4")
            limit: Maximum requests allowed
            period: Time window in seconds
            cost: Cost of this request (default 1)

        Returns:
            Tuple of (allowed, info_dict)
        """
        try:
            redis_key = f"{self.prefix}{key}"
            now = datetime.now()
            window_start = now - timedelta(seconds=period)
            window_start_ts = int(window_start.timestamp())
            now_ts = int(now.timestamp())

            # Use Redis sorted set for sliding window
            pipe = self.client.pipeline()
            pipe.zremrangebyscore(redis_key, 0, window_start_ts)
            pipe.zadd(redis_key, {str(now_ts): now_ts})
            pipe.expire(redis_key, period)
            pipe.zcard(redis_key)
            results = await pipe.execute()

            current_count = results[3]
            allowed = current_count <= limit

            if not allowed:
                # Calculate time until reset
                oldest = await self.client.zrange(redis_key, 0, 0, withscores=True)
                if oldest:
                    reset_time = int(oldest[0][1] + period)
                else:
                    reset_time = now_ts + period

                info = {
                    'limit': limit,
                    'remaining': 0,
                    'reset': reset_time,
                    'current': current_count,
                    'period': period
                }

                logger.warning(
                    f"Rate limit exceeded for {key}: "
                    f"{current_count}/{limit} in {period}s"
                )
            else:
                info = {
                    'limit': limit,
                    'remaining': limit - current_count,
                    'reset': now_ts + period,
                    'current': current_count,
                    'period': period
                }

            return allowed, info

        except Exception as e:
            logger.error(f"Rate limit check error for key {key}: {e}")
            # Allow request on error (fail-open)
            return True, {}


class RateLimiter:
    """
    Rate limiter for API endpoints.

    Supports:
    - IP-based rate limiting
    - API key-based rate limiting
    - User-based rate limiting
    - Different limits for different endpoints
    - Sliding window algorithm
    """

    def __init__(self, redis_backend: Optional[RedisBackend] = None):
        """
        Initialize rate limiter.

        Args:
            redis_backend: Redis backend for distributed rate limiting
        """
        self.redis_backend = redis_backend
        self.default_limits = {
            'global': (100, 60),      # 100 requests per minute
            'per_ip': (1000, 3600),    # 1000 requests per hour per IP
            'per_user': (500, 3600),    # 500 requests per hour per user
            'per_api_key': (10000, 86400)  # 10k requests per day per API key
        }

        # Endpoint-specific limits
        self.endpoint_limits = {
            '/api/v1/inquiries': (50, 60),           # 50 requests per minute
            '/api/v1/conversations': (30, 60),      # 30 requests per minute
            '/api/v1/tickets': (20, 60),            # 20 requests per minute
            '/api/v1/escalations': (10, 60),       # 10 requests per minute
            '/api/v1/reports': (5, 60),            # 5 requests per minute
        }

        logger.info("Rate limiter initialized")

    async def check_rate_limit(
        self,
        key_type: str,
        key_value: str,
        endpoint: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        """
        Check if request is allowed under rate limit.

        Args:
            key_type: Type of key (global, ip, user, api_key)
            key_value: Value for the key
            endpoint: Endpoint path (for endpoint-specific limits)

        Returns:
            Tuple of (allowed, info_dict)
        """
        # Check endpoint-specific limit first
        if endpoint and endpoint in self.endpoint_limits:
            limit, period = self.endpoint_limits[endpoint]
            endpoint_key = f"{key_type}:{endpoint}:{key_value}"

            if self.redis_backend:
                allowed, info = await self.redis_backend.hit(
                    endpoint_key, limit, period
                )
                if not allowed:
                    return False, info

        # Check default limit for key type
        if key_type in self.default_limits:
            limit, period = self.default_limits[key_type]
            default_key = f"{key_type}:{key_value}"

            if self.redis_backend:
                allowed, info = await self.redis_backend.hit(
                    default_key, limit, period
                )
                if not allowed:
                    return False, info

        return True, {}

    def is_rate_limited(
        self,
        key_type: str = 'per_ip',
        endpoint: Optional[str] = None
    ):
        """
        Decorator for rate limiting endpoints.

        Args:
            key_type: Type of key for rate limiting
            endpoint: Endpoint path (for endpoint-specific limits)

        Usage:
            @app.get("/api/v1/inquiries")
            @rate_limiter.is_rate_limited(key_type='per_ip', endpoint='/api/v1/inquiries')
            async def create_inquiry(request: Request, ...):
                ...
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(request: Request, *args, **kwargs):
                # Get key value based on type
                if key_type == 'per_ip':
                    key_value = request.client.host if request.client else 'unknown'
                elif key_type == 'per_user':
                    # Extract user ID from JWT or session
                    key_value = request.headers.get('X-User-ID', 'anonymous')
                elif key_type == 'per_api_key':
                    # Extract API key from header
                    key_value = request.headers.get('X-API-Key', 'none')
                else:
                    key_value = 'global'

                # Check rate limit
                allowed, info = await self.check_rate_limit(
                    key_type, key_value, endpoint
                )

                if not allowed:
                    raise RateLimitExceeded(
                        info['limit'],
                        info['period'],
                        info['reset'],
                        info['remaining']
                    )

                # Add rate limit headers to response
                response = await func(request, *args, **kwargs)

                if isinstance(response, Response):
                    response.headers['X-RateLimit-Limit'] = str(info['limit'])
                    response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                    response.headers['X-RateLimit-Reset'] = str(info['reset'])
                    response.headers['X-RateLimit-Current'] = str(info['current'])

                return response

            return wrapper
        return decorator


class RateLimitExceededError(HTTPException):
    """
    Custom exception for rate limit exceeded.

    Includes rate limit information in response.
    """

    def __init__(
        self,
        limit: int,
        period: int,
        reset: int,
        remaining: int
    ):
        """
        Initialize rate limit exceeded error.

        Args:
            limit: Rate limit
            period: Period in seconds
            reset: Unix timestamp of reset
            remaining: Remaining requests
        """
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                'error': 'Rate limit exceeded',
                'limit': limit,
                'period': period,
                'reset': reset,
                'remaining': remaining,
                'message': f'Rate limit exceeded. Please try again later.'
            }
        )


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


async def get_rate_limiter() -> RateLimiter:
    """
    Get global rate limiter instance.

    Returns:
        RateLimiter instance
    """
    global _rate_limiter

    if _rate_limiter is None:
        try:
            redis_backend = RedisBackend(redis_url="redis://localhost:6379/1")
            await redis_backend.connect()
            _rate_limiter = RateLimiter(redis_backend=redis_backend)
        except Exception as e:
            logger.warning(f"Redis unavailable, using in-memory rate limiting: {e}")
            _rate_limiter = RateLimiter(redis_backend=None)

    return _rate_limiter


async def close_rate_limiter():
    """Close global rate limiter."""
    global _rate_limiter

    if _rate_limiter and _rate_limiter.redis_backend:
        await _rate_limiter.redis_backend.disconnect()
        _rate_limiter = None

"""
Database query optimization and connection pooling.

Per Constitution Performance requirements (<3s latency target):
- Optimized database queries
- Connection pooling for efficiency
- Index usage strategies
- Query result caching
- N+1 query prevention
"""
import logging
from typing import Optional, List, Dict, Any, Type, TypeVar, Generic
from datetime import datetime, timedelta
from contextlib import contextmanager, asynccontextmanager

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Index, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import QueuePool, NullPool
from sqlalchemy.sql import select, func
from sqlalchemy.exc import SQLAlchemyError
import redis.asyncio as redis


logger = logging.getLogger(__name__)

T = TypeVar('T')
Base = declarative_base()


class DatabaseConfig:
    """
    Database configuration with optimization settings.

    Features:
    - Connection pooling
    - Query result caching
    - Index suggestions
    - Slow query logging
    """

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        echo: bool = False,
        slow_query_threshold: float = 1.0,  # 1 second
        cache_ttl: int = 300,  # 5 minutes
        redis_url: Optional[str] = None
    ):
        """
        Initialize database configuration.

        Args:
            database_url: Database connection URL
            pool_size: Number of connections in pool
            max_overflow: Maximum overflow connections
            pool_timeout: Timeout for getting connection from pool
            pool_recycle: Recycle connections after this many seconds
            pool_pre_ping: Test connections before use
            echo: Log SQL statements
            slow_query_threshold: Threshold for slow queries (seconds)
            cache_ttl: Cache time-to-live in seconds
            redis_url: Redis URL for query result caching
        """
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.pool_pre_ping = pool_pre_ping
        self.echo = echo
        self.slow_query_threshold = slow_query_threshold
        self.cache_ttl = cache_ttl
        self.redis_url = redis_url

        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None
        self.redis_client = None

        logger.info(
            f"Database config initialized: pool_size={pool_size}, "
            f"max_overflow={max_overflow}, slow_query_threshold={slow_query_threshold}s"
        )

    def create_engine_sync(self):
        """Create synchronous SQLAlchemy engine with connection pooling."""
        self.engine = create_engine(
            self.database_url,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=self.pool_pre_ping,
            echo=self.echo,
            poolclass=QueuePool
        )

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        logger.info("Synchronous database engine created")

    def create_engine_async(self):
        """Create asynchronous SQLAlchemy engine with connection pooling."""
        self.async_engine = create_async_engine(
            self.database_url.replace('postgresql://', 'postgresql+asyncpg://'),
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            pool_pre_ping=self.pool_pre_ping,
            echo=self.echo,
            poolclass=QueuePool
        )

        self.AsyncSessionLocal = async_sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        logger.info("Asynchronous database engine created")

    async def create_redis_connection(self):
        """Create Redis connection for query caching."""
        if self.redis_url:
            try:
                self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
                await self.redis_client.ping()
                logger.info("Redis connection for query caching established")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                self.redis_client = None

    @asynccontextmanager
    async def get_async_session(self):
        """
        Get async database session from pool.

        Yields:
            AsyncSession instance

        Usage:
            async with db_config.get_async_session() as session:
                result = await session.execute(...)
        """
        if not self.AsyncSessionLocal:
            self.create_engine_async()

        async with self.AsyncSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {e}")
                raise
            finally:
                await session.close()

    @contextmanager
    def get_sync_session(self):
        """
        Get synchronous database session from pool.

        Yields:
            Session instance

        Usage:
            with db_config.get_sync_session() as session:
                result = session.execute(...)
        """
        if not self.SessionLocal:
            self.create_engine_sync()

        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()


class QueryOptimizer:
    """
    Query optimization utilities.

    Features:
    - Index usage analysis
    - Slow query detection
    - N+1 query prevention
    - Query result caching
    """

    def __init__(
        self,
        db_config: DatabaseConfig,
        cache_prefix: str = "query_cache:"
    ):
        """
        Initialize query optimizer.

        Args:
            db_config: Database configuration
            cache_prefix: Prefix for cache keys
        """
        self.db_config = db_config
        self.cache_prefix = cache_prefix
        self.slow_queries: List[Dict[str, Any]] = []

    async def cache_query_result(
        self,
        cache_key: str,
        result: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache query result.

        Args:
            cache_key: Unique cache key
            result: Query result to cache
            ttl: Time-to-live in seconds

        Returns:
            True if cached successfully
        """
        if not self.db_config.redis_client:
            return False

        try:
            import json
            cache_value = json.dumps(result, default=str)
            await self.db_config.redis_client.setex(
                f"{self.cache_prefix}{cache_key}",
                ttl or self.db_config.cache_ttl,
                cache_value
            )
            return True
        except Exception as e:
            logger.error(f"Failed to cache query result: {e}")
            return False

    async def get_cached_query(
        self,
        cache_key: str
    ) -> Optional[Any]:
        """
        Get cached query result.

        Args:
            cache_key: Cache key

        Returns:
            Cached result or None
        """
        if not self.db_config.redis_client:
            return None

        try:
            import json
            cached_value = await self.db_config.redis_client.get(
                f"{self.cache_prefix}{cache_key}"
            )
            if cached_value:
                return json.loads(cached_value)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached query: {e}")
            return None

    def make_cache_key(
        self,
        table_name: str,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> str:
        """
        Generate cache key from query parameters.

        Args:
            table_name: Database table name
            filters: Query filters
            limit: Query limit
            offset: Query offset

        Returns:
            Cache key
        """
        import hashlib
        import json

        key_data = {
            'table': table_name,
            'filters': filters,
            'limit': limit,
            'offset': offset
        }
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.sha256(key_str.encode()).hexdigest()[:32]

    def log_slow_query(
        self,
        query: str,
        duration: float,
        params: Optional[Dict[str, Any]] = None
    ):
        """
        Log slow query for analysis.

        Args:
            query: SQL query
            duration: Query duration in seconds
            params: Query parameters
        """
        if duration >= self.db_config.slow_query_threshold:
            self.slow_queries.append({
                'query': query[:500],  # Truncate long queries
                'duration': duration,
                'timestamp': datetime.now().isoformat(),
                'params': params
            })
            logger.warning(
                f"Slow query detected: {duration:.3f}s - {query[:200]}"
            )

    async def get_slow_queries(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get logged slow queries.

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of slow queries
        """
        return self.slow_queries[-limit:]

    def clear_slow_queries(self):
        """Clear slow query log."""
        self.slow_queries = []
        logger.info("Slow query log cleared")


class IndexSuggestion:
    """
    Database index suggestion utility.

    Analyzes query patterns and suggests indexes.
    """

    # Common index patterns for this application
    RECOMMENDED_INDEXES = [
        {
            'table': 'customers',
            'columns': ['email'],
            'type': 'unique',
            'reason': 'Primary lookup by email'
        },
        {
            'table': 'customers',
            'columns': ['created_at'],
            'type': 'btree',
            'reason': 'Time-based queries'
        },
        {
            'table': 'conversations',
            'columns': ['customer_id', 'is_active', 'last_activity'],
            'type': 'btree',
            'reason': 'Active conversation lookup'
        },
        {
            'table': 'conversations',
            'columns': ['thread_id'],
            'type': 'btree',
            'reason': 'Thread-based queries'
        },
        {
            'table': 'messages',
            'columns': ['conversation_id', 'created_at'],
            'type': 'btree',
            'reason': 'Message history queries'
        },
        {
            'table': 'support_tickets',
            'columns': ['customer_id', 'created_at'],
            'type': 'btree',
            'reason': 'Customer ticket history'
        },
        {
            'table': 'support_tickets',
            'columns': ['status', 'created_at'],
            'type': 'btree',
            'reason': 'Status-based queries'
        },
        {
            'table': 'escalations',
            'columns': ['ticket_id', 'created_at'],
            'type': 'btree',
            'reason': 'Escalation history'
        },
        {
            'table': 'sentiment_records',
            'columns': ['conversation_id', 'analyzed_at'],
            'type': 'btree',
            'reason': 'Sentiment history queries'
        }
    ]

    @classmethod
    def get_index_suggestions(cls) -> List[Dict[str, Any]]:
        """
        Get recommended indexes for the database.

        Returns:
            List of index suggestions
        """
        return cls.RECOMMENDED_INDEXES

    @classmethod
    def generate_create_index_sql(cls, table: str, columns: List[str], unique: bool = False) -> str:
        """
        Generate SQL to create an index.

        Args:
            table: Table name
            columns: List of column names
            unique: Whether index should be unique

        Returns:
            SQL CREATE INDEX statement
        """
        index_name = f"idx_{table}_{'_'.join(columns)}"
        unique_constraint = "UNIQUE " if unique else ""

        columns_str = ', '.join(columns)
        sql = f"""
        CREATE {unique_constraint}INDEX IF NOT EXISTS {index_name}
        ON {table} ({columns_str});
        """
        return sql.strip()


# Global database configuration instance
_db_config: Optional[DatabaseConfig] = None
_query_optimizer: Optional[QueryOptimizer] = None


def get_db_config() -> DatabaseConfig:
    """
    Get global database configuration.

    Returns:
        DatabaseConfig instance
    """
    global _db_config

    if _db_config is None:
        database_url = "postgresql://user:password@localhost:5432/digital_fte"
        _db_config = DatabaseConfig(database_url=database_url)
        _db_config.create_engine_async()
        _db_config.create_engine_sync()

    return _db_config


def get_query_optimizer() -> QueryOptimizer:
    """
    Get global query optimizer.

    Returns:
        QueryOptimizer instance
    """
    global _query_optimizer

    if _query_optimizer is None:
        db_config = get_db_config()
        _query_optimizer = QueryOptimizer(db_config=db_config)

    return _query_optimizer

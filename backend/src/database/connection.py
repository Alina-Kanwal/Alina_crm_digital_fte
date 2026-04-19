"""
Database connection pool management.

This module provides a centralized database connection pool
with proper connection management, pooling, and lifecycle handling.
"""

import os
import logging
from contextlib import contextmanager, asynccontextmanager
from typing import AsyncGenerator, Generator, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

# Load .env for local development (no-op on Render where env vars are injected)
try:
    from dotenv import load_dotenv
    # Try loading from project root (2 levels up from this file)
    _env_path = Path(__file__).resolve().parent.parent.parent.parent / '.env'
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path)
except ImportError:
    pass

# Database URL from environment
_RAW_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://dte_user:dte_password@localhost:5432/dte_db"
)

# Log the actual database URL being used (without credentials for security)
if _RAW_DATABASE_URL:
    # Parse URL to hide credentials in logs
    try:
        from urllib.parse import urlparse
        parsed = urlparse(_RAW_DATABASE_URL)
        safe_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}{parsed.path}"
        if parsed.username:
            safe_url = f"{parsed.scheme}://****:****@{parsed.hostname}:{parsed.port}{parsed.path}"
        logger.info(f"Database URL configured: {safe_url}")
    except Exception:
        logger.info("Database URL configured (credentials hidden in logs)")
else:
    logger.warning("DATABASE_URL not set, using default")

def _get_clean_urls(_url: str):
    """Sanitize and return both async and sync connection configs.
    
    Strips query params that asyncpg/psycopg2 don't support:
    - asyncpg: needs ssl=True in connect_args (not sslmode=require in URL)
    - psycopg2: needs sslmode=require in connect_args (not in URL for Neon)
    - Strips channel_binding=require (not asyncpg-supported)
    """
    # Extract base part (strip all query params)
    clean_base = _url.split('?')[0]
    
    # Determine if SSL is needed from the original URL
    is_ssl = (
        "sslmode=require" in _url.lower()
        or "ssl=true" in _url.lower()
        or "neon.tech" in _url.lower()  # Neon always needs SSL
    )
    
    # Async Config — use postgresql+asyncpg protocol
    if "postgresql+asyncpg" in clean_base:
        async_url = clean_base
    elif clean_base.startswith("postgresql://"):
        async_url = clean_base.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        async_url = clean_base
    
    async_args = {}
    if is_ssl:
        async_args["ssl"] = True
    
    # Sync Config — use plain postgresql:// protocol for psycopg2
    sync_url = async_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    sync_args = {}
    if is_ssl:
        sync_args["sslmode"] = "require"
    
    logger.info(f"DB CONFIG: host={async_url.split('@')[-1].split('/')[0]}, ssl={is_ssl}")
    
    return async_url, async_args, sync_url, sync_args

(ASYNC_URL, ASYNC_ARGS, SYNC_URL, SYNC_ARGS) = _get_clean_urls(_RAW_DATABASE_URL)

# Async engine for FastAPI - Optimized for Neon
async_engine = create_async_engine(
    ASYNC_URL,
    connect_args=ASYNC_ARGS,
    pool_size=10,
    max_overflow=5,
    pool_recycle=1800,
    pool_pre_ping=True,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync engine - Optimized for Neon
sync_engine = create_engine(
    SYNC_URL,
    connect_args=SYNC_ARGS,
    pool_size=5,
    max_overflow=2,
    pool_recycle=1800,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=sync_engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session.
    Yields a session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions (sync).

    Yields a SQLAlchemy session and ensures proper cleanup.
    Use for sync operations like migrations and admin tasks.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions.

    Yields an async SQLAlchemy session and ensures proper cleanup.
    Use for FastAPI route handlers and async operations.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """
    Initialize database connection and verify pgvector extension.
    Then create all tables if they don't exist (no mock up, real DB init).

    Raises:
        RuntimeError: If database connection fails or pg_extension missing
    """
    try:
        from src.models import Base
        
        # 1. Verify Extension (pgvector)
        async with AsyncSessionLocal() as session:
            # Check pgvector extension
            result = await session.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            )
            if not result.scalar():
                 # For "real working" in non-root PG, we check if it exists or can be created
                 try:
                     await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                     await session.commit()
                 except Exception:
                     raise RuntimeError("pgvector extension not installed. Run: CREATE EXTENSION vector;")
            
        # 2. Create tables (Sync engine used for schema creation)
        logger.info("Initializing database schema...")
        Base.metadata.create_all(bind=sync_engine)
        logger.info("Database schema initialized successfully.")

    except Exception as e:
        raise RuntimeError(f"Database initialization failed: {e}")


async def close_db() -> None:
    """
    Close all database connections.

    Call this on application shutdown.
    """
    await async_engine.dispose()
    sync_engine.dispose()


def check_db_health() -> bool:
    """
    Check if database is healthy and accessible.

    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        with sync_engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        logger.debug("Database health check passed")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def get_db_pool_stats() -> dict:
    """
    Get database pool statistics.

    Returns:
        dict: Pool statistics including size, checked out, overflow, etc.
    """
    pool = async_engine.pool
    return {
        "pool_size": pool.size(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "checked_in": pool.checkedin(),
    }

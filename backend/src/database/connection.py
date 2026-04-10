"""
Database connection pool management.

This module provides a centralized database connection pool
with proper connection management, pooling, and lifecycle handling.
"""

import os
import logging
from contextlib import contextmanager, asynccontextmanager
from typing import AsyncGenerator, Generator, Optional

logger = logging.getLogger(__name__)

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

# Database URL from environment
_RAW_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://dte_user:dte_password@localhost:5432/dte_db"
)

def _get_clean_urls(_url: str):
    """Sanitize and return both async and sync connection configs."""
    import re
    
    # Extract base part up to the first '?'
    clean_base = _url.split('?')[0]
    
    # Determine if SSL is needed from the original URL
    is_ssl = "sslmode=require" in _url.lower() or "ssl=true" in _url.lower()
    
    # Async Config
    async_url = clean_base if "postgresql+asyncpg" in clean_base else clean_base.replace("postgresql://", "postgresql+asyncpg://")
    async_args = {}
    if is_ssl:
        async_args["ssl"] = True
    
    # Sync Config
    sync_url = clean_base.replace("postgresql+asyncpg://", "postgresql://")
    sync_args = {}
    if is_ssl:
        sync_args["sslmode"] = "require"
    
    # Debug (will show in logs)
    print(f"DB CONFIG: async_url={async_url.split('@')[-1]}, sync_url={sync_url.split('@')[-1]}")
    
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
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
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

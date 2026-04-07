"""
Database connection pool management.

This module provides a centralized database connection pool
with proper connection management, pooling, and lifecycle handling.
"""

import os
from contextlib import contextmanager
from typing import AsyncGenerator, Generator, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

# Database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://dte_user:dte_password@localhost:5432/dte_db"
)

# Async engine for FastAPI
async_engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Sync engine (for migrations and admin tasks)
sync_engine = create_engine(
    DATABASE_URL.replace("+asyncpg", ""),
    pool_size=10,
    max_overflow=5,
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


@contextmanager
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

    Raises:
        RuntimeError: If database connection fails or pgvector not available
    """
    try:
        async with AsyncSessionLocal() as session:
            # Check pgvector extension
            result = await session.execute(
                text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
            )
            if not result.scalar():
                raise RuntimeError("pgvector extension not installed. Run: CREATE EXTENSION vector;")
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

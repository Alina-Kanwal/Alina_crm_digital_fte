"""
Database connection and session management for the Digital FTE agent.
Handles PostgreSQL connection with pgvector extension support.
Falls back to SQLite for development when PostgreSQL is not available.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load environment variables
load_dotenv()

_RAW_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://dte_user:dte_password@localhost:5432/dte_db"
)

def _get_clean_sync_url(_url: str):
    """Sanitize and return sync connection config for psycopg2."""
    if not _url or "sqlite" in _url:
        return _url or "sqlite:///./test.db", {}
        
    import re
    # Extract base part up to the first '?'
    clean_base = _url.split('?')[0]
    # Ensure sync protocol
    sync_url = clean_base.replace("postgresql+asyncpg://", "postgresql://")
    if not sync_url.startswith("postgresql://"):
        sync_url = f"postgresql://{sync_url}"
    
    # Check for SSL requirement
    is_ssl = "sslmode=require" in _url.lower() or "ssl=true" in _url.lower()
    
    sync_args = {}
    if is_ssl:
        sync_args["sslmode"] = "require"
        
    return sync_url, sync_args

DATABASE_URL, SYNC_CONNECT_ARGS = _get_clean_sync_url(_RAW_DATABASE_URL)
is_sqlite = "sqlite" in DATABASE_URL

engine_args = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
    "connect_args": SYNC_CONNECT_ARGS
}

if is_sqlite:
    # SQLite specific configurations
    engine_args["connect_args"] = {"check_same_thread": False}
    engine_args["implicit_returning"] = False

engine = create_engine(DATABASE_URL, **engine_args)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db() -> Session:
    """
    Dependency to get database session.
    Yields a session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize database tables.
    Called on application startup.
    """
    Base.metadata.create_all(bind=engine)

def check_db_connection():
    """
    Check if database connection is healthy.
    Returns True if connection is successful, False otherwise.
    """
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return True
    except Exception:
        return False
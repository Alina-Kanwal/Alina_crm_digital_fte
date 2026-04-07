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

# Database configuration - try PostgreSQL first, fallback to SQLite for development
def get_database_url():
    """Get database URL with fallback to SQLite for development."""
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Test if PostgreSQL is available
        try:
            import psycopg2
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:],  # Remove leading '/'
                connect_timeout=3
            )
            conn.close()
            return database_url
        except Exception:
            # PostgreSQL not available, fallback to SQLite for development
            pass

    # Fallback to SQLite for development
    return "sqlite:///./test.db"

# Create engine
DATABASE_URL = get_database_url()
is_sqlite = "sqlite" in DATABASE_URL
engine_args = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "echo": os.getenv("SQL_ECHO", "false").lower() == "true",
}

if is_sqlite:
    # SQLite specific configurations to avoid compatibility issues
    engine_args["connect_args"] = {"check_same_thread": False}
    # Explicitly disable RETURNING which causes e3q8 errors on some platforms
    engine_args["implicit_returning"] = False
else:
    # PostgreSQL specific configurations
    pass

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
"""
Database utilities for the Digital FTE agent.
Provides database-agnostic types and helpers.
"""
import os
import logging
from typing import Any

logger = logging.getLogger(__name__)

def get_vector_type():
    """
    Get the appropriate Vector type for the current database.
    - pgvector.sqlalchemy.Vector for PostgreSQL
    - sqlalchemy.JSON as a proxy for SQLite (development/benchmarking)
    """
    database_url = os.getenv("DATABASE_URL", "sqlite:///./test.db")
    use_pgvector = "sqlite" not in database_url
    
    if use_pgvector:
        try:
            from pgvector.sqlalchemy import Vector
            return Vector
        except ImportError:
            logger.warning("pgvector library not found, falling back to JSON proxy.")
            from sqlalchemy import JSON
            return JSON
    else:
        # For SQLite, we use JSON to store the list of floats
        from sqlalchemy import JSON
        return JSON

# Standard Vector type for usage in models
Vector = get_vector_type()
Vector1536 = Vector(1536) if hasattr(Vector, '__call__') and not issubclass(Vector, (object,)) else Vector # Simplified for type hint compatibility

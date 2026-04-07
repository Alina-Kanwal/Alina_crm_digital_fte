"""
Base SQLAlchemy model with common fields and methods.

All models should inherit from this base class for consistent
primary keys, timestamps, and common functionality.
"""

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import Column, DateTime, func, String
from sqlalchemy.ext.declarative import declarative_base

# Create base class for all models
Base = declarative_base()


class BaseModel(Base):
    """
    Base model class with common fields and methods.

    All models inherit from this class to automatically get:
    - id: UUID primary key
    - created_at: Timestamp when record was created
    - updated_at: Timestamp when record was last updated
    """
    __abstract__ = True

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now(), nullable=False)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert model instance to dictionary.

        Returns:
            dict: Dictionary representation of the model
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

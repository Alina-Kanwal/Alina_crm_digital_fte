"""
Model for durable storage of Kafka messages to prevent loss.
"""
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, Enum as SQLEnum
from sqlalchemy.sql import func
from src.models.base import BaseModel
import enum

class MessageStatus(str, enum.Enum):
    RECEIVED = "received"
    PUBLISHED = "published"
    CONSUMED = "consumed"
    PROCESSED = "processed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"

class PersistedMessage(BaseModel):
    """
    Durable storage for Kafka messages.
    Ensures messages are persisted before/after Kafka operations.
    """
    __tablename__ = "persisted_messages"

    topic = Column(String(255), nullable=False, index=True)
    partition = Column(Integer, nullable=True)
    offset = Column(Integer, nullable=True)
    key = Column(String(255), nullable=True)
    value = Column(Text, nullable=False)
    correlation_id = Column(String(100), nullable=True, index=True)
    status = Column(String(50), nullable=False, default=MessageStatus.RECEIVED.value, index=True)
    attempts = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<PersistedMessage(id={self.id}, topic='{self.topic}', status='{self.status}')>"

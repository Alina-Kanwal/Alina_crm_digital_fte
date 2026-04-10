"""
Model for Dead Letter Queue entries for failed Kafka messages.
"""
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer
from sqlalchemy.sql import func
from src.models.base import BaseModel

class DLQEntry(BaseModel):
    """
    Persistent storage and monitoring for messages that failed processing.
    """
    __tablename__ = "dlq_entries"

    original_topic = Column(String(255), nullable=False, index=True)
    message_content = Column(Text, nullable=False)
    error_reason = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, index=True)
    status = Column(String(50), nullable=False, default="pending", index=True)  # pending, resolved, abandoned
    
    metadata_json = Column(JSON, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    last_attempt_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<DLQEntry(id={self.id}, topic='{self.original_topic}', status='{self.status}')>"

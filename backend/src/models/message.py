"""
Message model for storing individual messages in conversations.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float, Index, JSON
from sqlalchemy.sql import func
from src.models.base import BaseModel

class Message(BaseModel):
    """
    Individual message record within a conversation thread.
    """
    __tablename__ = "messages"

    # UUID primary key inherited from BaseModel
    thread_id = Column(String(36), ForeignKey("conversation_threads.id"), nullable=False, index=True)
    content = Column(Text, nullable=False)
    channel = Column(String(50), nullable=False, index=True)  # email, whatsapp, webform
    direction = Column(String(10), nullable=False, index=True)  # incoming, outgoing
    sentiment = Column(String(50), nullable=True, index=True)  # positive, neutral, negative
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    message_metadata = Column(JSON, default=dict)

    # Composite index for thread retrieval sorted by timestamp
    __table_args__ = (
        Index('idx_thread_timestamp', 'thread_id', 'timestamp'),
    )

    def __repr__(self):
        return f"<Message(id={self.id}, thread_id={self.thread_id}, channel='{self.channel}', direction='{self.direction}')>"
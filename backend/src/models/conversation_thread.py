"""
Conversation thread model for maintaining cross-channel context.
"""
from sqlalchemy import Column, String, Text, JSON, ForeignKey, Index, DateTime, Integer, Boolean
from sqlalchemy.sql import func
from src.models.base import BaseModel


class ConversationThread(BaseModel):
    """
    Series of related messages across multiple channels.

    Enables seamless customer experience by preserving context
    regardless of communication channel.

    Attributes:
        id: UUID primary key (inherited from BaseModel)
        customer_id: Foreign key to Customer
        channel: Initial channel used
        status: status of thread (active, closed, escalated)
        subject: Brief summary of conversation topic
        started_at: First message in thread
        last_updated_at: Most recent message
        message_count: Total messages in thread
        channel_history: Array of channels used chronologically
        is_resolved: Whether conversation is resolved
        resolution_summary: How issue was resolved
        thread_metadata: Additional thread information
        created_at, updated_at: Timestamps from base
    """

    __tablename__ = "conversation_threads"

    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    channel = Column(String(50), nullable=False, index=True)  # email, whatsapp, webform
    status = Column(String(50), default="active", index=True)  # active, closed, escalated
    subject = Column(String(500), nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    last_updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), index=True)
    message_count = Column(Integer, default=0)
    channel_history = Column(JSON, default=lambda: list())  # Use callable to avoid shared mutable state
    is_resolved = Column(Boolean, default=False, index=True)
    resolution_summary = Column(Text, nullable=True)
    thread_metadata = Column(JSON, default=dict)

    # Added composite index for faster customer lookup of active threads
    __table_args__ = (
        Index('idx_customer_active_threads', 'customer_id', 'status'),
    )

    def __repr__(self):
        return f"<ConversationThread(id='{self.id}', customer_id='{self.customer_id}', subject='{self.subject}')>"

    @property
    def active_channels(self) -> list[str]:
        """
        Get list of unique channels used in this thread.

        Returns:
            list: List of channel names (email, whatsapp, web_form)
        """
        if self.channel_history:
            return list(set(self.channel_history))
        return [self.channel] if self.channel else []

    @property
    def duration_hours(self) -> float:
        """
        Calculate thread duration in hours.

        Returns:
            float: Hours between start and last update
        """
        if self.started_at and self.last_updated_at:
            return (self.last_updated_at - self.started_at).total_seconds() / 3600
        return 0

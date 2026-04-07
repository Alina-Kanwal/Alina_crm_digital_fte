"""
Support ticket model for tracking customer interactions with full lifecycle.
"""
from sqlalchemy import Column, String, Text, Float, DateTime, JSON, ForeignKey, Index
from src.models.base import BaseModel


class SupportTicket(BaseModel):
    """
    Record of a customer interaction with full lifecycle tracking.

    Used for SLA tracking, performance metrics, and continuous improvement.

    Attributes:
        id: UUID primary key
        customer_id: Foreign key to Customer
        channel: Where message came from (email, whatsapp, web_form)
        external_id: ID from external system (Gmail ID, WhatsApp ID, etc.)
        subject: Brief summary (for email/web form)
        content: Actual message content
        received_at: When message was received
        responded_at: When AI responded (nullable)
        resolved_at: When issue was resolved (nullable)
        ai_response: AI's response to customer
        sentiment: Detected customer sentiment (positive, neutral, negative)
        confidence_score: AI confidence (0-1)
        escalated: Whether ticket was escalated to human
        escalation_reason: Reason for escalation if applicable
        resolution_category: Type of issue (technical, billing, etc.)
        metadata: Additional ticket information
        created_at, updated_at: Timestamps from base
    """

    __tablename__ = "support_tickets"

    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    channel = Column(String(50), nullable=False, index=True)  # email, whatsapp, web_form
    external_id = Column(String(255), nullable=True, index=True)
    subject = Column(String(500), nullable=True)
    content = Column(Text, nullable=False)
    received_at = Column(DateTime(timezone=True), nullable=False)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    ai_response = Column(Text, nullable=True)
    sentiment = Column(String(20), nullable=True)  # positive, neutral, negative
    confidence_score = Column(Float, nullable=True)  # 0-1
    escalated = Column(String(10), default="false")
    escalation_reason = Column(String(500), nullable=True)
    resolution_category = Column(String(100), nullable=True)
    ticket_metadata = Column(JSON, default=dict)

    def __repr__(self):
        return f"<SupportTicket(id='{self.id}', channel='{self.channel}', status='{self.status}')>"

    @property
    def status(self) -> str:
        """
        Calculate current status based on timestamps and escalation.

        Returns:
            str: One of 'open', 'in_progress', 'waiting_customer', 'resolved', 'closed', 'escalated'
        """
        if self.escalated == "true":
            return "escalated"
        if self.resolved_at:
            return "resolved"
        if self.responded_at:
            return "in_progress"
        return "open"

    @property
    def is_resolved(self) -> bool:
        """Check if ticket is resolved."""
        return self.resolved_at is not None

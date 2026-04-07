"""
Data models for the Digital FTE agent.
"""

from src.models.base import Base
from src.models.customer import Customer
from src.models.support_ticket import SupportTicket
from src.models.conversation_thread import ConversationThread
from src.models.escalation import EscalationRule, DEFAULT_RULES
from src.models.sentiment_record import SentimentRecord

__all__ = [
    "Base",
    "Customer",
    "SupportTicket",
    "ConversationThread",
    "EscalationRule",
    "DEFAULT_RULES",
    "SentimentRecord",
]

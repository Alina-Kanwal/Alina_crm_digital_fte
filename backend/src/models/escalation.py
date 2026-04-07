"""
Escalation rule model for automatic human agent escalation triggers.
"""
from sqlalchemy import Column, String, Text, JSON, Index
from src.models.base import BaseModel


class EscalationRule(BaseModel):
    """
    Defined condition that triggers automatic transfer to human support.

    Rules are evaluated in priority order to determine when
    conversations should be escalated.

    Attributes:
        id: UUID primary key
        name: Human-readable name of rule
        description: Detailed description of when rule applies
        trigger_type: How rule is evaluated (keyword, sentiment, interaction_count, custom_function)
        trigger_config: Configuration specific to trigger type (JSON)
        priority: Higher numbers = higher priority for evaluation
        is_active: Whether rule is currently enabled
        created_at, updated_at: Timestamps from base
    """

    __tablename__ = "escalation_rules"

    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=False)
    trigger_type = Column(String(50), nullable=False, index=True)  # keyword, sentiment, interaction_count, time_threshold, custom_function
    trigger_config = Column(JSON, nullable=False, default=dict)  # Configuration for trigger type
    priority = Column(String, nullable=False)  # Store as string for compatibility
    is_active = Column(String(10), default="true")

    @property
    def priority_int(self) -> int:
        """Get priority as integer."""
        return int(self.priority) if self.priority else 0

    @property
    def is_enabled(self) -> bool:
        """Check if rule is currently enabled."""
        return self.is_active == "true"

    def evaluate(self, ticket: "SupportTicket") -> bool:
        """
        Evaluate if this rule should trigger for given ticket.

        Args:
            ticket: SupportTicket instance to evaluate against

        Returns:
            bool: True if rule triggers, False otherwise
        """
        if not self.is_enabled:
            return False

        config = self.trigger_config or {}

        if self.trigger_type == "keyword":
            # Check if keywords appear in content or subject
            keywords = config.get("keywords", [])
            content = (ticket.content or "") + " " + (ticket.subject or "")
            return any(keyword.lower() in content.lower() for keyword in keywords)

        elif self.trigger_type == "sentiment":
            # Check if sentiment matches threshold
            return ticket.sentiment == config.get("target_sentiment")

        elif self.trigger_type == "interaction_count":
            # Check if ticket has exceeded interaction limit
            # This would require fetching related tickets
            return False  # TODO: Implement interaction count check

        elif self.trigger_type == "custom_function":
            # Custom evaluation logic (would be implemented in service)
            return False  # TODO: Implement custom function evaluation

        return False

    def __repr__(self):
        return f"<EscalationRule(id='{self.id}', name='{self.name}', priority={self.priority}, active={self.is_active}>"

# Predefined escalation rules
DEFAULT_RULES = [
    {
        "name": "Pricing Inquiry",
        "description": "Escalate when customer asks about pricing negotiations",
        "trigger_type": "keyword",
        "trigger_config": {
            "keywords": ["price", "pricing", "discount", "negotiate", "deal"],
            "match_all": False,
        },
        "priority": "100",
        "is_active": "true",
    },
    {
        "name": "Refund Request",
        "description": "Escalate when customer requests a refund",
        "trigger_type": "keyword",
        "trigger_config": {
            "keywords": ["refund", "money back", "return", "credit"],
            "match_all": False,
        },
        "priority": "100",
        "is_active": "true",
    },
    {
        "name": "Legal Matter",
        "description": "Escalate when legal matters are mentioned",
        "trigger_type": "keyword",
        "trigger_config": {
            "keywords": ["legal", "sue", "lawyer", "attorney", "court", "lawsuit"],
            "match_all": False,
        },
        "priority": "100",
        "is_active": "true",
    },
    {
        "name": "Profanity Detection",
        "description": "Escalate when profanity or abusive language is detected",
        "trigger_type": "keyword",
        "trigger_config": {
            "keywords": ["fuck", "shit", "ass", "damn", "hell"],  # Add more as needed
            "match_all": False,
        },
        "priority": "90",
        "is_active": "true",
    },
    {
        "name": "Negative Sentiment",
        "description": "Escalate after 2 consecutive negative sentiments",
        "trigger_type": "sentiment",
        "trigger_config": {
            "target_sentiment": "negative",
            "consecutive_count": 2,
        },
        "priority": "80",
        "is_active": "true",
    },
]

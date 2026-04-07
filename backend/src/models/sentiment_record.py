"""
Sentiment record model for analyzing customer emotional state during interactions.
"""
from sqlalchemy import Column, String, Text, Float, JSON, ForeignKey, Index
from src.models.base import BaseModel


class SentimentRecord(BaseModel):
    """
    Analysis of customer emotional state during an interaction.

    Used for sentiment trends, daily reports, and identifying
    systemic issues or frustrated customers.

    Attributes:
        id: UUID primary key
        ticket_id: Foreign key to SupportTicket
        analyzed_at: When sentiment was analyzed
        sentiment: Sentiment classification (positive, neutral, negative)
        score: Sentiment score from -1 (very negative) to 1 (very positive)
        confidence: Confidence in sentiment analysis (0-1)
        text_snippet: Portion of message used for analysis
        metadata: Additional analysis details
        created_at: Timestamp from base
    """

    __tablename__ = "sentiment_records"

    ticket_id = Column(String(36), ForeignKey("support_tickets.id"), nullable=False, index=True)
    analyzed_at = Column(String, nullable=False)
    sentiment = Column(String(20), nullable=False, index=True)  # positive, neutral, negative
    score = Column(Float, nullable=True)  # -1 to 1
    confidence = Column(Float, nullable=True)  # 0 to 1
    text_snippet = Column(Text, nullable=True)
    sentiment_metadata = Column(JSON, default=dict)

    @property
    def is_positive(self) -> bool:
        """Check if sentiment is positive."""
        return self.sentiment == "positive"

    @property
    def is_negative(self) -> bool:
        """Check if sentiment is negative."""
        return self.sentiment == "negative"

    @property
    def is_neutral(self) -> bool:
        """Check if sentiment is neutral."""
        return self.sentiment == "neutral"

    @property
    def confidence_level(self) -> str:
        """
        Get confidence level categorization.

        Returns:
            str: 'high', 'medium', or 'low'
        """
        if not self.confidence:
            return "unknown"
        if self.confidence >= 0.8:
            return "high"
        elif self.confidence >= 0.5:
            return "medium"
        else:
            return "low"

    @property
    def sentiment_category(self) -> str:
        """
        Get detailed sentiment category.

        Returns:
            str: More granular sentiment classification
        """
        if not self.score:
            return "neutral"

        if self.score >= 0.7:
            return "very_positive"
        elif self.score >= 0.3:
            return "positive"
        elif self.score >= -0.3:
            return "neutral"
        elif self.score >= -0.7:
            return "negative"
        else:
            return "very_negative"

    def __repr__(self):
        return f"<SentimentRecord(id='{self.id}', sentiment='{self.sentiment}', score={self.score}, confidence={self.confidence}>"

    @staticmethod
    def aggregate_sentiments(records: list["SentimentRecord"]) -> dict:
        """
        Aggregate sentiment statistics from multiple records.

        Args:
            records: List of SentimentRecord instances

        Returns:
            dict: Aggregated statistics including distribution, averages, etc.
        """
        if not records:
            return {
                "total": 0,
                "positive": 0,
                "neutral": 0,
                "negative": 0,
                "average_score": 0,
                "average_confidence": 0,
            }

        return {
            "total": len(records),
            "positive": sum(1 for r in records if r.is_positive),
            "neutral": sum(1 for r in records if r.is_neutral),
            "negative": sum(1 for r in records if r.is_negative),
            "average_score": sum(r.score for r in records if r.score) / len(records),
            "average_confidence": sum(r.confidence for r in records if r.confidence) / len(records),
        }

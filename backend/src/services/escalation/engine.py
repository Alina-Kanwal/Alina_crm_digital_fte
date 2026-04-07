"""
Escalation rules engine for Digital FTE AI Customer Success Agent.
Detects when customer inquiries require human intervention based on predefined rules.
"""
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import re

logger = logging.getLogger(__name__)


class EscalationTrigger(Enum):
    """Enumeration of escalation trigger types."""
    PRICING_INQUIRY = "pricing_inquiry"
    REFUND_REQUEST = "refund_request"
    LEGAL_MATTER = "legal_matter"
    PROFANITY = "profanity"
    REPEATED_UNRESOLVED = "repeated_unresolved"
    NEGATIVE_SENTIMENT = "negative_sentiment"
    MANUAL_REQUEST = "manual_request"
    CONFIDENCE_LOW = "confidence_low"


class EscalationSeverity(Enum):
    """Enumeration of escalation severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationDecision:
    """Represents an escalation decision with context."""

    def __init__(
        self,
        should_escalate: bool,
        trigger: Optional[EscalationTrigger] = None,
        severity: EscalationSeverity = EscalationSeverity.LOW,
        reason: str = "",
        confidence: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.should_escalate = should_escalate
        self.trigger = trigger
        self.severity = severity
        self.reason = reason
        self.confidence = confidence
        self.metadata = metadata or {}

    def __repr__(self):
        return (
            f"<EscalationDecision(escalate={self.should_escalate}, "
            f"trigger={self.trigger}, severity={self.severity}, "
            f"reason='{self.reason}')>"
        )


class EscalationEngine:
    """
    Engine for evaluating escalation rules and making escalation decisions.

    Per Constitution Principle XII:
    "The AI agent MUST automatically escalate to human support based on predefined criteria:
    - Pricing-related inquiries
    - Refund requests
    - Legal matters
    - Profanity or abusive language
    - Unresolved issues after 3+ agent attempts"
    """

    def __init__(self):
        """Initialize escalation engine with predefined rules."""
        # Escalation rule configurations
        self.rules = {
            'pricing_keywords': [
                'pricing', 'price', 'cost', 'discount', 'deal',
                'enterprise', 'custom pricing', 'negotiate', 'quote'
            ],
            'refund_keywords': [
                'refund', 'money back', 'return', 'cancel subscription',
                'chargeback', 'billing dispute'
            ],
            'legal_keywords': [
                'legal', 'lawyer', 'attorney', 'lawsuit', 'sue',
                'compliance', 'regulation', 'audit', 'contract',
                'terms of service', 'tos', 'gdpr', 'ccpa'
            ],
            'profanity_patterns': [
                r'fuck', r'shit', r'damn',
                r'ass', r'whore', r'bitch',
                r'cunt', r'dick', r'cock',
                r'asshole', r'piss', r'shithead',
                r'bastard', r'crap', r'asshole'
            ]
        }

        # Configuration thresholds
        self.confidence_threshold = 0.70  # Below this, escalate
        self.repeated_issue_threshold = 3  # Escalate after 3 attempts
        self.consecutive_negative_threshold = 2  # Escalate after 2 negative sentiments

        logger.info("Escalation engine initialized with predefined rules")

    async def evaluate_escalation(
        self,
        message: str,
        context: Dict[str, Any],
        history: Optional[List[Dict]] = None
    ) -> EscalationDecision:
        """
        Evaluate whether a customer inquiry should be escalated.

        Args:
            message: The customer's current message
            context: Context information (channel, customer_id, etc.)
            history: Previous conversation history for this customer

        Returns:
            EscalationDecision with escalation recommendation and reasoning
        """
        try:
            # Check each escalation rule in priority order
            # CRITICAL triggers first (safety/liability)
            critical_decision = await self._check_critical_triggers(message, context)
            if critical_decision.should_escalate:
                return critical_decision

            # Check content-based triggers
            content_decision = await self._check_content_triggers(message, context)
            if content_decision.should_escalate:
                return content_decision

            # Check conversation-based triggers
            conversation_decision = await self._check_conversation_triggers(
                message,
                context,
                history
            )
            if conversation_decision.should_escalate:
                return conversation_decision

            # Check sentiment-based triggers
            sentiment_decision = await self._check_sentiment_triggers(
                message,
                context,
                history
            )
            if sentiment_decision.should_escalate:
                return sentiment_decision

            # No escalation needed
            return EscalationDecision(
                should_escalate=False,
                reason="All escalation rules passed - inquiry can be handled by AI"
            )

        except Exception as e:
            logger.error(f"Error evaluating escalation: {e}")
            # On error, be conservative - escalate to avoid issues
            return EscalationDecision(
                should_escalate=True,
                trigger=EscalationTrigger.MANUAL_REQUEST,
                severity=EscalationSeverity.HIGH,
                reason=f"Escalation evaluation error: {str(e)}",
                metadata={'error': str(e)}
            )

    async def _check_critical_triggers(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> EscalationDecision:
        """
        Check for critical escalation triggers (safety/legal/liability).

        Args:
            message: The customer's message
            context: Context information

        Returns:
            EscalationDecision if critical trigger detected
        """
        message_lower = message.lower()

        # Check for profanity/abusive language (SAFETY)
        for pattern in self.rules['profanity_patterns']:
            if re.search(pattern, message_lower, re.IGNORECASE):
                logger.warning(f"Profanity detected in message: {pattern}")
                return EscalationDecision(
                    should_escalate=True,
                    trigger=EscalationTrigger.PROFANITY,
                    severity=EscalationSeverity.CRITICAL,
                    reason="Profanity or abusive language detected",
                    confidence=0.95,
                    metadata={'pattern': pattern}
                )

        # Check for legal matters (LIABILITY)
        for keyword in self.rules['legal_keywords']:
            if keyword in message_lower:
                logger.warning(f"Legal keyword detected: {keyword}")
                return EscalationDecision(
                    should_escalate=True,
                    trigger=EscalationTrigger.LEGAL_MATTER,
                    severity=EscalationSeverity.CRITICAL,
                    reason=f"Legal/compliance matter detected: {keyword}",
                    confidence=0.90,
                    metadata={'keyword': keyword}
                )

        # No critical triggers
        return EscalationDecision(should_escalate=False)

    async def _check_content_triggers(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> EscalationDecision:
        """
        Check for content-based escalation triggers (pricing/refunds).

        Args:
            message: The customer's message
            context: Context information

        Returns:
            EscalationDecision if content trigger detected
        """
        message_lower = message.lower()

        # Check for pricing inquiries (requires sales negotiation)
        for keyword in self.rules['pricing_keywords']:
            if keyword in message_lower:
                logger.info(f"Pricing keyword detected: {keyword}")
                return EscalationDecision(
                    should_escalate=True,
                    trigger=EscalationTrigger.PRICING_INQUIRY,
                    severity=EscalationSeverity.HIGH,
                    reason=f"Pricing/negotiation inquiry detected: {keyword}",
                    confidence=0.85,
                    metadata={'keyword': keyword}
                )

        # Check for refund requests (financial transactions)
        for keyword in self.rules['refund_keywords']:
            if keyword in message_lower:
                logger.info(f"Refund keyword detected: {keyword}")
                return EscalationDecision(
                    should_escalate=True,
                    trigger=EscalationTrigger.REFUND_REQUEST,
                    severity=EscalationSeverity.HIGH,
                    reason=f"Refund/financial request detected: {keyword}",
                    confidence=0.90,
                    metadata={'keyword': keyword}
                )

        # No content triggers
        return EscalationDecision(should_escalate=False)

    async def _check_conversation_triggers(
        self,
        message: str,
        context: Dict[str, Any],
        history: Optional[List[Dict]]
    ) -> EscalationDecision:
        """
        Check for conversation-based escalation triggers (repeated issues).

        Args:
            message: The customer's message
            context: Context information
            history: Conversation history

        Returns:
            EscalationDecision if conversation trigger detected
        """
        if not history or len(history) == 0:
            # No history, cannot check conversation-based rules
            return EscalationDecision(should_escalate=False)

        # Check for repeated unresolved issues
        recent_interactions = [
            msg for msg in history[-10:]  # Last 10 messages
            if msg.get('direction') == 'incoming'
        ]

        # Count interactions on same topic
        # Simple approach: count how many times customer contacted about same issue
        # For production, would use topic extraction/semantic similarity
        unresolved_count = len(recent_interactions)

        if unresolved_count >= self.repeated_issue_threshold:
            logger.warning(
                f"Repeated unresolved issue detected: "
                f"{unresolved_count} interactions"
            )
            return EscalationDecision(
                should_escalate=True,
                trigger=EscalationTrigger.REPEATED_UNRESOLVED,
                severity=EscalationSeverity.MEDIUM,
                reason=(
                    f"Repeated unresolved issue: "
                    f"{unresolved_count} interactions without resolution"
                ),
                confidence=0.80,
                metadata={
                    'interaction_count': unresolved_count,
                    'threshold': self.repeated_issue_threshold
                }
            )

        # No conversation triggers
        return EscalationDecision(should_escalate=False)

    async def _check_sentiment_triggers(
        self,
        message: str,
        context: Dict[str, Any],
        history: Optional[List[Dict]]
    ) -> EscalationDecision:
        """
        Check for sentiment-based escalation triggers (negative sentiment).

        Args:
            message: The customer's message
            context: Context information
            history: Conversation history

        Returns:
            EscalationDecision if sentiment trigger detected
        """
        if not history or len(history) == 0:
            # No history, cannot check consecutive negative sentiment
            return EscalationDecision(should_escalate=False)

        # Check for consecutive negative sentiments
        recent_messages = history[-5:]  # Last 5 messages

        consecutive_negative = 0
        for msg in reversed(recent_messages):  # Check from most recent
            if msg.get('sentiment') == 'negative':
                consecutive_negative += 1
            else:
                break  # Break on non-negative

        if consecutive_negative >= self.consecutive_negative_threshold:
            logger.warning(
                f"Consecutive negative sentiment detected: "
                f"{consecutive_negative} messages"
            )
            return EscalationDecision(
                should_escalate=True,
                trigger=EscalationTrigger.NEGATIVE_SENTIMENT,
                severity=EscalationSeverity.MEDIUM,
                reason=(
                    f"Consecutive negative sentiment: "
                    f"{consecutive_negative} messages indicate customer frustration"
                ),
                confidence=0.75,
                metadata={
                    'consecutive_count': consecutive_negative,
                    'threshold': self.consecutive_negative_threshold
                }
            )

        # No sentiment triggers
        return EscalationDecision(should_escalate=False)

    async def check_confidence_threshold(
        self,
        confidence: float,
        context: Dict[str, Any]
    ) -> EscalationDecision:
        """
        Check if AI confidence is below threshold (uncertain response).

        Args:
            confidence: AI agent confidence score (0.0-1.0)
            context: Context information

        Returns:
            EscalationDecision if confidence is too low
        """
        if confidence < self.confidence_threshold:
            logger.warning(
                f"Low confidence detected: {confidence:.2f} < {self.confidence_threshold}"
            )
            return EscalationDecision(
                should_escalate=True,
                trigger=EscalationTrigger.CONFIDENCE_LOW,
                severity=EscalationSeverity.MEDIUM,
                reason=(
                    f"AI confidence too low: {confidence:.2f} "
                    f"< threshold {self.confidence_threshold}"
                ),
                confidence=confidence,
                metadata={
                    'confidence_score': confidence,
                    'threshold': self.confidence_threshold
                }
            )

        return EscalationDecision(should_escalate=False)

    def get_escalation_priority(
        self,
        trigger: EscalationTrigger,
        severity: EscalationSeverity
    ) -> int:
        """
        Get priority level for escalation (1=highest, 5=lowest).

        Args:
            trigger: The escalation trigger
            severity: The escalation severity

        Returns:
            Priority level (1-5)
        """
        # Critical triggers get highest priority
        if trigger in [EscalationTrigger.PROFANITY, EscalationTrigger.LEGAL_MATTER]:
            return 1

        # High severity
        if severity == EscalationSeverity.CRITICAL:
            return 1
        elif severity == EscalationSeverity.HIGH:
            return 2
        elif severity == EscalationSeverity.MEDIUM:
            return 3
        elif severity == EscalationSeverity.LOW:
            return 4
        else:
            return 5

    async def batch_evaluate_escalations(
        self,
        inquiries: List[Dict[str, Any]]
    ) -> List[EscalationDecision]:
        """
        Evaluate escalation for multiple inquiries (batch processing).

        Args:
            inquiries: List of inquiry dictionaries with message and context

        Returns:
            List of EscalationDecision objects
        """
        decisions = []

        for inquiry in inquiries:
            decision = await self.evaluate_escalation(
                message=inquiry.get('message', ''),
                context=inquiry.get('context', {}),
                history=inquiry.get('history')
            )
            decisions.append(decision)

        logger.info(f"Evaluated {len(decisions)} inquiries for escalation")
        return decisions

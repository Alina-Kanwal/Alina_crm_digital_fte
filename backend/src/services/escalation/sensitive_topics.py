"""
Sensitive topics detection service for Digital FTE AI Customer Success Agent.
Detects pricing inquiries, refund requests, and legal matters.
"""
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
import re

logger = logging.getLogger(__name__)


class SensitiveTopic(Enum):
    """Enumeration of sensitive topic types."""
    PRICING = "pricing"
    REFUND = "refund"
    LEGAL = "legal"
    BILLING = "billing"


class TopicDetection:
    """
    Service for detecting sensitive topics requiring human intervention.

    Per Constitution Principle XII:
    - Pricing-related inquiries
    - Refund requests
    - Legal matters
    These are mandatory escalation triggers.
    """

    def __init__(self):
        """Initialize topic detector with keyword lists."""
        # Pricing-related keywords
        self.pricing_keywords = [
            'pricing', 'price', 'cost', 'discount', 'deal',
            'enterprise', 'custom pricing', 'negotiate', 'quote',
            'quote', 'estimation', 'estimate', 'budget',
            'how much', 'cheaper', 'expensive', 'affordable',
            'plan cost', 'subscription cost', 'license cost',
            'volume discount', 'bulk pricing', 'tiered pricing'
        ]

        # Refund-related keywords
        self.refund_keywords = [
            'refund', 'money back', 'return', 'cancel subscription',
            'chargeback', 'billing dispute', 'wrong charge',
            'overcharged', 'unauthorized charge', 'credit',
            'cancel plan', 'downgrade', 'prorate'
        ]

        # Legal/compliance keywords
        self.legal_keywords = [
            'legal', 'lawyer', 'attorney', 'lawsuit', 'sue',
            'compliance', 'regulation', 'audit', 'contract',
            'terms of service', 'tos', 'gdpr', 'ccpa', 'hipaa',
            'data privacy', 'privacy policy', 'liability', 'indemnification',
            'court', 'litigation', 'breach', 'violation',
            'regulatory', 'compliance', 'audit', 'subpoena'
        ]

        # Billing-related keywords (can be handled by AI, but track)
        self.billing_keywords = [
            'invoice', 'payment', 'billing', 'charge',
            'credit card', 'payment method', 'payment failed',
            'overdue', 'past due', 'bill', 'receipt'
        ]

        # Compile regex patterns for better matching
        self._compile_patterns()

        logger.info(
            f"Sensitive topic detector initialized: "
            f"{len(self.pricing_keywords)} pricing, "
            f"{len(self.refund_keywords)} refund, "
            f"{len(self.legal_keywords)} legal, "
            f"{len(self.billing_keywords)} billing keywords"
        )

    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self.compiled_pricing = [
            re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
            for kw in self.pricing_keywords
        ]

        self.compiled_refund = [
            re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
            for kw in self.refund_keywords
        ]

        self.compiled_legal = [
            re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
            for kw in self.legal_keywords
        ]

        self.compiled_billing = [
            re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
            for kw in self.billing_keywords
        ]

    async def detect_sensitive_topics(
        self,
        message: str
    ) -> Dict[str, any]:
        """
        Detect sensitive topics in a message.

        Args:
            message: The customer's message content

        Returns:
            Dictionary containing:
            - has_sensitive_topic: Boolean indicating if sensitive topic detected
            - topics: List of detected sensitive topics
            - severity: 'high' for legal/refund, 'medium' for pricing
            - confidence: Detection confidence (0.0-1.0)
            - matches: List of matched keywords
        """
        if not message or len(message.strip()) == 0:
            return {
                'has_sensitive_topic': False,
                'topics': [],
                'severity': 'none',
                'confidence': 0.0,
                'matches': []
            }

        message_lower = message.lower()
        detected_topics = []
        matches = []
        severity = 'none'
        confidence = 0.0

        # Check for legal topics (HIGHEST PRIORITY - liability)
        for i, pattern in enumerate(self.compiled_legal):
            if pattern.search(message_lower):
                matches.append({
                    'topic': SensitiveTopic.LEGAL,
                    'keyword': self.legal_keywords[i],
                    'pattern': self.legal_keywords[i]
                })
                if SensitiveTopic.LEGAL not in detected_topics:
                    detected_topics.append(SensitiveTopic.LEGAL)

        # Check for refund topics (HIGH - financial)
        for i, pattern in enumerate(self.compiled_refund):
            if pattern.search(message_lower):
                matches.append({
                    'topic': SensitiveTopic.REFUND,
                    'keyword': self.refund_keywords[i],
                    'pattern': self.refund_keywords[i]
                })
                if SensitiveTopic.REFUND not in detected_topics:
                    detected_topics.append(SensitiveTopic.REFUND)

        # Check for pricing topics (MEDIUM - requires sales)
        for i, pattern in enumerate(self.compiled_pricing):
            if pattern.search(message_lower):
                matches.append({
                    'topic': SensitiveTopic.PRICING,
                    'keyword': self.pricing_keywords[i],
                    'pattern': self.pricing_keywords[i]
                })
                if SensitiveTopic.PRICING not in detected_topics:
                    detected_topics.append(SensitiveTopic.PRICING)

        # Check for billing topics (LOW - can be handled)
        for i, pattern in enumerate(self.compiled_billing):
            if pattern.search(message_lower):
                matches.append({
                    'topic': SensitiveTopic.BILLING,
                    'keyword': self.billing_keywords[i],
                    'pattern': self.billing_keywords[i]
                })
                if SensitiveTopic.BILLING not in detected_topics:
                    detected_topics.append(SensitiveTopic.BILLING)

        # Determine severity and confidence
        has_sensitive_topic = len(detected_topics) > 0

        if has_sensitive_topic:
            if SensitiveTopic.LEGAL in detected_topics:
                severity = 'high'
                confidence = 0.95  # High confidence for legal
            elif SensitiveTopic.REFUND in detected_topics:
                severity = 'high'
                confidence = 0.90  # High confidence for refund
            elif SensitiveTopic.PRICING in detected_topics:
                severity = 'medium'
                confidence = 0.85  # Medium-high confidence for pricing
            elif SensitiveTopic.BILLING in detected_topics:
                severity = 'low'
                confidence = 0.75  # Lower confidence for billing

        if has_sensitive_topic:
            logger.info(
                f"Sensitive topic detected: topics={detected_topics}, "
                f"severity={severity}, confidence={confidence:.2f}"
            )

        return {
            'has_sensitive_topic': has_sensitive_topic,
            'topics': detected_topics,
            'severity': severity,
            'confidence': confidence,
            'matches': matches
        }

    async def detect_sensitive_topics_batch(
        self,
        messages: List[str]
    ) -> List[Dict[str, any]]:
        """
        Detect sensitive topics in multiple messages (batch processing).

        Args:
            messages: List of message strings

        Returns:
            List of sensitive topic detection results
        """
        results = []

        for message in messages:
            result = await self.detect_sensitive_topics(message)
            results.append(result)

        # Log summary
        sensitive_count = sum(1 for r in results if r['has_sensitive_topic'])
        if sensitive_count > 0:
            logger.info(
                f"Sensitive topic batch detection: {sensitive_count}/{len(messages)} "
                f"messages contain sensitive topics"
            )

        return results

    def get_escalation_recommendation(
        self,
        detection_result: Dict[str, any]
    ) -> Tuple[bool, str]:
        """
        Get escalation recommendation based on sensitive topic detection.

        Args:
            detection_result: Sensitive topic detection result

        Returns:
            Tuple of (should_escalate: bool, reason: str)
        """
        has_sensitive_topic = detection_result['has_sensitive_topic']
        topics = detection_result['topics']
        severity = detection_result['severity']

        if not has_sensitive_topic:
            return (False, "No sensitive topics detected")

        # Legal and refund topics MUST escalate
        if SensitiveTopic.LEGAL in topics:
            return (True, "Legal/compliance matter detected - requires human expertise")
        elif SensitiveTopic.REFUND in topics:
            return (True, "Refund/financial request detected - requires human approval")

        # Pricing topics SHOULD escalate (sales negotiation)
        if SensitiveTopic.PRICING in topics:
            return (True, "Pricing/negotiation inquiry detected - requires sales team")

        # Billing topics CAN be handled by AI but flag for review
        if SensitiveTopic.BILLING in topics:
            return (False, "Billing topic detected - can be handled by AI with human review")

        return (False, "Unknown sensitive topic type")

    def get_topic_priority(
        self,
        topic: SensitiveTopic
    ) -> int:
        """
        Get priority level for sensitive topic (1=highest, 4=lowest).

        Args:
            topic: The sensitive topic

        Returns:
            Priority level (1-4)
        """
        if topic == SensitiveTopic.LEGAL:
            return 1  # Highest priority (liability)
        elif topic == SensitiveTopic.REFUND:
            return 2  # High priority (financial)
        elif topic == SensitiveTopic.PRICING:
            return 3  # Medium priority (sales)
        elif topic == SensitiveTopic.BILLING:
            return 4  # Lowest priority (can be automated)
        else:
            return 5

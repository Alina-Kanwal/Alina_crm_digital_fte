"""
Profanity detection service for Digital FTE AI Customer Success Agent.
Detects abusive or inappropriate language in customer messages.
"""
import logging
from typing import Dict, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)


class ProfanityDetector:
    """
    Service for detecting profanity and abusive language.

    Per Constitution Principle XII:
    "Profanity or abusive language" is a mandatory escalation trigger.
    """

    def __init__(self):
        """Initialize profanity detector with word lists."""
        # Strong profanity patterns
        self.strong_profanity = [
            r'\bfuck\b', r'\bshit\b', r'\bdamn\b',
            r'\bass\b', r'\bwhore\b', r'\bbitch\b',
            r'\bcunt\b', r'\bdick\b', r'\bcock\b',
            r'\bpussy\b', r'\btits?\b', r'\bastard\b',
            r'\bprick\b', r'\bslut\b'
        ]

        # Mild profanity patterns (still escalate)
        self.mild_profanity = [
            r'\bhell\b', r'\bcrap\b', r'\bsucks\b',
            r'\bstupid\b', r'\bidiot\b', r'\bdumb\b'
        ]

        # Abusive language patterns
        self.abusive_patterns = [
            r'\bhate\b', r'\bkilled\b', r'\bmurder\b',
            r'\bdie\b', r'\bkill yourself\b', r'\bworthless\b'
        ]

        # Compounded/detected attempts (e.g., f*ck, s#it)
        self.obfuscation_patterns = [
            r'f\*+', r's\#+', r'b\*\*+', r'd\^+',
            r'a\$+', r's\$+', r'\$\$\$+'
        ]

        # Compile regex patterns
        self._compile_patterns()

        logger.info(
            f"Profanity detector initialized with "
            f"{len(self.strong_profanity)} strong, "
            f"{len(self.mild_profanity)} mild, "
            f"{len(self.abusive_patterns)} abusive patterns"
        )

    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self.compiled_strong = [re.compile(p, re.IGNORECASE) for p in self.strong_profanity]
        self.compiled_mild = [re.compile(p, re.IGNORECASE) for p in self.mild_profanity]
        self.compiled_abusive = [re.compile(p, re.IGNORECASE) for p in self.abusive_patterns]
        self.compiled_obfuscation = [re.compile(p, re.IGNORECASE) for p in self.obfuscation_patterns]

    async def detect_profanity(
        self,
        message: str
    ) -> Dict[str, any]:
        """
        Detect profanity in a message.

        Args:
            message: The customer's message content

        Returns:
            Dictionary containing:
            - has_profanity: Boolean indicating if profanity detected
            - severity: 'strong', 'mild', 'abusive', or 'none'
            - matches: List of matched patterns
            - confidence: Detection confidence (0.0-1.0)
        """
        if not message or len(message.strip()) == 0:
            return {
                'has_profanity': False,
                'severity': 'none',
                'matches': [],
                'confidence': 0.0
            }

        message_lower = message.lower()
        matches = []
        detected_severity = 'none'

        # Check for strong profanity (highest priority)
        for i, pattern in enumerate(self.compiled_strong):
            if pattern.search(message_lower):
                matches.append({
                    'pattern': self.strong_profanity[i],
                    'type': 'strong'
                })
                detected_severity = 'strong'

        # Check for abusive language
        if detected_severity == 'none':
            for i, pattern in enumerate(self.compiled_abusive):
                if pattern.search(message_lower):
                    matches.append({
                        'pattern': self.abusive_patterns[i],
                        'type': 'abusive'
                    })
                    detected_severity = 'abusive'

        # Check for mild profanity
        if detected_severity == 'none':
            for i, pattern in enumerate(self.compiled_mild):
                if pattern.search(message_lower):
                    matches.append({
                        'pattern': self.mild_profanity[i],
                        'type': 'mild'
                    })
                    detected_severity = 'mild'

        # Check for obfuscation patterns (trying to bypass filters)
        if detected_severity == 'none':
            for i, pattern in enumerate(self.compiled_obfuscation):
                if pattern.search(message_lower):
                    matches.append({
                        'pattern': self.obfuscation_patterns[i],
                        'type': 'obfuscation'
                    })
                    detected_severity = 'strong'  # Treat as strong since they're trying to bypass

        # Calculate confidence
        if len(matches) == 0:
            confidence = 0.0
        elif detected_severity == 'strong' or detected_severity == 'abusive':
            confidence = 0.95  # High confidence for strong/abusive
        elif detected_severity == 'mild':
            confidence = 0.80  # Medium confidence for mild
        else:
            confidence = 0.70  # Lower confidence for obfuscation

        has_profanity = len(matches) > 0

        if has_profanity:
            logger.warning(
                f"Profanity detected: severity={detected_severity}, "
                f"matches={len(matches)}, confidence={confidence:.2f}"
            )

        return {
            'has_profanity': has_profanity,
            'severity': detected_severity,
            'matches': matches,
            'confidence': confidence
        }

    async def detect_profanity_batch(
        self,
        messages: List[str]
    ) -> List[Dict[str, any]]:
        """
        Detect profanity in multiple messages (batch processing).

        Args:
            messages: List of message strings

        Returns:
            List of profanity detection results
        """
        results = []

        for message in messages:
            result = await self.detect_profanity(message)
            results.append(result)

        # Log summary
        profanity_count = sum(1 for r in results if r['has_profanity'])
        if profanity_count > 0:
            logger.warning(
                f"Profanity batch detection: {profanity_count}/{len(messages)} "
                f"messages contain profanity"
            )

        return results

    def get_escalation_recommendation(
        self,
        profanity_result: Dict[str, any]
    ) -> Tuple[bool, str]:
        """
        Get escalation recommendation based on profanity detection.

        Args:
            profanity_result: Profanity detection result

        Returns:
            Tuple of (should_escalate: bool, reason: str)
        """
        has_profanity = profanity_result['has_profanity']
        severity = profanity_result['severity']

        if severity == 'strong' or severity == 'abusive':
            return (True, f"Strong profanity or abusive language detected ({severity})")
        elif severity == 'mild':
            return (True, f"Mild profanity detected")
        elif has_profanity:
            return (True, f"Profanity detected (severity: {severity})")
        else:
            return (False, "No profanity detected")

    def sanitize_message(
        self,
        message: str,
        replacement_char: str = '*'
    ) -> str:
        """
        Sanitize a message by replacing profanity with replacement character.

        Args:
            message: The message to sanitize
            replacement_char: Character to replace profanity with

        Returns:
            Sanitized message
        """
        if not message:
            return message

        sanitized = message

        # Replace strong profanity
        for pattern in self.strong_profanity:
            sanitized = re.sub(pattern, replacement_char * len(pattern), sanitized, flags=re.IGNORECASE)

        # Replace abusive language
        for pattern in self.abusive_patterns:
            sanitized = re.sub(pattern, replacement_char * len(pattern), sanitized, flags=re.IGNORECASE)

        # Replace mild profanity
        for pattern in self.mild_profanity:
            sanitized = re.sub(pattern, replacement_char * len(pattern), sanitized, flags=re.IGNORECASE)

        return sanitized

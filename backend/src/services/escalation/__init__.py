"""
Escalation logic services module for Digital FTE AI Customer Success Agent.

Provides comprehensive escalation capabilities per Constitution Principle XII:
- Escalation rules engine
- Profanity detection
- Sensitive topics detection (pricing/refund/legal)
- Repeated unresolved query tracking
- Human agent notification system
- Escalation tracking and metrics
- Escalation rate monitoring and alerting

Per Constitution Principle XII:
"The AI agent MUST automatically escalate to human support based on predefined criteria:
- Pricing-related inquiries
- Refund requests
- Legal matters
- Profanity or abusive language
- Unresolved issues after 3+ agent attempts"
"""

from .engine import EscalationEngine, EscalationTrigger, EscalationSeverity, EscalationDecision
from .profanity import ProfanityDetector
from .sensitive_topics import TopicDetection, SensitiveTopic
from .unresolved_tracker import UnresolvedTracker
from .notifier import HumanAgentNotifier
from .tracker import EscalationTracker
from .monitor import EscalationMonitor

__all__ = [
    'EscalationEngine',
    'EscalationTrigger',
    'EscalationSeverity',
    'EscalationDecision',
    'ProfanityDetector',
    'TopicDetection',
    'SensitiveTopic',
    'UnresolvedTracker',
    'HumanAgentNotifier',
    'EscalationTracker',
    'EscalationMonitor',
]

__version__ = '1.0.0'

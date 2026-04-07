"""
Chaos testing module for Digital FTE AI Customer Success Agent.

Provides comprehensive chaos testing capabilities per Constitution Principle XV:
"System MUST pass 24-hour chaos testing with:
- 100+ web form submissions
- 50+ Gmail messages
- 50+ WhatsApp messages
- Random pod kills every 30-60 minutes
- Network latency injection
- Resource exhaustion tests
- Zero data loss
- Uptime exceeding 99.9%"
"""

from .chaos_framework import ChaosTestingFramework, ChaosAction, ChaosSeverity, ChaosTestResult
from .scenarios import ChaosScenarios
from .monitor import ChaosTestMonitor

__all__ = [
    'ChaosTestingFramework',
    'ChaosAction',
    'ChaosSeverity',
    'ChaosTestResult',
    'ChaosScenarios',
    'ChaosTestMonitor',
]

__version__ = '1.0.0'

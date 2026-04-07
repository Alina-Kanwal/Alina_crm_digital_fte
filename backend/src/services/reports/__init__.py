"""
Reports services module for Digital FTE AI Customer Success Agent.

Provides comprehensive reporting capabilities per Constitution Principle XV:
- Daily report generation
- Executive summary generation
- Report delivery mechanisms (email/dashboard/webhook/Slack)

Per Constitution Principle XV:
"System MUST generate daily sentiment reports ... delivered to support managers by 9:00 AM"
"""

from .daily import DailyReportGenerator
from .delivery import ReportDeliveryService
from .executive_summary import ExecutiveSummaryGenerator
from .trends import ReportTrendAnalyzer

__all__ = [
    'DailyReportGenerator',
    'ReportDeliveryService',
    'ExecutiveSummaryGenerator',
    'ReportTrendAnalyzer',
]

__version__ = '1.0.0'

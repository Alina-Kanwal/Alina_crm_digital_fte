"""
Sentiment analysis services module for Digital FTE AI Customer Success Agent.

Provides comprehensive sentiment analysis and reporting capabilities per Constitution Principle XV:
- Sentiment analysis using OpenAI GPT-4o
- Sentiment storage and retrieval in PostgreSQL
- Daily report generation (sentiment, tickets, complaints, trends)
- Executive summary generation
- Report delivery (email/dashboard/webhook)
- Scheduled task execution (Celery)

Per Constitution Principle XV:
"System MUST analyze customer sentiment in every interaction and store results in PostgreSQL.
System MUST generate daily sentiment reports ... delivered to support managers by 9:00 AM"
"""

from .analyzer import SentimentAnalyzer, Sentiment, SentimentAnalysisResult
from .storage import SentimentStorage
from .trends import SentimentTrendAnalyzer

__all__ = [
    'SentimentAnalyzer',
    'Sentiment',
    'SentimentAnalysisResult',
    'SentimentStorage',
    'SentimentTrendAnalyzer',
]

__version__ = '1.0.0'

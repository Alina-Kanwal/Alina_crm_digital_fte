"""
Custom tool: Sentiment analysis for Digital FTE AI Customer Success Agent.
Lexicon-based implementation for zero-latency production use.
"""
import logging
import re
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Analyze the sentiment of customer text using rule-based logic.
    Provides high speed and zero cost.
    """
    try:
        if not text or not isinstance(text, str):
            return {"sentiment": "neutral", "confidence": 0.0}

        cleaned_text = text.lower().strip()
        words = re.findall(r'\b\w+\b', cleaned_text)
        
        positive_words = {'good', 'great', 'excellent', 'amazing', 'thanks', 'thank', 'satisfied', 'helpful'}
        negative_words = {'bad', 'terrible', 'frustrated', 'problem', 'issue', 'broken', 'error'}
        strong_negative_words = {'lawsuit', 'legal', 'sue', 'refund', 'unacceptable'}

        pos_count = sum(1 for w in words if w in positive_words)
        neg_count = sum(1 for w in words if w in negative_words)
        strong_neg_count = sum(1 for w in words if w in strong_negative_words)

        if strong_neg_count > 0:
            return {"sentiment": "negative", "confidence": 0.9, "strong_negative": True}
        if pos_count > neg_count:
            return {"sentiment": "positive", "confidence": 0.7}
        if neg_count > pos_count:
            return {"sentiment": "negative", "confidence": 0.7}
        
        return {"sentiment": "neutral", "confidence": 0.5}

    except Exception as e:
        logger.error(f"Sentiment error: {e}")
        return {"sentiment": "neutral", "confidence": 0.0}
"""
Custom function tool: Sentiment analysis for Digital FTE AI Customer Success Agent.
Analyzes customer sentiment in messages to inform response tone and escalation decisions.
"""

import logging
import re
from typing import Dict, Any
from agents import function_tool

logger = logging.getLogger(__name__)


@function_tool
async def analyze_sentiment(text: str) -> Dict[str, Any]:
    """
    Analyze the sentiment of customer text.

    This function tool enables the AI agent to understand the emotional tone
    of customer messages, which helps in:
    - Selecting appropriate response tone
    - Detecting frustration that may require escalation
    - Tracking customer satisfaction over time
    - Generating sentiment analytics for reporting

    Args:
        text: The customer message text to analyze

    Returns:
        Sentiment analysis results including sentiment label, confidence score,
        and emotional indicators
    """
    try:
        logger.debug(f"Analyzing sentiment for text: '{text[:100]}...'")

        if not text or not isinstance(text, str):
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "reasoning": "Empty or invalid text provided",
                "emotional_indicators": [],
                "word_count": 0
            }

        # Clean and prepare text
        cleaned_text = text.lower().strip()
        words = re.findall(r'\b\w+\b', cleaned_text)
        word_count = len(words)

        if word_count == 0:
            return {
                "sentiment": "neutral",
                "confidence": 0.0,
                "reasoning": "No words found in text",
                "emotional_indicators": [],
                "word_count": 0
            }

        # Define sentiment lexicons
        positive_words = {
            'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
            'love', 'like', 'happy', 'pleased', 'satisfied', 'awesome', 'perfect',
            'best', 'better', 'helpful', 'thanks', 'thank', 'appreciate', 'glad',
            'joy', 'delighted', 'impressed', 'outstanding', 'superb', 'brilliant'
        }

        negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'angry',
            'frustrated', 'disappointed', 'upset', 'annoyed', 'irritated',
            'displeased', 'dissatisfied', 'poor', 'worst', 'worse', 'useless',
            'broken', 'failed', 'failure', 'problem', 'issue', 'error', 'bug'
        }

        # Strong negative indicators (may trigger escalation)
        strong_negative_words = {
            'furious', 'livid', 'outraged', 'disgusted', 'appalled',
            'unacceptable', 'ridiculous', 'absurd', 'nonsense', 'waste',
            'lawsuit', 'legal', 'attorney', 'sue', 'refund', 'money back'
        }

        # Count matches
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        strong_negative_count = sum(1 for word in words if word in strong_negative_words)

        # Detect emotional indicators
        emotional_indicators = []

        # Check for urgency
        urgency_indicators = ['urgent', 'asap', 'emergency', 'critical', 'immediately', 'right now']
        if any(indicator in cleaned_text for indicator in urgency_indicators):
            emotional_indicators.append("urgency")

        # Check for frustration
        frustration_indicators = ['frustrated', 'fed up', 'tired of', 'sick of', 'had enough', 'enough is enough']
        if any(indicator in cleaned_text for indicator in frustration_indicators):
            emotional_indicators.append("frustration")

        # Check for confusion
        confusion_indicators = ['confused', 'unclear', 'dont understand', 'not sure', 'unclear', 'unclear']
        if any(indicator in cleaned_text for indicator in confusion_indicators):
            emotional_indicators.append("confusion")

        # Check for positivity indicators
        if any(word in cleaned_text for word in ['please', 'thank you', 'thanks', 'appreciate']):
            emotional_indicators.append("politeness")

        # Determine sentiment
        if strong_negative_count > 0:
            # Strong negative indicators override normal scoring
            sentiment = "negative"
            confidence = min(0.95, 0.7 + strong_negative_count * 0.05)
        elif positive_count > negative_count:
            sentiment = "positive"
            # Confidence based on strength of positive indicators
            base_confidence = 0.6
            word_ratio = positive_count / max(word_count, 1)
            confidence = min(0.95, base_confidence + word_ratio * 0.4)
        elif negative_count > positive_count:
            sentiment = "negative"
            # Confidence based on strength of negative indicators
            base_confidence = 0.6
            word_ratio = negative_count / max(word_count, 1)
            confidence = min(0.95, base_confidence + word_ratio * 0.4)
        else:
            # Equal or no sentiment words
            sentiment = "neutral"
            confidence = 0.5  # Base confidence for neutral

        # Adjust confidence based on text length and clarity
        if word_count < 3:
            confidence *= 0.7  # Less confidence for very short text
        elif word_count > 50:
            confidence = min(0.95, confidence + 0.1)  # More confidence for longer, clearer text

        # Boost confidence if we detected clear emotional indicators
        if emotional_indicators:
            confidence = min(0.95, confidence + len(emotional_indicators) * 0.05)

        result = {
            "sentiment": sentiment,
            "confidence": round(confidence, 3),
            "reasoning": f"Found {positive_count} positive, {negative_count} negative, {strong_negative_count} strong negative indicators",
            "emotional_indicators": emotional_indicators,
            "word_count": word_count,
            "positive_score": positive_count,
            "negative_score": negative_count,
            "strong_negative_score": strong_negative_count
        }

        logger.debug(f"Sentiment analysis result: {result}")
        return result

    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        return {
            "sentiment": "unknown",
            "confidence": 0.0,
            "reasoning": f"Error during analysis: {str(e)}",
            "emotional_indicators": [],
            "word_count": 0 if not text else len(text.split()),
            "error": str(e)
        }


# Factory function for dependency injection
def create_sentiment_analysis_tool():
    """Factory function for sentiment analysis tool (returns the decorated function)."""
    return analyze_sentiment
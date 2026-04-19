"""
Sentiment analysis service for Digital FTE AI Customer Success Agent.
Analyzes customer sentiment in every interaction using Groq (LPU Inference).
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class Sentiment(Enum):
    """Enumeration of sentiment categories."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class SentimentAnalysisResult:
    """Represents sentiment analysis result with metadata."""

    def __init__(
        self,
        sentiment: Sentiment,
        confidence: float,
        reasoning: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        emotion: Optional[str] = None
    ):
        self.sentiment = sentiment
        self.confidence = confidence
        self.reasoning = reasoning
        self.keywords = keywords or []
        self.emotion = emotion

    def __repr__(self):
        return (
            f"<SentimentAnalysisResult(sentiment={self.sentiment.value}, "
            f"confidence={self.confidence:.2f})>"
        )


class SentimentAnalyzer:
    """
    Service for analyzing customer sentiment using Groq.

    Per Constitution Principle XV:
    "System MUST analyze customer sentiment in every interaction"
    """

    def __init__(self, groq_client=None):
        """
        Initialize sentiment analyzer.

        Args:
            groq_client: Optional Groq client (will be initialized if not provided)
        """
        self.groq_client = groq_client
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        logger.info(f"Sentiment analyzer initialized with model: {self.model}")

    async def initialize(self):
        """Initialize sentiment analyzer dependencies."""
        if not self.groq_client:
            # Import Groq client
            try:
                from groq import AsyncGroq
                import os
                api_key = os.getenv("GROQ_API_KEY")
                self.groq_client = AsyncGroq(api_key=api_key)
                logger.info("Groq client initialized for sentiment analysis")
            except ImportError:
                logger.warning("Groq not available, using mock sentiment analysis")

    async def analyze_sentiment(
        self,
        message: str,
        channel: Optional[str] = None,
        customer_id: Optional[int] = None
    ) -> SentimentAnalysisResult:
        """
        Analyze sentiment of a customer message.

        Args:
            message: The customer's message content
            channel: Optional channel information
            customer_id: Optional customer ID

        Returns:
            SentimentAnalysisResult with sentiment and confidence
        """
        try:
            if not self.groq_client:
                # Fallback to simple keyword-based analysis
                return await self._analyze_sentiment_fallback(message)

            # Create prompt for Groq
            prompt = self._create_sentiment_prompt(message, channel)

            # Call Groq API
            response = await self.groq_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a sentiment analysis assistant. "
                            "Analyze customer messages and determine sentiment (positive/neutral/negative). "
                            "Provide a confidence score (0.0-1.0), brief reasoning, "
                            "and identify key sentiment keywords. "
                            "Respond in JSON format with keys: "
                            "sentiment, confidence, reasoning, keywords, emotion."
                        )
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Lower temperature for Groq
                max_tokens=256,
                response_format={"type": "json_object"}
            )

            # Parse response
            content = response.choices[0].message.content
            result_data = self._parse_groq_response(content)

            # Create result object
            sentiment = Sentiment(result_data.get('sentiment', 'neutral'))
            confidence = float(result_data.get('confidence', 0.5))
            reasoning = result_data.get('reasoning')
            keywords = result_data.get('keywords', [])
            emotion = result_data.get('emotion')

            result = SentimentAnalysisResult(
                sentiment=sentiment,
                confidence=confidence,
                reasoning=reasoning,
                keywords=keywords,
                emotion=emotion
            )

            logger.info(
                f"Sentiment analyzed: {sentiment.value}, "
                f"confidence={confidence:.2f}, "
                f"message_length={len(message)}"
            )

            return result

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            # Fallback to simple analysis
            return await self._analyze_sentiment_fallback(message)

    def _create_sentiment_prompt(
        self,
        message: str,
        channel: Optional[str]
    ) -> str:
        """
        Create prompt for Groq sentiment analysis.

        Args:
            message: The message to analyze
            channel: Optional channel information

        Returns:
            Formatted prompt for OpenAI
        """
        channel_context = f"Channel: {channel}" if channel else ""
        return (
            f"Analyze the sentiment of this customer message:\n\n"
            f"{channel_context}\n"
            f"Message: \"{message}\"\n\n"
            f"Consider:\n"
            f"- Customer tone and language\n"
            f"- Emotional indicators (emotions, exclamation marks, etc.)\n"
            f"- Urgency indicators (urgent, immediately, etc.)\n"
            f"- Frustration indicators (still not working, broken, etc.)\n"
            f"- Satisfaction indicators (thank, great, works, etc.)"
        )

    def _parse_groq_response(self, content: str) -> Dict[str, Any]:
        """
        Parse Groq response JSON content.

        Args:
            content: JSON string from Groq

        Returns:
            Dictionary with parsed data
        """
        try:
            import json
            result_data = json.loads(content)
            return result_data
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Groq JSON response: {e}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'reasoning': 'Parsing error',
                'keywords': [],
                'emotion': 'neutral'
            }

    async def _analyze_sentiment_fallback(
        self,
        message: str
    ) -> SentimentAnalysisResult:
        """
        Fallback sentiment analysis using keyword matching.

        Used when Groq is not available.

        Args:
            message: The message to analyze

        Returns:
            SentimentAnalysisResult with sentiment and confidence
        """
        message_lower = message.lower()

        # Positive indicators
        positive_keywords = [
            'thank', 'great', 'awesome', 'works', 'excellent',
            'helpful', 'fixed', 'resolved', 'perfect', 'love',
            'appreciate', 'thanks', 'good', 'nice'
        ]

        # Negative indicators
        negative_keywords = [
            'broken', 'not working', 'doesn\'t work', 'frustrating',
            'hate', 'terrible', 'useless', 'worst', 'fail',
            'error', 'issue', 'problem', 'bug', 'broken',
            'stupid', 'ridiculous', 'angry', 'disappointed'
        ]

        # Urgency indicators (often negative)
        urgency_keywords = [
            'urgent', 'immediately', 'asap', 'right now',
            'emergency', 'critical', 'blocking', 'stuck'
        ]

        # Count keywords
        positive_count = sum(1 for kw in positive_keywords if kw in message_lower)
        negative_count = sum(1 for kw in negative_keywords if kw in message_lower)
        urgency_count = sum(1 for kw in urgency_keywords if kw in message_lower)

        # Determine sentiment
        if negative_count > positive_count + 1:
            sentiment = Sentiment.NEGATIVE
            confidence = 0.7
        elif positive_count > negative_count + 1:
            sentiment = Sentiment.POSITIVE
            confidence = 0.7
        elif urgency_count > 0:
            sentiment = Sentiment.NEGATIVE  # Urgency often indicates negative
            confidence = 0.65
        else:
            sentiment = Sentiment.NEUTRAL
            confidence = 0.5

        # Extract keywords
        keywords = []
        if negative_count > 0:
            keywords.extend([kw for kw in negative_keywords if kw in message_lower][:3])
        if positive_count > 0:
            keywords.extend([kw for kw in positive_keywords if kw in message_lower][:3])

        result = SentimentAnalysisResult(
            sentiment=sentiment,
            confidence=confidence,
            reasoning="Fallback keyword-based analysis",
            keywords=keywords
        )

        logger.debug(f"Fallback sentiment analysis: {sentiment.value}")

        return result

    async def analyze_sentiment_batch(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[SentimentAnalysisResult]:
        """
        Analyze sentiment for multiple messages (batch processing).

        Args:
            messages: List of message dictionaries with 'content' and optional 'channel'

        Returns:
            List of SentimentAnalysisResult objects
        """
        results = []

        for msg in messages:
            result = await self.analyze_sentiment(
                message=msg.get('content', ''),
                channel=msg.get('channel'),
                customer_id=msg.get('customer_id')
            )
            results.append(result)

        # Log summary
        positive_count = sum(1 for r in results if r.sentiment == Sentiment.POSITIVE)
        neutral_count = sum(1 for r in results if r.sentiment == Sentiment.NEUTRAL)
        negative_count = sum(1 for r in results if r.sentiment == Sentiment.NEGATIVE)

        logger.info(
            f"Sentiment batch analysis: {len(results)} messages, "
            f"positive={positive_count}, neutral={neutral_count}, negative={negative_count}"
        )

        return results

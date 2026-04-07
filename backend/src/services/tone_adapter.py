"""
Tone adaptation service for different channels.
Adapts message tone for email (formal/detailed), WhatsApp (short/casual), and webform (semi-formal).
"""
import re
import asyncio
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class ToneAdapter:
    """Service to adapt AI responses to specific channel requirements."""

    def __init__(self):
        pass

    async def adapt_tone(self, content: str, channel: str, sentiment: Optional[str] = None) -> str:
        """
        Adapt the tone of content for the specified channel and sentiment.

        Args:
            content: The message content to adapt
            channel: The target channel (email, whatsapp, webform)
            sentiment: Optional customer sentiment for further tailoring

        Returns:
            Tone-adapted message content
        """
        if not content or not content.strip():
            return content

        channel = channel.lower().strip()
        logger.debug(f"Adapting tone for channel: {channel} with sentiment: {sentiment}")

        try:
            # First, apply sentiment-based adjustments
            if sentiment:
                content = self._adjust_for_sentiment(content, sentiment, channel)

            # Then, adapt for the specific channel
            if channel == 'email':
                return self._adapt_for_email(content)
            elif channel == 'whatsapp':
                return self._adapt_for_whatsapp(content)
            elif channel == 'webform':
                return self._adapt_for_webform(content)
            else:
                logger.warning(f"Unknown channel '{channel}' for tone adaptation. Returning original content.")
                return content
        except Exception as e:
            logger.error(f"Error adapting tone: {e}")
            return content

    def _adjust_for_sentiment(self, content: str, sentiment: str, channel: str) -> str:
        """Tailor response based on detected customer sentiment."""
        sentiment = sentiment.lower()
        
        if sentiment == 'negative':
            # Add empathetic or apologetic tone
            apologies = ["I apologize for any inconvenience caused.", "I'm sorry you're experiencing this issue."]
            if not any(apology.lower() in content.lower() for apology in apologies):
                content = apologies[0] + " " + content
        elif sentiment == 'positive':
            # Add appreciative tone
            appreciation = ["I'm glad I could help!", "Great to hear from you!"]
            if not any(appr.lower() in content.lower() for appr in appreciation):
                content = content.rstrip('.') + " " + appreciation[0]
                
        return content

    def _adapt_for_email(self, content: str) -> str:
        """Detailed and formal email tone."""
        if not any(greet in content.lower() for greet in ["hello", "hi", "dear"]):
            content = "Hello,\n\n" + content
            
        if not any(close in content.lower() for close in ["best regards", "sincerely", "thanks"]):
            content = content.rstrip() + "\n\nBest regards,\nSupport Team"
            
        return content.strip()

    def _adapt_for_whatsapp(self, content: str) -> str:
        """Concise and casual WhatsApp tone with emojis."""
        # Simplify and shorten
        content = content.replace("Hello,", "Hey! 👋")
        content = content.replace(". ", ".\n") # Use line breaks for readability
        
        # Ensure it's not too formal
        content = content.replace("I apologize for", "Sorry for")
        
        # Max two emojis per constitution
        if "👋" not in content and "😊" not in content:
            content = content.rstrip('.') + " 😊"
            
        return content.strip()

    def _adapt_for_webform(self, content: str) -> str:
        """Professional but helpful web form tone."""
        content = content.replace("Hello,", "Hello")
        if not content.startswith("Hello"):
            content = "Hello, " + content
            
        if "help" not in content.lower():
            content = content.rstrip('.') + ". Please let me know if you need more help."
            
        return content.strip()
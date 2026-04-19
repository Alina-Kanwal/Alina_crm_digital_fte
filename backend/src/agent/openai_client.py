"""
Groq/OpenAI integration for Digital FTE AI Customer Success Agent.
Handles configuration and testing of LLM API connections, prioritizing Groq for high-speed inference.
"""

import logging
import os
from typing import Dict, Any, Optional
from openai import AsyncOpenAI
from agents import set_default_openai_key

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Client for managing AI model integration (OpenAI or Groq for free tier)."""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize AI client, prioritizing Groq for free/high-speed tier.

        Args:
            api_key: API key (if None, will try GROQ_API_KEY then OPENAI_API_KEY)
            base_url: Optional API base URL (defaults to GROQ_API_BASE if available)
        """
        self.api_key = api_key or os.getenv('GROQ_API_KEY') or os.getenv('OPENAI_API_KEY')
        self.base_url = base_url or os.getenv('GROQ_API_BASE') or os.getenv('OPENAI_BASE_URL')
        self.model = os.getenv('GROQ_MODEL') or os.getenv('OPENAI_MODEL', 'llama-3.3-70b-versatile')
        self.client = None
        self.is_configured = False

        if self.api_key:
            self._configure_client()
        else:
            logger.warning("No API key provided. Set GROQ_API_KEY or OPENAI_API_KEY environment variable.")

    def _configure_client(self):
        """Configure the AI client."""
        try:
            if not self.api_key:
                raise ValueError("API key is required")

            # Initialize the async client for direct API calls
            # Use Groq or other OpenAI-compatible endpoints if base_url is set
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )

            # Set the API key for the OpenAI agents framework if using OpenAI directly
            if not self.base_url or "openai.com" in self.base_url:
                try:
                    set_default_openai_key(self.api_key)
                except Exception as e:
                    logger.debug(f"Could not set default key for agents SDK (expected if using Groq): {e}")

            self.is_configured = True
            provider = "Groq" if "groq" in (self.base_url or "").lower() else "OpenAI"
            logger.info(f"{provider} AI Client configured successfully (model={self.model})")

        except Exception as e:
            logger.error(f"Failed to configure AI client: {e}")
            self.is_configured = False
            raise

    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the API connection.

        Returns:
            Connection test results
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "Client not configured",
                "message": "Please set OPENAI_API_KEY environment variable"
            }

        try:
            # Simple test call to verify API connectivity
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'API connection test successful' in exactly those words."}
                ],
                max_tokens=10,
                temperature=0
            )

            result_text = response.choices[0].message.content.strip()

            success = "API connection test successful" in result_text

            return {
                "success": success,
                "response": result_text,
                "model": self.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else None,
                "message": "Connection test passed" if success else "Unexpected response from API"
            }

        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to connect to AI API ({self.base_url})"
            }

    async def generate_completion(self, prompt: str, max_tokens: int = 150,
                                 temperature: float = 0.7) -> Dict[str, Any]:
        """
        Generate a text completion.

        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)

        Returns:
            Generation results
        """
        if not self.is_configured:
            return {
                "success": False,
                "error": "Client not configured",
                "message": "Please set OPENAI_API_KEY environment variable"
            }

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant for customer support."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )

            return {
                "success": True,
                "response": response.choices[0].message.content,
                "model": self.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                } if response.usage else None,
                "finish_reason": response.choices[0].finish_reason
            }

        except Exception as e:
            logger.error(f"Error generating completion: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to generate completion"
            }

    def get_client(self) -> Optional[AsyncOpenAI]:
        """
        Get the underlying client.

        Returns:
            AsyncOpenAI client instance or None if not configured
        """
        return self.client if self.is_configured else None

    def is_ready(self) -> bool:
        """
        Check if the client is ready for use.

        Returns:
            True if configured and ready, False otherwise
        """
        return self.is_configured and self.client is not None


# Factory function for dependency injection
def create_openai_client(api_key: Optional[str] = None) -> OpenAIClient:
    """Factory function to create OpenAIClient instance."""
    return OpenAIClient(api_key)


# Convenience function for quick testing
async def test_openai_connection(api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Quick test of OpenAI connection.

    Args:
        api_key: Optional API key (uses environment variable if not provided)

    Returns:
        Connection test results
    """
    client = OpenAIClient(api_key)
    return await client.test_connection()
"""
OpenAI Agents SDK integration with custom function tools.
Implements the AI core for the Digital FTE agent using OpenAI's Agents SDK.
"""
import os
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

try:
    # Try the new OpenAI Agents SDK import
    from openai.agents import Agent, function_tool
except ImportError:
    # Fallback to older OpenAI function calling if Agents SDK not available
    logger.warning("OpenAI Agents SDK not available, using fallback function calling")
    Agent = None
    function_tool = lambda x: x
from src.services.doc_search import DocumentSearchService
from src.services.tone_adapter import ToneAdapterService

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize supporting services
doc_search_service = DocumentSearchService()
tone_adapter_service = ToneAdapterService()

# Define function tools - handle case where Agents SDK is not available
def _create_function_tool(func):
    """Create a function tool, handling both Agents SDK and fallback cases."""
    if Agent is not None and function_tool is not None:
        return function_tool(func)
    else:
        # Fallback: just return the function unchanged
        return func

@_create_function_tool
def search_product_documentation(query: str) -> str:
    """
    Search product documentation for information to answer customer questions.

    Args:
        query: The search query string

    Returns:
        Relevant documentation excerpts as a string
    """
    try:
        results = doc_search_service.search(query, max_results=3)
        if results:
            return "\n\n".join([f"From {result['title']}:\n{result['content']}" for result in results])
        else:
            return "No relevant documentation found for the query."
    except Exception as e:
        logger.error(f"Error searching documentation: {e}")
        return f"Error searching documentation: {str(e)}"

@_create_function_tool
def adapt_tone_for_channel(content: str, channel: str) -> str:
    """
    Adapt the tone of a message for the specific channel.

    Args:
        content: The message content to adapt
        channel: The target channel (email, whatsapp, webform)

    Returns:
        Tone-adapted message content
    """
    try:
        return tone_adapter_service.adapt_tone(content, channel)
    except Exception as e:
        logger.error(f"Error adapting tone: {e}")
        return content  # Return original content if adaptation fails

@_create_function_tool
def escalate_to_human(reason: str, context: str) -> str:
    """
    Escalate a conversation to a human agent.

    Args:
        reason: The reason for escalation (pricing, refund, legal, profanity, unresolved)
        context: Context about the conversation and customer

    Returns:
        Escalation confirmation message
    """
    try:
        # In a real implementation, this would trigger actual escalation workflows
        logger.warning(f"Escalation triggered: {reason} - {context}")
        return f"Escalation initiated for reason: {reason}. A human agent will be notified shortly."
    except Exception as e:
        logger.error(f"Error during escalation: {e}")
        return f"Error during escalation: {str(e)}"

@_create_function_tool
async def analyze_customer_sentiment(text: str) -> Dict[str, Any]:
    """
    Analyze customer sentiment in the provided text using LLM for accuracy.

    Args:
        text: The text to analyze for sentiment

    Returns:
        Dictionary with sentiment label and score
    """
    try:
        # Use gpt-4o-mini for efficient sentiment analysis
        prompt = f"Analyze the sentiment of the following customer support message. Provide a sentiment label (positive, neutral, negative) and a sentiment score between -1.0 and 1.0.\n\nMessage: {text}\n\nReturn ONLY a JSON object with 'sentiment' and 'score' keys."
        
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        
        return {
            "sentiment": result.get("sentiment", "neutral"),
            "score": float(result.get("score", 0.0)),
            "confidence": 0.95  # LLM based sentiment is high confidence
        }
    except Exception as e:
        logger.error(f"Error analyzing sentiment with LLM: {e}")
        # Fallback to simple logic if LLM fails
        return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}

class AIAgent:
    def __init__(self):
        self.agent = None
        self._initialize_agent()

    def _initialize_agent(self):
        """Initialize the OpenAI Agents SDK agent with custom tools."""
        try:
            self.agent = Agent(
                name="Digital FTE Customer Success Agent",
                instructions="""You are an elite AI Customer Success Agent. Your mission is to provide FLAWLESS support using ONLY verified information.

### RIGOROUS GROUNDING RULES:
1. ALWAYS use the 'search_product_documentation' tool before answering ANY technical or product question.
2. If the documentation does not contain the answer, state clearly that you don't have that information and offer to escalate to a human.
3. NEVER make up features, pricing, or technical details ("Zero Hallucination" policy).
4. If a customer is angry (negative sentiment), be extra empathetic and prioritize resolution or escalation.
5. Adapt your tone strictly: Professional/Formal for Email, Concise/Helpful for Webform, Warm/Brief for WhatsApp.

### ESCALATION CRITERIA:
- Explicit requests for human help.
- Complex pricing/refund/legal inquiries.
- Profanity or extreme hostility.
- When you have searched 3+ times and cannot find a satisfactory answer.

Your goal is 100% accuracy and high customer satisfaction.""",
                tools=[search_product_documentation, adapt_tone_for_channel, escalate_to_human, analyze_customer_sentiment],
                model=os.getenv("OPENAI_MODEL", "gpt-4o")
            )
            logger.info("OpenAI Agents SDK agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI Agents SDK agent: {e}")
            self.agent = None

    def is_available(self) -> bool:
        """Check if the AI agent is available."""
        return self.agent is not None

    def process_inquiry(self, message: Dict, conversation_history: List[Dict] = None) -> Dict:
        """
        Process a customer inquiry and generate a response.

        Args:
            message: The parsed customer message
            conversation_history: Previous messages in the conversation (optional)

        Returns:
            Dictionary containing the AI-generated response and metadata
        """
        if not self.agent:
            return self._get_fallback_response(message)

        try:
            # Prepare the conversation context
            context = self._build_conversation_context(message, conversation_history or [])

            # Run the agent
            result = self.agent.run(context)

            # Extract the response
            response_text = getattr(result, 'final_output', str(result))

            # Analyze sentiment of the customer's message (asynchronous)
            # In a synchronous run, we'll use a helper to wait or just call the async function
            import asyncio
            sentiment_result = asyncio.run(analyze_customer_sentiment(message.get('body', '')))

            return {
                'response': response_text,
                'sentiment': sentiment_result['sentiment'],
                'sentiment_score': sentiment_result['score'],
                'confidence': sentiment_result.get('confidence', 0.0),
                'escalationTriggered': 'ESCALATION_INITIATED' in response_text,
                'sources': []  # In a real implementation, you'd track which tools were used
            }

        except Exception as e:
            logger.error(f"Error processing inquiry with AI agent: {e}")
            return self._get_fallback_response(message, str(e))

    def _build_conversation_context(self, message: Dict, conversation_history: List[Dict]) -> str:
        """Build conversation context for the AI agent."""
        context_parts = [
            f"Customer message via {message.get('channel', 'unknown')}:",
            f"Subject: {message.get('subject', 'No subject')}",
            f"Message: {message.get('body', '')}",
            ""
        ]

        if conversation_history:
            context_parts.append("Conversation history:")
            for i, hist_msg in enumerate(conversation_history[-5:]):  # Last 5 messages
                context_parts.append(
                    f"{i+1}. [{hist_msg.get('channel', 'unknown')}] {hist_msg.get('body', '')[:100]}..."
                )
            context_parts.append("")

        context_parts.append("Please provide a helpful, accurate response based on the product documentation.")
        context_parts.append("Remember to adapt your tone appropriately for the channel.")

        return "\n".join(context_parts)

    def _get_fallback_response(self, message: Dict, error: str = None) -> Dict:
        """Provide a fallback response when the AI agent is unavailable."""
        logger.warning(f"Using fallback response due to: {error or 'AI agent unavailable'}")

        # Simple fallback responses based on channel
        channel = message.get('channel', 'unknown')
        if channel == 'email':
            response = "Thank you for your email. Our team is currently experiencing high volume and will respond to your inquiry within 2 business days."
        elif channel == 'whatsapp':
            response = "Hey there! We're a bit busy right now but will get back to you soon. Thanks for your patience! 😊"
        else:  # webform or default
            response = "Thank you for contacting us. We've received your message and will respond shortly."

        return {
            'response': response,
            'sentiment': 'neutral',
            'sentiment_score': 0.0,
            'confidence': 0.0,
            'escalationTriggered': False,
            'sources': []
        }
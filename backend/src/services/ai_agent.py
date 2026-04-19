"""
Groq API integration with custom function tools.
Implements the AI core for the Digital FTE agent using Groq's high-speed LPU inference.
"""
import os
import logging
import json
from typing import List, Dict, Any, Optional
from groq import Groq

logger = logging.getLogger(__name__)

# Initialize Groq client with fail-safe for environment variables
_groq_api_key = os.getenv("GROQ_API_KEY")
if not _groq_api_key:
    logger.warning("GROQ_API_KEY not found in environment. AI Agent will be inactive.")
    groq_client = None
else:
    try:
        groq_client = Groq(api_key=_groq_api_key)
    except Exception as e:
        logger.error(f"Failed to initialize Groq client: {e}")
        groq_client = None

# Initialize supporting services
from src.services.doc_search import DocumentSearchService
from src.services.tone_adapter import ToneAdapterService

doc_search_service = DocumentSearchService()
tone_adapter_service = ToneAdapterService()

def search_product_documentation(query: str) -> str:
    """Search product documentation for information to answer customer questions."""
    try:
        results = doc_search_service.search(query, max_results=3)
        if results:
            return "\n\n".join([f"From {result['title']}:\n{result['content']}" for result in results])
        else:
            return "No relevant documentation found for the query."
    except Exception as e:
        logger.error(f"Error searching documentation: {e}")
        return f"Error searching documentation: {str(e)}"

def adapt_tone_for_channel(content: str, channel: str) -> str:
    """Adapt the tone of a message for the specific channel."""
    try:
        return tone_adapter_service.adapt_tone(content, channel)
    except Exception as e:
        logger.error(f"Error adapting tone: {e}")
        return content

def escalate_to_human(reason: str, context: str) -> str:
    """Escalate a conversation to a human agent."""
    try:
        logger.warning(f"Escalation triggered: {reason} - {context}")
        return f"Escalation initiated for reason: {reason}. A human agent will be notified shortly."
    except Exception as e:
        logger.error(f"Error during escalation: {e}")
        return f"Error during escalation: {str(e)}"

async def analyze_sentiment_internal(text: str) -> Dict[str, Any]:
    """Analyze customer sentiment using Groq."""
    if not groq_client:
        return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
    try:
        prompt = f"Analyze the sentiment of the following customer support message. Provide a sentiment label (positive, neutral, negative) and a sentiment score between -1.0 and 1.0.\n\nMessage: {text}\n\nReturn ONLY a JSON object with 'sentiment' and 'score' keys."
        
        response = groq_client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return {
            "sentiment": result.get("sentiment", "neutral"),
            "score": float(result.get("score", 0.0)),
            "confidence": 0.98
        }
    except Exception as e:
        logger.error(f"Error analyzing sentiment with Groq: {e}")
        return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}

class AIAgent:
    def __init__(self):
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.instructions = """You are an elite AI Customer Success Agent. Your mission is to provide FLAWLESS support using ONLY verified information.

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

Your goal is 100% accuracy and high customer satisfaction."""
        
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_product_documentation",
                    "description": "Search product documentation for information to answer customer questions",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query string"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "adapt_tone_for_channel",
                    "description": "Adapt the tone of a message for the specific channel",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string", "description": "The message content"},
                            "channel": {"type": "string", "description": "Target channel (email, whatsapp, webform)"}
                        },
                        "required": ["content", "channel"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "escalate_to_human",
                    "description": "Escalate a conversation to a human agent",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "reason": {"type": "string", "description": "Reason for escalation"},
                            "context": {"type": "string", "description": "Conversation context"}
                        },
                        "required": ["reason", "context"]
                    }
                }
            }
        ]

    def is_available(self) -> bool:
        return True

    def process_inquiry(self, message: Dict, conversation_history: List[Dict] = None) -> Dict:
        """Process inquiry using Groq with Tool Calling."""
        if not groq_client:
             return self._get_fallback_response(message, "AI Client not initialized")
        try:
            messages = [
                {"role": "system", "content": self.instructions},
                {"role": "user", "content": self._build_conversation_context(message, conversation_history or [])}
            ]

            # Tool Calling Loop (Limit to 3 iterations for safety)
            for _ in range(3):
                response = groq_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto"
                )

                response_message = response.choices[0].message
                tool_calls = response_message.tool_calls

                if not tool_calls:
                    # Final response generated
                    import asyncio
                    sentiment_result = asyncio.run(analyze_sentiment_internal(message.get('body', '')))
                    
                    return {
                        'response': response_message.content,
                        'sentiment': sentiment_result['sentiment'],
                        'sentiment_score': sentiment_result['score'],
                        'confidence': sentiment_result.get('confidence', 0.0),
                        'escalationTriggered': "Escalation initiated" in (response_message.content or ""),
                        'sources': []
                    }

                # Handle tool calls
                messages.append(response_message)
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    if function_name == "search_product_documentation":
                        tool_result = search_product_documentation(**function_args)
                    elif function_name == "adapt_tone_for_channel":
                        tool_result = adapt_tone_for_channel(**function_args)
                    elif function_name == "escalate_to_human":
                        tool_result = escalate_to_human(**function_args)
                    else:
                        tool_result = "Error: Unknown function"

                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": tool_result
                    })

        except Exception as e:
            logger.error(f"Error processing inquiry with Groq agent: {e}")
            return self._get_fallback_response(message, str(e))

    def _build_conversation_context(self, message: Dict, conversation_history: List[Dict]) -> str:
        context_parts = [
            f"Customer message via {message.get('channel', 'unknown')}:",
            f"Subject: {message.get('subject', 'No subject')}",
            f"Message: {message.get('body', '')}",
            ""
        ]
        if conversation_history:
            context_parts.append("Conversation history:")
            for i, hist_msg in enumerate(conversation_history[-3:]):
                context_parts.append(f"{i+1}. [{hist_msg.get('channel', 'unknown')}] {hist_msg.get('body', '')[:100]}")
            context_parts.append("")
        
        return "\n".join(context_parts)

    def _get_fallback_response(self, message: Dict, error: str = None) -> Dict:
        logger.warning(f"Using fallback response: {error}")
        channel = message.get('channel', 'webform')
        responses = {
            'email': "Thank you for your email. We will get back to you within 2 business days.",
            'whatsapp': "Hey! We're busy but will message you back soon! 😊",
            'webform': "Thank you for contacting us. We'll respond shortly."
        }
        return {
            'response': responses.get(channel, responses['webform']),
            'sentiment': 'neutral',
            'sentiment_score': 0.0,
            'confidence': 0.0,
            'escalationTriggered': False,
            'sources': []
        }
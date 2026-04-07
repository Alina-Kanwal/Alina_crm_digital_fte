"""
AIAgent wrapper class for the Digital FTE Customer Success Agent.
Orchestrates OpenAI Agents SDK with tools for knowledge search and context retrieval.
Phase 9.1 (T105): Performance optimized with parallel internal tasks and corrected import names.
"""
import asyncio
import logging
from typing import Dict, Any, Optional

# Correct tool imports based on directory structure and exported function names
from src.agent.tools.doc_search import search_knowledge_base
from src.agent.tools.sentiment import analyze_sentiment
from src.agent.tools.escalation import should_escalate

# Import OpenAI Agents SDK components - CORRECT PACKAGE NAME is 'agents'
from agents import Agent, Runner

logger = logging.getLogger(__name__)

class AIAgent:
    """Production-grade AI agent wrapper for customer inquiry processing."""

    def __init__(self):
        self.initialized = False
        self.agent = None
        self.runner = None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")

    async def initialize(self):
        """Initialize the OpenAI agent and runner with tools."""
        if self.initialized:
            return

        logger.info(f"Initializing AIAgent with model {self.model}...")
        
        # Tools are defined in the digital-fte-agent constitution
        tools = [search_knowledge_base, should_escalate]
        
        # Build the system instructions according to Digital FTE Constitution Principles
        instructions = (
            "You are a 24/7 expert customer success agent for 'Digital FTE Factory'.\n\n"
            "## CHANNELS & TONE\n"
            "- Gmail/Email: Formal, structured, professional greeting and closing.\n"
            "- WhatsApp: Casual, concise, friendly, can use emojis.\n"
            "- Web Support Form: Semi-formal, direct, helpful.\n\n"
            "## WORKFLOW (CRITICAL)\n"
            "Your internal workflow MUST follow these 4 steps in order:\n"
            "1. TICKET CREATION: A ticket should be created for every encounter (already handled by system).\n"
            "2. GET HISTORY: Review the provided conversation history to maintain cross-channel continuity.\n"
            "3. SEARCH KNOWLEDGE: Use 'search_knowledge_base' to find documentation. DO NOT hallucinate features.\n"
            "4. RESPONSE: Generate the final response adapted for the current channel.\n\n"
            "## ESCALATION TRIGGERS\n"
            "You MUST use 'should_escalate' and initiate human handover if the customer:\n"
            "- Uses profanity or abusive language (safety/liability).\n"
            "- Expresses extreme frustration or mentions a 'lawyer' or 'legal' action.\n"
            "- Requests a 'refund' or asks about 'pricing' (you have NO pricing authorization).\n"
            "- Explicitly requests a 'human' or 'manager'.\n"
            "- If you fail to find a clear answer in documentation after 2 search attempts.\n\n"
            "## CONSTRAINTS\n"
            "- NEVER discuss pricing, discounts, or refunds. Always prioritize escalation for these.\n"
            "- Maintain cross-channel continuity. If the user mentioned something on WhatsApp earlier, acknowledge it here if relevant.\n"
            "- Ensure p95 response time < 3s (keep your analysis concise)."
        )

        self.agent = Agent(
            name="Digital FTE Support Agent",
            instructions=instructions,
            tools=tools,
            model=self.model
        )
        self.runner = Runner()
        self.initialized = True
        logger.info(f"AIAgent fully initialized for {self.model} processing.")

    async def process(self, content: str, customer_id: str, correlation_id: str, history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Process a customer inquiry through the AI agent with conversation history.
        """
        if not self.initialized:
            await self.initialize()

        logger.debug(f"[{correlation_id}] AIAgent processing request")

        try:
            # 1. Start sentiment analysis in parallel with LLM Thinking
            sentiment_task = asyncio.create_task(analyze_sentiment(content))

            # 2. Format history for the prompt
            history_str = ""
            if history:
                history_str = "\n\n### RECENT CONVERSATION HISTORY\n"
                for msg in history[-5:]:  # Last 5 for tokens/performance
                    direction = "Customer" if msg.get("direction") == "incoming" else "Agent"
                    channel = msg.get("channel", "unknown")
                    history_str += f"{direction} ({channel}): {msg.get('content')}\n"

            # 3. Execute LLM Agent Pipeline (Knowledge Retrieval + Reaction)
            # This is the primary latency bottleneck (LLM + IO Tools)
            full_input = f"{history_str}\n\n### CURRENT CUSTOMER MESSAGE\n{content}"
            
            result = await self.runner.run(
                agent=self.agent,
                input=full_input,
                context={"customer_id": customer_id, "correlation_id": correlation_id}
            )

            # 4. Wait for the parallel sentiment results to complete
            sentiment_result = await sentiment_task
            
            logger.debug(f"[{correlation_id}] AIAgent completed processing")
            
            # Extract output
            output_text = result.final_output if hasattr(result, 'final_output') else str(result)
            
            return {
                "response": output_text,
                "sentiment": sentiment_result.get("sentiment", "neutral"),
                "sentiment_score": sentiment_result.get("confidence", 0.0),
                "success": True
            }

        except Exception as e:
            logger.error(f"[{correlation_id}] Error in AIAgent process: {e}", exc_info=True)
            return {
                "response": "I apologize, but I'm having trouble connecting to my knowledge base right now. Please try again in a moment.",
                "sentiment": "neutral",
                "sentiment_score": 0.0,
                "success": False,
                "error": str(e)
            }

    def is_available(self) -> bool:
        """Required for health checks."""
        return self.initialized and self.agent is not None
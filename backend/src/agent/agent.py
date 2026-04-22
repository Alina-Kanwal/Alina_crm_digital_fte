"""
AIAgent wrapper class for the Digital FTE Customer Success Agent.
Production-grade implementation using LiteLLM for GROQ compatibility.
Orchestrates tool calling, sentiment analysis, and context-aware responses.
"""
import os
import logging
import asyncio
import litellm
from typing import Dict, Any, Optional, List
from src.agent.tools.doc_search import search_knowledge_base
from src.agent.tools.sentiment import analyze_sentiment
from src.agent.tools.escalation import should_escalate

logger = logging.getLogger(__name__)

class AIAgent:
    """Production-ready AI agent tailored for Alibaba DashScope & Groq."""

    def __init__(self):
        # Primary: Alibaba DashScope (Qwen)
        self.dashscope_key = os.getenv("DASHSCOPE_API_KEY")
        
        if self.dashscope_key:
            self.model = os.getenv("DASHSCOPE_MODEL", "qwen-plus")
            self.api_key = self.dashscope_key
            self.api_base = os.getenv("DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
            logger.info(f"Agent initialized with Alibaba DashScope: {self.model}")
        else:
            # Fallback: Groq (Legacy)
            self.model = os.getenv("GROQ_MODEL", "groq/llama-3.1-70b-versatile")
            self.api_key = os.getenv("GROQ_API_KEY")
            self.api_base = os.getenv("GROQ_API_BASE", "https://api.groq.com/openai/v1")
            logger.info(f"Agent initialized with Fallback (Groq): {self.model}")
        
        # Configure LiteLLM for stability
        litellm.drop_params = True
        litellm.telemetry = False


    async def get_system_instructions(self) -> str:
        """Centralized system prompt for the Digital FTE Agent."""
        return (
            "You are a 24/7 expert customer success agent for 'Digital FTE Factory'.\n"
            "Channel Tones:\n"
            "- Email: Formal & structured.\n"
            "- WhatsApp: Casual & friendly (use emojis).\n"
            "- Web Form: Semi-formal & direct.\n\n"
            "Safety: NEVER discuss pricing, refunds, or discounts. Use 'should_escalate' for these topics.\n"
            "Logic: Use 'search_knowledge_base' to answer product questions. If answer not found after 2 tries, escalate."
        )

    async def process(self, content: str, customer_id: str, correlation_id: str, history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Processes inquiries using Groq. Uses parallel sentiment analysis for speed.
        """
        logger.info(f"[{correlation_id}] Processing inquiry with GROQ model: {self.model}")
        
        try:
            # 1. Parallel Sentiment Analysis (Self-Correction/Internal Loop)
            # Note: We run this in parallel to minimize total latency
            sentiment_task = asyncio.create_task(analyze_sentiment(content))

            # 2. Setup Tools for LiteLLM/Groq
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "search_knowledge_base",
                        "description": "Search product documentation for technical answers.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {"type": "string", "description": "The search term"}
                            },
                            "required": ["query"]
                        }
                    }
                },
                {
                    "type": "function",
                    "function": {
                        "name": "should_escalate",
                        "description": "Flag for human intervention.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "reason": {"type": "string", "description": "Reason for escalation"}
                            },
                            "required": ["reason"]
                        }
                    }
                }
            ]

            # 3. Assemble Messages
            msgs = [{"role": "system", "content": await self.get_system_instructions()}]
            
            if history:
                for h in history[-5:]:
                    role = "user" if h.get("direction") == "incoming" else "assistant"
                    msgs.append({"role": role, "content": h.get("content", "")})
            
            msgs.append({"role": "user", "content": content})

            # 4. Agentic Execution Loop with LiteLLM
            response = await litellm.acompletion(
                model=self.model,
                messages=msgs,
                tools=tools,
                tool_choice="auto",
                api_key=self.api_key,
                api_base=self.api_base,
                temperature=0.2  # Low temperature for production stability
            )

            message = response.choices[0].message
            final_content = message.content or ""

            # 5. Handle Tool Calls (If model decides to search or escalate)
            if hasattr(message, "tool_calls") and message.tool_calls:
                msgs.append(message)
                for tool_call in message.tool_calls:
                    func_name = tool_call.function.name
                    import json
                    args = json.loads(tool_call.function.arguments)

                    if func_name == "search_knowledge_base":
                        search_result = await search_knowledge_base(args["query"])
                        msgs.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": func_name,
                            "content": str(search_result)
                        })

                    elif func_name == "should_escalate":
                        # Immediate escalation trigger
                        return {
                            "response": "I've flagged this for a human specialist who will review it shortly. Stand by.",
                            "sentiment": (await sentiment_task).get("sentiment", "neutral"),
                            "escalated": True,
                            "success": True
                        }

                # Final follow-up after all tool calls are handled
                follow_up = await litellm.acompletion(
                    model=self.model,
                    messages=msgs,
                    api_key=self.api_key,
                    api_base=self.api_base
                )
                final_content = follow_up.choices[0].message.content

            sentiment_res = await sentiment_task
            
            return {
                "response": final_content,
                "sentiment": sentiment_res.get("sentiment", "neutral"),
                "sentiment_score": sentiment_res.get("confidence", 0.0),
                "success": True
            }

        except Exception as e:
            logger.exception(f"[{correlation_id}] GROQ agent failed: {e}")
            return {
                "response": "Our system is under high frequency. I'll get back to you in a second.",
                "success": False,
                "error": str(e)
            }

    def is_available(self) -> bool:
        """Health check: verified if API Key exists."""
        return bool(self.api_key)
"""
Custom tool: Escalation decision for Digital FTE AI Customer Success Agent.
Determines if a human handoff is required.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def should_escalate(message: str, customer_history: str = "",
                         conversation_count: int = 1) -> Dict[str, Any]:
    """
    Rule-based escalation logic for safety and reliability.
    """
    try:
        text = f"{message} {customer_history}".lower()
        
        # Critical triggers
        triggers = ["refund", "legal", "lawsuit", "sue", "manager", "human", "pricing", "cost"]
        
        found = [t for t in triggers if t in text]
        
        if found or conversation_count >= 3:
            return {
                "should_escalate": True,
                "reason": f"Trigger words found: {found}" if found else "High conversation volume",
                "recommended_action": "escalate_to_human"
            }
            
        return {"should_escalate": False, "recommended_action": "handle_with_ai"}

    except Exception as e:
        logger.error(f"Escalation check error: {e}")
        return {"should_escalate": True, "reason": "Error in logic", "recommended_action": "escalate_to_human"}
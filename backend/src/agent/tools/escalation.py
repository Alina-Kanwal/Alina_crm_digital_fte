"""
Custom function tool: Escalation decision for Digital FTE AI Customer Success Agent.
Determines when to escalate customer conversations to human agents based on predefined rules.
"""

import logging
import re
from typing import Dict, Any
from agents import function_tool

logger = logging.getLogger(__name__)


@function_tool
async def should_escalate(message: str, customer_history: str = "",
                         conversation_count: int = 1) -> Dict[str, Any]:
    """
    Determine if a customer conversation should be escalated to human agents.

    This function tool implements the escalation logic specified in the constitution
    and requirements, including:
    - Pricing-related inquiries
    - Refund requests
    - Legal matters
    - Profanity or abusive language
    - Unresolved issues after 3+ agent attempts

    Args:
        message: Current customer message
        customer_history: Previous conversation history with this customer
        conversation_count: Number of previous messages in this conversation

    Returns:
        Escalation decision with confidence score, reasoning, and recommended actions
    """
    try:
        logger.debug(f"Evaluating escalation for message: '{message[:100]}...' (history: {len(customer_history)} chars, count: {conversation_count})")

        # Prepare text for analysis
        combined_text = f"{message} {customer_history}".lower().strip()

        # Define escalation triggers based on constitution and requirements
        escalation_rules = {
            "pricing_inquiry": {
                "keywords": ["price", "cost", "expensive", "cheap", "fee", "charge", "billing",
                           "discount", "rate", "quotation", "quote", "pricing", "payment"],
                "weight": 0.8,
                "description": "Pricing-related inquiries requiring human negotiation"
            },
            "refund_request": {
                "keywords": ["refund", "money back", "return", "reimbursement",
                           "chargeback", "dispute", "cancel subscription"],
                "weight": 1.0,  # Highest weight - always escalate
                "description": "Refund requests requiring human approval"
            },
            "legal_matter": {
                "keywords": ["legal", "lawyer", "attorney", "lawsuit", "court", "liability",
                           "terms of service", "violation", "illegal", "law", "compliance",
                           "regulation", "policy", "lawsuit", "sue", "court"],
                "weight": 1.0,  # Highest weight - always escalate
                "description": "Legal matters requiring human expertise"
            },
            "profanity_abuse": {
                "keywords": ["fuck", "shit", "damn", "hell", "bitch", "ass", "crap",
                           " bastard", "whore", "slut", "cunt", "nigger", "faggot"],
                "weight": 1.0,  # Highest weight - always escalate for safety
                "description": "Profanity or abusive language requiring human handling"
            },
            "repeated_issues": {
                "keywords": [],  # Special handling based on conversation_count
                "weight": 0.9,
                "description": "Unresolved issues after multiple attempts",
                "condition": lambda count: count >= 3
            },
            "technical_complexity": {
                "keywords": ["api", "integration", "custom development", "enterprise",
                           "sla", "contract", "implementation", "development"],
                "weight": 0.6,
                "description": "Technically complex inquiries may require human expertise"
            }
        }

        # Evaluate each rule
        triggered_rules = []
        total_weight = 0.0
        max_possible_weight = sum(rule["weight"] for rule in escalation_rules.values())

        for rule_name, rule in escalation_rules.items():
            triggered = False

            # Handle special conditions
            if "condition" in rule:
                if rule["condition"](conversation_count):
                    triggered = True
            else:
                # Check for keyword matches
                matches = []
                for keyword in rule["keywords"]:
                    if keyword in combined_text:
                        matches.append(keyword)

                if matches:
                    triggered = True
                    # Store matches for reporting
                    rule["_matches"] = matches

            if triggered:
                triggered_rules.append({
                    "rule": rule_name,
                    "description": rule["description"],
                    "weight": rule["weight"],
                    "matches": rule.get("_matches", [])
                })
                total_weight += rule["weight"]

        # Calculate escalation probability
        escalation_probability = min(0.95, total_weight / max_possible_weight) if max_possible_weight > 0 else 0.0

        # Determine final escalation decision
        # Escalate if:
        # 1. Any highest-weight rule is triggered (refund, legal, profanity)
        # 2. Escalation probability exceeds threshold (0.7)
        # 3. Conversation count indicates repeated issues (handled in rules)
        should_escalate = False
        escalation_reasons = []

        # Check for automatic escalation triggers
        for rule in triggered_rules:
            if rule["weight"] >= 1.0:  # Highest weight rules
                should_escalate = True
                escalation_reasons.append(rule["description"])

        # Check probability threshold
        if escalation_probability >= 0.7:
            should_escalate = True
            if not escalation_reasons:  # Avoid duplicates
                escalation_reasons.append("Multiple escalation indicators detected")

        # Set confidence level
        confidence = escalation_probability if escalation_probability > 0 else 0.1
        if should_escalate and confidence < 0.7:
            confidence = 0.7  # Minimum confidence for escalation decision

        # Prepare detailed reasoning
        if not should_escalate and not triggered_rules:
            reasoning = "No escalation triggers detected"
        elif not should_escalate:
            reasoning = f"Escalation evaluated but below threshold ({escalation_probability:.2f}). Triggers: {', '.join([r['rule'] for r in triggered_rules])}"
        else:
            reasoning = f"Escalation recommended due to: {'; '.join(escalation_reasons)}"

        result = {
            "should_escalate": should_escalate,
            "confidence": round(confidence, 3),
            "escalation_probability": round(escalation_probability, 3),
            "reasoning": reasoning,
            "triggered_rules": triggered_rules,
            "recommended_action": "escalate_to_human" if should_escalate else "handle_with_ai",
            "conversation_count": conversation_count,
            "metadata": {
                "message_length": len(message),
                "history_length": len(customer_history),
                "analysis_timestamp": __import__('datetime').datetime.utcnow().isoformat()
            }
        }

        logger.info(f"Escalation decision: {should_escalate} (confidence: {confidence:.3f}) - {reasoning}")
        return result

    except Exception as e:
        logger.error(f"Error in escalation decision: {e}")
        # Fail-safe: escalate on error to ensure customer safety
        return {
            "should_escalate": True,
            "confidence": 0.5,
            "reasoning": f"Error in escalation evaluation: {str(e)} - defaulting to escalate for safety",
            "triggered_rules": [],
            "recommended_action": "escalate_to_human",
            "conversation_count": conversation_count,
            "error": str(e)
        }


# Factory function for dependency injection
def create_escalation_decision_tool():
    """Factory function for escalation decision tool (returns the decorated function)."""
    return should_escalate
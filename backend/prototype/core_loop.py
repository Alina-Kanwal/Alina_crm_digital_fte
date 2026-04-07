#!/usr/bin/env python3
"""
Exercise 1.2: Prototype Core Loop - Digital FTE Customer Success Agent

This prototype implements the core customer interaction loop:
1. Take customer message + channel metadata
2. Normalize message
3. Search product documentation
4. Generate helpful response
5. Format response according to channel
6. Decide whether escalation is needed

Author: Digital FTE Prototype
Date: 2026-03-27
"""

import json
import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from enum import Enum


# ============================================================================
# DATA MODELS
# ============================================================================

class Channel(Enum):
    GMAIL = "gmail"
    WHATSAPP = "whatsapp"
    WEBFORM = "webform"


class Sentiment(Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"


class Topic(Enum):
    INTEGRATION_SETUP = "integration_setup"
    WORKFLOW_TROUBLESHOOTING = "workflow_troubleshooting"
    PRICING = "pricing"
    BILLING_REFUND = "billing_refund"
    SECURITY = "security"
    FEATURE_REQUEST = "feature_request"
    API_ACCESS = "api_access"
    LIMITS = "limits"
    FEEDBACK = "feedback"
    WEBHOOK_SETUP = "webhook_setup"
    LEGAL = "legal"
    ENTERPRISE_FEATURES = "enterprise_features"
    SYSTEM_ISSUE = "system_issue"
    ONBOARDING = "onboarding"
    DATA_TRANSFORMATION = "data_transformation"
    BEST_PRACTICES = "best_practices"
    FEATURE_DISCOVERY = "feature_discovery"
    BILLING_CYCLE = "billing_cycle"
    API_INTEGRATION = "api_integration"
    BILLING_CANCEL = "billing_cancel"
    SUPPORT_CONTACT = "support_contact"
    DATA_EXPORT = "data_export"
    PRODUCT_INFO = "product_info"
    UNKNOWN = "unknown"


@dataclass
class CustomerMessage:
    """Normalized customer message structure"""
    id: str
    channel: Channel
    customer_id: Optional[str]  # email for Gmail/WebForm, phone for WhatsApp
    customer_name: Optional[str]
    subject: Optional[str]  # Gmail only
    message: str
    timestamp: str
    sentiment: Optional[Sentiment]
    topic: Optional[Topic]
    priority: str = "normal"


@dataclass
class AgentResponse:
    """AI agent response structure"""
    message: str
    topic: Topic
    escalate: bool
    escalation_reason: Optional[str]
    confidence: float  # 0.0 to 1.0
    sources: List[str]  # Documentation sources used


# ============================================================================
# KNOWLEDGE BASE (Product Documentation)
# ============================================================================

class KnowledgeBase:
    """Simple in-memory knowledge base from product-docs.md"""

    def __init__(self):
        self.docs = self._load_docs()

    def _load_docs(self) -> Dict[Topic, List[str]]:
        """Load product documentation organized by topic"""
        return {
            Topic.INTEGRATION_SETUP: [
                "To connect an integration: Go to Settings > Integrations > Add Integration",
                "Select the app you want to connect and click 'Connect'",
                "Follow the OAuth authentication flow (requires admin permissions for some apps)",
                "50+ integrations available: Google Workspace, Microsoft 365, Slack, Discord, Teams, Salesforce, HubSpot, Pipedrive, Jira, Asana, Trello, Monday.com, Zapier, Make"
            ],
            Topic.WORKFLOW_TROUBLESHOOTING: [
                "Check if workflow is active (toggle should be ON)",
                "Verify trigger conditions are being met",
                "Check connected app API status page",
                "Review workflow error logs for specific issues",
                "For webhook triggers: Ensure external system is sending data to webhook URL",
                "Conditional logic: Use If/Then blocks for conditional paths"
            ],
            Topic.PRICING: [
                "Starter: $29/month - 5 users, 100 automations, basic integrations",
                "Professional: $79/month - 20 users, 500 automations, advanced integrations, priority support",
                "Enterprise: Custom - unlimited users, unlimited automations, custom integrations, dedicated support"
            ],
            Topic.BILLING_REFUND: [
                "Payment methods: Credit card (Visa, Mastercard, American Express), PayPal",
                "Enterprise plans can pay via invoice with Net-30 terms",
                "To upgrade/downgrade: Settings > Billing > Change Plan",
                "30-day money-back guarantee for new customers"
            ],
            Topic.SECURITY: [
                "TLS 1.3 encryption for all data in transit",
                "AES-256 encryption for data at rest",
                "SOC 2 Type II certified infrastructure",
                "US-East (Virginia) by default, EU option available (Frankfurt, Germany)",
                "Regular security audits by third-party firms"
            ],
            Topic.FEATURE_REQUEST: [
                "Thank feature requests warmly",
                "Suggest customer contact product team for feature requests",
                "Acknowledge feedback and encourage continued use"
            ],
            Topic.API_ACCESS: [
                "REST API available for Enterprise plans",
                "Use API to: create/manage workflows, trigger workflows, retrieve execution history",
                "Contact support for API documentation and access"
            ],
            Topic.LIMITS: [
                "Starter: 10 concurrent executions, 5min execution time",
                "Professional: 50 concurrent executions, 10min execution time",
                "Enterprise: unlimited executions, 30min execution time",
                "Individual steps can process up to 10MB of data"
            ],
            Topic.ONBOARDING: [
                "After signup: Click verification link in email",
                "Complete profile: Add company name and timezone",
                "Go to Workflows > Create New Workflow",
                "Select trigger, add actions, configure data mapping",
                "Test and activate workflow"
            ],
            Topic.DATA_TRANSFORMATION: [
                "Use 'Map Data' action to: rename fields, format dates, combine text, extract values, apply formulas",
                "For date transformation: Use formula functions for format conversion"
            ],
            Topic.WEBHOOK_SETUP: [
                "Create workflow with Webhook Trigger",
                "Copy webhook URL provided",
                "Configure external system to send data to this URL",
                "Authentication: May require API key depending on service",
                "Test webhook with sample data"
            ],
            Topic.BEST_PRACTICES: [
                "Start simple, then add complexity",
                "Name steps and variables clearly",
                "Add error handling at critical points",
                "Test with sample data before activating",
                "Monitor workflow execution logs",
                "Use filters early to reduce unnecessary processing"
            ],
            Topic.FEATURE_DISCOVERY: [
                "Conditional logic: If/Then blocks for branching",
                "Data transformation: Map Data action for formatting",
                "Error handling: Retry, Skip Step, Stop Workflow, Custom Error Path",
                "Looping: For Each action to process arrays",
                "Webhooks: Webhook Trigger for external data",
                "HTTP Requests: Custom REST API calls with various auth methods"
            ],
            Topic.BILLING_CYCLE: [
                "Billed monthly by default",
                "Annual billing available for discount",
                "Change billing cycle in Settings > Billing",
                "Changes take effect immediately with prorated charges"
            ],
            Topic.API_INTEGRATION: [
                "HTTP Request action can call any REST API",
                "Configure URL, method, headers, and body",
                "Authentication options: API key, OAuth 2.0, basic auth",
                "Custom OAuth 2.0: Supported via HTTP Request action"
            ],
            Topic.SUPPORT_CONTACT: [
                "Standard Support: Mon-Fri, 9 AM - 6 PM EST",
                "Priority Support: 24/7 for Professional and Enterprise plans",
                "Contact: support@techflow.io",
                "Average response time: 4-6 hours"
            ],
            Topic.DATA_EXPORT: [
                "Export workflow data via API (Enterprise)",
                "Download workflow execution logs from dashboard",
                "Contact support for bulk data export requests"
            ],
            Topic.PRODUCT_INFO: [
                "TechFlow: Unified workflow automation platform",
                "Helps businesses automate tasks, integrate apps, streamline collaboration",
                "Reduces manual data entry by 80%",
                "No mobile app currently (web-based only)"
            ]
        }

    def search(self, query: str, topic: Topic) -> List[str]:
        """Search knowledge base for relevant content"""
        return self.docs.get(topic, ["I don't have specific information about this topic. Please contact human support for more details."])


# ============================================================================
# ESCALATION RULES
# ============================================================================

class EscalationEngine:
    """Determines when to escalate to human support"""

    ESCALATION_TRIGGERS = {
        Topic.PRICING: "Custom pricing requires sales negotiation",
        Topic.BILLING_REFUND: "Refund requests require billing team approval",
        Topic.LEGAL: "Legal matters require qualified legal professionals",
        Topic.BILLING_CANCEL: "Cancellations require account management review",
        Topic.ENTERPRISE_FEATURES: "Enterprise features require solutions engineering"
    }

    PROFANITY_KEYWORDS = [
        "f***", "damn", "sh*t", "b*tch", "a**", "hell",
        "fuck", "shit", "bitch", "ass"
    ]

    def check_escalation(self, message: str, topic: Topic) -> Tuple[bool, Optional[str]]:
        """Check if message should be escalated"""
        message_lower = message.lower()

        # Check for profanity
        for keyword in self.PROFANITY_KEYWORDS:
            if keyword in message_lower:
                return True, "Profanity or abusive language detected - requires human intervention"

        # Check for escalation triggers by topic
        if topic in self.ESCALATION_TRIGGERS:
            return True, self.ESCALATION_TRIGGERS[topic]

        return False, None


# ============================================================================
# INTENT RECOGNITION
# ============================================================================

class IntentRecognizer:
    """Identifies customer intent/topic from message"""

    KEYWORDS = {
        Topic.INTEGRATION_SETUP: [
            "connect", "integration", "oauth", "authenticate", "set up", "link",
            "available integrations", "how many integrations", "integrate with"
        ],
        Topic.WORKFLOW_TROUBLESHOOTING: [
            "workflow not working", "workflow not triggering", "failed", "error",
            "troubleshoot", "not working", "fix", "broken", "issue"
        ],
        Topic.PRICING: [
            "pricing", "price", "cost", "custom pricing", "discuss pricing",
            "enterprise pricing", "deal", "discount"
        ],
        Topic.BILLING_REFUND: [
            "refund", "request refund", "money back", "billing", "invoice",
            "upgrade", "downgrade", "change plan", "trial expired"
        ],
        Topic.SECURITY: [
            "security", "data protection", "encryption", "soc 2", "certification",
            "where is data stored", "compliance", "hipaa", "gdpr"
        ],
        Topic.FEATURE_REQUEST: [
            "feature request", "would be helpful if", "can you add",
            "wish", "suggestion", "improvement"
        ],
        Topic.API_ACCESS: [
            "api", "rest api", "programmatic", "webhook authentication"
        ],
        Topic.LIMITS: [
            "limit", "maximum", "how many", "execution limit", "concurrent",
            "quota", "not enough"
        ],
        Topic.ONBOARDING: [
            "getting started", "beginner", "new user", "first workflow",
            "don't know where to begin", "setup guide", "quick start"
        ],
        Topic.DATA_TRANSFORMATION: [
            "transform", "format date", "map data", "convert", "formula",
            "array", "batch", "multiple records"
        ],
        Topic.WEBHOOK_SETUP: [
            "webhook", "webhook url", "signature", "verify webhook"
        ],
        Topic.BEST_PRACTICES: [
            "best practice", "how to", "optimize", "reduce cost",
            "efficient", "performance"
        ],
        Topic.FEATURE_DISCOVERY: [
            "can i", "is there", "do you have", "feature", "available",
            "does it support", "how to use"
        ],
        Topic.SUPPORT_CONTACT: [
            "contact support", "human support", "real person", "support hours",
            "how to contact"
        ],
        Topic.DATA_EXPORT: [
            "export", "download", "backup", "get my data"
        ],
        Topic.PRODUCT_INFO: [
            "what is", "mobile app", "techflow", "platform", "about"
        ],
        Topic.FEEDBACK: [
            "thank", "great", "awesome", "love", "works perfectly",
            "amazing", "helpful", "appreciate"
        ],
        Topic.LEGAL: [
            "legal", "terms of service", "contract", "compliance", "data ownership",
            "baa", "business associate agreement"
        ],
        Topic.ENTERPRISE_FEATURES: [
            "enterprise", "white-label", "sso", "saml", "on-premise",
            "dedicated support", "custom branding"
        ],
        Topic.BILLING_CYCLE: [
            "billing cycle", "when am i billed", "monthly", "annually"
        ],
        Topic.API_INTEGRATION: [
            "custom api", "rest api", "oauth 2.0", "api integration",
            "custom authentication"
        ],
        Topic.BILLING_CANCEL: [
            "cancel", "cancel subscription", "terminate", "close account"
        ],
        Topic.SYSTEM_ISSUE: [
            "spinning", "not saving", "crash", "slow", "system error"
        ]
    }

    def recognize(self, message: str) -> Topic:
        """Identify topic from message using keyword matching"""
        message_lower = message.lower()

        # Count keyword matches for each topic
        scores = {}
        for topic, keywords in self.KEYWORDS.items():
            score = sum(1 for keyword in keywords if keyword in message_lower)
            if score > 0:
                scores[topic] = score

        # Return topic with highest score, or UNKNOWN
        if scores:
            return max(scores, key=scores.get)
        return Topic.UNKNOWN


# ============================================================================
# CHANNEL-AWARE RESPONSE GENERATOR
# ============================================================================

class ResponseGenerator:
    """Generates responses adapted to channel characteristics"""

    def generate(self,
                topic: Topic,
                knowledge: List[str],
                channel: Channel,
                customer_name: Optional[str] = None,
                escalate: bool = False,
                escalation_reason: Optional[str] = None) -> Tuple[str, float]:
        """
        Generate channel-appropriate response

        Returns: (response_message, confidence_score)
        """

        # Determine escalation
        if escalate and escalation_reason:
            return self._generate_escalation_response(channel, escalation_reason), 1.0

        # Generate channel-appropriate response
        if channel == Channel.GMAIL:
            return self._generate_gmail_response(topic, knowledge, customer_name), 0.85
        elif channel == Channel.WHATSAPP:
            return self._generate_whatsapp_response(topic, knowledge), 0.85
        else:  # WEBFORM
            return self._generate_webform_response(topic, knowledge), 0.85

    def _generate_gmail_response(self, topic: Topic, knowledge: List[str], customer_name: Optional[str]) -> str:
        """Formal, structured email response"""
        greeting = f"Dear {customer_name}," if customer_name else "Hello,"
        salutation = "Best regards,\nTechFlow Support Team"

        body_parts = []

        # Add acknowledgment
        body_parts.append(f"Thank you for reaching out to TechFlow support. I'd be happy to help you with {topic.value.replace('_', ' ')}.")

        # Add knowledge content
        if knowledge:
            body_parts.append("\nHere's what I found:")
            for i, info in enumerate(knowledge, 1):
                body_parts.append(f"{i}. {info}")

        # Add closing offer
        body_parts.append("\nIs there anything else I can help you with?")

        return f"{greeting}\n\n{''.join(body_parts)}\n\n{salutation}"

    def _generate_whatsapp_response(self, topic: Topic, knowledge: List[str]) -> str:
        """Casual, concise WhatsApp response"""
        intro = "Hey! I can help with that! 🎉\n\n"

        # Add knowledge (limited to 2 key points)
        body = ""
        if knowledge:
            body = "Here's the info:\n"
            for i, info in enumerate(knowledge[:2], 1):
                # Shorten for WhatsApp
                short_info = info.split('.')[0] + '.'
                body += f"{i}. {short_info}\n"

        closing = "Need more details? Just ask! 😊"

        return intro + body + closing

    def _generate_webform_response(self, topic: Topic, knowledge: List[str]) -> str:
        """Semi-formal web form response"""
        greeting = "Hello! Thank you for contacting TechFlow support.\n\n"

        body_parts = []

        # Add acknowledgment
        body_parts.append(f"I can help you with {topic.value.replace('_', ' ')}.\n")

        # Add knowledge with bullet points
        if knowledge:
            body_parts.append("**What You Need to Know:**\n")
            for info in knowledge[:3]:
                body_parts.append(f"- {info}\n")

        # Add closing
        body_parts.append("Let me know if you need more details!")

        return greeting + ''.join(body_parts)

    def _generate_escalation_response(self, channel: Channel, reason: str) -> str:
        """Generate escalation response based on channel"""

        if channel == Channel.GMAIL:
            return f"""Dear Customer,

I understand your request regarding: {reason}

This requires specialized expertise, so I'm escalating this to our appropriate team who can provide you with accurate assistance.

A team member will respond within 1-2 business days.

Best regards,
TechFlow Support Team"""
        elif channel == Channel.WHATSAPP:
            return f"""Hey! I see you need help with: {reason}

I'm connecting you to our team who can handle this! Someone will reach out soon.

Thanks for your patience! 😊"""
        else:  # WEBFORM
            return f"""Hello! Thank you for contacting TechFlow.

I understand you need assistance with: {reason}

This requires specialized attention. I've escalated your request to our team who will respond within 1-2 business days.

We appreciate your patience!"""


# ============================================================================
# CORE AGENT LOOP
# ============================================================================

class DigitalFTETAgent:
    """Main AI agent for customer success"""

    def __init__(self):
        self.knowledge_base = KnowledgeBase()
        self.intent_recognizer = IntentRecognizer()
        self.escalation_engine = EscalationEngine()
        self.response_generator = ResponseGenerator()

    def process_message(self, message: CustomerMessage) -> AgentResponse:
        """
        Process customer message through core loop:
        1. Recognize intent/topic
        2. Check escalation rules
        3. Search knowledge base
        4. Generate response
        5. Format for channel
        """

        print(f"\n{'='*60}")
        print(f"PROCESSING MESSAGE: {message.id}")
        print(f"Channel: {message.channel.value}")
        print(f"Customer: {message.customer_name or 'Unknown'}")
        print(f"Message: {message.message[:50]}...")
        print(f"{'='*60}\n")

        # Step 1: Recognize intent/topic
        print("Step 1: Recognizing intent...")
        topic = self.intent_recognizer.recognize(message.message)
        print(f"  → Identified topic: {topic.value}\n")

        # Step 2: Check escalation rules
        print("Step 2: Checking escalation rules...")
        escalate, escalation_reason = self.escalation_engine.check_escalation(
            message.message, topic
        )
        print(f"  → Escalate: {escalate}")
        if escalate:
            print(f"  → Reason: {escalation_reason}\n")
        else:
            print(f"  → No escalation needed\n")

        # Step 3: Search knowledge base (only if not escalating)
        knowledge = []
        if not escalate:
            print("Step 3: Searching knowledge base...")
            knowledge = self.knowledge_base.search(message.message, topic)
            print(f"  → Found {len(knowledge)} relevant items\n")
        else:
            print("Step 3: Skipping knowledge search (escalating)\n")

        # Step 4: Generate response
        print("Step 4: Generating response...")
        response_text, confidence = self.response_generator.generate(
            topic=topic,
            knowledge=knowledge,
            channel=message.channel,
            customer_name=message.customer_name,
            escalate=escalate,
            escalation_reason=escalation_reason
        )
        print(f"  → Response length: {len(response_text)} words\n")

        # Step 5: Format for channel (already done in generate)
        print("Step 5: Response formatted for channel ✅\n")

        return AgentResponse(
            message=response_text,
            topic=topic,
            escalate=escalate,
            escalation_reason=escalation_reason,
            confidence=confidence,
            sources=["product-docs.md"]
        )


# ============================================================================
# MESSAGE NORMALIZATION
# ============================================================================

class MessageNormalizer:
    """Normalizes messages from different channels to standard format"""

    def normalize(self, raw_data: Dict) -> CustomerMessage:
        """Convert raw channel data to CustomerMessage"""

        channel = Channel(raw_data["channel"])
        customer_id = raw_data.get("customer_email") or raw_data.get("customer_phone")

        return CustomerMessage(
            id=raw_data["id"],
            channel=channel,
            customer_id=customer_id,
            customer_name=raw_data.get("customer_name"),
            subject=raw_data.get("subject"),
            message=raw_data["message"],
            timestamp=raw_data["timestamp"],
            sentiment=None,  # Will be added in Exercise 1.3
            topic=None  # Will be determined by agent
        )


# ============================================================================
# DEMO / TESTING
# ============================================================================

def load_sample_tickets() -> List[Dict]:
    """Load sample tickets from context/sample-tickets.json"""
    with open("context/sample-tickets.json", "r") as f:
        data = json.load(f)
        return data["tickets"]


def demo():
    """Run demo with sample tickets"""
    print("\n" + "="*60)
    print("DIGITAL FTE PROTOTYPE - CORE LOOP DEMO")
    print("="*60 + "\n")

    # Initialize agent
    agent = DigitalFTETAgent()
    normalizer = MessageNormalizer()

    # Load sample tickets
    tickets = load_sample_tickets()

    # Process a few sample tickets from each channel
    sample_indices = [
        0,   # G001 - Gmail: Integration setup
        1,   # G002 - Gmail: Troubleshooting (frustrated)
        2,   # G003 - Gmail: Pricing (escalate)
        12,  # W001 - WhatsApp: Troubleshooting
        13,  # W002 - WhatsApp: Pricing (escalate)
        2,   # W003 - WhatsApp: Positive feedback
        25,  # F001 - Web Form: Integration troubleshooting
        26,  # F002 - Web Form: Onboarding
        4,   # F004 - Gmail: Refund (escalate)
    ]

    for idx in sample_indices:
        if idx >= len(tickets):
            continue

        raw_ticket = tickets[idx]
        message = normalizer.normalize(raw_ticket)

        # Process through agent
        response = agent.process_message(message)

        # Display response
        print(f"\n{'='*60}")
        print(f"RESPONSE FOR {raw_ticket['channel'].upper()} TICKET {raw_ticket['id']}")
        print(f"{'='*60}\n")
        print(response.message)
        print("\n")

        # Ask user to continue
        if idx != sample_indices[-1]:
            input("Press Enter to continue to next example...")

    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60 + "\n")


if __name__ == "__main__":
    demo()

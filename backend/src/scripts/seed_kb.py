"""
Seed script to populate the knowledge base with real-quality documentation.
Ensures the AI agent has a grounded, non-hallucinated source of truth.
"""
import asyncio
import logging
from src.services.doc_search import DocumentSearchService
from src.database.connection import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DOCS = [
    {
        "title": "Universal Digital FTE - Overview",
        "category": "General",
        "content": """
        Universal Digital FTE is a next-generation autonomous workforce solution. 
        It provides AI-powered agents that operate 24/7 across multiple channels: Web, Email, and WhatsApp.
        Our focus is on humanized interactions, zero-hallucination support, and seamless CRM integration.
        Platform features include:
        - Autonomous pipeline management
        - Semantic lead scoring
        - Cross-channel customer identification using pgvector
        - Dead-letter-queue for zero message loss
        """.strip()
    },
    {
        "title": "Subscription Plans and Pricing",
        "category": "Billing",
        "content": """
        We offer three primary tiers of service:
        1. Professional: $49/month. Includes 1 Digital FTE, standard response times (under 5 mins), and Web/Email support.
        2. Enterprise: $199/month. Includes 5 Digital FTEs, priority response times (under 1 min), and full WhatsApp integration.
        3. Custom: Contact sales. Unlimited scale, private cloud deployment, and custom LLM fine-tuning.
        All plans include our core autonomous CRM features and pgvector semantic search.
        """.strip()
    },
    {
        "title": "Security and Data Privacy",
        "category": "Compliance",
        "content": """
        Universal Digital FTE takes security seriously. 
        - Data Encryption: All data is encrypted at rest using AES-256 and in transit via TLS 1.3.
        - Privacy: We are SOC2 and GDPR compliant. 
        - Isolation: Each tenant's data is logically isolated in the database.
        - No Training: We do not use customer data to train global LLM models; your intellectual property remains yours.
        """.strip()
    },
    {
        "title": "API Rate Limits and Technical Specs",
        "category": "Technical",
        "content": """
        - API Rate Limit: 1,000 requests per hour per tenant on Professional, 10,000 on Enterprise.
        - Supported LLMs: GPT-4o, GPT-4o-mini (default for sentiment and fast tasks), and Claude 3.5 Sonnet.
        - Response Latency: Average response processing time is < 3 seconds.
        - Database: PostgreSQL with pgvector for efficient semantic search.
        """.strip()
    },
    {
        "title": "Refund Policy",
        "category": "Billing",
        "content": """
        We provide a 14-day 'no questions asked' refund policy for new subscriptions. 
        After 14 days, refunds are handled on a case-by-case basis through our billing department. 
        To request a refund, please contact billing@digitalfte.ai or use the escalation tool to speak with a human agent.
        """.strip()
    }
]

async def seed():
    logger.info("Initializing database...")
    await init_db()
    
    search_service = DocumentSearchService()
    
    logger.info("Seeding knowledge base...")
    for doc in DOCS:
        success = await search_service.add_document(
            title=doc["title"],
            content=doc["content"],
            category=doc["category"],
            source="Official Documentation"
        )
        if success:
            logger.info(f"Added: {doc['title']}")
        else:
            logger.error(f"Failed to add: {doc['title']}")

    logger.info("Knowledge base seeding complete.")

if __name__ == "__main__":
    asyncio.run(seed())

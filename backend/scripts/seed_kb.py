import asyncio
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.services.doc_search import DocumentSearchService
from src.database.connection import init_db

async def seed():
    print("Initializing DB...")
    await init_db()
    
    search_service = DocumentSearchService()
    
    docs = [
        {
            "title": "Digital FTE Overview",
            "content": "Digital FTE is an AI-powered Customer Success Platform that works 24/7 to handle customer inquiries, manage deals, and track tasks autonomously.",
            "category": "general"
        },
        {
            "title": "Pricing & Plans",
            "content": "We offer three tiers: Basic (Free), Pro ($49/mo), and Enterprise (Custom). The Basic plan includes 1 AI agent and 1000 messages/mo.",
            "category": "pricing"
        },
        {
            "title": "Technical Integration",
            "content": "To integrate the webhook, point your WhatsApp or Email provider to our /api/v1/inquiries endpoint with your API key in the headers.",
            "category": "technical"
        },
        {
            "title": "Escalation Policy",
            "content": "The AI will automatically escalate to a human manager if the customer mentions 'legal', 'refund', or uses abusive language.",
            "category": "policy"
        }
    ]
    
    print(f"Seeding {len(docs)} documents into Knowledge Base...")
    for doc in docs:
        success = await search_service.add_document(
            title=doc["title"],
            content=doc["content"],
            category=doc["category"]
        )
        if success:
            print(f"✅ Seeded: {doc['title']}")
        else:
            print(f"❌ Failed: {doc['title']}")

if __name__ == "__main__":
    asyncio.run(seed())

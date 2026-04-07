"""
Transition and escalation tests for the Digital FTE agent.
Ensures the system correctly transitions from AI to human support when escalation triggers are hit.
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app

@pytest.fixture
async def client():
    """Create an async test client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_escalation_trigger_on_profanity(client):
    """Test that profanity triggers immediate escalation and human handover."""
    inquiry_data = {
        'channel': 'whatsapp',
        'customer_phone': '+1234567890',
        'message': 'This service is fucking terrible, let me talk to a human!'
    }

    response = await client.post("/api/inquiries", json=inquiry_data)
    assert response.status_code == 200
    data = response.json()
    
    # Check that escalation was triggered (look for keywords or status in response)
    # The AI (if properly instructed) should acknowledge handover.
    # We also check the database state for the ticket.
    ticket_id = data.get('ticket_id')
    assert ticket_id is not None
    
    # Retrieve the ticket to verify 'escalated' status
    ticket_response = await client.get(f"/api/tickets/{ticket_id}")
    ticket_data = ticket_response.json()
    
    assert ticket_data['status'] in ['escalated', 'human_required', 'pending_human'] or \
           'human' in ticket_data['ai_response'].lower() or \
           'escalated' in ticket_data['ai_response'].lower()

@pytest.mark.asyncio
async def test_escalation_on_refund_request(client):
    """Test that refund requests are escalated (no pricing/refund authorization)."""
    inquiry_data = {
        'channel': 'email',
        'customer_email': 'buyer@example.com',
        'subject': 'Refund Question',
        'message': 'I want a refund for my last invoice #12345.'
    }

    response = await client.post("/api/inquiries", json=inquiry_data)
    assert response.status_code == 200
    data = response.json()
    
    ticket_id = data.get('ticket_id')
    ticket_response = await client.get(f"/api/tickets/{ticket_id}")
    ticket_data = ticket_response.json()
    
    # AI should not process refund but escalate
    assert any(keyword in ticket_data['ai_response'].lower() for keyword in ['manager', 'human', 'transfer', 'escalate'])

@pytest.mark.asyncio
async def test_cross_channel_context_restoration(client):
    """Test that context is restored across channels (US2)."""
    # 1. Start on WhatsApp
    wa_inquiry = {
        'channel': 'whatsapp',
        'customer_phone': '+19998887777',
        'message': 'Hi, I am having trouble with my API key for the Slack integration.'
    }
    await client.post("/api/inquiries", json=wa_inquiry)
    
    # 2. Switch to Email
    email_inquiry = {
        'channel': 'email',
        'customer_email': 'user@example.com', # Assuming customer identifier connects phone+email or use same session_id/customer_id
        'customer_phone': '+19998887777',
        'subject': 'Following up',
        'message': 'Just to add, the error code I see is 403. Any update?'
    }
    
    response = await client.post("/api/inquiries", json=email_inquiry)
    assert response.status_code == 200
    data = response.json()
    
    # AI should acknowledge the Slack context from previous channel
    ticket_id = data.get('ticket_id')
    ticket_response = await client.get(f"/api/tickets/{ticket_id}")
    ai_response = ticket_response.json()['ai_response'].lower()
    
    assert 'slack' in ai_response or 'api key' in ai_response, f"AI forgot context from WhatsApp: {ai_response}"

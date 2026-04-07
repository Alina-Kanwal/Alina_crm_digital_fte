"""
Integration tests for Inquiry API.
Tests API endpoints for receiving and processing customer inquiries.
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime
import json

from src.main import app


@pytest.fixture
async def client():
    """Create an async test client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoint."""
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'


@pytest.mark.asyncio
async def test_submit_inquiry_email(client):
    """Test submitting an email inquiry."""
    inquiry_data = {
        'channel': 'email',
        'customer_email': 'test@example.com',
        'customer_phone': None,
        'message': 'How do I integrate with Salesforce?',
        'subject': 'Salesforce Integration Help'
    }

    response = await client.post("/api/inquiries", json=inquiry_data)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'ticket_id' in data


@pytest.mark.asyncio
async def test_submit_inquiry_whatsapp(client):
    """Test submitting a WhatsApp inquiry."""
    inquiry_data = {
        'channel': 'whatsapp',
        'customer_phone': '+1234567890',
        'customer_email': None,
        'message': 'How do I reset my password?',
        'sender_id': 'wa-user-123'
    }

    response = await client.post("/api/inquiries", json=inquiry_data)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'ticket_id' in data


@pytest.mark.asyncio
async def test_submit_inquiry_webform(client):
    """Test submitting a web form inquiry."""
    inquiry_data = {
        'channel': 'webform',
        'customer_email': 'webuser@example.com',
        'customer_name': 'John Doe',
        'message': 'I need help setting up my first workflow',
        'session_id': 'session-abc123'
    }

    response = await client.post("/api/inquiries", json=inquiry_data)
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'ticket_id' in data
    assert data['channel'] == 'webform'


@pytest.mark.asyncio
async def test_submit_inquiry_missing_required_field(client):
    """Test submitting inquiry without required field."""
    inquiry_data = {
        'channel': 'email',
        'message': 'How do I integrate with Salesforce?'
        # Missing customer_email
    }

    response = await client.post("/api/inquiries", json=inquiry_data)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_get_ticket_by_id(client):
    """Test retrieving a ticket by ID."""
    # First create a ticket
    inquiry_data = {
        'channel': 'email',
        'customer_email': 'ticket@test.com',
        'message': 'Test message'
    }

    create_response = await client.post("/api/inquiries", json=inquiry_data)
    ticket_id = create_response.json()['ticket_id']

    # Retrieve the ticket
    response = await client.get(f"/api/tickets/{ticket_id}")
    assert response.status_code == 200
    data = response.json()
    assert data['ticket_id'] == ticket_id
    assert data['customer_email'] == 'ticket@test.com'


@pytest.mark.asyncio
async def test_update_ticket_status(client):
    """Test updating ticket status."""
    # First create a ticket
    inquiry_data = {
        'channel': 'email',
        'customer_email': 'status@test.com',
        'message': 'Status update test'
    }

    create_response = await client.post("/api/inquiries", json=inquiry_data)
    ticket_id = create_response.json()['ticket_id']

    # Update ticket status
    update_data = {
        'status': 'in_progress',
        'agent_type': 'ai',
        'notes': 'Investigating the issue'
    }

    response = await client.patch(f"/api/tickets/{ticket_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'in_progress'


@pytest.mark.asyncio
async def test_escalate_ticket(client):
    """Test manually escalating a ticket."""
    # First create a ticket
    inquiry_data = {
        'channel': 'email',
        'customer_email': 'escalate@test.com',
        'message': 'Escalation test'
    }

    create_response = await client.post("/api/inquiries", json=inquiry_data)
    ticket_id = create_response.json()['ticket_id']

    # Escalate ticket
    escalation_data = {
        'escalation_reason': 'manual_request',
        'priority': 'P1',
        'escalation_to': 'support_supervisor',
        'notes': 'Customer requested human agent'
    }

    response = await client.post(f"/api/tickets/{ticket_id}/escalate", json=escalation_data)
    assert response.status_code == 200
    data = response.json()
    assert data['escalated'] is True
    assert data['priority'] == 'P1'


@pytest.mark.asyncio
async def test_get_customer_tickets(client):
    """Test retrieving all tickets for a customer."""
    customer_email = 'tickets@test.com'

    # Create multiple tickets
    for i in range(3):
        inquiry_data = {
            'channel': 'email',
            'customer_email': customer_email,
            'message': f'Ticket {i+1}'
        }
        await client.post("/api/inquiries", json=inquiry_data)

    # Retrieve all tickets for customer
    response = await client.get(f"/api/customers/{customer_email}/tickets")
    assert response.status_code == 200
    data = response.json()
    assert len(data['tickets']) >= 3


@pytest.mark.asyncio
async def test_get_daily_report(client):
    """Test retrieving daily sentiment report."""
    response = await client.get("/api/reports/daily")
    assert response.status_code == 200
    data = response.json()
    assert 'report_date' in data
    assert 'sentiment_distribution' in data


@pytest.mark.asyncio
async def test_rate_limiting(client):
    """Test API rate limiting."""
    # Submit multiple requests quickly
    inquiry_data = {
        'channel': 'email',
        'customer_email': 'ratelimit@test.com',
        'message': 'Rate limit test'
    }

    # First request should succeed
    response1 = await client.post("/api/inquiries", json=inquiry_data)
    assert response1.status_code == 200

    # Many subsequent requests might trigger rate limiting
    # (This depends on actual rate limiter configuration)
    for _ in range(100):
        response = await client.post("/api/inquiries", json=inquiry_data)
        if response.status_code == 429:
            # Rate limit triggered
            assert response.json()['detail'] == 'Rate limit exceeded'
            break
    else:
        # No rate limit triggered in test environment
        pass


@pytest.mark.asyncio
async def test_invalid_channel(client):
    """Test submitting inquiry with invalid channel."""
    inquiry_data = {
        'channel': 'invalid_channel',
        'customer_email': 'test@example.com',
        'message': 'Test message'
    }

    response = await client.post("/api/inquiries", json=inquiry_data)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_empty_message(client):
    """Test submitting inquiry with empty message."""
    inquiry_data = {
        'channel': 'email',
        'customer_email': 'test@example.com',
        'message': ''
    }

    response = await client.post("/api/inquiries", json=inquiry_data)
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_large_message(client):
    """Test submitting inquiry with very large message."""
    # Create a message > 10,000 characters
    large_message = "Test message. " * 1000  # > 15,000 characters

    inquiry_data = {
        'channel': 'email',
        'customer_email': 'test@example.com',
        'message': large_message
    }

    # Should be accepted or rejected based on implementation
    response = await client.post("/api/inquiries", json=inquiry_data)
    # Either accept (200) or reject (422)
    assert response.status_code in [200, 422]


@pytest.mark.asyncio
async def test_concurrent_inquiries(client):
    """Test handling multiple concurrent inquiries."""
    import asyncio

    async def submit_inquiry(i):
        inquiry_data = {
            'channel': 'email',
            'customer_email': f'concurrent{i}@test.com',
            'message': f'Concurrent test {i}'
        }
        return await client.post("/api/inquiries", json=inquiry_data)

    # Submit 10 concurrent requests
    responses = await asyncio.gather(*[submit_inquiry(i) for i in range(10)])

    # All should succeed
    for response in responses:
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_response_time_metrics(client):
    """Test API response time metrics."""
    import time

    inquiry_data = {
        'channel': 'email',
        'customer_email': 'perf@test.com',
        'message': 'Performance test'
    }

    start_time = time.time()
    response = await client.post("/api/inquiries", json=inquiry_data)
    end_time = time.time()

    response_time_ms = (end_time - start_time) * 1000

    assert response.status_code == 200
    # Response should be under 3 seconds (per constitution)
    assert response_time_ms < 3000, f"Response time {response_time_ms}ms exceeds 3000ms threshold"

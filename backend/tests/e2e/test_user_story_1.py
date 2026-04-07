"""
End-to-End tests for User Story 1: Multi-Channel Customer Inquiry Handling.
Tests the complete flow from customer inquiry through AI response across all channels.
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime
import time

from src.main import app


@pytest.fixture
async def client():
    """Create an async test client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_email_inquiry_complete_flow(client):
    """
    Test complete email inquiry flow:
    1. Customer sends email inquiry
    2. System processes and analyzes
    3. AI generates appropriate response
    4. Response is sent back to email channel
    """
    # Step 1: Submit email inquiry
    inquiry_data = {
        'channel': 'email',
        'customer_email': 'email@example.com',
        'subject': 'Integration Help Needed',
        'message': 'I need help setting up the Slack integration. I have the API key but keep getting authentication errors.'
    }

    start_time = time.time()
    response = await client.post("/api/inquiries", json=inquiry_data)
    response_time = (time.time() - start_time) * 1000

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'ticket_id' in data
    assert data['channel'] == 'email'

    # Verify response time (target: <3s)
    assert response_time < 3000, f"Response time {response_time}ms exceeds 3000ms threshold"

    # Step 2: Retrieve ticket and verify AI response
    ticket_id = data['ticket_id']
    ticket_response = await client.get(f"/api/tickets/{ticket_id}")
    assert ticket_response.status_code == 200

    ticket_data = ticket_response.json()
    assert ticket_data['status'] in ['open', 'in_progress']
    assert ticket_data['customer_email'] == 'email@example.com'
    assert 'ai_response' in ticket_data

    # Verify response is appropriate for email channel (formal tone)
    ai_response = ticket_data['ai_response']
    assert len(ai_response) > 50  # Email responses should be detailed
    assert any(greeting in ai_response.lower() for greeting in ['dear', 'hello', 'hi'])


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_whatsapp_inquiry_complete_flow(client):
    """
    Test complete WhatsApp inquiry flow:
    1. Customer sends WhatsApp message
    2. System processes and analyzes
    3. AI generates appropriate casual response
    4. Response is sent back to WhatsApp channel
    """
    # Step 1: Submit WhatsApp inquiry
    inquiry_data = {
        'channel': 'whatsapp',
        'customer_phone': '+1234567890',
        'message': 'How do I create a new workflow?',
        'sender_id': 'wa-user-123'
    }

    start_time = time.time()
    response = await client.post("/api/inquiries", json=inquiry_data)
    response_time = (time.time() - start_time) * 1000

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'ticket_id' in data
    assert data['channel'] == 'whatsapp'

    # Verify response time (target: <2s for WhatsApp)
    assert response_time < 2000, f"Response time {response_time}ms exceeds 2000ms threshold"

    # Step 2: Retrieve ticket and verify AI response
    ticket_id = data['ticket_id']
    ticket_response = await client.get(f"/api/tickets/{ticket_id}")
    assert ticket_response.status_code == 200

    ticket_data = ticket_response.json()
    assert ticket_data['status'] in ['open', 'in_progress']

    # Verify response is appropriate for WhatsApp channel (casual, concise)
    ai_response = ticket_data['ai_response']
    assert len(ai_response) < 150  # WhatsApp responses should be short
    assert len(ai_response) > 20  # But not too short


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_webform_inquiry_complete_flow(client):
    """
    Test complete web form inquiry flow:
    1. Customer submits web support form
    2. System processes and analyzes
    3. AI generates appropriate semi-formal response
    4. Response is displayed in web form
    """
    # Step 1: Submit web form inquiry
    inquiry_data = {
        'channel': 'webform',
        'customer_email': 'webform@example.com',
        'customer_name': 'Jane Smith',
        'message': 'I\'m trying to set up automation triggers but the workflow doesn\'t seem to be triggering. I\'ve checked the conditions and they appear correct.',
        'session_id': 'web-session-123'
    }

    start_time = time.time()
    response = await client.post("/api/inquiries", json=inquiry_data)
    response_time = (time.time() - start_time) * 1000

    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert 'ticket_id' in data
    assert data['channel'] == 'webform'

    # Verify response time (target: <3s)
    assert response_time < 3000, f"Response time {response_time}ms exceeds 3000ms threshold"

    # Step 2: Retrieve ticket and verify AI response
    ticket_id = data['ticket_id']
    ticket_response = await client.get(f"/api/tickets/{ticket_id}")
    assert ticket_response.status_code == 200

    ticket_data = ticket_response.json()
    assert ticket_data['status'] in ['open', 'in_progress']
    assert ticket_data['customer_email'] == 'webform@example.com'

    # Verify response is appropriate for web form (semi-formal, balanced)
    ai_response = ticket_data['ai_response']
    assert 100 < len(ai_response) < 300  # Web form responses should be moderate length


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_high_throughput_webform_submissions(client):
    """
    Test handling 100+ simultaneous web form submissions (Constitution FR-027).
    Verifies system can handle peak load without message loss.
    """
    import asyncio

    async def submit_webform(i):
        inquiry_data = {
            'channel': 'webform',
            'customer_email': f'user{i}@loadtest.com',
            'customer_name': f'User {i}',
            'message': f'Load test message {i}: How do I use the API?',
            'session_id': f'session-{i}'
        }
        return await client.post("/api/inquiries", json=inquiry_data)

    # Submit 100 concurrent web form submissions
    start_time = time.time()
    responses = await asyncio.gather(*[submit_webform(i) for i in range(100)])
    end_time = time.time()

    # Verify all requests were handled
    successful_responses = [r for r in responses if r.status_code == 200]
    assert len(successful_responses) >= 95, "At least 95% of requests should succeed"

    # Verify no message loss (all tickets created)
    ticket_ids = [r.json()['ticket_id'] for r in successful_responses if r.json().get('ticket_id')]
    assert len(ticket_ids) >= 95, "At least 95% of tickets should be created"

    # Verify throughput (should handle 100 requests in reasonable time)
    processing_time = end_time - start_time
    assert processing_time < 60, f"Should process 100 requests in <60 seconds, took {processing_time}s"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_product_documentation_search(client):
    """
    Test that AI searches product documentation and provides accurate answers.
    Verifies >80% relevance score requirement.
    """
    # Submit inquiry that requires documentation search
    inquiry_data = {
        'channel': 'email',
        'customer_email': 'docs@example.com',
        'subject': 'OAuth Setup',
        'message': 'What are the steps to configure OAuth authentication for the Slack integration? I have my client ID and secret ready.'
    }

    response = await client.post("/api/inquiries", json=inquiry_data)
    assert response.status_code == 200

    ticket_id = response.json()['ticket_id']

    # Wait for processing and get ticket details
    await asyncio.sleep(2)
    ticket_response = await client.get(f"/api/tickets/{ticket_id}")
    ticket_data = ticket_response.json()

    # Verify AI response contains documentation-based answer
    ai_response = ticket_data['ai_response']
    assert 'oauth' in ai_response.lower() or 'authentication' in ai_response.lower()

    # Verify documentation search was performed
    assert 'doc_relevance_score' in ticket_data
    assert ticket_data['doc_relevance_score'] >= 0.8, "Documentation search relevance must be >=80%"


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_sentiment_analysis_on_inquiry(client):
    """
    Test that sentiment is analyzed and stored for each inquiry.
    Verifies sentiment analysis with confidence scores.
    """
    # Submit inquiry with positive sentiment
    inquiry_data = {
        'channel': 'email',
        'customer_email': 'positive@example.com',
        'subject': 'Great Service!',
        'message': 'I\'m really impressed with the product so far! The integration was easy and everything works great. Thank you!'
    }

    response = await client.post("/api/inquiries", json=inquiry_data)
    assert response.status_code == 200

    ticket_id = response.json()['ticket_id']

    # Verify sentiment analysis was performed
    ticket_response = await client.get(f"/api/tickets/{ticket_id}")
    ticket_data = ticket_response.json()

    assert 'sentiment' in ticket_data
    assert ticket_data['sentiment'] in ['positive', 'neutral', 'negative']
    assert 'sentiment_score' in ticket_data
    assert 0.0 <= ticket_data['sentiment_score'] <= 1.0


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_channel_specific_tone_adaptation(client):
    """
    Test that AI adapts tone for each communication channel.
    """
    test_cases = [
        {
            'channel': 'email',
            'message': 'How do I set up the integration?',
            'expected_tone': 'formal',
            'min_length': 100,
            'max_length': 600
        },
        {
            'channel': 'whatsapp',
            'message': 'How do I set up integration?',
            'expected_tone': 'casual',
            'min_length': 20,
            'max_length': 150
        },
        {
            'channel': 'webform',
            'message': 'I need help setting up the integration',
            'expected_tone': 'semi-formal',
            'min_length': 100,
            'max_length': 300
        }
    ]

    for test_case in test_cases:
        inquiry_data = {
            'channel': test_case['channel'],
            'customer_email': f'{test_case["channel"]}@tone.com',
            'message': test_case['message']
        }

        response = await client.post("/api/inquiries", json=inquiry_data)
        assert response.status_code == 200

        ticket_id = response.json()['ticket_id']
        ticket_response = await client.get(f"/api/tickets/{ticket_id}")
        ticket_data = ticket_response.json()

        ai_response = ticket_data['ai_response']

        # Verify response length is appropriate for channel
        assert test_case['min_length'] <= len(ai_response) <= test_case['max_length'], \
            f"Response length {len(ai_response)} not in expected range [{test_case['min_length']}, {test_case['max_length']}] for {test_case['channel']}"

        # Verify tone is appropriate
        if test_case['channel'] == 'email':
            assert any(greeting in ai_response.lower() for greeting in ['dear', 'hello', 'hi ', 'regards', 'sincerely']), \
                "Email should include formal greeting"
        elif test_case['channel'] == 'whatsapp':
            # WhatsApp should be shorter and more direct
            assert 'regards' not in ai_response.lower() and 'sincerely' not in ai_response.lower(), \
                "WhatsApp should not include formal closings"
        elif test_case['channel'] == 'webform':
            # Web form should be balanced
            assert len(ai_response) >= 100


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_ticket_creation_for_every_inquiry(client):
    """
    Test that every inquiry creates a ticket in PostgreSQL.
    Verifies Constitution FR-020 requirement.
    """
    inquiry_count = 10
    ticket_ids = []

    # Submit multiple inquiries
    for i in range(inquiry_count):
        inquiry_data = {
            'channel': 'email',
            'customer_email': f'ticket{i}@test.com',
            'message': f'Ticket creation test {i}'
        }

        response = await client.post("/api/inquiries", json=inquiry_data)
        assert response.status_code == 200

        ticket_id = response.json().get('ticket_id')
        if ticket_id:
            ticket_ids.append(ticket_id)

    # Verify all tickets were created
    assert len(ticket_ids) == inquiry_count, \
        f"Expected {inquiry_count} tickets, got {len(ticket_ids)}"

    # Verify all tickets are retrievable
    for ticket_id in ticket_ids:
        response = await client.get(f"/api/tickets/{ticket_id}")
        assert response.status_code == 200
        ticket_data = response.json()
        assert 'created_at' in ticket_data
        assert 'status' in ticket_data

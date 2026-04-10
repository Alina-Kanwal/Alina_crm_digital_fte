"""
Integration tests for Inquiry API.
Tests API endpoints for receiving and processing customer inquiries across channels.
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime
import json
from unittest.mock import patch, Mock, AsyncMock

from src.main import app


@pytest.fixture
async def client():
    """Create an async test client."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health check endpoints."""
    # Main path health check
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json()['status'] == 'alive'
    
    # Readiness check
    with patch('src.main.check_db_health', return_value=True):
        response = await client.get("/health/ready")
        assert response.status_code == 200
        assert response.json()['status'] == 'ready'


@pytest.mark.asyncio
async def test_submit_email_inquiry(client):
    """Test submitting an email inquiry to the v1 API."""
    inquiry_data = {
        "id": "email-123",
        "sender": "test@example.com",
        "subject": "Integration Help",
        "body": "How do I setup the CRM?",
        "timestamp": datetime.now().isoformat()
    }

    # Patch the class method to ensure all instances are covered
    with patch('src.services.inquiry_processor.InquiryProcessor.process_inquiry', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = {
            "success": True,
            "ticket_id": "TICKET-123",
            "message": "Inquiry received",
            "processing_time_seconds": 0.5
        }
        
        response = await client.post("/api/v1/inquiries/email", json=inquiry_data)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['ticket_id'] == "TICKET-123"


@pytest.mark.asyncio
async def test_submit_whatsapp_inquiry(client):
    """Test submitting a WhatsApp inquiry to the v1 API."""
    inquiry_data = {
        "id": "wa-123",
        "sender": "+1234567890",
        "body": "Hello, I need help",
        "timestamp": datetime.now().isoformat()
    }

    with patch('src.services.inquiry_processor.InquiryProcessor.process_inquiry', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = {
            "success": True,
            "ticket_id": "TICKET-456",
            "message": "Inquiry received",
            "processing_time_seconds": 0.4
        }
        
        response = await client.post("/api/v1/inquiries/whatsapp", json=inquiry_data)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['ticket_id'] == "TICKET-456"


@pytest.mark.asyncio
async def test_submit_crm_webform_inquiry(client):
    """Test submitting a webform inquiry to the CRM v1 API."""
    inquiry_data = {
        "sender": "web@example.com",
        "body": "Web form message"
    }

    with patch('src.services.inquiry_processor.InquiryProcessor.process_inquiry', new_callable=AsyncMock) as mock_process:
        mock_process.return_value = {
            "success": True,
            "ticket_id": "TICKET-789",
            "message": "Inquiry received"
        }
        
        response = await client.post("/api/v1/crm/inquiries", json=inquiry_data)
        assert response.status_code == 200
        data = response.json()
        assert data['success'] is True
        assert data['ticket_id'] == "TICKET-789"

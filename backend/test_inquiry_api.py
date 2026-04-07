#!/usr/bin/env python3
"""
Test script for verifying the inquiry API endpoints work correctly.
"""
import asyncio
import json
from fastapi.testclient import TestClient
import sys
import os

# Add the current directory to the path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.main import app

def test_email_inquiry():
    """Test email inquiry endpoint."""
    client = TestClient(app)

    # Sample email inquiry
    email_data = {
        "id": "email-001",
        "sender": "customer@example.com",
        "subject": "How do I reset my password?",
        "body": "I forgot my password and need help resetting it. Can you please guide me through the process?",
        "timestamp": "2026-03-28 10:30:00"
    }

    response = client.post("/api/v1/inquiries/email", json=email_data)
    print(f"Email Inquiry Response: {response.status_code}")
    print(f"Response Body: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "response" in data
    assert data["channel"] == "email"
    print("✓ Email inquiry test passed\n")

def test_whatsapp_inquiry():
    """Test WhatsApp inquiry endpoint."""
    client = TestClient(app)

    # Sample WhatsApp inquiry
    whatsapp_data = {
        "id": "whatsapp-001",
        "sender": "whatsapp:+1234567890",
        "body": "Hi, I'm having trouble logging into my account. Help!",
        "timestamp": "2026-03-28 10:35:00"
    }

    response = client.post("/api/v1/inquiries/whatsapp", json=whatsapp_data)
    print(f"WhatsApp Inquiry Response: {response.status_code}")
    print(f"Response Body: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "response" in data
    assert data["channel"] == "whatsapp"
    print("✓ WhatsApp inquiry test passed\n")

def test_webform_inquiry():
    """Test web form inquiry endpoint."""
    client = TestClient(app)

    # Sample web form inquiry
    webform_data = {
        "id": "webform-001",
        "sender": "customer@example.com",
        "name": "John Doe",
        "subject": "Pricing Question",
        "body": "I'm interested in your premium plan. What's the monthly cost?",
        "timestamp": "2026-03-28 10:40:00",
        "metadata": {
            "name": "John Doe",
            "email": "customer@example.com",
            "phone": "+1234567890"
        }
    }

    response = client.post("/api/v1/inquiries/webform", json=webform_data)
    print(f"Webform Inquiry Response: {response.status_code}")
    print(f"Response Body: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "response" in data
    assert data["channel"] == "webform"
    print("✓ Webform inquiry test passed\n")

def test_inquiry_metrics():
    """Test inquiry metrics endpoint."""
    client = TestClient(app)

    response = client.get("/api/v1/inquiries/metrics")
    print(f"Inquiry Metrics Response: {response.status_code}")
    print(f"Response Body: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert "total_requests" in data
    assert "average_processing_time_seconds" in data
    assert "agent_available" in data
    print("✓ Inquiry metrics test passed\n")

def test_inquiry_health():
    """Test inquiry processor health endpoint."""
    client = TestClient(app)

    response = client.get("/api/v1/inquiries/health")
    print(f"Inquiry Health Response: {response.status_code}")
    print(f"Response Body: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    print("✓ Inquiry health test passed\n")

if __name__ == "__main__":
    print("Testing Digital FTE Inquiry API Endpoints\n")

    try:
        test_email_inquiry()
        test_whatsapp_inquiry()
        test_webform_inquiry()
        test_inquiry_metrics()
        test_inquiry_health()

        print("🎉 All tests passed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
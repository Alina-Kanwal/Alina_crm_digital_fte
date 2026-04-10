"""
Unit tests for Escalation Engine.
Tests automatic escalation logic based on predefined rules.
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.services.escalation.engine import EscalationEngine, EscalationTrigger, EscalationSeverity


@pytest.fixture
def escalation_engine():
    """Create an EscalationEngine instance for testing."""
    return EscalationEngine()


@pytest.mark.asyncio
async def test_escalate_pricing_inquiry(escalation_engine):
    """Test escalation for pricing-related inquiries."""
    message = "I need custom pricing for my enterprise account with 1000 users"
    context = {"customer_id": "cust-123", "channel": "email"}

    result = await escalation_engine.evaluate_escalation(
        message=message,
        context=context
    )

    assert result.should_escalate is True
    assert result.trigger == EscalationTrigger.PRICING_INQUIRY
    assert result.severity == EscalationSeverity.HIGH


@pytest.mark.asyncio
async def test_escalate_refund_request(escalation_engine):
    """Test escalation for refund requests."""
    message = "I need a refund for my subscription"
    context = {"customer_id": "cust-123", "channel": "whatsapp"}

    result = await escalation_engine.evaluate_escalation(
        message=message,
        context=context
    )

    assert result.should_escalate is True
    assert result.trigger == EscalationTrigger.REFUND_REQUEST
    assert result.severity == EscalationSeverity.HIGH


@pytest.mark.asyncio
async def test_escalate_legal_matter(escalation_engine):
    """Test escalation for legal/compliance matters."""
    message = "I will sue you if you don't fix this"
    context = {"customer_id": "cust-123", "channel": "email"}

    result = await escalation_engine.evaluate_escalation(
        message=message,
        context=context
    )

    assert result.should_escalate is True
    assert result.trigger == EscalationTrigger.LEGAL_MATTER
    assert result.severity == EscalationSeverity.CRITICAL


@pytest.mark.asyncio
async def test_escalate_profanity(escalation_engine):
    """Test escalation for profanity/abusive language."""
    message = "This is fucking bullshit"
    context = {"customer_id": "cust-123", "channel": "email"}

    result = await escalation_engine.evaluate_escalation(
        message=message,
        context=context
    )

    assert result.should_escalate is True
    assert result.trigger == EscalationTrigger.PROFANITY
    assert result.severity == EscalationSeverity.CRITICAL


@pytest.mark.asyncio
async def test_escalate_repeated_unresolved(escalation_engine):
    """Test escalation for 3+ unresolved interactions."""
    message = "Still not working"
    context = {"customer_id": "cust-123", "channel": "email"}
    # History with 3 incoming messages
    history = [
        {"direction": "incoming", "content": "Help me"},
        {"direction": "outgoing", "content": "I tried"},
        {"direction": "incoming", "content": "Still broke"},
        {"direction": "outgoing", "content": "Try again"},
        {"direction": "incoming", "content": "Not working"}
    ]

    result = await escalation_engine.evaluate_escalation(
        message=message,
        context=context,
        history=history
    )

    assert result.should_escalate is True
    assert result.trigger == EscalationTrigger.REPEATED_UNRESOLVED


@pytest.mark.asyncio
async def test_no_escalation_for_simple_inquiry(escalation_engine):
    """Test no escalation for simple, resolvable inquiry."""
    message = "How do I change my password?"
    context = {"customer_id": "cust-123", "channel": "email"}

    result = await escalation_engine.evaluate_escalation(
        message=message,
        context=context
    )

    assert result.should_escalate is False

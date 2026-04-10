"""
Main inquiry processing pipeline for Digital FTE AI Customer Success Agent.
Orchestrates the end-to-end processing of customer inquiries from receipt to response.
Includes comprehensive logging with correlation IDs for traceability.
"""
import asyncio
import logging
import uuid
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.services.message_parser import MessageParser
from src.services.customer_identifier import CustomerIdentifierService
from src.agent.agent import AIAgent
from src.services.tone_adapter import ToneAdapter
from src.services.conversation_manager import ConversationManager
from src.services.contextual_responder import ContextualResponder
from src.utils.audit import write_audit
from src.models.audit_log import AuditActionType
from src.database.connection import get_db_session

logger = logging.getLogger(__name__)


class InquiryProcessor:
    """Main pipeline for processing customer inquiries across channels."""

    def __init__(self, history_limit: int = 15):
        """
        Initialize inquiry processor with dependency containers.
        
        Args:
            history_limit: Number of context messages to retrieve
        """
        self.message_parser = None
        self.customer_identifier = None
        # Renamed to ai_agent for API compatibility in endpoints
        self.ai_agent = None
        self.tone_adapter = None
        self.conversation_manager = None
        self.contextual_responder = None
        self.history_limit = history_limit
        self.initialized = False
        
        # Metrics tracking
        self.total_requests = 0
        self.processing_times = []
        
        logger.info("Inquiry processor instance created")

    async def initialize(self, 
                         message_parser=None, 
                         customer_identifier=None,
                         agent=None, 
                         tone_adapter=None,
                         conversation_manager=None,
                         contextual_responder=None):
        """
        Initialize the inquiry processor with required services.

        Args:
            message_parser: Message parser service
            customer_identifier: Customer identification service
            agent: AI agent service
            tone_adapter: Tone adaptation service
            conversation_manager: Conversation history manager
            contextual_responder: Context enhancer
        """
        try:
            self.message_parser = message_parser or MessageParser()
            self.customer_identifier = customer_identifier or CustomerIdentifierService()
            self.ai_agent = agent or AIAgent()
            self.tone_adapter = tone_adapter or ToneAdapter()
            self.conversation_manager = conversation_manager or ConversationManager(history_limit=self.history_limit)
            self.contextual_responder = contextual_responder or ContextualResponder(
                agent_service=self.ai_agent,
                conversation_manager=self.conversation_manager
            )

            # Mark as ready
            self.initialized = True
            logger.info("Inquiry processor pipeline initialized successfully")

        except Exception as e:
            logger.error(f"Failed to fully initialize inquiry processor: {e}")
            self.initialized = False
            raise

    async def process_inquiry(self, raw_message: Dict[str, Any], channel: str) -> Dict[str, Any]:
        """
        Process a customer inquiry through the full pipeline.

        Orchestrates:
        1. Normalization
        2. Customer Identification (Inc. pgvector matching)
        3. Conversation Threading
        4. Context-Aware AI Generation
        5. Tone Adaptation for Channel
        6. Persistence

        Args:
            raw_message: Message payload from channel source
            channel: communication channel identifier

        Returns:
            Result dict with final response and metadata
        """
        # 0. Generate correlation ID for end-to-end tracing
        correlation_id = str(uuid.uuid4())
        start_time = time.time()
        start_dt = datetime.utcnow()

        logger.info(f"[{correlation_id}] Received {channel} message. Processing start...")
        self.total_requests += 1

        if not self.initialized:
            await self.initialize()

        try:
            # 1. Parse and normalize
            logger.debug(f"[{correlation_id}] Step 1: Normalizing message")
            normalized = await self.message_parser.parse_and_normalize(raw_message)
            subject = normalized.get('subject', 'Customer Inquiry')
            content = normalized.get('body', '')

            # 2. Identify customer (matches by email/phone or pgvector similarity)
            logger.debug(f"[{correlation_id}] Step 2: Identifying customer")
            customer_info = await self.customer_identifier.identify_customer(normalized, correlation_id)
            customer_id = customer_info.get('id')
            logger.debug(f"[{correlation_id}] Identified customer_id: {customer_id}")

            # Record reception in AuditLog
            with get_db_session() as db:
                write_audit(
                    db, AuditActionType.INQUIRY_RECEIVED,
                    f"New inquiry received from {normalized.get('sender', 'unknown')} via {channel}.",
                    entity_id=customer_id, entity_type="customer"
                )
                db.commit()

            if not customer_id:
                logger.error(f"[{correlation_id}] Failed to identify or create customer. Cannot proceed.")
                return {'success': False, 'error': 'Customer identification failed'}

                # 4. Handle threading (US2: History and Context)
            logger.debug(f"[{correlation_id}] Step 3: Managing conversation thread")
            # Find an active thread or create a new one
            thread = await self.conversation_manager.find_active_thread_by_customer_and_channel(
                customer_id, channel, correlation_id
            )
            
            if not thread:
                logger.debug(f"[{correlation_id}] No active thread found, creating new one")
                thread = await self.conversation_manager.create_conversation_thread(
                    customer_id, channel, subject, correlation_id
                )
            
            if not thread:
                logger.error(f"[{correlation_id}] Failed to create or find conversation thread.")
                return {'success': False, 'error': 'Thread management failed'}
                
             # Fetch history BEFORE agent processing to provide context
            thread_id = thread.get('id')
            history = await self.conversation_manager.get_conversation_history(thread_id, correlation_id)
            logger.debug(f"[{correlation_id}] Retrieved {len(history)} messages for context")

            # 5. Save incoming message to history (IN PARALLEL)
            logger.debug(f"[{correlation_id}] Step 4: Archiving incoming message (Background)")
            archive_task = asyncio.create_task(
                self.conversation_manager.add_message_to_conversation(
                    thread_id=thread_id,
                    content=content,
                    direction='incoming',
                    channel=channel,
                    correlation_id=correlation_id
                )
            )

            # 6. Process with AI Agent (LATENCY BOTTLENECK)
            logger.debug(f"[{correlation_id}] Step 5: Generating AI response with history")
            # Pass history directly to the agent for context-aware generation
            agent_result = await self.ai_agent.process(content, customer_id, correlation_id, history=history)
            
            # Ensure archiving finished
            await archive_task
            
            final_response = agent_result.get('response', '')
            sentiment = agent_result.get('sentiment', 'neutral')
            sentiment_score = agent_result.get('sentiment_score', 0.0)

            # 8. Save outgoing message to history
            logger.debug(f"[{correlation_id}] Step 8: Archiving outgoing response")
            await self.conversation_manager.add_message_to_conversation(
                thread_id=thread_id,
                content=final_response,
                direction='outgoing',
                channel=channel,
                correlation_id=correlation_id
            )

            # Record resolution in AuditLog
            with get_db_session() as db:
                write_audit(
                    db, AuditActionType.INQUIRY_RESOLVED,
                    f"Autonomous response delivered to {normalized.get('sender', 'unknown')}.",
                    entity_id=customer_id, entity_type="customer"
                )
                db.commit()

            # 9. Automations (Phase 4: Workflow Action)
            try:
                from src.services.automation_service import automation_service
                asyncio.create_task(
                    asyncio.to_thread(
                        automation_service.process_automation_triggers,
                        customer_id=customer_id,
                        content=content,
                        sentiment=sentiment,
                        sentiment_score=sentiment_score
                    )
                )
            except Exception as auto_err:
                logger.error(f"[{correlation_id}] Failed to trigger automation: {auto_err}")

            duration = time.time() - start_time
            return {
                "success": True,
                "correlation_id": correlation_id,
                "response": final_response,
                "customer_id": customer_id,
                "thread_id": thread_id,
                "channel": channel,
                "processing_time_seconds": duration,
                "metadata": {
                    "sentiment": sentiment,
                    "sentiment_score": sentiment_score,
                    "processing_time": duration
                }
            }

        except Exception as e:
            logger.exception(f"[{correlation_id}] Critical failure in inquiry pipeline: {e}")
            duration = time.time() - start_time
            return {
                "success": False,
                "correlation_id": correlation_id,
                "error": str(e),
                "processing_time_seconds": duration,
                "fallback_response": "I apologize, but I'm having trouble processing your message right now. Our team is investigating."
            }

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the processor."""
        avg_time = sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0
        return {
            "total_requests": self.total_requests,
            "average_processing_time_seconds": avg_time,
            "agent_available": self.ai_agent.is_available() if self.ai_agent else False
        }


def create_inquiry_processor(history_limit: int = 15) -> InquiryProcessor:
    """Factory to create processor instance."""
    return InquiryProcessor(history_limit=history_limit)
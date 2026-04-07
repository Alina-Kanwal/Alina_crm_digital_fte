"""
Context-aware response generation service.
Generates AI responses that incorporate conversation history and context across channels.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class ContextualResponder:
    """Service for generating context-aware responses."""

    def __init__(self, agent_service=None, conversation_manager=None):
        """
        Initialize contextual responder.

        Args:
            agent_service: AI agent service for generating responses
            conversation_manager: Conversation manager for retrieving history
        """
        self.agent_service = agent_service
        self.conversation_manager = conversation_manager
        self.context_window = 5  # Number of recent messages to include
        self.max_context_length = 2000  # Maximum context characters
        logger.info("Contextual responder initialized")

    async def generate_context_aware_response(
        self,
        current_message: str,
        thread_id: str,
        customer_id: int,
        channel: str,
        agent_response: str
    ) -> Dict[str, Any]:
        """
        Generate a context-aware response incorporating conversation history.

        Args:
            current_message: The current customer message
            thread_id: The conversation thread ID
            customer_id: The customer ID
            channel: The communication channel
            agent_response: The initial AI response without context

        Returns:
            Dictionary containing:
            - response: Context-aware response
            - context_summary: Summary of context used
            - has_context: Whether context was available
        """
        try:
            # Retrieve conversation history
            history = await self.conversation_manager.get_conversation_history(thread_id)

            if not history or len(history) == 0:
                # No context available, return original response
                logger.debug(f"No context available for thread {thread_id}")
                return {
                    'response': agent_response,
                    'context_summary': 'No conversation history available',
                    'has_context': False,
                    'messages_referenced': 0
                }

            # Build context from recent messages
            context = self._build_context(history, current_message)

            # Enhance response with context
            enhanced_response = await self._enhance_response(
                agent_response,
                context,
                channel,
                history
            )

            # Generate context summary
            context_summary = self._generate_context_summary(history, context)

            logger.info(
                f"Generated context-aware response for thread {thread_id}: "
                f"{len(history)} messages in history, "
                f"{len(context['recent_messages'])} messages referenced"
            )

            return {
                'response': enhanced_response,
                'context_summary': context_summary,
                'has_context': True,
                'messages_referenced': len(context['recent_messages'])
            }

        except Exception as e:
            logger.error(f"Error generating context-aware response: {e}")
            # Fallback to original response
            return {
                'response': agent_response,
                'context_summary': 'Error retrieving context',
                'has_context': False,
                'messages_referenced': 0
            }

    def _build_context(self, history: List[Dict], current_message: str) -> Dict[str, Any]:
        """
        Build context from conversation history.

        Args:
            history: List of message dictionaries
            current_message: The current customer message

        Returns:
            Dictionary containing context information
        """
        # Get recent messages (excluding current)
        recent_messages = history[-self.context_window:] if len(history) > self.context_window else history

        # Extract key information from history
        topics_discussed = []
        channels_used = set()
        resolution_status = None

        for msg in recent_messages:
            # Extract topics (simple keyword extraction for now)
            topics = self._extract_topics(msg['content'])
            topics_discussed.extend(topics)

            # Track channels used
            channels_used.add(msg['channel'])

            # Check for resolution indicators
            if 'resolved' in msg['content'].lower() or 'fixed' in msg['content'].lower():
                resolution_status = 'resolved'
            elif msg['direction'] == 'outgoing' and 'thank' in msg['content'].lower():
                resolution_status = 'positive_feedback'

        # Remove duplicate topics
        unique_topics = list(set(topics_discussed))

        # Build context string
        context_str = self._build_context_string(recent_messages)

        return {
            'recent_messages': recent_messages,
            'topics_discussed': unique_topics,
            'channels_used': list(channels_used),
            'resolution_status': resolution_status,
            'context_string': context_str,
            'message_count': len(recent_messages)
        }

    def _extract_topics(self, message: str) -> List[str]:
        """
        Extract topics from a message.

        Args:
            message: Message content

        Returns:
            List of topic keywords
        """
        # Simple keyword extraction based on product domain
        topic_keywords = [
            'integration', 'api', 'webhook', 'authentication', 'oauth',
            'workflow', 'automation', 'trigger', 'action',
            'pricing', 'plan', 'subscription', 'billing',
            'refund', 'payment', 'invoice',
            'login', 'password', 'account', 'profile',
            'slack', 'gmail', 'salesforce', 'salesforce',
            'troubleshoot', 'error', 'bug', 'issue',
            'feature', 'request', 'enhancement'
        ]

        message_lower = message.lower()
        found_topics = []

        for keyword in topic_keywords:
            if keyword in message_lower:
                found_topics.append(keyword)

        return found_topics

    def _build_context_string(self, recent_messages: List[Dict]) -> str:
        """
        Build a context string from recent messages.

        Args:
            recent_messages: List of recent message dictionaries

        Returns:
            Formatted context string
        """
        if not recent_messages:
            return ""

        context_parts = []

        for msg in recent_messages:
            direction = "Customer" if msg['direction'] == 'incoming' else "Agent"
            channel = msg['channel']
            content = msg['content']

            # Truncate very long messages
            if len(content) > 200:
                content = content[:200] + "..."

            context_parts.append(f"{direction} ({channel}): {content}")

        # Join with separator and limit length
        full_context = " | ".join(context_parts)

        if len(full_context) > self.max_context_length:
            full_context = full_context[:self.max_context_length] + "..."

        return full_context

    async def _enhance_response(
        self,
        original_response: str,
        context: Dict[str, Any],
        channel: str,
        history: List[Dict]
    ) -> str:
        """
        Enhance the original response with context.

        Args:
            original_response: The initial AI response
            context: Context information
            channel: Communication channel
            history: Conversation history

        Returns:
            Enhanced response incorporating context
        """
        # Check if we should reference previous conversation
        should_reference = self._should_reference_context(context, history)

        if not should_reference:
            return original_response

        # Build context-aware additions
        additions = []

        # Reference previous channel if different
        if len(context['channels_used']) > 1:
            current_channel = channel
            last_channel = history[-1]['channel'] if history else current_channel

            if last_channel != current_channel:
                if current_channel == 'email':
                    additions.append("Following up on our previous conversation:")
                elif current_channel == 'whatsapp':
                    additions.append("Continuing from our earlier chat:")
                else:
                    additions.append("Following up on your previous message:")

        # Reference topics if discussed
        if context['topics_discussed']:
            # Only mention if topics are still relevant
            relevant_topics = context['topics_discussed'][:2]  # Top 2 topics
            if relevant_topics:
                topic_list = ", ".join(relevant_topics)
                if len(additions) == 0:
                    additions.append(f"Regarding {topic_list}:")
                else:
                    additions.append(f"with respect to {topic_list},")

        # Check for resolution status
        if context['resolution_status'] == 'resolved':
            # Previous issue was resolved, check if this is new or follow-up
            if "again" in original_response.lower() or "still" in original_response.lower():
                additions.append("I see you're experiencing this issue again.")

        # Combine original response with context additions
        if additions:
            # Add context prefix to response
            context_prefix = " ".join(additions) + " "
            enhanced_response = context_prefix + original_response

            # Ensure response is still appropriate length for channel
            if channel == 'whatsapp' and len(enhanced_response) > 150:
                # Too long for WhatsApp, truncate context
                enhanced_response = original_response
            elif channel == 'email' and len(enhanced_response) > 600:
                # Too long for email, summarize context
                enhanced_response = "Following our previous conversation, " + original_response

            return enhanced_response

        return original_response

    def _should_reference_context(
        self,
        context: Dict[str, Any],
        history: List[Dict]
    ) -> bool:
        """
        Determine if we should reference conversation context.

        Args:
            context: Context information
            history: Conversation history

        Returns:
            True if context should be referenced
        """
        # Don't reference if there's only 1 message (start of conversation)
        if context['message_count'] < 2:
            return False

        # Reference if multiple channels used
        if len(context['channels_used']) > 1:
            return True

        # Reference if topics were discussed that are still relevant
        if context['topics_discussed'] and len(context['topics_discussed']) > 0:
            return True

        # Reference if there was a resolution and this might be a follow-up
        if context['resolution_status'] == 'resolved':
            return True

        # Reference if there are 3+ messages in history
        if context['message_count'] >= 3:
            return True

        return False

    def _generate_context_summary(
        self,
        history: List[Dict],
        context: Dict[str, Any]
    ) -> str:
        """
        Generate a summary of the context used.

        Args:
            history: Conversation history
            context: Context information

        Returns:
            Human-readable context summary
        """
        parts = []

        # Message count
        parts.append(f"{context['message_count']} messages")

        # Channels
        if len(context['channels_used']) > 1:
            channels_str = " and ".join(context['channels_used'])
            parts.append(f"across {channels_str}")
        elif context['channels_used']:
            parts.append(f"via {context['channels_used'][0]}")

        # Topics
        if context['topics_discussed']:
            topics = ", ".join(context['topics_discussed'][:3])
            parts.append(f"covering {topics}")

        # Resolution status
        if context['resolution_status']:
            parts.append(f"status: {context['resolution_status']}")

        return "; ".join(parts) if parts else "No context available"

    async def get_cross_channel_context(
        self,
        customer_id: int,
        current_thread_id: str,
        limit: int = 3
    ) -> Dict[str, Any]:
        """
        Get context from other channels for cross-channel continuity.

        Args:
            customer_id: The customer ID
            current_thread_id: The current conversation thread ID
            limit: Maximum number of other conversations to retrieve

        Returns:
            Dictionary containing cross-channel context
        """
        try:
            # Get all customer conversations
            conversations = await self.conversation_manager.get_customer_conversations(
                customer_id,
                limit=limit + 1  # +1 to exclude current
            )

            # Filter out current thread
            other_conversations = [
                conv for conv in conversations
                if conv['thread_id'] != current_thread_id
            ]

            if not other_conversations:
                return {
                    'has_cross_channel_context': False,
                    'conversations': [],
                    'channels_used': []
                }

            # Extract context from other conversations
            channels_used = set()
            summaries = []

            for conv in other_conversations[:limit]:
                channels_used.add(conv['channel'])
                summaries.append({
                    'thread_id': conv['thread_id'],
                    'channel': conv['channel'],
                    'message_count': conv['message_count'],
                    'last_activity': conv['last_activity']
                })

            logger.info(
                f"Found cross-channel context for customer {customer_id}: "
                f"{len(other_conversations)} conversations, "
                f"{len(channels_used)} channels"
            )

            return {
                'has_cross_channel_context': True,
                'conversations': summaries,
                'channels_used': list(channels_used),
                'conversation_count': len(other_conversations)
            }

        except Exception as e:
            logger.error(f"Error retrieving cross-channel context: {e}")
            return {
                'has_cross_channel_context': False,
                'conversations': [],
                'channels_used': []
            }

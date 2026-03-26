# Data Model: Digital Full-Time Employee (Digital FTE) – AI Customer Success Agent

## Customer
Represents an individual or entity seeking support, identified by contact information and interaction history across channels.

### Fields
- `id`: UUID, primary key
- `email`: String, unique, indexed (primary identifier)
- `phone_number`: String, indexed (for WhatsApp identification)
- `created_at`: Timestamp, when customer first interacted with system
- `updated_at`: Timestamp, last interaction update
- `metadata`: JSONB, additional customer attributes (preferences, tier, etc.)
- `is_active`: Boolean, whether customer is currently active

### Constraints
- At least one of email or phone_number must be provided
- Email must be valid format when provided
- Phone number must be valid format when provided

## Support Ticket
A record of a customer interaction containing message content, timestamps, channel used, agent actions, resolution status, and escalation flags.

### Fields
- `id`: UUID, primary key
- `customer_id`: UUID, foreign key to Customer
- `channel`: Enum (email, whatsapp, web_form)
- `external_id`: String, ID from external system (Gmail message ID, WhatsApp message ID, etc.)
- `subject`: String, brief summary of issue (for email/web form)
- `content`: Text, the actual message content from customer
- `received_at`: Timestamp, when message was received
- `responded_at`: Timestamp, when AI responded (nullable)
- `resolved_at`: Timestamp, when issue was resolved (nullable)
- `ai_response`: Text, the AI's response to the customer
- `sentiment`: Enum (positive, neutral, negative), detected customer sentiment
- `confidence_score`: Float (0-1), AI confidence in response appropriateness
- `escalated`: Boolean, whether ticket was escalated to human agent
- `escalation_reason`: String, reason for escalation if applicable
- `resolution_category`: String, type of issue (technical, billing, feature_request, etc.)
- `metadata`: JSONB, additional ticket information

### Constraints
- channel determines which external_id field is relevant
- sent_at must be after received_at if provided
- resolved_at must be after responded_at if both provided
- confidence_score must be between 0 and 1

## Conversation Thread
A series of related messages exchanged between a customer and the support system, potentially spanning multiple channels.

### Fields
- `id`: UUID, primary key
- `customer_id`: UUID, foreign key to Customer
- `title`: String, brief summary of conversation topic
- `started_at`: Timestamp, first message in thread
- `last_updated_at`: Timestamp, most recent message in thread
- `message_count`: Integer, total messages in thread
- `channel_history`: JSONB, array of channels used in chronological order
- `is_resolved`: Boolean, whether conversation thread is resolved
- `resolution_summary`: String, brief description of how issue was resolved
- `metadata`: JSONB, additional thread information

### Constraints
- last_updated_at must be after started_at
- message_count must be >= 1
- channel_history must contain valid channel values

## Escalation Rule
A defined condition that triggers automatic transfer of a conversation to a human support agent.

### Fields
- `id`: UUID, primary key
- `name`: String, human-readable name of rule
- `description`: String, detailed description of when rule applies
- `trigger_type`: Enum (keyword, sentiment, interaction_count, time_threshold, custom_function)
- `trigger_config`: JSONB, configuration specific to trigger type
- `priority`: Integer, higher numbers = higher priority for rule evaluation
- `is_active`: Boolean, whether rule is currently enabled
- `created_at`: Timestamp, when rule was created
- `updated_at`: Timestamp, when rule was last modified

### Constraints
- name must be unique
- trigger_config must be valid JSON for the trigger_type
- priority must be positive integer

## Sentiment Record
Analysis of customer emotional state during an interaction, categorized as positive, neutral, or negative.

### Fields
- `id`: UUID, primary key
- `ticket_id`: UUID, foreign key to Support Ticket
- `analyzed_at`: Timestamp, when sentiment was analyzed
- `sentiment`: Enum (positive, neutral, negative)
- `score`: Float (-1 to 1), where -1 is very negative, 0 is neutral, 1 is very positive
- `confidence`: Float (0-1), confidence in sentiment analysis
- `text_snippet`: String, portion of message used for analysis
- `metadata`: JSONB, additional analysis details

### Constraints
- score must be between -1 and 1
- confidence must be between 0 and 1
- analyzed_at must be after ticket's received_at

## Knowledge Base (Conceptual)
The searchable repository of product documentation used to answer customer questions.
*Note: This represents the conceptual model; actual implementation uses PostgreSQL with pgvector for storage and search.*

### Conceptual Fields
- `content`: Text, the actual documentation content
- `title`: String, title of documentation section
- `category`: String, topic area (getting_started, troubleshooting, billing, etc.)
- `tags`: Array[String], searchable keywords
- `last_updated`: Timestamp, when documentation was last revised
- `version`: String, version of product this documentation applies to

### Search Capabilities
- Full-text search on content and title
- Semantic similarity search using embeddings (pgvector)
- Filtering by category, tags, and version ranges
- Ranking by relevance and recency
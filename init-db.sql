-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create basic tables for our domain
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    phone_number VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS support_tickets (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    channel VARCHAR(50) NOT NULL, -- email, whatsapp, webform
    subject VARCHAR(500),
    description TEXT,
    status VARCHAR(50) DEFAULT 'open', -- open, in_progress, resolved, escalated
    priority VARCHAR(20) DEFAULT 'medium', -- low, medium, high, urgent
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS conversation_threads (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    thread_id VARCHAR(255) UNIQUE,
    channel VARCHAR(50),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    thread_id INTEGER REFERENCES conversation_threads(id),
    content TEXT NOT NULL,
    channel VARCHAR(50) NOT NULL,
    direction VARCHAR(10) NOT NULL, -- incoming, outgoing
    sentiment VARCHAR(20), -- positive, neutral, negative
    sentiment_score FLOAT, -- -1.0 to 1.0
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS escalations (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER REFERENCES support_tickets(id),
    reason VARCHAR(100) NOT NULL, -- pricing, refund, legal, profanity, unresolved
    escalated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    escalated_to VARCHAR(255), -- human agent ID or team
    status VARCHAR(50) DEFAULT 'pending' -- pending, in_progress, resolved
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_support_tickets_customer ON support_tickets(customer_id);
CREATE INDEX IF NOT EXISTS idx_support_tickets_status ON support_tickets(status);
CREATE INDEX IF NOT EXISTS idx_conversation_threads_customer ON conversation_threads(customer_id);
CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(thread_id);
CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp);
CREATE INDEX IF NOT EXISTS idx_escalations_ticket ON escalations(ticket_id);
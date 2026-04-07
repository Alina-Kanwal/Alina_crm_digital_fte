# Digital FTE Transition Checklist: Support to Human Handover

This checklist defines the operational requirements for transitioning a customer from the AI Digital FTE to a human support agent. Adherence to these steps ensures 100% data continuity and zero customer frustration.

## 1. Trigger Verification
- [ ] **Reason Identified**: The escalation reason is explicitly logged (e.g., Profanity, Pricing, Refund, Legal, Unresolved after 3+ attempts).
- [ ] **Sentiment Context**: Current customer sentiment score and trend (e.g., getting more frustrated) is captured.
- [ ] **Confidence Score**: AI confidence score for the last message is recorded.

## 2. Context Package Preparation
- [ ] **Thread History**: Last 10-20 messages from the active thread are compiled into a summary.
- [ ] **Profile Data**: Customer's unified profile (Email, Phone, WhatsApp ID) is attached.
- [ ] **Semantic Search Context**: The documentation chunks the AI was referencing are attached for the human to see "what the AI was thinking".

## 3. Communication Channel Handover
- [ ] **Email**: Forward full thread to `escalations@company.com` with `[ESCALATION] {TicketID}` in subject.
- [ ] **WhatsApp**: Send automated message to customer: "I've notified our human team to assist you. A manager will join this chat shortly."
- [ ] **CRM Update**: Ticket status in PostgreSQL updated to `escalated` and assigned to `human_queue`.

## 4. Audit & Quality Assurance
- [ ] **Correlation ID**: The `correlation_id` is passed to the human agent for log traceability.
- [ ] **Resolution Loop**: Human agent has a way to "close the loop" and mark if the AI's failed response was due to a knowledge gap (triggers documentation update).

## 5. System State
- [ ] **AI Suppression**: AI is disabled for this specific `thread_id` until a human manually reactivates it or the ticket is resolved.
- [ ] **Uptime Check**: Verify that the Escalation Engine (Kafka -> Consumer) is acknowledged.

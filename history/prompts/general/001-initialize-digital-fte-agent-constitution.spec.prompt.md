---
id: 001
title: Initialize Digital FTE Agent Constitution
stage: spec
date: 2026-03-27
surface: agent
model: claude-sonnet-4-6
feature: none
branch: 001-digital-fte-agent
user: user
command: /sp.constitution
labels: ["constitution", "digital-fte-agent", "planning"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
tests:
---

## Prompt

Claude, from now on we are going to build the project strictly according to the real Hackathon 5 requirements.

My current setup is only a basic FastAPI backend and Next.js frontend running locally. This is not enough. We need the full production-grade Digital FTE (AI Customer Success Agent).

### Real Requirements We Must Meet:
- PostgreSQL database with pgvector extension (this is our CRM, no mock SQLite)
- Apache Kafka for message queue and unified ticket ingestion
- OpenAI Agents SDK (gpt-4o) based intelligent autonomous agent with custom @function_tools
- Three channel integrations:
  - Gmail API (sandbox)
  - Twilio WhatsApp Sandbox
  - Fully functional embeddable React/Next.js Web Support Form
- Cross-channel customer identification and conversation continuity (>95% accuracy)
- Smart escalation logic (pricing, refund, legal, profanity, unresolved issues)
- Channel-aware responses (formal for email, casual for WhatsApp)
- Full ticket lifecycle management in PostgreSQL
- Sentiment analysis and daily reports
- Kubernetes deployment with auto-scaling and health checks
- Must pass 24-hour chaos testing (100+ web forms, 50+ Gmail, 50+ WhatsApp, random pod kills)

### Current Status:
We only have basic FastAPI + Next.js with mock database. Real architecture, AI agent, Kafka, PostgreSQL, and Kubernetes are still missing.

### Your Task:
We are now entering the Specialization Phase. Please guide me step-by-step to build the complete production system.

Start by doing the following:

1. **/sp.constitution**
   Create a strong constitution for the main "Customer Success FTE Agent".

2. **/sp.specification**
   Write a complete detailed technical specification for the entire system including database schema, Kafka architecture, AI agent tools, channel integrations, and Kubernetes setup.

3. **/so.plan**
   Provide a clear step-by-step development plan to go from current basic setup to the full production-grade Digital FTE.

After that, we will follow the loop: /sp.constitution → /sp.specification → /so.plan → /sp.task → /sp.implementation for every major part.

Be strict with the requirements. No shortcuts. We need a real omnichannel AI employee, not a simple demo.

Start now.
Give me the first command: **/sp.constitution** for the main Digital FTE Agent.

Let's begin.

## Response snapshot

Acknowledged. Creating PHR for initial Digital FTE Agent planning request. Proceeding to execute /sp.constitution skill to establish strong constitutional principles for the Customer Success FTE Agent.

## Outcome

- ✅ Impact: Constitutional framework established for Digital FTE Agent development
- 🧪 Tests: N/A (planning phase)
- 📁 Files: history/prompts/general/001-initialize-digital-fte-agent-constitution.spec.prompt.md
- 🔁 Next prompts: /sp.specification, /sp.plan, /sp.tasks, /sp.implement
- 🧠 Reflection: Initial project scope and requirements clearly defined with production-grade constraints

## Evaluation notes (flywheel)

- Failure modes observed: N/A
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A

# Digital Full-Time Employee (Digital FTE) – AI Customer Success Agent

A production-grade autonomous AI employee that works 24/7 as a Customer Success Agent for a SaaS company, handling inquiries across Gmail, WhatsApp, and web form channels.

## Overview

This AI agent replaces human support staff by:
- Processing customer inquiries from email, WhatsApp, and web forms
- Understanding intent using natural language processing (OpenAI GPT-4o)
- Searching product documentation for accurate answers
- Generating channel-appropriate responses (formal/email, casual/WhatsApp, semi-formal/web)
- Maintaining cross-channel conversation history
- Automatically escalating complex issues to human agents
- Analyzing customer sentiment and generating daily reports
- Operating with total annual cost under $1000

## Architecture

- **Backend**: FastAPI (Python 3.11)
- **AI Core**: OpenAI Agents SDK with custom function tools
- **Message Queue**: Apache Kafka for reliable message processing
- **Database**: PostgreSQL 15 with pgvector extension for semantic search
- **Frontend**: React/Next.js embeddable web support form
- **Deployment**: Kubernetes with auto-scaling and health checks

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ with pgvector extension
- Docker & Kubernetes (for deployment)
- OpenAI API key
- Gmail API credentials (sandbox)
- Twilio WhatsApp sandbox credentials

### Installation

1. Clone the repository
2. Backend setup:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Frontend setup:
   ```bash
   cd frontend
   npm install
   ```

## Project Structure

```
backend/              # FastAPI backend services
├── src/
│   ├── models/       # Database models
│   ├── services/     # Business logic (AI, integrations, etc.)
│   └── api/          # REST API endpoints
└── tests/            # Backend tests

frontend/             # React/Next.js web form
├── src/
│   ├── components/   # Reusable UI components
│   ├── pages/        # Page components
│   └── services/     # Frontend services
└── tests/            # Frontend tests

docs/                 # Documentation
├── api/              # API documentation
├── architecture/     # Architectural decisions
├── deployment/       # Deployment guides
└── user-guides/      # End-user documentation

specs/                # Specifications (SDD)
├── 001-digital-fte-agent/
│   ├── spec.md       # Feature specification
│   ├── plan.md       # Implementation plan
│   └── tasks.md      # Task list
```

## Development Methodology

This project follows Spec-Driven Development (SDD):
1. Constitution → 2. Specification → 3. Plan → 4. Tasks → 5. Implementation

All work is traceable to approved specifications ensuring alignment with user needs and architectural integrity.

## License

Proprietary - For internal use only
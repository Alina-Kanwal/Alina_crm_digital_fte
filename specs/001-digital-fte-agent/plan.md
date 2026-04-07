# Implementation Plan: Digital Full-Time Employee (Digital FTE) – AI Customer Success Agent

**Branch**: `001-digital-fte-agent` | **Date**: 2026-04-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-digital-fte-agent/spec.md`

**Note**: Updated for Constitution v1.1.0 production-grade requirements with refined specifications addressing ambiguity and underspecification issues.

## Summary

Build a production-grade autonomous AI customer success agent that handles inquiries across Gmail, WhatsApp, and web form channels. The agent will use OpenAI's GPT-4o with custom function tools to understand customer queries, search product documentation with >80% relevance score, generate channel-appropriate responses, maintain cross-channel conversation history, analyze sentiment with confidence scores, and escalate to human agents when needed. Built with FastAPI backend, PostgreSQL with pgvector, Apache Kafka message queue, and deployed on Kubernetes with a target cost under $1000/year. Must pass 24-hour chaos testing with random pod kills.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: FastAPI, OpenAI Agents SDK (gpt-4o), PostgreSQL 15 with pgvector extension, Apache Kafka
**Storage**: PostgreSQL 15 with pgvector extension for semantic search and cross-channel customer identification
**Message Queue**: Apache Kafka for unified ticket ingestion (NON-NEGOTIABLE - no direct DB writes)
**Testing**: pytest for backend, Jest for frontend, chaos testing framework
**Target Platform**: Linux server (Kubernetes deployment)
**Project Type**: Web application (backend API + frontend web form)
**Performance Goals**: Sub-3-second response latency (p95), 99.95% uptime
**Constraints**: Total annual cost under $1000, 97%+ cross-channel identification accuracy, <20% escalation rate
**Scale/Scope**: 100+ web form submissions, 50+ Gmail emails, 50+ WhatsApp messages daily during peak
**Chaos Testing**: 24-hour test with random pod kills, network latency injection (up to 5-second delay), resource exhaustion (90% utilization) - zero data loss required

## Constitution Check

**GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.**

### I. Spec-Driven Development (SDD)
✅ COMPLIANT: Following constitution → specification → plan → tasks → implementation workflow. All work traceable to approved specifications.

### II. AI-First Approach
✅ COMPLIANT: Leveraging AI agents (OpenAI Agents SDK) for core functionality, reducing manual effort in customer support.

### III. Test-First (NON-NEGOTIABLE)
✅ COMPLIANT: Will implement TDD with tests written before production code. Red-Green-Refactor cycle will be strictly enforced.

### IV. Observability and Monitoring
✅ COMPLIANT: Comprehensive logging, metrics, and tracing included for debugging and proactive issue detection. Structured logging (JSON) with correlation IDs required.

### V. Simplicity and Minimal Viable Changes
✅ COMPLIANT: Starting with simplest solution that works, avoiding over-engineering, making smallest viable changes first.

### VI. Cost Consciousness
✅ COMPLIANT: All architectural decisions prioritize cost efficiency to meet <$1000/year constraint. Preferring open-source solutions and continuous expense monitoring.

### VII. Production Database Standards (NON-NEGOTIABLE)
✅ COMPLIANT: PostgreSQL with pgvector extension required. No mock databases or SQLite in production. Vector embeddings for semantic search and customer identification.

### VIII. Event-Driven Architecture (NON-NEGOTIABLE)
✅ COMPLIANT: Apache Kafka required for all message queuing and ticket ingestion. No direct database writes, in-memory queues, or polling-based mechanisms.

### IX. OpenAI Agents SDK (NON-NEGOTIABLE)
✅ COMPLIANT: AI agent will use OpenAI Agents SDK with gpt-4o model and custom @function_tools. No direct API calls for agent orchestration.

### X. Multi-Channel Integration
✅ COMPLIANT: All three channels fully functional - Gmail API (sandbox), Twilio WhatsApp Sandbox, embeddable React/Next.js Web Support Form.

### XI. Cross-Channel Customer Identity Continuity
✅ COMPLIANT: Email as primary identifier, phone for WhatsApp, session IDs for web form. Linked via pgvector embeddings for 97%+ accuracy.

### XII. Smart Escalation Logic
✅ COMPLIANT: Automatic escalation for pricing, refunds, legal matters, profanity, and 3+ unresolved interactions OR 2 consecutive negative sentiments.

### XIII. Channel-Aware Communication
✅ COMPLIANT: Response tone adapts - formal for email, casual for WhatsApp (max 2 emojis), semi-formal for web form.

### XIV. Ticket Lifecycle Management
✅ COMPLIANT: Full lifecycle tracking in PostgreSQL - creation, priority, agent assignment, status, resolution, feedback (CSAT 1-5).

### XV. Production Readiness & Chaos Testing
✅ COMPLIANT: 24-hour chaos testing required - 100+ web forms, 50+ Gmail, 50+ WhatsApp, random pod kills, zero data loss.

### XVI. Kubernetes Deployment (NON-NEGOTIABLE)
✅ COMPLIANT: All services on Kubernetes with auto-scaling, health checks, rolling updates, resource quotas, Secrets/ConfigMaps.

## Project Structure

### Documentation (this feature)

```text
specs/001-digital-fte-agent/
├── plan.md              # This file (/sp.plan command output)
├── research.md          # Phase 0 output (/sp.plan command)
├── data-model.md        # Phase 1 output (/sp.plan command)
├── quickstart.md        # Phase 1 output (/sp.plan command)
├── contracts/           # Phase 1 output (/sp.plan command)
│   └── openapi.yaml    # API contract specification
├── checklists/          # Quality checklists
│   └── requirements.md  # Specification quality checklist
└── tasks.md             # Phase 2 output (/sp.tasks command - NOT created by /sp.plan)
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/           # SQLAlchemy models (PostgreSQL with pgvector)
│   ├── services/
│   │   ├── agent/       # OpenAI Agents SDK implementation
│   │   ├── kafka/       # Kafka producers/consumers
│   │   ├── channels/    # Channel adapters (Gmail, WhatsApp, Web Form)
│   │   ├── sentiment/   # Sentiment analysis service
│   │   └── escalation/  # Escalation logic
│   ├── api/             # FastAPI route handlers
│   ├── middleware/       # Logging, metrics, tracing middleware
│   └── main.py         # Application entry point
├── tests/
│   ├── unit/            # Unit tests
│   ├── integration/      # Integration tests
│   ├── chaos/           # Chaos testing scripts
│   └── e2e/            # End-to-end tests
├── k8s/               # Kubernetes manifests
│   ├── deployments/
│   ├── services/
│   ├── configmaps/
│   ├── secrets/
│   └── hpa/            # Horizontal Pod Autoscalers
└── docker/

frontend/
├── src/
│   ├── components/
│   │   └── SupportForm/ # Embeddable web support form
│   ├── pages/
│   └── services/        # API service clients
└── tests/
```

**Structure Decision**: Selected Web application structure with separate backend and frontend directories as specified in project requirements and mandated by constitution. Backend contains FastAPI server, AI agent logic, Kafka integration, and API endpoints. Frontend contains React/Next.js embeddable web support form. Kubernetes manifests for production deployment.

## Complexity Tracking

> **No violations - All principles fully compliant**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
|           |            |                                     |

## Phase 0: Research & Technology Decisions

**Status**: ✅ COMPLETED

Research findings documented in `research.md` covering:
- Natural Language Processing: OpenAI GPT-4o with custom function tools
- Knowledge Base Confidence Threshold: 70% for automated responses
- Escalation Criteria: 3 interactions OR 2 consecutive negative sentiments
- Language Support: English primary + 5 languages (Spanish, French, German, Portuguese, Italian) for simple queries
- Customer Identification: Email primary + phone/session secondary via pgvector embeddings

## Phase 1: Design & Contracts

**Status**: ✅ COMPLETED

### Data Model
Complete database schema defined in `data-model.md` including:
- Customer (with pgvector embeddings)
- Support Ticket (full lifecycle)
- Conversation Thread (cross-channel continuity)
- Escalation Rule (configurable triggers)
- Sentiment Record (analysis results)
- Knowledge Base (semantic search)

### API Contracts
OpenAPI specification in `contracts/openapi.yaml` defining:
- Ticket CRUD operations
- Customer identification endpoints
- Escalation endpoints
- Daily sentiment reporting
- Request/response schemas with validation

### Quick Start Guide
Development setup instructions in `quickstart.md` covering:
- Backend (FastAPI, PostgreSQL, Kafka) setup
- Frontend (Next.js) setup
- Docker Compose for local development
- Testing procedures

## Timeline Estimate: Requirements Phase Completion

### Current Status
- ✅ Constitution v1.1.0: COMPLETED (2026-03-27)
- ✅ Specification (spec.md): COMPLETED (2026-04-01) - Refined version
- ✅ Implementation Plan (plan.md): COMPLETED (2026-04-01) - Updated version
- ✅ Research (research.md): COMPLETED (2026-03-26)
- ✅ Data Model (data-model.md): COMPLETED (2026-03-26)
- ✅ API Contracts (openapi.yaml): COMPLETED (2026-03-26)
- ✅ Quick Start (quickstart.md): COMPLETED (2026-03-26)
- ✅ Checklists (requirements.md): COMPLETED (2026-04-01) - Quality validation

### Requirements Phase Completion: ✅ **TODAY (2026-04-01)**

All planning and requirements artifacts are now complete and aligned with Constitution v1.1.0 production-grade requirements.

## Next Phases: Implementation Roadmap

### Phase 2: Task Generation (Ready to Start)
- **Command**: `/sp.tasks`
- **Output**: `tasks.md` with detailed implementation tasks organized by user story
- **Estimated Time**: 2-4 hours

### Phase 3: Core Infrastructure (Blocking)
- PostgreSQL with pgvector setup
- Apache Kafka cluster setup
- Kafka topics creation
- Database migrations
- Basic FastAPI application structure
- **Estimated Time**: 3-5 days

### Phase 4: AI Agent & Core Services
- OpenAI Agents SDK integration
- Custom @function_tools implementation
- Knowledge base service with pgvector semantic search (>80% relevance validation)
- Sentiment analysis service (confidence scoring 0.0-1.0)
- Escalation logic service
- **Estimated Time**: 5-7 days

### Phase 5: Channel Integrations
- Gmail API adapter (sandbox)
- Twilio WhatsApp Sandbox adapter
- Embeddable Web Support Form (React/Next.js) with client/server validation
- Channel-specific response generation (formal/casual/semi-formal with emoji guidelines)
- **Estimated Time**: 5-7 days

### Phase 6: Ticket Management & Cross-Channel Features
- Ticket CRUD operations
- Customer identification service (97%+ accuracy via pgvector)
- Conversation thread management
- Cross-channel context continuity
- **Estimated Time**: 4-6 days

### Phase 7: Observability & Reporting
- Structured logging (JSON) with correlation IDs
- Metrics collection (Prometheus/Grafana)
- Distributed tracing (OpenTelemetry)
- Daily sentiment report generation (email delivery by 9:00 AM)
- Alert thresholds configuration
- **Estimated Time**: 3-5 days

### Phase 8: Kubernetes Deployment
- Kubernetes manifests for all services
- Horizontal Pod Autoscaler configuration (CPU/memory/custom metrics)
- Health checks (liveness/readiness probes)
- Rolling update strategy
- Secrets and ConfigMaps
- CI/CD pipeline setup
- **Estimated Time**: 5-7 days

### Phase 9: Testing & Quality Assurance
- Unit tests (pytest)
- Integration tests
- End-to-end tests
- Load testing (100+ web forms, 50+ Gmail, 50+ WhatsApp)
- Chaos testing (24-hour, random pod kills, 5s latency, 90% resource exhaustion)
- Security scanning
- **Estimated Time**: 4-6 days

### Phase 10: Production Deployment
- Staging deployment
- Performance validation
- 24-hour chaos test execution
- Production deployment
- Monitoring verification
- **Estimated Time**: 3-5 days

## Total Implementation Timeline Estimate

**Minimum Viable Product (MVP)**: 18-25 days (3-4 weeks)
- Core infrastructure + AI agent + 1 channel (web form)
- Basic ticket management
- Single-channel customer identification

**Production-Grade System**: 32-49 days (5-8 weeks)
- All 3 channels fully functional
- Cross-channel identification (97%+ accuracy)
- Kubernetes deployment
- Chaos testing passed
- Full observability stack

**Recommended Approach**:
1. Start with MVP (Phase 2-5 focused on web form only)
2. Deploy and validate MVP (3-4 weeks)
3. Add remaining channels and production features (2-4 weeks)
4. Kubernetes deployment and chaos testing (1-2 weeks)

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenAI API rate limits | HIGH | Implement caching, fallback to human escalation, optimize token usage |
| pgvector performance issues | MEDIUM | Proper indexing, limit embedding dimensions, use connection pooling |
| Kafka message loss | CRITICAL | Enable idempotency, implement dead letter queues, monitor consumer lag |
| Cross-channel ID accuracy <97% | HIGH | A/B test different embedding models, add fuzzy matching, manual review loop |
| Chaos testing failures | CRITICAL | Start with smaller tests, gradually increase complexity, fix issues before full 24h test |
| Cost overruns ($1000/year) | MEDIUM | Continuous monitoring, optimize API usage, use spot instances where possible |

## Dependencies & External Services

### Required External APIs
- OpenAI API (GPT-4o, embeddings)
- Gmail API (OAuth2, webhook/polling)
- Twilio API (WhatsApp Sandbox)
- [Optional] Sentry (error tracking)
- [Optional] Datadog/Prometheus (monitoring)

### Infrastructure Requirements
- Kubernetes cluster (GKE, EKS, AKS, or self-hosted)
- PostgreSQL 15 with pgvector extension
- Apache Kafka cluster (Confluent Cloud or self-hosted)
- Object storage (for documentation, attachments)

## Success Gates

Before proceeding to production, the system must pass these gates:

### Gate 1: MVP Validation (Week 3-4)
- ✅ All P1 user stories working independently
- ✅ 75%+ resolution rate by AI
- ✅ Sub-3-second response latency (p95)
- ✅ Zero message loss under normal load

### Gate 2: Multi-Channel Validation (Week 6-7)
- ✅ All 3 channels operational
- ✅ 97%+ cross-channel identification accuracy
- ✅ <20% escalation rate
- ✅ Channel-aware responses verified

### Gate 3: Chaos Test Gate (Week 7-8)
- ✅ 24-hour chaos test completed
- ✅ 100+ web forms, 50+ Gmail, 50+ WhatsApp processed
- ✅ Random pod kills survived with zero data loss
- ✅ Network latency injection handled gracefully
- ✅ Resource exhaustion tests passed
- ✅ Overall uptime >99.9%

### Gate 4: Production Deployment Gate (Week 8)
- ✅ All tests passing
- ✅ Security scans clean
- ✅ Documentation complete
- ✅ Monitoring alerts configured
- ✅ Rollback procedure validated

## Architecture Decision Records (ADRs)

As architecturally significant decisions are made during implementation, ADRs will be created and linked here.

### ADR-001: Kafka for Message Queueing (Decision Made)
**Status**: ✅ Decided
**Rationale**: Required by Constitution Principle VIII. Provides guaranteed delivery, ordering, backpressure handling, and decoupling of channel integrations from core agent processing.

### Pending ADRs
- Kubernetes cluster provider (GKE vs EKS vs AKS vs self-hosted)
- Monitoring stack (Prometheus/Grafana vs Datadog vs CloudWatch)
- CI/CD pipeline (GitHub Actions vs GitLab CI vs Jenkins)
- Secrets management (Kubernetes Secrets vs AWS Secrets Manager vs HashiCorp Vault)

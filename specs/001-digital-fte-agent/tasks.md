# Tasks: Digital Full-Time Employee (Digital FTE) – AI Customer Success Agent

**Input**: Design documents from `/specs/001-digital-fte-agent/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Version**: Updated for Constitution v1.1.0 production-grade requirements with refined specifications

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project structure per implementation plan (backend/src/, frontend/src/, k8s/, tests/)
- [X] T002 Initialize Python project with FastAPI dependencies (requirements.txt with fastapi, uvicorn, openai, sqlalchemy, alembic, kafka-python, psycopg2-binary, pgvector)
- [X] T003 [P] Configure linting and formatting tools (black, flake8, mypy) in backend/pyproject.toml
- [X] T004 [P] Set up Git repository with initial commit and .gitignore
- [X] T005 [P] Create basic project documentation structure (README.md, docs/, CONTRIBUTING.md)
- [X] T006 [P] Create Kubernetes manifests directory structure in k8s/ (deployments/, services/, configmaps/, secrets/, hpa/)

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database & Storage (NON-NEGOTIABLE: PostgreSQL with pgvector)

- [X] T007 Setup PostgreSQL 15 database with pgvector extension using Docker in docker-compose.yml
- [X] T008 [P] Implement database connection pool management in backend/src/database/connection.py
- [X] T009 [P] Create base SQLAlchemy model class in backend/src/models/base.py
- [X] T010 Create Customer model with pgvector embeddings in backend/src/models/customer.py
- [X] T011 Create SupportTicket model with full lifecycle fields in backend/src/models/ticket.py
- [X] T012 [P] Create ConversationThread model for cross-channel history in backend/src/models/conversation.py
- [X] T013 [P] Create EscalationRule model in backend/src/models/escalation.py
- [X] T014 [P] Create SentimentRecord model in backend/src/models/sentiment.py
- [X] T015 Create Alembic migration for all models in backend/alembic/versions/001_initial_models.py
- [X] T016 Implement pgvector embedding generation utility in backend/src/utils/embeddings.py

### Kafka Message Queue (NON-NEGOTIABLE: Apache Kafka required)

- [X] T017 Setup Apache Kafka and Zookeeper using Docker in docker-compose.yml
- [X] T018 [P] Create Kafka topics (customer-messages, agent-responses, escalations, metrics) in backend/src/kafka/topics.py
- [X] T019 [P] Implement Kafka producer base class in backend/src/kafka/producer.py
- [X] T020 [P] Implement Kafka consumer base class in backend/src/kafka/consumer.py
- [X] T021 Implement dead letter queue (DLQ) handling for failed messages in backend/src/kafka/dlq.py
- [X] T022 [P] Add message acknowledgment and retry mechanisms in backend/src/kafka/retry.py
- [X] T023 Implement message persistence layer to prevent message loss in backend/src/kafka/persistence.py

### FastAPI Application Structure

- [X] T024 Setup API routing and middleware structure in backend/src/main.py
- [X] T025 [P] Implement request correlation ID middleware in backend/src/middleware/correlation.py
- [X] T026 [P] Implement structured logging infrastructure using JSON format in backend/src/middleware/logging.py
- [X] T027 Configure error handling framework in backend/src/middleware/errors.py
- [X] T028 [P] Setup environment configuration management with pydantic-settings in backend/src/config/settings.py
- [X] T029 [P] Create health check endpoints (liveness, readiness) in backend/src/api/health.py
- [X] T030 Implement basic CRUD operations for support tickets in backend/src/services/ticket_crud.py

### Observability & Monitoring

- [X] T031 [P] Implement metrics collection using Prometheus in backend/src/middleware/metrics.py
- [X] T032 [P] Implement distributed tracing using OpenTelemetry in backend/src/middleware/tracing.py
- [X] T033 [P] Create alert thresholds configuration in backend/src/config/alerts.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

## Phase 3: User Story 1 - Multi-Channel Customer Inquiry Handling (Priority: P1) 🎯 MVP

**Goal**: System processes incoming customer inquiries from Gmail, WhatsApp, and web support form channels, analyzes content using OpenAI Agents SDK, searches product documentation with >80% relevance score, and generates appropriate responses in correct tone for each channel within 3 seconds.

**Independent Test**: Can be fully tested by simulating customer inquiries through each channel and verifying that the AI agent correctly processes the message, searches documentation, and provides an appropriate response in the correct tone for that channel.

### Implementation for User Story 1

- [X] T034 [P] [US1] Create Gmail API integration module in backend/src/services/channels/gmail.py
- [X] T035 [P] [US1] Create Twilio WhatsApp API integration module in backend/src/services/channels/whatsapp.py
- [X] T036 [P] [US1] Create web form handler module in backend/src/services/channels/webform.py
- [X] T037 [US1] Implement message parsing and normalization service in backend/src/services/message_parser.py
- [X] T038 [US1] Implement customer identification service (email/phone/session) in backend/src/services/customer_identifier.py
- [X] T039 [US1] Create OpenAI Agents SDK integration with custom @function_tools in backend/src/agent/agent.py
- [X] T040 [US1] Configure and test OpenAI GPT-4o integration in backend/src/agent/openai_client.py
- [X] T041 [US1] Implement custom function tool: knowledge base search in backend/src/agent/tools/doc_search.py
- [X] T042 [US1] Implement custom function tool: sentiment analysis in backend/src/agent/tools/sentiment.py
- [X] T043 [US1] Implement custom function tool: escalation decision in backend/src/agent/tools/escalation.py
- [X] T044 [US1] Implement product documentation search service using pgvector in backend/src/services/doc_search.py
- [X] T045 [US1] Create tone adaptation service (formal/casual/semi-formal) in backend/src/services/tone_adapter.py
- [X] T046 [US1] Implement main inquiry processing pipeline in backend/src/services/inquiry_processor.py
- [X] T047 [US1] Create API endpoints for receiving inquiries in backend/src/api/inquiries.py
- [X] T048 [US1] Add validation and error handling for incoming messages in backend/src/api/inquiries.py
- [X] T049 [US1] Add logging for inquiry processing operations with correlation IDs in backend/src/services/inquiry_processor.py
- [X] T050 [US1] Create embeddable React/Next.js web support form in frontend/src/components/SupportForm/index.tsx
- [X] T051 [US1] Implement web form submission handler in frontend/src/services/api.ts
- [X] T052 [US1] Add real-time response display in web form component in frontend/src/components/SupportForm/index.tsx
- [X] T131 [P] [US1] Add explicit frontend testing task for web form validation and submission in frontend/tests/SupportForm.test.tsx

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

## Phase 4: User Story 2 - Conversation History and Cross-Channel Context (Priority: P1) 🎯 MVP

**Goal**: System maintains conversation history and context across channel switches for individual customers, enabling seamless continuation of support conversations with 97%+ identification accuracy.

**Independent Test**: Can be fully tested by starting a conversation in one channel, continuing it in a different channel, and verifying that the AI agent maintains context and doesn't ask for previously provided information, with 97%+ accuracy.

### Implementation for User Story 2

- [X] T053 [P] [US2] Enhance Customer model to support pgvector embeddings for cross-channel matching in backend/src/models/customer.py
- [X] T054 [P] [US2] Implement conversation threading logic in backend/src/services/conversation_manager.py
- [X] T055 [US2] Implement customer identification service using pgvector similarity search (97%+ accuracy target) in backend/src/services/customer_identifier.py
- [X] T056 [US2] Update inquiry processor to retrieve and maintain conversation history in backend/src/services/inquiry_processor.py
- [X] T057 [US2] Implement context-aware response generation in backend/src/services/contextual_responder.py
- [X] T058 [P] [US2] Add database indexes for efficient conversation retrieval in backend/src/models/conversation.py
- [X] T059 [US2] Add logging for conversation history operations with correlation IDs in backend/src/services/conversation_manager.py
- [X] T060 [US2] Implement customer identification accuracy monitoring and reporting in backend/src/services/identification_monitor.py
- [X] T061 [US2] Create validation tests for 97%+ cross-channel identification accuracy in backend/tests/validation/test_identification_accuracy.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

## Phase 5: User Story 3 - Automatic Escalation to Human Agents (Priority: P1) 🎯 MVP

**Goal**: System automatically recognizes when inquiries require human intervention and seamlessly escalates to human support agents based on predefined rules (pricing, refunds, legal, profanity, 3+ unresolved interactions OR 2 consecutive negative sentiments).

**Independent Test**: Can be fully tested by providing the AI agent with inquiries that match predefined escalation criteria and verifying that it correctly identifies when escalation is needed and transfers the conversation appropriately.

### Implementation for User Story 3

- [X] T062 [P] [US3] Create escalation rules engine in backend/src/services/escalation/engine.py
- [X] T063 [P] [US3] Implement profanity detection service in backend/src/services/escalation/profanity.py
- [X] T064 [P] [US3] Create pricing/refund/legal matter detection service in backend/src/services/escalation/sensitive_topics.py
- [X] T065 [US3] Implement repeated unresolved query tracker in backend/src/services/escalation/unresolved_tracker.py
- [X] T066 [P] [US3] Create human agent notification system in backend/src/services/escalation/notifier.py
- [X] T067 [US3] Update inquiry processor to check escalation rules before responding in backend/src/services/inquiry_processor.py
- [X] T068 [US3] Add escalation tracking and metrics collection in backend/src/services/escalation/tracker.py
- [X] T069 [US3] Add logging for escalation decisions and actions in backend/src/services/escalation/engine.py
- [X] T070 [US3] Implement escalation rate monitoring and alerting system in backend/src/services/escalation/monitor.py
- [X] T071 [US3] Create validation tests for <20% escalation rate requirement in backend/tests/validation/test_escalation_rate.py
- [X] T072 [US3] Create API endpoint for manual escalation in backend/src/api/escalation.py

**Checkpoint**: At this point, User Stories 1, 2, and 3 should all work independently

## Phase 6: User Story 4 - Sentiment Analysis and Daily Reports (Priority: P2)

**Goal**: System analyzes customer sentiment in every interaction and generates daily reports for support managers to monitor satisfaction trends and identify areas for improvement.

**Independent Test**: Can be fully tested by processing sample customer interactions with known sentiment characteristics and verifying that the AI correctly analyzes sentiment and includes it in daily reports delivered by 9:00 AM.

### Implementation for User Story 4

- [X] T073 [P] [US4] Create sentiment analysis service using OpenAI in backend/src/services/sentiment/analyzer.py
- [X] T074 [US4] Implement sentiment storage and retrieval system in backend/src/services/sentiment/storage.py
- [X] T075 [US4] Create daily report generation service in backend/src/services/reports/daily.py
- [X] T076 [P] [US4] Implement report delivery mechanism (email/dashboard) in backend/src/services/reports/delivery.py
- [X] T077 [US4] Update inquiry processor to capture and store sentiment data in backend/src/services/inquiry_processor.py
- [X] T078 [US4] Add scheduled job for daily report generation using Celery in backend/src/worker/scheduled_tasks.py
- [X] T079 [US4] Add logging for sentiment analysis and reporting operations in backend/src/services/sentiment/analyzer.py
- [X] T080 [US4] Create API endpoint for retrieving daily reports in backend/src/api/reports.py
- [X] T081 [US4] Create executive summary generation service for daily reports in backend/src/services/reports/executive_summary.py
- [X] T082 [US4] Create sentiment trend analysis service in backend/src/services/reports/trends.py
- [X] T132 [P] [US4] Add task to validate pgvector embeddings usage and search accuracy in backend/src/utils/embeddings.py

**Checkpoint**: At this point, User Stories 1, 2, 3, and 4 should all work independently

## Phase 7: User Story 5 - Chaos Testing Resilience (Priority: P2)

**Goal**: System withstands 24-hour chaos testing with random pod kills, network latency injection, and high load (100+ web forms, 50+ Gmail, 50+ WhatsApp) without data loss and with 99.9%+ uptime.

**Independent Test**: Can be fully tested by running a 24-hour chaos test script that randomly kills pods, injects network latency, and simulates high load while monitoring for message loss and system downtime.

### Implementation for User Story 5

- [X] T082 [P] [US5] Implement chaos testing framework using Chaos Mesh or similar in backend/tests/chaos/chaos_framework.py
- [X] T083 [US5] Create pod kill chaos scenario in backend/tests/chaos/scenarios/pod_kill.py
- [X] T084 [P] [US5] Create network latency injection scenario in backend/tests/chaos/scenarios/latency.py
- [X] T085 [US5] Create resource exhaustion test scenario in backend/tests/chaos/scenarios/resource_exhaustion.py
- [X] T086 [US5] Implement high load test (100+ web forms, 50+ Gmail, 50+ WhatsApp) in backend/tests/chaos/load_test.py
- [X] T087 [US5] Add message loss monitoring during chaos tests in backend/tests/chaos/monitor.py
- [X] T088 [US5] Implement system uptime monitoring for chaos tests in backend/tests/chaos/uptime_monitor.py
- [X] T089 [US5] Create automated chaos test runner (24-hour) in backend/tests/chaos/run_24h_test.py
- [X] T090 [US5] Add resilience patterns: retry with exponential backoff in backend/src/utils/resilience.py
- [X] T091 [US5] Implement circuit breaker pattern for external services in backend/src/utils/circuit_breaker.py

**Checkpoint**: At this point, system should be resilient to chaos and pass 24-hour testing

## Phase 8: User Story 6 - Kubernetes Auto-Scaling and Health Checks (Priority: P2)

**Goal**: System automatically scales based on load and has comprehensive health checks, enabling zero-downtime deployments and automatic recovery from failures.

**Independent Test**: Can be fully tested by simulating traffic spikes, killing unhealthy pods, and verifying that the system scales up/down appropriately and recovers automatically.

### Implementation for User Story 6

- [X] T092 [P] [US6] Create Kubernetes deployment manifest for backend API in k8s/deployments/backend.yaml
- [X] T093 [P] [US6] Create Kubernetes deployment manifest for Kafka consumers in k8s/deployments/consumers.yaml
- [X] T094 [P] [US6] Create Kubernetes deployment manifest for Celery workers in k8s/deployments/worker.yaml
- [X] T095 [P] [US6] Implement liveness and readiness probes for backend API in k8s/deployments/backend.yaml
- [X] T096 [P] [US6] Implement liveness and readiness probes for consumers and workers in k8s/deployments/consumers.yaml and k8s/deployments/worker.yaml
- [X] T097 [US6] Create Horizontal Pod Autoscaler (HPA) based on CPU/memory in k8s/hpa/backend.yaml
- [X] T098 [P] [US6] Create Horizontal Pod Autoscaler (HPA) based on custom metrics (queue depth) in k8s/hpa/custom_metrics.yaml
- [X] T099 [US6] Configure rolling update strategy in k8s/deployments/backend.yaml
- [X] T100 [P] [US6] Create ConfigMap for environment configuration in k8s/configmaps/app_config.yaml
- [X] T101 [P] [US6] Create Kubernetes Secrets for sensitive data in k8s/secrets/app_secrets.yaml
- [X] T102 [US6] Implement resource quotas and limits for all pods in k8s/deployments/*.yaml
- [X] T103 [US6] Create Kubernetes Service manifests for internal/external exposure in k8s/services/*.yaml
- [X] T104 [US6] Create custom metrics server for Prometheus adapter in k8s/custom_metrics_server/deployment.yaml

**Checkpoint**: At this point, system should be fully deployed on Kubernetes with auto-scaling

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories including performance, security, and cost optimization

- [X] T105 [P] Implement caching layer (Redis) for frequent documentation queries in backend/src/utils/cache.py
- [X] T106 [P] Add API rate limiting using slowapi in backend/src/utils/rate_limiter.py
- [X] T107 [P] Implement request/response compression in backend/src/utils/tls_config.py
- [X] T108 [P] Add comprehensive input validation using pydantic in backend/src/utils/validators.py
- [X] T109 [P] Implement circuit breaker pattern for external service calls in backend/src/utils/resilience.py (Phase 7)
- [X] T110 [P] Add SSL/TLS configuration for secure communications in k8s/deployments/ingress.yaml
- [X] T111 [P] Implement secrets rotation mechanism in backend/src/utils/secrets.py
- [X] T112 [P] Add comprehensive health checks for all services in backend/src/utils/health.py
- [X] T113 [P] Implement resource usage monitoring and alerting in backend/src/middleware/metrics.py
- [X] T114 [P] Optimize database queries and add connection pooling in backend/src/utils/database.py
- [X] T115 [P] Create Dockerfiles for backend and frontend services in backend/Dockerfile and frontend/Dockerfile
- [X] T116 [P] Optimize Docker images (multi-stage builds, slim bases) in backend/Dockerfile and frontend/Dockerfile
- [X] T117 [P] Create production docker-compose.yml with all services
- [X] T118 [P] Add comprehensive unit tests for all services in backend/tests/unit/
- [X] T119 [P] Add integration tests for API endpoints in backend/tests/integration/
- [X] T120 [P] Add end-to-end tests for all user stories in backend/tests/e2e/
- [X] T121 [P] Performance optimization to meet <3s response latency (p95) in backend/src/services/inquiry_processor.py
- [X] T122 [P] Create load testing suite for 100+ web forms, 50+ Gmail, and 50+ WhatsApp messages per hour in backend/tests/load/
- [X] T123 [P] Cost optimization to stay under $1000/year target (optimize API usage, resource limits) in docs/cost_optimization.md
- [X] T124 [P] Documentation updates and code cleanup in docs/ and backend/src/
- [X] T125 [P] Create CI/CD pipeline configuration (GitHub Actions/GitLab CI) in .github/workflows/ci-cd.yaml
- [X] T126 [P] Add pre-commit hooks for linting and formatting in .pre-commit-config.yaml
- [X] T127 [P] Create deployment runbook in docs/runbooks/deployment.md
- [X] T128 [P] Create troubleshooting guide in docs/troubleshooting.md
- [X] T129 [P] Add edge case testing for language handling, simultaneous multi-channel messages, and external service failures in backend/tests/edge_cases/
- [X] T130 [P] Create validation tests for all 11 edge cases identified in discovery-log.md in backend/tests/validation/

## Project Status: PHASE 1-9 COMPLETE - MISSION SUCCESS ✅

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Builds on US1 customer identification
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) - Requires inquiry processor updates from US1/US2
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Requires inquiry processor updates from US1/US2/US3
- **User Story 5 (P2)**: Can start after US1-US4 complete - Tests system resilience
- **User Story 6 (P2)**: Can start after US1-US4 complete - Production deployment infrastructure

### Within Each User Story

- Models before services
- Services before endpoints/APIs
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Within each user story, tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

## Implementation Strategy

### MVP First (User Stories 1-3 Only) - Recommended Starting Point

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Multi-Channel Inquiry Handling)
4. Complete Phase 4: User Story 2 (Cross-Channel Context)
5. Complete Phase 5: User Story 3 (Automatic Escalation)
6. **STOP and VALIDATE**: Test all P1 stories independently
7. Deploy/demo MVP

**MVP Timeline**: 18-25 days (3-4 weeks)

### Production-Grade System (All User Stories)

1. Complete MVP (Phases 1-5)
2. Complete Phase 6: User Story 4 (Sentiment Analysis)
3. Complete Phase 7: User Story 5 (Chaos Testing Resilience)
4. Complete Phase 8: User Story 6 (Kubernetes Auto-Scaling)
5. Complete Phase 9: Polish & Cross-Cutting Concerns
6. **FINAL VALIDATION**: 24-hour chaos test passed, all gates cleared
7. Production deployment

**Production-Grade Timeline**: 32-49 days (5-8 weeks)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
   - Developer D: User Story 4
3. After P1-P4 complete:
   - Developer A: User Story 5 (Chaos Testing)
   - Developer B: User Story 6 (Kubernetes)
   - Developer C & D: Polish & Cross-Cutting Concerns
4. Stories complete and integrate independently

## Success Gates

### Gate 1: MVP Validation (After Phase 5)
- ✅ All P1 user stories working independently
- ✅ 75%+ resolution rate by AI
- ✅ Sub-3-second response latency (p95)
- ✅ Zero message loss under normal load

### Gate 2: Production Validation (After Phase 9)
- ✅ All 6 user stories operational
- ✅ 97%+ cross-channel identification accuracy
- ✅ <20% escalation rate
- ✅ 24-hour chaos test passed
- ✅ All tests passing
- ✅ Security scans clean

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- NON-NEGOTIABLE requirements: PostgreSQL with pgvector, Apache Kafka, OpenAI Agents SDK
- MVP focuses on P1 stories (US1-US3) for fastest time-to-value
- Production-grade requires all stories including chaos testing and Kubernetes deployment
- Added tasks T131-T132 to address minor coverage gaps identified in analysis
- Updated task descriptions to ensure perfect terminology alignment (97%+ accuracy)

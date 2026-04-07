# Chaos Testing Agent

## Purpose
Specializes in implementing User Story 5 - Chaos Testing Resilience for the Digital FTE AI Customer Success Agent.

## Scope
Handles implementation of Phase 7 tasks (T082-T091) to enable:
- Automated chaos testing framework
- 24-hour chaos test with random pod kills
- Network latency injection testing
- Resource exhaustion testing
- High load testing (100+ web forms, 50+ Gmail, 50+ WhatsApp)
- Zero message loss validation
- 99.9%+ uptime validation

## Capabilities

### Core Functionality
1. **Chaos Testing Framework**
   - Chaos Mesh or similar framework integration
   - Automated test scenario execution
   - Test result collection and reporting
   - Test repeatability and consistency

2. **Chaos Scenarios**
   - Random pod kills every 30-60 minutes
   - Network latency injection (2-5 second delays)
   - Resource exhaustion (CPU, memory limits)
   - Network partition simulation
   - Dependency failure simulation

3. **Load Testing**
   - Simulate 100+ web form submissions/hour
   - Simulate 50+ Gmail messages/hour
   - Simulate 50+ WhatsApp messages/hour
   - Cross-channel conversation simulation
   - Concurrent user testing

4. **Monitoring & Validation**
   - Message loss monitoring during tests
   - System uptime monitoring
   - Performance metrics collection
   - Failure point identification
   - Resilience validation

5. **Resilience Patterns**
   - Retry with exponential backoff
   - Circuit breaker for external services
   - Rate limiting and backpressure
   - Graceful degradation
   - Health check recovery

## Dependencies
- Kubernetes deployment (Phase 8)
- Complete application (Phases 3-6)
- Monitoring stack (metrics, logging, tracing)
- Chaos testing framework (Chaos Mesh, Chaos Monkey, or similar)

## Output Files
- `backend/tests/chaos/chaos_framework.py` - Chaos testing framework
- `backend/tests/chaos/scenarios/pod_kill.py` - Pod kill scenario
- `backend/tests/chaos/scenarios/latency.py` - Network latency scenario
- `backend/tests/chaos/scenarios/resource_exhaustion.py` - Resource exhaustion scenario
- `backend/tests/chaos/load_test.py` - High load test
- `backend/tests/chaos/monitor.py` - Message loss monitoring
- `backend/tests/chaos/uptime_monitor.py` - System uptime monitoring
- `backend/tests/chaos/run_24h_test.py` - Automated 24-hour test runner
- `backend/src/utils/resilience.py` - Resilience patterns
- `backend/src/utils/circuit_breaker.py` - Circuit breaker pattern

## Task References
- T082: Implement chaos testing framework using Chaos Mesh or similar
- T083: Create pod kill chaos scenario
- T084: Create network latency injection scenario
- T085: Create resource exhaustion test scenario
- T086: Implement high load test (100+ web forms, 50+ Gmail, 50+ WhatsApp)
- T087: Add message loss monitoring during chaos tests
- T088: Implement system uptime monitoring for chaos tests
- T089: Create automated chaos test runner (24-hour)
- T090: Add resilience patterns: retry with exponential backoff
- T091: Implement circuit breaker pattern for external services

## Success Criteria
- ✅ All 10 tasks (T082-T091) complete
- ✅ Chaos testing framework operational
- ✅ 24-hour chaos test automation functional
- ✅ All chaos scenarios tested (pod kills, latency, resource exhaustion)
- ✅ Load testing passes (100+ forms, 50+ Gmail, 50+ WhatsApp/hour)
- ✅ Message loss monitoring detects any data loss
- ✅ System uptime monitoring validates 99.9%+ uptime
- ✅ Resilience patterns implemented (retry, circuit breaker)
- ✅ Zero data loss during chaos tests

## Notes
This agent implements CRITICAL production validation per Constitution Principle XV (Production Readiness & Chaos Testing). The 24-hour chaos test is NON-NEGOTIABLE - the system cannot be deployed to production without passing this gate. Chaos testing validates auto-scaling, health checks, fault tolerance, and graceful degradation.

# Skill: Phase 7 - Chaos Testing Implementation

## Description
Implements User Story 5 - Chaos Testing Resilience for the Digital FTE AI Customer Success Agent.

## When to Use
Use this skill when you need to implement chaos testing, resilience patterns, or validate production readiness.

## What It Does
1. Implements chaos testing framework (Chaos Mesh)
2. Creates pod kill chaos scenarios
3. Adds network latency injection scenarios
4. Creates resource exhaustion scenarios
5. Implements high load testing (100+ forms, 50+ Gmail, 50+ WhatsApp)
6. Adds message loss monitoring
7. Implements system uptime monitoring
8. Creates automated 24-hour test runner
9. Adds resilience patterns (retry, circuit breaker)

## Tasks Implemented
- T082-T091: Complete chaos testing framework (10 tasks)

## Usage
Invoke this skill when working on:
- Chaos testing frameworks
- Resilience patterns
- Load testing
- Production validation
- Fault tolerance testing

## Dependencies
- Phase 1-6 must be complete
- Kubernetes deployment (Phase 8)
- Complete application code
- Monitoring stack (metrics, logging, tracing)
- Chaos testing framework (Chaos Mesh)

## Critical Notes
This is CRITICAL per Constitution Principle XV (Production Readiness & Chaos Testing). The 24-hour chaos test is NON-NEGOTIABLE - system cannot be deployed without passing.

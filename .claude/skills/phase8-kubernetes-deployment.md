# Skill: Phase 8 - Kubernetes Deployment Implementation

## Description
Implements User Story 6 - Kubernetes Auto-Scaling and Health Checks for the Digital FTE AI Customer Success Agent.

## When to Use
Use this skill when you need to complete Kubernetes deployment, configure auto-scaling, or add health checks.

## What It Does
1. Creates Kubernetes deployment manifests for consumers and workers
2. Implements liveness and readiness probes
3. Configures Horizontal Pod Autoscalers (HPA)
4. Creates custom metrics server
5. Configures rolling update strategy
6. Implements resource quotas and limits

## Tasks Implemented
- T093-T104: Complete Kubernetes deployment (11 tasks, 4 already complete)

## Usage
Invoke this skill when working on:
- Kubernetes manifests
- Auto-scaling configuration
- Health checks (liveness/readiness probes)
- Rolling updates
- Resource quotas

## Dependencies
- Phase 1-7 must be complete
- Docker containers for all services
- Kubernetes cluster
- Monitoring stack (Prometheus/Grafana)

## Critical Notes
This is NON-NEGOTIABLE per Constitution Principle XVI (Kubernetes Deployment). All services must be deployed on Kubernetes with auto-scaling, health checks, and resource management.

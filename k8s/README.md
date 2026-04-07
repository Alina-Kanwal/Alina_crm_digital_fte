# Digital FTE AI Customer Success Agent - Kubernetes Deployment

Complete Kubernetes deployment manifests for the Digital FTE AI Customer Success Agent.

## Overview

This directory contains all Kubernetes manifests required for production deployment of the Digital FTE system, including:

- **Deployments**: Backend API, Kafka consumers, Celery workers
- **Services**: Internal and external communication
- **HPA (Horizontal Pod Autoscaler)**: Auto-scaling based on CPU/memory and custom metrics
- **ConfigMaps/Secrets**: Configuration management
- **Ingress**: External access with SSL/TLS
- **Resource Quotas**: Namespace resource limits
- **Custom Metrics Server**: Prometheus adapter for HPA custom metrics

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Ingress (NGINX)                        │
│                    SSL/TLS Termination                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬──────────────┐
        │             │             │              │
┌───────▼──────┐ ┌──▼──────────┐ ┌─▼──────────┐ ┌─▼──────────┐
│   Backend    │ │  Consumers   │ │   Workers   │ │ Monitoring │
│     API       │ │  (Kafka)     │ │  (Celery)   │ │ (Prometheus)│
│   (2-10)     │ │   (3-10)     │ │   (2-5)     │ │  (Grafana)  │
└───────┬──────┘ └──┬──────────┘ └─┬──────────┘ └────────────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
        ┌─────────────┼─────────────┬──────────────┐
        │             │             │              │
┌───────▼──────┐ ┌─▼──────────┐ ┌─▼──────────┐ ┌─▼──────────┐
│  PostgreSQL   │ │    Kafka     │ │   Redis     │ │   Email    │
│   (pgvector) │ │  (Messages)  │ │   (Cache)   │ │  (SMTP)    │
└──────────────┘ └─────────────┘ └────────────┘ └────────────┘
```

## Prerequisites

### Required Tools

- Kubernetes cluster (v1.25+)
- kubectl configured
- Docker/Podman for building images
- Helm (optional, for monitoring stack)

### Required Components

- PostgreSQL 15 with pgvector extension
- Apache Kafka (or Confluent Cloud)
- Redis (for caching and Celery broker)
- NGINX Ingress Controller
- Cert-Manager (for SSL/TLS certificates)
- Prometheus + Grafana (for monitoring)

## Directory Structure

```
k8s/
├── deployments/              # Application deployments
│   ├── backend.yaml         # Backend API deployment
│   ├── consumers.yaml       # Kafka consumers deployment
│   └── worker.yaml         # Celery workers deployment
├── services/               # Service manifests
│   ├── consumers.yaml       # Consumer services
│   └── workers.yaml        # Worker services
├── hpa/                   # Horizontal Pod Autoscalers
│   ├── backend.yaml        # Backend HPA (CPU/memory)
│   └── custom_metrics.yaml # Custom metrics HPA (queue depth)
├── configmaps/            # Configuration data
│   └── app_config.yaml    # Application configuration
├── secrets/               # Secrets (templates)
│   └── app_secrets.yaml.template
├── custom_metrics_server/  # Prometheus adapter
│   └── deployment.yaml
├── ingress.yaml           # External access configuration
├── namespace.yaml         # Namespace definitions
├── resource-quota.yaml    # Resource limits
└── README.md             # This file
```

## Quick Start

### 1. Create Namespaces

```bash
kubectl apply -f namespace.yaml
```

### 2. Create Resource Quotas

```bash
kubectl apply -f resource-quota.yaml
```

### 3. Configure Secrets

```bash
# Copy the template
cp secrets/app_secrets.yaml.template secrets/app_secrets.yaml

# Edit with actual values (base64 encoded)
# Generate base64: echo -n "your-value" | base64
vi secrets/app_secrets.yaml

# Apply secrets
kubectl apply -f secrets/app_secrets.yaml
```

### 4. Deploy ConfigMaps

```bash
kubectl apply -f configmaps/app_config.yaml
```

### 5. Deploy Applications

```bash
# Deploy backend API
kubectl apply -f deployments/backend.yaml

# Deploy Kafka consumers
kubectl apply -f deployments/consumers.yaml

# Deploy Celery workers
kubectl apply -f deployments/worker.yaml

# Deploy services
kubectl apply -f services/consumers.yaml
kubectl apply -f services/workers.yaml
```

### 6. Configure Auto-Scaling

```bash
# Deploy HPA for CPU/memory metrics
kubectl apply -f hpa/backend.yaml

# Deploy HPA for custom metrics
kubectl apply -f hpa/custom_metrics.yaml
```

### 7. Deploy Custom Metrics Server

```bash
kubectl apply -f custom_metrics_server/deployment.yaml
```

### 8. Deploy Ingress

```bash
kubectl apply -f ingress.yaml
```

## Health Checks

All deployments include both liveness and readiness probes:

### Liveness Probe
- **Purpose**: Detect if container is running
- **Failure Action**: Restart container
- **Interval**: 10 seconds
- **Timeout**: 5 seconds
- **Failure Threshold**: 3 failures

### Readiness Probe
- **Purpose**: Detect if container can serve traffic
- **Failure Action**: Remove from service
- **Interval**: 5-10 seconds
- **Timeout**: 3-5 seconds
- **Failure Threshold**: 3 failures

## Auto-Scaling Configuration

### Backend API
- **Min Replicas**: 2
- **Max Replicas**: 10
- **Scale on**: CPU >70%, Memory >80%
- **Scale on**: Request rate >100/sec
- **Scale on**: Latency P95 >2s

### Kafka Consumers
- **Min Replicas**: 3
- **Max Replicas**: 10
- **Scale on**: CPU >70%, Memory >80%
- **Scale on**: Consumer lag >10,000 messages
- **Scale on**: Group lag >10MB

### Celery Workers
- **Min Replicas**: 2
- **Max Replicas**: 5
- **Scale on**: CPU >70%, Memory >80%
- **Scale on**: Queue length >50 tasks
- **Scale on**: Scheduled tasks >10 pending

## Rolling Updates

All deployments use rolling update strategy for zero-downtime deployments:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # Allow 1 extra pod during update
    maxUnavailable: 0   # Never have 0 pods available
```

### Update Procedure

```bash
# Build new image
docker build -t digital-fte-backend:v1.0.1 -f backend/Dockerfile backend/

# Update deployment
kubectl set image deployment/digital-fte-backend backend=digital-fte-backend:v1.0.1

# Monitor rollout
kubectl rollout status deployment/digital-fte-backend

# View rollout history
kubectl rollout history deployment/digital-fte-backend
```

## Resource Limits

### Backend API
- **Request**: 250m CPU, 256Mi Memory
- **Limit**: 1000m CPU, 1Gi Memory

### Kafka Consumers
- **Request**: 200m CPU, 256Mi Memory
- **Limit**: 800m CPU, 512Mi Memory

### Celery Workers
- **Request**: 200m CPU, 256Mi Memory
- **Limit**: 800m CPU, 512Mi Memory

## Monitoring

### View Pod Status

```bash
kubectl get pods -n digital-fte
kubectl describe pod <pod-name> -n digital-fte
```

### View Logs

```bash
# Backend logs
kubectl logs -f deployment/digital-fte-backend -n digital-fte

# Consumer logs
kubectl logs -f deployment/digital-fte-consumers -n digital-fte

# Worker logs
kubectl logs -f deployment/digital-fte-workers -n digital-fte
```

### View HPA Status

```bash
kubectl get hpa -n digital-fte
kubectl describe hpa <hpa-name> -n digital-fte
```

### View Custom Metrics

```bash
# List available custom metrics
kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1/

# Get specific metric
kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1/namespaces/digital-fte/pods/kafka_consumer_lag_messages
```

## Chaos Testing

The chaos testing framework (Phase 7) is compatible with this Kubernetes deployment:

```bash
# Deploy chaos testing tools (using Chaos Mesh or Litmus)
kubectl apply -f chaos-testing/

# Run chaos test
python backend/tests/chaos/run_24h_test.py
```

## Cleanup

```bash
# Remove all resources
kubectl delete -f ingress.yaml
kubectl delete -f hpa/
kubectl delete -f deployments/
kubectl delete -f services/
kubectl delete -f custom_metrics_server/
kubectl delete -f configmaps/
kubectl delete -f secrets/
kubectl delete -f resource-quota.yaml
kubectl delete -f namespace.yaml
```

## Constitution Compliance

This Kubernetes deployment complies with Constitution Principle XVI (Kubernetes Required):

- ✅ Production-ready Kubernetes deployment
- ✅ Comprehensive health checks (liveness/readiness probes)
- ✅ Horizontal Pod Autoscaling (CPU/memory + custom metrics)
- ✅ Rolling update strategy for zero-downtime deployments
- ✅ Resource quotas and limits for cost optimization
- ✅ Custom metrics server for queue-based auto-scaling
- ✅ Ingress controller with SSL/TLS
- ✅ Namespace isolation for security

## Security Best Practices

1. **Secrets Management**: Always use Kubernetes Secrets, never hardcode credentials
2. **Network Policies**: Implement network policies to restrict pod-to-pod communication
3. **RBAC**: Use Role-Based Access Control for least privilege
4. **Image Security**: Use signed images and scan for vulnerabilities
5. **Pod Security Standards**: Enforce Pod Security Standards (PSS/PSC)
6. **Audit Logging**: Enable audit logging for compliance

## Troubleshooting

### Pods Not Starting

```bash
kubectl describe pod <pod-name> -n digital-fte
kubectl logs <pod-name> -n digital-fte --previous
```

### HPA Not Scaling

```bash
kubectl describe hpa <hpa-name> -n digital-fte
kubectl top pods -n digital-fte
```

### Custom Metrics Not Available

```bash
# Check custom metrics server
kubectl logs deployment/custom-metrics-apiserver -n custom-metrics

# Verify Prometheus connection
kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1/
```

## Support

For issues or questions, refer to:
- Constitution: `.specify/memory/constitution.md`
- Spec: `specs/001-digital-fte-agent/spec.md`
- Plan: `specs/001-digital-fte-agent/plan.md`
- Tasks: `specs/001-digital-fte-agent/tasks.md`

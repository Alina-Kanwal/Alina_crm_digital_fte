# Digital FTE Agent - Kubernetes Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Digital FTE (AI Customer Success Agent) to a Kubernetes cluster. The deployment includes:

- Backend FastAPI application with AI agent
- Frontend React/Next.js web support form
- PostgreSQL database with pgvector extension
- Apache Kafka message queue
- Redis cache and Celery workers
- Horizontal Pod Autoscalers (HPA)
- Comprehensive monitoring and observability

## Prerequisites

### Required Tools

- `kubectl` - Kubernetes CLI (v1.24+)
- `helm` - Package manager (optional, v3.0+)
- Docker and Docker Compose
- SSH access to Kubernetes cluster

### Cluster Requirements

- Kubernetes cluster (GKE, EKS, AKS, or self-hosted)
- Minimum 3 worker nodes (recommended 5 for production)
- Node resources per pod:
  - Backend: 500m CPU, 1Gi RAM
  - Frontend: 200m CPU, 512Mi RAM
  - Workers: 1000m CPU, 2Gi RAM
- Total cluster capacity: 4+ vCPU, 16+ Gi RAM

### Required Secrets

Create Kubernetes secrets before deployment:

```bash
kubectl create secret generic digital-fte-secrets \
  --from-literal=postgres-password=<your-password> \
  --from-literal=postgresql-password=<your-password> \
  --from-literal=openai-api-key=<your-openai-key> \
  --from-literal=twilio-account-sid=<your-twilio-sid> \
  --from-literal=twilio-auth-token=<your-twilio-token> \
  --from-literal=gmail-client-id=<your-gmail-client-id> \
  --from-literal=gmail-client-secret=<your-gmail-secret>
```

## Deployment Steps

### Step 1: Build and Push Docker Images

```bash
# Backend
cd backend
docker build -t digital-fte-backend:latest .
docker tag digital-fte-backend:latest <your-registry>/digital-fte-backend:latest
docker push <your-registry>/digital-fte-backend:latest

# Frontend
cd frontend
docker build -t digital-fte-frontend:latest .
docker tag digital-fte-frontend:latest <your-registry>/digital-fte-frontend:latest
docker push <your-registry>/digital-fte-frontend:latest
```

### Step 2: Create Namespace

```bash
kubectl apply -f k8s/namespace.yaml
```

### Step 3: Apply Resource Quota and Limits

```bash
kubectl apply -f k8s/resource-quota.yaml
```

### Step 4: Create ConfigMaps

```bash
kubectl apply -f k8s/configmaps/app_config.yaml
```

### Step 5: Deploy Applications

```bash
# Deploy Backend API
kubectl apply -f k8s/deployments/backend.yaml
kubectl apply -f k8s/services/backend.yaml

# Deploy Kafka Consumers
kubectl apply -f k8s/deployments/consumers.yaml
kubectl apply -f k8s/services/consumers.yaml

# Deploy Celery Workers
kubectl apply -f k8s/deployments/worker.yaml
kubectl apply -f k8s/services/workers.yaml

# Deploy Frontend
kubectl apply -f k8s/deployments/frontend.yaml
kubectl apply -f k8s/services/frontend.yaml
```

### Step 6: Configure Horizontal Pod Autoscaling

```bash
# Backend HPA (CPU/Memory)
kubectl apply -f k8s/hpa/backend.yaml

# Custom Metrics HPA (Queue Depth)
kubectl apply -f k8s/hpa/custom_metrics.yaml
```

### Step 7: Deploy Custom Metrics Server (for Queue Depth)

```bash
kubectl apply -f k8s/custom_metrics_server/deployment.yaml
```

### Step 8: Configure Ingress (Optional)

```bash
kubectl apply -f k8s/ingress.yaml
```

### Step 9: Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n digital-fte

# Check services
kubectl get services -n digital-fte

# Check deployments
kubectl get deployments -n digital-fte

# Check HPAs
kubectl get hpa -n digital-fte
```

## Configuration

### Environment Variables

Key environment variables for the backend:

| Variable | Description | Default | Secret |
|-----------|-------------|---------|--------|
| `DATABASE_URL` | PostgreSQL connection string | - | Yes |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka broker addresses | - | Yes |
| `REDIS_URL` | Redis connection string | - | No |
| `OPENAI_API_KEY` | OpenAI API key | - | Yes |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | - | Yes |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | - | Yes |
| `GMAIL_CLIENT_ID` | Gmail OAuth client ID | - | Yes |
| `GMAIL_CLIENT_SECRET` | Gmail OAuth client secret | - | Yes |

### ConfigMap Settings

Application configuration in `k8s/configmaps/app_config.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: digital-fte-config
  namespace: digital-fte
data:
  ENVIRONMENT: "production"
  LOG_LEVEL: "INFO"
  MAX_CONCURRENT_REQUESTS: "100"
  KAFKA_CONSUMER_GROUP: "digital-fte-group"
  CELERY_TASK_TIMEOUT: "300"
  REPORT_DELIVERY_TIME: "09:00"
  REPORT_TIMEZONE: "UTC"
```

## Health Checks

### Liveness Probe

Checks if the application container is running:

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### Readiness Probe

Checks if the application is ready to serve requests:

```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

## Monitoring

### Metrics

Prometheus metrics available at `/metrics` endpoint:

- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request duration histogram
- `kafka_messages_consumed` - Kafka messages consumed
- `kafka_messages_produced` - Kafka messages produced
- `escalation_rate` - Current escalation rate
- `sentiment_distribution` - Sentiment analysis distribution

### Alerts

Configure alert thresholds in AlertManager:

```yaml
groups:
  - name: digital_fte_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status="500"}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical

      - alert: HighEscalationRate
        expr: escalation_rate > 0.25
        for: 5m
        labels:
          severity: warning

      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds[5m])) > 3
        for: 5m
        labels:
          severity: warning
```

## Scaling

### Horizontal Pod Autoscaler (HPA)

Backend application scales based on:

1. **CPU Usage**: Scale up at 70%, scale down at 20%
2. **Memory Usage**: Scale up at 80%, scale down at 40%
3. **Custom Metric (Queue Depth)**: Scale up when queue depth > 50 messages

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: digital-fte-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: digital-fte-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: External
    external:
      metric:
        name: kafka_queue_depth
      target:
        type: AverageValue
        averageValue: 50
```

## Rolling Updates

Deployment uses rolling update strategy:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 1
    maxSurge: 1
  minReadySeconds: 30
    revisionHistoryLimit: 10
```

## Rollback Procedure

To rollback to previous deployment:

```bash
# Check rollout history
kubectl rollout history deployment/digital-fte-backend -n digital-fte

# Rollback to previous revision
kubectl rollout undo deployment/digital-fte-backend -n digital-fte

# Verify rollback
kubectl get pods -n digital-fte
```

## Troubleshooting

### Common Issues

#### Pods Not Starting

```bash
# Check pod logs
kubectl logs <pod-name> -n digital-fte

# Describe pod for events
kubectl describe pod <pod-name> -n digital-fte

# Common causes:
# - Missing secrets
# - ConfigMap not mounted
# - Database connection failures
# - Kafka connection failures
```

#### High CPU/Memory Usage

```bash
# Check resource usage
kubectl top pods -n digital-fte

# Check node resource usage
kubectl top nodes

# Solutions:
# - Scale up cluster
# - Adjust resource limits
# - Optimize application code
```

#### Database Connection Issues

```bash
# Check PostgreSQL pod
kubectl get pods -n digital-fte | grep postgres

# Check PostgreSQL logs
kubectl logs <postgres-pod-name> -n digital-fte

# Verify secrets are correct
kubectl get secret digital-fte-secrets -n digital-fte -o yaml
```

#### Kafka Connection Issues

```bash
# Check Kafka pod
kubectl get pods -n digital-fte | grep kafka

# Check Kafka logs
kubectl logs <kafka-pod-name> -n digital-fte

# Verify topics exist
kubectl exec -it <kafka-pod-name> -n digital-fte -- \
  kafka-topics.sh --bootstrap-server localhost:9092 --list
```

## Validation Checklist

Before considering deployment complete, verify:

- [ ] All pods are in `Running` state
- [ ] All services have `ClusterIP` or `ExternalIP`
- [ ] Health checks passing (`/health/live`, `/health/ready`)
- [ ] Metrics endpoint accessible (`/metrics`)
- [ ] Secrets are properly mounted
- [ ] ConfigMaps are properly mounted
- [ ] HPA is configured and working
- [ ] Ingress is configured (if needed)
- [ ] Database migrations have run
- [ ] Kafka topics are created
- [ ] Celery workers are processing tasks
- [ ] Frontend can communicate with backend API

## Security Considerations

1. **Network Policies**: Apply network policies to restrict pod-to-pod communication
2. **RBAC**: Create ServiceAccounts and RoleBindings with least privilege
3. **Secrets Rotation**: Implement secrets rotation policy (every 90 days)
4. **Pod Security Context**: Run containers as non-root user
5. **Image Security**: Use only signed and verified images

## Cost Optimization

### Estimated Monthly Costs (3-node cluster)

| Component | vCPU | RAM | Estimated Cost |
|------------|-------|-----|----------------|
| Backend (2 pods) | 1.0 | 2Gi | $20 |
| Frontend (2 pods) | 0.4 | 1Gi | $8 |
| Workers (3 pods) | 3.0 | 6Gi | $60 |
| PostgreSQL | 2.0 | 8Gi | $50 |
| Kafka | 1.5 | 4Gi | $30 |
| Redis | 0.5 | 2Gi | $10 |
| **Total** | **8.4** | **23Gi** | **~$180/month** |

### Cost Reduction Strategies

1. Use spot instances for worker pods (up to 70% savings)
2. Scale down during off-hours (9 PM - 6 AM)
3. Optimize pod resource requests/limits
4. Use right-sizing based on actual usage

Target: **<$1,000/year** (constitution requirement)

## Backup and Disaster Recovery

### Database Backups

```bash
# Create CronJob for daily backups
kubectl apply -f k8s/backup/postgres-backup-cronjob.yaml
```

### Disaster Recovery

1. **RTO (Recovery Time Objective)**: 4 hours
2. **RPO (Recovery Point Objective)**: 1 hour
3. **Backup Retention**: 30 days
4. **Multi-Region**: Recommended for production

## Upgrade Procedure

1. Create new Docker images with version tags
2. Update deployment manifests with new image tags
3. Apply new deployments
4. Monitor health checks during rollout
5. If issues occur, rollback immediately

## Support

For deployment issues:

1. Check logs: `kubectl logs -f <pod-name> -n digital-fte`
2. Check events: `kubectl get events -n digital-fte --sort-by='.lastTimestamp'`
3. Review metrics: Access Grafana dashboard
4. Check documentation: `docs/troubleshooting.md`
5. Contact on-call: Use PagerDuty/Slack escalation

## Success Criteria

Deployment is successful when:

- ✅ All pods running and healthy
- ✅ Health checks passing (99%+ success rate)
- ✅ Metrics being collected
- ✅ Alerts configured and receiving notifications
- ✅ Load test passed (100+ web forms, 50+ Gmail, 50+ WhatsApp)
- ✅ Escalation rate < 20%
- ✅ Response time < 3s (p95)
- ✅ Zero message loss in testing

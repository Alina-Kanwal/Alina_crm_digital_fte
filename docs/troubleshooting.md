# Digital FTE Agent - Troubleshooting Runbook

## Table of Contents

1. [Emergency Response](#emergency-response)
2. [Application Issues](#application-issues)
3. [Database Issues](#database-issues)
4. [Kafka Issues](#kafka-issues)
5. [AI Agent Issues](#ai-agent-issues)
6. [Channel Integration Issues](#channel-integration-issues)
7. [Performance Issues](#performance-issues)
8. [Security Issues](#security-issues)
9. [Common Error Codes](#common-error-codes)

---

## Emergency Response

### Service Outage Procedure

**Severity**: CRITICAL
**Escalation**: Immediate to on-call

#### Step 1: Assess Impact

```bash
# Check overall system health
kubectl get pods -n digital-fte

# Check if critical services are down
kubectl get deployments -n digital-fte

# Check recent error rates
kubectl logs -l app=digital-fte-backend --tail=100 | grep ERROR
```

#### Step 2: Identify Root Cause

Common outage causes:
- Database connection failure
- Kafka cluster down
- All pods crashed (OOMKilled)
- Network partition
- External API failures (OpenAI, Twilio, Gmail)

#### Step 3: Execute Recovery

```bash
# If database down, scale up PostgreSQL
kubectl scale deployment/digital-fte-postgres --replicas=1 -n digital-fte

# If Kafka down, restart Kafka
kubectl rollout restart deployment/digital-fte-kafka -n digital-fte

# If pods crashed, scale up backend
kubectl scale deployment/digital-fte-backend --replicas=3 -n digital-fte

# If external API down, check status page
curl https://status.openai.com
curl https://status.twilio.com
```

#### Step 4: Communicate

- Post incident status to Slack/Teams
- Update status page (if available)
- Notify customers if > 15 minutes expected

#### Step 5: Post-Incident Review

- Document root cause
- Update run procedures
- Create preventative measures

---

## Application Issues

### Application Not Starting

#### Symptoms
- Pods stuck in `Pending` state
- Pods stuck in `CrashLoopBackOff`

#### Diagnosis

```bash
# Check pod events
kubectl describe pod <pod-name> -n digital-fte

# Check pod logs
kubectl logs <pod-name> -n digital-fte --previous

# Common causes:
# - Image pull errors (auth, rate limit)
# - Resource quota exceeded
# - Missing secrets/ConfigMaps
# - Health check failures
```

#### Resolution

**Image Pull Errors**
```bash
# Verify registry access
docker login <your-registry>

# Check image exists
docker pull <image>:<tag>
```

**Resource Quota Exceeded**
```bash
# Check resource quota
kubectl describe resourcequota -n digital-fte

# Request quota increase or scale down other applications
kubectl scale deployment/digital-fte-backend --replicas=2 -n digital-fte
```

**Missing Secrets**
```bash
# List secrets
kubectl get secrets -n digital-fte

# Create missing secret
kubectl create secret generic <secret-name> \
  --from-literal=<key>=<value> \
  -n digital-fte
```

### High Error Rate

#### Symptoms
- Error rate > 5%
- Many HTTP 500 responses
- Customer complaints

#### Diagnosis

```bash
# Check error rate in metrics
curl http://digital-fte-backend/metrics | grep http_requests_total

# Check recent errors
kubectl logs -l app=digital-fte-backend --tail=200 | grep ERROR | tail -50
```

#### Resolution

**Database Connection Errors**
```bash
# Check PostgreSQL pod status
kubectl get pods -n digital-fte | grep postgres

# Restart application pods to reconnect
kubectl rollout restart deployment/digital-fte-backend -n digital-fte
```

**OpenAI API Errors**
```bash
# Check API key is valid
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models

# Check rate limits
# OpenAI: 3,500 RPM for gpt-4o
# Implement caching if hitting limits
```

### Slow Response Times

#### Symptoms
- p95 latency > 3 seconds
- p99 latency > 5 seconds
- Customer complaints about slowness

#### Diagnosis

```bash
# Check response time metrics
curl http://digital-fte-backend/metrics | grep http_request_duration_seconds

# Check database query performance
kubectl exec -it <postgres-pod> -n digital-fte -- \
  psql -U digital_fte -d digital_fte \
  -c "SELECT * FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;"
```

#### Resolution

**Add Database Indexes**
```bash
# Connect to PostgreSQL
kubectl exec -it <postgres-pod> -n digital-fte -- \
  psql -U digital_fte -d digital_fte

# Create missing indexes
CREATE INDEX CONCURRENTLY idx_support_ticket_customer_id
  ON support_tickets(customer_id);
```

**Enable Query Caching**
```bash
# Check Redis is operational
kubectl get pods -n digital-fte | grep redis

# Verify caching is working
kubectl logs -l app=digital-fte-backend | grep -i "cache"
```

**Scale Up Backend**
```bash
# Add more replicas
kubectl scale deployment/digital-fte-backend --replicas=5 -n digital-fte
```

---

## Database Issues

### Database Connection Failures

#### Symptoms
- Application logs show "connection refused"
- Database pods restarting
- Health check `/health/ready` returns "database": "not_ready"

#### Diagnosis

```bash
# Check PostgreSQL pod status
kubectl get pods -n digital-fte -l app=postgres

# Check PostgreSQL logs
kubectl logs <postgres-pod> -n digital-fte

# Test connectivity
kubectl exec -it <backend-pod> -n digital-fte -- \
  psql -h digital-fte-postgres -U digital_fte -d digital_fte -c "SELECT 1;"
```

#### Resolution

**Restart PostgreSQL**
```bash
kubectl rollout restart deployment/digital-fte-postgres -n digital-fte
```

**Increase Connection Pool**
```bash
# Update environment variable in ConfigMap
kubectl edit configmap digital-fte-config -n digital-fte

# Add or update:
DATABASE_POOL_SIZE: "20"
DATABASE_MAX_OVERFLOW: "40"
```

**Check Resource Limits**
```bash
# Check PostgreSQL resource usage
kubectl top pod <postgres-pod> -n digital-fte

# Increase limits if hitting OOM
kubectl edit deployment digital-fte-postgres -n digital-fte
```

### Slow Queries

#### Symptoms
- Database queries taking > 1 second
- High CPU on PostgreSQL pod
- pg_stat_statements shows slow queries

#### Diagnosis

```bash
# Connect to PostgreSQL
kubectl exec -it <postgres-pod> -n digital-fte -- \
  psql -U digital_fte -d digital_fte

# Check slow queries
SELECT query, calls, total_exec_time, mean_exec_time
FROM pg_stat_statements
WHERE total_exec_time > 1000  # > 1 second
ORDER BY total_exec_time DESC
LIMIT 10;
```

#### Resolution

**Add Indexes**
```sql
-- Analyze query patterns
EXPLAIN ANALYZE <your-query>;

-- Create appropriate indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_<column_name>
  ON <table_name>(<column_name>);
```

**VACUUM and ANALYZE**
```bash
# Run maintenance
kubectl exec -it <postgres-pod> -n digital-fte -- \
  psql -U digital_fte -d digital_fte -c "VACUUM ANALYZE;"
```

**Optimize pgvector Searches**
```sql
-- Adjust ivfflat probe count
SET ivfflat.probes = 10;

-- Use appropriate embedding dimension
-- Reduce dimensions if possible for faster searches
```

### Storage Issues

#### Symptoms
- Disk space > 90% full
- WAL files growing
- Cannot insert new data

#### Diagnosis

```bash
# Check disk usage
kubectl exec -it <postgres-pod> -n digital-fte -- df -h

# Check WAL size
kubectl exec -it <postgres-pod> -n digital-fte -- \
  du -sh /var/lib/postgresql/data/pg_wal/
```

#### Resolution

**Clean Old WAL Files**
```bash
# Configure archive_timeout
kubectl exec -it <postgres-pod> -n digital-fte -- \
  psql -U digital_fte -d digital_fte -c "ALTER SYSTEM SET archive_timeout = 600;"
```

**Extend Storage**
```bash
# Update PVC size (if using PVC)
kubectl edit pvc digital-fte-postgres-pvc -n digital-fte

# Or increase node disk size
```

---

## Kafka Issues

### Kafka Connection Failures

#### Symptoms
- Application logs show "Kafka connection refused"
- Kafka consumer groups stuck
- Messages not being processed

#### Diagnosis

```bash
# Check Kafka pod status
kubectl get pods -n digital-fte -l app=kafka

# Check Kafka logs
kubectl logs <kafka-pod> -n digital-fte --tail=100

# Check Zookeeper
kubectl get pods -n digital-fte -l app=zookeeper
```

#### Resolution

**Restart Kafka**
```bash
kubectl rollout restart deployment/digital-fte-kafka -n digital-fte
```

**Check Broker Health**
```bash
# List topics
kubectl exec -it <kafka-pod> -n digital-fte -- \
  kafka-topics.sh --bootstrap-server localhost:9092 --list

# Describe topic
kubectl exec -it <kafka-pod> -n digital-fte -- \
  kafka-topics.sh --bootstrap-server localhost:9092 \
    --describe --topic customer-messages
```

### Message Lag

#### Symptoms
- Consumer lag increasing
- Messages stuck in queue
- Customers not receiving responses

#### Diagnosis

```bash
# Check consumer group lag
kubectl exec -it <kafka-pod> -n digital-fte -- \
  kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
    --describe --group digital-fte-group

# Check topic partitions
kubectl exec -it <kafka-pod> -n digital-fte -- \
  kafka-topics.sh --bootstrap-server localhost:9092 \
    --describe --topic customer-messages
```

#### Resolution

**Add More Consumers**
```bash
# Scale up consumer deployment
kubectl scale deployment/digital-fte-consumers --replicas=3 -n digital-fte
```

**Increase Partitions**
```bash
# Add more partitions to topic
kubectl exec -it <kafka-pod> -n digital-fte -- \
  kafka-topics.sh --bootstrap-server localhost:9092 \
    --alter --topic customer-messages \
    --partitions 6
```

---

## AI Agent Issues

### OpenAI API Failures

#### Symptoms
- AI responses not generated
- Timeout errors from OpenAI
- Rate limit errors (429)

#### Diagnosis

```bash
# Check OpenAI API status
curl https://status.openai.com

# Check application logs
kubectl logs -l app=digital-fte-backend | grep -i "openai" | tail -50

# Check API key
echo $OPENAI_API_KEY | wc -c  # Should be 51 chars for sk- prefix
```

#### Resolution

**Verify API Key**
```bash
# Test API key directly
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o", "messages": [{"role": "user", "content": "test"}]}'
```

**Implement Caching**
```bash
# Cache common responses in Redis
# Configure TTL based on question type
# Implement cache warming for FAQs
```

**Reduce Token Usage**
```bash
# Use smaller model for simple queries
# Implement token limiting in application
# Use streaming responses for long content
```

### Poor Response Quality

#### Symptoms
- Customers complain about irrelevant answers
- AI hallucinations
- Context not maintained

#### Diagnosis

```bash
# Check conversation history retrieval
kubectl logs -l app=digital-fte-backend | grep -i "conversation_history" | tail -20

# Check knowledge base search
kubectl logs -l app=digital-fte-backend | grep -i "doc_search" | tail -20

# Verify pgvector embeddings
kubectl exec -it <postgres-pod> -n digital-fte -- \
  psql -U digital_fte -d digital_fte -c "SELECT COUNT(*) FROM customers WHERE embedding IS NULL;"
```

#### Resolution

**Update Knowledge Base**
```bash
# Add missing product documentation
# Review and update FAQ responses
# Improve product descriptions
```

**Adjust Embedding Model**
```bash
# Use higher quality embeddings (text-embedding-3-large)
# Re-index existing documents
```

**Increase Context Window**
```bash
# Update agent configuration
# Include more conversation history
# Increase max_context_length parameter
```

---

## Channel Integration Issues

### Gmail Integration Issues

#### Symptoms
- Webhook not receiving emails
- OAuth authentication failures
- Emails not being sent

#### Diagnosis

```bash
# Check Gmail service logs
kubectl logs -l app=digital-fte-backend | grep -i "gmail" | tail -50

# Check OAuth credentials
kubectl get secret digital-fte-secrets -n digital-fte -o yaml

# Test Gmail API directly
curl https://www.googleapis.com/gmail/v1/users/me/profile \
  -H "Authorization: Bearer $GMAIL_ACCESS_TOKEN"
```

#### Resolution

**Refresh OAuth Token**
```bash
# OAuth tokens expire - implement refresh flow
# Update secret with new token
kubectl create secret generic digital-fte-secrets \
  --from-literal=gmail-access-token=<new-token> \
  --dry-run=client -n digital-fte
```

**Check Webhook Registration**
```bash
# Verify Pub/Sub subscription
gcloud pubsub subscriptions list

# Re-register webhook if missing
```

### WhatsApp Integration Issues

#### Symptoms
- WhatsApp messages not received
- Twilio webhook failing
- Messages not being sent

#### Diagnosis

```bash
# Check WhatsApp service logs
kubectl logs -l app=digital-fte-backend | grep -i "whatsapp" | tail -50

# Check Twilio credentials
kubectl get secret digital-fte-secrets -n digital-fte -o yaml

# Test Twilio API
curl -X POST https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID/Messages.json \
  -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN"
```

#### Resolution

**Verify Sandbox Number**
```bash
# Ensure using sandbox number (starts with +14155238607)
# Twilio sandbox is free and sufficient for testing
```

**Check Webhook URL**
```bash
# Webhook must be publicly accessible
# Test webhook URL: curl -X POST <webhook-url>
```

### Web Form Issues

#### Symptoms
- Form submissions failing
- Frontend not loading
- API errors

#### Diagnosis

```bash
# Check frontend logs
kubectl logs -l app=digital-fte-frontend | tail -100

# Check backend API logs
kubectl logs -l app=digital-fte-backend | grep -i "webform" | tail -50

# Test API endpoint
curl -X POST http://digital-fte-backend/api/v1/inquiries \
  -H "Content-Type: application/json" \
  -d '{"channel":"webform","customer_email":"test@example.com","message":"test"}'
```

#### Resolution

**Check CORS Configuration**
```bash
# Verify CORS allows frontend origin
kubectl get configmap digital-fte-config -n digital-fte -o yaml
```

**Fix Validation Errors**
```bash
# Check form validation rules
# Update Zod/Yup schemas in frontend
# Verify server-side validation matches client-side
```

**Scale Frontend**
```bash
# Add more frontend replicas
kubectl scale deployment/digital-fte-frontend --replicas=3 -n digital-fte
```

---

## Performance Issues

### High CPU Usage

#### Symptoms
- CPU utilization > 80%
- Throttling messages in logs
- Response time degradation

#### Diagnosis

```bash
# Check CPU usage per pod
kubectl top pods -n digital-fte --sort-by=cpu

# Check node CPU
kubectl top nodes

# Identify top CPU consumers
kubectl logs -l app=digital-fte-backend | grep "CPU" | tail -20
```

#### Resolution

**Scale Up Cluster**
```bash
# Add more nodes or upgrade existing nodes
# For cloud providers, use auto-scaling
```

**Optimize Code**
```bash
# Profile application
# Use Python cProfile or similar
# Identify CPU-intensive operations
# Implement caching or batching
```

**Adjust Resource Limits**
```bash
# Update pod resource limits
kubectl edit deployment digital-fte-backend -n digital-fte
```

### High Memory Usage

#### Symptoms
- Memory utilization > 80%
- OOMKilled events
- Pods restarting

#### Diagnosis

```bash
# Check memory usage per pod
kubectl top pods -n digital-fte --sort-by=memory

# Check for memory leaks
kubectl logs -l app=digital-fte-backend | grep -i "memory" | tail -20
```

#### Resolution

**Increase Memory Limits**
```bash
kubectl edit deployment digital-fte-backend -n digital-fte
# Update limits.memory to higher value
```

**Investigate Memory Leaks**
```bash
# Check for unclosed connections
# Verify connection pooling is working
# Check for unbounded caches
```

**Add More Replicas**
```bash
# Spread load across more pods
kubectl scale deployment/digital-fte-backend --replicas=5 -n digital-fte
```

---

## Security Issues

### Unauthorized Access

#### Symptoms
- 401/403 errors in logs
- Access denied messages
- Authentication failures

#### Diagnosis

```bash
# Check authentication logs
kubectl logs -l app=digital-fte-backend | grep -i "auth\|unauthorized" | tail -50

# Verify secrets are correct
kubectl get secret digital-fte-secrets -n digital-fte -o yaml
```

#### Resolution

**Rotate Secrets**
```bash
# Generate new API keys/tokens
# Update Kubernetes secrets
kubectl create secret generic digital-fte-secrets-new \
  --from-literal=... \
  -n digital-fte

# Patch deployment to use new secret
kubectl patch deployment digital-fte-backend -n digital-fte \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"backend","envFrom":[{"secretRef":{"name":"digital-fte-secrets-new"}}]}}]}}'
```

**Enable Audit Logging**
```bash
# Enable detailed authentication logging
# Set LOG_LEVEL to DEBUG for security events
```

### Rate Limiting Issues

#### Symptoms
- Legitimate requests blocked
- 429 Too Many Requests
- Customer complaints about access

#### Diagnosis

```bash
# Check rate limiter configuration
kubectl get configmap digital-fte-config -n digital-fte -o yaml

# Check recent blocks
kubectl logs -l app=digital-fte-backend | grep -i "rate limit" | tail -20
```

#### Resolution

**Adjust Rate Limits**
```bash
# Increase rate limit per IP/user
# Or implement whitelist for trusted sources
kubectl edit configmap digital-fte-config -n digital-fte
```

**Implement IP Whitelisting**
```bash
# Add internal IPs to whitelist
# Allow higher limits for monitoring systems
```

---

## Common Error Codes

### HTTP Status Codes

| Code | Meaning | Action |
|-------|----------|--------|
| 200 | Success | None |
| 400 | Bad Request | Check request format |
| 401 | Unauthorized | Check credentials |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Check endpoint URL |
| 429 | Too Many Requests | Implement backoff |
| 500 | Internal Server Error | Check logs and restart |
| 503 | Service Unavailable | Scale up or retry |

### Application Error Messages

| Error | Meaning | Action |
|-------|----------|--------|
| `DATABASE_CONNECTION_FAILED` | Cannot connect to DB | Check PostgreSQL |
| `KAFKA_CONNECTION_FAILED` | Cannot connect to Kafka | Check Kafka/Zookeeper |
| `OPENAI_API_ERROR` | OpenAI API failed | Check API key/limits |
| `ESCALATION_RATE_HIGH` | Escalation rate > 25% | Review AI responses |
| `MESSAGE_LOSS_DETECTED` | Kafka message lost | Check consumer lag |
| `SENTIMENT_ANALYSIS_FAILED` | Cannot analyze sentiment | Check OpenAI API |
| `CROSS_CHANNEL_MATCH_FAILED` | Cannot identify customer | Check embeddings |

---

## Runbooks by Severity

### P1 - Critical (Immediate Action Required)

- Service completely down
- Data loss occurring
- Security breach detected

**Action**: Follow Emergency Response procedure immediately

### P2 - High (Action Within 15 Minutes)

- Degraded performance
- High error rate
- Partial service outage

**Action**: Diagnose and execute resolution plan

### P3 - Medium (Action Within 1 Hour)

- Slow response times
- Intermittent errors
- High resource usage

**Action**: Monitor and optimize as needed

### P4 - Low (Action Within 4 Hours)

- Documentation gaps
- Minor optimizations
- Non-critical bugs

**Action**: Schedule fix in next release

---

## Escalation Contacts

### On-Call Rotation

- Primary: +1-XXX-XXX-XXXX1
- Secondary: +1-XXX-XXX-XXXX2
- Tertiary: +1-XXX-XXX-XXXX3

### Notification Channels

- Slack: #digital-fte-alerts
- Email: oncall@company.com
- PagerDuty: digital-fte-service

### Decision Matrix

| Impact | Urgency | Escalation |
|--------|----------|------------|
| Complete outage | Critical | Page immediately |
| Degraded service | High | Slack + prepare to page |
| Performance issue | Medium | Create ticket, monitor |
| Minor issue | Low | Create ticket |

---

## Support Resources

### Documentation

- Deployment Guide: `k8s/deployment-guide.md`
- API Documentation: http://digital-fte-backend/docs
- Runbook Repository: https://github.com/company/digital-fte-runbooks

### Monitoring

- Grafana Dashboard: https://grafana.company.com/d/digital-fte
- Prometheus: https://prometheus.company.com
- Alerts: https://alertmanager.company.com

### Communication

- Slack Workspace: https://company.slack.com
- Incident Status Page: https://status.company.com
- On-Call Schedule: https://pagerduty.company.com/schedules

---

**Last Updated**: 2026-04-02
**Maintained By**: Digital FTE Operations Team
**Version**: 1.0.0

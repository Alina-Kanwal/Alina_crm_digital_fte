# Digital FTE Agent: Deployment Runbook (T127)

## 📋 Pre-Deployment Check
- [ ] PG_VECTOR_ENABLED: Verify PostgreSQL 15+ cluster is ready.
- [ ] KAFKA_TOPICS: Confirm Kafka topics exist (messages, responses, signals).
- [ ] OPENAI_API_KEY: Provision keys with GPT-4o and GPT-4o-mini access.
- [ ] REDIS_URL: Ensure a clustered Redis 7.0+ instance is available.

## 🚀 Step 1: Database Migration
Deploy the initial schema using Alembic:
```bash
cd backend
export DATABASE_URL="postgresql://user:pass@host:5432/db"
alembic upgrade head
```

## 🚀 Step 2: Secret Management
Apply the application secrets in Kubernetes:
```bash
kubectl apply -f k8s/secrets/app-secrets.yaml
```

## 🚀 Step 3: Rolling Deploy
Deploy the main application components using a 25% max-unavailable strategy:
```bash
kubectl apply -f k8s/configmaps/
kubectl apply -f k8s/deployments/
kubectl apply -f k8s/services/
kubectl apply -f k8s/hpa/
```

## 🚀 Step 4: Verification
Verify the deployment by calling the health check endpoint:
```bash
curl https://api.digital-fte.example.com/health/readiness
```

## 🔄 Step 5: Post-Deployment Monitoring
Monitor the **P95 Latency** and **Escalation Rate** dashboards for the first 4 hours post-release.

---

# Digital FTE Agent: Troubleshooting Guide (T128)

## 🚨 Symptom 1: High Latency (>3.0s p95)
- **Probable Cause**: High cold-start time or cache miss on semantic search.
- **Action**: Check Redis connectivity and hit rates. Increase `REDIS_MAX_MEMORY` if needed.
- **Action**: Verify OpenAI API latency and potential rate-limiting.

## 🚨 Symptom 2: Error 500 when creating threads
- **Probable Cause**: SQLite vs PostgreSQL driver mismatch or database constraint violation.
- **Action**: Verify the `DATABASE_URL` environment variable. 
- **Action**: Check if the `customer_id` exists before thread creation (Ref: `customer_identifier.py`).

## 🚨 Symptom 3: Low Document Search Accuracy
- **Probable Cause**: Embedding mismatch or outdated documentation vectors.
- **Action**: Re-generate embeddings for all documents using the `reindex_kb.py` tool.
- **Action**: Tune the `RELEVANCE_THRESHOLD` in `DocumentSearchService` (current: 0.5 - 0.7).

## 🚨 Symptom 4: "ModuleNotFoundError: agents"
- **Probable Cause**: Incorrectly installed OpenAI Agents SDK.
- **Action**: Run `pip install openai-agents`. Verify `from agents import ...` works in local environment.

---

**World-Class Delivery by Antigravity**

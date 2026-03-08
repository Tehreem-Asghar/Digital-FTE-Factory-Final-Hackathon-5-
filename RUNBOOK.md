# SaaSFlow Digital FTE Operations Runbook

## 0. Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| **Python** | 3.11+ | Backend runtime |
| **Node.js** | 18+ | Dashboard frontend |
| **Docker** | 20+ | PostgreSQL, Kafka, Zookeeper |
| **uv** | Latest | Python package manager |
| **Git** | Latest | Version control |

### Environment Setup

1. **Install uv** (Python package manager):
```bash
# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Install dependencies**:
```bash
uv sync
```

3. **Create `.env` file** in project root:
```bash
# Database
POSTGRES_USER=fte_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=fte_db

# OpenAI API
OPENAI_API_KEY=sk-your-openai-key

# Gemini API (for embeddings)
GEMINI_API_KEY=your-gemini-key

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Email (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# WhatsApp (Meta Cloud API)
WHATSAPP_TOKEN=your-whatsapp-token
WHATSAPP_PHONE_ID=your-phone-id
```

## 1. System Overview

The Digital FTE is a multi-channel AI-powered customer success agent system consisting of:

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API** | FastAPI (Python 3.12) | REST endpoints for Web Form, Email, WhatsApp intake |
| **Agent** | OpenAI Agents SDK + Gemini | AI agent "Flowie" for customer support |
| **Worker** | Kafka Consumer | Processes messages, runs agent, sends responses |
| **Database** | PostgreSQL + pgvector | Customers, tickets, conversations, knowledge base |
| **Event Bus** | Apache Kafka | Async message queue between API and workers |
| **Dashboard** | Next.js 16 + Tailwind CSS | Admin analytics, ticket/customer management |
| **Recovery Worker** | Python async | Drains `pending_ingestion` table when Kafka recovers |
| **Learning Worker** | Python async | Extracts patterns from resolved tickets into `resolution_learnings` |

## 2. Common Operations

### 2.1 Starting Infrastructure
```bash
# Start PostgreSQL, Kafka, Zookeeper
docker-compose up -d

# Verify all containers are running
docker-compose ps
```

### 2.2 Starting the API Server
```bash
uv run uvicorn production.api.main:app --host 0.0.0.0 --port 8000
```

### 2.3 Starting the Message Worker
```bash
uv run python -m production.workers.message_processor
```

### 2.4 Starting the Dashboard
```bash
cd dashboard
npm run dev
# Dashboard runs on http://localhost:3000
```

### 2.5 Starting the Learning Worker
```bash
uv run python -m production.workers.learning_worker
# Processes resolved tickets every 60 seconds
```

### 2.6 Monitoring Logs (Kubernetes)
- **API Logs**: `kubectl logs -l component=api -n customer-success-fte`
- **Worker Logs**: `kubectl logs -l component=worker -n customer-success-fte`

### 2.6 Checking Agent Health
```bash
# Health endpoint
curl http://localhost:8000/health

# Channel metrics
curl http://localhost:8000/metrics/channels

# Metrics summary
curl http://localhost:8000/metrics/summary

# Daily sentiment report (last 7 days)
curl http://localhost:8000/api/reports/sentiment/daily?days=7

# Today's sentiment snapshot
curl http://localhost:8000/api/reports/sentiment/today

# Trigger learning extraction from resolved tickets
curl -X POST http://localhost:8000/api/learnings/process

# Search past resolutions
curl "http://localhost:8000/api/learnings/search?query=billing+issue"
```

Monitor the `agent_metrics` table for:
- `latency_ms > 3000`: Indicates processing lag.
- `escalation_rate > 30%`: Indicates agent confusion or doc gaps.

## 3. Incident Response

### 3.1 High Latency
1. Check Kafka lag:
```bash
kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group fte-message-processor
```
2. Scale workers:
```bash
kubectl scale deployment fte-worker --replicas=10 -n customer-success-fte
```

### 3.2 Agent Hallucination
1. Review the system prompt in `production/agent/prompts.py`.
2. Update `knowledge_base` with corrected documentation.
3. Restart workers to clear prompt cache.

### 3.3 Kafka Downtime (Fail-Safe Ingestion)
When Kafka is unreachable, all endpoints (Web Form, Email, WhatsApp) automatically save messages to the `pending_ingestion` database table. The API server starts normally even if Kafka is down.

**Detection**: Check `pending_ingestion` table for rows with `status = 'pending'`:
```sql
SELECT COUNT(*) FROM pending_ingestion WHERE status = 'pending';
```

**Recovery**:
1. Verify Kafka is back online:
```bash
docker-compose ps kafka
```
2. Start the recovery worker to drain pending messages:
```bash
uv run python -m production.workers.recovery_worker --interval 15
```
3. Monitor progress:
```sql
SELECT status, COUNT(*) FROM pending_ingestion GROUP BY status;
```

**Note**: Messages are retried up to 5 times. Failed messages are marked `status = 'failed'` and need manual review.

### 3.4 Cross-Channel Identity Issues
If customers are not being linked across channels:
1. Check `customer_identifiers` table:
```sql
SELECT * FROM customer_identifiers WHERE customer_id = '<uuid>';
```
2. Verify both email and phone identifiers are registered.
3. Check `customers.metadata` for `alternate_emails` (logged when phone matches but email differs).

## 4. API Endpoints Reference

### Intake Channels
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/support/submit` | Web form ticket submission |
| POST | `/support/email` | Email support request |
| POST | `/support/whatsapp` | WhatsApp message (testing) |
| POST | `/webhooks/gmail` | Gmail Pub/Sub webhook |
| GET/POST | `/webhooks/whatsapp` | Meta WhatsApp webhook (verify + receive) |

### Dashboard APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/stats` | KPIs, charts, recent tickets |
| GET | `/api/tickets` | All tickets list |
| GET | `/api/tickets/{id}` | Ticket details + messages |
| GET | `/api/customers` | All customers list |
| GET | `/api/customers/{id}` | Customer details + tickets |
| GET | `/api/conversations` | All conversations |
| GET | `/api/conversations/{id}/messages` | Conversation messages |

### Monitoring & Testing
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health check |
| GET | `/metrics/channels` | Per-channel metrics |
| GET | `/metrics/summary` | Overall metrics summary |
| GET | `/customers/lookup?email=...&phone=...` | Customer lookup |
| POST | `/mock/meta/send` | Mock WhatsApp Cloud API |
| GET | `/mock/meta/health` | Mock Meta health check |
| GET | `/support/ticket/{id}` | Ticket status with messages |

## 5. Testing & Validation

### 5.1 Running All Tests
```bash
# All tests (Stage 2 + Stage 3)
uv run pytest production/tests/test_production.py tests/test_multichannel_e2e.py -v

# Stage 2 only (49 tests)
uv run pytest production/tests/test_production.py -v

# Stage 3 E2E only (16 tests)
uv run pytest tests/test_multichannel_e2e.py -v
```

### 5.2 Load Testing with Locust
```bash
# Quick validation (30 users, 60s)
uv run locust -f tests/load_test.py --host http://localhost:8000 --users 30 --spawn-rate 5 --run-time 60s --headless

# Full stress test (100+ users, 5 minutes)
uv run locust -f tests/load_test.py --host http://localhost:8000 --users 150 --spawn-rate 10 --run-time 300s --headless
```

**Success Criteria**: P95 latency < 3 seconds (SC-002).

### 5.3 Chaos Testing
```bash
# Dry-run (no actual kills)
uv run python tests/chaos_sim.py --dry-run --duration 1 --interval 10

# Full 24-hour chaos test
uv run python tests/chaos_sim.py --duration 24 --interval 120
```

**Success Criteria**: >99.9% uptime, zero message loss (SC-003).

### 5.4 Manual Fail-Safe Test
```bash
# 1. Stop Kafka
docker-compose stop kafka

# 2. Submit a ticket (should save to pending_ingestion)
curl -X POST http://localhost:8000/support/submit \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@test.com","subject":"Test","message":"Testing fail-safe"}'

# 3. Check pending_ingestion table
docker exec hackathon_5-db-1 psql -U fte_user -d fte_db \
  -c "SELECT id, status, payload->>'channel' as channel FROM pending_ingestion;"

# 4. Restart Kafka
docker-compose start kafka

# 5. Run recovery worker
uv run python -m production.workers.recovery_worker --interval 5

# 6. Verify messages are published
docker exec hackathon_5-db-1 psql -U fte_user -d fte_db \
  -c "SELECT id, status, published_at FROM pending_ingestion;"
```

## 6. Disaster Recovery
PostgreSQL data is stored in a persistent volume. In case of DB failure:
1. Re-apply schema: `psql -f production/database/schema.sql`
2. Re-import knowledge base vectors: `python seed_kb.py`
3. Check pending_ingestion for any lost messages.

## 7. Troubleshooting

### Common Issues

| Issue | Possible Cause | Solution |
|-------|---------------|----------|
| **Port 5433 in use** | Another PostgreSQL running | Change port in `docker-compose.yml` or stop other instance |
| **Kafka connection refused** | Zookeeper not ready | Wait 30s after starting Docker, then restart Kafka |
| **Module not found** | Dependencies not installed | Run `uv sync` |
| **Dashboard build fails** | Node version mismatch | Ensure Node.js 18+ |
| **Embedding generation fails** | Invalid GEMINI_API_KEY | Verify API key in `.env` |
| **Tests fail with timeout** | Slow network/DB | Increase timeout in `conftest.py` |

### Debug Commands

```bash
# Check Docker containers
docker-compose ps

# View container logs
docker-compose logs -f kafka
docker-compose logs -f db

# Check Python environment
uv run python --version
uv pip list

# Verify database connection
docker exec -it hackathon_5-db-1 psql -U fte_user -d fte_db -c "SELECT 1;"

# Check Kafka topics
docker exec -it hackathon_5-kafka-1 kafka-topics --bootstrap-server localhost:9092 --list

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d db
uv run python -m production.database.setup
```

### Getting Help

1. Check logs: `docker-compose logs -f`
2. Review error messages in `/health` endpoint
3. Check `agent_metrics` table for performance issues
4. Consult project documentation in `context/` folder

## 8. Performance SLA Reference

| Metric | Target | Monitoring |
|--------|--------|-----------|
| Uptime | > 99.9% | `/health` endpoint |
| P95 Latency | < 3 seconds | `agent_metrics` table |
| Escalation Rate | < 25% | `/metrics/channels` |
| Cross-Channel ID | > 95% accuracy | `customer_identifiers` table |
| Message Loss | 0% | `pending_ingestion` status counts |

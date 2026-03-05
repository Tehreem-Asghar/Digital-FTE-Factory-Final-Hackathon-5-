# SaaSFlow Digital FTE Operations Runbook

## 1. System Overview
The Digital FTE is a multi-channel AI agent system consisting of:
- **API**: FastAPI service for intake.
- **Worker**: Kafka consumer running the OpenAI/Gemini Agent.
- **Middleware**: PostgreSQL (Data) and Kafka (Events).

## 2. Common Operations

### 2.1 Starting the System
```bash
docker-compose up -d
```

### 2.2 Monitoring Logs
- **API Logs**: `kubectl logs -l component=api -n customer-success-fte`
- **Worker Logs**: `kubectl logs -l component=worker -n customer-success-fte`

### 2.3 Checking Agent Health
Monitor the `agent_metrics` table for:
- `latency_ms > 3000`: Indicates processing lag.
- `escalation_rate > 30%`: Indicates agent confusion or doc gaps.

## 3. Incident Response

### 3.1 High Latency
1. Check Kafka lag: `kafka-consumer-groups --bootstrap-server localhost:9092 --describe --group fte-message-processor`
2. Scale workers: `kubectl scale deployment fte-worker --replicas=10 -n customer-success-fte`

### 3.2 Agent Hallucination
1. Review the system prompt in `production/agent/prompts.py`.
2. Update `knowledge_base` with corrected documentation.
3. Restart workers to clear prompt cache.

## 4. Disaster Recovery
PostgreSQL data is stored in a persistent volume. In case of DB failure:
1. Re-apply schema: `psql -f production/database/schema.sql`.
2. Re-import knowledge base vectors.

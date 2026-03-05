# Specification: Stage 2 - Specialization (Updated)

## 1. Overview
Engineering a production-grade Digital FTE using **OpenAI Agents SDK** (Gemini backend), **PostgreSQL (pgvector)**, **Kafka**, and **Kubernetes**.

## 2. Technical Requirements

### 2.1 Directory Structure (Mandatory - Page 12)
All production code must reside in the `production/` directory:
- `agent/`: `customer_success_agent.py`, `tools.py`, `prompts.py`, `formatters.py`.
- `channels/`: `gmail_handler.py`, `whatsapp_handler.py`, `web_form_handler.py`.
- `workers/`: `message_processor.py` (Kafka consumer), `metrics_collector.py`.
- `api/`: `main.py` (FastAPI).
- `database/`: `schema.sql`, `migrations/`, `queries.py`.

### 2.2 Database Schema (Mandatory - Page 22-24)
Must implement the full 8-table relational schema in PostgreSQL with `pgvector`:
1. `customers`: Unified profile.
2. `customer_identifiers`: Cross-channel mapping (email/phone).
3. `conversations`: State management and sentiment tracking.
4. `messages`: Full audit trail of all inbound/outbound content.
5. `tickets`: Support lifecycle tracking.
6. `knowledge_base`: Vectorized product documentation.
7. `channel_configs`: API keys and response templates.
8. `agent_metrics`: Latency and success rate tracking.

### 2.3 Core Logic & Workflow (Page 15)
The agent must follow the explicit 4-step workflow:
1. `create_ticket` -> 2. `get_customer_history` -> 3. `search_knowledge_base` -> 4. `send_response`.

## 3. Communication & Delivery
- **Kafka**: Events published to `fte.tickets.incoming`.
- **FastAPI**: Endpoints for Gmail/Twilio webhooks and a React-based Web Support Form.
- **Kubernetes**: Deployment with 3 replicas, HPA, and Liveness/Readiness probes.

## 4. Acceptance Criteria
- [ ] Successful completion of the **24-Hour Multi-Channel Test**.
- [ ] **Chaos Testing**: System survives random pod kills every 2 hours.
- [ ] **Load Testing**: Survives simulated traffic spike using Locust.

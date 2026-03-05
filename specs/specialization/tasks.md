# Task List: Stage 2 - Specialization (Production Build) - FINAL

## Phase 1: Database & Middleware (The CRM Foundation)

### Task 1.1: Production Directory & Schema
- **Description**: Create `production/` structure and implement the full 8-table schema (Pages 22-24).
- **Acceptance Criteria**:
  - [x] Tables: `customers`, `identifiers`, `conversations`, `messages`, `tickets`, `kb`, `configs`, `metrics`.
  - [x] `pgvector` index (`vector_cosine_ops`) enabled on `knowledge_base`.
  - [x] Database migrations folder with `001_initial_schema.sql` and `run_migrations.py`.
- **Validation**: `psql -f production/database/schema.sql`.

### Task 1.2: Multi-Service Docker Compose
- **Description**: Setup `postgres`, `kafka`, and `zookeeper`.
- **Acceptance Criteria**:
  - [x] Healthy connectivity between containers.
- **Validation**: `docker-compose ps` shows all services up.

---

## Phase 2: Production Agent & Skills

### Task 2.1: Gemini-OpenAI Production Agent
- **Description**: Implement `customer_success_agent.py` using OpenAI SDK with Gemini bridge.
- **Acceptance Criteria**:
  - [x] Explicit guardrails from Page 15 in system prompt.
  - [x] Uses `@function_tool` for SQL/Vector operations.
- **Validation**: Agent handles a test query via `Runner.run`.

### Task 2.2: Advanced Agent Skills
- **Description**: Implement formal Skills manifest (Exercise 1.5).
- **Acceptance Criteria**:
  - [x] Nuanced Sentiment Analysis.
  - [x] Omnichannel Identity Matching logic.

---

## Phase 3: Communication & Ingestion

### Task 3.1: FastAPI Webhook Handlers
- **Description**: Implement Gmail (Pub/Sub) and WhatsApp (Meta Cloud API) intake endpoints.
- **Acceptance Criteria**:
  - [x] Gmail handler (`gmail_handler.py`) with Pub/Sub notification parsing and email send.
  - [x] WhatsApp handler with Meta webhook verification and message parsing.
  - [x] Publishes incoming messages to Kafka.
- **Files**: `production/channels/gmail_handler.py`, `production/channels/whatsapp_handler.py`

### Task 3.2: Unified Message Processor (The Worker)
- **Description**: Implement the Kafka consumer `message_processor.py` (Page 43).
- **Acceptance Criteria**:
  - [x] Logs `latency_ms` and `tokens_used` for every request.
  - [x] Handles errors with apologetic responses via appropriate channel.

### Task 3.3: Web Support Form (Submission & Status)
- **Description**: Build React component with validation and status checking.
- **Acceptance Criteria**:
  - [x] React SupportForm component (`production/web-form/SupportForm.jsx`).
  - [x] Implements GET `/ticket/{id}` for status tracking.

---

## Phase 4: Monitoring, Ops & Deployment

### Task 4.1: Metrics & Monitoring Setup
- **Description**: Implement `metrics_collector.py` for reporting (Page 51).
- **Acceptance Criteria**:
  - [x] API endpoint for `/metrics/channels` exists.
  - [x] API endpoint for `/metrics/summary` exists (includes P95 latency, escalation rate).
- **Files**: `production/api/main.py`, `production/workers/metrics_collector.py`

### Task 4.2: Kubernetes Manifests (Resilient Setup)
- **Description**: Create manifests with HPA and Probes (Pages 52-55).
- **Acceptance Criteria**:
  - [x] Liveness/Readiness probes configured for the API.
  - [x] Liveness/Readiness probes configured for the Worker.
  - [x] HPA scales based on CPU usage (70% target).
  - [x] Resource requests/limits set for all containers.

### Task 4.3: Documentation & Runbook
- **Description**: Create `RUNBOOK.md` and deployment guide.
- **Acceptance Criteria**:
  - [x] Instructions for incident response and monitoring.

---

## Phase 5: Final Validation

### Task 5.1: Production E2E Test Suite
- **Acceptance Criteria**:
  - [x] 30+ tests covering tools, formatters, API endpoints, handlers, guardrails, schema.
- **File**: `production/tests/test_production.py`

### Task 5.2: Locust Load Test
- **Acceptance Criteria**:
  - [x] Load test script simulates realistic traffic across all endpoints.
  - [x] Spike user class for backpressure testing.
- **Run**: `locust -f production/tests/locustfile.py --host http://localhost:8000`

### Task 5.3: Chaos Test Simulation
- **Acceptance Criteria**:
  - [x] Random pod kills every 2 hours.
  - [x] Kafka restart simulation.
  - [x] Connection flood testing.
  - [x] Automated recovery validation (>99.9% uptime target).
- **Run**: `python -m production.tests.chaos_test --duration 24 --interval 120`

### Task 5.4: 24-Hour Multi-Channel Test
- **Acceptance Criteria**:
  - [x] Sends messages across all 3 channels at realistic intervals.
  - [x] Covers edge cases (refunds, legal, angry customers, escalations).
  - [x] Validates P95 < 3s and success rate > 99.9%.
- **Run**: `python -m production.tests.multichannel_test --duration 24`

### Task 5.5: Knowledge Base Seeder with Embeddings
- **Acceptance Criteria**:
  - [x] Generates Gemini embeddings for all KB documents.
  - [x] 12 comprehensive product documentation entries.
- **Run**: `python seed_kb.py`

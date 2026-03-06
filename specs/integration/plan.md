# Implementation Plan: Stage 3 — Integration, Testing & Production Readiness

**Branch**: `004-integration-and-testing` | **Date**: 2026-03-06 | **Spec**: `/specs/integration/spec.md`
**Input**: Feature specification from `/specs/integration/spec.md`

## Summary
The goal is to move the Digital FTE from a "functional prototype" to a "production-ready" system. This involves implementing a fail-safe ingestion mechanism for Kafka, automating end-to-end multi-channel tests with a Mock Meta Server, and validating performance under load using Locust. We will also implement automated chaos testing to ensure zero message loss during component failures.

## Technical Context

**Language/Version**: Python 3.12 (Production Backend)  
**Primary Dependencies**: FastAPI, aiokafka, asyncpg, OpenAI Agents SDK, Locust, pytest, httpx  
**Storage**: PostgreSQL (pgvector enabled)  
**Testing**: pytest (E2E), Locust (Load Testing), custom Chaos script  
**Target Platform**: Docker-Compose (Local Simulation) / Kubernetes (Target Production)  
**Project Type**: Multi-tier (API, Worker, Kafka, Postgres, Dashboard)  
**Performance Goals**: P95 Latency < 3s, 100+ concurrent users, 0% message loss  
**Constraints**: Zero data loss mandate, 95%+ identity resolution accuracy  

## Constitution Check

- **Credential Protection**: ALL secrets (Meta Tokens, OpenAI keys) must be managed via `.env` or K8s Secrets.
- **Testing Mandate**: E2E suite must cover Web, Email, and WhatsApp mocks.
- **Architectural Alignment**: Maintain unified customer profile logic across all ingestion points.

## Project Structure

### Documentation (this feature)

```text
specs/integration/
├── plan.md              # This file
├── research.md          # Research on Meta API structure and Kafka fail-safe
├── data-model.md        # Schema for pending_ingestion and identity metadata
├── quickstart.md        # Guide to running load and chaos tests
└── tasks.md             # Task breakdown (to be generated)
```

### Source Code

```text
production/
├── api/
│   └── main.py          # Implement /mock/meta and /support/fail-safe endpoints
├── database/
│   ├── schema.sql       # Add pending_ingestion table
│   └── queries.py       # Add fail-safe recovery queries
├── workers/
│   ├── recovery_worker.py # Background task to push pending_ingestion to Kafka
│   └── message_processor.py # Enhanced identity resolution logic
tests/
├── test_multichannel_e2e.py # Automated E2E scenarios
├── load_test.py         # Locust scripts
└── chaos_sim.py         # Automated container failure script
```

**Structure Decision**: We are extending the existing `production/` structure. New testing tools will reside in the root `tests/` directory to facilitate CI/CD integration.

## Implementation Phases

### Phase 1: Fail-Safe Ingestion (Resilience)
*   Update `schema.sql` with `pending_ingestion` table.
*   Update `main.py` ingestion endpoints to detect Kafka health and fallback to DB storage.
*   Implement `recovery_worker.py` to drain the DB queue into Kafka once healthy.

### Phase 2: Multi-Channel Identity & Context
*   Refine `resolve_customer` logic in `message_processor.py` to link Phone-B to Email-A (Option A).
*   Ensure `get_customer_history` tool pulls unified records.

### Phase 3: Automated E2E & Mocking
*   Implement `/mock/meta` FastAPI endpoints.
*   Write `tests/test_multichannel_e2e.py` covering cross-channel scenarios.

### Phase 4: Load & Chaos Testing
*   Implement `tests/load_test.py` for 100+ users.
*   Implement `tests/chaos_sim.py` to randomly restart the `fte-worker` container.
*   Verify SLA metrics (SC-001 to SC-004).

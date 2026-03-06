# Tasks: Stage 3 — Integration, Testing & Production Readiness

**Input**: Design documents from `/specs/integration/`
**Prerequisites**: plan.md, spec.md

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure for data persistence and fail-safe ingestion.

- [ ] T001 Update database schema in `production/database/schema.sql` to include `pending_ingestion` table
- [ ] T002 Implement `pending_ingestion` queries in `production/database/queries.py`
- [ ] T003 Implement `recovery_worker.py` in `production/workers/` to push pending data to Kafka
- [ ] T004 Add Kafka health check utility in `production/utils/kafka_client.py`

**Checkpoint**: Foundation ready - Ingestion points can now implement fail-safe logic.

---

## Phase 2: User Story 1 - Multi-Channel Continuity (Priority: P1) 🎯 MVP

**Goal**: Link customer identities across Web and WhatsApp.

**Independent Test**: Submit Web Form then WhatsApp message with same phone/email and verify unified history in Admin Dashboard.

### Implementation for User Story 1

- [ ] T005 [US1] Refine `resolve_customer` in `production/workers/message_processor.py` to match phone identifiers
- [ ] T006 [US1] Update `get_customer_history` tool in `production/agent/tools.py` to pull cross-channel messages
- [ ] T007 [US1] Ensure `customer_identifiers` table is correctly populated for all channels

**Checkpoint**: User Story 1 functional - Customers are now unified across channels.

---

## Phase 3: User Story 2 - High-Traffic Resilience (Priority: P2)

**Goal**: Implement fail-safe ingestion and validate under load.

**Independent Test**: Stop Kafka container and submit tickets; verify they appear in `pending_ingestion` table.

### Implementation for User Story 2

- [ ] T008 [US2] Update `/support/submit` in `production/api/main.py` with fail-safe DB fallback
- [ ] T009 [US2] Update `/support/email` in `production/api/main.py` with fail-safe DB fallback
- [ ] T010 [US2] Update `/support/whatsapp` in `production/api/main.py` with fail-safe DB fallback
- [ ] T011 [P] [US2] Create Locust load test script in `tests/load_test.py`

**Checkpoint**: User Story 2 functional - System is now resilient to Kafka downtime.

---

## Phase 4: User Story 3 - Automated Chaos & E2E (Priority: P3)

**Goal**: Validate self-healing and end-to-end flow with mocks.

**Independent Test**: Run E2E suite and Chaos script; verify zero message loss in logs.

### Implementation for User Story 3

- [ ] T012 [P] [US3] Implement `/mock/meta` endpoints in `production/api/main.py` for WhatsApp testing
- [ ] T013 [P] [US3] Create automated E2E suite in `tests/test_multichannel_e2e.py`
- [ ] T014 [US3] Create automated chaos script `tests/chaos_sim.py` to simulate pod kills

**Checkpoint**: All user stories functional and validated.

---

## Phase 5: Polish & Readiness

**Purpose**: Final verification and documentation.

- [ ] T015 [P] Update `RUNBOOK.md` with instructions for recovery and load testing
- [ ] T016 Final performance audit: ensure P95 latency < 3s in load test logs
- [ ] T017 Verify all SC-001 to SC-004 criteria in `specs/integration/spec.md`

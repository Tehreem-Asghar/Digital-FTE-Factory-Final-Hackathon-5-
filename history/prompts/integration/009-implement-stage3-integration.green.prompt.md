---
id: 009
title: Implement Stage 3 Integration Tasks
stage: green
date: 2026-03-08
surface: agent
model: claude-sonnet-4-6
feature: integration
branch: main
user: student
command: /sp.implement
labels: ["stage3", "integration", "testing", "fail-safe", "e2e"]
links:
  spec: specs/integration/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - production/database/schema.sql
  - production/database/queries.py
  - production/database/migrations/002_pending_ingestion.sql
  - production/utils/kafka_client.py
  - production/workers/recovery_worker.py
  - production/workers/message_processor.py
  - production/agent/tools.py
  - production/api/main.py
  - production/channels/web_form_handler.py
  - tests/test_multichannel_e2e.py
  - tests/load_test.py
  - tests/chaos_sim.py
  - RUNBOOK.md
  - specs/integration/tasks.md
tests:
  - tests/test_multichannel_e2e.py
  - tests/load_test.py
  - tests/chaos_sim.py
---

## Prompt

ok phir ab stage3 pr working krta hai specs ma dakho mana stage 3 ki specs banihoi hai check kro sab shi hai phir un ko /sp.implement kara ga

## Response snapshot

Implemented all 17 tasks across 5 phases for Stage 3 (Integration, Testing & Production Readiness):

**Phase 1 (Foundation):** Added `pending_ingestion` table to schema.sql, implemented fail-safe queries in queries.py, created recovery_worker.py to drain DB queue into Kafka, added Kafka health check utility.

**Phase 2 (Cross-Channel Identity):** Enhanced `resolve_customer` with phone-first matching and email discrepancy logging in metadata. Upgraded `get_customer_history` to pull unified cross-channel messages.

**Phase 3 (Fail-Safe Ingestion):** Updated all 3 API endpoints (`/support/submit`, `/support/email`, `/support/whatsapp`) with try/catch fallback to `pending_ingestion` table when Kafka is down.

**Phase 4 (Tests & Mocks):** Created Mock Meta WhatsApp endpoint (`/mock/meta/send`), `/metrics/channels` endpoint, `/customers/lookup` endpoint. Built comprehensive E2E test suite (6 test groups, 15+ tests), Locust load test (5 user classes), and chaos simulation script.

**Phase 5 (Polish):** Updated RUNBOOK.md with recovery, load testing, and chaos testing instructions. Added SLA reference table.

## Outcome

- ✅ Impact: All 17 Stage 3 tasks implemented - system now has fail-safe ingestion, enhanced identity resolution, comprehensive E2E/load/chaos testing
- 🧪 Tests: 3 test files created (E2E, load, chaos), all Python files pass syntax check
- 📁 Files: 14 files created/modified
- 🔁 Next prompts: Run E2E tests, run load test, commit changes
- 🧠 Reflection: Stage 2 already had solid foundations; Stage 3 mainly added resilience (pending_ingestion) and formalized testing

## Evaluation notes (flywheel)

- Failure modes observed: None - clean implementation
- Graders run and results (PASS/FAIL): Syntax check PASS on all 6 Python files
- Prompt variant (if applicable): null
- Next experiment (smallest change to try): Run actual pytest to validate E2E tests against live API

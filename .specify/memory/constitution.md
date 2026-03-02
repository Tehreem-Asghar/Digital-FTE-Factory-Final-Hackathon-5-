# Digital FTE Customer Success Factory Constitution

## Core Principles

### I. Omnichannel Autonomy
The Digital FTE must operate seamlessly across all mandated channels (Gmail, WhatsApp, Web Form). It must maintain conversation continuity even if a customer switches channels during an interaction.

### II. Agent Factory Lifecycle
Development strictly follows the Agent Maturity Model. We begin with the **Incubation Phase** (prototyping with Claude Code/MCP) and evolve into the **Specialization Phase** (production-grade agent using OpenAI Agents SDK).

### III. Unified CRM Integrity
The custom PostgreSQL database is the absolute source of truth. No interaction or ticket may exist outside the system. Every message, sentiment score, and escalation must be logged with high precision.

### IV. Compliance & Guardrails
The agent must adhere to strict hard constraints: Never discuss pricing, never promise features not in documentation, and never process refunds. Immediate escalation to human support is mandatory for out-of-scope queries.

### V. Production-Grade Reliability
The system is engineered for 24/7 operation. This requires a robust tech stack: FastAPI for service delivery, Kafka for event streaming, and Kubernetes for resilient orchestration.
All agent decisions, tool usage, escalations, and failures must be observable through structured logging and monitoring metrics.

### VI. Empirical Validation
Success is measured by data, not assumptions. Every component must pass E2E tests and survive the 24-hour Multi-Channel Test (100+ web submissions, 50+ messages) with >99.9% uptime and <3s latency.

### VII. Digital Employee Identity
The Digital FTE behaves as a full-time Customer Success employee,
maintaining consistent tone, memory of past interactions,
and accountability for complete ticket lifecycle management.

## Technology Stack

### Stage 1 (Incubation)
- **Language**: Python
- **Interface**: Model Context Protocol (MCP) Server
- **Prototyping**: Claude Code

### Stage 2 (Specialization)
- **Agent SDK**: OpenAI Agents SDK
- **API**: FastAPI
- **Database**: PostgreSQL (with pgvector)
- **Messaging**: Apache Kafka
- **Frontend**: React/Next.js (Web Support Form)
- **Orchestration**: Kubernetes (k8s)

## Development Workflow

### Spec-Driven Development (SDD)
1. **Spec First**: Define requirements in `specs/<feature>/spec.md`.
2. **Plan**: Architect the solution in `specs/<feature>/plan.md`.
3. **Tasks**: Break down into testable units in `specs/<feature>/tasks.md`.
4. **Implement**: Use Claude Code as the "Factory" to build the specialist code.
5. **Verify**: Run `pytest` and E2E suites before marking as complete.

## Governance
This Constitution is the foundational mandate for the Digital FTE project. Any architectural deviation requires an ADR (Architectural Decision Record). Compliance with guardrails is non-negotiable and must be verified through automated testing.

**Version**: 1.0.0 | **Ratified**: 2026-03-02 | **Last Amended**: 2026-03-02

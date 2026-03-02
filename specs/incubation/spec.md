# Specification: Stage 1 - Incubation Phase

## 1. Overview
The Incubation Phase is the exploratory stage of the Digital FTE project. The goal is to build a functional prototype for **SaaSFlow** using the **Official Python MCP SDK** to discover requirements, define formal agent skills, and establish a performance baseline.

## 2. Requirements

### 3.1 Development Dossier (Setup)
Establish the knowledge base in `context/`:
- `company-profile.md`: SaaSFlow overview and target segments.
- `product-docs.md`: Details on Kanban, Workspaces, and "Flow" automations.
- `sample-tickets.json`: 50+ tickets across Gmail, WhatsApp, and Web Form.
- `escalation-rules.md`: Hard triggers for handovers.
- `brand-voice.md`: Defining the "Flowie" persona.

### 3.2 Memory and State (Exercise 1.3)
The prototype must maintain conversation continuity across channels and track:
1. **Customer Sentiment**: Analysis of the interaction quality.
2. **Topics Discussed**: For downstream reporting.
3. **Resolution Status**: Track as `solved`, `pending`, or `escalated`.
4. **Channel Switches**: Detect if a user moves from Web Form to WhatsApp.
5. **Customer Identifier**: Use Email address as the primary key.

### 3.3 Formal Agent Skills (Exercise 1.5)
The agent must be structured around five formal skills:
1. **Knowledge Retrieval Skill**: Semantic search on product documentation.
2. **Sentiment Analysis Skill**: Scoring every incoming message for confidence and emotion.
3. **Escalation Decision Skill**: Logic-based trigger after response generation.
4. **Channel Adaptation Skill**: Formatting text specifically for Email (Formal) vs WhatsApp (Concise).
5. **Customer Identification Skill**: Unifying metadata (phone/email) into a single `customer_id`.

### 3.4 MCP Server Implementation
Expose these tools via the Python MCP SDK:
- `search_knowledge_base(query)`
- `create_ticket(customer_id, issue, priority, channel)`
- `get_customer_history(customer_id)`
- `escalate_to_human(ticket_id, reason)`
- `send_response(ticket_id, message, channel)`

## 4. Mandatory Deliverables
The following documents must be generated during this phase:
- `specs/discovery-log.md`: Log of requirements found during exploration.
- `specs/customer-success-fte-spec.md`: Final crystallized functional spec.
- **Test Dataset**: 20+ edge cases per channel.
- **Response Templates**: Discovered templates for common queries.

## 5. Constraints & Guardrails
- **Hard Constraints**: NEVER discuss pricing, NEVER promise features not in docs, NEVER process refunds.
- **Processing Target**: Response time < 3 seconds.
- **Accuracy**: > 85% on the test set.

## 6. Acceptance Criteria
- [ ] Working prototype handles queries from Gmail, WhatsApp, and Web Form.
- [ ] MCP server exposes all 5 tools with channel-aware logic.
- [ ] Memory system preserves context after channel switching.
- [ ] All 5 Formal Skills are defined and operational.

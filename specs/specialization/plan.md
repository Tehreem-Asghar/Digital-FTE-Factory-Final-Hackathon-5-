# Architectural Plan: Stage 2 - Specialization (Refined)

## 1. Directory Strategy
We will transition from `src/` to the mandatory `production/` structure. This ensures compliance with grading criteria (Page 12).

## 2. Component Architecture (Production Flow)
1. **Intake Layer**: FastAPI endpoints for Web Form, Gmail, and WhatsApp.
2. **Streaming Layer**: Kafka producers push messages to `tickets.incoming` topic.
3. **Processing Layer**:
   - `UnifiedMessageProcessor` worker consumes events.
   - Calls `OpenAI Agents SDK` (Gemini backend).
   - Agent invokes `@function_tool`s (PostgreSQL/Vector interactions).
4. **Delivery Layer**: Response handler sends formatted replies back to user.

## 3. Detailed Data Schema (8 Tables)
We will implement the exact SQL schema from Pages 22-24, including:
- **Vector Search**: `knowledge_base` with `vector_cosine_ops` index for rapid retrieval.
- **Reporting**: `agent_metrics` to track sentiment and latency.

## 4. Execution Phases

### Phase 1: production/database/ & production/api/
- Establish PostgreSQL schema.
- Implement FastAPI skeleton with core endpoints.
- Setup Kafka topics.

### Phase 2: production/agent/ & production/channels/
- Implement the Gemini-OpenAI bridge.
- Develop channel-specific logic (Gmail API, Twilio).
- Migrate MCP tools to production `@function_tool`s.

### Phase 3: production/workers/ & Web Form
- Build the Kafka `message_processor`.
- Create the React/Next.js Web Support Form component.

### Phase 4: Kubernetes & Testing
- Containerize all services (Multi-pod).
- Implement Locust load testing and Chaos scenarios.

## 5. Success Metrics (Compliance Check)
- Survives 24-hour test with >99.9% uptime.
- P95 Latency < 3 seconds.
- Correct identity matching (>95% accuracy).

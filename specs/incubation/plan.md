# Architectural Plan: Stage 1 - Incubation

## 1. Scope & Goals
Build a functional prototype of "Flowie", the SaaSFlow AI Agent, using Python and the Model Context Protocol (MCP). The goal is to validate the core interaction loop, memory tracking, and channel-specific formatting before moving to production infrastructure.

## 2. Architecture Overview

### 2.1 Component Diagram
```
[User Input] --> [Simulator Script] --> [MCP Client]
                                          |
                                          v
                                    [MCP Server]
                                    (tools.py)
                                          |
                                          +--> [Knowledge Base] (product-docs.md)
                                          +--> [Ticket System] (In-Memory / JSON)
                                          +--> [Escalation Logic] (escalation-rules.md)
```

### 2.2 Tech Stack
- **Language**: Python 3.10+
- **Protocol**: `mcp` (Official Python SDK)
- **Search**: `numpy` + `scikit-learn` (Simple cosine similarity for prototype)
- **State**: In-memory dictionaries + JSON persistence (simulating DB)

## 3. Data Model (Prototype)

### 3.1 Ticket Schema
```json
{
  "id": "TKT-001",
  "customer_id": "email@example.com",
  "channel": "email",
  "status": "open",
  "sentiment_score": 0.8,
  "history": [
    {"role": "user", "content": "..."}
  ]
}
```

### 3.2 Skill Definitions
- **Knowledge Retrieval**: TF-IDF or simple keyword matching against `product-docs.md`.
- **Sentiment Analysis**: Basic keyword-based scoring (positive/negative word lists) for prototype speed.
- **Channel Adapter**: Template-based formatter.

## 4. Execution Plan

### Phase 1: Foundation
1. **Scaffold Project**: Set up `pyproject.toml`, `src/`, `tests/`.
2. **Load Context**: Write parsers for `context/*.md` files.
3. **Mock Database**: Implement a JSON-based state manager for tickets.

### Phase 2: MCP Server
1. **Server Setup**: Initialize `mcp.server.FastMCP`.
2. **Tool Implementation**:
   - `search_knowledge_base`
   - `create_ticket`
   - `get_customer_history`
   - `escalate_to_human`
   - `send_response`

### Phase 3: Core Logic (The "Brain")
1. **Agent Loop**: Write a script (`run_agent.py`) that simulates the LLM's decision-making process (using a mock or actual API call if key provided).
2. **Skill Integration**: Connect sentiment analysis and escalation rules to the loop.

### Phase 4: Validation
1. **Test Suite**: `pytest` for all tools.
2. **Simulation**: Run `sample-tickets.json` through the agent and log results to `specs/discovery-log.md`.

## 5. Risks
- **Performance**: Simple search might be inaccurate. *Mitigation: Accept lower accuracy for prototype; focus on flow.*
- **State Loss**: In-memory state resets on restart. *Mitigation: Dump state to `tickets.json` on exit.*

## 6. Success Metrics
- 5/5 MCP Tools operational.
- Correct formatting for Email vs WhatsApp.
- Escalation triggers correctly on "angry" sample tickets.

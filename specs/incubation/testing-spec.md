# Specification: Incubation Phase Testing

## 1. Objective
Ensure the prototype agent (Flowie) behaves predictably according to the hard constraints and business logic defined in the dossier. These tests must pass before the "Transition to Custom Agent" begins.

## 2. Test Suites (Ref: PDF Pages 16-18)

### 2.1 Core Logic & Edge Cases
- **Test ID**: `TC-001` (Empty Message)
  - **Scenario**: User sends an empty string.
  - **Expected**: Agent asks for clarification, does not crash.
- **Test ID**: `TC-002` (Pricing Escalation)
  - **Scenario**: User asks "How much does the Pro plan cost?".
  - **Expected**: `escalated = True`, reason includes "pricing".
- **Test ID**: `TC-003` (Angry Customer)
  - **Scenario**: User uses profanity or says "Your product is trash".
  - **Expected**: Immediate escalation to human.

### 2.2 Workflow & Tool Order
- **Test ID**: `TC-004` (Tool Sequence)
  - **Scenario**: User asks a technical question.
  - **Expected**:
    1. `create_ticket` is called first.
    2. `search_knowledge_base` is called.
    3. `send_response` is called last.
- **Test ID**: `TC-005` (Response Format)
  - **Scenario**: User message via `channel: whatsapp`.
  - **Expected**: Response length < 300 characters.

### 2.3 Knowledge Retrieval
- **Test ID**: `TC-006` (Documentation Accuracy)
  - **Scenario**: User asks "How to create a workspace?".
  - **Expected**: Response contains correct steps from `product-docs.md`.

## 3. Success Metrics (Performance Baseline)
- **Response Time**: Internal processing must be under 3 seconds.
- **Accuracy**: Agent must correctly identify 85% of queries from the sample ticket set.
- **Escalation Rate**: Should be < 20% for routine queries (ensure agent isn't being "lazy").

## 4. Tools for Validation
- `pytest` with `pytest-asyncio` for unit testing the MCP tools.
- A custom simulator script for E2E flow testing.

# Transition Checklist: General → Custom Agent (Incubation Discoveries)

## 1. Discovered Requirements
- **Channel Specifics**: WhatsApp users expect immediate, one-line answers. Email users prefer detailed step-by-step guides.
- **Triage Priority**: Billing issues must be escalated before the agent even attempts a knowledge search to prevent incorrect financial advice.
- **Continuity**: The agent needs a unique `customer_id` (Email) to bridge conversations between Web Form and WhatsApp.

## 2. Working Prompts (SaaSFlow System Intent)
"You are Flowie, a Senior Success Expert. Always create a ticket first. If sentiment < 0.3, escalate. For WhatsApp, be concise. For Email, be formal. Never discuss pricing."

## 3. Edge Cases Found & Handled
| Edge Case | How It Was Handled | Test Case Needed |
|-----------|-------------------|------------------|
| Empty message | Asks for clarification | Yes |
| Pricing inquiry | Immediate escalation | Yes |
| Refund request | Immediate escalation | Yes |
| Profanity/Anger | Immediate escalation | Yes |
| Out of context | Polite redirection to product features | Yes |
| Lamba content | Truncated for WhatsApp formatting | Yes |

## 4. Performance Baseline
- **Avg Response Time**: ~1.2s
- **Accuracy**: 90% (Handled 9/10 core intents correctly)
- **Escalation Rate**: 20% (Correctly escalated billing/anger)

## 5. Mapping for Stage 2
- **Prototype Script** → `agent/customer_success_agent.py`
- **MCP Tools** → `OpenAI Agents SDK @function_tool`
- **In-memory JSON** → `PostgreSQL Database`
- **Manual Simulation** → `FastAPI Endpoints + Kafka Events`

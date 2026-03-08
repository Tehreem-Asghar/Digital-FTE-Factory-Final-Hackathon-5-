# Customer Success FTE - Agent Skills Manifest

> Formal definition of all reusable capabilities for the **Flowie** Digital FTE Agent.
> Version: 1.0 | Last Updated: 2026-03-08

---

## Skill 1: Knowledge Retrieval

| Field | Value |
|-------|-------|
| **Skill ID** | `knowledge_retrieval` |
| **Tool** | `search_knowledge_base` |
| **When to Use** | Customer asks a product question, how-to, or troubleshooting query |
| **Inputs** | `query` (str): Natural language search text; `max_results` (int, default=3): Result limit |
| **Outputs** | Formatted documentation snippets with titles and relevance scores |
| **Method** | 1. Generate 768D embedding via Gemini `gemini-embedding-001` → 2. Cosine similarity search on `knowledge_base` table (pgvector IVFFlat index) → 3. Fallback to ILIKE keyword search if embeddings fail |
| **Constraints** | Max 5 results per query; only returns verified documentation from `knowledge_base` table |
| **Error Handling** | Returns "No relevant documentation found" if zero matches; falls back to keyword search on embedding API failure |

---

## Skill 2: Sentiment Analysis

| Field | Value |
|-------|-------|
| **Skill ID** | `sentiment_analysis` |
| **Function** | `analyze_sentiment()` |
| **When to Use** | Every inbound customer message (called automatically in `send_response`) |
| **Inputs** | `text` (str): Customer message content |
| **Outputs** | Float score 0.0 (very negative) to 1.0 (very positive) |
| **Method** | 1. Keyword-based analysis with regex word boundary matching (17 negative words) → 2. If `neg_count >= 2`, return 0.2 immediately → 3. For messages >100 chars, call Gemini API for nuanced scoring → 4. Default to 0.7 (neutral-positive) if no signals detected |
| **Constraints** | Gemini API rate-limited (5 req/min per key); uses key rotation for mitigation |
| **Thresholds** | `< 0.3` = Angry (triggers escalation); `0.3-0.6` = Concerned; `> 0.6` = Satisfied |

---

## Skill 3: Escalation Decision

| Field | Value |
|-------|-------|
| **Skill ID** | `escalation_decision` |
| **Tool** | `escalate_to_human` |
| **When to Use** | After generating response, when escalation triggers are detected |
| **Inputs** | `ticket_id` (str): UUID of the ticket; `reason` (str): Escalation reason |
| **Outputs** | Confirmation message with escalated ticket ID |
| **Triggers** | 1. Customer mentions "lawyer", "legal", "sue", "attorney" → 2. Sentiment score < 0.3 → 3. Cannot find relevant KB info after 2 search attempts → 4. Customer explicitly requests human help → 5. Pricing negotiations or refund requests → 6. Account security or data loss reports |
| **Actions** | Updates ticket status to `escalated`; updates conversation status and `escalated_to = 'human_agent'`; logs escalation metric to `agent_metrics` table |
| **Constraints** | Must include full conversation context; must log reason for audit trail |

---

## Skill 4: Channel Adaptation

| Field | Value |
|-------|-------|
| **Skill ID** | `channel_adaptation` |
| **Function** | `format_for_channel()` in `formatters.py` |
| **When to Use** | Before sending any response via `send_response` tool |
| **Inputs** | `message` (str): Raw response text; `channel` (str): Target channel; `customer_name` (str): Customer's name |
| **Outputs** | Channel-formatted response string |
| **Channel Rules** | |

| Channel | Style | Format | Max Length |
|---------|-------|--------|-----------|
| **Email** | Formal, detailed | Greeting + body + signature block ("Best regards, The SaaSFlow Success Team") | 500 words |
| **WhatsApp** | Conversational, concise | "Flowie: {message}" with checkmark emoji; truncated at 300 chars | 300 chars |
| **Web Form** | Semi-formal, structured | "SaaSFlow Support: {message}" | 300 words |

---

## Skill 5: Customer Identification (Cross-Channel)

| Field | Value |
|-------|-------|
| **Skill ID** | `customer_identification` |
| **Functions** | `resolve_customer_by_identifier()`, `register_customer_identifier()` |
| **When to Use** | On every incoming message to resolve or create customer identity |
| **Inputs** | Message metadata: `email` or `phone` from any channel |
| **Outputs** | Unified `customer_id` (UUID) with merged cross-channel history |
| **Method** | 1. Check `customer_identifiers` table for existing mapping → 2. Fallback to direct `customers` table lookup by email/phone → 3. If no match, create new customer record → 4. Register identifier for future cross-channel matching |
| **Accuracy Target** | >95% cross-channel identification accuracy |
| **Supported Identifiers** | `email` (primary), `phone`/`whatsapp` (secondary) |

---

## Skill Orchestration Flow

```
Incoming Message
    │
    ▼
┌─────────────────────────┐
│ Skill 5: Identify       │ → Resolve/create customer_id
│ Customer                │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│ Skill 2: Analyze        │ → Score sentiment (0.0-1.0)
│ Sentiment               │
└───────────┬─────────────┘
            │
    ┌───────┴───────┐
    │ sentiment<0.3?│
    └───┬───────┬───┘
       YES     NO
        │       │
        ▼       ▼
┌──────────┐ ┌─────────────────────┐
│ Skill 3: │ │ Skill 1: Knowledge  │ → Search KB
│ Escalate │ │ Retrieval           │
└──────────┘ └───────────┬─────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ Skill 4: Channel    │ → Format for email/whatsapp/web
              │ Adaptation          │
              └───────────┬─────────┘
                          │
                          ▼
                    Send Response
```

---

## Tool Registry Summary

| Tool Name | Input Schema | Database Tables Touched |
|-----------|-------------|------------------------|
| `search_knowledge_base` | `KBSearchInput(query, max_results)` | `knowledge_base` (READ) |
| `create_ticket` | `TicketInput(customer_id, issue, priority, channel)` | `customers`, `customer_identifiers`, `conversations`, `tickets`, `messages` (WRITE) |
| `get_customer_history` | `HistoryInput(customer_id)` | `customer_identifiers`, `customers`, `messages`, `conversations` (READ) |
| `escalate_to_human` | `EscalationInput(ticket_id, reason)` | `tickets`, `conversations`, `agent_metrics` (WRITE) |
| `send_response` | `ResponseInput(ticket_id, message, channel)` | `tickets`, `customers`, `messages`, `conversations`, `agent_metrics` (WRITE) |

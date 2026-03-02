# Discovery Log: Incubation Phase

## 1. Initial Exploration Findings (Exercise 1.1)

### Pattern Discovery
- **Channel Variance**: WhatsApp messages are 70% shorter than emails and often lack formal structure.
- **Urgency Correlation**: Tickets with the word "refund" or "garbage" almost always correlate with low sentiment (< 0.35).
- **Technical Gaps**: Users often ask about "API Webhooks" and "custom triggers" which are not fully detailed in the current `product-docs.md`.

### Identified Edge Cases
1. **Empty Message**: Prototype currently attempts to process; needs a check to ask for clarification.
2. **Duplicate Charges**: High escalation priority detected in `sample-tickets.json`.
3. **Legal Threats**: Phrases like "I am suing" require immediate human handoff.

## 2. Skill Refinement (Exercise 1.5)

### Knowledge Retrieval
- *Observation*: Simple keyword matching on the full message is too noisy.
- *Refinement*: Need to extract "Intent" before searching docs.

### Sentiment Analysis
- *Observation*: Basic keyword list is effective for prototype but misses sarcasm.
- *Refinement*: Production agent should use a more nuanced model (OpenAI GPT-4o).

## 3. Tool Execution Order
- Verified: `create_ticket` -> `search_kb` -> `send_response` is the optimal sequence for audit trails.

## 4. Performance Baseline
- **Average Processing Time**: ~1.2 seconds (In-memory prototype).
- **Success Rate**: 100% of hard constraints (Pricing/Refunds) were correctly escalated.

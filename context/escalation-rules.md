# SaaSFlow Escalation Rules

## 1. Hard Escalation Triggers
Hand over to a human specialist immediately if:

### 1.1 Pricing & Billing
- User asks for a **refund**.
- User wants to negotiate **subscription price**.
- User asks for a **custom Enterprise quote**.

### 1.2 Negative Sentiment
- Sentiment score is below **0.3**.
- User uses **profanity** or aggressive language.
- User mentions **legal action**, **lawyers**, or **suing**.

### 1.3 Capability Gaps
- Agent cannot find the answer in `product-docs.md` after **2 attempts**.
- User explicitly says "Talk to a person" or "Human support".

## 2. Handover Protocol
1. Polite acknowledgment: "I am connecting you with a human specialist who can assist with this."
2. Internal tag: Mark as `escalated`.
3. Pass full context to the support queue.

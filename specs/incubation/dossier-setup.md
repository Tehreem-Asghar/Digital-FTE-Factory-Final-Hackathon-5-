# Specification: Development Dossier Setup (Page 4)

## 1. Objective
Establish the "Dossier" - a set of context files that provide the AI Agent with all necessary business and technical knowledge before the "Initial Exploration" phase begins.

## 2. Dossier Structure (`context/` directory)

### 2.1 `company-profile.md`
- **Content**: Details about SaaSFlow (SaaS project management).
- **Required Info**: Mission, target audience (startups/agencies), and support strategy.

### 2.2 `product-docs.md`
- **Content**: Technical and functional documentation.
- **Required Info**: Workspaces, Kanban boards, "Flow" automation engine limits, billing plans (Free/Pro/Enterprise), and basic troubleshooting.

### 2.3 `sample-tickets.json`
- **Content**: A dataset of 50+ real-world simulation tickets.
- **Required Info**: Must include a mix of channels (Gmail, WhatsApp, Web Form), varying sentiment scores, and technical vs. billing queries.

### 2.4 `escalation-rules.md`
- **Content**: Logic for human handovers.
- **Required Info**: Specific triggers (pricing inquiries, refunds, sentiment < 0.3, legal threats).

### 2.5 `brand-voice.md`
- **Content**: Personality and formatting guidelines.
- **Required Info**: "Flowie" persona definition, channel-specific formatting rules (Email = Formal, WhatsApp = Concise).

## 3. Workflow for Dossier Creation
1. **Define Content**: Draft the core business logic for SaaSFlow.
2. **Review**: Ensure all "Hard Constraints" from the PDF (No pricing, No refunds) are embedded in the rules.
3. **Validation**: Verify that the `sample-tickets.json` contains enough edge cases to test the escalation logic.

## 4. Success Criteria
- All 5 files exist in the `context/` folder.
- Content is sufficient for the agent to answer 80% of routine questions without hallucinating.

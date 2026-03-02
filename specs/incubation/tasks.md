# Task List: Stage 1 - Incubation

## Phase 1: Foundation & Context Setup

### Task 1.1: Project Scaffolding
- **Description**: Initialize the Python environment and directory structure.
- **Acceptance Criteria**:
  - [ ] `pyproject.toml` exists with dependencies (`mcp`, `pytest`, `pydantic`).
  - [ ] Directory structure established: `src/agent`, `src/tools`, `tests/`, `context/`.
- **Validation**: Run `pip install -e .` and verify structure.

### Task 1.2: Context Dossier Loader
- **Description**: Implement a module to read and parse SaaSFlow context files (`.md` and `.json`).
- **Acceptance Criteria**:
  - [ ] `ContextLoader` can load `product-docs.md`.
  - [ ] `ContextLoader` can parse `sample-tickets.json` into a list of objects.
- **Test Case**: `tests/test_loader.py` - Verify that loading `brand-voice.md` returns the correct persona name ("Flowie").

---

## Phase 2: Agent Skills Implementation

### Task 2.1: Sentiment Analysis Skill
- **Description**: Basic logic to score customer sentiment.
- **Acceptance Criteria**:
  - [ ] Keyword-based scoring (e.g., "broken", "angry" -> low score).
  - [ ] Returns a float between 0.0 and 1.0.
- **Test Case**: `tests/test_skills.py` - Input "I am suing you" should result in sentiment < 0.3.

### Task 2.2: Channel Adaptation Skill
- **Description**: Logic to format responses based on the channel metadata.
- **Acceptance Criteria**:
  - [ ] `whatsapp` channel returns short, conversational text.
  - [ ] `email` channel wraps text in a formal greeting and signature.
- **Test Case**: Verify `format_for_channel("Hello", "email")` includes "Best regards".

---

## Phase 3: MCP Server & Tools

### Task 3.1: Initialize MCP Server
- **Description**: Set up the `FastMCP` server instance.
- **Acceptance Criteria**:
  - [ ] Server named `saasflow-fte` initialized.
  - [ ] Server starts without errors.
- **Validation**: Run server script and check logs.

### Task 3.2: Core Tools Implementation
- **Description**: Implement the 5 mandated tools.
- **Acceptance Criteria**:
  - [ ] `search_knowledge_base`: Returns top 3 matches from `product-docs.md`.
  - [ ] `create_ticket`: Saves a ticket to a local `tickets.json` file.
  - [ ] `get_customer_history`: Filters `tickets.json` by `customer_id`.
  - [ ] `escalate_to_human`: Updates ticket status to `escalated`.
  - [ ] `send_response`: Logs the delivery attempt and formats via the Adaptation Skill.
- **Test Case**: `tests/test_tools.py` - Call `create_ticket` and verify the ID exists in `tickets.json`.

---

## Phase 4: Core Loop & Simulation

### Task 4.1: Prototype Core Loop
- **Description**: Create a simulation script that takes a message, runs it through skills, and calls MCP tools.
- **Acceptance Criteria**:
  - [ ] Loops through `sample-tickets.json`.
  - [ ] For each ticket: Logs sentiment -> Searches Docs -> Formats Response -> Logs Status.
- **Validation**: Run `python src/simulator.py` and verify console output for 5 sample tickets.

---

## Phase 5: Documentation

### Task 5.1: Discovery Log & Final Spec
- **Description**: Record findings and crystallize the production spec.
- **Acceptance Criteria**:
  - [ ] `specs/discovery-log.md` contains 5+ identified edge cases.
  - [ ] `specs/customer-success-fte-spec.md` updated with finalized tool schemas.
- **Validation**: File existence check.

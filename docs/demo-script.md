# Demonstration Narrative

## Opening Context

Begin on the Constellations School homepage to establish the project as an embedded school support experience — not a standalone chatbot. The IT Agent button is visible in the header and as a floating launcher. This signals intentional product thinking: the AI is a feature of a real user environment, not a demo console.

## Recommended Demonstration Sequence

### 1. Small Talk — Smalltalk Agent
**Say or type:** "Hey, how are you doing today?"

**What happens:** The Smalltalk Agent responds warmly in 1–2 sentences and invites the user to ask about IT support. After a second casual message, it steers more clearly back to IT.

**Talking point:** The bot can hold a brief natural conversation without breaking. It doesn't refuse or robotically redirect on the first message. Once 2 or more consecutive casual turns are detected, the system increases redirect pressure — tracked in session metadata — and steers back to IT support.

---

### 2. Password Help Question — Knowledge Agent → Password Offer
**Say or type:** "How do I reset my password?"

**What happens:** The Intake Agent routes to Knowledge. The Knowledge Agent retrieves the relevant Confluence documentation, generates a grounded answer explaining the reset process, then offers: "Would you like me to perform the reset for you?"

**Talking point:** This is the two-flow password design. A question about passwords goes to RAG first — the user gets an actual explanation. The system then offers to act, bridging knowledge and workflow naturally. The LLM assessed this answer as high-confidence based on retrieved context, so it did not escalate.

---

### 3. Explicit Password Reset — Workflow Agent
**Say or type:** "Reset password for teacher3"

**What happens:** The Intake Agent routes directly to Workflow (skipping RAG — this is an action request, not a question). The Workflow Agent extracts the username and shows: "I found [display name] (teacher3). Should I reset the password for this user?" After you confirm, it calls the MCP tool to execute the reset and returns the temporary password and policy.

**Talking point:** Note the mandatory confirmation step — the system never executes a reset without explicit user approval. The LLM handles the confirmation detection, so "yep", "go for it", and "sounds good" all work — not just the word "yes."

---

### 4. Wi-Fi Troubleshooting — Knowledge Agent
**Say or type:** "My Chromebook won't connect to the school Wi-Fi"

**What happens:** The Knowledge Agent retrieves relevant troubleshooting documentation and generates a grounded, step-by-step answer.

**Talking point:** After a workflow action, the system returns cleanly to retrieval-based support. The answer is grounded in the actual school IT knowledge base — not a general guess.

---

### 5. Low-Confidence Escalation
**Say or type:** "What do I do if a student's account gets locked after a ransomware event?"

**What happens:** The Knowledge Agent finds no confident match in the knowledge base (self-assessed confidence below threshold). Rather than guessing, it escalates: "I wasn't able to find a confident answer — a human IT staff member would be best for this." It offers an appointment or request submission.

**Talking point:** The system knows what it doesn't know. LLM self-assessed confidence gates escalation — this is more semantically reliable than a raw FAISS distance score.

---

### 6. Appointment Scheduling — Escalation Agent
**Say or type:** "Yes, show me available appointments" (or click the option)

**What happens:** The Escalation Agent calls the MCP tool to list available slots. The user selects a slot from the structured card. The agent books it via MCP and confirms.

**Talking point:** The entire escalation path — offer → list → book — is driven by LLM action decisions, not keyword matching. Any natural affirmative ("sure, show me", "yes please") triggers the appointment listing correctly.

---

### 7. Software/Hardware Request in Plain English — Escalation Agent
**Say or type:** "I need Adobe Premiere for my video production class — it's for the whole film department"

**What happens:** The Escalation Agent recognizes this as a submittable request (enough context: what + why), creates a support ticket via MCP, and confirms: "Your request has been submitted. IT will get back to you within 72 hours."

**Talking point:** Previous versions required users to fill out a rigid 5-field form. The LLM now evaluates whether the user has provided enough context to submit — plain English works.

---

## Key Talking Points

- **LLM-first architecture.** Every routing and decision call goes to the LLM first. Python logic handles only deterministic data tasks (slot ID extraction, regex fast-path). This is the core architectural shift from the original implementation.
- **Structured prompts with examples.** Every agent prompt uses concrete examples and explicit decision fields to guide the model reliably.
- **Structured output on decision-making LLM calls.** Routing, workflow, escalation, and retrieval-answer calls return typed JSON: `{intent/action, confidence, reasoning}`. This enables gating, logging, and the reasoning trace.
- **Reasoning trace in every response.** The API returns `routing_confidence`, `agent_step`, `answer_confidence`, and `retrieval_scores` on every turn — making the system fully observable.
- **RAG with paragraph-level chunking.** Confluence pages are split into overlapping 800-character chunks for precise retrieval, not one blob per page.
- **MCP as the tool interface.** All operational actions (password reset, ticket creation, appointments) go through a standardized MCP server — the same pattern used in enterprise AI tooling.
- **Session memory for continuity.** Pending usernames and workflow state persist across turns through SQLite memory, enabling natural multi-step conversations.
- **Safe fallbacks on every agent.** Every agent wraps its LLM call in `try/except`. If the model call fails, intake defaults to `escalation`, workflow defaults to `ask_for_username`, knowledge escalates with a human-support offer, and escalation offers appointments. No agent silently fails.

## Special-Consideration Emphasis

### Retrieval-Augmented Generation
Emphasize that the Knowledge Agent does not generate answers from general model knowledge. It embeds the question, searches the FAISS index, retrieves school-specific IT documentation, and generates an answer grounded only in that context. The LLM self-assesses its confidence and escalates when the retrieved context is insufficient.

### Workflow Automation
The password reset is not described — it is executed. The MCP tool performs the actual (simulated) operation and returns a temporary password, role-specific policy, and next-step instructions. The workflow enforces a confirmation step before every execution.

### MCP Integration
MCP is the standard tool-access layer between agent reasoning and operational tooling. Agents call named tools through a typed client; the server owns the implementation. This is the same architectural pattern appearing in enterprise AI platforms and OpenAI's tool-use standards.

### Multi-Agent Collaboration
The handoff from knowledge → workflow → escalation → smalltalk is not branching inside a single agent. Each agent has a single responsibility and clear termination point. The Intake Agent handles all routing using LLM reasoning. This separation makes the system easier to debug, extend, and explain.

### Industry Awareness
Position this as a lightweight educational prototype of enterprise AI support patterns. Glean, Moveworks, and ServiceNow Now Assist demonstrate that modern support platforms combine grounded retrieval, workflow automation, tool standardization, and human escalation — this project implements those same ideas at K-12 school scale, with observable reasoning.

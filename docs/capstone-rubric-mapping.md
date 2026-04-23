# Capstone Rubric Alignment

## Project Definition and Use Case

This project addresses a realistic K-12 IT support problem: a small school technology team must respond to high volumes of repetitive requests while supporting classroom continuity and higher-priority incidents. The selected use cases cover password reset, Wi-Fi troubleshooting, Chromebook support, software and hardware requests, casual conversation handling, and escalation to human support.

The primary success criteria are:
- accurate LLM-guided routing of all common support request types
- grounded, confidence-gated answers from the school IT knowledge base
- successful multi-step password reset workflows with mandatory confirmation
- natural small talk engagement with graceful redirection to IT support
- appropriate escalation when the system lacks confidence or authority
- observable reasoning traces (intent, confidence, agent step) on every response turn

## Agent Identification

The system implements five agents orchestrated by LangGraph — one intake router and four specialists:

### Intake Agent
Classifies every user message using a structured LLM prompt with few-shot examples. Returns `intent` (`knowledge`, `workflow`, `escalation`, or `smalltalk`), `confidence` (0.0–1.0), and `reasoning` (one sentence). It is LLM-led for semantic routing, with deterministic safe fallbacks if the model is unavailable.

### Knowledge Agent
Handles retrieval-augmented question answering. Retrieves paragraph-level chunks from a FAISS index built on Confluence school IT documentation. The LLM generates a structured answer with self-assessed confidence and a password-relevance flag. Escalates when confidence is below 0.6. When a password question is detected, appends an offer to execute the reset — bridging knowledge and workflow without hardcoded keyword matching.

### Workflow Agent
Executes the password reset workflow through MCP tools. Uses the LLM to extract usernames from natural-language input and to decide the next safe step (`ask_for_username`, `confirm_target_user`, `execute_reset`, `escalate`). Enforces a mandatory confirmation step before any destructive operation. Creates support tickets on tool failures.

### Escalation Agent
Handles appointment scheduling, software/hardware request submission, and acknowledged declines. Uses LLM-guided action classification with a deterministic slot-ID fast path. Recognizes plain-English request submissions without requiring a rigid field format. Books appointments deterministically when a slot ID is detected.

### Smalltalk Agent
Handles casual conversation naturally for brief exchanges, then redirects to IT support. Tracks consecutive smalltalk turns in session metadata and increases redirect pressure once 2 or more consecutive casual turns are detected. Prevents the bot from feeling abrupt or broken when users greet it.

## UX Design

The application includes a school-themed web interface rather than a standalone technical console. The chatbot is embedded into a fictional Constellations School homepage with multiple support entry points. The interface supports conversational interaction, starter actions, structured response cards, appointment scheduling, and request-submission forms.

The reasoning trace returned on every response can power an optional developer panel showing routing confidence, agent step decisions, and retrieval quality — demonstrating system observability alongside the user-facing experience.

## System Development

The system is implemented as a full-stack application with the following major components:
- React frontend (school-themed SPA with chat modal)
- FastAPI backend with session-aware `POST /chat` endpoint
- LangGraph orchestration with five agents (one intake router + four specialists)
- OpenAI structured output API for decision-making LLM calls (routing, step decisions, answer generation)
- OpenAI embeddings (`text-embedding-3-small`) + FAISS vector store for RAG
- Paragraph-level chunking with overlap for precise retrieval
- MCP server (`FastMCP`) and typed MCP client for tool integration
- SQLite session memory with 6-turn context window
- Dockerized frontend and backend services
- `ReasoningTrace` schema surfaced in every API response

## Agentic Design Principles Applied

**LLM primary, Python for data formats and fast paths.** Semantic decisions (routing, step selection, confidence assessment, request classification) are made by the LLM via structured output. Python regex is used only for deterministic data-format tasks: slot ID extraction and username fast-path matching.

**Structured output for decision points.** Routing, workflow, escalation, and retrieval-answer calls return typed JSON objects with `action/intent`, `confidence`, and `reasoning`. This enables gating, logging, and observability without adding a second verification call.

**Fail safe, not fail open.** LLM exceptions default to `escalation` at intake and `ask_for_username` at workflow — the safest possible defaults in each context.

**Observable by design.** A `ReasoningTrace` is appended to every `ChatResponse`, exposing routing confidence, agent step reasoning, LLM answer confidence, and FAISS retrieval scores.

## Testing and Validation

The current validation approach covers scenario testing for:
- small talk and casual greetings (smalltalk agent)
- password-help questions (knowledge agent → password offer)
- explicit password-reset execution with natural-language confirmation (workflow agent)
- Wi-Fi and device troubleshooting (knowledge agent)
- low-confidence retrieval fallback to escalation
- plain-English software/hardware request submission (escalation agent)
- appointment scheduling and slot booking
- multi-turn session continuity with pending username tracking

## Presentation Readiness

The project supports a coherent scenario flow:
1. Casual greeting — handled by the smalltalk agent with a brief reply and IT redirect
2. Password-help question — knowledge agent retrieves and explains the reset process, then offers to execute
3. Explicit password reset — workflow agent confirms user, then executes
4. Wi-Fi troubleshooting — knowledge agent returns a grounded answer
5. Unsupported or low-confidence question — escalates with appointment offer
6. Appointment selection — books the slot via MCP tool
7. Software or hardware request in plain English — submitted without requiring rigid field format

## Special Considerations

### RAG Integration
The project implements a full RAG pipeline: live Confluence page ingestion via MCP, paragraph-level chunking with overlap, OpenAI embeddings, FAISS vector storage, top-k retrieval, and LLM grounded answer generation with self-assessed confidence. The LLM's confidence score replaces a fragile FAISS distance threshold, making escalation decisions semantically grounded.

### Workflow Automation
Password reset and related support actions are executed through a structured multi-step workflow with mandatory confirmation. The workflow layer is fully separate from the retrieval layer, making operational logic auditable and safe.

### Integration via MCP
MCP is used as the standard tool-access layer between agent logic and operational tooling. Six tools are exposed through a `FastMCP` server: user lookup, password reset, ticket creation, appointment listing, appointment booking, and Confluence retrieval. This demonstrates a standardized, extensible approach to tool integration.

### Multi-Agent Collaboration
The system separates knowledge retrieval, workflow execution, escalation, and small talk into four distinct specialist agents, each routed to by a dedicated intake agent, with clear boundaries throughout. The Intake Agent handles all routing using LLM reasoning. Each specialist agent handles only its designated concern — making the system easier to debug, extend, and explain.

### Industry Awareness
The project aligns with enterprise AI support patterns demonstrated by platforms such as Glean, Moveworks, and ServiceNow Now Assist: grounded retrieval, workflow automation, tool standardization, and human-support escalation, applied at K-12 school scale.

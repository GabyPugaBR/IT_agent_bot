# Constellations IT Support Agent Architecture

## System Summary

Constellations IT Support is a multi-agent AI support system for school IT operations. The system accepts chat requests from a React frontend, routes them through a FastAPI backend, and orchestrates them through a LangGraph agent graph. Every request is classified by an LLM-powered Intake Agent and dispatched to one of four specialist agents:

- **Knowledge Agent** — retrieval-augmented answers from the school IT knowledge base
- **Workflow Agent** — automated password reset execution with confirmation guardrails
- **Escalation Agent** — human-support handoff via appointments and request submission
- **Smalltalk Agent** — natural conversational engagement before steering back to IT support

The system is designed around a core principle: **the LLM reasons first**. Python logic is reserved for deterministic data-format tasks (slot ID extraction, fast-path username matching). All semantic decisions — routing, step selection, confidence assessment, request classification — are made by the language model using structured output and chain-of-thought prompting.

## High-Level Flow

1. User sends a message from the React frontend.
2. Frontend calls the FastAPI backend `POST /chat` endpoint.
3. FastAPI loads session memory from SQLite and builds the initial agent state.
4. LangGraph dispatches the request to the **Intake Agent**.
5. The Intake Agent uses the LLM to classify the request into one of four intents: `knowledge`, `workflow`, `escalation`, or `smalltalk`. It returns a confidence score and a one-sentence reasoning trace.
6. LangGraph routes to the appropriate specialist agent.
7. The specialist agent executes its logic — retrieving documents, running MCP tools, or generating a conversational reply — and returns a response with structured metadata.
8. FastAPI appends a `reasoning_trace` (routing confidence, agent step, answer confidence, retrieval scores) to the response and saves the turn to SQLite memory.
9. The frontend renders the response, structured cards, follow-up actions, appointment slots, or request forms as appropriate.

## Core Components

### 1. Frontend Layer

- React single-page application embedded in a school-themed landing page
- Chat modal with starter pills, structured response cards, appointment slot selection, and request forms
- Sends `POST /chat` with message and session ID; renders `reasoning_trace` and `metadata` from response
- Environment-configured backend URL via `REACT_APP_API_URL`

### 2. API Layer

- FastAPI backend
- Primary endpoint: `POST /chat`
- Health endpoint: `GET /`
- Builds agent state, invokes the LangGraph graph, assembles `ReasoningTrace`, and persists the turn to SQLite

### 3. Orchestration Layer

- Built with LangGraph `StateGraph`
- Entry point: **Intake Agent** (always first)
- Conditional routing to four specialist agents based on classified intent
- Each agent terminates at `END` after producing its response

### 4. Memory Layer

- SQLite-based session and conversation history storage
- Stores session metadata: session ID, username, user role, last intent, last agent
- Stores recent message history with per-turn metadata (pending usernames, workflow results, follow-up actions)
- Last 6 messages retrieved per turn to provide conversational context to agents

### 5. Knowledge Layer

- Retrieval-augmented generation pipeline over Confluence school IT documentation
- Documents fetched live via MCP, cleaned, and split into overlapping paragraph-based chunks (800 char max, 100 char overlap) for precise retrieval
- Embeddings generated with OpenAI `text-embedding-3-small` and stored in a FAISS flat inner-product index
- At query time: embed question → search FAISS → retrieve top-k chunks → LLM generates structured answer with self-assessed confidence, password-relevance flag, and source reasoning
- If LLM-assessed confidence < 0.6, agent escalates rather than guessing

### 6. Tool Layer

- MCP client launches a local `FastMCP` support server over stdio
- Agents call tools through the MCP client; the server wraps all operational logic
- MCP tools available:
  - `lookup_user` — look up a school user by username
  - `reset_user_password` — generate and apply a role-appropriate temporary password
  - `create_support_ticket` — log an escalation or failure as a support ticket
  - `list_it_appointments` — retrieve available IT appointment slots
  - `book_it_appointment` — book a selected slot
  - `fetch_confluence_pages` — retrieve live school IT documentation

### 7. Data Layer

- Synthetic user directory in JSON (students, teachers, staff, admins with role-specific password policies)
- Support ticket records in JSON
- Appointment calendar slots in JSON
- SQLite database for session and conversation memory
- FAISS vector index and chunk metadata for RAG

## Agent Descriptions

### Intake Agent

**Role:** LLM-powered router. The first node in every conversation turn.

**How it works:**
- Formats the last 6 conversation turns as a transcript
- Calls the LLM with a chain-of-thought prompt and structured output schema
- LLM returns: `intent`, `confidence` (0.0–1.0), `reasoning` (one sentence)
- Returns are written to `metadata` as `routing_confidence` and `routing_reasoning`
- Exception fallback: `escalation` (the safest default)

**What it handles:**
- `knowledge` — informational questions, how-to, policy, troubleshooting
- `workflow` — action requests (password reset) or workflow continuations (providing username, confirming reset)
- `escalation` — appointments, software/hardware requests, unsupported issues
- `smalltalk` — casual conversation, greetings, off-topic messages

**Why it matters:** Every misroute cascades into a wrong-agent experience. The Intake Agent was previously driven by 120+ lines of keyword sets and heuristics. It now uses a single LLM call with few-shot examples and explicit continuation rules, making it robust to natural-language variation.

### Knowledge Agent

**Role:** Retrieval-augmented question answering grounded in school IT documentation.

**How it works:**
- Embeds the user query and searches the FAISS index for top-k matching chunks
- Sends retrieved chunks to the LLM with a structured output prompt
- LLM returns: `answer`, `answer_confidence`, `is_password_related`, `reasoning`
- If `answer_confidence < 0.6` → escalates with a human-support offer
- If `is_password_related: true` → appends an offer to execute the reset and sets `offer_password_reset` in metadata

**Why it matters:** Keeps answers grounded in institutional documentation rather than free-form model generation. The LLM's self-assessed confidence replaces a fragile FAISS distance threshold.

### Workflow Agent

**Role:** Safe, confirmed execution of IT operations — currently password reset.

**How it works:**
- Attempts fast-path username extraction via regex; falls back to LLM extraction for natural-language variations ("teacher number 5", "admin-1")
- Searches conversation history for a `pending_reset_username` from a prior turn
- Calls the LLM to decide the next step: `ask_for_username`, `confirm_target_user`, `execute_reset`, or `escalate`
- LLM returns: `action`, `confidence`, `reasoning`
- Never executes a reset without a confirmed pending target
- Calls MCP tools for user lookup, password reset, and ticket creation on failure

**Why it matters:** Password reset is a sensitive operation. The workflow is intentionally sequential with a mandatory confirmation step. The LLM handles the full range of affirmative language ("yep", "go for it", "sounds good") without a brittle whitelist.

### Escalation Agent

**Role:** Human-support handoff — appointment scheduling, software/hardware requests, and acknowledged declines.

**How it works:**
- If a slot ID (`slot-NNN`) is detected in the message, deterministically books that appointment (no LLM needed)
- Otherwise calls the LLM to decide the action: `show_appointments`, `offer_appointments`, `show_request_form`, `submit_request`, `acknowledge_decline`, or `book_appointment`
- LLM also returns `is_request_submission: true/false` — replacing a previous check that required all 5 rigid fields to be present in the user's message
- Calls MCP tools for appointment listing, booking, and ticket creation

**Why it matters:** Users submitting requests in plain English ("I need Adobe for my video class") now have their submissions recognized and processed without needing to follow a rigid form format.

### Smalltalk Agent

**Role:** Natural conversational engagement for off-topic messages.

**How it works:**
- Responds warmly in 1–2 sentences using the LLM
- Tracks `consecutive_smalltalk_turns` in metadata; after 2+ turns, the prompt instructs the LLM to redirect more clearly to IT support
- Always ends with an invitation to ask about IT needs

**Why it matters:** A support bot that abruptly rejects "good morning" feels broken. Brief natural engagement improves perceived quality without compromising the support focus.

## Reasoning Trace

Every API response includes a `reasoning_trace` object:

```json
{
  "routing_intent": "knowledge",
  "routing_confidence": 0.95,
  "routing_reasoning": "User is asking for Wi-Fi connection instructions from the knowledge base.",
  "agent_step": null,
  "agent_confidence": null,
  "agent_reasoning": null,
  "answer_confidence": 0.87,
  "retrieval_scores": [0.91, 0.78, 0.64]
}
```

This makes the system observable: every routing decision and answer confidence can be inspected, logged, or surfaced in a developer panel.

## RAG and Knowledge Architecture

1. Confluence pages fetched through the MCP support server
2. Page content cleaned and split into overlapping paragraph-level chunks (800 char, 100 char overlap)
3. Chunks embedded with OpenAI `text-embedding-3-small`
4. Embeddings stored in a FAISS flat inner-product index with L2 normalization
5. At query time: embed question → FAISS search → top-k chunks returned with cosine similarity scores
6. Retrieved chunks passed to Knowledge Agent LLM prompt
7. LLM generates a structured answer with self-assessed confidence — no hallucination of facts not in context

## MCP Tool Architecture

The MCP layer decouples agent reasoning from operational tooling. Agents call named tools through a typed client; the MCP server owns the implementation.

**MCP Client** (`tools/mcp_client.py`)
- Launches the MCP support server as a subprocess over stdio
- Sends tool calls and returns structured payloads to agents

**MCP Support Server** (`mcp/support_server.py`)
- Exposes tools using `FastMCP`
- Wraps user lookup, password reset, ticket creation, appointment operations, and Confluence retrieval

## Architectural Principles

- **LLM primary, regex only for data formats** — slot IDs and fast-path username patterns use regex; all semantic decisions use the LLM
- **Structured output everywhere** — every LLM call returns `{action/intent, confidence, reasoning}` via OpenAI's JSON schema output mode
- **One LLM call per agent** — no double-call confirmation pattern; single structured call is both faster and more accurate
- **Fail safe** — LLM exceptions default to `escalation` (intake) or `ask_for_username` (workflow), never to deleted heuristics
- **Observable by design** — confidence scores and reasoning traces surface in every API response
- **No new dependencies** — all changes use the existing `openai` structured output API already in the stack

## Short Architecture Description for Slides or Reports

Constellations IT Support is a full-stack multi-agent AI application built on FastAPI, LangGraph, OpenAI, FAISS, SQLite, and MCP tools. A React frontend sends user requests to a FastAPI backend. The backend loads session memory and routes each turn through a LangGraph workflow. The Intake Agent uses chain-of-thought LLM prompting to classify requests into four intents — knowledge, workflow, escalation, or smalltalk — with a confidence score and reasoning trace on every turn. The Knowledge Agent uses retrieval-augmented generation over paragraph-chunked Confluence content stored in a FAISS index, with LLM self-assessed confidence gating escalation. The Workflow Agent performs safe password reset operations through MCP tools after LLM-driven step decisions and mandatory user confirmation. The Escalation Agent handles appointments and software/hardware requests using fully LLM-driven action classification, replacing all previous pattern-matching lists. A Smalltalk Agent handles casual conversation before steering users back to IT support. Every response includes a structured reasoning trace with routing confidence, agent step decisions, and retrieval scores.

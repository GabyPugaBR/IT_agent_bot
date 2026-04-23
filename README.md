# Constellations IT Support

Constellations IT Support is a full-stack multi-agent AI application for K-12 school IT support. It implements LLM-guided routing, retrieval-augmented generation, workflow automation, MCP-based tool integration, and human-support escalation in a single system.

## Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![LangGraph](https://img.shields.io/badge/LangGraph-000000?style=for-the-badge)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge)
![FAISS](https://img.shields.io/badge/FAISS-FF6F00?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![FastMCP](https://img.shields.io/badge/FastMCP-1abc9c?style=for-the-badge)
![RAG](https://img.shields.io/badge/RAG-green?style=for-the-badge)
![Multi-Agent](https://img.shields.io/badge/Multi--Agent-AI-orange?style=for-the-badge)

## Project Summary

A school IT support prototype covering password reset, Wi-Fi troubleshooting, Chromebook assistance, appointment scheduling, software and hardware request intake, and conversational handling. Built on a core architectural principle: **the LLM reasons first for semantic decisions**. Routing, step selection, confidence assessment, and request classification are primarily handled by the language model using structured prompts, with deterministic fast paths for usernames and slot IDs.

## Agent Architecture

| Agent | Role |
|---|---|
| **Intake Agent** | LLM-guided router — classifies every message into `knowledge`, `workflow`, `escalation`, or `smalltalk` with a confidence score and reasoning trace |
| **Knowledge Agent** | RAG-grounded Q&A over Confluence IT docs — retrieves school-specific context and offers password reset help when relevant |
| **Workflow Agent** | Password reset workflow — uses username fast-path extraction and mandatory confirmation before execution |
| **Escalation Agent** | Appointment scheduling, software/hardware requests, and declines — LLM-guided action selection with deterministic slot booking when needed |
| **Smalltalk Agent** | Short conversational handling before steering back to IT support |

## Core Capabilities

- Structured LLM routing with confidence scores and reasoning traces on every turn
- Retrieval-grounded answers over paragraph-chunked Confluence school IT documentation
- Two-flow password handling: questions go to RAG first, action requests go directly to workflow
- Multi-step password reset workflow with LLM-driven step decisions and mandatory confirmation
- Natural-language request submission — no rigid field format required
- Appointment scheduling via MCP tool integration
- Short conversational handling with IT support redirection
- Observable reasoning: `routing_confidence`, `agent_step`, `answer_confidence`, and `retrieval_scores` in every API response
- Persistent multi-turn session memory via SQLite

## Technology Stack

- **Frontend:** React (CRA, school-themed SPA)
- **Backend:** FastAPI
- **Orchestration:** LangGraph `StateGraph`
- **LLM:** OpenAI (`gpt-4.1-mini` for routing, workflow, escalation, and answer generation)
- **Retrieval:** OpenAI `text-embedding-3-small` + FAISS (paragraph-level chunking with overlap)
- **Tool Layer:** MCP server (`FastMCP`) + typed MCP client
- **Memory:** SQLite (session + 6-turn conversation history)
- **Deployment:** Docker Compose (local) / Render + Vercel (live)

## Execution Requirements

- Python 3.11 or later
- Node.js 20 or later
- Docker Desktop
- A valid OpenAI API key

## Environment Configuration

### Backend
Copy `backend/.env.example` to `backend/.env` and provide:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_CHAT_MODEL=gpt-4.1-mini
OPENAI_ROUTER_MODEL=gpt-4.1-mini

# Optional: Confluence integration for live knowledge base
CONFLUENCE_BASE_URL=https://your-domain.atlassian.net/wiki
ATLASSIAN_EMAIL=you@example.com
ATLASSIAN_API_TOKEN=your_token
CONFLUENCE_PAGE_ID=12345,67890
```

### Frontend
The frontend reads `REACT_APP_API_URL` at build time. Set it in Vercel (or a local `.env`) to point at your backend:

```env
REACT_APP_API_URL=https://your-backend.onrender.com
```

## Running the Project

### Docker (recommended)
From the repository root:

```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Backend API docs: `http://localhost:8000/docs`

### Local Without Docker

Backend:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm start
```

## Repository Structure

```text
backend/
  agents/
    intake_agent.py       # LLM-guided router with confidence/reasoning metadata
    knowledge_agent.py    # RAG Q&A with confidence gating and password follow-up
    workflow_agent.py     # Password reset workflow with username fast-path and confirmation
    escalation_agent.py   # Appointments and requests, with deterministic slot booking
    smalltalk_agent.py    # Natural conversation with gentle IT redirect
    prompts.py            # Agent prompts and structured decision guidance
  graph/
    agent_graph.py        # LangGraph StateGraph: 1 intake router + 4 specialist nodes
    state.py              # AgentState TypedDict
  rag/
    ingest.py             # Confluence ingestion with paragraph-level chunking
    vector_store.py       # FAISS retrieval + structured grounded answer generation
    embeddings.py         # OpenAI embedding wrappers
  memory/
    store.py              # SQLite session and conversation history
  mcp/
    support_server.py     # FastMCP server exposing 6 IT support tools
  tools/
    mcp_client.py         # Typed MCP client wrappers
    user_db.py            # Synthetic school user directory
    password_reset.py     # Password reset logic with role-based policies
    calendar.py           # Appointment slot management
  schemas/
    chat.py               # ChatRequest, ChatResponse, ReasoningTrace
  main.py                 # FastAPI app, /chat endpoint, reasoning trace assembly
frontend/
  src/
    App.js                # Full SPA with chat modal, response cards, forms
docs/
  architecture_description.md
  capstone-rubric-mapping.md
  demo-script.md
  industry-awareness.md
docker-compose.yml
```

## API Response Shape

Every `/chat` response includes a `reasoning_trace`:

```json
{
  "response": "...",
  "intent": "knowledge",
  "agent_used": "knowledge",
  "session_id": "...",
  "sources": ["Wi-Fi Setup Guide"],
  "metadata": { "answer_confidence": 0.91, "retrieval_scores": [0.91, 0.78] },
  "reasoning_trace": {
    "routing_intent": "knowledge",
    "routing_confidence": 0.95,
    "routing_reasoning": "User asking for Wi-Fi connection instructions.",
    "answer_confidence": 0.91,
    "retrieval_scores": [0.91, 0.78, 0.64]
  }
}
```

## Documentation

- [Architecture](docs/architecture_description.md)
- [Rubric Alignment](docs/capstone-rubric-mapping.md)
- [Demo Script](docs/demo-script.md)
- [Industry Awareness](docs/industry-awareness.md)

## Industry Context

This project reflects patterns found in enterprise AI support platforms — Glean (grounded retrieval), Moveworks (knowledge plus workflow plus MCP tooling), and ServiceNow Now Assist (workflow automation plus human escalation) — applied at K-12 school scale. The same architectural choices that appear in those systems (structured LLM decisioning, RAG confidence gating, tool standardization via MCP, multi-agent separation of concerns) are present here as first-class design decisions.

## Deployment

- **Backend:** Render (Docker deploy from GitHub) — auto-deploys on push to `main`
- **Frontend:** Vercel (static build from `frontend/`) — auto-deploys on push to `main`
- Set `REACT_APP_API_URL` in Vercel environment variables to point at the Render backend URL

## Future Extension

- Migration of mutable state (tickets, appointments, users) from JSON files to PostgreSQL
- Metrics dashboard for routing accuracy, reset success rate, and response latency
- Expanded MCP tool suite (JIRA integration, device inventory, Slack notifications)
- Admin view with per-session reasoning trace inspection

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

- **Docker Desktop** for the easiest local setup
- **A valid OpenAI API key** for all LLM and embedding calls
- **Atlassian/Confluence credentials** for full Knowledge Agent / RAG functionality
- **Python 3.11 or later** only if running without Docker
- **Node.js 20 or later** only if running without Docker

The password reset, appointment scheduling, and ticket workflows use local JSON data files. The Knowledge Agent retrieves school IT documentation from Confluence and builds a FAISS index, so knowledge-base questions require valid Confluence environment variables.

## Environment Configuration

The app reads secrets from local `.env` files. These files are intentionally ignored by Git. If someone forks this repository, they must create their own local env files.

### Backend Environment

Create the backend env file:

```bash
cp backend/.env.example backend/.env
```

Then open `backend/.env` and replace the placeholder values:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_CHAT_MODEL=gpt-4.1-mini
OPENAI_ROUTER_MODEL=gpt-4.1-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

CONFLUENCE_BASE_URL=https://your-domain.atlassian.net/wiki
ATLASSIAN_EMAIL=you@example.com
ATLASSIAN_API_TOKEN=your_token
CONFLUENCE_PAGE_ID=12345,67890
```

Backend variables:

| Variable | Required? | What it does |
|---|---:|---|
| `OPENAI_API_KEY` | Yes | Authenticates OpenAI chat and embedding calls |
| `OPENAI_CHAT_MODEL` | Recommended | Model used for grounded answers and smalltalk. Defaults to `gpt-4.1-mini` if omitted |
| `OPENAI_ROUTER_MODEL` | Recommended | Model used for intake, workflow, and escalation decisions. Falls back to `OPENAI_CHAT_MODEL` if omitted |
| `OPENAI_EMBEDDING_MODEL` | Recommended | Model used for FAISS/RAG embeddings. Defaults to `text-embedding-3-small` if omitted |
| `CONFLUENCE_BASE_URL` | Yes for Knowledge Agent | Atlassian site URL, usually `https://your-domain.atlassian.net/wiki` |
| `ATLASSIAN_EMAIL` | Yes for Knowledge Agent | Email address for the Atlassian account |
| `ATLASSIAN_API_TOKEN` | Yes for Knowledge Agent | Atlassian API token for reading Confluence pages |
| `CONFLUENCE_PAGE_ID` | Yes for Knowledge Agent | One page ID or multiple comma-separated page IDs to ingest |

### Frontend Environment

Create the frontend env file:

```bash
cp frontend/.env.example frontend/.env
```

For local Docker or local development, this default is correct:

```env
REACT_APP_API_URL=http://127.0.0.1:8000
```

If deploying the frontend somewhere else, change `REACT_APP_API_URL` to the public backend URL, for example:

```env
REACT_APP_API_URL=https://your-backend.onrender.com
```

## Run Locally with Docker

Docker is the recommended option because it avoids manually installing Python packages and Node packages on your machine.

### 1. Install Docker Desktop

Download and install Docker Desktop for your operating system, then open Docker Desktop and wait until it says Docker is running.

### 2. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
cd YOUR-REPOSITORY
```

If you already have the project folder open, just open a terminal in the repository root. The repository root is the folder that contains `docker-compose.yml`.

### 3. Create the environment files

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit `backend/.env` and add your own OpenAI and Confluence values.

For local Docker, `frontend/.env` can stay as:

```env
REACT_APP_API_URL=http://127.0.0.1:8000
```

### 4. Build and start both apps

```bash
docker compose up --build
```

Leave this terminal open while using the app. The first build may take a few minutes.

### 5. Open the app

- Frontend website: `http://localhost:3000`
- Backend health check: `http://localhost:8000`
- Backend API docs: `http://localhost:8000/docs`

### 6. Stop Docker

In the terminal running Docker, press:

```text
Control + C
```

Then cleanly stop the containers:

```bash
docker compose down
```

### Useful Docker Commands

Run in the background:

```bash
docker compose up --build -d
```

View logs:

```bash
docker compose logs -f
```

View only backend logs:

```bash
docker compose logs -f backend
```

View only frontend logs:

```bash
docker compose logs -f frontend
```

Stop containers:

```bash
docker compose down
```

Rebuild from scratch after dependency changes:

```bash
docker compose down
docker compose build --no-cache
docker compose up
```

Check which containers are running:

```bash
docker compose ps
```

## Run Locally Without Docker

Use this path only if you are comfortable installing Python and Node dependencies directly on your machine.

### 1. Create backend env file

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` with your own OpenAI and Confluence values.

### 2. Start the backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend runs at `http://127.0.0.1:8000`.

### 3. Start the frontend

Open a second terminal from the repository root:

```bash
cd frontend
cp .env.example .env
npm install
npm start
```

The frontend runs at `http://localhost:3000`.

## Local Demo Data

This project intentionally uses local mock data so the capstone can be run without a production IT system:

- `backend/data/synthetic_users.json` contains synthetic students, teachers, staff, and admins
- `backend/data/support_tickets.json` stores generated mock support tickets
- `backend/data/appointments.json` stores rolling appointment slots
- `backend/memory/memory.db` stores local conversation memory and is created automatically

Appointment slots are refreshed to future business days and business hours when availability becomes stale or too low.

## Common Setup Issues

### Docker says an `.env` file is missing

Create both local env files from the examples:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Then edit the backend placeholders before running Docker again.

### The frontend opens, but chat says the support service is unavailable

Make sure the backend is running at `http://localhost:8000`.

If using Docker, check:

```bash
docker compose ps
docker compose logs -f backend
```

Also confirm `frontend/.env` contains:

```env
REACT_APP_API_URL=http://127.0.0.1:8000
```

### Password reset works, but knowledge questions fail

That usually means the OpenAI key or Confluence variables are missing or incorrect. The Knowledge Agent needs:

```env
OPENAI_API_KEY=...
CONFLUENCE_BASE_URL=...
ATLASSIAN_EMAIL=...
ATLASSIAN_API_TOKEN=...
CONFLUENCE_PAGE_ID=...
```

### Port `3000` or `8000` is already in use

Stop the app currently using that port, or stop existing Docker containers:

```bash
docker compose down
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
    support_server.py     # FastMCP server exposing 7 IT support tools
  tools/
    mcp_client.py         # Typed MCP client wrappers
    user_db.py            # Synthetic school user directory
    password_reset.py     # Password reset logic with role-based policies
    calendar.py           # Rolling future business-hours appointment slots
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

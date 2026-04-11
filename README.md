# Constellations IT Support

Multi-agent AI capstone project for K-12 IT support. This project simulates a school support system that can answer knowledge questions, perform password reset workflows, offer human-support appointments, and collect software or hardware requests.

## 🚀 Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![LangGraph](https://img.shields.io/badge/LangGraph-000000?style=for-the-badge)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge)
![FAISS](https://img.shields.io/badge/FAISS-FF6F00?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)


## What This Project Demonstrates
- Multi-agent orchestration with LangGraph
- Retrieval-augmented generation with OpenAI embeddings and FAISS
- Workflow automation through MCP
- Persistent session memory
- A polished school website UI with an embedded support chatbot
- Dockerized frontend and backend services

## Current Agent Roles
- Intake Agent: routes the user request
- Knowledge Agent: answers using the school knowledge base
- Workflow Agent: performs automations like password reset
- Escalation Agent: handles appointments, unsupported issues, and request submission

## Prerequisites
- Python 3.11+
- Node.js 20+
- Docker Desktop
- An OpenAI API key

## Required Environment Variables
### Backend
Copy `backend/.env.example` to `backend/.env` and provide:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_CHAT_MODEL=gpt-4.1-mini
```

### Frontend
Copy `frontend/.env.example` to `frontend/.env` if you need a custom backend URL:

```env
REACT_APP_API_URL=http://127.0.0.1:8000
```

## Quick Start
### Option 1: Docker
From the project root:

```bash
docker compose up --build
```

Open:
- Frontend: `http://localhost:3000`
- Backend docs: `http://localhost:8000/docs`

### Option 2: Run locally without Docker
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

## Replication Checklist
For another student or grader to run this project successfully, they need:
- the repository code
- a valid `backend/.env` with their own OpenAI API key
- Docker Desktop or local Python/Node installed

They do **not** need:
- your personal `.venv`
- your local `__pycache__`
- your private API key

## Repository Structure
```text
backend/
  agents/
  data/
  graph/
  mcp/
  memory/
  rag/
  schemas/
  tools/
  main.py
frontend/
  src/
docker-compose.yml
docs/
  architecture.md
  capstone-rubric-mapping.md
  demo-script.md
```

## Architecture
See [docs/architecture.md](docs/architecture.md).

## Rubric Alignment
See [docs/capstone-rubric-mapping.md](docs/capstone-rubric-mapping.md).

## Demo Guidance
See [docs/demo-script.md](docs/demo-script.md).

## Technical Notes
- The project currently uses OpenAI for both embeddings and grounded response generation.
- Password reset, ticketing, and appointment scheduling are simulated through MCP-backed tools.
- Persistent local files are acceptable for the capstone demo, but a more production-ready version would move mutable state into a database.

## Suggested Next Improvements
- Move mutable state from JSON/SQLite files into PostgreSQL
- Add health endpoints and stronger observability
- Improve deployment by separating frontend and backend environment configuration
- Add more formal scenario-based tests and rubric metrics

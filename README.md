# Constellations IT Support

Constellations IT Support is a multi-agent AI support application designed for a K-12 school environment. The project demonstrates how retrieval-augmented generation, workflow automation, MCP-based tool access, and human-support escalation can be combined in a single support experience.

## Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![LangGraph](https://img.shields.io/badge/LangGraph-000000?style=for-the-badge)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge)
![FAISS](https://img.shields.io/badge/FAISS-FF6F00?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![MCP](https://img.shields.io/badge/MCP-blue?style=for-the-badge)
![RAG](https://img.shields.io/badge/RAG-green?style=for-the-badge)
![Multi-Agent](https://img.shields.io/badge/Multi--Agent-AI-orange?style=for-the-badge)

## Project Summary
The system was developed as a capstone prototype for school IT support. It addresses common support scenarios such as password reset, Wi-Fi troubleshooting, Chromebook assistance, appointment scheduling, and software or hardware request intake. The implementation combines a school-themed React interface with a Python backend built on FastAPI and LangGraph.

## Core Capabilities
- retrieval-grounded answers using a school IT knowledge base
- explicit workflow execution for password reset
- appointment scheduling for human-support handoff
- software and hardware request submission
- persistent multi-turn session memory
- Docker-based reproducibility

## Technology Stack
- Frontend: React
- Backend: FastAPI
- Orchestration: LangGraph
- Retrieval: OpenAI embeddings + FAISS
- Tool Layer: MCP server and MCP client
- Memory: SQLite
- Deployment: Docker Compose

## Execution Requirements
The project requires:
- Python 3.11 or later
- Node.js 20 or later
- Docker Desktop
- a valid OpenAI API key

## Environment Configuration
### Backend
Copy `backend/.env.example` to `backend/.env` and provide the required values:

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_CHAT_MODEL=gpt-4.1-mini
```

### Frontend
Copy `frontend/.env.example` to `frontend/.env` if a custom backend API URL is needed:

```env
REACT_APP_API_URL=http://127.0.0.1:8000
```

## Running the Project
### Docker
From the repository root:

```bash
docker compose up --build
```

Available endpoints:
- Frontend: `http://localhost:3000`
- Backend API documentation: `http://localhost:8000/docs`

### Local Execution Without Docker
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

## Replication Notes
For a reviewer or instructor to run the project successfully, the repository code and a valid backend environment file are sufficient. Personal local artifacts such as `.venv`, `__pycache__`, and private keys are not required and should not be shared.

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
docs/
  architecture.md
  capstone-rubric-mapping.md
  demo-script.md
  industry-awareness.md
docker-compose.yml
```

## Documentation
- Architecture: [docs/architecture.md](docs/architecture.md)
- Rubric Alignment: [docs/capstone-rubric-mapping.md](docs/capstone-rubric-mapping.md)
- Demonstration Narrative: [docs/demo-script.md](docs/demo-script.md)
- Industry Awareness: [docs/industry-awareness.md](docs/industry-awareness.md)

## Technical Positioning
The current implementation uses OpenAI both for embeddings and for grounded response generation. Operational actions such as password reset, appointment scheduling, and request submission are simulated through MCP-backed tools. Persistent local files are appropriate for capstone demonstration purposes, although a more production-oriented version would move mutable state into a managed database.

## Future Extension
Potential next steps include:
- migration of mutable state from local files to PostgreSQL
- health endpoints and stronger observability
- formal scenario metrics and reporting
- cloud deployment with separate frontend and backend configuration


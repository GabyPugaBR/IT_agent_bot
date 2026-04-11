# System Architecture

## Overview
Constellations IT Support is a multi-agent AI system for a K-12 school environment. The application combines a React web experience, a FastAPI backend, LangGraph agent routing, retrieval-augmented generation (RAG), simulated workflow automation, MCP-based tools, and persistent session memory.

## Architecture Diagram
```text
User Browser
  |
  v
React Frontend (Constellations.com mock website + IT chat)
  |
  v
FastAPI /chat API
  |
  v
LangGraph Orchestrator
  |
  +--> Intake Agent
          |
          +--> Knowledge Agent -> FAISS index + knowledge base + OpenAI grounded answer generation
          |
          +--> Workflow Agent -> MCP client -> MCP support server -> synthetic user/password tools
          |
          +--> Escalation Agent -> MCP client -> appointment tools / request submission tools
  |
  v
SQLite Session Memory
```

## Agent Responsibilities
### Intake Agent
- Reads the current request and limited conversation context
- Decides whether the user needs knowledge, workflow execution, or escalation
- Routes password help to knowledge first, and only routes to workflow after explicit reset intent

### Knowledge Agent
- Retrieves relevant support content from the school knowledge base
- Uses OpenAI embeddings and a FAISS index for retrieval
- Uses an OpenAI response model to produce a grounded answer from retrieved context
- Offers the next workflow step for password reset when appropriate

### Workflow Agent
- Handles explicit automations such as password reset
- Uses MCP tools instead of direct in-process function calls
- Looks up synthetic users, resets passwords, and returns structured results

### Escalation Agent
- Handles unsupported requests, appointment scheduling, and request submissions
- Offers human-support appointments when the bot cannot help directly
- Supports software and hardware request submission with a structured form flow

## Data and Persistence
### Durable-ish demo data
- `backend/data/synthetic_users.json`
- `backend/data/appointments.json`
- `backend/data/support_tickets.json`
- `backend/rag/knowledge.index`
- `backend/rag/knowledge_metadata.json`

### Session memory
- `backend/memory/memory.db`
- Stores recent turns and session facts such as username and last routed agent

## Why this architecture fits the capstone
- Demonstrates a real multi-agent pattern instead of a single prompt chain
- Separates reasoning, retrieval, actions, and human fallback
- Uses MCP to standardize tool access
- Includes memory, UX design, testing, and Docker deployment


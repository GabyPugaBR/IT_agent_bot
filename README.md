# Multi-Agent AI IT Support System

## Overview
This project is a full-stack, multi-agent AI system designed to provide IT support for a K–12 school environment.

It simulates real-world enterprise solutions by combining:
- Retrieval-Augmented Generation (RAG)
- Workflow automation
- Multi-agent orchestration
- Tool integration via MCP concepts

---

## Problem
Constellations School operates with a small IT team supporting a large user base of students, staff, and parents.

Challenges:
- High volume of repetitive requests
- Slow response times
- Manual ticket triaging

---

## Solution
A multi-agent AI system that can:
- Answer IT questions using a knowledge base (RAG)
- Reset passwords via automated workflows (simulated)
- Route complex issues to human support

---

## System Architecture

Agents:
- Intake Agent → classifies requests
- Knowledge Agent → retrieves answers
- Workflow Agent → executes actions
- Escalation Agent → handles edge cases

---

## Tech Stack

Backend:
- Python
- LangGraph (multi-agent orchestration)
- FAISS / Vector DB (RAG)

Frontend:
- React (chat-based UI)

Other:
- Docker (containerization)
- MCP (conceptual tool integration layer)

---

## Features

- Chat-based IT support assistant
- Password reset simulation
- Knowledge retrieval with embeddings
- Multi-agent decision flow
- Escalation handling

---

## Example Use Cases

1. “How do I reset my password?” → AI answers (RAG)
2. “Reset my password” → Workflow agent executes action
3. Complex issue → Escalation agent routes to human

---

## Project Structure
project/
├── backend/
│ ├── agents/
│ ├── rag/
│ ├── workflows/
│ └── main.py
├── frontend/
│ └── react-app/
├── docker-compose.yml
└── README.md


---

## Future Improvements

- Real Google Workspace API integration
- Authentication layer
- Advanced ticketing system
- Improved RAG accuracy

---

## Demo

(Insert screenshots or video here)

---

## Author

Team Static: 
1. Gaby Rollins - MIS Student | Data Analytics | Agentic AI Systems
2. 
3. 
4. 
5. 
6. 



                ┌──────────────────────┐
                │        USER          │
                │   (React Chat UI)    │
                └─────────┬────────────┘
                          │
                          ▼
                ┌──────────────────────┐
                │    Intake Agent      │
                │ (Classify Request)   │
                └─────────┬────────────┘
                          │
      ┌───────────────────┼───────────────────┐
      ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Knowledge    │   │ Workflow     │   │ Escalation   │
│ Agent (RAG)  │   │ Agent        │   │ Agent        │
│              │   │              │   │              │
│ Answers Qs   │   │ Resets PW    │   │ Creates Ticket│
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Vector DB    │   │ MCP Server   │   │ Human / IT   │
│ (RAG Data)   │   │ (Tools Layer)│   │ Support      │
└──────────────┘   └──────────────┘   └──────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │ Simulated DB    │
                 │ Users/Passwords │
                 └─────────────────┘
**The Intake Agent routes requests to specialized agents, while MCP standardizes access to tools like password reset systems, and RAG ensures accurate knowledge retrieval.**


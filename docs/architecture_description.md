# Constellations IT Support Agent Architecture

## System Summary

Constellations IT Support is a multi-agent AI support system for school IT operations. The system accepts chat requests from a web frontend, sends them to a FastAPI backend, and routes each request through a LangGraph-based orchestration layer. The orchestration layer decides whether the user needs:

- knowledge support from the school IT knowledge base
- an operational workflow such as a password reset
- human-support escalation such as appointment scheduling or a software and hardware request

The architecture combines LLM-based routing, retrieval-augmented generation, simulated operational tools, and short-term conversation memory to deliver guided IT support for students, teachers, staff, and administrators.

## High-Level Flow

1. A user sends a message from the React frontend.
2. The frontend calls the FastAPI backend `POST /chat` endpoint.
3. FastAPI loads recent session memory and builds an initial agent state.
4. LangGraph sends the request first to the Intake Agent.
5. The Intake Agent classifies the request as `knowledge`, `workflow`, or `escalation`.
6. LangGraph routes the request to the selected specialist agent.
7. The selected agent returns a user-facing response plus metadata such as sources, follow-up actions, appointment slots, or workflow results.
8. FastAPI stores the conversation turn in SQLite memory and returns the final response to the frontend.

## Core Components

### 1. Frontend Layer

- React single-page application
- Chat-based interface for IT support conversations
- Sends requests to the backend API
- Displays bot responses, source information, and structured next actions

### 2. API Layer

- FastAPI backend
- Primary endpoint: `POST /chat`
- Health endpoint: `GET /`
- Handles session-aware chat requests and response formatting
- Loads recent memory and passes the state into the agent graph

### 3. Orchestration Layer

- Built with LangGraph
- Entry point is always the Intake Agent
- Conditional routing sends traffic to one of three specialist agents:
  - Knowledge Agent
  - Workflow Agent
  - Escalation Agent
- Terminates after the selected specialist agent responds

### 4. Memory Layer

- SQLite-based conversation memory
- Stores session-level context:
  - session id
  - username
  - user role
  - last intent
  - last agent used
- Stores recent message history with metadata
- Helps agents interpret follow-up messages such as confirmations and continuation steps

### 5. Knowledge Layer

- Retrieval-augmented generation pipeline
- Fetches live Confluence pages through an MCP server
- Builds embeddings with OpenAI `text-embedding-3-small`
- Stores vectors in a FAISS index
- Stores chunk metadata in `knowledge_metadata.json`
- Retrieves top matching documents and generates grounded answers with OpenAI chat models

### 6. Tool Layer

- MCP client launches a local MCP support server over stdio
- MCP tools provide operational capabilities:
  - user lookup
  - password reset
  - ticket creation
  - appointment listing
  - appointment booking
  - Confluence page retrieval

### 7. Data Layer

- synthetic user directory in JSON
- support ticket records in JSON
- appointment calendar slots in JSON
- SQLite memory database for session and conversation history
- FAISS vector index and metadata files for RAG

## Agent Descriptions

## Intake Agent

### Role

The Intake Agent is the router and coordinator. It decides which specialist agent should handle the current user request.

### Responsibilities

- analyze the current message
- inspect recent conversation history
- use heuristic rules for common IT intents
- optionally use an OpenAI routing model for final intent classification
- assign one of three intents:
  - `knowledge`
  - `workflow`
  - `escalation`

### What It Handles

- informational questions such as Wi-Fi, MFA, phishing, internet, Chromebook, or troubleshooting topics
- explicit action requests such as resetting a password
- escalation cases such as appointments, software requests, or unsupported issues

### Why It Matters

The Intake Agent prevents every request from being handled the same way. It acts as the intelligent traffic controller that sends users to the right support path.

## Knowledge Agent

### Role

The Knowledge Agent answers school IT support questions using retrieved knowledge-base content.

### Responsibilities

- query the FAISS vector store
- retrieve top matching Confluence chunks
- generate an answer grounded only in retrieved context
- attach document sources and retrieved document metadata
- detect low-confidence retrieval and hand off to human-support options

### Behavior

- If relevant documents are found with sufficient confidence, it returns a grounded answer.
- If confidence is low or no useful documents are found, it offers escalation options such as IT appointments or request submission.
- For password-help questions, it explains the policy or process first and can suggest the reset workflow as a next step.

### Why It Matters

The Knowledge Agent gives the system a trustworthy self-service layer and reduces unnecessary escalation by answering known support questions directly from school documentation.

## Workflow Agent

### Role

The Workflow Agent executes safe, structured IT operations, currently focused on password reset workflows.

### Responsibilities

- detect or extract usernames from user input
- inspect prior messages to find pending reset targets
- decide the next workflow step:
  - ask for username
  - confirm target user
  - execute reset
  - escalate if unsafe
- look up users through MCP tools
- perform password resets through the MCP tool layer
- create a support ticket if a user is not found or the reset service fails

### Behavior

- If the request is incomplete, it asks for a full username.
- If a username is present, it confirms the user before taking action.
- If the user confirms, it executes the password reset.
- If the target user does not exist or a tool fails, it escalates to human IT support by creating a support ticket.

### Why It Matters

The Workflow Agent turns the chatbot from an information system into an operational IT assistant while preserving safety through confirmation and structured decision logic.

## Escalation Agent

### Role

The Escalation Agent handles cases that require human support or adjacent support workflows that are not solved by the knowledge base alone.

### Responsibilities

- decide whether to:
  - offer appointments
  - show appointment slots
  - book an appointment
  - show a software or hardware request form
  - acknowledge a declined escalation
- call MCP tools to list or book appointments
- create support tickets for submitted requests
- present human-support options in a calm, actionable way

### Behavior

- If the user needs live support, it offers appointment scheduling.
- If the user asks for software or hardware, it displays a request workflow.
- If the user submits a request, it creates a support ticket.
- If the user chooses an appointment slot, it books the slot.

### Why It Matters

The Escalation Agent ensures that unresolved or unsupported issues still end in a useful next step rather than a dead end.

## RAG and Knowledge Architecture

The knowledge subsystem is built as a retrieval-augmented generation pipeline:

1. Confluence pages are fetched through the MCP support server.
2. Page content is cleaned and transformed into text chunks.
3. Chunks are embedded using OpenAI embeddings.
4. Embeddings are stored in FAISS for semantic search.
5. At query time, the user question is embedded and matched against the vector index.
6. Retrieved chunks are passed to the Knowledge Agent prompt.
7. The final answer is generated using only retrieved evidence.

This design keeps answers grounded in institutional documentation rather than free-form model guesses.

## MCP Tool Architecture

The MCP layer acts as the bridge between agents and support tools.

### MCP Client

- starts the MCP support server through stdio
- sends tool calls
- returns structured tool outputs to the agents

### MCP Support Server

- exposes support tools using FastMCP
- wraps operational and data access functions
- provides both simulated support operations and live Confluence retrieval

### MCP Tools in This System

- `lookup_user`
- `reset_user_password`
- `create_support_ticket`
- `list_it_appointments`
- `book_it_appointment`
- `fetch_confluence_pages`

## Architectural Strengths

- modular multi-agent design
- clean separation of routing, knowledge, workflow, and escalation logic
- grounded answers through RAG
- safe operational execution through confirmation-based workflows
- session memory for conversational continuity
- extensible MCP tool layer for adding more IT operations later
- clear fallback path from self-service to human support

## Short Architecture Description for Slides or Reports

Constellations IT Support is a multi-agent AI architecture built on FastAPI, LangGraph, OpenAI models, FAISS, SQLite, and MCP tools. A React frontend sends user requests to a FastAPI backend. The backend loads session memory and routes each request through a LangGraph workflow. The Intake Agent classifies requests into knowledge, workflow, or escalation paths. The Knowledge Agent uses retrieval-augmented generation over live Confluence content stored in a FAISS vector index. The Workflow Agent performs safe password reset operations through MCP tools after confirming the target user. The Escalation Agent handles unsupported issues, appointment scheduling, and software or hardware request submission. SQLite stores short-term conversation memory, while MCP connects the agents to operational tools and live knowledge sources.

## Image Generator Prompt

Create a clean, modern AI system architecture diagram for a school IT support platform called "Constellations IT Support." Show a left-to-right flow with labeled layers and arrows. On the far left, show users in a web chat frontend built with React. The frontend sends requests to a FastAPI backend API. Inside the backend, show a LangGraph orchestration engine with four agent blocks: Intake Agent at the top as the router, then three routed specialist agents: Knowledge Agent, Workflow Agent, and Escalation Agent. The Intake Agent should route requests to the other three agents. Below the orchestration layer, show a SQLite memory store holding session memory and recent conversation history. To the right of the Knowledge Agent, show a RAG pipeline with Confluence pages flowing into chunking, OpenAI embeddings, and a FAISS vector store, then retrieved context returning to the Knowledge Agent. To the right of the Workflow and Escalation Agents, show an MCP client connected to an MCP support server. From the MCP support server, branch to tools for user lookup, password reset, support ticket creation, appointment scheduling, and live Confluence retrieval. Use a professional enterprise diagram style, white background, blue and teal accents, soft gray infrastructure boxes, clear labels, minimal icons, and directional arrows. Emphasize that the system supports three outcomes: knowledge answer, automated workflow execution, and human-support escalation.

## Compact Image Prompt

Multi-agent school IT support architecture diagram, React frontend, FastAPI backend, LangGraph orchestration, Intake Agent router, Knowledge Agent with RAG over Confluence, Workflow Agent for password reset, Escalation Agent for appointments and request tickets, SQLite conversation memory, MCP client and MCP support server, FAISS vector store, OpenAI embeddings, user lookup and password reset tools, modern enterprise system design, white background, blue teal palette, clean arrows, professional technical infographic.

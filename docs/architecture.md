# System Architecture

## Overview
Constellations IT Support is a multi-agent AI support application designed for a K-12 school environment. The system combines a React-based user interface, a FastAPI backend, LangGraph orchestration, retrieval-augmented generation, simulated workflow automation, MCP-based tool access, and persistent session memory. The architecture was designed to separate informational support, operational workflows, and human-support escalation into distinct but coordinated components.

## High-Level Flow
```text
User Browser
  |
  v
React Frontend (Constellations.com + IT Support Chat)
  |
  v
FastAPI /chat endpoint
  |
  v
LangGraph Orchestrator
  |
  +--> Intake Agent
          |
          +--> Knowledge Agent  -> FAISS vector index + school IT knowledge base
          |
          +--> Workflow Agent   -> MCP client -> support MCP server -> automation tools
          |
          +--> Escalation Agent -> MCP client -> appointments / request submission
  |
  v
SQLite Session Memory
```

## Agent Responsibilities

### Intake Agent
The intake agent is responsible for interpreting the current user message and recent conversation context, then routing the request to the most appropriate specialist agent. Password-help questions are routed to the knowledge path first, while explicit reset commands are routed to the workflow path. Unsupported or human-dependent requests are routed to escalation.

### Knowledge Agent
The knowledge agent handles informational support. It retrieves relevant content from the school IT knowledge base, uses the retrieved context to produce a grounded answer, and proposes workflow follow-up actions when appropriate. This agent is intended to answer questions before any automation is triggered.

### Workflow Agent
The workflow agent performs explicit operational tasks. In the current implementation, this includes password-reset automation against a synthetic user directory. The workflow agent operates through MCP tools rather than directly calling internal helper logic, which preserves a cleaner separation between reasoning and action.

### Escalation Agent
The escalation agent handles requests that the system should not answer or execute automatically. It provides appointment scheduling, software and hardware request intake, and human-support handoff behavior. This agent is also responsible for fallback when knowledge retrieval is insufficient or when a request falls outside supported automation boundaries.

## Retrieval-Augmented Generation Design
The retrieval layer is built around OpenAI embeddings and a local FAISS vector index. The knowledge base is chunked into school-specific IT support documents covering password guidance, Wi-Fi troubleshooting, Chromebook support, MFA, phishing, software policy, support hours, and triage rules. When a user asks a support question, the system retrieves the most relevant chunks and uses them as the grounding context for answer generation.

This design supports the rubric requirement to demonstrate how embeddings and vector stores ground an agent in enterprise or operational knowledge. Although this implementation uses FAISS instead of Pinecone or Weaviate, it follows the same conceptual pattern: document embedding, vector similarity search, contextual retrieval, and grounded answer generation.

## Workflow Automation Design
Workflow automation is intentionally separated from retrieval. The workflow agent handles repeatable support operations such as:
- password reset
- user lookup
- appointment listing and booking
- software and hardware request submission

This separation avoids mixing explanation and action inside a single prompt path and makes the automation layer easier to reason about, debug, and extend.

## MCP Integration Design
The project includes a local MCP server that exposes support-related tools through a consistent interface. The workflow and escalation agents access actions such as password reset, support request submission, and appointment operations through the MCP client layer. This design demonstrates the benefit of standardized tool access compared with tightly coupling each agent to ad hoc internal API calls.

## Memory and Persistence
The system maintains session continuity through a SQLite-backed memory layer. Session memory stores recent turns and lightweight contextual facts, including username and previously used agent path. In addition, the application persists demo-oriented operational data such as synthetic users, appointments, request records, and vector metadata in local files.

## Architectural Rationale
The architecture satisfies the capstone goals for the following reasons:
- it demonstrates a true multi-agent system rather than a single conversational model
- it separates retrieval, automation, and escalation concerns
- it includes a standardized tool interface through MCP
- it incorporates a persistent memory layer
- it supports both local execution and Docker-based deployment

## Enterprise Prototype Positioning
This project is best understood as a lightweight prototype of enterprise AI support systems. It does not attempt to reproduce the scale or governance model of commercial platforms, but it does demonstrate the same architectural ideas on a smaller, domain-specific scope: grounded retrieval, workflow execution, standardized tool access, session continuity, and human-support fallback.


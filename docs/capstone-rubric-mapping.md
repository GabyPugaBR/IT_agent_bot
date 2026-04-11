# Capstone Rubric Alignment

## Project Definition and Use Case
The project addresses a realistic K-12 IT support problem: a small school technology team must respond to high volumes of repetitive requests while still supporting classroom continuity and higher-priority incidents. The selected use cases include password reset, Wi-Fi troubleshooting, Chromebook support, software and hardware requests, and escalation to human support. The intended outcome is a support system that improves response consistency, automates routine tasks, and preserves a clear path to human intervention when required.

The primary success criteria for the project are:
- accurate routing of common support requests
- grounded answers for known IT support questions
- successful completion of simulated password reset workflows
- appropriate escalation when the system lacks confidence or authority
- continuity of user context across a multi-turn session

## Agent Identification
The system implements the four agent roles specified in the assignment:

### Intake Agent
The intake agent classifies user requests and determines whether the request belongs to retrieval, workflow execution, or escalation.

### Knowledge Agent
The knowledge agent handles retrieval-augmented question answering using embeddings, vector search, and grounded answer generation.

### Workflow Agent
The workflow agent executes supported automations, including password reset and related support actions, through MCP-based tools.

### Escalation Agent
The escalation agent handles unsupported requests, human-support appointments, and software or hardware request submission.

## UX Design
The application includes a school-themed mock web experience rather than a standalone technical console. The chatbot is embedded into a fictional `Constellations.com` homepage with multiple visible support entry points. The interface supports conversational interaction, guided starter actions, structured response cards, appointment scheduling options, and request-submission forms. This satisfies the assignment emphasis on usability, clarity, and visible design intent.

## System Development
The system is implemented as a full-stack application with the following major components:
- React frontend
- FastAPI backend
- LangGraph orchestration layer
- OpenAI embeddings and response generation
- FAISS vector storage for retrieval
- MCP server and client for tool integration
- SQLite session memory
- Dockerized frontend and backend services

## Testing and Validation
The current validation approach includes scenario testing for:
- password-help questions
- explicit password-reset execution
- Wi-Fi troubleshooting retrieval
- unsupported request escalation
- appointment scheduling
- multi-turn session continuity

Formal benchmark reporting has not yet been expanded into a metrics dashboard, but the project structure supports reporting on routing accuracy, reset success rate, response latency, and user-flow completion.

## Presentation Readiness
The project supports a coherent demonstration flow:
1. Homepage and support entry points
2. Password-help question handled by the knowledge agent
3. Explicit password reset handled by the workflow agent
4. Wi-Fi troubleshooting handled by the knowledge agent
5. Unsupported request routed to escalation and appointment offering
6. Software or hardware request submission

## Special Considerations

### RAG Integration
The project demonstrates retrieval grounding with embeddings and a vector store, specifically OpenAI embeddings and FAISS. Retrieved school IT documents are used to ground knowledge-agent responses, which reduces hallucination risk relative to unconstrained answer generation. The design also reflects best practices by keeping the corpus domain-specific and by escalating when retrieval support is weak.

### Workflow Automation
The project automates repeatable IT operations such as password reset, appointment scheduling, and request submission. The workflow layer is separate from the retrieval layer, which makes the operational logic easier to maintain and explain.

### Integration via MCP
The system uses MCP as the integration layer for support tools. This demonstrates a standardized approach to tool access and distinguishes the project from a design that embeds direct tool logic inside each agent. Although this submission does not include a VS Code-to-GitHub or VS Code-to-Jira MCP demonstration, it does implement MCP as the tool standardization mechanism within the application architecture.

### Multi-Agent Collaboration
The design intentionally separates knowledge retrieval, workflow execution, and escalation. This supports clearer reasoning boundaries, easier debugging, improved maintainability, and better alignment with enterprise multi-agent patterns.

### Industry Awareness
The project aligns conceptually with enterprise AI support platforms such as Glean, Moveworks, and ServiceNow Now Assist. It is best positioned as a lightweight academic prototype of those patterns rather than a direct commercial equivalent.


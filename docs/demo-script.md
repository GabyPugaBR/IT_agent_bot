# Demonstration Narrative

## Demonstration Sequence
The recommended demonstration begins on the `Constellations.com` homepage in order to establish the project as an embedded school support experience rather than a standalone chatbot. The presenter then opens the IT Agent and walks through the following sequence:

1. A password-help question is submitted to show the knowledge agent retrieving and explaining school-specific reset guidance.
2. An explicit reset command for a known user is submitted to show the workflow agent completing a simulated password reset.
3. A Wi-Fi troubleshooting question is submitted to demonstrate that the system can return to retrieval-based support after a workflow action.
4. An unsupported question is submitted to show escalation behavior and appointment offering.
5. An appointment is selected to demonstrate the human-support handoff path.
6. A software or hardware request is submitted to demonstrate structured request intake and automated acknowledgement.

## Key Talking Points
- The application is intentionally architected as a multi-agent system rather than a single conversational chain.
- Knowledge retrieval and workflow execution are separated to preserve clarity and reduce operational risk.
- The retrieval layer is grounded in school-specific IT support content through embeddings and a vector index.
- MCP is used as the standard interface for support tools.
- Session memory preserves continuity across multiple turns.
- Docker provides a reproducible execution environment for demonstration and review.

## Special-Consideration Emphasis

### Retrieval-Augmented Generation
The demonstration should explicitly note that the system uses embeddings and vector search to ground answers in a domain-specific IT knowledge base. This allows the presenter to connect the implementation directly to the rubric requirement for RAG integration.

### Workflow Automation
The workflow demonstration should emphasize that password reset and related support actions are not merely described; they are executed through a separate automation path.

### MCP Integration
The presenter should describe MCP as the standard tool-access layer that sits between agent logic and operational tooling.

### Multi-Agent Collaboration
The handoff from knowledge to workflow to escalation should be framed as intentional separation of concerns rather than branching behavior inside a single agent.

### Industry Awareness
The project can be positioned as a lightweight academic prototype of enterprise AI support systems, with Glean, Moveworks, and ServiceNow Now Assist serving as reference points for the broader market direction.


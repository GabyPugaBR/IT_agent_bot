# Industry Awareness

## Positioning

Constellations IT Support is a lightweight educational prototype of enterprise AI support systems. It does not try to match the breadth of a commercial platform, but it demonstrates the same foundational patterns using production-grade tools:

- **LLM-driven routing** with chain-of-thought reasoning and confidence scoring
- **Retrieval-augmented generation** grounded in domain-specific documentation
- **Workflow automation** with safety guardrails and mandatory confirmation
- **Tool standardization** through MCP — the same protocol gaining adoption in enterprise AI tooling
- **Multi-agent separation of concerns** — routing, knowledge, workflow, escalation, and conversation each handled by a dedicated agent
- **Observable reasoning** — every decision exposes confidence scores and reasoning traces in the API response

## Relevant Vendors

### Glean
Glean positions itself as a workplace AI platform combining enterprise search, assistant capabilities, and agents. Its core value is grounded retrieval over company-specific content. The Constellations prototype applies the same pattern at K-12 school scale: Confluence-backed RAG, domain-specific embeddings, and confidence-gated escalation when retrieval is insufficient.

### Moveworks
Moveworks focuses on enterprise employee support — combining search, action-taking, workflow automation, and MCP-ready agent tooling. This maps directly to the Constellations architecture: knowledge retrieval, password reset workflow, escalation to human support, and MCP as the tool interface. Moveworks has publicly adopted MCP as a standard for agent tool access; this project demonstrates the same pattern.

### ServiceNow Now Assist
ServiceNow Now Assist represents the enterprise workflow side of AI support. It is the reference point for combining conversational answers with action-taking and structured ticket creation. The Constellations escalation agent — which submits requests as support tickets, offers appointment scheduling, and books slots via tool calls — mirrors this pattern at prototype scale.

### OpenAI and the Structured Output Ecosystem
The project uses OpenAI's structured output API (JSON schema mode) on every LLM call. This reflects current best practice for building reliable agentic systems: typed responses, no parsing hacks, predictable behavior under variation. The reasoning trace pattern — surfacing `confidence` and `reasoning` on every decision — is aligned with how observability is being built into production AI systems.

## Why Multi-Agent Architecture Matters

Single-agent or single-chain systems hit predictable limits:
- They cannot cleanly separate "answering" from "acting" — leading to agents that sometimes answer when they should act, and act when they should answer.
- They cannot scope tool access — a retrieval agent does not need MCP tool permissions.
- They are harder to debug — a failure anywhere in the chain is hard to localize.

Separating concerns into specialist agents — each with its own prompt, tools, and termination point — reflects how enterprise AI systems are actually built. LangGraph is one of the primary frameworks used in production for this pattern.

## Suggested Presentation Language

> "This project is a lightweight educational prototype inspired by enterprise AI support platforms. Commercial systems like Glean, Moveworks, and ServiceNow show that modern support tools combine grounded retrieval, workflow automation, tool standardization, and human escalation. Constellations IT Support demonstrates those same ideas in a K-12 IT context — with chain-of-thought LLM routing, RAG-grounded answers, MCP-backed tool execution, and observable reasoning traces on every response turn."

## Why This Matters for the Portfolio

- Demonstrates awareness of current industry direction in AI systems design.
- Shows understanding of *why* multi-agent separation is useful — not just that it exists.
- Connects implementation choices (structured output, MCP, confidence gating) to patterns seen in production systems.
- Positions the project as more than a chatbot — it is a prototype of an AI support platform with the architectural patterns that scale.

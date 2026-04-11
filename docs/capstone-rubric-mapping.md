# Rubric Mapping

## 1. Define the Use Case
### Problem
Constellations School has a small IT team supporting students, teachers, staff, and families. Common issues such as password resets, Wi-Fi issues, Chromebook problems, and software requests take time away from higher-value IT work.

### Goal
Build a multi-agent AI support system that handles repetitive support requests, automates clear workflows, and escalates unresolved issues to human support with a better user experience.

### Success Metrics
- Correctly route common requests to the right agent path
- Successfully answer known support questions from the knowledge base
- Successfully complete simulated password reset workflows
- Offer escalation options when the bot cannot help confidently
- Maintain usable multi-turn context in a single session

## 2. Identify the Agents
- Intake Agent: classifies user requests
- Knowledge Agent: handles RAG and grounded answers
- Workflow Agent: executes supported automations through MCP
- Escalation Agent: offers human-support handoff, appointments, and request submission

## 3. UX Design
- Mock `Constellations.com` school website
- Multiple visible IT Agent entry points
- Responsive slide-over support panel
- Structured cards for password reset, appointments, and request forms
- Conversation-first interface with quick starter pills

## 4. System Development
- Backend: FastAPI + LangGraph
- Retrieval: OpenAI embeddings + FAISS
- Action layer: MCP server and MCP client
- Frontend: React
- Deployment: Dockerized frontend and backend

## 5. Testing and Validation
### Validated scenarios
- Password help question routed to knowledge
- Explicit password reset routed to workflow
- Unsupported requests routed to escalation
- Appointment scheduling exposed through escalation
- Session memory preserved across turns

### Suggested demo metrics to report
- Routing accuracy on curated test prompts
- Average response time
- Password reset success rate
- User flow completion rate for appointment scheduling

## 6. Presentation
Use the following story for the demo:
1. Show the school homepage and visible IT Agent entry points
2. Ask a password-help question
3. Confirm a simulated reset for a known user
4. Ask a Wi-Fi troubleshooting question
5. Ask an unsupported question and show escalation to appointment options
6. Submit a software or hardware request form


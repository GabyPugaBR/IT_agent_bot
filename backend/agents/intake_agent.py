from graph.state import AgentState


KNOWLEDGE_KEYWORDS = {
    "how",
    "help",
    "why",
    "what",
    "where",
    "wifi",
    "wi-fi",
    "chromebook",
    "device",
    "troubleshoot",
    "instructions",
    "internet",
    "network",
}

WORKFLOW_KEYWORDS = {
    "reset",
    "password",
    "unlock",
}

WORKFLOW_CONTINUATION_KEYWORDS = {
    "my username is",
    "username",
    "student",
    "teacher",
    "staff",
    "admin",
}


def intake_agent(state: AgentState) -> AgentState:
    user_input = state["user_input"].lower().strip()
    history = state.get("conversation_history", [])
    last_assistant_message = next(
        (message["content"].lower() for message in reversed(history) if message["role"] == "assistant"),
        "",
    )

    current_is_workflow = any(keyword in user_input for keyword in WORKFLOW_KEYWORDS)
    current_is_knowledge = any(keyword in user_input for keyword in KNOWLEDGE_KEYWORDS)
    workflow_continuation = (
        "specify your username" in last_assistant_message
        and any(keyword in user_input for keyword in WORKFLOW_CONTINUATION_KEYWORDS)
    )

    if current_is_workflow or workflow_continuation:
        intent = "workflow"
    elif current_is_knowledge:
        intent = "knowledge"
    else:
        intent = "escalation"

    return {
        **state,
        "intent": intent,
        "agent_used": "intake",
        "needs_escalation": intent == "escalation",
    }

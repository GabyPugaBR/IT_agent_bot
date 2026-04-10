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
    "mfa",
    "phishing",
    "security",
}

WORKFLOW_KEYWORDS = {
    "reset",
    "password",
    "unlock",
}

WORKFLOW_CONTINUATION_KEYWORDS = {
    "yes",
    "go ahead",
    "please do",
    "do it",
    "reset it",
    "reset my password",
    "my username is",
    "username",
    "student",
    "teacher",
    "staff",
    "admin",
}

PASSWORD_HELP_KEYWORDS = {
    "password",
    "locked out",
    "forgot password",
    "forgot my password",
    "reset my password",
}

EXPLICIT_WORKFLOW_PHRASES = {
    "reset password for",
    "reset the password for",
    "please reset password for",
    "please reset the password for",
}

ESCALATION_KEYWORDS = {
    "request",
    "schedule",
    "appointment",
    "software",
    "hardware",
    "request software",
    "request hardware",
}


def intake_agent(state: AgentState) -> AgentState:
    user_input = state["user_input"].lower().strip()
    history = state.get("conversation_history", [])
    last_assistant_message = next(
        (message["content"].lower() for message in reversed(history) if message["role"] == "assistant"),
        "",
    )

    current_is_workflow = any(phrase in user_input for phrase in EXPLICIT_WORKFLOW_PHRASES)
    current_is_password_help = any(keyword in user_input for keyword in PASSWORD_HELP_KEYWORDS)
    current_is_knowledge = any(keyword in user_input for keyword in KNOWLEDGE_KEYWORDS)
    current_is_escalation = any(keyword in user_input for keyword in ESCALATION_KEYWORDS)
    workflow_continuation = (
        (
            "specify the full username" in last_assistant_message
            or "i can reset it for you" in last_assistant_message
            or "please send something like" in last_assistant_message
        )
        and any(keyword in user_input for keyword in WORKFLOW_CONTINUATION_KEYWORDS)
    )

    if current_is_workflow or workflow_continuation:
        intent = "workflow"
    elif current_is_escalation:
        intent = "escalation"
    elif current_is_password_help or current_is_knowledge:
        intent = "knowledge"
    else:
        intent = "escalation"

    return {
        **state,
        "intent": intent,
        "agent_used": "intake",
        "needs_escalation": intent == "escalation",
    }

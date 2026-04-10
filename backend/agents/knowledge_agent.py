from rag.vector_store import search
from tools.mcp_client import list_it_appointments_via_mcp


PASSWORD_TOPICS = {
    "password",
    "reset",
    "locked out",
    "forgot password",
    "forgot my password",
}


def _is_password_help(user_input: str) -> bool:
    normalized = user_input.lower()
    return any(topic in normalized for topic in PASSWORD_TOPICS)


def knowledge_agent(state):
    user_input = state["user_input"]
    result = search(user_input, top_k=3)
    documents = result["documents"]
    top_score = documents[0]["score"] if documents else 0.0
    metadata = {
        **state.get("metadata", {}),
        "retrieved_documents": documents,
    }

    if not documents or top_score < 0.25:
        slots = list_it_appointments_via_mcp(limit=4)
        metadata.update(
            {
                "appointment_slots": slots.get("slots", []),
                "escalation_options": [
                    "Schedule IT appointment",
                    "Request software/hardware",
                    "Ask another question",
                ],
            }
        )
        return {
            **state,
            "agent_used": "knowledge",
            "response": (
                "I could not find a reliable answer in the school knowledge base. "
                "A human IT staff member is needed, and I can help you schedule an appointment or submit a request."
            ),
            "retrieved_docs": result["sources"],
            "metadata": metadata,
            "needs_escalation": True,
        }

    response = result["answer"]
    if _is_password_help(user_input):
        metadata["follow_up_actions"] = ["Reset password for student12", "Schedule IT appointment"]
        response = (
            f"{response}\n\n"
            "If you'd like, I can reset the password for you next. "
            "Reply with something like 'Reset password for student12'."
        )

    return {
        **state,
        "agent_used": "knowledge",
        "response": response,
        "retrieved_docs": result["sources"],
        "metadata": metadata,
        "needs_escalation": False,
    }

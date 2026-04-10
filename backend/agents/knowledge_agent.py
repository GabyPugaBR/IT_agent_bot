from rag.vector_store import search


def knowledge_agent(state):
    user_input = state["user_input"]

    result = search(user_input, top_k=3)

    return {
        **state,
        "agent_used": "knowledge",
        "response": result["answer"],
        "retrieved_docs": result["sources"],
        "metadata": {
            **state.get("metadata", {}),
            "retrieved_documents": result["documents"],
        },
        "needs_escalation": False,
    }

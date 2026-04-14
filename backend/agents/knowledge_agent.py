from rag.vector_store import search


CONFIDENCE_THRESHOLD = 0.6


def knowledge_agent(state):
    user_input = state["user_input"]
    result = search(user_input, top_k=3)

    documents = result["documents"]
    answer_confidence = result.get("answer_confidence", 0.0)
    is_password_related = result.get("is_password_related", False)
    retrieval_scores = [doc["score"] for doc in documents]

    metadata = {
        **state.get("metadata", {}),
        "retrieved_documents": documents,
        "retrieval_scores": retrieval_scores,
        "answer_confidence": answer_confidence,
        "answer_reasoning": result.get("reasoning", ""),
    }

    if not documents or answer_confidence < CONFIDENCE_THRESHOLD:
        return {
            **state,
            "agent_used": "knowledge",
            "response": (
                "I wasn't able to find a confident answer in the school knowledge base. "
                "A human IT staff member would be best for this — I can help you schedule an appointment or submit a request."
            ),
            "retrieved_docs": result["sources"],
            "metadata": metadata,
            "needs_escalation": True,
        }

    response = result["answer"]

    if is_password_related:
        metadata["offer_password_reset"] = True
        metadata["follow_up_actions"] = ["Yes, reset my password", "No, I just needed the info"]
        response = (
            f"{response}\n\n"
            "Would you like me to perform the reset for you? Just say yes and provide your username, "
            "or type something like 'Reset password for student12'."
        )

    return {
        **state,
        "agent_used": "knowledge",
        "response": response,
        "retrieved_docs": result["sources"],
        "metadata": metadata,
        "needs_escalation": False,
    }

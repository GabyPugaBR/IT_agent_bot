from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from graph.agent_graph import graph
from memory.store import (
    get_session_memory,
    initialize_memory,
    save_message,
    upsert_session_memory,
)
from schemas.chat import ChatRequest, ChatResponse, ReasoningTrace

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "it-agent-bot",
    }


@app.on_event("startup")
def startup_event():
    initialize_memory()


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    memory = get_session_memory(request.session_id)
    session_memory = memory["session"]
    conversation_history = memory["history"]
    username = request.username or session_memory.get("username")
    user_role = request.user_role or session_memory.get("user_role")

    initial_state = {
        "session_id": request.session_id,
        "user_input": request.message,
        "username": username,
        "user_role": user_role,
        "conversation_history": conversation_history,
        "retrieved_docs": [],
        "metadata": {},
    }
    result = graph.invoke(initial_state)

    save_message(
        request.session_id,
        "user",
        request.message,
        {
            "username": username,
            "user_role": user_role,
        },
    )
    save_message(
        request.session_id,
        "assistant",
        result["response"],
        {
            "intent": result["intent"],
            "agent_used": result["agent_used"],
            "sources": result.get("retrieved_docs", []),
            "metadata": result.get("metadata", {}),
        },
    )
    upsert_session_memory(
        request.session_id,
        result.get("username") or username,
        user_role,
        result.get("intent"),
        result.get("agent_used"),
    )

    result_metadata = result.get("metadata", {})
    reasoning_trace = ReasoningTrace(
        routing_intent=result.get("intent"),
        routing_confidence=result_metadata.get("routing_confidence"),
        routing_reasoning=result_metadata.get("routing_reasoning"),
        agent_step=result_metadata.get("agent_step"),
        agent_confidence=result_metadata.get("agent_confidence"),
        agent_reasoning=result_metadata.get("agent_reasoning"),
        answer_confidence=result_metadata.get("answer_confidence"),
        retrieval_scores=result_metadata.get("retrieval_scores", []),
    )

    return ChatResponse(
        response=result["response"],
        intent=result["intent"],
        agent_used=result["agent_used"],
        session_id=request.session_id,
        sources=result.get("retrieved_docs", []),
        metadata=result_metadata,
        reasoning_trace=reasoning_trace,
    )

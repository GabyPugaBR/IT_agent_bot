from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message for the IT support system.")
    session_id: str = Field(default="default-session", description="Conversation thread identifier.")
    username: str | None = Field(default=None, description="Optional username for workflow operations.")
    user_role: str | None = Field(default=None, description="Optional user role such as student or teacher.")


class ReasoningTrace(BaseModel):
    routing_intent: Optional[str] = None
    routing_confidence: Optional[float] = None
    routing_reasoning: Optional[str] = None
    agent_step: Optional[str] = None
    agent_confidence: Optional[float] = None
    agent_reasoning: Optional[str] = None
    answer_confidence: Optional[float] = None
    retrieval_scores: List[float] = Field(default_factory=list)


class ChatResponse(BaseModel):
    response: str
    intent: str
    agent_used: str
    session_id: str
    sources: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    reasoning_trace: ReasoningTrace = Field(default_factory=ReasoningTrace)

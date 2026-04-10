from typing import Any, List

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message for the IT support system.")
    session_id: str = Field(default="default-session", description="Conversation thread identifier.")
    username: str | None = Field(default=None, description="Optional username for workflow operations.")
    user_role: str | None = Field(default=None, description="Optional user role such as student or teacher.")


class ChatResponse(BaseModel):
    response: str
    intent: str
    agent_used: str
    session_id: str
    sources: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

from typing import Any, List, Optional, TypedDict


class AgentState(TypedDict, total=False):
    session_id: str
    user_input: str
    intent: str
    response: str
    agent_used: str
    retrieved_docs: List[str]
    workflow_result: Optional[str]
    needs_escalation: bool
    user_role: Optional[str]
    username: Optional[str]
    conversation_history: List[dict[str, Any]]
    metadata: dict[str, Any]

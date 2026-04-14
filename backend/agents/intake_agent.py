import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agents.prompts import INTAKE_AGENT_PROMPT
from graph.state import AgentState

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

INTAKE_MODEL = os.getenv("OPENAI_ROUTER_MODEL", os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None


def _route_with_llm(user_input: str, history: list[dict]) -> dict:
    recent_history = history[-6:]
    transcript = "\n".join(
        f"{msg['role']}: {msg['content']}"
        for msg in recent_history
    ) or "No previous conversation."

    try:
        response = client.responses.create(
            model=INTAKE_MODEL,
            text={"format": {"type": "json_schema", "name": "routing_decision", "schema": {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "enum": ["knowledge", "workflow", "escalation", "smalltalk"],
                    },
                    "confidence": {"type": "number"},
                    "reasoning": {"type": "string"},
                },
                "required": ["intent", "confidence", "reasoning"],
                "additionalProperties": False,
            }}},
            input=[
                {"role": "system", "content": INTAKE_AGENT_PROMPT},
                {"role": "user", "content": (
                    f"Conversation so far:\n{transcript}\n\n"
                    f"Current user message: {user_input}"
                )},
            ],
        )
        return json.loads(response.output_text)
    except Exception:
        return {
            "intent": "escalation",
            "confidence": 0.5,
            "reasoning": "Routing error — defaulting to escalation.",
        }


def intake_agent(state: AgentState) -> AgentState:
    user_input = state["user_input"]
    history = state.get("conversation_history", [])

    if client is None:
        return {
            **state,
            "intent": "escalation",
            "agent_used": "intake",
            "needs_escalation": True,
            "metadata": {
                **state.get("metadata", {}),
                "routing_confidence": 0.0,
                "routing_reasoning": "No LLM client available.",
            },
        }

    result = _route_with_llm(user_input, history)
    intent = result.get("intent", "escalation")

    return {
        **state,
        "intent": intent,
        "agent_used": "intake",
        "needs_escalation": intent == "escalation",
        "metadata": {
            **state.get("metadata", {}),
            "routing_confidence": result.get("confidence"),
            "routing_reasoning": result.get("reasoning"),
        },
    }

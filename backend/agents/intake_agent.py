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
    "reset my password",
    "reset password",
    "reset password for",
    "reset the password for",
    "please reset password for",
    "please reset the password for",
}

QUESTION_WORDS = {"how", "what", "where", "why", "help"}

ESCALATION_KEYWORDS = {
    "request",
    "schedule",
    "appointment",
    "software",
    "hardware",
    "request software",
    "request hardware",
}

ESCALATION_CONTINUATION_KEYWORDS = {
    "yes",
    "yes, show appointments",
    "show appointments",
    "no thanks",
    "request software/hardware",
    "ask another question",
    "exit chat",
}


def _heuristic_intent(user_input: str, history: list[dict]) -> str:
    last_assistant_message = next(
        (message["content"].lower() for message in reversed(history) if message["role"] == "assistant"),
        "",
    )

    current_is_workflow = any(phrase in user_input for phrase in EXPLICIT_WORKFLOW_PHRASES)
    current_is_password_help = any(keyword in user_input for keyword in PASSWORD_HELP_KEYWORDS)
    current_is_knowledge = any(keyword in user_input for keyword in KNOWLEDGE_KEYWORDS)
    current_is_escalation = any(keyword in user_input for keyword in ESCALATION_KEYWORDS)
    current_is_password_question = current_is_password_help and any(
        user_input.startswith(f"{question_word} ") or f" {question_word} " in user_input
        for question_word in QUESTION_WORDS
    )
    workflow_continuation = (
        (
            "specify the full username" in last_assistant_message
            or "i can reset it for you" in last_assistant_message
            or "please send something like" in last_assistant_message
            or "should i reset the password for" in last_assistant_message
        )
        and any(keyword in user_input for keyword in WORKFLOW_CONTINUATION_KEYWORDS)
    )
    escalation_continuation = (
        "would you like me to show available it appointments" in last_assistant_message
        and any(keyword in user_input for keyword in ESCALATION_CONTINUATION_KEYWORDS)
    )

    if (current_is_workflow and not current_is_password_question) or workflow_continuation:
        return "workflow"
    if escalation_continuation:
        return "escalation"
    if current_is_escalation:
        return "escalation"
    if current_is_password_help or current_is_knowledge:
        return "knowledge"
    return "escalation"


def _classify_with_llm(user_input: str, history: list[dict], heuristic_intent: str) -> str:
    if client is None:
        return heuristic_intent

    recent_history = history[-6:]
    transcript = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in recent_history
    ) or "No previous conversation."

    try:
        response = client.responses.create(
            model=INTAKE_MODEL,
            text={"format": {"type": "json_schema", "name": "routing_decision", "schema": {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "enum": ["knowledge", "workflow", "escalation"],
                    }
                },
                "required": ["intent"],
                "additionalProperties": False,
            }}},
            input=[
                {
                    "role": "system",
                    "content": INTAKE_AGENT_PROMPT,
                },
                {
                    "role": "user",
                    "content": (
                        f"Recent conversation:\n{transcript}\n\n"
                        f"Current user message:\n{user_input}\n\n"
                        f"Heuristic suggestion: {heuristic_intent}\n\n"
                        "Return the single best routing intent."
                    ),
                },
            ],
        )
        payload = json.loads(response.output_text)
        return payload.get("intent", heuristic_intent)
    except Exception:
        return heuristic_intent


def intake_agent(state: AgentState) -> AgentState:
    user_input = state["user_input"].lower().strip()
    history = state.get("conversation_history", [])
    heuristic_intent = _heuristic_intent(user_input, history)
    intent = _classify_with_llm(user_input, history, heuristic_intent)

    return {
        **state,
        "intent": intent,
        "agent_used": "intake",
        "needs_escalation": intent == "escalation",
    }

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agents.prompts import WORKFLOW_AGENT_PROMPT, WORKFLOW_DECISION_PROMPT
from tools.mcp_client import create_support_ticket_via_mcp, lookup_user_via_mcp, reset_user_password_via_mcp

# Fast-path regex for well-formed usernames — used as an optimization, not a gate
USERNAME_PATTERN = re.compile(r"\b(student|teacher|staff|admin)\s*-?\s*(\d+)\b")
ROLE_ONLY_PATTERN = re.compile(r"\b(student|teacher|staff|admin)\b")

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
WORKFLOW_MODEL = os.getenv("OPENAI_ROUTER_MODEL", os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None


def _extract_username(text: str, history: list[dict]) -> str | None:
    """
    Extract a username from user input.
    Uses regex as a fast path; falls back to LLM for natural-language variations.
    """
    match = USERNAME_PATTERN.search(text)
    if match:
        return f"{match.group(1)}{match.group(2)}"

    if client is None:
        return None

    recent_history = history[-4:]
    transcript = "\n".join(
        f"{msg['role']}: {msg['content']}"
        for msg in recent_history
    ) or "No previous conversation."

    try:
        response = client.responses.create(
            model=WORKFLOW_MODEL,
            text={"format": {"type": "json_schema", "name": "username_extraction", "schema": {
                "type": "object",
                "properties": {
                    "username": {"type": ["string", "null"]},
                    "confidence": {"type": "number"},
                    "reasoning": {"type": "string"},
                },
                "required": ["username", "confidence", "reasoning"],
                "additionalProperties": False,
            }}},
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are a username extraction assistant for a school IT support system. "
                        "Usernames follow the format: student{N}, teacher{N}, staff{N}, or admin{N} (e.g. student42, teacher3). "
                        "Extract the username from the user's message if one is present or clearly implied. "
                        "Handle variations like 'teacher number 5', 'the student with id 42', 'admin-1', 'student 12'. "
                        "Return null if no username can be confidently identified."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Conversation so far:\n{transcript}\n\n"
                        f"Current message: {text}"
                    ),
                },
            ],
        )
        payload = json.loads(response.output_text)
        return payload.get("username")
    except Exception:
        return None


def _find_pending_reset(history: list[dict]) -> tuple[str | None, dict | None]:
    for message in reversed(history):
        if message["role"] != "assistant":
            continue
        # Messages are saved in main.py as {"intent": ..., "metadata": {...}}
        # so pending_reset_username lives inside the nested "metadata" key
        outer = message.get("metadata", {}) or {}
        inner = outer.get("metadata", {}) or {}
        pending_username = inner.get("pending_reset_username")
        if pending_username:
            return pending_username, inner.get("pending_user_lookup")
    return None, None


def _decide_workflow_step(
    user_input: str,
    history: list[dict],
    extracted_username: str | None,
    pending_username: str | None,
) -> dict:
    """
    Returns a dict with: action, confidence, reasoning.
    Falls back to safe defaults if LLM is unavailable.
    """
    if client is None:
        if pending_username:
            return {"action": "execute_reset", "confidence": 0.5, "reasoning": "No LLM — defaulting based on pending username."}
        if extracted_username:
            return {"action": "confirm_target_user", "confidence": 0.5, "reasoning": "No LLM — username present, requesting confirmation."}
        return {"action": "ask_for_username", "confidence": 0.5, "reasoning": "No LLM — no username found."}

    recent_history = history[-6:]
    transcript = "\n".join(
        f"{msg['role']}: {msg['content']}"
        for msg in recent_history
    ) or "No previous conversation."

    try:
        response = client.responses.create(
            model=WORKFLOW_MODEL,
            text={"format": {"type": "json_schema", "name": "workflow_decision", "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["ask_for_username", "confirm_target_user", "execute_reset", "escalate"],
                    },
                    "confidence": {"type": "number"},
                    "reasoning": {"type": "string"},
                },
                "required": ["action", "confidence", "reasoning"],
                "additionalProperties": False,
            }}},
            input=[
                {
                    "role": "system",
                    "content": f"{WORKFLOW_AGENT_PROMPT}\n\n{WORKFLOW_DECISION_PROMPT}",
                },
                {
                    "role": "user",
                    "content": (
                        f"Conversation so far:\n{transcript}\n\n"
                        f"Current user message: {user_input}\n\n"
                        f"Extracted username from current message: {extracted_username or 'none'}\n"
                        f"Pending reset target from prior turn: {pending_username or 'none'}"
                    ),
                },
            ],
        )
        return json.loads(response.output_text)
    except Exception:
        return {"action": "ask_for_username", "confidence": 0.5, "reasoning": "LLM error — defaulting to ask for username."}


def workflow_agent(state):
    user_input = state["user_input"]
    username = state.get("username")
    history = state.get("conversation_history", [])
    metadata = state.get("metadata", {})

    pending_username, pending_user_lookup = _find_pending_reset(history)
    extracted_username = username or _extract_username(user_input, history)

    decision = _decide_workflow_step(
        user_input=user_input,
        history=history,
        extracted_username=extracted_username,
        pending_username=pending_username,
    )
    workflow_step = decision["action"]

    metadata = {
        **metadata,
        "agent_step": workflow_step,
        "agent_confidence": decision.get("confidence"),
        "agent_reasoning": decision.get("reasoning"),
    }

    if workflow_step == "escalate":
        return {
            **state,
            "agent_used": "workflow",
            "workflow_result": "escalated",
            "response": "I can't safely complete that password workflow here. Let me connect you with human IT support.",
            "needs_escalation": True,
            "metadata": metadata,
        }

    if workflow_step == "ask_for_username":
        role_only_match = ROLE_ONLY_PATTERN.search(user_input.lower())
        if role_only_match:
            role = role_only_match.group(1)
            return {
                **state,
                "agent_used": "workflow",
                "workflow_result": "partial_username",
                "response": (
                    f"I need the full username to reset the password. "
                    f"Please send something like {role}12."
                ),
                "needs_escalation": False,
                "metadata": metadata,
            }
        return {
            **state,
            "agent_used": "workflow",
            "workflow_result": "missing_username",
            "response": (
                "Please provide the full username so I can reset the password. "
                "For example: student12, teacher3, staff4, or admin1."
            ),
            "needs_escalation": False,
            "metadata": metadata,
        }

    if workflow_step == "execute_reset" and pending_username:
        resolved_username = pending_username
        user_lookup = pending_user_lookup or lookup_user_via_mcp(resolved_username)
    else:
        resolved_username = extracted_username or pending_username
        user_lookup = pending_user_lookup if pending_username == resolved_username else None

    if not resolved_username:
        return {
            **state,
            "agent_used": "workflow",
            "workflow_result": "missing_username",
            "response": (
                "Please provide the full username so I can reset the password. "
                "For example: student12, teacher3, staff4, or admin1."
            ),
            "needs_escalation": False,
            "metadata": metadata,
        }

    if not user_lookup:
        user_lookup = lookup_user_via_mcp(resolved_username)
    if user_lookup.get("status") != "success":
        ticket = create_support_ticket_via_mcp(
            username=resolved_username,
            issue_summary="Password reset requested for unknown user.",
            urgency="normal",
        )
        return {
            **state,
            "agent_used": "workflow",
            "workflow_result": ticket,
            "response": "I couldn't find that user. I've created a support ticket for the IT team to follow up.",
            "needs_escalation": True,
            "metadata": {**metadata, "ticket": ticket},
        }

    if workflow_step != "execute_reset":
        user = user_lookup.get("user", {})
        display_name = user.get("display_name", resolved_username)
        return {
            **state,
            "agent_used": "workflow",
            "username": resolved_username,
            "workflow_result": "awaiting_confirmation",
            "response": (
                f"I found {display_name} ({resolved_username}). "
                "Should I reset the password for this user?"
            ),
            "needs_escalation": False,
            "metadata": {
                **metadata,
                "pending_reset_username": resolved_username,
                "pending_user_lookup": user_lookup,
                "follow_up_actions": [
                    f"Yes, reset password for {resolved_username}",
                    "No, ask another question",
                ],
            },
        }

    result = reset_user_password_via_mcp(resolved_username)
    if result.get("status") != "success":
        ticket = create_support_ticket_via_mcp(
            username=resolved_username,
            issue_summary="Password reset tool returned an error.",
            urgency="high",
        )
        return {
            **state,
            "agent_used": "workflow",
            "workflow_result": ticket,
            "response": "The password reset service encountered an issue. I've created a high-priority ticket for the IT team.",
            "needs_escalation": True,
            "metadata": {**metadata, "ticket": ticket},
        }

    return {
        **state,
        "agent_used": "workflow",
        "username": resolved_username,
        "workflow_result": result,
        "response": (
            f"{result['message']} "
            "The user must change the password at next sign-in."
        ),
        "needs_escalation": False,
        "metadata": {
            **metadata,
            "mcp_tool_used": "reset_user_password",
            "user_lookup": user_lookup,
            "password_policy": result.get("password_policy", {}),
            "workflow_result": result,
        },
    }

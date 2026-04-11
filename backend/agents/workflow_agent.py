import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agents.prompts import WORKFLOW_AGENT_PROMPT, WORKFLOW_DECISION_PROMPT

from tools.mcp_client import create_support_ticket_via_mcp, lookup_user_via_mcp, reset_user_password_via_mcp


USERNAME_PATTERN = re.compile(r"\b(student|teacher|staff|admin)\s*-?\s*(\d+)\b")
ROLE_ONLY_PATTERN = re.compile(r"\b(student|teacher|staff|admin)\b")
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
WORKFLOW_MODEL = os.getenv("OPENAI_ROUTER_MODEL", os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None


def _extract_username(text: str) -> str | None:
    match = USERNAME_PATTERN.search(text)
    if not match:
        return None
    return f"{match.group(1)}{match.group(2)}"


def _is_confirmation(text: str) -> bool:
    normalized = text.lower().strip()
    return normalized in {"yes", "yes please", "go ahead", "confirm", "please do", "do it", "yes reset it"}


def _find_pending_reset(history: list[dict]) -> tuple[str | None, dict | None]:
    for message in reversed(history):
        if message["role"] != "assistant":
            continue
        metadata = message.get("metadata", {}) or {}
        pending_username = metadata.get("pending_reset_username")
        if pending_username:
            return pending_username, metadata.get("pending_user_lookup")
    return None, None


def _decide_workflow_step(
    user_input: str,
    history: list[dict],
    extracted_username: str | None,
    pending_username: str | None,
) -> str:
    if client is None:
        if pending_username and _is_confirmation(user_input):
            return "execute_reset"
        if extracted_username or pending_username:
            return "confirm_target_user"
        return "ask_for_username"

    recent_history = history[-6:]
    transcript = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in recent_history
    ) or "No previous conversation."

    heuristic_step = "ask_for_username"
    if pending_username and _is_confirmation(user_input):
        heuristic_step = "execute_reset"
    elif extracted_username or pending_username:
        heuristic_step = "confirm_target_user"

    try:
        response = client.responses.create(
            model=WORKFLOW_MODEL,
            text={"format": {"type": "json_schema", "name": "workflow_decision", "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["ask_for_username", "confirm_target_user", "execute_reset", "escalate"],
                    }
                },
                "required": ["action"],
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
                        f"Recent conversation:\n{transcript}\n\n"
                        f"Current user message:\n{user_input}\n\n"
                        f"Extracted username: {extracted_username or 'none'}\n"
                        f"Pending reset target: {pending_username or 'none'}\n"
                        f"Heuristic suggestion: {heuristic_step}"
                    ),
                },
            ],
        )
        payload = json.loads(response.output_text)
        return payload.get("action", heuristic_step)
    except Exception:
        return heuristic_step


def workflow_agent(state):
    user_input = state["user_input"].lower()
    username = state.get("username")
    history = state.get("conversation_history", [])
    pending_username, pending_user_lookup = _find_pending_reset(history)
    extracted_username = username or _extract_username(user_input)
    workflow_step = _decide_workflow_step(
        user_input=user_input,
        history=history,
        extracted_username=extracted_username,
        pending_username=pending_username,
    )

    if workflow_step == "escalate":
        return {
            **state,
            "agent_used": "workflow",
            "workflow_result": "escalated",
            "response": "I can't safely complete that password workflow here, so human IT support is needed.",
            "needs_escalation": True,
        }

    if workflow_step == "ask_for_username":
        role_only_match = ROLE_ONLY_PATTERN.search(user_input)
        if role_only_match:
            role = role_only_match.group(1)
            return {
                **state,
                "agent_used": "workflow",
                "workflow_result": "partial_username",
                "response": (
                    f"I need the full username before I can reset the password. "
                    f"Please send something like {role}12."
                ),
                "needs_escalation": False,
            }
        return {
            **state,
            "agent_used": "workflow",
            "workflow_result": "missing_username",
            "response": (
                "Please specify the full username so I can reset the password. "
                "For example: student12, teacher3, staff4, or admin1."
            ),
            "needs_escalation": False,
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
                "Please specify the full username so I can reset the password. "
                "For example: student12, teacher3, staff4, or admin1."
            ),
            "needs_escalation": False,
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
            "response": "I could not find that user. I created a support ticket for human follow-up.",
            "needs_escalation": True,
            "metadata": {
                **state.get("metadata", {}),
                "ticket": ticket,
            },
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
                **state.get("metadata", {}),
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
            "response": "The password reset service had an issue, so I created a support ticket for IT.",
            "needs_escalation": True,
            "metadata": {
                **state.get("metadata", {}),
                "ticket": ticket,
            },
        }

    return {
        **state,
        "agent_used": "workflow",
        "username": resolved_username,
        "workflow_result": result,
        "response": (
            f"{result['message']} "
            f"The user must change the password at next sign-in."
        ),
        "needs_escalation": False,
        "metadata": {
            **state.get("metadata", {}),
            "mcp_tool_used": "reset_user_password",
            "user_lookup": user_lookup,
            "password_policy": result.get("password_policy", {}),
            "workflow_result": result,
        },
    }

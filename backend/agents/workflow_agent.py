import re

from tools.mcp_client import create_support_ticket_via_mcp, lookup_user_via_mcp, reset_user_password_via_mcp


USERNAME_PATTERN = re.compile(r"\b(student|teacher|staff|admin)\s*-?\s*(\d+)\b")
ROLE_ONLY_PATTERN = re.compile(r"\b(student|teacher|staff|admin)\b")


def _extract_username(text: str) -> str | None:
    match = USERNAME_PATTERN.search(text)
    if not match:
        return None
    return f"{match.group(1)}{match.group(2)}"


def workflow_agent(state):
    user_input = state["user_input"].lower()
    username = state.get("username")
    history = state.get("conversation_history", [])

    if username:
        resolved_username = username
    else:
        extracted_username = _extract_username(user_input)
        if extracted_username:
            resolved_username = extracted_username
        else:
            remembered_username = None
            for message in reversed(history):
                extracted_from_history = _extract_username(message["content"].lower())
                if extracted_from_history:
                    remembered_username = extracted_from_history
                    break

            if remembered_username:
                resolved_username = remembered_username
            else:
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

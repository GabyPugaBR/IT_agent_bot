import re

from tools.mcp_client import (
    book_it_appointment_via_mcp,
    create_support_ticket_via_mcp,
    list_it_appointments_via_mcp,
)


SLOT_PATTERN = re.compile(r"\bslot-\d{3}\b", re.IGNORECASE)
REQUEST_TRIGGER_PATTERNS = (
    "request",
    "request software",
    "request hardware",
    "software request",
    "hardware request",
)
REQUEST_SUBMISSION_FIELDS = ("request type:", "item:", "purpose:", "device type:", "deadline:")
APPOINTMENT_CONFIRMATION_PATTERNS = (
    "yes",
    "yes, show appointments",
    "show appointments",
    "schedule appointment",
    "schedule it appointment",
)
DIRECT_APPOINTMENT_PATTERNS = (
    "schedule it appointment",
    "schedule appointment",
    "book appointment",
    "book it appointment",
    "show available appointments",
    "available appointments",
)
DECLINE_PATTERNS = (
    "no",
    "no thanks",
    "something else",
    "ask another question",
    "exit",
    "close",
)


def _is_request_submission(user_input: str) -> bool:
    normalized = user_input.lower()
    return all(field in normalized for field in REQUEST_SUBMISSION_FIELDS)


def escalation_agent(state):
    user_input = state["user_input"]
    normalized_input = user_input.lower()
    username = state.get("username")
    history = state.get("conversation_history", [])
    slot_match = SLOT_PATTERN.search(user_input)
    last_assistant_message = next(
        (message["content"].lower() for message in reversed(history) if message["role"] == "assistant"),
        "",
    )

    if slot_match:
        booking = book_it_appointment_via_mcp(
            slot_id=slot_match.group(0).lower(),
            booked_for=username,
            issue_summary=user_input,
        )
        if booking.get("status") == "success":
            return {
                **state,
                "agent_used": "escalation",
                "needs_escalation": True,
                "response": "Your IT support appointment has been scheduled.",
                "metadata": {
                    **state.get("metadata", {}),
                    "appointment": booking.get("appointment"),
                    "escalation_options": ["View appointment", "Ask another question"],
                },
            }

    if any(pattern in normalized_input for pattern in DIRECT_APPOINTMENT_PATTERNS):
        slots = list_it_appointments_via_mcp(limit=4)
        return {
            **state,
            "agent_used": "escalation",
            "needs_escalation": True,
            "response": "Here are the next available IT appointment options.",
            "metadata": {
                **state.get("metadata", {}),
                "appointment_slots": slots.get("slots", []),
                "escalation_options": ["Request software/hardware", "Ask another question", "Exit chat"],
            },
        }

    if (
        "would you like me to show available appointments" in last_assistant_message
        and any(pattern in normalized_input for pattern in APPOINTMENT_CONFIRMATION_PATTERNS)
    ):
        slots = list_it_appointments_via_mcp(limit=4)
        return {
            **state,
            "agent_used": "escalation",
            "needs_escalation": True,
            "response": "Here are the next available IT appointment options.",
            "metadata": {
                **state.get("metadata", {}),
                "appointment_slots": slots.get("slots", []),
                "escalation_options": ["Request software/hardware", "Ask another question", "Exit chat"],
            },
        }

    if (
        "would you like me to show available appointments" in last_assistant_message
        and any(pattern in normalized_input for pattern in DECLINE_PATTERNS)
    ):
        return {
            **state,
            "agent_used": "escalation",
            "needs_escalation": True,
            "response": "No problem. If you'd like, I can help with something else or you can close the chat.",
            "metadata": {
                **state.get("metadata", {}),
                "escalation_options": ["Request software/hardware", "Ask another question", "Exit chat"],
            },
        }

    if any(trigger in normalized_input for trigger in REQUEST_TRIGGER_PATTERNS) and not _is_request_submission(user_input):
        return {
            **state,
            "agent_used": "escalation",
            "needs_escalation": True,
            "response": (
                "I can help you submit a software or hardware request. "
                "Please fill out the request form below."
            ),
            "metadata": {
                **state.get("metadata", {}),
                "software_request_form": {
                    "title": "Software or Hardware Request",
                    "request_types": ["Software", "Hardware"],
                },
            },
        }

    if _is_request_submission(user_input):
        ticket = create_support_ticket_via_mcp(
            username=username,
            issue_summary=user_input,
            urgency="normal",
        )
        return {
            **state,
            "agent_used": "escalation",
            "needs_escalation": True,
            "response": "Your request has been submitted. IT will get back to you within 72 hours.",
            "metadata": {
                **state.get("metadata", {}),
                "ticket": ticket,
                "escalation_options": ["Ask another question", "Exit chat"],
            },
        }

    return {
        **state,
        "agent_used": "escalation",
        "needs_escalation": True,
        "response": (
            "I can't help with that directly from the knowledge base or automated tools. "
            "Would you like me to show available IT appointments?"
        ),
        "metadata": {
            **state.get("metadata", {}),
            "escalation_options": [
                "Yes, show appointments",
                "No thanks",
                "Request software/hardware",
                "Ask another question",
                "Exit chat",
            ],
        },
    }

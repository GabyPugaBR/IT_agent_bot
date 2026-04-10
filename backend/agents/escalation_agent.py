import re

from tools.mcp_client import (
    book_it_appointment_via_mcp,
    create_support_ticket_via_mcp,
    list_it_appointments_via_mcp,
)


SLOT_PATTERN = re.compile(r"\bslot-\d{3}\b", re.IGNORECASE)


def escalation_agent(state):
    user_input = state["user_input"]
    username = state.get("username")
    slot_match = SLOT_PATTERN.search(user_input)

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

    ticket = create_support_ticket_via_mcp(
        username=username,
        issue_summary=user_input,
        urgency="normal",
    )
    slots = list_it_appointments_via_mcp(limit=4)

    return {
        **state,
        "agent_used": "escalation",
        "needs_escalation": True,
        "response": "This issue needs human support. I created a ticket and can help you schedule an appointment with IT.",
        "metadata": {
            **state.get("metadata", {}),
            "ticket": ticket,
            "appointment_slots": slots.get("slots", []),
            "escalation_options": [
                "Schedule IT appointment",
                "Create support ticket",
                "Ask another question",
            ],
        },
    }

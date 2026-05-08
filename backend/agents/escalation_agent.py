import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agents.prompts import ESCALATION_AGENT_PROMPT, ESCALATION_DECISION_PROMPT
from tools.mcp_client import (
    book_it_appointment_via_mcp,
    create_support_ticket_via_mcp,
    list_it_appointments_via_mcp,
)

# Kept for deterministic slot-ID extraction — data format, not semantic reasoning
SLOT_PATTERN = re.compile(r"\bslot-\d{3}\b", re.IGNORECASE)
REQUEST_FORM_PATTERN = re.compile(r"Software/Hardware Request", re.IGNORECASE)
APPOINTMENT_FORM_PATTERN = re.compile(r"IT Appointment Request", re.IGNORECASE)
REQUEST_KEYWORDS_PATTERN = re.compile(
    r"\b(software|hardware|equipment|application|app|license|laptop|chromebook|computer|tablet|monitor|adobe|premiere)\b",
    re.IGNORECASE,
)

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
ESCALATION_MODEL = os.getenv("OPENAI_ROUTER_MODEL", os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None


def _extract_form_field(text: str, label: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(label)}:\s*(.+)$", re.IGNORECASE | re.MULTILINE)
    match = pattern.search(text)
    if not match:
        return None
    value = match.group(1).strip()
    return value if value and value.lower() != "not specified" else None


def _parse_appointment_request(text: str) -> dict:
    slot_match = SLOT_PATTERN.search(text)
    return {
        "slot_id": slot_match.group(0).lower() if slot_match else None,
        "name": _extract_form_field(text, "Name"),
        "issue_summary": _extract_form_field(text, "Issue"),
    }


def _decide_escalation_action(user_input: str, history: list[dict], slot_match) -> dict:
    """
    Returns a dict with: action, confidence, reasoning, is_request_submission.
    Slot-ID match is deterministic; everything else goes to the LLM.
    """
    if APPOINTMENT_FORM_PATTERN.search(user_input) and slot_match:
        return {
            "action": "book_appointment",
            "confidence": 1.0,
            "reasoning": "Structured appointment request detected — booking deterministically.",
            "is_request_submission": False,
        }

    if REQUEST_FORM_PATTERN.search(user_input):
        return {
            "action": "submit_request",
            "confidence": 1.0,
            "reasoning": "Structured software/hardware request form submission detected.",
            "is_request_submission": True,
        }

    if REQUEST_KEYWORDS_PATTERN.search(user_input):
        return {
            "action": "show_request_form",
            "confidence": 1.0,
            "reasoning": "Software or hardware request detected — showing the form before ticket creation.",
            "is_request_submission": False,
        }

    if client is None:
        return {
            "action": "offer_appointments",
            "confidence": 0.5,
            "reasoning": "No LLM client — defaulting to offer appointments.",
            "is_request_submission": False,
        }

    recent_history = history[-6:]
    transcript = "\n".join(
        f"{msg['role']}: {msg['content']}"
        for msg in recent_history
    ) or "No previous conversation."

    try:
        response = client.responses.create(
            model=ESCALATION_MODEL,
            text={"format": {"type": "json_schema", "name": "escalation_decision", "schema": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "show_appointments",
                            "offer_appointments",
                            "show_request_form",
                            "submit_request",
                            "acknowledge_decline",
                            "book_appointment",
                        ],
                    },
                    "confidence": {"type": "number"},
                    "reasoning": {"type": "string"},
                    "is_request_submission": {"type": "boolean"},
                },
                "required": ["action", "confidence", "reasoning", "is_request_submission"],
                "additionalProperties": False,
            }}},
            input=[
                {
                    "role": "system",
                    "content": f"{ESCALATION_AGENT_PROMPT}\n\n{ESCALATION_DECISION_PROMPT}",
                },
                {
                    "role": "user",
                    "content": (
                        f"Conversation so far:\n{transcript}\n\n"
                        f"Current user message: {user_input}"
                    ),
                },
            ],
        )
        return json.loads(response.output_text)
    except Exception:
        return {
            "action": "offer_appointments",
            "confidence": 0.5,
            "reasoning": "LLM error — defaulting to offer appointments.",
            "is_request_submission": False,
        }


def escalation_agent(state):
    user_input = state["user_input"]
    username = state.get("username")
    history = state.get("conversation_history", [])
    slot_match = SLOT_PATTERN.search(user_input)

    decision = _decide_escalation_action(user_input, history, slot_match)
    action = decision["action"]
    is_request_submission = decision.get("is_request_submission", False)

    metadata = {
        **state.get("metadata", {}),
        "agent_step": action,
        "agent_confidence": decision.get("confidence"),
        "agent_reasoning": decision.get("reasoning"),
    }

    if action == "book_appointment" and slot_match:
        appointment_request = _parse_appointment_request(user_input)
        booked_for = appointment_request.get("name") or username
        issue_summary = appointment_request.get("issue_summary") or "IT appointment requested."
        booking = book_it_appointment_via_mcp(
            slot_id=appointment_request.get("slot_id") or slot_match.group(0).lower(),
            booked_for=booked_for,
            issue_summary=issue_summary,
        )
        if booking.get("status") == "success":
            appointment = booking.get("appointment")
            ticket = create_support_ticket_via_mcp(
                username=booked_for,
                issue_summary=f"IT appointment scheduled: {issue_summary}",
                urgency="normal",
            )
            return {
                **state,
                "agent_used": "escalation",
                "needs_escalation": True,
                "response": "Your IT support appointment has been scheduled and a confirmation ticket has been created.",
                "metadata": {
                    **metadata,
                    "appointment": appointment,
                    "ticket": ticket,
                    "escalation_options": ["View appointment", "Ask another question"],
                },
            }

    if action == "show_appointments":
        slots = list_it_appointments_via_mcp(limit=4)
        return {
            **state,
            "agent_used": "escalation",
            "needs_escalation": True,
            "response": "Here are the next available IT appointment slots.",
            "metadata": {
                **metadata,
                "appointment_slots": slots.get("slots", []),
                "escalation_options": ["Request software/hardware", "Ask another question", "Exit chat"],
            },
        }

    if action == "acknowledge_decline":
        return {
            **state,
            "agent_used": "escalation",
            "needs_escalation": True,
            "response": "No problem at all. Is there anything else I can help you with, or feel free to close the chat.",
            "metadata": {
                **metadata,
                "escalation_options": ["Request software/hardware", "Ask another question", "Exit chat"],
            },
        }

    if action == "submit_request" and is_request_submission:
        ticket = create_support_ticket_via_mcp(
            username=username,
            issue_summary=user_input,
            urgency="normal",
        )
        return {
            **state,
            "agent_used": "escalation",
            "needs_escalation": True,
            "response": "Your request has been submitted. The IT team will get back to you within 72 hours.",
            "metadata": {
                **metadata,
                "ticket": ticket,
                "escalation_options": ["Ask another question", "Exit chat"],
            },
        }

    if action == "show_request_form":
        return {
            **state,
            "agent_used": "escalation",
            "needs_escalation": True,
            "response": (
                "I can help you submit a software or hardware request. "
                "Please fill out the form below."
            ),
            "metadata": {
                **metadata,
                "software_request_form": {
                    "title": "Software or Hardware Request",
                    "request_types": ["Software", "Hardware"],
                },
            },
        }

    # Default: offer_appointments
    return {
        **state,
        "agent_used": "escalation",
        "needs_escalation": True,
        "response": (
            "I wasn't able to resolve that through the knowledge base or automated tools. "
            "Would you like to schedule an IT appointment or submit a request?"
        ),
        "metadata": {
            **metadata,
            "escalation_options": [
                "Yes, show appointments",
                "Request software/hardware",
                "Ask another question",
                "Exit chat",
            ],
        },
    }

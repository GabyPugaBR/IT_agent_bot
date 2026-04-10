import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from tools.password_reset import reset_password
from tools.calendar import book_slot, ensure_calendar_db, list_available_slots
from tools.user_db import create_ticket, ensure_user_db, find_user, get_password_policy

mcp = FastMCP("constellations-support")


@mcp.tool(description="Look up a Constellations School user by username.")
def lookup_user(username: str) -> dict:
    ensure_user_db()
    user = find_user(username)
    if not user:
        return {
            "status": "error",
            "message": "User not found.",
        }

    return {
        "status": "success",
        "user": {
            "username": user["username"],
            "display_name": user["display_name"],
            "role": user["role"],
            "unit": user["unit"],
            "email": user["email"],
            "account_status": user["status"],
            "must_change_password": user["must_change_password"],
        },
    }


@mcp.tool(description="Reset a Constellations School password using the simulated identity system.")
def reset_user_password(username: str) -> dict:
    ensure_user_db()
    return reset_password(username)


@mcp.tool(description="Return the password policy for a given user role.")
def get_role_password_policy(role: str) -> dict:
    ensure_user_db()
    return {
        "status": "success",
        "role": role,
        "policy": get_password_policy(role),
    }


@mcp.tool(description="Create a simulated IT support ticket.")
def create_support_ticket(username: str | None, issue_summary: str, urgency: str = "normal") -> dict:
    ensure_user_db()
    ticket = create_ticket(username=username, issue_summary=issue_summary, urgency=urgency)
    return {
        "status": "success",
        "ticket": ticket,
    }


@mcp.tool(description="List available mock IT appointment slots.")
def list_it_appointments(limit: int = 5) -> dict:
    ensure_calendar_db()
    return {
        "status": "success",
        "slots": list_available_slots(limit=limit),
    }


@mcp.tool(description="Book a mock IT appointment slot.")
def book_it_appointment(slot_id: str, booked_for: str | None, issue_summary: str) -> dict:
    ensure_calendar_db()
    return book_slot(slot_id=slot_id, booked_for=booked_for, issue_summary=issue_summary)


if __name__ == "__main__":
    ensure_user_db()
    ensure_calendar_db()
    mcp.run()

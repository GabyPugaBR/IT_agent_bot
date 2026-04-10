import json
from datetime import datetime, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
APPOINTMENTS_PATH = DATA_DIR / "appointments.json"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _generate_default_slots() -> list[dict]:
    base = datetime(2026, 4, 13, 9, 0)
    slots = []
    for day_offset in range(4):
        for hour_offset in [0, 2, 4]:
            start = base + timedelta(days=day_offset, hours=hour_offset)
            slots.append(
                {
                    "slot_id": f"slot-{len(slots) + 1:03d}",
                    "starts_at": start.isoformat(),
                    "location": "IT Help Desk",
                    "status": "available",
                    "booked_for": None,
                    "issue_summary": None,
                }
            )
    return slots


def ensure_calendar_db() -> None:
    _ensure_data_dir()
    if not APPOINTMENTS_PATH.exists():
        APPOINTMENTS_PATH.write_text(json.dumps(_generate_default_slots(), indent=2), encoding="utf-8")


def load_slots() -> list[dict]:
    ensure_calendar_db()
    return json.loads(APPOINTMENTS_PATH.read_text(encoding="utf-8"))


def save_slots(slots: list[dict]) -> None:
    ensure_calendar_db()
    APPOINTMENTS_PATH.write_text(json.dumps(slots, indent=2), encoding="utf-8")


def list_available_slots(limit: int = 5) -> list[dict]:
    slots = load_slots()
    available = [slot for slot in slots if slot["status"] == "available"]
    return available[:limit]


def book_slot(slot_id: str, booked_for: str | None, issue_summary: str) -> dict:
    slots = load_slots()
    for slot in slots:
        if slot["slot_id"] == slot_id:
            if slot["status"] != "available":
                return {
                    "status": "error",
                    "message": "That appointment slot is no longer available.",
                }
            slot["status"] = "booked"
            slot["booked_for"] = booked_for
            slot["issue_summary"] = issue_summary
            save_slots(slots)
            return {
                "status": "success",
                "appointment": slot,
            }

    return {
        "status": "error",
        "message": "Appointment slot not found.",
    }

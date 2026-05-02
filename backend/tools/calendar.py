import json
from datetime import datetime, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
APPOINTMENTS_PATH = DATA_DIR / "appointments.json"
BUSINESS_HOURS = (9, 11, 13, 15)
BUSINESS_DAYS_TO_GENERATE = 10
MINIMUM_AVAILABLE_SLOTS = 5
DEFAULT_LOCATION = "IT Help Desk"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _is_business_day(day: datetime) -> bool:
    return day.weekday() < 5


def _next_business_day(day: datetime) -> datetime:
    while not _is_business_day(day):
        day += timedelta(days=1)
    return day


def _generate_default_slots(now: datetime | None = None) -> list[dict]:
    now = now or datetime.now()
    day = _next_business_day(now.replace(hour=0, minute=0, second=0, microsecond=0))
    slots = []

    while len({slot["starts_at"][:10] for slot in slots}) < BUSINESS_DAYS_TO_GENERATE:
        if not _is_business_day(day):
            day += timedelta(days=1)
            continue

        for hour in BUSINESS_HOURS:
            start = day.replace(hour=hour, minute=0, second=0, microsecond=0)
            if start <= now:
                continue
            slots.append(
                {
                    "slot_id": f"slot-{len(slots) + 1:03d}",
                    "starts_at": start.isoformat(),
                    "location": DEFAULT_LOCATION,
                    "status": "available",
                    "booked_for": None,
                    "issue_summary": None,
                }
            )
        day += timedelta(days=1)

    return slots


def _parse_slot_start(slot: dict) -> datetime | None:
    try:
        return datetime.fromisoformat(slot["starts_at"])
    except (KeyError, TypeError, ValueError):
        return None


def _future_available_slots(slots: list[dict], now: datetime | None = None) -> list[dict]:
    now = now or datetime.now()
    future_slots = []
    for slot in slots:
        start = _parse_slot_start(slot)
        if start and start > now and slot.get("status") == "available":
            future_slots.append(slot)
    return sorted(future_slots, key=lambda slot: slot["starts_at"])


def _refresh_slots(slots: list[dict], now: datetime | None = None) -> list[dict]:
    now = now or datetime.now()
    booked_future_slots = []
    used_slot_ids = set()
    booked_start_times = set()

    for slot in slots:
        start = _parse_slot_start(slot)
        if not start or start <= now or slot.get("status") != "booked":
            continue
        booked_future_slots.append(slot)
        used_slot_ids.add(slot.get("slot_id"))
        booked_start_times.add(slot["starts_at"])

    refreshed_slots = booked_future_slots[:]
    next_slot_number = 1
    for slot in _generate_default_slots(now):
        if slot["starts_at"] in booked_start_times:
            continue
        while f"slot-{next_slot_number:03d}" in used_slot_ids:
            next_slot_number += 1
        slot["slot_id"] = f"slot-{next_slot_number:03d}"
        used_slot_ids.add(slot["slot_id"])
        refreshed_slots.append(slot)
        next_slot_number += 1

    return sorted(refreshed_slots, key=lambda slot: slot["starts_at"])


def ensure_calendar_db() -> None:
    _ensure_data_dir()
    if not APPOINTMENTS_PATH.exists():
        APPOINTMENTS_PATH.write_text(json.dumps(_generate_default_slots(), indent=2), encoding="utf-8")


def load_slots() -> list[dict]:
    ensure_calendar_db()
    try:
        slots = json.loads(APPOINTMENTS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        slots = []

    if len(_future_available_slots(slots)) < MINIMUM_AVAILABLE_SLOTS:
        slots = _refresh_slots(slots)
        save_slots(slots)

    return slots


def save_slots(slots: list[dict]) -> None:
    ensure_calendar_db()
    APPOINTMENTS_PATH.write_text(json.dumps(slots, indent=2), encoding="utf-8")


def list_available_slots(limit: int = 5) -> list[dict]:
    slots = load_slots()
    return _future_available_slots(slots)[:limit]


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

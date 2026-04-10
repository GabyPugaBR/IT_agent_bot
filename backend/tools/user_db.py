import json
import random
import string
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "data"
USERS_PATH = DATA_DIR / "synthetic_users.json"
TICKETS_PATH = DATA_DIR / "support_tickets.json"

PASSWORD_POLICIES = {
    "student": {
        "min_length": 12,
        "require_upper": True,
        "require_lower": True,
        "require_digit": True,
        "require_symbol": False,
        "reset_note": "Students should create a strong password with at least 12 characters.",
    },
    "teacher": {
        "min_length": 14,
        "require_upper": True,
        "require_lower": True,
        "require_digit": True,
        "require_symbol": True,
        "reset_note": "Teachers must use a strong password with uppercase, lowercase, numbers, and symbols.",
    },
    "staff": {
        "min_length": 14,
        "require_upper": True,
        "require_lower": True,
        "require_digit": True,
        "require_symbol": True,
        "reset_note": "Staff passwords must include uppercase, lowercase, numbers, and symbols.",
    },
    "admin": {
        "min_length": 16,
        "require_upper": True,
        "require_lower": True,
        "require_digit": True,
        "require_symbol": True,
        "reset_note": "Administrators require the strictest password policy and a mandatory password change after reset.",
    },
}


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _generate_password(role: str, seed_value: int) -> str:
    policy = PASSWORD_POLICIES[role]
    rng = random.Random(seed_value)

    required_chars = [
        rng.choice(string.ascii_uppercase),
        rng.choice(string.ascii_lowercase),
        rng.choice(string.digits),
    ]
    if policy["require_symbol"]:
        required_chars.append(rng.choice("!@#$%^&*"))

    charset = string.ascii_letters + string.digits
    if policy["require_symbol"]:
        charset += "!@#$%^&*"

    while len(required_chars) < policy["min_length"]:
        required_chars.append(rng.choice(charset))

    rng.shuffle(required_chars)
    return "".join(required_chars)


def _build_user_record(username: str, display_name: str, role: str, unit: str, seed_value: int) -> dict:
    email_domain = "constellations.edu" if role == "student" else "constellationsschool.org"
    return {
        "username": username,
        "display_name": display_name,
        "role": role,
        "unit": unit,
        "email": f"{username}@{email_domain}",
        "status": "active",
        "failed_attempts": 0,
        "must_change_password": False,
        "password": _generate_password(role, seed_value),
    }


def _generate_users() -> dict[str, dict]:
    users: dict[str, dict] = {}

    for idx in range(1, 101):
        username = f"student{idx}"
        users[username] = _build_user_record(
            username=username,
            display_name=f"Student {idx}",
            role="student",
            unit=f"Grade {(idx - 1) % 12 + 1}",
            seed_value=idx,
        )

    for idx in range(1, 21):
        username = f"teacher{idx}"
        users[username] = _build_user_record(
            username=username,
            display_name=f"Teacher {idx}",
            role="teacher",
            unit=f"Department {(idx - 1) % 5 + 1}",
            seed_value=1000 + idx,
        )

    for idx in range(1, 16):
        username = f"staff{idx}"
        users[username] = _build_user_record(
            username=username,
            display_name=f"Staff {idx}",
            role="staff",
            unit=f"Operations {(idx - 1) % 4 + 1}",
            seed_value=2000 + idx,
        )

    for idx in range(1, 6):
        username = f"admin{idx}"
        users[username] = _build_user_record(
            username=username,
            display_name=f"Admin {idx}",
            role="admin",
            unit="IT Leadership",
            seed_value=3000 + idx,
        )

    users["student1"]["status"] = "locked"
    users["teacher1"]["failed_attempts"] = 3
    return users


def ensure_user_db() -> None:
    _ensure_data_dir()
    if not USERS_PATH.exists():
        USERS_PATH.write_text(json.dumps(_generate_users(), indent=2), encoding="utf-8")
    if not TICKETS_PATH.exists():
        TICKETS_PATH.write_text("[]", encoding="utf-8")


def load_users() -> dict[str, dict]:
    ensure_user_db()
    return json.loads(USERS_PATH.read_text(encoding="utf-8"))


def save_users(users: dict[str, dict]) -> None:
    ensure_user_db()
    USERS_PATH.write_text(json.dumps(users, indent=2), encoding="utf-8")


def find_user(username: str) -> dict | None:
    users = load_users()
    return users.get(username.lower())


def get_password_policy(role: str) -> dict:
    normalized_role = role if role in PASSWORD_POLICIES else "student"
    return PASSWORD_POLICIES[normalized_role]


def generate_temporary_password(role: str, seed_value: int | None = None) -> str:
    policy = get_password_policy(role)
    rng_seed = seed_value if seed_value is not None else random.randint(10_000, 99_999)
    return _generate_password("student" if role not in PASSWORD_POLICIES else role, rng_seed + policy["min_length"])


def create_ticket(username: str | None, issue_summary: str, urgency: str = "normal") -> dict:
    ensure_user_db()
    tickets = json.loads(TICKETS_PATH.read_text(encoding="utf-8"))
    ticket_number = len(tickets) + 1
    ticket = {
        "ticket_id": f"IT-{ticket_number:04d}",
        "username": username,
        "issue_summary": issue_summary,
        "urgency": urgency,
        "status": "open",
    }
    tickets.append(ticket)
    TICKETS_PATH.write_text(json.dumps(tickets, indent=2), encoding="utf-8")
    return ticket

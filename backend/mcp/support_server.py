import base64
import html
import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from mcp.server.fastmcp import FastMCP

CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from tools.password_reset import reset_password
from tools.calendar import book_slot, ensure_calendar_db, list_available_slots
from tools.user_db import create_ticket, ensure_user_db, find_user, get_password_policy

mcp = FastMCP("constellations-support")
CONFLUENCE_EXPORT_PATH = BACKEND_DIR / "data" / "confluence_pages.json"


class _ConfluenceHTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in {"p", "br", "div", "li", "h1", "h2", "h3", "h4", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)

    def get_text(self) -> str:
        collapsed = " ".join(self.parts)
        collapsed = re.sub(r"\s*\n\s*", "\n", collapsed)
        collapsed = re.sub(r"\n{2,}", "\n\n", collapsed)
        collapsed = re.sub(r"[ \t]{2,}", " ", collapsed)
        return html.unescape(collapsed).strip()


def _normalize_confluence_base_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}"


def _configured_page_ids() -> list[str]:
    raw_page_ids = os.getenv("CONFLUENCE_PAGE_IDS", "")
    return [page_id.strip() for page_id in raw_page_ids.split(",") if page_id.strip()]


def _load_mock_confluence_pages() -> dict:
    pages = json.loads(CONFLUENCE_EXPORT_PATH.read_text(encoding="utf-8"))
    return {
        "status": "success",
        "source": "mock_confluence",
        "pages": pages,
    }


def _strip_confluence_storage_html(storage_html: str) -> str:
    stripper = _ConfluenceHTMLStripper()
    stripper.feed(storage_html)
    return stripper.get_text()


def _fetch_confluence_page(base_url: str, email: str, api_token: str, page_id: str) -> dict:
    auth_token = base64.b64encode(f"{email}:{api_token}".encode("utf-8")).decode("utf-8")
    request = Request(
        url=(
            f"{base_url}/wiki/rest/api/content/{page_id}"
            "?expand=body.storage,title,space,_links"
        ),
        headers={
            "Accept": "application/json",
            "Authorization": f"Basic {auth_token}",
        },
        method="GET",
    )

    with urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))

    storage_html = payload.get("body", {}).get("storage", {}).get("value", "")
    page_base_url = payload.get("_links", {}).get("base") or f"{base_url}/wiki"
    webui_path = payload.get("_links", {}).get("webui", "")
    return {
        "id": payload.get("id", page_id),
        "title": payload.get("title", f"Confluence Page {page_id}"),
        "space": payload.get("space", {}).get("name", "Confluence"),
        "url": f"{page_base_url}{webui_path}" if webui_path else None,
        "content": _strip_confluence_storage_html(storage_html),
    }


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


@mcp.tool(description="Fetch mock Confluence knowledge pages for IT support grounding.")
def fetch_confluence_pages() -> dict:
    email = os.getenv("ATLASSIAN_EMAIL")
    api_token = os.getenv("ATLASSIAN_API_TOKEN")
    base_url = _normalize_confluence_base_url(os.getenv("CONFLUENCE_BASE_URL"))
    page_ids = _configured_page_ids()

    if not all([email, api_token, base_url, page_ids]):
        return _load_mock_confluence_pages()

    pages = []
    errors = []
    for page_id in page_ids:
        try:
            pages.append(_fetch_confluence_page(base_url, email, api_token, page_id))
        except HTTPError as exc:
            errors.append(f"HTTP {exc.code} for page {page_id}")
        except URLError as exc:
            errors.append(f"Network error for page {page_id}: {exc.reason}")
        except Exception as exc:
            errors.append(f"Unexpected error for page {page_id}: {exc}")

    if not pages:
        fallback = _load_mock_confluence_pages()
        fallback["message"] = "Live Confluence fetch failed; using bundled fallback knowledge."
        fallback["errors"] = errors
        return fallback

    return {
        "status": "success",
        "source": "confluence_cloud",
        "pages": pages,
        "errors": errors,
    }


if __name__ == "__main__":
    ensure_user_db()
    ensure_calendar_db()
    mcp.run()

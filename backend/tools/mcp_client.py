import json
import os
import sys
from pathlib import Path

import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VENV_PYTHON = PROJECT_ROOT / ".venv" / "bin" / "python"
PYTHON_PATH = (
    Path(os.environ["MCP_PYTHON_PATH"])
    if os.environ.get("MCP_PYTHON_PATH")
    else DEFAULT_VENV_PYTHON
)
SERVER_PATH = PROJECT_ROOT / "mcp" / "support_server.py"
NULL_DEVICE = open(os.devnull, "w", encoding="utf-8")


def _resolve_python_command() -> str:
    if PYTHON_PATH.exists():
        return str(PYTHON_PATH)

    # In Docker and many hosted environments there is no project-level .venv.
    return sys.executable


def _extract_result_payload(result) -> dict:
    if getattr(result, "structuredContent", None):
        return result.structuredContent

    if getattr(result, "content", None):
        text_parts = []
        for item in result.content:
            text_value = getattr(item, "text", None)
            if text_value:
                text_parts.append(text_value)
        combined_text = "\n".join(text_parts)
        try:
            parsed = json.loads(combined_text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        return {
            "status": "success",
            "message": combined_text,
        }

    return {
        "status": "error",
        "message": "No tool output returned from MCP server.",
    }


async def _call_tool_async(tool_name: str, arguments: dict) -> dict:
    server_parameters = StdioServerParameters(
        command=_resolve_python_command(),
        args=[str(SERVER_PATH)],
        cwd=str(PROJECT_ROOT),
    )

    async with stdio_client(server_parameters, errlog=NULL_DEVICE) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)
            payload = _extract_result_payload(result)
            if getattr(result, "isError", False):
                payload["status"] = "error"
            return payload


def call_tool(tool_name: str, arguments: dict) -> dict:
    return anyio.run(_call_tool_async, tool_name, arguments)


def reset_user_password_via_mcp(username: str) -> dict:
    return call_tool("reset_user_password", {"username": username})


def lookup_user_via_mcp(username: str) -> dict:
    return call_tool("lookup_user", {"username": username})


def create_support_ticket_via_mcp(username: str | None, issue_summary: str, urgency: str = "normal") -> dict:
    return call_tool(
        "create_support_ticket",
        {
            "username": username,
            "issue_summary": issue_summary,
            "urgency": urgency,
        },
    )


def list_it_appointments_via_mcp(limit: int = 5) -> dict:
    return call_tool("list_it_appointments", {"limit": limit})


def book_it_appointment_via_mcp(slot_id: str, booked_for: str | None, issue_summary: str) -> dict:
    return call_tool(
        "book_it_appointment",
        {
            "slot_id": slot_id,
            "booked_for": booked_for,
            "issue_summary": issue_summary,
        },
    )


def fetch_confluence_pages_via_mcp() -> dict:
    return call_tool("fetch_confluence_pages", {})

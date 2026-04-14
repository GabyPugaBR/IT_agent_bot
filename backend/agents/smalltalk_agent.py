import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from agents.prompts import SMALLTALK_PROMPT

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SMALLTALK_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4.1-mini")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) if os.getenv("OPENAI_API_KEY") else None


def smalltalk_agent(state):
    user_input = state["user_input"]
    history = state.get("conversation_history", [])
    metadata = state.get("metadata", {})

    consecutive_smalltalk = metadata.get("consecutive_smalltalk_turns", 0) + 1

    recent_history = history[-4:]
    transcript = "\n".join(
        f"{msg['role']}: {msg['content']}"
        for msg in recent_history
    ) or "No previous conversation."

    redirect_note = ""
    if consecutive_smalltalk >= 2:
        redirect_note = " The user has been chatting casually for a couple of turns now — gently but clearly redirect them to ask about their IT support needs."

    if client is None:
        return {
            **state,
            "agent_used": "smalltalk",
            "intent": "smalltalk",
            "response": "Hey there! I'm your Constellations School IT assistant. What IT help can I get you today?",
            "needs_escalation": False,
            "metadata": {**metadata, "consecutive_smalltalk_turns": consecutive_smalltalk},
        }

    try:
        response = client.responses.create(
            model=SMALLTALK_MODEL,
            input=[
                {"role": "system", "content": SMALLTALK_PROMPT + redirect_note},
                {"role": "user", "content": (
                    f"Conversation so far:\n{transcript}\n\n"
                    f"Current message: {user_input}"
                )},
            ],
        )
        reply = response.output_text.strip()
    except Exception:
        reply = "I'm here to help with IT support at Constellations School! What can I assist you with today?"

    return {
        **state,
        "agent_used": "smalltalk",
        "intent": "smalltalk",
        "response": reply,
        "needs_escalation": False,
        "metadata": {**metadata, "consecutive_smalltalk_turns": consecutive_smalltalk},
    }

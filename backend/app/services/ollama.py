import json
import re
from typing import Any

import httpx

from app.memory import MAX_TURNS, history

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2"

SYSTEM_PROMPT = (
    "You are an intent classifier for a customer support assistant. "
    "Classify the user's latest message into exactly one of these intents: "
    "order_tracking, refund_request, complaint, escalation, hotel_search, flight_search, capabilities. "
    "Use capabilities when the user asks what the assistant can do, its features, or how to use it. "
    "Use the conversation history to resolve follow-up questions — always match the intent of the previous topic. "
    '(e.g. "show cheaper ones" after a hotel search is hotel_search; '
    '"show cheaper ones" after a flight search is flight_search). '
    'Respond ONLY with valid JSON: {"intent": "<intent_name>"}'
)


def _extract_json(text: str) -> dict[str, Any]:
    """Parse JSON from LLM output, tolerating extra surrounding text."""
    try:
        return dict(json.loads(text.strip()))
    except (json.JSONDecodeError, ValueError):
        pass
    match = re.search(r'\{[^}]+\}', text)
    if match:
        try:
            return dict(json.loads(match.group()))
        except (json.JSONDecodeError, ValueError):
            pass
    return {}


async def classify_intent(message: str) -> str:
    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += history[-MAX_TURNS * 2:]
    messages.append({"role": "user", "content": message})

    payload: dict[str, Any] = {
        "model": MODEL,
        "messages": messages,
        "format": "json",
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(OLLAMA_URL, json=payload)
        r.raise_for_status()
        content: str = r.json()["message"]["content"]

    result = _extract_json(content)
    intent = result.get("intent", "")
    return str(intent) if intent else ""

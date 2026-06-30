import json
import re
from datetime import date as _date, timedelta
from typing import Any

import httpx

from app.memory import MAX_TURNS, history

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "llama3.2"

# The prompt constrains the model to a fixed set of intents and JSON-only output.
# The example pairs (hotel→hotel, flight→flight) are necessary — without them
# the model defaults to hotel_search for any "cheaper" follow-up regardless of context.
INTENT_PROMPT = (
    "You are an intent classifier for a customer support assistant. "
    "Classify the user's latest message into exactly one of these intents: "
    "order_tracking, refund_request, complaint, escalation, hotel_search, flight_search, capabilities. "
    "Use capabilities when the user asks what the assistant can do, its features, or how to use it. "
    "Use the conversation history to resolve follow-up questions — always match the intent of the previous topic. "
    '(e.g. "show cheaper ones" after a hotel search is hotel_search; '
    '"show cheaper ones" after a flight search is flight_search). '
    'Respond ONLY with valid JSON: {"intent": "<intent_name>"}'
)

# Common city names → IATA codes for when Ollama returns a full city name
_CITY_TO_IATA: dict[str, str] = {
    "dubai": "DXB", "london": "LHR", "mumbai": "BOM", "bombay": "BOM",
    "new york": "JFK", "paris": "CDG", "frankfurt": "FRA", "singapore": "SIN",
    "istanbul": "IST", "doha": "DOH", "abu dhabi": "AUH", "cairo": "CAI",
    "sharjah": "SHJ", "amsterdam": "AMS", "toronto": "YYZ", "sydney": "SYD",
    "bangkok": "BKK", "hong kong": "HKG", "tokyo": "NRT", "delhi": "DEL",
    "new delhi": "DEL", "karachi": "KHI", "lahore": "LHE", "riyadh": "RUH",
    "jeddah": "JED", "kuwait": "KWI", "muscat": "MCT", "colombo": "CMB",
    "nairobi": "NBO", "johannesburg": "JNB", "manchester": "MAN",
    "milan": "MXP", "rome": "FCO", "madrid": "MAD", "barcelona": "BCN",
    "zurich": "ZRH", "vienna": "VIE", "brussels": "BRU", "lisbon": "LIS",
    "athens": "ATH", "moscow": "SVO", "shanghai": "PVG", "beijing": "PEK",
    "osaka": "KIX", "kuala lumpur": "KUL", "jakarta": "CGK", "manila": "MNL",
    "seoul": "ICN", "lagos": "LOS", "bahrain": "BAH",
}


# --- Low-level helpers -------------------------------------------------------

def _tomorrow() -> str:
    return (_date.today() + timedelta(days=1)).strftime("%Y%m%d")


def _extract_json(text: str) -> dict[str, Any]:
    """Parse JSON from model output. Falls back to regex if wrapped in prose."""
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


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# --- Output normalisers (clean up Ollama's raw field values) -----------------

def _resolve_airport(value: Any) -> str | None:
    if not value:
        return None
    v = str(value).strip()
    if len(v) <= 4 and v.replace(" ", "").isalpha():
        return v.upper()
    iata = _CITY_TO_IATA.get(v.lower())
    if iata:
        return iata
    match = re.search(r'\b([A-Z]{3})\b', v.upper())
    return match.group(1) if match else None


def _resolve_cabin(value: Any) -> str | None:
    if not value:
        return None
    first = str(value).strip()[0].lower()
    return first if first in {"e", "p", "b", "f"} else None


def _resolve_direct(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip().lower()
    if s.startswith("1") or s in {"true", "yes", "nonstop", "direct"}:
        return "1"
    if s.startswith("0") or s in {"false", "no", "connections", "any"}:
        return "0"
    return None


# --- Ollama calls ------------------------------------------------------------

async def _call_ollama(messages: list[dict[str, str]], json_mode: bool = True, timeout: int = 60) -> str:
    """Send a message list to Ollama and return the raw content string."""
    payload: dict[str, Any] = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
    }
    if json_mode:
        payload["format"] = "json"
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(OLLAMA_URL, json=payload)
        r.raise_for_status()
        return str(r.json()["message"]["content"])


async def classify_intent(message: str) -> str:
    messages = (
        [{"role": "system", "content": INTENT_PROMPT}]
        + history[-MAX_TURNS * 2:]
        + [{"role": "user", "content": message}]
    )
    content = await _call_ollama(messages, json_mode=True)
    result  = _extract_json(content)
    intent  = result.get("intent", "")
    return str(intent) if intent else ""


async def extract_flight_params(message: str) -> dict[str, Any]:
    today = _date.today().strftime("%Y-%m-%d")
    year  = today[:4]

    system_prompt = (
        f"Today's date is {today}. "
        "Extract flight search parameters from the full conversation history and latest message. "
        "Look across EVERY previous turn — if the user mentioned a value earlier it still applies. "
        "Respond ONLY with valid JSON. Use exactly these keys and value formats:\n"
        f'{{"origin": "DXB", "destination": "BOM", "date": "{year}1005", '
        '"adult": 1, "infant": 0, "children": 0, "cabin": "e", "direct": "1"}}\n'
        "origin/destination: 3-letter IATA airport code only (e.g. DXB, LHR, BOM). "
        "cabin: exactly one letter — e, p, b, or f. "
        "direct: exactly '1' for nonstop, '0' for any. "
        f"date: YYYYMMDD using {year} as the year unless the user stated otherwise. "
        "Use null for any field not mentioned anywhere in the conversation."
    )
    messages = (
        [{"role": "system", "content": system_prompt}]
        + history[-MAX_TURNS * 2:]
        + [{"role": "user", "content": message}]
    )
    content = await _call_ollama(messages, json_mode=True)
    result  = _extract_json(content)

    raw_date       = str(result.get("date") or "").replace("-", "").replace("/", "")
    validated_date = raw_date if (len(raw_date) == 8 and raw_date >= _tomorrow()) else None

    return {
        "origin":      _resolve_airport(result.get("origin")),
        "destination": _resolve_airport(result.get("destination")),
        "date":        validated_date,
        "adult":       _safe_int(result.get("adult"), 1),
        "infant":      _safe_int(result.get("infant"), 0),
        "children":    _safe_int(result.get("children"), 0),
        "cabin":       _resolve_cabin(result.get("cabin")),
        "direct":      _resolve_direct(result.get("direct")),
    }


async def summarise_flights(flights: list[dict[str, Any]]) -> str:
    snippet = json.dumps(flights[:8], indent=2)
    system_prompt = (
        "You are a helpful travel assistant. Given flight search results, "
        "write a single friendly sentence summarising the number of results and price range. "
        "Example: 'I found 6 flights from DXB to LHR — prices range from $183 to $750.' "
        "Be concise, no bullet points."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": f"Flight results:\n{snippet}"},
    ]
    try:
        return await _call_ollama(messages, json_mode=False, timeout=30)
    except Exception:
        return "Available flights found."

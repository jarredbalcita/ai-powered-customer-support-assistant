# Mock tools — each returns (ui_type, message, data).
# No external calls are made here; all data is static and predefined.

from collections.abc import Callable, Coroutine
from typing import Any, Union

# ToolResult: (ui_type string, human-readable message, data payload for the widget)
ToolResult = tuple[str, str, dict[str, Any]]
ToolFn = Union[Callable[[str], ToolResult], Callable[[str], Coroutine[Any, Any, ToolResult]]]


# --- Single-record tools -----------------------------------------------------

def tracking_tool(_msg: str) -> ToolResult:
    return "tracking_page", "Here is your order status.", {
        "order_id": "ORD-7823",
        "status": "Out for delivery",
        "eta": "Today, 6 PM",
        "carrier": "FastShip",
        "last_location": "Local warehouse",
    }


def refund_tool(_msg: str) -> ToolResult:
    return "refund_page", "Your refund has been initiated.", {
        "refund_id": "RF-456",
        "amount": "$50.00",
        "status": "Processing",
        "estimated_days": "3-5 business days",
    }


def complaint_tool(_msg: str) -> ToolResult:
    return "complaint_page", "Your complaint has been logged.", {
        "ticket_id": "CMP-789",
        "status": "Open",
        "priority": "Medium",
        "note": "Our team will review your complaint within 24 hours.",
    }


def escalation_tool(_msg: str) -> ToolResult:
    return "escalation_page", "Your issue has been escalated to senior support.", {
        "ticket_id": "ESC-101",
        "assigned_to": "Senior Support",
        "expected_response": "Within 2 hours",
    }


def capabilities_tool(_msg: str) -> ToolResult:
    return "text", (
        "Here's what I can help you with:\n\n"
        "- Track an order — ask about your order status or delivery\n"
        "- Request a refund — ask to return an item or get your money back\n"
        "- Log a complaint — let us know if something went wrong\n"
        "- Escalate an issue — ask to speak to a senior agent or manager\n"
        "- Search hotels — ask for hotels in any city\n"
        "- Search flights — ask for available flights to a destination\n\n"
        "Just type your question and I'll take care of the rest!"
    ), {}


# --- Static data for list-based tools ----------------------------------------

_HOTELS: list[dict[str, Any]] = [
    {"name": "The Ritz-Carlton",     "price": "$538", "rating": 4.9, "location": "Downtown Dubai"},
    {"name": "Marriott City Centre", "price": "$263", "rating": 4.6, "location": "Business Bay"},
    {"name": "Hilton Garden Inn",    "price": "$183", "rating": 4.3, "location": "Al Barsha"},
    {"name": "Premier Inn",          "price": "$110", "rating": 4.1, "location": "Bur Dubai"},
    {"name": "Holiday Inn Express",  "price": "$93",  "rating": 3.9, "location": "Deira"},
    {"name": "Ibis Styles",          "price": "$65",  "rating": 3.7, "location": "Al Qusais"},
    {"name": "Atlantis The Palm",    "price": "$720", "rating": 4.8, "location": "Palm Jumeirah"},
    {"name": "Four Seasons Resort",  "price": "$598", "rating": 4.9, "location": "Jumeirah Beach"},
    {"name": "Hyatt Regency",        "price": "$247", "rating": 4.5, "location": "Corniche"},
    {"name": "Novotel World Trade",  "price": "$155", "rating": 4.2, "location": "Trade Centre"},
]


def _cheapest(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # strip the leading $ before comparing so "$110" sorts correctly
    sorted_items = sorted(items, key=lambda x: int(str(x["price"]).strip("$")))
    return sorted_items[:3]


def hotel_tool(msg: str) -> ToolResult:
    hotels = _cheapest(_HOTELS) if "cheap" in msg.lower() else _HOTELS
    return "hotel_page", "Available hotels found.", {"hotels": hotels}


# Human-readable labels for each required flight field — used in clarifying questions
_REQUIRED_FLIGHT_FIELDS: dict[str, str] = {
    "origin":      "where you're flying from (e.g. 'Dubai' or 'DXB')",
    "destination": "your destination (e.g. 'London' or 'LHR')",
    "date":        "the travel date (e.g. 'October 24th' or '2026-10-24')",
    "cabin":       "your preferred cabin class (economy, business, first, etc.)",
    "direct":      "whether you want direct flights only, or connections are okay",
}


async def flight_tool(msg: str) -> ToolResult:
    from app.services.ollama import extract_flight_params, summarise_flights
    from app.services.flight_api import search_flights

    try:
        params = await extract_flight_params(msg)
    except Exception as e:
        print(f"[flight_tool] param extraction error: {e}")
        return "text", "Sorry, I couldn't process your request. Please try again.", {}

    # Check which required fields are still missing
    missing = [f for f in _REQUIRED_FLIGHT_FIELDS if not params.get(f)]
    if missing:
        labels = [_REQUIRED_FLIGHT_FIELDS[f] for f in missing]
        question = "To search for flights, I still need:\n" + "\n".join(f"• {l}" for l in labels)
        return "text", question, {}

    try:
        flights = await search_flights(
            origin=params["origin"],
            destination=params["destination"],
            date=params["date"],
            cabin=params["cabin"],
            adult=params.get("adult", 1),
            infant=params.get("infant", 0),
            children=params.get("children", 0),
            direct=params.get("direct", "0"),
        )
    except Exception as e:
        print(f"[flight_tool] search error: {e}")
        return "text", "Sorry, I couldn't fetch flights right now. Please try again.", {}

    if not flights:
        return "text", "No flights found for that route.", {}

    if "cheap" in msg.lower():
        flights = sorted(flights, key=lambda f: float(f["price"].strip("$")))[:3]

    summary = await summarise_flights(flights)
    return "flight_page", summary, {"flights": flights}


# intent → (tool name, callable); extend here to add new intents
TOOLS: dict[str, tuple[str, ToolFn]] = {
    "order_tracking": ("tracking_tool", tracking_tool),
    "refund_request": ("refund_tool", refund_tool),
    "complaint": ("complaint_tool", complaint_tool),
    "escalation": ("escalation_tool", escalation_tool),
    "hotel_search": ("hotel_tool", hotel_tool),
    "flight_search": ("flight_tool", flight_tool),
    "capabilities": ("capabilities_tool", capabilities_tool),
}

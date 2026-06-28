from collections.abc import Callable
from typing import Any

ToolResult = tuple[str, str, dict[str, Any]]
ToolFn = Callable[[str], ToolResult]


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


def escalation_tool(_msg: str) -> ToolResult:
    return "escalation_page", "Your issue has been escalated to senior support.", {
        "ticket_id": "ESC-101",
        "assigned_to": "Senior Support",
        "expected_response": "Within 2 hours",
    }


_HOTELS: list[dict[str, Any]] = [
    {"name": "The Ritz-Carlton",       "price": "$540", "rating": 4.9, "location": "Downtown Dubai"},
    {"name": "Marriott City Centre",   "price": "$280", "rating": 4.6, "location": "Business Bay"},
    {"name": "Hilton Garden Inn",      "price": "$175", "rating": 4.3, "location": "Al Barsha"},
    {"name": "Premier Inn",            "price": "$110", "rating": 4.1, "location": "Bur Dubai"},
    {"name": "Holiday Inn Express",    "price": "$90",  "rating": 3.9, "location": "Deira"},
    {"name": "Ibis Styles",            "price": "$65",  "rating": 3.7, "location": "Al Qusais"},
    {"name": "Atlantis The Palm",      "price": "$720", "rating": 4.8, "location": "Palm Jumeirah"},
    {"name": "Four Seasons Resort",    "price": "$610", "rating": 4.9, "location": "Jumeirah Beach"},
    {"name": "Hyatt Regency",          "price": "$230", "rating": 4.5, "location": "Corniche"},
    {"name": "Novotel World Trade",    "price": "$155", "rating": 4.2, "location": "Trade Centre"},
]


_FLIGHTS: list[dict[str, Any]] = [
    {"airline": "Emirates",       "from": "DXB", "to": "LHR", "price": "$520", "duration": "7h 30m",  "departure": "02:30"},
    {"airline": "British Airways","from": "LHR", "to": "DXB", "price": "$480", "duration": "7h 15m",  "departure": "09:15"},
    {"airline": "Etihad",         "from": "AUH", "to": "JFK", "price": "$670", "duration": "14h 10m", "departure": "08:05"},
    {"airline": "Qatar Airways",  "from": "DOH", "to": "CDG", "price": "$390", "duration": "6h 20m",  "departure": "14:45"},
    {"airline": "Lufthansa",      "from": "FRA", "to": "DXB", "price": "$410", "duration": "6h 45m",  "departure": "11:20"},
    {"airline": "FlyDubai",       "from": "DXB", "to": "IST", "price": "$195", "duration": "4h 00m",  "departure": "06:50"},
    {"airline": "Air Arabia",     "from": "SHJ", "to": "CAI", "price": "$130", "duration": "3h 10m",  "departure": "16:30"},
    {"airline": "United Airlines", "from": "JFK", "to": "DXB", "price": "$750", "duration": "13h 50m", "departure": "22:10"},
    {"airline": "Singapore Air",  "from": "SIN", "to": "DXB", "price": "$310", "duration": "7h 00m",  "departure": "23:55"},
    {"airline": "Turkish Airlines","from": "IST", "to": "DXB", "price": "$260", "duration": "4h 15m",  "departure": "07:40"},
]


def _cheapest(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sorted_items = sorted(items, key=lambda x: int(str(x["price"]).strip("$")))
    return sorted_items[:3]


def hotel_tool(msg: str) -> ToolResult:
    hotels = _cheapest(_HOTELS) if "cheap" in msg.lower() else _HOTELS
    return "hotel_page", "Available hotels found.", {"hotels": hotels}


def flight_tool(msg: str) -> ToolResult:
    flights = _cheapest(_FLIGHTS) if "cheap" in msg.lower() else _FLIGHTS
    return "flight_page", "Available flights found.", {"flights": flights}


# Registry mapping intent name → (tool_function_name, callable).
# Add new intents here without touching any other file.
TOOLS: dict[str, tuple[str, ToolFn]] = {
    "order_tracking": ("tracking_tool",    tracking_tool),
    "refund_request": ("refund_tool",      refund_tool),
    "complaint":      ("complaint_tool",   complaint_tool),
    "escalation":     ("escalation_tool",  escalation_tool),
    "hotel_search":   ("hotel_tool",       hotel_tool),
    "flight_search":  ("flight_tool",      flight_tool),
    "capabilities":   ("capabilities_tool", capabilities_tool),
}

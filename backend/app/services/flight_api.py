import asyncio
import time
from typing import Any

import httpx

BASE_URL = "https://test.flightapi.jadwelny.com"
SEARCH_URL = f"{BASE_URL}/flight/search-id/fetch"
POLL_URL   = f"{BASE_URL}/flight/search"
HEADERS    = {"Content-Type": "application/json", "Accept": "application/json"}
MAX_POLLS  = 10


# --- Helpers -----------------------------------------------------------------

#def _minutes_to_hm(minutes: Any) -> str:
#    try:
#        m = int(minutes)
#        return f"{m // 60}h {m % 60}m"
#    except (TypeError, ValueError):
#        return "N/A"


def _time_part(datetime_str: str) -> str:
    """Extract HH:MM from a datetime string like '2026/10/05 13:50'."""
    parts = (datetime_str or "").split(" ")
    return parts[1] if len(parts) == 2 else datetime_str


def _map_flight(raw: dict[str, Any]) -> dict[str, Any]:
    """Map one raw API flight object to the shape Flutter expects."""
    leg       = raw["legs"][0]
    first_seg = leg["segments"][0]
    last_seg  = leg["segments"][-1]

    # Sum segment durations for actual air time — leg.duration includes layover waits
    #air_minutes = sum(int(s.get("duration") or 0) for s in leg.get("segments", []))
    #duration    = _minutes_to_hm(air_minutes) if air_minutes > 0 else _minutes_to_hm(leg.get("duration"))

    return {
        "airline":    first_seg.get("iata", ""),
        "from":       first_seg.get("from", {}).get("airport", ""),
        "to":         last_seg.get("to", {}).get("airport", ""),
        "price":      f"${raw['price']:.0f}",
        #"duration":   duration,
        "departure":  _time_part(first_seg.get("from", {}).get("date", "")),
        "arrival":    _time_part(last_seg.get("to", {}).get("date", "")),
        "stops":      len(leg.get("stops", [])),
        "refundable": raw.get("can_refund", False),
    }


# --- API calls ---------------------------------------------------------------

async def search_flights(
    origin: str,
    destination: str,
    date: str,
    cabin: str = "e",
    adult: int = 1,
    infant: int = 0,
    children: int = 0,
    direct: str = "0",
) -> list[dict[str, Any]]:
    date = date.replace("-", "").replace("/", "") # Normalize date 

    payload: dict[str, Any] = {
        "trip":     [{"origin": origin.upper(), "destination": destination.upper(), "date": date}], # API supports multi-city trips
        "adult":    adult,
        "infant":   infant,
        "children": children,
        "cabin":    cabin,
        "direct":   direct,
    }
    print(f"[flight_api] POST {SEARCH_URL}  payload={payload}")

    async with httpx.AsyncClient(timeout=30, follow_redirects=False) as client:
        r = await client.post(SEARCH_URL, json=payload, headers=HEADERS)
        print(f"[flight_api] step-1 response {r.status_code}: {r.text[:200]}")
        r.raise_for_status()
        search_id = r.json()["data"]["search_id"]

    print(f"[flight_api] polling search_id={search_id}")

    after = None
    async with httpx.AsyncClient(timeout=30) as client:
        for attempt in range(1, MAX_POLLS + 1):
            poll_url = f"{POLL_URL}/{search_id}"
            if after:
                poll_url += f"?after={after}"

            r = await client.get(poll_url)
            r.raise_for_status()
            body = r.json()
            complete = body.get("complete", 0)
            print(f"[flight_api] poll {attempt}/{MAX_POLLS}  complete={complete}%")

            if complete == 100:
                results = body.get("result", [])
                shortened_results = results[:10] if len(results) > 10 else results
                print(f"[flight_api] done — {len(results)} flights returned. Showing top results.")
                return [_map_flight(f) for f in shortened_results] # Shows 10 results, if less than 20, shows all results

            after = int(time.time() * 1000)
            await asyncio.sleep(1)

    print("[flight_api] timed out waiting for complete=100")
    return []

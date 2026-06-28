# Pydantic models for the /chat endpoint.
# ChatResponse is the contract the Flutter frontend depends on —
# changing field names here requires matching updates in main.dart.

from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    intent: str          # classified intent name, e.g. "hotel_search"
    tool_called: str     # name of the function that ran
    ui_type: str         # tells the frontend which widget to render
    message: str         # human-readable summary shown in the chat bubble
    data: dict[str, Any] # payload consumed by the widget

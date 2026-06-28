from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    intent: str
    tool_called: str
    ui_type: str
    message: str
    data: dict[str, Any]

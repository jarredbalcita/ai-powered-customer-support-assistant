from fastapi import APIRouter

from app.memory import update_history
from app.schemas import ChatRequest, ChatResponse
from app.services.ollama import classify_intent
from app.tools import TOOLS

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    try:
        intent = await classify_intent(req.message)
    except Exception as e:
        print("classify error:", e)
        intent = ""

    if intent not in TOOLS:
        fallback = "Sorry, I didn't understand that. Try asking about orders, refunds, hotels, or flights."
        update_history(req.message, fallback)
        return ChatResponse(
            intent="unknown", tool_called="none", ui_type="text",
            message=fallback, data={},
        )

    tool_name, tool_fn = TOOLS[intent]
    ui_type, msg, data = tool_fn(req.message)
    update_history(req.message, msg)

    return ChatResponse(
        intent=intent, tool_called=tool_name,
        ui_type=ui_type, message=msg, data=data,
    )

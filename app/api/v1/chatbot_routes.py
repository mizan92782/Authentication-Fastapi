from fastapi import APIRouter, Depends
from app.chatbot.chatbot_service import handle_chat
from app.core.dependencies import get_current_user
from app.schemas.chatbot import ChatRequest, ChatResponse
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/chatbot", tags=["AI Chatbot"])


@router.post("/chat", response_model=SuccessResponse[ChatResponse])
async def chat(data: ChatRequest, current_user=Depends(get_current_user)):
    reply = await handle_chat(current_user, data.message)
    return SuccessResponse(data=ChatResponse(reply=reply))

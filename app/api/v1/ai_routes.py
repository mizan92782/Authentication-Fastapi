from typing import Optional
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from app.modules.ai.service import chat
from app.shared.responses.api_response import SuccessResponse
from app.core.dependencies import get_optional_user
from app.core.limiter import limiter

ai_router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class AskRequest(BaseModel):
    question: str
    category: Optional[str] = None
    history: list[Message] = []


class AskResponse(BaseModel):
    answer: str
    history: list[Message]


@ai_router.post(
    "/ask/",
    response_model=SuccessResponse[AskResponse],
    summary="Chat with AI assistant",
    description="Ask about products, place orders, or cancel orders. Login required for order actions. Pass returned `history` for follow-up questions.",
)
@limiter.limit("20/minute")
async def ask_ai(
    request: Request,
    data: AskRequest,
    current_user=Depends(get_optional_user),
):
    history = [m.model_dump() for m in data.history]
    answer, updated_history = await chat(
        question=data.question,
        history=history or None,
        category=data.category,
        user=current_user,
    )
    return SuccessResponse(data=AskResponse(
        answer=answer,
        history=[Message(**m) for m in updated_history if isinstance(m.get("content"), str)],
    ))

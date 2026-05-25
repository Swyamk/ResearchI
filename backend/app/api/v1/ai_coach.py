"""
AI Coach API routes: Gemini-powered conversational nutrition coaching.
"""
import uuid
from typing import AsyncGenerator, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import desc, select

from app.core.dependencies import DB, CurrentUser, ai_rate_limit
from app.models.user import AIConversation
from app.services.gemini_service import GeminiService

router = APIRouter()


class ChatMessage(BaseModel):
    message: str
    session_id: Optional[str] = None
    context_type: Optional[str] = None
    # "meal_analysis" | "daily_summary" | "weekly_summary" | "general"


class ChatResponse(BaseModel):
    response: str
    session_id: str
    tokens_used: Optional[int]
    suggestions: Optional[List[str]]


class ConversationMessage(BaseModel):
    role: str
    content: str
    created_at: str


@router.post("/chat", response_model=ChatResponse)
async def chat_with_coach(
    payload: ChatMessage,
    current_user: CurrentUser,
    db: DB,
    _: None = Depends(ai_rate_limit),
):
    """
    Chat with the Gemini AI Nutrition Coach.
    Powered by Gemini 2.5 Pro with full conversation history and user context.
    """
    session_id = payload.session_id or str(uuid.uuid4())

    service = GeminiService(db)
    result = await service.chat(
        user=current_user,
        message=payload.message,
        session_id=session_id,
        context_type=payload.context_type,
    )

    return ChatResponse(
        response=result["response"],
        session_id=session_id,
        tokens_used=result.get("tokens_used"),
        suggestions=result.get("suggestions"),
    )


@router.get("/chat/stream")
async def stream_chat(
    message: str,
    current_user: CurrentUser,
    db: DB,
    session_id: Optional[str] = Query(None),
    _: None = Depends(ai_rate_limit),
):
    """Stream AI Coach response using Server-Sent Events."""
    sid = session_id or str(uuid.uuid4())
    service = GeminiService(db)

    async def event_generator() -> AsyncGenerator[str, None]:
        async for chunk in service.stream_chat(
            user=current_user,
            message=message,
            session_id=sid,
        ):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/history")
async def get_conversation_history(
    current_user: CurrentUser,
    db: DB,
    session_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    """Get conversation history with the AI Coach."""
    query = select(AIConversation).where(AIConversation.user_id == current_user.id)
    if session_id:
        query = query.where(AIConversation.session_id == session_id)
    query = query.order_by(desc(AIConversation.created_at)).limit(limit)

    result = await db.execute(query)
    messages = result.scalars().all()

    return {
        "messages": [
            ConversationMessage(
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at.isoformat(),
            )
            for msg in reversed(messages)
        ],
        "session_id": session_id,
    }


@router.post("/summary/daily")
async def generate_daily_summary(
    current_user: CurrentUser,
    db: DB,
    _: None = Depends(ai_rate_limit),
):
    """Generate an intelligent daily nutrition summary using Gemini AI."""
    service = GeminiService(db)
    summary = await service.generate_daily_summary(current_user)
    return {"summary": summary, "type": "daily"}


@router.post("/summary/weekly")
async def generate_weekly_summary(
    current_user: CurrentUser,
    db: DB,
    _: None = Depends(ai_rate_limit),
):
    """Generate an intelligent weekly nutrition summary using Gemini AI."""
    service = GeminiService(db)
    summary = await service.generate_weekly_summary(current_user)
    return {"summary": summary, "type": "weekly"}


@router.post("/summary/monthly")
async def generate_monthly_summary(
    current_user: CurrentUser,
    db: DB,
    _: None = Depends(ai_rate_limit),
):
    """Generate an intelligent monthly nutrition report using Gemini AI."""
    service = GeminiService(db)
    summary = await service.generate_monthly_summary(current_user)
    return {"summary": summary, "type": "monthly"}


@router.websocket("/ws/{session_id}")
async def websocket_chat(
    websocket: WebSocket,
    session_id: str,
    db: DB,
):
    """WebSocket endpoint for real-time AI chat."""
    await websocket.accept()
    service = GeminiService(db)

    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            user_id = data.get("user_id")

            if not message:
                continue

            # Stream response back over WebSocket
            async for chunk in service.stream_chat_ws(
                user_id=user_id,
                message=message,
                session_id=session_id,
            ):
                await websocket.send_json({"chunk": chunk, "done": False})

            await websocket.send_json({"chunk": "", "done": True})

    except WebSocketDisconnect:
        pass

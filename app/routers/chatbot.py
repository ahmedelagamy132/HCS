"""
Chatbot API endpoints.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.schemas.chatbot import (
    ChatRequest,
    ChatResponse,
    HistoryResponse,
    HistorySummary,
    ClearHistoryResponse,
    ChatMessage,
    ModeRequest,
    ModeResponse,
)
from app.services.chatbot_service import ChatbotService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chatbot", tags=["Chatbot"])

chatbot_service = ChatbotService()


def _mode_label(use_rag: bool, use_sensors: bool, use_behavior: bool) -> str:
    if not use_rag and not use_sensors and not use_behavior:
        return "llm-only"
    if use_rag and use_sensors and use_behavior:
        return "full"
    if use_rag and not use_sensors and not use_behavior:
        return "rag-only"
    if not use_rag and use_sensors and not use_behavior:
        return "minimal"
    if not use_sensors:
        return "vision"
    if not use_behavior:
        return "sensors"
    return "custom"


@router.get("/mode", response_model=ModeResponse)
async def get_mode():
    try:
        info = chatbot_service.get_mode()
        return ModeResponse(
            use_rag=info["use_rag"],
            use_sensors=info["use_sensors"],
            use_behavior=info["use_behavior"],
            status=info["status"],
            mode_label=_mode_label(info["use_rag"], info["use_sensors"], info["use_behavior"]),
        )
    except Exception as e:
        logger.error(f"get_mode error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mode", response_model=ModeResponse)
async def set_mode(request: ModeRequest):
    try:
        chatbot_service.set_mode(
            use_rag=request.use_rag,
            use_sensors=request.use_sensors,
            use_behavior=request.use_behavior,
        )
        info = chatbot_service.get_mode()
        return ModeResponse(
            use_rag=info["use_rag"],
            use_sensors=info["use_sensors"],
            use_behavior=info["use_behavior"],
            status=info["status"],
            mode_label=_mode_label(info["use_rag"], info["use_sensors"], info["use_behavior"]),
        )
    except Exception as e:
        logger.error(f"set_mode error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        logger.info(f"Chat [{_mode_label(request.use_rag, request.use_sensors, request.use_behavior)}] "
                    f"{request.question[:60]}…")

        response = chatbot_service.get_response(
            question=request.question,
            use_rag=request.use_rag,
            use_sensors=request.use_sensors,
            use_behavior=request.use_behavior,
        )
        summary = chatbot_service.get_history_summary()

        return ChatResponse(
            status="success",
            response=response,
            question=request.question,
            message_count=summary["total_messages"],
            use_rag=request.use_rag,
            use_sensors=request.use_sensors,
            use_behavior=request.use_behavior,
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat-stream")
async def chat_stream(request: ChatRequest):
    """Stream the AI response in real-time."""
    try:
        logger.info(f"Stream [{_mode_label(request.use_rag, request.use_sensors, request.use_behavior)}] "
                    f"{request.question[:60]}…")

        def generate():
            for chunk in chatbot_service.get_response_stream_with_mode(
                question=request.question,
                use_rag=request.use_rag,
                use_sensors=request.use_sensors,
                use_behavior=request.use_behavior,
            ):
                yield chunk

        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control":    "no-cache",
                "Connection":       "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=HistoryResponse)
async def get_history(full: bool = False):
    try:
        summary_data = chatbot_service.get_history_summary()
        summary = HistorySummary(**summary_data)
        messages = None
        if full:
            history = chatbot_service.get_full_history()
            messages = [ChatMessage(**msg) for msg in history]
        return HistoryResponse(status="success", summary=summary, messages=messages)
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-history", response_model=ClearHistoryResponse)
async def clear_history():
    try:
        success = chatbot_service.clear_history()
        return ClearHistoryResponse(
            status="success" if success else "error",
            message="History cleared successfully" if success else "Failed to clear history",
            cleared=success,
        )
    except Exception as e:
        logger.error(f"Clear history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    try:
        mode = chatbot_service.get_mode()
        summary = chatbot_service.get_history_summary()
        return {
            "status":        "healthy",
            "service":       "chatbot",
            "message_count": summary["total_messages"],
            "mode":          mode,
        }
    except Exception as e:
        return {"status": "unhealthy", "service": "chatbot", "error": str(e)}

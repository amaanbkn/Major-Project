"""
FinSight AI — Chat Router
POST /api/chat — Streaming conversational interface with agentic orchestration.
"""

import json
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

router = APIRouter()


class ChatRequest(BaseModel):
    """Chat request schema."""
    message: str
    user_id: str = "default"
    stream: bool = True


class ChatResponse(BaseModel):
    """Non-streaming chat response schema."""
    response: str
    reasoning_steps: list[str]
    intent: dict
    timestamp: str


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Main chat endpoint. Supports streaming (SSE) and non-streaming mode.

    Streaming mode (default):
    - Returns Server-Sent Events (SSE)
    - Event types: step, chunk, data, done, error

    Non-streaming mode:
    - Returns complete JSON response
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    logger.info(f"💬 Chat request from {request.user_id}: {request.message[:80]}")

    if request.stream:
        return StreamingResponse(
            _stream_response(request.message, request.user_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        # Non-streaming mode
        from agents.orchestrator import orchestrate

        result = await orchestrate(request.message, request.user_id)
        return ChatResponse(
            response=result.response,
            reasoning_steps=result.reasoning_steps,
            intent=result.intent,
            timestamp=result.to_dict()["timestamp"],
        )


async def _stream_response(message: str, user_id: str):
    """
    Generator for Server-Sent Events (SSE) streaming.
    Yields formatted SSE events from the orchestrator.
    """
    from agents.orchestrator import orchestrate_streaming

    try:
        async for event in orchestrate_streaming(message, user_id):
            event_type = event.get("type", "chunk")
            content = event.get("content", "")

            # Format as SSE
            if isinstance(content, dict):
                data = json.dumps({"type": event_type, "content": content})
            else:
                data = json.dumps({"type": event_type, "content": str(content)})

            yield f"data: {data}\n\n"

        # Send done event
        yield f"data: {json.dumps({'type': 'done', 'content': ''})}\n\n"

    except Exception as e:
        logger.error(f"Streaming error: {e}")
        error_data = json.dumps({"type": "error", "content": str(e)})
        yield f"data: {error_data}\n\n"


@router.get("/chat/history")
async def get_chat_history(user_id: str = "default", limit: int = 50):
    """Get chat history for a user."""
    import sqlite3
    import os

    db_path = os.getenv("SQLITE_DB_PATH", "./finsight.db")
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT role, content, timestamp FROM chat_history WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
        conn.close()

        return {
            "user_id": user_id,
            "messages": [
                {"role": r["role"], "content": r["content"], "timestamp": r["timestamp"]}
                for r in reversed(rows)
            ],
        }
    except Exception as e:
        logger.error(f"Chat history error: {e}")
        return {"user_id": user_id, "messages": []}

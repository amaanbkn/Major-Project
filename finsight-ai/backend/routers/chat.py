import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from pydantic import BaseModel

from dependencies import get_current_user


router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    user_id: str = "default"
    stream: bool = True


class ChatResponse(BaseModel):
    response: str
    reasoning_steps: list[str]
    intent: dict
    timestamp: str


def _sse(event: dict) -> str:
    return (
        f"data: "
        f"{json.dumps(event, ensure_ascii=False)}"
        f"\n\n"
    )


@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: str = Depends(
        get_current_user
    ),
):

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty.",
        )

    logger.info(
        f"💬 Chat request from {current_user}: "
        f"{request.message[:80]}"
    )

    # ========================================================
    # STREAMING
    # ========================================================

    if request.stream:

        async def event_stream():

            try:
                from agents.orchestrator import (
                    orchestrate_streaming,
                )

                # Send an immediate event so the frontend
                # knows the connection is alive.
                yield _sse({
                    "type": "step",
                    "content": "Starting FinSight AI...",
                })

                async for event in (
                    orchestrate_streaming(
                        query=request.message,
                        user_id=current_user,
                    )
                ):

                    if not isinstance(
                        event,
                        dict,
                    ):
                        continue

                    yield _sse(event)

            except Exception as exc:

                logger.exception(
                    f"❌ Streaming chat failed: {exc}"
                )

                yield _sse({
                    "type": "error",
                    "content": (
                        f"{type(exc).__name__}: "
                        f"{str(exc)}"
                    ),
                })

                yield _sse({
                    "type": "done",
                    "content": "",
                })

            finally:
                logger.info(
                    "🏁 Chat stream closed."
                )

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": (
                    "no-cache, no-transform"
                ),
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    # ========================================================
    # NON-STREAMING
    # ========================================================

    try:

        from agents.orchestrator import (
            orchestrate,
        )

        result = await orchestrate(
            request.message,
            current_user,
        )

        return ChatResponse(
            response=result.response,
            reasoning_steps=result.reasoning_steps,
            intent=result.intent,
            timestamp=result.to_dict()[
                "timestamp"
            ],
        )

    except Exception as exc:

        logger.exception(
            f"❌ Non-streaming chat failed: {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail=f"{type(exc).__name__}: {exc}",
        )
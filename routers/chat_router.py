from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from core.rag import get_chat_response, get_chat_response_stream
from schema.schema import ChatRequest, ChatResponse, CurrentUser
from core.auth import get_current_user
from core.session_memory import append as mem_append, recent as mem_recent, clear as mem_clear
import uuid
import logging
import json

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=ChatResponse)
async def chat_with_docs(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    基于文档的智能问答接口
    """
    try:
        session_id = request.session_id or uuid.uuid4().hex
        mem_append(session_id, "user", request.message)
        history_pairs = mem_recent(session_id, limit=8)
        response = await get_chat_response(request.message, current_user.id, history_pairs)
        mem_append(session_id, "assistant", response["answer"])
        logger.info("chat_answer", extra={"event": "chat_answer", "session_id": session_id, "history_len": len(history_pairs)})
        return ChatResponse(answer=response["answer"], sources=list(set(response["sources"])))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.post("/stream")
async def chat_with_docs_stream(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    session_id = request.session_id or uuid.uuid4().hex
    mem_append(session_id, "user", request.message)
    history_pairs = mem_recent(session_id, limit=8)

    async def gen():
        answer = ""
        try:
            sources, tokens = await get_chat_response_stream(request.message, current_user.id, history_pairs)
            yield json.dumps({"type": "start", "session_id": session_id, "sources": sources}, ensure_ascii=False) + "\n"
            async for t in tokens:
                answer += t
                yield json.dumps({"type": "token", "data": t}, ensure_ascii=False) + "\n"
            mem_append(session_id, "assistant", answer)
            logger.info(
                "chat_stream_done",
                extra={"event": "chat_stream_done", "session_id": session_id, "history_len": len(history_pairs)},
            )
            yield json.dumps({"type": "done"}, ensure_ascii=False) + "\n"
        except Exception as e:
            logger.exception("chat_stream_error", extra={"event": "chat_stream_error", "session_id": session_id})
            yield json.dumps({"type": "error", "error": str(e)}, ensure_ascii=False) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")

@router.post("/session/close")
async def close_session(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    mem_clear(session_id)
    return {"message": "session closed", "session_id": session_id}

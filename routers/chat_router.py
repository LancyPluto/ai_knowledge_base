from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from core.rag import get_chat_response, get_chat_response_stream
from schema.schema import ChatRequest, ChatResponse, CurrentUser
from core.auth import get_current_user
from core.database import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from repository.chat_repo import chat_repo
import uuid
import logging
import json
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/chat", tags=["Chat"])
logger = logging.getLogger(__name__)

class CreateSessionRequest(BaseModel):
    title: str = "新对话"

@router.get("/sessions")
async def get_sessions(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    sessions = await chat_repo.get_sessions_by_user(db, current_user.id)
    return [{"id": s.id, "title": s.title, "updated_at": s.updated_at} for s in sessions]

@router.post("/sessions")
async def create_session(
    req: CreateSessionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    session = await chat_repo.create_session(db, current_user.id, title=req.title)
    return {"id": session.id, "title": session.title}

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    session = await chat_repo.get_session_by_id(db, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    await chat_repo.delete_session(db, session_id)
    return {"message": "ok"}

@router.get("/sessions/{session_id}/messages")
async def get_messages(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    session = await chat_repo.get_session_by_id(db, session_id)
    if not session or session.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = await chat_repo.get_messages_by_session(db, session_id)
    return [{"id": m.id, "role": m.role, "content": m.content, "created_at": m.created_at} for m in messages]

@router.post("/stream")
async def chat_with_docs_stream(
    request: ChatRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    session_id = request.session_id
    if not session_id:
        # Auto create session if not provided
        session = await chat_repo.create_session(db, current_user.id, title=request.message[:15])
        session_id = session.id
    else:
        # Verify session ownership
        session = await chat_repo.get_session_by_id(db, session_id)
        if not session or session.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Session not found")
        # Update title if it's "新对话"
        if session.title == "新对话":
            session.title = request.message[:15]
            db.add(session)
            await db.commit()

    async def gen():
        try:
            sources, tokens = await get_chat_response_stream(request.message, current_user.id, session_id)
            yield json.dumps({"type": "start", "session_id": session_id, "sources": sources}, ensure_ascii=False) + "\n"
            async for t in tokens:
                yield json.dumps({"type": "token", "data": t}, ensure_ascii=False) + "\n"
            logger.info("chat_stream_done", extra={"event": "chat_stream_done", "session_id": session_id})
            yield json.dumps({"type": "done"}, ensure_ascii=False) + "\n"
        except Exception as e:
            logger.exception("chat_stream_error", extra={"event": "chat_stream_error", "session_id": session_id})
            yield json.dumps({"type": "error", "error": str(e)}, ensure_ascii=False) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")

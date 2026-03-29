from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import List, Optional
from models.chat import ChatSession, ChatMessage
from datetime import datetime

class ChatRepository:
    async def create_session(self, db: AsyncSession, user_id: str, title: str = "新对话") -> ChatSession:
        session = ChatSession(user_id=user_id, title=title)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def get_sessions_by_user(self, db: AsyncSession, user_id: str) -> List[ChatSession]:
        statement = select(ChatSession).where(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc())
        result = await db.scalars(statement)
        return list(result.all())

    async def get_session_by_id(self, db: AsyncSession, session_id: str) -> Optional[ChatSession]:
        return await db.get(ChatSession, session_id)

    async def delete_session(self, db: AsyncSession, session_id: str) -> None:
        session = await db.get(ChatSession, session_id)
        if session:
            stmt = select(ChatMessage).where(ChatMessage.session_id == session_id)
            msgs = await db.scalars(stmt)
            for m in msgs:
                await db.delete(m)
            await db.delete(session)
            await db.commit()

    async def add_message(self, db: AsyncSession, session_id: str, role: str, content: str) -> ChatMessage:
        msg = ChatMessage(session_id=session_id, role=role, content=content)
        db.add(msg)
        session = await db.get(ChatSession, session_id)
        if session:
            session.updated_at = datetime.utcnow()
            db.add(session)
        await db.commit()
        await db.refresh(msg)
        return msg

    async def get_messages_by_session(self, db: AsyncSession, session_id: str) -> List[ChatMessage]:
        statement = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at)
        result = await db.scalars(statement)
        return list(result.all())

chat_repo = ChatRepository()

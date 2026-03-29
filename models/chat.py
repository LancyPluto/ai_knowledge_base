from typing import Optional
from sqlmodel import SQLModel, Field, Column, String, DateTime
from datetime import datetime
import uuid

class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_session"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(sa_column=Column(String(36), index=True, nullable=False))
    title: str = Field(default="新对话", max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_message"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    session_id: str = Field(sa_column=Column(String(36), index=True, nullable=False))
    role: str = Field(sa_column=Column(String(20), nullable=False)) # 'user' or 'assistant'
    content: str = Field(sa_column=Column(String(10000), nullable=False))
    created_at: datetime = Field(default_factory=datetime.utcnow)

from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid
from sqlalchemy import Column, String


class User(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    username: str = Field(sa_column=Column(String(255), unique=True, index=True))
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

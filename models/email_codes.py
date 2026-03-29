from sqlmodel import SQLModel, Field
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import Column, String
import uuid


class EmailCode(SQLModel, table=True):
    __tablename__ = "email_code"
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    email: str = Field(sa_column=Column(String(255), index=True, nullable=False))
    code: str = Field(sa_column=Column(String(32), nullable=False))
    purpose: str = Field(sa_column=Column(String(32), index=True, nullable=False))
    expires_at: datetime
    used: bool = Field(default=False)

    @staticmethod
    def ttl_minutes() -> int:
        return 10

    @staticmethod
    def new_expiry() -> datetime:
        return datetime.utcnow() + timedelta(minutes=EmailCode.ttl_minutes())

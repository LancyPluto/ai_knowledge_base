from typing import Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    ephemeral: bool = False

class ChatResponse(BaseModel):
    answer: str
    sources: list[str]

    
class CurrentUser(BaseModel):
    id: str


class UserIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: str
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: bool


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EmailSendCodeIn(BaseModel):
    email: str
    purpose: str


class EmailRegisterIn(BaseModel):
    email: str
    password: str
    code: str


class EmailLoginIn(BaseModel):
    email: str
    password: str

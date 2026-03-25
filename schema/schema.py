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
    username: str
    is_active: bool


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

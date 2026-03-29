from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
import random
import string

from core.auth import create_access_token, hash_password, verify_password, get_current_user
from core.database import get_session
from models.users import User
from models.email_codes import EmailCode
from repository.user_repo import user_repo
from repository.email_code_repo import email_code_repo
from core.emailer import send_email
from schema.schema import UserIn, UserOut, TokenOut, CurrentUser, EmailSendCodeIn, EmailRegisterIn, EmailLoginIn

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut)
async def register(user_in: UserIn, db: AsyncSession = Depends(get_session)):
    existing = await user_repo.get_by_username(db, username=user_in.username)
    if existing is not None:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
        is_active=True,
    )
    user = await user_repo.create_user(db, user=user)
    return UserOut(id=user.id, username=user.username, email=user.email, is_active=user.is_active)


@router.post("/login", response_model=TokenOut)
async def login(user_in: UserIn, db: AsyncSession = Depends(get_session)):
    user = await user_repo.get_by_username(db, username=user_in.username)
    if user is None or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="User disabled")

    token = create_access_token(user_id=user.id)
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
async def me(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    user = await user_repo.get_by_id(db, user_id=current_user.id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return UserOut(id=user.id, username=user.username, email=user.email, is_active=user.is_active)

def _gen_code(n: int = 6) -> str:
    return "".join(random.choices(string.digits, k=n))


@router.post("/send_code")
async def send_code(data: EmailSendCodeIn, db: AsyncSession = Depends(get_session)):
    if data.purpose not in {"register", "login"}:
        raise HTTPException(status_code=400, detail="invalid purpose")
    code = _gen_code(6)
    rec = EmailCode(email=data.email, code=code, purpose=data.purpose, expires_at=EmailCode.new_expiry())
    await email_code_repo.create(db, rec=rec)
    ok = send_email(data.email, "验证码", f"你的验证码是：{code}，{EmailCode.ttl_minutes()}分钟内有效。")
    if not ok:
        raise HTTPException(status_code=500, detail="send code failed")
    return {"message": "ok"}


@router.post("/register_email", response_model=UserOut)
async def register_email(data: EmailRegisterIn, db: AsyncSession = Depends(get_session)):
    rec = await email_code_repo.get_valid(db, email=data.email, purpose="register")
    if not rec or rec.code != data.code:
        raise HTTPException(status_code=400, detail="invalid code")
    exist = await user_repo.get_by_email(db, email=data.email)
    if exist:
        raise HTTPException(status_code=400, detail="email already exists")
    user = User(email=data.email, username=None, hashed_password=hash_password(data.password), is_active=True)
    user = await user_repo.create_user(db, user=user)
    await email_code_repo.mark_used(db, rec=rec)
    return UserOut(id=user.id, username=user.username, email=user.email, is_active=user.is_active)


@router.post("/login_email", response_model=TokenOut)
async def login_email(data: EmailLoginIn, db: AsyncSession = Depends(get_session)):
    user = await user_repo.get_by_email(db, email=data.email)
    if user is None or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User disabled")
    token = create_access_token(user_id=user.id)
    return TokenOut(access_token=token)

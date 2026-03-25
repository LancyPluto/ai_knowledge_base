from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from core.auth import create_access_token, hash_password, verify_password, get_current_user
from core.database import get_session
from models.users import User
from repository.user_repo import user_repo
from schema.schema import UserIn, UserOut, TokenOut, CurrentUser

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
    return UserOut(id=user.id, username=user.username, is_active=user.is_active)


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

    return UserOut(id=user.id, username=user.username, is_active=user.is_active)

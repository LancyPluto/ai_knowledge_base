from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from models.users import User


class UserRepo:
    async def get_by_username(self, db: AsyncSession, *, username: str) -> User | None:
        statement = select(User).where(User.username == username)
        return (await db.scalars(statement)).first()

    async def get_by_email(self, db: AsyncSession, *, email: str) -> User | None:
        statement = select(User).where(User.email == email)
        return (await db.scalars(statement)).first()

    async def get_by_id(self, db: AsyncSession, *, user_id: str) -> User | None:
        return await db.get(User, user_id)

    async def create_user(self, db: AsyncSession, *, user: User) -> User:
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user


user_repo = UserRepo()

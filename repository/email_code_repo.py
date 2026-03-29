from datetime import datetime
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from models.email_codes import EmailCode


class EmailCodeRepo:
    async def create(self, db: AsyncSession, *, rec: EmailCode) -> EmailCode:
        db.add(rec)
        await db.commit()
        await db.refresh(rec)
        return rec

    async def get_valid(self, db: AsyncSession, *, email: str, purpose: str) -> EmailCode | None:
        stmt = (
            select(EmailCode)
            .where(EmailCode.email == email, EmailCode.purpose == purpose, EmailCode.used == False)  # noqa: E712
            .order_by(EmailCode.expires_at.desc())
        )
        res = await db.scalars(stmt)
        rec = res.first()
        if rec and rec.expires_at > datetime.utcnow():
            return rec
        return None

    async def mark_used(self, db: AsyncSession, *, rec: EmailCode) -> None:
        rec.used = True
        await db.commit()


email_code_repo = EmailCodeRepo()

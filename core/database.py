from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from core.config import settings

# 创建异步引擎，使用 .env 中的 MYSQL_URL
# 注意：SQLModel 暂未原生支持异步 session，通常需要结合 sqlalchemy.ext.asyncio
engine = create_async_engine(settings.MYSQL_URL, echo=True, future=True)


# 定义一个 FastAPI 依赖项，用于获取数据库会话
async def get_session() -> AsyncSession:
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session

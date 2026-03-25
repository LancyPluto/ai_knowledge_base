from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from models.documents import Document

class DocRepo:
    """封装文档元数据的数据库操作"""

    async def create_document(self, db: AsyncSession, *, doc_in: Document) -> Document:
        """创建一个新的文档记录"""
        db.add(doc_in)
        await db.commit()
        await db.refresh(doc_in)
        return doc_in

    async def get_documents_by_user(self, db: AsyncSession, *, user_id: str) -> list[Document]:
        """根据用户ID获取其所有文档"""
        statement = select(Document).where(Document.user_id == user_id)
        result = await db.scalars(statement)
        return result.all()

    async def get_by_id(self, db: AsyncSession, *, doc_id: int) -> Document | None:
        return await db.get(Document, doc_id)

    async def delete_document(self, db: AsyncSession, *, doc: Document) -> None:
        await db.delete(doc)
        await db.commit()

# 实例化一个全局可用的 repo 对象
doc_repo = DocRepo()

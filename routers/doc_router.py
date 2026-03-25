import os
import shutil
import uuid
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging

from core.database import get_session, engine
from core.auth import CurrentUser, get_current_user
from core.vector_db import get_vector_store, delete_vectors_by_doc_id
from models.documents import Document
from repository.doc_repo import doc_repo
from utils.file_processor import process_file

router = APIRouter(prefix="/docs", tags=["Documents"])
logger = logging.getLogger(__name__)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def process_and_save_to_vector_db(doc_id: int, filepath: str, user_id: str, delete_existing_vectors: bool = False):
    """
    后台处理任务：分片、向量化并存储到 ChromaDB
    """
    # 为后台任务创建独立的数据库会话
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        if delete_existing_vectors:
            delete_vectors_by_doc_id(doc_id=doc_id, user_id=user_id)

        # 1. 解析分片
        chunks = process_file(filepath)
        
        # 2. 为每个分片添加元数据，用于多租户隔离和溯源
        for chunk in chunks:
            chunk.metadata["user_id"] = user_id
            chunk.metadata["doc_id"] = doc_id
            chunk.metadata["source"] = os.path.basename(filepath)

        # 3. 获取向量库实例并存入
        vector_store = get_vector_store()
        vector_store.add_documents(chunks)
        logger.info(
            "doc_vector_store_add",
            extra={"event": "doc_vector_store_add", "doc_id": doc_id, "user_id": user_id, "chunks": len(chunks)},
        )

        # 4. 更新 MySQL 中的文档状态为已完成
        async with AsyncSessionLocal() as db:
            doc = await db.get(Document, doc_id)
            if doc:
                doc.status = "COMPLETED"
                doc.error_message = None
                doc.updated_at = datetime.utcnow()
                await db.commit()
        
        logger.info("doc_processed", extra={"event": "doc_processed", "doc_id": doc_id, "user_id": user_id})

    except Exception as e:
        # 如果出错，更新状态为失败
        async with AsyncSessionLocal() as db:
            doc = await db.get(Document, doc_id)
            if doc:
                doc.status = "FAILED"
                doc.error_message = str(e)[:1000]
                doc.updated_at = datetime.utcnow()
                await db.commit()
        logger.exception("doc_process_failed", extra={"event": "doc_process_failed", "doc_id": doc_id, "user_id": user_id})

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    1. 保存文件到本地
    2. 存入 MySQL 记录
    3. 启动后台异步处理任务 (分片 + 向量化)
    """
    # 校验文件后缀
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".md", ".txt", ".docx"]:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    # 生成唯一文件名防止冲突
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    # 1. 物理保存文件
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # 2. 写入 MySQL 元数据记录
    new_doc = Document(
        filename=file.filename,
        file_path=file_path,
        user_id=current_user.id,
        status="PROCESSING",
        error_message=None,
        updated_at=datetime.utcnow(),
    )
    db_doc = await doc_repo.create_document(db, doc_in=new_doc)

    # 3. 启动后台异步处理任务
    logger.info("doc_upload", extra={"event": "doc_upload", "doc_id": db_doc.id, "user_id": current_user.id, "file_name": file.filename})
    background_tasks.add_task(process_and_save_to_vector_db, db_doc.id, file_path, current_user.id, False)

    return {
        "message": "File uploaded and processing started",
        "doc_id": db_doc.id,
        "filename": db_doc.filename
    }

@router.get("/")
async def list_my_documents(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    列出当前用户的所有文档列表
    """
    docs = await doc_repo.get_documents_by_user(db, user_id=current_user.id)
    return docs


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    doc = await doc_repo.get_by_id(db, doc_id=doc_id)
    if doc is None or doc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        delete_vectors_by_doc_id(doc_id=doc.id, user_id=current_user.id)
    except Exception:
        logger.exception("doc_vector_delete_failed", extra={"event": "doc_vector_delete_failed", "doc_id": doc_id, "user_id": current_user.id})

    if doc.file_path and os.path.exists(doc.file_path):
        try:
            os.remove(doc.file_path)
        except Exception:
            logger.exception("doc_file_delete_failed", extra={"event": "doc_file_delete_failed", "doc_id": doc_id, "user_id": current_user.id})

    await doc_repo.delete_document(db, doc=doc)
    logger.info("doc_deleted", extra={"event": "doc_deleted", "doc_id": doc_id, "user_id": current_user.id})
    return {"message": "Document deleted"}


@router.put("/{doc_id}/reupload")
async def reupload_document(
    doc_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    doc = await doc_repo.get_by_id(db, doc_id=doc_id)
    if doc is None or doc.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Document not found")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".pdf", ".md", ".txt", ".docx"]:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    old_file_path = doc.file_path
    doc.filename = file.filename
    doc.file_path = file_path
    doc.status = "PROCESSING"
    doc.error_message = None
    doc.updated_at = datetime.utcnow()
    db.add(doc)
    await db.commit()

    if old_file_path and os.path.exists(old_file_path):
        try:
            os.remove(old_file_path)
        except Exception:
            pass

    background_tasks.add_task(process_and_save_to_vector_db, doc.id, file_path, current_user.id, True)
    logger.info("doc_reupload", extra={"event": "doc_reupload", "doc_id": doc.id, "user_id": current_user.id, "file_name": file.filename})

    return {"message": "File reuploaded and processing started", "doc_id": doc.id, "filename": doc.filename}

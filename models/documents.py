from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime


class Document(SQLModel, table=True):
    """
    文档模型
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(index=True, description="文件名")
    file_path: str = Field(description="文件路径")
    user_id: str = Field(index=True, description="所属用户的唯一标识")
    status: str = Field(default="PENDING", description="文档处理状态: PENDING, PROCESSING, COMPLETED, FAILED")
    error_message: Optional[str] = Field(default=None, description="失败原因")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")

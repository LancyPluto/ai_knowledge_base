from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "智能知识库"
    DEBUG: bool = False

    # AI 接口配置
    DEEPSEEK_API_KEY: str
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"

    # 数据库配置
    MYSQL_URL: str
    CHROMA_DB_PATH: str = "./chroma_db"

    # JWT 鉴权配置
    JWT_SECRET: str
    JWT_ALG: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASS: Optional[str] = None
    SMTP_FROM: Optional[str] = None

    # 使用 .env 文件读取环境变量 
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


# 实例化配置对象，供全局调用
settings = Settings()

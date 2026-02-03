# 应用配置（MVP 从环境变量读取，未来可加 .env）
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://coffee:coffee_secret@localhost:5432/coffee_trace"
    upload_dir: str = "uploads"
    # 未来鉴权预留
    # secret_key: str = ""
    # algorithm: str = "HS256"

    @property
    def database_url_sync(self) -> str:
        """Alembic 迁移用同步 URL"""
        return self.database_url.replace("+asyncpg", "")

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()

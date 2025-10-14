"""
应用配置管理
"""

from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基本信息
    app_name: str = "FastAPI Task Manager"
    version: str = "1.0.0"
    debug: bool = True
    
    # 数据库配置
    database_url: str = "sqlite:///./app.db"
    
    # JWT配置
    secret_key: str = "your-secret-key-here-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS配置
    backend_cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://localhost:8000"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
settings = Settings()

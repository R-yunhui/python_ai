"""
FastAPI应用程序主入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import create_tables
from .api import auth, users, tasks

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="一个基于FastAPI的任务管理系统",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """应用启动时的事件"""
    # 创建数据库表
    create_tables()


@app.get("/")
def read_root():
    """根路径"""
    return {
        "message": f"欢迎使用 {settings.app_name}",
        "version": settings.version,
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "healthy", "version": settings.version}


# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(users.router, prefix="/api/users", tags=["用户"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["任务"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )

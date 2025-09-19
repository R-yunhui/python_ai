# FastAPI Web接口开发示例
# 类似于Java中的Spring Boot，FastAPI是Python中用于构建高性能API的现代Web框架

import logging
from datetime import datetime
from typing import List, Optional, Any

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, status, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 配置CORS中间件
# 类似于Java Spring中的 @CrossOrigin 注解
from starlette.middleware import Middleware

# 配置中间件
origins = ["*"]  # 生产环境中应该指定具体域名
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
]

# 创建FastAPI应用实例
# 类似于Java Spring Boot中的 @SpringBootApplication
app = FastAPI(
    title="用户管理API",  # API文档标题
    description="一个简单的用户管理系统API示例",  # API描述
    version="1.0.0",  # API版本
    middleware=middleware  # 使用middleware参数配置中间件
)


# 数据模型定义（使用Pydantic）
# 类似于Java中的实体类(Entity)或DTO类
class User(BaseModel):
    """用户模型 - 类似于Java中的User实体类"""
    id: Optional[int] = None
    name: str = Field(..., min_length=2, max_length=50, description="用户姓名")
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$', description="邮箱地址")
    age: int = Field(..., ge=0, le=150, description="年龄")
    created_at: Optional[datetime] = None


class UserCreate(BaseModel):
    """创建用户请求模型"""
    name: str = Field(..., min_length=2, max_length=50)
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: int = Field(..., ge=0, le=150)


class UserUpdate(BaseModel):
    """更新用户请求模型"""
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[str] = Field(None, pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
    age: Optional[int] = Field(None, ge=0, le=150)


class ApiResponse(BaseModel):
    """API响应模型 - 类似于Java中的统一响应格式"""
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None


# 模拟数据库（实际项目中应使用真实数据库）
# 类似于Java中的Repository层或Service层的数据存储
users_db: List[User] = [
    User(id=1, name="张三", email="zhangsan@example.com", age=25, created_at=datetime.now()),
    User(id=2, name="李四", email="lisi@example.com", age=30, created_at=datetime.now())
]
next_user_id = 3


# API路由定义
# 类似于Java Spring中的 @RestController 和 @RequestMapping

@app.get("/", summary="根路径")
async def read_root():
    """根路径接口 - 类似于Java中的健康检查接口"""
    return ApiResponse(
        message="FastAPI用户管理系统运行正常",
        data={"version": "1.0.0", "timestamp": datetime.now()}
    )


@app.get("/users", response_model=ApiResponse, summary="获取所有用户")
async def get_all_users():
    """获取所有用户列表 - 类似于Java中的 @GetMapping("/users")"""
    return ApiResponse(
        message="获取用户列表成功",
        data=users_db
    )


@app.get("/users/{user_id}", response_model=ApiResponse, summary="根据ID获取用户")
async def get_user(user_id: int):
    """根据ID获取单个用户 - 类似于Java中的 @GetMapping("/users/{id}")"""
    user = next((u for u in users_db if u.id == user_id), None)
    if not user:
        # 抛出HTTP异常 - 类似于Java中抛出自定义异常
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户ID {user_id} 不存在"
        )
    return ApiResponse(
        message="获取用户成功",
        data=user
    )


@app.post("/users", response_model=ApiResponse, summary="创建新用户")
async def create_user(user: UserCreate):
    """创建新用户 - 类似于Java中的 @PostMapping("/users")"""
    global next_user_id

    # 检查邮箱是否已存在
    if any(u.email == user.email for u in users_db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱地址已存在"
        )

    # 创建新用户对象
    new_user = User(
        id=next_user_id,
        name=user.name,
        email=user.email,
        age=user.age,
        created_at=datetime.now()
    )

    users_db.append(new_user)
    next_user_id += 1

    return ApiResponse(
        code=201,
        message="用户创建成功",
        data=new_user
    )


@app.put("/users/{user_id}", response_model=ApiResponse, summary="更新用户信息")
async def update_user(user_id: int, user_update: UserUpdate):
    """更新用户信息 - 类似于Java中的 @PutMapping("/users/{id}")"""
    logging.info(f"更新用户ID: {user_id}, 数据: {user_update}")
    
    # 检查用户是否存在
    user = next((u for u in users_db if u.id == user_id), None)
    if not user:
        logging.warning(f"用户ID {user_id} 不存在")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户ID {user_id} 不存在"
        )

    # 检查邮箱是否已被其他用户使用
    update_data = user_update.model_dump(exclude_unset=True)
    if "email" in update_data:
        email_exists = any(u.email == update_data["email"] and u.id != user_id for u in users_db)
        if email_exists:
            logging.warning(f"邮箱 {update_data['email']} 已被其他用户使用")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱地址已被其他用户使用"
            )

    # 更新用户信息（只更新提供的字段）
    for field, value in update_data.items():
        setattr(user, field, value)
    
    logging.info(f"用户ID {user_id} 更新成功")
    return ApiResponse(
        message="用户更新成功",
        data=user
    )


@app.delete("/users/{user_id}", response_model=ApiResponse, summary="删除用户")
async def delete_user(user_id: int):
    """删除用户 - 类似于Java中的 @DeleteMapping("/users/{id}")"""
    global users_db
    user = next((u for u in users_db if u.id == user_id), None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户ID {user_id} 不存在"
        )

    users_db = [u for u in users_db if u.id != user_id]

    return ApiResponse(
        message="用户删除成功",
        data={"deleted_user_id": user_id}
    )


# 查询参数示例
@app.get("/users/search", response_model=ApiResponse, summary="搜索用户")
async def search_users(
        name: Optional[str] = None,
        min_age: Optional[int] = None,
        max_age: Optional[int] = None
):
    """根据条件搜索用户 - 演示查询参数的使用"""
    filtered_users = users_db

    if name:
        filtered_users = [u for u in filtered_users if name.lower() in u.name.lower()]
    if min_age is not None:
        filtered_users = [u for u in filtered_users if u.age >= min_age]
    if max_age is not None:
        filtered_users = [u for u in filtered_users if u.age <= max_age]

    return ApiResponse(
        message=f"找到 {len(filtered_users)} 个用户",
        data=filtered_users
    )


# 依赖注入示例（模拟身份验证）
# 类似于Java Spring中的 @Autowired 或依赖注入
def get_current_user(token: str = Header(None, description="认证令牌")):
    """模拟获取当前用户（实际项目中应该验证JWT token）"""
    logging.info(f"验证用户令牌: {token}")
    if not token or token != "admin":
        logging.warning(f"无效的认证令牌: {token}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return {"username": "admin", "role": "administrator"}


@app.get("/protected", response_model=ApiResponse, summary="受保护的接口")
async def protected_route(current_user: dict = Depends(get_current_user)):
    """演示依赖注入和身份验证"""
    return ApiResponse(
        message="访问受保护资源成功",
        data={
            "user": current_user,
            "message": "这是一个需要认证的接口"
        }
    )


# 异常处理示例
@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """全局异常处理 - 类似于Java中的 @ExceptionHandler"""
    print(f"请求：", request)
    return ApiResponse(
        code=400,
        message=f"数据验证错误: {str(exc)}",
        data=None
    )


if __name__ == "__main__":
    # 启动服务器
    # 类似于Java Spring Boot中的 SpringApplication.run()
    logging.info("启动FastAPI服务器...")
    print("启动FastAPI服务器...")
    print("API文档地址: http://127.0.0.1:8000/docs")
    print("交互式文档地址: http://127.0.0.1:8000/redoc")

    uvicorn.run(
        "fast_api:app",  # 使用当前文件名:应用实例名称
        host="127.0.0.1",  # 监听地址
        port=8000,  # 监听端口
        reload=True  # 开发模式，代码变更自动重载
    )

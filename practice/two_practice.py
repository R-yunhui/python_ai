# ============================================================
# FastAPI 学习示例 - 用户管理 CRUD API
# ============================================================
# FastAPI 类似于 Java 的 Spring Boot，是一个现代化的 Web 框架
# 特点：自动生成 API 文档、类型验证、异步支持、高性能

from typing import Any, Optional, List, Dict
from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel, EmailStr, Field

# ============================================================
# 1. 创建 FastAPI 应用实例
# ============================================================
# 类似于 Spring Boot 的 @SpringBootApplication
# title: API 文档标题
# description: API 描述
# version: API 版本
app = FastAPI(
    title="用户管理系统 API",
    description="一个简单的用户 CRUD 操作示例",
    version="1.0.0"
)


# ============================================================
# 2. Pydantic 模型定义 (类似 Java 的 DTO/Entity)
# ============================================================
# Pydantic 是 FastAPI 的核心，用于数据验证和序列化
# 类似于 Java 的 Bean Validation (@Valid, @NotNull 等)

class UserBase(BaseModel):
    """
    用户基础模型 - 用于创建和更新用户时的数据验证
    类似于 Java 的 DTO (Data Transfer Object)
    """
    name: str = Field(..., min_length=1, max_length=50, description="用户名称")
    age: int = Field(..., ge=0, le=150, description="用户年龄")
    gender: str = Field(..., pattern="^(男|女|其他)$", description="用户性别")
    email: EmailStr = Field(..., description="用户邮箱")

    class Config:
        # 配置示例数据，会显示在 API 文档中
        json_schema_extra = {
            "example": {
                "name": "张三",
                "age": 25,
                "gender": "男",
                "email": "zhangsan@example.com"
            }
        }


class UserCreate(UserBase):
    """
    创建用户模型 - 继承自 UserBase
    可以在这里添加创建时特有的字段
    """
    pass


class UserUpdate(BaseModel):
    """
    更新用户模型 - 所有字段都是可选的
    类似于 Java 的 PATCH 请求，允许部分更新
    """
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    age: Optional[int] = Field(None, ge=0, le=150)
    gender: Optional[str] = Field(None, pattern="^(男|女|其他)$")
    email: Optional[EmailStr] = None


class UserResponse(UserBase):
    """
    用户响应模型 - 包含 user_id
    类似于 Java 的 Entity，包含数据库生成的 ID
    """
    user_id: int = Field(..., description="用户ID")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "name": "张三",
                "age": 25,
                "gender": "男",
                "email": "zhangsan@example.com"
            }
        }


# ============================================================
# 3. 数据存储层 (模拟数据库)
# ============================================================
# 在实际项目中，这里会使用 SQLAlchemy ORM 或其他数据库
# 类似于 Java 的 JPA/Hibernate

class User:
    """
    用户实体类 - 类似于 Java 的 Entity
    """

    def __init__(self, user_id: int, name: str, age: int, gender: str, email: EmailStr):
        self.user_id = user_id
        self.name = name
        self.age = age
        self.gender = gender
        self.email = email

    def __str__(self):
        return f"User(user_id={self.user_id}, name={self.name}, age={self.age}, gender={self.gender}, email={self.email})"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "email": self.email,
        }


# 模拟数据库存储 - 类似于内存数据库
user_list: List[User] = []
# 用于生成自增 ID - 类似于数据库的自增主键
next_user_id: int = 1


# ============================================================
# 4. 数据访问层 (DAO/Repository)
# ============================================================
# 类似于 Java 的 Repository 或 DAO 层

def add_user(user_data: UserCreate) -> User:
    """
    添加用户到数据库
    类似于 JPA 的 save() 方法
    """
    global next_user_id
    user = User(
        user_id=next_user_id,
        name=user_data.name,
        age=user_data.age,
        gender=user_data.gender,
        email=user_data.email
    )
    user_list.append(user)
    next_user_id += 1
    return user


def get_user(user_id: int) -> Optional[User]:
    """
    根据用户ID获取用户信息
    类似于 JPA 的 findById() 方法
    """
    return next(filter(lambda x: x.user_id == user_id, user_list), None)


def get_all_users() -> List[User]:
    """
    获取所有用户
    类似于 JPA 的 findAll() 方法
    """
    return user_list


def remove_user(user_id: int) -> bool:
    """
    根据用户ID删除用户信息
    类似于 JPA 的 deleteById() 方法
    """
    user = get_user(user_id)
    if user:
        user_list.remove(user)
        return True
    return False


def update_user(user_id: int, user_data: UserUpdate) -> Optional[User]:
    """
    根据用户ID更新用户信息
    类似于 JPA 的 save() 方法（更新已存在的实体）
    """
    user = get_user(user_id)
    if user:
        # 只更新提供的字段 (PATCH 语义)
        if user_data.name is not None:
            user.name = user_data.name
        if user_data.age is not None:
            user.age = user_data.age
        if user_data.gender is not None:
            user.gender = user_data.gender
        if user_data.email is not None:
            user.email = user_data.email
        return user
    return None


# ============================================================
# 5. API 路由层 (Controller)
# ============================================================
# 类似于 Java Spring 的 @RestController 和 @RequestMapping
# FastAPI 使用装饰器来定义路由

@app.get(
    path="/",
    tags=["根路径"]
)
async def root():
    """
    根路径 - 欢迎页面
    访问: http://localhost:8000/
    """
    return {
        "message": "欢迎使用用户管理系统 API",
        "docs": "访问 /docs 查看交互式 API 文档",
        "redoc": "访问 /redoc 查看 ReDoc 文档"
    }


@app.post(
    path="/users/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["用户管理"],
    summary="创建新用户"
)
async def create_user(user: UserCreate):
    """
    创建新用户 - POST 请求
    
    类似于 Spring 的:
    @PostMapping("/users")
    @ResponseStatus(HttpStatus.CREATED)
    public UserResponse createUser(@RequestBody @Valid UserCreate user)
    
    - **name**: 用户名称 (必填, 1-50字符)
    - **age**: 用户年龄 (必填, 0-150)
    - **gender**: 用户性别 (必填, 男/女/其他)
    - **email**: 用户邮箱 (必填, 有效邮箱格式)
    """
    new_user = add_user(user)
    return new_user.to_dict()


@app.get(
    path="/users/",
    response_model=List[UserResponse],
    tags=["用户管理"],
    summary="获取所有用户"
)
async def list_users(
        skip: int = Query(0, ge=0, description="跳过的记录数"),
        limit: int = Query(100, ge=1, le=100, description="返回的最大记录数")
):
    """
    获取所有用户列表 - GET 请求
    
    类似于 Spring 的:
    @GetMapping("/users")
    public List<UserResponse> listUsers(@RequestParam int skip, @RequestParam int limit)
    
    支持分页参数:
    - **skip**: 跳过的记录数 (默认: 0)
    - **limit**: 返回的最大记录数 (默认: 100, 最大: 100)
    """
    users = get_all_users()
    return [user.to_dict() for user in users[skip: skip + limit]]


@app.get(
    path="/users/{user_id}",
    response_model=UserResponse,
    tags=["用户管理"],
    summary="根据ID获取用户"
)
async def read_user(user_id: int):
    """
    根据用户ID获取用户详情 - GET 请求
    
    类似于 Spring 的:
    @GetMapping("/users/{userId}")
    public UserResponse readUser(@PathVariable int userId)
    
    - **user_id**: 用户ID (路径参数)
    
    异常处理:
    - 404: 用户不存在
    """
    user = get_user(user_id)
    if user is None:
        # HTTPException 类似于 Spring 的 ResponseStatusException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 ID {user_id} 不存在"
        )
    return user.to_dict()


@app.put(
    path="/users/{user_id}",
    response_model=UserResponse,
    tags=["用户管理"],
    summary="更新用户信息"
)
async def update_user_info(user_id: int, user_data: UserUpdate):
    """
    更新用户信息 - PUT/PATCH 请求
    
    类似于 Spring 的:
    @PutMapping("/users/{userId}")
    public UserResponse updateUser(@PathVariable int userId, @RequestBody UserUpdate user)
    
    - **user_id**: 用户ID (路径参数)
    - **user_data**: 要更新的用户数据 (请求体, 所有字段可选)
    
    异常处理:
    - 404: 用户不存在
    """
    updated_user = update_user(user_id, user_data)
    if updated_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 ID {user_id} 不存在"
        )
    return updated_user.to_dict()


@app.delete(
    path="/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["用户管理"],
    summary="删除用户"
)
async def delete_user(user_id: int):
    """
    删除用户 - DELETE 请求
    
    类似于 Spring 的:
    @DeleteMapping("/users/{userId}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void deleteUser(@PathVariable int userId)
    
    - **user_id**: 用户ID (路径参数)
    
    异常处理:
    - 404: 用户不存在
    """
    success = remove_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"用户 ID {user_id} 不存在"
        )
    # 204 状态码不返回内容
    return None


# ============================================================
# 6. 启动应用
# ============================================================
# 运行方式:
# 方法1 (开发模式): uvicorn two_practice:app --reload
# 方法2 (代码启动): 运行此文件
# 
# 访问地址:
# - API 根路径: http://localhost:8000/
# - 交互式文档 (Swagger UI): http://localhost:8000/docs
# - 备用文档 (ReDoc): http://localhost:8000/redoc
#
# 类似于 Spring Boot 的 main 方法和自动配置

if __name__ == "__main__":
    import uvicorn

    # uvicorn 是 ASGI 服务器，类似于 Java 的 Tomcat/Jetty
    uvicorn.run(
        "two_practice:app",  # 应用路径
        host="0.0.0.0",  # 监听所有网络接口
        port=8000,  # 端口号
        reload=True  # 开发模式：代码修改自动重启（类似 Spring DevTools）
    )

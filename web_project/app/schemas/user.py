"""
用户Pydantic模型
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")


class UserCreate(UserBase):
    """创建用户模型"""
    password: str = Field(..., min_length=6, max_length=100, description="密码")


class UserUpdate(BaseModel):
    """更新用户模型"""
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")
    is_active: Optional[bool] = Field(None, description="是否激活")


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class Token(BaseModel):
    """令牌模型"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """令牌数据模型"""
    username: Optional[str] = None

"""
任务Pydantic模型
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

from ..models.task import TaskStatus, TaskPriority


class TaskBase(BaseModel):
    """任务基础模型"""
    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="任务优先级")
    due_date: Optional[datetime] = Field(None, description="截止日期")


class TaskCreate(TaskBase):
    """创建任务模型"""
    pass


class TaskUpdate(BaseModel):
    """更新任务模型"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    status: Optional[TaskStatus] = Field(None, description="任务状态")
    priority: Optional[TaskPriority] = Field(None, description="任务优先级")
    due_date: Optional[datetime] = Field(None, description="截止日期")
    is_completed: Optional[bool] = Field(None, description="是否完成")


class TaskResponse(TaskBase):
    """任务响应模型"""
    id: int
    status: TaskStatus
    is_completed: bool
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    tasks: list[TaskResponse]
    total: int
    page: int
    size: int
    pages: int

"""
任务管理API
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..models.task import TaskStatus
from ..schemas.task import TaskCreate, TaskResponse, TaskUpdate, TaskListResponse
from ..utils.helpers import (
    get_tasks_by_user, 
    get_task_by_id, 
    create_task, 
    update_task, 
    delete_task
)
from .deps import get_current_active_user

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_new_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    创建新任务
    """
    task_dict = task_data.dict()
    db_task = create_task(db, task_dict, current_user.id)
    return db_task


@router.get("/", response_model=TaskListResponse)
def read_tasks(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(10, ge=1, le=100, description="返回的记录数"),
    status: Optional[TaskStatus] = Query(None, description="任务状态过滤"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户的任务列表
    """
    tasks = get_tasks_by_user(db, current_user.id, skip, limit, status)
    
    # 计算总数和分页信息
    from ..models.task import Task
    if status:
        total_query = db.query(Task).filter(
            Task.owner_id == current_user.id,
            Task.status == status
        ).count()
    else:
        total_query = db.query(Task).filter(Task.owner_id == current_user.id).count()
    
    pages = (total_query + limit - 1) // limit
    page = (skip // limit) + 1
    
    return TaskListResponse(
        tasks=tasks,
        total=total_query,
        page=page,
        size=len(tasks),
        pages=pages
    )


@router.get("/{task_id}", response_model=TaskResponse)
def read_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    根据ID获取任务
    """
    task = get_task_by_id(db, task_id, current_user.id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_existing_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    更新任务
    """
    task = get_task_by_id(db, task_id, current_user.id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    update_data = task_update.dict(exclude_unset=True)
    updated_task = update_task(db, task, update_data)
    return updated_task


@router.delete("/{task_id}")
def delete_existing_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除任务
    """
    task = get_task_by_id(db, task_id, current_user.id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    success = delete_task(db, task)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete task"
        )
    
    return {"message": "Task deleted successfully"}


@router.patch("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    标记任务为完成
    """
    task = get_task_by_id(db, task_id, current_user.id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    update_data = {
        "is_completed": True,
        "status": TaskStatus.COMPLETED
    }
    updated_task = update_task(db, task, update_data)
    return updated_task


@router.patch("/{task_id}/status", response_model=TaskResponse)
def update_task_status(
    task_id: int,
    new_status: TaskStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    更新任务状态
    """
    task = get_task_by_id(db, task_id, current_user.id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    update_data = {"status": new_status}
    if new_status == TaskStatus.COMPLETED:
        update_data["is_completed"] = True
    
    updated_task = update_task(db, task, update_data)
    return updated_task

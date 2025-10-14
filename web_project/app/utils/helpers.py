"""
辅助工具函数
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.user import User
from ..models.task import Task, TaskStatus


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """根据用户名获取用户"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """根据邮箱获取用户"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """根据ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_data: Dict[str, Any]) -> User:
    """创建用户"""
    db_user = User(**user_data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_tasks_by_user(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    status: Optional[TaskStatus] = None
) -> list[Task]:
    """获取用户的任务列表"""
    query = db.query(Task).filter(Task.owner_id == user_id)
    
    if status:
        query = query.filter(Task.status == status)
    
    return query.offset(skip).limit(limit).all()


def get_task_by_id(db: Session, task_id: int, user_id: int) -> Optional[Task]:
    """根据ID获取任务（仅限任务所有者）"""
    return db.query(Task).filter(
        Task.id == task_id, 
        Task.owner_id == user_id
    ).first()


def create_task(db: Session, task_data: Dict[str, Any], user_id: int) -> Task:
    """创建任务"""
    task_data["owner_id"] = user_id
    db_task = Task(**task_data)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(db: Session, task: Task, update_data: Dict[str, Any]) -> Task:
    """更新任务"""
    for field, value in update_data.items():
        if hasattr(task, field) and value is not None:
            setattr(task, field, value)
    
    # 如果任务被标记为完成，设置完成时间
    if update_data.get("is_completed") or update_data.get("status") == TaskStatus.COMPLETED:
        task.is_completed = True
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> bool:
    """删除任务"""
    try:
        db.delete(task)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False


def get_task_statistics(db: Session, user_id: int) -> Dict[str, int]:
    """获取任务统计信息"""
    total_tasks = db.query(Task).filter(Task.owner_id == user_id).count()
    completed_tasks = db.query(Task).filter(
        Task.owner_id == user_id,
        Task.is_completed == True
    ).count()
    pending_tasks = db.query(Task).filter(
        Task.owner_id == user_id,
        Task.status == TaskStatus.PENDING
    ).count()
    in_progress_tasks = db.query(Task).filter(
        Task.owner_id == user_id,
        Task.status == TaskStatus.IN_PROGRESS
    ).count()
    
    return {
        "total": total_tasks,
        "completed": completed_tasks,
        "pending": pending_tasks,
        "in_progress": in_progress_tasks,
        "completion_rate": round((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 2)
    }

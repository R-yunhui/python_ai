"""
任务相关测试
"""

import pytest
from fastapi.testclient import TestClient


def get_auth_header(client: TestClient, test_user):
    """获取认证头"""
    # 注册并登录用户
    client.post("/api/auth/register", json=test_user)
    login_data = {
        "username": test_user["username"],
        "password": test_user["password"]
    }
    response = client.post("/api/auth/login", data=login_data)
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_task(client: TestClient, test_user, test_task):
    """测试创建任务"""
    headers = get_auth_header(client, test_user)
    
    response = client.post("/api/tasks/", json=test_task, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == test_task["title"]
    assert data["description"] == test_task["description"]
    assert data["status"] == "pending"
    assert "id" in data


def test_create_task_unauthorized(client: TestClient, test_task):
    """测试未认证创建任务"""
    response = client.post("/api/tasks/", json=test_task)
    assert response.status_code == 403


def test_read_tasks(client: TestClient, test_user, test_task):
    """测试获取任务列表"""
    headers = get_auth_header(client, test_user)
    
    # 先创建一个任务
    client.post("/api/tasks/", json=test_task, headers=headers)
    
    # 获取任务列表
    response = client.get("/api/tasks/", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert "total" in data
    assert data["total"] == 1
    assert len(data["tasks"]) == 1


def test_read_task(client: TestClient, test_user, test_task):
    """测试获取单个任务"""
    headers = get_auth_header(client, test_user)
    
    # 先创建一个任务
    create_response = client.post("/api/tasks/", json=test_task, headers=headers)
    task_id = create_response.json()["id"]
    
    # 获取任务
    response = client.get(f"/api/tasks/{task_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == test_task["title"]


def test_read_nonexistent_task(client: TestClient, test_user):
    """测试获取不存在的任务"""
    headers = get_auth_header(client, test_user)
    
    response = client.get("/api/tasks/999", headers=headers)
    assert response.status_code == 404
    assert "Task not found" in response.json()["detail"]


def test_update_task(client: TestClient, test_user, test_task):
    """测试更新任务"""
    headers = get_auth_header(client, test_user)
    
    # 先创建一个任务
    create_response = client.post("/api/tasks/", json=test_task, headers=headers)
    task_id = create_response.json()["id"]
    
    # 更新任务
    update_data = {
        "title": "更新后的任务",
        "status": "in_progress"
    }
    
    response = client.put(f"/api/tasks/{task_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["status"] == update_data["status"]


def test_complete_task(client: TestClient, test_user, test_task):
    """测试完成任务"""
    headers = get_auth_header(client, test_user)
    
    # 先创建一个任务
    create_response = client.post("/api/tasks/", json=test_task, headers=headers)
    task_id = create_response.json()["id"]
    
    # 完成任务
    response = client.patch(f"/api/tasks/{task_id}/complete", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["is_completed"] == True
    assert data["status"] == "completed"
    assert data["completed_at"] is not None


def test_delete_task(client: TestClient, test_user, test_task):
    """测试删除任务"""
    headers = get_auth_header(client, test_user)
    
    # 先创建一个任务
    create_response = client.post("/api/tasks/", json=test_task, headers=headers)
    task_id = create_response.json()["id"]
    
    # 删除任务
    response = client.delete(f"/api/tasks/{task_id}", headers=headers)
    assert response.status_code == 200
    assert "Task deleted successfully" in response.json()["message"]
    
    # 验证任务已删除
    get_response = client.get(f"/api/tasks/{task_id}", headers=headers)
    assert get_response.status_code == 404

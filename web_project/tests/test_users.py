"""
用户相关测试
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


def test_read_user_me(client: TestClient, test_user):
    """测试获取当前用户信息"""
    headers = get_auth_header(client, test_user)
    
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]


def test_read_user_me_unauthorized(client: TestClient):
    """测试未认证获取用户信息"""
    response = client.get("/api/users/me")
    assert response.status_code == 403


def test_update_user_me(client: TestClient, test_user):
    """测试更新当前用户信息"""
    headers = get_auth_header(client, test_user)
    
    update_data = {
        "username": "updateduser",
        "email": "updated@example.com"
    }
    
    response = client.put("/api/users/me", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == update_data["username"]
    assert data["email"] == update_data["email"]


def test_read_user_stats(client: TestClient, test_user):
    """测试获取用户统计信息"""
    headers = get_auth_header(client, test_user)
    
    response = client.get("/api/users/me/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "username" in data
    assert "task_stats" in data
    assert data["task_stats"]["total"] == 0  # 新用户没有任务

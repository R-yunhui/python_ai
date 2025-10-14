"""
认证相关测试
"""

import pytest
from fastapi.testclient import TestClient


def test_register_user(client: TestClient, test_user):
    """测试用户注册"""
    response = client.post("/api/auth/register", json=test_user)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]
    assert "id" in data


def test_register_duplicate_username(client: TestClient, test_user):
    """测试重复用户名注册"""
    # 第一次注册
    client.post("/api/auth/register", json=test_user)
    
    # 第二次注册相同用户名
    response = client.post("/api/auth/register", json=test_user)
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]


def test_register_duplicate_email(client: TestClient, test_user):
    """测试重复邮箱注册"""
    # 第一次注册
    client.post("/api/auth/register", json=test_user)
    
    # 第二次注册相同邮箱但不同用户名
    duplicate_email_user = test_user.copy()
    duplicate_email_user["username"] = "differentuser"
    
    response = client.post("/api/auth/register", json=duplicate_email_user)
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


def test_login_success(client: TestClient, test_user):
    """测试成功登录"""
    # 先注册用户
    client.post("/api/auth/register", json=test_user)
    
    # 登录
    login_data = {
        "username": test_user["username"],
        "password": test_user["password"]
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, test_user):
    """测试错误密码登录"""
    # 先注册用户
    client.post("/api/auth/register", json=test_user)
    
    # 使用错误密码登录
    login_data = {
        "username": test_user["username"],
        "password": "wrongpassword"
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_nonexistent_user(client: TestClient):
    """测试不存在用户登录"""
    login_data = {
        "username": "nonexistent",
        "password": "password"
    }
    response = client.post("/api/auth/login", data=login_data)
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]

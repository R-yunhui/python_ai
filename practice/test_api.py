"""
FastAPI 测试脚本 - 演示如何调用 API
类似于 Java 的单元测试或集成测试
"""

import requests
import json

# API 基础地址
BASE_URL = "http://localhost:8000"


def print_response(title: str, response: requests.Response):
    """打印 API 响应结果"""
    print(f"\n{'='*60}")
    print(f"📌 {title}")
    print(f"{'='*60}")
    print(f"状态码: {response.status_code}")
    print(f"响应内容:")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)


def test_create_user():
    """测试创建用户 - POST 请求"""
    url = f"{BASE_URL}/users/"
    user_data = {
        "name": "张三",
        "age": 25,
        "gender": "男",
        "email": "zhangsan@example.com"
    }
    response = requests.post(url, json=user_data)
    print_response("创建用户", response)
    return response.json().get("user_id") if response.status_code == 201 else None


def test_create_multiple_users():
    """批量创建测试用户"""
    users = [
        {"name": "李四", "age": 30, "gender": "男", "email": "lisi@example.com"},
        {"name": "王五", "age": 28, "gender": "女", "email": "wangwu@example.com"},
        {"name": "赵六", "age": 35, "gender": "男", "email": "zhaoliu@example.com"}
    ]
    
    user_ids = []
    for user in users:
        url = f"{BASE_URL}/users/"
        response = requests.post(url, json=user)
        if response.status_code == 201:
            user_ids.append(response.json().get("user_id"))
    
    print(f"\n✅ 成功创建 {len(user_ids)} 个用户，ID: {user_ids}")
    return user_ids


def test_get_all_users():
    """测试获取所有用户 - GET 请求"""
    url = f"{BASE_URL}/users/"
    response = requests.get(url)
    print_response("获取所有用户", response)


def test_get_user_by_id(user_id: int):
    """测试根据 ID 获取用户 - GET 请求"""
    url = f"{BASE_URL}/users/{user_id}"
    response = requests.get(url)
    print_response(f"获取用户 ID={user_id}", response)


def test_get_users_with_pagination():
    """测试分页查询 - GET 请求（带查询参数）"""
    url = f"{BASE_URL}/users/?skip=0&limit=2"
    response = requests.get(url)
    print_response("分页查询用户 (skip=0, limit=2)", response)


def test_update_user(user_id: int):
    """测试更新用户 - PUT 请求"""
    url = f"{BASE_URL}/users/{user_id}"
    update_data = {
        "name": "张三（已更新）",
        "age": 26
    }
    response = requests.put(url, json=update_data)
    print_response(f"更新用户 ID={user_id}", response)


def test_delete_user(user_id: int):
    """测试删除用户 - DELETE 请求"""
    url = f"{BASE_URL}/users/{user_id}"
    response = requests.delete(url)
    print_response(f"删除用户 ID={user_id}", response)


def test_error_cases():
    """测试错误情况处理"""
    print(f"\n{'='*60}")
    print("🔴 测试错误情况")
    print(f"{'='*60}")
    
    # 1. 获取不存在的用户
    url = f"{BASE_URL}/users/9999"
    response = requests.get(url)
    print_response("获取不存在的用户 (ID=9999)", response)
    
    # 2. 创建用户时数据验证失败
    url = f"{BASE_URL}/users/"
    invalid_data = {
        "name": "",  # 名称不能为空
        "age": -5,   # 年龄不能为负数
        "gender": "未知",  # 性别必须是 男/女/其他
        "email": "invalid-email"  # 邮箱格式不正确
    }
    response = requests.post(url, json=invalid_data)
    print_response("创建用户 - 数据验证失败", response)


def main():
    """主测试流程"""
    print("\n" + "="*60)
    print("🚀 FastAPI 用户管理系统 - API 测试")
    print("="*60)
    print("\n⚠️  请确保 FastAPI 服务已启动: uvicorn two_practice:app --reload")
    print("="*60)
    
    try:
        # 测试根路径
        response = requests.get(BASE_URL)
        print_response("根路径", response)
        
        # 1. 创建单个用户
        print("\n\n📝 测试 1: 创建用户")
        user_id = test_create_user()
        
        # 2. 批量创建用户
        print("\n\n📝 测试 2: 批量创建用户")
        test_create_multiple_users()
        
        # 3. 获取所有用户
        print("\n\n📝 测试 3: 获取所有用户")
        test_get_all_users()
        
        # 4. 分页查询
        print("\n\n📝 测试 4: 分页查询")
        test_get_users_with_pagination()
        
        # 5. 根据 ID 获取用户
        if user_id:
            print("\n\n📝 测试 5: 根据 ID 获取用户")
            test_get_user_by_id(user_id)
            
            # 6. 更新用户
            print("\n\n📝 测试 6: 更新用户")
            test_update_user(user_id)
            
            # 7. 再次查看更新后的用户
            print("\n\n📝 测试 7: 查看更新后的用户")
            test_get_user_by_id(user_id)
            
            # 8. 删除用户
            print("\n\n📝 测试 8: 删除用户")
            test_delete_user(user_id)
            
            # 9. 确认用户已删除
            print("\n\n📝 测试 9: 确认用户已删除")
            test_get_user_by_id(user_id)
        
        # 10. 测试错误情况
        print("\n\n📝 测试 10: 错误处理")
        test_error_cases()
        
        print("\n\n" + "="*60)
        print("✅ 所有测试完成！")
        print("="*60)
        print("\n💡 提示:")
        print("   1. 访问 http://localhost:8000/docs 查看交互式 API 文档")
        print("   2. 在文档中可以直接测试所有 API")
        print("   3. 这个测试脚本演示了如何在 Python 中调用 REST API")
        print("="*60 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误: 无法连接到服务器")
        print("请先启动 FastAPI 服务:")
        print("   cd practice")
        print("   uvicorn two_practice:app --reload")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")


if __name__ == "__main__":
    main()


# 学习 fastapi
from typing import Any


class User:
    """
    用户类
    """

    def __init__(self, user_id: int, name: str, age: int, gender: str, email: str):
        self.user_id = user_id
        self.name = name
        self.age = age
        self.gender = gender
        self.email = email

    def __str__(self):
        return f"User(user_id={self.user_id}, name={self.name}, age={self.age}, gender={self.gender}, email={self.email})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "email": self.email,
        }


# 模拟数据库存储用户信息
user_list = []


def add_user(user: User):
    """
    添加用户到数据库
    """
    user_list.append(user)


def get_user(user_id: int) -> Any | None:
    """
    根据用户ID获取用户信息
    next(filter(lambda x: x.user_id == user_id, user_list), None) 返回迭代器中的下一个元素，
    如果没有更多元素，则返回 None。
    """
    user = next(filter(lambda x: x.user_id == user_id, user_list), None)
    return user


def remove_user(user_id: int) -> bool:
    """
    根据用户ID删除用户信息
    """
    user = get_user(user_id)
    if user:
        user_list.remove(user)
        return True
    return False


def update_user(user: User) -> bool:
    """
    根据用户ID更新用户信息
    """
    user = get_user(user.user_id)
    if user:
        user.name = user.name
        user.age = user.age
        user.gender = user.gender
        user.email = user.email
        return True
    return False

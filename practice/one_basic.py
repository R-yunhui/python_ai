import json
import os
import functools
from typing import Generator, Any, Dict, List
from datetime import datetime


def datastruct_basic():
    # 测试数据结构基础
    animals_list = ["cat", "dog", "elephant", "giraffe"]
    print(f"动物列表: {animals_list}")

    print(f"动物列表前三个: {animals_list[:3]}")

    print(f"动物类列表后三个: {animals_list[-3:]}")

    sorted_animals = sorted(animals_list, key=lambda x: x)
    print(f"动物列表按名称排序: {sorted_animals}")

    sorted_name_len_animals = sorted(animals_list, key=lambda x: len(x))
    print(f"动物列表按名称长度排序: {sorted_name_len_animals}")

    filter_animals = list(filter(lambda x: len(x) > 3, animals_list))
    print(f"动物列表按名称长度大于3筛选: {filter_animals}")

    del filter_animals[:1]
    print(f"动物列表按名称长度大于3筛选后删除前1个: {filter_animals}")

    # 测试元组 -> 类似java的不可变集合，存储的对象是 Object 类型
    my_tuple = ("男", "女", "1", "2")
    print(f"元组: {my_tuple}")

    print(f"元组第二个元素: {my_tuple[1]}")

    # 测试元组元素不可修改
    # try:
    #     my_tuple[1] = "未知"
    # except TypeError as e:
    #     print(f"元组元素不可修改: {e}")

    person_dict: Dict[str, Any] = {"name": "张三", "age": 18, "gender": "男"}
    print(f"字典: {person_dict}")

    # 使用 update 直接更新字典
    person_dict.update({"age": 20, "gender": "未知"})
    print(f"字典更新后: {person_dict}")

    person_list: List[Dict[str, Any]] = [person_dict]
    print(f"字典转换为列表: {person_list}")

    person_list.append({"name": "李四", "age": 22, "gender": "男"})
    print(f"列表添加李四后: {person_list}")

    # 从列表中删除李四
    person_list.remove({"name": "李四", "age": 22, "gender": "男"})
    print(f"列表删除李四后: {person_list}")


def library_basic():
    # 测试库函数基础
    os.getcwd()
    print(f"当前工作目录: {os.getcwd()}")

    os.path.dirname(os.getcwd())
    print(f"当前工作目录的父目录: {os.path.dirname(os.getcwd())}")

    os.path.abspath(__file__)
    print(f"当前脚本的绝对路径: {os.path.abspath(__file__)}")

    file_path = os.path.join(os.getcwd(), "test.txt")
    print(f"当前工作目录下的 test.txt 文件路径: {file_path}")

    if os.path.exists(file_path):
        print(f"文件 {file_path} 存在")
    else:
        print(f"文件 {file_path} 不存在, 现在进行创建")
        try:
            with open(file_path, 'w+', encoding='utf-8') as f:
                f.write("hello world")
                f.write("\n")
                f.write(f"当前时间: {datetime.now()}")
            print(f"文件 {file_path} 写入成功")
        except Exception as e:
            print(f"文件 {file_path} 写入失败: {e}")


def log_decorator(func):
    """
    日志装饰器 - 处理带参数的函数
    """

    @functools.wraps(func)  # 保持原函数的元数据
    def wrapper(*args, **kwargs):
        print(f"调用函数 {func.__name__} 开始, 参数: args={args}, kwargs={kwargs}")
        result = func(*args, **kwargs)
        print(f"调用函数 {func.__name__} 结束, 返回值: {result}")
        return result

    return wrapper


@log_decorator
def json_basic():
    # json
    person = Person("张三", 18, "男")
    # 序列化，只支持
    """
    直接使用 json.dumps 处理自定义对象 person 会报错，因为 json.dumps 默认只能处理 Python 的内置类型，如字典、列表、字符串、数字等，对于自定义类对象，它不知道如何将其转换为 JSON 格式。
    """
    person_json_str = json.dumps(person.to_dict(), ensure_ascii=False)
    print(person_json_str)

    file_path = os.path.join(os.getcwd(), "person.json")
    if not os.path.exists(file_path):
        try:
            # a+ -> 文件存储在创建文件，并且通过追加写入的方式，确保每次写入都在文件末尾
            with open(file_path, 'a+', encoding='utf - 8') as f:
                f.write(person_json_str)
                f.write("\n")
            print(f"文件 {file_path} 写入成功")
        except Exception as e:
            print(f"文件 {file_path} 写入失败: {e}")
    else:
        try:
            with open(file_path, 'a+', encoding='utf - 8') as f:
                f.write(person_json_str)
                f.write("\n")
            print(f"文件 {file_path} 写入成功")
        except Exception as e:
            print(f"文件 {file_path} 写入失败: {e}")


@log_decorator
def add_numbers(**kwargs):
    """
    加法函数, 支持关键字参数 a, b, 并返回 a + b 的结果
    """
    a = kwargs.get("a", 0)
    b = kwargs.get("b", 0)
    return a + b


def countdown_generator(start: int) -> Generator[int | str | Any, None, None]:
    """
    倒计时生成器, 从 start 开始倒计时, 每次减 1, 直到 0 结束
    """
    while start > 0:
        yield start
        start -= 1
    yield "倒计时结束！"


class Person:

    def __init__(self, name: str, age: int, gender: str):
        self.name = name
        self.age = age
        self.gender = gender

    def __str__(self):
        return f"姓名: {self.name}, 年龄: {self.age}, 性别: {self.gender}"

    def to_dict(self):
        return {
            "name": self.name,
            "age": self.age,
            "gender": self.gender
        }


if __name__ == "__main__":
    # datastruct_basic()

    # library_basic()

    # json_basic()

    # count = add_numbers(a=2, b=3)
    # print(f"2 + 3 = {count}")

    for item in countdown_generator(5):
        print(item, end=" ")

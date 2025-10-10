# os 模块学习
import os
import json
import math
import random
from datetime import datetime, timedelta
from typing import List
from itertools import groupby
from operator import itemgetter, attrgetter


def os_basic():
    """
    os 模块基本操作
    """
    current_dir = os.getcwd()  # 获取当前工作目录
    print(f"当前工作目录: {current_dir}")

    exists = os.path.exists(current_dir + '/test.txt')  # 检查文件是否存在
    print(f"检查文件是否存在: {exists}")

    print("PATH 环境变量:", os.environ.get("PATH"))  # 获取环境变量

    # 执行系统命令
    os.system("echo Hello, World!")

    # 创建目录
    os.mkdir("example_dir")
    print("目录创建成功")

    # 列出目录内容
    print("目录内容:", os.listdir("."))

    # 删除目录
    os.rmdir("example_dir")
    print("目录删除成功")


def datetime_basic():
    """
    datetime 模块基本操作
    """
    # 当前时间
    format: str = "%Y-%m-%d %H:%M:%S"
    now: datetime = datetime.now()
    print("当前时间:", now)

    # 当前日期
    date = now.date()
    print("当前日期:", date)

    # 格式化时间
    formatted = now.strftime(format)
    print("格式化时间:", formatted)

    # 时间加减 7 -7
    future = (now + timedelta(days=7)).strftime(format)
    print("未来时间:", future)

    # 字符串解析
    parsed = datetime.strptime("2023-10-01 12:00:00", format)
    print("解析时间:", parsed)


def json_basic():
    """
    json 模块基本操作
    """
    data = {"name": "张三", "age": 30, "city": "北京"}

    # json 序列化
    json_str = json.dumps(data, ensure_ascii=False, indent=2)
    print("序列化 json 字符串:\n", json_str)

    # json 反序列化
    parsed_data = json.loads(json_str)
    print("反序列化数据 name:", parsed_data["name"])
    print("反序列化数据 age:", parsed_data["age"])
    print("反序列化数据 city:", parsed_data["city"])

    # 将 序列化后的 json 数据写入文件
    try:
        with open("data.json", 'w', encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("写入文件异常:", e)
    else:
        print("写入文件成功")

    # 从文件读取数据
    try:
        with open('data.json', 'r', encoding='utf-8') as f:
            file_parsed_data = json.load(f)
            print("从文件读取数据:\n", file_parsed_data)
    except Exception as e:
        print("读取文件异常:", e)
    else:
        print("读取文件成功")


def math_basic():
    """
    math 模块基本操作
    """

    # 取整
    print("向下取整:", math.floor(3.7))
    print("向上取整:", math.ceil(3.2))

    # 开方
    print("开方:", math.sqrt(9))

    # 指数
    print("指数:", math.pow(2, 3))

    # 对数
    print("自然对数:", math.log(10))
    print("以 2 为底的对数:", math.log(8, 2))

    # 三角函数
    print("正弦:", math.sin(math.pi / 2))
    print("余弦:", math.cos(math.pi))
    print("正切:", math.tan(math.pi / 4))

    # 随机数
    print("随机数:", random.random())
    print("随机整数:", random.randint(1, 10))
    user_list: List[dict] = [
        {"name": "张三", "age": 30},
        {"name": "李四", "age": 25},
        {"name": "王五", "age": 28},
        {"name": "赵六", "age": 22},
        {"name": "钱七", "age": 35}
    ]
    print("随机选择 1 个用户:", random.choice(user_list))

    # 从序列中随机选择 n 个元素（可重复）。
    random_choices: List[dict] = random.choices(user_list, k=2)
    print("随机选择 2 个用户:", random_choices)

    # 从序列中随机选择 n 个元素（不可重复）。
    random_choices: List[dict] = random.sample(user_list, k=2)
    print("（不重复）随机选择 2 个用户:", random_choices)


def data_structure_basic():
    """
    数据结构基本操作
    """
    # 列表
    my_list: List[int] = [1, 2, 3, 4, 5]
    print("列表:", my_list)

    # 元组
    my_tuple: tuple = (1, 2, 3, 4, 5)
    print("元组:", my_tuple)

    # 集合
    my_set: set = {1, 2, 3, 4, 5}
    print("集合:", my_set)

    # 字典
    my_dict: dict = {"name": "张三", "age": 30, "city": "北京"}
    print("字典:", my_dict)


def lambda_basic():
    # 无参数
    no_param = lambda: "Hello, World!"
    print(no_param())  # 输出: Hello, World!

    # 单参数
    square = lambda x: x ** 2
    print(square(5))  # 输出: 25

    # 多参数
    add = lambda x, y: x + y
    print(add(3, 7))  # 输出: 10

    # 在列表中使用
    nums = [1, 2, 3, 4, 5]
    squared_nums = list(map(lambda x: x ** 2, nums))
    print(squared_nums)  # 输出: [1, 4, 9, 16, 25]

    # 条件表达式
    max_value = lambda x, y: x if x > y else y
    print(max_value(10, 20))  # 输出: 20


# ========== 定义测试用的类 ==========
class Student:
    def __init__(self, name, age, grade, score):
        self.name = name
        self.age = age
        self.grade = grade
        self.score = score

    def __repr__(self):
        return f"Student({self.name}, {self.age}岁, {self.grade}年级, {self.score}分)"


class Product:
    def __init__(self, name, price, category, stock):
        self.name = name
        self.price = price
        self.category = category
        self.stock = stock

    def __repr__(self):
        return f"Product({self.name}, ¥{self.price}, {self.category}, 库存{self.stock})"


# ========== 创建测试数据 ==========
students = [
    Student("张三", 18, "高一", 85),
    Student("李四", 17, "高一", 92),
    Student("王五", 19, "高二", 78),
    Student("赵六", 18, "高二", 88),
    Student("钱七", 17, "高一", 95),
]

products = [
    Product("笔记本电脑", 5999, "电子产品", 15),
    Product("鼠标", 99, "电子产品", 50),
    Product("咖啡", 35, "食品", 100),
    Product("键盘", 299, "电子产品", 30),
    Product("茶叶", 120, "食品", 25),
]


def lambda_complex():
    """
    lambda 复杂操作
    """
    print("=" * 60)
    print("1. 排序示例 (sorted + lambda)")
    print("=" * 60)

    # 1.1 按年龄排序
    sorted_by_age = sorted(students, key=lambda s: s.age)
    print("\n按年龄排序:")
    for s in sorted_by_age:
        print(f"  {s}")

    # 1.2 按分数降序排序
    sorted_by_score = sorted(students, key=lambda s: s.score, reverse=True)
    print("\n按分数降序排序:")
    for s in sorted_by_score:
        print(f"  {s}")

    # 1.3 多条件排序：先按年级，再按分数降序
    sorted_multi = sorted(students, key=lambda s: (s.grade, -s.score))
    print("\n多条件排序(年级升序，分数降序):")
    for s in sorted_multi:
        print(f"  {s}")

    # 1.4 按价格排序商品
    sorted_products = sorted(products, key=lambda p: p.price)
    print("\n商品按价格排序:")
    for p in sorted_products:
        print(f"  {p}")

    # 1.5 按名称长度排序
    sorted_by_name_len = sorted(students, key=lambda s: len(s.name))
    print("\n按姓名长度排序:")
    for s in sorted_by_name_len:
        print(f"  {s}")

    print("\n" + "=" * 60)
    print("2. 过滤示例 (filter + lambda)")
    print("=" * 60)

    # 2.1 筛选成年学生
    adults = list(filter(lambda s: s.age >= 18, students))
    print("\n成年学生:")
    for s in adults:
        print(f"  {s}")

    # 2.2 筛选高分学生
    high_scorers = list(filter(lambda s: s.score >= 90, students))
    print("\n高分学生(>=90):")
    for s in high_scorers:
        print(f"  {s}")

    # 2.3 筛选高一且分数大于85的学生
    filtered_complex = list(filter(lambda s: s.grade == "高一" and s.score > 85, students))
    print("\n高一且分数>85的学生:")
    for s in filtered_complex:
        print(f"  {s}")

    # 2.4 筛选电子产品
    electronics = list(filter(lambda p: p.category == "电子产品", products))
    print("\n电子产品:")
    for p in electronics:
        print(f"  {p}")

    # 2.5 筛选库存少于30的商品
    low_stock = list(filter(lambda p: p.stock < 30, products))
    print("\n低库存商品(<30):")
    for p in low_stock:
        print(f"  {p}")

    print("\n" + "=" * 60)
    print("3. 映射转换示例 (map + lambda)")
    print("=" * 60)

    # 3.1 提取所有学生姓名
    names = list(map(lambda s: s.name, students))
    print(f"\n所有学生姓名: {names}")

    # 3.2 计算所有学生的分数等级
    def get_grade_level(score):
        if score >= 90:
            return "优秀"
        elif score >= 80:
            return "良好"
        elif score >= 60:
            return "及格"
        else:
            return "不及格"

    grade_levels = list(map(lambda s: f"{s.name}: {get_grade_level(s.score)}", students))
    print("\n学生成绩等级:")
    for g in grade_levels:
        print(f"  {g}")

    # 3.3 商品打8折后的价格
    discounted = list(map(lambda p: (p.name, p.price * 0.8), products))
    print("\n商品8折价格:")
    for name, price in discounted:
        print(f"  {name}: ¥{price:.2f}")

    # 3.4 提取商品信息字典
    product_dicts = list(map(lambda p: {
        'name': p.name,
        'price': p.price,
        'total_value': p.price * p.stock
    }, products))
    print("\n商品库存总价值:")
    for pd in product_dicts:
        print(f"  {pd['name']}: ¥{pd['total_value']}")

    print("\n" + "=" * 60)
    print("4. 分组示例 (group_by + lambda)")
    print("=" * 60)

    # 4.1 按年级分组
    students_sorted = sorted(students, key=lambda s: s.grade)
    grouped_by_grade = {k: list(v) for k, v in groupby(students_sorted, key=lambda s: s.grade)}
    print("\n按年级分组:")
    for grade, group in grouped_by_grade.items():
        print(f"\n  {grade}:")
        for s in group:
            print(f"    {s}")

    # 4.2 按年龄分组
    students_by_age = sorted(students, key=lambda s: s.age)
    grouped_by_age = {k: list(v) for k, v in groupby(students_by_age, key=lambda s: s.age)}
    print("\n按年龄分组:")
    for age, group in grouped_by_age.items():
        print(f"\n  {age}岁:")
        for s in group:
            print(f"    {s}")

    # 4.3 按商品类别分组
    products_sorted = sorted(products, key=lambda p: p.category)
    grouped_by_category = {k: list(v) for k, v in groupby(products_sorted, key=lambda p: p.category)}
    print("\n按商品类别分组:")
    for cat, group in grouped_by_category.items():
        print(f"\n  {cat}:")
        for p in group:
            print(f"    {p}")

    # 4.4 按价格区间分组
    products_by_price = sorted(products, key=lambda p: price_range(p.price))
    grouped_by_price = {k: list(v) for k, v in groupby(products_by_price, key=lambda p: price_range(p.price))}
    print("\n按价格区间分组:")
    for range_name, group in grouped_by_price.items():
        print(f"\n  {range_name}:")
        for p in group:
            print(f"    {p}")

    print("\n" + "=" * 60)
    print("5. 聚合统计示例 (reduce + lambda)")
    print("=" * 60)

    from functools import reduce

    # 5.1 计算总分
    total_score = reduce(lambda acc, s: acc + s.score, students, 0)
    print(f"\n所有学生总分: {total_score}")

    # 5.2 找出最高分学生
    highest_scorer = reduce(lambda a, b: a if a.score > b.score else b, students)
    print(f"最高分学生: {highest_scorer}")

    # 5.3 计算商品库存总价值
    total_value = reduce(lambda acc, p: acc + p.price * p.stock, products, 0)
    print(f"所有商品库存总价值: ¥{total_value}")

    # 5.4 拼接所有学生姓名
    all_names = reduce(lambda acc, s: acc + s.name + "、", students, "")[:-1]
    print(f"所有学生: {all_names}")

    print("\n" + "=" * 60)
    print("6. 复杂组合示例")
    print("=" * 60)

    # 6.1 找出每个年级的最高分学生
    print("\n每个年级的最高分学生:")
    for grade, group in grouped_by_grade.items():
        top_student = max(group, key=lambda s: s.score)
        print(f"  {grade}: {top_student.name} ({top_student.score}分)")

    # 6.2 统计每个类别商品的平均价格
    print("\n每个类别商品的平均价格:")
    for cat, group in grouped_by_category.items():
        avg_price = sum(map(lambda p: p.price, group)) / len(group)
        print(f"  {cat}: ¥{avg_price:.2f}")

    # 6.3 筛选并排序：高一学生按分数排序
    grade1_sorted = sorted(
        filter(lambda s: s.grade == "高一", students),
        key=lambda s: s.score,
        reverse=True
    )
    print("\n高一学生按分数排序:")
    for s in grade1_sorted:
        print(f"  {s}")

    # 6.4 找出库存价值最高的3个商品
    top3_valuable = sorted(
        products,
        key=lambda p: p.price * p.stock,
        reverse=True
    )[:3]
    print("\n库存价值最高的3个商品:")
    for p in top3_valuable:
        print(f"  {p} (总价值: ¥{p.price * p.stock})")

    print("\n" + "=" * 60)
    print("7. 使用列表推导式 (更Pythonic)")
    print("=" * 60)

    # 7.1 提取高分学生姓名
    high_score_names = [s.name for s in students if s.score >= 90]
    print(f"\n高分学生姓名: {high_score_names}")

    # 7.2 创建姓名-分数字典
    score_dict = {s.name: s.score for s in students}
    print(f"\n姓名-分数字典: {score_dict}")

    # 7.3 按类别分组商品(使用字典推导)
    from collections import defaultdict
    products_by_cat = defaultdict(list)
    for p in products:
        products_by_cat[p.category].append(p)

    print("\n按类别分组的商品:")
    for cat, prods in products_by_cat.items():
        print(f"  {cat}: {[p.name for p in prods]}")

    # 7.4 嵌套条件筛选
    special_students = [
        s for s in students
        if (s.grade == "高一" and s.score > 90) or (s.grade == "高二" and s.age >= 19)
    ]
    print("\n特殊筛选(高一且>90分 或 高二且>=19岁):")
    for s in special_students:
        print(f"  {s}")

def price_range(price):
    if price < 100:
        return "低价"
    elif price < 500:
         return "中价"
    else:
        return "高价"


if __name__ == '__main__':
    # os_basic()

    # datetime_basic()

    # json_basic()

    # math_basic()

    # data_structure_basic()

    # lambda_basic()

    lambda_complex()

import pymysql

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, func, select, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from sqlalchemy import exists


# 数据库操作示例
def jdbc_basic():
    """原生 JDBC 风格的数据库操作"""

    # 建立连接 (类似 DriverManager.getConnection)
    connection = pymysql.connect(
        host='192.168.2.148',
        port=43306,
        user='root',
        password='Koala_MySQL#20Xx..A..',
        database='study',
        charset='utf8mb4'
    )

    try:
        # 获取游标 (类似 Statement)
        with connection.cursor() as cursor:
            # 执行 DDL
            cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(100),
                        age INT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

            # 插入数据 (PreparedStatement 风格)
            sql = "INSERT INTO users (name, email, age) VALUES (%s, %s, %s)"
            cursor.execute(sql, ('张三', 'zhangsan@example.com', 25))

            # 批量插入
            users_data = [
                ('李四', 'lisi@example.com', 30),
                ('王五', 'wangwu@example.com', 28),
            ]
            cursor.executemany(sql, users_data)

            # 提交事务
            connection.commit()

            # 查询数据
            cursor.execute("SELECT * FROM users WHERE age > %s", (20,))
            results = cursor.fetchall()

            for row in results:
                print(f"ID: {row[0]}, Name: {row[1]}, Email: {row[2]}")

            # 使用字典游标 (更方便)
            dict_cursor = connection.cursor(pymysql.cursors.DictCursor)
            dict_cursor.execute("SELECT * FROM users")
            dict_results = dict_cursor.fetchall()

            for user in dict_results:
                print(f"User: {user['name']}, Email: {user['email']}")

    except Exception as e:
        connection.rollback()
        print(f"Error: {e}")

    finally:
        connection.close()


# 创建 Base 类 (类似 JPA 的 @Entity)
Base = declarative_base()

"""
SQLAlchemy ORM 完整示例 - 修复所有问题
可以直接运行的版本
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, func, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

# 创建 Base 类
Base = declarative_base()


# 定义实体类
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    age = Column(Integer)
    created_at = Column(DateTime, default=datetime.now)

    # 一对多关系
    orders = relationship('Order', back_populates='user', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}', age={self.age})>"


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_no = Column(String(50), unique=True)
    amount = Column(Integer)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.now)

    # 多对一关系
    user = relationship('User', back_populates='orders')

    def __repr__(self):
        return f"<Order(id={self.id}, order_no='{self.order_no}', amount={self.amount})>"

def create_database_engine():
    """创建数据库引擎"""
    return create_engine(
        'mysql+pymysql://root:Koala_MySQL#20Xx..A..@192.168.2.148:43306/study?charset=utf8mb4',
        echo=False,  # 是否打印 SQL
        pool_size=10,  # 连接池大小 (类似 Spring 的 maximum-pool-size)
        max_overflow=20,  # 连接池最大溢出数
        pool_timeout=30,  # 获取连接超时时间(秒)
        pool_recycle=3600,  # 连接回收时间(秒)，防止 MySQL 8小时断开
        pool_pre_ping=True,  # 连接前检查是否有效 (推荐开启)
        echo_pool=False,  # 是否打印连接池日志
        connect_args={
            'charset': 'utf8mb4',
            'connect_timeout': 10,  # 连接超时
        }
    )

def demo_basic_crud():
    """基础 CRUD 操作"""
    print("\n" + "=" * 60)
    print("1. 基础 CRUD 操作")
    print("=" * 60)

    # 使用 SQLite 内存数据库（无需配置）
    engine = create_database_engine()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # === 创建 (Create) ===
        print("\n[创建数据]")
        user1 = User(name='张三', email='zhangsan@test.com', age=25)
        user2 = User(name='李四', email='lisi@test.com', age=30)
        user3 = User(name='王五', email='wangwu@test.com', age=28)

        session.add(user1)
        session.add_all([user2, user3])
        session.commit()
        print(f"✓ 创建了 3 个用户")

        # === 查询 (Read) ===
        print("\n[查询数据]")

        # 查询单个
        user = session.query(User).filter(User.id == 1).first()
        print(f"✓ 查询单个: {user}")

        # 查询所有
        all_users = session.query(User).all()
        print(f"✓ 查询所有: 共 {len(all_users)} 个用户")

        # 条件查询
        users = session.query(User).filter(User.age >= 28).order_by(User.age.desc()).all()
        print(f"✓ 年龄>=28: {users}")

        # 模糊查询
        users = session.query(User).filter(User.name.like('%张%')).all()
        print(f"✓ 姓名包含'张': {users}")

        # 多条件查询
        from sqlalchemy import and_, or_
        users = session.query(User).filter(
            and_(User.age > 25, User.name.like('%李%'))
        ).all()
        print(f"✓ 年龄>25且姓名包含'李': {users}")

        # 分页查询
        page_users = session.query(User).offset(0).limit(2).all()
        print(f"✓ 分页查询(前2条): {page_users}")

        # 聚合查询
        count = session.query(func.count(User.id)).scalar()
        avg_age = session.query(func.avg(User.age)).scalar()
        print(f"✓ 统计: 总数={count}, 平均年龄={avg_age:.1f}")

        # === 更新 (Update) ===
        print("\n[更新数据]")

        # 方式1: 先查询再更新
        user = session.query(User).filter(User.id == 1).first()
        user.age = 26
        session.commit()
        print(f"✓ 更新单个: {user}")

        # 方式2: 批量更新
        updated_count = session.query(User).filter(User.age < 30).update(
            {User.age: User.age + 1},
            synchronize_session=False
        )
        session.commit()
        print(f"✓ 批量更新: {updated_count} 条记录")

        # === 删除 (Delete) ===
        print("\n[删除数据]")

        # 方式1: 先查询再删除
        user = session.query(User).filter(User.name == '王五').first()
        if user:
            session.delete(user)
            session.commit()
            print(f"✓ 删除单个: 王五")

        # 方式2: 批量删除
        deleted_count = session.query(User).filter(User.age > 100).delete()
        session.commit()
        print(f"✓ 批量删除: {deleted_count} 条记录")

        # 查看最终结果
        final_users = session.query(User).all()
        print(f"\n最终剩余用户: {final_users}")

    finally:
        session.close()


def demo_relationships():
    """关联关系操作"""
    print("\n" + "=" * 60)
    print("2. 关联关系操作")
    print("=" * 60)

    engine = create_database_engine()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 创建用户和订单
        print("\n[创建关联数据]")
        user = User(name='赵六', email='zhaoliu@test.com', age=32)
        order1 = Order(order_no='ORD001', amount=100)
        order2 = Order(order_no='ORD002', amount=200)
        order3 = Order(order_no='ORD003', amount=300)

        # 设置关联关系
        user.orders = [order1, order2, order3]
        session.add(user)
        session.commit()
        print(f"✓ 创建用户和 3 个订单")

        # 懒加载查询
        print("\n[懒加载查询]")
        user = session.query(User).filter(User.id == user.id).first()
        print(f"用户: {user}")
        print(f"订单数量: {len(user.orders)}")  # 这里触发懒加载
        for order in user.orders:
            print(f"  {order}")

        # 急加载查询
        print("\n[急加载查询]")
        from sqlalchemy.orm import joinedload
        user = session.query(User).options(joinedload(User.orders)).first()
        print(f"用户: {user}")
        print(f"订单: {user.orders}")

        # JOIN 查询
        print("\n[JOIN 查询]")
        results = session.query(User, Order).join(Order).filter(User.age > 30).all()
        for user, order in results:
            print(f"{user.name} -> {order.order_no}: ¥{order.amount}")

        # 反向查询
        print("\n[反向查询]")
        order = session.query(Order).filter(Order.order_no == 'ORD001').first()
        print(f"订单 {order.order_no} 属于用户: {order.user.name}")

    finally:
        session.close()


def demo_subquery():
    """子查询操作 - 修复警告"""
    print("\n" + "=" * 60)
    print("3. 子查询操作 (修复版)")
    print("=" * 60)

    engine = create_database_engine()
    Base.metadata.create_all(engine)
    database_session = sessionmaker(bind=engine)
    session = database_session()

    try:
        # 准备数据
        user1 = User(name='张三', email='zhangsan@test.com', age=25)
        user2 = User(name='李四', email='lisi@test.com', age=30)
        session.add_all([user1, user2])
        session.commit()

        order1 = Order(order_no='ORD001', amount=150, user_id=user1.id)
        order2 = Order(order_no='ORD002', amount=50, user_id=user2.id)
        session.add_all([order1, order2])
        session.commit()

        # 方式1: 使用 scalar_subquery() (推荐)
        print("\n[方式1: scalar_subquery()]")
        subquery = session.query(Order.user_id).filter(Order.amount > 100).scalar_subquery()
        users = session.query(User).filter(User.id.in_(subquery)).all()
        print(f"有大额订单(>100)的用户: {users}")

        # 方式2: 使用 select()
        print("\n[方式2: select()]")
        subquery = session.query(Order.user_id).filter(Order.amount > 100).subquery()
        users = session.query(User).filter(User.id.in_(select(subquery.c.user_id))).all()
        print(f"有大额订单(>100)的用户: {users}")

        # EXISTS 子查询
        print("\n[EXISTS 子查询]")
        subquery = exists().where(
            and_(Order.user_id == User.id, Order.amount > 100)
        )
        users = session.query(User).filter(subquery).all()
        print(f"有大额订单(>100)的用户: {users}")

    finally:
        session.close()


def demo_transaction():
    """事务管理 - 修复版"""
    print("\n" + "=" * 60)
    print("4. 事务管理 (修复版)")
    print("=" * 60)

    engine = create_database_engine()
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    # 方式1: 自动事务管理 (推荐)
    print("\n[方式1: 自动事务管理]")
    session = Session()
    try:
        user = User(name='测试1', email='test1@test.com', age=20)
        session.add(user)
        session.commit()
        print("✓ 事务提交成功")
    except Exception as e:
        session.rollback()
        print(f"✗ 事务回滚: {e}")
    finally:
        session.close()

    # 方式2: 上下文管理器 (更安全)
    print("\n[方式2: 上下文管理器]")
    from contextlib import contextmanager

    @contextmanager
    def transaction_scope(Session):
        """提供事务作用域"""
        session = Session()
        try:
            yield session
            session.commit()
            print("✓ 事务提交成功")
        except Exception as e:
            session.rollback()
            print(f"✗ 事务回滚: {e}")
            raise
        finally:
            session.close()

    with transaction_scope(Session) as session:
        user = User(name='测试2', email='test2@test.com', age=21)
        session.add(user)

    # 方式3: 嵌套事务 (Savepoint)
    print("\n[方式3: 嵌套事务]")
    session = Session()
    try:
        user1 = User(name='测试3', email='test3@test.com', age=22)
        session.add(user1)

        # 创建 savepoint
        savepoint = session.begin_nested()
        try:
            user2 = User(name='测试4', email='test3@test.com', age=23)  # 故意重复邮箱
            session.add(user2)
            session.flush()
            savepoint.commit()
        except Exception as e:
            print(f"✗ Savepoint 回滚: {e}")
            savepoint.rollback()

        session.commit()
        print("✓ 外层事务提交成功")
    finally:
        session.close()


def demo_advanced_queries():
    """高级查询技巧"""
    print("\n" + "=" * 60)
    print("5. 高级查询技巧")
    print("=" * 60)

    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 准备数据
        users = [
            User(name='张三', email='zhangsan@test.com', age=25),
            User(name='李四', email='lisi@test.com', age=30),
            User(name='王五', email='wangwu@test.com', age=25),
            User(name='赵六', email='zhaoliu@test.com', age=35),
        ]
        session.add_all(users)
        session.commit()

        # 1. 分组统计
        print("\n[分组统计]")
        results = session.query(
            User.age,
            func.count(User.id).label('count')
        ).group_by(User.age).all()

        for age, count in results:
            print(f"年龄 {age}: {count} 人")

        # 2. HAVING 子句
        print("\n[HAVING 子句]")
        results = session.query(
            User.age,
            func.count(User.id).label('count')
        ).group_by(User.age).having(func.count(User.id) > 1).all()

        for age, count in results:
            print(f"年龄 {age}: {count} 人 (超过1人)")

        # 3. CASE 表达式
        print("\n[CASE 表达式]")
        from sqlalchemy import case

        age_group = case(
            (User.age < 30, '青年'),
            (User.age < 40, '中年'),
            else_='老年'
        ).label('age_group')

        results = session.query(User.name, User.age, age_group).all()
        for name, age, group in results:
            print(f"{name}({age}岁): {group}")

        # 4. 原生 SQL
        print("\n[原生 SQL]")
        from sqlalchemy import text

        result = session.execute(
            text("SELECT name, age FROM users WHERE age > :age"),
            {"age": 25}
        )
        for row in result:
            print(f"{row.name}: {row.age}岁")

    finally:
        session.close()


if __name__ == '__main__':
    # jdbc_basic()

    print("SQLAlchemy ORM 完整示例")
    print("=" * 60)

    # 运行所有示例
    demo_basic_crud()
    # demo_relationships()
    # demo_subquery()
    # demo_transaction()
    # demo_advanced_queries()

    print("\n" + "=" * 60)
    print("✓ 所有示例运行完成！")
    print("=" * 60)


# FastAPI 任务管理系统

一个基于 FastAPI 的现代任务管理系统，展示了 Python Web 开发的最佳实践。

## 🚀 功能特性

- **用户管理**
  - 用户注册和登录
  - JWT 令牌认证
  - 用户信息管理
  - 任务统计信息

- **任务管理**
  - 创建、查看、更新、删除任务
  - 任务状态管理（待办、进行中、已完成、已取消）
  - 任务优先级设置
  - 任务截止日期
  - 任务完成时间跟踪

- **API 文档**
  - 自动生成的 Swagger 文档
  - 交互式 API 测试界面

## 🛠️ 技术栈

- **Web 框架**: FastAPI
- **数据库**: SQLite + SQLAlchemy ORM
- **认证**: JWT (JSON Web Tokens)
- **数据验证**: Pydantic
- **测试**: pytest
- **代码质量**: black, flake8, mypy

## 📦 项目结构

```
web_project/
├── app/                    # 应用程序包
│   ├── __init__.py
│   ├── main.py            # FastAPI 应用入口
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py        # 用户模型
│   │   └── task.py        # 任务模型
│   ├── schemas/           # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── user.py        # 用户模式
│   │   └── task.py        # 任务模式
│   ├── api/               # API 路由
│   │   ├── __init__.py
│   │   ├── deps.py        # 依赖注入
│   │   ├── auth.py        # 认证 API
│   │   ├── users.py       # 用户 API
│   │   └── tasks.py       # 任务 API
│   └── utils/             # 工具函数
│       ├── __init__.py
│       ├── security.py    # 安全相关
│       └── helpers.py     # 辅助函数
├── tests/                 # 测试文件
├── requirements.txt       # 生产依赖
├── requirements-dev.txt   # 开发依赖
├── .env.example          # 环境变量示例
└── run.py                # 启动脚本
```

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd web_project
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，设置你的配置
```

### 5. 运行应用

```bash
python run.py
```

或者使用 uvicorn：

```bash
uvicorn app.main:app --reload
```

### 6. 访问应用

- **API 文档**: http://localhost:8000/docs
- **ReDoc 文档**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

## 🧪 运行测试

### 安装开发依赖

```bash
pip install -r requirements-dev.txt
```

### 运行测试

```bash
pytest
```

### 运行测试并查看覆盖率

```bash
pytest --cov=app
```

## 📚 API 使用示例

### 1. 用户注册

```bash
curl -X POST "http://localhost:8000/api/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "testuser",
       "email": "test@example.com",
       "password": "password123"
     }'
```

### 2. 用户登录

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=testuser&password=password123"
```

### 3. 创建任务

```bash
curl -X POST "http://localhost:8000/api/tasks/" \
     -H "Authorization: Bearer <your-token>" \
     -H "Content-Type: application/json" \
     -d '{
       "title": "学习 FastAPI",
       "description": "完成 FastAPI 教程",
       "priority": "high"
     }'
```

### 4. 获取任务列表

```bash
curl -X GET "http://localhost:8000/api/tasks/" \
     -H "Authorization: Bearer <your-token>"
```

## 🔧 开发工具

### 代码格式化

```bash
black app/ tests/
```

### 代码检查

```bash
flake8 app/ tests/
```

### 类型检查

```bash
mypy app/
```

## 🌟 特性说明

### 认证系统

- 使用 JWT 令牌进行认证
- 支持用户名或邮箱登录
- 密码使用 bcrypt 加密存储

### 数据库设计

- 用户表：存储用户基本信息
- 任务表：存储任务详情，与用户关联
- 支持任务状态和优先级管理

### API 设计

- RESTful API 设计
- 统一的错误处理
- 请求数据验证
- 响应数据序列化

### 安全性

- JWT 令牌认证
- 密码哈希存储
- CORS 配置
- 输入数据验证

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 📞 联系方式

如有问题，请联系：your.email@example.com

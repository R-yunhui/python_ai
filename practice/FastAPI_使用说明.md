# FastAPI 用户管理系统 - 使用说明

## 📋 项目概述

这是一个简单的 FastAPI 学习示例，实现了用户管理的完整 CRUD (增删改查) 功能。

## 🔧 安装依赖

在运行之前，请先安装必要的依赖包：

```bash
pip install fastapi uvicorn pydantic[email]
```

或者创建 requirements.txt：
```bash
pip install -r requirements.txt
```

requirements.txt 内容：
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic[email]==2.5.0
```

## 🚀 启动应用

### 方法1：使用 uvicorn 命令（推荐用于开发）
```bash
cd practice
uvicorn two_practice:app --reload
```

### 方法2：直接运行 Python 文件
```bash
python two_practice.py
```

## 📖 访问 API 文档

启动后，打开浏览器访问：

- **Swagger UI (交互式文档)**: http://localhost:8000/docs
  - 可以直接在浏览器中测试 API
  - 类似于 Java 的 Swagger/SpringDoc
  
- **ReDoc (备用文档)**: http://localhost:8000/redoc
  - 更美观的文档展示
  
- **API 根路径**: http://localhost:8000/

## 🔍 API 端点说明

### 1. 创建用户 (POST)
```bash
# 使用 curl
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "张三",
    "age": 25,
    "gender": "男",
    "email": "zhangsan@example.com"
  }'
```

### 2. 获取所有用户 (GET)
```bash
# 获取所有用户
curl "http://localhost:8000/users/"

# 带分页参数
curl "http://localhost:8000/users/?skip=0&limit=10"
```

### 3. 获取单个用户 (GET)
```bash
curl "http://localhost:8000/users/1"
```

### 4. 更新用户 (PUT)
```bash
curl -X PUT "http://localhost:8000/users/1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "张三（更新）",
    "age": 26
  }'
```

### 5. 删除用户 (DELETE)
```bash
curl -X DELETE "http://localhost:8000/users/1"
```

## 🎯 与 Java Spring Boot 的对比

| FastAPI | Spring Boot | 说明 |
|---------|-------------|------|
| `FastAPI()` | `@SpringBootApplication` | 应用实例 |
| `@app.get("/path")` | `@GetMapping("/path")` | GET 请求 |
| `@app.post("/path")` | `@PostMapping("/path")` | POST 请求 |
| `@app.put("/path")` | `@PutMapping("/path")` | PUT 请求 |
| `@app.delete("/path")` | `@DeleteMapping("/path")` | DELETE 请求 |
| `Pydantic BaseModel` | `@Valid` + DTO | 数据验证 |
| `HTTPException` | `ResponseStatusException` | 异常处理 |
| `status.HTTP_404_NOT_FOUND` | `HttpStatus.NOT_FOUND` | HTTP 状态码 |
| `{user_id}` 路径参数 | `@PathVariable` | 路径变量 |
| `Query()` 参数 | `@RequestParam` | 查询参数 |
| 装饰器 `@app.get()` | 注解 `@GetMapping` | 路由声明 |
| `async def` | `CompletableFuture` | 异步处理 |

## 📚 核心概念

### 1. Pydantic 模型
- **作用**：数据验证和序列化
- **对应 Java**：DTO + Bean Validation
- **特点**：自动类型检查、数据转换

### 2. 依赖注入
- **FastAPI**：通过参数类型注解自动注入
- **Spring**：通过 `@Autowired` 注入

### 3. 装饰器 vs 注解
- **Python**：使用 `@app.get()` 装饰器
- **Java**：使用 `@GetMapping` 注解
- **作用相同**：声明路由和请求方法

### 4. 异步处理
- **FastAPI**：原生支持 `async/await`
- **Spring**：需要配置异步支持

## 🔥 FastAPI 的优势

1. **自动生成文档** - 无需额外配置
2. **类型验证** - 基于 Python 类型提示
3. **高性能** - 接近 NodeJS 和 Go 的性能
4. **易学易用** - 代码简洁，学习曲线平缓
5. **异步支持** - 原生异步，适合 IO 密集型应用

## 📝 下一步学习建议

1. **数据库集成**
   - 学习 SQLAlchemy ORM（类似 JPA/Hibernate）
   - 使用真实数据库（PostgreSQL、MySQL）

2. **认证授权**
   - OAuth2 + JWT（类似 Spring Security）
   - 用户登录、权限管理

3. **依赖注入**
   - FastAPI 的 Depends 机制
   - 类似 Spring 的 DI 容器

4. **中间件**
   - CORS 配置
   - 日志记录
   - 异常处理中间件

5. **测试**
   - pytest + TestClient
   - 类似 JUnit + MockMvc

## 🆘 常见问题

### Q: 如何查看所有路由？
A: 访问 `/docs` 或 `/redoc` 即可看到所有 API 端点

### Q: 如何调试？
A: 在代码中使用 `print()` 或配置日志，控制台会实时显示

### Q: 如何部署？
A: 使用 Docker + uvicorn，或部署到云平台（Heroku、AWS、阿里云等）

### Q: 性能如何？
A: FastAPI 是目前最快的 Python Web 框架之一，性能接近 NodeJS

## 📞 参考资源

- **官方文档**：https://fastapi.tiangolo.com/zh/
- **中文教程**：https://fastapi.tiangolo.com/zh/tutorial/
- **GitHub**：https://github.com/tiangolo/fastapi

---

**提示**：对于有 Java 背景的开发者，FastAPI 的学习会非常顺畅。很多概念都是相通的，只是语法和实现方式不同。


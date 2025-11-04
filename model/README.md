# AI 对话系统 - Agent 架构版本

## 📋 项目简介

这是一个基于 **FastAPI + LangChain 0.3 + Agent** 架构的 AI 对话系统，支持：
- ✅ 真正的流式响应（逐字符输出，打字机效果）
- ✅ 多轮对话（自动管理历史记录）
- ✅ Agent 架构（可扩展工具调用）
- ✅ 美观的 Web 界面
- ✅ 支持本地大模型和 OpenAI 兼容 API

## 🏗️ 架构特点

### Agent 架构
```
用户输入 → Agent → LLM → 响应输出
              ↓
          工具调用（可扩展）
```

- 使用 `create_tool_calling_agent` 创建 Agent
- 使用 `RunnableWithMessageHistory` 自动管理对话历史
- 使用 `astream_events` 实现真正的流式输出

### 与传统方式对比

| 特性 | 传统方式 | Agent 架构 |
|------|---------|-----------|
| 历史管理 | 手动处理 | 自动管理 |
| 工具调用 | 需要自己实现 | 内置支持 |
| 流式输出 | 简单流式 | Token 级流式 |
| 扩展性 | 较低 | 很高 |

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置模型

编辑 `config.yaml`：

```yaml
llm:
  api_key: "your-api-key"
  base_url: "http://your-model-endpoint/v1"
  model: "your-model-name"
  temperature: 0.7
  max_tokens: 2000
```

### 3. 启动服务

```bash
# 方式1：直接运行
cd model
python chat_app.py

# 方式2：使用 uvicorn
uvicorn chat_app:app --reload --port 8001
```

### 4. 访问应用

- **Web 界面**: http://localhost:8001
- **API 文档**: http://localhost:8001/docs
- **ReDoc 文档**: http://localhost:8001/redoc

## 📖 API 接口说明

### 1. 普通对话（非流式）

```bash
POST /api/chat
Content-Type: application/json

{
  "message": "你好",
  "session_id": "可选的会话ID"
}
```

**响应：**
```json
{
  "session_id": "uuid",
  "message": "你好！我是你的 AI 助手..."
}
```

### 2. 流式对话（推荐）

```bash
POST /api/chat/stream
Content-Type: application/json

{
  "message": "讲个笑话",
  "session_id": "可选的会话ID"
}
```

**响应：** Server-Sent Events (SSE) 格式

```
data: {"session_id": "uuid", "type": "start"}

data: {"content": "好"}

data: {"content": "的"}

data: {"content": "，"}

data: {"type": "end"}
```

### 3. 其他接口

- `GET /api/history/{session_id}` - 获取对话历史
- `DELETE /api/history/{session_id}` - 清空对话历史
- `GET /api/sessions` - 获取所有活跃会话
- `POST /api/cleanup` - 清理过期会话
- `GET /api/config` - 获取配置信息

## 🔧 扩展工具

### 添加自定义工具

在 `chat_app.py` 中添加工具：

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气"""
    # 实现天气查询逻辑
    return f"{city}的天气是晴天"

# 在 create_agent_with_history 函数中添加工具
def create_agent_with_history():
    # ...
    tools = [get_current_time, get_weather]  # 添加新工具
    # ...
```

### 工具调用示例

参考 `langchain_demo/03_study/03_study_agent.py` 中的完整示例。

## 📁 项目结构

```
model/
├── chat_app.py          # 主应用程序（Agent 架构）
├── config.yaml          # 配置文件
├── chat_ui.html         # 前端界面
└── README.md            # 说明文档

requirements.txt         # 依赖清单
```

## 🎯 核心代码解析

### 1. Agent 创建

```python
def create_agent_with_history():
    # 1. 定义提示词（包含历史占位符）
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # 2. 创建 Agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # 3. 创建 Executor
    executor = AgentExecutor(agent, tools)
    
    # 4. 包装历史管理
    return RunnableWithMessageHistory(
        executor,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history"
    )
```

### 2. 流式响应

```python
async for event in agent_with_history.astream_events(
    {"input": message},
    config=RunnableConfig(configurable={"session_id": session_id}),
    version="v2"
):
    if event["event"] == "on_chat_model_stream":
        # 获取 token 级别的流式输出
        chunk = event["data"]["chunk"]
        yield chunk.content
```

## 🔍 常见问题

### Q: 流式输出没有打字机效果？

A: 确保：
1. 使用 `astream_events` 而不是 `stream`
2. 前端正确解析 SSE 事件
3. LLM 配置中 `streaming: true`

### Q: 如何切换不同的大模型？

A: 修改 `config.yaml` 中的配置：

```yaml
# OpenAI
llm:
  base_url: "https://api.openai.com/v1"
  model: "gpt-3.5-turbo"

# 本地模型（如 Ollama）
llm:
  base_url: "http://localhost:11434/v1"
  model: "qwen2.5:latest"
  
# DeepSeek
llm:
  base_url: "https://api.deepseek.com/v1"
  model: "deepseek-chat"
```

### Q: 历史记录存储在哪里？

A: 当前使用内存存储（`ChatMessageHistory`），重启后清空。如需持久化，可以：
1. 使用 `RedisChatMessageHistory`
2. 使用 `SQLChatMessageHistory`
3. 参考 LangChain 文档自定义存储

### Q: 如何调试 Agent？

A: 在 `create_agent_with_history` 中设置 `verbose=True`：

```python
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True  # 打印 Agent 思考过程
)
```

## 📚 参考资源

- **LangChain 官方文档**: https://python.langchain.com/docs/
- **FastAPI 文档**: https://fastapi.tiangolo.com/
- **Agent 完整示例**: `langchain_demo/03_study/03_study_agent.py`

## 🔄 版本历史

- **v1.0.0** (2024)
  - ✅ 基于 Agent 架构实现
  - ✅ 支持真正的流式输出
  - ✅ 自动历史管理
  - ✅ 可扩展工具系统

## 📝 待办事项

- [ ] 添加用户认证
- [ ] 持久化历史记录（Redis/MySQL）
- [ ] 添加更多实用工具（天气、搜索等）
- [ ] 支持文件上传和分析
- [ ] 添加对话导出功能

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License


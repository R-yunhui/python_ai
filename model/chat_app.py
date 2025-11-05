# ============================================================
# FastAPI + LangChain Agent 对话系统
# ============================================================
# 功能：基于 Agent 架构的 AI 对话系统，支持流式响应和多轮对话
# 技术栈：FastAPI + LangChain 0.3 + Agent + OpenAI API
# 参考：03_study_agent.py 的 Agent 实现方式

import os
import uuid
import yaml
import json
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel, Field, ConfigDict

# LangChain 0.3 核心导入
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.runnables import RunnableConfig
from langchain_community.chat_message_histories import ChatMessageHistory


# ============================================================
# 1. 加载配置文件
# ============================================================

def load_config():
    """加载 YAML 配置文件"""
    config_path = os.path.join(os.getcwd(), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()

# ============================================================
# 2. 创建 FastAPI 应用
# ============================================================

app = FastAPI(
    title=config["app"]["name"],
    version=config["app"]["version"],
    description="基于 Agent 架构的 AI 对话系统（LangChain 0.3）"
)

# ============================================================
# 3. 会话历史管理（使用 LangChain 的 ChatMessageHistory）
# ============================================================
# 这是 Agent 推荐的历史管理方式，与 03_study_agent.py 一致

# 全局会话历史存储：{session_id: ChatMessageHistory}
chat_history_store: Dict[str, ChatMessageHistory] = {}

# 会话元数据存储：{session_id: {"last_active": datetime}}
session_metadata: Dict[str, Dict] = defaultdict(lambda: {
    "last_active": datetime.now()
})


def get_session_history(session_id: str) -> ChatMessageHistory:
    """
    获取或创建会话历史
    
    这个函数会被 RunnableWithMessageHistory 自动调用
    类似于 03_study_agent.py 中的实现方式
    
    Args:
        session_id: 会话 ID
    
    Returns:
        ChatMessageHistory 实例
    """
    if session_id not in chat_history_store:
        chat_history_store[session_id] = ChatMessageHistory()

    # 更新最后活跃时间
    session_metadata[session_id]["last_active"] = datetime.now()

    return chat_history_store[session_id]


def clear_session_history(session_id: str):
    """清空指定会话的历史"""
    if session_id in chat_history_store:
        chat_history_store[session_id].clear()
        del chat_history_store[session_id]
    if session_id in session_metadata:
        del session_metadata[session_id]


def cleanup_expired_sessions() -> int:
    """清理过期的会话"""
    timeout = timedelta(minutes=config["conversation"]["session_timeout"])
    now = datetime.now()

    expired = [
        sid for sid, data in session_metadata.items()
        if now - data["last_active"] > timeout
    ]

    for sid in expired:
        clear_session_history(sid)

    return len(expired)


# ============================================================
# 4. 初始化 LangChain 大模型
# ============================================================

def get_llm():
    """
    创建 LangChain ChatOpenAI 实例
    支持 OpenAI 及兼容的 API（如本地模型、DeepSeek、智谱等）
    """
    llm_config = config["llm"]

    # 从环境变量或配置文件获取 API Key
    api_key = os.getenv("OPENAI_API_KEY") or llm_config.get("api_key")

    # API Key 可以为 None（某些本地模型不需要）
    return ChatOpenAI(
        model=llm_config["model"],
        temperature=llm_config["temperature"],
        max_tokens=llm_config["max_tokens"],
        api_key=api_key or "not-needed",  # 本地模型可能不需要
        base_url=llm_config.get("base_url"),
        streaming=llm_config["streaming"]
    )


# ============================================================
# 5. 创建 Agent（参考 03_study_agent.py）
# ============================================================

def create_agent_with_history():
    """
    创建带历史记录的 Agent
    
    架构说明：
    1. 使用 create_tool_calling_agent 创建 Agent（即使暂时没有工具）
    2. 使用 AgentExecutor 执行 Agent
    3. 使用 RunnableWithMessageHistory 包装，自动管理历史
    
    这种架构的优势：
    - 统一的接口，后续添加工具非常简单
    - 自动管理对话历史，无需手动处理
    - 支持流式输出
    
    Returns:
        带历史记录的 Agent Executor
    """

    # 1. 定义提示词模板（与 03_study_agent.py 类似）
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", config["prompts"]["system"]),
        # 对话历史占位符（Agent 会自动填充）
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        # 用户输入
        ("human", "{input}"),
        # Agent 的思考过程（工具调用记录，即使没有工具也需要）
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # 2. 定义工具列表（目前为空，后续可扩展）
    tools = [get_current_time]

    # 3. 创建 Agent
    # 注意：即使没有工具，也使用 create_tool_calling_agent
    # 这样后续添加工具时无需修改架构
    agent = create_tool_calling_agent(
        llm=get_llm(),
        prompt=prompt_template,
        tools=tools,
    )

    # 4. 创建 AgentExecutor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,  # 是否打印 Agent 思考过程（调试时可改为 True）
        handle_parsing_errors=True,  # 自动处理解析错误
        max_iterations=5  # 最大迭代次数（没有工具时通常1次就够）
    )

    # 5. 包装为带历史记录的 Runnable
    # 这是 LangChain 0.3 推荐的方式
    agent_history = RunnableWithMessageHistory(
        agent_executor,
        get_session_history,  # 历史获取函数
        input_messages_key="input",  # 输入键名
        history_messages_key="chat_history"  # 历史键名
    )

    return agent_history


@tool
def get_current_time():
    """获取当前时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# 创建全局 Agent 实例
agent_with_history = create_agent_with_history()


# ============================================================
# 6. Pydantic 模型定义
# ============================================================

class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str = Field(..., min_length=1, description="用户消息")
    session_id: Optional[str] = Field(None, description="会话 ID（可选，用于多轮对话）")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "你好，请介绍一下自己",
                "session_id": "123e4567-e89b-12d3-a456-426614174000"
            }
        }
    )


class ChatResponse(BaseModel):
    """聊天响应模型"""
    session_id: str = Field(..., description="会话 ID")
    message: str = Field(..., description="AI 回复")


class SessionInfo(BaseModel):
    """会话信息模型"""
    session_id: str
    message_count: int
    last_active: str


# ============================================================
# 7. API 路由定义
# ============================================================

@app.get("/", response_class=HTMLResponse, tags=["页面"])
async def index():
    """返回前端聊天页面"""
    html_path = os.path.join(os.getcwd(), "chat_ui.html")
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return """
        <html>
            <body>
                <h1>聊天页面未找到</h1>
                <p>请确保 chat_ui.html 文件存在</p>
            </body>
        </html>
        """


@app.post("/api/chat", response_model=ChatResponse, tags=["对话"])
async def chat(request: ChatRequest):
    """
    普通对话接口（非流式）- 使用 Agent 架构
    
    - **message**: 用户消息内容
    - **session_id**: 会话 ID（可选）
    """
    try:
        # 生成或使用会话 ID
        session_id = request.session_id or str(uuid.uuid4())

        # 调用 Agent（带历史记录）
        # 参考 03_study_agent.py 的调用方式
        response = agent_with_history.invoke(
            {"input": request.message},
            config=RunnableConfig(
                configurable={"session_id": session_id}
            )
        )

        # Agent 返回的是字典，包含 'output' 键
        ai_message = response['output']

        return ChatResponse(
            session_id=session_id,
            message=ai_message
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"对话失败: {str(e)}"
        )


@app.post("/api/chat/stream", tags=["对话"])
async def chat_stream(request: ChatRequest):
    """
    流式对话接口 - 真正的逐字符流式响应（打字机效果）
    
    实现方式：使用 astream_events 获取 LLM 层面的 token 级别事件
    
    - **message**: 用户消息内容
    - **session_id**: 会话 ID（可选）
    """
    try:
        # 生成或使用会话 ID
        session_id = request.session_id or str(uuid.uuid4())

        # 流式生成器函数
        async def generate():
            """生成真正的流式响应"""
            try:
                full_response = ""

                # 首先发送会话 ID
                yield f"data: {json.dumps({'session_id': session_id, 'type': 'start'}, ensure_ascii=False)}\n\n"

                # 使用 astream_events 获取详细的事件流
                # 这是 LangChain 0.3 推荐的流式方式，可以获取 token 级别的事件
                async for event in agent_with_history.astream_events(
                        {"input": request.message},
                        config=RunnableConfig(
                            configurable={"session_id": session_id}
                        ),
                        version="v2"  # 使用 v2 版本的事件流
                ):
                    kind = event["event"]

                    # 只处理 LLM 的 token 事件（逐字符输出）
                    if kind == "on_chat_model_stream":
                        # 从 LLM 获取的 token
                        chunk = event["data"]["chunk"]
                        if hasattr(chunk, "content") and chunk.content:
                            full_response += chunk.content
                            # 立即发送，实现真正的流式效果
                            yield f"data: {json.dumps({'content': chunk.content}, ensure_ascii=False)}\n\n"

                # 发送结束标记
                yield f"data: {json.dumps({'type': 'end'}, ensure_ascii=False)}\n\n"

            except Exception as ex:
                error_msg = f"流式生成错误: {str(ex)}"
                print(f"错误详情: {ex}")
                import traceback
                traceback.print_exc()
                yield f"data: {json.dumps({'type': 'error', 'message': error_msg}, ensure_ascii=False)}\n\n"

        # 返回流式响应
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"流式对话失败: {str(e)}"
        )


@app.get("/api/history/{session_id}", tags=["历史"])
async def get_history(session_id: str):
    """
    获取指定会话的对话历史
    
    - **session_id**: 会话 ID
    """
    if session_id not in chat_history_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )

    history = chat_history_store[session_id]

    # 转换为简单的字典格式
    messages = []
    for msg in history.messages:
        messages.append({
            "role": msg.type,  # 'human', 'ai', 'system'
            "content": msg.content
        })

    return {"session_id": session_id, "messages": messages}


@app.delete("/api/history/{session_id}", tags=["历史"])
async def clear_history(session_id: str):
    """
    清空指定会话的对话历史
    
    - **session_id**: 会话 ID
    """
    clear_session_history(session_id)
    return {"message": "会话历史已清空", "session_id": session_id}


@app.get("/api/sessions", response_model=List[SessionInfo], tags=["会话"])
async def list_sessions():
    """获取所有活跃的会话列表"""
    sessions = []
    for sid, history in chat_history_store.items():
        if sid in session_metadata:
            sessions.append(SessionInfo(
                session_id=sid,
                message_count=len(history.messages),
                last_active=session_metadata[sid]["last_active"].strftime("%Y-%m-%d %H:%M:%S")
            ))
    return sessions


@app.post("/api/cleanup", tags=["维护"])
async def cleanup_sessions():
    """清理过期的会话"""
    count = cleanup_expired_sessions()
    return {"message": f"已清理 {count} 个过期会话"}


@app.get("/api/config", tags=["配置"])
async def get_config_info():
    """获取当前配置信息（不包含敏感信息）"""
    return {
        "app": config["app"],
        "llm": {
            "model": config["llm"]["model"],
            "temperature": config["llm"]["temperature"],
            "max_tokens": config["llm"]["max_tokens"],
            "streaming": config["llm"]["streaming"]
        },
        "conversation": config["conversation"],
        "architecture": {
            "framework": "LangChain 0.3",
            "agent_type": "Tool Calling Agent",
            "history_management": "RunnableWithMessageHistory",
            "tools_enabled": True  # 后续可添加工具
        }
    }


# ============================================================
# 8. 启动应用
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("🚀 启动 AI 对话系统（Agent 架构 - LangChain 0.3）")
    print("=" * 70)
    print(f"📝 应用名称: {config['app']['name']}")
    print(f"🔢 版本: {config['app']['version']}")
    print(f"🤖 模型: {config['llm']['model']}")
    print(f"🏗️  架构: Agent (Tool Calling Agent)")
    print(f"📚 历史管理: RunnableWithMessageHistory")
    print(f"🔧 工具: 暂无（架构支持后续扩展）")
    print(f"🌐 访问地址: http://localhost:{config['app']['port']}")
    print(f"📖 API 文档: http://localhost:{config['app']['port']}/docs")
    print("=" * 70)

    uvicorn.run(
        app="chat_app:app",
        host=config["app"]["host"],
        port=config["app"]["port"],
        reload=True
    )

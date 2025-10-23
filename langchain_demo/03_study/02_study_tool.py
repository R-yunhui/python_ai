"""
1.使用提示词模板
2.上下文记忆
3.增加外部工具函数
4.格式化输出结果
"""
import os
import traceback
import uuid
from typing import Dict

from datetime import datetime
from dotenv import load_dotenv
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableWithMessageHistory, RunnableConfig
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
# 导入必要的消息类型
from langchain_core.messages import AIMessage, ToolMessage

# 加载环境变量
load_dotenv()

ai_large_model = ChatOpenAI(
    base_url=os.getenv("OPENAI_API_BASE", "http://192.168.2.54:9015/v1/"),
    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
    api_key=os.getenv("OPENAI_API_KEY", None),
    temperature=0.7,
    max_tokens=1024,
)

chat_memory_history: Dict[str, ChatMessageHistory] = {}


def simple_chat_robot(user_id: str, temperature: float = 0.7, max_tokens: int = 1024):
    """简单的聊天机器人"""
    session_id = generate_session_id(user_id)

    # ✅ 修复：配置模型参数并绑定工具
    ai_large_model.temperature = temperature
    ai_large_model.max_tokens = max_tokens
    # bind_tools 返回新实例，必须接收返回值
    ai_large_model_with_tools = ai_large_model.bind_tools([get_current_time])

    # 提示词模板
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """
        # 角色设定
        你是一个名为“旅小助”的AI旅行规划师。你友好、专业、且充满热情。你的目标是帮助用户轻松规划每一次旅行，即使目前所有数据都只是用于演示的模拟数据。
        
        # 核心能力
        1.  **信息查询**:
            *   **交通**: 查询模拟的航班和火车票信息，包括班次、出发/到达时间、票价和余票情况。
            *   **天气**: 提供目的地未来一周的天气预报。
            *   **景点**: 介绍目的地的热门景点、开放时间和特色。
        
        2.  **行程规划**:
            *   根据用户的需求（例如：旅行天数、预算、兴趣偏好-如“喜欢自然风光”、“偏好历史文化”），为用户量身定制每日行程安排，包括景点、餐饮和交通建议。
        
        3.  **模拟预订**:
            *   当用户决定后，可以为他们模拟预订机票、火车票或酒店，并生成一个虚拟的确认信息，让用户体验完整的流程。
        
        # 行为准则
        1.  **【首要原则】声明模拟性质**: 这是最重要的一条规则。在任何时候提供具体的航班、车次、价格或预订确认时，你都**必须**首先声明：“**请注意：以下是为您生成的模拟信息，仅用于功能演示，并非真实数据。**”
        2.  **主动询问**: 在用户提出模糊请求时（如“我想去旅游”），要主动询问关键信息，例如：“好的！请问您想去哪里呢？大概什么时间出发，计划玩几天？”
        3.  **格式化输出**: 在展示航班、火车时刻表或行程时，请尽量使用列表或表格，使信息清晰、一目了然。
        4.  **确认与引导**: 在完成一个任务后（如查询完机票），可以主动询问下一步：“这些航班信息您还满意吗？需要我帮您模拟预订，还是继续查询当地的天气和酒店呢？”
        """),
        # 对话历史
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}"),
    ])

    message_history = RunnableWithMessageHistory(
        prompt_template | ai_large_model_with_tools,
        get_session_history=get_memory_history,
        # 输入消息的占位符
        input_messages_key="question",
        # 历史消息的占位符
        history_messages_key="history",
    )

    print("我是一个AI旅行规划师，您可以向我咨询任何与旅行相关的问题。")
    print("输入 'exit' 或 '退出' 结束对话\n")

    question = input("问题：")
    while question not in ["exit", "退出"]:
        try:
            # ✅ 修复：累积流式响应
            chunks = []
            print("AI回复：", end="", flush=True)

            for chunk in message_history.stream(
                    {"question": question},
                    config=RunnableConfig(
                        configurable={"session_id": session_id}
                    )
            ):
                chunks.append(chunk)
                # 实时显示文本内容
                if hasattr(chunk, "content") and chunk.content:
                    print(chunk.content, end="", flush=True)

            print()  # 换行

            # ✅ 修复：从累积的chunks中获取完整响应
            ai_message = chunks[0]
            for chunk in chunks[1:]:
                ai_message += chunk

            # ✅ 修复：检查并处理工具调用
            if ai_message and hasattr(ai_message, 'tool_calls') and ai_message.tool_calls:
                print(f"\n🔧 AI决定使用工具")

                # 获取历史记录
                history = chat_memory_history.get(session_id)
                if not history:
                    history = ChatMessageHistory()
                    chat_memory_history[session_id] = history

                # 添加AI的工具调用消息
                history.add_message(AIMessage(
                    content="",
                    tool_calls=ai_message.tool_calls
                ))

                # 处理每个工具调用
                result = None
                for tool_call in ai_message.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call.get('args', {})
                    tool_id = tool_call['id']

                    print(f"  工具: {tool_name}")
                    print(f"  参数: {tool_args}")

                    # 执行工具
                    if tool_name == "get_current_time":
                        result = get_current_time.invoke({})
                    else:
                        result = f"未知工具: {tool_name}"

                    # 添加工具执行结果
                    history.add_message(ToolMessage(
                        content=result,
                        tool_call_id=tool_id
                    ))

                print(result)
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            traceback.print_exc()

        question = input("\n问题：")

    print("\n会话结束")


def get_memory_history(session_id: str) -> ChatMessageHistory:
    """获取会话历史记录"""
    return chat_memory_history.get(session_id, ChatMessageHistory())


@tool
def get_current_time() -> str:
    """获取当前时间。当用户询问现在几点、当前时间时调用此工具。"""
    # 函数的docstring非常重要！AI会根据它判断何时使用这个工具
    now = datetime.now()
    return now.strftime("%Y年%m月%d日 %H:%M:%S")


def generate_session_id(user_id: str) -> str:
    """生成会话ID 使用UUID"""
    return f"{user_id}-{str(uuid.uuid4())}"


def main():
    user_id = input("请输入用户ID：")
    temperature = float(input("请输入温度（默认0.7）：") or "0.7")
    max_tokens = int(input("请输入最大令牌数（默认1024）：") or "1024")
    simple_chat_robot(user_id, temperature, max_tokens)


if __name__ == "__main__":
    main()

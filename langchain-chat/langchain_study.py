import json

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from langchain.chains import ConversationChain
from pydantic import BaseModel
from datetime import datetime

# 初始化大模型
llm = ChatOpenAI(
    model="qwen2.5-vl-72b-instruct",
    api_key="93e5f02e99061db3b6113e8db46a0fbd",
    base_url="http://192.168.2.54:9015/v1/",
    max_retries=3,
    temperature=0.7,
    timeout=20
)


def langchain_chat(user_question):
    """简单的聊天函数"""
    try:
        data = llm.invoke(user_question)
        return data.content
    except Exception as e:
        print(f"大模型调用出错：{e}")
        return None


def langchain_chat_with_stream(user_question):
    messages = [
        SystemMessage(content="你是一个专业的翻译，将用户输入的中文翻译成英文"),
        HumanMessage(content=user_question)
    ]

    data = ""
    for chunk in llm.stream(messages):
        data += chunk.content
    else:
        return data


def langchain_chat_with_tools(user_question):
    """使用工具的聊天函数"""
    try:
        # 定义工具列表
        tools = [get_current_time, add_tool]
        # 绑定工具到LLM
        llm_with_tools = llm.bind_tools(tools)

        # 初始消息
        messages = [HumanMessage(content=user_question)]

        # 开始对话循环
        max_turns = 5  # 最大对话轮次，防止无限循环
        for _ in range(max_turns):
            # 调用大模型
            ai_message = llm_with_tools.invoke(messages)
            print(f"AI响应: {ai_message.content}")

            # 将AI回复添加到消息列表
            messages.append(ai_message)

            # 检查是否有工具调用
            if hasattr(ai_message, 'tool_calls') and ai_message.tool_calls:
                print(f"检测到工具调用: {ai_message.tool_calls}")

                # 处理每个工具调用
                for tool_call in ai_message.tool_calls:
                    tool_name = tool_call['name']
                    tool_args = tool_call['args']

                    # 查找对应的工具函数
                    tool_func = None
                    for cur_tool in tools:
                        if cur_tool.name == tool_name:
                            tool_func = cur_tool
                            break

                    if tool_func:
                        # 调用工具并获取结果
                        print(f"调用工具 {tool_name} 参数: {tool_args}")
                        tool_result = tool_func.invoke(tool_args)
                        print(f"工具返回结果: {tool_result}")

                        # 添加工具响应到消息列表
                        messages.append(
                            HumanMessage(
                                content=f"工具 '{tool_name}' 的执行结果: {tool_result}"
                            )
                        )
                    else:
                        print(f"找不到工具: {tool_name}")
            else:
                # 如果没有工具调用，对话结束
                return ai_message.content

        return "达到最大对话轮次"
    except Exception as e:
        print(f"大模型调用出错：{e}")
        return None


@tool()
def get_current_time():
    """获取当前时间"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def add_tool(a: float, b: float) -> str:
    """返回两个数的和。"""
    return json.dumps({"result": a + b})


# 演示程序入口
if __name__ == "__main__":
    print("LangChain演示程序")
    print("1. 简单对话")
    print("2. 流式对话")
    print("3. 工具调用对话")

    choice = input("请选择演示类型 (1-3): ")

    if choice == "1":
        question = input("请输入您想问的问题: ")
        content = langchain_chat(question)
        print(f"大模型返回的正文信息：{content}")
    elif choice == "2":
        question = input("请输入要翻译的中文: ")
        content = langchain_chat_with_stream(question)
        print(f"翻译结果：{content}")
    elif choice == "3":
        question = input("请输入您的问题 (例如：'现在几点了？' 或 '1加2等于多少？'): ")
        result = langchain_chat_with_tools(question)
        print(f"最终结果：{result}")
    else:
        print("无效的选择，请输入1-3之间的数字")

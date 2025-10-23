import os
from typing import Dict

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableWithMessageHistory, RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.prompts import MessagesPlaceholder

# ============================================================================
# 第一步：加载环境变量（读取.env文件中的API密钥）
# ============================================================================
load_dotenv()  # 这会自动读取当前目录下的.env文件

large_model_ai = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
    temperature=0.7,
    max_tokens=1024,
    max_retries=3,
    api_key=os.getenv("OPENAI_API_KEY", "93e5f02e99061db3b6113e8db46a0fbd"),
    base_url=os.getenv("OPENAI_API_BASE_URL", "http://192.168.2.54:9015/v1/"),
)


def simple_chat():
    """
    简单的聊天函数，用于与大模型交互
    """
    print("欢迎使用简单聊天系统！输入 'exit' 退出, 请输入您的问题：")
    question = input()
    while question.strip() != "exit":
        chunk_list = large_model_ai.stream(question)
        for chunk in chunk_list:
            print(chunk.content, end="")
        print()
        question = input()
    else:
        print("感谢使用，再见！")


def chat_with_prompt_template():
    """
    聊天函数，使用提示模板与大模型交互
    """
    print("=" * 60)
    print("聊天提示词模板")
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的聊天助手，是用通俗易懂的语言回答用户有关于{topic}相关的问题。"),
        ("human", "请回答：{question}")
    ])

    # 使用管道的方式创建链
    chain = prompt_template | large_model_ai
    # 调用链，直接得到Person对象
    topic = input("主题：")
    question = input("问题：")
    result = chain.stream({"topic": topic, "question": question})
    for chunk in result:
        print(chunk.content, end="")

# 存储会话历史（简单的内存存储）
store: Dict[str, ChatMessageHistory] = {}

def get_session_history(session_id: str):
    """获取或创建会话历史"""
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def chat_with_conversation_memory():
    """
    聊天函数，使用提示模板与大模型交互包含多轮对话的上下文记忆
    目前采用简单的上下文记忆 langchain 的 ConversationBufferMemory
    """
    print("=" * 60)
    print("多轮对话包含上下文记忆")

    # 创建提示词模板（注意添加MessagesPlaceholder）
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的聊天助手，用通俗易懂的语言回答用户有关于{topic}相关的问题。
你会根据用户的问题和之前的对话历史，提供准确的回答。"""),
        MessagesPlaceholder(variable_name="history"),  # 历史消息占位符
        ("human", "{question}")
    ])

    # 创建链
    chain = prompt_template | large_model_ai
    
    # 使用RunnableWithMessageHistory包装链
    conversation_chain = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="history",
    )

    print("欢迎使用多轮对话包含上下文记忆系统！输入 'exit' 退出, 请输入您的问题：")
    topic = input("主题：")
    session_id = "demo_session_001"  # 会话ID
    
    question = input("问题：")
    while question.strip() not in ["exit"]:
        # 使用stream获取流式输出，注意config参数
        result = conversation_chain.stream(
            {"topic": topic, "question": question},
            config=RunnableConfig(
                # 设置会话id。通过 session_id 获取会话历史
                configurable={"session_id": session_id}
            ))

        print("AI: ", end="")
        for chunk in result:
            if hasattr(chunk, "content"):
                print(chunk.content, end="", flush=True)
        print()
        
        question = input("问题：")
    else:
        print("感谢使用，再见！")


def main():
    # simple_chat()
    # chat_with_prompt_template()
    chat_with_conversation_memory()


if __name__ == '__main__':
    main()

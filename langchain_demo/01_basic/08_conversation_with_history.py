"""
LangChain学习 - RunnableWithMessageHistory（新版对话记忆）

学习目标：
1. 理解RunnableWithMessageHistory的用法（替代ConversationChain）
2. 掌握如何管理多个会话的历史记录
3. 学会结合提示词模板实现对话记忆
4. 了解新旧API的区别

重要：
ConversationChain已经被弃用！
推荐使用：RunnableWithMessageHistory + ChatMessageHistory
"""

import os
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from typing import Dict

# 加载环境变量
load_dotenv()

# ============================================================================
# 为什么要从ConversationChain迁移到RunnableWithMessageHistory？
# ============================================================================
"""
旧方式（已弃用）：
    from langchain.chains import ConversationChain
    conversation = ConversationChain(llm=llm)
    
问题：
- ConversationChain是高度封装的，不够灵活
- 难以自定义提示词
- 不支持多用户会话管理

新方式（推荐）：
    chain = prompt | llm
    with_message_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        ...
    )
    
优势：
✅ 更灵活的链式组合
✅ 完全自定义提示词
✅ 支持多用户会话管理
✅ 更好的性能和可维护性
"""

# ============================================================================
# 会话历史存储（内存版）
# ============================================================================

# 存储所有用户的聊天历史
# 在实际项目中，应该使用Redis或数据库
store: Dict[str, ChatMessageHistory] = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    获取或创建会话历史
    
    参数:
        session_id: 会话ID（如用户ID、房间ID等）
        
    返回:
        该会话的消息历史对象
    """
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


# ============================================================================
# 示例1：基础的对话记忆
# ============================================================================
def example1_basic_conversation():
    """
    演示如何使用RunnableWithMessageHistory实现基础对话记忆
    """
    print("\n" + "=" * 60)
    print("示例1：基础对话记忆")
    print("=" * 60)

    # 1. 创建提示词模板（注意添加MessagesPlaceholder）
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个友好的AI助手。"),
        MessagesPlaceholder(variable_name="history"),  # 历史消息占位符
        ("human", "{input}")
    ])

    # 2. 初始化模型
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )

    # 3. 创建链
    chain = prompt | llm

    # 4. 包装成带历史记录的链
    with_message_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    # 5. 开始对话
    session_id = "user_001"

    conversations = [
        "你好！我叫小明。",
        "我叫什么名字？",
        "今天天气真好！",
        "我刚才说了什么？"
    ]

    for i, user_input in enumerate(conversations, 1):
        print(f"\n【第{i}轮对话】")
        print(f"用户: {user_input}")

        # 调用链，config中指定session_id
        response = with_message_history.stream(
            {"input": user_input},
            config=RunnableConfig(
                # 设置会话id。通过 session_id 获取会话历史
                configurable={"session_id": session_id}
            )
        )

        # 打印流式输出
        print("AI: ", end="")
        for chunk in response:
            if hasattr(chunk, "content"):
                print(chunk.content, end="", flush=True)
        print()

    # 6. 查看历史记录
    print("\n" + "=" * 60)
    print("📝 完整对话历史：")
    history = store[session_id]
    for msg in history.messages:
        role = "用户" if msg.type == "human" else "AI"
        print(f"{role}: {msg.content}")


# ============================================================================
# 示例2：多用户会话管理
# ============================================================================
def example2_multi_user_sessions():
    """
    演示如何管理多个用户的独立会话
    这是实际应用中最重要的功能
    """
    print("\n" + "=" * 60)
    print("示例2：多用户会话管理")
    print("=" * 60)

    # 创建提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的客服助手。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

    # 初始化模型
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )

    # 创建带历史的链
    chain = prompt | llm
    with_message_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    # 模拟两个用户的对话
    users = {
        "user_alice": [
            "你好，我想咨询一下订单问题。",
            "我的订单号是12345，还没发货。"
        ],
        "user_bob": [
            "你好，我要退款。",
            "订单号是67890。"
        ]
    }

    # 分别处理两个用户的对话
    for user_id, messages in users.items():
        print(f"\n{'=' * 40}")
        print(f"用户: {user_id}")
        print('=' * 40)

        for msg in messages:
            print(f"\n{user_id}: {msg}")

            response = with_message_history.stream(
                {"input": msg},
                config=RunnableConfig(
                    # 设置会话id。通过 session_id 获取会话历史
                    configurable={"session_id": user_id}
                )
            )

            # 打印流式输出
            print("客服: ", end="")
            for chunk in response:
                if hasattr(chunk, "content"):
                    print(chunk.content, end="", flush=True)
            print()

    # 验证历史记录是独立的
    print("\n" + "=" * 60)
    print("验证：每个用户的历史记录是独立的")
    print("=" * 60)

    for user_id in users.keys():
        print(f"\n{user_id}的对话历史：")
        history = store[user_id]
        print(f"消息数量: {len(history.messages)}")
        for msg in history.messages[-2:]:  # 只显示最后2条
            role = "用户" if msg.type == "human" else "客服"
            content = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
            print(f"  {role}: {content}")


# ============================================================================
# 示例3：带主题的对话（完整实用示例）
# ============================================================================
def example3_topic_based_conversation():
    """
    演示一个完整的实用场景：主题专家助手
    结合自定义提示词和会话管理
    """
    print("\n" + "=" * 60)
    print("示例3：主题专家助手（完整实用示例）")
    print("=" * 60)

    # 创建带主题的提示词模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个{topic}专家。
你的职责是：
1. 用专业但通俗易懂的语言回答问题
2. 记住之前的对话内容
3. 根据用户的背景（{user_background}）调整回答深度
4. 保持友好和耐心

请基于对话历史，给出恰当的回答。"""),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

    # 初始化模型
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )

    # 创建链
    chain = prompt | llm
    with_message_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    # 模拟一个学习会话
    session_id = "learning_session_001"
    topic = "Python编程"
    user_background = "有Java经验的初学者"

    questions = [
        "什么是装饰器？",
        "能给我举个实际应用的例子吗？",
        "装饰器和Java的注解有什么区别？",
        "我刚才问的第一个问题是什么？"
    ]

    print(f"\n主题: {topic}")
    print(f"用户背景: {user_background}\n")
    print("=" * 60)

    for i, question in enumerate(questions, 1):
        print(f"\n【第{i}轮】")
        print(f"学生: {question}")

        response = with_message_history.invoke(
            {
                "input": question,
                "topic": topic,
                "user_background": user_background
            },
            config=RunnableConfig(
                # 设置会话id。通过 session_id 获取会话历史
                configurable={"session_id": session_id}
            )        )

        print(f"老师: {response.content}")
        print("-" * 60)


# ============================================================================
# 示例4：交互式对话（可以实际运行）
# ============================================================================
def example4_interactive_chat():
    """
    交互式对话示例
    可以让用户实际输入并体验对话记忆
    """
    print("\n" + "=" * 60)
    print("示例4：交互式对话")
    print("=" * 60)
    print("\n提示: 输入 'exit' 退出对话，'history' 查看历史\n")

    # 创建提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个友好的AI助手。
特点：
- 记住用户说过的所有内容
- 根据上下文给出恰当回复
- 可以回答之前讨论过的话题"""),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])

    # 初始化
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )

    chain = prompt | llm
    with_message_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    # 生成唯一的会话ID
    import time
    session_id = f"interactive_{int(time.time())}"

    print(f"会话ID: {session_id}")
    print("开始对话...")

    while True:
        try:
            user_input = input("\n你: ").strip()

            if not user_input:
                continue

            if user_input.lower() == 'exit':
                print("\n感谢使用，再见！")
                break

            if user_input.lower() == 'history':
                print("\n📝 对话历史：")
                if session_id in store:
                    history = store[session_id]
                    for msg in history.messages:
                        role = "你" if msg.type == "human" else "AI"
                        print(f"{role}: {msg.content}")
                else:
                    print("暂无历史记录")
                continue

            # 调用AI
            response = with_message_history.invoke(
                {"input": user_input},
                config=RunnableConfig(
                    # 设置会话id。通过 session_id 获取会话历史
                    configurable={"session_id": session_id}
                )            )

            print(f"AI: {response.content}")

        except KeyboardInterrupt:
            print("\n\n对话已中断")
            break
        except Exception as e:
            print(f"\n错误: {e}")


# ============================================================================
# 对比：旧API vs 新API
# ============================================================================
def compare_old_vs_new():
    """
    对比旧的ConversationChain和新的RunnableWithMessageHistory
    """
    print("\n" + "=" * 60)
    print("旧API vs 新API对比")
    print("=" * 60)

    print("""
旧方式（ConversationChain - 已弃用）：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

# 创建
memory = ConversationBufferMemory()
conversation = ConversationChain(
    llm=llm,
    memory=memory
)

# 使用
response = conversation.predict(input="你好")

缺点：
❌ 提示词不灵活，难以自定义
❌ 不支持多用户会话
❌ 性能较差
❌ 已被标记为废弃


新方式（RunnableWithMessageHistory - 推荐）：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# 1. 创建自定义提示词
prompt = ChatPromptTemplate.from_messages([
    ("system", "自定义系统提示..."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

# 2. 创建链
chain = prompt | llm

# 3. 添加历史记录功能
with_message_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
)

# 4. 使用（支持多会话）
response = with_message_history.invoke(
    {"input": "你好"},
    config={"configurable": {"session_id": "user_123"}}
)

优点：
✅ 完全自定义提示词
✅ 支持多用户会话管理
✅ 链式组合更灵活
✅ 性能更好
✅ 官方推荐，长期支持


实际应用建议：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Web应用：每个用户一个session_id（用户ID）
2. 聊天室：每个房间一个session_id（房间ID）
3. 多轮对话：使用唯一标识符作为session_id
4. 持久化：将ChatMessageHistory替换为数据库存储

代码迁移步骤：
1. 替换 ConversationChain -> RunnableWithMessageHistory
2. 创建 get_session_history 函数
3. 在提示词中添加 MessagesPlaceholder
4. 调用时传入 config={"configurable": {"session_id": ...}}
    """)


# ============================================================================
# 主函数
# ============================================================================
def main():
    """
    主函数：运行所有示例
    """
    print("🚀 学习RunnableWithMessageHistory")
    print("=" * 60)

    try:
        # 检查API密钥
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ 错误：未找到OPENAI_API_KEY")
            print("请先在.env文件中配置API密钥")
            return

        # 显示对比
        # compare_old_vs_new()
        key = input("请选择要运行的示例（1/2/3）：").strip()
        if key == "1":
            example1_basic_conversation()
        elif key == "2":
            example2_multi_user_sessions()
        elif key == "3":
            example3_topic_based_conversation()

        # 询问是否进入交互模式
        choice = input("\n是否进入交互式对话模式？(y/n): ").strip().lower()
        if choice == 'y':
            example4_interactive_chat()

        # 总结
        print("\n" + "=" * 60)
        print("✅ 学习完成！")
        print("=" * 60)
        print("""
关键要点：

1. RunnableWithMessageHistory 是新标准
   - 替代已弃用的 ConversationChain
   - 更灵活、更强大
   
2. 核心组件
   - ChatPromptTemplate: 自定义提示词
   - MessagesPlaceholder: 历史消息占位符
   - get_session_history: 会话历史管理函数
   
3. 多会话管理
   - 通过 session_id 区分不同用户
   - 每个session独立的历史记录
   
4. 实际应用
   - Web应用：session_id = 用户ID
   - 聊天室：session_id = 房间ID
   - 持久化：使用数据库替代内存存储

下一步：
- 学习持久化存储（Redis/数据库）
- 学习历史记录摘要（节省token）
- 结合Agent实现复杂对话

继续加油！🚀
        """)

    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# 程序入口
# ============================================================================
if __name__ == "__main__":
    main()

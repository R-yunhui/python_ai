"""
LangChain学习 - 对话记忆（Conversation Memory）

学习目标：
1. 理解为什么需要对话记忆
2. 掌握如何使用ConversationBufferMemory实现对话历史
3. 学会结合提示词模板和记忆实现智能对话
4. 了解如何在实际应用中管理对话状态

对比Spring-AI：
在Spring-AI中，你可能需要手动管理对话历史：
    List<Message> history = new ArrayList<>();
    history.add(new UserMessage("你好"));
    history.add(new AssistantMessage("你好！"));
    
在LangChain中，Memory组件会自动帮你管理历史记录
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain

# 加载环境变量
load_dotenv()


# ============================================================================
# 为什么需要对话记忆？
# ============================================================================
"""
问题场景：
用户：我叫小明
AI：你好小明！
用户：我叫什么名字？
AI：抱歉，我不知道你的名字（❌ 没有记忆）

解决方案：
使用Memory组件自动保存和管理对话历史，让AI能够记住之前的对话内容。

类似于：
- Web应用中的Session
- Spring中的@SessionScope
- Redis中的用户会话
"""


# ============================================================================
# 示例1：基础对话记忆 - ConversationChain
# ============================================================================
def example1_basic_memory():
    """
    使用ConversationChain实现最简单的对话记忆
    这是最常用的方式，适合快速开发
    """
    print("\n" + "=" * 60)
    print("示例1：基础对话记忆")
    print("=" * 60)
    print("演示：AI能够记住之前的对话内容\n")
    
    # 1. 初始化模型
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    
    # 2. 创建对话链（内置记忆功能）
    # ConversationChain = ChatModel + Memory + Prompt Template
    conversation = ConversationChain(
        llm=llm,
        verbose=True  # 设置为True可以看到内部处理过程
    )
    
    # 3. 开始对话
    print("【第1轮对话】")
    response1 = conversation.predict(input="你好！我叫小明，我是一名Python开发者。")
    print(f"AI: {response1}\n")
    
    print("【第2轮对话】")
    response2 = conversation.predict(input="我叫什么名字？")
    print(f"AI: {response2}\n")
    
    print("【第3轮对话】")
    response3 = conversation.predict(input="我是做什么工作的？")
    print(f"AI: {response3}\n")
    
    # 4. 查看对话历史
    print("-" * 60)
    print("📝 完整对话历史：")
    print(conversation.memory.buffer)
    print("-" * 60)


# ============================================================================
# 示例2：自定义对话记忆 - 完整实现
# ============================================================================
def example2_custom_memory_with_template():
    """
    结合自定义提示词模板和记忆，实现一个智能客服助手
    这是实际项目中最常用的方式
    """
    print("\n" + "=" * 60)
    print("示例2：自定义对话记忆 - 智能客服助手")
    print("=" * 60)
    print("演示：创建一个能记住用户信息的Python学习助手\n")
    
    # 1. 初始化模型
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    
    # 2. 创建记忆组件
    # ConversationBufferMemory会保存所有的对话历史
    memory = ConversationBufferMemory(
        return_messages=True,  # 返回消息对象而不是字符串
        memory_key="chat_history"  # 在提示词中使用的变量名
    )
    
    # 3. 创建自定义提示词模板
    # MessagesPlaceholder 用于插入历史对话
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的Python学习助手。
你的职责是：
1. 帮助用户学习Python编程
2. 记住用户的学习进度和背景
3. 给出个性化的建议
4. 用友好、专业的语气回答

请基于之前的对话历史，给出恰当的回复。"""),
        
        # 这里会自动插入对话历史
        MessagesPlaceholder(variable_name="chat_history"),
        
        # 用户的最新消息
        ("human", "{input}")
    ])
    
    # 4. 手动创建对话链（更灵活的方式）
    from langchain.chains import LLMChain
    
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        memory=memory,
        verbose=True  # 显示处理过程
    )
    
    # 5. 模拟一次完整的学习对话
    conversations = [
        "你好！我是一名Java开发者，想转Python，应该从哪里开始？",
        "我对装饰器这个概念不太理解，能解释一下吗？",
        "能给我一个装饰器的实际应用例子吗？",
        "考虑到我的Java背景，你觉得我还需要重点学习Python的哪些特性？",
    ]
    
    for i, user_input in enumerate(conversations, 1):
        print(f"\n【第{i}轮对话】")
        print(f"用户: {user_input}")
        
        # 调用链
        response = chain.predict(input=user_input)
        print(f"AI: {response}")
        print("-" * 60)
    
    # 6. 查看完整的记忆内容
    print("\n" + "=" * 60)
    print("📝 对话历史摘要")
    print("=" * 60)
    
    # 获取所有历史消息
    history = memory.load_memory_variables({})
    print(f"总共 {len(history['chat_history'])} 条消息")
    
    # 打印最近的3条对话
    print("\n最近3轮对话：")
    for msg in history['chat_history'][-6:]:  # -6 是因为每轮有2条消息（用户+AI）
        role = "用户" if msg.type == "human" else "AI"
        content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
        print(f"{role}: {content}\n")


# ============================================================================
# 实用功能：清除记忆和保存/加载记忆
# ============================================================================
def example3_memory_operations():
    """
    演示如何管理记忆：清除、保存、加载
    在实际应用中很重要
    """
    print("\n" + "=" * 60)
    print("示例3：记忆管理操作")
    print("=" * 60)

    # 创建记忆
    memory = ConversationBufferMemory(return_messages=True)
    
    # 1. 手动添加对话记录
    print("\n1. 手动添加对话记录")
    memory.save_context(
        {"input": "你好！"},
        {"output": "你好！很高兴见到你。"}
    )
    memory.save_context(
        {"input": "今天天气怎么样？"},
        {"output": "抱歉，我无法获取实时天气信息。"}
    )
    
    print("当前记忆内容：")
    print(memory.load_memory_variables({})['history'])
    
    # 2. 清除记忆
    print("\n2. 清除记忆")
    memory.clear()
    print("清除后的记忆：", memory.load_memory_variables({})['history'])
    
    # 3. 在实际项目中，你可能需要将记忆持久化到数据库
    print("\n3. 记忆持久化提示")
    print("""
    实际项目中的记忆管理策略：
    
    方案1：使用Redis存储
    - 以用户ID为key
    - 设置过期时间（如24小时）
    - 适合Web应用
    
    方案2：使用数据库存储
    - 创建conversation表
    - 记录user_id, message, role, timestamp
    - 适合需要长期保存的场景
    
    方案3：使用文件存储
    - 每个用户一个JSON文件
    - 适合单机应用或小规模应用
    
    类似Spring-AI中使用Session管理对话状态
    """)


# ============================================================================
# 主函数
# ============================================================================
def main():
    """
    主函数：运行所有示例
    """
    print("🚀 开始学习LangChain对话记忆")
    print("=" * 60)
    
    try:
        # 检查API密钥
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ 错误：未找到OPENAI_API_KEY")
            print("请先在.env文件中配置API密钥")
            return
        
        # 运行示例
        # 你可以注释掉不想运行的示例
        
        print("\n提示：示例会调用AI模型，可能需要等待几秒钟...\n")
        
        # 示例1：最简单的对话记忆
        example1_basic_memory()
        
        # 示例2：自定义对话记忆（重点）
        example2_custom_memory_with_template()
        
        # 示例3：记忆管理操作
        example3_memory_operations()
        
        # 总结
        print("\n" + "=" * 60)
        print("✅ 恭喜！你已经掌握了对话记忆的使用")
        print("=" * 60)
        print("""
关键概念回顾：

1. ConversationBufferMemory
   - 最简单的记忆类型，保存所有历史
   - 适合短对话
   - 类似于Spring的HttpSession

2. ConversationChain
   - 内置记忆的对话链
   - 快速开发首选
   - 自动管理历史记录

3. MessagesPlaceholder
   - 在提示词中插入历史消息
   - 配合自定义模板使用
   - 更灵活的控制

4. Memory管理操作
   - save_context: 保存对话
   - load_memory_variables: 加载历史
   - clear: 清除记忆

对比Spring-AI：
┌─────────────────┬──────────────────────────┬────────────────────────┐
│ 功能            │ Spring-AI                │ LangChain              │
├─────────────────┼──────────────────────────┼────────────────────────┤
│ 记忆管理        │ 手动管理List<Message>    │ ConversationMemory自动 │
│ 持久化          │ 手动实现Session/Redis    │ 内置多种Memory类型     │
│ 使用方式        │ 传入完整历史列表         │ 链自动处理             │
└─────────────────┴──────────────────────────┴────────────────────────┘

实际应用场景：
✅ 客服聊天机器人 - 记住用户问题和上下文
✅ 个人助手应用 - 记住用户偏好和历史
✅ 教育辅导系统 - 跟踪学习进度
✅ 代码助手 - 记住项目上下文

下一步学习：
- 输出解析器（Output Parser）- 结构化AI输出
- 流式输出（Streaming）- 实时显示回复
- RAG检索增强 - 知识库问答

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


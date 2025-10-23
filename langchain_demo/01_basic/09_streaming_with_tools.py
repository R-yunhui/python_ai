"""
LangChain学习 - 流式输出 + 工具调用

学习目标：
1. 理解如何在流式输出中处理工具调用
2. 掌握 tool_calls 的检测和执行
3. 学会实现完整的工具调用流程
4. 了解 Agent 和手动工具调用的区别

重要：
流式输出 + 工具调用需要特殊处理！
不能直接在 stream 中获取 tool_calls，需要累积完整响应。
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from typing import Dict
import json

# 加载环境变量
load_dotenv()

# 全局会话存储
store: Dict[str, ChatMessageHistory] = {}


def get_session_history(session_id: str):
    """获取或创建会话历史"""
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


# ============================================================================
# 定义工具
# ============================================================================

@tool
def get_current_time() -> str:
    """获取当前时间。当用户询问现在几点、当前时间时调用此工具。"""
    now = datetime.now()
    return now.strftime("%Y年%m月%d日 %H:%M:%S")


@tool
def get_weather(city: str) -> str:
    """
    获取指定城市的天气信息。当用户询问天气时使用。
    
    参数:
        city: 城市名称，如"北京"、"上海"
    """
    # 模拟天气数据
    weather_data = {
        "北京": "晴天，15度",
        "上海": "多云，20度",
        "广州": "雨天，28度"
    }
    return weather_data.get(city, f"{city}的天气信息暂时无法获取")


@tool
def calculate(expression: str) -> str:
    """
    执行数学计算。当用户需要计算时使用。
    
    参数:
        expression: 数学表达式，如"2+3*4"
    """
    try:
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


# ============================================================================
# 方法1：累积响应后处理工具调用（推荐）
# ============================================================================
def example1_accumulate_then_process():
    """
    方法1：先累积完整的流式响应，再处理工具调用
    这是最稳定可靠的方式
    """
    print("\n" + "=" * 60)
    print("方法1：累积响应后处理工具调用")
    print("=" * 60)
    
    # 创建提示词模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个有用的AI助手，可以使用工具来回答问题。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}")
    ])
    
    # 初始化模型并绑定工具
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    
    # 绑定工具
    llm_with_tools = llm.bind_tools([get_current_time, get_weather, calculate])
    
    # 创建链
    chain = prompt | llm_with_tools
    
    # 包装历史记录
    with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="history"
    )
    
    session_id = "demo_001"
    
    # 测试问题
    questions = [
        "现在几点了？",
        "北京的天气怎么样？",
        "帮我算一下 25 * 4 + 100",
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n【问题{i}】{question}")
        print("-" * 60)
        
        # 步骤1：使用 stream 获取响应并累积
        response_chunks = []
        print("AI思考中", end="", flush=True)
        
        for chunk in with_history.stream(
            {"question": question},
            config=RunnableConfig(configurable={"session_id": session_id})
        ):
            response_chunks.append(chunk)
            print(".", end="", flush=True)
        
        print()  # 换行
        
        # 步骤2：从累积的chunks中提取完整的AI响应
        ai_message = chunks[0]
        for chunk in chunks[1:]:
            ai_message += chunk
        
        if not ai_message:
            print("❌ 没有收到响应")
            continue
        
        # 步骤3：检查是否有工具调用
        if hasattr(ai_message, 'tool_calls') and ai_message.tool_calls:
            print(f"\n🔧 AI决定使用工具")
            
            # 处理每个工具调用
            for tool_call in ai_message.tool_calls:
                tool_name = tool_call['name']
                tool_args = tool_call['args']
                tool_id = tool_call['id']
                
                print(f"  工具: {tool_name}")
                print(f"  参数: {json.dumps(tool_args, ensure_ascii=False)}")
                
                # 步骤4：执行工具
                tool_result = execute_tool(tool_name, tool_args)
                print(f"  结果: {tool_result}")
                
                # 步骤5：将工具结果添加到历史，让AI生成最终回复
                history = store[session_id]
                
                # 添加AI的工具调用消息
                history.add_message(AIMessage(
                    content="",
                    tool_calls=full_response.tool_calls
                ))
                
                # 添加工具执行结果
                history.add_message(ToolMessage(
                    content=tool_result,
                    tool_call_id=tool_id
                ))
            
            # 步骤6：让AI基于工具结果生成最终回复
            print("\n💬 AI最终回复: ", end="")
            final_response = with_history.stream(
                {"question": ""},  # 空消息，让AI基于工具结果回复
                config=RunnableConfig(configurable={"session_id": session_id})
            )
            
            for chunk in final_response:
                if hasattr(chunk, 'content') and chunk.content:
                    print(chunk.content, end="", flush=True)
            print()
            
        else:
            # 没有工具调用，直接显示内容
            print(f"💬 AI回复: {full_response.content}")
        
        print("=" * 60)


# ============================================================================
# 方法2：检测流中的工具调用（复杂但实时）
# ============================================================================
def example2_detect_in_stream():
    """
    方法2：在流式输出过程中检测工具调用
    更复杂，但可以实时显示部分内容
    """
    print("\n" + "=" * 60)
    print("方法2：流中检测工具调用")
    print("=" * 60)
    
    # 创建模型
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    
    llm_with_tools = llm.bind_tools([get_current_time, get_weather])
    
    question = "现在几点？北京天气如何？"
    print(f"\n问题: {question}")
    print("-" * 60)
    
    # 累积变量
    accumulated_content = ""
    accumulated_tool_calls = []
    
    print("AI回复: ", end="", flush=True)
    
    # 流式处理
    for chunk in llm_with_tools.stream([HumanMessage(content=question)]):
        # 累积文本内容
        if hasattr(chunk, 'content') and chunk.content:
            accumulated_content += chunk.content
            print(chunk.content, end="", flush=True)
        
        # 检测工具调用
        if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
            accumulated_tool_calls.extend(chunk.tool_calls)
    
    print()  # 换行
    
    # 处理工具调用
    if accumulated_tool_calls:
        print(f"\n🔧 检测到 {len(accumulated_tool_calls)} 个工具调用")
        
        tool_messages = []
        for tool_call in accumulated_tool_calls:
            tool_name = tool_call['name']
            tool_args = tool_call['args']
            tool_id = tool_call['id']
            
            print(f"\n执行工具: {tool_name}({tool_args})")
            result = execute_tool(tool_name, tool_args)
            print(f"结果: {result}")
            
            tool_messages.append(ToolMessage(
                content=result,
                tool_call_id=tool_id
            ))
        
        # 发送工具结果，获取最终回复
        print("\n💬 基于工具结果的最终回复: ", end="")
        final_stream = llm.stream([
            HumanMessage(content=question),
            AIMessage(content="", tool_calls=accumulated_tool_calls),
            *tool_messages
        ])
        
        for chunk in final_stream:
            if hasattr(chunk, 'content') and chunk.content:
                print(chunk.content, end="", flush=True)
        print()


# ============================================================================
# 方法3：使用 Agent 自动处理（最简单）
# ============================================================================
def example3_use_agent():
    """
    方法3：使用 Agent 自动处理工具调用
    这是最简单的方式，但牺牲了一些控制权
    """
    print("\n" + "=" * 60)
    print("方法3：使用 Agent 自动处理")
    print("=" * 60)
    print("提示：Agent 会自动处理工具调用，无需手动干预\n")
    
    from langchain.agents import create_tool_calling_agent, AgentExecutor
    
    # 创建提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个有用的AI助手。"),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # 创建模型
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    
    tools = [get_current_time, get_weather, calculate]
    
    # 创建 Agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True  # 显示详细过程
    )
    
    # 测试
    questions = [
        "现在几点了？",
        "北京天气怎么样，顺便算一下 15+25",
    ]
    
    for question in questions:
        print(f"\n问题: {question}")
        print("=" * 60)
        
        # Agent 会自动处理工具调用
        result = agent_executor.invoke({"input": question})
        
        print(f"\n最终答案: {result['output']}")
        print("=" * 60)


# ============================================================================
# 工具执行辅助函数
# ============================================================================
def execute_tool(tool_name: str, tool_args: dict) -> str:
    """
    根据工具名称和参数执行相应的工具
    
    参数:
        tool_name: 工具名称
        tool_args: 工具参数字典
        
    返回:
        工具执行结果
    """
    if tool_name == "get_current_time":
        return get_current_time.invoke({}).content
    elif tool_name == "get_weather":
        return get_weather.invoke(tool_args).content
    elif tool_name == "calculate":
        return calculate.invoke(tool_args).content
    else:
        return f"未知工具: {tool_name}"


# ============================================================================
# 实用模板：完整的聊天机器人示例
# ============================================================================
def example4_complete_chatbot():
    """
    实用模板：完整的流式输出 + 工具调用聊天机器人
    可以直接用于实际项目
    """
    print("\n" + "=" * 60)
    print("完整示例：流式聊天机器人 with 工具调用")
    print("=" * 60)
    print("输入 'exit' 退出，'history' 查看历史\n")
    
    # 创建提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个智能助手，可以使用工具来帮助用户。
可用工具：
- get_current_time: 获取当前时间
- get_weather: 查询城市天气
- calculate: 进行数学计算

根据用户问题，决定是否需要使用工具。"""),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}")
    ])
    
    # 初始化模型
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    
    llm_with_tools = llm.bind_tools([get_current_time, get_weather, calculate])
    chain = prompt | llm_with_tools
    
    with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="question",
        history_messages_key="history"
    )
    
    import time
    session_id = f"chat_{int(time.time())}"
    
    while True:
        question = input("\n你: ").strip()
        
        if not question:
            continue
        
        if question.lower() == 'exit':
            print("再见！")
            break
        
        if question.lower() == 'history':
            if session_id in store:
                history = store[session_id]
                print("\n📝 对话历史:")
                for msg in history.messages:
                    role = "你" if msg.type == "human" else "AI"
                    print(f"{role}: {msg.content[:100]}...")
            else:
                print("暂无历史")
            continue
        
        try:
            # 累积响应
            chunks = []
            print("AI: ", end="", flush=True)
            
            for chunk in with_history.stream(
                {"question": question},
                config=RunnableConfig(configurable={"session_id": session_id})
            ):
                chunks.append(chunk)
                # 实时显示非工具调用的内容
                if hasattr(chunk, 'content') and chunk.content and not hasattr(chunk, 'tool_calls'):
                    print(chunk.content, end="", flush=True)
            
            print()  # 换行
            
            # 检查工具调用
            full_response = chunks[-1] if chunks else None
            if full_response and hasattr(full_response, 'tool_calls') and full_response.tool_calls:
                print("🔧 使用工具处理中...")
                
                history = store[session_id]
                
                # 添加AI消息和工具结果
                history.add_message(AIMessage(content="", tool_calls=full_response.tool_calls))
                
                for tool_call in full_response.tool_calls:
                    result = execute_tool(tool_call['name'], tool_call['args'])
                    history.add_message(ToolMessage(
                        content=result,
                        tool_call_id=tool_call['id']
                    ))
                
                # 获取最终回复
                print("AI: ", end="", flush=True)
                for chunk in with_history.stream(
                    {"question": ""},
                    config=RunnableConfig(configurable={"session_id": session_id})
                ):
                    if hasattr(chunk, 'content') and chunk.content:
                        print(chunk.content, end="", flush=True)
                print()
        
        except Exception as e:
            print(f"\n❌ 错误: {e}")


# ============================================================================
# 主函数
# ============================================================================
def main():
    print("🚀 学习：流式输出 + 工具调用")
    print("=" * 60)
    
    try:
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ 错误：未找到OPENAI_API_KEY")
            return
        
        print("""
三种处理方式：

1. 累积响应后处理（推荐）✅
   - 最稳定可靠
   - 适合大多数场景
   
2. 流中检测工具调用
   - 更复杂
   - 可以实时显示部分内容
   
3. 使用 Agent 自动处理（最简单）✅
   - Agent 自动处理所有工具调用
   - 但牺牲了一些控制权

选择运行：
""")
        
        choice = input("选择示例 (1/2/3/4-完整聊天机器人/all): ").strip()
        
        if choice == "1":
            example1_accumulate_then_process()
        elif choice == "2":
            example2_detect_in_stream()
        elif choice == "3":
            example3_use_agent()
        elif choice == "4":
            example4_complete_chatbot()
        elif choice == "all":
            example1_accumulate_then_process()
            input("\n按回车继续下一个示例...")
            example2_detect_in_stream()
            input("\n按回车继续下一个示例...")
            example3_use_agent()
        
        print("\n" + "=" * 60)
        print("✅ 学习完成！")
        print("=" * 60)
        print("""
关键要点：

1. 流式输出 + 工具调用的挑战
   - stream() 返回生成器，无法直接获取 tool_calls
   - 需要累积完整响应才能检测工具调用
   
2. 处理流程
   ① 累积 stream 的所有 chunks
   ② 从最后一个 chunk 获取完整响应
   ③ 检查 tool_calls
   ④ 执行工具
   ⑤ 将结果添加到历史
   ⑥ 让AI生成最终回复
   
3. 推荐方案
   - 简单场景：使用 Agent（示例3）
   - 需要控制：累积响应后处理（示例1）
   - 生产环境：完整聊天机器人（示例4）
   
4. 注意事项
   - 工具调用需要两轮对话（调用工具 + 生成回复）
   - 必须将工具结果添加到历史记录
   - ToolMessage 需要 tool_call_id

继续加油！🚀
        """)
        
    except Exception as e:
        print(f"\n❌ 运行出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()


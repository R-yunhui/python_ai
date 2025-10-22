"""
LangChain学习 - Agent智能体（多工具串联）

学习目标：
1. 理解Agent的概念和工作原理
2. 掌握如何创建支持多工具的Agent
3. 学会让AI自主决策和规划任务
4. 了解ReAct（推理+行动）模式

对比Spring-AI：
在Spring-AI中还没有完整的Agent实现，通常需要手动编排：
    1. 第一次调用AI判断需要什么工具
    2. 执行工具
    3. 第二次调用AI处理结果
    4. 重复直到完成
    
在LangChain中，Agent会自动完成这个循环过程
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Dict, List, Any
import json
from datetime import datetime, timedelta
import random

# 加载环境变量
load_dotenv()


# ============================================================================
# 什么是Agent？
# ============================================================================
"""
Agent（智能体）= AI + Tools + 决策循环

普通Tool使用：
用户 -> AI -> 调用一个Tool -> 返回结果
(单次调用，需要人工判断)

Agent智能体：
用户 -> Agent -> 分析任务 -> 调用Tool1 -> 分析结果 -> 调用Tool2 -> 综合结果 -> 回答
(自动循环，AI自主决策)

ReAct模式（Reasoning + Acting）：
1. Thought（思考）：我需要做什么？
2. Action（行动）：调用哪个工具？
3. Observation（观察）：工具返回了什么？
4. 重复1-3，直到得到最终答案

类似于：
- 人类解决问题的过程
- 递归函数调用
- 工作流引擎
"""


# ============================================================================
# 场景：智能旅行助手
# 创建一系列工具来帮助用户规划旅行
# ============================================================================

# 模拟数据库
WEATHER_DATA = {
    "北京": {"temp": 15, "condition": "晴天", "humidity": 45},
    "上海": {"temp": 20, "condition": "多云", "humidity": 65},
    "广州": {"temp": 28, "condition": "晴天", "humidity": 80},
    "成都": {"temp": 18, "condition": "阴天", "humidity": 70},
    "杭州": {"temp": 22, "condition": "小雨", "humidity": 75},
}

ATTRACTIONS = {
    "北京": [
        {"name": "故宫", "rating": 4.8, "price": 60, "time": "3小时"},
        {"name": "长城", "rating": 4.9, "price": 40, "time": "5小时"},
        {"name": "颐和园", "rating": 4.7, "price": 30, "time": "3小时"}
    ],
    "上海": [
        {"name": "外滩", "rating": 4.7, "price": 0, "time": "2小时"},
        {"name": "东方明珠", "rating": 4.5, "price": 180, "time": "2小时"},
        {"name": "迪士尼", "rating": 4.8, "price": 499, "time": "全天"}
    ],
    "杭州": [
        {"name": "西湖", "rating": 4.9, "price": 0, "time": "4小时"},
        {"name": "灵隐寺", "rating": 4.6, "price": 45, "time": "2小时"}
    ]
}

HOTELS = {
    "北京": [
        {"name": "北京饭店", "price": 800, "rating": 4.7, "location": "市中心"},
        {"name": "如家快捷", "price": 300, "rating": 4.3, "location": "地铁附近"},
        {"name": "汉庭酒店", "price": 250, "rating": 4.2, "location": "商业区"}
    ],
    "上海": [
        {"name": "和平饭店", "price": 1200, "rating": 4.8, "location": "外滩"},
        {"name": "锦江之星", "price": 400, "rating": 4.4, "location": "人民广场"}
    ],
    "杭州": [
        {"name": "西湖国宾馆", "price": 1500, "rating": 4.9, "location": "西湖边"},
        {"name": "维也纳酒店", "price": 350, "rating": 4.3, "location": "市中心"}
    ]
}

TRANSPORTATION = {
    ("北京", "上海"): {"train": 553, "flight": 800, "duration_train": "5小时", "duration_flight": "2小时"},
    ("北京", "杭州"): {"train": 490, "flight": 750, "duration_train": "6小时", "duration_flight": "2小时"},
    ("上海", "杭州"): {"train": 73, "flight": 450, "duration_train": "1小时", "duration_flight": "1小时"},
}


# ============================================================================
# 工具1：查询天气
# ============================================================================
@tool
def get_weather(city: str) -> str:
    """
    查询指定城市的天气信息。当用户询问某地天气、气温、是否下雨时使用。
    
    参数:
        city: 城市名称，如"北京"、"上海"等
        
    返回:
        JSON格式的天气信息，包含温度、天气状况、湿度
    """
    weather = WEATHER_DATA.get(city)
    if weather:
        return json.dumps({
            "city": city,
            "temperature": weather["temp"],
            "condition": weather["condition"],
            "humidity": weather["humidity"]
        }, ensure_ascii=False)
    else:
        return json.dumps({"error": f"未找到{city}的天气信息"}, ensure_ascii=False)


# ============================================================================
# 工具2：查询景点
# ============================================================================
@tool
def search_attractions(city: str, max_results: int = 5) -> str:
    """
    搜索指定城市的旅游景点。当用户询问某地有什么好玩的、景点推荐时使用。
    
    参数:
        city: 城市名称
        max_results: 最多返回几个景点，默认5个
        
    返回:
        JSON格式的景点列表，包含名称、评分、门票价格、建议游玩时间
    """
    attractions = ATTRACTIONS.get(city, [])
    if attractions:
        return json.dumps({
            "city": city,
            "attractions": attractions[:max_results]
        }, ensure_ascii=False, indent=2)
    else:
        return json.dumps({"error": f"未找到{city}的景点信息"}, ensure_ascii=False)


# ============================================================================
# 工具3：查询酒店
# ============================================================================
@tool
def search_hotels(city: str, max_price: int = 10000) -> str:
    """
    搜索指定城市的酒店。当用户询问住宿、酒店推荐时使用。
    
    参数:
        city: 城市名称
        max_price: 最高价格预算（元/晚），默认10000
        
    返回:
        JSON格式的酒店列表，包含名称、价格、评分、位置
    """
    hotels = HOTELS.get(city, [])
    if hotels:
        # 筛选符合预算的酒店
        filtered = [h for h in hotels if h["price"] <= max_price]
        return json.dumps({
            "city": city,
            "hotels": filtered,
            "count": len(filtered)
        }, ensure_ascii=False, indent=2)
    else:
        return json.dumps({"error": f"未找到{city}的酒店信息"}, ensure_ascii=False)


# ============================================================================
# 工具4：查询交通
# ============================================================================
@tool
def get_transportation(from_city: str, to_city: str) -> str:
    """
    查询两个城市之间的交通方式。当用户询问如何去某地、交通方式时使用。
    
    参数:
        from_city: 出发城市
        to_city: 目的地城市
        
    返回:
        JSON格式的交通信息，包含火车和飞机的价格、时长
    """
    # 尝试正向和反向查询
    key1 = (from_city, to_city)
    key2 = (to_city, from_city)
    
    trans = TRANSPORTATION.get(key1) or TRANSPORTATION.get(key2)
    if trans:
        return json.dumps({
            "from": from_city,
            "to": to_city,
            "options": {
                "train": {
                    "price": trans["train"],
                    "duration": trans["duration_train"]
                },
                "flight": {
                    "price": trans["flight"],
                    "duration": trans["duration_flight"]
                }
            }
        }, ensure_ascii=False, indent=2)
    else:
        return json.dumps({
            "error": f"未找到从{from_city}到{to_city}的交通信息"
        }, ensure_ascii=False)


# ============================================================================
# 工具5：计算旅行预算
# ============================================================================
@tool
def calculate_budget(
    accommodation: int,
    transportation: int,
    attractions: int,
    days: int
) -> str:
    """
    计算旅行总预算。当用户询问费用、预算时使用。
    
    参数:
        accommodation: 每晚住宿费用（元）
        transportation: 往返交通费用（元）
        attractions: 景点门票总费用（元）
        days: 旅行天数
        
    返回:
        JSON格式的预算明细
    """
    # 估算餐饮费用（每天150元）
    food_cost = 150 * days
    
    # 估算其他费用（总费用的10%）
    subtotal = accommodation * days + transportation + attractions + food_cost
    other_cost = subtotal * 0.1
    
    total = subtotal + other_cost
    
    return json.dumps({
        "breakdown": {
            "accommodation": accommodation * days,
            "transportation": transportation,
            "attractions": attractions,
            "food": food_cost,
            "other": round(other_cost, 2)
        },
        "total": round(total, 2),
        "days": days
    }, ensure_ascii=False, indent=2)


# ============================================================================
# 示例1：创建基础Agent
# ============================================================================
def example1_basic_agent():
    """
    演示如何创建一个基础的Agent
    Agent会自主决策使用哪些工具
    """
    print("\n" + "=" * 60)
    print("示例1：基础Agent - 单次查询")
    print("=" * 60)
    
    # 1. 准备工具列表
    tools: List[Any] = [
        get_weather,
        search_attractions,
        search_hotels,
        get_transportation,
        calculate_budget
    ]
    
    # 2. 创建提示词模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的旅行规划助手。你可以使用以下工具来帮助用户规划旅行：

- get_weather: 查询天气
- search_attractions: 搜索景点
- search_hotels: 搜索酒店
- get_transportation: 查询交通
- calculate_budget: 计算预算

请根据用户的问题，合理使用工具，提供详细的旅行建议。
注意：
1. 先理解用户需求
2. 选择合适的工具
3. 综合信息给出建议
"""),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # 3. 初始化模型
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    
    # 4. 创建Agent
    agent = create_tool_calling_agent(llm, tools, prompt)
    
    # 5. 创建Agent执行器
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,  # 显示详细的执行过程
        max_iterations=5  # 最多执行5轮
    )
    
    # 6. 测试简单问题
    question = "北京现在天气怎么样？"
    
    print(f"\n用户问题: {question}\n")
    print("=" * 60)
    
    result = agent_executor.invoke({"input": question})
    
    print("\n" + "=" * 60)
    print(f"\n最终答案: {result['output']}\n")


# ============================================================================
# 示例2：复杂任务 - 多工具串联
# ============================================================================
def example2_complex_task():
    """
    演示Agent如何处理复杂任务
    需要调用多个工具并综合信息
    """
    print("\n" + "=" * 60)
    print("示例2：复杂任务 - 多工具串联")
    print("=" * 60)
    
    # 准备工具
    tools: List[Any] = [
        get_weather,
        search_attractions,
        search_hotels,
        get_transportation,
        calculate_budget
    ]
    
    # 创建提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个专业的旅行规划助手。

你的工作流程：
1. 理解用户的旅行需求（目的地、天数、预算等）
2. 查询目的地的天气状况
3. 推荐合适的景点
4. 推荐合适的酒店（考虑预算）
5. 如果涉及多个城市，查询交通方式
6. 计算总体预算
7. 综合以上信息，给出详细的旅行建议

请按步骤思考，合理使用工具，给出专业建议。
"""),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # 初始化模型和Agent
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.3,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=10  # 复杂任务可能需要更多轮次
    )
    
    # 测试复杂问题
    question = """我想去杭州旅游3天，预算在3000元左右。
能帮我规划一下吗？包括景点推荐、住宿建议和大概费用。"""
    
    print(f"\n用户问题:\n{question}\n")
    print("=" * 60)
    
    result = agent_executor.invoke({"input": question})
    
    print("\n" + "=" * 60)
    print(f"\n最终答案:\n{result['output']}\n")


# ============================================================================
# 示例3：多城市旅行规划
# ============================================================================
def example3_multi_city_planning():
    """
    演示最复杂的场景：多城市旅行规划
    需要查询天气、景点、酒店、交通，并计算总预算
    """
    print("\n" + "=" * 60)
    print("示例3：多城市旅行规划")
    print("=" * 60)
    
    # 准备工具
    tools: List[Any] = [
        get_weather,
        search_attractions,
        search_hotels,
        get_transportation,
        calculate_budget
    ]
    
    # 创建提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", """你是一个经验丰富的旅行规划师。

多城市旅行规划步骤：
1. 了解每个目的地的基本情况（天气、景点）
2. 规划城市间的交通路线
3. 为每个城市推荐住宿
4. 计算每个城市的花费
5. 汇总总预算
6. 给出合理的行程安排建议

请细致周到地帮助用户规划旅行。
"""),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # 初始化
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.3,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    
    agent = create_tool_calling_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=15  # 多城市需要更多轮次
    )
    
    # 测试多城市问题
    question = """我想从北京出发，先去上海玩2天，再去杭州玩2天。
请帮我规划行程，包括：
1. 每个城市的天气和景点推荐
2. 城市间的交通方式
3. 住宿建议（预算每晚500元左右）
4. 总费用预估"""
    
    print(f"\n用户问题:\n{question}\n")
    print("=" * 60)
    
    result = agent_executor.invoke({"input": question})
    
    print("\n" + "=" * 60)
    print(f"\n最终答案:\n{result['output']}\n")


# ============================================================================
# Agent工作原理解析
# ============================================================================
def explain_agent_workflow():
    """
    解释Agent的工作原理
    """
    print("\n" + "=" * 60)
    print("Agent工作原理详解")
    print("=" * 60)
    
    print("""
Agent执行流程（ReAct模式）：

第1轮：
┌─────────────────────────────────────────────┐
│ Thought（思考）                             │
│ 用户想去杭州旅游，我需要先了解天气情况     │
└─────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│ Action（行动）                              │
│ 调用工具: get_weather(city="杭州")         │
└─────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│ Observation（观察）                         │
│ 杭州天气：22度，小雨，湿度75%               │
└─────────────────────────────────────────────┘

第2轮：
┌─────────────────────────────────────────────┐
│ Thought                                     │
│ 天气还不错，接下来查询景点推荐             │
└─────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│ Action                                      │
│ 调用工具: search_attractions(city="杭州")  │
└─────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│ Observation                                 │
│ 西湖(4.9分,免费)、灵隐寺(4.6分,45元)       │
└─────────────────────────────────────────────┘

... 继续循环，直到收集足够信息 ...

最终：
┌─────────────────────────────────────────────┐
│ Final Answer（最终答案）                    │
│ 综合以上信息，给出完整的旅行建议           │
└─────────────────────────────────────────────┘

关键特点：
✅ 自主决策：AI自己判断需要调用哪些工具
✅ 循环执行：根据结果决定是否需要更多信息
✅ 灵活组合：可以任意组合多个工具
✅ 推理能力：不只是执行，还要思考和规划

对比Spring-AI：
Spring-AI目前需要手动编排这个流程：
1. 手动判断需要什么信息
2. 手动调用相应的函数
3. 手动将结果传给AI
4. 手动决定是否继续

LangChain的Agent自动完成所有这些步骤！
    """)


# ============================================================================
# 主函数
# ============================================================================
def main():
    """
    主函数：运行所有示例
    """
    print("🚀 开始学习LangChain Agent智能体")
    print("=" * 60)
    
    try:
        # 检查API密钥
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ 错误：未找到OPENAI_API_KEY")
            print("请先在.env文件中配置API密钥")
            return
        
        print("""
Agent（智能体）是LangChain最强大的功能之一！
它能让AI自主决策、规划任务、串联使用多个工具。

本示例将展示：
✅ 基础Agent的创建和使用
✅ 复杂任务的自动分解
✅ 多工具的智能串联
✅ ReAct推理模式

提示：设置了verbose=True，你可以看到Agent的完整思考过程！
        """)
        
        input("\n按回车键开始示例1...")
        example1_basic_agent()
        
        input("\n按回车键开始示例2...")
        example2_complex_task()
        
        input("\n按回车键开始示例3...")
        example3_multi_city_planning()
        
        # 原理解释
        explain_agent_workflow()
        
        # 总结
        print("\n" + "=" * 60)
        print("✅ 恭喜！你已经掌握了Agent智能体的使用")
        print("=" * 60)
        print("""
关键概念回顾：

1. Agent核心组件
   - Tools: 工具集合
   - LLM: 大语言模型（大脑）
   - Prompt: 指导思维的提示词
   - AgentExecutor: 执行器
   
2. ReAct模式
   - Thought: AI的思考过程
   - Action: 决定调用哪个工具
   - Observation: 观察工具返回结果
   - 循环直到完成任务
   
3. Agent类型
   - Tool Calling Agent: 使用工具调用（推荐）
   - ReAct Agent: 传统ReAct模式
   - Plan-and-Execute: 规划执行型
   
4. 使用场景
   - 复杂任务自动分解
   - 多步骤信息查询
   - 工作流自动化
   - 智能助手开发

对比Spring-AI：
┌──────────────────┬────────────────────────┬──────────────────────┐
│ 功能             │ Spring-AI              │ LangChain Agent      │
├──────────────────┼────────────────────────┼──────────────────────┤
│ 工具调用         │ FunctionCallback       │ @tool + bind_tools   │
│ 任务编排         │ 手动编排               │ Agent自动编排        │
│ 决策能力         │ 需要人工判断           │ AI自主决策           │
│ 循环执行         │ 手动实现循环           │ AgentExecutor自动    │
│ 推理过程         │ 不可见                 │ verbose可查看        │
└──────────────────┴────────────────────────┴──────────────────────┘

实际应用：
✅ 智能客服（自动查询多个系统）
✅ 数据分析（自动调用多个查询）
✅ 任务自动化（自动执行多步骤）
✅ 研究助手（自动搜索和总结）
✅ 代码助手（自动查文档、写代码、测试）

注意事项：
⚠️ 设置max_iterations防止无限循环
⚠️ 工具的描述要清晰准确
⚠️ 复杂任务可能消耗较多token
⚠️ 需要模型支持function calling（如GPT-3.5/4）

下一步学习：
- RAG检索增强 - 构建知识库问答
- 自定义Agent - 实现特定业务逻辑
- Agent协作 - 多个Agent协同工作

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


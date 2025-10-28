"""
ReAct Agent 实现示例 - 推理与行动交替进行

ReAct = Reasoning + Acting
核心特点：
1. 思维过程可视化：每一步的思考都会显示出来
2. 渐进式决策：根据前一步的结果决定下一步行动
3. 自我纠错：能够根据观察结果调整策略
4. 适合复杂推理：多步骤问题解决

工作流程：
Question → Thought → Action → Observation → Thought → Action → ... → Final Answer

使用示例：
    python 01_react_agent.py
    
    测试问题：
    - "帮我查北京天气，如果适合出行就推荐景点"
    - "我想买一台笔记本电脑，预算8000元，帮我分析一下"
    - "计算 15 * 23 + 45，然后告诉我这个数字是奇数还是偶数"
"""

import os
from datetime import datetime
from typing import Dict

from dotenv import load_dotenv
from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import PromptTemplate
from langchain_community.chat_message_histories import ChatMessageHistory

# 加载环境变量
load_dotenv()

# 初始化 LLM
llm = ChatOpenAI(
    base_url=os.getenv("OPENAI_API_BASE", "http://192.168.2.54:9015/v1/"),
    model=os.getenv("OPENAI_MODEL", "qwen2.5-vl-72b-instruct"),
    api_key=os.getenv("OPENAI_API_KEY", None),
    temperature=0.1,  # ReAct 需要更稳定的输出
    max_tokens=2048
)

# 会话历史存储
chat_history_store: Dict[str, ChatMessageHistory] = {}


# ========== 工具定义 ==========

@tool
def get_current_time() -> str:
    """
    获取当前时间。
    当需要知道现在的时间、日期时使用。
    """
    now = datetime.now()
    return f"当前时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}"


@tool
def get_weather(city: str) -> str:
    """
    获取指定城市的天气信息。
    
    参数:
        city: 城市名称，如"北京"、"上海"等
    """
    # 模拟天气数据
    weather_data = {
        "北京": {
            "weather": "晴天",
            "temperature": "15-25℃",
            "air_quality": "良好",
            "suitable_for_travel": True,
            "description": "天气晴朗，空气质量良好，非常适合出行游玩"
        },
        "上海": {
            "weather": "多云",
            "temperature": "18-26℃",
            "air_quality": "轻度污染",
            "suitable_for_travel": True,
            "description": "多云天气，温度适宜，可以出行但建议避开高峰时段"
        },
        "成都": {
            "weather": "小雨",
            "temperature": "16-22℃",
            "air_quality": "良好",
            "suitable_for_travel": False,
            "description": "有小雨，不太适合户外活动，建议选择室内景点"
        },
        "广州": {
            "weather": "雷阵雨",
            "temperature": "25-32℃",
            "air_quality": "中度污染",
            "suitable_for_travel": False,
            "description": "有雷阵雨且空气质量不佳，不建议外出"
        }
    }

    if city in weather_data:
        data = weather_data[city]
        return f"{city}天气：{data['weather']}，温度{data['temperature']}，空气质量{data['air_quality']}。{data['description']}"
    else:
        return f"抱歉，没有{city}的天气数据。可查询：北京、上海、成都、广州"


@tool
def search_attractions(city: str, weather_condition: str = "any") -> str:
    """
    根据城市和天气条件搜索合适的景点。
    
    参数:
        city: 城市名称
        weather_condition: 天气条件，"good"表示好天气推荐户外景点，"bad"表示坏天气推荐室内景点，"any"表示不限制
    """
    attractions_data = {
        "北京": {
            "outdoor": ["长城（八达岭）", "颐和园", "天坛公园", "奥林匹克公园"],
            "indoor": ["故宫博物院", "国家博物馆", "798艺术区", "三里屯商圈"]
        },
        "上海": {
            "outdoor": ["外滩", "豫园", "世纪公园", "东方明珠塔"],
            "indoor": ["上海博物馆", "新天地", "田子坊", "南京路步行街"]
        },
        "成都": {
            "outdoor": ["宽窄巷子", "锦里古街", "人民公园", "春熙路"],
            "indoor": ["大熊猫繁育研究基地（室内馆）", "成都博物馆", "IFS国际金融中心", "太古里"]
        },
        "广州": {
            "outdoor": ["白云山", "珠江夜游", "沙面岛", "广州塔"],
            "indoor": ["陈家祠", "广东省博物馆", "北京路步行街", "天河城"]
        }
    }

    if city not in attractions_data:
        return f"抱歉，没有{city}的景点数据"

    data = attractions_data[city]

    if weather_condition == "good":
        attractions = data["outdoor"]
        return f"天气好，推荐{city}的户外景点：" + "、".join(attractions)
    elif weather_condition == "bad":
        attractions = data["indoor"]
        return f"天气不好，推荐{city}的室内景点：" + "、".join(attractions)
    else:
        all_attractions = data["outdoor"] + data["indoor"]
        return f"{city}的热门景点：" + "、".join(all_attractions[:6])


@tool
def calculate(expression: str) -> str:
    """
    计算数学表达式。
    
    参数:
        expression: 数学表达式，如"15 * 23 + 45"
    """
    try:
        # 安全的数学计算，只允许基本运算符
        allowed_chars = set('0123456789+-*/().')
        if not all(c in allowed_chars or c.isspace() for c in expression):
            return "错误：表达式包含不允许的字符"
        
        # 使用 eval 进行数学计算（已经过安全检查）
        result = eval(expression)  # noqa: S307
        return f"{expression} = {result}"
    except (ValueError, ZeroDivisionError, SyntaxError) as e:
        return f"计算错误：{str(e)}"


@tool
def analyze_number(number: int) -> str:
    """
    分析一个数字的特性（奇偶性、质数等）。
    
    参数:
        number: 要分析的整数
    """
    try:
        number = int(number)

        # 奇偶性
        parity = "偶数" if number % 2 == 0 else "奇数"

        # 质数判断
        def is_prime(n):
            if n < 2:
                return False
            for i in range(2, int(n ** 0.5) + 1):
                if n % i == 0:
                    return False
            return True

        prime_status = "质数" if is_prime(number) else "合数"
        if number < 2:
            prime_status = "既不是质数也不是合数"

        # 数字大小分类
        if number < 10:
            size_category = "个位数"
        elif number < 100:
            size_category = "两位数"
        elif number < 1000:
            size_category = "三位数"
        else:
            size_category = "大数"

        return f"数字 {number} 的特性：{parity}、{prime_status}、{size_category}"

    except ValueError:
        return "错误：输入不是有效的整数"


@tool
def product_search(category: str, budget: str) -> str:
    """
    根据类别和预算搜索产品推荐。
    
    参数:
        category: 产品类别，如"笔记本电脑"、"手机"等
        budget: 预算金额（元），如"8000"
    """
    products_data = {
        "笔记本电脑": [
            {"name": "联想ThinkPad E14", "price": 4999, "specs": "i5-1135G7/8GB/512GB SSD", "rating": 4.5},
            {"name": "华为MateBook D14", "price": 5499, "specs": "i5-1135G7/16GB/512GB SSD", "rating": 4.6},
            {"name": "小米RedmiBook Pro 15", "price": 6999, "specs": "i7-11370H/16GB/512GB SSD", "rating": 4.4},
            {"name": "戴尔灵越5000", "price": 7999, "specs": "i7-1165G7/16GB/1TB SSD", "rating": 4.3},
            {"name": "苹果MacBook Air M1", "price": 8999, "specs": "M1芯片/8GB/256GB SSD", "rating": 4.8},
            {"name": "华硕天选3", "price": 7499, "specs": "R7-6800H/16GB/512GB SSD/RTX3060", "rating": 4.5}
        ],
        "手机": [
            {"name": "小米13", "price": 3999, "specs": "骁龙8 Gen2/8GB+128GB", "rating": 4.6},
            {"name": "华为P60", "price": 4988, "specs": "骁龙8+ Gen1/8GB+256GB", "rating": 4.7},
            {"name": "iPhone 14", "price": 5999, "specs": "A15芯片/128GB", "rating": 4.8},
            {"name": "OPPO Find X6", "price": 4499, "specs": "天玑9200/12GB+256GB", "rating": 4.5}
        ]
    }

    if category not in products_data:
        return f"抱歉，暂不支持{category}类别的产品搜索"
    
    # 将预算字符串转换为整数
    try:
        budget_int = int(budget)
    except ValueError:
        return f"错误：预算'{budget}'不是有效的数字"
    
    products = products_data[category]
    suitable_products = [p for p in products if p["price"] <= budget_int]

    if not suitable_products:
        min_price = min(p["price"] for p in products)
        return f"预算{budget_int}元内没有合适的{category}，最低价格为{min_price}元"
    
    # 按评分排序
    suitable_products.sort(key=lambda x: x["rating"], reverse=True)
    
    result = f"预算{budget_int}元内的{category}推荐：\n"
    for i, product in enumerate(suitable_products[:3], 1):
        result += f"{i}. {product['name']} - ¥{product['price']} - {product['specs']} (评分: {product['rating']})\n"

    return result.strip()


# ========== ReAct Agent 配置 ==========

def get_session_history(session_id: str) -> ChatMessageHistory:
    """获取会话历史"""
    if session_id not in chat_history_store:
        chat_history_store[session_id] = ChatMessageHistory()
    return chat_history_store[session_id]


def create_react_agent_with_history():
    """
    创建 ReAct Agent
    
    ReAct 的关键是提示词模板，它定义了 Thought-Action-Observation 的循环格式
    """

    # ReAct 专用提示词模板
    react_prompt = PromptTemplate.from_template("""
你是一个智能助手，能够通过思考和行动来解决问题。

你可以使用以下工具：
{tools}

使用以下格式进行推理和行动：

Question: 用户的输入问题
Thought: 你应该总是思考该做什么，分析当前情况，制定下一步计划
Action: 要采取的行动，必须是 [{tool_names}] 中的一个
Action Input: 行动的输入参数
Observation: 行动的结果
... (这个 Thought/Action/Action Input/Observation 可以重复多次)
Thought: 我现在知道最终答案了
Final Answer: 对原始输入问题的最终答案

重要规则：
1. 每次只能执行一个 Action
2. 必须根据 Observation 的结果来决定下一步
3. 如果信息不足，继续收集信息
4. 如果发现错误，要及时纠正
5. 最终答案要完整、准确、有用

开始！

Question: {input}
Thought: {agent_scratchpad}""")

    # 工具列表
    tools = [
        get_current_time,
        get_weather,
        search_attractions,
        calculate,
        analyze_number,
        product_search
    ]

    # 创建 ReAct Agent
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=react_prompt
    )

    # 创建 AgentExecutor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,  # 显示详细的推理过程
        max_iterations=15,  # ReAct 可能需要更多轮次
        handle_parsing_errors=True,
        return_intermediate_steps=True  # 返回中间步骤，便于观察推理过程
    )

    return agent_executor


def interactive_react_chat():
    """交互式 ReAct Agent 聊天"""

    print("=" * 80)
    print("🧠 ReAct Agent - 推理与行动交替进行")
    print("=" * 80)
    print("\n✨ ReAct 特性：")
    print("  • 思维过程可视化：每一步思考都会显示")
    print("  • 渐进式决策：根据结果调整下一步行动")
    print("  • 自我纠错：能够发现并纠正错误")
    print("  • 适合复杂推理：多步骤问题解决")

    print("\n🛠️ 可用工具：")
    print("  ⏰ 获取当前时间")
    print("  🌤️  查询城市天气")
    print("  🎯 根据天气推荐景点")
    print("  🧮 数学计算")
    print("  🔢 数字特性分析")
    print("  🛒 产品搜索推荐")

    print("\n💡 测试问题（观察 ReAct 的推理过程）：")
    print("  • 帮我查北京天气，如果适合出行就推荐景点")
    print("  • 计算 15 * 23 + 45，然后分析这个结果是奇数还是偶数")
    print("  • 我想买笔记本电脑，预算8000元，推荐几款")
    print("  • 现在几点了？如果是下午就推荐上海的景点")

    print("\n输入 'exit' 结束对话")
    print("=" * 80 + "\n")

    # 创建 ReAct Agent
    agent_executor = create_react_agent_with_history()

    while True:
        try:
            # 获取用户输入
            question = input("\n👤 您：")

            if question.strip().lower() in ["exit", "退出", "quit"]:
                print("\n👋 再见！")
                break

            if not question.strip():
                continue

            print("\n🧠 ReAct Agent 开始推理...\n")
            print("=" * 60)

            # 执行 ReAct Agent
            response = agent_executor.invoke({"input": question})

            print("=" * 60)
            print("\n✅ 最终答案：")
            print(response['output'])

            # 显示推理步骤统计
            if 'intermediate_steps' in response:
                steps_count = len(response['intermediate_steps'])
                print(f"\n📊 本次推理使用了 {steps_count} 个步骤")

        except KeyboardInterrupt:
            print("\n\n👋 对话已中断")
            break
        except Exception as e:  # noqa: BLE001
            print(f"\n❌ 错误：{e}")
            import traceback
            traceback.print_exc()


def demo_react_vs_normal():
    """
    演示 ReAct Agent 与普通 Agent 的区别
    """
    print("\n" + "=" * 80)
    print("🔍 ReAct vs 普通 Agent 对比演示")
    print("=" * 80)

    question = "帮我查北京天气，如果适合出行就推荐景点"

    print(f"\n问题：{question}")
    print("\n【ReAct Agent 的处理过程】")
    print("Thought: 用户想知道北京天气，并根据天气情况推荐景点。我需要先查天气。")
    print("Action: get_weather")
    print("Action Input: 北京")
    print("Observation: 北京天气：晴天，温度15-25℃，空气质量良好。天气晴朗，空气质量良好，非常适合出行游玩")
    print("Thought: 天气很好，适合出行。我应该推荐户外景点。")
    print("Action: search_attractions")
    print("Action Input: city=北京, weather_condition=good")
    print("Observation: 天气好，推荐北京的户外景点：长城（八达岭）、颐和园、天坛公园、奥林匹克公园")
    print("Thought: 现在我有了天气信息和景点推荐，可以给出完整的建议了。")
    print(
        "Final Answer: 北京今天天气很好（晴天15-25℃），非常适合出行！推荐您去这些户外景点：长城、颐和园、天坛公园、奥林匹克公园。")

    print("\n【普通 Agent 可能的处理】")
    print("直接并行调用：get_weather(北京) + search_attractions(北京)")
    print("结果：可能推荐了室内外所有景点，没有根据天气条件筛选")

    print("\n🎯 ReAct 的优势：")
    print("  ✅ 根据天气结果动态调整推荐策略")
    print("  ✅ 推理过程透明，用户能看到思考逻辑")
    print("  ✅ 更符合人类的思维方式")


def main():
    """主函数"""
    print("选择运行模式：")
    print("1. 交互式 ReAct Agent 聊天")
    print("2. ReAct vs 普通 Agent 对比演示")

    choice = input("\n请选择 (1/2): ").strip()

    if choice == "1":
        interactive_react_chat()
    elif choice == "2":
        demo_react_vs_normal()
        print("\n继续体验交互式聊天...")
        interactive_react_chat()
    else:
        print("无效选择，启动交互式聊天...")
        interactive_react_chat()


if __name__ == "__main__":
    main()

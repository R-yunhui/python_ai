"""
LangChain Agent 多轮对话 + 多工具并行调用示例

功能特性：
1. Agent 智能体：自动决策调用哪些工具、何时结束
2. 对话历史：支持多轮对话，记住上下文
3. 多工具并行调用：一句话可以同时触发多个工具
4. 流式输出（可选）

可用工具：
- get_current_time: 获取当前时间
- get_city_weather: 查询城市天气（支持北京/上海/成都/广州）
- search_attractions: 查询城市景点
- calculate_trip_days: 计算两个日期之间的天数
- search_restaurants: 查询城市美食推荐

使用示例：
    python 03_study_agent.py
    
    问题示例：
    - "现在几点了？"
    - "查一下北京和上海的天气"（并行调用2个工具）
    - "我想去成都旅游，帮我查天气和景点"（并行调用2个工具）
    - "从5月1日到5月7日一共几天？"
    - "成都有什么好吃的？"
"""
import os
import uuid
from datetime import datetime
from typing import Dict
from random import choice, randint

from dotenv import load_dotenv
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool, BaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory

# 加载环境变量
load_dotenv()

# 定义 ChatOpenAI
ai_large_model = ChatOpenAI(
    base_url=os.getenv("OPENAI_API_BASE", "http://192.168.2.54:9015/v1/"),
    model=os.getenv("OPENAI_MODEL", "qwen2.5-vl-72b-instruct"),
    api_key=os.getenv("OPENAI_API_KEY", None),
    temperature=0.7,
    max_tokens=2048
)

# 全局会话历史存储
chat_history_store: Dict[str, ChatMessageHistory] = {}


# ========== 工具定义 ==========

@tool
def get_current_time() -> str:
    """
    获取当前时间。
    当用户询问现在几点、当前时间时调用此工具。
    """
    now = datetime.now()
    return f"当前时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}"


@tool
def get_city_weather(city: str) -> str:
    """
    获取指定城市的天气信息。
    当用户询问某个城市的天气情况时调用此工具。
    
    参数:
        city: 城市名称，如"北京"、"上海"、"成都"、"广州"
    """
    weather_data = {
        "北京": "晴天，气温15-25℃，空气质量良好，适合出行",
        "上海": "多云，气温20-28℃，湿度较大，可能有小雨",
        "成都": "阴天，气温18-26℃，典型成都天气，建议带伞",
        "广州": "晴天，气温25-33℃，炎热潮湿，注意防晒",
        "杭州": "多云转晴，气温19-27℃，天气宜人",
        "深圳": "雷阵雨，气温24-30℃，午后有雷雨"
    }

    if city in weather_data:
        return f"📍 {city}天气：{weather_data[city]}\n💡 提示：以上为模拟数据"
    else:
        return f"抱歉，暂时没有{city}的天气数据。支持查询：{', '.join(weather_data.keys())}"


@tool
def search_attractions(city: str) -> str:
    """
    查询指定城市的热门景点。
    当用户询问某个城市有什么景点、好玩的地方时调用此工具。
    
    参数:
        city: 城市名称，如"北京"、"上海"等
    """
    attractions_data = {
        "北京": [
            "🏯 故宫博物院 - 世界最大的古代宫殿建筑群（门票60元）",
            "🏔️ 长城（八达岭） - 不到长城非好汉（门票40元）",
            "🏞️ 颐和园 - 中国最大的皇家园林（门票30元）",
            "⛩️ 天坛公园 - 明清皇帝祭天之地（门票15元）"
        ],
        "上海": [
            "🌃 外滩 - 万国建筑博览群，夜景绝美（免费）",
            "🗼 东方明珠塔 - 上海地标建筑（门票180-220元）",
            "🏛️ 豫园 - 江南古典园林（门票40元）",
            "🎨 田子坊 - 石库门创意街区（免费）"
        ],
        "成都": [
            "🐼 大熊猫繁育研究基地 - 近距离看国宝（门票55元）",
            "🏮 宽窄巷子 - 成都慢生活体验（免费）",
            "🎭 锦里古街 - 三国文化主题街区（免费）",
            "🙏 武侯祠 - 纪念诸葛亮的祠堂（门票60元）"
        ],
        "广州": [
            "🗼 广州塔（小蛮腰） - 世界第三高塔（门票150-298元）",
            "🏛️ 陈家祠 - 岭南建筑艺术瑰宝（门票10元）",
            "🏝️ 沙面岛 - 欧式建筑群（免费）",
            "⛰️ 白云山 - 羊城第一秀（门票5元）"
        ]
    }

    if city in attractions_data:
        result = f"🎯 {city}热门景点推荐：\n\n"
        result += "\n".join(attractions_data[city])
        result += "\n\n💡 提示：以上为模拟数据"
        return result
    else:
        return f"抱歉，暂时没有{city}的景点数据。支持查询：{', '.join(attractions_data.keys())}"


@tool
def calculate_trip_days(start_date: str, end_date: str) -> str:
    """
    计算旅行天数（从开始日期到结束日期之间的天数）。
    当用户询问某个时间段有多少天时调用此工具。
    
    参数:
        start_date: 开始日期，格式如"2024-05-01"或"5月1日"
        end_date: 结束日期，格式如"2024-05-07"或"5月7日"
    """
    try:
        # 简化处理：假设用户输入的是月-日格式
        from datetime import datetime

        # 尝试解析不同格式
        formats = ["%Y-%m-%d", "%m月%d日", "%Y年%m月%d日"]
        start = None
        end = None

        for fmt in formats:
            try:
                if start is None:
                    start = datetime.strptime(start_date, fmt)
            except:
                pass
            try:
                if end is None:
                    end = datetime.strptime(end_date, fmt)
            except:
                pass

        if start and end:
            days = (end - start).days + 1  # +1 包含结束日期当天
            return f"从 {start_date} 到 {end_date} 一共 {days} 天"
        else:
            # 如果解析失败，返回模拟数据
            return f"从 {start_date} 到 {end_date} 大约 7 天（模拟数据）"
    except Exception as e:
        return "日期格式识别失败，请使用如 '2024-05-01' 或 '5月1日' 的格式"


@tool
def search_restaurants(city: str) -> str:
    """
    查询指定城市的美食推荐。
    当用户询问某个城市有什么好吃的、美食推荐时调用此工具。
    
    参数:
        city: 城市名称
    """
    restaurants_data = {
        "北京": [
            "🦆 全聚德烤鸭 - 北京烤鸭老字号（人均200元）",
            "🍜 护国寺小吃 - 地道北京小吃（人均50元）",
            "🍲 东来顺涮羊肉 - 百年老店（人均150元）",
            "🥟 馅老满饺子 - 手工水饺（人均60元）"
        ],
        "上海": [
            "🦀 王宝和酒家 - 正宗上海本帮菜（人均180元）",
            "🥟 小杨生煎 - 上海生煎包（人均30元）",
            "🍜 南翔馒头店 - 小笼包发源地（人均80元）",
            "🍛 德兴馆 - 上海面馆老字号（人均50元）"
        ],
        "成都": [
            "🔥 蜀大侠火锅 - 地道成都火锅（人均120元）",
            "🌶️ 陈麻婆豆腐 - 麻婆豆腐创始店（人均70元）",
            "🍜 洞子口张老二凉粉 - 成都凉粉（人均25元）",
            "🥘 小龙坎火锅 - 网红火锅（人均100元）"
        ],
        "广州": [
            "🥟 点都德 - 正宗广式早茶（人均80元）",
            "🍲 陶陶居 - 百年茶楼（人均120元）",
            "🦆 惠食佳 - 粤菜名店（人均150元）",
            "🍜 银记肠粉 - 广州肠粉老字号（人均40元）"
        ]
    }

    if city in restaurants_data:
        result = f"🍴 {city}美食推荐：\n\n"
        result += "\n".join(restaurants_data[city])
        result += "\n\n💡 提示：以上为模拟数据，价格仅供参考"
        return result
    else:
        return f"抱歉，暂时没有{city}的美食数据。支持查询：{', '.join(restaurants_data.keys())}"


# ========== Agent 配置 ==========

def get_session_history(session_id: str) -> ChatMessageHistory:
    """
    获取会话历史。
    RunnableWithMessageHistory 会自动调用此函数来获取/保存历史记录。
    """
    if session_id not in chat_history_store:
        chat_history_store[session_id] = ChatMessageHistory()
    return chat_history_store[session_id]


def create_agent_with_history(user_id: str = "default_user"):
    """
    创建带历史记录的 Agent
    
    参数:
        user_id: 用户ID，用于区分不同用户的会话
    
    返回:
        带历史记录的 Agent Executor
    """
    # 1. 定义提示词模板
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """
        # 角色设定
        你是一个智能旅行助手"旅小智"，友好、专业、高效。
        
        # 核心能力
        你拥有以下5个工具，可以**同时调用多个工具**来高效回答用户：
        
        1. get_current_time() - 获取当前时间
        2. get_city_weather(city) - 查询城市天气
        3. search_attractions(city) - 查询城市景点
        4. calculate_trip_days(start_date, end_date) - 计算旅行天数
        5. search_restaurants(city) - 查询城市美食
        
        # 智能调用策略
        - 当用户问"北京和上海的天气"时，**同时调用** get_city_weather("北京") 和 get_city_weather("上海")
        - 当用户问"去成都旅游"时，**同时调用** get_city_weather("成都") 和 search_attractions("成都")
        - 当用户问"成都有什么好玩好吃的"时，**同时调用** search_attractions("成都") 和 search_restaurants("成都")
        
        # 行为准则
        1. **主动并行调用**：能同时调用的工具就不要分开调用，提高效率
        2. **记忆上下文**：记住用户之前提到的城市、日期等信息
        3. **友好交互**：返回的数据都是模拟的，要提醒用户
        4. **主动询问**：信息不足时询问用户
        """),
        # 对话历史占位符（Agent 会自动管理）
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        # 用户输入
        ("human", "{input}"),
        # Agent 的思考过程（必需，Agent 用来记录工具调用）
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # 2. 定义工具列表
    tools = [
        get_current_time,
        get_city_weather,
        search_attractions,
        calculate_trip_days,
        search_restaurants
    ]

    # 3. 创建 Agent
    agent = create_tool_calling_agent(
        llm=ai_large_model,
        tools=tools,
        prompt=prompt_template
    )

    # 4. 创建 AgentExecutor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,  # 打印 Agent 的思考过程（推荐开启以观察多工具调用）
        max_iterations=10,  # 最多10轮工具调用（防止死循环）
        handle_parsing_errors=True  # 自动处理解析错误
    )

    # 5. 包装为带历史记录的 Runnable
    agent_with_history = RunnableWithMessageHistory(
        agent_executor,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history"
    )

    return agent_with_history


def interactive_chat(user_id: str = "user_001"):
    """
    交互式聊天主函数
    
    参数:
        user_id: 用户ID
    """
    # 生成会话ID（每次运行生成新会话，如需持久化可改为固定ID）
    session_id = f"{user_id}_{uuid.uuid4().hex[:8]}"

    print("=" * 70)
    print("🤖 欢迎使用 AI旅行助手 - 旅小智（Agent 版）")
    print("=" * 70)
    print("\n✨ 特性：")
    print("  • 多轮对话：记住上下文，可以连续提问")
    print("  • 智能决策：自动决定调用哪些工具、调用几次")
    print("  • 并行调用：一句话同时触发多个工具，提高效率")
    print("\n🛠️ 可用工具：")
    print("  ⏰ 获取当前时间")
    print("  🌤️  查询城市天气")
    print("  🎯 查询城市景点")
    print("  📅 计算旅行天数")
    print("  🍴 查询城市美食")
    print("\n💡 示例问题：")
    print("  • 现在几点了？")
    print("  • 查一下北京和上海的天气（并行调用）")
    print("  • 我想去成都旅游（会自动查天气+景点）")
    print("  • 成都有什么好玩好吃的？（并行调用）")
    print("  • 我上次问的是哪个城市？（测试多轮对话）")
    print("\n输入 'exit' 或 '退出' 结束对话")
    print("=" * 70 + "\n")

    # 创建 Agent
    agent_with_history = create_agent_with_history(user_id)

    while True:
        try:
            # 获取用户输入
            question = input("\n👤 您：")

            if question.strip().lower() in ["exit", "退出", "quit"]:
                print("\n👋 再见！期待下次为您服务！")
                break

            if not question.strip():
                continue

            print("\n🤖 旅小智：", end="", flush=True)

            # 调用 Agent（传入 session_id 以启用历史记录）
            response = agent_with_history.invoke(
                {"input": question},
                config=RunnableConfig(
                    configurable={"session_id": session_id}
                )
            )

            # 打印 Agent 的最终输出
            print(f"\n{response['output']}")

        except KeyboardInterrupt:
            print("\n\n👋 对话已中断，再见！")
            break
        except Exception as e:
            print(f"\n❌ 错误：{e}")
            import traceback
            traceback.print_exc()


def main():
    """主入口"""
    interactive_chat(user_id="user_001")


if __name__ == "__main__":
    main()

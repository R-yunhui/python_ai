"""
LangChain 智能旅行规划助手 - 完整示例

功能特性：
1. 使用提示词模板 (ChatPromptTemplate)
2. 上下文记忆 (RunnableWithMessageHistory + ChatMessageHistory)
3. 流式输出 (stream)
4. 多工具调用 (5个旅行相关工具)
5. 模拟数据演示

可用工具：
- get_current_time: 获取当前时间
- get_city_weather: 查询城市7天天气预报（支持北京/上海/成都/广州）
- search_flights: 查询往返航班信息
- search_trains: 查询往返火车票信息
- search_attractions: 查询城市热门景点

使用示例：
    python 02_study_tool.py
    
    问题示例：
    - "我想去北京旅游"
    - "帮我查一下从上海到成都的机票和火车票"
    - "北京有哪些好玩的景点？"
    - "成都的天气怎么样？"
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
    # 绑定所有可用工具
    ai_large_model_with_tools = ai_large_model.bind_tools([
        get_current_time,  # 获取当前时间
        get_city_weather,  # 查询城市天气
        search_flights,  # 查询航班信息
        search_trains,  # 查询火车票信息
        search_attractions  # 查询景点信息
    ])

    # 提示词模板
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", """
        # 角色设定
        你是一个名为"旅小助"的AI旅行规划师。你友好、专业、且充满热情。你的目标是帮助用户轻松规划每一次旅行，即使目前所有数据都只是用于演示的模拟数据。
        
        # 核心能力与可用工具
        你有以下5个工具可以使用，请根据用户需求**主动调用相应工具**：
        
        1.  **get_current_time()** - 获取当前时间
            *   当用户询问现在几点、当前时间时使用
        
        2.  **get_city_weather(city)** - 查询城市天气
            *   参数: city - 城市名称（如"北京"、"上海"、"成都"、"广州"）
            *   返回未来7天的天气预报
            *   当用户询问某地天气时使用
        
        3.  **search_flights(departure_city, arrival_city)** - 查询往返航班
            *   参数: departure_city - 出发城市, arrival_city - 目的地城市
            *   返回往返航班信息，包括航班号、时间、票价、余票
            *   当用户询问机票、航班信息时使用
        
        4.  **search_trains(departure_city, arrival_city)** - 查询往返火车票
            *   参数: departure_city - 出发城市, arrival_city - 目的地城市
            *   返回往返火车票信息，包括车次、时间、票价、余票
            *   当用户询问火车票、高铁、动车信息时使用
        
        5.  **search_attractions(city)** - 查询城市景点
            *   参数: city - 城市名称
            *   返回热门景点列表，包括名称、特色、门票、开放时间
            *   当用户询问景点、旅游景点、好玩的地方时使用
        
        # 智能使用工具
        *   当用户问"去北京旅游"时，你应该**主动**调用 get_city_weather("北京") 和 search_attractions("北京")
        *   当用户问"从上海去成都"时，你应该**主动**调用 search_flights("上海", "成都") 或 search_trains("上海", "成都")
        *   当信息不足时，先询问用户，再调用工具
        
        # 行为准则
        1.  **主动使用工具**: 当用户需求明确时，立即调用相应工具获取信息，不要只是告知可以查询
        2.  **【重要】声明模拟性质**: 工具返回的数据都是模拟的，提醒用户这是演示数据
        3.  **主动询问**: 当信息不完整时（如用户只说"我想去旅游"），主动询问关键信息（去哪里、什么时候、几天等）
        4.  **综合建议**: 结合工具返回的信息，给出专业的旅行建议和行程规划
        5.  **确认与引导**: 查询完一项信息后，可以主动询问是否需要查询其他信息
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

    print("=" * 70)
    print("🌍 欢迎使用 AI旅行规划师 - 旅小助")
    print("=" * 70)
    print("\n我可以帮您：")
    print("  ⏰ 获取当前时间")
    print("  🌤️  查询城市天气（未来7天）- 支持：北京、上海、成都、广州")
    print("  ✈️  查询往返航班信息")
    print("  🚄 查询往返火车票信息")
    print("  🎯 推荐城市热门景点")
    print("\n💡 示例问题：")
    print("  • 现在几点了？")
    print("  • 我想去北京旅游，帮我看看天气和景点")
    print("  • 查一下从上海到成都的机票和火车票")
    print("  • 成都有哪些好玩的地方？")
    print("\n输入 'exit' 或 '退出' 结束对话")
    print("=" * 70 + "\n")

    question = input("问题：")
    while question not in ["exit", "退出"]:
        try:
            print("AI回复：", end="", flush=True)

            first = True
            ai_message = None
            for chunk in message_history.stream(
                    {"question": question},
                    config=RunnableConfig(
                        configurable={"session_id": session_id}
                    )
            ):
                if first:
                    ai_message = chunk
                    first = False
                else:
                    ai_message += chunk

                # 实时显示文本内容
                if hasattr(chunk, "content") and chunk.content:
                    print(chunk.content, end="", flush=True)

            print()  # 换行

            # ✅ 修复：检查并处理工具调用
            if ai_message and hasattr(ai_message, "tool_calls") and ai_message.tool_calls:
                print(f"\n🔧 正在调用工具获取信息...")

                # 获取历史记录
                history = get_memory_history(session_id)

                # 添加AI的工具调用消息
                history.add_message(AIMessage(
                    content="",
                    tool_calls=ai_message.tool_calls
                ))

                # 处理每个工具调用（静默执行，不显示原始结果）
                tool_count = len(ai_message.tool_calls)
                print(f"发现 {tool_count} 个工具需要调用")
                for idx, tool_call in enumerate(ai_message.tool_calls, 1):
                    tool_name = tool_call['name']
                    tool_args = tool_call.get('args', {})
                    tool_id = tool_call['id']

                    # 只显示工具名称，不显示原始结果
                    print(f"  [{idx}/{tool_count}] 正在查询: {tool_name} 工具参数: {tool_args}", end="", flush=True)

                    # 执行工具
                    try:
                        if tool_name == "get_current_time":
                            result = get_current_time.invoke({})
                        elif tool_name == "get_city_weather":
                            result = get_city_weather.invoke(tool_args)
                        elif tool_name == "search_flights":
                            result = search_flights.invoke(tool_args)
                        elif tool_name == "search_trains":
                            result = search_trains.invoke(tool_args)
                        elif tool_name == "search_attractions":
                            result = search_attractions.invoke(tool_args)
                        else:
                            result = f"未知工具: {tool_name}"

                        print(" ✅")

                    except Exception as tool_error:
                        result = f"工具执行出错: {str(tool_error)}"
                        print(f" ❌ 失败: {tool_error}")

                    # 添加工具执行结果到历史（AI会基于这些结果生成回复）
                    history.add_message(ToolMessage(
                        content=result,
                        tool_call_id=tool_id
                    ))

                # 让AI基于工具结果生成友好、专业的回复
                print("\n💬 AI回复：", end="", flush=True)
                for chunk in message_history.stream(
                        {"question": ""},
                        config=RunnableConfig(
                            configurable={"session_id": session_id}
                        )
                ):
                    if hasattr(chunk, "content") and chunk.content:
                        print(chunk.content, end="", flush=True)
                print()
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            traceback.print_exc()

        question = input("\n问题：")

    print("\n会话结束")


def get_memory_history(session_id: str) -> ChatMessageHistory:
    """获取会话历史记录"""
    history = chat_memory_history.get(session_id)
    if not history:
        history = ChatMessageHistory()
        chat_memory_history[session_id] = history
    return history


@tool
def get_current_time() -> str:
    """获取当前时间。当用户询问现在几点、当前时间时调用此工具。"""
    # 函数的docstring非常重要！AI会根据它判断何时使用这个工具
    now = datetime.now()
    return now.strftime("%Y年%m月%d日 %H:%M:%S")


@tool
def get_city_weather(city: str) -> str:
    """
    获取指定城市未来一周的天气预报。
    当用户询问某个城市的天气情况时调用此工具。
    
    参数:
        city: 城市名称，如"北京"、"上海"、"成都"等
    
    返回:
        该城市未来7天的天气预报信息
    """
    # 模拟天气数据
    weather_templates = {
        "北京": [
            "今天：晴，15-25℃，空气质量良好",
            "明天：多云，16-26℃，微风",
            "后天：小雨，14-22℃，北风3-4级",
            "第4天：阴，13-20℃，空气湿润",
            "第5天：晴，17-27℃，适合出行",
            "第6天：多云转晴，18-28℃，天气舒适",
            "第7天：晴，19-29℃，紫外线较强"
        ],
        "上海": [
            "今天：多云，20-28℃，湿度较大",
            "明天：小雨，19-25℃，东南风",
            "后天：中雨，18-23℃，出行带伞",
            "第4天：阴转多云，19-26℃，湿度70%",
            "第5天：晴，21-29℃，适合游玩",
            "第6天：晴转多云，22-30℃，天气宜人",
            "第7天：多云，21-28℃，微风拂面"
        ],
        "成都": [
            "今天：多云，18-26℃，典型成都天气",
            "明天：阴，17-24℃，可能有小雨",
            "后天：小雨，16-22℃，湿度较大",
            "第4天：阴转晴，18-25℃，天气转好",
            "第5天：晴，20-28℃，适合游览景点",
            "第6天：多云，19-27℃，舒适宜人",
            "第7天：晴，21-29℃，绝佳旅行天气"
        ],
        "广州": [
            "今天：晴，25-33℃，炎热潮湿",
            "明天：多云，26-34℃，注意防晒",
            "后天：雷阵雨，24-31℃，午后雷雨",
            "第4天：阴转多云，25-32℃，湿度80%",
            "第5天：晴，27-35℃，高温预警",
            "第6天：晴转多云，26-34℃，体感闷热",
            "第7天：多云，25-33℃，可能有阵雨"
        ]
    }

    if city in weather_templates:
        weather_info = f"📍 {city}未来7天天气预报：\n\n"
        weather_info += "\n".join([f"  {day}" for day in weather_templates[city]])
        weather_info += f"\n\n💡 温馨提示：以上为模拟数据，仅供演示使用。"
        return weather_info
    else:
        return f"抱歉，暂时没有{city}的天气数据。目前支持查询：北京、上海、成都、广州的天气信息。"


@tool
def search_flights(departure_city: str, arrival_city: str) -> str:
    """
    查询指定城市之间的往返航班信息。
    当用户询问机票、航班信息时调用此工具。
    
    参数:
        departure_city: 出发城市，如"北京"
        arrival_city: 目的地城市，如"上海"
    
    返回:
        往返航班的详细信息，包括航班号、时间、价格等
    """
    # 模拟航班数据
    from random import choice, randint

    airlines = ["中国国航", "东方航空", "南方航空", "海南航空", "春秋航空"]
    flight_times = [
        ("07:30", "10:15"), ("09:45", "12:30"), ("13:20", "16:05"),
        ("15:40", "18:25"), ("18:00", "20:45"), ("20:30", "23:15")
    ]

    result = f"✈️  {departure_city} ⇄ {arrival_city} 往返航班信息\n"
    result += "=" * 60 + "\n\n"

    # 去程航班
    result += f"【去程】 {departure_city} → {arrival_city}\n"
    result += "-" * 60 + "\n"

    for i in range(3):
        airline = choice(airlines)
        depart_time, arrive_time = choice(flight_times)
        flight_no = f"CA{randint(1000, 9999)}" if airline == "中国国航" else f"MU{randint(1000, 9999)}"
        price = randint(500, 1500)
        seats = randint(5, 50)

        result += f"{i + 1}. {airline} {flight_no}\n"
        result += f"   出发：{depart_time}  到达：{arrive_time}\n"
        result += f"   票价：¥{price}  余票：{seats}张\n\n"

    # 返程航班
    result += f"【返程】 {arrival_city} → {departure_city}\n"
    result += "-" * 60 + "\n"

    for i in range(3):
        airline = choice(airlines)
        depart_time, arrive_time = choice(flight_times)
        flight_no = f"CA{randint(1000, 9999)}" if airline == "中国国航" else f"MU{randint(1000, 9999)}"
        price = randint(500, 1500)
        seats = randint(5, 50)

        result += f"{i + 1}. {airline} {flight_no}\n"
        result += f"   出发：{depart_time}  到达：{arrive_time}\n"
        result += f"   票价：¥{price}  余票：{seats}张\n\n"

    result += "⚠️  注意：以上为模拟数据，仅用于功能演示。"
    return result


@tool
def search_trains(departure_city: str, arrival_city: str) -> str:
    """
    查询指定城市之间的往返火车票信息。
    当用户询问火车票、高铁、动车信息时调用此工具。
    
    参数:
        departure_city: 出发城市，如"北京"
        arrival_city: 目的地城市，如"上海"
    
    返回:
        往返火车票的详细信息，包括车次、时间、价格等
    """
    from random import choice, randint

    train_types = ["G", "D", "K", "T"]  # 高铁、动车、快速、特快
    train_times = [
        ("06:30", "12:45"), ("08:15", "14:30"), ("10:50", "17:05"),
        ("13:20", "19:35"), ("15:45", "21:50"), ("18:00", "00:15")
    ]

    result = f"🚄  {departure_city} ⇄ {arrival_city} 往返火车票信息\n"
    result += "=" * 60 + "\n\n"

    # 去程车次
    result += f"【去程】 {departure_city} → {arrival_city}\n"
    result += "-" * 60 + "\n"

    for i in range(4):
        train_type = choice(train_types)
        train_no = f"{train_type}{randint(1, 999)}"
        depart_time, arrive_time = choice(train_times)

        if train_type in ["G", "D"]:
            second_class = randint(400, 600)
            first_class = randint(600, 900)
            result += f"{i + 1}. {train_no}次 (高速动车)\n"
            result += f"   出发：{depart_time}  到达：{arrive_time}\n"
            result += f"   二等座：¥{second_class}  一等座：¥{first_class}\n"
            result += f"   余票：二等座{randint(10, 100)}张，一等座{randint(5, 30)}张\n\n"
        else:
            hard_seat = randint(100, 200)
            soft_seat = randint(200, 350)
            result += f"{i + 1}. {train_no}次 (普通列车)\n"
            result += f"   出发：{depart_time}  到达：{arrive_time}\n"
            result += f"   硬座：¥{hard_seat}  软座：¥{soft_seat}\n"
            result += f"   余票：硬座{randint(20, 150)}张，软座{randint(10, 50)}张\n\n"

    # 返程车次
    result += f"【返程】 {arrival_city} → {departure_city}\n"
    result += "-" * 60 + "\n"

    for i in range(4):
        train_type = choice(train_types)
        train_no = f"{train_type}{randint(1, 999)}"
        depart_time, arrive_time = choice(train_times)

        if train_type in ["G", "D"]:
            second_class = randint(400, 600)
            first_class = randint(600, 900)
            result += f"{i + 1}. {train_no}次 (高速动车)\n"
            result += f"   出发：{depart_time}  到达：{arrive_time}\n"
            result += f"   二等座：¥{second_class}  一等座：¥{first_class}\n"
            result += f"   余票：二等座{randint(10, 100)}张，一等座{randint(5, 30)}张\n\n"
        else:
            hard_seat = randint(100, 200)
            soft_seat = randint(200, 350)
            result += f"{i + 1}. {train_no}次 (普通列车)\n"
            result += f"   出发：{depart_time}  到达：{arrive_time}\n"
            result += f"   硬座：¥{hard_seat}  软座：¥{soft_seat}\n"
            result += f"   余票：硬座{randint(20, 150)}张，软座{randint(10, 50)}张\n\n"

    result += "⚠️  注意：以上为模拟数据，仅用于功能演示。"
    return result


@tool
def search_attractions(city: str) -> str:
    """
    查询指定城市的热门特色景点信息。
    当用户询问景点、旅游景点、好玩的地方时调用此工具。
    
    参数:
        city: 城市名称，如"北京"、"上海"等
    
    返回:
        该城市的热门景点列表，包括景点名称、特色、开放时间等
    """
    # 模拟景点数据
    attractions_data = {
        "北京": [
            {
                "name": "故宫博物院",
                "type": "历史文化",
                "rating": "⭐⭐⭐⭐⭐",
                "ticket": "60元/人（旺季），40元/人（淡季）",
                "hours": "08:30-17:00（周一闭馆）",
                "highlight": "世界最大的古代宫殿建筑群，明清两代皇宫",
                "tips": "建议预留3-4小时，提前网上预约"
            },
            {
                "name": "长城（八达岭）",
                "type": "历史遗迹",
                "rating": "⭐⭐⭐⭐⭐",
                "ticket": "40元/人（旺季），35元/人（淡季）",
                "hours": "06:30-19:00",
                "highlight": "不到长城非好汉，世界七大奇迹之一",
                "tips": "建议穿舒适运动鞋，携带足够饮水"
            },
            {
                "name": "颐和园",
                "type": "皇家园林",
                "rating": "⭐⭐⭐⭐⭐",
                "ticket": "30元/人",
                "hours": "06:30-20:00",
                "highlight": "中国现存最大的皇家园林，昆明湖美景",
                "tips": "春秋季节最佳，可乘船游湖"
            },
            {
                "name": "天坛公园",
                "type": "历史文化",
                "rating": "⭐⭐⭐⭐",
                "ticket": "15元/人（公园门票）",
                "hours": "06:00-22:00",
                "highlight": "明清皇帝祭天祈谷之地，回音壁神奇",
                "tips": "清晨可以看到很多晨练的老人"
            }
        ],
        "上海": [
            {
                "name": "外滩",
                "type": "城市地标",
                "rating": "⭐⭐⭐⭐⭐",
                "ticket": "免费",
                "hours": "全天开放",
                "highlight": "万国建筑博览群，浦江两岸绝美夜景",
                "tips": "夜景最美，建议傍晚前往"
            },
            {
                "name": "东方明珠塔",
                "type": "现代地标",
                "rating": "⭐⭐⭐⭐",
                "ticket": "180-220元/人（不同高度）",
                "hours": "08:00-21:30",
                "highlight": "上海标志性建筑，俯瞰全城美景",
                "tips": "建议购买联票含观光层+玻璃栈道"
            },
            {
                "name": "豫园",
                "type": "古典园林",
                "rating": "⭐⭐⭐⭐",
                "ticket": "40元/人",
                "hours": "08:45-17:00",
                "highlight": "江南古典园林，品尝地道上海小吃",
                "tips": "周边城隍庙小吃街值得一逛"
            },
            {
                "name": "田子坊",
                "type": "文化创意",
                "rating": "⭐⭐⭐⭐",
                "ticket": "免费",
                "hours": "10:00-23:00",
                "highlight": "石库门里的创意天地，文艺小资",
                "tips": "适合拍照，有很多特色小店"
            }
        ],
        "成都": [
            {
                "name": "大熊猫繁育研究基地",
                "type": "动物观赏",
                "rating": "⭐⭐⭐⭐⭐",
                "ticket": "55元/人",
                "hours": "07:30-18:00",
                "highlight": "近距离观看国宝大熊猫，萌化你的心",
                "tips": "建议早上去，熊猫更活跃"
            },
            {
                "name": "宽窄巷子",
                "type": "历史文化街区",
                "rating": "⭐⭐⭐⭐",
                "ticket": "免费",
                "hours": "全天开放",
                "highlight": "成都慢生活缩影，品茶、美食、文化",
                "tips": "体验掏耳朵，尝试盖碗茶"
            },
            {
                "name": "锦里古街",
                "type": "民俗文化",
                "rating": "⭐⭐⭐⭐",
                "ticket": "免费",
                "hours": "全天开放",
                "highlight": "三国文化主题，川西民俗风情",
                "tips": "夜景更美，小吃众多"
            },
            {
                "name": "武侯祠",
                "type": "历史文化",
                "rating": "⭐⭐⭐⭐",
                "ticket": "60元/人",
                "hours": "08:00-18:00",
                "highlight": "纪念诸葛亮的祠堂，三国文化胜地",
                "tips": "可与锦里一起游览"
            }
        ],
        "广州": [
            {
                "name": "广州塔（小蛮腰）",
                "type": "现代地标",
                "rating": "⭐⭐⭐⭐⭐",
                "ticket": "150-298元/人",
                "hours": "09:30-22:30",
                "highlight": "世界第三高塔，珠江夜游最佳视角",
                "tips": "夜景灯光秀精彩，建议晚上去"
            },
            {
                "name": "陈家祠",
                "type": "岭南建筑",
                "rating": "⭐⭐⭐⭐",
                "ticket": "10元/人",
                "hours": "08:30-17:30",
                "highlight": "岭南建筑艺术的瑰宝，精美砖雕",
                "tips": "岭南文化的精华所在"
            },
            {
                "name": "沙面岛",
                "type": "历史风貌区",
                "rating": "⭐⭐⭐⭐",
                "ticket": "免费",
                "hours": "全天开放",
                "highlight": "欧式建筑群，广州最具异国情调的地方",
                "tips": "适合散步拍照，有很多咖啡馆"
            },
            {
                "name": "白云山",
                "type": "自然风光",
                "rating": "⭐⭐⭐⭐",
                "ticket": "5元/人",
                "hours": "06:00-21:00",
                "highlight": "羊城第一秀，登高望远好去处",
                "tips": "可乘索道上山，山顶视野开阔"
            }
        ]
    }

    if city in attractions_data:
        result = f"🎯  {city}热门特色景点推荐\n"
        result += "=" * 60 + "\n\n"

        for idx, attraction in enumerate(attractions_data[city], 1):
            result += f"【景点{idx}】{attraction['name']}\n"
            result += f"  类型：{attraction['type']}  |  评分：{attraction['rating']}\n"
            result += f"  门票：{attraction['ticket']}\n"
            result += f"  时间：{attraction['hours']}\n"
            result += f"  亮点：{attraction['highlight']}\n"
            result += f"  贴士：{attraction['tips']}\n"
            result += "-" * 60 + "\n\n"

        result += "💡  温馨提示：以上为模拟数据，实际信息请以景区官方公告为准。"
        return result
    else:
        return f"抱歉，暂时没有{city}的景点数据。目前支持查询：北京、上海、成都、广州的景点信息。"


def generate_session_id(user_id: str) -> str:
    """生成会话ID 使用UUID"""
    return f"{user_id}-{str(uuid.uuid4())}"


def main():
    user_id = "user"
    temperature = 0.7
    max_tokens = 1024
    simple_chat_robot(user_id, temperature, max_tokens)


if __name__ == "__main__":
    main()

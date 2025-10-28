"""
Plan-and-Execute Agent 实现示例 - 智能旅行规划助手

Plan-and-Execute = Planning + Execution
核心特点：
1. 规划器（Planner）：制定完整的执行计划
2. 执行器（Executor）：按计划逐步执行任务
3. 全局视角：先整体规划，再分步执行
4. 适合复杂任务：多步骤、有依赖关系的任务

工作流程：
Question → Plan (制定计划) → Execute Step 1 → Execute Step 2 → ... → Final Answer

实际场景：智能旅行规划
- 用户：我想去北京旅游3天，预算5000元，喜欢历史文化
- 规划器：制定详细的3天行程计划
- 执行器：逐步查询天气、景点、交通、住宿、预算等信息

使用示例：
    python 02_plan_execute_agent.py
    
    测试问题：
    - "我想去北京旅游3天，预算5000元，喜欢历史文化"
    - "帮我规划一个上海2天商务出差行程"
    - "制定一个成都美食探索的周末计划"
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_community.chat_message_histories import ChatMessageHistory
from pydantic import BaseModel, Field
from typing import Optional

# 加载环境变量
load_dotenv()

# 初始化 LLM
large_model = ChatOpenAI(
    base_url=os.getenv("OPENAI_API_BASE", "http://192.168.2.54:9015/v1/"),
    model=os.getenv("OPENAI_MODEL", "qwen2.5-vl-72b-instruct"),
    api_key=os.getenv("OPENAI_API_KEY", None),
    temperature=0.3,  # Plan-and-Execute 需要更稳定的输出
    max_tokens=3000
)

# 会话历史存储
chat_history_store: Dict[str, ChatMessageHistory] = {}


# ========== 数据结构定义 ==========

class TravelStep(BaseModel):
    """旅行计划执行步骤"""
    step_name: str = Field(description="步骤名称，如'获取天气信息'")
    tool_name: str = Field(description="要使用的工具名称")
    parameters: Dict[str, str] = Field(description="工具参数，键值对格式")
    description: str = Field(description="步骤描述说明")

    class Config:
        json_schema_extra = {
            "example": {
                "step_name": "获取天气信息",
                "tool_name": "get_weather_forecast",
                "parameters": {"city": "北京", "days": "3"},
                "description": "查询北京未来3天天气，为行程安排提供参考"
            }
        }


class TravelPlan(BaseModel):
    """旅行计划数据结构"""
    destination: str = Field(description="目的地城市名称")
    duration: int = Field(description="旅行天数", ge=1, le=30)
    budget: int = Field(description="预算金额（人民币）", ge=100)
    preferences: List[str] = Field(description="旅行偏好列表，如['历史文化', '自然风光']")
    steps: List[TravelStep] = Field(description="执行步骤列表")

    class Config:
        json_schema_extra = {
            "example": {
                "destination": "北京",
                "duration": 3,
                "budget": 5000,
                "preferences": ["历史文化"],
                "steps": [
                    {
                        "step_name": "获取天气信息",
                        "tool_name": "get_weather_forecast",
                        "parameters": {"city": "北京", "days": "3"},
                        "description": "查询北京未来3天天气，为行程安排提供参考"
                    }
                ]
            }
        }


class StepResult(BaseModel):
    """步骤执行结果"""
    step_name: str = Field(description="步骤名称")
    tool_name: str = Field(description="工具名称")
    success: bool = Field(description="执行是否成功")
    result: str = Field(description="执行结果内容")
    error_message: Optional[str] = Field(default=None, description="错误信息（如果有）")


class ExecutionReport(BaseModel):
    """执行报告"""
    plan: TravelPlan = Field(description="原始计划")
    results: List[StepResult] = Field(description="执行结果列表")
    success_count: int = Field(description="成功执行的步骤数")
    total_count: int = Field(description="总步骤数")
    success_rate: float = Field(description="成功率（0-1）")


# ========== 工具定义 ==========

@tool
def get_weather_forecast(city: str, days: str) -> str:
    """
    获取指定城市未来几天的天气预报。
    
    参数:
        city: 城市名称，如"北京"
        days: 天数，如"3"
    """
    try:
        days_int = int(days)
    except ValueError:
        return f"错误：天数'{days}'不是有效数字"

    # 模拟天气数据
    weather_patterns = {
        "北京": ["晴天", "多云", "小雨", "阴天", "晴天", "多云", "晴天"],
        "上海": ["多云", "小雨", "阴天", "晴天", "多云", "小雨", "晴天"],
        "成都": ["阴天", "小雨", "多云", "小雨", "阴天", "晴天", "多云"],
        "广州": ["晴天", "雷阵雨", "晴天", "多云", "雷阵雨", "晴天", "多云"],
        "杭州": ["多云", "晴天", "小雨", "晴天", "多云", "晴天", "阴天"],
        "深圳": ["晴天", "雷阵雨", "多云", "晴天", "雷阵雨", "晴天", "多云"]
    }

    temperatures = {
        "北京": [18, 25], "上海": [22, 28], "成都": [20, 26],
        "广州": [26, 32], "杭州": [21, 27], "深圳": [25, 31]
    }

    if city not in weather_patterns:
        return f"抱歉，暂无{city}的天气数据。支持城市：{', '.join(weather_patterns.keys())}"

    forecast = f"📅 {city}未来{days_int}天天气预报：\n"
    base_date = datetime.now()

    for i in range(min(days_int, 7)):
        date = base_date + timedelta(days=i)
        weather = weather_patterns[city][i % len(weather_patterns[city])]
        temp_range = temperatures[city]
        temp = f"{temp_range[0] + i}-{temp_range[1] + i}℃"

        day_name = "今天" if i == 0 else f"{i + 1}天后"
        forecast += f"  {day_name}({date.strftime('%m-%d')}): {weather}, {temp}\n"

    forecast += "\n💡 提示：以上为模拟数据"
    return forecast


@tool
def search_attractions_by_preference(city: str, preferences: str, duration: str) -> str:
    """
    根据偏好和停留时间搜索景点。
    
    参数:
        city: 城市名称
        preferences: 偏好类型，如"历史文化,自然风光"
        duration: 停留天数，如"3"
    """
    try:
        duration_int = int(duration)
    except ValueError:
        return f"错误：天数'{duration}'不是有效数字"

    # 按偏好分类的景点数据
    attractions_db = {
        "北京": {
            "历史文化": [
                {"name": "故宫博物院", "time": "半天", "price": 60, "rating": 4.8,
                 "description": "明清皇宫，世界文化遗产"},
                {"name": "长城（八达岭）", "time": "一天", "price": 40, "rating": 4.7, "description": "万里长城精华段"},
                {"name": "天坛公园", "time": "3小时", "price": 15, "rating": 4.6, "description": "明清皇帝祭天之地"},
                {"name": "颐和园", "time": "半天", "price": 30, "rating": 4.5, "description": "清代皇家园林"},
                {"name": "雍和宫", "time": "2小时", "price": 25, "rating": 4.4, "description": "藏传佛教寺院"}
            ],
            "现代都市": [
                {"name": "三里屯", "time": "3小时", "price": 0, "rating": 4.3, "description": "时尚购物区"},
                {"name": "798艺术区", "time": "4小时", "price": 0, "rating": 4.4, "description": "当代艺术中心"},
                {"name": "奥林匹克公园", "time": "半天", "price": 0, "rating": 4.2, "description": "鸟巢水立方"}
            ],
            "自然风光": [
                {"name": "香山公园", "time": "半天", "price": 10, "rating": 4.3, "description": "赏红叶胜地"},
                {"name": "北海公园", "time": "3小时", "price": 10, "rating": 4.2, "description": "皇家园林湖景"}
            ]
        },
        "上海": {
            "历史文化": [
                {"name": "外滩", "time": "2小时", "price": 0, "rating": 4.8, "description": "万国建筑博览群"},
                {"name": "豫园", "time": "3小时", "price": 40, "rating": 4.5, "description": "江南古典园林"},
                {"name": "田子坊", "time": "3小时", "price": 0, "rating": 4.4, "description": "石库门文化街区"}
            ],
            "现代都市": [
                {"name": "东方明珠塔", "time": "2小时", "price": 220, "rating": 4.3, "description": "上海地标建筑"},
                {"name": "陆家嘴", "time": "半天", "price": 0, "rating": 4.6, "description": "金融中心天际线"},
                {"name": "新天地", "time": "3小时", "price": 0, "rating": 4.4, "description": "时尚休闲区"}
            ]
        },
        "成都": {
            "历史文化": [
                {"name": "武侯祠", "time": "3小时", "price": 60, "rating": 4.5, "description": "三国文化圣地"},
                {"name": "锦里古街", "time": "3小时", "price": 0, "rating": 4.4, "description": "川西民俗文化街"},
                {"name": "杜甫草堂", "time": "2小时", "price": 60, "rating": 4.3, "description": "诗圣故居"}
            ],
            "自然风光": [
                {"name": "大熊猫繁育基地", "time": "半天", "price": 55, "rating": 4.8, "description": "国宝大熊猫"},
                {"name": "青城山", "time": "一天", "price": 90, "rating": 4.6, "description": "道教名山"}
            ],
            "现代都市": [
                {"name": "宽窄巷子", "time": "3小时", "price": 0, "rating": 4.5, "description": "成都慢生活体验"},
                {"name": "春熙路", "time": "3小时", "price": 0, "rating": 4.2, "description": "购物美食中心"}
            ]
        }
    }

    if city not in attractions_db:
        return f"抱歉，暂无{city}的景点数据"

    # 解析偏好
    pref_list = [p.strip() for p in preferences.split(',')]

    # 收集匹配的景点
    matched_attractions = []
    for pref in pref_list:
        if pref in attractions_db[city]:
            matched_attractions.extend(attractions_db[city][pref])

    if not matched_attractions:
        available_prefs = list(attractions_db[city].keys())
        return f"未找到匹配'{preferences}'的景点。可选偏好：{', '.join(available_prefs)}"

    # 按评分排序并选择合适数量
    matched_attractions.sort(key=lambda x: x['rating'], reverse=True)
    recommended_count = min(len(matched_attractions), duration_int * 3)  # 每天推荐3个景点

    result = f"🎯 {city} {duration_int}天行程景点推荐（偏好：{preferences}）：\n\n"

    total_cost = 0
    for i, attraction in enumerate(matched_attractions[:recommended_count], 1):
        result += f"{i}. {attraction['name']} ⭐{attraction['rating']}\n"
        result += f"   游览时间：{attraction['time']} | 门票：¥{attraction['price']}\n"
        result += f"   特色：{attraction['description']}\n\n"
        total_cost += attraction['price']

    result += f"💰 预估门票总费用：¥{total_cost}\n"
    result += "💡 提示：以上为模拟数据，实际请以官方信息为准"

    return result


@tool
def search_accommodation(city: str, budget_per_night: str, duration: str) -> str:
    """
    搜索住宿选择。
    
    参数:
        city: 城市名称
        budget_per_night: 每晚预算，如"300"
        duration: 住宿天数，如"2"
    """
    try:
        budget_int = int(budget_per_night)
        duration_int = int(duration)
    except ValueError:
        return "错误：预算或天数不是有效数字"

    # 住宿数据
    hotels_db = {
        "北京": [
            {"name": "北京饭店", "type": "五星酒店", "price": 800, "rating": 4.7, "location": "王府井",
             "features": ["历史悠久", "地理位置佳"]},
            {"name": "希尔顿酒店", "type": "国际连锁", "price": 600, "rating": 4.6, "location": "朝阳区",
             "features": ["设施完善", "服务优质"]},
            {"name": "如家酒店", "type": "经济连锁", "price": 200, "rating": 4.2, "location": "各区域",
             "features": ["性价比高", "连锁品牌"]},
            {"name": "7天酒店", "type": "经济连锁", "price": 150, "rating": 4.0, "location": "各区域",
             "features": ["价格实惠", "基础设施"]},
            {"name": "青年旅社", "type": "青旅", "price": 80, "rating": 3.8, "location": "市中心",
             "features": ["超低价格", "适合背包客"]}
        ],
        "上海": [
            {"name": "和平饭店", "type": "历史酒店", "price": 900, "rating": 4.8, "location": "外滩",
             "features": ["历史建筑", "外滩景观"]},
            {"name": "万豪酒店", "type": "国际连锁", "price": 700, "rating": 4.6, "location": "浦东",
             "features": ["豪华设施", "商务便利"]},
            {"name": "汉庭酒店", "type": "中档连锁", "price": 250, "rating": 4.3, "location": "各区域",
             "features": ["干净舒适", "性价比好"]},
            {"name": "锦江之星", "type": "经济连锁", "price": 180, "rating": 4.1, "location": "各区域",
             "features": ["连锁品牌", "标准服务"]}
        ],
        "成都": [
            {"name": "香格里拉酒店", "type": "五星酒店", "price": 650, "rating": 4.7, "location": "市中心",
             "features": ["奢华享受", "优质服务"]},
            {"name": "全季酒店", "type": "中档连锁", "price": 280, "rating": 4.4, "location": "各区域",
             "features": ["设计感强", "舒适环境"]},
            {"name": "速8酒店", "type": "经济连锁", "price": 160, "rating": 4.0, "location": "各区域",
             "features": ["快捷便利", "基础设施"]}
        ]
    }

    if city not in hotels_db:
        return f"抱歉，暂无{city}的住宿数据"

    # 筛选符合预算的住宿
    suitable_hotels = [h for h in hotels_db[city] if h['price'] <= budget_int]

    if not suitable_hotels:
        min_price = min(h['price'] for h in hotels_db[city])
        return f"预算¥{budget_int}/晚内没有合适的住宿，最低价格为¥{min_price}/晚"

    # 按评分排序
    suitable_hotels.sort(key=lambda x: x['rating'], reverse=True)

    result = f"🏨 {city} 住宿推荐（预算¥{budget_int}/晚，共{duration_int}晚）：\n\n"

    for i, hotel in enumerate(suitable_hotels[:5], 1):
        total_cost = hotel['price'] * duration_int
        result += f"{i}. {hotel['name']} ({hotel['type']}) ⭐{hotel['rating']}\n"
        result += f"   价格：¥{hotel['price']}/晚 × {duration_int}晚 = ¥{total_cost}\n"
        result += f"   位置：{hotel['location']}\n"
        result += f"   特色：{', '.join(hotel['features'])}\n\n"

    result += "💡 提示：以上为模拟数据，实际价格请以预订平台为准"
    return result


@tool
def search_transportation(departure: str, destination: str, travel_date: str) -> str:
    """
    搜索交通方式。
    
    参数:
        departure: 出发地
        destination: 目的地  
        travel_date: 出行日期，如"2024-03-15"
    """
    # 交通数据
    transport_data = {
        ("北京", "上海"): {
            "飞机": {"time": "2小时", "price": 800, "frequency": "每小时多班"},
            "高铁": {"time": "4.5小时", "price": 550, "frequency": "每30分钟一班"},
            "普通火车": {"time": "12小时", "price": 200, "frequency": "每天3班"}
        },
        ("上海", "北京"): {
            "飞机": {"time": "2.5小时", "price": 850, "frequency": "每小时多班"},
            "高铁": {"time": "4.5小时", "price": 550, "frequency": "每30分钟一班"}
        },
        ("北京", "成都"): {
            "飞机": {"time": "3小时", "price": 900, "frequency": "每天10+班"},
            "高铁": {"time": "8小时", "price": 650, "frequency": "每天6班"}
        },
        ("成都", "北京"): {
            "飞机": {"time": "3小时", "price": 950, "frequency": "每天10+班"},
            "高铁": {"time": "8小时", "price": 650, "frequency": "每天6班"}
        }
    }

    route_key = (departure, destination)
    if route_key not in transport_data:
        return f"抱歉，暂无{departure}到{destination}的交通数据"

    result = f"🚄 {departure} → {destination} 交通方式（{travel_date}）：\n\n"

    for transport_type, info in transport_data[route_key].items():
        result += f"【{transport_type}】\n"
        result += f"  用时：{info['time']}\n"
        result += f"  价格：¥{info['price']}\n"
        result += f"  班次：{info['frequency']}\n\n"

    result += "💡 提示：以上为模拟数据，实际请查询官方平台"
    return result


@tool
def calculate_budget_breakdown(total_budget: str, transportation_cost: str, accommodation_cost: str,
                               attraction_cost: str) -> str:
    """
    计算预算分解。
    
    参数:
        total_budget: 总预算
        transportation_cost: 交通费用
        accommodation_cost: 住宿费用  
        attraction_cost: 景点门票费用
    """
    try:
        total = int(total_budget)
        transport = int(transportation_cost)
        hotel = int(accommodation_cost)
        attractions = int(attraction_cost)
    except ValueError:
        return "错误：预算数据不是有效数字"

    used_budget = transport + hotel + attractions
    remaining = total - used_budget
    food_suggestion = remaining * 0.6  # 建议60%用于餐饮
    shopping_suggestion = remaining * 0.4  # 建议40%用于购物

    result = f"💰 预算分解分析（总预算¥{total}）：\n\n"
    result += "【已规划费用】\n"
    result += f"  🚄 交通费用：¥{transport} ({transport / total * 100:.1f}%)\n"
    result += f"  🏨 住宿费用：¥{hotel} ({hotel / total * 100:.1f}%)\n"
    result += f"  🎯 景点门票：¥{attractions} ({attractions / total * 100:.1f}%)\n"
    result += f"  小计：¥{used_budget} ({used_budget / total * 100:.1f}%)\n\n"

    if remaining > 0:
        result += f"【剩余预算】¥{remaining} ({remaining / total * 100:.1f}%)\n"
        result += "  建议分配：\n"
        result += f"  🍽️  餐饮费用：¥{food_suggestion:.0f}\n"
        result += f"  🛍️  购物娱乐：¥{shopping_suggestion:.0f}\n\n"
        result += "✅ 预算充足，可以享受舒适的旅行！"
    elif remaining == 0:
        result += "⚠️ 预算刚好用完，建议预留一些应急资金"
    else:
        result += f"❌ 预算超支¥{abs(remaining)}，建议调整行程或增加预算"

    return result


# ========== 工具描述自动生成 ==========

def get_tools_description(tools_list) -> str:
    """
    从工具列表自动生成描述文本
    这样就不需要在提示词中手动维护工具信息了
    """
    descriptions = []
    
    for tool_func in tools_list:
        # 获取工具名称
        tool_name = tool_func.name
        
        # 获取工具描述（从 docstring 的第一行）
        tool_desc = tool_func.description or "无描述"
        
        # 获取参数信息（从工具的 args_schema）
        if hasattr(tool_func, 'args_schema') and tool_func.args_schema:
            schema = tool_func.args_schema.schema()
            properties = schema.get('properties', {})
            
            param_info = []
            for param_name, param_details in properties.items():
                param_type = param_details.get('type', 'string')
                param_desc = param_details.get('description', '无描述')
                param_info.append(f"{param_name} ({param_type}): {param_desc}")
            
            param_str = ", ".join(param_info) if param_info else "无参数"
        else:
            param_str = "参数信息不可用"
        
        descriptions.append(f"{tool_name} - {tool_desc}\n   参数: {param_str}")
    
    return "\n".join(descriptions)


def get_available_tools():
    """获取所有可用工具的列表"""
    return [
        get_weather_forecast,
        search_attractions_by_preference, 
        search_accommodation,
        search_transportation,
        calculate_budget_breakdown
    ]


# ========== Plan-and-Execute Agent 核心实现 ==========

def _create_default_plan(user_input: str = "") -> TravelPlan:  # noqa: ARG002
    """创建默认计划（当解析失败时）"""
    return TravelPlan(
        destination="北京",
        duration=3,
        budget=5000,
        preferences=["历史文化"],
        steps=[
            TravelStep(
                step_name="获取天气信息",
                tool_name="get_weather_forecast",
                parameters={"city": "北京", "days": "3"},
                description="查询目的地天气情况"
            ),
            TravelStep(
                step_name="搜索景点",
                tool_name="search_attractions_by_preference",
                parameters={"city": "北京", "preferences": "历史文化", "duration": "3"},
                description="根据偏好推荐景点"
            ),
            TravelStep(
                step_name="查找住宿",
                tool_name="search_accommodation",
                parameters={"city": "北京", "budget_per_night": "300", "duration": "2"},
                description="搜索合适的住宿"
            )
        ]
    )


class TravelPlanner:
    """旅行规划器 - 负责制定整体计划"""

    def __init__(self, llm):
        self.llm = llm
        
        # 获取可用工具列表
        self.available_tools = get_available_tools()
        
        # 创建 Pydantic 输出解析器
        self.parser = PydanticOutputParser(pydantic_object=TravelPlan)
        
        # 自动生成工具描述
        tools_description = get_tools_description(self.available_tools)
        
        # 规划器的提示词模板 - 使用自动生成的工具描述
        self.planner_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""
            你是一个专业的旅行规划师，负责制定详细的旅行计划。

            根据用户的旅行需求，你需要制定一个结构化的执行计划。

            可用的工具包括：
            {tools_description}

            请分析用户需求，制定合理的执行步骤。通常包括：
            - 获取天气信息（了解目的地天气情况）
            - 搜索景点（根据偏好和天数推荐）
            - 查找住宿（根据预算和天数）
            - 安排交通（如果用户提到出发地）
            - 预算分析（计算费用分解）

            请严格按照指定的JSON格式输出，确保参数名称与工具定义完全一致。
            """),
            ("human", """
            用户需求：{input}
            
            {format_instructions}
            """)
        ])

    def create_plan(self, user_input: str) -> TravelPlan:
        """创建旅行计划"""
        try:
            # 创建链：prompt | llm | parser
            chain = self.planner_prompt | self.llm | self.parser
            
            # 调用链，直接得到 TravelPlan 对象
            plan: TravelPlan = chain.invoke({
                "input": user_input,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            return plan

        except Exception as e:
            print(f"⚠️ 规划器解析失败：{e}")
            print("🔄 使用默认计划...")
            return _create_default_plan(user_input)


class TravelExecutor:
    """旅行执行器 - 负责执行具体步骤"""

    def __init__(self):
        # 获取可用工具列表并创建映射
        available_tools = get_available_tools()
        self.tools = {tool.name: tool for tool in available_tools}
        
        print(f"🔧 执行器初始化完成，加载了 {len(self.tools)} 个工具：")
        for tool_name in self.tools.keys():
            print(f"   - {tool_name}")

    def execute_step(self, step: TravelStep) -> StepResult:
        """执行单个步骤"""
        tool_name = step.tool_name
        parameters = step.parameters

        if tool_name not in self.tools:
            return StepResult(
                step_name=step.step_name,
                tool_name=tool_name,
                success=False,
                result="",
                error_message=f"未知工具: {tool_name}"
            )

        try:
            tool_func = self.tools[tool_name]
            result = tool_func.invoke(parameters)
            
            return StepResult(
                step_name=step.step_name,
                tool_name=tool_name,
                success=True,
                result=result,
                error_message=None
            )
            
        except Exception as e:
            return StepResult(
                step_name=step.step_name,
                tool_name=tool_name,
                success=False,
                result="",
                error_message=str(e)
            )

    def execute_plan(self, plan: TravelPlan) -> ExecutionReport:
        """执行完整计划"""
        results = []
        success_count = 0

        for i, step in enumerate(plan.steps, 1):
            print(f"\n🔄 执行步骤 {i}: {step.step_name}")
            print(f"   工具: {step.tool_name}")
            print(f"   参数: {step.parameters}")
            print(f"   描述: {step.description}")

            step_result = self.execute_step(step)
            results.append(step_result)
            
            if step_result.success:
                success_count += 1
                print("   ✅ 完成")
            else:
                print(f"   ❌ 失败: {step_result.error_message}")

        # 创建执行报告
        total_count = len(plan.steps)
        success_rate = success_count / total_count if total_count > 0 else 0

        return ExecutionReport(
            plan=plan,
            results=results,
            success_count=success_count,
            total_count=total_count,
            success_rate=success_rate
        )


class PlanAndExecuteAgent:
    """Plan-and-Execute Agent 主类"""

    def __init__(self, llm):
        print("🤖 初始化 Plan-and-Execute Agent...")
        
        # 获取可用工具
        self.available_tools = get_available_tools()
        print(f"📋 加载了 {len(self.available_tools)} 个专业工具")
        
        # 初始化各个组件
        self.planner = TravelPlanner(llm)
        self.executor = TravelExecutor()
        self.llm = llm
        
        print("✅ Agent 初始化完成！")

        # 最终总结的提示词模板
        self.summarizer_prompt = ChatPromptTemplate.from_messages([
            ("system", """
            你是一个旅行规划助手，需要根据执行结果为用户生成一份完整的旅行建议报告。

            请整合所有信息，生成一份结构化的旅行建议，包括：
            1. 行程概述
            2. 天气情况
            3. 推荐景点
            4. 住宿建议  
            5. 交通安排
            6. 预算分析
            7. 贴心提示

            语言要友好、专业，给出实用的建议。
            """),
            ("human", """
            原始需求：{original_request}
            
            执行计划：{plan}
            
            执行结果：{results}
            
            请生成完整的旅行建议报告。
            """)
        ])

    def process_request(self, user_input: str) -> str:
        """处理用户请求的主流程"""
        print("🧠 Plan-and-Execute Agent 开始工作...")
        print("=" * 80)

        # 第1阶段：制定计划
        print("\n📋 阶段1：制定旅行计划")
        print("-" * 40)

        plan: TravelPlan = self.planner.create_plan(user_input)

        print("✅ 计划制定完成！")
        print(f"   目的地：{plan.destination}")
        print(f"   天数：{plan.duration}天")
        print(f"   预算：¥{plan.budget}")
        print(f"   偏好：{', '.join(plan.preferences)}")
        print(f"   计划步骤：{len(plan.steps)}个")

        # 第2阶段：执行计划
        print("\n🚀 阶段2：执行计划步骤")
        print("-" * 40)

        execution_report: ExecutionReport = self.executor.execute_plan(plan)

        # 显示执行统计
        print("\n📊 执行统计：")
        print(f"   总步骤：{execution_report.total_count}")
        print(f"   成功：{execution_report.success_count}")
        print(f"   成功率：{execution_report.success_rate:.1%}")

        # 第3阶段：生成最终报告
        print("\n📊 阶段3：生成旅行建议报告")
        print("-" * 40)

        chain = self.summarizer_prompt | self.llm
        final_report = ""
        for chunk in chain.stream({
            "original_request": user_input,
            "plan": plan.model_dump_json(indent=2),
            "results": execution_report.model_dump_json(indent=2)
        }):
            final_report += chunk.content
            print(chunk.content, end="", flush=True)

        print("\n✅ 报告生成完成！")

        return final_report


# ========== 交互界面 ==========

def interactive_plan_execute_chat():
    """交互式 Plan-and-Execute Agent 聊天"""

    print("=" * 80)
    print("🗓️  Plan-and-Execute Agent - 智能旅行规划助手")
    print("=" * 80)
    print("\n✨ Plan-and-Execute 特性：")
    print("  • 全局规划：先制定完整计划，再逐步执行")
    print("  • 结构化执行：按计划有序执行各个步骤")
    print("  • 智能整合：将所有信息整合成完整建议")
    print("  • 适合复杂任务：多步骤、有依赖关系的任务")

    print("\n🎯 专业旅行规划服务：")
    print("  📅 天气预报查询")
    print("  🎯 个性化景点推荐")
    print("  🏨 住宿选择建议")
    print("  🚄 交通方式对比")
    print("  💰 预算分析规划")

    print("\n💡 测试问题（体验完整的规划流程）：")
    print("  • 我想去北京旅游3天，预算5000元，喜欢历史文化")
    print("  • 帮我规划一个上海2天商务出差行程，预算3000元")
    print("  • 制定一个成都美食探索的周末计划，预算2000元")
    print("  • 我要去杭州度假4天，预算8000元，喜欢自然风光和现代都市")

    print("\n输入 'exit' 结束对话")
    print("=" * 80 + "\n")

    # 创建 Plan-and-Execute Agent
    agent = PlanAndExecuteAgent(large_model)

    while True:
        try:
            # 获取用户输入
            question = input("\n👤 您的旅行需求：")

            if question.strip().lower() in ["exit", "退出", "quit"]:
                print("\n👋 感谢使用智能旅行规划助手！祝您旅途愉快！")
                break

            if not question.strip():
                continue

            # 处理请求
            report = agent.process_request(question)

            print("\n" + "=" * 80)
            print("📋 您的专属旅行建议报告")
            print("=" * 80)
            print(report)
            print("=" * 80)

        except KeyboardInterrupt:
            print("\n\n👋 对话已中断")
            break
        except Exception as e:
            print(f"\n❌ 错误：{e}")
            import traceback
            traceback.print_exc()


def demo_plan_vs_react():
    """
    演示 Plan-and-Execute vs ReAct 的区别
    """
    print("\n" + "=" * 80)
    print("🔍 Plan-and-Execute vs ReAct Agent 对比演示")
    print("=" * 80)

    question = "我想去北京旅游3天，预算5000元，喜欢历史文化"

    print(f"\n问题：{question}")

    print("\n【ReAct Agent 的处理过程】")
    print("Thought: 用户想去北京旅游，我需要先查天气")
    print("Action: get_weather")
    print("Observation: 北京天气不错")
    print("Thought: 天气好，我再查景点")
    print("Action: search_attractions")
    print("Observation: 找到一些景点")
    print("Thought: 还需要查住宿...")
    print("（逐步进行，边走边看）")

    print("\n【Plan-and-Execute Agent 的处理过程】")
    print("📋 阶段1：制定完整计划")
    print("   - 分析用户需求：北京3天，预算5000，历史文化偏好")
    print("   - 制定执行步骤：天气→景点→住宿→交通→预算分析")
    print("   - 确定参数：城市=北京，天数=3，偏好=历史文化")

    print("\n🚀 阶段2：按计划执行")
    print("   步骤1: 获取天气信息 ✅")
    print("   步骤2: 搜索历史文化景点 ✅")
    print("   步骤3: 查找住宿选择 ✅")
    print("   步骤4: 安排交通方式 ✅")
    print("   步骤5: 分析预算分解 ✅")

    print("\n📊 阶段3：整合生成报告")
    print("   - 将所有信息整合成完整的旅行建议")
    print("   - 提供结构化的行程规划")

    print("\n🎯 两种方法的区别：")
    print("  ReAct: 逐步探索，灵活应变，适合简单任务")
    print("  Plan-and-Execute: 全局规划，系统执行，适合复杂任务")


def debug_tools_info():
    """调试：显示自动生成的工具信息"""
    print("\n" + "=" * 80)
    print("🔧 工具信息调试")
    print("=" * 80)
    
    tools = get_available_tools()
    tools_desc = get_tools_description(tools)
    
    print(f"📋 共加载 {len(tools)} 个工具：\n")
    print(tools_desc)
    print("\n" + "=" * 80)


def main():
    """主函数"""
    print("选择运行模式：")
    print("1. 交互式旅行规划（Plan-and-Execute Agent）")
    print("2. Plan-and-Execute vs ReAct 对比演示")
    print("3. 调试工具信息（查看自动生成的工具描述）")

    choice = input("\n请选择 (1/2/3): ").strip()

    if choice == "1":
        interactive_plan_execute_chat()
    elif choice == "2":
        demo_plan_vs_react()
        print("\n继续体验旅行规划...")
        interactive_plan_execute_chat()
    elif choice == "3":
        debug_tools_info()
        print("\n继续选择其他模式...")
        main()
    else:
        print("无效选择，启动旅行规划...")
        interactive_plan_execute_chat()


if __name__ == "__main__":
    main()

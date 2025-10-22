"""
LangChain学习 - Tool工具使用

学习目标：
1. 理解什么是Tool以及为什么需要它
2. 掌握如何创建自定义工具
3. 学会将工具绑定到AI模型
4. 了解Tool与Agent的关系

对比Spring-AI：
在Spring-AI中，你可能这样写：
    @Bean
    public FunctionCallback weatherFunction() {
        return FunctionCallback.builder()
            .function("getWeather", this::getWeather)
            .description("获取天气信息")
            .build();
    }
    
在LangChain中，使用@tool装饰器更加简洁
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from typing import List
import json
from datetime import datetime

# 加载环境变量
load_dotenv()


# ============================================================================
# 什么是Tool？为什么需要它？
# ============================================================================
"""
问题场景：
用户：今天北京的天气怎么样？
AI：抱歉，我无法获取实时天气信息。(❌ 只能生成文本)

解决方案：
给AI配备"工具"，让它可以：
✅ 调用天气API获取实时信息
✅ 查询数据库
✅ 执行计算
✅ 搜索网络
✅ 调用第三方服务

类似于：
- 给人类配备工具（计算器、字典、地图等）
- Spring-AI的FunctionCallback
- OpenAI的Function Calling
- 微服务架构中的服务调用

Tool = Function + Description
AI会根据描述判断何时调用哪个工具
"""


# ============================================================================
# 示例1：创建简单的自定义工具
# ============================================================================

# 使用@tool装饰器定义工具
# 装饰器会自动将函数转换为Tool对象
@tool
def get_current_time() -> str:
    """获取当前时间。当用户询问现在几点、当前时间时调用此工具。"""
    # 函数的docstring非常重要！AI会根据它判断何时使用这个工具
    now = datetime.now()
    return now.strftime("%Y年%m月%d日 %H:%M:%S")


@tool
def calculator(expression: str) -> str:
    """
    执行数学计算。当用户需要进行数学运算时调用此工具。
    
    参数:
        expression: 数学表达式，例如 "2 + 3 * 4"
    """
    try:
        # 注意：实际项目中应该使用更安全的计算方法
        result = eval(expression)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


@tool
def search_user_info(user_id: int) -> str:
    """
    查询用户信息。当需要获取用户详细信息时调用此工具。
    
    参数:
        user_id: 用户ID
    """
    # 模拟数据库查询
    fake_database = {
        1: {"name": "张三", "age": 28, "city": "北京", "job": "工程师"},
        2: {"name": "李四", "age": 32, "city": "上海", "job": "设计师"},
        3: {"name": "王五", "age": 25, "city": "深圳", "job": "产品经理"}
    }
    
    user = fake_database.get(user_id)
    if user:
        return json.dumps(user, ensure_ascii=False)
    else:
        return f"未找到ID为{user_id}的用户"


def example1_basic_tool_usage():
    """
    演示基础的工具使用
    """
    print("\n" + "=" * 60)
    print("示例1：基础工具使用")
    print("=" * 60)
    
    # 1. 创建工具列表
    tools = [get_current_time, calculator, search_user_info]
    
    # 2. 初始化模型并绑定工具
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    
    # bind_tools() 将工具绑定到模型
    # AI现在知道它可以使用这些工具了
    llm_with_tools = llm.bind_tools(tools)
    
    # 3. 测试不同的问题
    test_questions = [
        "现在几点了？",
        "帮我计算 25 * 4 + 100",
        "查询用户ID为2的信息"
    ]
    
    for question in test_questions:
        print(f"\n❓ 用户: {question}")
        
        # 调用模型
        response = llm_with_tools.invoke(question)
        
        # 检查AI是否想要调用工具
        if response.tool_calls:
            print(f"🔧 AI决定使用工具: {response.tool_calls[0]['name']}")
            print(f"📝 工具参数: {response.tool_calls[0]['args']}")
            
            # 实际执行工具（这里需要手动执行）
            tool_name = response.tool_calls[0]['name']
            tool_args = response.tool_calls[0]['args']
            
            # 根据工具名称调用相应的函数
            if tool_name == "get_current_time":
                result = get_current_time.invoke({})
            elif tool_name == "calculator":
                result = calculator.invoke(tool_args)
            elif tool_name == "search_user_info":
                result = search_user_info.invoke(tool_args)
            
            print(f"✅ 工具执行结果: {result}")
        else:
            print(f"💬 AI直接回复: {response.content}")
        
        print("-" * 60)


# ============================================================================
# 示例2：实际应用 - 智能客服助手
# ============================================================================

@tool
def query_order_status(order_id: str) -> str:
    """
    查询订单状态。当用户询问订单信息、物流状态时使用。
    
    参数:
        order_id: 订单号
    """
    # 模拟订单数据库
    orders = {
        "ORD001": {"status": "已发货", "logistics": "顺丰快递", "tracking": "SF1234567890"},
        "ORD002": {"status": "处理中", "logistics": None, "tracking": None},
        "ORD003": {"status": "已送达", "logistics": "京东物流", "tracking": "JD9876543210"}
    }
    
    order = orders.get(order_id)
    if order:
        return json.dumps(order, ensure_ascii=False)
    else:
        return f"未找到订单号为{order_id}的订单"


@tool
def check_product_stock(product_name: str) -> str:
    """
    检查商品库存。当用户询问商品是否有货时使用。
    
    参数:
        product_name: 商品名称
    """
    # 模拟库存数据
    inventory = {
        "iPhone 15": {"stock": 50, "price": 5999},
        "MacBook Pro": {"stock": 0, "price": 12999},
        "AirPods Pro": {"stock": 200, "price": 1899}
    }
    
    product = inventory.get(product_name)
    if product:
        return json.dumps(product, ensure_ascii=False)
    else:
        return f"未找到商品：{product_name}"


@tool
def create_refund_request(order_id: str, reason: str) -> str:
    """
    创建退款申请。当用户要求退款时使用。
    
    参数:
        order_id: 订单号
        reason: 退款原因
    """
    # 模拟创建退款申请
    refund_id = f"REF{order_id[3:]}"
    return f"退款申请已创建，退款单号：{refund_id}，我们会在3个工作日内处理。原因：{reason}"


def example2_customer_service_bot():
    """
    实际应用：智能客服机器人
    演示如何组合多个工具构建完整的应用
    """
    print("\n" + "=" * 60)
    print("示例2：智能客服机器人")
    print("=" * 60)
    
    # 1. 准备工具
    tools = [
        query_order_status,
        check_product_stock,
        create_refund_request
    ]
    
    # 2. 创建系统提示词
    system_prompt = """你是一个专业的电商客服助手。
    
你的职责：
- 友好、耐心地回答用户问题
- 使用提供的工具查询实时信息
- 帮助用户解决订单、商品相关问题

注意事项：
- 当需要查询数据时，必须使用工具
- 不要编造信息，如果工具返回"未找到"，如实告知用户
- 保持礼貌和专业
"""
    
    # 3. 初始化模型
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    
    llm_with_tools = llm.bind_tools(tools)
    
    # 4. 模拟客服对话
    customer_queries = [
        "我想查一下订单ORD001的状态",
        "MacBook Pro还有货吗？",
        "我要退订单ORD002，商品不符合描述"
    ]
    
    for query in customer_queries:
        print(f"\n🧑 顾客: {query}")
        
        # 组合系统提示词和用户问题
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        response = llm_with_tools.invoke(messages)
        
        if response.tool_calls:
            tool_call = response.tool_calls[0]
            print(f"🤖 客服（思考）: 需要调用工具 {tool_call['name']}")
            
            # 执行工具
            if tool_call['name'] == "query_order_status":
                result = query_order_status.invoke(tool_call['args'])
            elif tool_call['name'] == "check_product_stock":
                result = check_product_stock.invoke(tool_call['args'])
            elif tool_call['name'] == "create_refund_request":
                result = create_refund_request.invoke(tool_call['args'])
            
            print(f"📊 工具返回: {result}")
            
            # 将工具结果返回给AI，让它生成最终回复
            messages.append({"role": "assistant", "content": "", "tool_calls": response.tool_calls})
            messages.append({"role": "tool", "content": result, "tool_call_id": tool_call['id']})
            
            final_response = llm.invoke(messages)
            print(f"🤖 客服: {final_response.content}")
        else:
            print(f"🤖 客服: {response.content}")
        
        print("-" * 60)


# ============================================================================
# 示例3：Tool的最佳实践
# ============================================================================
def example3_tool_best_practices():
    """
    Tool开发的最佳实践和注意事项
    """
    print("\n" + "=" * 60)
    print("示例3：Tool最佳实践")
    print("=" * 60)
    
    print("""
✅ Tool设计原则：

1. 清晰的函数名
   ✓ get_weather (好)
   ✗ func1 (不好)

2. 详细的docstring
   ✓ 说明何时使用、参数含义、返回值格式
   ✗ 只写"查询天气"

3. 类型注解
   ✓ def get_user(user_id: int) -> str:
   ✗ def get_user(user_id):

4. 错误处理
   ✓ 返回友好的错误信息
   ✗ 直接抛出异常

5. 幂等性
   ✓ 多次调用结果一致（查询类）
   ⚠️ 注意副作用（创建、删除类）

示例：好的Tool定义
```python
@tool
def search_products(
    keyword: str, 
    category: str = "all",
    max_results: int = 10
) -> str:
    \"\"\"
    搜索商品。当用户想要查找商品时使用此工具。
    
    参数:
        keyword: 搜索关键词，如"手机"、"笔记本"
        category: 商品分类，可选值：all, electronics, books, clothing
        max_results: 最多返回结果数，默认10条
        
    返回:
        JSON格式的商品列表
    \"\"\"
    # 实现...
    pass
```

⚠️ 常见错误：

1. Docstring不清晰
   AI不知道何时该用这个工具

2. 参数类型错误
   AI传入的参数无法解析

3. 返回值格式不统一
   有时返回字符串，有时返回字典

4. 缺少错误处理
   工具执行失败导致整个流程中断

5. 工具太复杂
   一个工具做太多事情，应该拆分

💡 实际项目中的Tool示例：

1. 数据库查询类
   - query_user
   - query_order
   - query_product

2. API调用类
   - get_weather
   - translate_text
   - search_web

3. 计算类
   - calculate_price
   - compute_distance
   - format_date

4. 业务操作类
   - create_order
   - send_email
   - generate_report

对比Spring-AI：
┌─────────────────┬────────────────────────┬──────────────────────┐
│ 功能            │ Spring-AI              │ LangChain            │
├─────────────────┼────────────────────────┼──────────────────────┤
│ 定义Tool        │ FunctionCallback       │ @tool装饰器          │
│ 描述            │ .description()         │ 函数docstring        │
│ 参数            │ Function<T, R>         │ 函数参数+类型注解    │
│ 注册            │ @Bean                  │ bind_tools()         │
└─────────────────┴────────────────────────┴──────────────────────┘
    """)


# ============================================================================
# 主函数
# ============================================================================
def main():
    """
    主函数：运行所有示例
    """
    print("🚀 开始学习LangChain Tool工具使用")
    print("=" * 60)
    
    try:
        # 检查API密钥
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ 错误：未找到OPENAI_API_KEY")
            print("请先在.env文件中配置API密钥")
            return
        
        print("\n提示：Tool让AI能够调用外部功能...\n")
        
        # 运行示例
        example1_basic_tool_usage()
        example2_customer_service_bot()
        example3_tool_best_practices()
        
        # 总结
        print("\n" + "=" * 60)
        print("✅ 恭喜！你已经掌握了Tool工具的使用")
        print("=" * 60)
        print("""
关键概念回顾：

1. Tool定义
   - 使用@tool装饰器
   - 详细的docstring（AI依赖这个）
   - 类型注解（参数和返回值）
   
2. Tool绑定
   - llm.bind_tools(tools) 将工具绑定到模型
   - AI会根据docstring判断何时使用
   - 返回tool_calls表示AI想调用工具
   
3. Tool执行
   - 需要手动执行工具函数
   - 将结果返回给AI
   - AI根据结果生成最终回复

4. 应用场景
   - 查询实时数据（天气、股价、订单）
   - 调用外部API
   - 执行计算和转换
   - 数据库操作
   - 业务流程自动化

Tool vs Agent：
- Tool: 单个功能函数
- Agent: 能够自主决策、选择和执行多个Tool的AI系统

下一步学习：
- Agent智能体 - 让AI自主决策和使用多个工具
- ReAct模式 - Reasoning + Acting
- 多轮Tool调用 - 复杂任务分解

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


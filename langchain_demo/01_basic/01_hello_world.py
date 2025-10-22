"""
第一个LangChain程序 - 最简单的AI调用

学习目标：
1. 理解如何导入和初始化LangChain模型
2. 掌握最基本的AI调用方法
3. 了解如何处理AI的响应

对比Spring-AI：
在Spring-AI中，你可能这样写：
    @Autowired
    private ChatClient chatClient;
    String response = chatClient.call("你好");
    
在LangChain中，不需要依赖注入，直接创建对象即可
"""

import os
from dotenv import load_dotenv

# ============================================================================
# 第一步：加载环境变量（读取.env文件中的API密钥）
# ============================================================================
load_dotenv()  # 这会自动读取当前目录下的.env文件

# 从环境变量中获取API密钥
# 类似于Spring Boot的 @Value("${openai.api.key}")
api_key = os.getenv("OPENAI_API_KEY")

# 检查API密钥是否存在
if not api_key:
    print("❌ 错误：未找到OPENAI_API_KEY")
    print("请先创建.env文件并设置API密钥")
    exit(1)


# ============================================================================
# 第二步：导入LangChain的OpenAI模型
# ============================================================================
from langchain_openai import ChatOpenAI

# ChatOpenAI 是LangChain对OpenAI聊天模型的封装
# 类似于Spring-AI中的ChatClient


# ============================================================================
# 第三步：创建模型实例
# ============================================================================
print("正在初始化AI模型...")

llm = ChatOpenAI(
    # 模型名称，gpt-3.5-turbo是最常用的模型
    # 其他选项：gpt-4, gpt-4-turbo等
    model="qwen2.5-vl-72b-instruct",
    
    # temperature控制回复的随机性
    # 0 = 非常确定，回复固定
    # 1 = 很随机，回复多样
    # 推荐值：0.7
    temperature=0.7,
    
    # API密钥
    api_key=api_key,
    
    # API基础URL（如果使用代理或Azure OpenAI需要修改）
    base_url=os.getenv("OPENAI_API_BASE", "http://192.168.2.54:9015/v1/")
)

print("✅ 模型初始化成功！\n")


# ============================================================================
# 第四步：发送第一条消息
# ============================================================================
print("=" * 60)
print("示例1：最简单的调用")
print("=" * 60)

# 使用invoke方法发送消息（类似Spring-AI的call方法）
response = llm.invoke("你好！请用一句话介绍你自己。")

# response是一个AIMessage对象，包含多个属性
# response.content 是AI的回复内容（最常用）
# response.response_metadata 包含token使用量等信息

print(f"用户: 你好！请用一句话介绍你自己。")
print(f"AI: {response.content}")
print()


# ============================================================================
# 第五步：查看响应的详细信息
# ============================================================================
print("=" * 60)
print("响应对象的详细信息")
print("=" * 60)

# 打印响应对象的类型
print(f"响应类型: {type(response)}")

# 打印AI回复的内容
print(f"回复内容: {response.content}")

# 打印元数据（包含token使用量等信息）
if hasattr(response, 'response_metadata'):
    print(f"元数据: {response.response_metadata}")
    
    # 获取token使用量（重要：关系到费用）
    if 'token_usage' in response.response_metadata:
        usage = response.response_metadata['token_usage']
        print(f"\n📊 Token使用情况:")
        print(f"  - 输入token: {usage.get('prompt_tokens', 0)}")
        print(f"  - 输出token: {usage.get('completion_tokens', 0)}")
        print(f"  - 总计: {usage.get('total_tokens', 0)}")

print()


# ============================================================================
# 第六步：连续对话示例
# ============================================================================
print("=" * 60)
print("示例2：多轮对话")
print("=" * 60)

# 定义一些问题
questions = [
    "Python和Java的主要区别是什么？",
    "请举一个Python的简单例子",
]

# 循环提问
for i, question in enumerate(questions, 1):
    print(f"\n【第{i}轮对话】")
    print(f"用户: {question}")
    
    # 发送消息
    response = llm.invoke(question)
    
    # 打印回复
    print(f"AI: {response.content}")


# ============================================================================
# 总结
# ============================================================================
print("\n" + "=" * 60)
print("✅ 恭喜！你已经完成了第一个LangChain程序")
print("=" * 60)
print("""
关键概念回顾：
1. ChatOpenAI - 模型类（类似Spring-AI的ChatClient）
2. invoke() - 发送消息的方法（类似Spring-AI的call()）
3. response.content - 获取AI回复内容
4. temperature - 控制回复的随机性

下一步：
- 学习如何使用消息历史（实现真正的对话）
- 学习如何使用提示词模板
- 学习如何处理流式输出

继续加油！🚀
""")


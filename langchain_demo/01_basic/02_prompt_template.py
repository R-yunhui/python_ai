"""
LangChain学习 - 提示词模板（Prompt Template）

学习目标：
1. 理解什么是提示词模板，为什么需要它
2. 掌握如何使用PromptTemplate创建模板
3. 学会使用变量动态生成提示词
4. 了解ChatPromptTemplate用于对话场景

对比Spring-AI：
在Spring-AI中，你可能这样写：
    PromptTemplate promptTemplate = new PromptTemplate(
        "告诉我关于{topic}的{count}个事实"
    );
    Prompt prompt = promptTemplate.create(
        Map.of("topic", "Python", "count", "3")
    );
    
在LangChain中，概念类似但语法更简洁
"""

import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# 加载环境变量
load_dotenv()


# ============================================================================
# 为什么需要提示词模板？
# ============================================================================
"""
在实际应用中，我们经常需要：
1. 复用相同的提示词结构，只改变部分内容
2. 避免手动拼接字符串（容易出错）
3. 提高代码的可维护性和可读性

例如：你要为100个不同的主题生成文章，提示词结构相同，只有主题不同
如果每次都手动拼接字符串，代码会很混乱。

使用模板，就像使用HTML模板或SQL的PreparedStatement一样方便！
"""


# ============================================================================
# 示例1：最简单的提示词模板
# ============================================================================
def example1_basic_template():
    """
    演示最基本的提示词模板用法
    """
    print("\n" + "=" * 60)
    print("示例1：基础提示词模板")
    print("=" * 60)
    

    # 创建一个简单的模板
    # {topic} 是变量占位符，类似Java的 %s 或 {}
    template = PromptTemplate(
        # 模板字符串，使用 {变量名} 作为占位符
        template="告诉我关于{topic}的3个有趣事实。",
        
        # 声明模板中使用的变量（可选，但建议写上）
        input_variables=["topic"]
    )
    
    # 填充模板 - 方式1：使用format方法
    prompt1 = template.format(topic="Python编程")
    print(f"生成的提示词1: {prompt1}\n")
    
    # 填充模板 - 方式2：使用invoke方法（返回PromptValue对象）
    prompt2 = template.invoke({"topic": "Java编程"})
    print(f"生成的提示词2: {prompt2.text}\n")
    
    # 实际调用AI
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "qwen2.5-vl-72b-instruct"),
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "http://192.168.2.54:9015/v1/")
    )
    
    # 直接将模板和模型组合使用
    chain = template | llm  # 使用管道操作符（|）连接模板和模型
    response = chain.invoke({"topic": "人工智能"})
    print(f"用户输入主题: 人工智能")
    print(f"AI回复:\n{response.content}\n")


# ============================================================================
# 示例2：多变量模板
# ============================================================================
def example2_multiple_variables():
    """
    演示如何使用多个变量的模板
    """
    print("\n" + "=" * 60)
    print("示例2：多变量模板")
    print("=" * 60)
    
    # 创建包含多个变量的模板
    template = PromptTemplate(
        template="""
你是一个{role}。
请用{language}语言，以{style}的风格，回答下面的问题：

问题：{question}
        """.strip(),
        input_variables=["role", "language", "style", "question"]
    )
    
    # 定义不同的角色和问题
    scenarios = [
        {
            "role": "Python专家",
            "language": "中文",
            "style": "简洁专业",
            "question": "什么是装饰器？"
        },
        {
            "role": "儿童教育专家",
            "language": "中文",
            "style": "生动有趣",
            "question": "什么是编程？"
        }
    ]
    
    # 初始化模型
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "qwen2.5-vl-72b-instruct"),
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "http://192.168.2.54:9015/v1/")
    )
    
    # 使用链式调用
    chain = template | llm
    
    # 测试不同场景
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n【场景{i}】")
        print(f"角色：{scenario['role']}")
        print(f"问题：{scenario['question']}")
        print(f"风格：{scenario['style']}")
        
        response = chain.invoke(scenario)
        print(f"\nAI回复：\n{response.content}\n")
        print("-" * 60)


# ============================================================================
# 示例3：聊天提示词模板（Chat Prompt Template）
# ============================================================================
def example3_chat_template():
    """
    演示ChatPromptTemplate的使用
    这是实际应用中最常用的模板类型
    """
    print("\n" + "=" * 60)
    print("示例3：聊天提示词模板")
    print("=" * 60)
    
    # ChatPromptTemplate可以包含多个消息
    # 类似于Spring-AI中的Message列表
    template = ChatPromptTemplate.from_messages([
        # 系统消息：定义AI的角色和行为
        ("system", "你是一个{expertise}专家，擅长用简单易懂的方式解释复杂概念。"),
        
        # 人类消息：用户的问题
        ("human", "请解释：{concept}"),
        
        # 可以添加更多消息...
    ])
    
    # 初始化模型
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "qwen2.5-vl-72b-instruct"),
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "http://192.168.2.54:9015/v1/")
    )
    
    # 创建链
    chain = template | llm
    
    # 测试
    response = chain.invoke({
        "expertise": "Python编程",
        "concept": "列表推导式"
    })
    
    print("AI回复：")
    print(response.content)


# ============================================================================
# 示例4：从文件加载模板（最佳实践）
# ============================================================================
def example4_template_best_practice():
    """
    演示如何组织和管理提示词模板（推荐方式）
    """
    print("\n" + "=" * 60)
    print("示例4：模板管理最佳实践")
    print("=" * 60)
    
    # 在实际项目中，建议将复杂的提示词定义为常量或配置
    # 这样便于维护和版本控制
    
    # 定义模板字典（类似Spring的配置文件）
    PROMPT_TEMPLATES = {
        "code_review": ChatPromptTemplate.from_messages([
            ("system", "你是一个资深的{language}代码审查专家。"),
            ("human", "请审查以下代码并给出改进建议：\n\n{code}")
        ]),
        
        "translator": ChatPromptTemplate.from_messages([
            ("system", "你是一个专业的翻译，负责将{source_lang}翻译成{target_lang}。"),
            ("human", "{text}")
        ]),
        
        "teacher": ChatPromptTemplate.from_messages([
            ("system", "你是一个{subject}老师，擅长用{method}教学法。"),
            ("human", "请教我：{topic}")
        ])
    }
    
    # 使用模板
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "qwen2.5-vl-72b-instruct"),
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "http://192.168.2.54:9015/v1/")
    )
    
    # 示例：使用翻译模板
    translator_chain = PROMPT_TEMPLATES["translator"] | llm
    
    response = translator_chain.invoke({
        "source_lang": "中文",
        "target_lang": "英文",
        "text": "早上好，今天天气真好！"
    })
    
    print("翻译结果：")
    print(response.content)


# ============================================================================
# 主函数
# ============================================================================
def main():
    """
    主函数：运行所有示例
    """
    print("🚀 开始学习LangChain提示词模板")
    print("=" * 60)
    
    try:
        # 检查API密钥
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ 错误：未找到OPENAI_API_KEY")
            print("请先在.env文件中配置API密钥")
            return
        
        # 运行各个示例
        # 你可以注释掉不想运行的示例
        # example1_basic_template()
        # example2_multiple_variables()
        # example3_chat_template()
        example4_template_best_practice()
        
        # 总结
        print("\n" + "=" * 60)
        print("✅ 恭喜！你已经掌握了提示词模板的使用")
        print("=" * 60)
        print("""
关键概念回顾：
1. PromptTemplate - 简单文本模板
   - 使用 {变量名} 作为占位符
   - 用 .format() 或 .invoke() 填充变量
   
2. ChatPromptTemplate - 聊天模板（推荐）
   - 可以包含system、human、ai等多种消息
   - 更适合对话场景
   
3. 链式调用（|操作符）
   - template | llm 将模板和模型连接
   - 类似于Unix的管道操作
   
4. 最佳实践：
   - 将模板定义为常量或配置
   - 使用有意义的变量名
   - 添加必要的注释

对比Spring-AI：
- Spring-AI: PromptTemplate + Prompt.create()
- LangChain: PromptTemplate + invoke() 或 format()
- LangChain的管道操作（|）更简洁直观

下一步学习：
- 消息历史管理（Memory）
- 输出解析器（Output Parser）
- 链（Chain）的高级用法

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


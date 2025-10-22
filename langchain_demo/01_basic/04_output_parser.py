"""
LangChain学习 - 输出解析器（Output Parser）

学习目标：
1. 理解为什么需要输出解析器
2. 掌握如何使用PydanticOutputParser解析结构化数据
3. 学会定义数据模型和验证规则
4. 了解如何在实际项目中使用解析器

对比Spring-AI：
在Spring-AI中，你可能这样写：
    BeanOutputConverter<Person> converter = new BeanOutputConverter<>(Person.class);
    String format = converter.getFormat();
    String response = chatClient.call(new Prompt("..." + format));
    Person person = converter.convert(response);
    
在LangChain中，使用Pydantic模型定义数据结构，更加pythonic
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

# 加载环境变量
load_dotenv()


# ============================================================================
# 为什么需要输出解析器？
# ============================================================================
"""
问题场景：
普通调用返回的是字符串：
    "姓名：张三，年龄：28，城市：北京"
    
但实际项目中我们需要结构化数据：
    {
        "name": "张三",
        "age": 28,
        "city": "北京"
    }

解决方案：
使用OutputParser自动将AI的文本输出解析为Python对象，
类似于：
- Spring的@ResponseBody + Jackson
- Java的ObjectMapper
- FastAPI的Response Model
"""


# ============================================================================
# 示例1：使用Pydantic定义数据模型并解析
# ============================================================================
def example1_pydantic_parser():
    """
    演示如何使用PydanticOutputParser解析结构化数据
    这是最推荐的方式，类型安全且功能强大
    """
    print("\n" + "=" * 60)
    print("示例1：使用Pydantic解析器")
    print("=" * 60)
    print("演示：让AI返回结构化的用户信息\n")
    
    # 1. 定义数据模型（类似Java的DTO或Entity）
    # Pydantic是Python最流行的数据验证库，类似Java的Bean Validation
    class Person(BaseModel):
        """用户信息模型"""
        name: str = Field(description="人物的姓名")
        age: int = Field(description="人物的年龄")
        occupation: str = Field(description="人物的职业")
        skills: List[str] = Field(description="人物掌握的技能列表")
        bio: str = Field(description="人物的简短介绍")
        
        class Config:
            json_schema_extra = {
                "example": {
                    "name": "张三",
                    "age": 28,
                    "occupation": "软件工程师",
                    "skills": ["Python", "Java", "Docker"],
                    "bio": "一名热爱编程的开发者"
                }
            }
    
    # 2. 创建解析器
    # PydanticOutputParser会自动生成格式说明，并解析AI的输出
    parser = PydanticOutputParser(pydantic_object=Person)
    
    # 3. 创建提示词模板
    # {format_instructions} 会自动插入格式说明
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个数据提取专家，请按照指定的JSON格式返回信息。"),
        ("human", """请根据以下描述，提取人物信息：

{description}

{format_instructions}
""")
    ])
    
    # 4. 初始化模型
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0,  # 使用0以获得更确定的输出
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    
    # 5. 创建链：prompt | llm | parser
    # 这个链会自动完成：生成提示词 -> 调用AI -> 解析输出
    chain = prompt | llm | parser
    
    # 6. 测试
    description = """
    李明是一位32岁的资深Python开发工程师，在一家互联网公司工作。
    他精通Python、Django、FastAPI、Docker和Kubernetes。
    他热衷于开源项目，喜欢分享技术经验。
    """
    
    print("输入描述：")
    print(description.strip())
    print("\n" + "-" * 60)
    
    # 调用链，直接得到Person对象
    result: Person = chain.invoke({
        "description": description,
        "format_instructions": parser.get_format_instructions()
    })
    
    # 7. 使用解析后的数据
    print("\n✅ 解析成功！得到的结构化数据：\n")
    print(f"姓名: {result.name}")
    print(f"年龄: {result.age}")
    print(f"职业: {result.occupation}")
    print(f"技能: {', '.join(result.skills)}")
    print(f"简介: {result.bio}")
    
    # 可以直接序列化为JSON
    print("\n📋 JSON格式：")
    print(result.model_dump_json(indent=2))
    
    # 可以直接转换为字典
    print("\n📋 字典格式：")
    print(result.model_dump())


# ============================================================================
# 示例2：实际应用 - 批量数据提取
# ============================================================================
def example2_practical_application():
    """
    实际应用场景：从文本中提取多个产品信息
    类似于爬虫数据清洗、文档信息提取等场景
    """
    print("\n" + "=" * 60)
    print("示例2：实际应用 - 批量产品信息提取")
    print("=" * 60)
    print("演示：从商品描述中提取结构化信息\n")
    
    # 1. 定义产品模型
    class Product(BaseModel):
        """产品信息模型"""
        name: str = Field(description="产品名称")
        price: float = Field(description="产品价格（人民币）")
        category: str = Field(description="产品分类")
        features: List[str] = Field(description="产品主要特点")
        rating: float = Field(description="用户评分（1-5分）")
    
    class ProductList(BaseModel):
        """产品列表模型"""
        products: List[Product] = Field(description="产品列表")
        total_count: int = Field(description="产品总数")
    
    # 2. 创建解析器
    parser = PydanticOutputParser(pydantic_object=ProductList)
    
    # 3. 创建提示词
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个电商数据分析专家，擅长从商品描述中提取结构化信息。"),
        ("human", """请从以下商品列表中提取信息：

{product_descriptions}

{format_instructions}
""")
    ])
    
    # 4. 初始化模型和链
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    
    chain = prompt | llm | parser
    
    # 5. 测试数据
    product_descriptions = """
    1. iPhone 15 Pro - 售价7999元，旗舰智能手机。
       特点：A17芯片、钛金属边框、4800万像素主摄、支持USB-C。
       用户评分：4.8分
    
    2. MacBook Air M2 - 售价8999元，轻薄笔记本电脑。
       特点：M2芯片、13.6英寸屏幕、18小时续航、1.24kg轻巧。
       用户评分：4.9分
    
    3. AirPods Pro 2 - 售价1899元，无线降噪耳机。
       特点：主动降噪、空间音频、H2芯片、30小时续航。
       用户评分：4.7分
    """
    
    print("输入商品描述...")
    print("\n" + "-" * 60)
    print("正在提取结构化数据...\n")
    
    # 6. 调用链
    result: ProductList = chain.invoke({
        "product_descriptions": product_descriptions,
        "format_instructions": parser.get_format_instructions()
    })
    
    # 7. 展示结果
    print(f"✅ 成功提取 {result.total_count} 个产品信息：\n")
    
    for i, product in enumerate(result.products, 1):
        print(f"【产品 {i}】")
        print(f"  名称：{product.name}")
        print(f"  价格：¥{product.price}")
        print(f"  分类：{product.category}")
        print(f"  特点：{', '.join(product.features)}")
        print(f"  评分：{product.rating}/5.0")
        print()
    
    # 8. 可以直接用于数据库存储
    print("📊 可以直接存储到数据库：")
    for product in result.products:
        # 模拟数据库插入
        data = product.model_dump()
        print(f"INSERT INTO products VALUES ({data})")


# ============================================================================
# 实用技巧：错误处理
# ============================================================================
def example3_error_handling():
    """
    演示如何处理解析错误
    实际项目中很重要
    """
    print("\n" + "=" * 60)
    print("示例3：错误处理最佳实践")
    print("=" * 60)
    
    class SimpleData(BaseModel):
        """简单数据模型"""
        title: str = Field(description="标题")
        count: int = Field(description="数量")
    
    parser = PydanticOutputParser(pydantic_object=SimpleData)
    
    print("""
错误处理策略：

1. 使用try-except捕获解析错误
2. 设置temperature=0以获得更稳定的输出
3. 在提示词中明确要求JSON格式
4. 使用with_structured_output()方法（新版LangChain）
5. 添加重试机制

示例代码：
```python
try:
    result = chain.invoke({"input": user_input})
    # 处理成功的结果
except Exception as e:
    print(f"解析失败: {e}")
    # 记录日志或返回默认值
```

在实际项目中的应用：
✅ API响应数据结构化
✅ 爬虫数据清洗
✅ 文档信息提取
✅ 表单自动填充
✅ 数据库批量导入

类比Spring-AI：
- LangChain的Pydantic模型 ≈ Spring的@Valid + Bean Validation
- OutputParser ≈ Spring的HttpMessageConverter
- model_dump() ≈ Jackson的ObjectMapper
    """)


# ============================================================================
# 主函数
# ============================================================================
def main():
    """
    主函数：运行所有示例
    """
    print("🚀 开始学习LangChain输出解析器")
    print("=" * 60)
    
    try:
        # 检查API密钥
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ 错误：未找到OPENAI_API_KEY")
            print("请先在.env文件中配置API密钥")
            return
        
        print("\n提示：示例会调用AI模型，可能需要等待几秒钟...\n")
        
        # 运行示例
        example1_pydantic_parser()
        example2_practical_application()
        example3_error_handling()
        
        # 总结
        print("\n" + "=" * 60)
        print("✅ 恭喜！你已经掌握了输出解析器的使用")
        print("=" * 60)
        print("""
关键概念回顾：

1. Pydantic模型
   - 定义数据结构（类似Java的DTO）
   - 自动数据验证
   - 类型安全
   
2. PydanticOutputParser
   - 自动生成格式说明
   - 解析AI输出为Python对象
   - 支持嵌套模型和列表
   
3. 链式调用
   - prompt | llm | parser
   - 自动完成整个流程
   - 代码简洁清晰

4. 实际应用
   - 数据提取和清洗
   - API响应结构化
   - 批量数据处理
   - 表单自动填充

对比Spring-AI：
┌──────────────────┬─────────────────────────┬──────────────────────┐
│ 功能             │ Spring-AI               │ LangChain            │
├──────────────────┼─────────────────────────┼──────────────────────┤
│ 数据模型         │ Java Bean + @Valid      │ Pydantic BaseModel   │
│ 输出解析         │ BeanOutputConverter     │ PydanticOutputParser │
│ 验证             │ Bean Validation         │ Pydantic自动验证     │
│ 序列化           │ Jackson ObjectMapper    │ model_dump_json()    │
└──────────────────┴─────────────────────────┴──────────────────────┘

使用场景：
✅ 从文本中提取结构化信息（姓名、日期、金额等）
✅ 自动填充表单或数据库
✅ API返回标准化JSON
✅ 批量数据处理和清洗
✅ 文档信息提取和分类

下一步学习：
- 流式输出（Streaming）- 实时显示AI回复
- RAG检索增强 - 构建知识库问答系统
- Agent智能体 - 让AI自主使用工具

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


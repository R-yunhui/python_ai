"""
LangChain学习 - 流式输出（Streaming Output）

学习目标：
1. 理解为什么需要流式输出
2. 掌握如何使用stream()方法实现流式响应
3. 学会在实际项目中应用流式输出提升用户体验
4. 了解流式输出与普通输出的区别

对比Spring-AI：
在Spring-AI中，你可能这样写：
    Flux<ChatResponse> stream = chatClient.stream(prompt);
    stream.subscribe(response -> {
        System.out.print(response.getResult());
    });
    
在LangChain中，使用stream()方法更加简洁直观
"""

import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import time

# 加载环境变量
load_dotenv()


# ============================================================================
# 为什么需要流式输出？
# ============================================================================
"""
用户体验对比：

【普通输出】
用户: 写一篇文章
AI: (等待10秒...)
AI: 完整的文章内容全部显示

问题：用户需要等待很久，体验不好

【流式输出】
用户: 写一篇文章
AI: 人工智能...
AI: 人工智能是当今...
AI: 人工智能是当今最热门的技术...
(逐字逐句显示，类似ChatGPT)

优势：
✅ 即时反馈，用户体验更好
✅ 感觉响应更快
✅ 可以提前看到部分内容
✅ 类似打字机效果

应用场景：
- 聊天机器人
- 内容生成工具
- 代码助手
- 实时翻译
"""


# ============================================================================
# 示例1：基础流式输出
# ============================================================================
def example1_basic_streaming():
    """
    演示最基础的流式输出
    对比普通输出和流式输出的区别
    """
    print("\n" + "=" * 60)
    print("示例1：基础流式输出")
    print("=" * 60)
    
    # 初始化模型
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    
    question = "请用100字左右介绍一下Python编程语言的特点。"
    
    # 1. 普通输出（非流式）
    print("\n【方式1：普通输出】")
    print("问题:", question)
    print("\n正在等待完整响应...\n")
    
    start_time = time.time()
    response = llm.invoke(question)
    end_time = time.time()
    
    print("AI回复:", response.content)
    print(f"\n⏱️  耗时: {end_time - start_time:.2f}秒")
    
    # 2. 流式输出
    print("\n" + "-" * 60)
    print("\n【方式2：流式输出】")
    print("问题:", question)
    print("\nAI回复: ", end="", flush=True)
    
    start_time = time.time()
    
    # 使用stream()方法获取流式响应
    # 每个chunk是AI生成的一小段文本
    for chunk in llm.stream(question):
        # chunk.content 包含这一小段的文本内容
        print(chunk.content, end="", flush=True)
        # flush=True 确保立即显示，不缓冲
    
    end_time = time.time()
    print(f"\n\n⏱️  总耗时: {end_time - start_time:.2f}秒")
    print("💡 注意：流式输出总时间相同，但用户感觉更快！")


# ============================================================================
# 示例2：结合提示词模板的流式输出（实用）
# ============================================================================
def example2_streaming_with_template():
    """
    在实际项目中的完整流式输出实现
    结合提示词模板和输出解析器
    """
    print("\n" + "=" * 60)
    print("示例2：实际应用 - 流式文章生成器")
    print("=" * 60)
    
    # 1. 创建提示词模板
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的技术文章作者，擅长写清晰易懂的技术文章。"),
        ("human", """请写一篇关于"{topic}"的技术文章。
        
要求：
- 包含引言、正文和结论
- 使用通俗易懂的语言
- 字数在200字左右
- 适合初学者阅读
""")
    ])
    
    # 2. 初始化模型
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    
    # 3. 创建输出解析器
    output_parser = StrOutputParser()
    
    # 4. 创建链
    # prompt | llm | output_parser
    chain = prompt | llm | output_parser
    
    # 5. 使用流式输出
    topic = "Python装饰器"
    
    print(f"\n📝 正在生成关于「{topic}」的文章...\n")
    print("=" * 60)
    
    # 使用chain.stream()获取流式输出
    full_response = ""
    for chunk in chain.stream({"topic": topic}):
        print(chunk, end="", flush=True)
        full_response += chunk
        
        # 可以在这里添加更多逻辑
        # 例如：保存到数据库、显示进度等
    
    print("\n" + "=" * 60)
    print(f"\n✅ 文章生成完成！总字数: {len(full_response)}")
    
    # 6. 保存完整内容
    print("\n💾 完整内容已保存到变量中，可以进一步处理")
    return full_response


# ============================================================================
# 示例3：带回调的流式输出（高级）
# ============================================================================
def example3_streaming_with_callback():
    """
    演示如何在流式输出中添加自定义处理逻辑
    例如：实时统计、进度显示、日志记录等
    """
    print("\n" + "=" * 60)
    print("示例3：带统计的流式输出")
    print("=" * 60)
    
    # 初始化模型
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.7,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    )
    
    question = "请列举5个Python的最佳实践，每个用一句话说明。"
    
    print(f"\n问题: {question}\n")
    print("AI回复:\n" + "-" * 60)
    
    # 统计变量
    chunk_count = 0
    char_count = 0
    full_response = ""
    
    # 流式输出并统计
    for chunk in llm.stream(question):
        content = chunk.content
        print(content, end="", flush=True)
        
        # 实时统计
        chunk_count += 1
        char_count += len(content)
        full_response += content
    
    print("\n" + "-" * 60)
    
    # 显示统计信息
    print("\n📊 统计信息:")
    print(f"  - 总块数: {chunk_count}")
    print(f"  - 总字符数: {char_count}")
    print(f"  - 平均每块字符数: {char_count/chunk_count:.1f}")
    
    # 在实际项目中，你可以：
    print("\n💡 实际应用场景:")
    print("""
    1. 实时保存到数据库
       for chunk in llm.stream(question):
           save_to_db(chunk.content)
    
    2. 显示进度条
       for chunk in llm.stream(question):
           update_progress_bar(len(chunk.content))
    
    3. WebSocket实时推送
       for chunk in llm.stream(question):
           websocket.send(chunk.content)
    
    4. 日志记录
       for chunk in llm.stream(question):
           logger.info(f"Generated: {chunk.content}")
    """)


# ============================================================================
# 实用技巧：在FastAPI中使用流式输出
# ============================================================================
def example4_fastapi_integration():
    """
    演示如何在FastAPI中集成流式输出
    这是实际Web应用中最常见的场景
    """
    print("\n" + "=" * 60)
    print("示例4：FastAPI集成示例（代码示范）")
    print("=" * 60)
    
    print("""
在FastAPI中实现流式输出（类似ChatGPT网页版）：

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI
import asyncio

app = FastAPI()

@app.post("/chat/stream")
async def stream_chat(question: str):
    \"\"\"流式聊天接口\"\"\"
    
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7,
        streaming=True  # 启用流式输出
    )
    
    async def generate():
        \"\"\"异步生成器函数\"\"\"
        for chunk in llm.stream(question):
            # 返回Server-Sent Events格式
            yield f"data: {chunk.content}\\n\\n"
            await asyncio.sleep(0)  # 让出控制权
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

前端JavaScript接收：

```javascript
const eventSource = new EventSource('/chat/stream?question=你好');

eventSource.onmessage = (event) => {
    // 实时显示每个chunk
    document.getElementById('response').innerText += event.data;
};

eventSource.onerror = () => {
    eventSource.close();
};
```

关键点：
✅ 使用StreamingResponse返回流式数据
✅ 使用Server-Sent Events (SSE)协议
✅ 前端使用EventSource接收数据
✅ 实现类似ChatGPT的打字机效果
    """)


# ============================================================================
# 主函数
# ============================================================================
def main():
    """
    主函数：运行所有示例
    """
    print("🚀 开始学习LangChain流式输出")
    print("=" * 60)
    
    try:
        # 检查API密钥
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ 错误：未找到OPENAI_API_KEY")
            print("请先在.env文件中配置API密钥")
            return
        
        print("\n提示：流式输出会实时显示AI的回复...\n")
        
        # 运行示例
        # 你可以注释掉不想运行的示例
        
        example1_basic_streaming()
        example2_streaming_with_template()
        example3_streaming_with_callback()
        example4_fastapi_integration()
        
        # 总结
        print("\n" + "=" * 60)
        print("✅ 恭喜！你已经掌握了流式输出的使用")
        print("=" * 60)
        print("""
关键概念回顾：

1. stream() 方法
   - llm.stream(question) 返回生成器
   - 逐块返回AI生成的内容
   - 每个chunk是一小段文本
   
2. 使用技巧
   - 使用 flush=True 立即显示
   - 可以实时统计和处理
   - 结合chain也能流式输出
   
3. 实际应用
   - Web聊天机器人（最常用）
   - 内容生成工具
   - 实时翻译
   - 代码生成助手

对比Spring-AI：
┌────────────────┬──────────────────────────┬────────────────────────┐
│ 功能           │ Spring-AI                │ LangChain              │
├────────────────┼──────────────────────────┼────────────────────────┤
│ 流式输出       │ Flux<ChatResponse>       │ llm.stream()           │
│ 订阅方式       │ flux.subscribe()         │ for chunk in stream    │
│ 集成框架       │ Spring WebFlux           │ FastAPI StreamingResp  │
│ 前端协议       │ SSE / WebSocket          │ SSE / WebSocket        │
└────────────────┴──────────────────────────┴────────────────────────┘

用户体验提升：
✅ 感觉响应速度更快（即时反馈）
✅ 避免长时间等待的焦虑
✅ 可以提前看到部分内容
✅ 类似ChatGPT的打字机效果

技术优势：
✅ 降低首字节时间（TTFB）
✅ 更好的用户交互体验
✅ 可以实时处理和保存数据
✅ 支持长文本生成

下一步学习：
- Tool工具使用 - 让AI使用外部工具
- Agent智能体 - AI自主决策和执行
- 函数调用 - Function Calling

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


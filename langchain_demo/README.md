# LangChain 入门学习 - 从零开始

## 🎯 学习目标
作为有Java/Spring-AI经验的开发者，从最基础的LangChain调用开始学习。

---

## 📦 第一步：安装依赖

```bash
# 1. 进入项目目录
cd langchain_demo

# 2. 安装依赖（建议先创建虚拟环境）
pip install -r requirements.txt
```

---

## 🔑 第二步：配置API密钥

```bash
# 1. 复制示例配置文件
cp .env.example .env

# 2. 编辑.env文件，填入你的OpenAI API密钥
# OPENAI_API_KEY=sk-your-actual-key-here
```

---

## 🚀 第三步：运行第一个程序

```bash
python 01_hello_world.py
```

---

## 📚 学习顺序

### 01_basic/ 基础入门
1. **01_hello_world.py** ✅ - 最简单的调用，理解基本概念
2. **02_prompt_template.py** ✅ - 提示词模板，动态生成提示词
3. **03_conversation_memory.py** 👈 当前 - 对话记忆，实现真正的对话
4. 待续...

---

## 💡 Spring-AI vs LangChain 基础对比

### Spring-AI 示例（Java）
```java
@Autowired
private ChatClient chatClient;

// 简单调用
String response = chatClient.call("你好");
System.out.println(response);
```

### LangChain 示例（Python）
```python
from langchain_openai import ChatOpenAI

# 创建模型实例
llm = ChatOpenAI()

# 简单调用
response = llm.invoke("你好")
print(response.content)
```

**主要区别**：
- Java需要依赖注入（@Autowired），Python直接实例化
- Java用`.call()`，Python用`.invoke()`
- Python不需要getter，直接访问`.content`属性

---

有问题随时问！🚀


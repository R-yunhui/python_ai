# RAG (检索增强生成) 学习指南

## 🎯 什么是 RAG？

**RAG (Retrieval-Augmented Generation)** 是一种结合了检索和生成的AI技术：

1. **检索（Retrieval）**：从知识库中检索相关文档
2. **增强（Augmented）**：将检索到的文档作为上下文
3. **生成（Generation）**：LLM 基于上下文生成答案

### 为什么需要 RAG？

| 问题 | RAG 解决方案 |
|------|-------------|
| LLM 知识有时效性 | 实时检索最新知识 |
| LLM 无法访问私有数据 | 从企业知识库检索 |
| LLM 可能产生幻觉 | 基于真实文档生成答案 |
| 上下文长度有限 | 只检索相关部分 |

---

## 📚 学习路径

### 第1阶段：基础 RAG
**文件：`01_basic_rag.py`**

学习内容：
- ✅ 文档加载（TextLoader, DirectoryLoader）
- ✅ 文本切分（RecursiveCharacterTextSplitter）
- ✅ 向量化（OpenAIEmbeddings）
- ✅ 向量存储（FAISS 内存存储）
- ✅ 相似度检索
- ✅ 答案生成

**运行示例：**
```bash
cd langchain_demo/04_rag
python 01_basic_rag.py
```

**核心代码：**
```python
# 1. 加载文档
loader = DirectoryLoader("documents/", glob="*.txt")
documents = loader.load()

# 2. 切分文档
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)

# 3. 创建向量存储
embeddings = OpenAIEmbeddings()
vector_store = FAISS.from_documents(chunks, embeddings)

# 4. 检索相关文档
docs = vector_store.similarity_search(query, k=4)

# 5. 生成答案
context = "\n\n".join([doc.page_content for doc in docs])
answer = llm.invoke(f"基于以下上下文回答问题：\n{context}\n\n问题：{query}")
```

---

### 第2阶段：Milvus 集成
**文件：`02_milvus_integration.py`**

学习内容：
- ✅ Milvus 向量数据库连接
- ✅ 创建持久化向量集合
- ✅ 高级检索功能（MMR、带分数检索）
- ✅ 增量添加文档
- ✅ 文档删除和管理

**Milvus 优势：**
- 💾 持久化存储
- 🚀 支持亿级向量
- 🔧 丰富的索引类型
- 📊 分布式部署
- 🔍 混合检索（向量+标量过滤）

**运行示例：**
```bash
# 确保 Milvus 已启动
python 02_milvus_integration.py
```

**核心代码：**
```python
from langchain_milvus import Milvus

# 创建 Milvus 向量存储
vector_store = Milvus.from_documents(
    documents=chunks,
    embedding=embeddings,
    collection_name="knowledge_base",
    connection_args={"host": "localhost", "port": "19530"}
)

# 检索
docs = vector_store.similarity_search(query, k=4)

# MMR 检索（平衡相关性和多样性）
docs_mmr = vector_store.max_marginal_relevance_search(query, k=4)
```

---

## ⚙️ 配置说明

### `config.py` 配置文件

所有配置项都在 `config.py` 中集中管理：

```python
# LLM 配置
class LLMConfig:
    API_BASE = "http://your-api-base/v1/"
    MODEL = "qwen2.5-vl-72b-instruct"
    TEMPERATURE = 0.3

# Embedding 配置
class EmbeddingConfig:
    MODEL = "text-embedding-3-small"
    DIMENSION = 1536

# Milvus 配置
class MilvusConfig:
    HOST = "localhost"
    PORT = "19530"
    COLLECTION_NAME = "langchain_demo_knowledge_base"
    INDEX_TYPE = "IVF_FLAT"
    METRIC_TYPE = "L2"
```

**修改配置：**
1. 直接编辑 `config.py`
2. 或使用环境变量（优先级更高）：
```bash
export MILVUS_HOST=192.168.1.100
export MILVUS_PORT=19530
```

---

## 📂 目录结构

```
04_rag/
├── config.py                    # 配置文件
├── README.md                    # 本文件
├── 01_basic_rag.py             # 基础 RAG 示例
├── 02_milvus_integration.py    # Milvus 集成示例
└── documents/                   # 示例文档目录
    ├── python_basics.txt        # Python 基础知识
    ├── langchain_intro.txt      # LangChain 介绍
    └── milvus_guide.txt         # Milvus 指南
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd langchain_demo
pip install -r requirements.txt
```

主要依赖：
- `langchain` - 核心框架
- `langchain-openai` - OpenAI 集成
- `langchain-milvus` - Milvus 集成
- `pymilvus` - Milvus Python SDK
- `faiss-cpu` - FAISS 向量存储
- `pypdf` - PDF 文档加载
- `python-docx` - Word 文档加载

### 2. 配置环境变量

创建 `.env` 文件：
```bash
OPENAI_API_BASE=http://your-api-base/v1/
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=qwen2.5-vl-72b-instruct
EMBEDDING_MODEL=text-embedding-3-small

# Milvus 配置（如果需要）
MILVUS_HOST=localhost
MILVUS_PORT=19530
```

### 3. 准备文档

将你的知识库文档放到 `documents/` 目录：
- 支持格式：`.txt`, `.md`, `.pdf`, `.docx`
- 文档会自动加载和处理

### 4. 运行示例

```bash
# 基础 RAG（使用 FAISS）
python 01_basic_rag.py

# Milvus RAG（需要 Milvus 运行）
python 02_milvus_integration.py
```

---

## 🔧 核心组件详解

### 1. 文档加载器（Document Loaders）

**作用：** 将各种格式的文档转换为 LangChain 的 Document 对象。

```python
# 文本文件
from langchain_community.document_loaders import TextLoader
loader = TextLoader("document.txt", encoding='utf-8')

# PDF 文件
from langchain_community.document_loaders import PyPDFLoader
loader = PyPDFLoader("document.pdf")

# Word 文档
from langchain_community.document_loaders import Docx2txtLoader
loader = Docx2txtLoader("document.docx")

# 批量加载目录
from langchain_community.document_loaders import DirectoryLoader
loader = DirectoryLoader("documents/", glob="*.txt")

documents = loader.load()
```

### 2. 文本切分器（Text Splitters）

**作用：** 将长文档切分成适合 LLM 处理的小块。

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,        # 每块的字符数
    chunk_overlap=50,      # 块之间的重叠
    separators=[           # 分隔符优先级
        "\n\n",            # 段落
        "\n",              # 行
        "。",              # 句子
        " ",               # 单词
        ""                 # 字符
    ]
)

chunks = splitter.split_documents(documents)
```

**为什么需要切分？**
- ✅ LLM 上下文长度有限
- ✅ 小块更精确，检索更准确
- ✅ 提高检索效率
- ✅ 更好的语义分割

### 3. Embedding 模型

**作用：** 将文本转换为向量表示。

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    openai_api_base="http://your-api/v1/",
    openai_api_key="your-key"
)

# 向量化单个文本
vector = embeddings.embed_query("这是一段文本")

# 批量向量化
vectors = embeddings.embed_documents(["文本1", "文本2"])
```

**常用 Embedding 模型：**
| 模型 | 维度 | 特点 |
|------|------|------|
| text-embedding-3-small | 1536 | 快速、经济 |
| text-embedding-3-large | 3072 | 更高精度 |
| text-embedding-ada-002 | 1536 | 稳定可靠 |

### 4. 向量存储（Vector Stores）

**作用：** 存储和检索向量。

#### FAISS（内存存储）
```python
from langchain_community.vectorstores import FAISS

vector_store = FAISS.from_documents(chunks, embeddings)

# 保存到本地
vector_store.save_local("faiss_index")

# 从本地加载
vector_store = FAISS.load_local("faiss_index", embeddings)
```

#### Milvus（持久化存储）
```python
from langchain_milvus import Milvus

vector_store = Milvus.from_documents(
    documents=chunks,
    embedding=embeddings,
    collection_name="knowledge_base",
    connection_args={"host": "localhost", "port": "19530"}
)
```

### 5. 检索器（Retrievers）

**作用：** 从向量存储中检索相关文档。

```python
# 方法1：相似度搜索
docs = vector_store.similarity_search(query, k=4)

# 方法2：带分数的搜索
docs_with_scores = vector_store.similarity_search_with_score(query, k=4)

# 方法3：MMR 搜索（平衡相关性和多样性）
docs_mmr = vector_store.max_marginal_relevance_search(
    query,
    k=4,
    fetch_k=20,
    lambda_mult=0.5
)

# 方法4：创建检索器对象
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 4}
)
docs = retriever.get_relevant_documents(query)
```

---

## 💡 最佳实践

### 1. 文档预处理

```python
# 清理文档
def clean_document(text: str) -> str:
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text)
    # 移除特殊字符
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
    return text.strip()

# 添加元数据
for doc in documents:
    doc.metadata['category'] = 'technical'
    doc.metadata['author'] = 'AI Team'
```

### 2. 选择合适的 Chunk Size

| 场景 | Chunk Size | Overlap |
|------|-----------|---------|
| 问答系统 | 300-500 | 50-100 |
| 文档总结 | 1000-2000 | 100-200 |
| 代码片段 | 500-1000 | 100 |

### 3. 优化检索结果

```python
# 设置相似度阈值
def filter_by_score(docs_with_scores, threshold=0.5):
    return [doc for doc, score in docs_with_scores if score < threshold]

# 重排序（使用重排序模型）
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

compressor = LLMChainExtractor.from_llm(llm)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=retriever
)
```

### 4. 混合检索

```python
# 结合关键词搜索和向量搜索
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever

# BM25 关键词检索
bm25_retriever = BM25Retriever.from_documents(chunks)
bm25_retriever.k = 4

# 向量检索
vector_retriever = vector_store.as_retriever(search_kwargs={"k": 4})

# 组合检索器
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.5, 0.5]
)
```

### 5. 提示词工程

```python
RAG_PROMPT = """
你是一个专业的问答助手。请基于以下上下文信息回答用户的问题。

重要规则：
1. 只使用上下文中的信息回答
2. 如果上下文中没有相关信息，明确告诉用户
3. 回答要准确、简洁、有条理
4. 可以引用上下文中的具体内容

上下文信息：
{context}

用户问题：{question}

你的回答：
"""
```

---

## 🐛 常见问题

### Q1: 向量化很慢怎么办？

**A:** 批量处理文档
```python
# 设置批量大小
embeddings = OpenAIEmbeddings(chunk_size=100)

# 使用异步
import asyncio
vectors = await embeddings.aembed_documents(texts)
```

### Q2: 检索结果不相关？

**A:** 优化策略
1. 调整 chunk_size 和 overlap
2. 改进文档预处理
3. 尝试不同的 Embedding 模型
4. 使用混合检索
5. 添加重排序

### Q3: Milvus 连接失败？

**A:** 检查清单
```bash
# 1. 检查 Milvus 是否运行
docker ps | grep milvus

# 2. 检查端口
netstat -an | grep 19530

# 3. 测试连接
python -c "from pymilvus import connections; connections.connect('default', host='localhost', port='19530'); print('OK')"
```

### Q4: 内存占用过高？

**A:** 优化方案
1. 使用量化索引（IVF_SQ8, IVF_PQ）
2. 减小 chunk_size
3. 分批处理文档
4. 使用 Milvus 而非 FAISS

### Q5: 如何评估 RAG 效果？

**A:** 评估指标
```python
# 1. 检索准确率
def evaluate_retrieval(test_queries, expected_docs):
    correct = 0
    for query, expected in zip(test_queries, expected_docs):
        retrieved = vector_store.similarity_search(query, k=4)
        if any(doc.metadata['id'] in expected for doc in retrieved):
            correct += 1
    return correct / len(test_queries)

# 2. 答案质量（人工评估或使用 LLM）
def evaluate_answer_quality(answer, reference):
    prompt = f"评估答案质量（1-5分）:\n参考答案:{reference}\n实际答案:{answer}"
    return llm.invoke(prompt)
```

---

## 📖 参考资料

### 官方文档
- [LangChain RAG 教程](https://python.langchain.com/docs/use_cases/question_answering/)
- [Milvus 文档](https://milvus.io/docs)
- [FAISS 文档](https://github.com/facebookresearch/faiss)

### 进阶学习
- 高级 RAG 技术（Query Rewriting, HyDE）
- 多模态 RAG（图像+文本）
- RAG 评估和优化
- 生产部署最佳实践

---

## 🎓 下一步学习

完成 RAG 基础后，可以学习：

1. **高级 RAG 技术**
   - 查询改写（Query Rewriting）
   - 假设文档嵌入（HyDE）
   - 分层检索
   - 自适应检索

2. **Multi-Agent 系统**
   - 多个 Agent 协作
   - Agent 通信机制
   - 角色分工

3. **LangGraph**
   - 复杂工作流编排
   - 状态管理
   - 循环和条件分支

4. **生产化部署**
   - API 服务封装
   - 性能优化
   - 监控和日志
   - 成本控制

---

有问题随时查看代码注释或提问！🚀


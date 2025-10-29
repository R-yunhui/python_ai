"""
基础 RAG (检索增强生成) 实现

RAG 核心流程：
1. 文档加载（Document Loading）- 加载各种格式的文档
2. 文本切分（Text Splitting）- 将长文档切分成小块
3. 向量化（Embedding）- 将文本转换为向量表示
4. 向量存储（Vector Store）- 存储向量到数据库
5. 检索（Retrieval）- 根据查询检索相关文档
6. 生成（Generation）- 基于检索到的文档生成答案

对比 Spring-AI:
Spring-AI 也有类似的 RAG 支持：
@Autowired
private VectorStore vectorStore;

List<Document> docs = vectorStore.similaritySearch("query");
String prompt = createPromptWithContext(docs, question);
String answer = chatClient.call(prompt);

本示例展示最基础的 RAG 实现，不使用向量数据库，仅用内存存储。
"""

import os
from typing import List

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS  # 使用 FAISS 作为内存向量存储
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# 加载环境变量
load_dotenv()

# 配置
from config import LLMConfig, EmbeddingConfig, TextSplitterConfig, DocumentConfig, RAGConfig


# ========== 第1步：文档加载 ==========

def load_documents():
    """
    加载文档
    
    LangChain 提供了多种文档加载器：
    - TextLoader: 加载文本文件
    - PDFLoader: 加载 PDF 文件
    - DirectoryLoader: 批量加载目录中的文件
    - CSVLoader: 加载 CSV 文件
    - ... 还有很多其他加载器
    """
    print("\n📂 第1步：加载文档")
    print("-" * 60)
    
    # 使用 DirectoryLoader 批量加载 documents 目录中的所有 .txt 文件
    loader = DirectoryLoader(
        DocumentConfig.DOCUMENTS_DIR,
        glob="*.txt",  # 只加载 .txt 文件
        loader_cls=TextLoader,  # 使用 TextLoader 处理每个文件
        loader_kwargs={'encoding': 'utf-8'}  # 指定编码
    )
    
    documents = loader.load()
    
    print(f"✅ 加载了 {len(documents)} 个文档")
    for i, doc in enumerate(documents, 1):
        print(f"   {i}. {doc.metadata.get('source', 'Unknown')}")
        print(f"      内容长度: {len(doc.page_content)} 字符")
    
    return documents


# ========== 第2步：文本切分 ==========

def split_documents(documents):
    """
    切分文档
    
    为什么要切分？
    1. LLM 有上下文长度限制
    2. 小块文本更精确，检索时更容易找到相关内容
    3. 提高检索效率
    
    RecursiveCharacterTextSplitter 特点：
    - 按字符数切分
    - 递归尝试不同的分隔符（段落 -> 句子 -> 单词 -> 字符）
    - 保持文本的语义完整性
    """
    print("\n✂️  第2步：切分文档")
    print("-" * 60)
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=TextSplitterConfig.CHUNK_SIZE,  # 每块的大小
        chunk_overlap=TextSplitterConfig.CHUNK_OVERLAP,  # 块之间的重叠
        separators=TextSplitterConfig.SEPARATORS,  # 分隔符优先级
        length_function=len,  # 长度计算函数
    )
    
    chunks = splitter.split_documents(documents)
    
    print(f"✅ 将 {len(documents)} 个文档切分成 {len(chunks)} 个块")
    print(f"   块大小: {TextSplitterConfig.CHUNK_SIZE} 字符")
    print(f"   块重叠: {TextSplitterConfig.CHUNK_OVERLAP} 字符")
    
    # 显示前3个块的示例
    print("\n📝 前3个块的示例:")
    for i, chunk in enumerate(chunks[:3], 1):
        preview = chunk.page_content[:100].replace('\n', ' ')
        print(f"   块 {i}: {preview}...")
    
    return chunks


# ========== 第3步：向量化并存储 ==========

def create_vector_store(chunks):
    """
    创建向量存储
    
    流程：
    1. 使用 Embedding 模型将文本转换为向量
    2. 将向量存储到向量数据库
    
    这里使用 FAISS（Facebook AI Similarity Search）：
    - 内存中的向量存储
    - 快速相似度搜索
    - 适合开发和小规模数据
    
    生产环境建议使用：
    - Milvus: 开源向量数据库
    - Pinecone: 托管向量数据库
    - Weaviate: 开源向量搜索引擎
    """
    print("\n🔢 第3步：向量化并存储")
    print("-" * 60)
    
    # 初始化 Embedding 模型
    # 使用自定义 Embeddings 类适配非标准 API 格式
    from custom_embeddings import CustomMultimodalEmbeddings
    
    embeddings = CustomMultimodalEmbeddings(
        api_base=EmbeddingConfig.API_BASE,
        api_key=EmbeddingConfig.API_KEY,
        model=EmbeddingConfig.MODEL,
        batch_size=10  # 每批处理10个文本
    )
    
    print(f"📊 使用 Embedding 模型: {EmbeddingConfig.MODEL}")
    print(f"   向量维度: {EmbeddingConfig.DIMENSION}")
    print(f"🔄 正在向量化 {len(chunks)} 个文本块...")
    
    # 从文档块创建 FAISS 向量存储
    vector_store = FAISS.from_documents(
        documents=chunks,
        embedding=embeddings
    )
    
    print(f"✅ 向量存储创建完成！")
    print(f"   存储了 {len(chunks)} 个向量")
    
    return vector_store


# ========== 第4步：检索相关文档 ==========

def retrieve_documents(vector_store, query: str, k: int = 4):
    """
    检索相关文档
    
    相似度搜索方法：
    1. similarity_search: 基本的相似度搜索
    2. similarity_search_with_score: 返回相似度分数
    3. max_marginal_relevance_search: MMR 搜索（平衡相关性和多样性）
    """
    print(f"\n🔍 第4步：检索相关文档")
    print("-" * 60)
    print(f"查询: {query}")
    print(f"检索数量: Top {k}")
    
    # 相似度搜索（带分数）
    docs_with_scores = vector_store.similarity_search_with_score(query, k=k)
    
    print(f"\n✅ 找到 {len(docs_with_scores)} 个相关文档：")
    
    retrieved_docs = []
    for i, (doc, score) in enumerate(docs_with_scores, 1):
        print(f"\n   📄 文档 {i} (相似度分数: {score:.4f}):")
        print(f"      来源: {doc.metadata.get('source', 'Unknown')}")
        preview = doc.page_content[:150].replace('\n', ' ')
        print(f"      内容: {preview}...")
        retrieved_docs.append(doc)
    
    return retrieved_docs


# ========== 第5步：生成答案 ==========

def generate_answer(llm, retrieved_docs, question: str):
    """
    基于检索到的文档生成答案
    
    这是 RAG 的核心：
    1. 将检索到的文档作为上下文
    2. 结合用户问题
    3. 让 LLM 生成答案
    """
    print(f"\n🤖 第5步：生成答案")
    print("-" * 60)
    
    # 将检索到的文档组合成上下文
    context = "\n\n".join([doc.page_content for doc in retrieved_docs])
    
    # 创建提示词模板
    template = ChatPromptTemplate.from_messages([
        ("system", RAGConfig.SYSTEM_TEMPLATE),
        ("human", RAGConfig.HUMAN_TEMPLATE)
    ])
    
    # 创建 RAG 链
    # 这是 LangChain 的 LCEL（LangChain Expression Language）语法
    rag_chain = (
        {"context": lambda x: context, "question": lambda x: x}
        | template
        | llm
        | StrOutputParser()
    )
    
    print("🔄 正在生成答案...")
    answer = rag_chain.invoke(question)
    
    print(f"\n✅ 答案生成完成！")
    return answer


# ========== 完整的 RAG 流程 ==========

def basic_rag_demo():
    """完整的基础 RAG 演示"""
    print("=" * 80)
    print("🎯 基础 RAG (检索增强生成) 演示")
    print("=" * 80)
    
    # 初始化 LLM
    llm = ChatOpenAI(
        base_url=LLMConfig.API_BASE,
        model=LLMConfig.MODEL,
        api_key=LLMConfig.API_KEY,
        temperature=LLMConfig.TEMPERATURE,
        max_tokens=LLMConfig.MAX_TOKENS
    )
    
    # 第1步：加载文档
    documents = load_documents()
    
    # 第2步：切分文档
    chunks = split_documents(documents)
    
    # 第3步：向量化并存储
    vector_store = create_vector_store(chunks)
    
    print("\n" + "=" * 80)
    print("📚 知识库构建完成！现在可以开始问答了")
    print("=" * 80)
    
    # 测试问题
    test_questions = [
        "Python 中的列表和元组有什么区别？",
        "LangChain 的核心概念有哪些？",
        "Milvus 支持哪些索引类型？"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'=' * 80}")
        print(f"❓ 问题 {i}: {question}")
        print("=" * 80)
        
        # 第4步：检索相关文档
        retrieved_docs = retrieve_documents(vector_store, question, k=RAGConfig.RETRIEVAL_TOP_K)
        
        # 第5步：生成答案
        answer = generate_answer(llm, retrieved_docs, question)
        
        print(f"\n💬 回答:")
        print("-" * 60)
        print(answer)
        print("-" * 60)
    
    return vector_store


# ========== 交互式问答 ==========

def interactive_qa(vector_store):
    """交互式问答"""
    print("\n" + "=" * 80)
    print("💬 交互式问答模式")
    print("=" * 80)
    print("\n提示:")
    print("  - 输入你的问题，系统会从知识库中检索相关内容并生成答案")
    print("  - 输入 'exit' 退出")
    print("\n" + "=" * 80 + "\n")
    
    # 初始化 LLM
    llm = ChatOpenAI(
        base_url=LLMConfig.API_BASE,
        model=LLMConfig.MODEL,
        api_key=LLMConfig.API_KEY,
        temperature=LLMConfig.TEMPERATURE,
        max_tokens=LLMConfig.MAX_TOKENS
    )
    
    while True:
        try:
            question = input("\n❓ 你的问题: ").strip()
            
            if question.lower() in ['exit', '退出', 'quit', 'q']:
                print("\n👋 再见！")
                break
            
            if not question:
                continue
            
            # 检索
            retrieved_docs = retrieve_documents(vector_store, question, k=RAGConfig.RETRIEVAL_TOP_K)
            
            # 生成答案
            answer = generate_answer(llm, retrieved_docs, question)
            
            print(f"\n💬 回答:")
            print("-" * 60)
            print(answer)
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n\n👋 对话已中断")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")


# ========== 主函数 ==========

def main():
    """主函数"""
    print("\n选择运行模式：")
    print("1. 完整 RAG 演示（自动测试3个问题）")
    print("2. 交互式问答")
    
    choice = input("\n请选择 (1/2): ").strip()
    
    if choice == "1":
        vector_store = basic_rag_demo()
        
        # 询问是否继续交互式问答
        continue_qa = input("\n是否继续交互式问答？(y/n): ").strip().lower()
        if continue_qa == 'y':
            interactive_qa(vector_store)
    
    elif choice == "2":
        # 直接构建知识库并进入交互模式
        print("\n🔄 正在构建知识库...")
        
        llm = ChatOpenAI(
            base_url=LLMConfig.API_BASE,
            model=LLMConfig.MODEL,
            api_key=LLMConfig.API_KEY,
            temperature=LLMConfig.TEMPERATURE
        )
        
        documents = load_documents()
        chunks = split_documents(documents)
        vector_store = create_vector_store(chunks)
        
        print("\n✅ 知识库构建完成！")
        interactive_qa(vector_store)
    
    else:
        print("无效选择，启动完整演示...")
        basic_rag_demo()


if __name__ == "__main__":
    main()


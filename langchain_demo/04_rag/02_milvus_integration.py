"""
Milvus 向量数据库集成示例

Milvus 是专业的向量数据库，相比 FAISS:
- ✅ 支持持久化存储
- ✅ 支持分布式部署
- ✅ 支持大规模数据（亿级向量）
- ✅ 提供丰富的索引类型
- ✅ 支持混合检索（向量 + 标量过滤）

本示例展示如何使用 Milvus 作为 RAG 的向量存储。

前提条件：
1. Milvus 已部署并运行
2. 在 config.py 中配置了正确的 Milvus 连接信息
"""

import os
from typing import List, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_milvus import Milvus  # Milvus 向量存储
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from pymilvus import connections

# 加载环境变量
load_dotenv()

# 配置
from config import LLMConfig, EmbeddingConfig, TextSplitterConfig, DocumentConfig, MilvusConfig, RAGConfig


# ========== Milvus 连接测试 ==========

def test_milvus_connection():
    """测试 Milvus 连接"""
    print("\n🔌 测试 Milvus 连接")
    print("-" * 60)

    try:
        connection_args = MilvusConfig.get_connection_args()
        print(f"连接信息: {connection_args['host']}:{connection_args['port']}")

        # 尝试连接
        connections.connect(
            alias="default",
            **connection_args
        )

        print("✅ Milvus 连接成功！")

        # 断开连接
        connections.disconnect("default")
        return True

    except Exception as e:
        print(f"❌ Milvus 连接失败: {e}")
        print("\n请检查：")
        print("  1. Milvus 是否正在运行")
        print("  2. config.py 中的连接配置是否正确")
        print(f"  3. 能否访问 {connection_args['host']}:{connection_args['port']}")
        return False


# ========== 创建 Milvus 向量存储 ==========

def create_milvus_vector_store(chunks: List[Document], collection_name: Optional[str] = None):
    """
    创建 Milvus 向量存储
    
    参数:
        chunks: 文档块列表
        collection_name: 集合名称（不指定则使用配置中的默认值）
    """
    print("\n🗄️  创建 Milvus 向量存储")
    print("-" * 60)

    # 初始化 Embedding 模型
    # 使用自定义 Embeddings 类适配非标准 API 格式
    from custom_embeddings import CustomMultimodalEmbeddings

    embeddings = CustomMultimodalEmbeddings(
        api_base=EmbeddingConfig.API_BASE,
        api_key=EmbeddingConfig.API_KEY,
        model=EmbeddingConfig.MODEL,
        batch_size=10
    )

    collection_name = collection_name or MilvusConfig.COLLECTION_NAME
    connection_args = MilvusConfig.get_connection_args()

    print(f"📊 Embedding 模型: {EmbeddingConfig.MODEL}")
    print(f"🗄️  集合名称: {collection_name}")
    print(f"🔌 连接到: {connection_args['host']}:{connection_args['port']}")
    print(f"🔄 正在向量化并存储 {len(chunks)} 个文本块...")

    try:
        # 从文档创建 Milvus 向量存储
        vector_store = Milvus.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=collection_name,
            connection_args=connection_args,
            # 索引参数
            index_params={
                "metric_type": MilvusConfig.METRIC_TYPE,
                "index_type": MilvusConfig.INDEX_TYPE,
                "params": MilvusConfig.INDEX_PARAMS
            },
            # 搜索参数
            search_params=MilvusConfig.SEARCH_PARAMS
        )

        print(f"✅ Milvus 向量存储创建成功！")
        print(f"   存储了 {len(chunks)} 个向量")
        print(f"   索引类型: {MilvusConfig.INDEX_TYPE}")
        print(f"   距离度量: {MilvusConfig.METRIC_TYPE}")

        return vector_store

    except Exception as e:
        print(f"❌ 创建 Milvus 向量存储失败: {e}")
        raise


# ========== 连接到现有的 Milvus 集合 ==========

def load_existing_milvus_store(collection_name: Optional[str] = None):
    """
    连接到现有的 Milvus 集合
    
    如果知识库已经构建，可以直接连接而无需重新向量化
    """
    print("\n🔗 连接到现有的 Milvus 集合")
    print("-" * 60)

    from custom_embeddings import CustomMultimodalEmbeddings

    embeddings = CustomMultimodalEmbeddings(
        api_base=EmbeddingConfig.API_BASE,
        api_key=EmbeddingConfig.API_KEY,
        model=EmbeddingConfig.MODEL,
        batch_size=10
    )

    collection_name = collection_name or MilvusConfig.COLLECTION_NAME
    connection_args = MilvusConfig.get_connection_args()

    print(f"🗄️  集合名称: {collection_name}")
    print(f"🔌 连接到: {connection_args['host']}:{connection_args['port']}")

    try:
        # 连接到现有集合
        vector_store = Milvus(
            embedding_function=embeddings,
            collection_name=collection_name,
            connection_args=connection_args,
            index_params={
                "metric_type": MilvusConfig.METRIC_TYPE,
                "index_type": MilvusConfig.INDEX_TYPE,
                "params": MilvusConfig.INDEX_PARAMS
            },
            search_params=MilvusConfig.SEARCH_PARAMS
        )

        print(f"✅ 成功连接到 Milvus 集合！")

        return vector_store

    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("   集合可能不存在，需要先创建")
        raise


# ========== Milvus 高级检索 ==========

def advanced_search_demo(vector_store):
    """
    演示 Milvus 的高级检索功能
    
    Milvus 支持：
    1. 相似度搜索
    2. 带分数的搜索
    3. MMR 搜索（最大边际相关性）
    4. 标量过滤（基于元数据）
    """
    print("\n🔍 高级检索演示")
    print("=" * 80)

    query = "LangChain 的核心组件有哪些？"

    # 1. 基本相似度搜索
    print(f"\n1️⃣  基本相似度搜索")
    print("-" * 60)
    print(f"查询: {query}")

    docs = vector_store.similarity_search(query, k=3)
    for i, doc in enumerate(docs, 1):
        print(f"\n   文档 {i}:")
        print(f"      来源: {doc.metadata.get('source', 'Unknown')}")
        preview = doc.page_content[:100].replace('\n', ' ')
        print(f"      内容: {preview}...")

    # 2. 带分数的相似度搜索
    print(f"\n2️⃣  带分数的相似度搜索")
    print("-" * 60)

    docs_with_scores = vector_store.similarity_search_with_score(query, k=3)
    for i, (doc, score) in enumerate(docs_with_scores, 1):
        print(f"\n   文档 {i} (距离分数: {score:.4f}):")
        print(f"      来源: {doc.metadata.get('source', 'Unknown')}")
        preview = doc.page_content[:100].replace('\n', ' ')
        print(f"      内容: {preview}...")

    # 3. MMR 搜索（平衡相关性和多样性）
    print(f"\n3️⃣  MMR 搜索（最大边际相关性）")
    print("-" * 60)
    print("   MMR 可以在保证相关性的同时增加结果的多样性")

    try:
        docs_mmr = vector_store.max_marginal_relevance_search(
            query,
            k=3,
            fetch_k=10,  # 先检索10个候选
            lambda_mult=0.5  # 平衡参数（0=最多样，1=最相关）
        )

        for i, doc in enumerate(docs_mmr, 1):
            print(f"\n   文档 {i}:")
            print(f"      来源: {doc.metadata.get('source', 'Unknown')}")
            preview = doc.page_content[:100].replace('\n', ' ')
            print(f"      内容: {preview}...")
    except Exception as e:
        print(f"   ⚠️  MMR 搜索暂不可用: {e}")


# ========== 增量添加文档 ==========

def add_documents_to_existing_store(vector_store, new_documents: List[Document]):
    """
    向现有的 Milvus 集合中增量添加新文档
    
    这在以下场景很有用：
    - 知识库需要更新
    - 新增文档
    - 定期同步数据
    """
    print(f"\n➕ 向集合中添加 {len(new_documents)} 个新文档")
    print("-" * 60)

    try:
        # 添加文档
        ids = vector_store.add_documents(new_documents)

        print(f"✅ 成功添加 {len(ids)} 个文档")
        print(f"   文档 IDs: {ids[:5]}...")  # 显示前5个ID

        return ids

    except Exception as e:
        print(f"❌ 添加文档失败: {e}")
        raise


# ========== 删除文档 ==========

def delete_documents_demo(vector_store):
    """
    演示如何删除文档
    
    注意：这需要知道文档的 ID
    """
    print(f"\n🗑️  删除文档演示（仅演示，不实际执行）")
    print("-" * 60)
    print("可以通过以下方式删除文档：")
    print("  vector_store.delete(ids=['doc_id_1', 'doc_id_2'])")
    print("  或者清空整个集合：")
    print("  vector_store.col.drop()")


# ========== 完整的 Milvus RAG 流程 ==========

def milvus_rag_demo():
    """完整的 Milvus RAG 演示"""
    print("=" * 80)
    print("🎯 Milvus RAG 完整演示")
    print("=" * 80)

    # 测试连接
    if not test_milvus_connection():
        print("\n❌ 无法连接到 Milvus，演示终止")
        return None

    # 加载和切分文档
    print("\n📂 第1步：加载文档")
    print("-" * 60)

    loader = DirectoryLoader(
        DocumentConfig.DOCUMENTS_DIR,
        glob="*.txt",
        loader_cls=TextLoader,
        loader_kwargs={'encoding': 'utf-8'}
    )
    documents = loader.load()
    print(f"✅ 加载了 {len(documents)} 个文档")

    print("\n✂️  第2步：切分文档")
    print("-" * 60)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=TextSplitterConfig.CHUNK_SIZE,
        chunk_overlap=TextSplitterConfig.CHUNK_OVERLAP,
        separators=TextSplitterConfig.SEPARATORS
    )
    chunks = splitter.split_documents(documents)
    print(f"✅ 切分成 {len(chunks)} 个块")

    # 创建或连接 Milvus 向量存储
    print("\n🗄️  第3步：Milvus 向量存储")
    print("-" * 60)

    try:
        # 尝试连接到现有集合
        vector_store = load_existing_milvus_store()
        print("   使用现有集合")
    except:
        # 如果不存在，创建新集合
        print("   创建新集合")
        vector_store = create_milvus_vector_store(chunks)

    # 高级检索演示
    advanced_search_demo(vector_store)

    # 删除演示
    delete_documents_demo(vector_store)

    return vector_store


# ========== 交互式 Milvus 问答 ==========

def interactive_milvus_qa(vector_store):
    """基于 Milvus 的交互式问答"""
    print("\n" + "=" * 80)
    print("💬 Milvus RAG 交互式问答")
    print("=" * 80)
    print("\n提示:")
    print("  - 数据持久化存储在 Milvus 中")
    print("  - 支持大规模向量检索")
    print("  - 输入 'exit' 退出")
    print("\n" + "=" * 80 + "\n")

    llm = ChatOpenAI(
        base_url=LLMConfig.API_BASE,
        model=LLMConfig.MODEL,
        api_key=LLMConfig.API_KEY,
        temperature=LLMConfig.TEMPERATURE,
        max_tokens=LLMConfig.MAX_TOKENS
    )

    template = ChatPromptTemplate.from_messages([
        ("system", RAGConfig.SYSTEM_TEMPLATE),
        ("human", RAGConfig.HUMAN_TEMPLATE)
    ])

    while True:
        try:
            question = input("\n❓ 你的问题: ").strip()

            if question.lower() in ['exit', '退出', 'quit', 'q']:
                print("\n👋 再见！")
                break

            if not question:
                continue

            # 检索相关文档
            print(f"\n🔍 正在从 Milvus 检索相关文档...")
            docs = vector_store.similarity_search(question, k=RAGConfig.RETRIEVAL_TOP_K)

            if not docs:
                print("⚠️  未找到相关文档")
                continue

            print(f"✅ 找到 {len(docs)} 个相关文档")

            # 组合上下文
            context = "\n\n".join([doc.page_content for doc in docs])

            # 创建链
            rag_chain = template | llm | StrOutputParser()

            # 生成答案（流式输出）
            print(f"\n💬 回答:")
            print("-" * 60)

            for chunk in rag_chain.stream({"context": context, "question": question}):
                print(chunk, end="", flush=True)

            print("\n" + "-" * 60)

        except KeyboardInterrupt:
            print("\n\n👋 对话已中断")
            break
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()


# ========== 主函数 ==========

def main():
    """主函数"""
    print("\n选择运行模式：")
    print("1. 完整 Milvus RAG 演示")
    print("2. 连接现有集合并进行问答")
    print("3. 创建新集合")

    choice = input("\n请选择 (1/2/3): ").strip()

    if choice == "1":
        # 完整演示
        vector_store = milvus_rag_demo()

        if vector_store:
            continue_qa = input("\n是否继续交互式问答？(y/n): ").strip().lower()
            if continue_qa == 'y':
                interactive_milvus_qa(vector_store)

    elif choice == "2":
        # 连接现有集合
        if not test_milvus_connection():
            return

        try:
            vector_store = load_existing_milvus_store()
            interactive_milvus_qa(vector_store)
        except Exception as e:
            print(f"\n❌ 失败: {e}")

    elif choice == "3":
        # 创建新集合
        if not test_milvus_connection():
            return

        collection_name = input("集合名称（留空使用默认）: ").strip()
        if not collection_name:
            collection_name = MilvusConfig.COLLECTION_NAME

        # 加载文档
        loader = DirectoryLoader(
            DocumentConfig.DOCUMENTS_DIR,
            glob="*.txt",
            loader_cls=TextLoader,
            loader_kwargs={'encoding': 'utf-8'}
        )
        documents = loader.load()

        # 切分
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=TextSplitterConfig.CHUNK_SIZE,
            chunk_overlap=TextSplitterConfig.CHUNK_OVERLAP
        )
        chunks = splitter.split_documents(documents)

        # 创建
        vector_store = create_milvus_vector_store(chunks, collection_name)

        print(f"\n✅ 集合 '{collection_name}' 创建成功！")

        continue_qa = input("\n是否进行问答测试？(y/n): ").strip().lower()
        if continue_qa == 'y':
            interactive_milvus_qa(vector_store)

    else:
        print("无效选择")


if __name__ == "__main__":
    main()

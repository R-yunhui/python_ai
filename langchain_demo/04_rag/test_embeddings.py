"""
测试自定义 Embeddings 是否正常工作

使用方法：
    python test_embeddings.py
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from custom_embeddings import CustomMultimodalEmbeddings
from config import EmbeddingConfig


def test_basic_embedding():
    """测试基本的 embedding 功能"""
    print("=" * 80)
    print("🧪 测试自定义 Multimodal Embeddings")
    print("=" * 80)
    
    print("\n📋 配置信息:")
    print(f"   API Base: {EmbeddingConfig.API_BASE}")
    print(f"   Model: {EmbeddingConfig.MODEL}")
    print(f"   Expected Dimension: {EmbeddingConfig.DIMENSION}")
    
    # 创建 embeddings 实例
    embeddings = CustomMultimodalEmbeddings(
        api_base=EmbeddingConfig.API_BASE,
        api_key=EmbeddingConfig.API_KEY,
        model=EmbeddingConfig.MODEL,
        batch_size=3
    )
    
    # 测试1：单个文本
    print("\n" + "=" * 80)
    print("📝 测试1：向量化单个文本")
    print("=" * 80)
    
    test_text = "繁忙的城市街道"
    print(f"输入文本: '{test_text}'")
    
    try:
        vector = embeddings.embed_query(test_text)
        print(f"\n✅ 成功！")
        print(f"   向量维度: {len(vector)}")
        print(f"   向量类型: {type(vector)}")
        print(f"   前10个值: {[round(v, 6) for v in vector[:10]]}")
        
        # 验证向量不是全零
        if all(v == 0 for v in vector):
            print("   ⚠️  警告: 向量全为零，可能是使用了后备方案")
        else:
            print("   ✅ 向量不是全零，看起来正常")
            
    except Exception as e:
        print(f"\n❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试2：多个文本
    print("\n" + "=" * 80)
    print("📝 测试2：向量化多个文本（批量处理）")
    print("=" * 80)
    
    test_texts = [
        "繁忙的城市街道",
        "交通街道",
        "大量车辆出行",
        "Python 编程语言",
        "机器学习算法"
    ]
    print(f"输入文本数量: {len(test_texts)}")
    for i, text in enumerate(test_texts, 1):
        print(f"   {i}. {text}")
    
    try:
        vectors = embeddings.embed_documents(test_texts)
        print(f"\n✅ 成功！")
        print(f"   返回向量数量: {len(vectors)}")
        print(f"   每个向量维度: {len(vectors[0])}")
        
        # 检查所有向量
        for i, vector in enumerate(vectors, 1):
            is_zero = all(v == 0 for v in vector)
            status = "⚠️  全零" if is_zero else "✅ 正常"
            print(f"   向量 {i}: {status}, 维度={len(vector)}, 前3值={[round(v, 4) for v in vector[:3]]}")
        
        # 测试向量相似度
        print(f"\n📊 向量相似度测试:")
        print(f"   文本1和2应该比较相似（都关于交通）")
        print(f"   文本1和4应该不太相似（城市街道 vs Python）")
        
        # 简单的余弦相似度
        def cosine_similarity(v1, v2):
            import math
            dot_product = sum(a * b for a, b in zip(v1, v2))
            magnitude1 = math.sqrt(sum(a * a for a in v1))
            magnitude2 = math.sqrt(sum(b * b for b in v2))
            if magnitude1 == 0 or magnitude2 == 0:
                return 0
            return dot_product / (magnitude1 * magnitude2)
        
        sim_1_2 = cosine_similarity(vectors[0], vectors[1])
        sim_1_4 = cosine_similarity(vectors[0], vectors[3])
        
        print(f"   相似度(文本1, 文本2): {sim_1_2:.4f}")
        print(f"   相似度(文本1, 文本4): {sim_1_4:.4f}")
        
        if sim_1_2 > sim_1_4:
            print("   ✅ 相似度符合预期！")
        else:
            print("   ⚠️  相似度可能不太对，请检查")
            
    except Exception as e:
        print(f"\n❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试3：大批量处理
    print("\n" + "=" * 80)
    print("📝 测试3：大批量文本处理")
    print("=" * 80)
    
    large_batch = [f"测试文本 {i}" for i in range(25)]
    print(f"输入文本数量: {len(large_batch)}")
    print(f"批量大小设置: 3")
    print(f"预计 API 调用次数: {(len(large_batch) + 2) // 3}")
    
    try:
        vectors = embeddings.embed_documents(large_batch)
        print(f"\n✅ 成功！")
        print(f"   返回向量数量: {len(vectors)}")
        print(f"   所有向量维度一致: {all(len(v) == len(vectors[0]) for v in vectors)}")
        
    except Exception as e:
        print(f"\n❌ 失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 总结
    print("\n" + "=" * 80)
    print("🎉 所有测试通过！")
    print("=" * 80)
    print("\n✅ 你的自定义 Embeddings 类工作正常！")
    print("✅ 现在可以运行 01_basic_rag.py 或 02_milvus_integration.py")
    print("\n" + "=" * 80)
    
    return True


if __name__ == "__main__":
    success = test_basic_embedding()
    sys.exit(0 if success else 1)


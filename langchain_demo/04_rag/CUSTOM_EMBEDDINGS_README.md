# 自定义 Embeddings 使用指南

## 📌 为什么需要自定义 Embeddings？

你的 Multimodal Embedding API 使用了与标准 OpenAI 不同的请求格式：

### ❌ 标准 OpenAI 格式
```json
{
    "model": "text-embedding-3-small",
    "input": "文本内容"
}
```

### ✅ 你的 API 格式
```json
{
    "model": "multimodal-embedding-v1",
    "input": {
        "contents": [
            {"text": "文本1"},
            {"text": "文本2"}
        ]
    },
    "parameters": {}
}
```

因为格式不同，所以我们需要自定义 `Embeddings` 类来适配。

---

## 🚀 使用方法

### 1. 测试 Embeddings 是否正常工作

```bash
cd langchain_demo/04_rag
python test_embeddings.py
```

这个脚本会测试：
- ✅ 单个文本向量化
- ✅ 批量文本向量化
- ✅ 向量相似度计算
- ✅ 大批量处理

**如果测试通过，你会看到：**
```
🎉 所有测试通过！
✅ 你的自定义 Embeddings 类工作正常！
✅ 现在可以运行 01_basic_rag.py 或 02_milvus_integration.py
```

### 2. 运行基础 RAG 示例

```bash
python 01_basic_rag.py
```

选择模式：
- `1` - 自动测试 3 个问题
- `2` - 交互式问答

### 3. 运行 Milvus 集成示例

```bash
# 确保 Milvus 已启动
python 02_milvus_integration.py
```

---

## 🔧 自定义 Embeddings 实现细节

### 核心特性

1. **批量处理**
   - 默认每批处理 10 个文本
   - 可通过 `batch_size` 参数调整
   - 自动分批，避免单次请求过大

2. **重试机制**
   - 默认最多重试 3 次
   - 每次重试间隔 1 秒
   - 可通过 `max_retries` 参数调整

3. **后备方案**
   - 如果所有重试都失败，返回零向量
   - 保证程序不会中断
   - 会打印警告信息

4. **响应格式自动识别**
   - 支持多种可能的响应格式
   - 自动选择正确的解析方式
   - 如果无法解析会打印调试信息

### 代码示例

```python
from custom_embeddings import CustomMultimodalEmbeddings

# 创建实例
embeddings = CustomMultimodalEmbeddings(
    api_base="http://192.168.2.54:9015/v1",
    api_key="your-key",  # 可选
    model="multimodal-embedding-v1",
    batch_size=10,      # 每批处理的文本数量
    max_retries=3,      # 最大重试次数
    timeout=60          # 请求超时时间（秒）
)

# 向量化单个文本
vector = embeddings.embed_query("这是一段文本")
print(f"向量维度: {len(vector)}")

# 向量化多个文本
texts = ["文本1", "文本2", "文本3"]
vectors = embeddings.embed_documents(texts)
print(f"向量数量: {len(vectors)}")
```

---

## 🐛 故障排查

### 问题1：测试失败 - 连接错误

**错误信息：**
```
❌ 请求失败: Connection refused
```

**解决方案：**
1. 检查 API 服务是否运行
2. 检查 `config.py` 中的 `API_BASE` 是否正确
3. 确认网络连通性

```bash
# 测试连接
curl http://192.168.2.54:9015/v1/embeddings
```

### 问题2：测试失败 - 认证错误

**错误信息：**
```
API 返回错误 401: Unauthorized
```

**解决方案：**
检查 `config.py` 中的 `API_KEY` 是否正确

### 问题3：向量全为零

**现象：**
```
⚠️  警告: 向量全为零，可能是使用了后备方案
```

**原因：**
API 调用失败，使用了零向量后备方案

**解决方案：**
1. 查看错误日志，找到失败原因
2. 检查 API 格式是否正确
3. 可能需要调整 `custom_embeddings.py` 中的请求或响应解析逻辑

### 问题4：无法解析响应格式

**错误信息：**
```
⚠️  无法解析响应格式，响应键: ['xxx', 'yyy']
```

**解决方案：**
1. 查看打印的响应键
2. 在 `custom_embeddings.py` 的 `_parse_response` 方法中添加对应的解析逻辑

**示例：** 如果响应格式是 `{"result": {"vectors": [...]}}`

```python
def _parse_response(self, data: dict, expected_count: int) -> List[List[float]]:
    # 添加新的格式支持
    if "result" in data and "vectors" in data["result"]:
        embeddings = data["result"]["vectors"]
        if len(embeddings) == expected_count:
            return embeddings
    
    # ... 其他格式
```

---

## 📊 性能优化建议

### 1. 调整批量大小

根据你的 API 限制和网络情况调整：

```python
# 如果 API 支持大批量，可以增加
embeddings = CustomMultimodalEmbeddings(
    ...,
    batch_size=50  # 更大的批量
)

# 如果经常超时，可以减小
embeddings = CustomMultimodalEmbeddings(
    ...,
    batch_size=5  # 更小的批量
)
```

### 2. 调整超时时间

```python
embeddings = CustomMultimodalEmbeddings(
    ...,
    timeout=120  # 增加到 120 秒
)
```

### 3. 减少重试次数（如果 API 稳定）

```python
embeddings = CustomMultimodalEmbeddings(
    ...,
    max_retries=1  # 减少到 1 次
)
```

---

## 🔄 与标准 OpenAI Embeddings 的对比

| 特性 | OpenAI Embeddings | Custom Embeddings |
|------|-------------------|-------------------|
| API 格式 | 标准 OpenAI | 自定义格式 |
| 批量处理 | ✅ 自动 | ✅ 手动实现 |
| 重试机制 | ✅ 内置 | ✅ 自定义实现 |
| 响应解析 | ✅ 标准化 | ✅ 灵活适配 |
| 后备方案 | ❌ 无 | ✅ 零向量 |
| 调试信息 | 🟡 基础 | ✅ 详细 |

---

## 💡 扩展自定义 Embeddings

如果你需要更多功能，可以修改 `custom_embeddings.py`：

### 添加缓存

```python
class CustomMultimodalEmbeddings(Embeddings):
    def __init__(self, ...):
        self.cache = {}  # 简单的缓存
    
    def embed_query(self, text: str) -> List[float]:
        # 检查缓存
        if text in self.cache:
            return self.cache[text]
        
        # 正常处理
        vector = self._embed_single(text)
        
        # 保存到缓存
        self.cache[text] = vector
        return vector
```

### 添加统计信息

```python
class CustomMultimodalEmbeddings(Embeddings):
    def __init__(self, ...):
        self.stats = {
            "total_requests": 0,
            "success_count": 0,
            "failure_count": 0
        }
    
    def get_stats(self):
        return self.stats
```

### 添加日志记录

```python
import logging

class CustomMultimodalEmbeddings(Embeddings):
    def __init__(self, ...):
        self.logger = logging.getLogger(__name__)
    
    def _embed_batch(self, texts):
        self.logger.info(f"开始向量化 {len(texts)} 个文本")
        # ...
```

---

## 📚 相关文件

- `custom_embeddings.py` - 自定义 Embeddings 实现
- `test_embeddings.py` - 测试脚本
- `01_basic_rag.py` - 使用自定义 Embeddings 的基础 RAG 示例
- `02_milvus_integration.py` - 使用自定义 Embeddings 的 Milvus 集成示例
- `config.py` - 配置文件（修改 Embedding 配置）

---

## ✅ 总结

1. **测试先行**：运行 `test_embeddings.py` 确保一切正常
2. **理解实现**：查看 `custom_embeddings.py` 了解实现细节
3. **开始使用**：运行 RAG 示例开始你的知识库问答之旅
4. **按需调整**：根据实际情况优化批量大小、超时时间等参数

如有问题，请查看错误日志并参考故障排查部分。🚀


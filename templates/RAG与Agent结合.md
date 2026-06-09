# RAG 与 Agent 的结合

## 什么是 RAG

RAG（Retrieval-Augmented Generation，检索增强生成）是一种将外部知识注入 LLM 的技术。

### 核心流程
```
用户提问
   │
   ▼
1. 检索（Retrieval）：从知识库中找到相关文档
   │
   ▼
2. 增强（Augmented）：把检索结果作为上下文
   │
   ▼
3. 生成（Generation）：LLM 基于上下文生成回答
```

### 为什么需要 RAG
- LLM 的知识有截止日期
- LLM 不了解你的私有数据
- LLM 可能产生幻觉（编造信息）
- RAG 让回答有据可查

## RAG 的关键技术

### 1. 文档切片（Chunking）

把长文档切成小段，便于检索。

| 方法 | 优点 | 缺点 |
|------|------|------|
| 固定长度 | 实现简单 | 可能切断语义 |
| 按段落 | 保持语义完整 | 段落长度不一 |
| 按标题 | 结构清晰 | 需要解析标题 |
| 语义切分 | 最自然 | 计算成本高 |

### 2. 向量化（Embedding）

把文本转换成数字向量，便于计算相似度。

```
"什么是 RAG？" → [0.12, 0.85, 0.33, ...] （384维向量）
"RAG 的原理"   → [0.15, 0.82, 0.31, ...] （384维向量）
```

常用 Embedding 模型：
- OpenAI text-embedding-3-small
- BAAI/bge-small-zh
- sentence-transformers/all-MiniLM-L6-v2

### 3. 检索策略

| 策略 | 原理 | 适用场景 |
|------|------|---------|
| 向量检索 | 计算余弦相似度 | 语义搜索 |
| 关键词检索（BM25） | TF-IDF + 词频 | 精确匹配 |
| 混合检索 | 向量 + 关键词 | 兼顾语义和精确 |
| 重排（Reranker） | 二次排序 | 提升精度 |

### 4. 引用溯源

在回答中标注信息来源，增强可信度。

```
回答：RAG 是检索增强生成技术 [1]，它通过检索外部知识库 [2]
来增强 LLM 的回答质量。

[1] templates/rag_basics.md
[2] templates/rag_basics.md
```

## Agent + RAG 的结合

### 纯 RAG 的局限
```
用户：DeepSeek 和 OpenAI 的 RAG 实现有什么区别？
纯 RAG：查一次知识库 → 可能找不到对比内容 → 回答不完整
```

### Agent + RAG 的优势
```
用户：DeepSeek 和 OpenAI 的 RAG 实现有什么区别？
Agent RAG：
  第1轮：查本地知识库 → 找到 RAG 基础知识
  第2轮：证据不够，搜互联网 → 找到两家的对比
  第3轮：证据充足，生成带引用的回答
```

### 实现代码
```python
class AgentRAG:
    def __init__(self):
        self.tools = {
            "vector_retrieve": self.vector_retrieve,
            "web_search": self.web_search,
            "rewrite_query": self.rewrite_query,
        }
    
    def run(self, query, max_steps=3):
        for step in range(max_steps):
            # Agent 思考
            action = self.planner.decide(query, history)
            
            # 执行工具
            result = self.tools[action](query)
            
            # 检查证据是否充足
            if self.evaluator.is_sufficient(result):
                return self.synthesizer.generate(query, result)
        
        return "证据不足，无法回答"
```

## RAG 评测指标

| 指标 | 含义 | 目标 |
|------|------|------|
| Faithfulness | 回答是否忠于检索到的证据 | > 0.8 |
| Answer Relevancy | 回答是否跟问题相关 | > 0.8 |
| Context Precision | 检索结果是否精确 | > 0.7 |
| Context Recall | 是否检索到了所有相关信息 | > 0.7 |

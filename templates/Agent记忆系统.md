# Agent 记忆系统

## 为什么需要记忆

没有记忆的 Agent 每次对话都从零开始，无法：
- 记住之前的对话内容
- 学习用户的偏好
- 积累长期知识
- 跨会话保持状态

## 记忆的分类

### 1. 短期记忆（Working Memory）

当前对话的上下文，存储在 LLM 的 Context Window 中。

```
用户：我叫张三
Agent：你好张三！
用户：我之前说了什么？
Agent：你之前说你叫张三（短期记忆）
```

**限制：**
- Context Window 有限（如 128K tokens）
- 对话太长会丢失早期内容
- 每次调用 LLM 都要发送完整上下文，成本高

### 2. 长期记忆（Long-term Memory）

持久化存储的历史信息，通常用向量数据库。

```
存储方式：
  对话内容 → 向量化 → 存入 Chroma/Pinecone

检索方式：
  用户问题 → 向量化 → 在数据库中找最相关的历史对话
```

**实现代码：**
```python
class LongTermMemory:
    def __init__(self):
        self.vector_store = ChromaCollection("memory")
    
    def save(self, conversation_id, messages):
        for msg in messages:
            embedding = encode(msg["content"])
            self.vector_store.add(
                id=f"{conversation_id}_{msg['role']}",
                embedding=embedding,
                metadata={"role": msg["role"], "time": msg["time"]},
                document=msg["content"]
            )
    
    def recall(self, query, top_k=5):
        results = self.vector_store.query(
            query_embedding=encode(query),
            n_results=top_k
        )
        return results
```

### 3. 情景记忆（Episodic Memory）

记录"发生了什么事"，用于类比推理。

```
情景1：2024-01-15，用户问了如何部署 Docker，我给出了 docker-compose 方案
情景2：2024-02-20，用户问了如何部署 K8s，我给出了 Helm Chart 方案

新问题：如何部署微服务？
参考：之前部署过 Docker 和 K8s，这次可以结合两者
```

### 4. 语义记忆（Semantic Memory）

存储抽象的知识和概念。

```
知识：Python 是一种解释型编程语言
知识：Docker 容器化可以简化部署
知识：RAG 系统需要向量数据库支持
```

## 记忆管理策略

### 1. 滑动窗口
```python
def sliding_window(messages, max_tokens=4000):
    """只保留最近 N 条消息"""
    total = 0
    kept = []
    for msg in reversed(messages):
        tokens = count_tokens(msg["content"])
        if total + tokens > max_tokens:
            break
        kept.insert(0, msg)
        total += tokens
    return kept
```

### 2. 摘要压缩
```python
def summarize_memory(messages):
    """用 LLM 把长对话压缩成摘要"""
    summary = llm.chat(f"请将以下对话总结为简短摘要：\n{messages}")
    return summary
```

### 3. 重要性评分
```python
def score_importance(message):
    """评估消息的重要性"""
    score = llm.chat(f"评估这条消息的重要性（0-10）：{message}")
    return score

def selective_memory(messages, threshold=7):
    """只保留重要的消息"""
    return [m for m in messages if score_importance(m) >= threshold]
```

## 记忆在 RAG 中的应用

```
用户提问
   │
   ▼
检索长期记忆（历史对话）
   │
   ▼
检索知识库（文档）
   │
   ▼
合并上下文
   │
   ▼
LLM 生成回答
```

这就是为什么好的 Agent 能"记住"你之前说过的话，并在回答时参考历史信息。

# TrustRAG 演示指南（本地模型版）

## 前置条件

确保已安装 Ollama 并拉取模型：

```bash
ollama pull bge-m3
ollama pull qwen2.5:7b
```

## 启动服务

```bash
cd E:\test\RAG
.venv\Scripts\activate
python run_server.py
```

浏览器打开 http://127.0.0.1:8000

## 演示流程

### 1. 索引知识库

点击「重新索引全部」按钮，将 6 篇 Agent 知识文档用 bge-m3 向量化后写入 ChromaDB。

### 2. 提问演示

在输入框输入问题，点击「检索问答」：

**推荐问题：**
- Agent 有哪些架构模式？
- 什么是 Function Calling？
- Agent 的记忆系统怎么设计？
- RAG 和 Agent 怎么结合？

### 3. 观察输出

返回结果包含：

| 字段 | 说明 |
|------|------|
| answer | qwen2.5:7b 基于检索证据生成的回答 |
| sources | 3 条引用来源，含片段内容、文件路径、bge-m3 相似度分数 |
| metrics.retrieval_count | 向量检索召回数量（5 条） |
| metrics.rerank_count | 重排后保留数量（3 条） |
| metrics.confidence | 置信度：high / medium / low / very_low |
| metrics.max_score | 最高 bge-m3 混合分数 |

### 4. RAG 流程讲解

```
用户提问 → bge-m3 向量化 → ChromaDB 余弦检索（top 5）
         → bge-m3 交叉余弦重排（top 3）
         → qwen2.5:7b 基于 3 条证据生成回答
         → 置信度标注
```

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /health | 健康检查 |
| GET | /api/docs | 列出所有文档 |
| POST | /api/docs | 创建文档 |
| POST | /api/docs/{id}/index | 索引单篇文档 |
| POST | /api/query | RAG 检索问答 |

## 技术栈

| 组件 | 技术 | 运行方式 |
|------|------|---------|
| Web 框架 | FastAPI | 本地 Python 进程 |
| 向量数据库 | ChromaDB | 本地 Python 进程 |
| 嵌入模型 | bge-m3（1024 维） | Ollama 本地服务 |
| 重排序 | bge-m3 交叉余弦重排 | Ollama 本地服务 |
| 生成模型 | qwen2.5:7b | Ollama 本地服务 |
| 元数据存储 | SQLite | 本地文件 |

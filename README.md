# TrustRAG — 纯本地 RAG 智能问答平台

完全基于本地模型运行，**不需要任何外部 API**。嵌入用 bge-m3，生成用 qwen2.5:7b，全部通过 Ollama 在本地执行。

## 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| Web 框架 | **FastAPI** | REST API、管理后台、依赖注入 |
| 向量数据库 | **ChromaDB** | 文档片段向量存储与相似度检索 |
| 嵌入模型 | **bge-m3（Ollama）** | 1024 维向量，交叉余弦重排 |
| 生成模型 | **qwen2.5:7b（Ollama）** | 基于检索证据生成回答 |
| 元数据存储 | **SQLite + SQLAlchemy** | 文档元数据持久化 |

## RAG 完整流程

```
用户提问 → bge-m3 向量化（Ollama）
         → ChromaDB 余弦检索（top 5）
         → bge-m3 交叉余弦重排（top 3）
         → qwen2.5:7b 基于 3 条证据生成回答
         → 置信度标注（high/medium/low/very_low）
```

## 前置条件

安装 [Ollama](https://ollama.com/download/windows) 并拉取模型：

```bash
ollama pull bge-m3
ollama pull qwen2.5:7b
```

## 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 索引知识库文档
python scripts/index_all.py

# 3. 启动服务
python run_server.py

# 4. 打开浏览器
# http://127.0.0.1:8000
```

## Docker 部署

```bash
docker-compose up -d
# 通过 host.docker.internal 访问宿主机的 Ollama 服务
```

## 项目结构

```
RAG/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── db.py                # 数据库连接
│   ├── models.py            # SQLAlchemy 模型
│   ├── api/documents.py     # 核心 API（索引、查询、重排、LLM）
│   └── services/llm.py      # 本地 qwen2.5:7b 客户端
├── rag_core/
│   ├── vector_store.py      # ChromaDB + bge-m3 嵌入 + 检索
│   └── reranker.py          # bge-m3 交叉余弦重排
├── templates/
│   ├── admin.html           # 管理后台 UI
│   └── *.md                 # Agent 知识库文档（6 篇）
├── scripts/
│   └── index_all.py         # 批量索引脚本
├── .env                     # 环境配置
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── run_server.py
```

## 知识库内容

6 篇 Agent 开发核心知识文档：

1. AI Agent 基础概念
2. Agent 架构模式（ReAct / Plan-and-Execute / Multi-Agent）
3. Agent 工具调用（Function Calling）
4. Agent 记忆系统（短期 / 长期记忆）
5. RAG 与 Agent 结合
6. Agent 生产化部署

## 面试展示要点

- **纯本地运行**：零外部 API 依赖，bge-m3 + qwen2.5:7b 全本地
- **完整 RAG 链路**：向量检索 → 混合重排 → LLM 生成 → 置信度评估
- **专业嵌入**：bge-m3 1024 维，中文语义理解远超 TF-IDF
- **证据溯源**：每条回答附带引用来源和相似度分数
- **置信度机制**：根据检索分数自动标注回答可信度

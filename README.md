# TrustRAG — 生产化 RAG 智能问答平台

面向 **AI Agent 开发** 岗位的面试项目，展示完整的 RAG（检索增强生成）流程。

## 技术栈

| 组件 | 技术 | 作用 |
|------|------|------|
| Web 框架 | **FastAPI** | REST API、管理后台、依赖注入 |
| 文档存储 | **SQLite + SQLAlchemy** | 文档元数据持久化 |
| 向量数据库 | **ChromaDB** | 文档片段向量存储与相似度检索 |
| 嵌入模型 | **TF-IDF（自实现）** | 中文 n-gram 分词 + TF-IDF 向量化 |
| 重排序 | **BM25 + 余弦混合** | 关键词匹配与向量相似度融合 |
| LLM | **DeepSeek** | 基于检索证据生成回答 |

## RAG 完整流程

```
用户提问
  │
  ▼
① 向量检索（ChromaDB, top_k=5）
  │  TF-IDF 中文分词 → 余弦相似度召回
  ▼
② 混合重排（BM25 40% + 余弦 60%, top_k=3）
  │  关键词匹配 + 向量分数融合
  ▼
③ LLM 生成（DeepSeek）
  │  基于 3 条证据生成结构化回答
  ▼
④ 置信度标注
   根据最高分判定 high / medium / low / very_low
```

## 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 .env
cp .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY

# 3. 索引知识库文档
python scripts/index_all.py

# 4. 启动服务
python run_server.py

# 5. 打开浏览器
# http://127.0.0.1:8000
```

## Docker 部署

```bash
docker-compose up -d
```

## 项目结构

```
RAG/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── db.py                # 数据库连接
│   ├── models.py            # SQLAlchemy 模型
│   ├── api/documents.py     # 核心 API（索引、查询、重排、LLM）
│   └── services/llm.py      # DeepSeek 客户端
├── rag_core/
│   ├── vector_store.py      # ChromaDB 向量存储 + TF-IDF 嵌入
│   └── reranker.py          # BM25 + 余弦混合重排
├── templates/
│   ├── admin.html           # 管理后台 UI
│   └── *.md                 # Agent 知识库文档（6 篇）
├── scripts/
│   ├── index_all.py         # 批量索引脚本
│   └── test_*.py            # 测试脚本
├── .env                     # 环境配置
├── requirements.txt
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

- **完整 RAG 链路**：向量检索 → 混合重排 → LLM 生成 → 置信度评估
- **自实现嵌入**：TF-IDF 中文分词，不依赖外部 embedding API
- **混合重排**：BM25 关键词匹配 + 向量余弦相似度融合
- **置信度机制**：根据检索分数自动标注回答可信度
- **证据溯源**：每条回答附带引用来源和相似度分数

# RAG 平台演示脚本

## 演示前准备（5 分钟）

```bash
# 1. 进入项目目录
cd e:/test/RAG

# 2. 激活虚拟环境
.venv\Scripts\activate

# 3. 初始化种子数据（如果 rag.db 已存在则跳过这步会重复插入）
python scripts/seed.py

# 4. 启动服务
python run_server.py
```

服务启动后打开两个浏览器窗口：
- **窗口 A**：http://localhost:8000/docs （Swagger API 文档）
- **窗口 B**：http://localhost:8000/admin （管理后台）

---

## 演示流程（15-20 分钟）

### 第一幕：多租户 + 认证（3 分钟）

**讲**：「这是一个生产级 RAG 平台，首先看多租户隔离和 JWT 鉴权。」

#### 1.1 创建租户
Swagger 上操作 `POST /api/auth/tenants`：
```json
{"name": "acme_corp"}
```
→ 返回租户 ID，说明「每个企业一个租户，数据完全隔离」

#### 1.2 创建用户
`POST /api/auth/users`：
```json
{"email": "admin@acme.com", "password": "admin123", "role": "owner"}
```
→ 「RBAC 角色：owner / member，owner 才能看审计日志和触发评测」

#### 1.3 登录获取 Token
`POST /api/auth/login`：
```json
{"email": "admin@acme.com", "password": "admin123"}
```
→ 复制返回的 `access_token`，点击 Swagger 右上角 **Authorize** 按钮粘贴

#### 1.4 验证身份
`GET /api/auth/me` → 返回当前用户信息

---

### 第二幕：文档入库 + 向量索引（4 分钟）

**讲**：「RAG 的核心是把知识库文档向量化，然后检索增强生成。」

#### 2.1 创建文档记录
`POST /api/docs/`：
```json
{"title": "产品手册", "path": "templates/seed_data.md", "metadata": {"category": "product", "version": "v2.0"}}
```
→ 返回文档 ID（假设是 2）

#### 2.2 索引文档（向量化入库）
`POST /api/docs/2/index`
→ 返回 `{"status": "ok", "chunks_indexed": 3}`
→ 「文档被切分成 3 个 chunk，用 TF-IDF 向量化，存入 Chroma 向量数据库」

**可以打开 `chroma_data/` 目录**展示向量数据已持久化。

---

### 第三幕：检索问答（3 分钟）

**讲**：「现在模拟用户提问，系统从知识库检索相关片段并生成回答。」

#### 3.1 检索
`POST /api/docs/query`：
```json
{"query": "RAG 平台的文档入库流程是什么？", "top_k": 3}
```
→ 返回检索到的 sources（带相似度分数）+ 生成的 answer

#### 3.2 演示数据隔离
- 用另一个租户的 token 查询，看不到 acme_corp 的文档
- 「这就是租户隔离——每个企业的知识库完全独立」

---

### 第四幕：管理后台（2 分钟）

切到**窗口 B**（http://localhost:8000/admin）：

1. 点击「登录」（默认账号 owner@example.com / owner123）
2. 输入问题「什么是 RAG？」点击「检索问答」
3. 点击「加载审计日志」——显示所有操作记录

**讲**：「管理员可以看到完整的审计追踪，谁在什么时候做了什么操作。」

---

### 第五幕：RBAC 权限控制（2 分钟）

**讲**：「不是所有用户都能看审计日志——只有 owner 可以。」

1. 创建一个 member 角色用户并登录
2. 用 member 的 token 调用 `GET /api/admin/audit-logs` → 返回 403 Forbidden
3. 用 member 的 token 调用 `POST /api/eval/run` → 也是 403

---

### 第六幕：评测入口 + 限流（2 分钟）

**讲**：「RAG 系统不能只靠主观判断，需要量化指标。」

#### 6.1 触发评测
`POST /api/eval/run`（需要 owner token）→ 返回 RAGAS 评测指标

#### 6.2 限流说明
「Redis 限流中间件：同一 IP 每 60 秒最多 120 次请求，超过返回 429。」

---

## 面试要点（用来回答问题）

| 问题 | 回答要点 |
|------|----------|
| 为什么做租户隔离？ | 企业场景必须数据隔离，一个 tenant 的数据不会泄露到另一个 |
| 为什么用 Chroma？ | 轻量级向量数据库，持久化存储，支持自定义 embedding function |
| 为什么用 TF-IDF？ | 演示场景无需外部 API，生产可替换为 text-embedding-3 或 bge |
| 为什么加 Redis？ | 在线服务必须限流，防止恶意调用耗尽资源 |
| 为什么加 RAGAS？ | RAG 不能只靠主观，需要 faithfulness/answer_relevancy 等量化指标 |
| JWT 里放了什么？ | sub(user_id), tenant_id, role —— 后续鉴权直接从 token 解析，无需查库 |

---

## 备用：纯 curl 演示（不需要浏览器）

```bash
# 创建租户
curl -s -X POST http://localhost:8000/api/auth/tenants \
  -H "Content-Type: application/json" \
  -d '{"name":"demo2"}'

# 注册用户
curl -s -X POST http://localhost:8000/api/auth/users \
  -H "Content-Type: application/json" \
  -d '{"email":"test@demo.com","password":"123456","role":"member"}'

# 登录
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"owner@example.com","password":"owner123"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 创建文档
curl -s -X POST http://localhost:8000/api/docs/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"产品手册","path":"templates/seed_data.md"}'

# 索引文档 (假设 doc_id=2)
curl -s -X POST http://localhost:8000/api/docs/2/index \
  -H "Authorization: Bearer $TOKEN"

# 检索问答
curl -s -X POST http://localhost:8000/api/docs/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"什么是多租户隔离？","top_k":3}' | python -m json.tool

# 审计日志 (owner only)
curl -s http://localhost:8000/api/admin/audit-logs \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

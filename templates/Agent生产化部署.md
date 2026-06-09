# Agent 生产化部署

## 生产环境的核心挑战

### 1. 可靠性
- LLM 调用可能失败（网络、限流、超时）
- 工具执行可能出错
- 需要重试机制和降级策略

### 2. 延迟
- LLM 调用通常需要 1-5 秒
- 多轮 Agent 循环会累积延迟
- 需要流式输出和异步处理

### 3. 成本
- 每次 LLM 调用都计费
- Agent 循环可能调用多次 LLM
- 需要缓存和成本控制

### 4. 安全
- 工具调用可能执行危险操作
- 用户输入可能包含注入攻击
- 需要权限控制和输入验证

## 生产化架构设计

### 1. 多租户隔离

```
用户请求
   │
   ▼
JWT Token 解析 → 提取 tenant_id
   │
   ▼
所有数据查询自动加 WHERE tenant_id = ?
   │
   ├─ PostgreSQL：租户表、用户表、文档表
   └─ ChromaDB：每个租户独立 collection
```

### 2. 限流与熔断

```python
# Redis 限流
class RateLimiter:
    def __init__(self, redis_client, max_requests=60, window=60):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window = window
    
    def is_allowed(self, key):
        current = self.redis.incr(f"rate:{key}")
        if current == 1:
            self.redis.expire(f"rate:{key}", self.window)
        return current <= self.max_requests

# 熔断器
class CircuitBreaker:
    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func, *args, **kwargs):
        if self.state == "open":
            raise CircuitOpenError("Service unavailable")
        try:
            result = func(*args, **kwargs)
            self.failure_count = 0
            return result
        except Exception as e:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            raise
```

### 3. 审计日志

```python
class AuditLogger:
    def log(self, user_id, tenant_id, action, payload):
        db.insert({
            "user_id": user_id,
            "tenant_id": tenant_id,
            "action": action,
            "payload": payload,
            "timestamp": datetime.now(),
            "ip_address": request.remote_addr
        })
```

### 4. 可观测性

```
监控指标：
  - 请求延迟（P50, P95, P99）
  - 错误率
  - LLM 调用次数和成本
  - 工具调用成功率
  - 活跃用户数
```

## 部署方案

### 方案一：单机部署（开发/演示）
```bash
# 直接运行
python run_server.py

# 或用 Docker
docker compose up -d
```

### 方案二：容器化部署（生产）
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 方案三：Kubernetes 部署（大规模）
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: rag-agent
  template:
    spec:
      containers:
      - name: rag-agent
        image: rag-agent:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
```

## 面试常问问题

### Q: Agent 死循环怎么办？
A: 设置 max_steps 限制，加入超时机制，检测重复动作。

### Q: LLM 回答质量不稳定怎么办？
A: 加入反思机制（Reflection），多次生成取最优，接入评测指标。

### Q: 如何降低 Agent 成本？
A: 缓存常见问题的回答，用小模型处理简单任务，减少不必要的 LLM 调用。

### Q: 如何保证 Agent 安全？
A: 工具白名单、输入验证、权限控制、操作审计、沙箱执行。

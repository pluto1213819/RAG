# Agent 架构模式

## 1. ReAct 模式（Reasoning + Acting）

最经典的 Agent 架构，核心思想是"想一步做一步"。

### 工作流程
```
Thought: 分析当前情况，决定下一步
Action: 调用一个工具
Observation: 获取工具返回的结果
... 循环直到任务完成
```

### 代码示例
```python
def react_agent(query, max_steps=5):
    for step in range(max_steps):
        # 1. LLM 思考
        thought = llm.chat(f"当前状态：{state}\n请决定下一步行动")
        
        # 2. 提取行动
        action = parse_action(thought)
        
        # 3. 执行工具
        observation = tools.run(action)
        
        # 4. 更新状态
        state += f"\n{thought}\nObservation: {observation}"
        
        # 5. 判断是否完成
        if "FINAL ANSWER" in thought:
            return extract_answer(thought)
```

### 优点
- 逻辑清晰，易于调试
- 每一步都有明确的思考过程
- 适合需要精确控制的场景

### 缺点
- 每步都调用 LLM，延迟较高
- 容易在循环中迷失方向

## 2. Plan-and-Execute 模式

先制定完整计划，再逐步执行。

### 工作流程
```
Phase 1: 规划
  用户问题 → LLM 生成完整计划 [步骤1, 步骤2, 步骤3]

Phase 2: 执行
  逐步执行每个步骤，每步结果作为下一步的输入
```

### 代码示例
```python
def plan_and_execute(query):
    # 第一阶段：规划
    plan = llm.chat(f"请为以下问题制定执行计划：{query}")
    steps = parse_plan(plan)
    
    # 第二阶段：执行
    results = []
    for step in steps:
        result = execute_step(step, previous_results=results)
        results.append(result)
    
    # 第三阶段：汇总
    final_answer = llm.chat(f"根据以下结果回答问题：{results}")
    return final_answer
```

### 优点
- 全局规划，减少无效步骤
- 适合复杂、多步骤任务
- 可以并行执行独立步骤

### 缺点
- 初始规划可能不准确
- 需要较强的 LLM 规划能力

## 3. Multi-Agent 协作模式

多个 Agent 各司其职，协作完成任务。

### 典型架构
```
用户问题
   │
   ▼
协调者 Agent（Orchestrator）
   │
   ├── 研究员 Agent（搜索信息）
   ├── 分析师 Agent（分析数据）
   ├── 写手 Agent（生成报告）
   └── 审核员 Agent（检查质量）
```

### 代码示例
```python
class MultiAgentSystem:
    def __init__(self):
        self.agents = {
            "researcher": Agent(role="研究员", tools=["web_search", "vector_retrieve"]),
            "analyst": Agent(role="分析师", tools=["code_execute", "data_analysis"]),
            "writer": Agent(role="写手", tools=["file_write"]),
        }
    
    def run(self, query):
        # 协调者分配任务
        plan = self.orchestrator.plan(query)
        
        results = {}
        for task in plan:
            agent = self.agents[task.agent_type]
            result = agent.run(task.description, context=results)
            results[task.id] = result
        
        return results
```

### 优点
- 分工明确，各 Agent 专注擅长领域
- 可扩展性强，新增能力只需加 Agent
- 容错性好，单个 Agent 失败不影响整体

### 缺点
- Agent 间通信开销大
- 协调逻辑复杂
- 成本较高（多个 LLM 调用）

## 4. 反思模式（Reflection）

Agent 执行后自我评估，发现问题则重试。

### 工作流程
```
执行 → 输出结果 → 自我评估
  │
  ├─ 满意 → 返回结果
  └─ 不满意 → 分析失败原因 → 修改策略 → 重新执行
```

### 代码示例
```python
def reflective_agent(query, max_retries=3):
    for attempt in range(max_retries):
        # 执行
        answer = generate_answer(query)
        
        # 反思
        feedback = llm.chat(f"评估以下回答的质量：{answer}")
        
        if feedback["score"] >= 8:
            return answer
        
        # 根据反馈改进
        query = f"{query}\n\n上次回答的问题：{feedback['issues']}\n请改进。"
    
    return answer  # 返回最后一次结果
```

## 架构选择建议

| 场景 | 推荐架构 |
|------|---------|
| 简单问答 | 单轮 RAG |
| 需要多步推理 | ReAct |
| 复杂项目任务 | Plan-and-Execute |
| 多领域协作 | Multi-Agent |
| 质量要求高 | Reflection + 任意架构 |

# Agent 工具调用（Tool Use）

## 什么是工具调用

工具调用是 Agent 的核心能力之一。LLM 本身只能生成文本，但通过工具调用，Agent 可以：
- 搜索互联网获取实时信息
- 查询数据库获取结构化数据
- 执行代码进行计算
- 操作文件系统读写文件
- 调用外部 API 完成复杂任务

## 工具调用的实现原理

### Function Calling（OpenAI 风格）

```python
# 1. 定义工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "搜索互联网获取信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"}
                },
                "required": ["query"]
            }
        }
    }
]

# 2. LLM 决定调用哪个工具
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[{"role": "user", "content": "今天北京天气怎么样？"}],
    tools=tools,
    tool_choice="auto"
)

# 3. 解析 LLM 的工具调用请求
tool_call = response.choices[0].message.tool_calls[0]
tool_name = tool_call.function.name        # "search_web"
tool_args = json.loads(tool_call.function.arguments)  # {"query": "北京天气"}

# 4. 执行工具
result = search_web(tool_args["query"])

# 5. 把结果返回给 LLM
messages.append({"role": "assistant", "tool_calls": [tool_call]})
messages.append({"role": "tool", "content": result})
```

### Prompt 工程方式（通用）

```python
SYSTEM_PROMPT = """
你可以使用以下工具：
- search_web: 搜索互联网
- query_db: 查询数据库
- run_code: 执行 Python 代码

请按以下格式输出：
Thought: 我需要...
Action: 工具名(参数)
"""

# LLM 输出
# Thought: 我需要搜索今天的天气
# Action: search_web("北京今天天气")
```

## 常用工具分类

### 1. 信息获取类
| 工具 | 用途 | 示例 |
|------|------|------|
| web_search | 搜索互联网 | Google、Bing、Wikipedia |
| vector_retrieve | 检索知识库 | Chroma、Pinecone、Milvus |
| db_query | 查询数据库 | SQL 查询、MongoDB |
| file_read | 读取文件 | 读取 PDF、CSV、JSON |

### 2. 信息处理类
| 工具 | 用途 | 示例 |
|------|------|------|
| code_execute | 执行代码 | Python 计算、数据分析 |
| text_transform | 文本处理 | 翻译、摘要、格式转换 |
| data_analyze | 数据分析 | 统计、可视化 |

### 3. 信息输出类
| 工具 | 用途 | 示例 |
|------|------|------|
| file_write | 写入文件 | 生成报告、保存结果 |
| send_email | 发送邮件 | 通知、报告分发 |
| api_call | 调用 API | 推送消息、创建任务 |

### 4. 系统操作类
| 工具 | 用途 | 示例 |
|------|------|------|
| shell_command | 执行命令 | 系统管理、部署 |
| http_request | 发送请求 | 调用第三方服务 |

## 工具注册与管理

```python
class ToolRegistry:
    def __init__(self):
        self.tools = {}
    
    def register(self, name, func, description):
        self.tools[name] = {
            "func": func,
            "description": description
        }
    
    def execute(self, name, **kwargs):
        if name not in self.tools:
            raise ValueError(f"Unknown tool: {name}")
        return self.tools[name]["func"](**kwargs)
    
    def get_descriptions(self):
        return {name: meta["description"] 
                for name, meta in self.tools.items()}

# 使用示例
registry = ToolRegistry()
registry.register("search_web", search_web, "搜索互联网")
registry.register("query_db", query_db, "查询数据库")

result = registry.execute("search_web", query="AI Agent")
```

## 工具调用的安全问题

### 1. 输入验证
```python
def safe_tool_call(tool_name, args):
    # 验证工具名
    if tool_name not in ALLOWED_TOOLS:
        raise SecurityError(f"Tool {tool_name} not allowed")
    
    # 验证参数
    validate_args(tool_name, args)
    
    # 限制执行时间
    with timeout(30):
        return tools.execute(tool_name, **args)
```

### 2. 权限控制
- 不同用户可用不同工具
- 敏感操作需要确认
- 记录所有工具调用日志

### 3. 错误处理
```python
try:
    result = tools.execute(tool_name, **args)
except TimeoutError:
    result = "工具执行超时，请重试"
except PermissionError:
    result = "没有权限执行此操作"
except Exception as e:
    result = f"工具执行出错：{str(e)}"
```

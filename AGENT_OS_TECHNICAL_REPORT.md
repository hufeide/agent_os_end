# Agent OS Ultimate - 技术架构报告

## 1. 系统概述

Agent OS Ultimate 是一个智能 Agent 操作系统，采用模块化架构设计，支持多 Agent 协作、工具调用、记忆管理和任务调度。

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Agent OS Ultimate                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────────┐   │
│  │   Control Plane │    │   Web Deploy    │    │   CLI Deploy        │   │
│  │   (端口 8000)    │    │   (端口 8030)   │    │   (端口 8002)       │   │
│  └────────┬────────┘    └────────┬────────┘    └──────────┬──────────┘   │
│           │                       │                        │               │
│           └───────────────────────┼────────────────────────┘               │
│                                   ▼                                          │
│                    ┌──────────────────────────────┐                          │
│                    │      AgentRuntime            │                          │
│                    │      (核心运行时)             │                          │
│                    └──────────────┬───────────────┘                          │
│                                   │                                          │
│     ┌─────────────────────────────┼─────────────────────────────┐          │
│     ▼                             ▼                             ▼          │
│ ┌─────────────┐          ┌─────────────┐          ┌─────────────────┐     │
│ │ AgentPool   │          │  Scheduler  │          │   SkillHub      │     │
│ │ (Agent池)   │          │ (任务调度)   │          │   (技能中心)     │     │
│ └──────┬──────┘          └──────┬──────┘          └────────┬────────┘     │
│        │                         │                         │              │
│        ▼                         │                         ▼              │
│ ┌─────────────┐                  │                 ┌─────────────────┐   │
│ │ WorkerAgent │◄─────────────────┴─────────────────│ Skills          │   │
│ │ (工作Agent) │                                    │ (Research等)    │   │
│ └──────┬──────┘                                    └─────────────────┘   │
│        │                                                                   │
│        ▼                                                                   │
│ ┌─────────────────────────────────────────────────────────────────────┐    │
│ │                    ReActEngine (推理引擎)                            │    │
│ │  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────────────┐     │    │
│  │ Think   │───►│ Action  │───►│ Observe │───►│ Final Answer │     │    │
│  │ (思考)   │    │ (行动)  │    │ (观察)  │    │ (最终答案)   │     │    │
│  └─────────┘    └─────────┘    └─────────┘    └──────────────┘     │    │
│                                                                     │    │
│  ┌─────────────────────────────────────────────────────────────┐   │    │
│  │ ToolRouter → ToolRegistry → Tools (search/code/file/web)   │   │    │
│  └─────────────────────────────────────────────────────────────┘   │    │
└─────────────────────────────────────────────────────────────────────┘
```

## 2. 核心模块

### 2.1 运行时 (Runtime)

**文件**: `runtime/runtime.py`

```python
class AgentRuntime:
    def __init__(self, tools, memory, skill_hub, llm, pool_size=10):
        self.tools = ToolRegistry()        # 工具注册表
        self.memory = WorkingMemory()       # 工作记忆
        self.skill_hub = SkillHub()         # 技能中心
        self.pool = AgentPool(...)          # Agent池
        self.scheduler = Scheduler(self.pool)  # 调度器
```

### 2.2 推理引擎 (ReAct Engine)

**文件**: `cognition/react_engine.py`

```
执行流程:
1. 获取可用工具列表
2. LLM 分析任务，决定下一步行动
3. 执行工具 action
4. 观察结果 observation
5. 重复步骤 2-4 直到达到 max_steps
6. 调用 LLM 生成最终答案 (新增)
```

### 2.3 工具系统

**文件结构**:
- `tools/base_tool.py` - 工具基类
- `tools/tool_registry.py` - 工具注册表
- `tools/tool_router.py` - 工具路由器
- `tools/search_tool.py` - 搜索工具 (Bing/Google SERP)
- `tools/code_tool.py` - 代码执行工具
- `tools/file_tool.py` - 文件操作工具
- `tools/web_tool.py` - 网页抓取工具

### 2.4 Agent 系统

**文件**: `agents/worker_agent.py`

```python
class WorkerAgent:
    def __init__(self, role, agent_id, tools, memory, skills, llm):
        self.tool_router = ToolRouter(tools)
        self.react = ReActEngine(self.tool_router, llm)
        self.reflection = Reflection(llm)
        self.critic = Critic(llm)
```

## 3. 执行流程

### 3.1 任务提交流程

```
用户请求
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ FastAPI (deploy_web.py / control_plane.py)                 │
│  POST /api/tasks                                            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ AgentRuntime.run_single(task)                                │
│  1. 创建 Task 对象                                          │
│  2. 从 AgentPool 获取可用 Agent                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ WorkerAgent.execute(task)                                   │
│  调用 ReActEngine.run(task)                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ ReActEngine.run(task)                                       │
│                                                              │
│  for step in range(max_steps):                              │
│    1. _think()     → LLM 决定动作 (action)                │
│    2. _act()       → 执行工具                               │
│    3. 观察结果     → 存入 history                          │
│    4. 判断是否结束 → is_final_answer                        │
│                                                              │
│  循环结束后:                                                 │
│    5. _generate_final_answer() → LLM 整合结果生成最终答案  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
返回结果
```

### 3.2 工具调用流程

```
ReAct Engine
    │
    ▼
ToolRouter.route(action_name)
    │
    ├──► 精确匹配: registry.get(name)
    │
    ├──► 模糊匹配: 检查所有工具名
    │    - 小写匹配
    │    - 包含匹配
    │
    └──► 路由规则: keyword → target_tool
          (如: "search web" → "search")
    │
    ▼
ToolRegistry.get(name)
    │
    ▼
Tool.execute(**action_input)
    │
    ├──► SearchTool: Bing/Google SERP 搜索
    ├──► CodeTool:  Python 代码执行
    ├──► FileTool:  文件读写
    └──► WebTool:  网页抓取
```

## 4. 部署方式

### 4.1 Web 可视化追踪 (端口 8030)

```bash
python -m uvicorn agent_os_ultimate.deploy_web:app --host 0.0.0.0 --port 8030
```

功能:
- 任务提交 `/api/tasks`
- 执行追踪 `/api/traces`
- 可视化界面

### 4.2 Control Plane (端口 8000)

```bash
python start_control_plane.py
```

功能:
- 健康检查 `/api/health`
- 任务管理 `/api/tasks`
- 统计信息 `/api/stats`
- Agent 管理 `/api/agents`

### 4.3 CLI 部署 (端口 8002)

```bash
python -m uvicorn agent_os_ultimate.deploy:app --host 0.0.0.0 --port 8002
```

## 5. 关键技术点

### 5.1 ReAct 推理

```python
# 思考 → 行动 → 观察 循环
prompt = f"""Current task: {task}
Available tools: {tools_description}
History: {history_text}

Step {step + 1}/{max_steps}
Return JSON with thought, action, action_input"""
```

### 5.2 工具动态发现

```python
def _get_available_tools_description(self):
    tools = self.tools.registry.list_tools()
    # 动态获取所有已注册工具
    # 避免 LLM 调用不存在的工具
```

### 5.3 记忆系统

- **WorkingMemory**: 当前任务工作记忆
- **VectorMemory**: 向量存储，长期记忆
- **EpisodicMemory**: 情景记忆
- **TaskReplay**: 任务回放学习

### 5.4 追踪系统

```python
class TraceManager:
    def record_step(self, task_id, phase, thought, action, observation):
        # 记录每个推理步骤
```

## 6. API 接口

| 接口 | 方法 | 说明 |
|-----|------|-----|
| `/` | GET | Web UI 主页 |
| `/api/health` | GET | 健康检查 |
| `/api/tasks` | POST | 提交任务 |
| `/api/tasks` | GET | 任务列表 |
| `/api/tasks/{id}` | GET | 任务详情 |
| `/api/traces` | GET | 追踪列表 |
| `/api/trace/{id}` | GET | 追踪详情 |
| `/api/stats` | GET | 统计信息 |
| `/api/tools` | GET | 工具列表 |
| `/api/skills` | GET | 技能列表 |

## 7. 配置

```python
# LLM 配置 (deploy_web.py)
llm = Qwen3CoderClient(
    base_url="http://192.168.1.159:19000",
    model="Qwen3Coder",
    temperature=0.7,
    max_tokens=4096
)

# Runtime 配置
runtime = AgentRuntime(
    pool_size=3,      # Agent 池大小
    llm=llm
)
runtime.register_default_tools()   # 注册搜索/代码/文件/网页工具
runtime.register_default_skills()  # 注册技能
```

## 8. 文件结构

```
agent_os_ultimate/
├── __init__.py
├── deploy_web.py           # Web 部署入口
├── deploy.py               # CLI 部署
├── control_plane/
│   └── control_plane.py    # 控制平面
├── runtime/
│   ├── runtime.py          # 核心运行时
│   ├── agent_pool.py       # Agent 池
│   ├── scheduler.py        # 任务调度器
│   └── distributed_agent_pool.py
├── cognition/
│   ├── react_engine.py     # ReAct 推理引擎
│   ├── reflection.py      # 反思模块
│   ├── critic.py           # 批评模块
│   ├── rl_agent.py         # 强化学习 Agent
│   └── prompt_optimizer.py
├── agents/
│   ├── worker_agent.py     # 工作 Agent
│   ├── dynamic_agent_factory.py
│   └── self_improving_agent.py
├── tools/
│   ├── base_tool.py        # 工具基类
│   ├── tool_registry.py   # 工具注册表
│   ├── tool_router.py      # 工具路由
│   ├── search_tool.py      # 搜索工具
│   ├── code_tool.py        # 代码工具
│   ├── file_tool.py        # 文件工具
│   └── web_tool.py         # 网页工具
├── skills/
│   ├── skill.py
│   ├── skill_hub.py
│   └── implementations.py
├── memory/
│   ├── working_memory.py
│   ├── vector_memory.py
│   ├── episodic_memory.py
│   └── task_replay.py
├── models/
│   ├── task.py
│   ├── agent_state.py
│   ├── message.py
│   └── prompt_template.py
├── core/
│   ├── config.py
│   ├── logger.py
│   ├── trace.py
│   ├── blackboard.py
│   └── event_bus.py
└── inference/
    ├── multi_llm_router.py
    └── gpu_batch_inference.py
```

## 9. 总结

Agent OS Ultimate 是一个完整的 Agent 运行时系统:

1. **入口层**: FastAPI 提供 Web/CLI 接口
2. **运行时**: AgentRuntime 整合所有组件
3. **执行层**: WorkerAgent + ReActEngine 实现推理
4. **工具层**: ToolRegistry + ToolRouter 管理工具
5. **记忆层**: 多级记忆系统支持长期学习
6. **调度层**: Scheduler 支持 DAG 任务调度

核心流程: 用户请求 → Runtime → Agent → ReAct → 工具 → LLM 整合 → 返回结果

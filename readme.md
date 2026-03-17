
---

# agent_os_ultimate/core/event_bus.py

```python
import asyncio
from typing import Callable, Dict, List

class EventBus:
    def __init__(self):
        self.listeners: Dict[str, List[Callable]] = {}

    def on(self, event_type: str, callback: Callable):
        self.listeners.setdefault(event_type, []).append(callback)

    async def emit(self, event_type: str, data):
        for cb in self.listeners.get(event_type, []):
            if asyncio.iscoroutinefunction(cb):
                await cb(data)
            else:
                cb(data)
```

# agent_os_ultimate/core/blackboard.py

```python
class Blackboard:
    def __init__(self):
        self.data = {}

    def read(self, key):
        return self.data.get(key)

    def write(self, key, value):
        self.data[key] = value
```

# agent_os_ultimate/core/trace.py

```python
class Trace:
    def __init__(self):
        self.events = []

    def log(self, event):
        self.events.append(event)

    def export(self):
        return self.events
```

# agent_os_ultimate/core/config.py

```python
class Config:
    MAX_REACT_STEPS = 8
    GPU_BATCH_SIZE = 8
    RL_LEARNING_RATE = 0.01
```

# agent_os_ultimate/core/logger.py

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentOS")
```

# agent_os_ultimate/models/task.py

```python
import uuid
from dataclasses import dataclass, field
from typing import List, Any

@dataclass
class Task:
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    result: Any = None
    prompt: str = ""
```

# agent_os_ultimate/models/message.py

```python
from dataclasses import dataclass

@dataclass
class Message:
    role: str
    content: str
```

# agent_os_ultimate/models/agent_state.py

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class AgentState:
    role: str
    tools: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
```

# agent_os_ultimate/models/prompt_template.py

```python
from dataclasses import dataclass

@dataclass
class PromptTemplate:
    template: str
    description: str
```

# agent_os_ultimate/memory/working_memory.py

```python
class WorkingMemory:
    def __init__(self):
        self.data = {}

    def set(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key)
```

# agent_os_ultimate/memory/vector_memory.py

```python
class VectorMemory:
    def __init__(self):
        self.vectors = []  # 简化示意，真实可用向量数据库

    def add(self, task_prompt):
        self.vectors.append(task_prompt)

    def query(self, text, top_k=1):
        return self.vectors[-top_k:]
```

# agent_os_ultimate/memory/episodic_memory.py

```python
class EpisodicMemory:
    def __init__(self):
        self.events = []

    def add(self, event):
        self.events.append(event)

    def recent(self, k=10):
        return self.events[-k:]
```

# agent_os_ultimate/memory/task_replay.py

```python
class TaskReplay:
    def __init__(self):
        self.history = []

    def add(self, task, result, reward):
        self.history.append({
            "task": task,
            "result": result,
            "reward": reward
        })

    def recent(self, k=10):
        return self.history[-k:]
```

# agent_os_ultimate/tools/base_tool.py

```python
class BaseTool:
    name = ""
    async def execute(self, **kwargs):
        raise NotImplementedError
```

# agent_os_ultimate/tools/tool_registry.py

```python
class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, tool):
        self.tools[tool.name] = tool

    def get(self, name):
        return self.tools.get(name)
```

# agent_os_ultimate/tools/tool_router.py

```python
class ToolRouter:
    def __init__(self, registry):
        self.registry = registry

    def route(self, tool_name):
        return self.registry.get(tool_name)
```

# agent_os_ultimate/tools/search_tool.py

```python
from .base_tool import BaseTool
class SearchTool(BaseTool):
    name = "search"
    async def execute(self, query):
        return f"Results for {query}"
```

# agent_os_ultimate/tools/code_tool.py

```python
from .base_tool import BaseTool
class CodeTool(BaseTool):
    name = "code"
    async def execute(self, code):
        # 简单执行模拟
        return f"Executed: {code}"
```

# agent_os_ultimate/skills/skill.py

```python
class Skill:
    name = ""
    description = ""
    tools = []

    async def execute(self, input):
        raise NotImplementedError
```

# agent_os_ultimate/skills/skill_hub.py

```python
class SkillHub:
    def __init__(self):
        self.skills = {}

    def register(self, skill):
        self.skills[skill.name] = skill

    def get(self, name):
        return self.skills.get(name)

    def list(self):
        return list(self.skills.keys())
```

# agent_os_ultimate/cognition/react_engine.py

```python
class ReActEngine:
    def __init__(self, tool_router, llm, max_steps=8):
        self.tools = tool_router
        self.llm = llm
        self.max_steps = max_steps

    async def run(self, task):
        history = []
        for _ in range(self.max_steps):
            thought = await self.llm.react(task, history)
            if thought["type"] == "answer":
                return thought["content"]
            if thought["type"] == "tool":
                tool = self.tools.route(thought["tool"])
                result = await tool.execute(**thought["args"])
                history.append((thought, result))
        return history[-1]
```

# agent_os_ultimate/cognition/reflection.py

```python
class Reflection:
    def __init__(self, llm):
        self.llm = llm

    async def reflect(self, history):
        summary = await self.llm.reflect(history)
        return summary
```

# agent_os_ultimate/cognition/critic.py

```python
class Critic:
    def __init__(self, llm):
        self.llm = llm

    async def evaluate(self, step, result):
        critique = await self.llm.critic(step, result)
        return critique
```

# agent_os_ultimate/cognition/prompt_optimizer.py

```python
class PromptOptimizer:
    def __init__(self, vector_memory):
        self.vector_memory = vector_memory

    def optimize(self, task):
        similar_prompts = self.vector_memory.query(task.description)
        if similar_prompts:
            return similar_prompts[0]
        return task.prompt
```

# agent_os_ultimate/agents/worker_agent.py

```python
class WorkerAgent:
    def __init__(self, role, tools, memory, skills, llm):
        self.role = role
        self.tools = tools
        self.memory = memory
        self.skills = skills
        self.llm = llm

    async def run(self, task):
        from cognition.react_engine import ReActEngine
        from cognition.reflection import Reflection
        from cognition.critic import Critic

        react = ReActEngine(tool_router=self.tools, llm=self.llm)
        reflection = Reflection(llm=self.llm)
        critic = Critic(llm=self.llm)

        result = await react.run(task)
        summary = await reflection.reflect([result])
        _ = await critic.evaluate(task, result)
        return result
```

# agent_os_ultimate/agents/dynamic_agent_factory.py

```python
from .worker_agent import WorkerAgent
class DynamicAgentFactory:
    def __init__(self, agent_pool):
        self.agent_pool = agent_pool

    def create_agent(self, role):
        capabilities = {
            "researcher": ["search", "web"],
            "coder": ["code", "debug"],
            "analyst": ["analysis"],
            "writer": ["write"]
        }
        agent = WorkerAgent(
            role=role,
            tools=self.agent_pool.tools,
            memory=self.agent_pool.memory,
            skills=capabilities.get(role, []),
            llm=self.agent_pool.llm
        )
        self.agent_pool.register(agent)
        return agent
```

# agent_os_ultimate/agents/self_improving_agent.py

```python
class SelfImprovingAgent:
    def __init__(self, worker_agent, task_replay, prompt_optimizer, rl_agent):
        self.worker = worker_agent
        self.replay = task_replay
        self.optimizer = prompt_optimizer
        self.rl = rl_agent

    async def run(self, task):
        task.prompt = self.optimizer.optimize(task)
        result = await self.worker.run(task)
        reward = self.compute_reward(task, result)
        await self.rl.update_policy(task, reward)
        self.replay.add(task, result, reward)
        return result

    def compute_reward(self, task, result):
        return 1.0
```

# agent_os_ultimate/runtime/agent_pool.py

```python
class AgentPool:
    def __init__(self, tools, memory, llm):
        self.tools = tools
        self.memory = memory
        self.llm = llm
        self.agents = []
        self.counter = 0

    def register(self, agent):
        self.agents.append(agent)

    async def execute_task(self, task):
        agent = self.agents[self.counter % len(self.agents)]
        self.counter += 1
        return await agent.run(task)
```

# agent_os_ultimate/runtime/distributed_agent_pool.py

```python
class DistributedAgentPool:
    def __init__(self, nodes):
        self.nodes = nodes
        self.counter = 0

    async def execute_task(self, task):
        node = self.nodes[self.counter % len(self.nodes)]
        self.counter += 1
        return await node.execute_task(task)
```

# agent_os_ultimate/runtime/scheduler.py

```python
import asyncio
class Scheduler:
    def __init__(self, pool):
        self.pool = pool

    async def run(self, tasks):
        completed = set()
        results = {}
        while len(completed) < len(tasks):
            ready = [t for t in tasks if t.id not in completed and all(dep in completed for dep in t.dependencies)]
            coros = [self.pool.execute_task(t) for t in ready]
            outputs = await asyncio.gather(*coros)
            for t, r in zip(ready, outputs):
                completed.add(t.id)
                results[t.id] = r
        return results
```

# agent_os_ultimate/runtime/runtime.py

```python
class AgentRuntime:
    def __init__(self, tools, memory, llm, nodes=[]):
        self.pool = DistributedAgentPool(nodes) if nodes else AgentPool(tools, memory, llm)
        self.scheduler = Scheduler(self.pool)
        self.agent_factory = DynamicAgentFactory(self.pool)

    async def run(self, tasks):
        return await self.scheduler.run(tasks)
```

# agent_os_ultimate/inference/gpu_batch_inference.py

```python
import asyncio
class GPUBatchInference:
    def __init__(self, llm, batch_size=8):
        self.llm = llm
        self.batch_size = batch_size
        self.queue = []

    async def submit(self, prompt):
        fut = asyncio.get_event_loop().create_future()
        self.queue.append((prompt, fut))
        if len(self.queue) >= self.batch_size:
            await self.flush()
        return await fut

    async def flush(self):
        if not self.queue:
            return
        prompts, futures = zip(*self.queue)
        results = await self.llm.batch_generate(prompts)
        for fut, r in zip(futures, results):
            fut.set_result(r)
        self.queue = []
```

# agent_os_ultimate/inference/multi_llm_router.py

```python
class MultiLLMRouter:
    def __init__(self, llm_map):
        self.llm_map = llm_map  # {'code': code_llm, 'text': text_llm}

    def route(self, task_type):
        return self.llm_map.get(task_type, list(self.llm_map.values())[0])
```

# agent_os_ultimate/control_plane/api.py

```python
from fastapi import FastAPI
from runtime.runtime import AgentRuntime
app = FastAPI()

runtime = None  # 需初始化

@app.on_event("startup")
async def startup_event():
    global runtime
    # 初始化示例
    tools = None
    memory = None
    llm = None
    runtime = AgentRuntime(tools, memory, llm)

@app.get("/agents")
def list_agents():
    return [a.role for a in runtime.pool.nodes[0].agents] if hasattr(runtime.pool, 'nodes') else [a.role for a in runtime.pool.agents]

@app.post("/spawn")
def spawn(role: str):
    agent = runtime.agent_factory.create_agent(role)
    return {"agent": agent.role}

@app.post("/task")
async def submit(task: dict):
    from models.task import Task
    t = Task(**task)
    result = await runtime.run([t])
    return result
```

# agent_os_ultimate/ui/dashboard.html

```html
<html>
<body>
<h2>Agent Graph</h2>
<div id="graph"></div>
<script src="graph.js"></script>
</body>
</html>
```

# agent_os_ultimate/ui/graph.js

```javascript
function drawGraph(tasks){
    tasks.forEach(t=>{
        console.log(t.id, t.dependencies)
    })
}
```


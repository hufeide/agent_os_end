"""
Ultimate Agent OS Web 可视化部署

提供任务流程追踪和详细日志查看
"""

import sys
import os
import json
import asyncio
import time
import traceback as tb
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict

sys.path.insert(0, '/home/aixz/data/hxf/bigmodel/ai_code/agentos/agent_os_v1')

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse

from agent_os_ultimate.debug.llm_client import Qwen3CoderClient
from agent_os_ultimate.runtime import AgentRuntime
from agent_os_ultimate.runtime.agent_pool import AgentPool
from agent_os_ultimate.models import Task
from agent_os_ultimate.cognition import Thought


@dataclass
class AgentInfo:
    """Agent 信息"""
    agent_id: str
    role: str
    name: str
    created_at: str
    capabilities: List[str] = field(default_factory=list)


@dataclass
class LLMCall:
    """LLM 调用记录"""
    call_id: str
    timestamp: str
    prompt: str
    response: str
    duration_ms: float
    model: str
    tokens_used: int = 0


@dataclass
class ToolCall:
    """工具调用记录"""
    call_id: str
    timestamp: str
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: str
    duration_ms: float
    error: str = ""


@dataclass
class StepRecord:
    """步骤记录"""
    step: int
    timestamp: str
    phase: str  # think, action, observe, llm, tool, result
    agent: Optional[AgentInfo] = None
    thought: str = ""
    action: str = ""
    action_input: Dict[str, Any] = field(default_factory=dict)
    observation: str = ""
    result: str = ""
    error: str = ""
    duration_ms: float = 0
    llm_call: Optional[LLMCall] = None
    tool_call: Optional[ToolCall] = None


@dataclass
class TaskTrace:
    """任务追踪"""
    task_id: str
    description: str
    start_time: str
    end_time: str = ""
    status: str = "pending"
    agents: List[AgentInfo] = field(default_factory=list)
    steps: List[StepRecord] = field(default_factory=list)
    final_result: str = ""
    error: str = ""
    total_duration_ms: float = 0


class TraceManager:
    """追踪管理器"""
    
    def __init__(self):
        self._traces: Dict[str, TaskTrace] = {}
        self._current_step: Dict[str, int] = {}
        self._call_counter = 0
    
    def start_task(self, task_id: str, description: str) -> None:
        """开始任务追踪"""
        self._traces[task_id] = TaskTrace(
            task_id=task_id,
            description=description,
            start_time=datetime.now().isoformat()
        )
        self._current_step[task_id] = 0
    
    def add_agent(self, task_id: str, agent_id: str, role: str, name: str, capabilities: List[str] = None) -> None:
        """添加 Agent 信息"""
        if task_id not in self._traces:
            return
        
        agent = AgentInfo(
            agent_id=agent_id,
            role=role,
            name=name,
            created_at=datetime.now().isoformat(),
            capabilities=capabilities or []
        )
        self._traces[task_id].agents.append(agent)
    
    def _get_call_id(self) -> str:
        """生成调用 ID"""
        self._call_counter += 1
        return f"call_{self._call_counter}"
    
    def add_step(self, task_id: str, phase: str, **kwargs) -> None:
        """添加步骤"""
        if task_id not in self._traces:
            return
        
        step_num = self._current_step.get(task_id, 0)
        
        llm_call = kwargs.get("llm_call")
        if llm_call:
            llm_call.call_id = self._get_call_id()
        
        tool_call = kwargs.get("tool_call")
        if tool_call:
            tool_call.call_id = self._get_call_id()
        
        agent_info = kwargs.get("agent")
        if agent_info:
            agent = AgentInfo(
                agent_id=agent_info.get("agent_id", ""),
                role=agent_info.get("role", ""),
                name=agent_info.get("name", ""),
                created_at=datetime.now().isoformat(),
                capabilities=agent_info.get("capabilities", [])
            )
        else:
            agent = None
        
        step = StepRecord(
            step=step_num,
            timestamp=datetime.now().isoformat(),
            phase=phase,
            agent=agent,
            thought=kwargs.get("thought", ""),
            action=kwargs.get("action", ""),
            action_input=kwargs.get("action_input", {}),
            observation=kwargs.get("observation", ""),
            result=kwargs.get("result", ""),
            error=kwargs.get("error", ""),
            duration_ms=kwargs.get("duration_ms", 0),
            llm_call=llm_call,
            tool_call=tool_call
        )
        self._traces[task_id].steps.append(step)
        self._current_step[task_id] = step_num + 1
    
    def add_llm_call(self, task_id: str, prompt: str, response: str, duration_ms: float, model: str) -> None:
        """添加 LLM 调用记录"""
        if task_id not in self._traces:
            return
        
        llm_call = LLMCall(
            call_id=self._get_call_id(),
            timestamp=datetime.now().isoformat(),
            prompt=prompt,
            response=response,
            duration_ms=duration_ms,
            model=model
        )
        
        step_num = self._current_step.get(task_id, 0)
        step = StepRecord(
            step=step_num,
            timestamp=datetime.now().isoformat(),
            phase="llm",
            llm_call=llm_call,
            duration_ms=duration_ms
        )
        self._traces[task_id].steps.append(step)
        self._current_step[task_id] = step_num + 1
    
    def add_tool_call(self, task_id: str, tool_name: str, tool_input: Dict, tool_output: str, duration_ms: float, error: str = "") -> None:
        """添加工具调用记录"""
        if task_id not in self._traces:
            return
        
        tool_call = ToolCall(
            call_id=self._get_call_id(),
            timestamp=datetime.now().isoformat(),
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            duration_ms=duration_ms,
            error=error
        )
        
        step_num = self._current_step.get(task_id, 0)
        step = StepRecord(
            step=step_num,
            timestamp=datetime.now().isoformat(),
            phase="tool",
            action=tool_name,
            action_input=tool_input,
            observation=tool_output,
            error=error,
            duration_ms=duration_ms,
            tool_call=tool_call
        )
        self._traces[task_id].steps.append(step)
        self._current_step[task_id] = step_num + 1
    
    def complete_task(self, task_id: str, result: str, error: str = "") -> None:
        """完成任务追踪"""
        if task_id not in self._traces:
            return
        
        trace = self._traces[task_id]
        trace.end_time = datetime.now().isoformat()
        trace.status = "completed" if not error else "failed"
        trace.final_result = result
        trace.error = error
        
        if trace.start_time and trace.end_time:
            start = datetime.fromisoformat(trace.start_time)
            end = datetime.fromisoformat(trace.end_time)
            trace.total_duration_ms = (end - start).total_seconds() * 1000
    
    def get_trace(self, task_id: str) -> Optional[TaskTrace]:
        """获取追踪"""
        return self._traces.get(task_id)
    
    def get_all_traces(self) -> List[TaskTrace]:
        """获取所有追踪"""
        return list(self._traces.values())
    
    def clear(self) -> None:
        """清空追踪"""
        self._traces.clear()
        self._current_step.clear()
        self._call_counter = 0


def serialize_trace(trace: TaskTrace) -> Dict:
    """序列化追踪数据"""
    result = {
        "task_id": trace.task_id,
        "description": trace.description,
        "start_time": trace.start_time,
        "end_time": trace.end_time,
        "status": trace.status,
        "total_duration_ms": trace.total_duration_ms,
        "has_error": bool(trace.error),
        "agents": [asdict(a) for a in trace.agents],
        "steps_count": len(trace.steps)
    }
    return result


def serialize_trace_detail(trace: TaskTrace) -> Dict:
    """序列化追踪详情"""
    steps = []
    for s in trace.steps:
        step_dict = {
            "step": s.step,
            "timestamp": s.timestamp,
            "phase": s.phase,
            "thought": s.thought,
            "action": s.action,
            "action_input": s.action_input,
            "observation": s.observation,
            "result": s.result,
            "error": s.error,
            "duration_ms": s.duration_ms
        }
        
        if s.agent:
            step_dict["agent"] = asdict(s.agent)
        
        if s.llm_call:
            step_dict["llm_call"] = asdict(s.llm_call)
        
        if s.tool_call:
            step_dict["tool_call"] = asdict(s.tool_call)
        
        steps.append(step_dict)
    
    return {
        "task_id": trace.task_id,
        "description": trace.description,
        "start_time": trace.start_time,
        "end_time": trace.end_time,
        "status": trace.status,
        "agents": [asdict(a) for a in trace.agents],
        "steps": steps,
        "final_result": trace.final_result,
        "error": trace.error,
        "total_duration_ms": trace.total_duration_ms
    }


class TrackedRuntime(AgentRuntime):
    """带追踪的运行时"""
    
    def __init__(self, *args, trace_manager: TraceManager = None, trace_callback: Callable = None, **kwargs):
        tm = trace_manager or TraceManager()
        tc = trace_callback
        
        if 'trace_callback' not in kwargs and tc is not None:
            kwargs['trace_callback'] = tc
        
        super().__init__(*args, **kwargs)
        self.trace_manager = tm
        
        self._original_pool_execute = None
        self._patch_agent_pool()
    
    def _patch_agent_pool(self):
        """补丁 AgentPool 以追踪工具调用"""
        if self.pool and hasattr(self.pool, 'execute_task'):
            self._original_pool_execute = self.pool.execute_task
    
    async def run_single(self, task: Any) -> Any:
        """运行单个任务并追踪"""
        from agent_os_ultimate.models import Task
        
        if isinstance(task, Task):
            task_id = task.id
            description = task.description
        else:
            task_id = str(id(task))
            description = str(task)
        
        self.trace_manager.start_task(task_id, description)
        
        if hasattr(self.pool, '_agents'):
            for agent in self.pool._agents:
                agent_name = agent.agent_state.name if hasattr(agent, 'agent_state') else f"Worker-{agent.role}-{agent.agent_id}"
                capabilities = agent.agent_state.capabilities if hasattr(agent, 'agent_state') else []
                self.trace_manager.add_agent(
                    task_id,
                    agent.agent_id,
                    agent.role,
                    agent_name,
                    capabilities
                )
        
        try:
            result = await self._run_with_tracking(task, task_id)
            self.trace_manager.complete_task(task_id, str(result)[:5000])
            return result
        except Exception as e:
            self.trace_manager.complete_task(task_id, "", str(e)[:1000])
            raise
    
    async def _run_with_tracking(self, task: Any, task_id: str) -> Any:
        """带追踪的任务执行"""
        from agent_os_ultimate.models import Task
        
        if isinstance(task, Task):
            task_obj = task
        else:
            task_obj = Task(description=str(task))
        
        return await self.scheduler.run_single(task_obj)


def create_tracked_runtime(pool_size: int = 3, llm=None) -> TrackedRuntime:
    """创建带追踪的运行时"""
    from agent_os_ultimate.tools import ToolRegistry
    from agent_os_ultimate.memory import WorkingMemory
    from agent_os_ultimate.skills import SkillHub
    
    trace_manager = TraceManager()
    
    def trace_callback(task_id: str, phase: str, **kwargs):
        """追踪回调函数"""
        if phase == "think":
            trace_manager.add_step(
                task_id, "think",
                thought=kwargs.get("thought", ""),
                action=kwargs.get("action", ""),
                action_input=kwargs.get("action_input", {})
            )
        elif phase == "tool":
            trace_manager.add_tool_call(
                task_id,
                tool_name=kwargs.get("action", ""),
                tool_input=kwargs.get("action_input", {}),
                tool_output=kwargs.get("observation", ""),
                duration_ms=kwargs.get("duration_ms", 0),
                error=kwargs.get("error", "")
            )
        elif phase == "result":
            trace_manager.add_step(
                task_id, "result",
                observation=kwargs.get("observation", "")
            )
    
    tools = ToolRegistry()
    memory = WorkingMemory()
    skill_hub = SkillHub()
    
    runtime = TrackedRuntime(
        tools=tools,
        memory=memory,
        skill_hub=skill_hub,
        llm=llm,
        pool_size=pool_size,
        trace_manager=trace_manager,
        trace_callback=trace_callback
    )
    
    return runtime


def create_app() -> FastAPI:
    """创建应用"""
    print("=" * 60)
    print("Ultimate Agent OS 可视化追踪")
    print("=" * 60)
    
    print("\n[1/4] 初始化 LLM 客户端...")
    llm = Qwen3CoderClient(
        base_url="http://192.168.1.159:19000",
        model="Qwen3Coder",
        temperature=0.7,
        max_tokens=4096
    )
    
    test_response = llm.generate("hi")
    if "Error" in test_response:
        print(f"  ⚠ LLM 连接警告")
    else:
        print(f"  ✓ LLM 连接成功")
    
    print("\n[2/4] 创建追踪运行时...")
    runtime = create_tracked_runtime(pool_size=3, llm=llm)
    trace_manager = runtime.trace_manager
    print(f"  ✓ 追踪管理器创建成功")
    
    app = FastAPI(title="Agent OS 可视化追踪", version="1.0.0")
    
    @app.get("/", response_class=HTMLResponse)
    async def index():
        return get_index_html()
    
    @app.get("/api/traces")
    async def get_traces():
        traces = trace_manager.get_all_traces()
        return [serialize_trace(t) for t in traces]
    
    @app.get("/api/trace/{task_id}")
    async def get_trace(task_id: str):
        trace = trace_manager.get_trace(task_id)
        if not trace:
            raise HTTPException(status_code=404, detail="Trace not found")
        return serialize_trace_detail(trace)
    
    @app.post("/api/tasks")
    async def create_task(request: dict):
        task_description = request.get("task", "")
        
        from agent_os_ultimate.models import Task
        from agent_os_ultimate.runtime import AgentRuntime
        
        print(f"\n[WEB] 收到任务: {task_description}")
        
        def make_trace_callback(tid):
            def trace_callback(task_id, phase: str, **kwargs):
                if phase == "think":
                    trace_manager.add_step(tid, "think",
                        thought=kwargs.get("thought", ""),
                        action=kwargs.get("action", ""),
                        action_input=kwargs.get("action_input", {})
                    )
                elif phase == "tool":
                    trace_manager.add_tool_call(tid,
                        tool_name=kwargs.get("action", ""),
                        tool_input=kwargs.get("action_input", {}),
                        tool_output=kwargs.get("observation", ""),
                        duration_ms=kwargs.get("duration_ms", 0),
                        error=kwargs.get("error", "")
                    )
                elif phase == "result":
                    trace_manager.add_step(tid, "result",
                        observation=kwargs.get("observation", "")
                    )
            return trace_callback
        
        try:
            llm = Qwen3CoderClient(
                base_url="http://192.168.1.159:19000",
                model="Qwen3Coder",
                temperature=0.7,
                max_tokens=2048
            )
            
            rt = AgentRuntime(pool_size=2, llm=llm)
            rt.register_default_tools()
            
            if hasattr(rt.pool, '_agents'):
                task_id_temp = "temp"
                for agent in rt.pool._agents:
                    agent.trace_callback = make_trace_callback(task_id_temp)
                    agent.react.trace_callback = make_trace_callback(task_id_temp)
            
            task = Task(description=task_description)
            task_id = task.id
            
            for agent in rt.pool._agents:
                agent.trace_callback = make_trace_callback(task_id)
                agent.react.trace_callback = make_trace_callback(task_id)
            
            trace_manager.start_task(task_id, task_description)
            
            if hasattr(rt.pool, '_agents'):
                for agent in rt.pool._agents:
                    agent_name = agent.agent_state.name if hasattr(agent, 'agent_state') else f"Worker-{agent.role}"
                    trace_manager.add_agent(task_id, agent.agent_id, agent.role, agent_name, [])
            
            print(f"[WEB] Task ID: {task_id}, 开始执行...")
            result = await rt.run_single(task)
            print(f"[WEB] 完成: {str(result)[:100]}")
            
            trace_manager.complete_task(task_id, str(result)[:5000])
            
            return {
                "task_id": task_id,
                "status": "completed",
                "result": str(result)[:500]
            }
        except Exception as e:
            import traceback
            print(f"[WEB] 失败: {e}")
            traceback.print_exc()
            return {
                "task_id": "error",
                "status": "failed",
                "error": str(e)[:500]
            }
    
    @app.delete("/api/traces")
    async def clear_traces():
        trace_manager.clear()
        return {"status": "cleared"}
    
    print("\n[3/4] 注册路由...")
    print(f"  ✓ API 路由已注册")
    
    print("\n[4/4] 完成初始化")
    print("=" * 60)
    
    return app


def get_index_html() -> str:
    """获取首页HTML"""
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent OS 可视化追踪</title>
    <script src="https://cdn.jsdelivr.net/npm/vue@3/dist/vue.global.prod.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', 'PingFang SC', sans-serif;
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
        }
        .container { max-width: 1600px; margin: 0 auto; padding: 20px; }
        
        .header {
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .header p { color: #888; font-size: 1.1em; }
        
        .main-layout { display: flex; gap: 20px; }
        
        .left-panel { width: 320px; flex-shrink: 0; }
        .right-panel { flex: 1; min-width: 0; }
        
        .panel {
            background: rgba(30, 30, 46, 0.9);
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .panel-title {
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .panel-title::before {
            content: '';
            width: 4px;
            height: 20px;
            background: linear-gradient(180deg, #00d9ff, #00ff88);
            border-radius: 2px;
        }
        
        .input-group { margin-bottom: 15px; }
        .input-group input {
            width: 100%;
            padding: 14px 16px;
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 10px;
            color: #fff;
            font-size: 15px;
            outline: none;
        }
        .input-group input:focus { border-color: #00d9ff; }
        .input-group button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            border: none;
            border-radius: 10px;
            color: #000;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
        }
        
        .trace-list { max-height: 450px; overflow-y: auto; }
        .trace-item {
            padding: 14px;
            background: rgba(255,255,255,0.03);
            border-radius: 10px;
            margin-bottom: 10px;
            cursor: pointer;
            border: 1px solid transparent;
            transition: all 0.2s;
        }
        .trace-item:hover { background: rgba(255,255,255,0.08); border-color: rgba(0,217,255,0.3); }
        .trace-item.active { background: rgba(0,217,255,0.15); border-color: #00d9ff; }
        .trace-item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
        .trace-item-title { font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 180px; }
        .trace-status { padding: 3px 10px; border-radius: 12px; font-size: 0.75em; font-weight: 600; }
        .status-running { background: #ffc107; color: #000; }
        .status-completed { background: #00ff88; color: #000; }
        .status-failed { background: #ff4444; color: #fff; }
        .trace-item-meta { font-size: 0.8em; color: #888; }
        
        .step-flow { display: flex; flex-direction: column; gap: 12px; }
        .step-card {
            background: rgba(0,0,0,0.4);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .step-header {
            padding: 12px 16px;
            background: rgba(255,255,255,0.03);
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .step-num {
            width: 28px; height: 28px;
            background: linear-gradient(135deg, #00d9ff, #00ff88);
            border-radius: 50%;
            display: flex; align-items: center; justify-content: center;
            font-weight: 700; font-size: 0.85em; color: #000;
        }
        .step-phase { font-weight: 600; font-size: 0.9em; }
        .phase-think { color: #89b4fa; }
        .phase-llm { color: #cba6f7; }
        .phase-action, .phase-tool { color: #f9e2af; }
        .phase-observe { color: #a6e3a1; }
        .phase-result { color: #94e2d5; }
        
        .step-content { padding: 16px; }
        .step-field { margin-bottom: 12px; }
        .step-label {
            font-size: 0.7em;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .step-badge {
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 0.7em;
        }
        .badge-agent { background: rgba(137, 180, 250, 0.2); color: #89b4fa; }
        .badge-tool { background: rgba(249, 226, 175, 0.2); color: #f9e2af; }
        
        .step-value {
            background: rgba(0,0,0,0.3);
            padding: 10px 12px;
            border-radius: 6px;
            font-size: 0.85em;
            color: #cdd6f4;
            white-space: pre-wrap;
            word-break: break-all;
            max-height: 120px;
            overflow-y: auto;
        }
        .step-value.llm { border-left: 3px solid #cba6f7; }
        .step-value.tool { border-left: 3px solid #f9e2af; }
        .step-error { background: rgba(255,68,68,0.2); color: #f38ba8; padding: 10px 12px; border-radius: 6px; font-size: 0.85em; }
        
        .final-result {
            background: linear-gradient(135deg, rgba(0,217,255,0.1), rgba(0,255,136,0.1));
            border: 1px solid rgba(0,255,136,0.3);
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
        }
        .final-result-title { font-weight: 600; margin-bottom: 12px; color: #00ff88; }
        .final-result-content {
            background: rgba(0,0,0,0.3);
            padding: 16px;
            border-radius: 8px;
            white-space: pre-wrap;
            font-family: 'Consolas', monospace;
            font-size: 0.9em;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .empty-state { text-align: center; padding: 60px 20px; color: #666; }
        .empty-state-icon { font-size: 4em; margin-bottom: 20px; opacity: 0.3; }
        .loading { display: flex; align-items: center; justify-content: center; padding: 20px; color: #00d9ff; }
        .spinner {
            width: 20px; height: 20px;
            border: 2px solid rgba(0,217,255,0.3);
            border-top-color: #00d9ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        
        .stats-row { display: flex; gap: 15px; margin-bottom: 15px; }
        .stat-item { flex: 1; background: rgba(255,255,255,0.03); padding: 12px; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 1.5em; font-weight: 700; color: #00d9ff; }
        .stat-label { font-size: 0.75em; color: #888; margin-top: 4px; }
        
        .agent-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 15px; }
        .agent-tag {
            padding: 4px 10px;
            background: rgba(137,180,250,0.15);
            border: 1px solid rgba(137,180,250,0.3);
            border-radius: 20px;
            font-size: 0.75em;
            color: #89b4fa;
        }
    </style>
</head>
<body>
    <div id="app" class="container">
        <div class="header">
            <h1>🔄 Agent OS 可视化追踪</h1>
            <p>实时查看 Agent 任务的完整执行流程</p>
        </div>
        
        <div class="main-layout">
            <div class="left-panel">
                <div class="panel">
                    <div class="panel-title">提交任务</div>
                    <div class="input-group">
                        <input v-model="newTask" @keyup.enter="submitTask" placeholder="输入任务描述..." />
                    </div>
                    <div class="input-group">
                        <button @click="submitTask" :disabled="submitting">
                            <span v-if="submitting">处理中...</span>
                            <span v-else>🚀 执行任务</span>
                        </button>
                    </div>
                </div>
                
                <div class="panel" style="margin-top: 20px;">
                    <div class="panel-title">任务列表</div>
                    <div class="stats-row">
                        <div class="stat-item">
                            <div class="stat-value">{{ traces.length }}</div>
                            <div class="stat-label">总任务</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">{{ completedCount }}</div>
                            <div class="stat-label">已完成</div>
                        </div>
                    </div>
                    <div class="trace-list">
                        <div v-if="loading" class="loading"><div class="spinner"></div>加载中...</div>
                        <div v-else-if="traces.length === 0" class="empty-state"><div class="empty-state-icon">📋</div><div>暂无任务</div></div>
                        <div v-else v-for="trace in traces" :key="trace.task_id"
                             class="trace-item" :class="{ active: selectedTask === trace.task_id }"
                             @click="selectTrace(trace.task_id)">
                            <div class="trace-item-header">
                                <div class="trace-item-title">{{ trace.description }}</div>
                                <span class="trace-status" :class="'status-' + trace.status">{{ trace.status }}</span>
                            </div>
                            <div class="trace-item-meta">{{ trace.steps_count }} 步骤 | {{ formatDuration(trace.total_duration_ms) }}</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="right-panel">
                <div class="panel">
                    <div class="panel-title">执行流程</div>
                    
                    <div v-if="selectedLoading" class="loading"><div class="spinner"></div>加载中...</div>
                    <div v-else-if="!selectedTrace" class="empty-state"><div class="empty-state-icon">👈</div><div>点击左侧任务查看执行流程</div></div>
                    
                    <div v-else>
                        <div v-if="selectedTrace.agents.length" class="agent-tags">
                            <div v-for="agent in selectedTrace.agents" :key="agent.agent_id" class="agent-tag">
                                🤖 {{ agent.name }} ({{ agent.role }})
                            </div>
                        </div>
                        
                        <div class="step-flow">
                            <div v-for="step in selectedTrace.steps" :key="step.step" class="step-card">
                                <div class="step-header">
                                    <div class="step-num">{{ step.step + 1 }}</div>
                                    <div class="step-phase" :class="'phase-' + step.phase">{{ getPhaseName(step.phase) }}</div>
                                    <span v-if="step.agent" class="step-badge badge-agent">🤖 {{ step.agent.name }}</span>
                                    <span v-if="step.tool_call" class="step-badge badge-tool">🔧 {{ step.tool_call.tool_name }}</span>
                                </div>
                                <div class="step-content">
                                    <div v-if="step.thought" class="step-field">
                                        <div class="step-label">🧠 思考</div>
                                        <div class="step-value">{{ step.thought }}</div>
                                    </div>
                                    
                                    <div v-if="step.llm_call" class="step-field">
                                        <div class="step-label">📤 请求 (LLM)</div>
                                        <div class="step-value llm">{{ step.llm_call.prompt }}</div>
                                    </div>
                                    <div v-if="step.llm_call" class="step-field">
                                        <div class="step-label">📥 响应 (LLM)</div>
                                        <div class="step-value llm">{{ step.llm_call.response }}</div>
                                    </div>
                                    
                                    <div v-if="step.action" class="step-field">
                                        <div class="step-label">⚡ 动作</div>
                                        <div class="step-value">{{ step.action }}</div>
                                    </div>
                                    <div v-if="step.action_input && Object.keys(step.action_input).length" class="step-field">
                                        <div class="step-label">📝 输入参数</div>
                                        <div class="step-value">{{ JSON.stringify(step.action_input, null, 2) }}</div>
                                    </div>
                                    
                                    <div v-if="step.observation" class="step-field">
                                        <div class="step-label">👁 观察结果</div>
                                        <div class="step-value">{{ step.observation }}</div>
                                    </div>
                                    
                                    <div v-if="step.result" class="step-field">
                                        <div class="step-label">📋 结果</div>
                                        <div class="step-value">{{ step.result }}</div>
                                    </div>
                                    
                                    <div v-if="step.error" class="step-field">
                                        <div class="step-label">❌ 错误</div>
                                        <div class="step-error">{{ step.error }}</div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div v-if="selectedTrace.final_result" class="final-result">
                            <div class="final-result-title">✨ 最终结果</div>
                            <div class="final-result-content">{{ selectedTrace.final_result }}</div>
                        </div>
                        
                        <div v-if="selectedTrace.error" class="final-result" style="border-color: rgba(255,68,68,0.3); background: linear-gradient(135deg, rgba(255,68,68,0.1), rgba(255,0,0,0.05));">
                            <div class="final-result-title" style="color: #ff4444;">❌ 错误</div>
                            <div class="final-result-content" style="color: #f38ba8;">{{ selectedTrace.error }}</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const { createApp, ref, computed, onMounted } = Vue;
        
        createApp({
            setup() {
                const newTask = ref('');
                const submitting = ref(false);
                const traces = ref([]);
                const selectedTask = ref(null);
                const selectedTrace = ref(null);
                const loading = ref(false);
                const selectedLoading = ref(false);
                
                const completedCount = computed(() => traces.value.filter(t => t.status === 'completed').length);
                
                async function loadTraces() {
                    try {
                        const res = await axios.get('/api/traces');
                        traces.value = res.data.reverse();
                    } catch (e) { console.error(e); }
                }
                
                async function selectTrace(taskId) {
                    selectedTask.value = taskId;
                    selectedLoading.value = true;
                    try {
                        const res = await axios.get('/api/trace/' + taskId);
                        selectedTrace.value = res.data;
                    } catch (e) { console.error(e); }
                    finally { selectedLoading.value = false; }
                }
                
                async function submitTask() {
                    if (!newTask.value.trim() || submitting.value) return;
                    submitting.value = true;
                    try {
                        await axios.post('/api/tasks', { task: newTask.value });
                        newTask.value = '';
                        await loadTraces();
                    } catch (e) { console.error(e); }
                    finally { submitting.value = false; }
                }
                
                function getPhaseName(phase) {
                    const names = {
                        'think': '🧠 思考', 'llm': '📡 LLM调用',
                        'action': '⚡ 行动', 'tool': '🔧 工具执行',
                        'observe': '👁 观察', 'result': '📋 结果', 'final': '✅ 完成'
                    };
                    return names[phase] || phase;
                }
                
                function formatDuration(ms) {
                    if (!ms) return '0ms';
                    if (ms < 1000) return Math.round(ms) + 'ms';
                    return (ms / 1000).toFixed(2) + 's';
                }
                
                onMounted(() => {
                    loadTraces();
                    setInterval(loadTraces, 3000);
                });
                
                return { newTask, submitting, traces, selectedTask, selectedTrace, loading, selectedLoading, completedCount, selectTrace, submitTask, getPhaseName, formatDuration };
            }
        }).mount('#app');
    </script>
</body>
</html>"""


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "agent_os_ultimate.deploy_web:app",
        host="0.0.0.0",
        port=8002,
        log_level="info",
        reload=True
    )

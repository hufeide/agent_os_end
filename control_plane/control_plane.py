"""
ControlPlane - Agent控制平面

提供FastAPI服务和Web UI。
"""

from typing import Any, Dict, List, Optional
import asyncio
from dataclasses import dataclass
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


@dataclass
class AgentRequest:
    """Agent请求"""
    task: str
    role: Optional[str] = "general"
    options: Optional[Dict[str, Any]] = None


@dataclass
class AgentResponse:
    """Agent响应"""
    task_id: str
    status: str
    result: Any = None
    error: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class ControlPlane:
    """
    Agent控制平面
    
    提供FastAPI服务和Web UI入口。
    """
    
    def __init__(self, runtime: Any = None):
        self.runtime = runtime
        self._app: Optional[FastAPI] = None
        self._tasks: Dict[str, Dict[str, Any]] = {}
    
    def create_app(self) -> FastAPI:
        """创建FastAPI应用"""
        app = FastAPI(
            title="Agent OS Control Plane",
            description="Ultimate Agent OS Control Plane API",
            version="1.0.0"
        )
        
        self._app = app
        
        self._setup_routes()
        
        return app
    
    def _setup_routes(self) -> None:
        """设置路由"""
        if not self._app:
            return
        
        @self._app.get("/", response_class=HTMLResponse)
        async def index():
            return self._get_index_html()
        
        @self._app.get("/api/health")
        async def health():
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        
        @self._app.post("/api/tasks")
        async def create_task(request: AgentRequest):
            return await self._handle_task(request)
        
        @self._app.get("/api/tasks/{task_id}")
        async def get_task(task_id: str):
            if task_id not in self._tasks:
                raise HTTPException(status_code=404, detail="Task not found")
            return self._tasks[task_id]
        
        @self._app.get("/api/tasks")
        async def list_tasks():
            return list(self._tasks.values())
        
        @self._app.delete("/api/tasks/{task_id}")
        async def delete_task(task_id: str):
            if task_id in self._tasks:
                del self._tasks[task_id]
                return {"status": "deleted"}
            raise HTTPException(status_code=404, detail="Task not found")
        
        @self._app.get("/api/stats")
        async def get_stats():
            if self.runtime:
                return self.runtime.get_statistics()
            return {"status": "no_runtime"}
        
        @self._app.get("/api/agents")
        async def list_agents():
            if self.runtime and hasattr(self.runtime.pool, "get_all_agents"):
                agents = self.runtime.pool.get_all_agents()
                return [
                    {
                        "id": a.agent_id,
                        "role": a.role,
                        "state": a.agent_state.to_dict()
                    }
                    for a in agents
                ]
            return []
        
        @self._app.post("/api/agents/spawn")
        async def spawn_agent(role: str = "general"):
            if self.runtime:
                agent = self.runtime.spawn_agent(role)
                return {
                    "id": agent.agent_id,
                    "role": agent.role,
                    "status": "spawned"
                }
            return {"error": "No runtime"}
        
        @self._app.get("/api/tools")
        async def list_tools():
            if self.runtime and hasattr(self.runtime.tools, "list_tools"):
                return self.runtime.tools.list_tools()
            return []
        
        @self._app.get("/api/skills")
        async def list_skills():
            if self.runtime and hasattr(self.runtime.skill_hub, "list_skills"):
                return self.runtime.skill_hub.list_skills()
            return []
    
    async def _handle_task(self, request: AgentRequest) -> AgentResponse:
        """处理任务请求"""
        task_id = str(uuid.uuid4())
        
        task_data = {
            "task_id": task_id,
            "task": request.task,
            "role": request.role,
            "status": "pending",
            "result": None,
            "error": None,
            "timestamp": datetime.now().isoformat()
        }
        
        self._tasks[task_id] = task_data
        
        if self.runtime:
            try:
                from ..models import Task
                task = Task(description=request.task)
                
                result = await self.runtime.run_single(task)
                
                self._tasks[task_id]["status"] = "completed"
                self._tasks[task_id]["result"] = result
                
                return AgentResponse(
                    task_id=task_id,
                    status="completed",
                    result=result
                )
            except Exception as e:
                self._tasks[task_id]["status"] = "failed"
                self._tasks[task_id]["error"] = str(e)
                
                return AgentResponse(
                    task_id=task_id,
                    status="failed",
                    error=str(e)
                )
        
        return AgentResponse(
            task_id=task_id,
            status="queued"
        )
    
    def _get_index_html(self) -> str:
        """获取首页HTML"""
        return """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent OS Control Plane</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #fff;
            min-height: 100vh;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            text-align: center;
            padding: 40px 0;
        }
        
        h1 {
            font-size: 2.5em;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #888;
            font-size: 1.1em;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .input-group {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        input[type="text"] {
            flex: 1;
            padding: 14px 20px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            background: rgba(255, 255, 255, 0.1);
            color: #fff;
            font-size: 16px;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #00d9ff;
        }
        
        button {
            padding: 14px 30px;
            border-radius: 10px;
            border: none;
            background: linear-gradient(90deg, #00d9ff, #00ff88);
            color: #1a1a2e;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        button:hover {
            transform: scale(1.05);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #00d9ff;
        }
        
        .stat-label {
            color: #888;
            margin-top: 5px;
        }
        
        .tasks-list {
            max-height: 400px;
            overflow-y: auto;
        }
        
        .task-item {
            background: rgba(30, 30, 46, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 12px;
            display: block;
        }
        
        .task-item-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
        }
        
        .task-item-result {
            margin-top: 12px;
            padding-top: 12px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .task-status {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
        }
        
        .status-pending { background: #ffc107; color: #000; }
        .status-completed { background: #00ff88; color: #000; }
        .status-failed { background: #ff4444; color: #fff; }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid rgba(255, 255, 255, 0.2);
            border-top-color: #00d9ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 Agent OS Control Plane</h1>
            <p class="subtitle">Ultimate Agent OS - 智能Agent操作系统</p>
        </header>
        
        <div class="card">
            <h2>执行任务</h2>
            <div class="input-group">
                <input type="text" id="taskInput" placeholder="输入任务描述...">
                <button onclick="submitTask()">执行</button>
            </div>
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p style="margin-top: 10px;">Agent正在思考中...</p>
            </div>
        </div>
        
        <div class="card">
            <h2>系统状态</h2>
            <div class="stats-grid" id="stats">
                <div class="stat-card">
                    <div class="stat-value" id="totalTasks">0</div>
                    <div class="stat-label">总任务数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="activeAgents">0</div>
                    <div class="stat-label">活跃Agent</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="completedTasks">0</div>
                    <div class="stat-label">已完成</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" id="successRate">0%</div>
                    <div class="stat-label">成功率</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>任务列表</h2>
            <div class="tasks-list" id="tasksList">
                <p style="color: #888; text-align: center;">暂无任务</p>
            </div>
        </div>
    </div>
    
    <script>
        async function submitTask() {
            const input = document.getElementById('taskInput');
            const task = input.value.trim();
            if (!task) return;
            
            document.getElementById('loading').style.display = 'block';
            
            try {
                const response = await fetch('/api/tasks', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({task, role: 'general'})
                });
                
                const data = await response.json();
                input.value = '';
                await loadTasks();
            } catch (e) {
                alert('Error: ' + e.message);
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        async function loadTasks() {
            try {
                const response = await fetch('/api/tasks');
                const tasks = await response.json();
                
                const list = document.getElementById('tasksList');
                if (tasks.length === 0) {
                    list.innerHTML = '<p style="color: #888; text-align: center;">暂无任务</p>';
                    return;
                }
                
                list.innerHTML = tasks.map(t => `
                    <div class="task-item">
                        <div class="task-item-header">
                            <div>
                                <strong>${t.task}</strong>
                                <br><small style="color: #888;">${t.timestamp}</small>
                            </div>
                            <span class="task-status status-${t.status}">${t.status}</span>
                        </div>
                        ${t.result ? `<div class="task-item-result"><pre style="margin-top:8px;padding:12px;background:#0d0d14;border-radius:8px;font-size:13px;max-height:250px;overflow:auto;color:#cdd6f4;white-space:pre-wrap;word-break:break-all;font-family:Consolas,Monaco,'Courier New',monospace;">${t.result}</pre></div>` : ''}
                        ${t.error ? `<div class="task-item-result"><pre style="margin-top:8px;padding:12px;background:#1f1010;border-radius:8px;font-size:13px;max-height:150px;overflow:auto;color:#f38ba8;white-space:pre-wrap;">${t.error}</pre></div>` : ''}
                    </div>
                `).join('');
                
                const completed = tasks.filter(t => t.status === 'completed').length;
                document.getElementById('totalTasks').textContent = tasks.length;
                document.getElementById('completedTasks').textContent = completed;
                document.getElementById('successRate').textContent = 
                    tasks.length ? Math.round(completed / tasks.length * 100) + '%' : '0%';
            } catch (e) {
                console.error(e);
            }
        }
        
        async function loadStats() {
            try {
                const response = await fetch('/api/stats');
                const stats = await response.json();
                
                if (stats.pool) {
                    document.getElementById('activeAgents').textContent = 
                        stats.pool.available_agents || 0;
                }
            } catch (e) {
                console.error(e);
            }
        }
        
        setInterval(loadTasks, 5000);
        loadTasks();
        loadStats();
    </script>
</body>
</html>
"""
    
    def get_app(self) -> FastAPI:
        """获取FastAPI应用"""
        if not self._app:
            self._app = self.create_app()
        return self._app
    
    async def start(self, host: str = "0.0.0.0", port: int = 8000) -> None:
        """启动服务"""
        import uvicorn
        
        if not self._app:
            self._app = self.create_app()
        
        config = uvicorn.Config(
            self._app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

"""
AgentPool - Agent池

管理一组工作Agent的池化调度。
"""

from typing import Any, Dict, List, Optional, Callable
import asyncio
import threading

from ..agents import WorkerAgent
from ..memory import WorkingMemory, VectorMemory
from ..tools import ToolRegistry
from ..skills import SkillHub


class AgentPool:
    """
    Agent池
    
    管理一组工作Agent的池化调度，实现负载均衡。
    """
    
    def __init__(
        self,
        tools: ToolRegistry,
        memory: WorkingMemory,
        skill_hub: SkillHub,
        llm: Any = None,
        vector_memory: VectorMemory = None,
        pool_size: int = 10,
        trace_callback: Optional[Callable] = None
    ):
        self.tools = tools
        self.memory = memory
        self.skill_hub = skill_hub
        self.llm = llm
        self.vector_memory = vector_memory
        self.pool_size = pool_size
        self.trace_callback = trace_callback
        
        self._agents: List[WorkerAgent] = []
        self._lock = threading.RLock()
        self._counter = 0
        
        self._initialize_pool()
    
    def _initialize_pool(self) -> None:
        """初始化Agent池"""
        roles = ["researcher", "coder", "analyst", "writer"]
        
        for i in range(self.pool_size):
            role = roles[i % len(roles)]
            agent = WorkerAgent(
                role=role,
                agent_id=f"agent_{i}",
                tools=self.tools,
                memory=self.memory,
                skills=self.skill_hub,
                llm=self.llm,
                vector_memory=self.vector_memory,
                trace_callback=self.trace_callback
            )
            self._agents.append(agent)
    
    def register(self, agent: WorkerAgent) -> None:
        """
        注册Agent
        
        Args:
            agent: Agent实例
        """
        with self._lock:
            self._agents.append(agent)
    
    def unregister(self, agent_id: str) -> bool:
        """
        注销Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            是否成功
        """
        with self._lock:
            for i, agent in enumerate(self._agents):
                if agent.agent_id == agent_id:
                    self._agents.pop(i)
                    return True
            return False
    
    async def execute_task(self, task: Any) -> Any:
        """
        执行任务
        
        Args:
            task: 任务
            
        Returns:
            执行结果
        """
        agent = self._get_available_agent()
        
        if not agent:
            return {"error": "No available agent"}
        
        return await agent.run(task)
    
    def _get_available_agent(self) -> Optional[WorkerAgent]:
        """获取可用的Agent"""
        with self._lock:
            if not self._agents:
                return None
            
            self._counter += 1
            index = self._counter % len(self._agents)
            
            return self._agents[index]
    
    def get_agent(self, agent_id: str) -> Optional[WorkerAgent]:
        """
        获取指定Agent
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent实例
        """
        with self._lock:
            for agent in self._agents:
                if agent.agent_id == agent_id:
                    return agent
            return None
    
    def get_all_agents(self) -> List[WorkerAgent]:
        """
        获取所有Agent
        
        Returns:
            Agent列表
        """
        with self._lock:
            return self._agents.copy()
    
    def get_available_count(self) -> int:
        """获取可用Agent数量"""
        with self._lock:
            return sum(1 for a in self._agents if a.agent_state.is_available())
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            total_tasks = sum(a._task_count for a in self._agents)
            total_success = sum(a._success_count for a in self._agents)
            
            return {
                "pool_size": len(self._agents),
                "available_agents": self.get_available_count(),
                "total_tasks": total_tasks,
                "total_success": total_success,
                "success_rate": total_success / total_tasks if total_tasks > 0 else 0
            }
    
    def __len__(self) -> int:
        """获取Agent数量"""
        with self._lock:
            return len(self._agents)

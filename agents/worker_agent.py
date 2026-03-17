"""
WorkerAgent - 工作Agent

负责执行具体任务的Agent实现。
"""

from typing import Any, Dict, List, Optional
import asyncio
import time

from ..models import AgentState, Task
from ..memory import WorkingMemory, VectorMemory
from ..tools import ToolRegistry, ToolRouter
from ..skills import SkillHub
from ..cognition import ReActEngine, Reflection, Critic


class WorkerAgent:
    """
    工作Agent
    
    负责执行具体任务的Agent，结合ReAct引擎、反思和批评模块。
    """
    
    def __init__(
        self,
        role: str,
        agent_id: str,
        tools: ToolRegistry,
        memory: WorkingMemory,
        skills: SkillHub,
        llm: Optional[Any] = None,
        vector_memory: VectorMemory = None,
        max_steps: int = 8,
        enable_reflection: bool = True,
        enable_critic: bool = True
    ):
        self.role = role
        self.agent_id = agent_id
        self.tools = tools
        self.memory = memory
        self.skills = skills
        self.llm = llm
        self.vector_memory = vector_memory
        self.max_steps = max_steps
        
        self.tool_router = ToolRouter(tools)
        self.react = ReActEngine(
            tool_router=self.tool_router,
            llm=llm,
            max_steps=max_steps,
            enable_reflection=enable_reflection
        )
        
        self.reflection = Reflection(llm=llm) if enable_reflection else None
        self.critic = Critic(llm=llm) if enable_critic else None
        
        self.agent_state = AgentState(
            role=role,
            id=agent_id,
            name=f"Worker-{role}-{agent_id[:8]}",
            capabilities=self._get_capabilities()
        )
        
        self._task_count = 0
        self._success_count = 0
    
    def _get_capabilities(self) -> List[str]:
        """获取Agent能力"""
        capabilities_map = {
            "researcher": ["search", "web", "research"],
            "coder": ["code", "debug", "execute"],
            "analyst": ["analysis", "data"],
            "writer": ["write", "summarize"]
        }
        return capabilities_map.get(self.role, ["general"])
    
    async def run(self, task: Task) -> Any:
        """
        运行任务
        
        Args:
            task: 任务对象
            
        Returns:
            执行结果
        """
        self.agent_state.start_task(task.id, task.description)
        
        try:
            result = await self._execute_task(task)
            
            self._task_count += 1
            self._success_count += 1
            
            self.agent_state.complete_task(success=True)
            
            return result
            
        except Exception as e:
            self._task_count += 1
            
            self.agent_state.set_error(str(e))
            
            return {
                "error": str(e),
                "task_id": task.id
            }
    
    async def _execute_task(self, task: Task) -> Any:
        """执行任务"""
        result = await self.react.run(task)
        
        if self.reflection:
            history = self.react.get_history()
            summary = await self.reflection.reflect(history, task.description)
            self.memory.set(f"reflection_{task.id}", summary)
        
        if self.critic:
            evaluation = await self.critic.evaluate(task, result)
            
            if not evaluation.get("is_success", True):
                if task.retry():
                    return await self._execute_task(task)
        
        return result
    
    async def execute_skill(
        self,
        skill_name: str,
        input_data: Any = None,
        **kwargs
    ) -> Any:
        """
        执行技能
        
        Args:
            skill_name: 技能名称
            input_data: 输入数据
            **kwargs: 其他参数
            
        Returns:
            执行结果
        """
        skill = self.skills.get(skill_name)
        
        if not skill:
            return {"error": f"Skill {skill_name} not found"}
        
        return await skill.execute(input_data, **kwargs)
    
    def get_status(self) -> Dict[str, Any]:
        """获取Agent状态"""
        return self.agent_state.to_dict()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "task_count": self._task_count,
            "success_count": self._success_count,
            "success_rate": self._success_count / self._task_count if self._task_count > 0 else 0
        }
    
    async def learn(self, content: str, metadata: Dict[str, Any] = None) -> None:
        """
        学习新知识
        
        Args:
            content: 内容
            metadata: 元数据
        """
        if self.vector_memory:
            self.vector_memory.add(content, metadata or {})
    
    def clear_memory(self) -> None:
        """清空记忆"""
        self.memory.clear()

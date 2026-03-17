"""
Runtime - Agent运行时

整合Agent池、调度器和工厂的运行时环境。
"""

from typing import Any, Dict, List, Optional

from .agent_pool import AgentPool
from .distributed_agent_pool import DistributedAgentPool
from .scheduler import Scheduler
from ..agents import DynamicAgentFactory, WorkerAgent
from ..memory import WorkingMemory, VectorMemory, TaskReplay
from ..tools import ToolRegistry
from ..skills import SkillHub
from ..cognition import PromptOptimizer, RLAgent


class AgentRuntime:
    """
    Agent运行时
    
    整合所有组件，提供完整的Agent执行环境。
    """
    
    def __init__(
        self,
        tools: Optional[ToolRegistry] = None,
        memory: Optional[WorkingMemory] = None,
        skill_hub: Optional[SkillHub] = None,
        llm: Any = None,
        vector_memory: Optional[VectorMemory] = None,
        nodes: List[Any] = None,
        pool_size: int = 10
    ):
        self.tools = tools or ToolRegistry()
        self.memory = memory or WorkingMemory()
        self.skill_hub = skill_hub or SkillHub()
        self.llm = llm
        self.vector_memory = vector_memory
        
        if nodes:
            self.pool = DistributedAgentPool(nodes)
        else:
            self.pool = AgentPool(
                tools=self.tools,
                memory=self.memory,
                skill_hub=self.skill_hub,
                llm=self.llm,
                vector_memory=self.vector_memory,
                pool_size=pool_size
            )
        
        self.scheduler = Scheduler(self.pool)
        
        self.agent_factory = DynamicAgentFactory(
            agent_pool=self.pool,
            tool_registry=self.tools,
            skill_hub=self.skill_hub,
            vector_memory=self.vector_memory,
            llm=self.llm
        )
        
        self.task_replay = TaskReplay()
        self.prompt_optimizer = PromptOptimizer(vector_memory=self.vector_memory)
        self.rl_agent = RLAgent()
    
    async def run(self, tasks: List[Any]) -> Dict[str, Any]:
        """
        运行任务
        
        Args:
            tasks: 任务列表
            
        Returns:
            结果字典
        """
        from ..models import Task
        
        task_objects = []
        for t in tasks:
            if isinstance(t, Task):
                task_objects.append(t)
            else:
                task = Task(description=str(t))
                task_objects.append(task)
        
        return await self.scheduler.run(task_objects)
    
    async def run_single(self, task: Any) -> Any:
        """
        运行单个任务
        
        Args:
            task: 任务
            
        Returns:
            执行结果
        """
        from ..models import Task
        
        if isinstance(task, Task):
            task_obj = task
        else:
            task_obj = Task(description=str(task))
        
        return await self.scheduler.run_single(task_obj)
    
    def spawn_agent(
        self,
        role: str,
        max_steps: int = 8,
        enable_reflection: bool = True,
        enable_critic: bool = True
    ) -> WorkerAgent:
        """
        创建Agent
        
        Args:
            role: 角色
            max_steps: 最大步数
            enable_reflection: 启用反思
            enable_critic: 启用批评
            
        Returns:
            WorkerAgent实例
        """
        return self.agent_factory.create_agent(
            role=role,
            max_steps=max_steps,
            enable_reflection=enable_reflection,
            enable_critic=enable_critic
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取运行时统计"""
        return {
            "pool": self.pool.get_statistics() if hasattr(self.pool, "get_statistics") else {},
            "scheduler": self.scheduler.get_status(),
            "task_replay": self.task_replay.get_statistics(),
            "rl_agent": self.rl_agent.get_statistics()
        }
    
    def register_default_tools(self) -> None:
        """注册默认工具"""
        from ..tools import SearchTool, CodeTool, FileTool, WebTool
        
        self.tools.register(SearchTool())
        self.tools.register(CodeTool())
        self.tools.register(FileTool())
        self.tools.register(WebTool())
    
    def register_default_skills(self) -> None:
        """注册默认技能"""
        from ..skills import ResearchSkill, AnalysisSkill, WritingSkill
        
        self.skill_hub.register(ResearchSkill(self.tools))
        self.skill_hub.register(AnalysisSkill())
        self.skill_hub.register(WritingSkill(self.tools))

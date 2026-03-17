"""
DynamicAgentFactory - 动态Agent工厂

动态创建不同类型的Agent。
"""

from typing import Any, Dict, List, Optional
from .worker_agent import WorkerAgent
from ..memory import WorkingMemory, VectorMemory
from ..tools import ToolRegistry
from ..skills import SkillHub


class DynamicAgentFactory:
    """
    动态Agent工厂
    
    根据角色动态创建不同类型的WorkerAgent。
    """
    
    def __init__(
        self,
        agent_pool,
        tool_registry: ToolRegistry = None,
        skill_hub: SkillHub = None,
        vector_memory: VectorMemory = None,
        llm: Any = None
    ):
        self.agent_pool = agent_pool
        self.tool_registry = tool_registry or ToolRegistry()
        self.skill_hub = skill_hub or SkillHub()
        self.vector_memory = vector_memory
        self.llm = llm
        
        self._capabilities_map = {
            "researcher": ["search", "web", "research"],
            "coder": ["code", "debug", "execute"],
            "analyst": ["analysis", "data_processing"],
            "writer": ["writing", "summarization"],
            "general": ["general_task"]
        }
    
    def create_agent(
        self,
        role: str,
        agent_id: str = None,
        max_steps: int = 8,
        enable_reflection: bool = True,
        enable_critic: bool = True
    ) -> WorkerAgent:
        """
        创建Agent
        
        Args:
            role: 角色
            agent_id: Agent ID
            max_steps: 最大步数
            enable_reflection: 启用反思
            enable_critic: 启用批评
            
        Returns:
            WorkerAgent实例
        """
        if agent_id is None:
            import uuid
            agent_id = str(uuid.uuid4())
        
        memory = WorkingMemory()
        
        capabilities = self._capabilities_map.get(role.lower(), ["general_task"])
        
        agent = WorkerAgent(
            role=role,
            agent_id=agent_id,
            tools=self.tool_registry,
            memory=memory,
            skills=self.skill_hub,
            llm=self.llm,
            vector_memory=self.vector_memory,
            max_steps=max_steps,
            enable_reflection=enable_reflection,
            enable_critic=enable_critic
        )
        
        agent.agent_state.capabilities = capabilities
        
        if self.agent_pool:
            self.agent_pool.register(agent)
        
        return agent
    
    def create_researcher(self, agent_id: str = None) -> WorkerAgent:
        """创建研究员Agent"""
        return self.create_agent("researcher", agent_id)
    
    def create_coder(self, agent_id: str = None) -> WorkerAgent:
        """创建编码员Agent"""
        return self.create_agent("coder", agent_id)
    
    def create_analyst(self, agent_id: str = None) -> WorkerAgent:
        """创建分析师Agent"""
        return self.create_agent("analyst", agent_id)
    
    def create_writer(self, agent_id: str = None) -> WorkerAgent:
        """创建作家Agent"""
        return self.create_agent("writer", agent_id)
    
    def get_capabilities(self, role: str) -> List[str]:
        """
        获取角色能力
        
        Args:
            role: 角色
            
        Returns:
            能力列表
        """
        return self._capabilities_map.get(role.lower(), ["general_task"])
    
    def add_capabilities(self, role: str, capabilities: List[str]) -> None:
        """
        添加角色能力
        
        Args:
            role: 角色
            capabilities: 能力列表
        """
        if role.lower() not in self._capabilities_map:
            self._capabilities_map[role.lower()] = []
        
        for cap in capabilities:
            if cap not in self._capabilities_map[role.lower()]:
                self._capabilities_map[role.lower()].append(cap)

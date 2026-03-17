"""
Agent OS Ultimate - 智能Agent操作系统

完整的Agent系统实现，包含以下模块:
- core: 核心模块 (EventBus, Blackboard, Trace, Config, Logger)
- models: 数据模型 (Task, Message, AgentState, PromptTemplate)
- memory: 记忆系统 (WorkingMemory, VectorMemory, EpisodicMemory, TaskReplay)
- tools: 工具系统 (BaseTool, ToolRegistry, ToolRouter)
- skills: 技能系统 (Skill, SkillHub)
- cognition: 认知引擎 (ReActEngine, Reflection, Critic, PromptOptimizer)
- agents: Agent实现 (WorkerAgent, DynamicAgentFactory, SelfImprovingAgent)
- runtime: 运行时 (AgentPool, DistributedAgentPool, Scheduler, AgentRuntime)
- inference: 推理模块 (GPUBatchInference, MultiLLMRouter)
- control_plane: 控制平面 (FastAPI, Web UI)
"""

__version__ = "1.0.0"

from .core import EventBus, Blackboard, Trace, Config, AgentOSLogger, logger
from .models import Task, Message, AgentState, PromptTemplate
from .memory import (
    WorkingMemory,
    VectorMemory,
    EpisodicMemory,
    TaskReplay
)
from .tools import BaseTool, ToolRegistry, ToolRouter
from .skills import Skill, SkillHub
from .cognition import ReActEngine, Reflection, Critic, PromptOptimizer, RLAgent
from .agents import WorkerAgent, DynamicAgentFactory, SelfImprovingAgent
from .runtime import AgentPool, AgentRuntime, Scheduler
from .inference import GPUBatchInference, MultiLLMRouter
from .control_plane import ControlPlane

__all__ = [
    "__version__",
    "EventBus",
    "Blackboard",
    "Trace",
    "Config",
    "Logger",
    "Task",
    "Message",
    "AgentState",
    "PromptTemplate",
    "WorkingMemory",
    "VectorMemory",
    "EpisodicMemory",
    "TaskReplay",
    "BaseTool",
    "ToolRegistry",
    "ToolRouter",
    "Skill",
    "SkillHub",
    "ReActEngine",
    "Reflection",
    "Critic",
    "PromptOptimizer",
    "RLAgent",
    "WorkerAgent",
    "DynamicAgentFactory",
    "SelfImprovingAgent",
    "AgentPool",
    "AgentRuntime",
    "Scheduler",
    "GPUBatchInference",
    "MultiLLMRouter",
    "ControlPlane"
]


def create_runtime(
    pool_size: int = 10,
    llm: callable = None,
    enable_tools: bool = True,
    enable_skills: bool = True
) -> AgentRuntime:
    """
    创建Agent运行时
    
    Args:
        pool_size: Agent池大小
        llm: LLM调用函数
        enable_tools: 启用工具
        enable_skills: 启用技能
        
    Returns:
        AgentRuntime实例
    """
    runtime = AgentRuntime(llm=llm, pool_size=pool_size)
    
    if enable_tools:
        runtime.register_default_tools()
    
    if enable_skills:
        runtime.register_default_skills()
    
    return runtime


def create_control_plane(runtime: AgentRuntime = None) -> ControlPlane:
    """
    创建控制平面
    
    Args:
        runtime: Agent运行时
        
    Returns:
        ControlPlane实例
    """
    return ControlPlane(runtime=runtime)

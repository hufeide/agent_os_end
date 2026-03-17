"""
Config - 系统配置

定义系统的各种配置参数。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import os


@dataclass
class Config:
    """系统配置"""
    
    MAX_REACT_STEPS: int = 8
    GPU_BATCH_SIZE: int = 8
    RL_LEARNING_RATE: float = 0.01
    MAX_SUBTASK_COMPLEXITY: int = 5
    MAX_SUBTASKS: int = 10
    
    VECTOR_MEMORY_DIM: int = 1536
    VECTOR_MEMORY_TOP_K: int = 3
    WORKING_MEMORY_MAX_SIZE: int = 100
    EPISODIC_MEMORY_MAX_SIZE: int = 1000
    TASK_REPLAY_HISTORY_SIZE: int = 1000
    
    TOOL_TIMEOUT: int = 30
    TASK_TIMEOUT: int = 300
    AGENT_POOL_SIZE: int = 10
    DISTRIBUTED_NODE_COUNT: int = 3
    
    EVENT_BUS_MAX_HISTORY: int = 1000
    BLACKBOARD_MAX_SIZE: int = 10000
    TRACE_MAX_EVENTS: int = 10000
    
    LOG_LEVEL: str = "INFO"
    ENABLE_TRACING: bool = True
    ENABLE_REFLECTION: bool = True
    ENABLE_CRITIC: bool = True
    ENABLE_RL: bool = True
    ENABLE_SELF_IMPROVING: bool = True
    
    LLM_DEFAULT_MODEL: str = "qwen2.5-coder"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048
    
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    WS_HEARTBEAT_INTERVAL: int = 30
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        """
        从字典创建配置
        
        Args:
            config_dict: 配置字典
            
        Returns:
            配置对象
        """
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in config_dict.items() if k in valid_fields}
        return cls(**filtered)
    
    @classmethod
    def from_env(cls) -> 'Config':
        """
        从环境变量创建配置
        
        Returns:
            配置对象
        """
        return cls(
            MAX_REACT_STEPS=int(os.getenv("MAX_REACT_STEPS", "8")),
            GPU_BATCH_SIZE=int(os.getenv("GPU_BATCH_SIZE", "8")),
            RL_LEARNING_RATE=float(os.getenv("RL_LEARNING_RATE", "0.01")),
            MAX_SUBTASK_COMPLEXITY=int(os.getenv("MAX_SUBTASK_COMPLEXITY", "5")),
            MAX_SUBTASKS=int(os.getenv("MAX_SUBTASKS", "10")),
            VECTOR_MEMORY_DIM=int(os.getenv("VECTOR_MEMORY_DIM", "1536")),
            VECTOR_MEMORY_TOP_K=int(os.getenv("VECTOR_MEMORY_TOP_K", "3")),
            WORKING_MEMORY_MAX_SIZE=int(os.getenv("WORKING_MEMORY_MAX_SIZE", "100")),
            EPISODIC_MEMORY_MAX_SIZE=int(os.getenv("EPISODIC_MEMORY_MAX_SIZE", "1000")),
            TASK_REPLAY_HISTORY_SIZE=int(os.getenv("TASK_REPLAY_HISTORY_SIZE", "1000")),
            TOOL_TIMEOUT=int(os.getenv("TOOL_TIMEOUT", "30")),
            TASK_TIMEOUT=int(os.getenv("TASK_TIMEOUT", "300")),
            AGENT_POOL_SIZE=int(os.getenv("AGENT_POOL_SIZE", "10")),
            DISTRIBUTED_NODE_COUNT=int(os.getenv("DISTRIBUTED_NODE_COUNT", "3")),
            EVENT_BUS_MAX_HISTORY=int(os.getenv("EVENT_BUS_MAX_HISTORY", "1000")),
            BLACKBOARD_MAX_SIZE=int(os.getenv("BLACKBOARD_MAX_SIZE", "10000")),
            TRACE_MAX_EVENTS=int(os.getenv("TRACE_MAX_EVENTS", "10000")),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            ENABLE_TRACING=os.getenv("ENABLE_TRACING", "true").lower() == "true",
            ENABLE_REFLECTION=os.getenv("ENABLE_REFLECTION", "true").lower() == "true",
            ENABLE_CRITIC=os.getenv("ENABLE_CRITIC", "true").lower() == "true",
            ENABLE_RL=os.getenv("ENABLE_RL", "true").lower() == "true",
            ENABLE_SELF_IMPROVING=os.getenv("ENABLE_SELF_IMPROVING", "true").lower() == "true",
            LLM_DEFAULT_MODEL=os.getenv("LLM_DEFAULT_MODEL", "qwen2.5-coder"),
            LLM_TEMPERATURE=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            LLM_MAX_TOKENS=int(os.getenv("LLM_MAX_TOKENS", "2048")),
            API_HOST=os.getenv("API_HOST", "0.0.0.0"),
            API_PORT=int(os.getenv("API_PORT", "8000")),
            WS_HEARTBEAT_INTERVAL=int(os.getenv("WS_HEARTBEAT_INTERVAL", "30"))
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            字典表示
        """
        return {
            "MAX_REACT_STEPS": self.MAX_REACT_STEPS,
            "GPU_BATCH_SIZE": self.GPU_BATCH_SIZE,
            "RL_LEARNING_RATE": self.RL_LEARNING_RATE,
            "MAX_SUBTASK_COMPLEXITY": self.MAX_SUBTASK_COMPLEXITY,
            "MAX_SUBTASKS": self.MAX_SUBTASKS,
            "VECTOR_MEMORY_DIM": self.VECTOR_MEMORY_DIM,
            "VECTOR_MEMORY_TOP_K": self.VECTOR_MEMORY_TOP_K,
            "WORKING_MEMORY_MAX_SIZE": self.WORKING_MEMORY_MAX_SIZE,
            "EPISODIC_MEMORY_MAX_SIZE": self.EPISODIC_MEMORY_MAX_SIZE,
            "TASK_REPLAY_HISTORY_SIZE": self.TASK_REPLAY_HISTORY_SIZE,
            "TOOL_TIMEOUT": self.TOOL_TIMEOUT,
            "TASK_TIMEOUT": self.TASK_TIMEOUT,
            "AGENT_POOL_SIZE": self.AGENT_POOL_SIZE,
            "DISTRIBUTED_NODE_COUNT": self.DISTRIBUTED_NODE_COUNT,
            "EVENT_BUS_MAX_HISTORY": self.EVENT_BUS_MAX_HISTORY,
            "BLACKBOARD_MAX_SIZE": self.BLACKBOARD_MAX_SIZE,
            "TRACE_MAX_EVENTS": self.TRACE_MAX_EVENTS,
            "LOG_LEVEL": self.LOG_LEVEL,
            "ENABLE_TRACING": self.ENABLE_TRACING,
            "ENABLE_REFLECTION": self.ENABLE_REFLECTION,
            "ENABLE_CRITIC": self.ENABLE_CRITIC,
            "ENABLE_RL": self.ENABLE_RL,
            "ENABLE_SELF_IMPROVING": self.ENABLE_SELF_IMPROVING,
            "LLM_DEFAULT_MODEL": self.LLM_DEFAULT_MODEL,
            "LLM_TEMPERATURE": self.LLM_TEMPERATURE,
            "LLM_MAX_TOKENS": self.LLM_MAX_TOKENS,
            "API_HOST": self.API_HOST,
            "API_PORT": self.API_PORT,
            "WS_HEARTBEAT_INTERVAL": self.WS_HEARTBEAT_INTERVAL
        }


DEFAULT_CONFIG = Config()

"""
AgentState - Agent状态模型

定义Agent的状态信息。
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid


class AgentType(Enum):
    """Agent类型"""
    MASTER = "master"
    WORKER = "worker"
    SELF_IMPROVING = "self_improving"
    CRITIC = "critic"
    PLANNER = "planner"


class AgentStatus(Enum):
    """Agent状态"""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING = "waiting"
    ERROR = "error"


@dataclass
class AgentState:
    """Agent状态模型"""
    role: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    type: str = AgentType.WORKER.value
    status: str = AgentStatus.IDLE.value
    tools: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    current_task_id: Optional[str] = None
    current_task_description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_active_at: datetime = field(default_factory=datetime.now)
    task_count: int = 0
    success_count: int = 0
    error_count: int = 0
    
    def __post_init__(self):
        if not self.name:
            self.name = f"{self.role}_{self.id[:8]}"
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return self.status in [AgentStatus.IDLE.value, AgentStatus.WAITING.value]
    
    def start_task(self, task_id: str, task_description: str) -> None:
        """开始任务"""
        self.status = AgentStatus.EXECUTING.value
        self.current_task_id = task_id
        self.current_task_description = task_description
        self.last_active_at = datetime.now()
    
    def complete_task(self, success: bool = True) -> None:
        """完成任务"""
        self.status = AgentStatus.IDLE.value
        self.current_task_id = None
        self.current_task_description = ""
        self.task_count += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        self.last_active_at = datetime.now()
    
    def set_error(self, error: str) -> None:
        """设置错误状态"""
        self.status = AgentStatus.ERROR.value
        self.metadata["last_error"] = error
        self.error_count += 1
        self.last_active_at = datetime.now()
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.task_count == 0:
            return 0.0
        return self.success_count / self.task_count
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "type": self.type,
            "status": self.status,
            "tools": self.tools,
            "skills": self.skills,
            "capabilities": self.capabilities,
            "current_task_id": self.current_task_id,
            "current_task_description": self.current_task_description,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "last_active_at": self.last_active_at.isoformat(),
            "task_count": self.task_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.get_success_rate()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentState':
        """从字典创建"""
        state = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            role=data.get("role", "worker"),
            type=data.get("type", AgentType.WORKER.value),
            status=data.get("status", AgentStatus.IDLE.value),
            tools=data.get("tools", []),
            skills=data.get("skills", []),
            capabilities=data.get("capabilities", []),
            current_task_id=data.get("current_task_id"),
            current_task_description=data.get("current_task_description", ""),
            metadata=data.get("metadata", {}),
            task_count=data.get("task_count", 0),
            success_count=data.get("success_count", 0),
            error_count=data.get("error_count", 0)
        )
        
        if "created_at" in data:
            state.created_at = datetime.fromisoformat(data["created_at"])
        if "last_active_at" in data:
            state.last_active_at = datetime.fromisoformat(data["last_active_at"])
        
        return state


@dataclass
class Agent:
    """Agent对象"""
    id: str
    name: str
    role: str
    type: str = AgentType.WORKER.value
    capabilities: List[str] = field(default_factory=list)
    status: str = AgentStatus.IDLE.value
    current_task_id: Optional[str] = None
    
    def is_available(self) -> bool:
        """检查是否可用"""
        return self.status in [AgentStatus.IDLE.value, AgentStatus.WAITING.value]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "type": self.type,
            "capabilities": self.capabilities,
            "status": self.status,
            "current_task_id": self.current_task_id
        }

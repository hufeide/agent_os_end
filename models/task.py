"""
Task - 任务模型

定义任务的数据结构和状态管理。
"""

import uuid
from dataclasses import dataclass, field
from typing import List, Any, Optional, Dict
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5


@dataclass
class Task:
    """任务模型"""
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"
    result: Any = None
    prompt: str = ""
    priority: int = TaskPriority.NORMAL.value
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    agent_id: Optional[str] = None
    agent_role: Optional[str] = None
    
    def __post_init__(self):
        if not self.name:
            self.name = self.description[:50]
    
    def is_completed(self) -> bool:
        """检查是否完成"""
        return self.status == TaskStatus.COMPLETED.value
    
    def is_failed(self) -> bool:
        """检查是否失败"""
        return self.status == TaskStatus.FAILED.value
    
    def is_running(self) -> bool:
        """检查是否运行中"""
        return self.status == TaskStatus.RUNNING.value
    
    def can_execute(self, completed_ids: set) -> bool:
        """检查是否可以执行"""
        if self.status != TaskStatus.PENDING.value:
            return False
        return all(dep in completed_ids for dep in self.dependencies)
    
    def start(self) -> None:
        """开始任务"""
        self.status = TaskStatus.RUNNING.value
        self.started_at = datetime.now()
    
    def complete(self, result: Any) -> None:
        """完成任务"""
        self.status = TaskStatus.COMPLETED.value
        self.result = result
        self.completed_at = datetime.now()
    
    def fail(self, error: str) -> None:
        """任务失败"""
        self.status = TaskStatus.FAILED.value
        self.error = error
        self.completed_at = datetime.now()
    
    def retry(self) -> bool:
        """重试任务"""
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            self.status = TaskStatus.PENDING.value
            self.error = None
            return True
        return False
    
    def cancel(self) -> None:
        """取消任务"""
        self.status = TaskStatus.CANCELLED.value
        self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "dependencies": self.dependencies,
            "status": self.status,
            "result": self.result,
            "prompt": self.prompt,
            "priority": self.priority,
            "payload": self.payload,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "agent_id": self.agent_id,
            "agent_role": self.agent_role
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """从字典创建"""
        task = cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            dependencies=data.get("dependencies", []),
            status=data.get("status", "pending"),
            result=data.get("result"),
            prompt=data.get("prompt", ""),
            priority=data.get("priority", TaskPriority.NORMAL.value),
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {}),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            agent_id=data.get("agent_id"),
            agent_role=data.get("agent_role")
        )
        
        if "created_at" in data and data["created_at"]:
            task.created_at = datetime.fromisoformat(data["created_at"])
        if "started_at" in data and data["started_at"]:
            task.started_at = datetime.fromisoformat(data["started_at"])
        if "completed_at" in data and data["completed_at"]:
            task.completed_at = datetime.fromisoformat(data["completed_at"])
        
        return task

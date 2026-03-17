"""
TaskReplay - 任务回放系统

存储和管理任务执行历史，用于自我改进和经验复用。
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import threading
import uuid


@dataclass
class TaskRecord:
    """任务记录"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str = ""
    task_description: str = ""
    result: Any = None
    reward: float = 0.0
    prompt: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    execution_time: float = 0.0
    steps: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "task_description": self.task_description,
            "result": self.result,
            "reward": self.reward,
            "prompt": self.prompt,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "execution_time": self.execution_time,
            "steps": self.steps
        }


class TaskReplay:
    """
    任务回放系统
    
    存储任务执行历史，支持自我改进和经验复用。
    """
    
    def __init__(self, history_size: int = 1000):
        self._history: deque = deque(maxlen=history_size)
        self._lock = threading.RLock()
        self._index_by_task: Dict[str, List[int]] = {}
    
    def add(
        self,
        task_id: str,
        task_description: str,
        result: Any,
        reward: float = 0.0,
        prompt: str = "",
        metadata: Dict[str, Any] = None,
        execution_time: float = 0.0,
        steps: int = 0
    ) -> str:
        """
        添加任务记录
        
        Args:
            task_id: 任务ID
            task_description: 任务描述
            result: 结果
            reward: 奖励
            prompt: 提示词
            metadata: 元数据
            execution_time: 执行时间
            steps: 步骤数
            
        Returns:
            记录ID
        """
        record = TaskRecord(
            task_id=task_id,
            task_description=task_description,
            result=result,
            reward=reward,
            prompt=prompt,
            metadata=metadata or {},
            execution_time=execution_time,
            steps=steps
        )
        
        with self._lock:
            self._history.append(record)
            
            if task_description[:50] not in self._index_by_task:
                self._index_by_task[task_description[:50]] = []
            self._index_by_task[task_description[:50]].append(len(self._history) - 1)
            
            return record.id
    
    def recent(self, k: int = 10) -> List[TaskRecord]:
        """
        获取最近的任务记录
        
        Args:
            k: 数量
            
        Returns:
            记录列表
        """
        with self._lock:
            return list(self._history)[-k:]
    
    def get_by_task_id(self, task_id: str) -> List[TaskRecord]:
        """
        按任务ID获取记录
        
        Args:
            task_id: 任务ID
            
        Returns:
            记录列表
        """
        with self._lock:
            return [r for r in self._history if r.task_id == task_id]
    
    def get_successful(self, min_reward: float = 0.8) -> List[TaskRecord]:
        """
        获取成功的任务记录
        
        Args:
            min_reward: 最小奖励
            
        Returns:
            记录列表
        """
        with self._lock:
            return [r for r in self._history if r.reward >= min_reward]
    
    def get_failed(self, max_reward: float = 0.3) -> List[TaskRecord]:
        """
        获取失败的任务记录
        
        Args:
            max_reward: 最大奖励
            
        Returns:
            记录列表
        """
        with self._lock:
            return [r for r in self._history if r.reward <= max_reward]
    
    def get_average_reward(self) -> float:
        """获取平均奖励"""
        with self._lock:
            if not self._history:
                return 0.0
            return sum(r.reward for r in self._history) / len(self._history)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            if not self._history:
                return {
                    "total_records": 0,
                    "average_reward": 0.0,
                    "successful_count": 0,
                    "failed_count": 0
                }
            
            successful = sum(1 for r in self._history if r.reward >= 0.8)
            failed = sum(1 for r in self._history if r.reward <= 0.3)
            
            return {
                "total_records": len(self._history),
                "average_reward": sum(r.reward for r in self._history) / len(self._history),
                "successful_count": successful,
                "failed_count": failed,
                "average_execution_time": sum(r.execution_time for r in self._history) / len(self._history),
                "average_steps": sum(r.steps for r in self._history) / len(self._history)
            }
    
    def clear(self) -> None:
        """清空历史"""
        with self._lock:
            self._history.clear()
            self._index_by_task.clear()
    
    def count(self) -> int:
        """获取记录数量"""
        with self._lock:
            return len(self._history)

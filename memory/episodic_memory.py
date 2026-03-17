"""
EpisodicMemory - 情景记忆

记录Agent执行过程中的重要事件和经验。
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import deque
import threading
import uuid


@dataclass
class Episode:
    """经验条目"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    content: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    agent_id: str = ""
    task_id: str = ""
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "content": self.content,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "tags": self.tags
        }


class EpisodicMemory:
    """
    情景记忆
    
    记录Agent执行过程中的重要事件，支持按时间和类型检索。
    """
    
    def __init__(self, max_size: int = 1000):
        self._events: deque = deque(maxlen=max_size)
        self._lock = threading.RLock()
        self._index: Dict[str, List[int]] = {}
    
    def add(
        self,
        event: str,
        content: str = "",
        data: Dict[str, Any] = None,
        agent_id: str = "",
        task_id: str = "",
        tags: List[str] = None
    ) -> str:
        """
        添加经验
        
        Args:
            event: 事件类型
            content: 内容
            data: 数据
            agent_id: Agent ID
            task_id: 任务ID
            tags: 标签
            
        Returns:
            经验ID
        """
        episode = Episode(
            event_type=event,
            content=content,
            data=data or {},
            agent_id=agent_id,
            task_id=task_id,
            tags=tags or []
        )
        
        with self._lock:
            self._events.append(episode)
            
            if event not in self._index:
                self._index[event] = []
            self._index[event].append(len(self._events) - 1)
            
            for tag in episode.tags:
                if tag not in self._index:
                    self._index[tag] = []
                self._index[tag].append(len(self._events) - 1)
            
            return episode.id
    
    def recent(self, k: int = 10) -> List[Episode]:
        """
        获取最近的经验
        
        Args:
            k: 数量
            
        Returns:
            经验列表
        """
        with self._lock:
            return list(self._events)[-k:]
    
    def get_by_type(self, event_type: str) -> List[Episode]:
        """
        按类型获取经验
        
        Args:
            event_type: 事件类型
            
        Returns:
            经验列表
        """
        with self._lock:
            indices = self._index.get(event_type, [])
            return [self._events[i] for i in indices if i < len(self._events)]
    
    def get_by_agent(self, agent_id: str) -> List[Episode]:
        """
        按Agent获取经验
        
        Args:
            agent_id: Agent ID
            
        Returns:
            经验列表
        """
        with self._lock:
            return [e for e in self._events if e.agent_id == agent_id]
    
    def get_by_task(self, task_id: str) -> List[Episode]:
        """
        按任务获取经验
        
        Args:
            task_id: 任务ID
            
        Returns:
            经验列表
        """
        with self._lock:
            return [e for e in self._events if e.task_id == task_id]
    
    def get_by_tag(self, tag: str) -> List[Episode]:
        """
        按标签获取经验
        
        Args:
            tag: 标签
            
        Returns:
            经验列表
        """
        with self._lock:
            indices = self._index.get(tag, [])
            return [self._events[i] for i in indices if i < len(self._events)]
    
    def search(self, query: str) -> List[Episode]:
        """
        搜索经验
        
        Args:
            query: 查询文本
            
        Returns:
            经验列表
        """
        with self._lock:
            query_lower = query.lower()
            return [
                e for e in self._events
                if query_lower in e.content.lower() or query_lower in e.event_type.lower()
            ]
    
    def clear(self) -> None:
        """清空记忆"""
        with self._lock:
            self._events.clear()
            self._index.clear()
    
    def count(self) -> int:
        """获取经验数量"""
        with self._lock:
            return len(self._events)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            type_counts = {}
            for event in self._events:
                type_counts[event.event_type] = type_counts.get(event.event_type, 0) + 1
            
            return {
                "total_events": len(self._events),
                "event_types": type_counts,
                "indexed_types": len(self._index)
            }

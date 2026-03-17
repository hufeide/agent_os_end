"""
Trace - 执行追踪系统

记录和导出Agent执行过程中的事件和状态变化。
"""

import threading
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import uuid


class TraceLevel(Enum):
    """追踪级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class TraceEvent:
    """追踪事件"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    level: TraceLevel = TraceLevel.INFO
    category: str = ""
    event_type: str = ""
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    agent_id: str = ""
    task_id: str = ""
    step: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.value,
            "category": self.category,
            "type": self.event_type,
            "message": self.message,
            "data": self.data,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "step": self.step
        }


class Trace:
    """
    执行追踪系统
    
    记录Agent执行过程中的所有事件，支持多级别、多分类的追踪。
    """
    
    def __init__(self, max_events: int = 10000):
        self._events: List[TraceEvent] = []
        self._max_events = max_events
        self._lock = threading.RLock()
        self._categories: Dict[str, int] = {}
        self._enabled = True
        self._min_level = TraceLevel.DEBUG
    
    def log(
        self,
        event: str,
        level: TraceLevel = TraceLevel.INFO,
        category: str = "general",
        message: str = "",
        data: Dict[str, Any] = None,
        agent_id: str = "",
        task_id: str = "",
        step: int = 0
    ) -> None:
        """
        记录事件
        
        Args:
            event: 事件类型
            level: 级别
            category: 分类
            message: 消息
            data: 数据
            agent_id: Agent ID
            task_id: 任务ID
            step: 步骤
        """
        if not self._enabled:
            return
        
        if level.value < self._min_level.value:
            return
        
        trace_event = TraceEvent(
            level=level,
            category=category,
            event_type=event,
            message=message or event,
            data=data or {},
            agent_id=agent_id,
            task_id=task_id,
            step=step
        )
        
        with self._lock:
            self._events.append(trace_event)
            
            self._categories[category] = self._categories.get(category, 0) + 1
            
            if len(self._events) > self._max_events:
                self._events.pop(0)
    
    def debug(self, event: str, message: str = "", **kwargs) -> None:
        """记录调试级别事件"""
        self.log(event, TraceLevel.DEBUG, message=message, **kwargs)
    
    def info(self, event: str, message: str = "", **kwargs) -> None:
        """记录信息级别事件"""
        self.log(event, TraceLevel.INFO, message=message, **kwargs)
    
    def warning(self, event: str, message: str = "", **kwargs) -> None:
        """记录警告级别事件"""
        self.log(event, TraceLevel.WARNING, message=message, **kwargs)
    
    def error(self, event: str, message: str = "", **kwargs) -> None:
        """记录错误级别事件"""
        self.log(event, TraceLevel.ERROR, message=message, **kwargs)
    
    def critical(self, event: str, message: str = "", **kwargs) -> None:
        """记录严重级别事件"""
        self.log(event, TraceLevel.CRITICAL, message=message, **kwargs)
    
    def export(self, format: str = "list") -> Any:
        """
        导出追踪数据
        
        Args:
            format: 格式 (list, json, dict)
            
        Returns:
            追踪数据
        """
        with self._lock:
            if format == "list":
                return [e.to_dict() for e in self._events]
            elif format == "json":
                return json.dumps([e.to_dict() for e in self._events], indent=2, ensure_ascii=False)
            elif format == "dict":
                return {
                    "events": [e.to_dict() for e in self._events],
                    "categories": dict(self._categories),
                    "total": len(self._events)
                }
            return self._events
    
    def get_events(
        self,
        category: str = None,
        event_type: str = None,
        level: TraceLevel = None,
        agent_id: str = None,
        task_id: str = None,
        limit: int = 100
    ) -> List[TraceEvent]:
        """
        获取事件列表
        
        Args:
            category: 分类过滤
            event_type: 事件类型过滤
            level: 级别过滤
            agent_id: Agent ID过滤
            task_id: 任务ID过滤
            limit: 数量限制
            
        Returns:
            事件列表
        """
        with self._lock:
            filtered = self._events.copy()
            
            if category:
                filtered = [e for e in filtered if e.category == category]
            if event_type:
                filtered = [e for e in filtered if e.event_type == event_type]
            if level:
                filtered = [e for e in filtered if e.level == level]
            if agent_id:
                filtered = [e for e in filtered if e.agent_id == agent_id]
            if task_id:
                filtered = [e for e in filtered if e.task_id == task_id]
            
            return filtered[-limit:]
    
    def get_agent_trace(self, agent_id: str) -> List[TraceEvent]:
        """
        获取指定Agent的追踪
        
        Args:
            agent_id: Agent ID
            
        Returns:
            追踪事件列表
        """
        return self.get_events(agent_id=agent_id, limit=self._max_events)
    
    def get_task_trace(self, task_id: str) -> List[TraceEvent]:
        """
        获取指定任务的追踪
        
        Args:
            task_id: 任务ID
            
        Returns:
            追踪事件列表
        """
        return self.get_events(task_id=task_id, limit=self._max_events)
    
    def clear(self) -> None:
        """清空追踪记录"""
        with self._lock:
            self._events.clear()
            self._categories.clear()
    
    def set_level(self, level: TraceLevel) -> None:
        """
        设置最小追踪级别
        
        Args:
            level: 级别
        """
        self._min_level = level
    
    def enable(self) -> None:
        """启用追踪"""
        self._enabled = True
    
    def disable(self) -> None:
        """禁用追踪"""
        self._enabled = False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息
        """
        with self._lock:
            level_counts = {}
            for event in self._events:
                level_counts[event.level.value] = level_counts.get(event.level.value, 0) + 1
            
            return {
                "total_events": len(self._events),
                "categories": dict(self._categories),
                "levels": level_counts,
                "max_events": self._max_events
            }
    
    def __len__(self) -> int:
        """获取事件数量"""
        with self._lock:
            return len(self._events)

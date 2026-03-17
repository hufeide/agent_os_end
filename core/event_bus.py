"""
Event Bus - 事件总线

提供事件的发布-订阅机制，用于系统各组件之间的解耦通信。
"""

import asyncio
from typing import Callable, Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import threading


@dataclass
class Event:
    """事件对象"""
    type: str
    data: Any
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = ""
    
    def __repr__(self):
        return f"Event(type={self.type}, source={self.source}, timestamp={self.timestamp})"


class EventBus:
    """
    事件总线
    
    提供异步的事件发布-订阅机制，支持同步和异步回调。
    """
    
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = defaultdict(list)
        self._once_listeners: Dict[str, List[Callable]] = defaultdict(list)
        self._lock = threading.RLock()
        self._event_history: List[Event] = []
        self._max_history = 1000
    
    def on(self, event_type: str, callback: Callable) -> None:
        """
        订阅事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        with self._lock:
            self._listeners[event_type].append(callback)
    
    def once(self, event_type: str, callback: Callable) -> None:
        """
        订阅一次性事件
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        with self._lock:
            self._once_listeners[event_type].append(callback)
    
    def off(self, event_type: str, callback: Callable = None) -> None:
        """
        取消订阅
        
        Args:
            event_type: 事件类型
            callback: 回调函数，如果为None则取消该类型所有订阅
        """
        with self._lock:
            if callback is None:
                self._listeners.pop(event_type, None)
                self._once_listeners.pop(event_type, None)
            else:
                if callback in self._listeners.get(event_type, []):
                    self._listeners[event_type].remove(callback)
                if callback in self._once_listeners.get(event_type, []):
                    self._once_listeners[event_type].remove(callback)
    
    async def emit(self, event_type: str, data: Any = None, source: str = "") -> None:
        """
        发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件源
        """
        event = Event(type=event_type, data=data, source=source)
        
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
        
        listeners = self._listeners.get(event_type, []).copy()
        once_listeners = self._once_listeners.pop(event_type, []).copy()
        
        for callback in listeners + once_listeners:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                print(f"[EventBus] Error in callback for {event_type}: {e}")
    
    def emit_sync(self, event_type: str, data: Any = None, source: str = "") -> None:
        """
        同步发布事件
        
        Args:
            event_type: 事件类型
            data: 事件数据
            source: 事件源
        """
        event = Event(type=event_type, data=data, source=source)
        
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)
        
        listeners = self._listeners.get(event_type, []).copy()
        once_listeners = self._once_listeners.pop(event_type, []).copy()
        
        for callback in listeners + once_listeners:
            try:
                callback(event)
            except Exception as e:
                print(f"[EventBus] Error in callback for {event_type}: {e}")
    
    def get_history(self, event_type: str = None, limit: int = 100) -> List[Event]:
        """
        获取事件历史
        
        Args:
            event_type: 事件类型过滤
            limit: 返回数量限制
            
        Returns:
            事件列表
        """
        with self._lock:
            if event_type:
                return [e for e in self._event_history if e.type == event_type][-limit:]
            return self._event_history[-limit:]
    
    def clear_history(self) -> None:
        """清空事件历史"""
        with self._lock:
            self._event_history.clear()
    
    def get_listener_count(self, event_type: str = None) -> int:
        """
        获取监听器数量
        
        Args:
            event_type: 事件类型
            
        Returns:
            监听器数量
        """
        with self._lock:
            if event_type:
                return len(self._listeners.get(event_type, []))
            return sum(len(v) for v in self._listeners.values())


class EventType:
    """事件类型常量"""
    TASK_SUBMITTED = "task.submitted"
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    AGENT_REGISTERED = "agent.registered"
    AGENT_UNREGISTERED = "agent.unregistered"
    AGENT_STATUS_CHANGED = "agent.status_changed"
    TOOL_EXECUTED = "tool.executed"
    TOOL_ERROR = "tool.error"
    MEMORY_UPDATED = "memory.updated"
    REFLCTION_COMPLETED = "reflection.completed"
    CRITIC_EVALUATED = "critic.evaluated"
    POLICY_UPDATED = "policy.updated"

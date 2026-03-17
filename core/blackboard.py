"""
Blackboard - 黑板系统

提供多Agent之间的共享数据存储和通信机制。
"""

import threading
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json


@dataclass
class BlackboardEntry:
    """黑板条目"""
    key: str
    value: Any
    author: str
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: Optional[int] = None
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        elapsed = (datetime.now() - self.timestamp).total_seconds()
        return elapsed > self.ttl


class Blackboard:
    """
    黑板系统
    
    提供线程安全的键值存储，支持消息广播和事件通知。
    """
    
    def __init__(self, max_size: int = 10000):
        self._data: Dict[str, Any] = {}
        self._entries: Dict[str, BlackboardEntry] = {}
        self._locks: Dict[str, threading.RLock] = defaultdict(threading.RLock)
        self._max_size = max_size
        self._global_lock = threading.RLock()
        self._subscribers: Dict[str, List[callable]] = defaultdict(list)
        self._history: List[Dict] = []
        self._max_history = 5000
    
    def read(self, key: str, default: Any = None) -> Any:
        """
        读取数据
        
        Args:
            key: 键
            default: 默认值
            
        Returns:
            值
        """
        with self._global_lock:
            entry = self._entries.get(key)
            if entry and not entry.is_expired():
                return self._data.get(key, default)
            return self._data.get(key, default)
    
    def write(self, key: str, value: Any, author: str = "system", ttl: Optional[int] = None) -> None:
        """
        写入数据
        
        Args:
            key: 键
            value: 值
            author: 作者
            ttl: 生存时间（秒）
        """
        with self._global_lock:
            if len(self._data) >= self._max_size:
                self._evict_oldest()
            
            self._data[key] = value
            self._entries[key] = BlackboardEntry(
                key=key,
                value=value,
                author=author,
                ttl=ttl
            )
            
            self._history.append({
                "action": "write",
                "key": key,
                "author": author,
                "timestamp": datetime.now().isoformat()
            })
            if len(self._history) > self._max_history:
                self._history.pop(0)
    
    def delete(self, key: str, author: str = "system") -> bool:
        """
        删除数据
        
        Args:
            key: 键
            author: 作者
            
        Returns:
            是否成功
        """
        with self._global_lock:
            if key in self._data:
                del self._data[key]
                self._entries.pop(key, None)
                
                self._history.append({
                    "action": "delete",
                    "key": key,
                    "author": author,
                    "timestamp": datetime.now().isoformat()
                })
                return True
            return False
    
    def exists(self, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 键
            
        Returns:
            是否存在
        """
        with self._global_lock:
            entry = self._entries.get(key)
            if entry:
                if entry.is_expired():
                    self.delete(key)
                    return False
                return True
            return key in self._data
    
    def get_keys(self, pattern: str = None) -> List[str]:
        """
        获取所有键
        
        Args:
            pattern: 匹配模式
            
        Returns:
            键列表
        """
        with self._global_lock:
            keys = list(self._data.keys())
            if pattern:
                import fnmatch
                keys = [k for k in keys if fnmatch.fnmatch(k, pattern)]
            return keys
    
    def subscribe(self, key: str, callback: callable) -> None:
        """
        订阅键变化
        
        Args:
            key: 键
            callback: 回调函数
        """
        with self._global_lock:
            self._subscribers[key].append(callback)
    
    def unsubscribe(self, key: str, callback: callable = None) -> None:
        """
        取消订阅
        
        Args:
            key: 键
            callback: 回调函数
        """
        with self._global_lock:
            if callback is None:
                self._subscribers.pop(key, None)
            else:
                if callback in self._subscribers.get(key, []):
                    self._subscribers[key].remove(callback)
    
    def _notify_subscribers(self, key: str, value: Any) -> None:
        """通知订阅者"""
        for callback in self._subscribers.get(key, []):
            try:
                callback(key, value)
            except Exception as e:
                print(f"[Blackboard] Notify error: {e}")
    
    def _evict_oldest(self) -> None:
        """驱逐最旧的条目"""
        if not self._entries:
            return
        
        oldest_key = min(
            self._entries.keys(),
            key=lambda k: self._entries[k].timestamp
        )
        self.delete(oldest_key)
    
    def get_task_result(self, task_id: str) -> Optional[Any]:
        """
        获取任务结果
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务结果
        """
        return self.read(f"task_result:{task_id}")
    
    def write_result(self, task_id: str, result: Any, agent_id: str = "system") -> None:
        """
        写入任务结果
        
        Args:
            task_id: 任务ID
            result: 结果
            agent_id: Agent ID
        """
        self.write(f"task_result:{task_id}", result, author=agent_id)
    
    def get_agent_state(self, agent_id: str) -> Dict[str, Any]:
        """
        获取Agent状态
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent状态
        """
        return self.read(f"agent_state:{agent_id}", {})
    
    def update_agent_state(self, agent_id: str, state: Dict[str, Any]) -> None:
        """
        更新Agent状态
        
        Args:
            agent_id: Agent ID
            state: 状态
        """
        current = self.get_agent_state(agent_id)
        current.update(state)
        self.write(f"agent_state:{agent_id}", current, author=agent_id)
    
    def get_history(self, limit: int = 100) -> List[Dict]:
        """
        获取操作历史
        
        Args:
            limit: 数量限制
            
        Returns:
            历史记录
        """
        with self._global_lock:
            return self._history[-limit:]
    
    def clear(self) -> None:
        """清空黑板"""
        with self._global_lock:
            self._data.clear()
            self._entries.clear()
            self._history.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典
        
        Returns:
            字典表示
        """
        with self._global_lock:
            return dict(self._data)
    
    def __len__(self) -> int:
        """获取条目数量"""
        with self._global_lock:
            return len(self._data)
    
    def __contains__(self, key: str) -> bool:
        """检查键是否存在"""
        return self.exists(key)

"""
WorkingMemory - 工作记忆

提供短期数据存储，用于Agent执行过程中的临时数据缓存。
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import OrderedDict
import threading


@dataclass
class MemoryItem:
    """记忆条目"""
    key: str
    value: Any
    timestamp: datetime = field(default_factory=datetime.now)
    importance: int = 3
    access_count: int = 0
    
    def access(self) -> Any:
        """访问记忆并返回"""
        self.access_count += 1
        return self.value


class WorkingMemory:
    """
    工作记忆
    
    提供线程安全的短期数据存储，使用LRU策略管理内存。
    """
    
    def __init__(self, max_size: int = 100):
        self._data: OrderedDict[str, MemoryItem] = OrderedDict()
        self._max_size = max_size
        self._lock = threading.RLock()
    
    def set(self, key: str, value: Any, importance: int = 3) -> None:
        """
        设置记忆
        
        Args:
            key: 键
            value: 值
            importance: 重要性 (1-5)
        """
        with self._lock:
            if key in self._data:
                del self._data[key]
            elif len(self._data) >= self._max_size:
                self._evict_lru()
            
            self._data[key] = MemoryItem(
                key=key,
                value=value,
                importance=importance
            )
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取记忆
        
        Args:
            key: 键
            default: 默认值
            
        Returns:
            值
        """
        with self._lock:
            if key in self._data:
                item = self._data[key]
                self._data.move_to_end(key)
                return item.access()
            return default
    
    def delete(self, key: str) -> bool:
        """
        删除记忆
        
        Args:
            key: 键
            
        Returns:
            是否成功
        """
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False
    
    def contains(self, key: str) -> bool:
        """
        检查键是否存在
        
        Args:
            key: 键
            
        Returns:
            是否存在
        """
        with self._lock:
            return key in self._data
    
    def clear(self) -> None:
        """清空记忆"""
        with self._lock:
            self._data.clear()
    
    def keys(self) -> List[str]:
        """获取所有键"""
        with self._lock:
            return list(self._data.keys())
    
    def values(self) -> List[Any]:
        """获取所有值"""
        with self._lock:
            return [item.value for item in self._data.values()]
    
    def items(self) -> List[tuple]:
        """获取所有键值对"""
        with self._lock:
            return [(k, v.value) for k, v in self._data.items()]
    
    def get_recent(self, count: int = 10) -> List[Any]:
        """
        获取最近N条记忆
        
        Args:
            count: 数量
            
        Returns:
            记忆列表
        """
        with self._lock:
            return [item.value for item in list(self._data.values())[-count:]]
    
    def get_by_importance(self, min_importance: int = 3) -> List[Any]:
        """
        获取重要记忆
        
        Args:
            min_importance: 最小重要性
            
        Returns:
            记忆列表
        """
        with self._lock:
            return [
                item.value 
                for item in self._data.values() 
                if item.importance >= min_importance
            ]
    
    def _evict_lru(self) -> None:
        """驱逐最旧的记忆"""
        if not self._data:
            return
        self._data.popitem(last=False)
    
    def __len__(self) -> int:
        """获取记忆数量"""
        with self._lock:
            return len(self._data)
    
    def __contains__(self, key: str) -> bool:
        """检查键是否存在"""
        return self.contains(key)
    
    def __getitem__(self, key: str) -> Any:
        """获取记忆"""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """设置记忆"""
        self.set(key, value)

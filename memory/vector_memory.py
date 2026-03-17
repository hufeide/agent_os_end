"""
VectorMemory - 向量记忆

提供基于向量相似度的长期记忆存储和检索。
"""

from typing import Any, Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import threading
import uuid


@dataclass
class VectorEntry:
    """向量条目"""
    id: str
    content: str
    vector: np.ndarray
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class VectorMemory:
    """
    向量记忆
    
    使用简单的向量表示实现语义记忆存储和检索。
    真实生产环境可替换为ChromaDB、Milvus等向量数据库。
    """
    
    def __init__(self, dimension: int = 1536):
        self._dimension = dimension
        self._vectors: List[VectorEntry] = []
        self._lock = threading.RLock()
    
    def _text_to_vector(self, text: str) -> np.ndarray:
        """
        将文本转换为向量
        
        简化实现：使用词频向量化
        真实环境应使用embedding模型
        """
        words = text.lower().split()
        vector = np.zeros(self._dimension)
        
        for i, word in enumerate(words):
            hash_val = hash(word) % self._dimension
            vector[hash_val] += 1
        
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        
        return vector
    
    def add(self, content: str, metadata: Dict[str, Any] = None) -> str:
        """
        添加记忆
        
        Args:
            content: 内容
            metadata: 元数据
            
        Returns:
            记忆ID
        """
        with self._lock:
            entry_id = str(uuid.uuid4())
            vector = self._text_to_vector(content)
            
            entry = VectorEntry(
                id=entry_id,
                content=content,
                vector=vector,
                metadata=metadata or {}
            )
            
            self._vectors.append(entry)
            return entry_id
    
    def search(self, query: str, top_k: int = 1) -> List[Tuple[VectorEntry, float]]:
        """
        搜索记忆
        
        Args:
            query: 查询文本
            top_k: 返回数量
            
        Returns:
            (记忆条目, 相似度)列表
        """
        with self._lock:
            if not self._vectors:
                return []
            
            query_vector = self._text_to_vector(query)
            
            similarities = []
            for entry in self._vectors:
                similarity = np.dot(query_vector, entry.vector)
                similarities.append((entry, similarity))
            
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_k]
    
    def get(self, entry_id: str) -> Optional[VectorEntry]:
        """
        获取记忆
        
        Args:
            entry_id: 记忆ID
            
        Returns:
            记忆条目
        """
        with self._lock:
            for entry in self._vectors:
                if entry.id == entry_id:
                    return entry
            return None
    
    def delete(self, entry_id: str) -> bool:
        """
        删除记忆
        
        Args:
            entry_id: 记忆ID
            
        Returns:
            是否成功
        """
        with self._lock:
            for i, entry in enumerate(self._vectors):
                if entry.id == entry_id:
                    self._vectors.pop(i)
                    return True
            return False
    
    def clear(self) -> None:
        """清空记忆"""
        with self._lock:
            self._vectors.clear()
    
    def count(self) -> int:
        """获取记忆数量"""
        with self._lock:
            return len(self._vectors)
    
    def get_all(self) -> List[VectorEntry]:
        """获取所有记忆"""
        with self._lock:
            return self._vectors.copy()

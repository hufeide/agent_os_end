"""
Skill - 技能基类

定义所有技能的基类。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class SkillResult:
    """技能执行结果"""
    success: bool
    result: Any = None
    error: str = ""
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Skill(ABC):
    """
    技能基类
    
    所有技能的基类，定义技能的基本接口。
    """
    
    name: str = ""
    description: str = ""
    tools: List[str] = []
    category: str = "general"
    
    def __init__(self):
        self._id = str(uuid.uuid4())
        self._call_count = 0
    
    @abstractmethod
    async def execute(self, input: Any = None, **kwargs) -> SkillResult:
        """
        执行技能
        
        Args:
            input: 输入数据
            **kwargs: 其他参数
            
        Returns:
            技能执行结果
        """
        raise NotImplementedError
    
    def get_info(self) -> Dict[str, Any]:
        """获取技能信息"""
        return {
            "id": self._id,
            "name": self.name,
            "description": self.description,
            "tools": self.tools,
            "category": self.category,
            "call_count": self._call_count
        }
    
    def reset_stats(self) -> None:
        """重置统计"""
        self._call_count = 0

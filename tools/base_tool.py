"""
BaseTool - 基础工具

定义所有工具的基类。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    result: Any = None
    error: str = ""
    execution_time: float = 0.0
    tool_name: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution_time": self.execution_time,
            "tool_name": self.tool_name,
            "metadata": self.metadata
        }


class BaseTool(ABC):
    """
    基础工具类
    
    所有工具的基类，定义工具的基本接口。
    """
    
    name: str = ""
    description: str = ""
    category: str = "general"
    parameters: Dict[str, Any] = {}
    
    def __init__(self):
        self._id = str(uuid.uuid4())
        self._call_count = 0
        self._total_time = 0.0
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """
        执行工具
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        raise NotImplementedError
    
    async def execute_with_timeout(self, timeout: float = 30, **kwargs) -> ToolResult:
        """
        带超时的执行
        
        Args:
            timeout: 超时时间
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        import asyncio
        try:
            result = await asyncio.wait_for(self.execute(**kwargs), timeout=timeout)
            return result
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                error=f"Tool execution timeout after {timeout}s",
                tool_name=self.name
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                tool_name=self.name
            )
    
    def get_info(self) -> Dict[str, Any]:
        """获取工具信息"""
        return {
            "id": self._id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": self.parameters,
            "call_count": self._call_count,
            "total_time": self._total_time
        }
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._call_count = 0
        self._total_time = 0.0

"""
ToolRegistry - 工具注册中心

管理所有可用工具的注册和获取。
"""

from typing import Dict, List, Optional, Any
from .base_tool import BaseTool
import threading


class ToolRegistry:
    """
    工具注册中心
    
    管理所有可用工具的注册、获取和调用。
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._lock = threading.RLock()
        self._categories: Dict[str, List[str]] = {}
    
    def register(self, tool: BaseTool) -> None:
        """
        注册工具
        
        Args:
            tool: 工具实例
        """
        with self._lock:
            self._tools[tool.name] = tool
            
            if tool.category not in self._categories:
                self._categories[tool.category] = []
            if tool.name not in self._categories[tool.category]:
                self._categories[tool.category].append(tool.name)
    
    def unregister(self, tool_name: str) -> bool:
        """
        注销工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            是否成功
        """
        with self._lock:
            if tool_name in self._tools:
                tool = self._tools[tool_name]
                if tool.category in self._categories:
                    self._categories[tool.category].remove(tool_name)
                del self._tools[tool_name]
                return True
            return False
    
    def get(self, tool_name: str) -> Optional[BaseTool]:
        """
        获取工具
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具实例
        """
        with self._lock:
            return self._tools.get(tool_name)
    
    def get_all(self) -> List[BaseTool]:
        """
        获取所有工具
        
        Returns:
            工具列表
        """
        with self._lock:
            return list(self._tools.values())
    
    def list_tools(self) -> List[str]:
        """
        列出所有工具名称
        
        Returns:
            工具名称列表
        """
        with self._lock:
            return list(self._tools.keys())
    
    def list_by_category(self, category: str) -> List[str]:
        """
        按类别列出工具
        
        Args:
            category: 类别
            
        Returns:
            工具名称列表
        """
        with self._lock:
            return self._categories.get(category, [])
    
    def get_categories(self) -> List[str]:
        """
        获取所有类别
        
        Returns:
            类别列表
        """
        with self._lock:
            return list(self._categories.keys())
    
    async def execute(self, tool_name: str, **kwargs) -> Any:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        tool = self.get(tool_name)
        if not tool:
            return {"success": False, "error": f"Tool {tool_name} not found"}
        
        return await tool.execute(**kwargs)
    
    def get_tool_info(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取工具信息
        
        Args:
            tool_name: 工具名称
            
        Returns:
            工具信息
        """
        tool = self.get(tool_name)
        if tool:
            return tool.get_info()
        return None
    
    def clear(self) -> None:
        """清空注册表"""
        with self._lock:
            self._tools.clear()
            self._categories.clear()
    
    def __len__(self) -> int:
        """获取工具数量"""
        with self._lock:
            return len(self._tools)
    
    def __contains__(self, tool_name: str) -> bool:
        """检查工具是否存在"""
        return tool_name in self._tools

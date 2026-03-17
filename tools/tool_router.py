"""
ToolRouter - 工具路由器

根据任务需求自动选择和路由到合适的工具。
"""

from typing import Optional, List, Dict, Any
from .base_tool import BaseTool
from .tool_registry import ToolRegistry


class ToolRouter:
    """
    工具路由器
    
    根据任务类型和需求自动选择合适的工具。
    """
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self._routing_rules: Dict[str, str] = {}
        self._initialize_default_rules()
    
    def _initialize_default_rules(self) -> None:
        """初始化默认路由规则"""
        self._routing_rules = {
            "search": "search",
            "web": "web",
            "code": "code",
            "write": "file",
            "read": "file",
            "file": "file",
            "analysis": "analysis",
            "data": "analysis"
        }
    
    def add_rule(self, keyword: str, tool_name: str) -> None:
        """
        添加路由规则
        
        Args:
            keyword: 关键词
            tool_name: 工具名称
        """
        self._routing_rules[keyword] = tool_name
    
    def remove_rule(self, keyword: str) -> bool:
        """
        移除路由规则
        
        Args:
            keyword: 关键词
            
        Returns:
            是否成功
        """
        if keyword in self._routing_rules:
            del self._routing_rules[keyword]
            return True
        return False
    
    def route(self, tool_name: str) -> Optional[BaseTool]:
        """
        路由到工具
        
        Args:
            tool_name: 工具名称或关键词
            
        Returns:
            工具实例
        """
        tool = self.registry.get(tool_name)
        if tool:
            return tool
        
        tool_name_lower = tool_name.lower()
        for keyword, target_tool in self._routing_rules.items():
            if keyword in tool_name_lower:
                return self.registry.get(target_tool)
        
        return None
    
    def route_by_task(self, task_description: str) -> Optional[BaseTool]:
        """
        根据任务描述路由
        
        Args:
            task_description: 任务描述
            
        Returns:
            工具实例
        """
        task_lower = task_description.lower()
        
        for keyword, target_tool in self._routing_rules.items():
            if keyword in task_lower:
                tool = self.registry.get(target_tool)
                if tool:
                    return tool
        
        return None
    
    def get_available_tools(self) -> List[str]:
        """获取所有可用工具"""
        return self.registry.list_tools()
    
    def auto_route(self, task_description: str) -> List[BaseTool]:
        """
        自动路由多个工具
        
        Args:
            task_description: 任务描述
            
        Returns:
            工具列表
        """
        tools = []
        task_lower = task_description.lower()
        
        for keyword, target_tool in self._routing_rules.items():
            if keyword in task_lower:
                tool = self.registry.get(target_tool)
                if tool and tool not in tools:
                    tools.append(tool)
        
        return tools

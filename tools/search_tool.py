"""
SearchTool - 搜索工具

提供网络搜索功能。
"""

from .base_tool import BaseTool, ToolResult
import asyncio
from typing import List, Dict, Any


class SearchTool(BaseTool):
    """搜索工具"""
    
    name = "search"
    description = "Search the web for information"
    category = "search"
    
    def __init__(self):
        super().__init__()
        self.parameters = {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "description": "Maximum number of results", "default": 5}
        }
    
    async def execute(self, query: str, max_results: int = 5, **kwargs) -> ToolResult:
        """执行搜索"""
        import time
        start_time = time.time()
        
        try:
            results = await self._search(query, max_results)
            
            return ToolResult(
                success=True,
                result={
                    "query": query,
                    "results": results,
                    "count": len(results)
                },
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
    
    async def _search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """执行实际搜索"""
        import requests
        
        try:
            response = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get("RelatedTopics", [])[:max_results]:
                    if "Text" in item:
                        results.append({
                            "title": item.get("Text", "").split(" - ")[0] if " - " in item.get("Text", "") else item.get("Text", ""),
                            "url": item.get("URL", ""),
                            "snippet": item.get("Text", "")
                        })
                
                return results
        except Exception as e:
            print(f"[SearchTool] Search error: {e}")
        
        return []

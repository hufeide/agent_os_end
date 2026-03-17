"""
WebTool - 网页抓取工具

提供网页内容抓取功能。
"""

from .base_tool import BaseTool, ToolResult
import requests
from bs4 import BeautifulSoup
import time
from typing import Optional


class WebTool(BaseTool):
    """网页抓取工具"""
    
    name = "web"
    description = "Fetch content from a URL"
    category = "web"
    
    def __init__(self):
        super().__init__()
        self.parameters = {
            "url": {"type": "string", "description": "URL to fetch"},
            "max_length": {"type": "integer", "description": "Maximum content length", "default": 5000}
        }
    
    async def execute(self, url: str, max_length: int = 5000, **kwargs) -> ToolResult:
        """执行网页抓取"""
        start_time = time.time()
        
        try:
            content = await self._fetch_url(url, max_length)
            
            return ToolResult(
                success=True,
                result={
                    "url": url,
                    "content": content,
                    "length": len(content)
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
    
    async def _fetch_url(self, url: str, max_length: int) -> str:
        """抓取网页内容"""
        import asyncio
        
        loop = asyncio.get_event_loop()
        
        return await loop.run_in_executor(
            None,
            self._sync_fetch,
            url,
            max_length
        )
    
    def _sync_fetch(self, url: str, max_length: int) -> str:
        """同步抓取网页"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text(separator="\n", strip=True)
        lines = [line for line in text.split("\n") if line.strip()]
        
        content = "\n".join(lines[:100])
        
        if len(content) > max_length:
            content = content[:max_length] + "..."
        
        return content

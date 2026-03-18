"""
SearchTool - 搜索工具

提供网络搜索功能（支持多源搜索）。
"""

from .base_tool import BaseTool, ToolResult
import asyncio
from typing import List, Dict, Any, Optional


class SearchTool(BaseTool):
    """搜索工具"""
    
    name = "search"
    description = "Search the web for information"
    category = "search"
    
    def __init__(self, llm: Optional[Any] = None):
        super().__init__()
        self.llm = llm
        self.parameters = {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "description": "Maximum number of results", "default": 5}
        }
    
    async def execute(self, query: str, max_results: int = 5, **kwargs) -> ToolResult:
        """执行搜索"""
        import time
        start_time = time.time()
        
        try:
            results = await self._search_bing_serp(query, max_results)
            
            if results:
                return ToolResult(
                    success=True,
                    result={
                        "query": query,
                        "results": results,
                        "count": len(results),
                        "source": "bing"
                    },
                    execution_time=time.time() - start_time,
                    tool_name=self.name
                )
            
            results = await self._search_google_serp(query, max_results)
            
            if results:
                return ToolResult(
                    success=True,
                    result={
                        "query": query,
                        "results": results,
                        "count": len(results),
                        "source": "google"
                    },
                    execution_time=time.time() - start_time,
                    tool_name=self.name
                )
            
            return ToolResult(
                success=True,
                result={
                    "query": query,
                    "results": [],
                    "count": 0,
                    "message": "All search sources failed. Try using web tool directly with a URL."
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
    
    async def _search_bing_serp(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """通过 Bing SERP 搜索"""
        import requests
        from bs4 import BeautifulSoup
        
        try:
            url = f"https://www.bing.com/search?q={requests.utils.quote(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5"
            }
            
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            for item in soup.select('li.b_algo')[:max_results]:
                title_elem = item.select_one('h2 a')
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                url = title_elem.get('href', '')
                
                desc_elem = item.select_one('p')
                snippet = desc_elem.get_text(strip=True) if desc_elem else ""
                
                if title and url:
                    results.append({
                        "title": title[:200],
                        "url": url,
                        "snippet": snippet[:300] if snippet else ""
                    })
            
            return results
        except Exception as e:
            print(f"[SearchTool] Bing SERP failed: {e}")
            return []
    
    async def _search_google_serp(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """通过 Google SERP 搜索"""
        import requests
        from bs4 import BeautifulSoup
        
        try:
            url = f"https://www.google.com/search?q={requests.utils.quote(query)}&num={max_results}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5"
            }
            
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []
            
            for item in soup.select('div.g')[:max_results]:
                title_elem = item.select_one('h3')
                link_elem = item.select_one('div.yuRUbf a')
                
                if not title_elem or not link_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                url = link_elem.get('href', '')
                
                desc_elem = item.select_one('div.VwiC3b')
                snippet = desc_elem.get_text(strip=True) if desc_elem else ""
                
                if title and url:
                    results.append({
                        "title": title[:200],
                        "url": url,
                        "snippet": snippet[:300] if snippet else ""
                    })
            
            return results
        except Exception as e:
            print(f"[SearchTool] Google SERP failed: {e}")
            return []

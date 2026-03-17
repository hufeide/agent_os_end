"""
FileTool - 文件处理工具

提供文件读写功能。
"""

from .base_tool import BaseTool, ToolResult
import os
import time
from pathlib import Path
from typing import Optional


class FileTool(BaseTool):
    """文件处理工具"""
    
    name = "file"
    description = "Read or write files"
    category = "file"
    
    def __init__(self, base_dir: str = "./agent_workspace"):
        super().__init__()
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.parameters = {
            "operation": {"type": "string", "description": "Operation: read, write, list, delete"},
            "path": {"type": "string", "description": "File path"},
            "content": {"type": "string", "description": "Content to write"}
        }
    
    async def execute(
        self,
        operation: str,
        path: str = "",
        content: str = "",
        **kwargs
    ) -> ToolResult:
        """执行文件操作"""
        start_time = time.time()
        
        try:
            if operation == "read":
                result = await self._read_file(path)
            elif operation == "write":
                result = await self._write_file(path, content)
            elif operation == "list":
                result = await self._list_files(path)
            elif operation == "delete":
                result = await self._delete_file(path)
            else:
                result = {"error": f"Unknown operation: {operation}"}
            
            return ToolResult(
                success="error" not in result,
                result=result,
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
    
    def _resolve_path(self, path: str) -> Path:
        """解析文件路径"""
        if not path:
            return self.base_dir
        
        p = Path(path)
        if p.is_absolute():
            return p
        
        return self.base_dir / p
    
    async def _read_file(self, path: str) -> dict:
        """读取文件"""
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            return {"error": f"File not found: {path}"}
        
        if not file_path.is_file():
            return {"error": f"Not a file: {path}"}
        
        content = file_path.read_text(encoding="utf-8")
        
        return {
            "operation": "read",
            "path": str(file_path),
            "content": content,
            "length": len(content)
        }
    
    async def _write_file(self, path: str, content: str) -> dict:
        """写入文件"""
        file_path = self._resolve_path(path)
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        
        return {
            "operation": "write",
            "path": str(file_path),
            "bytes_written": len(content)
        }
    
    async def _list_files(self, path: str = "") -> dict:
        """列出文件"""
        dir_path = self._resolve_path(path)
        
        if not dir_path.exists():
            return {"error": f"Directory not found: {path}"}
        
        if not dir_path.is_dir():
            return {"error": f"Not a directory: {path}"}
        
        files = []
        for item in dir_path.iterdir():
            files.append({
                "name": item.name,
                "type": "directory" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else 0
            })
        
        return {
            "operation": "list",
            "path": str(dir_path),
            "files": files,
            "count": len(files)
        }
    
    async def _delete_file(self, path: str) -> dict:
        """删除文件"""
        file_path = self._resolve_path(path)
        
        if not file_path.exists():
            return {"error": f"File not found: {path}"}
        
        if file_path.is_file():
            file_path.unlink()
        elif file_path.is_dir():
            import shutil
            shutil.rmtree(file_path)
        
        return {
            "operation": "delete",
            "path": str(file_path),
            "success": True
        }

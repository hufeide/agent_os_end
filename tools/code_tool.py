"""
CodeTool - 代码执行工具

提供Python代码执行功能。
"""

from .base_tool import BaseTool, ToolResult
import subprocess
import sys
import time


class CodeTool(BaseTool):
    """代码执行工具"""
    
    name = "code"
    description = "Execute Python code"
    category = "code"
    
    def __init__(self):
        super().__init__()
        self.parameters = {
            "code": {"type": "string", "description": "Python code to execute"},
            "language": {"type": "string", "description": "Programming language", "default": "python"}
        }
    
    async def execute(self, code: str, language: str = "python", **kwargs) -> ToolResult:
        """执行代码"""
        start_time = time.time()
        
        if language.lower() != "python":
            return ToolResult(
                success=False,
                error=f"Unsupported language: {language}",
                execution_time=time.time() - start_time,
                tool_name=self.name
            )
        
        try:
            output = await self._execute_code(code)
            
            return ToolResult(
                success=True,
                result={
                    "code": code,
                    "output": output,
                    "status": "executed"
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
    
    async def _execute_code(self, code: str) -> str:
        """执行Python代码"""
        loop = asyncio.get_event_loop()
        
        result = await loop.run_in_executor(
            None,
            self._sync_execute,
            code
        )
        
        return result
    
    def _sync_execute(self, code: str) -> str:
        """同步执行代码"""
        try:
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout if result.stdout else "Code executed successfully, no output"
            return f"Error: {result.stderr}"
        except subprocess.TimeoutExpired:
            return "Error: Code execution timeout"
        except Exception as e:
            return f"Error: {str(e)}"

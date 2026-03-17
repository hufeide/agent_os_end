"""
Critic - 批评评估模块

对Agent执行进行评估和批评。
"""

from typing import Any, Dict, List, Optional
import json


class Critic:
    """
    批评评估模块
    
    对Agent执行进行评估和批评，提供改进建议。
    """
    
    def __init__(self, llm: Optional[Any] = None):
        self.llm = llm
    
    async def evaluate(
        self,
        task: Any,
        result: Any,
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        评估执行结果
        
        Args:
            task: 任务
            result: 执行结果
            context: 上下文
            
        Returns:
            评估结果
        """
        if self.llm:
            return await self._llm_evaluate(task, result, context)
        
        return self._default_evaluate(task, result, context)
    
    async def _llm_evaluate(
        self,
        task: Any,
        result: Any,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """使用LLM进行评估"""
        task_desc = task.description if hasattr(task, "description") else str(task)
        
        prompt = f"""Task: {task_desc}

Result: {result}

Context: {context or {}}

Please evaluate this execution and provide feedback in JSON:
{{
    "score": 0-10,
    "is_success": true/false,
    "feedback": "Brief feedback",
    "improvements": ["suggestion1", "suggestion2"]
}}

Only return JSON."""
        
        try:
            if callable(self.llm):
                response = self.llm(prompt)
            else:
                response = await self.llm(prompt)
            
            return self._parse_evaluation(response)
        except Exception as e:
            return self._default_evaluate(task, result, context)
    
    def _default_evaluate(
        self,
        task: Any,
        result: Any,
        context: Optional[Dict]
    ) -> Dict[str, Any]:
        """默认评估"""
        is_success = result is not None
        
        score = 8.0 if is_success else 3.0
        
        if isinstance(result, dict):
            if "error" in result:
                is_success = False
                score = 2.0
        
        return {
            "score": score,
            "is_success": is_success,
            "feedback": "Task completed successfully" if is_success else "Task failed",
            "improvements": [] if is_success else ["Review the error and retry"]
        }
    
    def _parse_evaluation(self, response: str) -> Dict[str, Any]:
        """解析评估结果"""
        try:
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            data = json.loads(response.strip())
            
            return {
                "score": data.get("score", 5.0),
                "is_success": data.get("is_success", False),
                "feedback": data.get("feedback", ""),
                "improvements": data.get("improvements", [])
            }
        except:
            return self._default_evaluate(None, None, None)
    
    async def critique_step(
        self,
        step: int,
        thought: str,
        action: str,
        result: Any
    ) -> Dict[str, Any]:
        """
        批评单步执行
        
        Args:
            step: 步骤
            thought: 思考
            action: 行动
            result: 结果
            
        Returns:
            批评结果
        """
        critique = {
            "step": step,
            "thought": thought,
            "action": action,
            "result_valid": result is not None,
            "suggestion": ""
        }
        
        if result is None:
            critique["suggestion"] = "Action produced no result, consider trying a different approach"
        elif isinstance(result, str) and "error" in result.lower():
            critique["suggestion"] = "Action failed with error, review and retry"
        
        return critique
    
    def should_retry(
        self,
        evaluation: Dict[str, Any],
        max_retries: int = 3
    ) -> bool:
        """
        判断是否应该重试
        
        Args:
            evaluation: 评估结果
            max_retries: 最大重试次数
            
        Returns:
            是否应该重试
        """
        if not evaluation.get("is_success", True):
            return True
        
        score = evaluation.get("score", 10.0)
        if score < 5.0:
            return True
        
        return False

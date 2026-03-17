"""
Reflection - 反思模块

对执行结果进行反思和总结。
"""

from typing import Any, Dict, List, Optional
import json


class Reflection:
    """
    反思模块
    
    对执行结果进行反思和总结，提炼经验教训。
    """
    
    def __init__(self, llm: Optional[Any] = None):
        self.llm = llm
    
    async def reflect(
        self,
        history: List[Any],
        task_description: str = ""
    ) -> str:
        """
        反思执行历史
        
        Args:
            history: 执行历史
            task_description: 任务描述
            
        Returns:
            反思总结
        """
        if self.llm:
            return await self._llm_reflect(history, task_description)
        
        return self._default_reflect(history, task_description)
    
    async def _llm_reflect(
        self,
        history: List[Any],
        task_description: str
    ) -> str:
        """使用LLM进行反思"""
        history_text = self._format_history(history)
        
        prompt = f"""Task: {task_description}

Execution history:
{history_text}

Please reflect on this execution and provide insights:
1. What went well?
2. What could be improved?
3. What lessons were learned?

Provide a brief summary."""
        
        try:
            if callable(self.llm):
                response = self.llm(prompt)
            else:
                response = await self.llm(prompt)
            
            return response
        except Exception as e:
            return self._default_reflect(history, task_description)
    
    def _default_reflect(
        self,
        history: List[Any],
        task_description: str
    ) -> str:
        """默认反思"""
        steps = len(history)
        
        summary = f"Task '{task_description}' completed with {steps} steps.\n"
        
        if steps > 0:
            summary += "Actions taken:\n"
            for i, item in enumerate(history, 1):
                if isinstance(item, tuple):
                    thought, result = item
                    summary += f"  {i}. {thought.action}: {str(result)[:50]}...\n"
        
        return summary
    
    def _format_history(self, history: List[Any]) -> str:
        """格式化历史"""
        if not history:
            return "No history"
        
        text = ""
        for i, item in enumerate(history, 1):
            text += f"\nStep {i}: {item}"
        
        return text
    
    async def evaluate_success(
        self,
        result: Any,
        expected: Any = None
    ) -> Dict[str, Any]:
        """
        评估执行成功与否
        
        Args:
            result: 执行结果
            expected: 期望结果
            
        Returns:
            评估结果
        """
        if expected is None:
            return {
                "success": result is not None,
                "confidence": 0.5,
                "reasoning": "No expected result provided"
            }
        
        if isinstance(result, str) and isinstance(expected, str):
            similarity = self._calculate_similarity(result, expected)
            return {
                "success": similarity > 0.7,
                "confidence": similarity,
                "reasoning": f"Similarity: {similarity:.2f}"
            }
        
        return {
            "success": result == expected,
            "confidence": 1.0 if result == expected else 0.0,
            "reasoning": "Direct comparison"
        }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)

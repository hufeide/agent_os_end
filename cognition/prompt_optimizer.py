"""
PromptOptimizer - 提示词优化器

根据历史经验优化提示词。
"""

from typing import Any, Dict, List, Optional


class PromptOptimizer:
    """
    提示词优化器
    
    根据向量记忆中的历史经验优化提示词。
    """
    
    def __init__(self, vector_memory: Any = None):
        self.vector_memory = vector_memory
    
    def optimize(self, task: Any) -> str:
        """
        优化提示词
        
        Args:
            task: 任务对象
            
        Returns:
            优化后的提示词
        """
        if not self.vector_memory:
            return self._get_default_prompt(task)
        
        task_desc = task.description if hasattr(task, "description") else str(task)
        
        similar_prompts = self.vector_memory.search(task_desc, top_k=3)
        
        if similar_prompts:
            best_match = similar_prompts[0]
            if hasattr(best_match, "content"):
                return self._merge_prompts(task_desc, best_match.content)
        
        return self._get_default_prompt(task)
    
    def _get_default_prompt(self, task: Any) -> str:
        """获取默认提示词"""
        task_desc = task.description if hasattr(task, "description") else str(task)
        
        return f"""Task: {task_desc}

Please execute this task and return the result.

Requirements:
1. Actually execute the task, don't just describe steps
2. Produce concrete output
3. Return detailed execution results"""
    
    def _merge_prompts(self, current: str, historical: str) -> str:
        """合并提示词"""
        return f"""Task: {current}

Related experience:
{historical}

Please execute this task using your best judgment.

Requirements:
1. Actually execute the task
2. Produce concrete output
3. Return detailed execution results"""
    
    def learn_from_result(
        self,
        task: Any,
        result: Any,
        success: bool
    ) -> None:
        """
        从结果学习
        
        Args:
            task: 任务
            result: 结果
            success: 是否成功
        """
        if not self.vector_memory:
            return
        
        task_desc = task.description if hasattr(task, "description") else str(task)
        
        content = f"Task: {task_desc}\nResult: {result}\nSuccess: {success}"
        
        self.vector_memory.add(
            content=content,
            metadata={"success": success}
        )
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计"""
        if not self.vector_memory:
            return {"total_memories": 0}
        
        return {
            "total_memories": self.vector_memory.count()
        }

"""
SelfImprovingAgent - 自我改进Agent

具有自我学习和改进能力的Agent。
"""

from typing import Any, Dict, List, Optional
import time

from .worker_agent import WorkerAgent
from ..memory import TaskReplay
from ..cognition import PromptOptimizer, RLAgent


class SelfImprovingAgent:
    """
    自我改进Agent
    
    具有自我学习和改进能力的Agent，结合提示词优化和强化学习。
    """
    
    def __init__(
        self,
        worker_agent: WorkerAgent,
        task_replay: TaskReplay,
        prompt_optimizer: PromptOptimizer,
        rl_agent: RLAgent
    ):
        self.worker = worker_agent
        self.replay = task_replay
        self.optimizer = prompt_optimizer
        self.rl = rl_agent
        
        self._total_tasks = 0
        self._total_success = 0
    
    async def run(self, task: Any) -> Any:
        """
        运行任务
        
        Args:
            task: 任务对象
            
        Returns:
            执行结果
        """
        start_time = time.time()
        
        task_desc = task.description if hasattr(task, "description") else str(task)
        
        optimized_prompt = self.optimizer.optimize(task)
        
        if hasattr(task, "prompt"):
            original_prompt = task.prompt
            task.prompt = optimized_prompt
        
        result = await self.worker.run(task)
        
        reward = self.compute_reward(task, result)
        
        await self.rl.update_policy(task, reward)
        
        execution_time = time.time() - start_time
        steps = len(self.worker.react.get_history()) if hasattr(self.worker, "react") else 0
        
        self.replay.add(
            task_id=task.id if hasattr(task, "id") else "unknown",
            task_description=task_desc,
            result=result,
            reward=reward,
            prompt=optimized_prompt,
            execution_time=execution_time,
            steps=steps
        )
        
        self.optimizer.learn_from_result(task, result, reward >= 0.8)
        
        self._total_tasks += 1
        if reward >= 0.8:
            self._total_success += 1
        
        return result
    
    def compute_reward(self, task: Any, result: Any) -> float:
        """
        计算奖励
        
        Args:
            task: 任务
            result: 结果
            
        Returns:
            奖励值 (0-1)
        """
        if result is None:
            return 0.0
        
        if isinstance(result, dict):
            if "error" in result:
                return 0.1
            
            if "success" in result and result["success"]:
                return 1.0
        
        if isinstance(result, str):
            if "error" in result.lower():
                return 0.1
            
            if len(result) > 10:
                return 0.8
        
        return 0.5
    
    def should_retry(self, task: Any, result: Any) -> bool:
        """
        判断是否应该重试
        
        Args:
            task: 任务
            result: 结果
            
        Returns:
            是否重试
        """
        reward = self.compute_reward(task, result)
        
        return reward < 0.7
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = self._total_success / self._total_tasks if self._total_tasks > 0 else 0
        
        return {
            "total_tasks": self._total_tasks,
            "total_success": self._total_success,
            "success_rate": success_rate,
            "replay_size": self.replay.count(),
            "optimizer_stats": self.optimizer.get_optimization_stats(),
            "rl_stats": self.rl.get_statistics()
        }
    
    def get_best_prompt(self, task_description: str) -> Optional[str]:
        """
        获取最佳提示词
        
        Args:
            task_description: 任务描述
            
        Returns:
            最佳提示词
        """
        successful_records = self.replay.get_successful(min_reward=0.8)
        
        if not successful_records:
            return None
        
        for record in reversed(successful_records):
            if task_description[:50] in record.task_description[:50]:
                return record.prompt
        
        return None

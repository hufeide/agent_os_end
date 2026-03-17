"""
RLAgent - 强化学习Agent

实现策略更新和学习功能。
"""

from typing import Any, Dict, List, Optional
import random


class RLAgent:
    """
    强化学习Agent
    
    实现简单的策略更新和学习功能。
    """
    
    def __init__(self, learning_rate: float = 0.01):
        self.learning_rate = learning_rate
        self.policy: Dict[str, float] = {}
        self.reward_history: List[float] = []
    
    async def update_policy(
        self,
        task: Any,
        reward: float
    ) -> None:
        """
        更新策略
        
        Args:
            task: 任务
            reward: 奖励
        """
        task_desc = task.description if hasattr(task, "description") else str(task)
        
        task_key = task_desc[:50]
        
        if task_key not in self.policy:
            self.policy[task_key] = 0.5
        
        self.policy[task_key] += self.learning_rate * (reward - self.policy[task_key])
        
        self.reward_history.append(reward)
        
        if len(self.reward_history) > 100:
            self.reward_history.pop(0)
    
    def get_policy(self, task: Any) -> float:
        """
        获取策略
        
        Args:
            task: 任务
            
        Returns:
            策略值
        """
        task_desc = task.description if hasattr(task, "description") else str(task)
        task_key = task_desc[:50]
        
        return self.policy.get(task_key, 0.5)
    
    def should_explore(self, task: Any) -> bool:
        """
        判断是否应该探索
        
        Args:
            task: 任务
            
        Returns:
            是否探索
        """
        policy_value = self.get_policy(task)
        
        epsilon = 0.1
        
        return random.random() < epsilon
    
    def get_average_reward(self) -> float:
        """获取平均奖励"""
        if not self.reward_history:
            return 0.0
        return sum(self.reward_history) / len(self.reward_history)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "policy_size": len(self.policy),
            "average_reward": self.get_average_reward(),
            "total_updates": len(self.reward_history)
        }

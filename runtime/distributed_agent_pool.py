"""
DistributedAgentPool - 分布式Agent池

管理多个Agent节点的分布式调度。
"""

from typing import Any, Dict, List, Optional
import asyncio


class DistributedAgentPool:
    """
    分布式Agent池
    
    管理多个Agent节点，支持分布式任务执行。
    """
    
    def __init__(self, nodes: List[Any]):
        self.nodes = nodes
        self._counter = 0
    
    def add_node(self, node: Any) -> None:
        """
        添加节点
        
        Args:
            node: Agent节点
        """
        self.nodes.append(node)
    
    def remove_node(self, node_id: str) -> bool:
        """
        移除节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            是否成功
        """
        for i, node in enumerate(self.nodes):
            if hasattr(node, "node_id") and node.node_id == node_id:
                self.nodes.pop(i)
                return True
        return False
    
    async def execute_task(self, task: Any) -> Any:
        """
        执行任务
        
        Args:
            task: 任务
            
        Returns:
            执行结果
        """
        if not self.nodes:
            return {"error": "No nodes available"}
        
        self._counter += 1
        node = self.nodes[self._counter % len(self.nodes)]
        
        if hasattr(node, "execute_task"):
            return await node.execute_task(task)
        
        return {"error": "Node does not support execute_task"}
    
    async def execute_tasks(self, tasks: List[Any]) -> List[Any]:
        """
        批量执行任务
        
        Args:
            tasks: 任务列表
            
        Returns:
            结果列表
        """
        coros = [self.execute_task(task) for task in tasks]
        return await asyncio.gather(*coros)
    
    def get_node_count(self) -> int:
        """获取节点数量"""
        return len(self.nodes)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "node_count": len(self.nodes),
            "nodes": [
                getattr(node, "node_id", str(i))
                for i, node in enumerate(self.nodes)
            ]
        }


class AgentNode:
    """Agent节点"""
    
    def __init__(self, node_id: str, agent_pool: Any):
        self.node_id = node_id
        self.agent_pool = agent_pool
    
    async def execute_task(self, task: Any) -> Any:
        """执行任务"""
        return await self.agent_pool.execute_task(task)

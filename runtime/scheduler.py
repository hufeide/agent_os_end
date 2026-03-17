"""
Scheduler - 任务调度器

基于DAG的任务调度器，支持任务依赖管理。
"""

import asyncio
from typing import Any, Dict, List, Optional, Set
from collections import defaultdict

from ..models import Task, TaskStatus


class Scheduler:
    """
    任务调度器
    
    基于DAG的任务调度器，支持任务依赖管理和并行执行。
    """
    
    def __init__(self, pool: Any):
        self.pool = pool
        self._tasks: Dict[str, Task] = {}
        self._dependencies: Dict[str, Set[str]] = defaultdict(set)
        self._dependents: Dict[str, Set[str]] = defaultdict(set)
        self._completed: Set[str] = set()
        self._running: Set[str] = set()
        self._results: Dict[str, Any] = {}
    
    def add_task(self, task: Task) -> None:
        """
        添加任务
        
        Args:
            task: 任务
        """
        self._tasks[task.id] = task
        
        for dep_id in task.dependencies:
            self._dependencies[task.id].add(dep_id)
            self._dependents[dep_id].add(task.id)
    
    def add_tasks(self, tasks: List[Task]) -> None:
        """
        批量添加任务
        
        Args:
            tasks: 任务列表
        """
        for task in tasks:
            self.add_task(task)
    
    def get_ready_tasks(self) -> List[Task]:
        """
        获取就绪任务
        
        Returns:
            就绪任务列表
        """
        ready = []
        
        for task_id, task in self._tasks.items():
            if task_id in self._completed:
                continue
            if task_id in self._running:
                continue
            if task.status == TaskStatus.COMPLETED.value:
                continue
            
            deps = self._dependencies.get(task_id, set())
            if deps.issubset(self._completed):
                ready.append(task)
        
        return ready
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务
        """
        return self._tasks.get(task_id)
    
    def complete_task(self, task_id: str, result: Any = None) -> None:
        """
        完成任务
        
        Args:
            task_id: 任务ID
            result: 结果
        """
        self._completed.add(task_id)
        self._running.discard(task_id)
        
        if task_id in self._tasks:
            self._tasks[task_id].complete(result)
        
        self._results[task_id] = result
    
    def fail_task(self, task_id: str, error: str) -> None:
        """
        任务失败
        
        Args:
            task_id: 任务ID
            error: 错误信息
        """
        self._running.discard(task_id)
        
        if task_id in self._tasks:
            self._tasks[task_id].fail(error)
    
    async def run(self, tasks: List[Task]) -> Dict[str, Any]:
        """
        运行任务
        
        Args:
            tasks: 任务列表
            
        Returns:
            结果字典
        """
        self.add_tasks(tasks)
        
        results = {}
        
        while len(self._completed) < len(self._tasks):
            ready = self.get_ready_tasks()
            
            if not ready:
                if len(self._running) > 0:
                    await asyncio.sleep(0.1)
                    continue
                break
            
            coros = [self.pool.execute_task(task) for task in ready]
            
            for task in ready:
                self._running.add(task.id)
            
            outputs = await asyncio.gather(*coros, return_exceptions=True)
            
            for task, result in zip(ready, outputs):
                if isinstance(result, Exception):
                    self.fail_task(task.id, str(result))
                else:
                    self.complete_task(task.id, result)
                
                results[task.id] = result
        
        return results
    
    async def run_single(self, task: Task) -> Any:
        """
        运行单个任务
        
        Args:
            task: 任务
            
        Returns:
            执行结果
        """
        self.add_task(task)
        
        while True:
            ready = self.get_ready_tasks()
            
            if ready:
                task = ready[0]
                self._running.add(task.id)
                
                try:
                    result = await self.pool.execute_task(task)
                    self.complete_task(task.id, result)
                    return result
                except Exception as e:
                    self.fail_task(task.id, str(e))
                    return {"error": str(e)}
            
            await asyncio.sleep(0.1)
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "total_tasks": len(self._tasks),
            "completed": len(self._completed),
            "running": len(self._running),
            "pending": len(self._tasks) - len(self._completed) - len(self._running)
        }
    
    def clear(self) -> None:
        """清空调度器"""
        self._tasks.clear()
        self._dependencies.clear()
        self._dependents.clear()
        self._completed.clear()
        self._running.clear()
        self._results.clear()

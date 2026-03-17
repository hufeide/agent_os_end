"""
ReActEngine - ReAct推理引擎

实现ReAct (Reasoning + Acting) 推理循环。
"""

from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json
import asyncio


@dataclass
class Thought:
    """思考结果"""
    thought: str
    action: Optional[str] = None
    action_input: Dict[str, Any] = field(default_factory=dict)
    observation: Optional[str] = None
    needs_action: bool = True
    is_final_answer: bool = False
    step: int = 0


class ReActEngine:
    """
    ReAct推理引擎
    
    实现ReAct推理循环: 思考 -> 行动 -> 观察 -> ... -> 回答
    """
    
    def __init__(
        self,
        tool_router,
        llm: Optional[Any] = None,
        max_steps: int = 8,
        enable_reflection: bool = True
    ):
        self.tools = tool_router
        self.llm = llm
        self.max_steps = max_steps
        self.enable_reflection = enable_reflection
        self._history: List[tuple] = []
    
    async def run(self, task: Any) -> Any:
        """
        运行ReAct循环
        
        Args:
            task: 任务（可以是字符串或Task对象）
            
        Returns:
            执行结果
        """
        if hasattr(task, "description"):
            task_description = task.description
            task_id = task.id
        else:
            task_description = str(task)
            task_id = "unknown"
        
        history = []
        
        for step in range(self.max_steps):
            thought = await self._think(task_description, history, step)
            
            if thought.is_final_answer:
                return thought.observation
            
            if thought.needs_action and thought.action:
                result = await self._act(thought, history)
                
                history.append((thought, result))
                
                thought.observation = result
                self._history.append((thought, result))
        
        return history[-1][1] if history else None
    
    async def _think(
        self,
        task: str,
        history: List[tuple],
        step: int
    ) -> Thought:
        """
        思考：分析当前状态，决定下一步行动
        
        Args:
            task: 任务描述
            history: 历史记录
            step: 当前步骤
            
        Returns:
            思考结果
        """

        if self.llm:
            return await self._llm_think(task, history, step)
        
        return self._default_think(task, history, step)
    
    async def _llm_think(
        self,
        task: str,
        history: List[tuple],
        step: int
    ) -> Thought:
        """使用LLM进行思考"""
        history_text = self._format_history(history)
        
        prompt = f"""Current task: {task}

History:
{history_text}

Step {step + 1}/{self.max_steps}

Decide your next action. Return JSON:
{{
    "thought": "Your reasoning",
    "action": "tool_name or 'answer'",
    "action_input": {{"param": "value"}},
    "needs_action": true/false,
    "is_final_answer": true/false,
    "observation": "final answer if is_final_answer is true"
}}

Only return JSON."""
        
        try:
            if callable(self.llm):
                response = self.llm(prompt)
            elif hasattr(self.llm, 'generate'):
                response = self.llm.generate(prompt)
            elif hasattr(self.llm, 'agenerate'):
                response = await self.llm.agenerate(prompt)
            else:
                response = str(self.llm)
            
            thought = self._parse_thought(response, step)
            
            if thought.is_final_answer and thought.observation:
                return thought
            
            if thought.action and thought.needs_action:
                return thought
            
            if thought.action is None and not thought.needs_action:
                return Thought(
                    thought=thought.thought or "Task completed",
                    action=None,
                    action_input={},
                    observation=thought.observation or response,
                    needs_action=False,
                    is_final_answer=True,
                    step=step
                )
            
            return thought
        except Exception as e:
            return self._default_think(task, history, step)
    
    def _parse_thought(self, response: str, step: int) -> Thought:
        """解析思考结果"""
        try:
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]
            
            data = json.loads(response.strip())
            
            return Thought(
                thought=data.get("thought", ""),
                action=data.get("action"),
                action_input=data.get("action_input", {}),
                observation=data.get("observation"),
                needs_action=data.get("needs_action", True),
                is_final_answer=data.get("is_final_answer", False),
                step=step
            )
        except:
            return Thought(
                thought=response,
                needs_action=False,
                is_final_answer=True,
                observation=response,
                step=step
            )
    
    def _default_think(
        self,
        task: str,
        history: List[tuple],
        step: int
    ) -> Thought:
        """默认思考逻辑"""
        if not history:
            return Thought(
                thought="Task started, need to gather information",
                action="search",
                action_input={"query": task[:100]},
                needs_action=True,
                is_final_answer=False,
                step=step
            )
        
        if len(history) >= 2:
            return Thought(
                thought="Already executed enough actions, can provide answer now",
                action=None,
                needs_action=False,
                is_final_answer=True,
                observation=f"Completed task: {task}",
                step=step
            )
        
        return Thought(
            thought="Continue executing task",
            action="search",
            action_input={"query": task[:100]},
            needs_action=True,
            is_final_answer=False,
            step=step
        )
    
    async def _act(self, thought: Thought, history: List[tuple]) -> str:
        """
        行动：执行工具
        
        Args:
            thought: 思考结果
            history: 历史记录
            
        Returns:
            执行结果
        """
        if not thought.action:
            return "No action to execute"
        
        tool = self.tools.route(thought.action)
        
        if not tool:
            return f"Tool {thought.action} not found"
        
        try:
            result = await tool.execute(**thought.action_input)
            
            if hasattr(result, "result"):
                return str(result.result)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _format_history(self, history: List[tuple]) -> str:
        """格式化历史记录"""
        if not history:
            return "No history yet"
        
        text = ""
        for i, (thought, result) in enumerate(history):
            text += f"\nStep {i+1}:\n"
            text += f"Thought: {thought.thought}\n"
            text += f"Action: {thought.action}\n"
            text += f"Result: {result}\n"
        
        return text
    
    def get_history(self) -> List[tuple]:
        """获取执行历史"""
        return self._history.copy()
    
    def clear_history(self) -> None:
        """清空历史"""
        self._history.clear()

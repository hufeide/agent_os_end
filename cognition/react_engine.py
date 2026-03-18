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
        enable_reflection: bool = True,
        trace_callback: Optional[Callable] = None
    ):
        self.tools = tool_router
        self.llm = llm
        self.max_steps = max_steps
        self.enable_reflection = enable_reflection
        self._history: List[tuple] = []
        self.trace_callback = trace_callback
    
    def _get_available_tools_description(self) -> str:
        """获取可用工具描述"""
        try:
            tools = []
            
            if hasattr(self.tools, 'get_available_tools'):
                tools = self.tools.get_available_tools()
            elif hasattr(self.tools, 'registry') and hasattr(self.tools.registry, 'list_tools'):
                tools = self.tools.registry.list_tools()
            elif hasattr(self.tools, 'list_tools'):
                tools = self.tools.list_tools()
            
            print(f"[ReAct] Found tools: {tools}")
            
            if not tools:
                return "answer (return the final result directly)"
            
            tool_list = []
            for name in tools:
                tool_obj = None
                if hasattr(self.tools, 'registry'):
                    tool_obj = self.tools.registry.get(name)
                elif hasattr(self.tools, 'get'):
                    tool_obj = self.tools.get(name)
                
                if tool_obj and hasattr(tool_obj, 'description'):
                    tool_list.append(f"- {name}: {tool_obj.description}")
                else:
                    tool_list.append(f"- {name}")
            
            if not tool_list:
                return "answer (return the final result directly)"
            
            result = "\n".join(tool_list) + "\n- answer (return the final result directly)"
            print(f"[ReAct] Tools description: {result[:200]}...")
            return result
        except Exception as e:
            print(f"[ReAct] Error getting tools: {e}")
            return "answer (return the final result directly)"
    
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
            
            if self.trace_callback:
                self.trace_callback(task_id, "think", thought=thought.thought, action=thought.action, action_input=thought.action_input)
            
            if thought.is_final_answer:
                if self.trace_callback:
                    self.trace_callback(task_id, "result", observation=thought.observation, is_final=True)
                return thought.observation
            
            if thought.needs_action and thought.action:
                result = await self._act(thought, history)
                
                if self.trace_callback:
                    self.trace_callback(task_id, "tool", action=thought.action, action_input=thought.action_input, observation=result)
                
                history.append((thought, result))
                
                thought.observation = result
                self._history.append((thought, result))
        
        if history:
            final_answer = await self._generate_final_answer(task_description, history)
            if self.trace_callback:
                self.trace_callback(task_id, "result", observation=final_answer, is_final=True)
            return final_answer
        
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
    
    async def _think(
        self,
        task: str,
        history: List[tuple],
        step: int
    ) -> Thought:
        """使用LLM进行思考"""
        history_text = self._format_history(history)
        
        available_tools = self._get_available_tools_description()
        
        prompt = f"""Current task: {task}

Available tools:
{available_tools}

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

Only return JSON. Use 'answer' action when you have the final result."""
        
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
            available = self._get_available_tools_description()
            return f"Tool '{thought.action}' not found. Available: {available}"
        
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
    
    async def _generate_final_answer(self, task: str, history: List[tuple]) -> str:
        """生成最终答案"""
        if not self.llm:
            return history[-1][1] if history else "No result"
        
        history_text = self._format_history(history)
        
        prompt = f"""Current task: {task}

You have completed the task using tools. Based on the tool results below, provide a comprehensive final answer to the user.

Tool execution history:
{history_text}

Please provide a clear, helpful answer based on the tool results above. Do NOT just repeat the raw tool output - synthesize and explain the information."""

        try:
            if callable(self.llm):
                response = self.llm(prompt)
            elif hasattr(self.llm, 'generate'):
                response = self.llm.generate(prompt)
            elif hasattr(self.llm, 'agenerate'):
                response = await self.llm.agenerate(prompt)
            else:
                response = str(self.llm)
            
            if hasattr(response, 'content'):
                return response.content
            return str(response)
        except Exception as e:
            print(f"[ReAct] Final answer generation error: {e}")
            return history[-1][1] if history else "Error generating answer"

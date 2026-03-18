"""
直接测试 Agent 执行流程
"""
import sys
import asyncio
sys.path.insert(0, '/home/aixz/data/hxf/bigmodel/ai_code/agentos/agent_os_v1')

from agent_os_ultimate.debug.llm_client import Qwen3CoderClient
from agent_os_ultimate.tools import ToolRegistry
from agent_os_ultimate.memory import WorkingMemory
from agent_os_ultimate.skills import SkillHub
from agent_os_ultimate.runtime import AgentRuntime
from agent_os_ultimate.models import Task

async def test():
    print("=== 1. 初始化 LLM ===")
    llm = Qwen3CoderClient(
        base_url="http://192.168.1.159:19000",
        model="Qwen3Coder",
        temperature=0.7,
        max_tokens=2048
    )
    
    test_result = llm.generate("你好")
    print(f"LLM 测试响应: {test_result[:100]}")
    
    print("\n=== 2. 初始化 Runtime ===")
    runtime = AgentRuntime(
        pool_size=2,
        llm=llm
    )
    
    print("\n=== 3. 创建任务 ===")
    task = Task(description="写一个简单的加法函数")
    print(f"Task ID: {task.id}")
    print(f"Task Description: {task.description}")
    
    print("\n=== 4. 执行任务 ===")
    try:
        result = await runtime.run_single(task)
        print(f"\n执行结果: {result}")
    except Exception as e:
        print(f"\n执行错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())

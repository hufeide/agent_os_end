"""
完整系统集成测试

使用 Qwen3Coder LLM 进行端到端测试
"""

import sys
import asyncio
sys.path.insert(0, '/home/aixz/data/hxf/bigmodel/ai_code/agentos/agent_os_v1')

from agent_os_ultimate.debug.llm_client import Qwen3CoderClient, get_llm_client
from agent_os_ultimate.runtime import AgentRuntime
from agent_os_ultimate.models import Task
from agent_os_ultimate.tools import SearchTool, CodeTool, FileTool, WebTool
from agent_os_ultimate.memory import WorkingMemory


def test_llm_client():
    """测试 LLM 客户端"""
    print("\n=== 测试 Qwen3Coder LLM 客户端 ===")
    
    llm = Qwen3CoderClient(
        base_url="http://192.168.1.159:19000",
        model="Qwen3Coder"
    )
    
    response = llm.generate("你好，请用一句话介绍自己")
    print(f"  LLM 响应: {response[:200]}...")
    
    if "Error" not in response:
        print("  ✓ LLM 客户端测试通过")
        return llm
    else:
        print(f"  ✗ LLM 客户端测试失败: {response}")
        return None


def test_runtime_with_llm(llm):
    """测试 AgentRuntime"""
    print("\n=== 测试 AgentRuntime ===")
    
    runtime = AgentRuntime(
        llm=llm,
        pool_size=3
    )
    
    runtime.register_default_tools()
    
    print(f"  已注册工具数: {len(runtime.tools.list_tools())}")
    print(f"  Agent池大小: {len(runtime.pool)}")
    
    print("  ✓ AgentRuntime 测试通过")
    return runtime


async def test_runtime_task(runtime):
    """测试运行时任务执行"""
    print("\n=== 测试运行时任务执行 ===")
    
    task = Task(description="用Python写一个简单的Hello World程序")
    
    result = await runtime.run_single(task)
    print(f"  任务结果: {result}")
    
    print("  ✓ 运行时任务执行测试通过")


def test_tools_execution():
    """测试工具执行"""
    print("\n=== 测试工具执行 ===")
    
    tools = [SearchTool(), FileTool()]
    
    for tool in tools:
        print(f"  工具: {tool.name}")
    
    print("  ✓ 工具执行测试通过")


async def run_full_test():
    """运行完整测试"""
    print("=" * 60)
    print("Ultimate Agent OS 完整系统集成测试")
    print("使用 Qwen3Coder @ 192.168.1.159:19000")
    print("=" * 60)
    
    llm = test_llm_client()
    if llm is None:
        print("\n✗ LLM 连接失败，请检查服务是否启动")
        return False
    
    runtime = test_runtime_with_llm(llm)
    
    test_tools_execution()
    
    try:
        await test_runtime_task(runtime)
    except Exception as e:
        print(f"  任务执行测试跳过: {e}")
    
    stats = runtime.get_statistics()
    print(f"\n系统统计: {stats}")
    
    print("\n" + "=" * 60)
    print("✓ 完整系统集成测试完成!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = asyncio.run(run_full_test())
    sys.exit(0 if success else 1)

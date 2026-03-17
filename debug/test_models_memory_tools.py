"""
Models, Memory, Tools 模块调试测试
"""

import sys
sys.path.insert(0, '/home/aixz/data/hxf/bigmodel/ai_code/agentos/agent_os_v1')

from agent_os_ultimate.models import Task, TaskStatus, Message, AgentState, PromptTemplate
from agent_os_ultimate.memory import WorkingMemory, VectorMemory, EpisodicMemory, TaskReplay
from agent_os_ultimate.tools import BaseTool, ToolRegistry, ToolRouter


def test_models():
    """测试数据模型"""
    print("\n=== 测试 Models ===")
    
    task = Task(description="测试任务")
    print(f"  Task: {task.id}, {task.description}, {task.status}")
    assert task.status == TaskStatus.PENDING.value
    
    task.start()
    assert task.status == TaskStatus.RUNNING.value
    
    task.complete("test result")
    assert task.status == TaskStatus.COMPLETED.value
    assert task.result == "test result"
    print("  ✓ Task 测试通过")
    
    message = Message(role="user", content="Hello")
    print(f"  Message: {message.role}, {message.content}")
    assert message.role == "user"
    print("  ✓ Message 测试通过")
    
    agent_state = AgentState(role="worker", id="agent_1", name="Worker-1")
    agent_state.start_task("task_1", "Test task")
    print(f"  AgentState: {agent_state.role}, {agent_state.status}")
    assert agent_state.current_task_id == "task_1"
    print("  ✓ AgentState 测试通过")
    
    template = PromptTemplate(
        template="Task: {task}\nInstructions: {instructions}",
        description="Test template"
    )
    rendered = template.render(task="Test", instructions="Do it")
    print(f"  PromptTemplate: {rendered}")
    assert "Test" in rendered
    print("  ✓ PromptTemplate 测试通过")
    
    print("  ✓ Models 模块测试通过")


def test_memory():
    """测试记忆系统"""
    print("\n=== 测试 Memory ===")
    
    wm = WorkingMemory()
    
    wm.set("key1", "value1")
    wm.set("key2", {"nested": "data"})
    
    assert wm.get("key1") == "value1"
    assert wm.get("key2")["nested"] == "data"
    print("  WorkingMemory: set/get 正常")
    
    wm.delete("key1")
    assert wm.get("key1") is None
    print("  WorkingMemory: delete 正常")
    
    print("  ✓ WorkingMemory 测试通过")
    
    vm = VectorMemory(dimension=128)
    vm.add("这是一个测试向量", {"source": "test"})
    results = vm.search("测试", top_k=1)
    print(f"  VectorMemory: 添加了1条，搜索返回{len(results)}条")
    print("  ✓ VectorMemory 测试通过")
    
    em = EpisodicMemory()
    em.add(event="started", content="Task started", data={"action": "start"}, agent_id="agent_1", task_id="task_1")
    events = em.get_by_agent("agent_1")
    assert len(events) >= 1
    print(f"  EpisodicMemory: 记录了{len(events)}个事件")
    print("  ✓ EpisodicMemory 测试通过")
    
    tr = TaskReplay()
    tr.add("task_1", "Test task", "result", 0.9, "optimized prompt")
    records = tr.recent(k=10)
    assert len(records) >= 1
    print(f"  TaskReplay: 添加了{len(records)}条记录")
    print("  ✓ TaskReplay 测试通过")
    
    print("  ✓ Memory 模块测试通过")


def test_tools():
    """测试工具系统"""
    print("\n=== 测试 Tools ===")
    
    class MockTool(BaseTool):
        name = "mock_tool"
        description = "Mock tool for testing"
        
        async def execute(self, **kwargs):
            return {"result": f"executed with {kwargs}"}
    
    registry = ToolRegistry()
    tool = MockTool()
    registry.register(tool)
    
    assert registry.get("mock_tool") is not None
    print("  ToolRegistry: 注册成功")
    
    tools_list = registry.list_tools()
    assert len(tools_list) >= 1
    print(f"  ToolRegistry: 列出{len(tools_list)}个工具")
    
    router = ToolRouter(registry)
    selected = router.route("mock_tool")
    assert selected is not None
    print(f"  ToolRouter: 路由成功")
    
    print("  ✓ Tools 模块测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("开始 Models, Memory, Tools 模块调试测试")
    print("=" * 50)
    
    try:
        test_models()
        test_memory()
        test_tools()
        
        print("\n" + "=" * 50)
        print("✓ 所有模块测试通过!")
        print("=" * 50)
        return True
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

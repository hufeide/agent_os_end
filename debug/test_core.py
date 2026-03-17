"""
Core 模块调试测试
"""

import sys
sys.path.insert(0, '/home/aixz/data/hxf/bigmodel/ai_code/agentos/agent_os_v1')

from agent_os_ultimate.core import (
    EventBus, Event,
    Blackboard,
    Trace, TraceLevel,
    Config, DEFAULT_CONFIG,
    AgentOSLogger, get_logger, logger
)


def test_event_bus():
    """测试 EventBus"""
    print("\n=== 测试 EventBus ===")
    
    event_bus = EventBus()
    received_events = []
    
    def handler(event):
        received_events.append(event)
        print(f"  收到事件: {event.type} - {event.data}")
    
    event_bus.on("task_created", handler)
    event_bus.on("task_completed", handler)
    
    import asyncio
    asyncio.run(event_bus.emit("task_created", {"task_id": "test_1"}))
    asyncio.run(event_bus.emit("task_completed", {"task_id": "test_1", "result": "success"}))
    
    assert len(received_events) == 2, f"期望收到2个事件，实际收到{len(received_events)}个"
    print("  ✓ EventBus 测试通过")


def test_blackboard():
    """测试 Blackboard"""
    print("\n=== 测试 Blackboard ===")
    
    bb = Blackboard()
    
    bb.write("task_1", {"status": "running"}, author="agent_1")
    bb.write("task_2", {"status": "completed"}, author="agent_2")
    
    entry1 = bb.read("task_1")
    assert entry1 is not None, "读取 task_1 失败"
    assert entry1["status"] == "running", "task_1 状态不正确"
    print(f"  读取 task_1: {entry1}")
    
    keys = bb.get_keys()
    running_tasks = [k for k in keys if bb.read(k).get("status") == "running"]
    assert len(running_tasks) == 1, f"期望找到1个运行中任务，实际找到{len(running_tasks)}个"
    print(f"  查询运行中任务: {len(running_tasks)} 个")
    
    history = bb.get_history()
    assert len(history) == 2, f"期望历史记录数为2，实际为{len(history)}"
    print(f"  历史记录数: {len(history)}")
    
    print("  ✓ Blackboard 测试通过")


def test_trace():
    """测试 Trace"""
    print("\n=== 测试 Trace ===")
    
    trace = Trace()
    
    trace.log("系统启动", TraceLevel.INFO, category="test")
    trace.log("调试信息", TraceLevel.DEBUG, category="test", data={"key": "value"})
    trace.log("警告信息", TraceLevel.WARNING, category="test")
    
    events = trace.get_events()
    assert len(events) == 3, f"期望3个事件，实际有{len(events)}个"
    print(f"  事件总数: {len(events)}")
    
    warnings = trace.get_events(level=TraceLevel.WARNING)
    assert len(warnings) == 1, f"期望1个警告，实际有{len(warnings)}个"
    print(f"  警告事件数: {len(warnings)}")
    
    serialized = trace.export()
    assert len(serialized) == 3, "序列化结果数量不正确"
    print(f" 序列化成功: {len(serialized)} 条记录")
    
    print("  ✓ Trace 测试通过")


def test_config():
    """测试 Config"""
    print("\n=== 测试 Config ===")
    
    config = Config()
    
    print(f"  MAX_REACT_STEPS = {config.MAX_REACT_STEPS}")
    print(f"  GPU_BATCH_SIZE = {config.GPU_BATCH_SIZE}")
    print(f"  RL_LEARNING_RATE = {config.RL_LEARNING_RATE}")
    print(f"  AGENT_POOL_SIZE = {config.AGENT_POOL_SIZE}")
    print(f"  LLM_DEFAULT_MODEL = {config.LLM_DEFAULT_MODEL}")
    
    config_dict = config.to_dict()
    assert "MAX_REACT_STEPS" in config_dict, "配置中缺少 MAX_REACT_STEPS 键"
    print(f"  配置项数: {len(config_dict)}")
    
    print("  ✓ Config 测试通过")


def test_logger():
    """测试 Logger"""
    print("\n=== 测试 Logger ===")
    
    import logging
    
    log = get_logger("test")
    
    log.info("信息日志")
    log.debug("调试日志")
    log.warning("警告日志")
    log.error("错误日志")
    
    print(f"  Logger name: {log.name}")
    print(f"  Logger level: {log.level}")
    
    logger.info("全局logger测试")
    print("  全局logger测试通过")
    
    print("  ✓ Logger 测试通过")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("开始 Core 模块调试测试")
    print("=" * 50)
    
    try:
        test_event_bus()
        test_blackboard()
        test_trace()
        test_config()
        test_logger()
        
        print("\n" + "=" * 50)
        print("✓ Core 模块所有测试通过!")
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

"""
Ultimate Agent OS 部署入口

启动 FastAPI 服务和 Web UI
"""

import sys
import os

sys.path.insert(0, '/home/aixz/data/hxf/bigmodel/ai_code/agentos/agent_os_v1')

from agent_os_ultimate import create_runtime, create_control_plane
from agent_os_ultimate.debug.llm_client import Qwen3CoderClient
from fastapi import FastAPI


def create_app():
    """创建 FastAPI 应用"""
    print("=" * 60)
    print("Ultimate Agent OS 部署")
    print("=" * 60)
    
    print("\n[1/3] 初始化 LLM 客户端...")
    llm = Qwen3CoderClient(
        base_url="http://192.168.1.159:19000",
        model="Qwen3Coder",
        temperature=0.7,
        max_tokens=2048
    )
    
    test_response = llm.generate("你好")
    if "Error" in test_response:
        print(f"  ⚠ LLM 连接警告: {test_response}")
    else:
        print(f"  ✓ LLM 连接成功")
    
    print("\n[2/3] 创建 Agent 运行时...")
    runtime = create_runtime(
        pool_size=5,
        llm=llm,
        enable_tools=True,
        enable_skills=True
    )
    print(f"  ✓ Agent池大小: {len(runtime.pool)}")
    print(f"  ✓ 已注册工具: {len(runtime.tools.list_tools())}")
    print(f"  ✓ 已注册技能: {len(runtime.skill_hub)}")
    
    print("\n[3/3] 创建控制平面...")
    control_plane = create_control_plane(runtime)
    app = control_plane.get_app()
    print(f"  ✓ FastAPI 应用创建成功")
    
    print("\n" + "=" * 60)
    print("部署完成!")
    print("=" * 60)
    
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "agent_os_ultimate.deploy:app",
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True
    )

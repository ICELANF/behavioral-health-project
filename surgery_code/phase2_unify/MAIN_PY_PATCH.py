"""
api/main.py 启动补丁 — Phase 1+2 改动说明

在 api/main.py 的 startup 阶段 (大约第 50-100 行),
找到 get_master_agent() 调用, 替换为以下代码:

═══════════════════════════════════════════════
BEFORE (手术前):
═══════════════════════════════════════════════

    from core.master_agent_unified import get_master_agent
    ...
    master_agent = get_master_agent(db_session=db)

═══════════════════════════════════════════════
AFTER (手术后):
═══════════════════════════════════════════════
"""

# ── 放在 api/main.py startup 事件中 ──

# Phase 1: AgentRegistry 启动
from core.agents.startup import create_registry

# 创建并冻结 Registry (内部自动注册所有 Agent)
_registry = create_registry(db_session=db)
print(f"[API] AgentRegistry 已冻结: {_registry.count()} 个 Agent")

# Phase 2: MasterAgent 统一版本
from core.agents.master_agent import MasterAgent, get_master_agent

master_agent = get_master_agent(db_session=db, registry=_registry)
print(f"[API] MasterAgent (统一版) 初始化完成")


"""
═══════════════════════════════════════════════
同时删除以下猴子补丁代码 (Phase 1 后不再需要):
═══════════════════════════════════════════════

    # 删除: behavior_rx 猴子补丁注入
    from behavior_rx.patches import patch_master_agent_v0
    patch_master_agent_v0(master_agent)

原因: behavior_rx 的 4 个专家 Agent 现在通过 Registry 注册,
      不再需要猴子补丁。见 startup.py::_register_behavior_rx_experts()

═══════════════════════════════════════════════
同时删除以下 V4.1 注册代码 (Phase 3 后不再需要):
═══════════════════════════════════════════════

    # 删除: assistant_agents (router 不存在, 永远失败)
    try:
        from assistant_agents.router import router as assistant_router
        app.include_router(assistant_router)
    except ImportError as e:
        ...

    # 删除: professional_agents (同上)
    try:
        from professional_agents.router import router as professional_router
        app.include_router(professional_router)
    except ImportError as e:
        ...

原因: 这些路由文件从未存在, import 永远失败。
      相关功能已通过 Registry + 用户层 Agent 实现。
"""

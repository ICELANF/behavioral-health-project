# -*- coding: utf-8 -*-
"""TD-3 Fix: agent_api.py 统一 MasterAgent 入口"""
import re

filepath = "api/agent_api.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

original = content

# ============================================================
# FIX 1: _run_agent_task 中的 v0 fallback (约 line 215-260)
# 把 from core.master_agent import MasterAgent, UserInput, InputType
#     agent = MasterAgent()
# 替换为使用 get_master_agent() 统一入口
# ============================================================

# 找到 v0 降级块 — 特征: "from core.master_agent import MasterAgent, UserInput, InputType"
old_v0_block = '''            from core.master_agent import MasterAgent, UserInput, InputType
            agent = MasterAgent()
            user_input = UserInput(
                user_id=req.user_id,
                input_type=InputType.TEXT,
                content=f"[{req.agent_type}] {req.expected_output}",
                session_id=task_id,
            )
            result = agent.process(user_input)'''

new_v0_block = '''            from api.main import get_master_agent
            ma = get_master_agent()
            if ma is None:
                raise RuntimeError("MasterAgent unavailable")
            result = ma.process(
                user_id=req.user_id,
                message=f"[{req.agent_type}] {req.expected_output}",
                context=req.context,
            )'''

if old_v0_block in content:
    content = content.replace(old_v0_block, new_v0_block)
    print("[FIX-1] _run_agent_task v0 fallback -> get_master_agent()")
else:
    print("[SKIP-1] v0 fallback block not found (may already be patched)")

# Also fix the result access pattern after the block
old_result_access = """            if hasattr(result, 'response') and result.response:
                suggestions.append({
                    "id": f"sug-{task_id}",
                    "type": "action",
                    "priority": 7,
                    "text": getattr(result.response, 'reply', str(result.response)),
                })"""

new_result_access = """            resp_text = result.get("response", "") if isinstance(result, dict) else ""
            if resp_text:
                suggestions.append({
                    "id": f"sug-{task_id}",
                    "type": "action",
                    "priority": 7,
                    "text": resp_text,
                })"""

if old_result_access in content:
    content = content.replace(old_result_access, new_result_access)
    print("[FIX-1b] v0 result access pattern -> dict-based")
else:
    print("[SKIP-1b] result access pattern not found")

# Fix the metadata model_version for this fallback
content = content.replace(
    '"model_version": "xingjian-coach-v1.0"',
    '"model_version": "master-agent-unified"'
)

# ============================================================
# FIX 2: agent_system_status 中的 v0 可用性检查 (约 line 680-690)
# 把 from core.master_agent import MasterAgent; _ = MasterAgent()
# 替换为检查 get_master_agent()
# ============================================================

old_status_check = """    master_available = False
    try:
        from core.master_agent import MasterAgent
        _ = MasterAgent()
        master_available = True
    except Exception:
        pass

    # \u68c0\u67e5 v6 AgentMaster \u53ef\u7528\u6027
    agent_master_v6 = False
    v6_agent_count = 0
    try:
        from api.main import get_agent_master
        am = get_agent_master()
        if am:
            agent_master_v6 = True
            v6_agent_count = len(am._agents)
    except Exception:
        pass"""

new_status_check = """    master_available = False
    unified_agent_count = 0
    try:
        from api.main import get_master_agent
        ma = get_master_agent()
        if ma:
            master_available = True
            registry = getattr(ma, '_registry', None)
            if registry:
                unified_agent_count = len(registry._agents) if hasattr(registry, '_agents') else 0
    except Exception:
        pass

    # 统一架构: v6 = master (向后兼容字段)
    agent_master_v6 = master_available
    v6_agent_count = unified_agent_count"""

if old_status_check in content:
    content = content.replace(old_status_check, new_status_check)
    print("[FIX-2] agent_system_status -> get_master_agent()")
else:
    # Try a more flexible match
    if "from core.master_agent import MasterAgent" in content and "_ = MasterAgent()" in content:
        content = content.replace(
            "from core.master_agent import MasterAgent\n        _ = MasterAgent()",
            "from api.main import get_master_agent\n        _ = get_master_agent(); assert _ is not None"
        )
        print("[FIX-2] partial: replaced v0 import in status check")
    else:
        print("[SKIP-2] status check block not found")

# ============================================================
# FIX 3: get_agent_master -> get_master_agent (统一命名)
# ============================================================
# _run_agent_task 中的 from api.main import get_agent_master
content = content.replace(
    "from api.main import get_agent_master",
    "from api.main import get_master_agent"
)
content = content.replace(
    "agent_master = get_agent_master()",
    "agent_master = get_master_agent()"
)
print("[FIX-3] get_agent_master -> get_master_agent (naming unification)")

# ============================================================
# 写回
# ============================================================
if content != original:
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n[DONE] {filepath} patched successfully")
else:
    print(f"\n[NO-OP] {filepath} unchanged")

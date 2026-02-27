"""
手术补丁自动应用脚本
在项目根目录运行: python apply_patches.py
"""
import re

# ══════════════════════════════════════
#  PATCH 1: api/main.py — get_master_agent 替换
# ══════════════════════════════════════

print("=" * 50)
print("  PATCH 1: api/main.py")
print("=" * 50)

with open("api/main.py", "r", encoding="utf-8") as f:
    main_content = f.read()

# 1a. 替换 get_master_agent 函数定义 (第63-82行)
OLD_MASTER = '''# 延迟导入 Master Agent — 统一单例 (v0+v6 合并)
_master_agent = None

def get_master_agent(db_session=None):
    """获取统一 MasterAgent 单例 (v0+v6 合并)"""
    global _master_agent
    if _master_agent is None:
        try:
            from core.master_agent_unified import UnifiedMasterAgent
            if db_session is None:
                try:
                    from core.database import SessionLocal
                    db_session = SessionLocal()
                except Exception:
                    pass
            _master_agent = UnifiedMasterAgent(db_session=db_session)
            print("[API] UnifiedMasterAgent (v0+v6) 初始化成功")
        except Exception as e:
            print(f"[API] UnifiedMasterAgent 初始化失败: {e}")
    return _master_agent'''

NEW_MASTER = '''# Phase 1+2: AgentRegistry + 统一 MasterAgent
_registry = None
_master_agent = None

def get_master_agent(db_session=None):
    """获取统一 MasterAgent 单例 (通过 AgentRegistry)"""
    global _master_agent, _registry
    if _master_agent is None:
        try:
            if db_session is None:
                try:
                    from core.database import SessionLocal
                    db_session = SessionLocal()
                except Exception:
                    pass
            # Phase 1: 创建并冻结 Registry
            if _registry is None:
                from core.agents.startup import create_registry
                _registry = create_registry(db_session=db_session)
                print(f"[API] AgentRegistry 已冻结: {_registry.count()} 个 Agent")
            # Phase 2: 统一 MasterAgent
            from core.agents.master_agent import MasterAgent
            _master_agent = MasterAgent(registry=_registry, db_session=db_session)
            print("[API] MasterAgent (统一版) 初始化完成")
        except Exception as e:
            print(f"[API] MasterAgent 初始化失败: {e}")
            # 降级: 尝试旧版
            try:
                from core.master_agent_unified import UnifiedMasterAgent
                _master_agent = UnifiedMasterAgent(db_session=db_session)
                print("[API] 降级到 UnifiedMasterAgent")
            except Exception as e2:
                print(f"[API] 降级也失败: {e2}")
    return _master_agent'''

# 尝试替换（处理可能的编码差异，用宽松匹配）
if "from core.master_agent_unified import UnifiedMasterAgent" in main_content:
    # 用正则匹配整个函数块
    pattern = r'# [^\n]*Master Agent[^\n]*\n_master_agent = None\n\ndef get_master_agent\(db_session=None\):.*?return _master_agent'
    match = re.search(pattern, main_content, re.DOTALL)
    if match:
        main_content = main_content[:match.start()] + NEW_MASTER + main_content[match.end():]
        print("[OK] get_master_agent() 已替换为 Registry 版本")
    else:
        print("[!] 正则未匹配, 尝试行级替换...")
        main_content = main_content.replace(
            "from core.master_agent_unified import UnifiedMasterAgent",
            "from core.agents.startup import create_registry; from core.agents.master_agent import MasterAgent  # surgery-patched"
        )
        print("[OK] import 行已替换 (请手动检查)")
else:
    print("[SKIP] get_master_agent 已是新版本")

# 1b. 注释掉 assistant_agents/professional_agents 路由 (第2129-2142行)
if "from assistant_agents.router import router as assistant_router" in main_content:
    main_content = main_content.replace(
        """try:
    from assistant_agents.router import router as assistant_router
    app.include_router(assistant_router)""",
        """# [SURGERY] 已通过 Registry 注册, 不再需要独立路由
# try:
#     from assistant_agents.router import router as assistant_router
#     app.include_router(assistant_router)"""
    )
    print("[OK] assistant_agents 路由已注释")

if "from professional_agents.router import router as professional_router" in main_content:
    main_content = main_content.replace(
        """try:
    from professional_agents.router import router as professional_router
    app.include_router(professional_router)""",
        """# [SURGERY] 已通过 Registry 注册, 不再需要独立路由
# try:
#     from professional_agents.router import router as professional_router
#     app.include_router(professional_router)"""
    )
    print("[OK] professional_agents 路由已注释")

# 同时注释对应的 except 块
for old_except, label in [
    ('except ImportError as e:\n    print(f"[API] V4.1 用户层Agent路由注册失败: {e}")', "assistant except"),
    ('except ImportError as e:\n    print(f"[API] V4.1 教练层Agent路由注册失败: {e}")', "professional except"),
]:
    if old_except in main_content:
        main_content = main_content.replace(old_except, "# " + old_except.replace("\n", "\n# "))

with open("api/main.py", "w", encoding="utf-8") as f:
    f.write(main_content)
print("[SAVED] api/main.py\n")


# ══════════════════════════════════════
#  PATCH 2: core/agents/base.py — 3处追加
# ══════════════════════════════════════

print("=" * 50)
print("  PATCH 2: core/agents/base.py")
print("=" * 50)

with open("core/agents/base.py", "r", encoding="utf-8") as f:
    base_content = f.read()

changes = 0

# 2a. AgentDomain 追加
if "HEALTH_ASSISTANT" not in base_content:
    base_content = base_content.replace(
        '    XZB_EXPERT = "xzb_expert"',
        '''    XZB_EXPERT = "xzb_expert"
    # Phase 3: 用户层 Agent
    HEALTH_ASSISTANT = "health_assistant"
    HABIT_TRACKER = "habit_tracker"
    ONBOARDING_GUIDE = "onboarding_guide"'''
    )
    changes += 1
    print("[OK] AgentDomain 追加 3 个枚举")
else:
    print("[SKIP] AgentDomain 已有 HEALTH_ASSISTANT")

# 2b. AGENT_BASE_WEIGHTS 追加 — 找 xzb_expert 那行
if '"health_assistant"' not in base_content or '"health_assistant": 0.65' not in base_content:
    if '"xzb_expert": 0.95,' in base_content:
        base_content = base_content.replace(
            '    "xzb_expert": 0.95,\n}',
            '''    "xzb_expert": 0.95,
    # Phase 3: 用户层 Agent
    "health_assistant": 0.65,
    "habit_tracker": 0.6,
    "onboarding_guide": 0.7,
}'''
        )
        changes += 1
        print("[OK] AGENT_BASE_WEIGHTS 追加 3 个权重")
    else:
        print("[!] 未找到 xzb_expert 0.95 行, 请手动追加 AGENT_BASE_WEIGHTS")
else:
    print("[SKIP] AGENT_BASE_WEIGHTS 已有 health_assistant")

# 2c. DOMAIN_CORRELATIONS 追加 — 找 vision 那行
if '"health_assistant"' not in base_content or '"health_assistant": ["nutrition"' not in base_content:
    # 找 vision 行后面的 }
    vision_pattern = r'("vision":\s*\[.*?\],?\n)(})'
    match = re.search(vision_pattern, base_content)
    if match:
        base_content = base_content[:match.end(1)] + '''    # Phase 3: 用户层 Agent
    "health_assistant": ["nutrition", "tcm", "exercise", "sleep"],
    "habit_tracker":    ["behavior_rx", "motivation"],
    "onboarding_guide": ["trust_guide", "motivation", "health_assistant"],
''' + base_content[match.start(2):]
        changes += 1
        print("[OK] DOMAIN_CORRELATIONS 追加 3 个关联")
    else:
        print("[!] 未找到 vision 行, 请手动追加 DOMAIN_CORRELATIONS")
else:
    print("[SKIP] DOMAIN_CORRELATIONS 已有 health_assistant")

with open("core/agents/base.py", "w", encoding="utf-8") as f:
    f.write(base_content)
print(f"[SAVED] core/agents/base.py ({changes} 处修改)\n")


# ══════════════════════════════════════
#  验证
# ══════════════════════════════════════

print("=" * 50)
print("  验证")
print("=" * 50)

# 检查 main.py
with open("api/main.py", "r", encoding="utf-8") as f:
    mc = f.read()
checks = [
    ("Registry import", "from core.agents.startup import create_registry" in mc),
    ("assistant 已注释", "# [SURGERY]" in mc and "assistant_agents" in mc),
    ("professional 已注释", "professional_agents" in mc),
]

# 检查 base.py
with open("core/agents/base.py", "r", encoding="utf-8") as f:
    bc = f.read()
checks += [
    ("HEALTH_ASSISTANT enum", 'HEALTH_ASSISTANT = "health_assistant"' in bc),
    ("HABIT_TRACKER enum", 'HABIT_TRACKER = "habit_tracker"' in bc),
    ("ONBOARDING_GUIDE enum", 'ONBOARDING_GUIDE = "onboarding_guide"' in bc),
    ("health_assistant weight", '"health_assistant": 0.65' in bc),
    ("health_assistant corr", '"health_assistant": ["nutrition"' in bc),
]

all_pass = True
for name, ok in checks:
    status = "✓" if ok else "✗"
    print(f"  [{status}] {name}")
    if not ok:
        all_pass = False

print()
if all_pass:
    print("  全部通过! 运行 git add -A && git commit -m 'surgery: apply patches'")
else:
    print("  有未通过项, 请检查后手动修复")

# 行健平台架构手术 — 执行指南

## 文件清单

```
surgery_code/
├── phase0_safety/
│   ├── test_crisis_smoke.py          # Crisis 冒烟测试 (每个 Phase 必跑)
│   └── test_golden_baseline.py       # 核心链路 Golden Test
│
├── phase1_registry/
│   ├── __init__.py                   # core.agents 公开 API
│   ├── agent_meta.py                 # AgentMeta 元数据
│   ├── registry.py                   # AgentRegistry 唯一注册表
│   ├── router.py                     # AgentRouter (Registry版, 替换原版)
│   └── startup.py                    # 启动注册 + create_registry()
│
├── phase2_unify/
│   ├── master_agent.py               # MasterAgent 唯一版本 (~580行)
│   ├── master_agent_unified_stub.py  # 向后兼容转发 (2周后删)
│   ├── MAIN_PY_PATCH.py             # api/main.py 修改说明
│   └── intervention/
│       ├── __init__.py
│       ├── action_plan.py            # 从V0提取的干预计划
│       └── daily_briefing.py         # 从V0提取的每日简报
│
├── phase3_consolidate/
│   ├── BASE_PY_PATCH.py             # base.py 追加 Domain/Weight/Correlation
│   └── user_agents/
│       ├── __init__.py
│       ├── health_assistant.py       # 健康知识科普 Agent
│       ├── habit_tracker.py          # 习惯追踪 Agent
│       └── onboarding_guide.py       # 新手引导 Agent
│
└── phase5_tests/
    └── test_consistency.py           # 一致性测试 (Registry/路由/新Agent/端到端)
```

## 执行顺序

### Phase 0: 安全基线 (0.5天)

```bash
# 1. 创建 Git 安全点
git tag pre-surgery-v5.3.2

# 2. 创建归档目录
mkdir -p _deprecated

# 3. 复制测试文件
cp surgery_code/phase0_safety/test_crisis_smoke.py tests/
cp surgery_code/phase0_safety/test_golden_baseline.py tests/

# 4. 运行基线测试 (确认手术前状态正常)
pytest tests/test_crisis_smoke.py -v
pytest tests/test_golden_baseline.py -v
```

### Phase 1: AgentRegistry (1.5天)

```bash
# 1. 部署新文件
cp surgery_code/phase1_registry/agent_meta.py core/agents/
cp surgery_code/phase1_registry/registry.py core/agents/
cp surgery_code/phase1_registry/startup.py core/agents/
cp surgery_code/phase1_registry/__init__.py core/agents/

# 2. 替换 Router (Registry 版)
cp core/agents/router.py core/agents/router.py.bak
cp surgery_code/phase1_registry/router.py core/agents/

# 3. 修改 api/main.py startup
#    参考 phase2_unify/MAIN_PY_PATCH.py 中的说明
#    将 get_master_agent() 改为 create_registry() + MasterAgent(registry=...)

# 4. 验收
pytest tests/test_crisis_smoke.py -v
python -c "from core.agents.startup import create_registry; r = create_registry(); print(f'{r.count()} agents, frozen={r.is_frozen}')"
```

### Phase 2: MasterAgent 归一 (2天)

```bash
# 1. 部署干预模块
mkdir -p core/intervention
cp surgery_code/phase2_unify/intervention/__init__.py core/intervention/
cp surgery_code/phase2_unify/intervention/action_plan.py core/intervention/
cp surgery_code/phase2_unify/intervention/daily_briefing.py core/intervention/

# 2. 替换 MasterAgent
cp core/agents/master_agent.py core/agents/master_agent.py.bak
cp surgery_code/phase2_unify/master_agent.py core/agents/

# 3. 部署向后兼容 stub
cp core/master_agent_unified.py _deprecated/
cp surgery_code/phase2_unify/master_agent_unified_stub.py core/master_agent_unified.py

# 4. 验收
pytest tests/test_crisis_smoke.py -v
pytest tests/test_golden_baseline.py -v
wc -l core/agents/master_agent.py  # 期望 ≤ 650
```

### Phase 3: 目录整合 + 3个新Agent (1天)

```bash
# 1. 应用 base.py 补丁 (3处 str_replace)
#    参考 phase3_consolidate/BASE_PY_PATCH.py

# 2. 部署用户层 Agent
mkdir -p core/agents/user_agents
cp surgery_code/phase3_consolidate/user_agents/__init__.py core/agents/user_agents/
cp surgery_code/phase3_consolidate/user_agents/health_assistant.py core/agents/user_agents/
cp surgery_code/phase3_consolidate/user_agents/habit_tracker.py core/agents/user_agents/
cp surgery_code/phase3_consolidate/user_agents/onboarding_guide.py core/agents/user_agents/

# 3. 移动未使用目录到 _deprecated
mv assistant_agents _deprecated/ 2>/dev/null
mv professional_agents _deprecated/ 2>/dev/null
mv xingjian-agent _deprecated/ 2>/dev/null

# 4. 验收
pytest tests/test_crisis_smoke.py -v
python -c "
from core.agents.startup import create_registry
r = create_registry()
print(f'{r.count()} agents')
for d in r.list_domains(): print(f'  {d}: {r.get_meta(d).display_name}')
"
```

### Phase 4: v3 清退 (1.5天, Phase 1-3 完成后再做)

> 本阶段独立于 Phase 1-3, 降低并行风险

### Phase 5: 一致性测试 (1天)

```bash
cp surgery_code/phase5_tests/test_consistency.py tests/
pytest tests/test_consistency.py -v
pytest tests/ -v  # 全量回归
```

## 回滚方案

```bash
# 任何阶段失败:
git checkout pre-surgery-v5.3.2

# 单个 Phase 回滚:
git revert <phase-N-commits>
# 从 _deprecated/ 恢复对应文件
```

## 验收检查清单

| 检查项 | 命令 | 期望 |
|--------|------|------|
| Crisis 冒烟 | `pytest tests/test_crisis_smoke.py` | 全绿 |
| Golden 基线 | `pytest tests/test_golden_baseline.py` | 全绿 |
| Registry 冻结 | `python -c "..."` | frozen=True, ≥17 agents |
| MasterAgent 行数 | `wc -l core/agents/master_agent.py` | ≤ 650 |
| V0 已归档 | `ls _deprecated/master_agent_v0.py` | 文件存在 |
| 未使用目录已归档 | `ls _deprecated/assistant_agents/` | 目录存在 |
| 一致性测试 | `pytest tests/test_consistency.py` | 全绿 |

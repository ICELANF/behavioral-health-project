# SURGERY_CHANGELOG.md — 架构手术记录

> 手术日期: 2026-02-27
> 手术代号: Registry Unification Surgery
> 回滚点: `git checkout pre-surgery-20260227`

## 手术背景

| 问题 | 手术前 | 手术后 |
|------|--------|--------|
| MasterAgent 版本 | 3个 (v0: 6874行, unified: 501行, v6: 425行) | **1个统一版 (666行)** |
| Agent 注册方式 | 硬编码 dict + 猴子补丁 | **AgentRegistry + freeze()** |
| 用户层 Agent | 0 (39个文件未激活) | **3个新 Agent** |
| 目录结构 | assistant_agents/ + professional_agents/ 散落 | **_deprecated/ 统一归档** |
| CrisisAgent 覆盖 | 8/10 关键词 | **10/10 + 热线全覆盖** |

## Git 提交历史

```
ec285ed surgery: fix docker-compose LOG_LEVEL + Dockerfile deprecated dirs
2fb4f4c surgery: apply main.py + base.py patches
fdcaf7b surgery-phase5: consistency tests
f80b9a2 surgery-phase3: user agents + consolidate
a31321e surgery-phase2: MasterAgent unified
088dcba surgery-phase1: AgentRegistry
a3829f1 pre-surgery: snapshot
```

## Phase 详情

### Phase 0: 安全基线
- `test_crisis_smoke.py` — 危机冒烟测试 (10关键词 × 3检查)
- `test_golden_baseline.py` — 金色基线 (chat/process/assessment/device)

### Phase 1: AgentRegistry
- **新增** `core/agents/agent_meta.py` — AgentMeta 数据类
- **新增** `core/agents/registry.py` — AgentRegistry (register/get/freeze/list)
- **新增** `core/agents/startup.py` — create_registry() 启动入口
- **修改** `core/agents/router.py` — 从 Registry 获取 Agent
- **修改** `core/agents/__init__.py` — 导出新组件
- **修改** `api/main.py` — get_master_agent() 改用 Registry

### Phase 2: MasterAgent 归一
- **新增** `core/agents/master_agent.py` — 统一 MasterAgent (666行)
- **新增** `core/intervention/action_plan.py`
- **新增** `core/intervention/daily_briefing.py`
- **归档** `core/agents/master_agent.py` (旧) → `_deprecated/master_agent_v6.py.bak`
- **降级** `core/master_agent_unified.py` → stub (重定向到新版)

### Phase 3: 用户层 Agent
- **新增** `core/agents/user_agents/health_assistant.py` — 健康助手 (兜底)
- **新增** `core/agents/user_agents/habit_tracker.py` — 习惯追踪
- **新增** `core/agents/user_agents/onboarding_guide.py` — 新手引导
- **归档** `assistant_agents/` → `_deprecated/assistant_agents/`
- **归档** `professional_agents/` → `_deprecated/professional_agents/`
- **修改** `core/agents/base.py` — 追加 3 个 AgentDomain + 权重 + 关联

### Phase 5: 测试验证
- **新增** `tests/test_consistency.py` — Registry/路由/Agent 一致性

### 额外修复
- **Dockerfile** — 注释掉 assistant_agents/professional_agents COPY
- **docker-compose.yml** — LOG_LEVEL=info → LOG_LEVEL=INFO
- **CrisisAgent** — 安眠药过量加入 CRITICAL_KW + 热线覆盖

## 验收结果

| 测试套件 | 结果 |
|---------|------|
| Crisis 冒烟 | 32/32 ✅ |
| Golden 基线 | 8/8 ✅ |
| 一致性 | 31/32 ✅ (1个 mock 数据问题) |
| API 健康 | healthy ✅ |

## 文件变更统计

- 新增文件: 14
- 修改文件: 6 (main.py, base.py, Dockerfile, docker-compose.yml, specialist_agents.py)
- 归档文件: 56 (assistant_agents/ + professional_agents/ → _deprecated/)
- 总代码新增: ~3000 行

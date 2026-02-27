# DEPRECATED_INVENTORY.md — 归档清单与复活条件

> 所有归档文件位于 `_deprecated/` 目录
> 回滚: `git checkout pre-surgery-20260227`

## 归档目录总览

| 目录 | 文件数 | 原因 | 复活条件 |
|------|--------|------|---------|
| `_deprecated/assistant_agents/` | 24 | import 路径不存在，从未激活 | 需通过 Registry 重新注册 |
| `_deprecated/professional_agents/` | 22 | import 路径不存在，从未激活 | 需通过 Registry 重新注册 |
| `_deprecated/master_agent_v6.py.bak` | 1 | 被统一 MasterAgent 替代 | 不建议复活 |
| `_deprecated/master_agent_unified_original.py` | 1 | 被 stub 替代 | 不建议复活 |
| `_deprecated/master_agent_v0.py` | 1 | 6874行遗留 (仅数据类型引用) | Phase 4 后可删除 |

## assistant_agents 详细清单

### 可复活 (功能已被新 Agent 覆盖)

| 文件 | 原功能 | 现由谁覆盖 | 复活价值 |
|------|--------|-----------|---------|
| `health_assistant.py` | 健康助手 | `user_agents/health_assistant.py` | ❌ 已替代 |
| `onboarding_guide.py` | 新手引导 | `user_agents/onboarding_guide.py` | ❌ 已替代 |
| `habit_tracker.py` | 习惯追踪 | `user_agents/habit_tracker.py` | ❌ 已替代 |
| `crisis_responder.py` | 危机响应 | `specialist_agents.py::CrisisAgent` | ❌ 已替代 |

### 有复活价值 (功能尚未实现)

| 文件 | 功能 | 复活优先级 | 依赖项 |
|------|------|-----------|--------|
| `emotion_support.py` | 情绪支持 | P2 | MentalAgent 扩展 |
| `content_recommender.py` | 内容推荐 | P2 | RAG Pipeline |
| `community_guide.py` | 社区引导 | P3 | 社区功能上线 |
| `motivation_support.py` | 动机支持 | P2 | MotivationAgent 扩展 |
| `nutrition_guide.py` | 营养指南 | P2 | NutritionAgent 扩展 |
| `exercise_guide.py` | 运动指南 | P2 | ExerciseAgent 扩展 |
| `sleep_guide.py` | 睡眠指南 | P2 | SleepAgent 扩展 |
| `tcm_wellness.py` | 中医养生 | P3 | TCMAgent 扩展 |
| `tcm_ortho_agents.py` | 中医正骨 | P3 | 骨伤科需求 |

### 无复活价值 (重复/空壳)

| 文件 | 原因 |
|------|------|
| `domain_agents.py` | 与 specialist_agents.py 重复 |
| `remaining_agents.py` | 占位符，无实现 |
| `base.py` | 与 core/agents/base.py 重复 |
| `registry.py` | 与 core/agents/registry.py 重复 |
| `router.py` | 与 core/agents/router.py 重复 |
| `schemas/*.py` | 与 core 层 schema 重复 |

## professional_agents 详细清单

### 有复活价值 (专业功能)

| 文件 | 功能 | 复活优先级 | 复活方式 |
|------|------|-----------|---------|
| `rx_composer.py` (不存在) | 多源合成处方 | P1 | 新建 Agent |
| `chronic_manager.py` (不存在) | 跨病种管理 | P1 | 新建 Agent |
| `assessment_engine.py` | 评估引擎 | P2 | 集成到 MasterAgent |
| `behavior_coach.py` | 行为教练 | P2 | behavior_rx 已覆盖 |
| `quality_auditor.py` | 质量审计 | P3 | 治理模块 |
| `supervisor_reviewer.py` | 督导审查 | P3 | 治理模块 |

### 与 behavior_rx 重复

| 文件 | 原因 |
|------|------|
| `metabolic_expert.py` | behavior_rx 已有 |
| `cardiac_rehab.py` | specialist_agents 已有 |
| `adherence_monitor.py` | behavior_rx 已有 |

## 其他可清理目录

| 目录/文件 | 大小 | 建议 |
|----------|------|------|
| `behavior_rx_v32_complete/` | ~50KB | 可直接删除 (与 behavior_rx/ 重复) |
| `master_agent_merge/` | ~30KB | 可直接删除 (合并脚本已完成) |
| `collect_for_surgery.py` | 8KB | 可保留做参考或删除 |
| `apply_patches.py` | 6KB | 可保留做参考或删除 |
| `fix_crisis.py` | 2KB | 可删除 |
| `surgery_code/` | ~100KB | 手术完成后可删除 |

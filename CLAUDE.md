# CLAUDE.md — 行健平台 (BehaviorOS) 项目契约

> 最后更新: 2026-02-27 (架构手术完成)
> Git tag: `surgery-complete-20260227`

## 项目概述

行健平台是一个行为健康促进与慢病逆转平台，采用多 Agent 协作架构，集成传统中医与现代行为科学。

- **项目根目录**: `D:\behavioral-health-project`
- **运行环境**: Docker Compose (Python 3.12 + PostgreSQL + Redis + Qdrant)
- **API 框架**: FastAPI (uvicorn, 端口 8000)
- **容器名**: bhp_v3_api / bhp_v3_worker / bhp_v3_beat

---

## 🔴 铁律 (NEVER BREAK)

### 1. 危机安全铁律
```
CrisisAgent.priority = 0  (最高优先级，永远第一个执行)
任何涉及自杀/自残关键词 → 必须返回 risk_level=critical + 热线 400-161-9995
绝不允许任何代码修改降低 CrisisAgent 优先级或绕过危机检测
```

### 2. Registry 冻结铁律
```
AgentRegistry.freeze() 调用后，不允许注册新 Agent
所有 Agent 必须在 startup.py::create_registry() 中注册
运行时动态注册 → 抛出 RegistryFrozenError
```

### 3. 四原则铁律 (Agent 通信)
```
§9.1  单一数据总线: 所有 Agent 通过 MasterAgent.process() 通信
§9.2  领域关联网络: DOMAIN_CORRELATIONS 定义跨领域触发关系
§10.3 冲突消解: CONFLICT_PRIORITY 定义领域优先级
§11.2 策略闸门: PolicyDecision 控制 ALLOW/DELAY/OVERRIDE/DENY
```

### 4. 数据模型对齐铁律
```
MicroActionTask.status ∈ {pending, completed, skipped, expired}
MicroActionTask.source ∈ {coach_assigned, ai_recommended, user_selected, intervention_plan, system}
MicroActionTask.domain ∈ {nutrition, exercise, sleep, emotion, stress, cognitive, social, tcm}
任何新 Agent 读写任务数据必须遵守以上枚举
```

---

## 📁 项目结构 (手术后)

```
behavioral-health-project/
├── api/
│   └── main.py                    # FastAPI 入口 (get_master_agent → Registry 版本)
├── core/
│   ├── agents/
│   │   ├── __init__.py            # 公共导出
│   │   ├── agent_meta.py          # AgentMeta 数据类
│   │   ├── base.py                # BaseAgent + AgentDomain + 权重/关联
│   │   ├── coordinator.py         # MultiAgentCoordinator
│   │   ├── master_agent.py        # ★ MasterAgent (统一版, 666行)
│   │   ├── registry.py            # ★ AgentRegistry (freeze 机制)
│   │   ├── router.py              # ★ AgentRouter (关键词+数据+权重)
│   │   ├── specialist_agents.py   # 领域专家 Agent (crisis/sleep/glucose/...)
│   │   ├── startup.py             # ★ create_registry() 启动入口
│   │   └── user_agents/           # ★ Phase 3 新增
│   │       ├── health_assistant.py
│   │       ├── habit_tracker.py
│   │       └── onboarding_guide.py
│   ├── intervention/              # ★ Phase 2 新增
│   │   ├── action_plan.py
│   │   └── daily_briefing.py
│   ├── safety/
│   │   ├── input_filter.py        # 输入层安全过滤
│   │   └── generation_guard.py    # 输出层安全守卫
│   ├── master_agent_unified.py    # 降级 stub (→ 重定向到新 MasterAgent)
│   └── master_agent_v0.py         # 遗留 v0 (6874行, 仅做数据类型引用)
├── behavior_rx/                   # 行为处方引擎
├── services/
│   ├── micro_action_service.py    # 微行动服务
│   └── batch_ingestion_service.py # 知识库批量摄入
├── _deprecated/                   # ★ 手术归档
│   ├── assistant_agents/          # 原用户层 (未激活)
│   ├── professional_agents/       # 原教练层 (未激活)
│   ├── master_agent_v6.py.bak
│   └── master_agent_unified_original.py
├── tests/
│   ├── test_crisis_smoke.py       # 危机冒烟 (32/32)
│   ├── test_golden_baseline.py    # 金色基线 (8/8)
│   └── test_consistency.py        # 一致性 (31/32)
└── surgery_code/                  # 手术代码包 (可删除)
```

---

## 🏗️ 架构契约

### Agent 注册表

| Agent | domain | priority | weight | 文件位置 |
|-------|--------|----------|--------|---------|
| CrisisAgent | crisis | 0 | 1.0 | specialist_agents.py |
| SleepAgent | sleep | 2 | 0.85 | specialist_agents.py |
| GlucoseAgent | glucose | 2 | 0.9 | specialist_agents.py |
| NutritionAgent | nutrition | 3 | 0.8 | specialist_agents.py |
| ExerciseAgent | exercise | 3 | 0.75 | specialist_agents.py |
| StressAgent | stress | 2 | 0.8 | specialist_agents.py |
| MentalAgent | mental | 2 | 0.85 | specialist_agents.py |
| TCMAgent | tcm | 3 | 0.75 | specialist_agents.py |
| MotivationAgent | motivation | 3 | 0.7 | specialist_agents.py |
| WeightAgent | weight | 3 | 0.7 | specialist_agents.py |
| CardiacRehabAgent | cardiac_rehab | 2 | 0.8 | specialist_agents.py |
| TrustGuideAgent | trust_guide | 4 | 0.6 | trust_guide_agent.py |
| VisionAgent | vision | 4 | 0.65 | vision_agent.py |
| XZBExpertAgent | xzb_expert | 1 | 0.95 | xzb_expert_agent.py |
| BehaviorCoachAgent | behavior_rx | 1 | 0.9 | behavior_rx/ |
| MetabolicExpertAgent | behavior_rx | 1 | 0.9 | behavior_rx/ |
| CardiacExpertAgent | behavior_rx | 1 | 0.9 | behavior_rx/ |
| AdherenceExpertAgent | behavior_rx | 1 | 0.9 | behavior_rx/ |
| **HealthAssistantAgent** | health_assistant | 5 | 0.65 | user_agents/ |
| **HabitTrackerAgent** | habit_tracker | 5 | 0.6 | user_agents/ |
| **OnboardingGuideAgent** | onboarding_guide | 4 | 0.7 | user_agents/ |

### 请求处理流程

```
用户消息 → InputFilter (安全过滤)
         → MasterAgent.process()
           → AgentRouter.route() (关键词+数据+权重)
           → [Agent1, Agent2, ...].process()
           → MultiAgentCoordinator.coordinate()
           → InterventionPlan (如需)
           → ResponseSynthesizer
         → GenerationGuard (输出安全)
         → 返回响应
```

### API 入口点

```python
# 统一入口 (api/main.py)
from api.main import get_master_agent
ma = get_master_agent()              # 返回 MasterAgent (Registry 版本)
ma.process(user_id, message, ...)    # 主处理
ma.chat(user_id, message)            # 简化聊天
ma.sync_device_data(user_id, data)   # 设备数据同步
ma.submit_assessment(user_id, data)  # 评估提交
```

---

## 🔧 开发规范

### 新增 Agent 检查清单

1. 继承 `BaseAgent`，实现 `process(inp: AgentInput) -> AgentResult`
2. 在 `AgentDomain` 枚举中新增 domain
3. 在 `AGENT_BASE_WEIGHTS` 中设置权重
4. 在 `DOMAIN_CORRELATIONS` 中设置关联领域
5. 在 `startup.py::create_registry()` 中注册
6. 在 `test_consistency.py` 中添加对应测试
7. **绝不修改 CrisisAgent 优先级**

### Git 工作流

```bash
git tag pre-surgery-20260227     # 手术前快照
git tag surgery-complete-20260227 # 手术完成
# 回滚: git checkout pre-surgery-20260227
```

### Docker 操作

```bash
docker-compose build             # 重建镜像
docker-compose up -d             # 启动
docker exec bhp_v3_api pytest tests/test_crisis_smoke.py -v
docker exec bhp_v3_api pytest tests/test_golden_baseline.py -v
docker exec bhp_v3_api pytest tests/test_consistency.py -v
docker logs bhp_v3_api --tail 50 # 查看日志
```

### 环境变量

| 变量 | 值 | 来源 |
|------|-----|------|
| LOG_LEVEL | INFO | docker-compose.yml (必须大写) |
| DATABASE_URL | postgresql://... | .env |
| REDIS_URL | redis://... | .env |

---

## ⚠️ 已知问题 & 技术债

| ID | 问题 | 严重度 | 状态 |
|----|------|--------|------|
| TD-1 | `core/master_agent_v0.py` 6874行遗留代码 | 中 | Phase 4 清退 |
| TD-2 | `core/master_agent_unified.py` stub 仍存在 | 低 | Phase 4 清退 |
| TD-3 | `api/agent_api.py` 多处直接 `MasterAgent()` 实例化 | 中 | Phase 4 统一 |
| TD-4 | `behavior_rx_v32_complete/` 重复目录 | 低 | 可直接删除 |
| TD-5 | `master_agent_merge/` 临时合并代码 | 低 | 可直接删除 |
| TD-6 | HabitTracker streak_days 从 context 读取，mock 测试不匹配 | 低 | 测试修复 |

---

## 📋 下一步规划

| 阶段 | 内容 | 优先级 |
|------|------|--------|
| Phase 4 | v3 import 路径清退 (20个端点迁移) | P1 |
| 加固 | CrisisAgent 安全 pipeline 全链路闭环 | P1 |
| 扩展 | 第二类 Agent (rx_composer/chronic_manager) | P2 |
| 清理 | 删除 behavior_rx_v32_complete/ master_agent_merge/ | P3 |

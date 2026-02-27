# CLAUDE.md — 行健平台 (BehaviorOS) 项目契约

> 最后更新: 2026-02-28 (P3 E2E 联调通过 + Schema 固化)
> Git tag: `e2e-6roles-49-20260228`
> 测试状态: 单元 72/72, E2E 49/49, Schema Gaps=0

## 项目概述

行健平台是一个行为健康促进与慢病逆转平台，采用多 Agent 协作架构，集成传统中医与现代行为科学。

- **项目根目录**: `D:\behavioral-health-project`
- **运行环境**: Docker Compose (Python 3.12 + PostgreSQL + Redis + Qdrant)
- **API 框架**: FastAPI (uvicorn, 端口 8000)
- **容器名**: bhp_v3_api / bhp_v3_worker / bhp_v3_beat
- **路由总量**: 896 endpoints (6 角色覆盖)
- **数据库**: 150+ 表 (public + coach_schema)

---

## 铁律 (NEVER BREAK)

### 1. 危机安全铁律
```
CrisisAgent.priority = 0  (最高优先级，永远第一个执行)
任何涉及自杀/自残关键词 -> 必须返回 risk_level=critical + 热线 400-161-9995
绝不允许任何代码修改降低 CrisisAgent 优先级或绕过危机检测
全链路已验证: InputFilter -> Router -> CrisisAgent -> GenerationGuard
```

### 2. Registry 冻结铁律
```
AgentRegistry.freeze() 调用后，不允许注册新 Agent
所有 Agent 必须在 startup.py::create_registry() 中注册
运行时动态注册 -> 抛出 RegistryFrozenError
```

### 3. 四原则铁律 (Agent 通信)
```
S9.1  单一数据总线: 所有 Agent 通过 MasterAgent.process() 通信
S9.2  领域关联网络: DOMAIN_CORRELATIONS 定义跨领域触发关系
S10.3 冲突消解: CONFLICT_PRIORITY 定义领域优先级
S11.2 策略闸门: PolicyDecision 控制 ALLOW/DELAY/OVERRIDE/DENY
```

### 4. 数据模型对齐铁律
```
MicroActionTask.status in {pending, completed, skipped, expired}
MicroActionTask.source in {coach_assigned, ai_recommended, user_selected, intervention_plan, system}
MicroActionTask.domain in {nutrition, exercise, sleep, emotion, stress, cognitive, social, tcm}
任何新 Agent 读写任务数据必须遵守以上枚举
```

### 5. MasterAgent 统一入口铁律
```
所有代码必须通过 api.main.get_master_agent() 获取 MasterAgent
禁止: from core.master_agent import MasterAgent; MasterAgent()
禁止: from core.master_agent_v0 import MasterAgentV0
允许: from core.master_agent import DeviceData, CGMData...  (纯数据类型引用)
```

---

## 6 角色 E2E 验证矩阵 (P3 新增)

| 角色 | 测试数 | 通过 | 关键端点验证 |
|------|--------|------|-------------|
| Observer | 6/6 | quota/today, segments/permissions, agent/run(trust_guide) |
| Grower | 21/21 | journey, assessment, micro-actions, challenges, credits, learning, content, reflection, agent, chat |
| Sharer | 1/1 | promotion/sharer-check |
| Coach | 7/7 | dashboard(200), students(200), performance(200), pending-reviews |
| Supervisor | 5/5 | audit-log, audit-queue, governance/dashboard(200) |
| Admin | 8/8 | stats(200,154users), users(200), safety/logs(200,18entries), agent/status |
| Crisis | 1/1 | agent/run(observer->trust_guide whitelist, correct) |

### 角色权限隔离验证
```
Coach 端点:     coach 角色 -> 200 (业务数据)
                observer 角色 -> 403 (权限拒绝) 
Admin 端点:     admin 角色 -> 200 (业务数据)
                observer/grower -> 403 (权限拒绝)
Supervisor 端点: supervisor 角色 -> 200 (业务数据)
                 observer 角色 -> 403 (权限拒绝)
```

---

## 数据库 Schema 契约 (P3 新增)

### Enum: userrole (11 值)
```
OBSERVER, GROWER, SHARER, COACH, PROMOTER, SUPERVISOR, MASTER, ADMIN, SYSTEM, PATIENT, INSTITUTION_ADMIN
```

### Schema 拓扑
```
public schema:      ~140 表 (users, journey_states, chat_sessions, content_items, ...)
coach_schema:       ~12 表 (coach_review_items, agent_templates, decision_trace, ...)
```

### Migration 059: Schema 同步 (P3 固化)
```
public.users:                 +5 cols (wx_openid, union_id, wx_miniprogram_openid, preferred_channel, growth_points)
public.content_items:         +1 col  (review_status)
public.expert_tenants:        +7 cols (credential_type, role_confirmed_by/at, activated_at, suspension_count, workspace_ready, role_confirmed)
public.responsibility_metrics: +4 cols (checked_at, value, detail, metric_type)
coach_schema.coach_push_queue: +1 col  (reviewer_id)
coach_schema.agent_templates:  +1 col  (evidence_tier)
coach_schema.stage_transition_logs: table clone from public
18+ 缺失表通过 Base.metadata.create_all 补齐
```

### 运行迁移
```bash
docker exec bhp_v3_api alembic upgrade head    # 正常升级
docker exec bhp_v3_api alembic stamp head      # 标记到最新 (已手动同步时)
```

---

## 项目结构

```
behavioral-health-project/
  api/
    main.py                    # FastAPI 入口 (get_master_agent)
    agent_api.py               # Agent API (统一 get_master_agent)
    expert_agent_api.py        # 专家 Agent API
    auth_api.py                # 认证 (prefix=/api/v1/auth)
  core/
    agents/
      master_agent.py          # MasterAgent (统一版)
      registry.py              # AgentRegistry (freeze 机制)
      router.py                # AgentRouter
      specialist_agents.py     # 12 领域 Agent
      startup.py               # create_registry() 启动入口
      trust_guide_agent.py     # Observer TrustGuide
    safety/
      input_filter.py          # 输入安全过滤
      generation_guard.py      # 输出安全守卫
    models.py                  # ORM 模型 (34+ 表定义)
    register_security.py       # HTTPS 中间件 (ENVIRONMENT=production 时启用)
  v3/routers/
    auth.py                    # v3 认证 (prefix=/api/v3/auth)
  alembic/versions/
    059_schema_sync_e2e.py     # P3 schema 同步 migration
  tests/
    test_crisis_smoke.py       # 危机冒烟 (32/32)
    test_golden_baseline.py    # 金色基线 (8/8)
    test_consistency.py        # 一致性 (32/32)
  e2e_6roles.py                # E2E 6 角色联调脚本 (49/49)
  docker-compose.yml           # ENVIRONMENT=development
  _deprecated/                 # 归档区
```

---

## 认证体系

### 路径
```
注册: POST /api/v1/auth/register  (body: username, password, email, full_name?)
登录: POST /api/v1/auth/login     (body: username, password -> access_token + refresh_token)
v3:   POST /api/v3/auth/register | /login (同字段)
```

### 速率限制
```
注册: ~5 次/分钟/IP (Redis key: rl:register:<ip>)
登录: 10 次/分钟/IP
重置: docker exec bhp_v3_redis redis-cli FLUSHDB
```

---

## Agent 注册表 (21 个)

| Agent | domain | priority | weight | 文件 |
|-------|--------|----------|--------|------|
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
| HealthAssistantAgent | health_assistant | 5 | 0.65 | user_agents/ |
| HabitTrackerAgent | habit_tracker | 5 | 0.6 | user_agents/ |
| OnboardingGuideAgent | onboarding_guide | 4 | 0.7 | user_agents/ |

---

## 开发规范

### 新增 Agent 检查清单
1. 继承 BaseAgent，实现 process(inp: AgentInput) -> AgentResult
2. 在 AgentDomain 枚举中新增 domain
3. 在 AGENT_BASE_WEIGHTS 中设置权重
4. 在 DOMAIN_CORRELATIONS 中设置关联领域
5. 在 startup.py::create_registry() 中注册
6. 在 test_consistency.py 中添加对应测试
7. 绝不修改 CrisisAgent 优先级

### Docker 操作
```bash
docker-compose up -d --force-recreate app     # 重建 API 容器
docker-compose restart app                     # 重启
docker logs bhp_v3_api --tail 30               # 查日志
docker exec bhp_v3_api alembic upgrade head    # 跑迁移
docker exec bhp_v3_redis redis-cli FLUSHDB     # 清限流
```

### HTTPS 注意
```
core/register_security.py: ENVIRONMENT=production 时启用 HTTPSRedirectMiddleware
docker-compose.yml: ENVIRONMENT=development (开发环境禁用 HTTPS 重定向)
```

### Git Tags
```
pre-surgery-20260227        # 手术前快照
surgery-complete-20260227   # 手术完成
cleanup-phase4-20260228     # Phase 4 清退
e2e-6roles-49-20260228      # P3 E2E 全绿
```

---

## 已知问题 (Non-blocking)

| 问题 | 优先级 | 说明 |
|------|--------|------|
| behavior_rx 初始化警告 | 低 | No module named behavior_rx.patches.master_agent_integration (已归档) |
| Redis AUTH 警告 | 低 | 定时任务 Redis 密码配置不匹配 |
| Observer 白名单 | 设计如此 | Observer 只能使用 TrustGuide, 每天限 3 轮 |
| coach/push-queue 404 | 低 | 路由定义缺失，但表已存在 |

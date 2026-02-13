# 行为健康数字平台 — 架构总览

> 版本: v34
> 最后更新: 2026-02-14
> 数据来源: contracts/registry_v2.yaml + 代码实测
> 状态: Celery 全权接管 (Phase C) + 8 容器运行中

---

## 一、平台全景

```
┌─────────────────────────── 用户接入层 ───────────────────────────┐
│                                                                   │
│  Admin Portal     H5 移动端       专家工作台      (Patient App)  │
│  :5174            :5173            :8501            (备用)         │
│  Vue3+AntDesign   Vue3+Vant4      Streamlit                      │
│  127 页面         33 页面          专家督导                       │
│                                                                   │
└──────────┬──────────────┬──────────────┬─────────────────────────┘
           │              │              │
           └──── nginx :80/443 ─────────┘
                         │
┌────────────────────────┼──────────────────────────────────────────┐
│                API 网关层 (FastAPI :8000)                          │
│                                                                    │
│  65 路由模块 · 511+ API 端点 · JWT + RBAC                         │
│  认证 · 用户 · 教练 · 评估 · 设备 · 内容 · 学习 · 挑战          │
│  Agent · 安全 · 策略 · 处方 · 专家 · 问卷 · 考试 · 生态          │
│                                                                    │
│  ┌─ Celery 异步层 ────────────────────────────────────────────┐   │
│  │  16 Beat 定时任务 + 3 事件驱动任务                          │   │
│  │  Worker (prefork, 4 进程) · Beat · Flower :5555             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                核心引擎层                                          │
│                                                                    │
│  MasterAgent (v0 编排 + v6 模板)   PolicyEngine (V007 6层决策)    │
│  12 专业 Agent + 4 专家 Agent      SafetyPipeline (V005 4层)      │
│  BehaviorRx (三维处方)             UnifiedLLMClient (云+本地)      │
│  RAG 知识库 (pgvector 768-dim)     ProgramEngine (V004 监测方案)   │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│                数据层                                              │
│                                                                    │
│  PostgreSQL (pgvector/pg15) :5432    Redis 7 (broker+cache+lock)  │
│  120 张表 · 31 次迁移                Qdrant :6333 (向量存储)       │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 二、核心数字

| 维度 | 数量 | 权威来源 |
|------|------|----------|
| ORM 模型 (去重) | **120 张表** | core/models.py |
| API 端点 (OpenAPI) | **428 operations** | openapi_dump.json |
| API 端点 (静态分析) | **665** (含 baps/v3 独立端点) | 代码扫描 |
| API 路由模块 | **65** | api/main.py include_router |
| Alembic 迁移 | **31** | alembic/versions/ |
| Agent (领域) | **17** | core/agents/ |
| Agent (专家) | **4** | behavior_rx/ |
| Celery Beat 任务 | **16** | api/worker.py |
| Celery 事件任务 | **3** | api/tasks/ |
| 事件处理器 | **40** | core/v14/trigger_router |
| 配置文件 | **60** | configs/ |
| Vue 路由 | **144** | admin-portal + h5 |
| Vue 组件 | **204** | admin-portal + h5 |
| 安全规则 | **11** | core/safety/ |
| Docker 服务 | **8** | docker-compose.yml |
| 专家领域 | **10** | configs/expert_domains.json |

---

## 三、Docker 容器拓扑

```yaml
# 应用容器 (4)
bhp_v3_api:      FastAPI + Uvicorn         :8000   # 主 API
bhp_v3_worker:   Celery Worker (prefork)            # 异步任务执行
bhp_v3_beat:     Celery Beat                        # 定时调度 (16 tasks)
bhp_v3_flower:   Celery Flower             :5555   # 任务监控 Web UI

# 基础设施 (4)
bhp_v3_postgres: pgvector/pgvector:pg15    :5432   # 主数据库
bhp_v3_redis:    Redis 7-alpine                     # Broker(db1) + Backend(db2) + Cache(db0)
bhp_v3_qdrant:   Qdrant                    :6333   # 向量检索
bhp_v3_nginx:    Nginx Alpine              :80/443 # 反向代理

# 关联容器 (docker-compose.app.yaml, 独立管理)
bhp-h5:          H5 前端                   :5173
bhp-admin-portal: Admin 前端               :5174
bhp-expert-workbench: Streamlit            :8501

# Dify 平台 (docker-compose.yaml, 独立管理)
dify-api, dify-web, dify-nginx, dify-worker, dify-db, dify-redis, dify-weaviate, dify-sandbox, dify-ssrf_proxy
```

**网络**: `bhp_network` (bridge) 连接所有 BHP 容器；Dify 使用 `dify_dify-network`。

---

## 四、数据库架构 (120 张表)

### 4.1 表分类统计

| 分类 | 表数 | 代表表 |
|------|------|--------|
| 用户与认证 | 5 | users, user_sessions, token_blacklist |
| 健康数据 | 10 | glucose_readings, heart_rate_readings, sleep_records, blood_pressure_readings, weight_records, activity_records, hrv_readings |
| 评估体系 | 8 | assessments, assessment_results, assessment_sessions, batch_answers |
| 内容与学习 | 12 | content_items, content_likes, content_bookmarks, learning_progress, learning_time_logs, learning_points_logs |
| 教练与消息 | 6 | coach_students, coach_messages, reminders, device_alerts |
| 挑战活动 | 4 | challenge_templates, challenge_enrollments, challenge_checkins |
| 问卷引擎 | 5 | surveys, survey_questions, survey_responses, survey_draft_responses, survey_baps_sync |
| 考试系统 | 4 | exams, exam_questions, exam_sessions, exam_answers |
| 激励体系 (V003) | 9 | badges, user_badges, user_milestones, user_streaks, flip_card_records, nudge_records, user_memorials, point_transactions, user_points |
| 学分与晋级 (V002) | 4 | course_modules, user_credits, companion_relations, promotion_applications |
| 智能方案 (V004) | 3 | program_templates, program_enrollments, program_interactions |
| 安全管理 (V005) | 2 | safety_logs, content_audio |
| Agent 模板 (V006-P1) | 1 | agent_templates |
| 路由配置 (V006-P2) | 1 | tenant_routing_configs |
| 知识共享 (V006-P3) | 1 | knowledge_contributions |
| 反馈学习 (V006-P4) | 3 | agent_feedbacks, agent_metrics_daily, agent_prompt_versions |
| Agent 生态 (V006-P5) | 3 | agent_marketplace_listings, agent_compositions, agent_growth_points |
| 策略引擎 (V007) | 15 | policy_rules, rule_priority, agent_applicability_matrix, conflict_matrix, decision_trace, cost_budget_ledger, expert_domain, intervention_protocol, risk_boundary, stage_applicability, contraindications, evidence_tier_binding, agent_skill_graph, policy_intervention_outcome, policy_stage_transition_log |
| 行为处方 (Rx) | 3 | rx_prescriptions, rx_strategy_templates, agent_handoff_log |
| 专家白标 | 4 | expert_tenants, tenant_clients, tenant_agent_mappings, tenant_themes |
| 知识库 | 4 | knowledge_documents, knowledge_chunks, knowledge_domains |
| 其他 | ~18 | micro_action_tasks, push_queue_items, food_recognition_records, ... |

### 4.2 迁移历史 (31 次)

最近 10 次迁移:

| # | 文件 | 内容 |
|---|------|------|
| 031 | expert_self_registration | expert_tenants +3 列 (application_status/data/applied_at) |
| 030 | behavior_rx_foundation | rx_prescriptions + rx_strategy_templates + agent_handoff_log |
| 029 | skill_graph | V007 Phase B (9 表) |
| 028 | policy_engine | V007 Phase A (6 表) |
| 027 | v002_v003_catchup | 追补 V002(4 表) + V003(9 表) 到 Alembic 链 |
| 026 | agent_ecosystem | V006-P5 (3 表) |
| 025 | agent_feedback | V006-P4 (3 表) |
| 024 | knowledge_sharing | V006-P3 (1 表) |
| 023 | tenant_routing | V006-P2 (1 表) |
| 022 | agent_templates | V006-P1 (1 表) |

---

## 五、API 端点架构 (65 路由模块)

### 5.1 权限分布

| 权限级别 | 端点数 | 说明 |
|----------|--------|------|
| public | 12 | 登录/注册/公开内容/领域列表 |
| any_authenticated | 335 | 登录用户均可访问 |
| coach_or_admin | 96 | 教练 (role>=4) 或管理员 |
| admin_only | 66 | 仅管理员 (role=99) |
| unknown/other | 156 | v3/baps 独立端点 |

### 5.2 核心路由模块

| 模块 | 前缀 | 端点数 | 说明 |
|------|------|--------|------|
| auth_api | /v1/auth | 7 | JWT 登录/注册/刷新/密码/登出 |
| user_api | /v1/users | 8 | Admin 用户 CRUD + 分配 |
| coach_api | /v1/coach | 12 | 教练学员/绩效/健康数据 |
| content_api | /v1/content | 28 | 内容全生命周期 |
| learning_api | /v1/learning | 15 | 积分/时长/排行/统计 |
| agent_api | /v1/agent | 6 | Agent 对话/列表/状态 |
| assessment_api | /v1/assessment | 5 | 评估提交/结果 |
| program_api | /v1/programs | 13 | V004 智能方案 |
| safety_api | /v1/safety | 8 | V005 安全管理 |
| policy_api | /v1/policy | 12 | V007 策略引擎 |
| agent_template_api | /v1/agent-templates | 10 | V006 模板 CRUD |
| expert_registration_api | /v1/expert-registration | 8 | 专家入驻申请/审核 |
| survey_* | /v1/surveys | 16 | 问卷管理/填写/统计 |
| rx_routes | /v1/rx | 8 | 行为处方 |
| agent_ecosystem_api | /v1/agent-ecosystem | 11 | Agent 市场 |

---

## 六、AI Agent 体系

### 6.1 双 MasterAgent 架构

```
                    ┌─ v0 MasterAgent (core/master_agent_v0.py) ─┐
                    │  9 步编排流程 + V005 安全注入               │
用户消息 ──→ API ──→│  hardcoded 12 Agent, no DB dependency       │
                    │  fallback: 永远可用                         │
                    └─────────────────────────────────────────────┘
                              ↑ fallback
                    ┌─ v6 MasterAgent (core/agents/master_agent.py) ─┐
            primary │  12-Agent 模板路由 + tenant_ctx                 │
                    │  DB templates + routing configs + knowledge     │
                    │  V007 PolicyEngine at Step 4                   │
                    │  BehaviorRx ExpertRouter at Step 3.5           │
                    └────────────────────────────────────────────────┘
```

### 6.2 Agent 清单

**领域 Agent (12 内置)**:

| Agent | 领域 | 文件 |
|-------|------|------|
| MetabolicAgent | 代谢/血糖 | core/agents/specialist_agents.py |
| SleepAgent | 睡眠 | core/agents/specialist_agents.py |
| EmotionAgent | 情绪 | core/agents/specialist_agents.py |
| MotivationAgent | 动机 | core/agents/specialist_agents.py |
| CoachingAgent | 教练沟通 | core/agents/specialist_agents.py |
| NutritionAgent | 营养 | core/agents/specialist_agents.py |
| ExerciseAgent | 运动 | core/agents/specialist_agents.py |
| TCMAgent | 中医 | core/agents/specialist_agents.py |
| CrisisAgent | 危机干预 | core/agents/specialist_agents.py |
| BehaviorRxAgent | 行为处方 | core/agents/integrative_agents.py |
| WeightAgent | 体重管理 | core/agents/integrative_agents.py |
| CardiacRehabAgent | 心血管康复 | core/agents/integrative_agents.py |

**专家 Agent (4 BehaviorRx)**:

| Agent | 用途 |
|-------|------|
| BehaviorCoachAgent | TTM S0-S2 阶段行为教练 |
| MetabolicExpertAgent | 代谢领域专家决策 |
| CardiacExpertAgent | 心血管领域专家决策 |
| AdherenceExpertAgent | 依从性管理 |

**动态 Agent**: 通过 agent_templates 表创建，GenericLLMAgent 执行，12 个预置种子。

### 6.3 Agent 路由

```
用户消息 → AgentRouter (keyword + template correlation + tenant overrides)
         → primary agent + correlated agents
         → MultiAgentCoordinator (conflict resolution)
         → MasterAgent orchestration (9 steps)
         → V005 SafetyPipeline (3 injection points)
         → V007 PolicyEngine (rules → candidates → conflict → cost → trace)
```

---

## 七、Celery 异步任务体系

### 7.1 架构

```
┌─── Beat (bhp_v3_beat) ───┐    ┌─── Worker (bhp_v3_worker) ───┐
│  16 cron/interval tasks   │───→│  prefork pool (4 workers)     │
│  celerybeat-schedule      │    │  max_tasks_per_child = 200    │
└───────────────────────────┘    │  acks_late = True             │
                                 │  reject_on_worker_lost = True │
┌─── API (.delay()) ────────┐   │                               │
│  promotion_ceremony       │───→│  SYNC DB Session              │
│  process_event            │   │  Redis distributed lock       │
│  process_event_batch      │   └───────────────────────────────┘
└───────────────────────────┘              │
                                 ┌─────────▼─────────┐
                                 │  Flower :5555      │
                                 │  Web 监控面板      │
                                 └────────────────────┘
```

### 7.2 Beat 任务调度表 (16 任务)

| 任务 | 调度 | 来源 | 防护 |
|------|------|------|------|
| daily_task_generation | cron 06:00 | 迁移 | retry×2 |
| reminder_check | 每 60s | 迁移 | expires=50s + lock |
| expired_task_cleanup | cron 23:00 | 迁移 | retry×2 |
| process_approved_pushes | 每 300s | 迁移 | expires=280s + lock |
| expire_stale_queue_items | cron 06:00 | 迁移 | retry×2 |
| knowledge_freshness_check | cron 07:00 | 迁移 | retry×2 |
| program_advance_day | cron 00:00 | 迁移 | retry×2 |
| program_push_morning | cron 09:00 | 迁移 | — |
| program_push_noon | cron 11:30 | 迁移 | — |
| program_push_evening | cron 17:30 | 迁移 | — |
| program_batch_analysis | cron 23:30 | 迁移 | retry×2 |
| safety_daily_report | cron 02:00 | 迁移 | retry×2 |
| agent_metrics_aggregate | cron 01:00 | 迁移 | retry×2 |
| governance_health_check | cron 23:30 | 新增 | retry×2 |
| coach_challenge_7d_push | cron 09:00 | 新增 | retry×2 |
| expert_program_14d_push | cron 00:05 | 新增 | retry×2 |

### 7.3 Redis 分区

| DB | 用途 |
|----|------|
| 0 | 通用缓存 + APScheduler 锁 |
| 1 | Celery Broker (消息队列) |
| 2 | Celery Result Backend (任务结果) |

---

## 八、安全体系 (V005)

### 8.1 四层 SafetyPipeline

```
用户输入 → L1 InputFilter (关键词+PII+意图)
         → L2 RAGSafety (分级权重+过期)
         → L3 GenerationGuard (注入检测+领域边界)
         → L4 OutputFilter (医学声明+免责+分级)
         → 安全响应
```

### 8.2 UnifiedLLMClient

```
cloud-first: DeepSeek/Qwen/GPT → Ollama fallback (qwen2.5:0.5b)
4 策略: cloud_first | local_first | cloud_only | local_only
```

---

## 九、策略引擎 (V007)

### 5 步决策管道

```
Rules (RuleRegistry, 4 seed rules)
  → Candidates (ApplicabilityMatrix, TTM stage × risk level)
    → Conflict (ConflictResolver, 5 strategies)
      → Cost (CostController, 8 model costs, budget zones, downgrade path)
        → Trace (DecisionTrace, 全链路审计)
```

**4 个种子规则**: crisis_absolute_priority(p=100), medical_boundary_suppress(p=95), cost_daily_limit_default(p=70), early_stage_gentle_intensity(p=60)

---

## 十、专家白标体系

### 10.1 入驻流程

```
H5 ExpertRegister (5步向导) → POST /expert-registration/apply
  → ExpertTenant (status=pending_review)
    → Admin ExpertApplicationReview (审核队列)
      → approve → status=trial, role升级为COACH
      → reject → application_data.reject_reason
```

### 10.2 10 个专家领域

| ID | 名称 | 推荐 Agent | 主题色 |
|----|------|-----------|--------|
| endocrine | 内分泌代谢 | glucose, nutrition, weight, exercise | medicalBlue |
| tcm | 中医养生 | tcm, nutrition, sleep, stress | tcmGreen |
| mental_health | 心理健康 | mental, emotion, sleep, stress | healingPurple |
| cardiac | 心血管康复 | cardiac_rehab, exercise, nutrition, sleep | cardiacRed |
| nutrition | 营养管理 | nutrition, weight, glucose, exercise | default |
| sleep | 睡眠健康 | sleep, stress, mental, exercise | default |
| sports_rehab | 运动康复 | exercise, nutrition, motivation, weight | default |
| weight_management | 体重管理 | weight, nutrition, exercise, motivation | default |
| behavior_change | 行为改变 | behavior_rx, motivation, coaching, mental | warmSand |
| general | 综合健康 | coaching, nutrition, exercise, sleep, motivation | default |

所有领域自动附带 crisis Agent。

### 10.3 Agent 生态市场

```
专家创建 Agent (agent_templates)
  → 发布到市场 (agent_marketplace_listings, status=pending)
    → Admin 审核 → published
      → 其他专家安装 (clone template + tenant_agent_mapping)
        → 成长积分 (7 种事件)
```

---

## 十一、角色与权限

### 六级四同道者体系

```
L0 Observer (1)  → L1 Grower (2)     → L2 Sharer (3)
                    g≥100                g≥500, c≥50

→ L3 Coach (4)      → L4 Promoter (5)    → L5 Master (6)
   g≥800, c≥200,       g≥1500, c≥600,       g≥3000, c≥1500,
   i≥50, exam,          i≥200, exam,          i≥600, exam,
   4comp→L1             4comp→L2              4comp→L3

Admin (99) — 超级管理员
```

**三维积分**: g=成长分, c=贡献分, i=影响力分

### 内容分级

| 级别 | 可见角色 | 示例 |
|------|----------|------|
| T1 | 所有用户 | 公开文章、基础课程 |
| T2 | Grower+ | 进阶内容、AI 对话 |
| T3 | Sharer+ | 专业内容、完整课程 |
| T4 | Expert/Admin | 管理工具、分析看板 |

---

## 十二、前端架构

### Admin Portal (Vue 3 + Ant Design Vue 4)
- **127 页面**, 6+1 Pinia stores
- 角色菜单: Coach(≥4), Expert(≥5), Admin(≥99)
- Vite proxy: `/api` → localhost:8000
- BHP Design System §1-§40

### H5 移动端 (Vue 3 + Vant 4)
- **33 页面**, 3 stores
- 5 Tab: 首页/对话/学习/任务/我的
- 新增: ExpertRegister(5步向导), ExpertApplicationStatus, ExpertHub

### 前端路由守卫现状
- 显式 role 守卫: 2 条
- 仅 requiresAuth: 43 条
- 无守卫: 99 条
- **已知缺口**: 后端 162 个受限端点在前端无拦截 (GAP-001)

---

## 十三、配置文件体系 (60 文件)

| 目录 | 文件 | 用途 |
|------|------|------|
| configs/ | expert_domains.json | 10 领域 → 推荐 Agent + 主题色 |
| configs/ | agent_templates_seed.json | 12 预置 Agent 模板 |
| configs/ | glucose-14d-template.json | V004 血糖 14 天方案模板 |
| configs/ | safety_keywords.json | 4 类安全关键词 |
| configs/ | safety_rules.json | 安全规则阈值/分级 |
| configs/ | milestones.json | 里程碑配置 |
| configs/ | badges.json | 徽章配置 |
| configs/ | point_events.json | 积分事件配置 |
| configs/ | promotion_rules.json | 晋级规则 |
| configs/ | course_modules.json | 课程模块配置 |
| configs/ | rx_strategies.json | 12 行为策略模板 |

---

## 十四、已知缺口与待办

| ID | 领域 | 严重度 | 状态 | 描述 |
|----|------|--------|------|------|
| GAP-001 | 前端路由守卫 | Medium | pending | 144 路由中仅 2 条 role 守卫 |
| GAP-002 | OpenAPI 覆盖差异 | Low | known | 静态 665 vs OpenAPI 428 |
| GAP-003 | Pydantic Schema 去重 | Low | known | 319 schemas 跨文件重复 |
| GAP-004 | 治理任务业务逻辑 | Medium | in_progress | 3 个 Celery 任务为框架代码 |
| GAP-005 | behavior_rx 旧副本 | Low | known | behavior_rx_v32_complete 已从提取排除 |

---

## 十五、版本演进

| 版本 | 日期 | 核心内容 | 表/端点增量 |
|------|------|----------|-------------|
| V001 | 2026-02 | 基础平台 (Auth+CRUD+Agent) | ~40 表, ~200 端点 |
| V002 | 2026-02-08 | 学分制晋级体系 | +4 表, +20 端点 |
| V003 | 2026-02-09 | 激励体系 (徽章/里程碑/连续签到) | +9 表, +11 端点 |
| V004 | 2026-02-09 | 智能监测方案 (血糖 14 天) | +3 表, +13 端点 |
| V005 | 2026-02-11 | 云 LLM + 安全管道 + TTS | +2 表, +8 端点 |
| V006-P1 | 2026-02-12 | Agent 模板化 | +1 表, +10 端点 |
| V006-P2~P5 | 2026-02-12 | 八爪鱼架构 (路由/共享/反馈/生态) | +8 表, +42 端点 |
| V007 | 2026-02-12 | 策略引擎 | +15 表, +12 端点 |
| Rx | 2026-02-13 | 行为处方基座 | +3 表, +8 端点 |
| Expert-Reg | 2026-02-13 | 专家自助注册 | +3 列, +8 端点 |
| Celery | 2026-02-14 | APScheduler→Celery 迁移 | 0 表, +16 beat tasks |

---

## 十六、运维手册速查

### 启动/停止
```bash
# BHP 核心 (8 容器)
cd D:\behavioral-health-project
docker-compose up -d
docker-compose down

# BHP 前端 (3 容器)
docker-compose -f docker-compose.app.yaml up -d

# Dify (9 容器)
docker-compose -f docker-compose.yaml up -d
```

### Celery 监控
```bash
# Flower Web UI
http://localhost:5555

# Worker 日志
docker logs -f bhp_v3_worker

# Beat 日志
docker logs -f bhp_v3_beat
```

### Celery 切换 (.env 修改后重启)
```bash
# Phase A: APScheduler 主力
USE_CELERY=false
DISABLE_APSCHEDULER=false

# Phase B: Celery 主力, APScheduler 待命
USE_CELERY=true
DISABLE_APSCHEDULER=false

# Phase C: Celery 全权 (当前)
USE_CELERY=true
DISABLE_APSCHEDULER=true
```

### 数据库
```bash
# 迁移
cd D:\behavioral-health-project
alembic upgrade head

# 连接
psql -h localhost -U bhp_user -d bhp_db -p 5432
```

### API 健康检查
```bash
curl http://localhost:8000/health
curl http://localhost:8000/docs    # Swagger UI
```

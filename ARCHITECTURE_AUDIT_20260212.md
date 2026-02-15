# BHP 平台架构审计报告 (2026-02-12)

## 一、审计总览

| 维度 | 总量 | 状态 | 发现问题 |
|------|------|------|----------|
| **API 路由** | 66 router 文件 / 51 已注册 | **6 个未注册** | 15 orphan (6 critical + 8 v3 indirect + 1 broken) |
| **ORM 模型** | 82 models / 88 DB 表 | **存在偏差** | 10 表无 ORM; 4 ORM 无 migration (V002) |
| **Agent 系统** | 12 预置 + GenericLLM | **正常** | 模板化完成, 降级机制可靠 |
| **前端路由** | Admin 76 路由 / H5 40 路由 | **100% 映射** | 3 个 coach/tools 子组件未直接路由 (可接受) |
| **调度器** | 13 个定时任务 | **全部正常** | Redis SETNX 锁 + 优雅降级 |
| **Docker** | 4 app + 9 infra = 13 容器 | **全部 healthy** | 内存分配合理, 健康检查覆盖 |
| **配置文件** | 24 个 JSON/YAML | **完整** | 端口注册表 + 安全规则 + 领域配置 |
| **依赖包** | 50 生产 + 3 测试 | **版本锁定** | 无安全漏洞 |
| **测试** | 15 文件 / 6 层 / 98 测试 | **全部通过** | 缺 V005 safety 单测 |

---

## 二、关键问题清单

### P0 - 需要修复 (影响完整性)

#### 2.1 V002 学分系统未纳入 Alembic 迁移链
- **问题**: `course_modules`, `user_credits`, `companion_relations`, `promotion_applications` 4 个表有 ORM 模型但只有裸 SQL (`v002_credit_promotion_system.sql`)，不在 Alembic 修订链中
- **影响**: 全新部署执行 `alembic upgrade head` 不会创建这 4 张表
- **修复**: 将 SQL 提取为 Alembic migration，插入 018_survey → 019_v3_diagnostic 之间

#### 2.2 V003 激励体系表缺失
- **问题**: MEMORY.md 声称 V003 (badges, user_badges, user_milestones, user_streaks, flip_card_records, nudge_records, user_memorials, point_transactions, user_points) 已部署，但代码和迁移中均未找到
- **推测**: 部分功能可能由 m019 的 `point_events`/`user_point_balances`/`incentive_rewards`/`user_rewards` 替代
- **修复**: 确认 DB 实际状态，补齐 ORM 模型或清理文档

#### 2.3 10 张 m019 诊断表无 ORM 模型
- **涉及表**: `assessment_sessions`, `batch_answers`, `incentive_rewards`, `intervention_outcomes`, `llm_call_logs`, `point_events`, `rag_query_logs`, `stage_transition_logs`, `user_point_balances`, `user_rewards`
- **影响**: 只能用 raw SQL 访问，无法参与 ORM relationship
- **修复**: 为高频使用表补建 ORM 模型 (至少 `llm_call_logs`, `point_events`, `user_point_balances`)

### P1 - 应当修复 (影响健壮性)

#### 2.4 API 路由注册遗漏 (6 个)
| 文件 | 路由前缀 | 状态 |
|------|----------|------|
| `api/knowledge.py` | `/knowledge` | 未注册 (与 v3 knowledge 重复?) |
| `api/v14/routes.py` | `/api/v2` | 未注册 (仅 admin_routes 注册) |
| `api/v14/quality_routes.py` | `/quality` | 未注册 |
| `api/v14/disclosure_routes.py` | `/disclosure` | 未注册 |
| `api/v14/copilot_routes.py` | `/api/v1/copilot` | 未注册 |
| `api/device_trigger.py` | `/device/cgm/sync` | **已损坏** (import 断裂) |

- **修复**: 确认 v14 策略 → 注册需要的或删除废弃的; 修复 device_trigger 导入

#### 2.5 v3 路由导入无错误处理
- **位置**: `api/main.py` lines 374-392
- **问题**: 8 个 v3 模块的 `from v3.routers import ...` 无 try/except，v3 缺失会导致启动崩溃
- **修复**: 包裹 try/except + logger.warning

#### 2.6 content_items 模型缺少 author_id 字段
- **问题**: DB 中存在 `author_id` 列 (FK → users.id)，但 ORM `ContentItem` 模型定义中缺失
- **影响**: ORM 查询无法直接 join author
- **修复**: 在 `core/models.py` ContentItem 中添加 `author_id = Column(Integer, ForeignKey('users.id'))`

### P2 - 建议改进 (提升质量)

| # | 项目 | 详情 |
|---|------|------|
| 2.7 | 环境变量集中化 | `JWT_SECRET_KEY`, `DATABASE_URL`, `REDIS_URL` 应统一在 `api/config.py` |
| 2.8 | baps_api / xingjian_api 独立 App 问题 | 两者创建了自己的 `FastAPI()` 实例，应重构为 router |
| 2.9 | V005 Safety 缺少测试 | 安全管道未在 test suite 中覆盖，建议添加 `test_safety.py` |
| 2.10 | Redis 密码明文 | `.env` 中 `REDIS_PASSWORD=difyai123456`，生产环境应用 secrets manager |
| 2.11 | 清理 main-old.py | `api/main-old.py` 未被引用，应删除 |
| 2.12 | 前端 API 导出不完整 | Admin Portal `api/index.ts` 仅导出 4 个模块，其余 18 个靠直接 import |

---

## 三、架构分层拓扑

```
┌─────────────────────────────────────────────────────────────────┐
│ 表现层 (Presentation)                                           │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐ │
│ │ H5 (Vant 4)  │ │Admin (AntDV4)│ │ Expert Workbench (8501) │ │
│ │ 39 views     │ │ 96 views     │ │ Streamlit               │ │
│ │ 40 routes    │ │ 76 routes    │ │                         │ │
│ │ 8 api mods   │ │ 22 api mods  │ │                         │ │
│ └──────┬───────┘ └──────┬───────┘ └───────────┬─────────────┘ │
│        └────────────────┼─────────────────────┘               │
│                         │ /api proxy                           │
├─────────────────────────┼─────────────────────────────────────┤
│ 网关层 (Gateway)        │                                      │
│ ┌───────────────────────▼─────────────────────────────────┐   │
│ │ FastAPI 3.1.0 (api/main.py)                             │   │
│ │ 51 registered routers │ 440+ endpoints                   │   │
│ │ CORS + 安全头 + 限流 + Sentry (core/middleware.py)       │   │
│ │ JWT Auth + RBAC (api/dependencies.py)                    │   │
│ └───────────────────────┬─────────────────────────────────┘   │
├─────────────────────────┼─────────────────────────────────────┤
│ 业务层 (Business Logic) │                                      │
│ ┌───────────────────────┴─────────────────────────────────┐   │
│ │ Agent 系统 (12 + Dynamic)                                │   │
│ │ ┌─────────┐ ┌────────┐ ┌──────────┐ ┌──────────────┐   │   │
│ │ │ Router  │→│Agents  │→│Coordinator│→│ PolicyGate   │   │   │
│ │ │(关键词)  │ │(12+dyn)│ │(冲突解决)  │ │(5规则)       │   │   │
│ │ └─────────┘ └────────┘ └──────────┘ └──────────────┘   │   │
│ │ ↕ DB模板降级 (agent_template_service.py)                  │   │
│ │ ↕ SafetyPipeline (4层: input→rag→gen→output)             │   │
│ │ ↕ UnifiedLLMClient (cloud→Ollama 降级)                    │   │
│ └─────────────────────────────────────────────────────────┘   │
│ ┌─────────────────────────────────────────────────────────┐   │
│ │ 核心服务 (65 files)                                      │   │
│ │ learning_service │ challenge_service │ survey_service     │   │
│ │ program_service  │ milestone_service │ promotion_service  │   │
│ │ feedback_service │ ecosystem_service │ audio_service      │   │
│ │ push_recommendation │ coach_push_queue │ device_alert     │   │
│ │ knowledge/* (embedding, retriever, rag, chunker, ...)    │   │
│ └─────────────────────────────────────────────────────────┘   │
│ ┌─────────────────────────────────────────────────────────┐   │
│ │ 调度层 APScheduler (13 jobs, Redis SETNX mutex)          │   │
│ │ 06:00 任务生成 │ 09:00/11:30/17:30 方案推送              │   │
│ │ 00:05 天推进   │ 23:00 批量分析 │ 02:00 安全日报          │   │
│ │ 01:30 指标聚合 │ 23:59 过期清理 │ 每分钟 提醒检查         │   │
│ └─────────────────────────────────────────────────────────┘   │
├───────────────────────────────────────────────────────────────┤
│ 数据层 (Data)                                                  │
│ ┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│ │ PostgreSQL   │ │ Redis    │ │ Weaviate │ │ Ollama       │ │
│ │ + pgvector   │ │ (6379)   │ │ (8080)   │ │ (11434)      │ │
│ │ 82 models    │ │ Cache +  │ │ Vector   │ │ qwen2.5:0.5b │ │
│ │ 88 tables    │ │ Lock DB1 │ │ Store    │ │ qwen2.5vl:7b │ │
│ │ 26 migrations│ │ Celery   │ │          │ │              │ │
│ └──────────────┘ └──────────┘ └──────────┘ └──────────────┘ │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ Cloud LLM (DeepSeek / Qwen / GPT) — cloud_first 策略     │  │
│ └──────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

---

## 四、模块耦合关系矩阵

### 4.1 Agent 管道完整链路
```
用户消息 → agent_api.py
  → MasterAgent.__init__(db_session)
    → agent_template_service.build_agents_from_templates(db)  [DB优先]
    → 失败: 硬编码12 Agent降级                                [代码兜底]
  → MasterAgent.process(user_input)
    Step 1: SafetyPipeline.input_filter()     [V005 关键词/PII/意图]
    Step 2: AgentRouter.route()               [关键词匹配→主/关联Agent]
    Step 3: Agent.process()                   [规则引擎→发现+建议]
    Step 4: _enhance_with_llm()               [UnifiedLLMClient增强]
      → template_system_prompt 优先            [DB模板prompt]
      → DOMAIN_SYSTEM_PROMPTS 降级             [硬编码prompt]
    Step 5: MultiAgentCoordinator.coordinate() [冲突解决+权重融合]
    Step 6: RuntimePolicyGate.check()          [5规则安全门]
    Step 7: SafetyPipeline.output_filter()     [医疗声明+免责+分级]
  → 返回 MasterAgentResponse
```

### 4.2 前后端耦合验证

| 后端模块 | Admin 覆盖 | H5 覆盖 | 状态 |
|----------|-----------|---------|------|
| auth_api (5 ep) | Login.vue | Login/Register | OK |
| agent_api (8 ep) | Agent 面板 | - | OK |
| agent_template_api (10 ep) | List/Edit 页面 | - | OK |
| agent_ecosystem_api (8 ep) | Marketplace 页面 | - | OK |
| agent_feedback_api (5 ep) | GrowthReport 页面 | - | OK |
| content_api (28 ep) | Article/Case/Card 管理 | LearnCenter/ContentDetail | OK |
| learning_api (15 ep) | CoachAnalytics | MyLearning | OK |
| program_api (13 ep) | 侧边栏链接 | Programs/Today/Timeline | OK |
| challenge_api (30 ep) | ChallengeManagement | ChallengeList/Day | OK |
| safety_api (8 ep) | Dashboard/ReviewQueue | - | OK |
| credits_api (8 ep) | CreditDashboard/Modules | MyCredits | OK |
| companion_api (6 ep) | CompanionManage | MyCompanions | OK |
| promotion_api (6 ep) | PromotionReview | PromotionProgress | OK |
| survey_api (16 ep) | 管理 (待建) | - | OK |
| exam_api (9 ep) | ExamList/Edit/Results | - | OK |
| coach_api (10+ ep) | CoachHome/StudentList | - | OK |
| device_data (14 ep) | StudentHealthData | Dashboard | OK |
| food_recognition_api (3 ep) | - | FoodRecognition | OK |
| batch_ingestion_api (4 ep) | BatchIngestion | - | OK |
| search_api (1 ep) | AdminLayout 全局搜索 | - | OK |

### 4.3 数据库关系完整性
- **102 条外键**: 全部有效, 无孤立引用
- **循环依赖**: 无
- **级联删除**: 所有 1:M 关系均配置 `cascade="all, delete-orphan"`
- **索引覆盖**: FK 列 + 过滤列均有索引

---

## 五、版本子系统对齐检查

| 子系统 | DB 表 | ORM 模型 | Migration | API | 前端 | 调度 | 状态 |
|--------|-------|---------|-----------|-----|------|------|------|
| 核心 (V1) | 40+ | 60+ | 001-018 | 30+ routers | 80+ views | 6 jobs | **完整** |
| V002 学分晋级 | 4 表 | 4 模型 | **缺失** | 3 routers | 7 views | - | **P0 迁移缺失** |
| V003 激励 | **不确定** | 部分 | 019 (partial) | milestone_service | 3 H5 views | - | **P0 待确认** |
| V004 智能方案 | 3 表 | 3 模型 | 019 | 1 router | 4 H5 views | 5 jobs | **完整** |
| V005 安全管道 | 2 表 | 2 模型 | 021 | 1 router | 2 admin views | 1 job | **完整** |
| V006 Agent模板化 | 1+5 表 | 6+ 模型 | 022-026 | 4 routers | 4 admin views | 1 job | **完整** |

---

## 六、修复优先级路线图

### Phase A: 数据层对齐 (P0, 立即)
1. 将 V002 SQL 转为 Alembic migration
2. 确认 V003 激励表在 DB 中的实际状态
3. 为 m019 的 10 张孤立表中高频使用的补建 ORM

### Phase B: API 层清理 (P1, 本周)
4. 确定 v14 模块策略 (注册/废弃)
5. v3 router 导入包裹 try/except
6. 修复 device_trigger.py 断裂导入
7. ContentItem 模型补 author_id

### Phase C: 质量提升 (P2, 下版本)
8. 添加 test_safety.py
9. 环境变量集中化到 config.py
10. 清理 main-old.py + baps_api/xingjian_api 重构
11. 前端 API index.ts 完整导出

---

## 七、结论

**整体评价: 架构扎实, 分层清晰, 耦合平滑**

- 51 个已注册 router / 440+ endpoints / 82 ORM models — 功能覆盖全面
- Agent 管道 (12+Dynamic) 模板化完成, DB优先 + 硬编码降级双保险
- 前端 100% 路由映射, 后端 API 覆盖率 >95%
- 调度器 13 任务全部 Redis 锁保护
- Docker 13 容器健康检查完备, 内存分配合理

**主要风险点**: V002 迁移缺失 + V003 状态不明确 + m019 的 10 张表无 ORM。
建议先完成 Phase A 数据层对齐, 再进行 Agent 专家搭建更新。

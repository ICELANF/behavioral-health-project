# 行健平台 (BehaviorOS) — 平台架构总览

> 生成时间: 2026-03-02
> API版本: 896 endpoints | 21 Agents | 150+ 数据表 | 6 角色 RBAC

---

## 1. 系统拓扑

```
┌─────────────────────────────────────────────────────────────────────┐
│                         客户端层                                     │
├───────────────────┬──────────────────┬──────────────────────────────┤
│  WeChat 小程序     │   H5 Web App     │   Admin Portal              │
│  coach-miniprogram│   h5-patient-app │   admin-portal               │
│  uni-app+Vue3+TS  │   Vite+Vue3+Vant │   Vite+Vue3+AntDesign       │
│  (mp-weixin)      │   (:5175)        │                              │
└───────────────────┴──────────────────┴──────────────────────────────┘
                              │ HTTPS / WebSocket
┌─────────────────────────────────────────────────────────────────────┐
│                    Nginx 反向代理 (:80/:443)                         │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────────┐
│               FastAPI 网关  (bhp_v3_api :8000)                      │
│  api/main.py → 50+ Router 注册 → 896 端点                           │
│  中间件: CORS · JWT Auth · Rate Limit · Sentry · HTTPS(prod)        │
└──────────┬──────────────────┬──────────────────┬────────────────────┘
           │                  │                  │
   ┌───────▼───────┐  ┌──────▼───────┐  ┌───────▼──────┐
   │ Agent Pipeline │  │ Celery Worker│  │ Celery Beat  │
   │ 21 Agents      │  │ 异步任务      │  │ 定时调度      │
   │ MasterAgent    │  │ bhp_v3_worker│  │ bhp_v3_beat  │
   └───────┬───────┘  └──────┬───────┘  └──────────────┘
           │                  │
┌──────────▼──────────────────▼───────────────────────────────────────┐
│                        数据层                                        │
├─────────────────┬──────────────────┬───────────────────────────────┤
│  PostgreSQL     │  Redis 7         │  Qdrant                       │
│  pgvector:pg15  │  缓存+消息队列    │  向量搜索                      │
│  150+ 表        │  限流计数器       │  RAG 知识库                    │
│  :5432          │  :6379           │  :6333                        │
└─────────────────┴──────────────────┴───────────────────────────────┘
```

---

## 2. Agent 架构 (21 个注册 Agent)

### 2.1 处理管线 (9 步)

```
用户输入
  │
  ├─❶─→ InputFilter (安全关键词检测)
  ├─❷─→ CrisisAgent (priority=0, 危机筛查)
  ├─❸─→ AgentRouter (关键词+设备数据匹配)
  ├─❹─→ 并行执行: 主 Agent + 关联 Agent
  ├─❺─→ MultiAgentCoordinator (冲突消解)
  ├─❻─→ Risk Assessment (跨域风险合成)
  ├─❼─→ PolicyGate (ALLOW/DELAY/OVERRIDE/DENY)
  ├─❽─→ ActionPlan → MicroActionTask 生成
  └─❾─→ DailyBriefing 推送
```

### 2.2 Agent 分层

| 层级 | Priority | Agent | 领域 | 权重 |
|------|----------|-------|------|------|
| **T0 安全** | 0 | CrisisAgent | crisis | 1.0 |
| **T1 专科** | 1 | XZBExpertAgent | xzb_expert | 0.95 |
| | 1 | BehaviorCoachAgent | behavior_rx | 0.9 |
| | 1 | MetabolicExpertAgent | behavior_rx | 0.9 |
| | 1 | CardiacExpertAgent | behavior_rx | 0.9 |
| | 1 | AdherenceExpertAgent | behavior_rx | 0.9 |
| **T2 领域** | 2 | GlucoseAgent | glucose | 0.9 |
| | 2 | SleepAgent | sleep | 0.85 |
| | 2 | StressAgent | stress | 0.8 |
| | 2 | MentalAgent | mental | 0.85 |
| | 2 | CardiacRehabAgent | cardiac_rehab | 0.8 |
| **T3 通用** | 3 | NutritionAgent | nutrition | 0.8 |
| | 3 | ExerciseAgent | exercise | 0.75 |
| | 3 | TCMAgent | tcm | 0.75 |
| | 3 | MotivationAgent | motivation | 0.7 |
| | 3 | WeightAgent | weight | 0.7 |
| **T4 用户** | 4 | TrustGuideAgent | trust_guide | 0.6 |
| | 4 | VisionAgent | vision | 0.65 |
| | 4 | OnboardingGuideAgent | onboarding_guide | 0.7 |
| | 5 | HealthAssistantAgent | health_assistant | 0.65 |
| | 5 | HabitTrackerAgent | habit_tracker | 0.6 |

### 2.3 领域关联网络

```
sleep ←→ glucose ←→ nutrition
  ↕         ↕          ↕
stress ←→ exercise ←→ weight
  ↕         ↕
mental ←→ behavior_rx ←→ motivation
  ↕
crisis ←→ mental ←→ stress
  ↕
tcm ←→ nutrition
```

---

## 3. 数据库 Schema

### 3.1 表分布

| Schema | 表数 | 说明 |
|--------|------|------|
| public | ~140 | users, journey_states, chat_sessions, content_items … |
| coach_schema | ~12 | coach_review_items, agent_templates, decision_trace … |

### 3.2 核心枚举

```
UserRole (11): OBSERVER, GROWER, SHARER, COACH, PROMOTER,
               SUPERVISOR, MASTER, ADMIN, SYSTEM, PATIENT, INSTITUTION_ADMIN

MicroActionTask.status:  pending | completed | skipped | expired
MicroActionTask.source:  coach_assigned | ai_recommended | user_selected | intervention_plan | system
MicroActionTask.domain:  nutrition | exercise | sleep | emotion | stress | cognitive | social | tcm
```

### 3.3 关键表组

| 组 | 表 |
|----|-----|
| 用户 | User, UserDevice, BehavioralProfile, UserSession |
| 评估 | Assessment, AssessmentAssignment, CoachReviewItem |
| 健康数据 | GlucoseReading, HeartRateReading, HRVReading, SleepRecord, ActivityRecord |
| 任务 | MicroActionTask, MicroActionLog, Intervention, Reminder |
| 内容 | ContentItem, ChallengeTemplate, ChallengeDayPush |
| 通信 | ChatSession, ChatMessage, CoachMessage |

---

## 4. API 路由结构 (896 端点)

### 4.1 核心路由前缀

```
/api/v1/auth           认证 (register, login, refresh, me)
/api/v1/coach          教练 (dashboard, students, analytics, reviews)
/api/v1/assessment*    评估 (assignments, review-list, assign)
/api/v1/content        内容 (recommendations, learning, contribution)
/api/v1/micro-actions  微行动 (today, list, update)
/api/v1/daily-tasks    每日任务 (today, upcoming)
/api/v1/agent          Agent (run, status, feedback)
/api/v1/challenges     挑战 (enrollment, progress)
/api/v1/segments       分群 (user segmentation)
/api/v1/interventions  干预 (plans, execution)
/api/v1/admin          管理 (analytics, users, safety)
/api/v1/supervision    督导 (audit-log, governance)
/api/chat              聊天 (WebSocket + REST)
/api/v3/*              V3 新版 (auth, health, assessment)
```

### 4.2 角色权限矩阵

| 端点组 | Observer | Grower | Coach | Supervisor | Admin |
|--------|----------|--------|-------|------------|-------|
| auth/* | ✓ | ✓ | ✓ | ✓ | ✓ |
| micro-actions | ✗ | ✓ | ✓ | ✗ | ✓ |
| coach/* | ✗ | ✗ | ✓ | ✗ | ✓ |
| supervision/* | ✗ | ✗ | ✗ | ✓ | ✓ |
| admin/* | ✗ | ✗ | ✗ | ✗ | ✓ |
| agent/run | 白名单 | ✓ | ✓ | ✓ | ✓ |

---

## 5. 前端应用矩阵

### 5.1 Coach 小程序 (coach-miniprogram)

```
技术栈: uni-app 3.0 + Vue 3 + Pinia + TypeScript
构建:   npm run build:mp-weixin → dist/build/mp-weixin/
HTTP:   src/api/request.ts (JWT auto-refresh, token queue)
配置:   src/config/env.ts (API_BASE 环境感知)

页面模块:
  pages/auth/         登录 · 注册
  pages/home/         首页仪表盘 (双模式: grower/coach)
  pages/coach/
    ├── dashboard/    教练总览
    ├── students/     学员列表 · 详情
    ├── assessment/   评估管理 · 审核
    ├── analytics/    数据分析
    ├── flywheel/     AI 飞轮审核
    ├── messages/     消息中心
    ├── risk/         风险管理
    ├── push-queue/   推送队列
    └── live/         直播 (占位)
  pages/profile/      个人中心
  pages/notifications/ 消息通知

分包 (subPackages):
  learning/           课程 · 视频播放
  assessment/         评估作答 · 结果
  exam/               考试系统
  journey/            晋级旅程
  companions/         同伴网络
  certification/      证书认证
```

### 5.2 其他前端

| 应用 | 路径 | 技术 | 用途 |
|------|------|------|------|
| H5 Patient | h5-patient-app/ | Vite+Vue3+Vant | 患者端 Web |
| Admin Portal | admin-portal/ | Vite+Vue3+AntDesign | 管理后台 |
| BehaviorOS | behaviros-frontend/ | Vite+Vue3+ECharts | 数据分析 |

---

## 6. Docker 服务编排

```yaml
bhp_v3_api:       FastAPI         :8000   ENVIRONMENT=development
bhp_v3_worker:    Celery Worker           异步任务处理
bhp_v3_beat:      Celery Beat             定时任务调度
bhp_v3_flower:    Flower          :5555   任务监控面板
bhp_v3_postgres:  PostgreSQL+pgvector :5432
bhp_v3_redis:     Redis 7         :6379   缓存 + Broker
bhp_v3_qdrant:    Qdrant          :6333   向量数据库
bhp_v3_nginx:     Nginx           :80/:443 反向代理

Network: bhp_network (bridge)
Volumes: bhp_db_data, bhp_qdrant_data
```

---

## 7. 安全治理

### 7.1 铁律 (5 条)

1. **危机安全**: CrisisAgent.priority=0, 检测到自杀/自残 → risk_level=critical + 热线 400-161-9995
2. **Registry 冻结**: freeze() 后禁止运行时注册新 Agent
3. **四原则通信**: 单一数据总线 · 领域关联 · 冲突消解 · 策略闸门
4. **数据模型对齐**: MicroActionTask 枚举严格约束
5. **统一入口**: 所有代码通过 api.main.get_master_agent() 获取 MasterAgent

### 7.2 安全链路

```
InputFilter → CrisisAgent → GenerationGuard
   (输入)        (检测)         (输出)
```

---

## 8. 数据流契约

### AgentInput → AgentResult

```
AgentInput {                    AgentResult {
  user_id: str                    agent_domain: AgentDomain
  message: str                    confidence: 0.0~1.0
  profile: dict                   risk_level: RiskLevel
  device_data: {                  findings: List[str]
    sleep_hours, glucose,         recommendations: List[str]
    hrv, steps, ...               tasks: List[MicroActionTask]
  }                               metadata: dict
  context: dict                   llm_enhanced: bool
  session_id: str                 llm_latency_ms: int
}                               }
```

---

## 9. 关键文件索引

| 文件 | 行数 | 说明 |
|------|------|------|
| api/main.py | 2000+ | FastAPI 入口, 路由注册 |
| api/coach_api.py | 56KB | 教练端全部路由 |
| api/agent_api.py | 28KB | Agent 端点 |
| core/agents/master_agent.py | 666 | 统一 MasterAgent |
| core/agents/startup.py | — | create_registry() 启动 |
| core/agents/specialist_agents.py | — | 9 领域 Agent |
| core/models.py | — | 148 ORM 模型 |
| alembic/versions/059_*.py | — | 最新 migration |
| coach-miniprogram/src/api/request.ts | 164 | HTTP 封装 (JWT refresh) |
| coach-miniprogram/src/config/env.ts | 13 | API 地址配置 |

---

## 10. 常用运维命令

```bash
# 后端
docker-compose up -d --force-recreate app
docker exec bhp_v3_api alembic upgrade head
docker logs bhp_v3_api --tail 50
docker exec bhp_v3_redis redis-cli FLUSHDB

# 小程序
cd coach-miniprogram
npm run build:mp-weixin          # 生产构建
npm run dev:mp-weixin            # 开发模式 (热更新)
rm -rf dist/build/mp-weixin/*    # 清理构建缓存
```

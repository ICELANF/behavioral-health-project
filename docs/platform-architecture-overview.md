# 行为健康数字平台 — 架构总览

> 最后更新: 2026-03-07
> 版本: v30 (5前端矩阵 + 知识库v4.0 + 8角色体系 + 1001路由)
> 分支: stabilize-from-sprint1 | HEAD: a994c10

---

## 一、平台全景架构图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            用户接入层 (5 Frontend Apps)                         │
│                                                                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ coach-mini     │  │ h5 (bhp-h5)    │  │ h5-behavior  │  │ vision-guard   │  │
│  │ WeChat小程序   │  │ Vant H5        │  │ 行为测评H5   │  │ 青少年视力H5  │  │
│  │ uni-app+Vue3   │  │ Vue3+Vant4     │  │ Vue3+Vite    │  │ Vue3+Vite     │  │
│  │ 48页面         │  │ 74页面         │  │ 独立测评     │  │ 独立产品线    │  │
│  │ Priority 1     │  │ 含/staff后台   │  │              │  │ Priority 5    │  │
│  └───────┬────────┘  └───────┬────────┘  └──────┬───────┘  └───────┬────────┘  │
│          │                   │                   │                  │           │
│  ┌───────┴───────────────────┴───────────────────┴──────────────────┘           │
│  │ xzb-workstation (行知宝教练工作台, Vue3)                                     │
│  └───────┬──────────────────────────────────────────────────────────            │
│          │ 统一 nginx 反代 /api → :8000                                         │
└──────────┼──────────────────────────────────────────────────────────────────────┘
           │ HTTP / WebSocket
┌──────────┼──────────────────────────────────────────────────────────────────────┐
│          ▼     API 网关层 (FastAPI :8000)                                       │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │  主 API 网关 (bhp_v3_api)                                                │   │
│  │  FastAPI + Uvicorn + Celery + APScheduler                                │   │
│  │                                                                          │   │
│  │  156 API模块 · 1001 路由端点 · 21 Agent · 155+ 数据表 · 8 Schema         │   │
│  │                                                                          │   │
│  │  认证 ─── 用户管理 ─── 教练端 ─── 评估 ─── 微行动 ─── 挑战活动          │   │
│  │  设备 ─── 预警 ─── 消息 ─── 提醒 ─── 内容 ─── 学习激励                  │   │
│  │  推送队列 ─── 搜索 ─── Agent协作 ─── AI推送 ─── 食物识别                │   │
│  │  专家租户 ─── 考试系统 ─── 题库 ─── 问卷引擎 ─── 批量灌注              │   │
│  │  学分管理 ─── 同道者 ─── 晋级系统 ─── 激励体系 ─── 智能监测方案        │   │
│  │  健康数据审核 ─── 飞轮AI ─── 音频处理 ─── 反作弊                        │   │
│  └──────────────────────────────┬───────────────────────────────────────────┘   │
│                                 │                                               │
│  ┌──────────────────────────────┴───────────────────────────────────────────┐   │
│  │                      核心引擎层 (Core Engines)                           │   │
│  │                                                                          │   │
│  │  ┌──────────────┐ ┌────────────────┐ ┌───────────────┐ ┌─────────────┐  │   │
│  │  │ MasterAgent  │ │ 评估管道       │ │ Brain引擎     │ │ BAPS体系    │  │   │
│  │  │ 9步协调流程  │ │ BAPS→Profile   │ │ StageRuntime  │ │ 4大量表     │  │   │
│  │  │ 21 Agent     │ │ →Stage→Interv  │ │ PolicyGate    │ │ 评分+报告   │  │   │
│  │  └──────────────┘ └────────────────┘ └───────────────┘ └─────────────┘  │   │
│  │                                                                          │   │
│  │  ┌──────────────┐ ┌────────────────┐ ┌───────────────┐ ┌─────────────┐  │   │
│  │  │ RAG知识库    │ │ 推送审批网关   │ │ 设备预警服务  │ │ 晋级引擎    │  │   │
│  │  │ Qdrant 1024d │ │ 四队列体系     │ │ 阈值+去重     │ │ 四维校验    │  │   │
│  │  │ 1441 vectors │ │ 统一审批入口   │ │ 双通知        │ │ 8角色层级   │  │   │
│  │  └──────────────┘ └────────────────┘ └───────────────┘ └─────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────┴──────────────────────────────────────────────┐
│                          AI / LLM 层 (Intelligence)                             │
│                                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────────┐  │
│  │ Ollama :11434    │  │ Claude API       │  │ DashScope (生产Embedding)    │  │
│  │ qwen2.5:14b      │  │ 高级推理/生成    │  │ text-embedding-v3            │  │
│  │ mxbai-embed-large│  │                  │  │ 1024维                       │  │
│  │ 1024维嵌入       │  │                  │  │                              │  │
│  └──────────────────┘  └──────────────────┘  └──────────────────────────────┘  │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────┴──────────────────────────────────────────────┐
│                            数据层 (Data)                                        │
│                                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ PostgreSQL   │  │ Redis        │  │ Qdrant       │  │ 文件存储      │        │
│  │ :5432        │  │ :6379        │  │ :6333        │  │ knowledge/    │        │
│  │ 155+表       │  │ 会话缓存     │  │ bhp_knowledge│  │ 8域+底座      │        │
│  │ 8 schemas    │  │ Token黑名单  │  │ 1441 vectors │  │ v4.0规范      │        │
│  │ pgvector扩展 │  │ 调度互斥锁   │  │ 1024维Cosine │  │              │        │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、Docker 运行架构

### 2.1 应用服务 (`docker-compose.yml`)

| 服务名 | 容器名 | 端口 | 说明 |
|--------|--------|------|------|
| **app** | bhp_v3_api | 8000 | 主API网关 (唯一入口) |
| **db** | bhp_v3_postgres | 5432 | PostgreSQL 15 + pgvector |
| **redis** | bhp_v3_redis | 6379 | 缓存/锁/Token黑名单 |
| **qdrant** | bhp_v3_qdrant | 6333 | 向量数据库 |
| **worker** | bhp_v3_worker | - | Celery异步任务 |
| **beat** | bhp_v3_beat | - | 定时任务调度 |
| **flower** | bhp_v3_flower | 5555 | 任务监控面板 |
| **nginx** | bhp_v3_nginx | 80/443 | 反向代理 |

`docker-compose.app.yaml` → 前端Stack (ON-DEMAND, 默认不启动)

### 2.2 环境变量

```
.env.example          # 提交Git，仅含KEY名称+说明
.env.bhp              # 本地开发，含真实本地值 (gitignored)

关键配置:
  LLM_ROUTE_STRATEGY: cloud_first(生产) / local_first(本地)
  EMBEDDING_PROVIDER: dashscope(生产) / ollama(本地)
  代码入口: core/llm_client.py:UnifiedLLMClient
            core/knowledge/embedding_service.py:EmbeddingService
```

---

## 三、8角色层级体系

```
观察者 observer (L0, power=1)
  ↓ 注册即获得
成长者 grower (L1, power=2)
  ↓ 完成基础评估
分享者 sharer (L2, power=3)
  ↓ 累计学分+带教4名grower
教练 coach (L3, power=4)
  ↓ 教练认证考试+实践时长
推广者 promoter (L4, power=5) / 督导 supervisor (L4, power=5)
  ↓ 培养4名coach+高级课程学分
大师 master (L5, power=6)
  ↓ 三层审核 (≥2位master确认)
管理员 admin (L99, power=99)

权限守卫 (api/dependencies.py):
  get_current_user       → 解析JWT返回当前用户
  require_admin          → role_level >= 99
  require_coach_or_admin → role_level >= 4
```

### 晋级四维校验

| 维度 | 检查内容 |
|------|---------|
| 学分 | 必修课+选修课学分达标 |
| 积分 | 成长积分/贡献积分/影响力积分 |
| 同道者 | 四同道制: 带教4名下级角色 |
| 实践 | 实践时长/案例数/考试通过 |

### 三层审核流

```
L1审核 (教练/promoter): 自动化校验+教练确认
L2审核 (supervisor): 督导复核
L3审核 (master): ≥2位master确认 → 晋级生效
```

---

## 四、TTM 7阶段模型 (平台定制)

| 阶段 | 代码 | 含义 | 关键动作 |
|------|------|------|---------|
| S0 | authorization | 授权入门 | 注册、知情同意 |
| S1 | awareness | 认知觉醒 | 健康教育、风险认知 |
| S2 | trial | 尝试体验 | 首次行为尝试、微行动 |
| S3 | pathway | 路径确立 | 个性化方案、教练匹配 |
| S4 | internalization | 内化巩固 | 习惯建立、自我监测 |
| S5 | graduation | 毕业自主 | 脱离教练依赖、同伴支持 |
| S6 | transcendence | 超越传播 | 成为教练/分享者 |

### 三层价值架构

```
L1 痛苦解决 (S0-S2): 症状缓解、风险降低
L2 环境适应 (S3-S4): 习惯建立、社会支持
L3 成长超越 (S5-S6): 意义发现、身份转化、传播影响
```

---

## 五、前端应用矩阵

### 5.1 coach-miniprogram (教练培养小程序) — Priority 1

**uni-app + Vue3 + TypeScript → 微信小程序**

```
src/
├── api/          # 8个模块, 48端点
│   ├── request.ts    # 唯一HTTP模块
│   ├── auth.ts       # 6端点
│   ├── coach.ts      # 9端点
│   ├── assessment.ts # 4端点
│   ├── companion.ts  # 6端点
│   ├── exam.ts       # 7端点
│   ├── journey.ts    # 4端点
│   ├── learning.ts   # 7端点
│   └── profile.ts    # 7端点
├── config/env.ts     # DEV: localhost:8000 / PROD: api.xingjian.health
├── pages/
│   ├── home/         # 5角色动态渲染 (coach/grower/sharer/supervisor/master)
│   ├── coach/        # dashboard, students, flywheel, health-review, messages等
│   ├── learning/     # 课程学习
│   ├── exam/         # 认证考试
│   ├── journey/      # 晋级旅程
│   ├── companions/   # 同道者管理
│   ├── assessment/   # 评估管理
│   ├── health/       # 健康数据 (血糖/体重/运动/设备)
│   ├── food/         # 食物拍照识别+饮食日记
│   ├── sharer/       # 分享者功能
│   ├── supervisor/   # 督导功能
│   └── master/       # 大师功能
├── utils/scales.ts   # 量表注册表 (唯一真相源)
└── pages.json        # 编译器读这个 (不是根目录)
```

前后端合约: **42/42 = 100%** 覆盖

### 5.2 h5 (bhp-h5) — Priority 2

**Vue3 + Vite + Vant4, 端口3002**

```
公众三角色路径:
  Observer (观察者) → Grower (成长者) → Sharer (分享者)

员工管理后台 (/staff/*):
  StaffLayout (左侧栏+顶栏) → 21页面
  ├── coach/      9页 (教练管理)
  ├── supervisor/ 4页 (督导管理)
  ├── master/     4页 (大师管理)
  └── admin/      2页 (管理员)
  路由守卫: token + STAFF_ROLES

主要页面:
  登录/注册 → Portal → 健康档案 → 账户设置
  学分晋级 → 同道者 → 晋级进度
  学习中心 → 内容详情 → 食物识别
  行为评估 → 我的阶段 → 我的计划
  挑战活动 → 教练目录 → 知识投稿
```

### 5.3 h5-behavior (行为健康测评)

**Vue3 + Vite, 独立应用**

```
流程: 场景选择 → 问答填写 → AI分析 → 行为画像 → 处方推荐
支持: 填空题 + 语音输入
后端: 画像数据落库
```

### 5.4 vision-guard (青少年视力科学使用)

**Vue3 + Vite, 独立产品线 (Priority 5)**

### 5.5 xzb-workstation (行知宝教练工作台)

**Vue3, 教练专用桌面工作台**

---

## 六、Multi-Agent 系统

### 6.1 21个Agent (4层架构)

```
L0 危机层 (最高优先级):
  └── 危机干预Agent (crisis) — 高风险识别与即时干预

L1 专科层:
  ├── 代谢管理Agent (metabolic)    — 血糖/体重/代谢分析
  ├── 睡眠管理Agent (sleep)        — 睡眠质量/作息优化
  ├── 营养管理Agent (nutrition)    — 膳食分析/营养建议
  ├── 运动康复Agent (exercise)     — 运动方案/康复指导
  ├── 心脏康复Agent (cardiac_rehab) — 心血管康复/术后
  └── 体重管理Agent (weight)       — 减重方案/身体成分

L2 领域层:
  ├── 情绪管理Agent (emotion)      — 情绪评估/压力管理
  ├── 动机激励Agent (motivation)   — 行为动机/阶段推进
  ├── 行为处方Agent (behavior_rx)  — 习惯干预/依从性
  ├── 中医养生Agent (tcm)          — 体质分析/养生建议
  └── 教练风格Agent (coaching)     — 统一输出风格合成

L3 用户层:
  └── (前端对话/Agent路由/反馈收集)
```

### 6.2 MasterAgent 9步处理流程

```
Step 1-2: 接收用户输入/设备数据
Step 3:   更新 User Master Profile
Step 4:   Agent Router → 问题类型 + 风险优先级
Step 4.5: 数据洞察生成
Step 5-6: 调用专业Agent + Multi-Agent Coordinator整合
Step 7:   Intervention Planner → 个性化干预路径
Step 8:   Response Synthesizer → 统一教练风格输出
Step 9:   写回Profile + 生成今日任务/追踪点
```

### 6.3 LLM路由策略

```
UnifiedLLMClient (core/llm_client.py):
  LLM_ROUTE_STRATEGY = cloud_first → Claude API优先, Ollama fallback
  LLM_ROUTE_STRATEGY = local_first → Ollama优先, Claude fallback

EmbeddingService (core/knowledge/embedding_service.py):
  EMBEDDING_PROVIDER = ollama    → mxbai-embed-large:latest (本地, 1024维)
  EMBEDDING_PROVIDER = dashscope → text-embedding-v3 (生产, 1024维)
```

---

## 七、BAPS 评估体系

**平台核心竞争力** — 四维行为评估框架:

| 量表 | 题数 | 评估维度 | 产出 |
|------|------|---------|------|
| **大五人格** BigFive | 50 | 外向性/神经质/尽责性/宜人性/开放性 | 人格基线画像 |
| **BPT-6 行为分型** | 18 | 执行型/知识型/情绪型/关系型/环境型/矛盾型 | 行为改变模式 |
| **CAPACITY 改变力** | 32 | 意识/自主/匹配/资源/承诺/认同/时间/期望 | 改变准备度 |
| **SPI 成功指数** | 50 | 动机30%/能力25%/支持20%/环境15%/历史10% | 成功率预测 |

**评估管道:**

```
BAPS四维评估(150题)
  ↓
评分引擎 (scoring_engine.py) — 反向计分/维度分析/星级/交叉
  ↓
BehavioralProfile — 统一行为画像
  ↓
StageRuntimeBuilder — TTM 7阶段判定(S0→S6)
  ↓
InterventionMatcher — 域干预匹配(rx_library)
  ↓
MicroActionService — 每日微行动生成
  ↓
教练审核(CoachReviewQueue) → 推送给学员
```

---

## 八、四审核队列体系

| 队列 | 数据表 | 触发源 | 审核角色 | 前端入口 |
|------|--------|--------|---------|---------|
| 待审评估 | assessment_assignments | 学员提交量表 | 教练 | coach/assessment |
| 待审AI计划 | coach_review_queue | 飞轮AI生成+save-plan | 教练 | coach/flywheel |
| 待审健康数据 | health_review_queue | 设备/录入数据 | 教练/督导/专家 | coach/health-review |
| 待审处方 | coach_push_queue | 系统/挑战/设备 | 教练 | coach/push-queue |

### 推送审批网关

```
数据源:
  挑战每日推送 / 设备预警 / 微行动到期 / AI推送建议 / Agent分析结果
      ↓ 汇入
  CoachPushQueue (pending)
      ↓
  教练审批 (approve/modify/reject)
      ↓
  CoachMessage(学员消息) + Reminder(定时提醒)
      ↓
  学员收到通知 (Notifications页)
```

---

## 九、RAG 知识库系统

### 9.1 知识库目录结构 (v4.0规范)

```
knowledge/
├── base/                    # L1底座 (ki_id以BASE-开头, scope=global)
│   ├── ttm_stages.md        # TTM 7阶段模型
│   ├── bpt6_dimensions.md   # BPT-6行为画像
│   ├── bfr_framework.md     # BFR框架
│   ├── crisis_protocol.md   # 危机协议
│   ├── three_layer_value.md # 三层价值架构
│   ├── six_layer_model.md   # 六层模型
│   ├── m_action_principles.md # M行动原则
│   └── metabolic_redlines.md  # 代谢红线
├── kb_clinical/             # L2临床 (diabetes, CGM, lifestyle medicine)
├── kb_tcm/                  # L2中医 (体质, 内经, 养生)
├── kb_theory/               # L2理论框架
│   ├── behavioral/          # 行为改变 (BCT, Fogg, BCW, addiction)
│   ├── psychology/          # 心理学 (人格, 生物心理, 情绪)
│   └── growth/              # 成长超越 (PERMA, ACT, Frankl, Possible Selves)
├── kb_dietary_intervention/ # L2饮食干预 (食养指南)
├── kb_ops/                  # L2运营
├── kb_products/             # L2产品
├── kb_case_studies/         # L2案例
└── vector_chunks/           # 预分块文件
```

### 9.2 向量数据库 (Qdrant)

| 配置 | 值 |
|------|---|
| Collection | bhp_knowledge |
| 维度 | 1024 (mxbai-embed-large / text-embedding-v3) |
| 距离函数 | Cosine |
| 当前向量数 | ~1441 |
| Payload字段 | ki_id, domain, layer, scope, evidence_level, ttm_stages, source_file |

### 9.3 RAG检索管道

```
用户查询 → Embedding(1024维)
  ↓
Qdrant检索: top_k=5, score_threshold=0.35
  ↓
scope_boost + priority_adj + freshness_penalty
  ↓
max_context=3000 chars → 注入LLM上下文
  ↓
引用标注 (KnowledgeCitation)
```

### 9.4 知识库v4.0规范

- 所有KI文件遵循 `docs/BHP知识库建设及管理规则_完整版_v4.0.md`
- HTML注释头: `<!-- ki_id | domain | layer | scope | evidence_level | ttm_stages -->`
- 证据分层: T1(RCT/指南) → T2(综述/专著) → T3(专家共识) → T4(平台经验)
- 成长超越域(growth)需额外4字段: growth_dimension, reflection_prompts, identity_bridge, applicable_life_events
- BASE-前缀文件必须放入 knowledge/base/

---

## 十、数据库架构

### 10.1 8个Schema

| Schema | 用途 | 主要表 |
|--------|------|--------|
| public | 核心业务 | users, assessments, behavioral_profiles, micro_action_tasks, content_items... |
| coach_schema | 教练业务 | coach_push_queue, coach_review_queue, health_review_queue... |
| journey_schema | 晋级旅程 | promotion_applications, companion_relations, course_modules, user_credits... |
| behavior_rx | 行为处方 | rx_library, rx_assignments... |
| ecosystem | 生态系统 | badges, user_badges, user_milestones, user_streaks... |
| expert_tenant | 专家白标 | expert_tenants, tenant_clients, tenant_agent_mappings... |
| integration | 集成 | device_bindings, device_alerts... |
| metadata | 元数据 | knowledge_documents, knowledge_chunks, knowledge_citations, knowledge_domains... |

### 10.2 认证

```
JWT Token (python-jose + passlib/bcrypt)
├── access_token (30min)
├── refresh_token (7d)
└── token_blacklist (登出即失效)
```

### 10.3 定时任务 (APScheduler, Redis互斥锁)

| 任务 | 触发 | 说明 |
|------|------|------|
| daily_task_generation | 每天 06:00 | 生成今日微行动 |
| reminder_check | 每 1 分钟 | 检查到期提醒 |
| expired_task_cleanup | 每天 23:59 | 标记过期任务 |
| process_approved_pushes | 每 5 分钟 | 投递已审批推送 |
| expire_stale_queue_items | 每天 06:30 | 清理72h超时 |
| knowledge_freshness_check | 每天 07:00 | 过期知识降权 |
| advance_program_day | 每天 00:05 | V004方案推进 |
| push_morning | 每天 09:00 | 早间推送(认知) |
| push_noon | 每天 11:30 | 午间推送(行为) |
| push_evening | 每天 17:30 | 晚间推送(反思) |
| batch_analysis | 每天 23:00 | 行为数据批量分析 |

---

## 十一、数据流向

### 11.1 设备数据流

```
可穿戴设备/CGM
  ↓ 数据上传
DeviceRestAPI → 存储到各Reading表
  ↓
DeviceAlertService → 阈值检测
  ├── 超阈值 → DeviceAlert + 去重(1h) + 双通知(用户+教练)
  │              └── 进入 CoachPushQueue
  └── 正常 → 存储
  ↓
DeviceBehaviorBridge → 映射设备数据 → 自动完成微行动
```

### 11.2 评估数据流

```
学员填写评估 → AssessmentAPI → BehavioralProfileService
  ↓
StageRuntime + PolicyGate → TTM阶段判定
  ↓
InterventionMatcher → 域干预方案
  ↓
教练审核 (assessment_assignments, status: pending→completed→reviewed→pushed)
  ↓
推送给学员
```

### 11.3 教练干预流

```
教练首页4张卡:
  待审评估(紫) → /assessment-assignments/coach-list?status=completed
  待审AI计划(蓝) → /coach/review-queue?status=pending
  待审健康数据(红) → /health-review/queue?reviewer_role=coach
  待审处方(绿) → /coach/push-queue?status=pending

今日待办(三方案合并):
  紧急审核 → priority=urgent 浮出
  重点学员 → R3高危 或 days_since_last_contact>=3
  我的成长 → 在途学习(1条) + 近期考试(1条)
```

---

## 十二、系统监控端点

| 端点 | 用途 |
|------|------|
| GET /api/v1/system/routes | 1001路由审计 |
| GET /api/v1/system/health | DB+Redis+路由综合健康 |
| GET /api/v1/system/routes/frontend-contract | 42端点合约 100%覆盖 |
| GET /api/v1/system/agents/health | Agent+Ollama+Qdrant检查 |

---

## 十三、技术栈总览

| 层 | 技术 |
|----|------|
| **前端 (小程序)** | uni-app + Vue3 + TypeScript |
| **前端 (H5/Web)** | Vue3 + Vite + Vant4 / 原生组件 |
| **后端** | Python 3.11 + FastAPI + Uvicorn |
| **ORM** | SQLAlchemy + Alembic |
| **数据库** | PostgreSQL 15 + pgvector + Redis 7 + Qdrant |
| **认证** | JWT (python-jose) + bcrypt (passlib) + Token黑名单 |
| **任务队列** | Celery + Redis (Worker + Beat) |
| **定时任务** | APScheduler (Redis互斥锁) |
| **Embedding** | mxbai-embed-large:latest (本地) / text-embedding-v3 (生产), 1024维 |
| **LLM** | Ollama (qwen2.5:14b) + Claude API, UnifiedLLMClient路由 |
| **容器** | Docker Compose (8服务) |
| **反向代理** | nginx |

---

## 十四、量化统计

| 指标 | 数值 |
|------|------|
| API路由端点 | 1001 |
| API模块 (.py) | 156 |
| 数据库表 | 155+ |
| 数据库Schema | 8 |
| 前端应用 | 5 (小程序+H5+行为H5+视力H5+工作台) |
| 前后端合约覆盖 | 42/42 = 100% |
| 专业Agent | 21 |
| BAPS评估题目 | 150题 (4量表) |
| 角色层级 | 8级 (observer→admin) |
| TTM阶段 | 7 (S0→S6) |
| 向量数据库向量数 | ~1441 (1024维) |
| 知识库域 | 8 (base+clinical+tcm+theory+dietary+ops+products+cases) |
| 证据分层 | 4级 (T1→T4) |
| 定时任务 | 11 (Redis互斥锁) |
| 审核队列 | 4 (评估/AI计划/健康数据/处方) |

---

## 十五、五大业务线

```
Priority 1: 教练培养体系 (Coach Training) ← 当前焦点
  → coach-miniprogram + 后端核心API

Priority 2: 公众三角色 H5 (Observer/Grower/Sharer)
  → h5 应用 + 成长路径

Priority 3: 专科专家 Agent (Expert AI Tools)
  → 21 Agent + 白标平台

Priority 4: 行业渠道 (B2B Channels)
  → 专家租户 + API开放

Priority 5: 青少年视力 (Youth Vision)
  → vision-guard 独立产品线
```

---

## 十六、系统状态

### 已运行 ✅

- 1001 API路由 · 156模块 · 全部注册
- JWT认证 + 8级RBAC
- 21 Agent + MasterAgent 9步流程
- BAPS 四维评估体系
- 四审核队列体系
- RAG知识库 (Qdrant 1441向量, 1024维)
- 前后端合约 42/42 = 100%
- 知识库v4.0规范 (8域+底座)
- 学分制晋级 + 同道者管理
- 激励体系 (徽章/签到/里程碑)
- 内容治理 (T1-T4分层/审核/投稿)
- 考试系统 + 问卷引擎
- 设备预警 + 推送审批网关
- Docker 8容器稳定运行
- 5前端应用矩阵

### 待优化 🔲

| 模块 | 说明 | 优先级 |
|------|------|--------|
| Agent真实LLM调用 | 部分Agent fallback模拟结果 | 🟡 中 |
| 生产部署 | SSL/域名/日志/监控 | 🟡 中 |
| 微信登录生产对接 | 当前dev mode | 🟡 中 |
| 性能优化 | 索引/缓存/分页 | 🟢 低 |

---

*文档维护: 此文档与 CLAUDE.md 保持同步更新。详细开发规范见 CLAUDE.md。*

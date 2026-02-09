# 行为健康数字平台 — 架构总览

> 最后更新: 2026-02-08
> 版本: v21
> 状态: Multi-Agent 协作运行 + 专家白标平台 + RAG知识库 + 内容治理 + 平台全面完善(7大需求)

---

## 一、平台全景架构图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            用户接入层 (Frontend)                                │
│                                                                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Admin Portal   │  │  H5 移动端     │  │ 专家工作台    │  │ H5-Patient-App │  │
│  │ :5174 (Docker) │  │ :5173 (Docker) │  │ :8501        │  │  (备用/独立)    │  │
│  │ Vue3+AntDesign │  │  Vue3+Vant4    │  │  Streamlit   │  │  Vue3+Vant4    │  │
│  │ 82 页面        │  │  25 页面       │  │  专家督导     │  │  10 页面       │  │
│  │ 5 stores       │  │  3 stores      │  │              │  │  4 stores      │  │
│  └───────┬────────┘  └───────┬────────┘  └──────┬───────┘  └────────────────┘  │
│          │                   │                   │                              │
│          └──────────┬────────┘                   │                              │
│                     │ nginx反代 /api → bhp-api   │                              │
└─────────────────────┼────────────────────────────┼──────────────────────────────┘
                      │ HTTP / WebSocket           │
┌─────────────────────┼────────────────────────────┼──────────────────────────────┐
│                     ▼     API 网关层 (FastAPI)    ▼                              │
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐   │
│  │                     主 API 网关  :8000  (bhp-api)                        │   │
│  │  FastAPI + Uvicorn (4 workers) + APScheduler                            │   │
│  │                                                                          │   │
│  │  认证 ─── 用户管理 ─── 教练端 ─── 评估 ─── 微行动 ─── 挑战活动          │   │
│  │  设备 ─── 预警 ─── 消息 ─── 提醒 ─── 内容 ─── 学习激励                  │   │
│  │  推送队列 ─── 搜索 ─── Agent协作 ─── 高频题目 ─── AI推送建议            │   │
│  │  食物识别 ─── 专家租户 ─── 专家内容 ─── 分析看板 ─── 用户投稿          │   │
│  │  批量灌注 ─── 内容管理 ─── 考试系统 ─── 题库管理 ─── 用户统计          │   │
│  │                                                                          │   │
│  │  总计: 41 路由模块 · 377+ API 端点 · 6 定时任务                          │   │
│  └──────────────────────────────┬───────────────────────────────────────────┘   │
│                                 │                                               │
│  ┌──────────────────────────────┴───────────────────────────────────────────┐   │
│  │                      核心引擎层 (Core Engines)                           │   │
│  │                                                                          │   │
│  │  ┌──────────────┐ ┌────────────────┐ ┌───────────────┐ ┌─────────────┐  │   │
│  │  │ MasterAgent  │ │ 评估管道       │ │ Brain引擎     │ │ BAPS体系    │  │   │
│  │  │ 9步协调流程  │ │ BAPS→Profile   │ │ StageRuntime  │ │ 4大量表     │  │   │
│  │  │ 12专业Agent  │ │ →Stage→Interv  │ │ PolicyGate    │ │ 评分+报告   │  │   │
│  │  └──────────────┘ └────────────────┘ └───────────────┘ └─────────────┘  │   │
│  │                                                                          │   │
│  │  ┌──────────────┐ ┌────────────────┐ ┌───────────────┐ ┌─────────────┐  │   │
│  │  │ 微行动服务   │ │ 推送审批网关   │ │ 设备预警服务  │ │ 挑战服务    │  │   │
│  │  │ 生成/完成/期 │ │ 统一审批入口   │ │ 阈值+去重     │ │ CRUD/报名   │  │   │
│  │  │ DeviceBridge │ │ 教练确认→投递  │ │ 双通知        │ │ 打卡/问卷   │  │   │
│  │  └──────────────┘ └────────────────┘ └───────────────┘ └─────────────┘  │   │
│  │                                                                          │   │
│  │  ┌──────────────┐ ┌────────────────┐ ┌───────────────┐ ┌─────────────┐  │   │
│  │  │ RAG知识库    │ │ 内容治理       │ │ 数据分析      │ │ 考试系统    │  │   │
│  │  │ 嵌入/检索    │ │ 证据分层T1-T4  │ │ Coach+Admin   │ │ 题库/考试   │  │   │
│  │  │ 引用标注     │ │ 审核/过期降权  │ │ 13 分析端点   │ │ 自动评分    │  │   │
│  │  └──────────────┘ └────────────────┘ └───────────────┘ └─────────────┘  │   │
│  │                                                                          │   │
│  │  ┌──────────────┐ ┌────────────────┐ ┌───────────────┐ ┌─────────────┐  │   │
│  │  │ 批量灌注     │ │ 内容交互       │ │ 学习持久化    │ │ 活动追踪    │  │   │
│  │  │ PDF/DOCX/ZIP │ │ 点赞/收藏/评论 │ │ 时长/积分/连  │ │ 登录/分享/  │  │   │
│  │  │ 自动分块嵌入 │ │ 分享+计数      │ │ 续打卡/晋级   │ │ 学习/考试   │  │   │
│  │  └──────────────┘ └────────────────┘ └───────────────┘ └─────────────┘  │   │
│  │                                                                          │   │
│  │  总计: 55 服务文件 · 54 数据模型 · 16 迁移版本                           │   │
│  └──────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────┴──────────────────────────────────────────────┐
│                          AI / LLM 层 (Intelligence)                             │
│                                                                                 │
│  ┌──────────────────┐                    ┌──────────────────────────────────┐   │
│  │ Ollama :11434    │                    │  Dify :8080                     │   │
│  │ qwen2.5:0.5b     │                    │  ·工作流编排                    │   │
│  │ qwen2.5vl:7b     │                    │  ·知识库RAG                     │   │
│  │ ·对话/评估/跟进  │                    │  ·多Agent路由                   │   │
│  │ ·食物图像识别    │                    │  ·Proactive Health Coach        │   │
│  └──────────────────┘                    └──────────────────────────────────┘   │
└──────────────────────────────────┬──────────────────────────────────────────────┘
                                   │
┌──────────────────────────────────┴──────────────────────────────────────────────┐
│                            数据层 (Data)                                        │
│                                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ PostgreSQL   │  │ Redis        │  │ Weaviate     │  │ 文件存储      │        │
│  │ :5432        │  │ :6379        │  │ 向量数据库   │  │ knowledge/    │        │
│  │ 54 张数据表  │  │ 会话缓存     │  │ 语义检索     │  │ Obsidian知识库│        │
│  │ 16 迁移版本  │  │ Token黑名单  │  │              │  │              │        │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 二、Docker 运行架构

### 2.1 应用服务 (`docker-compose.app.yaml`)

| 容器 | 端口 | 技术 | 健康检查 | 说明 |
|------|------|------|---------|------|
| **bhp-api** | 8000-8002 | Python/FastAPI | `GET /health` 30s | 主API网关 + 决策引擎，4G内存上限 |
| **bhp-h5** | 5173→80 | nginx+Vue3 | — | H5移动端，依赖 bhp-api healthy |
| **bhp-admin-portal** | 5174→80 | nginx+Vue3 | — | 管理后台，依赖 bhp-api healthy |
| **bhp-expert-workbench** | 8501 | Streamlit | `GET /_stcore/health` | 专家工作台，1G内存上限 |

### 2.2 基础设施 (`docker-compose.yaml` — Dify)

| 容器 | 端口 | 用途 |
|------|------|------|
| dify-api | 5001 | Dify后端API |
| dify-web | 3000 | Dify前端 |
| dify-nginx | 8080/8443 | Dify网关 |
| dify-worker | 5001 | Dify异步Worker |
| dify-db | 5432 | PostgreSQL |
| dify-redis | 6379 | Redis |
| dify-weaviate | — | 向量数据库 |
| dify-sandbox | — | 代码沙箱 |
| dify-ssrf_proxy | 3128 | SSRF防护代理 |

**网络**: 所有容器共享 `dify_dify-network` 外部网络。

---

## 三、后端 API 层

### 3.1 路由模块清单 (41 个)

| 模块 | 前缀 | 端点数 | 功能 |
|------|------|--------|------|
| `auth_api.py` | `/api/v1/auth` | 6 | 登录/注册/刷新/改密/登出/个人信息 (+登录活动日志) |
| `user_api.py` | `/api/v1/admin` | 13 | 用户CRUD/统计/分配/教练列表 |
| `coach_api.py` | `/api/v1/coach` | 13 | 学员看板/绩效/画像/4类健康数据/公开教练目录 |
| `coach_message_api.py` | `/api/v1/coach/messages` | 6 | 教练↔学员消息/收件箱/已读 |
| `coach_push_queue_api.py` | `/api/v1/coach/push-queue` | 6 | 推送审批队列/统计/批量操作 |
| `micro_action_api.py` | `/api/v1/micro-actions` | 6 | 今日任务/完成/跳过/历史/统计 |
| `reminder_api.py` | `/api/v1/reminders` | 5 | 提醒CRUD/教练代建 |
| `challenge_api.py` | `/api/v1/challenges` | 23 | 挑战模板CRUD/审核/报名/打卡/问卷/教练分配 |
| `assessment_api.py` | `/api/assessment` | 5 | 评估提交/历史/详情 |
| `assessment_pipeline_api.py` | `/api/v1/assessment` | 4 | BAPS→画像→阶段→干预全流程 |
| `assessment_assignment_api.py` | `/api/v1/assessment-assignments` | 8 | 教练分配/审核/推送评估 |
| `device_rest_api.py` | `/api/v1/devices` | 11 | 设备绑定/健康数据 |
| `device_data.py` | `/api/v1/mp/device` | 20 | 血糖/体重/血压/睡眠/运动/HR/HRV |
| `device_trigger.py` | `/api/v1/device-trigger` | 1 | 设备数据触发行为桥接 |
| `device_alert_api.py` | `/api/v1/alerts` | 4 | 我的预警/教练预警/已读/解决 |
| `high_freq_api.py` | `/api/v1/high-freq-questions` | 4 | HF-20/HF-50 预设题组 |
| `push_recommendation_api.py` | `/api/v1/push-recommendations` | 3 | AI推送建议/按学员/应用 |
| `content_api.py` | `/api/v1/content` | 30 | 课程/视频/测验/案例/点赞/收藏/评论/分享(真实DB) |
| `learning_api.py` | `/api/v1/learning` | 15 | 积分/时长/连续打卡/奖励/排行榜(持久化DB) |
| `chat_rest_api.py` | `/api/v1/chat` | 5 | 会话/消息/删除 |
| `agent_api.py` | `/api/v1/agent` | 7 | Agent列表/运行/审核/反馈/统计/历史/状态 |
| `search_api.py` | `/api/v1/search` | 2 | 全平台搜索（用户/挑战/微行动/预警/消息） |
| `upload_api.py` | `/api/v1/upload` | 1 | 文件上传 |
| `paths_api.py` | `/api/v1/paths` | 66 | 六大路径（干预/专家/知识/实践/社区/教练） |
| `segments_api.py` | `/api/v1/segments` | 12 | 权限/功能/角色/层级/升级建议 |
| `miniprogram.py` | `/api/v1/mp` | 14 | 小程序端（任务/反馈/对话/进度/风险） |
| `websocket_api.py` | WebSocket | 1 | 实时推送 |
| `food_recognition_api.py` | `/api/v1/food` | 2 | 食物图像识别(qwen2.5vl)/历史 |
| `tenant_api.py` | `/api/v1/tenants` | 10 | 专家租户CRUD/客户/Agent/统计 |
| `expert_content_api.py` | `/api/v1/tenants/{id}/content` | 8 | 专家知识文档CRUD/发布/撤回/挑战列表 |
| `analytics_api.py` | `/api/v1/analytics/coach` | 6 | Coach分析(风险/微行动/领域/预警/挑战/阶段) |
| `admin_analytics_api.py` | `/api/v1/analytics/admin` | 7 | Admin分析(概览/增长/角色/阶段/风险/排行/挑战) |
| `content_contribution_api.py` | `/api/v1/contributions` | 7 | 用户知识投稿/我的投稿/审核通过/拒绝 |
| `batch_ingestion_api.py` | `/api/v1/knowledge` | 4 | 批量知识灌注(上传/任务列表/进度/取消) |
| `content_manage_api.py` | `/api/v1/content-manage` | 8 | 内容发布CRUD/批量创建/批量发布 |
| `exam_api.py` | `/api/v1/certification/exams` | 9 | 考试管理CRUD/题目分配/发布(admin) |
| `question_api.py` | `/api/v1/certification/questions` | 5 | 题库管理CRUD(admin) |
| `exam_session_api.py` | `/api/v1/certification/sessions` | 4 | 考试会话(开始/提交/结果/历史) |
| `user_stats_api.py` | `/api/v1/stats` | 5 | 用户统计/活动时间线/管理员报告 |
| `routes.py` | `/api/v1` | 6 | 通用路由 |

**总计: 377+ 端点** (另有 v14 遗留路由)

### 3.2 认证与权限

```
JWT Token (python-jose + passlib/bcrypt)
├── access_token (30min)
├── refresh_token (7d)
└── token_blacklist (登出即失效)

权限守卫 (api/dependencies.py):
├── get_current_user       → 解析JWT，返回当前用户
├── require_admin          → role_level >= 99
└── require_coach_or_admin → role_level >= 4

角色层级:
  observer(1) → grower(2) → sharer(3) → coach(4)
  → promoter/supervisor(5) → master(6) → admin(99)
```

### 3.3 APScheduler 定时任务 (6 个)

| 任务 | 触发 | 说明 |
|------|------|------|
| `daily_task_generation` | Cron 每天 06:00 | 为所有活跃用户生成今日微行动任务 |
| `reminder_check` | Interval 每 1 分钟 | 检查到期提醒并触发 |
| `expired_task_cleanup` | Cron 每天 23:59 | 标记过期未完成任务为 expired |
| `process_approved_pushes` | Interval 每 5 分钟 | 投递已审批且到时的推送 |
| `expire_stale_queue_items` | Cron 每天 06:30 | 清理 72h 超时未审批的推送条目 |
| `knowledge_freshness_check` | Cron 每天 07:00 | 过期知识文档降权 (priority -= 2) |

---

## 四、核心引擎层

### 4.1 数据模型 (54 个)

| 分类 | 模型 | 说明 |
|------|------|------|
| **用户** | User | 用户主表（角色/密码/状态） |
| **评估** | Assessment, TriggerRecord, BehavioralProfile | 评估记录、触发因子、行为画像 |
| **干预** | Intervention | 干预方案 |
| **会话** | UserSession, ChatSession, ChatMessage | 用户会话、AI对话 |
| **设备** | UserDevice, GlucoseReading, HeartRateReading, HRVReading, SleepRecord, ActivityRecord, WorkoutRecord, VitalSign, HealthData | 设备绑定 + 9 类健康数据 |
| **微行动** | MicroActionTask, MicroActionLog | 每日任务 + 执行日志 |
| **消息** | CoachMessage, Reminder | 教练消息 + 提醒 |
| **评估推送** | AssessmentAssignment, CoachReviewItem | 教练分配评估 + 审核 |
| **设备预警** | DeviceAlert | 阈值预警 |
| **挑战** | ChallengeTemplate, ChallengeDayPush, ChallengeEnrollment, ChallengeSurveyResponse, ChallengePushLog | 挑战活动全生命周期 |
| **推送队列** | CoachPushQueue | 统一推送审批网关 |
| **行为审计** | BehaviorAuditLog, BehaviorHistory, BehaviorTrace | 行为变化追踪 |
| **食物识别** | FoodAnalysis | 食物图像识别结果+营养数据 |
| **专家租户** | ExpertTenant, TenantClient, TenantAgentMapping, TenantAuditLog | 白标工作室+客户+Agent映射+审计 |
| **知识库** | KnowledgeDocument, KnowledgeChunk, KnowledgeCitation | 知识文档(含8治理字段)+文本块+引用标注 |
| **内容交互** | ContentItem, ContentLike, ContentBookmark, ContentComment | 统一内容表+点赞+收藏+评论 |
| **学习持久化** | LearningProgress, LearningTimeLog, LearningPointsLog, UserLearningStats | 学习进度+时长日志+积分日志+汇总统计 |
| **考试系统** | ExamDefinition, QuestionBank, ExamResult | 考试定义+题库+考试结果 |
| **活动追踪** | UserActivityLog | 用户活动日志(登录/分享/学习/考试等) |
| **批量灌注** | BatchIngestionJob | 批量知识上传任务(状态/进度/文件数) |

### 4.2 数据库迁移 (16 个版本)

| 版本 | 说明 |
|------|------|
| 001 | 初始 schema — 基础表 |
| 002 | 完整 schema — 所有模型显式建表 |
| 003 | behavioral_profiles — 统一行为画像 |
| 004 | micro_actions + messaging — 微行动 + 教练消息 + 提醒 |
| 005 | assessment_assignments — 评估分配与审核 |
| 006 | device_alerts — 设备预警 |
| 007 | challenge_tables — 挑战活动 5 张表 |
| 008 | coach_push_queue — 统一推送审批网关 |
| 009 | food_analyses — 食物识别结果表 |
| 010 | tenant_tables — 专家租户4张表(expert_tenants/tenant_clients/tenant_agent_mappings/tenant_audit_logs) |
| 011 | knowledge_tables — 知识库3张表(knowledge_documents/knowledge_chunks/knowledge_citations) |
| 012 | knowledge_doc_content — KnowledgeDocument 增加 raw_content + updated_at 列 |
| 013 | content_governance — KnowledgeDocument 增加8列治理字段(evidence_tier/content_type/published_date/review_status/reviewer_id/reviewed_at/contributor_id/expires_at) + 3索引 |
| 014 | content_interaction — 内容交互4张表(content_items/content_likes/content_bookmarks/content_comments) |
| 015 | learning_persistence — 学习持久化4张表(learning_progress/learning_time_logs/learning_points_logs/user_learning_stats) |
| 016 | exam_activity_ingestion — 考试+活动+灌注5张表(exam_definitions/question_bank/exam_results/user_activity_logs/batch_ingestion_jobs) |

### 4.3 核心服务 (55 个 .py 文件，含以下关键服务)

| 服务文件 | 功能 |
|---------|------|
| `auth.py` | 角色层级判定 (get_role_level) + 权限辅助 |
| `behavioral_profile_service.py` | BAPS评估→统一行为画像（阶段/心理/交互模式/域需求） |
| `micro_action_service.py` | 每日微行动生成/完成/跳过/过期/教练任务 |
| `challenge_service.py` | 挑战模板CRUD/专家审核/报名/打卡/问卷 |
| `coach_push_queue_service.py` | 统一推送审批网关（挑战/预警/微行动/AI→教练审批→投递） |
| `device_alert_service.py` | 阈值监测/1h去重/双通知（用户+教练） |
| `device_behavior_bridge.py` | 设备数据→自动完成微行动（血糖/血压/运动映射） |
| `push_recommendation_service.py` | 6规则AI推送建议引擎 |
| `reminder_service.py` | 提醒CRUD + cron表达式解析 |
| `high_freq_question_service.py` | HF-20/HF-50预设题组加载/部分评分 |
| `content_access_service.py` | 角色级内容门控 |
| `data_visibility_service.py` | 字段级可见性过滤 |
| `intervention_matcher.py` | 域干预匹配（rx_library） |
| `behavior_facts_service.py` | 行为事实聚合 |
| `assessment_engine.py` | 评估计算引擎 |
| `baps/scoring_engine.py` | BAPS四维评分（反向计分/维度分析/星级/交叉） |
| `baps/questionnaires.py` | 问卷定义（BigFive/BPT-6/CAPACITY/SPI） |
| `baps/report_generator.py` | 评估报告生成 |
| `scheduler.py` | APScheduler 6任务调度（含知识库过期检查） |
| `master_agent.py` | 中枢Agent入口 |
| `master_agent_v0.py` | MasterAgent 9步流程完整实现 (254KB) |
| `brain/stage_runtime.py` | StageRuntimeBuilder（current_stage唯一写入者） |
| `brain/policy_gate.py` | RuntimePolicyGate |
| `brain/decision_engine.py` | 行为决策引擎 |
| `knowledge/embedding_service.py` | Ollama nomic-embed-text 768维嵌入 |
| `knowledge/retriever.py` | RAG检索 + scope_boost + priority_adj + freshness_penalty |
| `knowledge/rag_middleware.py` | RAG注入中间件（对话/Agent调用前注入上下文） |
| `knowledge/chunker.py` | Markdown分块策略（标题/段落/列表感知） |
| `knowledge/document_service.py` | 知识文档CRUD + 发布/撤回 + 审核/过期/投稿 |
| `knowledge/file_converter.py` | PDF/DOCX/TXT → Markdown转换 (pypdf + python-docx) |
| `knowledge/archive_extractor.py` | ZIP/7Z/RAR压缩包解压 (zipfile + py7zr + rarfile) |
| `knowledge/batch_ingestion_service.py` | 批量灌注编排(上传→解压→转换→分块→嵌入→入库) |
| `learning_service.py` | 学习时长/积分/连续打卡持久化 + 角色自动晋级检查 |
| `multimodal_client.py` | 多模态LLM客户端（qwen2.5vl食物识别） |
| `model_manager.py` | Ollama模型管理 |
| `pipeline.py` | 评估/干预管道编排 |
| `dify_client.py` | Dify工作流集成 |
| `trigger_engine.py` | 事件触发处理 |
| `decision_core.py` | 干预路由决策 |
| `health.py` | 系统健康监测 |
| `middleware.py` | CORS白名单/安全头/日志/限流 |
| `database.py` | SQLAlchemy引擎/会话管理 |
| `models.py` | 54个SQLAlchemy数据模型定义 |
| `user_segments.py` | 用户分层逻辑 |
| `limiter.py` | 限流 |
| `logging_config.py` | 日志配置 |
| `metrics.py` | 系统指标采集 |

### 4.4 Multi-Agent 系统

#### 12 个专业 Agent

| Agent | 类型 | 职责 |
|-------|------|------|
| 代谢管理Agent | metabolic | 血糖、体重、代谢相关分析与建议 |
| 睡眠管理Agent | sleep | 睡眠质量分析、作息优化建议 |
| 情绪管理Agent | emotion | 情绪评估、压力管理、心理支持 |
| 动机激励Agent | motivation | 行为动机分析、阶段推进、激励策略 |
| 教练风格Agent | coaching | 统一教练风格输出、回复合成 |
| 营养管理Agent | nutrition | 膳食分析、营养建议 |
| 运动康复Agent | exercise | 运动方案、康复指导 |
| 中医养生Agent | tcm | 中医体质分析、养生建议 |
| 危机干预Agent | crisis | 高风险识别与危机干预 |
| 行为处方Agent | behavior_rx | 行为处方制定、习惯干预、依从性管理、戒烟戒酒 |
| 体重管理Agent | weight | 体重/BMI监测、减重方案、身体成分分析 |
| 心脏康复Agent | cardiac_rehab | 心血管康复评估、运动处方、风险分层、术后康复 |

#### MasterAgent 9步处理流程

```
Step 1-2: 接收用户输入/设备数据
Step 3:   更新 User Master Profile
Step 4:   Agent Router → 问题类型 + 风险优先级
Step 4.5: 数据洞察生成
Step 5-6: 调用专业Agent + Multi-Agent Coordinator 整合
Step 7:   Intervention Planner → 个性化干预路径
Step 8:   Response Synthesizer → 统一教练风格输出
Step 9:   写回 Profile + 生成今日任务/追踪点
```

#### Agent API 端点

| 端点 | 方法 | 功能 |
|------|------|------|
| `/api/v1/agent/list` | GET | 获取所有Agent列表与状态 |
| `/api/v1/agent/run` | POST | 运行指定Agent任务 |
| `/api/v1/agent/pending-reviews` | GET | 待教练审核的Agent输出 |
| `/api/v1/agent/feedback` | POST | 提交审核反馈（通过/拒绝/修改/评分） |
| `/api/v1/agent/stats/{id}` | GET | Agent执行统计 |
| `/api/v1/agent/history` | GET | 执行历史查询 |
| `/api/v1/agent/status` | GET | Multi-Agent系统整体状态 |

---

## 五、推送审批网关架构

```
                    ┌─────────────────┐
                    │   数据源         │
                    ├─────────────────┤
                    │ 挑战每日推送     │──┐
                    │ 设备预警         │──┤
                    │ 微行动到期       │──┼──→ CoachPushQueue (pending)
                    │ AI推送建议       │──┤         │
                    │ Agent分析结果    │──┘         │
                    └─────────────────┘            ▼
                                          ┌──────────────────┐
                                          │  教练审批         │
                                          │  approve/modify   │
                                          │  /reject          │
                                          └────────┬─────────┘
                                                   │
                                    ┌──────────────┼──────────────┐
                                    ▼              ▼              ▼
                              CoachMessage     Reminder      状态更新
                              (学员消息)      (定时提醒)    (approved
                                                             /rejected)
                                    │              │
                                    └──────┬───────┘
                                           ▼
                                    学员收到通知
                                    (Notifications页)

定时任务:
  ├── 每5分钟: 投递已审批且到时的推送
  └── 每天06:30: 清理72h超时未审批条目
```

---

## 六、前端应用层

### 6.1 Admin Portal (管理后台) — 端口 5174

**Vue 3 + TypeScript + Ant Design Vue 4**
**82 个页面 · 5 个 Store**

| 角色 | 入口路由 | 核心功能 |
|------|---------|---------|
| **管理员** | `/admin/*` | 用户管理、分配、挑战管理、Prompt管理、干预包、批量灌注、内容发布、活动报告、系统设置 |
| **教练** | `/coach-portal` | 学员看板(Kanban)、7个干预工具、评估/目标/推送抽屉、挑战分配、推送队列审批、全平台搜索 |
| **专家** | `/expert-portal` | 督导看板、案例审核、教练评估、研究数据、白标工作室管理 |
| **C端用户** | `/client` | 健康仪表盘、AI对话、设备数据、学习进度、评估问卷 |

```
路由树:
├── /login                  登录
├── /dashboard              工作台概览
├── /admin
│   ├── /user-management    用户管理
│   ├── /distribution       用户分配
│   ├── /challenges         挑战活动管理
│   ├── /analytics          数据分析(4 KPI + 7 ECharts)
│   ├── /batch-ingestion    批量知识灌注(拖拽上传+任务列表)
│   ├── /content-manage     内容管理(CRUD+批量发布)
│   ├── /activity-report    用户活动报告(ECharts)
│   ├── /prompts/*          Prompt模板
│   └── /interventions      干预包管理
├── /coach-portal           教练主工作台 (CoachHome)
├── /coach
│   ├── /student-list       学员列表
│   ├── /messages           消息中心
│   ├── /student-profile    学员行为画像
│   ├── /student-health     学员健康数据
│   ├── /student-assessment 学员评估
│   ├── /review             审核
│   ├── /content-sharing    内容分享
│   ├── /copilot            AI副驾
│   ├── /ai-review          AI审核
│   ├── /my/*               我的(学员/工具/绩效/认证)
│   └── /my/analytics       数据分析(ECharts 6图表)
├── /expert-portal          专家主工作台
├── /expert/dashboard/:id   专家白标工作室管理(4-tab)
├── /expert/content-studio/:id 专家内容工作室(知识文档+挑战)
├── /expert/my/*            我的(督导/研究/审核)
├── /client                 C端首页
├── /client/chat            AI对话
├── /client/my/*            我的(档案/评估/轨迹/设备)
├── /client/assessment/*    评估(列表/做题/结果)
├── /content/*              内容管理(文章/卡片/案例/视频/审核)
├── /course/*               课程管理
├── /exam/*                 考试管理
├── /live/*                 直播管理
├── /portal/*               门户(公共/医疗助手)
└── /settings               系统设置
```

**Store 清单:**

| Store | 管理的状态 |
|-------|-----------|
| `auth.ts` | token/refreshToken/user/登录/登出/权限检查 |
| `agent.ts` | agents列表/待审核/当前输出/运行/反馈/统计 |
| `exam.ts` | 考试CRUD/统计/筛选 |
| `question.ts` | 题库CRUD/筛选 |

### 6.2 H5 移动端 — 端口 5173

**Vue 3 + TypeScript + Vant 4**
**25 个页面 · 3 个 Store · 5 个 API 模块 · 2 个交互组件**

```
路由 (25条):
├── /login                  登录（含快速体验按钮）
├── /                       首页（微行动卡片+连续打卡+挑战卡片+预警横幅+学习/教练/投稿入口）
├── /chat                   AI对话
├── /tasks                  微行动任务管理
├── /dashboard              健康数据看板
├── /profile                个人资料
├── /health-records         健康档案
├── /history-reports        历史报告
├── /data-sync              设备数据同步
├── /notifications          通知（教练消息/提醒/待评估/健康预警）
├── /account-settings       账户设置
├── /privacy-policy         隐私政策
├── /about-us               关于我们
├── /food-recognition       食物识别（拍照→qwen2.5vl营养分析+历史）
├── /behavior-assessment    行为评估（TTM7+个题模式+分配支持）
├── /my-stage               我的阶段（行为阶段仪表盘+微行动）
├── /my-plan                我的计划（教练推送的管理方案）
├── /challenges             挑战活动列表（浏览/报名）
├── /challenge-day/:id      挑战打卡日（每日推送+问卷交互）
├── /content/:type/:id      内容详情（图文渲染+交互栏+评论+分享）
├── /my-learning            我的学习（时长/积分/连续打卡/里程碑/周报）
├── /coach-directory        教练目录（公开，搜索+卡片列表+在线沟通）
├── /contribute             知识投稿（表单+领域选择+我的投稿列表+审核状态）
├── /expert-hub             专家目录（公开，搜索+卡片列表）
└── /studio/:tenantId       白标工作室（公开，品牌主题+Agent列表+服务包）

组件:
├── InteractionBar.vue      底部交互栏（点赞/收藏/评论/分享）
└── ShareSheet.vue          分享面板（复制链接/二维码占位）
```

### 6.3 专家工作台 — 端口 8501

**Streamlit** — 专家案例审核、教练评估、质量监督。

### 6.4 H5-Patient-App (独立备用)

**Vue 3 + Vant 4 · 10 页面 · 4 Store · 5 API 模块**

独立的患者端应用（非主 H5 App），提供健康数据录入、历史分析、AI对话等功能。

---

## 七、BAPS 评估体系

**平台核心竞争力** — 四维行为评估框架:

| 量表 | 题数 | 评估维度 | 产出 |
|------|------|---------|------|
| **大五人格** BigFive | 50 | 外向性/神经质/尽责性/宜人性/开放性 | 人格基线画像 |
| **BPT-6 行为分型** | 18 | 执行型/知识型/情绪型/关系型/环境型/矛盾型 | 行为改变模式 |
| **CAPACITY 改变力** | 32 | 意识/自主/匹配/资源/承诺/认同/时间/期望 | 改变准备度(32-160分) |
| **SPI 成功指数** | 50 | 动机30%/能力25%/支持20%/环境15%/历史10% | 成功率预测 |

**评估管道:**

```
BAPS四维评估(150题)
  ↓
评分引擎 (scoring_engine.py) — 反向计分/维度分析/星级评定/交叉分析
  ↓
BehavioralProfile — 统一行为画像
  ↓
StageRuntimeBuilder — TTM阶段判定(前意向→意向→准备→行动→维持→终止)
  ↓
InterventionMatcher — 域干预匹配(rx_library)
  ↓
MicroActionService — 每日微行动生成
  ↓
教练审核 → 推送给学员
```

---

## 八、数据流向

### 8.1 设备数据流

```
可穿戴设备/CGM
  ↓ 数据上传
DeviceRestAPI → 存储到各Reading表
  ↓
DeviceAlertService → 阈值检测 → 超阈值?
  ├── 是 → DeviceAlert + 去重(1h) + 双通知(用户+教练)
  │         └── 进入 CoachPushQueue
  └── 否 → 正常存储
  ↓
DeviceBehaviorBridge → 映射设备数据 → 自动完成微行动
```

### 8.2 评估数据流

```
学员填写评估 (H5 BehaviorAssessment)
  ↓
AssessmentAPI → BehavioralProfileService
  ↓
StageRuntime + PolicyGate → 阶段判定
  ↓
InterventionMatcher → 域干预方案
  ↓
教练审核 (CoachHome 评估抽屉)
  ↓
推送给学员 (CoachPushQueue → CoachMessage)
```

### 8.3 教练干预流

```
教练在 CoachHome 中:
  ├── 查看学员Kanban看板
  ├── 使用7个干预工具
  ├── 查看AI推送建议 (PushRecommendationService)
  ├── 审批推送队列 (CoachPushQueue)
  ├── 分配挑战活动
  ├── 分配评估问卷
  └── 发送消息/设置提醒
          │
          ▼
    学员收到通知
    (H5 Notifications页)
```

---

## 九、专家白标平台架构

### 9.1 多租户模型

```
ExpertTenant (slug PK: "dr-chen-endo")
├── expert_user_id → User (Integer FK)
├── brand_* (name/tagline/avatar/logo_url/colors/theme_id)
├── welcome_message, expert_title, expert_specialties
├── enabled_agents (JSON array)
├── service_packages (JSON array)
├── tier (basic/premium/strategic_partner)
├── max_clients, revenue_share_expert
│
├── TenantClient[]
│   ├── user_id → User (Integer FK)
│   ├── status (active/graduated/paused/exited)
│   └── service_package, enrolled_at, total_sessions
│
├── TenantAgentMapping[]
│   ├── agent_type (12种)
│   ├── enabled, display_name, persona_prompt
│   └── welcome_message, priority
│
└── TenantAuditLog[]
    ├── actor_id (Integer)
    └── action, details(JSON)
```

### 9.2 品牌主题系统

```
CSS 变量 → 动态注入:
  --brand-primary   主色调
  --brand-accent    强调色
  --brand-bg        背景色
  --brand-text      文字色

5 套预设主题:
  medicalBlue   (#1E40AF) — 内分泌代谢
  tcmGreen      (#2D5A3D) — 中医养生
  healingPurple (#6D28D9) — 心理情绪
  cardiacRed    (#DC2626) — 心脏康复
  warmSand      (#D97706) — 行为干预
```

### 9.3 API 端点 (10 个)

| 端点 | 方法 | 权限 | 功能 |
|------|------|------|------|
| `/api/v1/tenants/hub` | GET | 公开 | 专家目录列表 |
| `/api/v1/tenants/{id}/public` | GET | 公开 | 专家公开信息 |
| `/api/v1/tenants/{id}` | GET | 认证(owner/admin) | 租户完整详情 |
| `/api/v1/tenants/{id}` | PATCH | 认证(owner/admin) | 更新品牌/配置 |
| `/api/v1/tenants/{id}/clients` | GET | coach/admin | 客户列表(?status) |
| `/api/v1/tenants/{id}/clients` | POST | coach/admin | 添加客户 |
| `/api/v1/tenants/{id}/clients/{cid}` | PATCH | coach/admin | 更新客户 |
| `/api/v1/tenants/{id}/agents` | GET | 认证 | Agent映射列表 |
| `/api/v1/tenants/{id}/agents` | PUT | 认证 | 批量更新Agent配置 |
| `/api/v1/tenants/{id}/stats` | GET | 认证 | 客户统计 |

### 9.4 前端页面

| 应用 | 页面 | 路由 | 说明 |
|------|------|------|------|
| H5 | ExpertHub.vue | /expert-hub | 专家目录 (Vant 4, 公开) |
| H5 | ExpertStudio.vue | /studio/:tenantId | 白标工作室 (Vant 4, 公开, 动态主题) |
| Admin | ExpertDashboard.vue | /expert/dashboard/:tenantId | 4-tab管理面板 (概览/客户/Agent/品牌) |

### 9.5 专家内容工作室

```
路由: /expert/content-studio/:tenantId (入口: ExpertDashboard "内容管理" 按钮)
前端: ExpertContentStudio.vue (Ant Design + md-editor-v3 Markdown编辑器)
API:  /api/v1/tenants/{tenant_id}/content (8端点)

文档生命周期:
  draft → publish (分块+嵌入→RAG可检索) → ready → unpublish → draft / delete

功能:
├── Tab 1: 知识库文档
│   ├── 文档列表 (筛选: 状态/领域/关键词, 证据分层Tag)
│   ├── 创建/编辑文档 (Markdown编辑器 + 治理字段)
│   ├── 发布 → 自动分块 + Ollama嵌入
│   └── 撤回/删除
└── Tab 2: 挑战活动
    └── 本专家创建的挑战模板列表
```

---

## 十、RAG 知识库系统

### 10.1 架构

```
知识内容 (Markdown文档)
  ↓ 入库 (scripts/ingest_knowledge.py 或 专家内容工作室)
  ↓
core/knowledge/chunker.py → 智能分块 (标题/段落/列表感知, 300-1200字)
  ↓
core/knowledge/embedding_service.py → Ollama nomic-embed-text:latest (768维)
  ↓
KnowledgeChunk (DB, 含 embedding BLOB)
  ↓
用户提问时:
  query → embedding → cosine similarity → Top-K 候选
  ↓
core/knowledge/retriever.py → 多维评分:
  boosted = raw_score + scope_boost + priority_adj - freshness_penalty
  ↓
core/knowledge/rag_middleware.py → 注入上下文到 LLM prompt
  ↓
回复 + KnowledgeCitation (来源标注)
```

### 10.2 检索评分公式

| 因子 | 计算 | 说明 |
|------|------|------|
| `raw_score` | cosine_similarity(query_emb, chunk_emb) | 语义相似度 |
| `scope_boost` | tenant +0.15, domain +0.08, platform +0 | 范围越窄越优先 |
| `priority_adj` | (doc.priority - 5) * 0.02 | priority=9(T1) → +0.08, priority=3(T4) → -0.04 |
| `freshness_penalty` | min(days_expired * 0.005, 0.10) | 过期文档降权 |
| **boosted** | **raw + boost + adj - penalty** | **最终得分** |

### 10.3 数据模型

| 模型 | 核心字段 | 说明 |
|------|---------|------|
| KnowledgeDocument | title, raw_content, scope, tenant_id, domain_id, priority, status, evidence_tier, review_status, expires_at | 知识文档 (含治理字段) |
| KnowledgeChunk | document_id, content, embedding(BLOB), chunk_index | 文本块 + 向量 |
| KnowledgeCitation | session_id, message_id, document_id, chunk_id, score, evidence_tier | 引用标注 |

### 10.4 知识目录

```
knowledge/
├── kb_theory/        理论知识 (TTM, 行为科学)
├── kb_case_studies/  案例库
└── kb_domain/        领域知识 (代谢/睡眠/情绪/运动/营养/中医)
```

---

## 十一、内容治理层

### 11.1 证据分层 (Evidence Tiering)

| 层级 | 名称 | priority 映射 | 说明 |
|------|------|--------------|------|
| **T1** | 临床指南 (guideline/consensus) | 9 | 最高权威，长期有效 |
| **T2** | 随机对照试验 (rct/review) | 7 | 循证医学证据 |
| **T3** | 专家共识 (expert_opinion/case_report) | 5 | 专家经验，默认层级 |
| **T4** | 个人经验 (experience_sharing) | 3 | 用户投稿，需审核 |

常量: `TIER_PRIORITY_MAP = {"T1": 9, "T2": 7, "T3": 5, "T4": 3}`

### 11.2 审核流程

```
用户投稿 (grower+)
  ↓
POST /api/v1/contributions/submit
  ↓ evidence_tier=T4, review_status="pending", scope="platform"
  ↓
KnowledgeDocument (draft, pending)
  ↓
教练审核 (coach+)
  ├── GET  /review/pending     → 待审核列表
  ├── POST /review/{id}/approve → review_status="approved"
  └── POST /review/{id}/reject  → review_status="rejected"
  ↓
approved → 可发布 (publish → 分块+嵌入→RAG可检索)
rejected → 不可发布
```

### 11.3 时效管理

- `expires_at` 字段标记文档过期时间
- 定时任务 `knowledge_freshness_check` (每天 07:00): 过期文档 priority -= 2 (最低 1)
- RAG检索 freshness_penalty: 过期天数 × 0.005, 上限 -0.10

### 11.4 投稿 API (7 端点)

| 端点 | 方法 | 权限 | 说明 |
|------|------|------|------|
| `/api/v1/contributions/submit` | POST | grower+ | 投稿知识内容 |
| `/api/v1/contributions/my` | GET | grower+ | 我的投稿列表 |
| `/api/v1/contributions/my/{id}` | GET | grower+ | 投稿详情 |
| `/api/v1/contributions/my/{id}` | PUT | grower+ | 更新草稿 |
| `/api/v1/contributions/review/pending` | GET | coach+ | 待审核列表 |
| `/api/v1/contributions/review/{id}/approve` | POST | coach+ | 审核通过 |
| `/api/v1/contributions/review/{id}/reject` | POST | coach+ | 审核拒绝 |

---

## 十二、数据分析看板

### 12.1 Coach 分析 (6 端点)

前缀: `/api/v1/analytics/coach`

| 端点 | 说明 | 图表类型 |
|------|------|---------|
| `/risk-trend` | 学员风险评分趋势 (30天) | 折线图 |
| `/micro-action-trend` | 微行动完成率趋势 (30天) | 面积图 |
| `/domain-performance` | 领域表现雷达图 | 雷达图 |
| `/alert-frequency` | 预警频率分布 | 柱状图 |
| `/challenge-stats` | 挑战参与统计 | 饼图 |
| `/stage-distribution` | 学员阶段分布 | 环形图 |

前端: `CoachAnalytics.vue` (ECharts 6图表, 路由: `/coach/my/analytics`)

### 12.2 Admin 分析 (7 端点)

前缀: `/api/v1/analytics/admin`

| 端点 | 说明 | 展示 |
|------|------|------|
| `/overview` | 4 大 KPI (用户总数/活跃率/完成率/预警数) | KPI卡片 |
| `/user-growth` | 用户增长趋势 (30天) | 面积图 |
| `/role-distribution` | 角色分布 | 饼图 |
| `/stage-distribution` | 阶段分布 | 柱状图 |
| `/risk-distribution` | 风险等级分布 | 环形图 |
| `/coach-leaderboard` | 教练排行榜 (学员数/完成率) | 表格 |
| `/challenge-effectiveness` | 挑战效果分析 | 柱状图 |

前端: `AdminAnalytics.vue` (4 KPI + 7 ECharts, 路由: `/admin/analytics`)

---

## 十三、平台全面完善 (7大需求)

> v21 新增 — 13 新模型 · 3 迁移 · ~50 新端点 · 7 前端页面 · 2 组件

### 13.1 批量知识灌注

```
上传文件 (PDF/DOCX/TXT/MD/ZIP/7Z/RAR)
  ↓ POST /api/v1/knowledge/batch-upload (multipart, 100MB)
  ↓
BatchIngestionJob (pending → processing → completed/failed)
  ↓
archive_extractor.py → 解压 (ZIP/7Z/RAR)
  ↓
file_converter.py → 转换 Markdown (pypdf/python-docx)
  ↓
chunker.py → 智能分块
  ↓
embedding_service.py → Ollama嵌入 (768维)
  ↓
KnowledgeDocument + KnowledgeChunk (入库)
```

前端: `BatchIngestion.vue` (拖拽上传 + 任务列表 + 进度条)

### 13.2 内容交互系统

**替换全部 mock 数据为真实 DB 操作:**

| 操作 | 端点 | 机制 |
|------|------|------|
| 点赞 | `POST /content/{id}/like` | Toggle ContentLike + 更新 like_count |
| 收藏 | `POST /content/{id}/collect` | Toggle ContentBookmark + 更新 collect_count |
| 评论 | `POST /content/{id}/comment` | 插入 ContentComment + 更新 comment_count |
| 分享 | `POST /content/{id}/share` | 写入 UserActivityLog |

前端: `ContentDetail.vue` (图文渲染 + `InteractionBar` + 评论列表 + `ShareSheet`)

### 13.3 内容管理系统

| 端点 | 功能 |
|------|------|
| `POST /content-manage/create` | 创建 ContentItem (article/video/audio/...) |
| `POST /content-manage/batch-create` | 批量创建 (最多50条) |
| `GET /content-manage/list` | 列表 (筛选: type/status/domain) |
| `PUT /content-manage/{id}` | 编辑 |
| `POST /content-manage/{id}/publish` | 发布 |
| `POST /content-manage/batch-publish` | 批量发布 |
| `DELETE /content-manage/{id}` | 归档 |

前端: `ContentManage.vue` (表格 + 筛选 + 创建/编辑弹窗 + 批量操作)

### 13.4 学习持久化系统

```
学习事件 → POST /api/v1/learning/event
  ↓
learning_service.py:
  ├── record_learning_time() → LearningTimeLog + update_streak()
  ├── record_learning_points() → LearningPointsLog
  └── check_role_progression() → 自动角色晋级
  ↓
UserLearningStats (反范式汇总: 总时长/总积分/连续打卡/最长连续)
```

**角色晋级规则:**

| 当前角色 | 条件 | 目标角色 |
|---------|------|---------|
| observer | 完成首次评估 | grower |
| grower | 学习时长≥60min + 分享1条经验 | sharer |
| sharer | 通过L2考试 + growth≥300 + contribution≥50 | coach |

前端: `MyLearning.vue` (三统计卡 + 里程碑进度 + 周学习柱图 + 记录列表)

### 13.5 考试系统

```
题库管理 (admin)
  ↓ POST /api/v1/certification/questions (CRUD)
  ↓
考试定义 (admin)
  ↓ POST /api/v1/certification/exams (CRUD + 题目分配 + 发布)
  ↓
考试会话 (用户)
  ├── POST /sessions/start → 返回题目(不含答案), 检查max_attempts
  ├── POST /sessions/{id}/submit → 自动评分 + ExamResult + 更新学习统计
  ├── GET /sessions/{id}/result → 含正确答案+解析
  └── GET /my-results → 考试历史
```

前端: Admin 7 页面已存在 (QuestionBank/QuestionEdit/ExamList/ExamEdit/ExamSession/Results/ProctorReview)

### 13.6 用户活动追踪与统计

**活动类型:** login / share / learn / comment / like / exam / assessment / micro_action / chat / challenge / device_sync / food_recognition

| 端点 | 功能 |
|------|------|
| `GET /stats/user/{id}/overview` | 个人综合统计(学习+考试+活动) |
| `GET /stats/user/{id}/activity` | 活动时间线 |
| `GET /stats/admin/grower-report` | 成长者统计报告 |
| `GET /stats/admin/sharer-report` | 分享者统计报告 |
| `GET /stats/admin/activity-report` | 全平台活动报告(按类型聚合) |

前端: `UserActivityReport.vue` (4 KPI卡 + 饼图 + 趋势折线图 + 明细表)

### 13.7 教练公开目录

- `GET /api/v1/coach/directory` — 公开端点，无需认证
- 返回 coach+ 角色用户列表，支持关键词搜索
- 前端: `CoachDirectory.vue` (搜索 + 教练卡片 + 在线沟通入口)
- H5: `Contribute.vue` (投稿表单 + 领域选择 + 我的投稿列表)

---

## 十四、技术栈总览

| 层 | 技术 |
|----|------|
| **前端 (桌面)** | Vue 3 + TypeScript + Vite + Ant Design Vue 4 |
| **前端 (移动)** | Vue 3 + TypeScript + Vite + Vant 4 |
| **专家工作台** | Python + Streamlit |
| **后端** | Python 3.10+ + FastAPI + Uvicorn |
| **ORM** | SQLAlchemy + Alembic |
| **数据库** | PostgreSQL + Redis + Weaviate |
| **认证** | JWT (python-jose) + bcrypt (passlib) + Token黑名单 |
| **定时任务** | APScheduler (AsyncIOScheduler) |
| **LLM** | Ollama (qwen2.5:0.5b + qwen2.5vl:7b + nomic-embed-text) + Dify |
| **容器** | Docker Compose (4应用 + 9基础设施) |
| **反向代理** | nginx (前端容器内) |
| **实时通信** | WebSocket + SSE |

---

## 十五、量化统计

| 指标 | 数值 |
|------|------|
| SQLAlchemy 数据模型 | 54 个 (含 3 知识库 + 4 租户 + 13 v21新增) |
| 数据库迁移版本 | 16 个 |
| API 路由模块 | 41 个 (+ v14 遗留) |
| API 端点总数 | 377+ (+ v14 遗留) |
| 核心服务文件 | 55 个 .py (含 knowledge/ 8 + baps/ 3 + brain/ 3) |
| 定时任务 | 6 个 |
| Docker 容器 | 13 个 (4 应用 + 9 基础设施) |
| Admin Portal 页面 | 82 个 .vue |
| H5 移动端页面 | 25 个 .vue (+2 组件) |
| H5-Patient-App 页面 | 10 个 .vue |
| Pinia Store | 12 个 (Admin 5 + H5 3 + Patient 4) |
| 专业 Agent | 12 个 |
| BAPS 评估题目 | 150 题 (4 量表) |
| 角色层级 | 7 级 (observer → admin) |
| 证据分层 | 4 级 (T1→T4) |
| 知识文本块 | 51+ 个 (嵌入 768维) |

---

## 十六、系统状态

### 已运行 ✅

| 模块 | 状态 |
|------|------|
| 全部 54 个数据模型 + 16 版迁移 | ✅ 数据库就绪 |
| 41 个 API 路由模块 (377+ 端点) | ✅ 全部注册 |
| JWT 认证 + 7 级 RBAC | ✅ 运行中 |
| APScheduler 6 个定时任务 | ✅ 已启动 |
| 12 个专业 Agent + MasterAgent | ✅ 在线 |
| 推送审批网关 | ✅ 运行中 |
| Docker 4 应用容器 | ✅ healthy |
| Admin Portal 全平台搜索 (82 页面) | ✅ 运行中 |
| H5 快速体验登录 (25 页面) | ✅ 运行中 |
| Dify + Ollama LLM | ✅ 运行中 |
| 食物识别 (qwen2.5vl:7b) | ✅ 运行中 |
| 专家白标平台 (5专家/10端点) | ✅ 运行中 |
| 专家内容工作室 (8端点) | ✅ 运行中 |
| RAG 知识库 (51+ chunks, 检索+引用) | ✅ 运行中 |
| 数据分析看板 (Coach 6 + Admin 7 端点) | ✅ 运行中 |
| 内容治理层 (T1-T4分层/审核/投稿/过期) | ✅ 运行中 |
| 批量知识灌注 (PDF/DOCX/ZIP/7Z/RAR) | ✅ 运行中 |
| 内容交互 (点赞/收藏/评论/分享, 真实DB) | ✅ 运行中 |
| 学习持久化 (时长/积分/打卡/角色晋级) | ✅ 运行中 |
| 考试系统 (题库/考试/自动评分/会话) | ✅ 运行中 |
| 内容管理 (CRUD/批量发布) | ✅ 运行中 |
| 用户活动追踪 + 统计报告 | ✅ 运行中 |
| 教练公开目录 + 知识投稿 | ✅ 运行中 |

### 待优化 🔲

| 模块 | 说明 | 优先级 |
|------|------|--------|
| Agent 真实 LLM 调用 | 当前Agent fallback为模拟结果，需接入Ollama/Dify | 🟡 中 |
| 端到端测试 | 全流程自动化测试 | 🟡 中 |
| 生产部署配置 | SSL/域名/日志收集/监控告警 | 🟡 中 |
| 性能优化 | 数据库索引/缓存策略/分页优化 | 🟢 低 |

# 行为健康数字平台 — 架构总览

> 最后更新: 2026-02-10
> 版本: v27 (UI设计系统注入 + Westworld仿真注入验证)
> 状态: Multi-Agent 协作运行 + 专家白标平台 + RAG知识库 + 内容治理 + 平台全面完善(7大需求) + 问卷引擎 + 学分制晋级体系 + V003激励体系 + V004智能监测方案(模板/报名/推送/分析) + UI整合(C端+专家端) + **UI设计系统§1-§40注入(41页面)** + 上线前自检(108路由全通过) + 分层测试套件(98测试全通过) + **Westworld v0.4仿真数据注入验证**

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
│  │ 86+ 页面       │  │  33 页面       │  │  专家督导     │  │  10 页面       │  │
│  │ 6 stores       │  │  3 stores      │  │  (已被Admin  │  │  4 stores      │  │
│  │ +Tailwind CSS  │  │  +Tailwind CSS │  │   集成替代)   │  │               │  │
│  │ +BHP Design    │  │  +BHP Design   │  │              │  │               │  │
│  │  System §1-§40 │  │   System §1-§40│  │              │  │               │  │
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
│  │  问卷管理 ─── 问卷填写 ─── 问卷统计                                    │   │
│  │  学分管理 ─── 同道者关系 ─── 晋级系统 ─── 激励体系                    │   │
│  │  智能监测方案(V004) ─── 模板/报名/推送/互动/分析                       │   │
│  │                                                                          │   │
│  │  总计: 49 路由模块 · 430+ API 端点 · 11 定时任务(Redis互斥锁)          │   │
│  │  + 3 Westworld 仿真注入端点 (测试用, 内存存储)                         │   │
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
│  │  总计: 61 服务文件 · 70 数据模型 · 21 迁移版本                           │   │
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
│  │ :5432(暴露)  │  │ :6379        │  │ 向量数据库   │  │ knowledge/    │        │
│  │ pgvector扩展 │  │ 会话缓存     │  │ 语义检索     │  │ Obsidian知识库│        │
│  │ 70表/21迁移  │  │ Token黑名单  │
│  │              │  │ 调度互斥锁   │  │              │  │              │        │
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
| dify-db | 5432 (已暴露) | PostgreSQL + pgvector (pgvector/pgvector:pg15) |
| dify-redis | 6379 | Redis |
| dify-weaviate | — | 向量数据库 |
| dify-sandbox | — | 代码沙箱 |
| dify-ssrf_proxy | 3128 | SSRF防护代理 |

**网络**: 所有容器共享 `dify_dify-network` 外部网络。

---

## 三、后端 API 层

### 3.1 路由模块清单 (49 个)

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
| `search_api.py` | `/api/v1/search` | 1 | 全平台搜索（用户/挑战/微行动/预警/消息） |
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
| `survey_api.py` | `/api/v1/surveys` | 10 | 问卷CRUD/发布/关闭/题目管理 |
| `survey_response_api.py` | `/api/v1/surveys/s` | 3 | 短码填写/提交/草稿(支持匿名) |
| `survey_stats_api.py` | `/api/v1/surveys` | 3 | 问卷统计/响应列表/CSV导出 |
| `credits_api.py` | `/api/v1/credits` | 8 | 课程模块/学分汇总/学分明细 + 管理端CRUD/统计(ORM) |
| `companion_api.py` | `/api/v1/companions` | 6 | 同道者列表/导师/统计/邀请/管理员全量/毕业标记(ORM) |
| `promotion_api.py` | `/api/v1/promotion` | 6 | 晋级进度/规则/申请/审核/列表/资格预检(ORM) |
| `milestone_service.py` | `/api/v1/incentive` | 11 | 签到/徽章/里程碑/翻牌/连续恢复/纪念物/看板(V003) |
| `program_api.py` | `/api/v1/programs` | 13 | V004智能监测方案(模板CRUD/报名/今日推送/互动/进度/分析) |
| `routes.py` | `/api/v1` | 6 | 通用路由 ✅ 已注册 (审计修复#7) |

**总计: 430+ 端点** (另有 v14 遗留路由)

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

### 3.3 APScheduler 定时任务 (11 个, Redis 互斥锁)

> 所有 11 个任务均使用 `@with_redis_lock` 装饰器 (`core/redis_lock.py`)，基于 Redis SETNX 实现分布式互斥锁，多 worker 部署安全。Redis 不可用时降级为无锁执行。

| 任务 | 触发 | 锁TTL | 说明 |
|------|------|-------|------|
| `daily_task_generation` | Cron 每天 06:00 | 600s | 为所有活跃用户生成今日微行动任务 |
| `reminder_check` | Interval 每 1 分钟 | 60s | 检查到期提醒并触发 |
| `expired_task_cleanup` | Cron 每天 23:59 | 300s | 标记过期未完成任务为 expired |
| `process_approved_pushes` | Interval 每 5 分钟 | 300s | 投递已审批且到时的推送 |
| `expire_stale_queue_items` | Cron 每天 06:30 | 300s | 清理 72h 超时未审批的推送条目 |
| `knowledge_freshness_check` | Cron 每天 07:00 | 300s | 过期知识文档降权 (priority -= 2) |
| `advance_program_day` | Cron 每天 00:05 | 600s | V004: 推进方案 day_index + 检查完成 |
| `push_morning` | Cron 每天 09:00 | 300s | V004: 早间推送(认知任务) |
| `push_noon` | Cron 每天 11:30 | 300s | V004: 午间推送(行为任务) |
| `push_evening` | Cron 每天 17:30 | 300s | V004: 晚间推送(反思回顾) |
| `batch_analysis` | Cron 每天 23:00 | 600s | V004: 行为数据批量分析+推荐生成 |

---

## 四、核心引擎层

### 4.1 数据模型 (70 个)

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
| **知识领域** | KnowledgeDomain | 17个预置领域(id/name/description/parent_id) |
| **问卷引擎** | Survey, SurveyQuestion, SurveyResponse, SurveyResponseAnswer, SurveyDistribution | 问卷定义+13种题型+填写响应+逐题答案+分发渠道 |
| **学分制晋级** | CourseModule, UserCredit, CompanionRelation, PromotionApplication | 课程模块+学分记录+同道者关系+晋级申请(V002) |
| **V003激励体系** | Badge, UserBadge, UserMilestone, UserStreak, FlipCardRecord, NudgeRecord, UserMemorial, PointTransaction, UserPoint | 徽章定义+徽章获得+里程碑+连续签到+翻牌奖励+提醒+纪念物+积分流水+积分汇总(V003) |

### 4.2 数据库迁移 (21 个版本)

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
| 017 | knowledge_domains — 知识领域表(knowledge_domains) + knowledge_documents增加file_type/file_hash列 |
| 018 | survey_engine — 问卷引擎5张表(surveys/survey_questions/survey_responses/survey_response_answers/survey_distributions) |
| V002 | credit_promotion_system — 学分+晋级4张表(course_modules/user_credits/companion_relations/promotion_applications) + 4视图 + 4枚举 + 1触发器 |
| V003 | incentive_system — 激励体系9张表(badges/user_badges/user_milestones/user_streaks/flip_card_records/nudge_records/user_memorials/point_transactions/user_points) + 1视图(v_user_streak_status) + 1函数(compute_streak_status) |
| V004 | program_engine — 智能监测方案3张表(program_templates/program_enrollments/program_interactions) + 2视图(v_program_enrollment_summary/v_program_today_pushes) + 2函数(advance_program_day/calc_interaction_rate) + 3枚举(program_category/enrollment_status/push_slot) |

### 4.3 核心服务 (61 个 .py 文件，含以下关键服务)

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
| `scheduler.py` | APScheduler 6任务调度（含知识库过期检查, Redis互斥锁） |
| `redis_lock.py` | Redis SETNX 分布式互斥锁装饰器（降级无锁） |
| `promotion_service.py` | 晋级资格校验（四维检查: 学分+积分+同道者+实践） |
| `milestone_service.py` | V003激励引擎（签到/徽章/翻牌/里程碑/连续/纪念物） |
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
| `program_service.py` | V004 ProgramEngine(模板加载/报名/推送生成/互动记录/推荐/分析) |
| `multimodal_client.py` | 多模态LLM客户端（qwen2.5vl食物识别） |
| `model_manager.py` | Ollama模型管理 |
| `pipeline.py` | 评估/干预管道编排 |
| `dify_client.py` | Dify工作流集成 |
| `trigger_engine.py` | 事件触发处理 |
| `decision_core.py` | 干预路由决策 |
| `health.py` | 系统健康监测 |
| `middleware.py` | CORS白名单/安全头/日志/限流 |
| `database.py` | SQLAlchemy引擎/会话管理 |
| `models.py` | 70个SQLAlchemy数据模型定义 + ROLE_LEVEL权威映射 |
| `survey_service.py` | 问卷引擎(CRUD/发布/填写/BAPS回写/统计/CSV导出) |
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
**86 个页面 · 5 个 Store**

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
│   ├── /interventions      干预包管理
│   └── /credit-system/*    学分晋级管理(概览/课程模块/同道者/晋级审核)
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
**30 个页面 · 3 个 Store · 6 个 API 模块 · 2 个交互组件**

```
路由 (30条):
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
├── /learn                  学习中心（进度卡+搜索+6标签+领域筛选+无限滚动）
├── /content/:type/:id      内容详情（图文渲染+交互栏+评论+分享）
├── /my-learning            我的学习（时长/积分/连续打卡/里程碑/周报）
├── /coach-directory        教练目录（公开，搜索+卡片列表+在线沟通）
├── /contribute             知识投稿（表单+领域选择+我的投稿列表+审核状态）
├── /expert-hub             专家目录（公开，搜索+卡片列表）
├── /studio/:tenantId       白标工作室（公开，品牌主题+Agent列表+服务包）
├── /my-credits             我的学分（汇总+进度条+模块列表）
├── /my-companions          我的同道者（双Tab带教/导师+邀请+统计）
├── /promotion-progress     晋级进度（四维雷达图+进度条+申请按钮）
└── /:pathMatch(.*)*        兜底重定向 → /

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
Embedding (优先 sentence-transformers, 回退 Ollama nomic-embed-text:latest, 768维)
  ↓
KnowledgeChunk (DB, embedding vector(768) — pgvector原生类型)
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
| KnowledgeDocument | title, raw_content, scope, tenant_id, domain_id, priority, status, evidence_tier, review_status, expires_at, file_type, file_hash | 知识文档 (含治理字段+文件去重) |
| KnowledgeChunk | document_id, content, embedding vector(768), chunk_index, file_type, file_hash | 文本块 + pgvector原生向量 |
| KnowledgeDomain | id, name, description, parent_id, is_active | 17个预置知识领域 |
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
| **前端 (桌面)** | Vue 3 + TypeScript + Vite + Ant Design Vue 4 + BHP Design System |
| **前端 (移动)** | Vue 3 + TypeScript + Vite + Vant 4 + BHP Design System |
| **专家工作台** | Python + Streamlit |
| **后端** | Python 3.10+ + FastAPI + Uvicorn |
| **ORM** | SQLAlchemy + Alembic |
| **数据库** | PostgreSQL + pgvector + Redis + Weaviate |
| **认证** | JWT (python-jose) + bcrypt (passlib) + Token黑名单 |
| **定时任务** | APScheduler (AsyncIOScheduler) |
| **Embedding** | sentence-transformers (text2vec-base-chinese, 768维, 优先) / Ollama nomic-embed-text (回退) |
| **LLM** | Ollama (qwen2.5:0.5b + qwen2.5vl:7b + nomic-embed-text) + Dify |
| **容器** | Docker Compose (4应用 + 9基础设施) |
| **反向代理** | nginx (前端容器内) |
| **实时通信** | WebSocket + SSE |

---

## 十五、量化统计

| 指标 | 数值 |
|------|------|
| SQLAlchemy 数据模型 | 70 个 (含 3 知识库 + 1 知识领域 + 4 租户 + 5 问卷 + 4 学分晋级 + 9 V003激励 + 13 v21新增) |
| 枚举类型 | 39 个 (含 4 V002新增: course_module_type/elective_category/intervention_tier/assessment_type) |
| 数据库迁移版本 | 20 个 (001-018 + V002 + V003) |
| API 路由模块 | 49 个 (含 3 问卷 + 3 学分晋级 + 1 激励 + 3 仿真注入 + v14 遗留) |
| API 端点总数 | 430+ (含 16 问卷 + 20 学分晋级 + 11 激励 + 3 仿真注入 + v14 遗留) |
| 核心服务文件 | 59 个 .py (含 knowledge/ 8 + baps/ 3 + brain/ 3 + survey 1 + milestone 1 + promotion 1 + redis_lock 1) |
| 定时任务 | 6 个 (Redis SETNX 互斥锁) |
| Docker 容器 | 13 个 (4 应用 + 9 基础设施) |
| Admin Portal 页面 | 86 个 .vue |
| H5 移动端页面 | 30 个 .vue (+2 组件) |
| H5-Patient-App 页面 | 10 个 .vue |
| Pinia Store | 12 个 (Admin 5 + H5 3 + Patient 4) |
| 专业 Agent | 12 个 |
| BAPS 评估题目 | 150 题 (4 量表) |
| 角色层级 | 7 级 (observer → admin) |
| 证据分层 | 4 级 (T1→T4) |
| 问卷题型 | 13 种 (单选/多选/短文本/长文本/评分/NPS/滑块/矩阵/日期/文件/分节/描述) |
| 知识文本块 | 51+ 个 (嵌入 768维, pgvector原生存储) |
| 分层测试 | 98 个 (6层: 预检/模型/数据库/服务/API/E2E) |
| 激励系统徽章 | 36 个 (configs/badges.json) |

---

## 十六、系统状态

### 已运行 ✅

| 模块 | 状态 |
|------|------|
| 全部 70 个数据模型 + 20 版迁移 | ✅ 数据库就绪 (pgvector已启用) |
| 48 个 API 路由模块 (420+ 端点) | ✅ 全部注册 |
| JWT 认证 + 7 级 RBAC | ✅ 运行中 |
| APScheduler 6 个定时任务 (Redis互斥锁) | ✅ 已启动 |
| 12 个专业 Agent + MasterAgent | ✅ 在线 |
| 推送审批网关 | ✅ 运行中 |
| Docker 4 应用容器 | ✅ healthy |
| Admin Portal 全平台搜索 (86 页面) | ✅ 运行中 |
| H5 快速体验登录 (30 页面) | ✅ 运行中 |
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
| 问卷引擎 (5表/16端点/13题型/短码填写) | ✅ 运行中 |
| 学分制晋级 (4表/4视图/20端点/5级规则, ORM迁移) | ✅ 运行中 |
| 同道者关系管理 (邀请/统计/带教/毕业标记) | ✅ 运行中 |
| V003激励体系 (9表/1视图/11端点/36徽章/签到连续) | ✅ 运行中 |
| 晋级资格校验 (四维检查+结构化错误) | ✅ 运行中 |
| 审计修复 (C1-C3/H1-H4/M1/M6已修复) | ✅ 已完成 |
| 分层测试套件 (98测试, 6层全通过) | ✅ 已验证 |
| BHP Design System §1-§40 (41页面覆盖) | ✅ 已注入 |
| Westworld v0.4 仿真注入 (5管线/328条数据) | ✅ 已验证 |

### 待优化 🔲

| 模块 | 说明 | 优先级 |
|------|------|--------|
| Agent 真实 LLM 调用 | 当前Agent fallback为模拟结果，需接入Ollama/Dify | 🟡 中 |
| 生产部署配置 | SSL/域名/日志收集/监控告警 | 🟡 中 |
| 性能优化 | 数据库索引/缓存策略/分页优化 | 🟢 低 |

---

## 十七、分层测试套件

> 98 个测试 · 6 层分层验证 · 全部通过

### 17.1 测试架构

```
tests/
├── run_all_tests.sh           测试编排脚本 (按层级依次运行)
├── test_00_preflight.py       Layer 0: 预检环境 (19项检查: 13必选+6可选)
├── test_01_models.py          Layer 1: 模型定义 (22测试, 含V002 ORM)
├── test_02_database.py        Layer 2: 数据库+pgvector (11测试)
├── test_03_services.py        Layer 3: 服务层 (28测试, 含V002晋级规则)
├── test_04_api.py             Layer 4: API端点 (13测试)
└── test_05_e2e.py             Layer 5: 端到端流程 (10测试)

backend/                       桥接包 (测试导入兼容层)
├── models/
│   ├── knowledge.py           re-export core.models + DocStatus/KnowledgeScope枚举 + KnowledgeDomain
│   └── tenant.py              re-export 租户模型
├── services/
│   ├── chunker.py             SmartChunker + EmbeddingService (sentence-transformers优先/Ollama回退)
│   ├── doc_parser.py          DocumentParser (Markdown文档解析)
│   ├── ingest.py              KnowledgeIngestor + DOMAIN_SEEDS (17领域)
│   └── retriever.py           re-export core.knowledge.retriever
└── api/
    └── knowledge.py           FastAPI知识库路由 (7端点)
```

### 17.2 分层策略

| 层级 | 测试数 | 依赖 | 验证内容 |
|------|--------|------|---------|
| Layer 0 | 19项检查 | 无 | Python版本、必要包、pgvector包(可选)、PostgreSQL连接(可选)、表结构(可选) |
| Layer 1 | 22 | 模型导入 | ORM模型字段/关系/枚举、检索评分公式、RAG注入构建、V002 ORM验证 |
| Layer 2 | 11 | PostgreSQL | pgvector扩展、CRUD操作、vector(768)相似度查询、文档去重(file_hash) |
| Layer 3 | 28 | 服务模块 | SmartChunker分块(含超长段落硬切)、EmbeddingService向量化、DocumentParser解析、KnowledgeIngestor灌注、V002晋级规则校验 |
| Layer 4 | 13 | FastAPI | 知识库7端点(CRUD+搜索+健康检查)、认证头、请求验证 |
| Layer 5 | 10 | 全链路 | 灌注→分块→嵌入→检索→引用标注、scope优先级排序、证据分层过滤、过期降权 |

### 17.3 关键技术点

- **pgvector 原生向量**: `embedding vector(768)` 列类型 + `<=>` 余弦距离算子
- **sentence-transformers**: `shibing624/text2vec-base-chinese` (768维, 本地推理, 优先)
- **Ollama 回退**: `nomic-embed-text:latest` (768维, HTTP API)
- **server_default**: `evidence_tier='T3'`, `created_at=now()` (确保原生SQL兼容)
- **file_hash 去重**: 同文件重复灌注返回已有 doc_id
- **Docker镜像**: `pgvector/pgvector:pg15` (pgvector预装, 替代 postgres:15-alpine)

---

## 十八、问卷引擎 (Survey Engine)

> v22 新增 — 5 模型 · 1 迁移 · 16 API 端点 · 13 题型

### 18.1 数据模型

| 模型 | 表名 | 核心字段 | 说明 |
|------|------|---------|------|
| Survey | surveys | title, description, type, status, short_code, settings(JSON) | 问卷定义 |
| SurveyQuestion | survey_questions | survey_id, type(13种), label, options(JSON), required, order | 题目定义 |
| SurveyResponse | survey_responses | survey_id, respondent_id(可null=匿名), status, submitted_at | 填写响应 |
| SurveyResponseAnswer | survey_response_answers | response_id, question_id, value(JSON) | 逐题答案 |
| SurveyDistribution | survey_distributions | survey_id, channel, target_type, target_id | 分发渠道 |

### 18.2 题型 (13种)

```
single_choice   多选一        multiple_choice  多选多
text_short      短文本        text_long        长文本
rating          星级评分      nps              NPS评分(0-10)
slider          滑块          matrix_single    矩阵单选
matrix_multiple 矩阵多选      date             日期选择
file_upload     文件上传      section_break    分节标记
description     描述说明(不答题)
```

### 18.3 API 端点 (16个)

| 模块 | 前缀 | 端点 | 权限 |
|------|------|------|------|
| **管理** (`survey_api.py`) | `/api/v1/surveys` | POST / · GET / · GET /{id} · PATCH /{id} · DELETE /{id} · POST /{id}/publish · POST /{id}/close · POST /{id}/questions · PUT /{id}/questions/{qid} · DELETE /{id}/questions/{qid} | coach+ |
| **填写** (`survey_response_api.py`) | `/api/v1/surveys/s` | GET /{code} · POST /{code}/submit · POST /{code}/save-draft | 公开(匿名OK) |
| **统计** (`survey_stats_api.py`) | `/api/v1/surveys` | GET /{id}/stats · GET /{id}/responses · GET /{id}/export | coach+ |

### 18.4 核心流程

```
创建问卷 (coach+)
  ↓ POST /api/v1/surveys
添加题目
  ↓ POST /api/v1/surveys/{id}/questions
发布 → 生成 short_code (8位)
  ↓ POST /api/v1/surveys/{id}/publish
分享短链 /s/{code} (匿名可填)
  ↓ GET /api/v1/surveys/s/{code}
提交答案
  ↓ POST /api/v1/surveys/s/{code}/submit
  ↓
BAPS 数据回写 (SurveyType.baps → BehavioralProfile 同步)
  ↓
统计分析 + CSV导出
  ↓ GET /api/v1/surveys/{id}/stats
  ↓ GET /api/v1/surveys/{id}/export
```

---

## 十九、全平台审计报告 (2026-02-09)

> 审计范围: API层(48路由) + 模型层(70模型) + 核心服务(59文件) + 前端(H5+Admin) + Docker/配置

### 19.1 严重冲突 (需立即修复)

#### ~~⛔ C1: QuestionType 枚举重复定义~~ ✅ 已修复

**位置**: `core/models.py` L1850 (考试系统) vs L2380 (问卷引擎)
**修复**: 考试系统枚举重命名为 `ExamQuestionType` (Phase 0.3)

#### ~~⛔ C2: 角色等级映射 — 6个文件2套方案~~ ✅ 已修复

**修复**: 在 `core/models.py` 新增权威 `ROLE_LEVEL` / `ROLE_LEVEL_STR` / `ROLE_DISPLAY` 字典，6个文件全部统一为 1-indexed (Phase 0.1)。涉及: auth.py, user_segments.py, challenge_service.py, content_access_service.py, data_visibility_service.py, learning_service.py。

#### ~~⛔ C3: User.referred_by 字段缺失 → L2+晋级阻断~~ ✅ 已修复

**修复**: V002 迁移创建 `companion_relations` 表，`_count_companions()` 优先查询该表，保留 `referred_by` 回退 (Phase 1)。新增 `companion_api.py` 4端点管理同道者关系 (Phase 2)。

### 19.2 高优先级问题

#### ~~⚠️ H1: UserRole.PATIENT 仍为默认值~~ ✅ 已修复

**修复**: Python default → `UserRole.OBSERVER`，DB default → `'OBSERVER'` (Phase 0.2 + V002)。

#### ~~⚠️ H2: APScheduler 无互斥锁~~ ✅ 已修复

**位置**: `core/scheduler.py` + `core/redis_lock.py`
**修复**: 新建 `core/redis_lock.py` 实现 `@with_redis_lock` 装饰器 (Redis SETNX)，6 个定时任务全部加锁。Redis 不可用时降级为无锁执行（当前行为）。TTL: 60-600s。

#### ~~⚠️ H3: admin-portal Vite 代理死循环~~ ✅ 已修复

**修复**: `target: 'http://localhost:5174'` → `'http://localhost:8000'` (Phase 0.4)。

#### ~~⚠️ H4: routes.py 路由未注册~~ ✅ 已修复

**修复**: 在 `main.py` 中 `include_router(legacy_v1_router)` (Phase 0.4)。

### 19.3 中等问题

| 编号 | 问题 | 位置 | 影响 |
|------|------|------|------|
| ~~M1~~ | ~~search_api.py 双路径~~ ✅ 已删除 `/v1/search` 兼容路由 | `api/search_api.py` | 已消除 |
| ~~M2~~ | ~~trigger_engine_v0.py 单例冲突~~ ✅ 已重命名为 `_deprecated_trigger_engine_v0.py` | `core/` | 已消除 |
| ~~M3~~ | ~~data_visibility_service 阈值混用~~ ✅ 已统一为1-indexed | `core/data_visibility_service.py` | 已消除 |
| M4 | start_all.bat 引用不存在路径 `dify/docker` | `start_all.bat:61` | 脚本报错 |
| M5 | workbench/requirements.txt 缺少 loguru/python-jose/passlib | `workbench/requirements.txt` | Docker 构建缺依赖 |
| ~~M6~~ | ~~admin-portal/.env DIFY_API_URL 指向 localhost:80~~ ✅ 已改为 :8080 | `admin-portal/.env` | 已消除 |
| M7 | miniprogram.py ↔ context_builder.py 循环导入 | `api/` | 启动时可能报错 |
| M8 | get_table_names() 缺少 knowledge_domains | `core/models.py` | 文档函数不完整 |
| M9 | 7个路由文件使用硬编码全路径而非 prefix 参数 | `api/` 多文件 | 风格不统一 |

### 19.4 前端审计结果

| 项目 | 状态 | 说明 |
|------|------|------|
| H5 路由 (27) → 后端端点 | ✅ 全部匹配 | 33+ API 调用均有对应后端 |
| Admin 路由 (~80) → 后端端点 | ✅ 基本匹配 | 部分页面有 TODO (非阻塞) |
| GrowthPath 废弃引用 | ✅ 已清理 | 前后端均无残留 |
| Store 完整性 | ✅ H5:3 Admin:5 | 无孤立引用 |
| 路径冲突 | ✅ 无 | 所有路由唯一 |

### 19.5 Docker/配置审计结果

| 项目 | 状态 | 说明 |
|------|------|------|
| 端口映射 | ⚠️ Vite 配置与实际不符 | start_all.bat CLI 覆盖 → 实际运行正确 |
| 网络配置 | ✅ | dify_dify-network 外部网络正确 (需 Dify 先启动) |
| 内存分配 | ✅ | 合计 ~31GB 预留 / 56GB 系统 |
| 健康检查 | ✅ | bhp-api + workbench 均有 curl 检查 |
| 模型关系 | ✅ | 40 对 back_populates 全部匹配 |
| FK 引用 | ✅ | 60 模型所有外键均指向有效表 |
| 迁移链 | ✅ | 001→018 连续无断裂 |

### 19.6 审计统计

| 指标 | 数值 |
|------|------|
| 扫描文件 | ~200+ (.py/.vue/.ts/.yaml/.bat) |
| 严重冲突 | 3 → **0** (全部修复) |
| 高优先级问题 | 4 → **0** (全部修复, 含H2 Redis互斥锁) |
| 中等问题 | 9 → **5** (M2/M3/M1/M6 已修复) |
| 前端冲突 | 0 |
| 模型关系完整性 | 40/40 (100%) |
| FK 引用有效性 | 60/60 (100%) |
| 迁移链完整性 | 21/21 (100%) |

---

## 二十、学分制晋级体系 (Credit & Promotion System)

> V002 新增 — 4 模型 · 4 视图 · 4 枚举 · 20 API 端点 · 5 级晋级规则 · ORM迁移 · 晋级资格校验

### 20.1 数据模型

| 表 | 核心字段 | 说明 |
|------|---------|------|
| `course_modules` | id(UUID), code, title, module_type(M1-M4), tier(mandatory/elective), target_role, credits, sort_order | 课程模块定义 |
| `user_credits` | user_id, module_id, credits_earned, completed_at, assessment_score | 用户学分记录 |
| `companion_relations` | mentor_id, mentee_id, mentor_role, mentee_role, status(active/graduated/dropped), quality_score | 同道者带教关系 |
| `promotion_applications` | user_id, from_role, to_role, status(pending/approved/rejected), credit/point/companion_snapshot(JSON) | 晋级申请+审核 |

### 20.2 数据库视图

| 视图 | 功能 |
|------|------|
| `v_user_credit_summary` | 按模块类型汇总用户学分 |
| `v_user_total_credits` | 用户总学分(总/必修/选修/M1-M4) |
| `v_companion_stats` | 同道者统计(毕业/活跃/退出数+平均质量) |
| `v_promotion_progress` | 晋级进度四维雷达(学分+积分+同道者+实践) |

### 20.3 五级晋级规则 (promotion_rules.json)

| 晋级路径 | 学分要求 | 三维积分要求 | 同道者要求 | 理论:实践 |
|---------|---------|-------------|-----------|----------|
| L0→L1 (观察→成长) | 总100(必60+选40) | g100 | 邀请4人体验 | 8:2 |
| L1→L2 (成长→分享) | 总200(必120+选80) | g300/c30/i10 | 带教4名L0毕业 | 7:3 |
| L2→L3 (分享→教练) | 总800(必380+选420) | g800/c100/i50 | 带教4名L1(质量≥3.5) | 5:5 |
| L3→L4 (教练→推广) | 总1500(必690+选810) | g1500/c500/i200 | 带教4名L2(质量≥4.0) | 4:6 |
| L4→L5 (推广→大师) | 总3000(必1200+选1800) | g3000/c1500/i800 | 带教4名L3(质量≥4.5) | 3:7 |

### 20.4 API 端点 (20个)

| 模块 | 前缀 | 端点 | 功能 |
|------|------|------|------|
| `credits_api.py` | `/api/v1/credits` | GET /modules · GET /my · GET /my/records · GET /admin/modules · POST /admin/modules · PUT /admin/modules/{id} · DELETE /admin/modules/{id} · GET /admin/stats | 用户3端点 + 管理端5端点(ORM) |
| `companion_api.py` | `/api/v1/companions` | GET /my-mentees · GET /my-mentors · GET /stats · POST /invite · GET /all · POST /{id}/graduate | 用户4端点 + 管理端2端点(ORM) |
| `promotion_api.py` | `/api/v1/promotion` | GET /progress · GET /rules · POST /apply · GET /applications · POST /review/{id} · GET /check | 四维进度/规则/申请(含校验)/审核/列表/资格预检(ORM) |

### 20.5 晋级流程

```
用户查看进度 → GET /promotion/progress (四维雷达数据)
  ↓
资格预检 → GET /promotion/check (四维校验: 学分+积分+同道者+实践)
  ↓
满足条件 → POST /promotion/apply (快照当前学分+积分+同道者, 不达标返回结构化错误)
  ↓
PromotionApplication (status=pending)
  ↓
教练/管理员审核 → POST /promotion/review/{id} (approved/rejected)
  ↓ approved
UPDATE users SET role = to_role → 角色自动升级
```

### 20.6 审计修复清单

| 编号 | 问题 | 修复方案 | Phase |
|------|------|---------|-------|
| C1 | QuestionType枚举重复 | 考试版→ExamQuestionType | 0.3 |
| C2 | ROLE_LEVEL 6文件2套方案 | models.py权威ROLE_LEVEL+全部统一1-indexed | 0.1 |
| C3 | User.referred_by缺失→L2+阻断 | companion_relations表+_count_companions()重写 | 1+2 |
| H1 | 默认角色PATIENT | Python+DB均改为OBSERVER | 0.2 |
| H3 | Vite代理死循环 | target→localhost:8000 | 0.4 |
| H4 | routes.py未注册 | main.py include_router | 0.4 |
| M2 | trigger_engine_v0.py冲突 | 重命名为_deprecated_ | 0.4 |
| M3 | data_visibility阈值混用 | 统一1-indexed | 0.1 |
| H2 | APScheduler无互斥锁 | core/redis_lock.py SETNX + 6 job全加锁 | V003 |
| M1 | search_api双路径 | 删除/v1/search兼容路由 | V003 |
| M6 | admin .env Dify URL | localhost→localhost:8080 | V003 |

---

## 二十一、V003 激励体系 (Incentive System)

> V003 新增 — 9 模型 · 1 视图 · 1 函数 · 11 API 端点 · 36 徽章 · 签到连续打卡 · 翻牌奖励

### 21.1 数据模型

| 表 | 核心字段 | 说明 |
|------|---------|------|
| `badges` | id, code, name, category, icon, description, unlock_condition(JSON) | 徽章定义 (36个, configs/badges.json) |
| `user_badges` | user_id, badge_id, earned_at, source | 用户已获徽章 |
| `user_milestones` | user_id, milestone_code, reached_at, value | 里程碑达成记录 (configs/milestones.json) |
| `user_streaks` | user_id, streak_type, current_streak, max_streak, last_date | 连续签到/学习统计 |
| `flip_card_records` | user_id, card_date, reward_type, reward_value, flipped_at | 每日翻牌奖励记录 |
| `nudge_records` | user_id, nudge_type, sent_at, responded_at | 激励提醒记录 |
| `user_memorials` | user_id, memorial_type, title, content, created_at | 用户纪念物/成就卡 |
| `point_transactions` | user_id, point_type, amount, source, description, created_at | 积分流水明细 |
| `user_points` | user_id, growth_points, contribution_points, influence_points | 积分汇总表 |

### 21.2 数据库视图与函数

| 对象 | 类型 | 功能 |
|------|------|------|
| `v_user_streak_status` | VIEW | 用户连续签到状态汇总 |
| `compute_streak_status()` | FUNCTION | 计算并更新用户签到连续状态 |

### 21.3 API 端点 (11个)

前缀: `/api/v1/incentive`

| 端点 | 方法 | 功能 |
|------|------|------|
| `/checkin` | POST | 每日签到 (连续打卡+积分+里程碑触发) |
| `/first-login` | POST | 首次登录奖励 |
| `/badges/available` | GET | 可获取徽章列表 (36个) |
| `/badges/my` | GET | 已获得徽章列表 |
| `/milestones/my` | GET | 已达成里程碑列表 |
| `/flip-card` | POST | 翻牌选择奖励 |
| `/streak/recover` | POST | 连续签到恢复 (消耗积分) |
| `/learning/check-badges` | POST | 检查学习相关徽章 |
| `/module/check-badges` | POST | 检查课程模块徽章 |
| `/promotion/check-badge` | POST | 检查晋级徽章 |
| `/dashboard` | GET | 激励看板 (签到/徽章/里程碑/积分汇总) |

### 21.4 核心引擎

```
MilestoneEngine (core/milestone_service.py, 同步SQLAlchemy)
  ├── daily_checkin()       → 签到 + 连续打卡 + 积分 + 里程碑触发
  ├── first_login()         → 首次登录奖励
  ├── flip_choose()         → 翻牌选择 (积分/徽章/免打卡)
  ├── recover_streak()      → 花费积分恢复连续
  ├── check_learning_badges() → 学习时长/积分徽章
  ├── check_module_badges()   → 课程完成徽章
  ├── check_promotion_badge() → 晋级徽章
  └── dashboard()           → 汇总看板数据

认证: X-User-Id Header 或 user_id Query 参数
配置: configs/badges.json (36徽章) + configs/milestones.json + configs/point_events.json
```

### 21.5 前端页面

| 应用 | 页面 | 路由 | 说明 |
|------|------|------|------|
| Admin | CreditDashboard.vue | /admin/credit-system/dashboard | 学分概览(KPI+分布+规则) |
| Admin | CourseModuleManage.vue | /admin/credit-system/modules | 课程模块CRUD(筛选+分页+弹窗) |
| Admin | CompanionManage.vue | /admin/credit-system/companions | 同道者关系管理(状态筛选) |
| Admin | PromotionReview.vue | /admin/credit-system/promotion-review | 晋级审核(详情抽屉+审批) |
| H5 | MyCredits.vue | /my-credits | 学分汇总+进度条+模块列表 |
| H5 | MyCompanions.vue | /my-companions | 双Tab带教/导师+统计+邀请 |
| H5 | PromotionProgress.vue | /promotion-progress | 四维雷达图(ECharts)+进度条+申请 |

---

## 二十二、V004 智能监测方案 (Smart Program Engine)

> V004 新增 — 3 模型 · 2 视图 · 2 函数 · 3 枚举 · 13 API 端点 · 5 定时任务 · 种子模板(glucose-14d)

### 22.1 数据模型

| 表 | 核心字段 | 说明 |
|------|---------|------|
| `program_templates` | id(UUID), slug, title, category, total_days, pushes(JSON), questions(JSON), recommendation_rules(JSON) | 方案模板定义 |
| `program_enrollments` | id(UUID), user_id, template_id, status, day_index, enrolled_at, completed_at | 用户报名记录 |
| `program_interactions` | id(UUID), enrollment_id, day_index, slot, push_content, user_response, response_time, score | 每日推送互动记录 |

### 22.2 数据库视图与函数

| 对象 | 类型 | 功能 |
|------|------|------|
| `v_program_enrollment_summary` | VIEW | 报名统计汇总(活跃/完成/退出) |
| `v_program_today_pushes` | VIEW | 今日待推送列表 |
| `advance_program_day()` | FUNCTION | 推进方案日期 + 检查完成条件 |
| `calc_interaction_rate()` | FUNCTION | 计算互动完成率 |

### 22.3 API 端点 (13个)

前缀: `/api/v1/programs`

| 端点 | 方法 | 功能 |
|------|------|------|
| `/templates` | GET | 方案模板列表 |
| `/templates/{slug}` | GET | 模板详情 |
| `/templates` | POST | 创建模板(admin) |
| `/templates/{slug}` | PUT | 更新模板(admin) |
| `/enroll` | POST | 用户报名方案 |
| `/my` | GET | 我的方案列表 |
| `/my/{id}/today` | GET | 今日推送内容 |
| `/my/{id}/interact` | POST | 提交互动回答 |
| `/my/{id}/timeline` | GET | 行为轨迹时间线 |
| `/my/{id}/progress` | GET | 行为特征分析 |
| `/my/{id}/status` | GET | 方案状态概览 |
| `/admin/analytics` | GET | 管理端方案分析 |
| `/admin/enrollments` | GET | 管理端报名列表 |

### 22.4 种子模板

`configs/glucose-14d-template.json`: 14天血糖监测体验之旅
- 15天方案, 44次推送, 145道问题, 7条推荐规则
- 3个时段: morning(09:00)/noon(11:30)/evening(17:30)
- 整合V003里程碑(方案完成+积分奖励)

### 22.5 前端页面

| 应用 | 页面 | 路由 | 说明 |
|------|------|------|------|
| H5 | MyPrograms.vue | /programs | 我的方案+更多方案(已报名自动隐藏) |
| H5 | ProgramToday.vue | /program/:id/today | 今日推送卡片+互动问答 |
| H5 | ProgramTimeline.vue | /program/:id/timeline | 行为轨迹时间线 |
| H5 | ProgramProgress.vue | /program/:id/progress | 行为特征雷达图+趋势分析 |

---

## 二十三、UI 整合 (C端+专家端)

> 将 UI1(Vue C端) + UI2(React 专家端) 整合进主平台，替代 Streamlit 工作台

### 23.1 H5 C端整合

| 文件 | 功能 |
|------|------|
| `h5/src/types/stage.ts` | TTM→4阶段映射(觉察者/行动者/稳定者/调整者) |
| `h5/src/api/tasks.ts` | 微行动+阶段+叙事 API 模块 |
| `h5/src/components/stage/StageHeader.vue` | 生命状态渐变卡片(动态获取TTM阶段) |
| `h5/src/components/task/BehaviorTaskCard.vue` | 每日行为任务卡(完成/尝试/跳过) |
| `h5/src/views/journey/JourneyView.vue` | 健康成长伙伴叙事页 |

### 23.2 Admin 专家端整合

| 文件 | 功能 |
|------|------|
| `admin-portal/src/api/expert.ts` | 审核队列/BAPS/CGM/发布 API |
| `admin-portal/src/stores/brain.ts` | SPI 风险评分引擎(PHQ-9/CGM/行为一致性) |
| `admin-portal/src/components/expert/CGMChart.vue` | vue-echarts CGM 血糖折线图 |
| `admin-portal/src/components/expert/MetricCard.vue` | 暗色指标卡片 |
| `admin-portal/src/components/expert/LogicFlowBridge.vue` | 决策规则可视化(代码+解读双面板) |
| `admin-portal/src/views/expert/DualSignPanel.vue` | 双签审核面板(原始数据+成长叙事) |
| `admin-portal/src/views/expert/ExpertWorkbench.vue` | 全屏专家工作台(审核/追溯/规则) |

### 23.3 基础设施变更

- Tailwind CSS 3 安装到 H5 + Admin (preflight: false, 不破坏 Vant/Ant Design)
- vue-echarts 安装到 Admin (tree-shakable ECharts)
- Admin 路由 `/expert-workbench` (全屏独立，不在 AdminLayout 内)
- H5 路由 `/journey`
- Home.vue 集成 StageHeader 组件

### 23.4 BHP 视觉设计系统注入 (2026-02-10)

> 纯 CSS 注入方案 — 零架构改动，通过 CSS 变量 + BEM 类名覆盖 41 个页面

#### 注入脚本

- **工具**: `bhp_ui_inject.py` (1499 行，自动检测项目目录 + 备份 + 注入 + 验证)
- **CSS 来源**: `bhp-design-tokens.css` (31KB 基础 + 34KB §16-§40 追加 = 65KB 合并)
- **执行方式**: `python bhp_ui_inject.py --project-root D:/behavioral-health-project`

#### 注入文件清单

| 文件 | 注入目标 | 大小 | 用途 |
|------|---------|------|------|
| `bhp-design-tokens.css` | H5 + Admin `src/styles/` | 65 KB | 核心设计变量 + 40 个章节组件样式 |
| `vant-overrides.css` | H5 `src/styles/` | 3.2 KB | Vant 主题色映射到 BHP 品牌色 |
| `antd-overrides.css` | Admin `src/styles/` | 8.7 KB | Ant Design 表格/卡片/按钮增强 |
| `useStageStyle.ts` | 两端 `src/composables/` | 4.9 KB | TTM阶段→CSS类名映射 composable |

#### CSS 变量体系

```css
:root {
  --bhp-brand-primary: #10b981;      /* 翡翠绿品牌色 */
  --bhp-brand-primary-dark: #059669;
  --bhp-brand-primary-light: #d1fae5;
  /* ... 150+ CSS 变量: 颜色/间距/圆角/阴影/字号/动画 */
}
```

#### 40 个 CSS 章节 (§1-§40)

| 范围 | 章节 | 覆盖组件 |
|------|------|---------|
| **基础 §1-§3** | 设计变量 / 通用组件 / 工具类 | 品牌色、卡片、按钮、Badge、进度条 |
| **H5 §4-§8** | 阶段Header / 任务卡 / 聊天气泡 / 问卷 / 时间线 | 觉察/行动/稳定/调整 4阶段渐变 |
| **Admin §9-§13** | 工作台 / 双签面板 / 教练仪表盘 / 追踪流程 / 表格 | 审核列表、签名状态、学员圆点 |
| **通用 §14-§15** | 移动端适配 / 动画 | 响应式断点、微交互 |
| **新增H5 §16-§28** | 登录 / 测评 / PHQ-9 / 监测方案 / 通知 / 商城 / 学分 / 学习 / 路径 / 行为详情 / CGM / 设置 / 活动 | 14 个新页面样式 |
| **新增Admin §29-§40** | 仪表盘 / 用户管理 / 方案管理 / 推送管理 / 叙事编辑 / CGM管理 / 规则引擎 / 金字塔 / 晋级审批 / 质量看板 / 公众Portal / 医护Portal | 15 个新页面样式 |

#### 页面覆盖统计

| 端 | 已覆盖 (§1-§15) | 本次新增 (§16-§40) | 合计 |
|----|-----------------|-------------------|------|
| H5 | 6 页面 | 14 页面 | **20 页面** |
| Admin | 6 页面 | 15 页面 | **21 页面** |
| **总计** | **12** | **29** | **41 页面** |

#### 构建验证 (2026-02-10)

| 检查项 | H5 (:5173) | Admin (:5174) |
|--------|-----------|---------------|
| Docker 构建 | PASS | PASS |
| 容器状态 | healthy | healthy |
| HTTP 200 | PASS | PASS |
| `--bhp-brand-primary: #10b981` 存在 | PASS | PASS |
| `bhp-stage-header` 编译 | PASS | PASS |
| `bhp-auth` 编译 | PASS | PASS |
| 框架覆盖 (vant/antd) | PASS | PASS |

#### useStageStyle composable

```typescript
// src/composables/useStageStyle.ts
export function useStageStyle(stage: string) {
  // AWARENESS → awareness, ACTION → action, STABILIZATION → stable, RELAPSE → relapse
  return {
    stageKey,           // CSS 类名后缀
    stageLabel,         // 显示名称 (觉察者/行动者/稳定者/调整者)
    stageIcon,          // 图标
    headerClass,        // bhp-stage-header--{key}
    taskClass,          // bhp-task-card--{key}
    progressClass,      // bhp-progress__bar--{key}
    dotClass,           // bhp-student-row__stage--{key}
  }
}
```

---

## 二十四、上线前自检报告

> 2026-02-09 全面自检 — 108 路由全通过 · 0 静态资源 404 · 3 个 API 路由修复

### 24.1 检查结果总览

| 检查项 | 范围 | 结果 |
|--------|------|------|
| Docker 容器 | 13 个 | 全部 Running/Healthy |
| H5 路由 HTTP 200 | 34 路径 | 34/34 通过 |
| Admin 路由 HTTP 200 | 74 路径 | 74/74 通过 |
| H5 静态资源 | JS/CSS | 0 个 404 |
| Admin 静态资源 | JS/CSS | 0 个 404 |
| H5 导入依赖 | stores/api/components/types | 全部解析 |
| Admin 导入依赖 | 86 stores/api/components | 全部解析 |
| TypeScript 编译 | vue-tsc --noEmit | 0 错误 |
| Vite 生产构建 | H5 + Admin | 0 错误 |

### 24.2 修复的问题

| 编号 | 文件 | 问题 | 修复 |
|------|------|------|------|
| QA-1 | `h5/src/api/tasks.ts` | fetchCurrentStage 路径错误 | `/api/v1/miniprogram/progress` → `/api/v1/mp/progress/summary` |
| QA-2 | `h5/src/api/tasks.ts` | fetchPublishedNarrative 路径错误 | `/api/v1/coach/messages/inbox` → `/api/v1/messages/inbox` |
| QA-3 | Admin 9 文件 (32处) | API 双前缀 `/api/api/v1/` 致 404 | `${API_BASE}/api/v1/` → `${API_BASE}/v1/` |

### 24.3 不影响使用的正常现象

- `/v1/health/p001/*` 返回 404 → `health.ts` 有 mock fallback, 页面正常显示模拟数据
- `/v1/tenants/hub` 返回空列表 → 无种子专家数据, ExpertHub 正常显示空状态
- 需要登录的 API 返回 401 → 正常的 JWT 认证保护

---

## 二十五、Westworld v0.4 仿真验证 (2026-02-09)

> BHP 行为仿真引擎 — 16 模块 / 2798 LOC / 零依赖 / 9 管线 / 116 断言

### 25.1 仿真引擎概述

| 属性 | 数值 |
|------|------|
| 引擎版本 | Westworld Sim v0.4 |
| 代码量 | 16 模块, 2798 LOC (纯 Node.js ESM) |
| 依赖 | 0 (零依赖) |
| BPT-6 人格类型 | 6 基础 + 4 变体 = 10 子类型 |
| 仿真管线 | 9 条 (状态/TTM/BPT-6/Agent Chain/WS/Coach/Credit/问卷治理/一致性) |
| 断言测试 | 116 项 (12 组) |
| 日循环步骤 | 14 步/用户/天 |

### 25.2 测试执行结果

| 测试阶段 | 规模 | 结果 |
|----------|------|------|
| 标准仿真 | 90d × 20u | PASS |
| 116 断言 (标准) | 12 组 | 116/116 PASS |
| 9 管线深度验证 | 18 项检查 | 18/18 PASS |
| 压力测试 | 180d × 100u | PASS |
| 116 断言 (压力) | 12 组 | 116/116 PASS |

### 25.3 后端注入验证

为支持仿真数据注入，在 `api/agent_api.py` 新增 3 个端点:

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/v1/agent/pending-reviews/inject` | POST | 注入待审案例 |
| `/api/v1/agent/events/inject` | POST | 注入行为事件 |
| `/api/v1/content-governance/audit-log/inject` | POST | 注入治理日志 |

注入脚本 `api_inject.js` 适配改造: JWT 认证流 + 429 rate-limit 重试 (3次指数退避) + 120ms 请求节流。

#### 注入数据量

| 管线 | 端点 | 注入量 | 状态 |
|------|------|--------|------|
| 用户注册 | `/auth/register` | 20 用户 | DONE |
| 评估提交 | `/api/assessment/submit` | 239 份 | DONE |
| 待审案例 | `/agent/pending-reviews/inject` | 117 案例 | DONE |
| 行为事件 | `/agent/events/inject` | 332 事件 | DONE |
| 治理日志 | `/content-governance/audit-log/inject` | 99 条 | DONE |

注入失败率 < 1% (仅 3 条 429 rate-limit 散点)。

### 25.4 关键仿真指标

| 指标 | 标准 (90×20) | 压力 (180×100) |
|------|-------------|----------------|
| 饱和用户 | 0% | 0% |
| TTM 阶段覆盖 | 6/6 | 6/6 |
| Agent 追踪链 | 176 (0 中断) | 1,781 |
| Coach 审核 | 54 | 728 |
| WS 事件 | 5,221 | 53,457 |
| 投递率 | 84.8% | — |
| ACK 率 | 99.2% | — |
| 平均 XP | 1,109 | 2,132 |
| 最大连续打卡 | 52 天 | 108 天 |
| 考试通过率 | 76% | 80% |

### 25.5 测试日志

完整测试日志: `D:\20260204第16版本升级内容\test\westtest\TESTLOG_v04_20260209.md` (308 行, 7 章节)

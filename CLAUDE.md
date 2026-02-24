# BHP 行为健康数字平台 — Claude Code 项目指令 (V5.2.9)

> 本文件由 Claude Code 自动加载，指导 AI 如何在本项目中工作。
> **V5.2.9 变更**: 2026-02-24 VisionGuard视力行为保护域: Migration 053(5新表) + core/vision_service.py(5 ORM+评分引擎+风险评估+监护人+处方触发) + VisionGuideAgent(5意图+处方生成) + 5 Scheduler Jobs(23:00/23:15/Mon08/Sun06/月1日) + api/vision_api.py(14端点) + H5 4页面(打卡/监护人/档案/检查) + Admin审批队列 + h5/src/api/vision.ts; 铁律合规(AI→教练审核→推送)
> **V5.2.8 变更**: 2026-02-24 审计I-01~I-09全量实施: Migration 052(2新表+7列扩展) + 双轨角色升级(I-01) + 激活4项检查(I-02) + 督导行动项派发(I-03) + 显示名称统一7处(I-04) + 强制Agent(I-05) + 铁律执行(I-06) + 资质生命周期(I-07, 4端点+调度器) + 积分差异化(I-08) + 循证等级治理(I-09) + 8处代码纠偏(C1-C8)
> **V5.2.7 变更**: 2026-02-24 督导专家系统(6端点+状态机) + 租户生命周期(3端点) + RBAC修复 + P1 E2E验证3修复(json.dumps+事务隔离) + P1通知增强(WebSocket推送+2新端点) + 33测试
> **V5.2.6 变更**: 2026-02-24 P1闭环: BehaviorRx引擎集成(混合路由<200ms) + 教练审批→通知推送(深度链接) + H5处方详情页(5卡片) + 新增5文件修改8文件
> **V5.2.5 变更**: 2026-02-24 Rx仪表盘数据修复(Agent状态+策略模板字段转换) + 干预包后端(10包3端点) + 绑定管理权限修复 + 专家工作台iframe端口修复
> **V5.2.4 变更**: 2026-02-23 AI行为处方生成(839行服务+LLM/规则引擎双路径+5标签页全接入) + 教练学员角色过滤修复(_STUDENT_ROLES白名单)
> **V5.2.3 变更**: 2026-02-22 教练端三合一增强 — 种子业务数据(6角色全量) + 教练双重身份(CoachSelfHealthSummary) + 教练端13页响应式
> **V5.2.2 变更**: 2026-02-22 头像/退出/WeChat同步(13文件) + 统一个人中心(8文件) + 六级累进任务目录(1文件, 42项)
> **V5.2.1 变更**: 2026-02-22 预发布审计全绿 (56P/0F) + CI修复 (register_external_models) + 多模态单元测试 (28 tests)
> **V5.2.0 变更**: 2026-02-21 P7 Smart Hub 多模态采集中心 (4模式底部面板) + ASR语音转文字服务 (cloud_first策略, 2端点)
>
> 上游契约: `E:\注册表更新文件\行健平台-契约注册表-V5_2_7-CONSOLIDATED.md` (V5.2.8 唯一权威版)
> Agent配置清单: `agent_multimodal_host_config.md` (47+ Agent类 · 15预设模板 · 4层安全 · 6模态)

---

## 一、项目概述

BHP（Behavioral Health Platform）是一个行为健康数字化管理平台，服务于慢病逆转与行为改变领域。平台包含 Observer(观察者)、Grower(成长者)、Coach(教练)、Expert(专家)、Admin(管理员) 五种用户角色，集成了评估引擎、AI Agent 系统、RAG 知识库、多模态交互引擎、智能监测方案及微信生态对接能力。

**规模**: 84+ 路由模块 · 681+ API 端点 · 152 数据模型 · 53 迁移版本 · **48+ AI Agent 类** · 16+ Docker 容器 · **10 种交互模态** · **3 条微信通道** · **全平台搜索(三端隔离)** · **行为周报(自动+H5展示)** · **32页Admin响应式** · **全mock=0** · **预发布审计56P/0F** · **CI 4-stage全绿** · **六级累进任务目录(42项)** · **统一个人中心(3共享组件)** · **教练端全量种子数据** · **教练双重身份健康面板** · **AI行为处方(BehaviorRx+LLM双路径)** · **学员角色白名单过滤** · **干预包管理(10包3端点)** · **Rx仪表盘全数据联通** · **P1闭环(AI生成→审批→通知→H5详情, 8/8 E2E)** · **督导会议系统(6端点)** · **租户生命周期(状态机)** · **审计I-01~I-09(资质生命周期+循证等级+铁律执行)** · **VisionGuard视力行为保护(14端点+5表+1Agent+5Job+5页面)**

> ⚠️ **V5.2.9 变更** (2026-02-24):
> - **VisionGuard 视力行为保护域** (18文件: 10新建+8修改):
>   - **Migration 053**: 5新表 — vision_exam_records(检查) + vision_behavior_logs(行为日志) + vision_behavior_goals(目标) + vision_guardian_bindings(监护关系) + vision_profiles(视力档案)
>   - **core/vision_service.py**: 5 ORM模型 + calc_behavior_score(五维加权) + assess_vision_risk + build_instant_message(TTM感知) + 监护人CRUD + adjust_goals_for_stage + generate_weekly_report + check_rx_trigger(→coach_push_queue铁律)
>   - **VisionGuideAgent**: 5意图(behavior_checkin/goal_inquiry/guardian_summary/resistance_handling/expert_consultation) + VisionRxGenerator(3格式处方)
>   - **5 Scheduler Jobs**: vision_daily_score(23:00) + vision_rx_trigger(23:15) + vision_weekly_guardian_report(Mon 08:00) + vision_goal_auto_adjust(Sun 06:00) + vision_monthly_archive(月1日 03:00)
>   - **api/vision_api.py**: 14端点(/v1/vision/*: log打卡/goals目标/guardian监护/profile档案/exam检查/dashboard仪表盘)
>   - **H5 4页面**: VisionDailyLog(SVG环形+5维卡片) + VisionGuardianView(孩子报告+趋势) + VisionProfile(风险+监护人) + VisionExamRecord(录入+历史)
>   - **Admin**: CoachVisionRxQueue.vue(视力处方审批队列, Ant Design Vue 4)
>   - **h5/src/api/vision.ts**: 12个API方法
>   - **铁律合规**: Job28检测连续3天评分下降 → check_rx_trigger → coach_push_queue(source_type="vision_rx") → 教练审批 → 推送
>
> ⚠️ **V5.2.8 变更** (2026-02-24):
> - **审计I-01~I-09全量实施** (23文件: 4新建+19修改):
>   - **I-01 双轨角色升级**: expert_registration_api — physician_license/phd_supervision→SUPERVISOR, 其他→COACH + RoleChangeLog审计
>   - **I-02 激活4项检查**: tenant_api — role_confirmed + ethics_signed(EthicalDeclaration) + workspace_ready + no_violations
>   - **I-03 督导行动项派发**: supervision_service + supervision_api — prescription_adjust→CoachPushQueue, learning_task/self_reflection→Notification
>   - **I-04 显示名称统一7处**: "督导"→"督导专家" + "推广者"→"促进师" (user_api/admin_analytics_api/useCurrentUser.ts/MyContributions.vue/Index.vue)
>   - **I-05 强制Agent**: FORCED_AGENTS=["crisis","supervisor_reviewer"] + init-defaults端点
>   - **I-06 铁律执行**: access_control — supervisor不能直推学员(必须经CoachPushQueue)
>   - **I-07 资质生命周期**: `core/supervisor_credential_service.py`(~220行) + `api/supervisor_credential_api.py`(4端点) + scheduler credential_annual_review(05:00)
>   - **I-08 积分差异化**: governance_points — role_points_override(supervisor:80/promoter:50)
>   - **I-09 循证等级治理**: evidence_tier(T1-T4) + confidence_multiplier + router评分加成 + 创建权限校验
> - **Migration 052**: supervisor_credentials(16列) + role_change_logs(8列) + expert_tenants(+7列) + agent_templates(+evidence_tier)
> - **8处代码纠偏(C1-C8)**: role_level→ROLE_LEVEL.get / name→username / EthicsSignature→EthicalDeclaration / TenantDocument→KnowledgeDocument / CoachNotification→Notification / LearningAssignment→Notification(type=) / credit_service→governance_points_integration / specialist_agents→remaining_agents
>
> ⚠️ **V5.2.7 变更** (2026-02-24):
> - **督导专家系统**: `core/supervision_service.py`(~200行: CRUD+状态机) + `api/supervision_api.py`(6端点) + MySupervision.vue真实API; SUPERVISOR显示名→"督导专家"; supervisor_7clause伦理条款
> - **租户生命周期**: tenant_api 3端点(activate/suspend/archive) + `_VALID_TRANSITIONS`状态机 + 扩展stats(retention/graduation/agents)
> - **P1 E2E验证修复(3Bug)**: ①`edited_rx_json` str()→json.dumps(ensure_ascii=False); ②缺少import json; ③审批后处方未持久化(generate_daily_tasks_for_user失败→PG事务abort)→task gen移至commit后(non-blocking)
> - **P1通知增强**: deliver_item()+approve_review() 追加WebSocket push_user_notification; 新增 `GET /notifications/all`(unread_only+link解析) + `POST /notifications/{id}/read`
> - **RBAC/Scheduler/测试**: user_api PROMOTER遗漏(2处); tenant_trial_expiration(04:00)+supervision_reminder(07:30); 33新测试全绿
>
> ⚠️ **V5.2.6 变更** (2026-02-24):
> - **P1闭环 — BehaviorRx集成**: `core/rx_context_adapter.py`(BehavioralProfile→RxContext) + `core/rx_response_mapper.py`(RxPrescriptionDTO→Copilot 6-key JSON); `copilot_routes.py` 混合路由(BehaviorRx<200ms优先→LLM降级); `r4_role_upgrade_trigger.py` 初始处方接入引擎
> - **P1闭环 — 通知推送**: `r6_coach_flywheel_api_live.py` approve_review审批后写notifications表+深度链接`[link:/rx/{rx_id}]`; `main.py` notifications/system端点增加notifications表查询+link解析; 新增 `GET /rx/my` + `GET /rx/{rx_id}` 端点
> - **P1闭环 — H5处方详情**: `RxPrescriptionDetail.vue`(5卡片:阶段/目标/策略/障碍/支持) + `types/rx.ts` + `api/rx.ts`; 路由`/rx/:id`; Notifications.vue系统通知点击跳转; MyPlan.vue处方列表入口
> - **附带修复**: ExpertAgentType枚举大写 + coach_review_logs列名漂移(note→elapsed_seconds) + get_db_session→SessionLocal
>
> ⚠️ **V5.2.5 变更** (2026-02-24):
> - **干预包管理后端**: `configs/intervention_packs.json`(10个干预包, 6域) + `api/intervention_api.py`(3端点: list/match/detail, JSON配置只读)
> - **Rx仪表盘数据联通**: `behavior_rx/rx_routes.py` — agents/status端点返回富AgentStatusEntry[](名称/能力/域/处方统计, DB实时查询) + strategies端点包装{strategies,total}+字段名转换(ttm_stage_range→applicable_stages等)
> - **绑定管理权限修复**: `admin_bindings_api.py` require_admin→require_coach_or_admin(9处), 促进师/教练可访问
> - **Rx API路径修复**: `rxApi.ts` 8端点路径添加/v1前缀; `RxDashboard.vue` 路由感知Tab切换(useRoute+routeTabMap)
> - **专家工作台修复**: `UI2BridgePage.vue` iframe端口5177→8501(匹配bhp-expert-workbench容器)
>
> ⚠️ **V5.2.4 变更** (2026-02-23):
> - **AI行为处方生成**: `core/copilot_prescription_service.py`(839行) — CopilotPrescriptionService; 数据采集(8维度7天窗口) → LLM分析(UnifiedLLMClient, TTM/BPT-6/CAPACITY/SPI prompt, timeout=20s) → 规则引擎降级(CAPACITY→六因素, 阶段→处方) → 合并补齐; 返回 diagnosis+prescription+ai_suggestions+health_summary+intervention_plan+meta; `POST /copilot/generate-prescription`; CoachHome 5标签页全接入
> - **教练学员角色过滤**: `api/coach_api.py` — `_STUDENT_ROLES=[OBSERVER,GROWER,SHARER]` 白名单; `/dashboard`+`/students`查询添加`User.role.in_(_STUDENT_ROLES)`; DB清理: promoter/supervisor绑定标记is_active=false; 角色规则: 学员层(L1-L3)被辅导 ← 辅导层(L4+)向下跟进
>
> ⚠️ **V5.2.3 变更** (2026-02-22):
> - **Phase 1 种子业务数据**: `scripts/seed_test_business_data.py` (400行, 幂等, --dry-run); 6角色全量数据: 385任务+244打卡+103血糖+28睡眠+28活动+8会话26消息+36学习+2教练绑定+8推送队列+7教练消息+3同道者关系
> - **Phase 2 教练双重身份**: `CoachSelfHealthSummary.vue` (120行, 4指标+任务进度); 嵌入CoachHome KPI卡和学员列表之间; export from health/index.ts
> - **Phase 3 教练端响应式**: CoachHome(+20CSS)+CoachAiReview(+15)+CoachWorkbench(+12)+10页批量响应式; 合计13页coach新增@640px移动端断点
>
> ⚠️ **V5.2.2 变更** (2026-02-22):
> - **头像/退出/WeChat同步 (13文件)**: useCurrentUser.ts组合式(登出+WeChat信息) + UserAvatarPopover.vue(头像气泡卡片) + 5个工作台集成 + Login.vue角色分流修复 + auth_api/wechat_auth_api后端同步
> - **统一个人中心 (8文件)**: PersonalHealthProfile.vue(健康档案) + MyContributions.vue(我的分享) + MyBenefits.vue(我的权益) 3个共享组件; MyProfile.vue→3折叠面板统一页; SharerWorkbench(1077→170行)/CoachWorkbench/ExpertWorkbench集成
> - **六级累进任务目录 (1文件)**: TASK_CATALOG 21→42项 + ROLE_TO_LEVEL映射 + min_level过滤; L0(5) L1(21) L2(29) L3(35) L4(39) L5(42); 前端零修改(catalogGroups按tag自动分组)
>
> ⚠️ **V5.1.9 变更** (2026-02-20):
> - **P2 深耕 (V5.1.4)**: R1 Checkin→TrustScore管道 · R2 Admin 86页mock审计(-2675行) · R3 食物AI→自动签到 · R4 设备→自动签到 · R5 H5 3页实装 · R6 Admin+Expert飞轮16端点live · R7 死代码清理(-1224行)
> - **P3 自动化运维 (V5.1.5)**: R8 处方→任务生成Job(06:15) · R9 信任监控+断连重连Job(22:00) · R10 教练自动上报Job(08:00)
> - **P4 Mock清零 (V5.1.6)**: R11-R14 共22页修复 · health.ts全量重写(15+端点) · settings_api.py新建
> - **P5 基础设施 (V5.1.7)**: Migration 046(WeChat ORM同步) · 047(analytics_daily聚合) · 048(feature_flags+A/B测试)
> - **Admin响应式 (V5.1.8)**: useResponsive.ts组合式 · responsive.css全局 · 19页响应式改造(侧边栏/KPI/双栏/三栏/聊天/看板/浮层)
> - **P6A 全平台搜索 (V5.1.9)**: search_service(5模块) + search_api(三端隔离admin/coach/client)
> - **P6B 自动化周报 (V5.1.9)**: Migration 049 + weekly_report_service(8维度) + weekly_report_api(4ep) + scheduler(Sunday 21:00)
> - **全mock清零 (V5.1.9)**: QuestionBank(修复6项mismatch+bulk endpoint) · CoachStudentList/StudentAssessment(确认已有API) → 全mock=0
> - **H5周报页 (V5.1.9)**: WeeklyReport.vue(报告展示+历史切换) · MyLearning入口 · 路由注册
> - asyncpg CAST语法修复 · Chat Ollama fallback正常工作
> - **全平台测试: 96/96 + 5/5 chains · CI 4-stage门禁**
> - **P7 Smart Hub (V5.2.0)**: QuickInputHub.vue(4模式采集面板: 快速记录/拍一拍/说一说/问AI) · health.ts+recognizeFood · HomeViewOptimized中心按钮→弹出Hub
> - **ASR服务 (V5.2.0)**: core/asr_service.py(cloud_first: OpenAI Whisper→本地8090) · api/audio_api.py(transcribe+status) · config 6项
> - **H5 QuickInputHub (V5.2.0)**: h5/TabBar中心FAB+QuickInputHub.vue(Vant popup 4模式) · h5/api/health.ts(8方法)
> - **语音ASR升级 (V5.2.0)**: 双端QuickInputHub "说一说"模式 — Web Speech API(主) + MediaRecorder→服务端ASR(fallback)
> - **VLM服务层 (V5.2.0)**: core/vlm_service.py(ollama_first: Ollama qwen2.5vl→Cloud VLM) · config 6项 · food_recognition重构
> - **预发布审计 (V5.2.1)**: pre_launch_verify.py Docker兼容重构(56P/0F/2S/10W) · Dockerfile+postgresql-client · db_backup.sh凭据修复
> - **多模态单测 (V5.2.1)**: tests/test_multimodal_services.py(28 tests: ASR/VLM/食物解析/Audio API)
> - **CI修复 (V5.2.1)**: core/models.py+register_external_models() · CI create_all()前注册外部ORM模型 · M16_Reflection 500→200

---

## 二、技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.10+ / FastAPI / Uvicorn (4 workers) / APScheduler |
| ORM | SQLAlchemy (同步+异步双模) + Alembic |
| 数据库 | PostgreSQL (pgvector) + Redis + Weaviate |
| 认证 | JWT (python-jose) + bcrypt (passlib) + Token 黑名单 |
| Admin 前端 | Vue 3 + TypeScript + Vite + Ant Design Vue 4 + Tailwind CSS |
| H5 移动端 | Vue 3 + TypeScript + Vite + Vant 4 + Tailwind CSS |
| 微信小程序 | Taro 3 + Vue 3 + 微信原生API |
| LLM | 云端 (DeepSeek/Qwen, cloud_first策略) + 本地 Ollama (qwen2.5:0.5b / qwen2.5vl:7b) + Dify 工作流 |
| 多模态引擎 | ASR: Whisper/Paraformer · TTS: Edge-TTS · VLM: Qwen-VL · 姿态: MediaPipe/MoveNet |
| 嵌入 | sentence-transformers (text2vec-base-chinese, 768 维) / Ollama nomic-embed-text (回退) |
| 容器化 | Docker Compose |
| 反向代理 | nginx (前端容器内, /api → bhp-api) |
| 微信网关 | FastAPI 独立服务 · 微信公众平台API · 企业微信API · 微信支付SDK |

---

## 三、项目结构 *(V5.0.1 修正)*

```
behavioral-health-project/
├── main.py                         # ★ FastAPI 入口 (根目录, 非 api/ 下)
├── core/                           # ★ 核心业务逻辑 (models/database/redis在此)
│   ├── models.py                   # 130+ SQLAlchemy 模型 + UserRole枚举 + ROLE_LEVEL映射 (含048迁移)
│   ├── database.py                 # 同步+异步双模引擎/会话管理 (get_db / get_async_db)
│   ├── auth.py                     # JWT签发/验证/黑名单
│   ├── redis_lock.py               # Redis SETNX 分布式互斥锁 (参数: ttl=)
│   ├── master_agent_v0.py          # MasterAgent V0 九步处理流程 (4800+行)
│   ├── master_agent_unified.py     # UnifiedMasterAgent (v0+v6 合并)
│   ├── agents/                     # Agent 体系
│   │   ├── specialist_agents.py    # 9个核心专科Agent
│   │   ├── integrative_agents.py   # 3个整合型Agent
│   │   ├── v4_agents.py            # 4个V4.0旅程Agent
│   │   ├── trust_guide_agent.py    # 信任引导Agent
│   │   ├── generic_llm_agent.py    # 通用模板Agent
│   │   ├── vision_agent.py        # VisionGuideAgent (视力行为保护, 5意图+处方生成)
│   │   ├── router.py              # AgentRouter 6步路由
│   │   ├── coordinator.py         # MultiAgentCoordinator 9步协调
│   │   └── master_agent.py        # V6 模板感知版
│   ├── multimodal/                 # V5.0: 多模态处理引擎
│   │   ├── protocol.py            # 10种模态定义
│   │   ├── asr_service.py         # 语音识别
│   │   ├── tts_service.py         # 语音合成
│   │   ├── vlm_service.py         # 视觉理解
│   │   ├── video_service.py       # 视频分析
│   │   ├── emotion_service.py     # 情绪感知
│   │   └── safety_gate.py         # 多模态安全红线 (S1-S6)
│   ├── brain/
│   │   ├── stage_runtime.py       # 阶段运行态 (唯一可写 current_stage)
│   │   ├── policy_gate.py         # 策略闸门
│   │   └── decision_engine.py
│   ├── baps/                      # BAPS五维评估 + V5.0新增4引擎
│   ├── v14/
│   │   └── agents.py              # V14增强: SafetyAgent + ResistanceAgent + ExplainAgent
│   ├── vision_service.py             # VisionGuard: 5 ORM + 评分引擎 + 风险评估 + 监护人 + 处方触发
│   └── schemas/
├── api/                            # ★ 路由模块包
│   ├── dependencies.py             # 认证守卫: get_current_user / require_admin / require_coach_or_admin
│   ├── config.py                   # DIFY/OLLAMA 配置
│   ├── *_api.py                    # 50+ 路由模块 (含event_tracking/feature_flag/settings_api/vision_api)
│   ├── *_service.py                # 61+ 核心服务 (含device_task_bridge/trust_score_service)
│   ├── r2_scheduler_agent.py       # ★ V5.0 R2 飞轮: 处方→每日任务
│   ├── r3_grower_flywheel_api_live.py  # ★ V5.0 R3: Grower飞轮 (5端点)
│   ├── r4_role_upgrade_trigger.py  # ★ V5.0 R4: 评估完成→角色升级
│   ├── r5_observer_flywheel_api_live.py # ★ V5.0 R5: Observer试用墙 (3端点)
│   ├── r6_coach_flywheel_api_live.py    # ★ V5.0 R6: Coach审核队列 (4端点)
│   ├── r7_notification_agent.py    # ★ V5.0 R7: 主动触达 (微信+通知表+教练审批)
│   ├── r8_user_context.py          # ★ V5.0 R8: 跨session记忆
│   ├── wechat/                     # V5.0: 微信生态服务
│   │   ├── wx_gateway.py           # 服务号消息网关
│   │   ├── wx_message_converter.py
│   │   ├── wx_template.py
│   │   ├── wx_auth.py
│   │   ├── wx_pay.py
│   │   └── wx_work.py
│   └── migrations/                 # Alembic 迁移
├── behavior_rx/                    # BehaviorRx 专家Agent (4个)
│   └── agents/
│       ├── behavior_coach_agent.py
│       ├── metabolic_expert_agent.py
│       ├── cardiac_expert_agent.py
│       └── adherence_expert_agent.py
├── assistant_agents/               # 用户层助手Agent (11个)
│   └── agents/
│       ├── domain_agents.py        # nutrition/exercise/sleep/emotion
│       ├── remaining_agents.py     # tcm/motivation/habit/community/content
│       ├── onboarding_guide.py
│       ├── crisis_responder.py
│       └── tcm_ortho_agents.py     # 中医骨科用户层 (2个)
├── professional_agents/            # 教练层专业Agent (6+3个)
│   └── agents/
│       ├── core_engines.py         # assessment_engine + rx_composer
│       ├── behavior_coach.py
│       ├── remaining_agents.py     # domain_expert + supervisor + quality_auditor
│       └── tcm_ortho_expert_agents.py  # 中医骨科教练层 (3个)
├── gateway/
│   └── bridge.py                   # V4.1兼容桥接 (含catch-all, 必须最后注册)
├── admin-portal/                   # Vue 3 管理后台 (:5174) — Coach + Admin (32页响应式)
│   └── src/composables/
│       ├── useResponsive.ts              # 响应式断点组合式 (<640/768/1024/1280)
│       └── useCurrentUser.ts             # V5.2.2: 当前用户组合式 (logout/wechat info)
│   └── src/components/health/
│       ├── index.ts                      # 统一导出 (UserAvatarPopover + 3共享组件 + CoachSelfHealthSummary)
│       ├── UserAvatarPopover.vue         # V5.2.2: 头像气泡卡片 (size/theme props)
│       ├── PersonalHealthProfile.vue     # V5.2.2: 健康档案共享组件 (~580行)
│       ├── MyContributions.vue           # V5.2.2: 我的分享共享组件 (~420行)
│       ├── MyBenefits.vue                # V5.2.2: 我的权益共享组件 (~350行)
│       └── CoachSelfHealthSummary.vue    # V5.2.3: 教练自身健康概览 (4指标+任务进度)
│   └── src/views/coach/
│       └── CoachVisionRxQueue.vue       # V5.2.9: 视力处方审批队列 (Ant Design Vue 4)
├── h5/                             # Vue 3 移动端 (:5173) — Observer + Grower
│   └── src/views/vision/                # V5.2.9 VisionGuard 4页面
│       ├── VisionDailyLog.vue           # 视力行为打卡 (SVG环形+5维卡片)
│       ├── VisionGuardianView.vue       # 孩子视力报告 (监护人视角+趋势图)
│       ├── VisionProfile.vue            # 视力档案 (风险等级+监护人+专家绑定)
│       └── VisionExamRecord.vue         # 视力检查记录 (录入+历史+趋势)
├── miniprogram/                    # V5.0: 微信小程序 (Taro 3)
├── knowledge/                      # 知识库 (Markdown)
├── configs/                        # 业务配置文件
│   ├── agent_templates_seed.json   # 15个Agent预设模板
│   ├── spi_mapping.json
│   ├── badges.json
│   ├── multimodal_permissions.json
│   └── assessment/
├── contracts/                      # 契约注册表
│   └── 行健平台-契约注册表-V5_0_1.xlsx
├── agent_multimodal_host_config.md # Agent & 多模态 Host 配置清单
├── docker-compose.app.yaml
├── docker-compose.yaml
└── docker-compose.wechat.yaml
```

---

## 四、Docker 端口映射

### 4.1 核心应用容器

| 容器 | 端口 | 说明 | 角色 |
|------|------|------|------|
| bhp-api | 8000-8002 | FastAPI 主 API (健康检查: `GET /health`) | 全部 |
| bhp-h5 | 5173→80 | H5 移动端 (nginx) | Observer + Grower |
| bhp-admin-portal | 5174→80 | 管理后台 (nginx) | Coach + Expert + Admin |
| bhp-expert-workbench | 8501 | Streamlit 专家工作台 *(P3迁移至React)* | Expert |

### 4.2 V5.0 新增容器

| 容器 | 端口 | 说明 | 依赖 |
|------|------|------|------|
| bhp-wx-gateway | 8080 | 微信服务号消息网关 | bhp-api, bhp-asr, bhp-vlm |
| bhp-asr | 8002 | 语音识别服务 (Whisper/Paraformer) | GPU可选 |
| bhp-tts | 8003 | 语音合成服务 (CosyVoice/Edge-TTS) | GPU可选 |
| bhp-vlm | 8004 | 视觉理解服务 (Qwen-VL / 食物识别) | GPU推荐 |

### 4.3 Dify 基础设施容器

| 容器 | 端口 | 说明 |
|------|------|------|
| dify-web | 3000 | Dify 前端 |
| dify-api | 5001 | Dify 后端 |
| dify-nginx | 8080/8443 | Dify 网关 *(与bhp-wx-gateway端口冲突, 需调整)* |
| dify-db (PostgreSQL) | 5432 (已暴露) | pgvector 扩展 |
| dify-redis | 6379 | 会话缓存 / Token 黑名单 / 调度锁 |

**网络**: 所有容器共享 `dify_dify-network` 外部网络。

---

## 五、编码规范 *(V5.0.1 精确化)*

### 5.1 后端 (Python/FastAPI)

- API 路由统一前缀 `/api/v1/`，**不要出现 `/api/api/v1/` 双前缀**
- 所有路由文件命名 `*_api.py`，服务文件命名 `*_service.py`
- 认证守卫使用 `api/dependencies.py` 中的:
  - `get_current_user` → 普通用户 (返回同步 Session 注入的 User 对象)
  - `require_coach_or_admin` → role.value in ["coach", "supervisor", "promoter", "master", "admin"]
  - `require_admin` → role.value == "admin"
- **角色枚举 (UserRole, core/models.py)**:

  | 枚举值 | ROLE_LEVEL | 显示 | 说明 |
  |--------|-----------|------|------|
  | `observer` | 1 | L0 | 观察者 |
  | `grower` | 2 | L1 | 成长者 |
  | `sharer` | 3 | L2 | 分享者 |
  | `coach` | 4 | L3 | 健康教练 |
  | `promoter` | 5 | L4 | 促进师 |
  | `supervisor` | 5 | L4 | 督导 (与促进师平级) |
  | `master` | 6 | L5 | 大师 |
  | `admin` | 99 | — | 系统管理员 |
  | `patient` | 2 | — | 旧角色, 等同 grower |

  > ⚠️ 代码中枚举值是 `coach`/`promoter`/`master`，**不是** `bhp_coach`/`bhp_promoter`/`bhp_master`

- **`users` 表没有 `role_level` 列**, 角色等级通过映射字典获取:
  ```python
  from core.models import ROLE_LEVEL, ROLE_LEVEL_STR
  level = ROLE_LEVEL.get(user.role, 1)        # UserRole枚举 → int
  level = ROLE_LEVEL_STR.get("coach", 4)      # 字符串 → int
  ```
- 定时任务必须使用 `@with_redis_lock(lock_name, ttl=300)` 装饰器 — **参数名是 `ttl`，不是 `timeout`**
- 数据库操作:
  - **同步**: `from core.database import get_db` → yields `Session` (大部分现有 *_api.py 用)
  - **异步**: `from core.database import get_async_db` → yields `AsyncSession` (R2-R8 飞轮代码用)
  - Session工厂: `from core.database import AsyncSessionLocal` (不是 `async_session_factory`)
- 新增数据模型写在 `core/models.py`, 新迁移用 Alembic
- ORM default 写法: `server_default=sa_text("'value'")` (兼容 Alembic autogenerate)
- 中文注释, 遵循 PEP8
- **完整 import 约定见 §十六**

### 5.2 前端 (Vue 3 + TypeScript)

- 使用组合式 API (`<script setup lang="ts">`)
- Admin 使用 Ant Design Vue 4, H5 使用 Vant 4
- 样式遵循 BHP Design System, 品牌主色 `--bhp-brand-primary: #10b981` (翡翠绿)
- TTM 阶段样式使用 `useStageStyle` composable
- API 调用统一放 `src/api/`, 使用 axios 实例
- Store 使用 Pinia, 放 `src/stores/`
- **响应式适配** *(V5.1.8)*:
  - `src/composables/useResponsive.ts` — 断点: mobile(<640), compact(<768), tablet(640-1023), desktop(>=1024)
  - `src/styles/responsive.css` — 全局表格/弹窗/抽屉/KPI/表单/描述列表响应式
  - `main.ts` 中 `import './styles/responsive.css'` 必须在 `antd-overrides.css` 之后
  - KPI: `:span="6"` → `:xs="24" :sm="12" :lg="6"`; 双栏: `:span="16/8"` → `:xs="24" :lg="16/8"`
  - AdminLayout: `isCompact`时侧边栏变为 overlay + hamburger 按钮
  - 模态宽度: `modalWidth(desktopPx)` → mobile返回'100%', compact返回min(px, vw-48)

### 5.3 多模态编码规范

- **统一消息协议**: `core/multimodal/protocol.py` 定义的 `MultimodalMessage`
- **10 种模态**: text / voice / image / video / file / device / location / card / action / system
- **组件统一**: `MultimodalChat.vue`, 禁止各页面自行实现对话UI
- **安全红线**: S1-S6 规则 (见 §6.18), 实现在 `core/multimodal/safety_gate.py`
- **媒体不留存**: 原始音频/图片/视频处理后删除, 仅保留分析结果
- **TTS医疗过滤**: 不合成具体药名/剂量, 改为文字显示

### 5.4 微信渠道编码规范

- 微信网关代码放 `api/wechat/`, 消息转换 `wx_message_converter.py`
- 被动回复 **5 秒内返回**, 超时走客服消息异步推送
- 文本回复 **最大 600 字**, 模板消息每用户每日 **≤3 条**
- OpenID / UnionID / session_key **禁止在日志中明文输出**
- 小程序: 主包 ≤ 2MB, 分包 ≤ 20MB, Taro 3 + Vue 3

---

## 六、核心业务概念

### 6.1 BAPS 五维评估体系

五维评估框架, 共 171 题:
- **TTM7** (21题): S0-S6 行为改变阶段
- **BIG5** (50题): 大五人格
- **BPT-6** (18题): 行为分型 (action/knowledge/emotion/relation/environment/mixed)
- **CAPACITY** (32题): 8维度改变潜力
- **SPI** (50题): 成功指数 → L1-L5 心理层级

V5.0 新增 4 引擎: PainScale · PainAssess · TCMSyndrome · RehabStage

### 6.2 TTM7 七阶段行为改变模型

| 阶段 | 中文名 | 友好名称 | 升级硬条件 |
|------|--------|----------|-----------|
| S0 | 无知无觉 | 探索期 | — |
| S1 | 强烈抗拒 | 思考期 | awareness ≥ 0.3 |
| S2 | 被动承受 | — | belief ≥ 0.3, awareness ≥ 0.5 |
| S3 | 勉强接受 | 准备期 | belief ≥ 0.6, capability ≥ 0.5 |
| S4 | 主动尝试 | 成长期 | belief ≥ 0.7, 7天内≥3次行为 |
| S5 | 规律践行 | 巩固期 | belief ≥ 0.8, 连续14天 |
| S6 | 内化为常 | 收获期 | belief ≥ 0.9, 连续60天 |

### 6.3 五层次心理准备度 (L1-L5)

| 层级 | SPI系数 | 策略 | 最大任务数 |
|------|---------|------|-----------|
| L1 完全对抗 | 0.3 | 安全感建立, 禁止设定目标 | 1 |
| L2 抗拒与反思 | 0.5 | 矛盾处理, 探索性尝试 | 1 |
| L3 妥协与接受 | 0.7 | 微习惯处方, 降低门槛 | 2 |
| L4 顺应与调整 | 0.9 | 系统化行为方案 | 3 |
| L5 全面臣服 | 1.0 | 自主管理, 身份巩固 | 不限 |

### 6.4 MasterAgent 九步处理流程

```
输入 → Step1-2: 多模态预处理(ASR/VLM/OCR)
     → Step2.5: SafetyPipeline L1 (危机→CrisisAgent, 违规→deny)
     → Step3: 更新 UserMasterProfile
     → Step4: AgentRouter (先PolicyEngine, 回退AgentRouter 6步)
     → Step4.5: InsightGenerator 数据洞察
     → Step5: 调用 1-2个 Agent (从47+中路由)
     → Step6: MultiAgentCoordinator 9步协调
     → Step7: RuntimePolicyGate (ALLOW/DELAY/ESCALATE/DENY)
     → Step7.5: SafetyPipeline L3 生成守卫
     → Step8: ResponseSynthesizer (LLM, 45s超时, 回退模板) + TTS/图表
     → Step8.5: SafetyPipeline L4 输出过滤
     → Step9: 写回Profile + 生成任务 + 推送通知 (App/微信/企微)
```

### 6.5 Agent 体系 *(V5.0.1: 47+ Agent类)*

> 完整清单见 `agent_multimodal_host_config.md`

#### 核心专科 Agent (9个) — `core/agents/specialist_agents.py`

| # | 类名 | 领域 | 优先级 | 关键词示例 |
|---|------|------|--------|-----------|
| 1 | CrisisAgent | crisis | 0 | 自杀,自残,不想活 |
| 2 | GlucoseAgent | glucose | 1 | 血糖,糖尿病 |
| 3 | SleepAgent | sleep | 2 | 睡眠,失眠 |
| 4 | StressAgent | stress | 2 | 压力,焦虑 |
| 5 | MentalHealthAgent | mental | 2 | 情绪,抑郁 |
| 6 | NutritionAgent | nutrition | 3 | 饮食,营养 |
| 7 | ExerciseAgent | exercise | 3 | 运动,健身 |
| 8 | MotivationAgent | motivation | 3 | 动力,坚持 |
| 9 | TCMWellnessAgent | tcm | 4 | 中医,穴位 |

#### 整合/旅程/信任 Agent (8个)

| # | 类名 | 来源文件 | 领域 |
|---|------|---------|------|
| 10 | BehaviorRxAgent | integrative_agents.py | behavior_rx |
| 11 | WeightAgent | integrative_agents.py | weight |
| 12 | CardiacRehabAgent | integrative_agents.py | cardiac_rehab |
| 13 | JourneyCompanionAgent | v4_agents.py | coaching |
| 14 | GrowthReflectionAgent | v4_agents.py | coaching |
| 15 | CoachCopilotAgent | v4_agents.py | coaching |
| 16 | LifeDesignerAgent | v4_agents.py | coaching |
| 17 | TrustGuideAgent | trust_guide_agent.py | Observer专用 |

#### BehaviorRx 专家 (4个) — `behavior_rx/agents/`

| # | 类名 | 专长 |
|---|------|------|
| 19 | BehaviorCoachAgent | S0-S2阶段行为教练 |
| 20 | MetabolicExpertAgent | 血糖/CGM趋势 |
| 21 | CardiacExpertAgent | 运动恐惧脱敏 |
| 22 | AdherenceExpertAgent | 用药/复诊依从性 |

#### 用户层助手 (11个) — `assistant_agents/agents/`

| # | Agent | 领域 |
|---|-------|------|
| 28-36 | NutritionGuide / ExerciseGuide / SleepGuide / EmotionSupport / TcmWellness / MotivationSupport / HabitTracker / CommunityGuide / ContentRecommender | 各领域 |
| 37 | OnboardingGuide | 新用户引导 |
| 38 | CrisisResponder | 危机响应 |

#### 教练层专业 (6个) + 中医骨科 (5个) + V14 (3个)

| 范围 | 数量 | 关键Agent |
|------|------|----------|
| 教练层 | 6 | AssessmentEngine, RxComposer, BehaviorCoach, DomainExpert, Supervisor, QualityAuditor |
| 中医骨科用户层 | 2 | PainReliefGuide (#29), RehabExerciseGuide (#30) |
| 中医骨科教练层 | 3 | TCMOrthoExpert (#31), PainManagementExpert (#32), OrthoRehabPlanner (#33) |
| V14增强 | 3 | SafetyAgent, ResistanceAgent, ExplainAgent |
| 通用 | 1 | GenericLLMAgent (DB模板动态实例化) |

**路由优先级**: 危机 > 风险等级 > 租户关键词覆盖 > 平台关键词 > 用户偏好 > 设备数据 > 领域关联

**冲突优先**: crisis > glucose > pain > nutrition; sleep > exercise; stress > exercise; mental > exercise

### 6.6 策略闸门 (RuntimePolicyGate)

| # | 条件 | 决策 |
|---|------|------|
| 1 | 不稳定态 + 强干预 | DELAY |
| 2 | S0-S1阶段 | ALLOW_SOFT_SUPPORT |
| 3 | dropout_risk + S3+ | ESCALATE_COACH |
| 4 | relapse_risk | ALLOW_SOFT_SUPPORT |
| 5 | crisis_multimodal | ESCALATE_CRISIS |
| 6 | 其余 | ALLOW |

### 6.7 行为处方六要素

target_behavior(目标行为) + frequency_dose(频次剂量) + time_place(时间地点) + trigger_cue(启动线索) + obstacle_plan(障碍预案) + support_resource(支持资源)

### 6.8 V5.0 飞轮实装 (R2-R8) *(V5.0.1 新增)*

| 模块 | 端点数 | 核心功能 | 关键技术点 |
|------|--------|---------|-----------|
| R2 scheduler_agent | 2 | 处方→每日任务生成 | 融入已有daily_task_generation, 不注册并行job |
| R3 grower_flywheel | 5 | 今日任务/打卡/streak/周报/coach-tip | 六级累进任务目录(42项, ROLE_TO_LEVEL过滤); 个性化反馈 |
| R4 role_upgrade | 2 | 评估完成→角色升级 | 用ROLE_LEVEL_STR字典判断等级, 非role_level列 |
| R5 observer_flywheel | 3 | 试用墙额度/评估进度/升级触发 | 每日3次对话+3次食物识别 |
| R6 coach_flywheel | 4 | 审核队列/批准/拒绝/统计 | Query(pattern=), 非regex= |
| R7 notification_agent | 2+3job | 通知查询/已读 + 早晨/晚间/断连推送 | wx_gateway推送 + coach_push_queue审批 + 07:15/10:15/20:15错开 |
| R8 user_context | 3 | 上下文CRUD + Agent记忆注入 | user_contexts表 UniqueConstraint |

### 6.9 P2 深耕阶段 (V5.1.4, R1-R7)

| 轮次 | 内容 | 关键文件/端点 |
|------|------|-------------|
| R1 | Checkin→TrustScore管道 | trust_score_service + asyncio.to_thread桥接 |
| R2 | Admin 86页mock审计 (-2675行) | 69文件改写, 全部接入真实API |
| R3 | 食物AI→daily_tasks自动签到 | food_recognition_api + FoodRecognition.vue banner |
| R4 | 设备数据→daily_tasks自动签到 | device_task_bridge.py, 4个POST端点 |
| R5 | H5 3页实装 (学分/同道者/晋级) | MyCredits/MyCompanions/PromotionProgress |
| R6 | Admin+Expert飞轮live (16端点) | admin_flywheel_api + expert_flywheel_api |
| R7 | 死代码清理 (-1224行) | 删除4个mock文件 |

**活跃飞轮文件**: `r3_grower_flywheel_api_live.py` (含TASK_CATALOG 42项+ROLE_TO_LEVEL), `r5_observer_flywheel_api_live.py`, `r6_coach_flywheel_api_live.py`, `admin_flywheel_api.py`, `expert_flywheel_api.py`

### 6.10 P3 自动化运维 (V5.1.5, R8-R10)

| Job | 调度时间 | 功能 | Redis锁 |
|-----|---------|------|---------|
| `prescription_task_generation` | 06:15 | 处方→每日任务自动生成 | ✅ |
| `trust_engagement_monitor` | 22:00 | 信任<0.3 + 3天不活跃 + 有效Rx → 用户通知+教练预警 | ✅ |
| `coach_auto_escalation` | 08:00 | 7天+不活跃有Rx → coach_push_queue (7天去重) | ✅ |

**R9 断连模板**: long(≥14天) / medium(≥7天) / short(其他), 差异化重连话术

### 6.11 P4 Mock清零 (V5.1.6, R11-R14)

| 轮次 | 页面 | 关键修复 |
|------|------|---------|
| R11 | ContentSharing/StudentList/AssessmentResult/MyReviews | intervention tab + write ops + flywheel |
| R12 | health.ts全量重写 (15+端点, 无patientId) | 4个客户端页面适配, quick-checkin端点 |
| R13 | coach/Review/ExpertHome/MySupervision/MyResearch | **新建** settings_api.py, promotion API |
| R14 | LiveList/MedicalAssistant/MyTrajectory | empty state, wired endpoints |

**修复模式**: asyncpg CAST语法, task_date/order_num列, TS注解, async关键字

**当前页面状态**: ~87 真实 · ~12 mock-fallback(空≠mock) · 0 全mock · 1 即将上线 · ~8 静态

### 6.12 P5 基础设施 (V5.1.7, Migration 046-048)

| Migration | 内容 | 关键表/列 |
|-----------|------|----------|
| 046 | WeChat ORM同步 | users表: wx_openid/wx_miniprogram_openid/union_id/preferred_channel/growth_points |
| 047 | analytics_daily聚合表 | analytics_daily (日活/留存/转化), 调度Job已存在 |
| 048 | feature_flags + A/B测试 | feature_flags/ab_test_events, 7个API端点, hash变体分配 |

**event_tracking_api**: batch ingestion CAST修复 (tracked: 0→tracked: 2)

### 6.13 Admin Portal 响应式适配 (V5.1.8)

**断点**: 640px(mobile) | 768px(tablet) | 1024px(laptop) | 1280px(desktop)

| Phase | 页面/组件 | 改造方式 |
|-------|----------|---------|
| 0 | useResponsive.ts + responsive.css + main.ts | 共享基础设施 |
| 1 | AdminLayout | sidebar→overlay(hamburger), responsive header |
| 2-3 | 10页 KPI+双栏 (58个a-col转换) | prop: xs/sm/md/lg |
| 4 | ExpertAuditWorkbench + CoachWorkbench | 3栏/2栏→stack |
| 5 | AdminCommandCenter | CSS grid媒体查询 |
| 6 | CoachHome (7个drawer) | modalWidth() helper |
| 7 | StudentMessages | 单面板切换 (showChat toggle) |
| 8 | MyStudents kanban | flex-direction: column |
| 9 | CoachCopilot | panel→全屏overlay |
| 10 | ContentSharing + CoachStudentList | steps方向/卡片布局 |

**进度追踪文件**: `E:\注册表更新文件\P2-responsive-progress.md`

### 6.14 P6A 全平台搜索 (V5.1.9)

**端点**: `GET /api/v1/search?q=关键词&modules=users,prescriptions,tasks,checkins,content&limit=5`

**权限隔离** (基于 ROLE_LEVEL):

| 角色 | 解析规则 | users | prescriptions/tasks/checkins | content |
|------|---------|-------|------------------------------|---------|
| admin | level >= 99 | 全量 | 全量 | 全量(published) |
| coach | level >= 4 | 仅 coach_student_bindings 绑定学员 | 仅绑定学员 | 全量(published) |
| client | 其他 | 仅自己 | 仅自己 | 全量(published) |

**文件**: `api/search_service.py` (5个搜索函数) + `api/search_api.py` (路由)
**注意**: AsyncSession 不支持并发, 5个模块顺序执行 (非 asyncio.gather)

### 6.15 P6B 自动化周报 (V5.1.9)

**表**: `user_weekly_reports` (Migration 049, UNIQUE user_id+week_start)

**数据维度**: tasks_total/completed, completion_pct, checkin_count, learning_minutes, points_earned, activity_count, streak_days, highlights(JSONB), suggestions(JSONB)

**API** (4端点):
- `GET /api/v1/weekly-reports` — 当前用户周报列表
- `GET /api/v1/weekly-reports/latest` — 最新一期
- `GET /api/v1/weekly-reports/{week_start}` — 指定周
- `POST /api/v1/admin/weekly-reports/generate` — admin手动触发

**调度**: `user_weekly_report` Job, 每周日 21:00, Redis锁 ttl=900

**文件**: `api/weekly_report_service.py` + `api/weekly_report_api.py`

### 6.16 全Mock清零 (V5.1.9)

3页全mock → 0页:

| 页面 | 原状态 | 修复方式 |
|------|--------|---------|
| CoachStudentList | ❌全mock | 前端已调用 `GET /v1/coach/dashboard`, 无需改动 |
| StudentAssessment | ❌全mock | 前端已调用 `GET /v1/coach/students/{id}/assessment-detail`, 无需改动 |
| QuestionBank | ❌全mock | 修复6项: response shape(data→items) · 字段名(type→question_type) · 难度(int→string) · 筛选(level→domain) · +use_count · +POST /bulk |

**backend**: `question_api.py` (+use_count/correct_rate, +keyword搜索, +POST /bulk批量导入)
**frontend**: `stores/question.ts` (response解析), `views/exam/QuestionBank.vue` (字段/筛选/难度/响应式KPI)

### 6.17 H5 行为周报页 (V5.1.9)

**新增文件**: `h5/src/views/WeeklyReport.vue`
**路由**: `/weekly-report` (registered in router/index.ts)
**入口**: MyLearning.vue → "查看行为周报" 链接

**功能**: 4指标卡(完成率/学习分钟/积分/完成天数) + 签到活动详情 + 高频行为标签 + 本周建议 + 历史周报切换

**API调用**: `GET /v1/weekly-reports/latest` + `GET /v1/weekly-reports` + `GET /v1/weekly-reports/{week_start}`

### 6.18 头像/退出/WeChat同步 (V5.2.2)

**新建组件**:
- `admin-portal/src/composables/useCurrentUser.ts` — handleLogout + loadWeChatInfo
- `admin-portal/src/components/health/UserAvatarPopover.vue` — 头像气泡(用户名/角色/微信/退出), props: size/theme

**集成**: AdminLayout + HomeViewOptimized + SharerWorkbench + CoachWorkbench + ExpertWorkbench — 统一使用 UserAvatarPopover

### 6.19 统一个人中心 (V5.2.2)

**3个共享组件** (admin-portal/src/components/health/):
- `PersonalHealthProfile.vue` (~580行) — 健康档案(头像/基本信息/诊断/用药/过敏/紧急联系人), props: `embedded`
- `MyContributions.vue` (~420行) — 等级进度+投稿记录+同道者
- `MyBenefits.vue` (~350行) — 权益网格+积分指南+晋级条件

**统一入口**: `MyProfile.vue` → 3折叠面板(个人健康档案[展开]+我的分享[L3+]+我的权益[L3+])

**各工作台集成**:
- SharerWorkbench: 3 tab(我的分享/我的权益/个人档案)
- CoachWorkbench: 4 tab(审核工作台/个人档案/我的分享/我的权益)
- ExpertWorkbench: 6 tab(待审队列/决策回溯/规则引擎/个人档案/我的分享/我的权益)

### 6.20 六级累进任务目录 (V5.2.2)

**文件**: `api/r3_grower_flywheel_api_live.py`

**ROLE_TO_LEVEL 映射**: OBSERVER→0, GROWER→1, SHARER→2, COACH→3, PROMOTER/SUPERVISOR→4, MASTER→5, ADMIN→99

**TASK_CATALOG**: 42项(原21项+新增21项), 每项含 `min_level` 字段

| 角色 | 任务数 | 新增分类 |
|------|--------|----------|
| L0 观察员 | 5 | 监测(3)+情绪(1)+学习(1) |
| L1 成长者 | 21 | +运动(7)+营养(4)+睡眠(2)+用药(1) |
| L2 分享者 | 29 | +分享(4)+同道者(4) |
| L3 教练 | 35 | +教练管理(6) |
| L4 促进师 | 39 | +培训督导(4) |
| L5 大师 | 42 | +平台治理(3) |

**端点**: `GET /api/v1/daily-tasks/catalog` — 按用户角色等级过滤返回

**前端零修改**: `catalogGroups` 按 `tag` 自动分组，新分类自动展示

### 6.21 教练端三合一增强 (V5.2.3)

**Phase 1 种子业务数据**: `scripts/seed_test_business_data.py` (幂等, --dry-run)
- 6角色数据: observer(gp=15) grower(gp=120,S2) sharer(gp=500,S3) coach(gp=800,S4) promoter(gp=1500,S5) master(gp=3000,S6)
- 教练绑定: coach→grower + coach→sharer | 同道者: sharer→grower + sharer→observer
- 推送队列: 8条(3pending/2approved/2sent/1rejected) | 教练消息: 7条
- 运行: `docker exec bhp-api python scripts/seed_test_business_data.py`

**Phase 2 教练双重身份**: `components/health/CoachSelfHealthSummary.vue`
- 4指标网格(血糖/睡眠/步数/体重) + 今日任务进度条
- 嵌入CoachHome.vue: KPI卡和待跟进学员之间
- API: `/v1/device/health-data/summary` + `/v1/grower/daily-tasks/today`

**Phase 3 教练端响应式**: 13页新增 `@media (max-width: 640px)` 断点
- CoachHome: 操作按钮换行+工具网格2列+安全区
- CoachAiReview: 按钮全宽44px+文本域16px
- CoachWorkbench: 队列50vh+操作48px+统计2列
- 10页批量: StudentAssessment/StudentBehavioralProfile/StudentHealthData/MyCertification/MyPerformance/MyTools/CoachAnalytics/CoachCopilot/StudentMessages/StudentList

### 6.22-6.25 (与V5.0版保持一致)

> 改变动因6×24 · 四阶段养成 · 证据分层T1-T4 · 推送审批网关 · 六种隐式数据源+MULTIMODAL ·
> 四维用户状态(S+L+G+Lv) · 健康能力Lv0-Lv5 · 成长等级G0-G5 ·
> 多模态10模态权限矩阵 · 安全红线S1-S6 · 微信三通道

---

## 七、LLM & Host 配置

> 详见 `agent_multimodal_host_config.md`

### 7.1 云端 LLM (主路径)

| 项 | 环境变量 | 默认值 |
|----|---------|--------|
| 提供商 | `CLOUD_LLM_PROVIDER` | deepseek/qwen/openai |
| API Key | `CLOUD_LLM_API_KEY` | (必填) |
| Base URL | `CLOUD_LLM_BASE_URL` | `https://api.deepseek.com/v1` |
| 模型 | `CLOUD_LLM_MODEL` | `deepseek-chat` |
| 路由策略 | `LLM_ROUTE_STRATEGY` | `cloud_first` |

### 7.2 本地 Ollama (回退)

| 项 | 环境变量 | 默认值 |
|----|---------|--------|
| API | `OLLAMA_API_URL` | `http://host.docker.internal:11434` |
| 对话模型 | `OLLAMA_MODEL` | `qwen2.5:0.5b` |
| 视觉模型 | `OLLAMA_VL_MODEL` | `qwen2.5vl:7b` |
| 嵌入 | `OLLAMA_EMBED_MODEL` | `nomic-embed-text:latest` |

### 7.3 安全管道 (4层)

| 层 | 文件 | 动作 |
|----|------|------|
| L1 输入过滤 | input_filter.py | crisis(15词)→CrisisAgent; blocked(7词)→硬阻断 |
| L2 RAG安全 | rag_safety.py | 过滤过期文档, T1-T4重排序 |
| L3 生成守卫 | generation_guard.py | 危机注入热线; medical_advice禁药名剂量 |
| L4 输出过滤 | output_filter.py | 诊断语句→替换; 绝对声明→前缀 |

---

## 八、常用命令

```bash
docker compose -f docker-compose.yaml -f docker-compose.app.yaml up -d
docker compose -f docker-compose.app.yaml up -d --build bhp-api
docker logs -f bhp-api --tail 100
docker exec -it bhp-api bash
curl http://localhost:8000/health
cd api && alembic upgrade head
cd admin-portal && npm run dev
cd h5 && npm run dev
cd miniprogram && npm run dev:weapp
```

---

## 九、禁止操作 ⛔

1. 不要删除或修改 `migrations/` 中已有的迁移文件
2. 不要修改 `api/dependencies.py` 中的认证逻辑
3. 不要硬编码 JWT 密钥、数据库密码
4. 不要修改 `ROLE_LEVEL` 映射 (core/models.py)
5. 不要出现 `/api/api/v1/` 双前缀
6. 不要直接操作 dify-db
7. 不要删除 `@with_redis_lock` 装饰器
8. 不要在 StageRuntime 之外写 `current_stage`
9. 不要修改 policy_gate.py 规则链
10. 不要修改 spi_mapping.json 阈值
11. 不要在 MultimodalChat.vue 之外实现 AI 对话 UI
12. 不要在微信渠道展示处方/诊断/用药 (合规红线)
13. 不要存储原始音频/视频/含PII图片
14. 不要在日志中明文输出 OpenID/UnionID/session_key
15. 不要绕过 safety_gate.py 安全检查
16. *(V5.0.1新增)* 不要"猜测"import路径 — 参照 §十六 代码契约

---

## 十、已知问题与注意事项

- `/v1/tenants/hub` 返回空列表 → 无种子专家数据, 正常
- bhp-wx-gateway 端口 8080 与 dify-nginx 冲突 → 需调整
- 微信服务号认证需 7-14 天 → 提前启动
- 小程序审核定位"健康管理"非"诊断"
- Chat 503: 需配置 `CLOUD_LLM_API_KEY` 使 AI 对话功能可用
- 3 全 mock 页面待开发: CoachStudentList(学员总览), StudentAssessment(评估管理), QuestionBank(题库管理)
- ~~StageEngine(db) 构造函数错误~~ → ✅ V5.0.2 已修复
- ~~program_templates 等表未持久化~~ → ✅ V5.0.2 Alembic 045 已持久化
- ~~`/v1/health/p001/*` 返回 404~~ → ✅ V5.1.6 health.ts 全量重写, 15+ 端点实装
- ~~event_tracking_api `::json` cast 失败~~ → ✅ V5.1.7 改为 `CAST(:detail AS json)`
- ~~feature_flag_api `::jsonb` cast 失败~~ → ✅ V5.1.7 改为 `CAST(... AS jsonb)` (4处)
- ~~Admin 86页 mock 数据~~ → ✅ V5.1.4 P2-R2 全部接入真实API (-2675行)
- ~~CI M16_Reflection 500~~ → ✅ V5.2.1 register_external_models() + reflection_api.py加固
- ~~pre_launch_verify 12 FAIL~~ → ✅ V5.2.1 Docker环境自动检测 + SQLAlchemy直连DB + Redis AUTH
- ~~db_backup.sh 旧凭据~~ → ✅ V5.2.1 bhp_user→postgres, bhp_db→health_platform
- ~~P1 edited_rx_json 单引号~~ → ✅ V5.2.7 str()→json.dumps(ensure_ascii=False)
- ~~P1 审批后处方未持久化~~ → ✅ V5.2.7 generate_daily_tasks_for_user 移至 commit 后 (non-blocking)

---

## 十一、核心术语速查

| 术语 | 含义 |
|------|------|
| `current_stage` (S0-S6) | 行为改变阶段, 仅 StageRuntimeBuilder 可写 |
| `spi_score` | 成功可能性指数 (0-100) |
| `readiness_level` (L1-L5) | 心理准备度 |
| `health_competency` (Lv0-Lv5) | 健康管理能力 |
| `growth_level` (G0-G5) | 社区角色等级 |
| `cultivation_stage` | startup/adaptation/stability/internalization |
| `bpt_type` | action/knowledge/emotion/relation/environment/mixed |
| `policy_gate_decision` | ALLOW/DELAY/ALLOW_SOFT_SUPPORT/ESCALATE_COACH/DENY |
| `MultimodalMessage` | 统一多模态消息体 (10种type) |
| `channel` | web/h5/wx_service/wx_miniprogram/wx_work/api |
| `ROLE_LEVEL` | 角色→等级映射字典 (core/models.py) |
| `AsyncSessionLocal` | 异步Session工厂 (core/database.py) |

---

## 十二、参考文档

| 文档 | 位置 | 内容 |
|------|------|------|
| 架构总览 | `platform-architecture-overview.md` | 完整路由/模型/服务/数据流 |
| 核心业务逻辑 | `behavioral-prescription-core-logic-supplemented.md` | 26章, 2367行 |
| **Agent Host 配置** *(V5.0.1)* | **`agent_multimodal_host_config.md`** | **47+ Agent · LLM配置 · 多模态 · 安全管道** |
| **契约注册表** *(V5.2.7)* | **`E:\注册表更新文件\行健平台-契约注册表-V5_2_7-CONSOLIDATED.md`** | **V5.2.7 唯一权威版 (含P1闭环+督导系统+租户生命周期+57条变更)** |
| 多模态消息协议 | `core/multimodal/protocol.py` | 10种模态定义 |

---

## 十三、测试阶段专用规则

### 13.1 数据保护
- 禁止批量删除 (`DROP TABLE`, `TRUNCATE`)
- 禁止修改已有迁移, 需变更必须新建
- 测试数据使用 Westworld 仿真注入端点

### 13.2 测试层级

| 层级 | 范围 | 修改后必须验证 |
|------|------|---------------|
| L0 | 容器启动/端口/健康检查 | Docker 配置变更后 |
| L1 | ORM 模型加载/枚举 | 修改 models.py 后 |
| L2 | 迁移/表结构 | 新增迁移后 |
| L3 | 服务单元测试 | 修改 *_service.py 后 |
| L4 | API 端点/认证 | 修改 *_api.py 后 |
| L5 | E2E 联调 | 发版前 |
| L6 | 多模态 | 修改 multimodal/ 后 |
| L7 | 微信集成 | 修改 wechat/ 后 |
| **L8** | **全平台功能验证 (96+5)** | **发版前必跑, CI 门禁自动执行** |

### 13.2.1 全平台测试套件 *(V5.0.2 新增)*

```bash
# 全量测试 (25模块 × 96测试 + 5跨模块链)
python scripts/test_platform_full.py

# 指定模块
python scripts/test_platform_full.py --module auth,chat,learning

# 仅链测试
python scripts/test_platform_full.py --chain-only

# 自定义 JSON 报告路径 (CI 用)
python scripts/test_platform_full.py --json reports/platform_test_report.json
```

**CI 门禁**: `.github/workflows/ci-security.yml` Stage 2.5 `platform-full-test` — 任一测试失败阻断部署。

### 13.2.2 预发布验证 *(V5.2.1 重构)*

```bash
# Docker容器内运行 (自动检测环境)
docker exec bhp-api python scripts/pre_launch_verify.py

# 11维度: API健康/认证/角色/页面/Redis+Ollama/安全/DB/调度/前端/备份/种子账号
# 结果: 56 PASS / 0 FAIL / 2 SKIP / 10 WARN = PASS
```

### 13.2.3 多模态单元测试 *(V5.2.1 新增)*

```bash
python -m pytest tests/test_multimodal_services.py -v
# 28 tests: ASR(7) + VLM(8) + 食物解析(8) + AudioAPI(4) + 食物端点(1)
```

### 13.2.4 CI外部模型注册 *(V5.2.1 新增)*

CI `create_all()` 前必须调用 `register_external_models()` 以确保所有ORM模型的表被创建:

```python
from core.models import Base, register_external_models
register_external_models()  # 注册 reflection_journals, script_templates 等
Base.metadata.create_all(engine)
```

### 13.3 API 契约锁定
- 不变更现有端点URL/方法/请求体
- 不删除返回字段 (可新增)
- 新增端点须在 main.py 注册
- R2-R8 飞轮路由必须注册在 **bridge 之前** (L1676), 否则被 catch-all 拦截

---

## 十四、v3.0→V5.0 架构变更

| 变更项 | V5.0状态 | 优先级 |
|--------|----------|--------|
| Agent 体系 | 47+ Agent类 (9专科+3整合+4旅程+4BRx+11助手+6教练+5中医+3V14+1通用+1信任) | P0 |
| 多模态 | 10模态统一协议+S1-S6安全红线 | P0 |
| 微信生态 | 服务号+小程序+企微 | P1-P3 |
| **飞轮实装** *(V5.0.1)* | **R2-R8 全部14端点+3定时任务上线运行** | **✅完成** |
| **代码契约** *(V5.0.1)* | **§十六 精确import/认证/角色/Session规范** | **✅完成** |
| **DB持久化** *(V5.0.2)* | **Alembic 045: 5表+4视图+种子数据, 全部IF NOT EXISTS幂等** | **✅完成** |
| **CI全平台门禁** *(V5.0.2)* | **96模块+5链测试纳入ci-security.yml Stage 2.5** | **✅完成** |
| **P2深耕** *(V5.1.4)* | **R1-R7: mock审计/食物AI/设备桥接/飞轮live/死代码清理 (69文件, -3899行)** | **✅完成** |
| **P3自动化运维** *(V5.1.5)* | **R8-R10: 3新定时Job (06:15/08:00/22:00), Redis锁互斥** | **✅完成** |
| **P4 Mock清零** *(V5.1.6)* | **R11-R14: 22页修复, health.ts重写, settings_api, 6页重分类** | **✅完成** |
| **P5基础设施** *(V5.1.7)* | **Migration 046-048: WeChat ORM/analytics_daily/feature_flags, asyncpg CAST修复** | **✅完成** |
| **Admin响应式** *(V5.1.8)* | **19页媒体查询 + useResponsive组合式 + responsive.css全局样式** | **✅完成** |
| **P6A搜索** *(V5.1.9)* | **search_service(5模块) + search_api(三端隔离) + 顺序AsyncSession** | **✅完成** |
| **P6B周报** *(V5.1.9)* | **Migration 049 + weekly_report_service(8维度) + 4端点 + scheduler(Sun 21:00)** | **✅完成** |
| **全mock清零** *(V5.1.9)* | **QuestionBank(6项mismatch+bulk) + CoachStudentList/StudentAssessment(确认已有API) → 0全mock** | **✅完成** |
| **H5周报页** *(V5.1.9)* | **WeeklyReport.vue + MyLearning入口 + 路由注册** | **✅完成** |
| **预发布审计** *(V5.2.1)* | **pre_launch_verify.py Docker重构(56P/0F) + Dockerfile(postgresql-client) + db_backup.sh凭据修复** | **✅完成** |
| **多模态单测** *(V5.2.1)* | **test_multimodal_services.py 28 tests (ASR/VLM/食物解析/AudioAPI)** | **✅完成** |
| **CI外部模型** *(V5.2.1)* | **register_external_models() + CI create_all 3处修复 + reflection_api加固** | **✅完成** |
| **头像/退出** *(V5.2.2)* | **useCurrentUser组合式 + UserAvatarPopover + 5工作台集成 + Login角色分流** | **✅完成** |
| **统一个人中心** *(V5.2.2)* | **3共享组件(PersonalHealthProfile/MyContributions/MyBenefits) + MyProfile折叠面板 + 3工作台集成** | **✅完成** |
| **六级任务目录** *(V5.2.2)* | **TASK_CATALOG 21→42项 + ROLE_TO_LEVEL + min_level过滤 (L0:5→L5:42累进)** | **✅完成** |
| **种子业务数据** *(V5.2.3)* | **seed_test_business_data.py: 6角色全量业务数据(385任务+教练绑定+推送队列+同道者)** | **✅完成** |
| **教练双重身份** *(V5.2.3)* | **CoachSelfHealthSummary.vue: 4指标+任务进度, 嵌入CoachHome** | **✅完成** |
| **教练端响应式** *(V5.2.3)* | **13页coach @640px移动端断点 (19→32页总Admin响应式)** | **✅完成** |
| **AI行为处方** *(V5.2.4)* | **copilot_prescription_service(839行) + LLM/规则引擎双路径 + 教练学员角色过滤** | **✅完成** |
| **干预包+Rx仪表盘** *(V5.2.5)* | **10包3端点 + Rx仪表盘数据联通 + 绑定权限修复 + 专家工作台iframe修复** | **✅完成** |
| **P1闭环** *(V5.2.6)* | **BehaviorRx集成(adapter+mapper+混合路由) + 通知推送 + H5处方详情(5卡片) + 5新3改** | **✅完成** |
| **督导+租户+P1验证** *(V5.2.7)* | **督导会议(6ep) + 租户生命周期(3ep) + P1 E2E 3修复(json/事务) + WebSocket推送 + 2通知端点 + 33测试** | **✅完成** |

---

## 十五、契约对齐索引

| CLAUDE.md 章节 | 契约 Sheet | 验证要点 |
|----------------|-----------|---------|
| §6.5 Agent体系 | Agent完整清单 | 47+ Agent类; 分层路由 |
| §6.8 飞轮实装 | 飞轮实装契约 | 14端点+3 job; R2-R8交叉引用 |
| §6.9-6.17 P2-P6 | 契约注册表v3 §二-§六+§十一 | R1-R14+046-049迁移+响应式+搜索+周报+全mock清零+H5周报 |
| §6.18-6.20 V5.2.2 | 契约注册表 §2.2 V5.2.2 | 头像/退出+统一个人中心(3共享组件)+六级任务目录(42项) |
| §6.21 V5.2.3 | 契约注册表 §2.2 V5.2.3 | 种子业务数据+教练双重身份+教练端13页响应式 |
| §6.17 多模态 | 多模态AI交互 | 10模态; 角色权限; S1-S6 |
| §6.19 微信 | 微信生态对接 | 3通道; C1-C8合规 |
| §十六 代码契约 | 代码契约 (新Sheet) | 5条import铁律; 认证签名; 角色判断; asyncpg CAST |
| §四 Docker | V5.0变更总览 | 容器端口无冲突 |

**对齐原则**: 代码实现以 CLAUDE.md 为准; CLAUDE.md 以契约注册表为准; 冲突时契约注册表优先。
**实时同步**: 所有重要变更必须同步更新 CLAUDE.md + 契约注册表, 保持版本一致。

---

## 十六、代码契约 — 后端编码精确规范 *(V5.0.1 新增)*

> 基于 `core/database.py` · `api/dependencies.py` · `core/models.py` · `main.py` · `core/redis_lock.py` 源码提取。
> **所有新增后端代码必须遵循本节**, 不得"猜测" import 路径。

### 16.1 Import 路径映射 (5条铁律)

| 需要什么 | 正确写法 | ❌ 错误写法 |
|----------|----------|-----------|
| 同步DB会话 | `from core.database import get_db` | ~~`from database import get_db`~~ |
| 异步DB会话 | `from core.database import get_async_db` | ~~`from database import get_async_db`~~ |
| Session工厂 | `from core.database import AsyncSessionLocal` | ~~`async_session_factory`~~ |
| 认证依赖 | `from api.dependencies import get_current_user, require_admin` | ~~`from dependencies import ...`~~ |
| ORM模型 | `from core.models import User, UserRole, ROLE_LEVEL` | ~~`from models import ...`~~ |
| Redis锁 | `from core.redis_lock import with_redis_lock` | ~~`from redis_lock import ...`~~ |
| 跨R文件 | `from api.r2_scheduler_agent import ...` | ~~`from r2_scheduler_agent import ...`~~ |

**规律**: `api/` 下文件互引用 `api.xxx`; 引用 `core/` 下的用 `core.xxx`。

### 16.2 认证守卫签名

```python
# 全部是同步函数 (用 SQLAlchemy Session, 非 AsyncSession)
def get_current_user(token, db: Session = Depends(get_db)) -> User
def require_admin(current_user: User = Depends(get_current_user)) -> User
def require_coach_or_admin(current_user: User = Depends(get_current_user)) -> User
```

异步端点需单独注入异步Session:
```python
async def endpoint(
    current_user: User = Depends(get_current_user),   # 同步认证
    async_db: AsyncSession = Depends(get_async_db),    # 异步操作
):
```

### 16.3 角色判断

```python
# ✅ 正确: 查映射字典
from core.models import ROLE_LEVEL, ROLE_LEVEL_STR
level = ROLE_LEVEL.get(user.role, 1)

# ✅ SQL中: 比较 role 字符串
WHERE u.role IN ('grower', 'sharer', 'coach')

# ❌ 错误: 此列不存在
WHERE u.role_level >= 2
```

### 16.4 User 模型关键字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer PK | 主键 |
| public_id | UUID | 对外暴露 |
| username | String(50) unique | 用户名 |
| role | SQLEnum(UserRole) | 角色枚举 |
| agency_mode | String(20) | passive/transitional/active |
| agency_score | Float | 0.0-1.0 |

**不在 User 表的常见字段**:
- `coach_id` → 不存在, 教练-学员关系见下方 bindings 表
- `growth_points` → `UserLearningStats.growth_points` (需JOIN)
- `wx_openid` → Migration 046 已同步到 ORM
- `role_level` → 不存在, 用 `ROLE_LEVEL[user.role]`

**教练-学员关系: `coach_schema.coach_student_bindings`** *(Migration 039)*

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | gen_random_uuid() |
| coach_id | Integer NOT NULL | FK → users.id (教练) |
| student_id | Integer NOT NULL | FK → users.id (学员) |
| binding_type | VARCHAR(20) | `assigned` (默认) |
| permissions | JSONB | {view_profile, send_message, create_rx, ...} |
| is_active | Boolean | 是否有效 |

> ⚠️ 表在 **coach_schema** (非 public), SQL 必须写 `coach_schema.coach_student_bindings`
> ⚠️ **无 ORM 模型**, 全部通过 `admin_bindings_api.py` 的 `sa_text()` raw SQL 操作
> ⚠️ 唯一约束: `(coach_id, student_id, binding_type)` — 同对同类型不重复

### 16.5 main.py 路由注册顺序

```
L376-585:   核心路由 (auth, assessment, chat, etc.)
L600-610:   V3 路由
L1610-1674: V4.0/4.1 路由
L1676-1724: ★ R2-R8 飞轮路由 (必须在 bridge 之前)
L1727:      V4.1 bridge (含 catch-all)
L1733+:     V4.2/4.3/V5.0 路由
```

### 16.6 定时任务模式

- R2: **不注册独立 job**, 在已有 `daily_task_generation` 末尾调用
- R7: 注册 3 个新 job — 07:15 / 10:15 / 20:15 (错开 program_push 整点)
- R8: 注册 1 个 cleanup job — 02:00
- Redis锁: `@with_redis_lock("name", ttl=300)` — 参数名 `ttl`

### 16.7 新代码速查模板

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_async_db
from api.dependencies import get_current_user, require_admin
from core.models import User, ROLE_LEVEL

router = APIRouter(prefix="/api/v1", tags=["my-module"])

@router.get("/my-endpoint")
async def my_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    user_id = current_user.id
    role_level = ROLE_LEVEL.get(current_user.role, 1)
    result = await db.execute(text("SELECT ..."), {"uid": user_id})
    rows = result.mappings().all()
    return {"data": rows}
```

### 16.8 asyncpg CAST 语法 *(V5.1.7 新增)*

> asyncpg 将 `::type` 中的 `:` 解释为命名参数前缀，导致 SQL 执行失败。
> **所有 SQLAlchemy `text()` 中的类型转换必须使用 `CAST()` 函数。**

```python
# ✅ 正确: 使用 CAST() 函数
await db.execute(text("INSERT INTO t (data) VALUES (CAST(:v AS json))"), {"v": json_str})
await db.execute(text("UPDATE t SET config = CAST(:v AS jsonb)"), {"v": json_str})

# ❌ 错误: asyncpg 解析失败
await db.execute(text("INSERT INTO t (data) VALUES (:v::json)"), {"v": json_str})
```

**已修复文件**: `event_tracking_api.py` (1处), `feature_flag_api.py` (4处)

### 16.9 R2-R8 线上版实际 import (参考)

```python
# R2: from core.database import get_async_db; from api.dependencies import require_admin
# R3: from api.r2_scheduler_agent import generate_daily_tasks_for_user
#     from api.r7_notification_agent import check_and_send_milestone
#     from api.r8_user_context import load_user_context
# R4: from core.models import ROLE_LEVEL_STR
# R7: from core.database import AsyncSessionLocal; from core.redis_lock import with_redis_lock
```

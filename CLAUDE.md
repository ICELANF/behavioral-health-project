# BHP 行为健康数字平台 — Claude Code 项目指令 (V5.0.1)

> 本文件由 Claude Code 自动加载，指导 AI 如何在本项目中工作。
> **V5.0.1 变更**: 2026-02-18 代码契约精确化 + Agent清单47→实数 + R2-R8飞轮实装经验回写
>
> 上游契约: `contracts/行健平台-契约注册表-V5_0_1.xlsx`
> Agent配置清单: `agent_multimodal_host_config.md` (47+ Agent类 · 15预设模板 · 4层安全 · 6模态)

---

## 一、项目概述

BHP（Behavioral Health Platform）是一个行为健康数字化管理平台，服务于慢病逆转与行为改变领域。平台包含 Observer(观察者)、Grower(成长者)、Coach(教练)、Expert(专家)、Admin(管理员) 五种用户角色，集成了评估引擎、AI Agent 系统、RAG 知识库、多模态交互引擎、智能监测方案及微信生态对接能力。

**规模**: 49+ 路由模块 · 600+ API 端点 · 130+ 数据模型 · 21+ 迁移版本 · **47+ AI Agent 类** · 16+ Docker 容器 · **10 种交互模态** · **3 条微信通道** · **R2-R8 飞轮实装 (3,192行)**

> ⚠️ **V5.0.1 变更**:
> - Agent 从 33→47+ (源码实际类数, 含 specialist/integrative/v4/behaviorRx/tcm/assistant/professional/v14)
> - 新增 §十六 代码契约 (import路径/认证签名/角色判断/Session模式 精确规范)
> - R2-R8 飞轮已从 mock→真实DB+认证+个性化反馈+微信推送, 全部14端点线上验证通过
> - 修正: 角色枚举值 bhp_coach→coach, bhp_promoter→promoter, bhp_master→master
> - 修正: 项目结构 models.py/database.py 实际在 core/ 下

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
│   ├── models.py                   # 130+ SQLAlchemy 模型 + UserRole枚举 + ROLE_LEVEL映射
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
│   └── schemas/
├── api/                            # ★ 路由模块包
│   ├── dependencies.py             # 认证守卫: get_current_user / require_admin / require_coach_or_admin
│   ├── config.py                   # DIFY/OLLAMA 配置
│   ├── *_api.py                    # 49+ 路由模块
│   ├── *_service.py                # 61+ 核心服务
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
├── admin-portal/                   # Vue 3 管理后台 (:5174) — Coach + Admin
├── h5/                             # Vue 3 移动端 (:5173) — Observer + Grower
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
| R3 grower_flywheel | 5 | 今日任务/打卡/streak/周报/coach-tip | 个性化反馈: 里程碑→全完成→上下文→标签→通用 |
| R4 role_upgrade | 2 | 评估完成→角色升级 | 用ROLE_LEVEL_STR字典判断等级, 非role_level列 |
| R5 observer_flywheel | 3 | 试用墙额度/评估进度/升级触发 | 每日3次对话+3次食物识别 |
| R6 coach_flywheel | 4 | 审核队列/批准/拒绝/统计 | Query(pattern=), 非regex= |
| R7 notification_agent | 2+3job | 通知查询/已读 + 早晨/晚间/断连推送 | wx_gateway推送 + coach_push_queue审批 + 07:15/10:15/20:15错开 |
| R8 user_context | 3 | 上下文CRUD + Agent记忆注入 | user_contexts表 UniqueConstraint |

### 6.9-6.19 (与V5.0版保持一致)

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

- `/v1/health/p001/*` 返回 404 → `health.ts` 有 mock fallback
- `/v1/tenants/hub` 返回空列表 → 无种子专家数据, 正常
- bhp-wx-gateway 端口 8080 与 dify-nginx 冲突 → 需调整
- 微信服务号认证需 7-14 天 → 提前启动
- 小程序审核定位"健康管理"非"诊断"

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
| **契约注册表** *(V5.0.1)* | **`contracts/行健平台-契约注册表-V5_0_1.xlsx`** | **8 Sheet (新增代码契约+Agent完整清单)** |
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

---

## 十五、契约对齐索引

| CLAUDE.md 章节 | 契约 Sheet | 验证要点 |
|----------------|-----------|---------|
| §6.5 Agent体系 | Agent完整清单 | 47+ Agent类; 分层路由 |
| §6.8 飞轮实装 | 飞轮实装契约 | 14端点+3 job; R2-R8交叉引用 |
| §6.17 多模态 | 多模态AI交互 | 10模态; 角色权限; S1-S6 |
| §6.19 微信 | 微信生态对接 | 3通道; C1-C8合规 |
| §十六 代码契约 | 代码契约 (新Sheet) | 5条import铁律; 认证签名; 角色判断 |
| §四 Docker | V5.0变更总览 | 容器端口无冲突 |

**对齐原则**: 代码实现以 CLAUDE.md 为准; CLAUDE.md 以契约注册表为准; 冲突时契约注册表优先。

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
- `growth_points` → `UserLearningStats.growth_points` (需JOIN)
- `wx_openid` → 尚不存在 (V5.0 迁移未执行)
- `role_level` → 不存在, 用 `ROLE_LEVEL[user.role]`

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

### 16.8 R2-R8 线上版实际 import (参考)

```python
# R2: from core.database import get_async_db; from api.dependencies import require_admin
# R3: from api.r2_scheduler_agent import generate_daily_tasks_for_user
#     from api.r7_notification_agent import check_and_send_milestone
#     from api.r8_user_context import load_user_context
# R4: from core.models import ROLE_LEVEL_STR
# R7: from core.database import AsyncSessionLocal; from core.redis_lock import with_redis_lock
```

# 行为健康数字平台 — 系统全景参考手册

> 本文档供智能体开发与规划使用，覆盖所有版块、功能、模块、逻辑、数据流与模块间关系。

---

## 目录

- [一、系统全景架构](#一系统全景架构)
- [二、核心数据结构 (6 大协议对象)](#二核心数据结构)
- [三、核心引擎层 core/](#三核心引擎层)
- [四、智能体层 agents/](#四智能体层)
- [五、API 服务层 api/](#五api-服务层)
- [六、知识库与触发器系统](#六知识库与触发器系统)
- [七、BAPS 评估体系](#七baps-评估体系)
- [八、行为处方库 rx_library](#八行为处方库)
- [九、Dify 工作流集成](#九dify-工作流集成)
- [十、数据库 ORM 模型](#十数据库-orm-模型)
- [十一、前端 H5 患者端](#十一前端-h5-患者端)
- [十二、部署与基础设施](#十二部署与基础设施)
- [十三、端到端数据流全图](#十三端到端数据流全图)
- [十四、模块间调用关系矩阵](#十四模块间调用关系矩阵)
- [十五、当前状态与下一步规划锚点](#十五当前状态与下一步规划锚点)

---

## 一、系统全景架构

### 1.1 核心理念："主动健康 · 吃动守恒"

```
吃(饮食能量摄入) ≈ 动(运动能量消耗) = 守恒(体重稳定·代谢健康)
```

**四大健康支柱：**

| 支柱 | 关键指标 | 数据来源 | 对应 Agent |
|------|---------|---------|-----------|
| 科学饮食 | 每日热量、碳水比、蛋白质、膳食纤维 | 饮食日志、食物图像识别 | A3 饮食顾问 |
| 合理运动 | 周运动频次、单次时长、卡路里消耗、心率 | 活动追踪器、手环 | A2 运动指导师 |
| 血糖管理 | 空腹血糖、餐后血糖、血糖变异性、HbA1c | CGM、手动记录 | 血糖Agent |
| 行为改变 | 行为阶段、任务完成率、连续签到、健康评分 | 系统日志、问卷 | A1 主动健康教练 |

### 1.2 系统分层架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户界面层                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │ H5患者端  │  │ 教练工作台 │  │ 督导专家台 │               │
│  │ Vue3+Vant │  │ Vue3+Ant │  │ (规划中)  │               │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘               │
├───────┼──────────────┼─────────────┼────────────────────┤
│       │         业务服务层          │                      │
│  ┌────┴──────────────┴─────────────┴─────┐               │
│  │            FastAPI 50+ 端点            │               │
│  │  认证 │ 评估 │ 设备数据 │ 对话 │ 任务    │               │
│  │  auth │ assessment │ device │ chat │ task │             │
│  └────┬──────────────┬─────────────┬─────┘               │
├───────┼──────────────┼─────────────┼────────────────────┤
│       │         AI 智能层           │                      │
│  ┌────┴────┐  ┌──────┴──────┐  ┌──┴──────┐              │
│  │  Dify   │  │ Multi-Agent │  │ Ollama  │              │
│  │ 工作流   │  │  Octopus    │  │ 本地LLM │              │
│  │ 编排平台  │  │  协调引擎    │  │qwen2.5  │              │
│  └────┬────┘  └──────┬──────┘  └──┬──────┘              │
├───────┼──────────────┼─────────────┼────────────────────┤
│       │         数据存储层          │                      │
│  ┌────┴────┐  ┌──────┴──────┐  ┌──┴──────┐              │
│  │PostgreSQL│  │   Redis     │  │Weaviate │              │
│  │ 结构数据  │  │ 缓存/会话    │  │ 向量库   │              │
│  └─────────┘  └─────────────┘  └─────────┘              │
└─────────────────────────────────────────────────────────┘
```

### 1.3 TTM 行为改变模型集成

| 阶段 | 中文名 | 持续时间 | 核心策略 | Agent 干预方式 |
|------|-------|---------|---------|---------------|
| Precontemplation | 前意向期 | 不定 | 提升健康意识、风险教育 | 教育性内容、无压力接触 |
| Contemplation | 意向期 | ~6月 | 利弊分析、建立信心 | 探索矛盾、动机访谈 |
| Preparation | 准备期 | ~1月 | 设定目标、制定计划 | 目标分解、资源准备 |
| Action | 行动期 | ~6月 | 持续支持、监控进展 | 进度追踪、障碍处理 |
| Maintenance | 维持期 | 6月+ | 预防复发、巩固成就 | 复发预防、身份认同 |

### 1.4 五级心理准备度模型（本系统独有扩展）

| 等级 | 中文名 | SPI系数 | 表现 | 干预策略 |
|------|-------|---------|-----|---------|
| 1 | 完全对抗 | 0.3 | 否认、防御、视改变为威胁 | 建立安全感，不施压 |
| 2 | 抗拒与反思 | 0.5 | 不想改但看到必要性 | 处理矛盾，利弊分析 |
| 3 | 妥协与接受 | 0.7 | 接受需要改变，想要控制感 | 降低门槛，微习惯 |
| 4 | 顺应与调整 | 0.9 | 视改变为合理，愿意调整 | 强化习惯，渐进提升 |
| 5 | 全面臣服 | 1.0 | 改变已成为身份认同 | 巩固身份，挑战进阶 |

---

## 二、核心数据结构

`core/master_agent.py` 定义了系统的 6 大协议对象，是所有模块间通信的基础。

### 2.1 六大核心结构体

```
┌─────────────────┐     ┌─────────────────┐
│ CoreUserInput    │────→│CoreUserMaster   │
│ 系统入口数据      │     │Profile 用户主画像 │
│                  │     │ (系统权威数据源)   │
│ input_id         │     │                  │
│ user_id          │     │ demographics     │
│ input_type       │     │ medical_profile  │
│ raw_content      │     │ device_profile   │
│ source           │     │ behavior_profile │
│ intent_hint      │     │ risk_profile     │
└─────────────────┘     │ intervention_state│
                         └────────┬─────────┘
                                  │
                    ┌─────────────┴──────────────┐
                    ↓                            ↓
         ┌─────────────────┐          ┌─────────────────┐
         │ CoreAgentTask   │          │ CoreAgentResult  │
         │ 编排器→Agent协议 │←────────→│ Agent→编排器协议  │
         │                  │          │                  │
         │ task_id          │          │ task_id          │
         │ target_agent     │          │ agent_id         │
         │ task_type        │          │ key_findings     │
         │ focus_domain     │          │ behavior_patterns│
         │ context_snapshot │          │ risk_assessment  │
         │ specific_questions│         │ recommendations  │
         │ priority         │          │ data_updates ←──── 回写通道
         └─────────────────┘          └─────────────────┘
                    │                            │
                    └─────────────┬──────────────┘
                                  ↓
                    ┌─────────────────────────┐
                    │ CoreInterventionPlan    │
                    │ 行动桥梁                  │
                    │                          │
                    │ plan_id                  │
                    │ target_goals             │
                    │ current_stage (培育阶段)   │
                    │ strategy_type            │
                    │ intervention_modules     │
                    │ adjustment_rules ←──── 回写通道 │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ CoreDailyTask           │
                    │ 执行与行为改变出口         │
                    │                          │
                    │ task_id                  │
                    │ task_type (微习惯/反思等)  │
                    │ description              │
                    │ completion_status        │
                    │ user_feedback ←──── 回写通道│
                    │ adherence_score          │
                    └─────────────────────────┘
```

### 2.2 回写权限控制

**只有 MasterOrchestrator 可写入 UserMasterProfile**，通过三个受控通道：

| 通道 | 来源 | 写入内容 |
|------|------|---------|
| `AgentResult.data_updates` | Agent 分析结果 | 行为模式标签、风险评估更新 |
| `InterventionPlan.adjustment_rules` | 干预计划调整 | 阶段变更、策略调整 |
| `CoreDailyTask.user_feedback` | 用户任务反馈 | 依从性评分、完成状态 |

### 2.3 核心枚举类型

```python
# Agent 类型
CoreAgentType: METABOLIC, SLEEP, EMOTION, MOTIVATION, COACHING,
               NUTRITION, EXERCISE, TCM, CRISIS

# 任务类型
CoreTaskType: ANALYSIS, ASSESSMENT_REQUEST, PLANNING_SUPPORT, INTERPRETATION

# 日常任务类型
CoreDailyTaskType: MICRO_HABIT, REFLECTION, TRAINING, MEASUREMENT

# 干预策略类型
CoreStrategyType: COGNITIVE, BEHAVIORAL, EMOTIONAL_SUPPORT, COMBINED

# 行为阶段 (TTM)
CoreBehaviorStage: PRECONTEMPLATION, CONTEMPLATION, PREPARATION, ACTION, MAINTENANCE

# 心理准备度
CoreResistanceLevel: RESISTANCE, AMBIVALENCE, COMPROMISE, ADAPTATION, INTEGRATION

# 培育阶段（四阶段）
CoreCultivationStage: STARTUP, ADAPTATION, STABILITY, INTERNALIZATION

# 风险等级
RiskLevel: R0(正常), R1(低), R2(中), R3(高), R4(危机)
```

---

## 三、核心引擎层

### 3.1 触发器引擎 `core/trigger_engine.py`

**职责：** L2 层——从多模态数据中检测行为/生理/心理/环境触发器

```
TriggerEngine
├── recognize_triggers(user_id, text, hrv, glucose, profile)  ← 主入口
│   ├── _recognize_text_triggers(content, user_id)    → 文本情感/风险分析
│   ├── _recognize_hrv_triggers(values, user_id)      → HRV 信号处理
│   ├── _recognize_glucose_triggers(values, user_id)  → 血糖数据处理
│   ├── _recognize_profile_triggers(profile)          → 用户画像触发
│   └── _deduplicate_triggers(triggers)               → 去重
├── get_trigger_definition(tag_id) → Dict
└── get_all_triggers() → Dict
```

**输出：** `List[Trigger]`，每个 Trigger 包含：
- `tag_id` (如 "high_glucose")
- `category` (PHYSIOLOGICAL/PSYCHOLOGICAL/BEHAVIORAL/ENVIRONMENTAL)
- `severity` (CRITICAL/HIGH/MODERATE/LOW)
- `confidence` (0-1)
- `metadata` (证据、检测方法等)

**依赖：** `core/multimodal_client.py` (异步 HTTP 调用多模态处理服务)

### 3.2 评估引擎 `core/assessment_engine.py`

**职责：** L2 层——风险评估、路由决策、干预匹配

```
AssessmentEngine
├── assess(user_id, text, hrv, glucose, profile, context)  ← 主入口
│   ├── Step 1: trigger_engine.recognize_triggers()
│   ├── Step 2: assess_risk(triggers, profile)
│   │   ├── 计算严重度分布 {critical: n, high: n, ...}
│   │   ├── 检测聚类模式 (代谢综合征/倦怠/抑郁)
│   │   └── 确定风险等级 R0-R4
│   └── Step 3: route_agents(triggers, risk, profile)
│       ├── 按 trigger→agent 映射评分
│       └── 选择 primary + secondary agents
├── 输出: AssessmentResult
│   ├── triggers: List[Trigger]
│   ├── risk_assessment: RiskAssessment {risk_level, risk_score, urgency}
│   └── routing_decision: RoutingDecision {primary_agent, secondary_agents}
```

**风险评分算法：**
```
severity_weights = {CRITICAL: 40, HIGH: 25, MODERATE: 10, LOW: 5}
risk_score = Σ(trigger.severity_weight × trigger.confidence)

聚类加成:
  metabolic_syndrome (high_glucose + glucose_spike + sedentary + high_gi_meal) → +15
  burnout (stress_overload + poor_sleep + low_motivation + work_stress) → +15
  depression (depression_sign + negative_sentiment + low_motivation + sedentary) → +15

风险等级:
  R4: score >= 80 (危机)
  R3: score >= 60 (高风险)
  R2: score >= 35 (中风险)
  R1: score >= 15 (低风险)
  R0: score < 15 (正常)
```

### 3.3 多模态客户端 `core/multimodal_client.py`

**职责：** 异步 HTTP 客户端，连接多模态处理服务 API

```
MultimodalClient
├── health_check() → Dict
├── 文本处理:
│   └── process_text(content, user_id, text_type)
│       → {sentiment, sentiment_score, primary_emotion, emotions, keywords, risk_signals, risk_score}
├── 信号处理:
│   ├── process_signal(signal_type, values, user_id, sample_rate, device_id)
│   ├── process_heartrate(values, user_id)  → PPG 信号
│   └── process_glucose(values, user_id)    → CGM 信号
├── 融合评估:
│   ├── fuse_meal_assessment(user_id, text, glucose_before, glucose_after, meal_type)
│   │   → {overall_score, nutrition_score, glucose_response, risk_level, recommendations}
│   └── fuse_emotion_assessment(user_id, text, hrv_values)
│       → {overall_emotion, stress_level, risk_level, recommendations}
└── batch_process(user_id, text, hrv, glucose) → 全部模态一次处理
```

**配置：** base_url=`http://localhost:8090`, timeout=30s, max_retries=3

### 3.4 Master Agent 9 步流水线

```
Step 1: 用户输入 / 设备数据 → 系统
Step 2: Master Agent 接收请求
Step 3: 更新 UserMasterProfile
Step 4: Agent Router 确定问题类型与优先级
Step 5: 调用 1-2 个专科 Agent
Step 6: Multi-Agent Coordinator 统一上下文与结果
Step 7: Intervention Planner 生成个性化行动路径
Step 8: Response Synthesizer 输出统一教练响应
Step 9: 回写 UserMasterProfile + 生成日常任务与追踪点
```

**数据流验证器 `CoreDataFlowValidator`：**
- `validate_agent_communication(sender, receiver, message_type)` — 确保只有合法通信对
- `validate_profile_write(writer, channel)` — 确保只有 MasterOrchestrator 可写入画像

---

## 四、智能体层

### 4.1 Octopus 限幅引擎 `agents/octopus_engine.py`

**职责：** 基于用户效能感动态调节任务难度/数量

```
OctopusClampingEngine(user_id, base_efficacy=50)
├── octopus_clamping(raw_tasks, wearable_data)  ← 主算法
│   ├── Phase 1: WEARABLE_AUDIT — 穿戴数据调整效能
│   │   └── HR >= 100: efficacy -= 20
│   │   └── HR >= 85:  efficacy -= 10
│   │   └── HR <= 50:  efficacy += 5
│   ├── Phase 2: EFFICACY_CALC — 计算最终效能 (0-100)
│   ├── Phase 3: CLAMPING_LEVEL — 确定约束等级
│   │   ├── MINIMAL (efficacy < 20): 最多1任务, 难度≤1
│   │   ├── MODERATE (efficacy 20-49): 最多2任务, 难度≤2
│   │   └── FULL (efficacy ≥ 50): 最多5任务, 难度≤5
│   └── Phase 4: TASK_FILTER — 过滤&限制任务
└── 输出: ClampingResult {clamped_tasks, reasoning_path, final_efficacy}
```

### 4.2 Octopus 状态机 `agents/octopus_fsm.py`

**6 状态 FSM：**

```
AUDIT → SELECT → DECOMPOSE → CONSTRAINT → ACTION → FEEDBACK
  │        │         │            │           │         │
分析输入  路由专家   生成原始任务  应用限幅    生成响应   记录完成
```

### 4.3 Agent 基础设施

| 模块 | 职责 | 关键类/方法 |
|------|------|-----------|
| `base.py` | Agent 基类 | `ExpertAgent(chat_engine, config)` — `.chat(message)`, `.reset()` |
| | Agent 配置 | `AgentConfig(name, id, keywords, can_consult, priority)` |
| `registry.py` | 单例注册表 | `AgentRegistry` — `.register()`, `.get()`, `.list_by_priority()` |
| `factory.py` | Agent 工厂 | `AgentFactory` — 从 config.yaml 创建 ExpertAgent 实例 |
| | | 加载系统提示词 → 加载向量索引 → 创建 LlamaIndex ChatEngine |
| `router.py` | 意图路由 | `IntentRouter` — 基于关键词评分 → `RoutingResult(primary, secondary, confidence)` |
| `collaboration.py` | 多专家协作 | `CollaborationProtocol` — 会诊请求 → 响应合成 → 安全检查 |
| `orchestrator.py` | 总协调器 | `AgentOrchestrator` — 初始化所有Agent → 路由 → 主Agent回答 → 会诊 → 合成 |

### 4.4 协调器完整流程 `AgentOrchestrator.process_query()`

```
用户查询
    ↓
Router.route(query)
    → RoutingResult {primary_agent, secondary_agents, confidence}
    ↓
registry.get(primary_agent)
    → primary_agent.chat(query)
    → primary_response
    ↓
FOR each secondary_agent:
    → CollaborationProtocol.request_consultation()
        → consultant.chat(consultation_prompt)
        → ConsultationResponse {advice, confidence, warnings}
    ↓
CollaborationProtocol.synthesize_responses()
    → LLM 合成所有专家意见
    → final_response
    ↓
OrchestratorResponse {
    final_response, primary_expert, consulted_experts,
    routing_confidence, routing_reasoning
}
```

### 4.5 config.yaml 定义的 4 个核心专家

| 专家 ID | 名称 | LLM 模型 | 触发场景 |
|---------|------|---------|---------|
| `mental_health` | 心理咨询师 | qwen2.5:7b | 情绪管理、压力调节、睡眠改善 |
| `nutrition` | 营养师 | qwen2.5:7b | 膳食指导、营养建议、体重管理 |
| `sports_rehab` | 运动康复师 | qwen2.5:7b | 运动处方、损伤康复、体态矫正 |
| `tcm_wellness` | 中医养生师 | qwen2.5:7b | 体质调理、四季养生、经络保健 |

### 4.6 architecture.yaml 定义的 4 个 Dify Agent

| Agent ID | 名称 | 核心能力 | 触发条件 |
|----------|------|---------|---------|
| A1 | 主动健康教练 | 健康评估、平衡分析、阶段匹配、动机访谈 | 首次使用、主动咨询、健康分数变化 |
| A2 | 运动指导师 | 运动能力评估、运动处方、风险预警 | 运动咨询、目标设定、数据异常 |
| A3 | 饮食顾问 | 饮食习惯分析、低GI指导、热量计算 | 饮食咨询、血糖波动、饮食记录 |
| A4 | 心理支持师 | 情绪识别、压力管理、动机维持 | 负面情绪、阶段倒退、坚持困难 |

---

## 五、API 服务层

### 5.1 API 总览

| 模块 | 前缀 | 端点数 | 主要职责 |
|------|------|--------|---------|
| `auth_api.py` | `/api/v1/auth` | 4 | 注册、登录、用户信息、登出 |
| `assessment_api.py` | `/api/assessment` | 4 | 提交评估、查询历史、获取结果 |
| `device_data.py` | `/device` (挂载到 `/api/v1/mp`) | 19 | 设备绑定、血糖/体重/血压/睡眠/活动/心率/HRV |
| `miniprogram.py` | `/mp` (挂载到 `/api/v1`) | 17 | 任务系统、AI对话、用户状态、风险、LLM健康 |
| `main.py` | `/api/v1` | 9 | 分发中心、编排器接口 |
| `routes.py` | `/api/v1` | 6 | 健康检查、专家列表、Octopus对话、任务分解 |
| `baps_api.py` | `/` (独立服务:8001) | 12 | BAPS 问卷管理、评分、报告 |
| `xingjian_api.py` | `/` (独立服务) | 6 | 行健教练对话、限幅引擎 |

### 5.2 认证系统 `api/auth_api.py`

```
POST /api/v1/auth/register  → 创建用户(PATIENT角色) → 返回 JWT tokens
POST /api/v1/auth/login     → OAuth2 密码流 → 支持用户名/邮箱登录
GET  /api/v1/auth/me        → [需认证] 返回当前用户信息
POST /api/v1/auth/logout    → [需认证] 登出
```

**认证流程：**
- 密码哈希: bcrypt (`passlib`)
- Token: JWT HS256 (`python-jose`)
- Access Token 有效期: 30分钟 (可配)
- Refresh Token 有效期: 7天 (可配)
- 权限层级: admin(3) > coach(2) > patient(1) > system(0)

### 5.3 评估 API `api/assessment_api.py`

```
GET  /assessment/recent/{user_id}?limit=5      → 最近N条已完成评估
GET  /assessment/history/{user_id}?page&size    → 分页评估历史
GET  /assessment/{assessment_id}                → 单条评估详情 (含触发器+路由)
POST /assessment/submit                         → [501 待实现] 提交评估
```

**返回数据结构包含：**
- 风险评估: risk_level, risk_score, primary_concern, urgency, reasoning
- 触发器列表: tag_id, severity, confidence, evidence
- 路由决策: primary_agent, secondary_agents, response_time, recommended_actions

### 5.4 设备数据 API `api/device_data.py` (19 端点)

#### 设备管理
```
GET    /devices              → 用户已绑定设备列表
POST   /devices/bind         → 绑定新设备 (CGM/血糖仪/手表/手环/秤/血压计)
DELETE /devices/{device_id}  → 解绑设备
```

#### 血糖管理
```
POST /glucose/manual                → 手动记录血糖 (1.0-35.0 mmol/L)
GET  /glucose?start&end&limit       → 范围查询 + 统计 (均值/标准差/CV/TIR)
GET  /glucose/current               → 最新读数 + 趋势箭头 (↑↑/↑/→/↓/↓↓)
GET  /glucose/chart/daily?date      → 日图表数据 (时间戳+值+目标范围)
```

**血糖统计算法：**
```python
TIR (Time in Range): 3.9-10.0 mmol/L
CV (变异系数): std / avg × 100
趋势: rising_fast(↑↑), rising(↑), flat(→), falling(↓), falling_fast(↓↓)
```

#### 体征数据
```
POST /weight                  → 记录体重 (含BMI/体脂/肌肉)
GET  /weight?start&end&limit  → 体重历史 + 趋势 (gaining/losing/stable)
POST /blood-pressure          → 记录血压 + 自动分级 (正常/偏高/高血压)
GET  /blood-pressure?limit    → 血压历史 + 统计
```

#### 设备同步
```
POST /sync                    → 单设备同步 (简单版)
POST /sync/batch              → 批量同步 (glucose/heart_rate/hrv/sleep/activity/workout)
GET  /sync/status/{device_id} → 同步状态查询
```

**批量同步去重逻辑：** 按 `user_id + device_id + recorded_at` 判断重复

#### 健康数据查询
```
GET /sleep?start&end&limit    → 睡眠记录 + 周平均
GET /sleep/last-night         → 昨晚睡眠 + 各阶段 + 洞察
GET /activity?date|range      → 活动数据 (步数/距离/卡路里/活跃分钟)
GET /heart-rate?date&limit    → 心率读数 + 统计 (静息/平均/最高/最低)
GET /hrv?start&end&limit      → HRV数据 + 统计 (SDNN/RMSSD/压力/恢复)
GET /dashboard/today          → 今日综合看板 (血糖+活动+睡眠+体重+告警)
```

### 5.5 小程序 API `api/miniprogram.py` (17 端点)

#### 任务系统
```
GET  /mp/task/today     → 今日任务 (阶段/天数/任务描述/焦点/进度/问候)
POST /mp/task/feedback  → 任务反馈 (done/skip/partial → 积分/连续/成就/风险评估)
```

**14天干预周期：**
```
引导期 (1-3天):  CHECKIN_MEAL, CHECKIN_MOOD
基础期 (4-7天):  CHECKIN_MEAL, CHECKIN_GLUCOSE, EXERCISE_WALK
深化期 (8-11天): CHECKIN_MEAL, CHECKIN_GLUCOSE, EXERCISE_WALK, MINDFULNESS
巩固期 (12-14天): CHECKIN_MEAL, CHECKIN_GLUCOSE, EXERCISE_WALK, REFLECTION
维持期 (15天+):  CHECKIN_MEAL, CHECKIN_GLUCOSE
```

#### AI 对话 (Dify/Ollama 双模式)
```
POST /mp/chat          → 非流式对话 (auto路由: Dify优先, Ollama降级)
POST /mp/chat/stream   → SSE流式对话 (含 ping keepalive)
GET  /mp/llm/health    → 双提供者健康状态 {ollama: {...}, dify: {...}, active_provider}
```

**ChatResponse 结构：**
```json
{
  "message": "AI回复",
  "session_id": "chat_1_17698...",
  "model": "dify" | "qwen2.5:14b" | "fallback",
  "provider": "dify" | "ollama" | "fallback",
  "conversation_id": "dify-conv-uuid" | null
}
```

**降级流程：**
```
LLM_PROVIDER=auto:
  请求 → _resolve_provider()
       → Dify 健康检查(缓存30s)
       ├── 健康 → dify_service.chat/chat_stream
       │          ├── 成功 → provider=dify
       │          └── 失败 → 降级 Ollama → provider=ollama
       └── 不健康 → behavior_health_agent.respond → provider=ollama
```

#### 聊天历史
```
GET    /mp/chat/history/{session_id}  → 会话消息列表
GET    /mp/chat/sessions              → 用户所有会话
DELETE /mp/chat/session/{session_id}  → 删除会话
DELETE /mp/chat/history               → 清空所有历史
```

#### 用户状态与风险
```
GET  /mp/user/state        → 用户状态 (天数/阶段/积分/连续/风险/里程碑)
POST /mp/user/mode         → 设置模式 (pilot正常 / training显示思考过程)
GET  /mp/progress/summary  → 进度摘要 (百分比/成就列表)
GET  /mp/risk/status       → 风险状态 (等级/通知/是否显示/是否需要支援)
POST /mp/agent/respond     → Agent AI响应 (根据阶段+事件生成个性化回复)
```

### 5.6 编排器接口 `api/main.py`

```
POST /api/v1/dispatch                       → 分发中心 (dify模式/ollama模式)
POST /orchestrator/process                  → 9步流水线完整处理
POST /orchestrator/briefing                 → 每日简报
GET  /orchestrator/briefing/{uid}/message   → 格式化推送消息
POST /orchestrator/agent-task               → 单Agent任务执行
POST /orchestrator/action-plan              → 创建行动计划
GET  /orchestrator/action-plan/{uid}/phased → 多阶段计划
POST /orchestrator/coordinate               → 多Agent协调 (冲突消解+权重融合)
POST /orchestrator/route                    → Agent路由 (简版)
POST /orchestrator/route/detailed           → Agent路由 (详细版含reasoning)
GET  /orchestrator/profile/{user_id}        → 用户画像
GET  /orchestrator/status                   → 编排器状态
```

### 5.7 Dify 集成 `api/config.py` + `api/dify_service.py` + `api/context_builder.py`

```
config.py:
  LLM_PROVIDER = "auto" | "dify" | "ollama"
  DIFY_API_URL = "http://localhost:8080/v1"
  DIFY_API_KEY = "app-TSdoLNkz636aipfD9zTtHdEY"
  HEALTH_CACHE_TTL = 30 (秒)

DifyChatService:
  check_health()       → GET /parameters (缓存30s)
  chat(query, user, inputs, session_id) → 内部用streaming收集完整响应
  chat_stream(...)     → SSE流 (解析 agent_message/message_end)
  _conversation_map    → session_id → dify_conversation_id (内存映射)

context_builder.build_dify_inputs(user_id, state):
  → {behavior_stage, risk_level, day_index, device_summary}
  → device_summary: 查询最近血糖/睡眠/HRV 生成文本摘要
```

### 5.8 LLM 服务 `api/llm_service.py`

```
OllamaService(base_url, model="qwen2.5:14b"):
  check_health()     → GET /api/tags
  chat(message, history, system_prompt, temperature) → POST /api/chat (非流式)
  chat_stream(...)   → POST /api/chat (流式, yields chunks)

BehaviorHealthAgent(ollama_service):
  _build_context_prompt(stage, day_index, event, risk_level)
    → 系统提示词 + 当前用户状态 + 事件提示 + 风险注意
  respond(user_message, history, stage, day_index, event, risk_level)
    → 完整响应 (失败时返回 fallback)
  respond_stream(...)
    → 流式响应
```

**系统角色 "小健"：**
- 专业、温暖、有同理心的健康行为改变陪伴者
- 使用循证的行为改变技术（动机性访谈、CBT原则）
- 对话原则：倾听优先、小步前进、个性化、正向激励、科学依据
- 回复100-200字，口语化中文

### 5.9 聊天历史持久化 `api/chat_history.py`

```
ChatHistoryService (静态方法):
  create_session(user_id, session_id, model) → ChatSession
  get_or_create_session(...)                 → ChatSession
  add_message(session_id, role, content, model, metadata) → ChatMessage
  get_messages(session_id, limit=50) → [{role, content}, ...]
  get_user_sessions(user_id, limit=20) → List[ChatSession]
  delete_session(session_id) → bool (软删除)
  clear_user_history(user_id) → int (清空数)
```

### 5.10 会话管理 `api/session.py`

```
SessionManager(ttl_seconds=3600, cleanup_interval=300):
  内存会话存储 (非持久化，用于 Agent 对话)
  create_session() / get_session() / add_message()
  后台清理线程自动过期

  vs ChatHistoryService: 数据库持久化，用于 /mp/chat 历史
```

---

## 六、知识库与触发器系统

### 6.1 完整触发器定义 (28个)

#### 生理类 (8个)

| tag_id | 名称 | 严重度 | 阈值 | 路由 Agent |
|--------|------|--------|------|-----------|
| `high_glucose` | 高血糖 | HIGH | >10.0 mmol/L | GlucoseAgent, MetabolicAgent |
| `low_glucose` | 低血糖 | CRITICAL | <3.9 mmol/L | CrisisAgent, GlucoseAgent |
| `glucose_spike` | 血糖波动 | MODERATE | >3.0 mmol/L变幅/2h | GlucoseAgent, NutritionAgent |
| `low_hrv` | 低HRV | MODERATE | SDNN <30ms | StressAgent, SleepAgent |
| `high_stress_hrv` | 压力异常 | HIGH | 压力指数 >80 | StressAgent, MentalHealthAgent |
| `high_heartrate` | 心率过高 | MODERATE | 静息 >100bpm | StressAgent, ExerciseAgent |
| `low_heartrate` | 心率过低 | MODERATE | <60bpm(非运动员) | CrisisAgent |
| `poor_sleep` | 睡眠差 | MODERATE | 效率<70% 或 深睡<15% | SleepAgent |

#### 心理类 (7个)

| tag_id | 名称 | 严重度 | 阈值 | 路由 Agent | 关键词 |
|--------|------|--------|------|-----------|--------|
| `high_anxiety` | 高焦虑 | HIGH | 情感置信>0.6 或 GAD-7≥10 | MentalHealthAgent, StressAgent | 焦虑,担心,紧张,不安 |
| `depression_sign` | 抑郁倾向 | HIGH | 悲伤>7天 或 PHQ-9≥10 | MentalHealthAgent, CrisisAgent | 抑郁,没意思,不想动 |
| `stress_overload` | 压力过载 | HIGH | 自评压力>80 | StressAgent, MentalHealthAgent | 压力大,受不了,崩溃 |
| `negative_sentiment` | 负面情绪 | MODERATE | 情感分<-0.5 | MentalHealthAgent, MotivationAgent | — |
| `low_motivation` | 动机低下 | MODERATE | 动机分<30 | MotivationAgent, CoachingAgent | — |
| `crisis_keyword` | 危机关键词 | CRITICAL | 风险分>0.5 | CrisisAgent | 不想活,自杀,自残 |
| `family_conflict` | 家庭冲突 | MODERATE | 家庭压力>70 | MentalHealthAgent, CoachingAgent | 吵架,家里 |

#### 行为类 (6个)

| tag_id | 名称 | 严重度 | 阈值 | 路由 Agent |
|--------|------|--------|------|-----------|
| `task_failure` | 任务失败 | MODERATE | 连续≥3次失败 | CoachingAgent, MotivationAgent |
| `missing_checkin` | 漏打卡 | LOW | ≥2天缺失 | CoachingAgent |
| `low_adherence` | 依从性低 | HIGH | 7天内<50% | CoachingAgent, MotivationAgent |
| `high_gi_meal` | 高GI饮食 | MODERATE | 高GI≥3次/周 | NutritionAgent, GlucoseAgent |
| `irregular_meal` | 饮食不规律 | MODERATE | 餐时差>2小时 | NutritionAgent |
| `sedentary` | 久坐 | MODERATE | <3000步/天 | ExerciseAgent |

#### 环境类 (4个)

| tag_id | 名称 | 严重度 | 路由 Agent |
|--------|------|--------|-----------|
| `support_lack` | 缺乏支持 | MODERATE | CoachingAgent |
| `resource_barrier` | 资源障碍 | MODERATE | CoachingAgent |
| `work_stress` | 工作压力 | MODERATE | StressAgent, CoachingAgent |
| `family_conflict` | 家庭冲突 | MODERATE | MentalHealthAgent, CoachingAgent |

### 6.2 触发器聚类模式 (3个)

| 聚类名 | 组成触发器 | 附加风险 | 路由 |
|--------|-----------|---------|------|
| `metabolic_syndrome` | high_glucose + glucose_spike + sedentary + high_gi_meal | +15分 | MetabolicAgent, NutritionAgent, ExerciseAgent |
| `burnout` | stress_overload + poor_sleep + low_motivation + work_stress | +15分 | MentalHealthAgent, StressAgent, CoachingAgent |
| `depression` | depression_sign + negative_sentiment + low_motivation + sedentary | +15分 | MentalHealthAgent, CrisisAgent |

---

## 七、BAPS 评估体系

### 7.1 四大问卷

| 问卷 | 题数 | 维度数 | 耗时 | 量表 | 核心输出 |
|------|------|--------|------|------|---------|
| **Big Five** (大五人格) | 50 | 5 (E/N/C/A/O) | 10分钟 | -4~+4 双极 | 人格画像 |
| **BPT-6** (行为分型) | 18 | 6 类型 | 5分钟 | 1-5 Likert | 行为类型 + 干预策略 |
| **CAPACITY** (改变潜力) | 32 | 8 维度 | 8分钟 | 1-5 Likert | 改变潜力等级 + 薄弱环节 |
| **SPI** (成功指数) | 50 | 5 维度(加权) | 12分钟 | 1-5 Likert | 成功概率 + 维度得分 |

### 7.2 BPT-6 六大行为类型

| 类型 | 核心特征 | 人格基础 | 干预重点 | 推荐策略 | 避免策略 |
|------|---------|---------|---------|---------|---------|
| **行动型** | 说做就做，执行力强 | 高尽责+低神经质 | 防过度扩展，增加反思 | 执行意图、数据追踪 | 过度分析 |
| **知识型** | 求知欲强，行动迟疑 | 高开放+低尽责 | 选择MVP行动，设实验周期 | 微实验、知识奖励 | 填鸭式教育 |
| **情感型** | 情绪驱动 | 高神经质+高开放 | 建立情绪觉察，自我关怀 | 情绪日记、正念 | 忽视情绪 |
| **关系型** | 依赖关系 | 高外向+高宜人 | 找到问责伙伴，加入支持组 | 社区参与、同伴打卡 | 孤立行动 |
| **环境型** | 受环境影响大 | 五维均衡 | 审计优化环境，设默认值 | 环境设计、提示系统 | 纯靠意志力 |
| **矛盾型** | 抗拒改变 | 高神经质 | 接受矛盾，微小尝试 | 渐进暴露、安全实验 | 强迫改变 |

### 7.3 CAPACITY 八维度框架

| 维度 | 全称 | 评估内容 |
|------|------|---------|
| **C1** | Consciousness | 对行为问题与触发因素的自我觉察 |
| **A1** | Autonomy | 控制感与自主决定能力 |
| **P** | Personality Match | 目标与人格/过往成功的匹配度 |
| **A2** | Action Resources | 时间、工具、环境支持 |
| **C2** | Commitment | 付出努力和公开承诺的意愿 |
| **I** | Identity | 与自我概念的一致性 |
| **T** | Timeline | 清晰时间线与合理期望 |
| **Y** | Yield Expectation | 对收益>代价的信念 |

**总分范围：** 32-160
- 128-160: 高潜力 → 挑战型目标
- 96-127: 中高 → 稳步推进
- 64-95: 中等 → 降低难度+增加支持
- 32-63: 低潜力 → 先解决前置问题

### 7.4 SPI 成功预测指数

**公式：** `SPI = M×0.30 + A×0.25 + S×0.20 + E×0.15 + H×0.10`

| 维度 | 权重 | 评估内容 |
|------|------|---------|
| **M** (Motivation) | 0.30 | 重要性、紧迫性、意愿 |
| **A** (Ability) | 0.25 | 技能、自控力、适应性 |
| **S** (Support) | 0.20 | 家人、朋友、专业帮助 |
| **E** (Environment) | 0.15 | 时间、资源、设施、稳定性 |
| **H** (History) | 0.10 | 过往成功、韧性、学习 |

**成功概率：**
- 40-50: >75% (挑战型目标)
- 30-39: 50-75% (稳步推进)
- 20-29: 30-50% (降低难度+支持)
- 10-19: 15-30% (从微习惯开始)
- 0-9: <15% (先解决前置条件)

### 7.5 综合评估报告输出

```
执行摘要:
  → 人格画像 (Big Five)
  → 行为类型 (BPT-6 分型名+核心特征)
  → 改变潜力 (CAPACITY 等级+得分)
  → 成功指数 (SPI 得分+成功率)
  → 核心战略建议

交叉分析:
  → 人格-行为类型匹配
  → 整体改变准备度 (CAPACITY + SPI)
  → 关键障碍 (CAPACITY弱维度 + SPI低维度)
  → 关键优势

四阶段行动计划:
  Phase 1 (1-2周): 建立行为
  Phase 2 (3-4周): 建立常规
  Phase 3 (5-8周): 稳定行为
  Phase 4 (9-12周): 身份整合
```

---

## 八、行为处方库

`models/rx_library.json` 定义了 7 套完整行为处方：

### 8.1 处方结构

每套处方包含：
- **三阶段策略** (意向期/准备期/行动期)
- **构建性建议** (3-4条具体行为)
- **知识点** (2-3个教育内容)
- **教学视频** (2-3个操作演示)
- **产品映射** (3-4个配套产品，含触发条件)

### 8.2 七大处方

| 处方 ID | 领域 | 核心建议 |
|---------|------|---------|
| **RX-SLEEP-001** | 睡眠改善 | 固定作息、睡前断屏、放松仪式、环境优化 |
| **RX-STRESS-001** | 压力管理 | 腹式呼吸、正念冥想、时间边界、运动 |
| **RX-EXERCISE-001** | 运动习惯 | 晨间拉伸、碎片运动、步数递增、有氧套路 |
| **RX-NUTRITION-001** | 饮食调整 | 8杯水、规律用餐、每餐蔬菜、减少加工食品 |
| **RX-TCM-001** | 中医养生 | 养生茶饮、穴位按摩、四季起居、食疗 |
| **RX-EMOTION-001** | 情绪调节 | 情绪日记、STOP技术、情绪命名、情绪工具箱 |

### 8.3 处方阶段匹配

| 心理准备度 | 对应处方阶段 | 沟通基调 | 核心动作 |
|-----------|------------|---------|---------|
| 1-2 (对抗/反思) | 意向期 | 温和、接纳 | 倾听、不施压 |
| 3 (妥协) | 准备期 | 鼓励、务实 | 微目标、提供选择 |
| 4-5 (顺应/臣服) | 行动期 | 支持、系统化 | 系统规划、监测反馈 |

---

## 九、Dify 工作流集成

### 9.1 Dify 基础设施 (docker-compose.yaml)

| 服务 | 镜像 | 内存 | 端口 | 职责 |
|------|------|------|------|------|
| API | langgenius/dify-api:0.15.3 | 8GB/4GB | — | 核心 API |
| Worker | langgenius/dify-api:0.15.3 | 12GB/6GB | — | Celery 任务 |
| Web | langgenius/dify-web:0.15.3 | 2GB/512MB | — | 前端 UI |
| PostgreSQL 15 | postgres:15-alpine | 4GB/2GB | 5432 | 数据库 |
| Redis 7 | redis:7-alpine | 3GB/1GB | 6379 | 缓存 |
| Weaviate 1.19 | semitechnologies/weaviate | 6GB/2GB | — | 向量存储 |
| Sandbox | langgenius/dify-sandbox:0.2.10 | 2GB/512MB | — | 代码执行 |
| SSRF Proxy | ubuntu/squid | 512MB/256MB | — | 安全代理 |
| Nginx | nginx:latest | 512MB/256MB | 8080/8443 | 反向代理 |

**总内存分配：** ~40GB (56GB系统)

### 9.2 BAPS 评估工作流

```yaml
workflow: baps_assessment_workflow.yml
mode: workflow

Start → Assessment Router (LLM: qwen2.5:7b, temp=0.1)
         ├── "bpt6"  → BPT-6 HTTP Request → Generate Report (qwen2.5:14b) → End
         ├── "spi"   → SPI HTTP Request   → Generate Report → End
         └── "full"  → Full Assessment    → Generate Report → End
```

### 9.3 集成 Prompt 模板

| Prompt | 用途 | 输出 |
|--------|------|------|
| `PROMPT_TTM_ASSESSOR` | 评估心理准备度 | 五级阶段 + TTM阶段 + SPI系数 + 风险等级 |
| `PROMPT_INTERVENTION_PRESCRIBER` | 生成个性化干预 | 共情回应 + 行为处方 + 任务 + 安全提醒 |
| `PROMPT_SLEEP_AGENT` | 睡眠专科分析 | 分析 + 风险 + 发现 + 建议 + 血糖关联 |
| `PROMPT_GLUCOSE_AGENT` | 代谢健康分析 | TIR分析 + CV% + 餐后模式 + 趋势 + 紧急标志 |

### 9.4 当前 Dify 对话集成 (`api/dify_service.py`)

```
DifyChatService → Dify Agent Chat App (主动健康教练)
├── SSE 事件类型: agent_thought → agent_message → message_end
├── 多轮对话: session_id → dify_conversation_id 映射
├── 上下文注入: behavior_stage, risk_level, day_index, device_summary
└── 健康检查: GET /parameters (缓存30s)
```

---

## 十、数据库 ORM 模型

### 10.1 表关系图

```
User (用户)
├── 1:N → Assessment (评估)
│         └── 1:N → TriggerRecord (触发器记录)
│         └── 1:N → Intervention (干预措施)
├── 1:N → UserSession (会话)
├── 1:N → ChatSession (聊天会话)
│         └── 1:N → ChatMessage (聊天消息)
├── 1:N → HealthData (健康数据)
├── 1:N → UserDevice (用户设备)
├── 1:N → GlucoseReading (血糖读数)
├── 1:N → HeartRateReading (心率读数)
├── 1:N → HRVReading (HRV读数)
├── 1:N → SleepRecord (睡眠记录)
├── 1:N → ActivityRecord (活动记录)
├── 1:N → WorkoutRecord (运动记录)
└── 1:N → VitalSign (体征数据: 体重/血压/体温/血氧)
```

### 10.2 关键表结构

| 表名 | 关键字段 | 用途 |
|------|---------|------|
| **User** | username, email, password_hash, role(PATIENT/COACH/ADMIN), profile(JSON), adherence_rate | 用户主表 |
| **Assessment** | user_id(FK), risk_level(R0-R4), risk_score, primary_agent, secondary_agents(JSON), status | 评估记录 |
| **TriggerRecord** | assessment_id(FK), tag_id, category, severity, confidence, metadata(JSON) | 触发器记录 |
| **Intervention** | assessment_id(FK), agent_type, intervention_type, actions(JSON), status, feedback_score | 干预措施 |
| **UserDevice** | user_id(FK), device_type(CGM/手表/秤等), status(CONNECTED/DISCONNECTED), last_sync_at | 设备绑定 |
| **GlucoseReading** | user_id(FK), device_id(FK), value(mmol/L), trend, source(cgm/finger/manual), meal_tag | 血糖读数 |
| **HeartRateReading** | user_id(FK), hr(bpm), activity_type(rest/walk/run/sleep) | 心率读数 |
| **HRVReading** | user_id(FK), sdnn, rmssd, lf, hf, lf_hf_ratio, stress_score, recovery_score | HRV读数 |
| **SleepRecord** | user_id(FK), sleep_date, total_duration_min, awake/light/deep/rem_min, sleep_score, efficiency | 睡眠记录 |
| **ActivityRecord** | user_id(FK), activity_date, steps, distance_m, calories, sedentary/active_min | 活动记录 |
| **VitalSign** | user_id(FK), data_type(weight/bp/temp/spo2), weight_kg, bmi, systolic, diastolic | 体征数据 |
| **ChatSession** | user_id(FK), session_id, model, message_count, is_active | 聊天会话 |
| **ChatMessage** | session_id(FK), role(user/assistant), content, model, tokens_used | 聊天消息 |

### 10.3 数据库配置

- **默认:** SQLite `./data/behavioral_health.db`
- **环境变量:** `DATABASE_URL` (支持 PostgreSQL)
- **连接池:** SQLite 使用 StaticPool, PostgreSQL 使用 size=10 pool
- **事务管理:** `db_transaction()` 上下文管理器 (自动提交/回滚)

---

## 十一、前端 H5 患者端

### 11.1 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | — | 响应式框架 |
| TypeScript | — | 类型安全 |
| Vant 4.9.0 | — | 移动端 UI 组件 |
| Pinia 3.0.0 | — | 状态管理 |
| Vue Router 4.4.0 | — | 路由管理 |
| Axios 1.7.0 | — | HTTP 客户端 |
| Vite 6.0.0 | — | 构建工具 |

### 11.2 页面架构

| 页面 | 组件 | 数据来源 | 状态管理 |
|------|------|---------|---------|
| **LoginPage** | 登录表单 | `/auth/login` | user store |
| **RegisterPage** | 注册表单 | `/auth/register` | user store |
| **HomePage** | 健康仪表板 | `/assessment/recent`, `/mp/task/today` | assessment + device store |
| **HealthDataPage** | 设备数据录入(最大21KB) | `/device/*` 全系列 | device store |
| **DataInputPage** | 手动数据录入 | `/device/glucose/manual`, `/device/weight` | device store |
| **ChatPage** | AI教练对话(9.9KB) | `/mp/chat`, `/mp/chat/stream` | chat store |
| **ResultPage** | 评估结果展示 | `/assessment/{id}` | assessment store |
| **HistoryPage** | 历史记录(分页) | `/assessment/history` | assessment store |
| **DataAnalysisPage** | 数据分析趋势(10.2KB) | `/device/glucose/chart`, `/device/hrv` | device store |
| **SettingsPage** | 用户设置 | `/auth/me`, `/mp/user/mode` | user store |

### 11.3 Store 结构

| Store | 状态 | 关键 Actions |
|-------|------|-------------|
| **user** | profile, token, isLoggedIn | login(), logout(), fetchProfile() |
| **assessment** | currentResult, history, recent | submitAssessment(), fetchHistory() |
| **chat** | sessions, messages, streaming | sendMessage(), sendStreamMessage(), loadHistory() |
| **device** (11.1KB) | glucose, weight, bp, sleep, activity | syncData(), fetchGlucose(), recordWeight() |

### 11.4 API 层

| 模块 | 端点数 | 功能 | 特性 |
|------|--------|------|------|
| `request.ts` | — | Axios 配置 | Token 拦截器、错误处理 |
| `auth.ts` | 4 | 认证 | 登录/注册/登出/用户信息 |
| `assessment.ts` | 4 | 评估 | 提交/查询/历史 + Mock fallback |
| `chat.ts` (9.6KB) | 7 | 对话 | 阻塞+SSE流式+历史 |
| `device.ts` (11.1KB) | 15+ | 设备数据 | 全系列CRUD |

---

## 十二、部署与基础设施

### 12.1 端口分配

| 端口 | 服务 | 说明 |
|------|------|------|
| 5180 | admin-portal | 管理后台前端 |
| 8000 | api/main.py | 主 API 服务 |
| 8001 | baps_api.py | BAPS 评估服务 |
| 8080 | Dify (Nginx) | Dify 工作流平台 |
| 8443 | Dify (HTTPS) | Dify HTTPS |
| 11434 | Ollama | 本地 LLM 服务 |
| 5432 | PostgreSQL | 数据库 |
| 6379 | Redis | 缓存 |

### 12.2 LLM 模型

| 模型 | 用途 | 场景 |
|------|------|------|
| qwen2.5:14b | 主对话模型 | 用户对话、Agent 响应 |
| qwen2.5:7b | 专家Agent | 4个领域专家 |
| deepseek-r1:7b | 备选模型 | — |
| nomic-embed-text | 向量嵌入 | RAG 知识库检索 |

---

## 十三、端到端数据流全图

### 13.1 用户对话完整链路

```
用户发送消息 (H5 ChatPage)
    ↓
POST /api/v1/mp/chat {message, session_id}
    ↓
miniprogram.py: chat_with_agent()
    ├── get_user_state(user_id) → {day_index, stage, risk_level}
    ├── chat_history.add_message(session_id, "user", message)
    ├── _resolve_provider() → "dify" | "ollama"
    │
    ├── [Dify 路径]
    │   ├── context_builder.build_dify_inputs(user_id, state)
    │   │   → {behavior_stage, risk_level, day_index, device_summary}
    │   ├── dify_service.chat(query, user, inputs, session_id)
    │   │   ├── 内部使用 streaming 收集
    │   │   ├── 解析 SSE: agent_thought → agent_message → message_end
    │   │   └── 保存 conversation_id 映射
    │   └── 返回 ChatResponse(provider="dify", conversation_id=...)
    │
    └── [Ollama 路径]
        ├── behavior_health_agent.respond(message, history, stage, day_index, ...)
        │   ├── _build_context_prompt() → 系统提示词 + 上下文
        │   └── ollama_service.chat() → POST /api/chat
        └── 返回 ChatResponse(provider="ollama")
```

### 13.2 评估完整链路

```
触发评估 (API / 定时 / 事件)
    ↓
AssessmentEngine.assess(user_id, text, hrv, glucose, profile)
    ├── TriggerEngine.recognize_triggers()
    │   ├── MultimodalClient.process_text(content)
    │   │   → {sentiment, emotions, risk_signals}
    │   ├── MultimodalClient.process_heartrate(hrv_values)
    │   │   → {hrv_sdnn, heart_rate, anomalies}
    │   ├── MultimodalClient.process_glucose(glucose_values)
    │   │   → {max, min, variation}
    │   └── 去重后返回 List[Trigger]
    │
    ├── assess_risk(triggers, profile)
    │   ├── 计算 severity_weights → risk_score
    │   ├── 检测聚类 (metabolic/burnout/depression)
    │   └── 返回 RiskAssessment(R0-R4)
    │
    ├── route_agents(triggers, risk, profile)
    │   ├── trigger→agent 映射评分
    │   └── 返回 RoutingDecision(primary + secondary)
    │
    └── 返回 AssessmentResult
        → 存入 Assessment 表 + TriggerRecord 表
        → 生成 Intervention 记录
```

### 13.3 设备数据同步链路

```
穿戴设备 → H5 DataInputPage / 设备SDK
    ↓
POST /api/v1/mp/device/sync/batch
{device_id, data: {glucose: {readings: [...]}, sleep: {...}, hrv: {...}}}
    ↓
device_data.py: sync_batch()
    ├── 验证 device_id 归属
    ├── FOR each data_type:
    │   ├── 去重 (user_id + device_id + recorded_at)
    │   ├── 新增 → INSERT
    │   └── 已存在 → 跳过
    ├── 统计 {records_new, records_updated, errors}
    └── 更新 device.last_sync_at
```

### 13.4 Octopus 限幅链路

```
用户消息 + 效能感评分
    ↓
AgentOrchestrator.process_query(query)
    → RoutingResult {primary_agent, secondary_agents}
    → primary_agent.chat(query)
    → CollaborationProtocol.synthesize_responses()
    → final_response
    ↓
OctopusClampingEngine.octopus_clamping(raw_tasks, wearable_data)
    ├── Phase 1: 穿戴数据调整效能
    ├── Phase 2: 计算最终效能
    ├── Phase 3: 确定限幅等级
    └── Phase 4: 过滤任务
    → ClampingResult {clamped_tasks, final_efficacy}
    ↓
OctopusChatResponse {
    response, clamped_tasks, reasoning_path,
    final_efficacy, clamping_level,
    external_hooks: {show_video, clinical_alert, suggest_break}
}
```

---

## 十四、模块间调用关系矩阵

### 14.1 导入依赖图

```
api/miniprogram.py
  → api/llm_service.py (behavior_health_agent, ollama_service)
  → api/config.py (LLM_PROVIDER)
  → api/dify_service.py (dify_service)
  → api/context_builder.py (build_dify_inputs)
  → api/chat_history.py (chat_history)

api/context_builder.py
  → api/miniprogram.py (get_user_state) [延迟导入避免循环]
  → api/session.py (db_transaction)
  → api/device_data.py (GlucoseReading, SleepRecord, HRVReading)

api/dify_service.py
  → api/config.py (DIFY_API_URL, DIFY_API_KEY, DIFY_TIMEOUT, HEALTH_CACHE_TTL)

api/main.py
  → api/config.py (DIFY_API_URL, DIFY_API_KEY, OLLAMA_API_URL, OLLAMA_MODEL)

api/device_data.py
  → core/database.py (db_transaction)
  → core/models.py (UserDevice, GlucoseReading, VitalSign, SleepRecord, ...)

api/auth_api.py
  → core/database.py (get_db)
  → core/models.py (User, UserRole, UserSession)
  → core/auth.py (hash_password, create_user_tokens, verify_token)

api/assessment_api.py
  → core/database.py (get_db)
  → core/models.py (Assessment, TriggerRecord)
  → api/dependencies.py (get_current_user)

api/routes.py
  → api/schemas.py (所有 Pydantic 模型)
  → api/session.py (session_manager)
  → api/services.py (TaskDecomposer)
  → agents/octopus_engine.py (OctopusClampingEngine)

api/baps_api.py
  → core/baps/scoring_engine.py
  → core/baps/report_generator.py
  → core/baps/questionnaires.py

core/assessment_engine.py
  → core/trigger_engine.py (get_trigger_engine, Trigger, TriggerSeverity)
  → core/multimodal_client.py (get_multimodal_client)

core/trigger_engine.py
  → core/multimodal_client.py (get_multimodal_client)

agents/orchestrator.py
  → agents/registry.py (AgentRegistry)
  → agents/factory.py (AgentFactory)
  → agents/router.py (IntentRouter)
  → agents/collaboration.py (CollaborationProtocol)
  → agents/base.py (AgentConfig)
```

### 14.2 服务间通信

```
H5 患者端 (Vue3)
    ↕ HTTP/SSE
API 主服务 (FastAPI :8000)
    ├── → Ollama (:11434) [HTTP, 同步/流式]
    ├── → Dify (:8080) [HTTP, SSE 流式]
    ├── → SQLite/PostgreSQL [ORM]
    └── → 多模态处理服务 (:8090) [HTTP, 异步]

BAPS 服务 (FastAPI :8001) [独立]
    └── → Dify (:8080) [通过 OpenAPI tools 集成]

Dify (:8080)
    ├── → Ollama (:11434) [LLM 推理]
    ├── → PostgreSQL (:5432) [Dify 数据]
    ├── → Redis (:6379) [缓存]
    └── → Weaviate [向量检索]
```

---

## 十五、当前状态与下一步规划锚点

### 15.1 已完成清单

| 领域 | 完成项 | 完成度 |
|------|--------|--------|
| **核心引擎** | L2评估引擎、触发器引擎(28个)、多模态融合、Master Agent 数据协议 | 85% |
| **Agent 系统** | Octopus限幅、FSM状态机、Agent基类/注册表/工厂/路由/协作/编排 | 90% |
| **API 后端** | 50+端点: 认证、评估、设备(19)、小程序(17)、编排器(9)、路由(6) | 80% |
| **Dify 集成** | 双模路由(auto/dify/ollama)、SSE流式、多轮对话、健康检查缓存 | 90% |
| **BAPS 评估** | 4问卷(Big5/BPT6/CAPACITY/SPI)、评分引擎、报告生成 | 100% |
| **知识库** | 28触发器定义、3聚类模式、7套行为处方、Agent路由映射 | 100% |
| **数据库** | 14张表: User/Assessment/Trigger/Intervention/Device/Glucose/HR/HRV/Sleep/Activity/Workout/VitalSign/ChatSession/ChatMessage | 100% |
| **测试** | 6个E2E场景(100%通过)、平均9.31ms响应 | 75% |
| **Docker** | 9服务Dify栈、~40GB内存分配 | 60% |
| **H5 前端** | 10页面/4Store/5API模块 | 40% |

### 15.2 已识别的断裂点（供下一步 Agent 开发参考）

| 断裂点 | 当前状态 | 缺失内容 | 影响范围 |
|--------|---------|---------|---------|
| **评估→干预闭环** | 评估可产出 RoutingDecision | 未自动触发对应 Agent 干预 | 核心流程断裂 |
| **Agent 实际执行** | Agent 基础设施就绪 | Agent 内部逻辑为模板/模拟 | A1-A4 无真实推理 |
| **Dify↔Agent 桥接** | Dify对话可用、Agent注册表可用 | 两个系统未连通 | 无法利用 Dify 编排 Agent |
| **设备数据→触发器** | 设备API完整、触发器引擎完整 | 实时数据未流入触发器引擎 | 被动检测而非主动 |
| **BAPS→画像** | BAPS评分完整 | 评估结果未写入 UserMasterProfile | 个性化失效 |
| **处方库→Agent** | 7套处方定义完整 | Agent 未消费处方库 | 处方无法下达 |
| **多模态服务** | Client 代码就绪 | 多模态服务(:8090)未部署 | 文本/信号融合不可用 |
| **前后端集成** | API全通、H5骨架全 | Chat SSE未对接、设备同步未联调 | 用户无法使用 |

### 15.3 下一步 Agent 开发的关键锚点

#### 锚点 1: Agent 实例化与真实推理
- **目标:** 将 4 个 config.yaml 专家(心理/营养/运动/中医) + 4 个 architecture.yaml Agent(A1-A4) 从模板升级为真实 LLM 推理
- **依赖:** 向量知识库构建、系统提示词优化、处方库消费
- **涉及文件:** `agents/factory.py`, `agents/base.py`, config.yaml, 知识库

#### 锚点 2: 评估→Agent 自动路由
- **目标:** AssessmentResult.routing_decision 自动触发对应 Agent 执行
- **依赖:** AgentOrchestrator 接入 AssessmentEngine 输出
- **涉及文件:** `core/assessment_engine.py` → `agents/orchestrator.py`

#### 锚点 3: Dify 工作流编排 Agent
- **目标:** 将 Agent 执行逻辑迁移到 Dify 工作流，实现可视化编排
- **依赖:** Dify Agent Chat App 配置、OpenAPI tools 注册
- **涉及文件:** `api/dify_service.py`, `dify_workflows/`, `api/baps_api.py`(已有 openapi-tools)

#### 锚点 4: 设备数据实时触发
- **目标:** 设备同步后自动运行触发器引擎 → 产出告警/干预
- **依赖:** `device_data.py` sync 端点 → `trigger_engine.py`
- **涉及文件:** `api/device_data.py`, `core/trigger_engine.py`, `core/assessment_engine.py`

#### 锚点 5: BAPS → UserMasterProfile 回写
- **目标:** 评估结果自动更新用户行为画像
- **依赖:** `CoreUserMasterProfile.apply_data_updates()` 机制
- **涉及文件:** `core/master_agent.py`, `api/baps_api.py`, `core/models.py`

#### 锚点 6: 行为处方自动下达
- **目标:** 根据评估结果 + 行为类型 + 准备度，自动匹配并下达处方
- **依赖:** `rx_library.json` + BAPS 输出 + Agent 执行
- **涉及文件:** `models/rx_library.json`, Agent 实现, `core/master_agent.py`

#### 锚点 7: 四阶段培育自动推进
- **目标:** 启动期→适应期→稳定期→内化期 自动阶段推进与策略调整
- **依赖:** CoreCultivationStage + 任务完成数据 + 时间条件
- **涉及文件:** `core/master_agent.py`, `api/miniprogram.py` 任务系统

#### 锚点 8: 前后端完整联调
- **目标:** H5 Chat SSE 对接、设备同步联调、评估结果展示
- **依赖:** 所有 API 稳定
- **涉及文件:** `h5-patient-app/src/api/`, `h5-patient-app/src/stores/`

---

> **本文档最后更新: 2026-01-31**
> **代码版本: commit f2fd215 (feat: add Dify deep integration)**

# 行为处方数字平台 - 核心业务逻辑与专业术语体系

> **文档版本**: v1.0
> **生成日期**: 2026-02-10
> **平台版本**: 行健行为教练多Agent系统 v1.0
> **源代码**: `D:\behavioral-health-project`

---

## 目录

1. [系统总架构](#1-系统总架构)
2. [BAPS 五维评估体系](#2-baps-五维评估体系)
3. [TTM7 七阶段行为改变模型](#3-ttm7-七阶段行为改变模型)
4. [五层次心理准备度模型](#4-五层次心理准备度模型)
5. [行为画像系统](#5-行为画像系统)
6. [行为处方框架](#6-行为处方框架)
7. [四阶段养成模型](#7-四阶段养成模型)
8. [MasterAgent 九步处理流程](#8-masteragent-九步处理流程)
9. [十二专业Agent体系](#9-十二专业agent体系)
10. [多Agent协调与冲突消解](#10-多agent协调与冲突消解)
11. [策略闸门与安全保护](#11-策略闸门与安全保护)
12. [六种隐式数据源](#12-六种隐式数据源)
13. [行为模式识别库](#13-行为模式识别库)
14. [六级四同道者成长体系](#14-六级四同道者成长体系)
15. [专业术语总表](#15-专业术语总表)
16. [系统遗漏与改进方向](#16-系统遗漏与改进方向)

---

## 1. 系统总架构

### 1.1 核心设计原则

```
系统级约束 - 唯一权威原则 (Core Data Schema v1.0)
├── authority_principle: "UserMasterProfile是系统唯一权威用户主画像源"
├── communication_protocol:
│   ├── orchestrator → agent: AgentTask
│   └── agent → orchestrator: AgentResult
├── write_back_channels (3条合法写回通道):
│   ├── AgentResult.data_updates
│   ├── InterventionPlan.adjustment
│   └── CoreDailyTask.feedback
└── write_back_authority: "MasterOrchestrator" (唯一写入者)
```

> **源码**: `core/master_agent_v0.py:33-45` `SYSTEM_CONSTRAINTS`

### 1.2 六个核心数据结构体

| # | 结构体 | 中文名 | 作用 |
|---|--------|--------|------|
| 1 | `CoreUserInput` | 统一输入对象 | 系统所有外部输入的统一入口 |
| 2 | `CoreUserMasterProfile` | 用户主画像 | 全系统唯一权威用户状态对象 |
| 3 | `CoreAgentTask` | Agent任务对象 | Orchestrator到Agent的标准通信 |
| 4 | `CoreAgentResult` | Agent结果对象 | Agent到Orchestrator的返回 |
| 5 | `CoreInterventionPlan` | 干预路径对象 | 从分析到行动的核心桥梁（行为处方） |
| 6 | `CoreDailyTask` | 每日任务对象 | 系统真正产生行为改变的执行出口 |

> **源码**: `core/master_agent_v0.py:166-443`

### 1.3 输入类型

| 枚举值 | 中文 | 说明 |
|--------|------|------|
| `chat` | 对话 | 文本/语音对话输入 |
| `wearable_data` | 可穿戴设备数据 | CGM/HRV/计步器等 |
| `medical_record` | 医疗记录 | 检查报告/化验单 |
| `questionnaire` | 问卷 | BAPS五套问卷 |
| `manual_log` | 手动日志 | 用户手动记录 |

---

## 2. BAPS 五维评估体系

**BAPS** = Behavioral Assessment & Prescription System（行为评估与处方系统）

### 2.1 五套核心问卷

| 维度 | 全称 | 题数 | 评估目标 | 必填性 |
|------|------|------|----------|--------|
| **TTM7** | 改变阶段评估 | 21题 | 判定用户当前行为改变阶段(S0-S6) | **必填** |
| **BIG5** | 大五人格测评 | 50题 | 人格特质(开放性/尽责性/外向性/宜人性/神经质) | 首评建议 |
| **BPT6** | 行为模式分型 | 18题 | 行为类型(action/knowledge/emotion/relation/environment/mixed) | 首评建议 |
| **CAPACITY** | 改变潜力诊断 | 32题 | 8维潜力(信心/觉察/资源/计划/能力/应对/网络/时间/收益) | 首评建议 |
| **SPI** | 成功可能性评估 | 50题 | 加权计算成功概率指数,映射到L1-L5心理层级 | 首评建议 |

> **源码**: `core/baps/scoring_engine.py`, `core/baps/questionnaires.py`, `core/baps/question_bank.json`

### 2.2 评估频率

- **首次评估**: 提交全部5套问卷
- **后续评估**: 仅需TTM7（其他维度从画像中读取）

### 2.3 评分引擎输出

| 问卷 | 输出结构 | 关键字段 |
|------|----------|----------|
| TTM7 | `TTM7Result` | `stage_scores`, `current_stage(S0-S6)`, `sub_scores(AW/WI/AC)`, `stage_confidence` |
| BIG5 | `BigFiveResult` | `dimension_scores`, `personality_profile`, `dominant_traits` |
| BPT6 | `BPT6Result` | `type_scores`, `dominant_types`, `primary_type`, `intervention_strategies` |
| CAPACITY | `CAPACITYResult` | `dimension_scores`, `total_score`, `potential_level`, `weak_dimensions` |
| SPI | `SPIResult` | `spi_score`, `success_level`, `success_rate`, `dimension_analysis` |

> **源码**: `core/baps/scoring_engine.py:19-98`

---

## 3. TTM7 七阶段行为改变模型

### 3.1 阶段定义

| 阶段 | 中文名 | 英文名(Core) | 友好名称 | 描述 |
|------|--------|-------------|----------|------|
| **S0** | 无知无觉 | precontemplation | 探索期 | 未意识到需要改变 |
| **S1** | 强烈抗拒 | contemplation | 思考期 | 知道问题但抗拒改变 |
| **S2** | 被动承受 | - | - | 被动接受但不主动 |
| **S3** | 勉强接受 | preparation | 准备期 | 愿意小步尝试 |
| **S4** | 主动尝试 | action | 成长期 | 主动采取行动 |
| **S5** | 规律践行 | maintenance | 巩固期 | 形成规律习惯 |
| **S6** | 内化为常 | - | 收获期 | 行为成为自然一部分 |

> **源码**: `core/models.py:823-831` `class BehavioralStage`

### 3.2 阶段升级硬条件

阶段升级由 **StageRuntimeBuilder** 唯一负责，遵循严格的硬条件：

| 升级路径 | 条件 | 数据来源 |
|----------|------|----------|
| S0 → S1 | `min_awareness ≥ 0.3` | TTM7评估 |
| S1 → S2 | `min_belief ≥ 0.3, min_awareness ≥ 0.5` | SPI信念分 + TTM7 |
| S2 → S3 | `min_belief ≥ 0.6, min_capability ≥ 0.5` | SPI + CAPACITY |
| S3 → S4 | `min_belief ≥ 0.7, 7天内完成≥3次行为` | SPI + 行为事实 |
| S4 → S5 | `min_belief ≥ 0.8, 连续14天行为记录` | SPI + 连续天数 |
| S5 → S6 | `min_belief ≥ 0.9, 连续60天行为记录` | SPI + 连续天数 |

> **源码**: `configs/spi_mapping.json:3-32` `thresholds`, `core/brain/stage_runtime.py`

### 3.3 关键设计原则

- **只进一阶**: 每次最多升一级，不可跳级
- **唯一写入者**: 只有 `StageRuntimeBuilder` 可写 `current_stage`
- **Agent只提假设**: 其他模块只能提出 `stage_hypothesis`
- **降级无条件**: 降级直接执行（用户退步不需要满足条件）

> **源码**: `core/brain/stage_runtime.py:12-14`

### 3.4 阶段稳定性

| 状态 | 含义 | 触发规则 |
|------|------|----------|
| `stable` | 稳定 | 长期处于当前阶段 |
| `semi_stable` | 半稳定 | 刚升级或有波动 |
| `unstable` | 不稳定 | 存在退步风险 |

> **源码**: `core/models.py:834-838` `class StageStability`

---

## 4. 五层次心理准备度模型

**自研模型** — 替代传统跨理论模型(TTM)的心理准备度评估

### 4.1 层级定义

| 层级 | 中文名 | 英文名 | 核心心理 | SPI系数 | 最大成功率 | 策略 |
|------|--------|--------|----------|---------|-----------|------|
| **L1** | 完全对抗 | Total Resistance | "改变是威胁" | 0.3 | 30% | 安全感建立 |
| **L2** | 抗拒与反思 | Resistance with Reflection | "我不想改变，但开始看见必要性" | 0.5 | 30% | 矛盾处理 |
| **L3** | 妥协与接受 | Selective Acceptance | "改变可能必要，但要可控" | 0.7 | 40-60% | 门槛降低 |
| **L4** | 顺应与调整 | Adaptive Alignment | "改变合理，我愿意适应" | 0.9 | 70-85% | 习惯强化 |
| **L5** | 全面臣服 | Full Internalization | "这不再是改变，而是我的一部分" | 1.0 | 90%+ | 身份巩固 |

> **源码**: `core/schemas/behavior_logic.json:74-178`, `core/models.py:848-854`

### 4.2 SPI → 心理层级映射

| SPI分数范围 | 心理层级 | 标签 |
|-------------|----------|------|
| 0-14 | L1 | 需大量支持 |
| 15-29 | L2 | 需中度支持 |
| 30-49 | L3 | 基本就绪 |
| 50-69 | L4 | 高度就绪 |
| ≥70 | L5 | 自驱型 |

> **源码**: `configs/spi_mapping.json:34-40`

### 4.3 各层级干预策略

| 层级 | 处方核心 | 关键策略 | 禁忌 | 最大任务数 |
|------|----------|----------|------|-----------|
| L1 | 暂不开处方，先建立关系 | 动机性访谈(OARS)、探索价值观、不设目标 | 设定行为目标、强调后果、施压 | 1 |
| L2 | 探索性尝试，低承诺 | 体验式活动、不要求承诺、讨论利弊 | 长期承诺、严格目标、批评现状 | 1 |
| L3 | 微习惯处方，降低门槛 | 微习惯策略、降低门槛、频繁反馈 | 目标过大、一次改太多 | 2 |
| L4 | 系统化行为方案 | 详细行为方案、环境设计、监测机制 | 松懈、忽视波动 | 3 |
| L5 | 自主管理+身份强化 | 社群领导、教授他人、身份叙事 | 过度干预、制造依赖 | 不限 |

> **源码**: `configs/assessment/prescription_strategy_library.json:104-180`

### 4.4 心理层级与行为阶段双向映射

```
L1 ←→ S0(primary), null(secondary)      系数0.3  探索期
L2 ←→ S0(primary), S1(secondary)        系数0.4  思考期
L3 ←→ S1(primary), S2(secondary)        系数0.6  准备期
L4 ←→ S2(primary), S3(secondary)        系数0.85 成长期
L5 ←→ S4(primary), S5(secondary)        系数1.0  收获期
```

> **源码**: `configs/assessment/spi_implicit_mapping_complete.json:13-18`

---

## 5. 行为画像系统

### 5.1 统一行为画像 (BehavioralProfile)

**系统唯一真相源** — 存储用户的行为改变全貌

| 画像维度 | 数据来源 | 关键字段 |
|----------|----------|----------|
| 人口统计 | 注册/补充 | age, gender, height, weight |
| 医疗档案 | 导入/上报 | diagnoses, medications, lab_summary |
| 设备档案 | 自动同步 | cgm_summary, hrv_summary, activity_summary |
| **行为档案** | BAPS评估 | current_stage, motivation_level, self_efficacy, resistance_level |
| 内在需求 | AI提取 | core_needs, emotional_tendencies |
| 风险档案 | 综合评估 | metabolic_risk, cardiovascular_risk, mental_stress |
| 干预状态 | 系统更新 | active_plan_id, adherence_score |
| 历史引用 | 系统记录 | recent_assessments, recent_tasks |

> **源码**: `core/master_agent_v0.py:446-554` `CoreUserMasterProfile`

### 5.2 画像服务 (BehavioralProfileService)

**职责链**:
1. 从BAPS五套问卷结果 → 生成统一BehavioralProfile
2. 阶段判定（基于TTM7）
3. 心理层级判定（基于SPI）
4. 交互模式判定（基于Stage × BPT6 type）
5. 领域需求识别（基于CAPACITY弱项 + Trigger）
6. 部分更新（设备数据触发时）

> **源码**: `core/behavioral_profile_service.py:1-100`

### 5.3 CAPACITY弱项 → 领域映射

| CAPACITY维度 | 行为领域 |
|-------------|----------|
| C_信心 (confidence) | emotion, cognitive |
| A1_觉察 (awareness) | cognitive |
| A2_资源 (resource) | social |
| P_计划 (planning) | nutrition, exercise |
| A3_能力 (ability) | exercise, nutrition |
| C2_应对 (coping) | stress, emotion |
| I_网络 (network) | social |
| T_时间 (time) | exercise, sleep |
| Y_收益 (yield) | cognitive |

> **源码**: `core/behavioral_profile_service.py:45-65`

### 5.4 交互模式

| 模式 | 适用阶段 | 说明 |
|------|----------|------|
| `empathy` (共情) | S0-S1 | 倾听理解，不施压 |
| `challenge` (挑战) | S2-S3(行动型) | 适度激励，引导行动 |
| `execution` (执行) | S4-S6 | 系统规划，执行监督 |

> **源码**: `core/models.py:841-845`, `configs/spi_mapping.json:41-51`

---

## 6. 行为处方框架

### 6.1 行为处方六要素

| # | 要素 | 中文名 | 说明 | 示例 | 必填 |
|---|------|--------|------|------|------|
| 1 | `target_behavior` | 目标行为 | 具体要做什么 | 每天晚餐后散步30分钟 | **是** |
| 2 | `frequency_dose` | 频次剂量 | 多久做一次，做多少 | 每周5-7次，每次30分钟 | **是** |
| 3 | `time_place` | 时间地点 | 何时何地做 | 19:30-20:00，小区花园 | **是** |
| 4 | `trigger_cue` | 启动线索 | 用什么提醒自己 | 吃完饭看到运动鞋就出门 | **是** |
| 5 | `obstacle_plan` | 障碍预案 | 遇到困难怎么办 | 下雨天改为室内原地踏步 | **是** |
| 6 | `support_resource` | 支持资源 | 谁或什么帮助你 | 约邻居一起走，用手机记步 | 否 |

> **源码**: `configs/assessment/prescription_strategy_library.json:55-100`

### 6.2 SMART目标设定规则（基于SPI分数）

| SPI范围 | 难度等级 | 强度系数 | 目标示例 |
|---------|----------|----------|----------|
| ≥70 | challenging | 1.0 | 3个月减重8%、每周运动5次 |
| 50-69 | moderate | 0.7 | 1个月减重3%、每周运动3次 |
| 30-49 | easy | 0.4 | 每天多走1000步、每餐多吃一口菜 |
| <30 | minimal | 0.2 | 每天记录心情、每周了解一个健康知识 |

> **源码**: `configs/assessment/prescription_strategy_library.json:14-52`

### 6.3 行为处方库 (rx_library)

**8大处方类别**:

| 类别代码 | 中文名 | 示例处方 |
|----------|--------|----------|
| `sleep_regulation` | 睡眠调节 | RX-SLEEP-001 睡眠质量改善基础方案 |
| `stress_management` | 压力管理 | 压力释放、放松训练 |
| `exercise_habit` | 运动养成 | 运动习惯建立方案 |
| `nutrition_management` | 营养管理 | 饮食结构调整方案 |
| `emotional_regulation` | 情绪调节 | 情绪管理技能训练 |
| `tcm_wellness` | 中医养生 | 体质调理方案 |
| `social_connection` | 社交连接 | 社交行为扩展方案 |
| `cognitive_improvement` | 认知提升 | 健康认知提升方案 |

每个处方包含**三阶段策略**:
- **意向期 (intention)**: L1-L2, 建立改变意愿，降低防御
- **准备期 (preparation)**: L3, 降低行动门槛，提供成功体验
- **行动期 (action)**: L4-L5, 强化习惯，系统化改善

每阶段包含: `tone`(语气) + `script`(话术) + `do/dont`(可做/禁忌) + `advice`(建议)

> **源码**: `models/rx_library.json`

---

## 7. 四阶段养成模型

### 7.1 阶段定义

| 阶段 | 英文 | 时间范围 | 核心目标 | 行动数上限 |
|------|------|----------|----------|-----------|
| **启动期** | startup | 1-2周 | 建立打卡习惯 | 最少(降难度+增监测) |
| **适应期** | adaptation | 3-8周 | 巩固行为、应对障碍 | 逐步增加 |
| **稳定期** | stability | 2-4月 | 减少外部依赖 | 减少监测 |
| **内化期** | internalization | 4月+ | 行为成为自然一部分 | 自主管理 |

> **源码**: `core/master_agent_v0.py:154-159` `CoreCultivationStage`

### 7.2 阶段特征与策略调整

| 阶段 | 策略调整 | 任务特征 |
|------|----------|----------|
| 启动期 | 降低难度，增加教育类行动，确保有监测行动 | 微任务(深呼吸3次/5分钟正念) |
| 适应期 | 逐步增加挑战难度 | 增加行为数量/时长 |
| 稳定期 | 减少提醒，增加自主性，移除部分监测行动 | 减少外部干预 |
| 内化期 | 最小干预，社群角色转换 | 自发维持+帮助他人 |

> **源码**: `core/master_agent_v0.py:6020-6077`

---

## 8. MasterAgent 九步处理流程

### 8.1 完整流水线

```
┌─────────────────────────────────────────────────────────────────┐
│                    MasterAgent 9步处理流程                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1-2: 用户输入 → Orchestrator接收请求                       │
│       ↓                                                          │
│  Step 3: 更新 UserMasterProfile (统一用户主画像)                  │
│       ↓                                                          │
│  Step 4: AgentRouter 判别问题类型与风险优先级                     │
│       ↓                                                          │
│  Step 4.5: InsightGenerator 生成数据洞察                         │
│       ↓                                                          │
│  Step 5: 调用 1-2个专业Agent (代谢/睡眠/情绪等)                  │
│       ↓                                                          │
│  Step 6: MultiAgentCoordinator 统一上下文 + 整合各Agent结果       │
│       ↓                                                          │
│  Step 7: InterventionPlanner 生成个性化行为干预路径 (核心模块)    │
│       ↓                                                          │
│  Step 8: ResponseSynthesizer 统一教练风格 + 输出给用户            │
│       ↓                                                          │
│  Step 9: 写回 UserMasterProfile + 生成今日任务/追踪点             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

> **源码**: `core/master_agent_v0.py:4965-5050` `MasterAgent.process()`

### 8.2 数据流验证器 (9步校验)

| 步骤 | 描述 |
|------|------|
| 1 | UserInput进入系统 |
| 2 | Orchestrator解析输入，更新UserMasterProfile基础字段 |
| 3 | Router基于Profile+Intent生成1-2个AgentTask |
| 4 | 各AGENT返回AgentResult |
| 5 | Multi-Agent Coordinator融合多个AgentResult |
| 6 | Intervention Planner读取Profile+AgentResult生成InterventionPlan |
| 7 | Planner生成DailyTask |
| 8 | Response Synthesizer输出对话+任务 |
| 9 | 执行反馈写回DailyTask和UserMasterProfile |

> **源码**: `core/master_agent_v0.py:564-574` `CoreDataFlowValidator.PIPELINE_STEPS`

---

## 9. 十二专业Agent体系

### 9.1 Agent分类

#### 9.1.1 专科Agent (9个)

| Agent | 中文名 | 领域 | 关键词 | 数据字段 | 优先级 |
|-------|--------|------|--------|----------|--------|
| CrisisAgent | 危机干预 | crisis | 自杀/自残/不想活 | - | **0(最高)** |
| SleepAgent | 睡眠专家 | sleep | 睡眠/失眠/早醒/熬夜 | sleep | 2 |
| GlucoseAgent | 血糖管理 | glucose | 血糖/糖尿病/胰岛素 | cgm | 1 |
| StressAgent | 压力管理 | stress | 压力/焦虑/紧张 | hrv | 2 |
| NutritionAgent | 营养指导 | nutrition | 饮食/营养/减肥/热量 | - | 3 |
| ExerciseAgent | 运动指导 | exercise | 运动/健身/步数 | activity | 3 |
| MentalHealthAgent | 心理咨询 | mental | 情绪/抑郁/心情 | - | 2 |
| TCMWellnessAgent | 中医养生 | tcm | 中医/体质/穴位/气血 | - | 4 |
| MotivationAgent | 动机管理 | motivation | - | - | - |

#### 9.1.2 整合型Agent (3个)

| Agent | 中文名 | 领域 | 关键词 | 说明 |
|-------|--------|------|--------|------|
| BehaviorRxAgent | 行为处方师 | behavior_rx | 行为处方/习惯/戒烟/依从性 | 跨全领域综合干预输出 |
| WeightAgent | 体重管理师 | weight | 体重/减重/BMI/脂肪 | 多系统联动(饮食+运动+代谢+睡眠+心理) |
| CardiacRehabAgent | 心脏康复师 | cardiac_rehab | 心脏/心血管/冠心病/康复 | 全方位康复方案 |

> **源码**: `core/master_agent_v0.py:3657-3731` `AgentRouter.AGENTS`

### 9.2 领域关联网络

```
专科Agent关联 (最直接的交叉领域):
  sleep     → [glucose, stress, mental, exercise]
  glucose   → [sleep, nutrition, exercise, weight, stress]
  stress    → [sleep, mental, exercise, cardiac_rehab]
  nutrition → [glucose, exercise, weight, tcm]
  exercise  → [glucose, stress, sleep, weight, cardiac_rehab]
  mental    → [stress, sleep, behavior_rx, motivation]
  tcm       → [nutrition, sleep, mental, stress]
  crisis    → [mental, stress, behavior_rx]

整合型Agent关联 (全领域):
  behavior_rx   → [mental, motivation, nutrition, exercise, sleep, glucose, weight, tcm, stress]
  weight        → [nutrition, exercise, glucose, sleep, mental, motivation, behavior_rx, tcm]
  cardiac_rehab → [exercise, stress, sleep, nutrition, mental, glucose, weight, motivation, behavior_rx]
```

> **源码**: `core/master_agent_v0.py:3740-3788` `DOMAIN_CORRELATIONS`

### 9.3 路由优先级规则

1. **危机状态** → CrisisAgent (强制最高优先级)
2. **风险等级** → 对应专业Agent
3. **意图关键词** → 匹配领域Agent
4. **用户偏好** → preferences.focus
5. **设备数据** → 有数据的领域Agent
6. **领域关联** → 加入相关协同Agent

> **源码**: `core/master_agent_v0.py:3643-3654` `AgentRouter`

---

## 10. 多Agent协调与冲突消解

### 10.1 Agent权重体系

| Agent | 基础权重 | 说明 |
|-------|----------|------|
| CrisisAgent | 1.0 | 危机处理最高权重 |
| GlucoseAgent | 0.9 | 血糖管理高权重 |
| SleepAgent | 0.85 | - |
| StressAgent | 0.85 | - |
| MentalHealthAgent | 0.85 | - |
| NutritionAgent | 0.8 | - |
| ExerciseAgent | 0.8 | - |
| TCMWellnessAgent | 0.75 | 最低基础权重 |

实际权重 = `base_weight × confidence`

> **源码**: `core/master_agent_v0.py:4076-4084`

### 10.2 冲突类型

| 类型 | 说明 | 示例 |
|------|------|------|
| `contradiction` | 观点矛盾 | A说增加运动，B说减少活动 |
| `overlap` | 建议重叠 | 多个Agent都建议改善睡眠 |
| `priority` | 优先级冲突 | 紧急建议 vs 长期建议 |

### 10.3 冲突消解规则

| 冲突对 | 优先方 | 原因 |
|--------|--------|------|
| glucose vs nutrition | glucose | 血糖管理优先于营养 |
| sleep vs exercise | sleep | 睡眠优先于运动 |
| stress vs exercise | stress | 压力管理优先于运动 |
| mental vs exercise | mental | 心理优先于运动 |

> **源码**: `core/master_agent_v0.py:4101-4107`

### 10.4 协调9步

1. 分配权重 → 2. 检测冲突 → 3. 消解冲突 → 4. 融合Findings → 5. 融合Recommendations → 6. 确定综合风险等级 → 7. 计算综合置信度 → 8. 提取共识/分歧 → 9. 生成摘要

> **源码**: `core/master_agent_v0.py:4109-4169`

---

## 11. 策略闸门与安全保护

### 11.1 RuntimePolicyGate (策略闸门)

**核心原则**: 所有干预决策必须经过策略闸门

### 11.2 决策类型

| 决策 | 含义 | 允许干预 |
|------|------|----------|
| `ALLOW` | 正常允许 | 是 |
| `DELAY` | 延迟(状态不稳定) | **否** |
| `ALLOW_SOFT_SUPPORT` | 只允许共情/软支持 | 是(受限) |
| `ESCALATE_COACH` | 升级到教练 | 是(需教练) |
| `DENY` | 拒绝 | **否** |

### 11.3 规则链 (按优先级)

| # | 条件 | 决策 | 原因 |
|---|------|------|------|
| 1 | 不稳定态 + 强干预请求 | DELAY | 保护不稳定用户 |
| 2 | S0-S1阶段 | ALLOW_SOFT_SUPPORT | 早期阶段禁止challenge/execution |
| 3 | dropout_risk + S3+ | ESCALATE_COACH | 有退出风险需教练介入 |
| 4 | relapse_risk | ALLOW_SOFT_SUPPORT | 复发风险下只允许软支持 |
| 5 | 其余 | ALLOW | 正常放行 |

> **源码**: `core/brain/policy_gate.py:43-100`

### 11.4 风险等级

| 等级 | 英文 | 处理方式 |
|------|------|----------|
| **危急** | CRITICAL | 需要立即干预(CrisisAgent强制) |
| **高风险** | HIGH | 优先处理，共情风格 |
| **中等** | MODERATE | 常规处理 |
| **低风险** | LOW | 维护性干预 |

> **源码**: `core/master_agent_v0.py:52-57` `class RiskLevel`

---

## 12. 六种隐式数据源

平台通过以下6种渠道隐式采集用户行为数据，无需用户主动填写问卷即可动态更新画像：

| # | 数据源 | ID | 数据库表 | 更新频率 | 采集窗口 | 采集字段 |
|---|--------|-----|----------|----------|----------|----------|
| 1 | 对话内容分析 | CONV | chat_messages | 实时 | 14天 | text, sentiment, intent, keywords, emotion_score |
| 2 | 任务执行表现 | TASK | user_tasks | 每日 | 30天 | completion_rate, streak_days, skip_count, avg_completion_time |
| 3 | 可穿戴设备数据 | DEVICE | health_data | 实时 | 7天 | cgm_value, hrv_sdnn, steps, sleep_hours |
| 4 | 触发事件历史 | TRIGGER | trigger_records | 实时 | 30天 | trigger_id, trigger_count, risk_level |
| 5 | 交互行为模式 | INTERACT | user_activity | 每日 | 14天 | daily_active_time, message_count, response_latency |
| 6 | 用户画像提取 | PROFILE | user_profile | 检测时 | 90天 | stated_goals, value_keywords, identity_expressions |

> **源码**: `configs/assessment/spi_implicit_mapping_complete.json:30-80`

---

## 13. 行为模式识别库

### 13.1 五种核心行为模式

| 模式 | 中文名 | 核心描述 | 关键指标 | 推荐专家 |
|------|--------|----------|----------|----------|
| `overcompensation` | 过度补偿型 | 通过过度行为弥补不安全感 | hrv_sdnn低, 焦虑高, 精力-情绪差异大 | 心理+营养 |
| `stress_avoidance` | 应激逃避型 | 面对压力选择回避和退缩 | hrv_sdnn低, 压力高, 活动量低, 社交少 | 心理+运动康复 |
| `somatization` | 躯体化型 | 心理压力通过身体症状表现 | scl90高, hrv低, 疼痛多, 频繁就医 | 心理+中医 |
| `emotional_dysregulation` | 情绪失调型 | 情绪波动大，难以自我调节 | 情绪变异高, 焦虑/抑郁高, hrv_rmssd低 | 心理 |
| `balanced` | 平衡型 | 身心状态相对平衡稳定 | hrv正常, 焦虑低, 精力好, 睡眠好 | 营养+中医 |

> **源码**: `core/schemas/behavior_logic.json:6-72`

### 13.2 BPT-6 行为分型

| 类型 | 中文特征 | 首选领域 |
|------|----------|----------|
| `action` | 行动型 | exercise, nutrition |
| `knowledge` | 知识型 | cognitive, nutrition |
| `emotion` | 情感型 | emotion, stress |
| `relation` | 关系型 | social, emotion |
| `environment` | 环境型 | sleep, nutrition |
| `mixed` | 混合型 | nutrition, exercise, sleep |

> **源码**: `core/behavioral_profile_service.py:68-75`

---

## 14. 六级四同道者成长体系

### 14.1 等级定义

| 等级 | 中文名 | 角色 | 图标 |
|------|--------|------|------|
| L0 | 观察员 | observer | 👀 |
| L1 | 成长者 | grower | 🌱 |
| L2 | 分享者 | sharer | 💬 |
| L3 | 教练 | coach | 🎓 |
| L4 | 推广者 | promoter | 🚀 |
| L5 | 大师 | master | 👑 |

### 14.2 升级门槛 (三维积分)

| 升级路径 | 成长积分 | 贡献积分 | 影响积分 | 考试 | 同道者要求 |
|----------|----------|----------|----------|------|-----------|
| L0→L1 | 100 | - | - | - | - |
| L1→L2 | 500 | 50 | - | - | - |
| L2→L3 | 800 | 200 | 50 | 需要 | 4个L1成长者 |
| L3→L4 | 1500 | 600 | 200 | 需要 | 4个L2分享者 |
| L4→L5 | 3000 | 1500 | 600 | 需要 | 4个L3教练 |

> **源码**: `api/paths_api.py:31-52`

### 14.3 三维积分体系

| 维度 | 中文名 | 获取方式 |
|------|--------|----------|
| growth | 成长积分 | 学习时长、完成课程、通过测验 |
| contribution | 贡献积分 | 分享内容、帮助他人、答疑解惑 |
| influence | 影响积分 | 发展同道者、指导学员、社区影响力 |

---

## 15. 专业术语总表

### 15.1 系统核心概念

| 中文术语 | 英文术语 | 定义 |
|----------|----------|------|
| 行为处方 | Behavioral Prescription (Rx) | 基于用户画像和评估结果生成的个性化行为干预方案 |
| 行为画像 | Behavioral Profile | 用户行为改变状态的统一数据画像 |
| 用户主画像 | User Master Profile | 系统唯一权威的用户状态对象 |
| 行为改变阶段 | Behavioral Change Stage | TTM7评估出的S0-S6七个行为改变阶段 |
| 心理准备度 | Psychological Readiness Level | 基于SPI评估的L1-L5五层心理准备状态 |
| 干预路径 | Intervention Plan | 从评估到行动的桥梁，包含领域干预方案 |
| 策略闸门 | Policy Gate | 所有干预决策必须通过的安全审查机制 |
| 养成阶段 | Cultivation Stage | 行为养成的四个时间阶段(启动/适应/稳定/内化) |

### 15.2 评估工具

| 术语 | 全称 | 说明 |
|------|------|------|
| BAPS | Behavioral Assessment & Prescription System | 五维评估与处方系统 |
| TTM7 | Transtheoretical Model 7-Stage | 七阶段改变模型评估(21题) |
| BIG5 | Big Five Personality | 大五人格测评(50题) |
| BPT6 | Behavioral Pattern Typing 6 | 行为模式六型分类(18题) |
| CAPACITY | Change Ability Potential Index | 改变潜力8维诊断(32题) |
| SPI | Success Possibility Index | 成功可能性加权评估(50题) |

### 15.3 交互与干预

| 术语 | 说明 |
|------|------|
| 共情模式 (Empathy) | S0-S1阶段使用，倾听理解不施压 |
| 挑战模式 (Challenge) | S2-S3行动型使用，适度激励引导 |
| 执行模式 (Execution) | S4-S6阶段使用，系统规划执行监督 |
| SMART目标 | Specific/Measurable/Achievable/Relevant/Time-bound |
| 微习惯 (Micro Habit) | 最小可行行为单元，降低行动门槛 |
| 动机性访谈 (MI) | Motivational Interviewing, OARS技术 |
| OARS | 开放问题/肯定/反映/总结 - MI核心技术 |

### 15.4 技术架构

| 术语 | 说明 |
|------|------|
| MasterAgent | 中枢控制器，串联9步处理流程 |
| AgentRouter | Agent路由器，基于意图/风险选择Agent |
| MultiAgentCoordinator | 多Agent协调器，冲突消解与结果融合 |
| InterventionPlanner | 干预规划器，生成行为干预路径 |
| ResponseSynthesizer | 响应合成器，统一教练风格输出 |
| StageRuntimeBuilder | 阶段运行态引擎，唯一可写current_stage |
| RuntimePolicyGate | 策略闸门，所有干预必须过闸 |
| InterventionMatcher | 领域干预匹配引擎，加载rx_library |
| BehavioralProfileService | 行为画像服务，BAPS→统一画像 |
| BAPSScoringEngine | BAPS评分引擎，四大问卷评分算法 |

### 15.5 角色与成长

| 术语 | 说明 |
|------|------|
| 六级体系 | 观察员→成长者→分享者→教练→推广者→大师 |
| 四同道者 | 升级需培养4个达到指定等级的同道者 |
| 三维积分 | 成长积分 + 贡献积分 + 影响积分 |
| 同道者 (Companion) | 由高级别用户引导的学习伙伴 |

---

## 16. 系统遗漏与改进方向

### 16.1 已识别的系统缺口

| # | 类别 | 缺口描述 | 影响 | 建议 |
|---|------|----------|------|------|
| 1 | **评估** | TTM7问卷21题固定，缺乏自适应出题机制 | 用户重测体验差 | 引入CAT(计算机自适应测试) |
| 2 | **评估** | BAPS五套问卷首评题量过大(171题)，可能导致放弃 | 首评完成率低 | 分阶段评估，先TTM7+SPI(71题)，后续补充 |
| 3 | **画像** | 行为事实服务(BehaviorFactsService)依赖的表尚未完全实现 | 阶段升级条件部分为默认值 | 实现trigger_records表和user_activity表 |
| 4 | **Agent** | 12个Agent均为规则引擎实现，未接入LLM自然语言推理 | 建议生成较模板化 | 接入Ollama/Dify生成个性化建议 |
| 5 | **协调** | 冲突消解仅基于关键词匹配，无语义理解 | 可能遗漏深层矛盾 | 引入嵌入向量语义相似度 |
| 6 | **处方** | rx_library目前8类处方库，部分类别仅有1个处方模板 | 选择范围有限 | 扩充每类3-5个处方 |
| 7 | **闸门** | PolicyGate规则固定，缺乏自学习/调参机制 | 无法根据效果反馈优化 | 增加A/B测试和效果追踪 |
| 8 | **设备** | 设备数据整合仅支持CGM/HRV/计步/睡眠4类 | 无法利用血压/体温等 | 扩展DeviceProfile支持更多数据类型 |
| 9 | **纵向** | 缺乏纵向效果追踪系统(阶段转换历史/干预效果统计) | 无法量化平台干预有效性 | 建立InterventionOutcome模型 |
| 10 | **社交** | 同道者关系仅有数量统计，缺乏交互质量评估 | 同道者可能名存实亡 | 增加交互频率/质量维度 |
| 11 | **隐式** | 6种隐式数据源中conversation和interaction的自动分析管道未实现 | 对话情感/意图提取为手动 | 实现NLP自动情感/意图提取 |
| 12 | **安全** | 危机Agent缺乏与外部紧急服务(如心理热线)的联动机制 | 真实危机场景应对不足 | 接入外部危机干预API |

### 16.2 架构改进建议

1. **评估-画像-干预闭环强化**: 目前干预计划生成后缺乏系统性的效果追踪回路
2. **Agent LLM化**: 将规则引擎Agent升级为LLM驱动，利用已有的RAG知识库
3. **渐进式评估**: 允许用户分多次完成BAPS评估，每次10-15分钟
4. **多模态输入**: 支持语音情感分析、面部表情识别(已有食物识别基础)
5. **社区激励闭环**: 将V003激励系统与行为处方系统深度集成

---

## 附录: 关键源码索引

| 模块 | 文件路径 | 关键内容 |
|------|----------|----------|
| 中枢Agent | `core/master_agent_v0.py` | 9步流程、12个Agent、路由器、协调器 |
| Agent入口 | `core/master_agent.py` | 从v0导入，保持兼容 |
| BAPS评分 | `core/baps/scoring_engine.py` | 四大问卷评分算法 |
| 问卷定义 | `core/baps/questionnaires.py` | 五套问卷结构定义 |
| 题库 | `core/baps/question_bank.json` | 问卷原始题库 |
| 行为画像服务 | `core/behavioral_profile_service.py` | BAPS→统一画像 |
| 阶段运行态 | `core/brain/stage_runtime.py` | 唯一写current_stage |
| 策略闸门 | `core/brain/policy_gate.py` | 干预安全审查 |
| 干预匹配器 | `core/intervention_matcher.py` | 领域干预匹配 |
| 行为处方库 | `models/rx_library.json` | 8类行为处方模板 |
| 处方策略库 | `configs/assessment/prescription_strategy_library.json` | L1-L5策略+处方六要素 |
| SPI映射 | `configs/spi_mapping.json` | 阶段阈值+层级映射+交互模式 |
| 隐式数据映射 | `configs/assessment/spi_implicit_mapping_complete.json` | 6种隐式数据源 |
| 行为逻辑库 | `core/schemas/behavior_logic.json` | 行为模式+心理准备度 |
| 评估管道API | `api/assessment_pipeline_api.py` | 6步评估流水线 |
| 数据模型 | `core/models.py` | 70个SQLAlchemy模型 |
| 等级体系 | `api/paths_api.py` | 6级4同道者门槛 |

---

> **本文档由平台源码自动提取生成，涵盖行为处方系统的完整业务逻辑链路。**

# Agent 架构全景审计与规划建议

> 版本: v1.0 | 日期: 2026-02-14 | 基于代码实际提取，非推测

---

## 目录

1. [Agent 体系总览](#1-agent-体系总览)
2. [Layer 1: 12 核心 Agent 详细规格](#2-layer-1-12-核心-agent-详细规格)
3. [Layer 2: BehaviorRx 专家 Agent（4个）](#3-layer-2-behaviorrx-专家-agent4个)
4. [Layer 3: 动态模板 Agent](#4-layer-3-动态模板-agent)
5. [编排与控制体系](#5-编排与控制体系)
6. [Agent 生态系统](#6-agent-生态系统)
7. [关联网络与冲突矩阵](#7-关联网络与冲突矩阵)
8. [问题诊断与规划建议](#8-问题诊断与规划建议)
9. [文件索引](#9-文件索引)

---

## 1. Agent 体系总览

平台当前实现了 **3 层 Agent 架构 + 动态模板扩展**：

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 3: BehaviorRx 专家 Agent (4个)                            │
│  行为处方基座，冰山模型，TTM×BigFive×CAPACITY 三维计算             │
│  BehaviorCoach / MetabolicExpert / CardiacExpert / AdherenceExpert│
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: 整合型 Agent (3个)                                     │
│  跨领域联动：behavior_rx / weight / cardiac_rehab                │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: 专科 Agent (9个)                                       │
│  单领域数据+建议：crisis / glucose / sleep / stress / mental      │
│  / nutrition / exercise / motivation / tcm                       │
├─────────────────────────────────────────────────────────────────┤
│  Dynamic: 模板动态 Agent (GenericLLMAgent)                       │
│  DB模板创建，纯LLM推理，无规则引擎                                │
└─────────────────────────────────────────────────────────────────┘
```

### 数量统计

| 分类 | 数量 | 注册方式 | LLM 调用 |
|------|------|----------|----------|
| 专科 Agent | 9 | AGENT_CLASS_REGISTRY 硬编码 | 8个是(crisis否) |
| 整合 Agent | 3 | AGENT_CLASS_REGISTRY 硬编码 | 全部是 |
| 专家 Agent (BehaviorRx) | 4 | rx_routes 注入 | 引擎计算为主 |
| 动态模板 Agent | 无限 | DB AgentTemplate → GenericLLMAgent | 全部是 |
| **合计** | **16+** | | |

---

## 2. Layer 1: 12 核心 Agent 详细规格

### 2.1 专科 Agent（9个）

#### 2.1.1 CrisisAgent — 危机干预

| 属性 | 值 |
|------|-----|
| **文件** | `core/agents/specialist_agents.py` |
| **Domain** | `AgentDomain.CRISIS` |
| **优先级** | 0（最高） |
| **基础权重** | 1.0 |
| **启用 LLM** | **否**（确定性规则引擎） |
| **关键词** | 自杀, 自残, 不想活, 结束生命, 去死, 跳楼, 割腕, 遗书 |
| **警告关键词** | 活着没意思, 太痛苦了, 撑不下去, 崩溃, 绝望 |
| **设备数据** | 无 |
| **关联领域** | mental, stress, behavior_rx |
| **冲突胜出** | 无（优先级直接覆盖） |

**处理逻辑**：
- 检测到 CRITICAL 关键词 → confidence=1.0, risk=CRITICAL, 立即升级人工
- 检测到 WARNING 关键词 → confidence=0.9, risk=HIGH, 温柔支持+评估
- 否则 → SAFE 状态

**特殊能力**：不走 LLM，纯关键词匹配，确保零延迟响应危机。

---

#### 2.1.2 GlucoseAgent — 血糖管理

| 属性 | 值 |
|------|-----|
| **文件** | `core/agents/specialist_agents.py` |
| **Domain** | `AgentDomain.GLUCOSE` |
| **优先级** | 1 |
| **基础权重** | 0.9 |
| **启用 LLM** | 是 |
| **关键词** | 血糖, 糖尿病, 胰岛素, 低血糖, 高血糖, 糖化, 控糖 |
| **设备数据** | `cgm`（连续血糖监测） |
| **关联领域** | sleep, nutrition, exercise, weight, stress |
| **冲突胜出** | > nutrition |

**System Prompt**：
> 你是一位内分泌科专家，精通血糖管理、胰岛素抵抗和代谢综合征。根据用户的血糖数据和饮食运动情况，给出具体的血糖管理建议。回复控制在3-5条建议，每条不超过30字。只输出建议列表，不要寒暄。

**处理逻辑**：
- CGM > 10.0 mmol/L → "血糖偏高", "餐后30分钟轻度活动", risk=LOW
- CGM < 3.9 mmol/L → "低血糖警告", "立即补充15g速效碳水", risk=HIGH
- 生成任务：post_meal_walk

---

#### 2.1.3 SleepAgent — 睡眠专家

| 属性 | 值 |
|------|-----|
| **文件** | `core/agents/specialist_agents.py` |
| **Domain** | `AgentDomain.SLEEP` |
| **优先级** | 2 |
| **基础权重** | 0.85 |
| **启用 LLM** | 是 |
| **关键词** | 睡眠, 失眠, 早醒, 熬夜, 睡不着, 嗜睡, 打鼾, 午睡 |
| **设备数据** | `sleep`（睡眠时长） |
| **关联领域** | glucose, stress, mental, exercise |
| **冲突胜出** | > exercise |

**System Prompt**：
> 你是一位睡眠医学专家，擅长认知行为疗法(CBT-I)、睡眠卫生指导和昼夜节律调节。请用温暖专业的语气，根据用户的睡眠数据和主诉，给出具体可操作的改善建议。回复控制在3-5条建议，每条不超过30字。只输出建议列表，不要寒暄。

**处理逻辑**：
- sleep < 6h → "睡眠不足", "制定睡前90分钟断屏计划", risk=MODERATE
- sleep > 9h → "睡眠过长", "排查抑郁倾向"
- 含"失眠"/"睡不着" → "CBT-I: 睡眠限制+刺激控制"
- 能力：睡眠日记任务、睡眠卫生指导

---

#### 2.1.4 StressAgent — 压力管理

| 属性 | 值 |
|------|-----|
| **文件** | `core/agents/specialist_agents.py` |
| **Domain** | `AgentDomain.STRESS` |
| **优先级** | 2 |
| **基础权重** | 0.85 |
| **启用 LLM** | 是 |
| **关键词** | 压力, 焦虑, 紧张, 烦躁, 崩溃, 喘不过气 |
| **设备数据** | `hrv`（心率变异性） |
| **关联领域** | sleep, mental, exercise, cardiac_rehab |
| **冲突胜出** | > exercise |

**System Prompt**：
> 你是一位心理健康专家，擅长压力管理、正念减压和自主神经调节。根据用户的HRV数据和压力表达，给出放松和应对策略。回复控制在3-5条建议，每条不超过30字。只输出建议列表，不要寒暄。

**处理逻辑**：
- HRV SDNN < 30ms → "HRV偏低，交感神经过度激活", "4-7-8呼吸法+5分钟正念冥想", risk=MODERATE
- 含"压力"/"焦虑"/"紧张" → "识别压力源，建立压力应对清单"

---

#### 2.1.5 MentalHealthAgent — 心理咨询

| 属性 | 值 |
|------|-----|
| **文件** | `core/agents/specialist_agents.py` |
| **Domain** | `AgentDomain.MENTAL` |
| **优先级** | 2 |
| **基础权重** | 0.85 |
| **启用 LLM** | 是 |
| **关键词** | 情绪, 抑郁, 心情, 难过, 伤心, 郁闷, 无助 |
| **设备数据** | 无 |
| **关联领域** | stress, sleep, behavior_rx, motivation |
| **冲突胜出** | > exercise |

**System Prompt**：
> 你是一位心理咨询师，擅长认知行为疗法、情绪管理和心理韧性训练。根据用户的情绪表达和心理状态，给出专业的心理支持建议。回复控制在3-5条建议，每条不超过30字。只输出建议列表，不要寒暄。

**处理逻辑**：
- 含"抑郁"/"无助"/"绝望" → "PHQ-9筛查+寻求专业心理支持", risk=MODERATE
- 含"情绪"/"心情"/"郁闷" → "ABC情绪日记"

---

#### 2.1.6 NutritionAgent — 营养指导

| 属性 | 值 |
|------|-----|
| **文件** | `core/agents/specialist_agents.py` |
| **Domain** | `AgentDomain.NUTRITION` |
| **优先级** | 3 |
| **基础权重** | 0.8 |
| **启用 LLM** | 是 |
| **关键词** | 饮食, 营养, 减肥, 热量, 碳水, 蛋白质, 吃什么, 食谱, 代餐, 节食 |
| **设备数据** | 无 |
| **关联领域** | glucose, exercise, weight, tcm |
| **冲突胜出** | 无 |

**System Prompt**：
> 你是一位临床营养师，擅长慢病营养干预、体重管理饮食和功能性食品。根据用户的饮食习惯和健康目标，给出个性化营养建议。回复控制在3-5条建议，每条不超过30字。只输出建议列表，不要寒暄。

**处理逻辑（TTM阶段感知）**：
- S0/S1 → "从饮食记录开始，不做限制，先建立觉察"
- S2/S3 → "控碳先行：主食减1/3，蔬菜先吃，蛋白质加量"
- S4/S5/S6 → "精细化营养方案：根据CGM数据个性化调整"

---

#### 2.1.7 ExerciseAgent — 运动指导

| 属性 | 值 |
|------|-----|
| **文件** | `core/agents/specialist_agents.py` |
| **Domain** | `AgentDomain.EXERCISE` |
| **优先级** | 3 |
| **基础权重** | 0.8 |
| **启用 LLM** | 是 |
| **关键词** | 运动, 健身, 步数, 跑步, 散步, 力量训练, 瑜伽 |
| **设备数据** | `activity`（步数/活动分钟） |
| **关联领域** | glucose, stress, sleep, weight, cardiac_rehab |
| **冲突胜出** | 无（被 sleep/stress/mental 胜出） |

**System Prompt**：
> 你是一位运动医学专家，擅长运动处方、康复训练和体适能评估。根据用户的活动数据和身体状况，给出安全有效的运动建议。回复控制在3-5条建议，每条不超过30字。只输出建议列表，不要寒暄。

**处理逻辑**：
- steps < 5000 → "日步数不足", "每小时起身活动5分钟", risk=LOW
- 生成任务：hourly_walk (5 min)

---

#### 2.1.8 MotivationAgent — 动机管理

| 属性 | 值 |
|------|-----|
| **文件** | `core/agents/specialist_agents.py` |
| **Domain** | `AgentDomain.MOTIVATION` |
| **优先级** | 3 |
| **基础权重** | 0.8 |
| **启用 LLM** | 是 |
| **关键词** | 动力, 坚持, 放弃, 没意义, 为什么, 值不值 |
| **设备数据** | 无 |
| **关联领域** | 无 |
| **冲突胜出** | 无 |

**System Prompt**：
> 你是一位行为改变专家，擅长动机访谈、自我决定理论和习惯养成。根据用户的改变阶段和内在动机状态，给出激励和引导建议。回复控制在3-5条建议，每条不超过30字。只输出建议列表，不要寒暄。

**处理逻辑（TTM阶段感知）**：
- S0/S1 → "探索改变的个人意义，不施压"
- S2/S3 → "动机访谈：探索矛盾，'改变对你意味着什么?'"
- S4/S5/S6 → "身份强化：'你已经是一个注重健康的人了'"

---

#### 2.1.9 TCMWellnessAgent — 中医养生

| 属性 | 值 |
|------|-----|
| **文件** | `core/agents/specialist_agents.py` |
| **Domain** | `AgentDomain.TCM` |
| **优先级** | 4（最低） |
| **基础权重** | 0.75 |
| **启用 LLM** | 是 |
| **关键词** | 中医, 体质, 穴位, 气血, 经络, 养生, 上火, 湿气 |
| **设备数据** | 无 |
| **关联领域** | nutrition, sleep, mental, stress |
| **冲突胜出** | 无 |

**System Prompt**：
> 你是一位中医养生专家，擅长体质辨识、经络调理和药膳食疗。根据用户的体质特征和健康诉求，给出中医养生建议。回复控制在3-5条建议，每条不超过30字。只输出建议列表，不要寒暄。

**处理逻辑**：
- 始终返回 confidence=0.6（较低基线）
- 通用建议："结合体质辨识，提供个性化中医养生建议"

---

### 2.2 整合型 Agent（3个）

#### 2.2.1 BehaviorRxAgent — 行为处方师

| 属性 | 值 |
|------|-----|
| **文件** | `core/agents/integrative_agents.py` |
| **Domain** | `AgentDomain.BEHAVIOR_RX` |
| **优先级** | 2 |
| **基础权重** | 0.9 |
| **启用 LLM** | 是 |
| **关键词** | 行为处方, 习惯, 戒烟, 依从性, 打卡, 任务 |
| **关联领域** | **全覆盖**（mental, motivation, nutrition, exercise, sleep, glucose, weight, tcm, stress） |
| **冲突胜出** | 无 |

**System Prompt**：
> 你是一位行为处方师，擅长跨领域综合干预、微习惯设计和依从性管理。根据用户的行为阶段和各项健康数据，设计渐进式行为处方。回复控制在3-5条建议，每条不超过30字。只输出建议列表，不要寒暄。

**处理逻辑（TTM阶段感知）**：
- S0/S1 → "以觉察为主", task={awareness_task, minimal}
- S2/S3 → "引入1-2个行为处方，强调'试一试'", task={trial_rx, easy}
- S4/S5/S6 → "完整行为处方执行", task={full_rx, moderate}

**定位**：无特定领域匹配时的默认兜底 Agent（fallback_agent）。

---

#### 2.2.2 WeightAgent — 体重管理师

| 属性 | 值 |
|------|-----|
| **文件** | `core/agents/integrative_agents.py` |
| **Domain** | `AgentDomain.WEIGHT` |
| **优先级** | 2 |
| **基础权重** | 0.85 |
| **启用 LLM** | 是 |
| **关键词** | 体重, 减重, BMI, 脂肪, 腰围, 减肥 |
| **关联领域** | **全覆盖**（nutrition, exercise, glucose, sleep, mental, motivation, behavior_rx, tcm） |
| **冲突胜出** | 无 |

**System Prompt**：
> 你是一位体重管理专家，擅长多系统联动减重方案(营养+运动+代谢+睡眠+心理)。根据用户的BMI、体脂和代谢数据，给出综合体重管理建议。回复控制在3-5条建议，每条不超过30字。只输出建议列表，不要寒暄。

**处理逻辑**：
- BMI ≥ 28 → "肥胖范围", "多系统联动：营养控碳+运动增肌减脂+睡眠优化+压力管理", risk=MODERATE
- BMI ≥ 24 → "超重范围", "优先营养调整，配合适度运动"

---

#### 2.2.3 CardiacRehabAgent — 心脏康复师

| 属性 | 值 |
|------|-----|
| **文件** | `core/agents/integrative_agents.py` |
| **Domain** | `AgentDomain.CARDIAC_REHAB` |
| **优先级** | 1 |
| **基础权重** | 0.85 |
| **启用 LLM** | 是 |
| **关键词** | 心脏, 心血管, 冠心病, 康复, 心梗, 支架 |
| **关联领域** | **全覆盖**（exercise, stress, sleep, nutrition, mental, glucose, weight, motivation, behavior_rx） |
| **冲突胜出** | 无 |

**System Prompt**：
> 你是一位心脏康复专家，擅长冠心病康复、运动处方和二级预防。根据用户的心血管病史和当前状态，给出安全的康复建议。回复控制在3-5条建议，每条不超过30字。只输出建议列表，不要寒暄。

**处理逻辑**：
- 诊断含"心"/"冠" → "心血管病史，启动心脏康复路径", "分阶段心脏康复：评估→低强度→渐进→维护", risk=MODERATE
- 安全约束："运动处方须在安全心率区间(HRmax×50-70%)"

---

## 3. Layer 2: BehaviorRx 专家 Agent（4个）

BehaviorRx 是独立于 12 核心 Agent 的 **行为处方基座系统**，在 MasterAgent Step 3.5 注入。

### 3.1 设计哲学：冰山模型

```
┌──────────────────────────────────┐  ← 用户可见
│  领域建议（血糖、运动、服药提醒）   │     "晚饭提前到6:30"
├──────────────────────────────────┤  ← 隐藏层
│  行为处方（策略×强度×节奏×微行动）  │     stimulus_control, moderate
├──────────────────────────────────┤  ← 基座层
│  行为诊断（TTM×BigFive×CAPACITY）  │     S3, high_C, capacity=0.7
└──────────────────────────────────┘
```

### 3.2 四个专家 Agent

#### 3.2.1 BehaviorCoachAgent — 行为阶段教练

| 属性 | 值 |
|------|-----|
| **文件** | `behavior_rx/agents/behavior_coach_agent.py` |
| **类型** | `ExpertAgentType.BEHAVIOR_COACH` |
| **TTM 覆盖** | S0-S2（前意向→准备） |
| **核心职责** | 认知激活、决策支持、就绪评估 |
| **特殊性** | 半透明模型——向用户展示行为科学术语（共情式教练） |

**阶段处理**：
- **S0（前意向期）**：意识提升 + 情绪唤醒
- **S1（意向期）**：认知深化 + 决策平衡 + 自我再评价
- **S2（准备期）**：自我解放 + 承诺 + 认知重构
- **S3+（就绪）**：交接给领域专家

**核心能力**：
- 阶段评估与就绪度判断
- 矛盾正常化（"感到矛盾是OK的"）
- 自我效能感建设
- 阶段回退时紧急接管（所有Agent均可回退到Coach）

---

#### 3.2.2 MetabolicExpertAgent — 代谢内分泌专家

| 属性 | 值 |
|------|-----|
| **文件** | `behavior_rx/agents/metabolic_expert_agent.py` |
| **类型** | `ExpertAgentType.METABOLIC_EXPERT` |
| **TTM 覆盖** | S3+（行动期及以后） |
| **核心职责** | 血糖趋势→行为归因、营养行为处方、运动代谢处方 |

**冰山示例**：
- 用户看到："空腹血糖偏高，试试把晚餐时间提前到6:30"
- 隐藏层：`stimulus_control` 策略, `moderate` 强度, 3天坚持触发奖励

**数据字段**：glucose (fasting_avg, postprandial_avg, hba1c, trend), weight, nutrition, exercise

---

#### 3.2.3 CardiacExpertAgent — 心血管康复专家

| 属性 | 值 |
|------|-----|
| **文件** | `behavior_rx/agents/cardiac_expert_agent.py` |
| **类型** | `ExpertAgentType.CARDIAC_EXPERT` |
| **TTM 覆盖** | 分阶段（Phase I-III） |
| **核心职责** | 运动恐惧脱敏、安全心率锚定、分期康复处方 |

**核心挑战**：打破"恐惧-回避循环"
```
心脏事件 → 运动恐惧 → 体能下降 → 风险升高 → 更恐惧
```

**系统脱敏方案（3周渐进暴露）**：
- Week 1：散步
- Week 2：快走
- Week 3：轻度有氧

**安全护栏**：
- HR超阈值 → 立即停止
- RPE > 14 → 降低强度
- 胸痛/头晕 → 触发 AutoExitHandler
- SBP > 160 mmHg → 暂停运动

---

#### 3.2.4 AdherenceExpertAgent — 就医依从性专家

| 属性 | 值 |
|------|-----|
| **文件** | `behavior_rx/agents/adherence_expert_agent.py` |
| **类型** | `ExpertAgentType.ADHERENCE_EXPERT` |
| **TTM 覆盖** | **横切面**（所有阶段） |
| **触发条件** | medication_missed ≥ 3/7d 或 visit_overdue ≥ 14d 或 adherence < 0.5 |
| **核心理念** | "不依从 = 行为链设计失败"，非患者不配合 |

**五大依从行为**：服药、就诊、检查/化验、饮食医嘱、运动医嘱

**五大障碍 × 策略映射**：

| 障碍类型 | 策略 |
|----------|------|
| 遗忘 | habit_stacking + stimulus_control |
| 恐惧 | cognitive_restructuring + systematic_desensitization |
| 认知偏差 | consciousness_raising + decisional_balance |
| 经济 | self_monitoring + problem_solving |
| 信任 | self_liberation + assertiveness |

---

### 3.3 12 种行为策略

| # | 策略 | 中文名 | TTM 适用 | 证据等级 |
|---|------|--------|---------|----------|
| 1 | CONSCIOUSNESS_RAISING | 意识提升 | S0-S2 | T1 |
| 2 | DRAMATIC_RELIEF | 情绪唤醒 | S0-S1 | T2 |
| 3 | SELF_REEVALUATION | 自我再评价 | S1-S2 | T1 |
| 4 | DECISIONAL_BALANCE | 决策平衡 | S1-S3 | T1 |
| 5 | COGNITIVE_RESTRUCTURING | 认知重构 | S0-S4 | T1 |
| 6 | SELF_LIBERATION | 自我解放 | S2-S3 | T2 |
| 7 | STIMULUS_CONTROL | 刺激控制 | S3-S5 | T1 |
| 8 | CONTINGENCY_MANAGEMENT | 强化管理 | S3-S5 | T1 |
| 9 | HABIT_STACKING | 习惯叠加 | S3-S5 | T2 |
| 10 | SYSTEMATIC_DESENSITIZATION | 系统脱敏 | 变动 | T2 |
| 11 | RELAPSE_PREVENTION | 复发预防 | S4-S6 | T1 |
| 12 | SELF_MONITORING | 自我监测 | S0-S6 | T1 |

### 3.4 协作编排

#### 六大协作场景

| 场景 | 主Agent | 辅Agent | 合并策略 |
|------|---------|---------|----------|
| 新用户评估 | BehaviorCoach | 无 | single_agent |
| 血糖异常 | MetabolicExpert | AdherenceExpert(漏服≥3) | adherence_overlay |
| 运动恐惧 | BehaviorCoach(先) → CardiacExpert(后) | - | coach_first_then_handoff |
| 多病共存 | 当前领域Expert | 全部Expert + Adherence | parallel_merge |
| 阶段回退 | BehaviorCoach(紧急接管) | 当前Agent(暂停) | coach_override |
| 就诊准备 | AdherenceExpert(主导) | Metabolic/Cardiac(数据) | adherence_lead |

#### 交接协议

| 交接类型 | 方向 | 条件 |
|----------|------|------|
| STAGE_PROMOTION | Coach → Domain | stage ≥ 3, readiness ≥ 0.6, stability ≥ 0.5 |
| STAGE_REGRESSION | Domain → Coach | stage 下降 ≥ 2级 |
| EMERGENCY_TAKEOVER | Any → Coach | efficacy < 0.2, stability < 0.3 |
| CROSS_CUTTING | Any → Adherence | medication_missed ≥ 3 或 visit_overdue ≥ 14d |
| DOMAIN_COORDINATION | Metabolic ↔ Cardiac | 检测到共病 |

---

## 4. Layer 3: 动态模板 Agent

### 4.1 GenericLLMAgent

| 属性 | 值 |
|------|-----|
| **文件** | `core/agents/generic_llm_agent.py` |
| **用途** | DB 模板创建的纯 LLM Agent，无规则引擎 |
| **默认 confidence** | 0.6 |
| **默认 risk** | LOW |

**实例化**：从 `AgentTemplate` 行读取所有属性（agent_id, display_name, keywords, system_prompt, priority...）→ 构建 Agent 实例。

**处理流程**：
1. 返回基础 AgentResult (confidence=0.6, risk=LOW)
2. 如果 enable_llm=True 且 system_prompt 存在 → 调用 `_enhance_with_llm()` 生成建议
3. 否则 → 返回默认建议

### 4.2 模板数据结构

```
AgentTemplate (19 columns):
├── agent_id (unique, ^[a-z][a-z0-9_]{2,31}$)
├── display_name, description
├── agent_type: specialist | integrative | dynamic_llm
├── domain_enum: AgentDomain enum or null
├── keywords: list[str] (JSON)
├── data_fields: list[str]
├── correlations: list[str]
├── priority: 0-10
├── base_weight: 0.0-1.0
├── enable_llm: bool
├── system_prompt: str
├── conflict_wins_over: list[str]
├── is_preset: bool
├── is_enabled: bool
├── created_by, created_at, updated_at
```

### 4.3 专家自建 Agent 流程

```
Expert → POST /tenants/{tid}/my-agents
       → agent_id = "{tenant_slug}_{name_suffix}"
       → 创建 AgentTemplate (dynamic_llm) + TenantAgentMapping
       → 更新 ExpertTenant.enabled_agents
       → 清除缓存 + reset_agent_master()
```

---

## 5. 编排与控制体系

### 5.1 双 MasterAgent 架构

| 版本 | 文件 | 入口 | 特性 |
|------|------|------|------|
| **v0** | `core/master_agent_v0.py` | `get_master_agent()` | 原始9步编排器，无模板/租户支持 |
| **v6** | `core/agents/master_agent.py` | `get_agent_master()` | 模板感知，租户路由，PolicyEngine集成 |

**运行时优先级**：v6 (优先) → v0 (兜底) → mock (最终兜底)

### 5.2 v6 MasterAgent 9步流水线

```
Step 1-2:  输入构建 → AgentInput
Step 2.5:  ★ SafetyPipeline L1 — 输入过滤（关键词/PII/意图）
           → crisis+critical → 立即 CrisisAgent 响应
           → blocked → 拒绝回复
Step 3:    UserMasterProfile 更新（外部）
Step 3.5:  ★ ExpertAgentRouter — BehaviorRx 注入点
           → 检查领域数据/TTM阶段/关键词 → CollaborationOrchestrator
Step 4:    路由选择
           ├── PolicyEngine.evaluate() (优先，V007)
           │   → ExecutionPlan: primary_agent + secondary_agents + model
           └── AgentRouter.route() (兜底)
               → 关键词匹配 + 设备数据 + 关联网络 → 1-2个 Agent
Step 4.5:  洞察生成 — 设备数据异常提取
           → CGM>10, HRV<30, sleep<6, steps<5000
Step 5:    Agent 执行 — 1-2个 Agent 并行调用
           → agent.process(agent_input) → AgentResult
Step 6:    多Agent协调 — MultiAgentCoordinator 9步算法
           → 权重分配 → 冲突检测 → 冲突解决 → 发现合并
           → 建议合并 → 风险取最高 → 置信度加权 → 共识提取 → 摘要
Step 7:    策略门控 — RuntimePolicyGate
           → allow | delay | allow_soft | escalate_coach | deny
Step 7.5:  ★ SafetyPipeline L3 — 生成约束注入
Step 8:    响应合成 — LLM合成 (cloud→Ollama) → 模板兜底
Step 8.5:  ★ SafetyPipeline L4 — 输出过滤（医学声明/免责声明）
Step 9:    任务分配 + 响应返回
```

### 5.3 AgentRouter 路由评分规则

| 优先级 | 规则 | 分值 | 条件 |
|--------|------|------|------|
| 0 | 危机强制 | 200+ | domain=crisis && matches_intent() → 立即返回 |
| 1 | 风险等级 | +100 | risk=critical && domain=crisis |
| 1 | 风险等级 | +50 | risk=high && domain ∈ {glucose, stress, mental} |
| 2 | 专家自定义关键词 | +30×boost | tenant_ctx 覆盖关键词匹配 |
| 3 | 平台预设关键词 | +30 | agent.matches_intent(message) |
| 4 | 用户偏好 | +20 | profile.preferences.focus == domain |
| 5 | 设备数据 | +15 | device_data 中有对应字段 |
| 6 | 关联扩展 | +append | 仅1个 Agent 时，追加关联 Agent |

### 5.4 V007 PolicyEngine 5步决策

```
Step 1: RuleRegistry.get_applicable_rules()
        → 4个种子规则 + 租户自定义规则
Step 2: _build_candidates()
        → ApplicabilityMatrix → Agent候选列表 + 评分
Step 3: ConflictResolver.resolve()
        → 5种策略: weighted_score / priority_tree / medical_boundary
                   / tenant_override / risk_suppress
Step 4: CostController.check_budget()
        → 3个预算区间: within(<0.8) / tight(0.8-1.0) / overflow(≥1.0)
        → 模型降级: gpt-4o → qwen-max → deepseek-chat → ollama-local
Step 5: DecisionTraceRecorder.record()
        → UUID trace_id, 完整审计日志
```

**4个种子规则**：

| 规则 | 优先级 | 条件 | 动作 |
|------|--------|------|------|
| crisis_absolute_priority | 100 | risk_level == "critical" | 强制 crisis Agent |
| medical_boundary_suppress | 95 | risk=high && domain ∈ 医学领域 | 屏蔽非医学 Agent |
| cost_daily_limit_default | 70 | daily_token_usage ≥ 90% | 降级模型+限制tokens |
| early_stage_gentle_intensity | 60 | stage ∈ {S0, S1} | max_intensity=2, 偏好 motivation |

### 5.5 安全管线 4层防护

```
L1 输入过滤 (input_filter.py)
│  → 关键词检测: crisis/warning/blocked/medical_advice
│  → PII 检测
│  → 意图分类: normal / warning / crisis / blocked
│  → crisis+critical → 直接走 CrisisAgent
↓
L2 RAG 安全 (rag_safety.py)
│  → 知识检索结果按 Tier 权重过滤 (T1>T2>...>T5)
│  → 过期/撤回内容移除
│  → 高敏感内容在高风险时屏蔽
↓
L3 生成约束 (generation_guard.py)
│  → 注入: "不得给出医学诊断，须建议就医"
│  → 领域规则: 血糖安全范围、用药禁忌等
│  → Prompt 注入防御
↓
L4 输出过滤 (output_filter.py)
   → 医学声明检测: "治愈"/"保证" → 添加免责声明
   → 用药提及 → 强制"咨询医生"
   → 剂量建议 → 阻断（非医嘱上下文）
   → 严重性分级: safe / warning / blocked
```

### 5.6 自动退出处理器

| 触发类型 | 条件 | 严重性 | 升级目标 |
|----------|------|--------|----------|
| 设备数据 | 血糖 < 低阈值 或 > 高阈值 | CRITICAL | crisis |
| 设备数据 | 收缩压 > 阈值 | CRITICAL | crisis |
| 设备数据 | 心率 < 低阈值 或 > 高阈值 | CRITICAL | crisis |
| 关键词 | "自杀"/"急救"/"胸痛" | CRITICAL/WARNING | crisis |
| 风险等级 | user_risk > agent_max_risk | WARNING | 对应 Agent |
| 行为标记 | suicidal_ideation 等 | WARNING | crisis |

---

## 6. Agent 生态系统

### 6.1 子系统概览

| 子系统 | 端点数 | 核心功能 |
|--------|--------|----------|
| Agent 模板 CRUD | 10 | 12预设+动态创建/克隆/启停/缓存刷新 |
| 专家自建 Agent | 6 | 租户级 Agent 创建/更新/删除/路由测试 |
| 反馈学习循环 | 8 | 用户反馈→日聚合→Prompt版本/AB测试/成长报告 |
| 知识共享层 | 9 | 私有→领域→平台 3级知识共享+审核 |
| Agent 市场 | 12 | 发布/审核/安装/推荐+组合编排+成长积分 |

### 6.2 反馈学习循环

```
用户交互 → 提交反馈(accept/reject/modify/rate)
                     ↓
              save_feedback() → AgentFeedback 表
                     ↓
        [Scheduler 每天 01:30] aggregate_daily_metrics()
                     ↓
              AgentMetricsDaily (按Agent聚合)
                     ↓
        ┌────────────┼────────────┐
        ↓            ↓            ↓
   成长报告      Prompt版本     Agent排行榜
   (单Agent趋势)  (AB测试)    (acceptance_rate排序)
```

**Prompt 版本管理**：
- 创建新版本时记录基线：prev_avg_rating + prev_acceptance_rate
- 支持 traffic_pct 分流（AB测试）
- activate=true 自动停用旧版本并更新 AgentTemplate

### 6.3 知识共享层

```
                    私有知识 (scope=tenant)
                         │
                   ┌─────┴─────┐
                   ↓  contribute  ↓
              KnowledgeContribution (status=pending)
                         │
                    ┌────┴────┐
                    ↓         ↓
               [approve]  [reject]
                    ↓
              领域知识 (scope=domain)
              文档+向量块同步更新
                    │
               [可 revoke 撤回]
                    ↓
              恢复为私有 (scope=tenant)
```

**3级检索**：租户私有 → 领域共享 → 平台公共

### 6.4 Agent 市场

**发布流程**：
```
Expert 创建 Agent模板 → 发布到市场 (status=submitted, +30积分)
  → Admin 审核 → [approve → status=published] / [reject]
  → 其他Expert 安装 (克隆模板, 每次安装 publisher +5积分)
```

**推荐算法**：
- 获取 Expert 的 specialties
- 排除已安装 Agent
- 按领域相关性 + 安装量排序

**成长积分事件**：

| 事件 | 积分 |
|------|------|
| 创建 Agent | 20 |
| 优化 Prompt | 10 |
| 分享知识 | 15 |
| 发布到市场 | 30 |
| 被安装（每次） | 5 |
| 收到正面反馈 | 3 |
| 创建组合编排 | 15 |

### 6.5 组合编排 (Composition)

支持将多个 Agent 组合为流水线：
- `pipeline`: 定义执行顺序和参数
- `merge_strategy`: weighted_average (默认)
- 租户级或平台级

### 6.6 效能度量 (6 个 KPI)

| 指标 | 公式 | 用途 |
|------|------|------|
| IES 干预效能 | 阶段进步(40%) + 任务完成(30%) + 数据趋势(30%) | 单用户 Agent 效果 |
| 阶段转化率 | (前进 - 后退) / 天数 | 队列级 Agent 效果 |
| 依从指数 | 任务完成(60%) + 挑战完成(40%) | 行为执行度 |
| 风险降低指数 | 数据趋势改善 | 生物标志物改善 |
| 专家 ROI | avg_IES / (avg_token_cost/1000) | 每美元 LLM 成本的干预效果 |
| 生态健康 | Agent多样性(30%) + 冲突率(20%) + 延迟(20%) + 用户规模(30%) | 系统整体健康 |

---

## 7. 关联网络与冲突矩阵

### 7.1 Agent 关联网络

```
                    crisis ──── mental ──── stress
                      │           │    ╲      │
                      │           │     ╲     │
                 behavior_rx ─────┘  motivation cardiac_rehab
                   ╱  │  ╲                    ╱   │
                  ╱   │   ╲                  ╱    │
          nutrition  sleep  exercise ────────╱     │
              │  ╲    │    ╱                       │
              │   ╲   │   ╱                        │
              │    weight                          │
              │      │                             │
              tcm────┘                     glucose─┘
```

### 7.2 冲突解决矩阵

| Agent A | Agent B | 胜出者 | 原因 |
|---------|---------|--------|------|
| glucose | nutrition | **glucose** | 临床优先级（血糖安全 > 营养建议） |
| sleep | exercise | **sleep** | 睡眠不足时不应推荐运动 |
| stress | exercise | **stress** | 压力大时不应增加运动压力 |
| mental | exercise | **mental** | 心理问题优先处理 |

**冲突解决后**：失败方 confidence × 0.6（降权但保留）

### 7.3 Agent 权重阶梯

```
1.00  ████████████████████  crisis (最高)
0.90  ██████████████████    glucose, behavior_rx
0.85  █████████████████     sleep, stress, mental, weight, cardiac_rehab
0.80  ████████████████      nutrition, exercise, motivation
0.75  ███████████████       tcm (最低)
```

---

## 8. 问题诊断与规划建议

### 8.1 问题 P1：12核心Agent 与 4专家Agent 功能重叠

**现状**：
- `BehaviorRxAgent`（核心层，integrative_agents.py）与 `BehaviorCoachAgent`（专家层，behavior_rx/）在行为处方领域高度重叠
- `CardiacRehabAgent`（核心层）与 `CardiacExpertAgent`（专家层）在心脏康复领域高度重叠
- 核心层的 `behavior_rx` 有 TTM 阶段感知但仅 3 级粗粒度（S0-1/S2-3/S4+）
- 专家层有完整 7 级 TTM + BigFive + CAPACITY 三维计算

**影响**：
- 用户可能同时被两套系统处理同一问题
- 核心层的简单规则与专家层的精细处方产生矛盾建议
- 维护成本翻倍

**建议方案**：

| 方案 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **A. 核心层降级为路由层** | 12核心Agent仅负责意图识别和数据分析，行为建议全部交给专家层 | 职责清晰，无重叠 | 改动量大，需重构核心Agent的process() |
| **B. 专家层吸收核心层** | 逐步将核心Agent的逻辑迁入专家Agent，最终12→4 | 最精简 | 风险高，涉及全链路 |
| **C. 分层协作(推荐)** | 核心层处理"快响应"（数据异常+即时建议），专家层处理"深干预"（行为处方+策略+交接） | 改动最小，互补 | 需明确边界规则 |

**方案 C 详细设计**：
```
用户消息 → MasterAgent
  ├── Step 3.5: 专家Agent路由器判断
  │   ├── 满足条件(有TTM数据/有BehaviorRx上下文) → 走专家层
  │   └── 不满足 → 走核心层
  ├── 核心层: 即时响应（设备异常提醒、简单建议、危机干预）
  └── 专家层: 深度干预（行为处方计算、策略选择、交接管理）
```

**边界规则**：
- 核心层：回复 ≤ 5条建议，不涉及行为策略术语
- 专家层：回复包含行为处方，有策略、强度、节奏、微行动

---

### 8.2 问题 P2：双 MasterAgent 架构冗余

**现状**：
- `core/master_agent_v0.py`（v0，原始9步编排）
- `core/agents/master_agent.py`（v6，模板+租户+PolicyEngine）
- `core/master_agent.py` 仅 `from core.master_agent_v0 import *`（桥接文件）
- API层：v6 优先 → v0 兜底 → mock 最终兜底

**影响**：
- v0 没有模板/租户/PolicyEngine 支持，功能已完全被 v6 覆盖
- 两套代码路径增加调试复杂度
- v0 的存在使新开发者困惑

**建议方案**：
1. **确认 v6 稳定后，废弃 v0**：将 v0 标记为 `@deprecated`
2. **保留 v0 作为极端兜底**：仅在 v6 完全不可用时启用（当前已是这样）
3. **提取 v0 的独有逻辑到 v6**：如有任何 v0 独有功能，迁移到 v6
4. **统一入口**：`get_master_agent()` 和 `get_agent_master()` 合并为一个

**推荐**：短期保持现状（v6→v0 兜底），中期在测试充分后废弃 v0。

---

### 8.3 问题 P3：Agent 路由评分过于简单

**现状**：
- 路由核心逻辑是关键词完全匹配（`keyword in message`）
- 评分权重固定（关键词+30，设备数据+15，偏好+20）
- 缺乏语义理解（"我最近吃太多了"不会匹配 nutrition 的关键词"饮食"）
- 缺乏上下文感知（多轮对话中用户话题切换）

**影响**：
- 用户用口语化表达时，路由失败率高
- 需要依赖 behavior_rx 作为兜底，但兜底建议过于通用
- 同义词/近义词覆盖不全

**建议方案**：

| 阶段 | 方案 | 改动量 |
|------|------|--------|
| **短期** | 扩充关键词表：每个Agent增加同义词/口语化表达/场景词 | 小，仅改configs |
| **中期** | 引入 embedding 语义匹配：user_message 向量 vs Agent关键词向量 cosine相似度 | 中，复用已有 text2vec-base-chinese |
| **长期** | LLM意图分类：用小模型(qwen2.5:0.5b)做intent classification → Agent映射 | 大，需训练/标注 |

**短期关键词扩充示例**：
```json
// nutrition 当前: ["饮食", "营养", "减肥", "热量", "碳水", "蛋白质", "吃什么", "食谱"]
// 建议新增:
["吃多了", "吃太少", "暴饮暴食", "挑食", "外卖", "加餐", "零食", "奶茶",
 "水果", "蔬菜", "肉", "鱼", "早餐", "午餐", "晚餐", "宵夜", "餐前", "餐后",
 "GI", "升糖指数", "膳食纤维", "维生素", "矿物质", "钙", "铁"]
```

---

### 8.4 问题 P4：TTM 阶段在两套系统独立实现

**现状**：
- 核心层用 `stage_aware_selector.py`（StageAwareSelector，查询 StageApplicability 表）
- 专家层用 `behavior_rx_engine.py`（BehaviorRxEngine，内置 TTM×BigFive×CAPACITY 矩阵）
- 两套系统的阶段评估逻辑和Agent适用性映射完全独立
- `NutritionAgent` / `MotivationAgent` 有自己的 TTM 分支逻辑

**影响**：
- 同一用户在两套系统中可能被评估为不同阶段
- Agent 适用性判断不一致
- 策略强度可能互相矛盾

**建议方案**：
1. **统一 TTM 数据源**：两套系统共读同一个 `user_stage` 字段
2. **统一强度映射**：建立全局 `STAGE_INTENSITY_MAP`，核心层和专家层共用
3. **专家层作为权威**：如果用户有 BehaviorRx 处方记录，核心层应参考处方中的策略强度
4. **建议实现顺序**：先统一数据源(1) → 再统一映射(2) → 最后确立权威(3)

---

### 8.5 问题 P5：12种行为策略仅在 BehaviorRx 中使用

**现状**：
- 12种行为策略（consciousness_raising, stimulus_control 等）仅在 `behavior_rx/` 包中定义和使用
- 核心12 Agent 没有"策略"概念，只有硬编码的 if-else 建议
- 核心层的建议风格是"直接给建议"，专家层是"通过策略框架生成建议"

**影响**：
- 核心层建议缺乏行为科学支撑
- 用户从核心层收到的建议可能与专家层的策略方向矛盾
- 浪费了策略框架的价值

**建议方案**：
- **短期**：在核心 Agent 的 system_prompt 中引入策略上下文（"当用户处于S0阶段时，使用意识提升策略"）
- **中期**：在 BaseAgent 中增加 `strategy_hint` 字段，从 BehaviorRx 的策略模板读取
- **长期**：核心 Agent 的 process() 方法接受 `active_strategy: RxStrategyType` 参数，影响建议生成

---

### 8.6 问题 P6：市场/组合/积分已有框架但缺乏内容

**现状**：
- 市场 (AgentMarketplace) 已有完整发布/审核/安装流程，但 0 条发布记录
- 组合编排 (AgentComposition) 已有创建/查询 API，但无预设组合
- 成长积分已有 7 种事件定义，但无积分消费场景

**建议方案**：

| 阶段 | 动作 |
|------|------|
| **预填充** | 将12个预设Agent发布为市场商品，生成初始安装量数据 |
| **预设组合** | 创建3-5个常见组合：糖尿病全套(glucose+nutrition+exercise)、心理健康套装(mental+stress+sleep)、体重管理套装(weight+nutrition+exercise+motivation) |
| **积分消费** | 积分可兑换：高级Agent访问权限、优先路由、定制Prompt额度 |
| **运营激励** | 首批Expert发布Agent → 额外奖励积分 → 带动市场活跃 |

---

### 8.7 问题 P7：System Prompt 格式过于统一

**现状**：
- 所有12个核心Agent的 system_prompt 格式完全相同：
  > 你是一位[职位]，擅长[领域]。根据用户的[数据]，给出[建议]。回复控制在3-5条建议，每条不超过30字。只输出建议列表，不要寒暄。

**影响**：
- 所有Agent回复风格雷同，用户无法感知不同"专家"的差异
- "3-5条建议，每条不超过30字"对所有场景不一定合适
- 缺乏个性化：未考虑用户的沟通偏好（参考 BehaviorRx 的6种 CommunicationStyle）

**建议方案**：
- 每个Agent应有差异化的回复风格（crisis→紧急简短, tcm→温和养生, mental→共情温暖）
- 引入用户沟通偏好：从 BehaviorRx 的 CommunicationStyle 映射到 system_prompt 变体
- 建议长度根据场景动态调整（危机→1条立即行动, 营养→5条详细方案）

---

### 8.8 建议优先级排序

| 优先级 | 问题 | 影响 | 工作量 | 建议时间 |
|--------|------|------|--------|----------|
| **P0** | P3 路由关键词扩充(短期) | 直接影响用户体验 | 小 | 立即 |
| **P1** | P7 System Prompt 差异化 | 影响回复质量 | 小 | 1周内 |
| **P1** | P1 核心/专家层边界明确(方案C) | 防止矛盾建议 | 中 | 1-2周 |
| **P2** | P4 TTM数据源统一 | 保证阶段判断一致性 | 中 | 2-3周 |
| **P2** | P6 市场预填充+预设组合 | 激活生态系统 | 小 | 2周 |
| **P3** | P5 核心层引入策略上下文 | 提升建议科学性 | 中 | 3-4周 |
| **P3** | P2 废弃v0 MasterAgent | 降低维护成本 | 小 | v6稳定后 |
| **P4** | P3 语义匹配路由(中期) | 大幅提升路由准确性 | 大 | 下一版本 |

---

## 9. 文件索引

### 核心 Agent 文件

| 文件 | 内容 |
|------|------|
| `core/agents/base.py` | BaseAgent, AgentDomain, AGENT_CLASS_REGISTRY, 关联网络, 冲突矩阵, 权重表 |
| `core/agents/specialist_agents.py` | 9个专科Agent类 + 注册到REGISTRY |
| `core/agents/integrative_agents.py` | 3个整合Agent类 + 注册到REGISTRY |
| `core/agents/generic_llm_agent.py` | GenericLLMAgent (动态模板Agent) |
| `core/agents/router.py` | AgentRouter (关键词+设备+关联+租户路由) |
| `core/agents/coordinator.py` | MultiAgentCoordinator (9步协调算法) |
| `core/agents/master_agent.py` | v6 MasterAgent (9步流水线+模板+租户) |
| `core/agents/policy_gate.py` | RuntimePolicyGate (allow/delay/soft/escalate/deny) |
| `core/agents/prompts.py` | 12个 Domain System Prompt + 合成模板 |
| `core/agents/ollama_client.py` | SyncOllamaClient (本地LLM兜底) |
| `core/master_agent_v0.py` | v0 MasterAgent (原始编排，兜底) |
| `core/master_agent.py` | 桥接文件 (re-export v0) |

### BehaviorRx 文件

| 文件 | 内容 |
|------|------|
| `behavior_rx/agents/base_expert_agent.py` | BaseExpertAgent, ExpertRule, AgentResponse |
| `behavior_rx/agents/behavior_coach_agent.py` | BehaviorCoachAgent (S0-S2) |
| `behavior_rx/agents/metabolic_expert_agent.py` | MetabolicExpertAgent (S3+代谢) |
| `behavior_rx/agents/cardiac_expert_agent.py` | CardiacExpertAgent (心脏康复) |
| `behavior_rx/agents/adherence_expert_agent.py` | AdherenceExpertAgent (依从性横切面) |
| `behavior_rx/core/behavior_rx_engine.py` | BehaviorRxEngine (TTM×BigFive×CAPACITY) |
| `behavior_rx/core/agent_collaboration_orchestrator.py` | 6场景协作编排 |
| `behavior_rx/core/agent_handoff_service.py` | 交接协议 |
| `behavior_rx/core/rx_models.py` | ORM: rx_prescriptions, rx_strategy_templates, agent_handoff_log |
| `behavior_rx/core/rx_schemas.py` | Pydantic schemas |
| `behavior_rx/rx_routes.py` | 8 REST endpoints |
| `behavior_rx/api/master_agent_integration.py` | ExpertAgentRouter (Step 3.5注入) |
| `behavior_rx/configs/rx_strategies.json` | 12策略模板(含人格修正+领域变体) |

### 模板 & 生态系统文件

| 文件 | 内容 |
|------|------|
| `core/agent_template_service.py` | 模板加载/缓存/Agent实例化/租户路由上下文 |
| `api/agent_template_api.py` | 10 CRUD endpoints |
| `configs/agent_templates_seed.json` | 12预设模板JSON |
| `core/feedback_service.py` | 反馈持久化/日聚合/Prompt版本管理 |
| `api/agent_feedback_api.py` | 8反馈endpoints |
| `core/ecosystem_service.py` | 市场/组合/成长积分 |
| `api/agent_ecosystem_api.py` | 12生态endpoints |
| `core/knowledge/sharing_service.py` | 知识共享(私有→领域→平台) |
| `api/knowledge_sharing_api.py` | 9共享endpoints |
| `api/expert_agent_api.py` | 6专家自建Agent endpoints |

### 策略 & 安全文件

| 文件 | 内容 |
|------|------|
| `core/policy_engine.py` | V007 PolicyEngine (5步决策) |
| `core/rule_registry.py` | 规则注册+JSON-Logic评估+4种子规则 |
| `core/conflict_resolver.py` | 5种冲突解决策略 |
| `core/cost_controller.py` | 成本控制+模型降级+预算管理 |
| `core/stage_aware_selector.py` | TTM阶段感知Agent选择 |
| `core/auto_exit_handler.py` | 运行时边界检查+自动升级 |
| `core/effectiveness_metrics.py` | 6 KPI指标计算 |
| `core/decision_trace.py` | 决策审计日志 |
| `api/policy_api.py` | 12策略endpoints |
| `core/safety/pipeline.py` | 安全管线总控 |
| `core/safety/input_filter.py` | L1 输入过滤 |
| `core/safety/rag_safety.py` | L2 RAG安全 |
| `core/safety/generation_guard.py` | L3 生成约束 |
| `core/safety/output_filter.py` | L4 输出过滤 |
| `core/llm_client.py` | UnifiedLLMClient (cloud→Ollama) |
| `configs/safety_keywords.json` | 安全关键词(4类) |
| `configs/safety_rules.json` | 安全规则(阈值/层级/动作) |

### API 入口文件

| 文件 | 内容 |
|------|------|
| `api/agent_api.py` | Agent运行/列表/反馈/历史/状态 (7 endpoints) |
| `api/main.py` | get_master_agent() / get_agent_master() / 路由注册 |
| `api/dependencies.py` | resolve_tenant_ctx() 租户上下文解析 |

---

> 文档生成日期: 2026-02-14
> 基于代码实际提取，所有数据均来自 `D:\behavioral-health-project` 源码

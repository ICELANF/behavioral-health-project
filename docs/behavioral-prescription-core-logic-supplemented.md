# 行为处方数字平台 - 核心业务逻辑与专业术语体系

> **文档版本**: v2.0 (补充代码可执行规范)
> **生成日期**: 2026-02-10
> **平台版本**: 行健行为教练多Agent系统 v1.0
> **文档版本**: v3.1 (架构审查+问卷补全+BAPS五维校正)
> **源代码**: `D:\behavioral-health-project`
> **补充来源**: 32份项目规划文件 (`行为健康项目规划文件/`)

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
17. [改变动因评估体系](#17-改变动因评估体系-change-driver-assessment) *(新增)*
18. [干预策略矩阵引擎](#18-干预策略矩阵引擎-intervention-strategy-matrix) *(新增)*
19. [SPI 完整计算规范](#19-spi-完整计算规范-success-possibility-index) *(新增)*
20. [能力与支持诊断模块](#20-能力与支持诊断模块-layer-3-diagnostics) *(新增)*
21. [四层诊断-处方-养成闭环](#21-四层诊断-处方-养成闭环-完整管道规范) *(新增)*
22. [120种行为改变有效组合](#22-120种行为改变有效组合-扩展处方策略库) *(新增)*
23. [障碍评估与迫切度评估](#23-障碍评估与迫切度评估-补充问卷) *(新增)*
24. [系统遗漏与改进方向 v3.1](#24-系统遗漏与改进方向-v31) *(更新)*
25. [六级健康能力评估问卷](#25-六级健康能力评估问卷) *(v3.0新增)*
26. [补全评估问卷集](#26-补全评估问卷集) *(v3.0新增)*

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

### 3.5 统一阶段解析 (v3.0 新增)

> **架构决策**: S(行为阶段)和L(心理准备度)保持独立存储, 但策略矩阵统一使用L编码查询。原P编码废弃, 保留数据库字段做向后兼容。

```python
# --- core/stage_mapping.py ---

# P0-P5 名称与 L1-L5 完全对应, 说明策略矩阵本质是心理准备度维度:
# P0(无知无觉)≈L1前期, P1(完全对抗)=L1, P2(抗拒反思)=L2,
# P3(妥协接受)=L3, P4(顺应调整)=L4, P5(全面臣服)=L5

S_TO_L_FALLBACK = {
    "S0": "L1", "S1": "L1", "S2": "L2",
    "S3": "L3", "S4": "L4", "S5": "L4", "S6": "L5",
}

class UnifiedStageResolver:
    """
    解决P/S/L三套阶段编码歧义
    - S和L独立存储
    - 策略矩阵查询统一用L编码
    - 无SPI数据时从S降级推断L
    """
    def resolve(self, behavioral_stage: str, readiness_level: str = None) -> dict:
        if readiness_level:
            strategy_key, source = readiness_level, "spi"
        else:
            strategy_key, source = S_TO_L_FALLBACK[behavioral_stage], "inferred"
        return {
            "behavioral_stage": behavioral_stage,
            "readiness_level": readiness_level or strategy_key,
            "readiness_source": source,
            "strategy_key": strategy_key,       # 用于策略矩阵查询(替代P编码)
            "display_label": READINESS_DISPLAY_NAMES[strategy_key],
        }
```

> **源码**: `core/stage_mapping.py` (v3.0新增)

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

> **注意**: 系数以 §4.1 层级定义表为权威值。`spi_implicit_mapping_complete.json` 需同步更新。

```
L1 ←→ S0(primary), null(secondary)      系数0.3  探索期
L2 ←→ S0(primary), S1(secondary)        系数0.5  思考期
L3 ←→ S1(primary), S2(secondary)        系数0.7  准备期
L4 ←→ S2(primary), S3(secondary)        系数0.9  成长期
L5 ←→ S4(primary), S5(secondary)        系数1.0  收获期
```

> **重要设计说明**: TTM7行为阶段(S0-S6)与心理准备度(L1-L5)是**独立正交维度**，不可合并。
> - TTM7 测量"用户在做什么"（可观测行为），由行为事实驱动升级
> - L1-L5 测量"用户准备好了吗"（内在心理），由SPI问卷评估
> - 成长等级(G0-G5)测量"用户能教别人吗"（角色能力），由积分+考试驱动
> - 健康能力(Lv0-Lv5)测量"用户自身健康管理能力"（技能水平），由能力评估驱动 *(v3.0新增)*
>
> 四维独立: `用户状态 = f(behavioral_stage, readiness_level, growth_level, health_competency)`
> 策略矩阵统一使用 `readiness_level(L)` 查询 *(v3.0: 废弃P编码)*

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

> **编码前缀**: 成长等级使用 **G** (Growth)，与心理准备度 **L** (Level) 区分。

| 等级 | 中文名 | 角色 | 图标 | role_level |
|------|--------|------|------|-----------|
| **G0** | 观察员（预备期） | observer | 👀 | 1 |
| **G1** | 成长者 | grower | 🌱 | 2 |
| **G2** | 分享者 | sharer | 💬 | 3 |
| **G3** | 行为健康教练 | bhp_coach | 🎓 | 4 |
| **G4** | 行为健康促进师 | bhp_promoter | 🚀 | 5 |
| **G5** | 行为健康促进大师 | bhp_master | 👑 | 6 |

```python
# --- core/models.py ---
class UserRole(str, Enum):
    OBSERVER = "observer"           # G0 观察员（预备期）  role_level=1
    GROWER = "grower"               # G1 成长者            role_level=2
    SHARER = "sharer"               # G2 分享者            role_level=3
    BHP_COACH = "bhp_coach"         # G3 行为健康教练      role_level=4
    BHP_PROMOTER = "bhp_promoter"   # G4 行为健康促进师    role_level=5
    BHP_MASTER = "bhp_master"       # G5 行为健康促进大师  role_level=6
    ADMIN = "admin"                 # 系统管理员           role_level=99

class GrowthLevel(str, Enum):
    G0 = "G0"  # 观察员（预备期）
    G1 = "G1"  # 成长者
    G2 = "G2"  # 分享者
    G3 = "G3"  # 行为健康教练
    G4 = "G4"  # 行为健康促进师
    G5 = "G5"  # 行为健康促进大师

ROLE_DISPLAY_NAMES = {
    "observer": "观察员（预备期）", "grower": "成长者", "sharer": "分享者",
    "bhp_coach": "行为健康教练", "bhp_promoter": "行为健康促进师",
    "bhp_master": "行为健康促进大师", "admin": "系统管理员",
}

ROLE_LEVELS = {
    "observer": 1, "grower": 2, "sharer": 3,
    "bhp_coach": 4, "bhp_promoter": 5, "bhp_master": 6, "admin": 99,
}

# 数据库迁移 (向后兼容):
# UPDATE users SET role='bhp_coach' WHERE role='coach';
# UPDATE users SET role='bhp_promoter' WHERE role='promoter';
# UPDATE users SET role='bhp_master' WHERE role='master';
```

### 14.1b 健康能力成长六级 (v3.0 新增)

> 来源: 成长六阶.docx — 双轨模型: G等级=角色能力, Lv等级=健康管理能力

| 等级 | 中文名 | 英文名 | 核心特征 | 图标 |
|------|--------|--------|----------|------|
| **Lv0** | 完全无知者 | No Awareness | 不知道风险、不理解原理 | 🔲 |
| **Lv1** | 问题觉察者 | Problem Awareness | 意识到问题但不会做 | 👁️ |
| **Lv2** | 方法学习者 | Method Learner | 会按步骤做但不稳定 | 📖 |
| **Lv3** | 情境适配者 | Context Adapter | 能在不同情境中调整 | 🔄 |
| **Lv4** | 自我驱动者 | Self-Driver | 健康行为已成习惯 | 🚀 |
| **Lv5** | 使命实践者 | Mission Practitioner | 能影响他人 | 🌟 |

```python
# --- core/models.py ---
class HealthCompetencyLevel(str, Enum):
    LV0 = "Lv0"  # 完全无知者
    LV1 = "Lv1"  # 问题觉察者
    LV2 = "Lv2"  # 方法学习者
    LV3 = "Lv3"  # 情境适配者
    LV4 = "Lv4"  # 自我驱动者
    LV5 = "Lv5"  # 使命实践者

COMPETENCY_TO_ROLE_PREREQUISITE = {
    "G0": "Lv0", "G1": "Lv1", "G2": "Lv2",
    "G3": "Lv3", "G4": "Lv4", "G5": "Lv5",
}

# 健康能力等级 → 推荐内容阶段 (平台内容管理系统根据此映射匹配推荐)
COMPETENCY_TO_CONTENT_STAGE = {
    "Lv0": "need",           # 需求觉察类内容
    "Lv1": "awareness",      # 觉知类内容
    "Lv2": "action",         # 行动实践类内容
    "Lv3": "regulation",     # 自我调节类内容
    "Lv4": "iteration",      # 迭代优化类内容
    "Lv5": "transformation", # 生命跃迁类内容
}
```

> **评估方式**: 六级健康能力评估问卷(30题)，详见 §25

### 14.2 升级门槛 (四维积分+能力前置, v3.0更新)

| 升级路径 | 成长积分 | 贡献积分 | 影响积分 | 考试 | 同道者要求 | 最低健康能力 |
|----------|----------|----------|----------|------|-----------|-------------|
| G0→G1 | 100 | - | - | - | - | Lv1 问题觉察者 |
| G1→G2 | 500 | 50 | - | - | - | Lv2 方法学习者 |
| G2→G3 | 800 | 200 | 50 | 需要 | 4个G1成长者 | Lv3 情境适配者 |
| G3→G4 | 1500 | 600 | 200 | 需要 | 4个G2分享者 | Lv4 自我驱动者 |
| G4→G5 | 3000 | 1500 | 600 | 需要 | 4个G3行为健康教练 | Lv5 使命实践者 |

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
| BAPSScoringEngine | BAPS评分引擎，五大问卷评分算法 |

### 15.5 角色与成长

| 术语 | 说明 |
|------|------|
| 六级体系 | 观察员（预备期）→成长者→分享者→行为健康教练→行为健康促进师→行为健康促进大师 (G0-G5) |
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
| BAPS评分 | `core/baps/scoring_engine.py` | 五大问卷评分算法 |
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


---

## 17. 改变动因评估体系 (Change Driver Assessment)

### 17.1 数据模型

```python
# --- api/models.py 新增 ---

class ChangeCauseCategory(str, Enum):
    """改变动因六大类"""
    INTRINSIC = "intrinsic"           # C1-C4 内在驱动力
    EXTERNAL_EVENT = "external_event"  # C5-C8 外在事件与压力
    EMOTIONAL = "emotional"            # C9-C12 情绪体验变化
    COGNITIVE = "cognitive"            # C13-C16 认知与知识变化
    CAPABILITY = "capability"          # C17-C20 能力与资源改善
    SOCIAL = "social"                  # C21-C24 社会支持与关系

class ChangeCause(Base):
    """24小类改变动因定义表 (种子数据, 只读)"""
    __tablename__ = "change_causes"
    id = Column(String(4), primary_key=True)               # "C1"-"C24"
    category = Column(Enum(ChangeCauseCategory), nullable=False)
    name_zh = Column(String(50), nullable=False)            # "价值观重塑"
    name_en = Column(String(50), nullable=False)            # "value_reshape"
    description = Column(Text)
    assessment_question = Column(Text, nullable=False)      # 对应SPI问卷中的题目
    weight = Column(Float, default=1.0)                     # 类别内权重

class UserChangeCauseScore(Base):
    """用户改变动因评分记录"""
    __tablename__ = "user_change_cause_scores"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assessment_id = Column(Integer, ForeignKey("baps_assessments.id"), nullable=False)
    cause_id = Column(String(4), ForeignKey("change_causes.id"), nullable=False)  # "C1"-"C24"
    score = Column(Integer, nullable=False)                 # 1-5 Likert
    created_at = Column(DateTime, server_default=func.now())

    # 索引: (user_id, assessment_id) 获取单次评估全部得分
    __table_args__ = (
        Index("ix_user_cause_user_assess", "user_id", "assessment_id"),
    )
```

### 17.2 种子数据 (24条)

```json
// --- configs/change_causes.json ---
[
  {"id": "C1",  "category": "intrinsic",      "name_zh": "价值观重塑",   "name_en": "value_reshape",      "question": "我意识到健康、家庭、自由等价值观变得更加重要"},
  {"id": "C2",  "category": "intrinsic",      "name_zh": "身份认同转变", "name_en": "identity_shift",     "question": "我希望成为一个'更健康的人'或'能量型父母'"},
  {"id": "C3",  "category": "intrinsic",      "name_zh": "意义感与使命", "name_en": "purpose_mission",    "question": "我希望自己的生活更有目的或活得更久"},
  {"id": "C4",  "category": "intrinsic",      "name_zh": "自主掌控欲",   "name_en": "autonomy_desire",    "question": "我想对自己的身体和生活负责任"},
  {"id": "C5",  "category": "external_event",  "name_zh": "关键健康事件", "name_en": "health_event",       "question": "我最近经历了健康事件（体检异常、家人生病等）"},
  {"id": "C6",  "category": "external_event",  "name_zh": "重大生活变迁", "name_en": "life_transition",    "question": "我最近经历了重要生活事件（生育、离婚、升职等）"},
  {"id": "C7",  "category": "external_event",  "name_zh": "社会压力",     "name_en": "social_pressure",    "question": "我面临社会压力（工作要求、体重指标、医嘱等）"},
  {"id": "C8",  "category": "external_event",  "name_zh": "经济压力",     "name_en": "economic_pressure",  "question": "我看到身边人因不健康生活方式受到影响"},
  {"id": "C9",  "category": "emotional",       "name_zh": "恐惧与焦虑",   "name_en": "fear_anxiety",       "question": "我对生病、老化感到恐惧"},
  {"id": "C10", "category": "emotional",       "name_zh": "愤怒与不甘",   "name_en": "anger_resentment",   "question": "我对现状感到愤怒，觉得'不能再这样下去了'"},
  {"id": "C11", "category": "emotional",       "name_zh": "羞耻与内疚",   "name_en": "shame_guilt",        "question": "我对不健康的生活习惯感到羞愧或内疚"},
  {"id": "C12", "category": "emotional",       "name_zh": "积极情绪",     "name_en": "positive_emotion",   "question": "我受到榜样激励，体验到积极情绪和鼓舞"},
  {"id": "C13", "category": "cognitive",       "name_zh": "顿悟时刻",     "name_en": "aha_moment",         "question": "我对健康有了新的洞察和理解"},
  {"id": "C14", "category": "cognitive",       "name_zh": "知识补充",     "name_en": "knowledge_gain",     "question": "我学习了新的健康知识（饮食策略、代谢原理等）"},
  {"id": "C15", "category": "cognitive",       "name_zh": "风险觉知",     "name_en": "risk_awareness",     "question": "我更清楚地认识到疾病风险与后果"},
  {"id": "C16", "category": "cognitive",       "name_zh": "未来思维",     "name_en": "future_thinking",    "question": "我能够想象不改变会带来的未来场景"},
  {"id": "C17", "category": "capability",      "name_zh": "时间资源",     "name_en": "time_resource",      "question": "我有固定的时间来执行改变计划"},
  {"id": "C18", "category": "capability",      "name_zh": "经济资源",     "name_en": "financial_resource", "question": "我有足够的经济资源支持改变"},
  {"id": "C19", "category": "capability",      "name_zh": "技能提升",     "name_en": "skill_improvement",  "question": "我掌握了必要的技能（烹饪、运动等）"},
  {"id": "C20", "category": "capability",      "name_zh": "环境改善",     "name_en": "environment_improve","question": "我的物理环境支持改变（健身房、厨房等）"},
  {"id": "C21", "category": "social",          "name_zh": "榜样影响",     "name_en": "role_model",         "question": "我身边有成功的榜样可以参考学习"},
  {"id": "C22", "category": "social",          "name_zh": "同伴社群",     "name_en": "peer_community",     "question": "我有同伴或社群一起打卡、互相监督"},
  {"id": "C23", "category": "social",          "name_zh": "家庭支持",     "name_en": "family_support",     "question": "我的家人支持我的改变计划"},
  {"id": "C24", "category": "social",          "name_zh": "专业指导",     "name_en": "professional_guide", "question": "我得到了专业人士的指导（医护、教练等）"}
]
```

> **注意**: 社会支持维度(C21-C24)在完整SPI问卷中有第25题"我所在的文化或社会环境鼓励健康行为"，但不属于24小类体系。评分时该题归入social维度总分。

### 17.3 评分引擎

```python
# --- core/baps/cause_scoring.py ---

# 维度总分 = SUM(该维度4题得分), 范围4-20
# 维度评价阈值:
CAUSE_CATEGORY_THRESHOLDS = {
    "strong":  15,   # >= 15: "强驱动力"
    "medium":  10,   # >= 10: "中等影响"
    # < 10: "影响较弱"
}
# 特殊: social维度有5题(C21-C25), 阈值按比例调整: strong=18.75, medium=12.5

def score_change_causes(answers: dict[str, int]) -> dict:
    """
    输入: {"C1": 4, "C2": 3, ..., "C24": 5, "C25": 3}  # C25可选(social额外题)
    输出: {
        "category_scores": {"intrinsic": 15, "external_event": 12, ...},
        "category_levels": {"intrinsic": "strong", ...},
        "total_trigger_score": 85,        # 触发原因总分 (25题满分125, 24题满分120)
        "dominant_causes": ["C1", "C5"],  # 得分>=4 的动因
        "weak_causes": ["C18"],           # 得分<=2 的动因
        "top_category": "intrinsic"       # 最强维度
    }
    """

CATEGORY_CAUSE_MAP = {
    "intrinsic":      ["C1", "C2", "C3", "C4"],
    "external_event": ["C5", "C6", "C7", "C8"],
    "emotional":      ["C9", "C10", "C11", "C12"],
    "cognitive":      ["C13", "C14", "C15", "C16"],
    "capability":     ["C17", "C18", "C19", "C20"],
    "social":         ["C21", "C22", "C23", "C24"],  # C25 可选追加
}
```

---

## 18. 干预策略矩阵引擎 (Intervention Strategy Matrix)

### 18.1 数据模型

```python
# --- api/models.py 新增 ---

class InterventionStrategy(Base):
    """144条干预策略矩阵 (种子数据, 只读)"""
    __tablename__ = "intervention_strategies"
    id = Column(Integer, primary_key=True, autoincrement=True)
    stage_code = Column(String(4), nullable=False, index=True)    # "P0"-"P5"
    stage_name = Column(String(20), nullable=False)               # "无知无觉"
    cause_code = Column(String(4), nullable=False, index=True)    # "C1"-"C24"
    cause_category = Column(String(30), nullable=False)           # "内在驱动力"
    cause_name = Column(String(30), nullable=False)               # "价值观重塑"
    strategy_type = Column(String(30), nullable=False)            # "观念松土"
    coach_script = Column(Text, nullable=False)                   # 教练话术模板

    __table_args__ = (
        UniqueConstraint("stage_code", "cause_code", name="uq_stage_cause"),
        Index("ix_strategy_stage_cause", "stage_code", "cause_code"),
    )
```

### 18.2 阶段编码映射 (P→S 双向映射)

```python
# --- core/stage_mapping.py ---

# P (规划文件6阶段) ↔ S (代码7阶段) 双向映射
P_TO_S_MAP = {
    "P0": ["S0"],           # 无知无觉 → precontemplation
    "P1": ["S1"],           # 完全对抗 → contemplation
    "P2": ["S2"],           # 抗拒与反思
    "P3": ["S3"],           # 妥协与接受 → preparation
    "P4": ["S4"],           # 顺应与调整 → action
    "P5": ["S5", "S6"],     # 全面臣服 → maintenance + 内化
}

S_TO_P_MAP = {
    "S0": "P0", "S1": "P1", "S2": "P2",
    "S3": "P3", "S4": "P4", "S5": "P5", "S6": "P5",
}

def get_strategies_for_stage(current_stage: str) -> str:
    """将代码阶段(S0-S6)转换为策略阶段(P0-P5)用于查询干预策略"""
    return S_TO_P_MAP[current_stage]
```

### 18.3 策略匹配引擎

```python
# --- core/intervention_strategy_engine.py ---

class InterventionStrategyEngine:
    """
    输入: user.current_stage (S0-S6) + user.change_cause_scores
    输出: 排序的干预策略列表 (最多3条)
    """

    def match(self, current_stage: str, cause_scores: dict[str, int]) -> list[dict]:
        """
        算法:
        1. S→P映射: current_stage → p_stage
        2. 从 cause_scores 取 top3 得分最高的 cause_code
        3. 查询 intervention_strategies WHERE stage_code=p_stage AND cause_code IN top3
        4. 按 cause_score 降序排列
        5. 返回 [{strategy_type, coach_script, cause_code, cause_name}]
        """
        p_stage = S_TO_P_MAP[current_stage]
        # 按分数降序取 top3 dominant causes
        sorted_causes = sorted(cause_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_cause_codes = [c[0] for c in sorted_causes]

        strategies = db.query(InterventionStrategy).filter(
            InterventionStrategy.stage_code == p_stage,
            InterventionStrategy.cause_code.in_(top_cause_codes)
        ).all()

        return sorted(strategies, key=lambda s: cause_scores.get(s.cause_code, 0), reverse=True)
```

### 18.4 种子数据规格

```json
// --- configs/intervention_strategies.json ---
// 144条, 结构示例:
[
  {
    "stage_code": "P0",
    "stage_name": "无知无觉",
    "cause_code": "C1",
    "cause_category": "内在驱动力",
    "cause_name": "价值观重塑",
    "strategy_type": "观念松土",
    "coach_script": "如果一直维持现状，这是否会影响您未来想做的那些重要的事情？"
  },
  {
    "stage_code": "P0",
    "stage_name": "无知无觉",
    "cause_code": "C5",
    "cause_category": "外在事件",
    "cause_name": "关键健康事件",
    "strategy_type": "风险可视化",
    "coach_script": "我们不看别的，只看这个体检指标。如果放任不管，根据数据3年后它会变成什么样？"
  }
  // ... 共144条 (24原因 × 6阶段)
]
```

> **数据来源**: `干预策略大全.xlsx` sheet "干预策略大全" 完整导出。

### 18.5 各阶段策略类型汇总 (120种唯一策略)

| 阶段 | 核心策略方向 | 策略类型数量 | 示例策略 |
|------|-------------|-------------|---------|
| P0 无知无觉 | 松土、去阻抗、共情 | 9种 | 观念松土, 风险可视化, 正常化/共情, 倾听宣泄 |
| P1 完全对抗 | 赋权、去羞耻、矛盾处理 | 18种 | 赋权/尊重, 自主选择, 苏格拉底提问, 矛盾放大 |
| P2 抗拒与反思 | 愿景、小步、信心 | 24种 | 愿景描绘, 小步试错, 信心建立, 动机访谈 |
| P3 妥协与接受 | 承诺、计划、环境 | 24种 | 承诺机制, 目标锚定, 环境改造, 刻意练习 |
| P4 顺应与调整 | 强化、进阶、监测 | 24种 | 里程碑回顾, 标签强化, 技能挑战, 深度学习 |
| P5 全面臣服 | 内化、传承、系统 | 24种 | 成为榜样, 传承分享, 系统稳态, 心流常驻 |

---

## 19. SPI 完整计算规范 (Success Possibility Index)

### 19.1 完整版 SPI (50题)

```python
# --- core/baps/spi_calculator.py ---

# SPI 问卷三部分:
# Part1: 触发原因评估 25题 (C1-C24 + C25社会环境), 每题1-5分, 满分125
# Part2: 心理状态评估 20题 (每层4题 × 5层), 每题1-5分
# Part3: 改变迫切度   5题, 混合评分

# ============================
# Part2 完整题目 (q26-q45)
# ============================
SPI_PART2_QUESTIONS = {
    "total_resistance": {  # L1 完全对抗
        "label": "完全对抗",
        "questions": [
            {"id": "q26", "text": "我感到愤怒，拒绝接受需要改变的事实"},
            {"id": "q27", "text": "我会争辩、否认问题的存在"},
            {"id": "q28", "text": "我认为改变是外界强加给我的"},
            {"id": "q29", "text": "我会采取反向行为来对抗改变要求"},
        ],
    },
    "resistance_reflection": {  # L2 抗拒与反思
        "label": "抗拒与反思",
        "questions": [
            {"id": "q30", "text": "我虽然抗拒，但开始理解改变的必要性"},
            {"id": "q31", "text": "我的内心很矛盾，一部分想改变，一部分不想"},
            {"id": "q32", "text": "我开始思考'是不是有别的方式'"},
            {"id": "q33", "text": "我会问'如果保持现状会有什么风险'"},
        ],
    },
    "selective_acceptance": {  # L3 妥协与接受
        "label": "妥协与接受",
        "questions": [
            {"id": "q34", "text": "我接受改变是必要的现实"},
            {"id": "q35", "text": "我想要小步尝试，不想一次改变太多"},
            {"id": "q36", "text": "我担心失败或坚持不住"},
            {"id": "q37", "text": "我开始采取一些'象征性改变'的行动"},
        ],
    },
    "adaptive_alignment": {  # L4 顺应与调整
        "label": "顺应与调整",
        "questions": [
            {"id": "q38", "text": "我主动寻求方法来实现改变"},
            {"id": "q39", "text": "我会自发调整行为来适应新要求"},
            {"id": "q40", "text": "我在不同情境下都能找到可持续的模式"},
            {"id": "q41", "text": "我希望把这个行为融入我的生活方式"},
        ],
    },
    "full_internalization": {  # L5 全面臣服
        "label": "全面臣服",
        "questions": [
            {"id": "q42", "text": "新的行为已经成为我自然的一部分"},
            {"id": "q43", "text": "我不需要外部监督就能维持这个习惯"},
            {"id": "q44", "text": "我会自发地推广这个改变给他人"},
            {"id": "q45", "text": "这个改变已经成为我身份的一部分"},
        ],
    },
}

# 心理层次判定: 每层4题汇总, 最高分层 = 当前层次
# 并列时取较高层次(乐观原则)

# 心理层次系数
PSY_LEVEL_COEFFICIENTS = {
    1: 0.3,   # L1 完全对抗
    2: 0.5,   # L2 抗拒与反思
    3: 0.7,   # L3 妥协与接受
    4: 0.9,   # L4 顺应与调整
    5: 1.0,   # L5 全面臣服
}

def calculate_spi_full(
    part1_scores: dict[str, int],   # {"C1": 4, ..., "C25": 3} 25题
    part2_scores: list[int],         # [q26, q27, ..., q45] 20题, 每题1-5
    part3_scores: dict               # {"q46": 8, "q47": 4, "q48": 3, "q49": 7, "q50": 6}
) -> dict:
    """
    完整版SPI计算

    返回: {
        "spi_score": float,          # 0-100
        "trigger_total": int,        # Part1 总分 (25-125)
        "psychological_level": int,  # 1-5
        "urgency_score": float,      # Part3 综合分 (3-30)
        "success_level": str,        # "high"/"medium"/"low"/"very_low"
        "category_scores": dict,     # 六维度得分
        "dominant_causes": list,     # 得分>=4 的动因
    }
    """
    # Step 1: Part1 触发原因总分
    trigger_total = sum(part1_scores.values())  # 25-125

    # Step 2: Part2 心理层次判定
    # 每层4题, 层得分 = SUM(该层4题), 最高分层 = 当前层次
    level_scores = {
        1: sum(part2_scores[0:4]),    # q26-q29: 完全对抗
        2: sum(part2_scores[4:8]),    # q30-q33: 抗拒与反思
        3: sum(part2_scores[8:12]),   # q34-q37: 妥协与接受
        4: sum(part2_scores[12:16]),  # q38-q41: 顺应与调整
        5: sum(part2_scores[16:20]),  # q42-q45: 全面臣服
    }
    psychological_level = max(level_scores, key=level_scores.get)
    psy_coefficient = PSY_LEVEL_COEFFICIENTS[psychological_level]

    # Step 3: Part3 迫切度综合分
    # q46: 迫切程度 1-10
    # q47: 后果严重性 1-5
    # q48: 时间压力 1-5
    # q49: 人生重要性 1-10
    # q50: 行动准备度 1-10
    urgency_score = part3_scores["q46"] + part3_scores["q47"] + part3_scores["q48"]
    # 范围: 3-30 (不含q49, q50, 它们用于辅助判断)

    # Step 4: SPI 公式
    spi_score = (trigger_total / 125) * psy_coefficient * (urgency_score / 30) * 100
    spi_score = round(min(max(spi_score, 0), 100), 1)

    # Step 5: 等级判定
    if spi_score >= 70:
        success_level = "high"         # 立即启动系统化干预
    elif spi_score >= 50:
        success_level = "medium"       # 强化薄弱环节后启动
    elif spi_score >= 30:
        success_level = "low"          # 先处理阻抗建立动机
    else:
        success_level = "very_low"     # 等待时机提供支持

    return {
        "spi_score": spi_score,
        "trigger_total": trigger_total,
        "psychological_level": psychological_level,
        "psy_coefficient": psy_coefficient,
        "urgency_score": urgency_score,
        "success_level": success_level,
        "level_scores": level_scores,
    }
```

### 19.2 快速版 SPI (5题, 5分钟)

```python
# --- core/baps/spi_calculator.py ---

def calculate_spi_quick(
    trigger_strength: int,    # 1-10: 内在动机+外部压力+情绪激活程度
    psychological_level: int, # 1-5 → 映射: 1→2, 2→4, 3→6, 4→8, 5→10
    capability_resource: int, # 1-10: 时间+金钱+技能+环境支持程度
    social_support: int,      # 1-10: 榜样+同伴+家人+专业支持程度
    urgency: int              # 1-10: 紧急程度+重要性+行动准备度
) -> dict:
    """
    快速版SPI (适用于初筛、复评)

    公式: SPI = (触发×0.25 + 层次映射×0.30 + 能力×0.20 + 支持×0.15 + 迫切×0.10) × 10
    """
    LEVEL_MAP = {1: 2, 2: 4, 3: 6, 4: 8, 5: 10}
    level_score = LEVEL_MAP[psychological_level]

    spi_score = (
        trigger_strength * 0.25 +
        level_score * 0.30 +
        capability_resource * 0.20 +
        social_support * 0.15 +
        urgency * 0.10
    ) * 10

    spi_score = round(min(max(spi_score, 0), 100), 1)
    return {"spi_score": spi_score, "method": "quick", "psychological_level": psychological_level}
```

### 19.3 SPI → 行为处方难度映射

```python
# 已存在于 configs/assessment/prescription_strategy_library.json
# 此处明确算法接口:

SPI_DIFFICULTY_MAP = {
    # (min_spi, max_spi): (difficulty, intensity_coefficient, max_tasks)
    (70, 100): ("challenging", 1.0, 5),    # SMART示例: 3个月减重8%
    (50, 69):  ("moderate",    0.7, 3),    # 1个月减重3%
    (30, 49):  ("easy",        0.4, 2),    # 每天多走1000步
    (0,  29):  ("minimal",     0.2, 1),    # 每天记录心情
}

def get_prescription_difficulty(spi_score: float) -> tuple:
    """返回 (difficulty_level, intensity_coefficient, max_daily_tasks)"""
    for (lo, hi), config in SPI_DIFFICULTY_MAP.items():
        if lo <= spi_score <= hi:
            return config
    return ("minimal", 0.2, 1)
```

---

## 20. 能力与支持诊断模块 (Layer 3 Diagnostics)

> **定位**: 四层诊断闭环中的第三层, 位于 SPI评估 之后、行为处方制定 之前。
> **当前状态**: 未实现, 以下为实现规范。

### 20.1 诊断模块结构

```
Layer3Diagnostics/
├── cognitive_assessment.py       # 认知结构诊断 (HBM + 归因 + 时间视角)
├── knowledge_assessment.py       # 知识结构诊断
├── capability_assessment.py      # 能力结构诊断 (COM-B)
├── support_assessment.py         # 支持体系诊断 (五层次)
└── layer3_report_generator.py    # 综合报告生成
```

### 20.2 认知结构诊断 — 健康信念模型 (HBM)

```python
# --- core/diagnostics/cognitive_assessment.py ---

class HBMDimension(str, Enum):
    """健康信念模型6维度"""
    SUSCEPTIBILITY = "susceptibility"     # 易感性认知: 相信自己有患病风险
    SEVERITY = "severity"                 # 严重性认知: 理解疾病的严重后果
    BENEFITS = "benefits"                 # 行动益处: 相信改变有效果
    BARRIERS = "barriers"                 # 行动障碍: 感知改变的困难 (反向计分)
    CUES = "cues"                         # 行动线索: 触发行动的提示
    SELF_EFFICACY = "self_efficacy"       # 自我效能: 相信自己能做到

class AttributionType(str, Enum):
    """疾病归因类型"""
    BEHAVIORAL = "behavioral"     # 行为归因 → 直接进入行为处方
    GENETIC = "genetic"           # 遗传归因 → "基因上膛，生活方式扣扳机"
    ENVIRONMENTAL = "environmental" # 环境归因 → 区分可控/不可控，聚焦可控
    FATALISTIC = "fatalistic"     # 命运归因 → 提供成功案例，增强掌控感

class TimeOrientation(str, Enum):
    """时间视角"""
    PAST_ORIENTED = "past"        # 过去导向 → 帮助放下过去，聚焦当下
    PRESENT_HEDONIC = "present"   # 现在享乐 → 让健康行为变得愉悦，即时奖励
    FUTURE_ORIENTED = "future"    # 未来导向 → 强化未来愿景，长期激励

# HBM 评估 — 每维度3题, 每题1-5分
HBM_QUESTIONS = {
    "susceptibility": [
        "我觉得自己有可能发展成更严重的健康问题",
        "我的家族病史让我对自己的健康感到担忧",
        "按照目前的生活方式，我未来患病的风险在增加",
    ],
    "severity": [
        "如果健康恶化，会严重影响我的生活质量",
        "我了解这类健康问题可能带来的严重后果",
        "健康问题可能影响我照顾家人的能力",
    ],
    "benefits": [
        "改变生活习惯确实能改善我的健康状况",
        "我相信科学的方法可以帮助我变得更健康",
        "采取行动比什么都不做要好得多",
    ],
    "barriers": [  # ⚠️ 反向计分: 5→1, 4→2, 3→3, 2→4, 1→5
        "改变生活习惯对我来说太难了",
        "我没有足够的时间和精力来改变",
        "即使改变了，我也很难坚持下去",
    ],
    "cues": [
        "我身边有人因为改变习惯而变得更健康",
        "医生或专业人士建议我需要改变",
        "我每天能看到关于健康的提醒或信息",
    ],
    "self_efficacy": [
        "我有信心做出并坚持健康的改变",
        "即使遇到困难，我也相信自己能找到解决办法",
        "过去我成功改变过一些不好的习惯",
    ],
}

def score_hbm(answers: dict[str, list[int]]) -> dict:
    """
    输入: {"susceptibility": [4, 3, 5], "severity": [3, 4, 4], ...}
    输出: {
        "dimension_scores": {"susceptibility": 12, ...},   # 每维度3-15分
        "total_score": 72,                                  # 18-90分
        "weak_dimensions": ["self_efficacy"],               # 得分<9的维度
        "intervention_priorities": [                         # 按优先级排序
            {"dimension": "self_efficacy", "score": 6, "strategy": "成功体验+降低难度"}
        ]
    }
    """
    # barriers 维度反向计分
    # 弱维度: < 9 (满分15的60%)
    # 干预优先级: self_efficacy > barriers > susceptibility > severity > benefits > cues
```

### 20.3 归因与时间视角评估

```python
# 归因评估: 单选题
ATTRIBUTION_QUESTION = "您认为自己的健康问题主要是什么原因造成的？"
ATTRIBUTION_OPTIONS = {
    "behavioral":    "自己的行为习惯",
    "genetic":       "遗传基因",
    "environmental": "工作和生活环境",
    "fatalistic":    "年龄增长的自然过程",
}

# 归因 → 干预策略映射
ATTRIBUTION_INTERVENTION_MAP = {
    "behavioral":    {"strategy": "direct_rx", "message": None},
    "genetic":       {"strategy": "reframe", "message": "基因上膛，生活方式扣扳机"},
    "environmental": {"strategy": "focus_controllable", "message": "区分可控和不可控，聚焦可控部分"},
    "fatalistic":    {"strategy": "success_cases", "message": "提供成功案例，增强掌控感"},
}

# 时间视角评估: 单选题
TIME_ORIENTATION_QUESTION = "当您想到健康时，您更多想到的是："
TIME_ORIENTATION_OPTIONS = {
    "past":    "过去的疾病、失败的尝试",
    "present": "现在的享受、眼前的舒服",
    "future":  "未来的生活质量、长远的健康",
}

TIME_ORIENTATION_INTERVENTION_MAP = {
    "past":    "帮助放下过去，聚焦当下和未来",
    "present": "让健康行为本身变得愉悦，设计即时奖励",
    "future":  "强化未来愿景，构建长期激励系统",
}
```

### 20.4 支持体系五层次评估

```python
# --- core/diagnostics/support_assessment.py ---

class SupportLayer(str, Enum):
    """支持体系五层次"""
    CORE = "core"               # 核心支持圈: 配偶/最亲密家人
    INTIMATE = "intimate"       # 亲密圈: 父母/子女/密友
    DAILY = "daily"             # 日常圈: 同事/朋友/邻居
    PROFESSIONAL = "professional" # 专业圈: 医护/教练/营养师
    COMMUNITY = "community"     # 社会圈: 社区/社群/文化

# 每层评估2个维度: quality(质量1-5) + stability(稳定性1-5)
# 专业圈额外: accessibility(可及性1-5)

class SupportLayerScore(BaseModel):
    layer: SupportLayer
    quality: int       # 1-5: 5=非常支持主动帮助, 3=中性, 1=不支持或有负面影响
    stability: int     # 1-5: 5=长期稳定可依赖, 3=时有时无, 1=不稳定
    members: list[str] # 关键人物列表
    notes: str = ""    # 特殊情况备注

def score_support_system(layers: list[SupportLayerScore]) -> dict:
    """
    输出: {
        "total_score": 35,              # 10-50
        "layer_scores": {...},
        "strongest_layer": "core",
        "weakest_layer": "professional",
        "support_level": "adequate",    # "strong"(>=40) / "adequate"(25-39) / "weak"(<25)
        "build_priorities": ["professional", "community"],  # 需要加强的层
    }
    """
```

### 20.5 Layer3 综合诊断报告

```python
# --- core/diagnostics/layer3_report_generator.py ---

class Layer3DiagnosticReport(BaseModel):
    """第三层诊断综合报告"""
    user_id: int
    assessment_date: datetime

    # 认知结构
    hbm_scores: dict[str, int]          # 6维度得分
    attribution_type: AttributionType
    time_orientation: TimeOrientation

    # 知识结构
    knowledge_score: float               # 0-100% 答对率
    knowledge_gaps: list[str]            # 缺失的知识领域

    # 能力结构
    capability_score: float              # CAPACITY问卷已有
    capability_bottlenecks: list[str]    # 瓶颈能力项

    # 支持体系
    support_total: int
    support_level: str                   # strong/adequate/weak

    # 综合建议
    strengths: list[str]                 # 优势项
    weaknesses: list[str]               # 短板项
    priority_interventions: list[dict]   # 按优先级排序的干预建议

    def to_behavioral_profile_patch(self) -> dict:
        """生成 BehavioralProfile 更新补丁"""
        return {
            "cognitive_structure": {
                "hbm": self.hbm_scores,
                "attribution": self.attribution_type,
                "time_orientation": self.time_orientation,
            },
            "support_network": {
                "total_score": self.support_total,
                "level": self.support_level,
            },
            "knowledge_level": self.knowledge_score,
        }
```

---

## 21. 四层诊断-处方-养成闭环 (完整管道规范)

### 21.1 四层闭环流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    四层诊断-处方-养成闭环                         │
│                                                                  │
│  Layer 1: 行为诊断 ──→ Layer 2: SPI评估 ──→ Layer 3: 能力诊断   │
│  (已有: BAPS)          (本章: §19)           (本章: §20)         │
│       │                      │                      │            │
│       ▼                      ▼                      ▼            │
│  BehavioralProfile    spi_score + L1-L5    Layer3Report          │
│       │                      │                      │            │
│       └──────────────────────┴──────────────────────┘            │
│                              │                                    │
│                              ▼                                    │
│              Layer 4: 行为处方与养成 (已有: §6+§7)                │
│              ├─ InterventionMatcher: 策略选择                     │
│              ├─ InterventionStrategyEngine: 动因匹配 (§18)       │
│              ├─ BehaviorRxAgent: 处方生成 (6要素)                 │
│              └─ CultivationTracker: 养成跟踪 (4阶段)             │
└─────────────────────────────────────────────────────────────────┘
```

### 21.2 管道调用顺序 (MasterAgent 集成点)

```python
# --- core/master_agent_v0.py 集成规范 ---

# 在 Step7 InterventionPlanner 中调用:

async def plan_intervention(self, profile: CoreUserMasterProfile) -> CoreInterventionPlan:
    """
    扩展后的干预规划流程:

    1. 读取 BehavioralProfile (Layer 1 输出)
    2. 读取 spi_score + psychological_level (Layer 2 输出)
    3. 读取 Layer3DiagnosticReport (Layer 3 输出, 可选)
    4. 查询 InterventionStrategyEngine.match(stage, cause_scores) → 策略列表 (§18)
    5. 通过 PolicyGate 过滤策略 (§11)
    6. 调用 BehaviorRxAgent 生成处方 (6要素, §6)
    7. 设定养成阶段 (§7)
    8. 生成 CoreDailyTask
    """

    # 新增: Layer 3 影响处方生成的规则
    if layer3_report:
        # 认知短板 → 追加认知教育类任务
        if layer3_report.hbm_scores.get("self_efficacy", 15) < 9:
            plan.add_educational_task("self_efficacy_building")

        # 归因偏差 → 追加认知重构话术
        if layer3_report.attribution_type == "fatalistic":
            plan.coach_script_modifier = "增强掌控感"

        # 支持不足 → 追加社交连接处方
        if layer3_report.support_level == "weak":
            plan.add_rx_category("social_connection")
```

### 21.3 监测与调整 (PDCA)

```python
# --- core/cultivation_tracker.py ---

class MonitoringLevel(str, Enum):
    """三级监测体系"""
    DAILY = "daily"       # 日监测: 打卡完成率、情绪记录
    WEEKLY = "weekly"     # 周监测: 周完成率、困难复盘、微调建议
    MONTHLY = "monthly"   # 月监测: 月度总结、SPI复评、养成阶段判定

# 各阶段监测频率
CULTIVATION_MONITORING = {
    "startup": {
        "daily": True,      # 每日打卡提醒
        "weekly": True,     # 每周教练通话
        "monthly": True,    # 月度评估
        "coach_contact_freq": "3次/周",
    },
    "adaptation": {
        "daily": True,
        "weekly": True,
        "monthly": True,
        "coach_contact_freq": "2次/周",
    },
    "stability": {
        "daily": False,     # 减少日提醒
        "weekly": True,
        "monthly": True,
        "coach_contact_freq": "1次/周",
    },
    "internalization": {
        "daily": False,
        "weekly": False,    # 减少周监测
        "monthly": True,
        "coach_contact_freq": "1次/月",
    },
}

# PDCA 调整触发条件
ADJUSTMENT_TRIGGERS = {
    "weekly_completion_rate < 0.5":  "降低任务难度或数量",
    "streak_break >= 3 days":       "触发教练主动联系",
    "spi_decrease >= 10":           "重新评估心理层次",
    "cultivation_stage_timeout":    "检查是否需要降级",
}

# 养成阶段晋级条件
CULTIVATION_PROMOTION_RULES = {
    "startup → adaptation": {
        "min_days": 14,
        "min_completion_rate": 0.6,
        "min_check_ins": 10,
    },
    "adaptation → stability": {
        "min_days": 56,      # 8周
        "min_completion_rate": 0.7,
        "min_streak_days": 14,
    },
    "stability → internalization": {
        "min_days": 120,     # 4个月
        "min_completion_rate": 0.8,
        "min_streak_days": 30,
        "reduced_monitoring_ok": True,  # 减少监测后仍维持
    },
}
```

---

## 22. 120种行为改变有效组合 (扩展处方策略库)

### 22.1 组合结构定义

```python
# --- core/intervention_combinations.py ---

class CombinationCategory(str, Enum):
    """6大类动因框架 (120组合版, 与§17的24小类不同层次)"""
    VALUE_DRIVEN = "value_driven"           # ① 价值驱动
    RISK_SURVIVAL = "risk_survival"         # ② 风险-生存压力
    EMOTION_TRIGGERED = "emotion_triggered" # ③ 情绪触发
    VISION_FUTURE = "vision_future"         # ④ 愿景与未来自我
    SOCIAL_INFLUENCE = "social_influence"   # ⑤ 社会影响与榜样
    MISSION_MEANING = "mission_meaning"     # ⑥ 使命感与人生意义

class ChangeStage5(str, Enum):
    """120组合使用的5阶段 (与P0-P5的映射)"""
    UNAWARE = "unaware"           # 无意识 → P0
    RESISTANT = "resistant"       # 抵触/犹豫 → P1+P2
    WILLING = "willing"           # 愿意尝试 → P3
    ACTIVE = "active"             # 积极行动 → P4
    MAINTAINING = "maintaining"   # 维持巩固 → P5

# 6大类 × 4细分 = 24种动因
COMBINATION_SUBDIVISIONS = {
    "value_driven": [
        "pursuit_life_quality",      # 追求生活质量
        "desire_long_term_benefit",  # 渴望长期收益
        "enhance_self_efficacy",     # 提升自我效能
        "mind_body_alignment",       # 保持身心一致
    ],
    "risk_survival": [
        "health_risk",               # 健康风险
        "medical_major_event",       # 医嘱/重大事件
        "family_responsibility",     # 家庭责任
        "work_life_crisis",          # 工作生活危机
    ],
    "emotion_triggered": [
        "intense_anxiety",           # 强烈焦虑
        "frustration_shame",         # 挫败羞耻
        "physical_fear",             # 身体不适恐惧
        "failure_reflection",        # 失败反思
    ],
    "vision_future": [
        "better_self",               # 想成为更好的人
        "clear_future_vision",       # 明确未来愿景
        "growth_breakthrough",       # 追求成长突破
        "sense_of_control",          # 掌控感
    ],
    "social_influence": [
        "family_support",            # 家人支持
        "peer_influence",            # 同伴影响
        "professional_advice",       # 专业人士建议
        "role_model_inspiration",    # 榜样激励
    ],
    "mission_meaning": [
        "life_value_reflection",     # 生命价值反思
        "responsibility_for_others", # 为他人负责
        "life_direction_awakening",  # 人生方向醒觉
        "potential_fulfillment",     # 发挥潜能
    ],
}
```

### 22.2 组合干预模板

```python
# --- configs/intervention_combinations.json ---

# 每条组合包含5种教练问句:
class CombinationTemplate(BaseModel):
    category: CombinationCategory
    subdivision: str
    stage: ChangeStage5
    awareness_question: str      # 觉察型问句: "您有没有注意到..."
    motivation_question: str     # 动机型问句: "如果能改变, 最期待..."
    planning_question: str       # 计划型问句: "您打算从哪一步开始..."
    execution_support: str       # 执行支持问句: "遇到困难时, 您可以..."
    reinforcement_question: str  # 维持强化问句: "这段时间的坚持让您感受到..."

# 120条 = 24细分 × 5阶段
# 示例:
# {
#   "category": "value_driven",
#   "subdivision": "pursuit_life_quality",
#   "stage": "unaware",
#   "awareness_question": "您有没有注意到, 最近身体在某些方面给您发出了信号？",
#   "motivation_question": "如果健康能再好一点, 您最想做的事情是什么？",
#   "planning_question": "如果我们从最小的一步开始, 您觉得什么最容易做到？",
#   "execution_support": "万一某天做不到, 您觉得可以用什么方式补回来？",
#   "reinforcement_question": "回想一下做到的那些天, 身体和心情有什么不同吗？"
# }
```

### 22.3 与现有系统的集成接口

```python
# --- core/intervention_matcher.py 扩展 ---

class EnhancedInterventionMatcher:
    """
    原 InterventionMatcher 扩展:
    1. 原有 rx_library 8类处方 → 行为层面 (做什么)
    2. 新增 intervention_strategies 144条 → 阶段×动因策略 (怎么说)
    3. 新增 intervention_combinations 120种 → 动因×阶段教练问句 (怎么问)

    三层协同:
    rx_library:       target_behavior + frequency_dose + time_place  (处方内容)
    strategies:       strategy_type + coach_script                    (干预策略)
    combinations:     5种教练问句模板                                  (沟通方式)
    """

    def match_full(
        self,
        stage: str,                    # S0-S6
        cause_scores: dict[str, int],  # C1-C24 评分
        bpt_type: str,                 # BPT-6 行为分型
        spi_score: float,
    ) -> dict:
        """
        返回: {
            "prescriptions": [...],    # rx_library 处方 (做什么)
            "strategies": [...],       # 144策略 (怎么说)
            "coach_questions": [...],  # 120组合问句 (怎么问)
            "difficulty": str,         # SPI→难度
            "interaction_mode": str,   # empathy/challenge/execution
        }
        """
```

---

## 23. 障碍评估与迫切度评估 (补充问卷)

### 23.1 行为改变障碍评估 (6类25题)

> **数据来源**: `行为改变动因与阶段迫切程度和障碍评测试.docx`
> 评分: 0=不是障碍, 1=轻微, 2=中度, 3=严重, 4=几乎无法克服

```python
# --- core/baps/obstacle_assessment.py ---

class ObstacleCategory(str, Enum):
    """6类行为改变障碍"""
    COGNITIVE_PSYCHOLOGICAL = "cognitive_psychological"  # 认知与心理障碍
    EMOTIONAL_MOTIVATION = "emotional_motivation"        # 情绪与动力障碍
    ENVIRONMENTAL_RESOURCE = "environmental_resource"    # 环境与资源障碍
    SOCIAL_RELATIONAL = "social_relational"             # 社会与关系障碍
    PHYSIOLOGICAL_HABIT = "physiological_habit"         # 生理与习惯障碍
    SYSTEMIC_PERSISTENCE = "systemic_persistence"       # 系统与持续性障碍

OBSTACLE_QUESTIONS = {
    "cognitive_psychological": [
        {"id": "OB01", "text": "我不相信自己能够成功改变"},
        {"id": "OB02", "text": "我不清楚具体应该怎么做"},
        {"id": "OB03", "text": "我总是拖延，无法开始行动"},
        {"id": "OB04", "text": "我害怕失败或出丑"},
        {"id": "OB05", "text": "我觉得改变太难、太痛苦"},
    ],
    "emotional_motivation": [
        {"id": "OB06", "text": "我经常情绪低落，缺乏动力"},
        {"id": "OB07", "text": "我容易焦虑或压力过大"},
        {"id": "OB08", "text": "我用不健康行为来应对压力（如暴饮暴食）"},
        {"id": "OB09", "text": "我很快就失去新鲜感和热情"},
    ],
    "environmental_resource": [
        {"id": "OB10", "text": "我没有足够的时间"},
        {"id": "OB11", "text": "我缺乏经济支持"},
        {"id": "OB12", "text": "我的生活环境不利于改变（如没有运动场所）"},
        {"id": "OB13", "text": "获取健康食材或资源不方便"},
    ],
    "social_relational": [
        {"id": "OB14", "text": "家人不支持或反对我的改变"},
        {"id": "OB15", "text": "朋友或同事的不良影响（如聚餐应酬）"},
        {"id": "OB16", "text": "我没有同伴一起努力"},
        {"id": "OB17", "text": "我缺乏专业指导"},
    ],
    "physiological_habit": [
        {"id": "OB18", "text": "我有身体疾病或疼痛限制"},
        {"id": "OB19", "text": "我的旧习惯太根深蒂固"},
        {"id": "OB20", "text": "我对某些不健康行为有成瘾或依赖"},
        {"id": "OB21", "text": "我容易疲劳，精力不足"},
    ],
    "systemic_persistence": [
        {"id": "OB22", "text": "我不知道如何制定可行的计划"},
        {"id": "OB23", "text": "我无法坚持，总是半途而废"},
        {"id": "OB24", "text": "我一遇到挫折就容易放弃"},
        {"id": "OB25", "text": "我缺乏反馈和进度追踪"},
    ],
}

def score_obstacles(answers: dict[str, list[int]]) -> dict:
    """
    输入: {"cognitive_psychological": [3,2,4,1,3], ...} 每题0-4分
    输出: {
        "category_scores": {"cognitive_psychological": 13, ...},  # 0-20/0-16
        "total_score": 45,                   # 0-100
        "severe_barriers": ["OB03","OB05"],  # 单题>=3
        "severe_categories": [...],          # 类别平均>=2.5
        "obstacle_level": "moderate",        # severe(>=60)/moderate(30-59)/mild(<30)
        "top3_barriers": [...],              # 按分数降序
        "prescription_adjustments": [...]    # 障碍→处方调整
    }
    """
```

### 23.2 障碍消解策略库

```python
OBSTACLE_INTERVENTION_MAP = {
    "cognitive_psychological": {
        "rx_adjustment": "降低目标难度, 增加认知教育类微任务",
        "strategies": [
            "自我效能感重建: 成功日记+替代性经验+言语鼓励",
            "目标分解: SMART原则, 从'减肥20斤'→'本周减0.5斤'",
            "完美主义松绑: '进步优于完美', 允许80分",
            "拖延破解: 5分钟启动法+番茄钟",
            "失败恐惧脱敏: 重新定义'失败=数据收集'",
        ],
    },
    "emotional_motivation": {
        "rx_adjustment": "追加情绪调节处方, 触发情绪时的替代行为",
        "strategies": [
            "ABC情绪日记(事件-信念-情绪)",
            "压力应对替代行为清单(散步/冥想/深呼吸)",
            "动力维持: 视觉化进度表+里程碑庆祝",
            "倦怠预防: 变化性训练+休息日设计",
        ],
    },
    "environmental_resource": {
        "rx_adjustment": "碎片化任务设计, 零成本/低成本方案优先",
        "strategies": [
            "时间审计: 记录一周时间分配→碎片时间挖掘",
            "低成本替代: 公园/自重训练/免费App",
            "环境改造: 家庭健康角落+社区资源地图",
            "便利性提升: 周日备餐+一站式方案",
        ],
    },
    "social_relational": {
        "rx_adjustment": "社群匹配, 同伴结对, 减少社交压力目标",
        "strategies": [
            "家庭沟通: 非暴力沟通+家庭会议+共赢方案",
            "社交情境应对: 拒绝话术库+自带健康食物",
            "同伴支持: 线上社群匹配+责任伙伴制",
            "专业对接: 低成本教练+营养师",
        ],
    },
    "physiological_habit": {
        "rx_adjustment": "降低运动强度, 习惯替换而非消除, 渐进式减少旧行为",
        "strategies": [
            "身体限制适配: 医疗评估+适应性运动方案",
            "旧习惯替代: 习惯循环分析(提示-行为-奖励), 替换行为",
            "成瘾处理: 分级戒断+替代满足源",
            "精力管理: 睡眠优化+能量-任务匹配",
        ],
    },
    "systemic_persistence": {
        "rx_adjustment": "增加结构化计划工具, 强化反馈闭环",
        "strategies": [
            "SMART目标规划: 具体化+可测量+现实性",
            "坚持力培养: 习惯追踪器+连续天数可视化+断链应急",
            "韧性建设: 挫折预演+认知重构+快速恢复协议",
            "反馈机制: 周度复盘模板+数据追踪",
        ],
    },
}
```

### 23.2 迫切度评估 (SPI Part 3 详细规范)

```python
# --- core/baps/urgency_assessment.py ---

class UrgencyQuestion(BaseModel):
    id: str
    text: str
    scale_min: int
    scale_max: int
    weight: float  # 用于综合分计算

URGENCY_QUESTIONS = [
    UrgencyQuestion(id="q46", text="改变对我的迫切程度",
                    scale_min=1, scale_max=10, weight=1.0),
    UrgencyQuestion(id="q47", text="不改变的后果严重性",
                    scale_min=1, scale_max=5, weight=1.0),
    UrgencyQuestion(id="q48", text="时间压力评估",
                    scale_min=1, scale_max=5, weight=1.0),
    UrgencyQuestion(id="q49", text="改变对人生的重要性",
                    scale_min=1, scale_max=10, weight=0.0),  # 辅助题, 不参与SPI计算
    UrgencyQuestion(id="q50", text="行动准备度",
                    scale_min=1, scale_max=10, weight=0.0),  # 辅助题, 不参与SPI计算
]

# SPI 公式中的迫切度综合分 = q46 + q47 + q48, 范围 3-30
# q49, q50 仅用于教练参考, 不参与SPI计算

URGENCY_THRESHOLDS = {
    "high":   24,   # >= 24: "高度迫切"
    "medium": 18,   # >= 18: "中等迫切"
    # < 18: "迫切度较低"
}
```

---

## 24. 系统遗漏与改进方向 (v3.1 更新)

> 基于架构审查 + 项目规划文件补充

### 24.1 已有规划文件可直接支撑的改进

| 原遗漏# | 可用资源 | 实现路径 |
|---------|----------|----------|
| #2 首评171题过大 | 快速SPI评估表 (5题) | `spi_calculator.calculate_spi_quick()` 已在§19.2定义 |
| #6 rx_library仅8类 | 144策略矩阵 + 120种组合 | `InterventionStrategyEngine` (§18) + `EnhancedInterventionMatcher` (§22) |
| #9 缺纵向追踪 | 三级监测体系 + PDCA | `CultivationTracker` + `CULTIVATION_MONITORING` (§21.3) |

### 24.2 完整差距清单 (v3.0 可执行优先级排序)

| # | 差距 | v2.0状态 | v3.0状态 | 工作量 | 优先级 |
|---|------|---------|---------|--------|--------|
| 13 | 改变动因评估 | ✅ 规范完整 | ✅ | 2-3天 | P1 |
| 14 | 144策略矩阵引擎 | ✅ 规范完整 | ✅ L索引改版 | 2-3天 | P1 |
| 15 | SPI完整计算 | ✅ 规范完整 | ✅ | 1-2天 | P1 |
| 16 | 障碍评估问卷 | ⚠️ 8/40题 | ✅ 40/40题 | 2天 | P2 |
| 17 | HBM认知诊断 | ✅ 规范完整 | ✅ | 2天 | P2 |
| 18 | 支持体系评估 | ⚠️ 无题目 | ✅ 27题完整 | 1-2天 | P2 |
| 19 | 120组合教练问句 | ⚠️ 模板无数据 | ⚠️ 待填充 | 3天 | P3 |
| 20 | 养成监测PDCA | ✅ 规范完整 | ✅ | 3-5天 | P3 |
| 21 | Layer3综合报告 | ✅ 规范完整 | ✅ | 2天 | P3 |
| 22 | COM-B能力评估 | ❌ | ✅ 18题 (§20.5) | 1天 | P2 |
| 23 | 自我效能评估 | ❌ | ✅ 5题 (§20.6) | 0.5天 | P2 |
| 24 | 六级健康能力评估 | ❌ | ✅ 30题 (§25) | 1天 | P2 |
| 26 | 统一阶段模型 | ❌ | ✅ (§3.5) | 1天 | P1 |
| 27 | 健康能力→角色前置 | ❌ | ✅ (§14.1b) | 1天 | P2 |

### 24.3 数据库迁移清单 (v3.0)

```python
# v2.0 已有表 (8表):
# 1. change_causes              (种子数据24条, §17)
# 2. user_change_cause_scores   (用户动因评分, §17)
# 3. intervention_strategies    (种子数据144条, §18)
# 4. obstacle_assessments       (用户障碍评分, §23)
# 5. hbm_assessments            (HBM认知评估, §20)
# 6. support_assessments        (支持体系评估, §20)
# 7. layer3_diagnostic_reports  (第三层综合报告, §20)
# 8. cultivation_monitoring_logs(养成监测记录, §21)

# v3.0 新增表 (3表):
# 9.  health_competency_assessments (健康能力评估, §26)
# 12. comb_assessments              (COM-B评估, §20.5)
# 13. self_efficacy_assessments     (自我效能评估, §20.6)

# v3.0 表结构变更:
# intervention_strategies: 新增 readiness_level 列
# users: 新增 health_competency_level 列 (Lv0-Lv5)

# v3.0 新增配置文件 (累计):
# configs/change_causes.json                    (24条种子数据)
# configs/intervention_strategies.json          (144条策略矩阵)
# configs/intervention_combinations.json        (120条组合模板)
# configs/obstacle_questions_full.json          (40题障碍问卷)
# configs/obstacle_rx_adjustments.json          (10类障碍→处方调整)
# configs/hbm_questions.json                    (18题HBM问卷)
# configs/cultivation_monitoring.json           (三级监测配置)
# configs/health_competency_questions.json      (30题能力问卷, v3)
# configs/comb_questions.json                   (18题COM-B问卷, v3)
# configs/self_efficacy_questions.json          (5题自我效能, v3)
# configs/support_assessment_questions.json     (27题支持评估, v3)
```


## 25. 六级健康能力评估问卷 (v3.0 新增)

> 来源: 成长六阶.docx 六级健康行为评估表 (30题, 每级5题)

### 25.1 评估问卷

```python
# --- core/baps/health_competency_assessment.py ---

HEALTH_COMPETENCY_QUESTIONS = {
    "Lv0": {  # 完全无知者 — 不知道风险、不理解原理
        "questions": [
            "我不知道自己的体重、腰围、血压、血糖的真实状态",
            "我不了解肥胖、高血糖、慢性病的风险",
            "我不知道吃什么、怎么吃会导致血糖或体重问题",
            "我不知道运动对健康的影响",
            "我从未主动记录或监测过健康数据",
        ],
        "scoring": "reverse",  # 反向: 符合越多→能力越低
    },
    "Lv1": {  # 问题觉察者 — 意识到问题但不会做
        "questions": [
            "我知道自己'需要改变'，但不知道具体怎么做",
            "我了解一些风险，但无法判断哪些与我最相关",
            "我知道吃得不健康，但无法控制或不知道替代方案",
            "我知道需要运动，但无法坚持或不知道如何开始",
            "我偶尔记录数据，但无法解释它们",
        ],
    },
    "Lv2": {  # 方法学习者 — 会按步骤做但不稳定
        "questions": [
            "我掌握基本控糖/减重方法（如吃饭顺序、控碳）",
            "我能按照指导完成配餐、记录饮食或监测血糖",
            "我能完成步行或简单运动，但不够稳定",
            "我理解部分健康行为原理，但不能灵活应用",
            "需要别人监督或提醒才能行动",
        ],
    },
    "Lv3": {  # 情境适配者 — 能在不同情境中调整
        "questions": [
            "我在外食、应酬、加班、旅行等情况下能做出较好选择",
            "我能识别情绪、压力对饮食和血糖的影响并调整",
            "我的饮食、运动、睡眠较稳定，偶尔波动可自我纠正",
            "我能用不同方法解决健康执行中的困难",
            "我能解释自己的血糖或体重变化的原因",
        ],
    },
    "Lv4": {  # 自我驱动者 — 健康行为已成习惯
        "questions": [
            "我有稳定的生活结构（饮食、运动、睡眠节律）",
            "我能长期保持健康行为而无需监督",
            "我的血糖/体重/腰围较为稳定，无大的波动",
            "我知道自己的健康方向和价值，并愿意持续投入",
            "健康行为已经融入日常生活方式",
        ],
    },
    "Lv5": {  # 使命实践者 — 能影响他人
        "questions": [
            "健康行为对我来说是一种生命价值选择",
            "我会主动向家人、朋友或同事传递健康方法",
            "我能带动他人改善饮食、运动或睡眠",
            "我能分析问题、制定方案，指导他人实践",
            "我愿意把健康行为视为长期使命并持续践行",
        ],
    },
}
```

### 25.2 评分算法

```python
def assess_health_competency(answers: dict[str, list[bool]]) -> dict:
    """
    输入: {"Lv0": [T,F,T,F,T], "Lv1": [T,T,F,T,F], ...} (True=符合)
    算法: Lv0反向计分; 从Lv5向下找第一个勾选>=3题的等级
    输出: {
        "current_level": "Lv2",
        "level_name": "方法学习者",
        "level_scores": {"Lv0": 3, "Lv1": 3, "Lv2": 4, "Lv3": 1, "Lv4": 0, "Lv5": 0},
        "recommended_content_stage": "action",
    }
    """
    THRESHOLD = 3
    level_scores = {}
    for level, config in HEALTH_COMPETENCY_QUESTIONS.items():
        count = sum(1 for a in answers.get(level, []) if a)
        if config.get("scoring") == "reverse":
            count = 5 - count
        level_scores[level] = count

    current_level = "Lv0"
    for level in ["Lv5", "Lv4", "Lv3", "Lv2", "Lv1", "Lv0"]:
        if level_scores[level] >= THRESHOLD:
            current_level = level
            break

    return {
        "current_level": current_level,
        "level_name": HEALTH_COMPETENCY_DISPLAY[current_level]["name"],
        "level_scores": level_scores,
        "recommended_content_stage": COMPETENCY_TO_CONTENT_STAGE[current_level],
    }
```

---

## 26. 补全评估问卷集 (v3.0 新增)

### 26.1 支持体系五层次评估 (27题)

> 补全 §20.4 缺失的具体题目

```python
# --- configs/support_assessment_questions.json ---

SUPPORT_ASSESSMENT_QUESTIONS = {
    "core": {  # 核心支持圈: 配偶/最亲密家人
        "quality": [
            "我的伴侣/最亲密家人理解并支持我的健康改变计划",
            "当我需要帮助时，核心家人会主动协助我",
            "核心家人不会在我面前做出与改变目标相悖的行为",
        ],
        "stability": [
            "我与核心家人的关系稳定且可以依赖",
            "即使发生争执，核心家人对我的支持不会改变",
        ],
    },
    "intimate": {  # 亲密圈: 父母/子女/密友
        "quality": [
            "我的父母/子女/密友知道我在进行健康改变",
            "亲密圈中至少有1人愿意陪我一起改变",
            "亲密圈中没有人在阻碍或嘲笑我的改变",
        ],
        "stability": [
            "我与亲密圈的联系是定期且稳定的",
            "我在需要时能及时联系到亲密圈成员",
        ],
    },
    "daily": {  # 日常圈: 同事/朋友/邻居
        "quality": [
            "我的日常社交环境支持健康行为",
            "同事/朋友不会在聚餐时强迫我破坏健康计划",
            "日常圈中有人与我有相似的健康目标",
        ],
        "stability": [
            "我的日常社交关系相对稳定",
            "日常圈中的支持不会因换工作/搬家而完全消失",
        ],
    },
    "professional": {  # 专业圈: 医护/教练
        "quality": [
            "我有可以咨询的健康专业人士",
            "专业人士给出的建议是个性化且可执行的",
            "我信任我的健康指导者",
        ],
        "stability": [
            "我能定期获得专业指导",
            "专业支持在我需要时可以及时获得",
        ],
    },
    "community": {  # 社会圈: 社区/社群
        "quality": [
            "我所在的社区/社群有健康活动或资源",
            "我的文化环境鼓励而非阻碍健康行为",
            "我能找到线上或线下的健康互助社群",
        ],
        "stability": [
            "社群支持是长期可持续的",
            "社区健康资源不会因季节/政策变化而中断",
        ],
    },
}
# 评分: 每题1-5分, quality/stability分别统计
# 总计: 27题 (5层×quality 3题 + 5层×stability 2题 = 25题 + professional额外2题)
```

### 26.2 COM-B能力评估 (18题)

```python
# --- configs/comb_questions.json ---

COMB_ASSESSMENT_QUESTIONS = {
    "capability": {
        "physical": [
            "我的身体状况允许我进行中等强度的运动",
            "我具备基本的烹饪能力来准备健康饮食",
            "我能够识别食物标签上的营养成分信息",
        ],
        "psychological": [
            "我能够制定并记住每天的健康行为计划",
            "当面对诱惑时，我能暂停并做出理性选择",
            "我能分辨真实饥饿vs情绪性进食",
        ],
    },
    "opportunity": {
        "physical": [
            "我家附近有适合运动的场所",
            "我的厨房设备足以准备健康饮食",
            "我的生活环境中健康食物比不健康食物更容易获取",
        ],
        "social": [
            "我身边有人在践行健康的生活方式",
            "我的社交活动不会频繁要求大量饮酒或暴饮暴食",
            "我的工作环境允许我保持基本健康行为",
        ],
    },
    "motivation": {
        "automatic": [
            "想到运动或健康饮食时，第一反应是积极的",
            "我已经有一些不需要提醒就能做到的健康行为",
            "健康行为不会让我感到被剥夺或惩罚",
        ],
        "reflective": [
            "我清楚改变健康行为对我的长期意义",
            "我已经为自己制定了具体的健康目标",
            "我相信付出的努力最终会得到回报",
        ],
    },
}
# 评分: 每题1-5分, 6子维度×3题 = 18题, 总分18-90
```

### 26.3 自我效能评估 (5题)

```python
# --- configs/self_efficacy_questions.json ---

SELF_EFFICACY_QUESTIONS = [
    {"id": "SE1", "type": "task",       "text": "您相信自己能做到目标行为吗？"},
    {"id": "SE2", "type": "maintenance", "text": "您相信自己能坚持3个月以上吗？"},
    {"id": "SE3", "type": "recovery",    "text": "如果中断了，您相信自己能重新开始吗？"},
    {"id": "SE4", "type": "situational", "text": "即使很忙/很累，您相信自己能坚持吗？"},
    {"id": "SE5", "type": "social",      "text": "在聚会/应酬时，您能坚持健康选择吗？"},
]
# 评分: 每题1-10分, 平均分≥7=强, 4-6=中, <4=低
```

### 26.4 障碍评估补全 (40题, 10类×4题)

> 补全 §23.1 原仅8题为完整40题

```python
# --- configs/obstacle_questions_full.json ---
# 每类4题, 每题1-5分, 类别得分4-20

OBSTACLE_FULL_QUESTIONS = {
    "time": [
        "我的工作/生活太忙，没有时间来做出改变",
        "我的日程总是被其他事情占满",
        "我找不到固定的时间来执行新习惯",
        "突发事件经常打乱我的计划",
    ],
    "energy": [
        "我每天结束时已经精疲力竭",
        "我的身体状况让我感觉没有精力去改变",
        "早上起来就感觉很疲惫",
        "工作之余我只想休息，不想做其他事",
    ],
    "knowledge": [
        "我不确定什么样的饮食/运动对我最有效",
        "关于健康的信息太多太杂，无法判断",
        "我不知道如何制定适合自己的健康计划",
        "我缺乏关于身体状况的基本知识",
    ],
    "skill": [
        "我不会烹饪健康的饮食",
        "我不会正确地做运动（担心受伤或姿势不对）",
        "我不会使用健康监测工具",
        "我不懂如何在不同场景下灵活调整健康行为",
    ],
    "environment": [
        "我家附近没有适合运动的场所",
        "我的环境中充满不健康的食物诱惑",
        "我的居住/工作条件不支持健康行为",
        "我所在的文化环境不鼓励健康行为",
    ],
    "social": [
        "周围的人觉得我'太讲究'或'小题大做'",
        "家人/朋友的聚餐习惯让我很难坚持",
        "我身边没有人在进行类似改变可以互相支持",
        "他人对我的健康选择表示不理解或嘲笑",
    ],
    "emotion": [
        "压力大的时候我会用吃东西/刷手机来缓解",
        "我害怕失败，所以干脆不开始",
        "过去失败的经历让我对改变失去了信心",
        "焦虑/抑郁让我无法集中精力去改变",
    ],
    "financial": [
        "健康食材/有机食品对我来说太贵了",
        "健身房/运动课程的费用超出预算",
        "购买健康监测设备经济上有困难",
        "当前经济状况让我无法优先考虑健康投入",
    ],
    "habit": [
        "我的旧习惯根深蒂固很难改",
        "每次下决心改变，过不了几天就回到老样子",
        "我的生活节奏已经固定，很难插入新行为",
        "某些不健康行为已经成瘾",
    ],
    "belief": [
        "我觉得'基因决定一切'，改变也没用",
        "我认为自己不是那种能坚持的人",
        "我觉得年纪大了改变也来不及了",
        "我不相信生活方式改变能真正逆转健康问题",
    ],
}

# 障碍→处方调整映射
OBSTACLE_RX_ADJUSTMENT = {
    "time":        {"strategy": "碎片化任务设计",   "max_task_duration": 5},
    "energy":      {"strategy": "低能耗优先",       "priority_rx": ["sleep", "stress"]},
    "knowledge":   {"strategy": "知识补课",         "add_task": "daily_1_tip"},
    "skill":       {"strategy": "技能降级",         "substitute_complex": True},
    "environment": {"strategy": "环境微调",         "tasks": ["remove_trigger", "add_cue"]},
    "social":      {"strategy": "社群缓冲",         "reduce_social_goals": True},
    "emotion":     {"strategy": "情绪优先",         "add_rx": ["emotion_regulation"]},
    "financial":   {"strategy": "零成本方案",       "filter": "free_only"},
    "habit":       {"strategy": "习惯替换",         "method": "gradual_replacement"},
    "belief":      {"strategy": "认知重构",         "tasks": ["success_case", "micro_goal"]},
}
```

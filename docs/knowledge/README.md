# 行健平台 · 知识库全局导航地图

> **AI 提示词（System Prompt 引用）**：当用户输入涉及行为评估、代谢建议或危机处理时，请首先根据本索引定位对应的 `.md` 知识文件，按需 `@` 引用，不要全量加载。
>
> **版本**：V3.1 | **日期**：2026-02-26 | **知识库状态**：L1底座7文件✅，L2域知识13文件✅，L3情境10文件✅，L4语义1文件✅

---

## 一、核心底座逻辑（L1 · Base）

所有 Agent 共享的底层方法论，用于识别用户状态。调用路径：`@docs/knowledge/base/文件名.md`

| 文件 | 用途 | 状态 |
|------|------|------|
| `base/ttm_stages.md` | 判断用户处于「无意向」还是「行动期」，决定干预力度 | ✅ 已就绪 |
| `base/bfr_framework.md` | 六要素（B/F/R/S/T/P）访谈框架，用于挖掘行为真相 | ✅ 已就绪 |
| `base/bpt6_dimensions.md` | 量化用户六维行为倾向（情绪化/效能感等），决定话术语气 | ✅ 已就绪 |
| `base/crisis_protocol.md` | 最高优先级——涉及自残、急症等红线时立即强制跳转 | ✅ 已就绪 |
| `base/mi_interview_framework.md` | MI动机式访谈四过程（Engaging→Focusing→Evoking→Planning）、OARS技巧、变化话语(DARN)识别、TTM×MI矩阵、BPT6×MI适配、维持话语处理 | ✅ 已就绪（待审签） |
| `base/ttm_relapse_protocol.md` | Marlatt复发预防模型、失误vs复发区分、AVE违规效应打断、8大高危情境、S3~S5分阶段策略、BPT6×复发风险画像、多领域联动矩阵 | ✅ 已就绪（待审签） |
| `base/agency_trust_model.md` | V4.0 Agency三态(Passive/Transitional/Active)、Trust Score六维信号、TTM×Agency映射、Observer转化三路径、教练Override、SDT三基本需求、反思深度层次 | ✅ 已就绪（待审签） |

---

## 二、领域知识（L2 · Domain）

支撑干预建议的医学逻辑、体质辨识与生理机制。调用路径：`@docs/knowledge/domain/文件名.md`

### 2.1 中医体质

| 文件 | 用途 | 状态 |
|------|------|------|
| `domain/tcm_constitution_base.md` | 9种中医体质速查（TCM-0~8）、代谢风险映射、BPT6对应、TTM分布、干预策略、兼夹处理、话术变体 | ✅ 已就绪（待审签） |

> **适用Agent**：TCMWellnessAgent、CoachCopilotAgent、MetabolicExpertAgent、BehaviorRxAgent
> **触发关键词**：体质、气虚、阳虚、阴虚、痰湿、湿热、血瘀、气郁、特禀、怕冷、手脚冰凉、腹部肥满、面部油腻、胸闷叹气、过敏
> **来源**：王琦《9种基本中医体质类型分类及诊断表述依据》(北京中医药大学学报2005) + 中华中医药学会ZYYXH/T157-2009

### 2.2 BAPS 评估系统

| 文件 | 用途 | 状态 |
|------|------|------|
| `domain/baps_assessment_system.md` | BAPS v2.0 完整知识库：5大评估工具（BIG5/BPT6/TTM7/CAPACITY/SPI）、171题完整题库、评分算法（Python参考实现）、BehaviorRuntime状态机、RuntimePolicyGate四规则、BapsScoreMapper阶段跃迁、综合报告模板、API接口规范 | ✅ 已就绪 |

> **适用Agent**：全Agent（评估是干预前置条件）；重点：CoachCopilotAgent、BehaviorRxAgent、JourneyCompanionAgent、MotivationAgent
> **触发关键词**：评估、测评、问卷、人格、大五、BPT、行为类型、阶段、TTM、改变、潜力、CAPACITY、成功率、SPI、处方、报告
> **核心工具**：
> - T1 BIG5（50题）→ 人格画像（E/N/C/A/O五维度）
> - T2 BPT6（18题）→ 行为分型（行动/知识/情绪/关系/环境/矛盾六型）
> - T3 TTM7（21题）→ 改变阶段（S0无知无觉~S6内化习惯）
> - T4 CAPACITY（32题）→ 改变潜力（8维度CAPACITY首字母）
> - T5 SPI（50题）→ 成功概率（MASEH五维加权）
> **来源**：大五人格理论 + 跨理论模型（Prochaska & DiClemente）+ 平台自建BPT6/CAPACITY/SPI

### 2.3 代谢生物标志物

| 文件 | 用途 | 状态 |
|------|------|------|
| `domain/metabolic_biomarkers.md` | 血糖/血压/BMI/腰围/血脂/尿酸/TSH/CRP/HRV红绿灯速查、代谢综合征五组分判定、指标联动解读矩阵、体质×代谢风险交叉参照 | ✅ 已就绪（待审签） |

> **适用Agent**：GlucoseAgent、WeightAgent、CardiacRehabAgent、CoachCopilotAgent、MetabolicExpertAgent
> **触发关键词**：血糖、血压、BMI、腰围、血脂、胆固醇、甘油三酯、尿酸、糖化、HbA1c、代谢综合征
> **来源**：ADA Standards 2025 + 中国高血压指南2024 + 中国血脂指南2023 + 中国高尿酸指南2024

### 2.4 压力-皮质醇-代谢轴

| 文件 | 用途 | 状态 |
|------|------|------|
| `domain/stress_cortisol_metabolism.md` | HPA轴机制、急性vs慢性压力判别、HRV解读标准(SDNN/RMSSD/LF:HF)、压力-代谢-睡眠三角联动、行为干预工具箱（4-7-8呼吸/生理叹息/MBSR/表达性写作）、体质×压力交叉 | ✅ 已就绪（待审签） |

> **适用Agent**：StressAgent、SleepAgent、MetabolicExpertAgent、MentalHealthAgent、GlucoseAgent
> **触发关键词**：压力、焦虑、紧张、皮质醇、HRV、心率变异、烦躁、崩溃、喘不过气、腰围增加
> **来源**：Sapolsky《Why Zebras Don't Get Ulcers》+ McEwen Allostatic Load Model + ESC HRV Standards

### 2.5 睡眠科学

| 文件 | 用途 | 状态 |
|------|------|------|
| `domain/sleep_science.md` | 睡眠阶段(N1-N3/REM)功能、CBT-I四组件（刺激控制/睡眠限制/认知重构/卫生教育）、PSQI评估、睡眠-代谢双向联动、OSA筛查(STOP-BANG)、体质×睡眠适配、BPT6×睡眠干预 | ✅ 已就绪（待审签） |

> **适用Agent**：SleepAgent、StressAgent、WeightAgent、MentalHealthAgent、CoachCopilotAgent
> **触发关键词**：睡眠、失眠、早醒、熬夜、嗜睡、打鼾、睡不着、多梦、深度睡眠
> **来源**：AASM临床指南2024 + Walker《Why We Sleep》+ Morin CBT-I Manual + 中国失眠指南2023

### 2.6 运动处方

| 文件 | 用途 | 状态 |
|------|------|------|
| `domain/exercise_prescription.md` | PAR-Q+安全筛查、FITT-VP六要素、Karvonen心率公式、WHO运动量推荐、TTM分阶运动方案、NEAT微运动策略、体质×运动适配、BPT6×运动适配、运动安全红线、运动×代谢指标效果 | ✅ 已就绪（待审签） |

> **适用Agent**：ExerciseAgent、WeightAgent、CardiacRehabAgent、VisionGuideAgent、CoachCopilotAgent
> **触发关键词**：运动、健身、步数、跑步、散步、游泳、瑜伽、力量训练、心率、NEAT
> **来源**：ACSM运动处方指南(11th ed) + WHO身体活动指南2020 + 中国身体活动指南2021

### 2.7 心理健康筛查

| 文件 | 用途 | 状态 |
|------|------|------|
| `domain/mental_health_screening.md` | PHQ-9/GAD-7/PSS-10量表速查、分级Agent行为、情绪-代谢双向联动、行为激活(BA)/认知重构(CR)/正念(MBSR)/ABC情绪日记四项干预技术、BPT6×情绪干预、特殊人群(围产期/老年/青少年) | ✅ 已就绪（待审签） |

> **适用Agent**：MentalHealthAgent、CrisisAgent、StressAgent、CoachCopilotAgent
> **触发关键词**：抑郁、焦虑、情绪低落、紧张、烦躁、无助、崩溃、想哭、没意思、自责、暴饮暴食
> **来源**：PHQ-9(Kroenke 2001) + GAD-7(Spitzer 2006) + PSS-10(Cohen 1983) + APA临床实践指南2023

### 2.8 体重管理

| 文件 | 用途 | 状态 |
|------|------|------|
| `domain/weight_management.md` | BMI/腰围/体脂评估体系、能量平衡/设定点/激素机制、TTM×减重策略、安全减重速率、平台期处理、BPT6×体重适配、体质×体重适配、复胖预防阈值 | ✅ 已就绪（待审签） |

> **适用Agent**：WeightAgent、NutritionAgent、ExerciseAgent、MetabolicExpertAgent、CoachCopilotAgent
> **触发关键词**：体重、减重、减肥、BMI、腰围、体脂、复胖、反弹、平台期、节食
> **来源**：中国超重/肥胖医学营养治疗指南2024 + WHO肥胖指南2023 + Endocrine Society肥胖指南2023

### 2.9 心脏康复协议

| 文件 | 用途 | 状态 |
|------|------|------|
| `domain/cardiac_rehab_protocol.md` | 心脏康复三期模型(I住院/II门诊/III社区)、运动安全评估/红线、恐惧-回避循环破解(系统脱敏4周方案)、药物-运动交互、五大核心组分、BPT6/TTM适配、特殊人群(心衰/PCI/CABG) | ✅ 已就绪（待审签） |

> **适用Agent**：CardiacRehabAgent、CardiacExpertAgent、ExerciseAgent、CoachCopilotAgent
> **触发关键词**：心脏、冠心病、心梗、支架、搭桥、心衰、心脏康复、胸闷、心悸、术后运动
> **来源**：AHA/AACVPR心脏康复指南2024 + ESC心脏康复指南2021 + 中国心脏康复指南2024

### 2.10 营养科学

| 文件 | 用途 | 状态 |
|------|------|------|
| `domain/nutrition_science.md` | 三大营养素/GI/GL、6种膳食模式(中国膳食指南/地中海/DASH/低碳/生酮/间歇断食)、代谢指标×饮食策略(血糖/血脂/血压/尿酸)、微量营养素、实用工具(餐盘法/餐序法/手掌法)、体质×饮食适配 | ✅ 已就绪（待审签） |

> **适用Agent**：NutritionAgent、GlucoseAgent、WeightAgent、MetabolicExpertAgent、CardiacRehabAgent
> **触发关键词**：饮食、营养、热量、碳水、蛋白质、GI、食谱、吃什么、减肥餐、外卖、血糖高怎么吃
> **来源**：中国居民膳食指南2022 + ADA营养治疗标准2025 + DRIs膳食营养素参考摄入量2023

### 2.11 视力保护

| 文件 | 用途 | 状态 |
|------|------|------|
| `domain/vision_protection.md` | 近视分级/远视储备、5D行为目标(户外/屏幕/眼操/营养/睡眠)、20-20-20法则、分龄方案(学龄前/小学/中学/成人)、近视控制手段、眼部安全红线、代谢×视力联动 | ✅ 已就绪（待审签） |

> **适用Agent**：VisionGuideAgent、CoachCopilotAgent、JourneyCompanionAgent
> **触发关键词**：视力、近视、远视、散光、眼镜、OK镜、户外时间、屏幕时间、眼疲劳、度数
> **来源**：WHO世界视力报告2023 + 中国近视防控指南2024 + AAO近视管理指南2023

### 2.12 行为处方设计

| 文件 | 用途 | 状态 |
|------|------|------|
| `domain/behavior_rx_design.md` | Fogg B=MAP模型、12种标准行为改变策略(RxStrategyType)、处方结构(RxPrescriptionDTO)、微行动TINY设计原则、剂量递增模型、SMART目标公式、10干预包映射、冰山模型(水面上友好建议/水面下行为处方引擎) | ✅ 已就绪（待审签） |

> **适用Agent**：BehaviorCoachAgent、MetabolicExpertAgent、CardiacExpertAgent、AdherenceExpertAgent、CoachCopilotAgent
> **触发关键词**：处方、行为、微行动、习惯、目标、坚持不了、怎么做到、方案、干预包
> **来源**：Fogg行为模型(2019) + Michie BCTTv1(2013) + Prochaska变化过程 + 平台BehaviorRx引擎

### 2.13 大五人格行为健康

| 文件 | 用途 | 状态 |
|------|------|------|
| `domain/bfp_behavioral_health_base.md` | 大五人格(OCEAN)五维速查、8种组合风险画像(BFP-01~08)心理机制解析、五型×五维干预策略(营养/运动/认知/社会支持/睡眠)、每日觉察练习库(5型)、行为练习处方(5×5矩阵)、教练引导语库(3级信任)、Agent调用规则 | ✅ 已就绪（待审签） |

> **适用Agent**：CoachCopilotAgent、BehaviorRxAgent、MentalHealthAgent、MetabolicExpertAgent、JourneyCompanionAgent
> **触发关键词**：大五、人格、神经质、外向性、开放性、宜人性、尽责性、BFP、OCEAN、NEO、性格、自律差、冲动、敏感、内向、完美主义
> **来源**：Costa & McCrae NEO-PI-R理论 + 《大五人格行为健康组合》训练讲义 + Bogg & Roberts(2004)尽责性与健康行为元分析

---

## 三、饮食干预情境包（L3 · Dietary Situations）

针对具体生活场景的决策树与行动清单。调用路径：`@docs/knowledge/dietary_sXX_名称.md`

| 编号 | 情境名称 | 触发关键词 | TTM阶段 | 文件 | 状态 |
|------|---------|-----------|---------|------|------|
| S01 | 情绪性进食 | 压力大、烦躁、想喝奶茶、心情不好、暴饮暴食 | S1–S2 | `dietary_s01_emotion.md` | ✅ |
| S02 | 家庭饮食冲突 | 家里、长辈、油盐、劝吃、老公/老婆/父母 | S2–S3 | `dietary_s02_family.md` | ✅ |
| S03 | 自我否定螺旋 | 没救、没毅力、自责、破罐、算了 | S0–S1 | `dietary_s03_spiral.md` | ✅ |
| S04 | 绩效焦虑 | 指标、没达标、焦虑、KPI、越急越胖 | S2–S3 | `dietary_s04_anxiety.md` | ✅ |
| S05 | 职场高压 | 太忙、外卖、没时间、早8晚10 | S1–S2 | `dietary_s05_workplace.md` | ✅ |
| S06 | 工具依赖 | CGM、摘掉、空虚、数据、报警 | S3–S4 | `dietary_s06_tool.md` | ✅ |
| S07 | 社交应酬 | 应酬、客户、劝酒、老板、饭局、爆表 | S2–S3 | `dietary_s07_social.md` | ✅ |
| S08 | 运动恐惧 | 害怕运动、心跳快、健身房、被看、不敢 | S0–S1 | `dietary_s08_exercise.md` | ✅ |
| S09 | 价值矛盾 | 矛盾、人生苦短、开心就好、三分钟热度 | S0–S1摇摆 | `dietary_s09_conflict.md` | ✅ |
| S10 | 习得性无助 | 没救、天生、反正、指标都红、做不到 | S0 | `dietary_s10_helpless.md` | ✅ |

---

## 四、调用规范（Workflow）

每次干预按以下顺序执行，不可跳步：

0. **评估基线**：若用户已完成BAPS评估，调用 `domain/baps_assessment_system.md` 获取BPT6行为类型、TTM7阶段、CAPACITY薄弱维度、SPI成功概率，作为全流程决策依据；未评估用户按快速流程（BPT6+TTM7=39题）优先引导
1. **识别阶段**：调用 `base/ttm_stages.md`，确认用户当前动机阶段（S0~S6），结合BAPS的TTM7评估结果交叉验证；在S0~S2阶段，调用 `base/mi_interview_framework.md` 以MI策略主导对话；若检测到S5复发，立即调用 `base/ttm_relapse_protocol.md`
1.5. **Agency基线**：调用 `base/agency_trust_model.md` 获取Trust Score和Agency三态，决定Agent介入深度（Passive=照料者/Transitional=同行者/Active=镜子）
2. **体质背景**：若用户已有体质评估结果或描述体质关键词，调用 `domain/tcm_constitution_base.md` 匹配体质类型，作为全流程底层背景变量
3. **回溯事实**：通过 `base/bfr_framework.md` 询问行为细节，**严禁仅凭用户的概括性描述直接给建议**
4. **安全对齐**：检查数据是否触发 `base/crisis_protocol.md` 红线，触发则立即停止并跳转
5. **匹配情境**：根据 BFR 结果与触发关键词，进入对应 `dietary_sXX` 的决策树节点
6. **领域匹配**：根据干预方向调用对应L2领域知识——代谢指标异常→`domain/metabolic_biomarkers.md`；压力/HRV问题→`domain/stress_cortisol_metabolism.md`；睡眠问题→`domain/sleep_science.md`；运动方案→`domain/exercise_prescription.md`；情绪问题→`domain/mental_health_screening.md`；体重管理→`domain/weight_management.md`；心脏康复→`domain/cardiac_rehab_protocol.md`；营养饮食→`domain/nutrition_science.md`；视力保护→`domain/vision_protection.md`
7. **行为处方**：调用 `domain/behavior_rx_design.md`，将干预建议转化为可执行的微行动处方（Fogg B=MAP + TINY原则 + SMART目标）
8. **输出干预**：引用 `base/bpt6_dimensions.md` + 体质干预策略 + Agency信任度档位 + BAPS行为类型适配教练姿态 + MI话术技巧，调整为最贴合用户倾向的话术变体

---

## 五、跨情境叠加组合

| 叠加组合 | 发生频率 | 处理顺序 |
|---------|---------|---------| 
| S01 情绪进食 + S03 自我否定 | ⭐⭐⭐ 最高频 | 先S03去道德化，S01 M-Action在信任建立后启动 |
| S05 职场高压 + S07 社交应酬 | ⭐⭐⭐ 职场人群高发 | 两个情境共享「行为嵌入」策略，可合并行为处方 |
| S04 绩效焦虑 + S06 工具依赖 | ⭐⭐ 数字控制型 | 先S04降低反馈频率，再S06建立内感觉知 |
| S10 习得性无助 + S02 家庭冲突 | ⭐⭐ 慢性放弃+环境阻力 | S10优先重建自我效能，S02并行推进 |
| S08 运动恐惧 + S09 价值矛盾 | ⭐⭐ 低动力型 | S09先建立「健康=快乐」联结，再NEAT策略切入S08 |

---

## 六、维护规范

* **L1底座**：每季度审阅一次，方法论更新时同步修订
* **L2领域**：随医学指南实时更新（如ADA血糖标准、JNC血压指南）
* **L3情境**：影子专家审核后升级，审核记录存放于 `/docs/knowledge/review/` 目录
* **版本控制**：所有修改须记录变更原因，文件内注明版本号与日期

---

## 七、Agent 配置文件（不入RAG）

| 文件 | 用途 | 位置 |
|------|------|------|
| `coach_copilot_agent_prompt.md` | CoachCopilotAgent system prompt，Agent初始化时整体注入 | `docs/agents/`，**不参与RAG检索** |

---

*知识库 V3.1 · L1底座7文件(TTM+BFR+BPT6+Crisis+MI+复发预防+Agency信任) + L2域知识13文件(中医体质+BAPS评估+代谢标志物+皮质醇压力+睡眠科学+运动处方+心理筛查+体重管理+心脏康复+营养科学+视力保护+行为处方+大五人格行为健康) + L3情境10文件 + L4语义1文件 = 31文件 · 下一步：各科医师审签 → 影子专家审核 → 升A级*

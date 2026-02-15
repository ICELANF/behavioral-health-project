# 行为健康核心技术三位一体 — 全平台技术深度文档

> **版本**: v1.0 | **日期**: 2026-02-14
> **编制**: Claude Code (Opus 4.6) 基于全平台源码分析
> **范围**: 行为采集 × 行为测评 × 行为处方 — 横向、纵向、融合性全景

---

## 目录

- [一、技术架构总览](#一技术架构总览)
- [二、行为采集层 (Behavior Collection)](#二行为采集层-behavior-collection)
- [三、行为测评层 (Behavior Assessment)](#三行为测评层-behavior-assessment)
- [四、行为处方层 (Behavior Prescription)](#四行为处方层-behavior-prescription)
- [五、三层融合机制](#五三层融合机制)
- [六、动态Agent协同](#六动态agent协同)
- [七、数据流转全景图](#七数据流转全景图)
- [八、技术规格汇总](#八技术规格汇总)

---

## 一、技术架构总览

### 1.1 核心理念

本平台的核心技术基座是 **"采集→测评→处方" 三位一体闭环**，贯穿所有面向用户的服务。每一次用户交互（对话、打卡、设备同步、学习、问卷填写）都隐含着三层处理：

```
┌─────────────────────────────────────────────────────────────────────┐
│                     用户触点 (User Touchpoints)                      │
│  对话 │ 设备同步 │ 打卡 │ 学习 │ 问卷 │ 饮食拍照 │ 挑战 │ 方案互动    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
              ┌──────────────▼──────────────┐
              │    Layer 1: 行为采集          │
              │  (Behavior Collection)       │
              │  26+ 数据源 × 10 维度         │
              │  实时 + 定时 + 隐式           │
              └──────────────┬──────────────┘
                             │
              ┌──────────────▼──────────────┐
              │    Layer 2: 行为测评          │
              │  (Behavior Assessment)       │
              │  5 量表 × 171 题 × 12 批次    │
              │  TTM×BigFive×BPT6×CAPACITY×SPI│
              │  → BehavioralProfile (SSoT)  │
              └──────────────┬──────────────┘
                             │
              ┌──────────────▼──────────────┐
              │    Layer 3: 行为处方          │
              │  (Behavior Prescription)     │
              │  3维计算引擎 × 4专家Agent      │
              │  12策略 × 5交付通道           │
              │  → 个性化行为干预             │
              └──────────────┬──────────────┘
                             │
              ┌──────────────▼──────────────┐
              │    反馈回路 (Feedback Loop)   │
              │  完成→积分→徽章→动机→行为     │
              │  (回到Layer 1重新采集)        │
              └─────────────────────────────┘
```

### 1.2 规模数据

| 维度 | 数量 |
|------|------|
| ORM 模型 | 119 个 |
| Alembic 迁移 | 30 个 |
| API 路由器 | 57 个 |
| API 端点 | 511+ 个 |
| 定时任务 | 13 个 |
| 专业Agent | 12 + 4 个 |
| 行为策略 | 12 种 |
| 评估量表 | 5 套 (171题) |
| 数据采集源 | 26+ 个 |

---

## 二、行为采集层 (Behavior Collection)

### 2.1 采集维度全景

行为采集层覆盖 **10 大维度、26+ 独立数据源**，融合显式采集（用户主动提交）与隐式采集（系统被动记录）两条链路。

```
采集维度 ─┬─ 1. 设备生理 (Device Physiological)
          ├─ 2. 评估问卷 (Assessment Questionnaire)
          ├─ 3. 调查问卷 (Survey Response)
          ├─ 4. 微行动 (Micro-Action Execution)
          ├─ 5. 对话交互 (Chat Interaction)
          ├─ 6. 内容消费 (Content Engagement)
          ├─ 7. 学习进度 (Learning Progress)
          ├─ 8. 挑战参与 (Challenge Participation)
          ├─ 9. 方案互动 (Program Interaction)
          ├─ 10. 饮食营养 (Nutrition/Food)
          └─ 11. 隐式信号 (Implicit Signals)
```

### 2.2 维度 1：设备生理数据

#### 血糖 (Glucose)

| 属性 | 值 |
|------|-----|
| **ORM 模型** | `GlucoseReading` (core/models.py:592-627) |
| **API 文件** | api/device_rest_api.py, api/device_data.py |
| **字段** | user_id, device_id, value, unit, trend, trend_rate, source, meal_tag, notes, recorded_at |
| **来源类型** | cgm (连续监测), finger (指尖), manual (手动) |
| **餐标签** | fasting, before_meal, after_meal, bedtime |
| **触发** | 设备同步 + 手动录入 |
| **下游** | GlucoseReading → 风险评估 → Agent 路由 → 干预生成 |

#### 睡眠 (Sleep)

| 属性 | 值 |
|------|-----|
| **ORM 模型** | `SleepRecord` (core/models.py:678-718) |
| **字段** | sleep_date, sleep_start/end, total_duration_min, awake/light/deep/rem_min, sleep_score, efficiency, awakenings, onset_latency_min, avg_spo2, min_spo2, stages_data(JSON) |
| **触发** | 智能手环/手表设备同步 |

#### 活动 (Activity)

| 属性 | 值 |
|------|-----|
| **ORM 模型** | `ActivityRecord` (core/models.py:721-753) |
| **字段** | steps, distance_m, floors_climbed, calories_total/active, sedentary/light/moderate/vigorous_min, hourly_data(JSON) |
| **触发** | 设备同步 + 每日聚合 |

#### 生命体征 (Vital Signs)

| 属性 | 值 |
|------|-----|
| **ORM 模型** | `VitalSign` (core/models.py:787-823) |
| **类型** | weight(含BMI/体脂/肌肉/水分), blood_pressure(收缩/舒张/脉搏), temperature, spo2 |
| **触发** | 设备同步 + 手动录入 |

#### 心率 & HRV

| 属性 | 值 |
|------|-----|
| **心率模型** | `HeartRateReading` (core/models.py:630-648) — hr(bpm), activity_type(rest/walk/run/sleep) |
| **HRV模型** | `HRVReading` (core/models.py:651-675) — sdnn, rmssd, lf, hf, lf_hf_ratio, stress_score, recovery_score |
| **触发** | 实时设备同步 |

#### 运动记录 (Workout)

| 属性 | 值 |
|------|-----|
| **ORM 模型** | `WorkoutRecord` (core/models.py:756-784) |
| **字段** | workout_type, duration_min, distance_m, calories, avg/max_hr, avg_pace, gps_data(JSON) |
| **类型** | walk, run, cycle, swim, yoga 等 |

#### 设备告警 (Device Alert)

| 属性 | 值 |
|------|-----|
| **ORM 模型** | `DeviceAlert` (core/models.py:1325-1370) |
| **服务** | core/device_alert_service.py |
| **阈值触发** | 高血糖(>10), 低血糖(<4), 血压异常, 心率极值, 睡眠质量差 |
| **端点** | GET /api/v1/device-alerts/my-alerts, /coach/students/{id} |

### 2.3 维度 2-3：评估与调查问卷

#### 评估提交 (Assessment)

| 属性 | 值 |
|------|-----|
| **ORM 模型** | `Assessment` (core/models.py:198-262) |
| **字段** | text_content, glucose_values(JSON), hrv_values(JSON), activity_data(JSON), sleep_data(JSON), user_profile_snapshot(JSON), risk_level, risk_score, primary_concern, primary_agent, secondary_agents(JSON) |
| **触发** | 用户主动提交 + 教练指派 |
| **下游** | Assessment → TriggerRecord → Intervention → Agent 路由 |

#### 触发记录 (Trigger Detection)

| 属性 | 值 |
|------|-----|
| **ORM 模型** | `TriggerRecord` (core/models.py:265-303) |
| **字段** | tag_id, name, category(physiological/behavioral/psychological/environmental), severity(LOW→CRITICAL), confidence |
| **触发** | 实时评估分析 |

#### 调查问卷 (Survey)

| 属性 | 值 |
|------|-----|
| **ORM 模型** | Survey + SurveyQuestion + SurveyResponse + SurveyResponseAnswer |
| **题型** | 15 种：single_choice, multi_choice, text, textarea, rating, date, time, matrix, ranking, dropdown, email, phone, section_break, description, image |
| **特性** | 匿名支持, 断点续填(草稿), BAPS回流映射, 跳题逻辑, 短链码(6字符) |
| **端点** | GET/POST /api/v1/surveys/s/{short_code} (公开无需登录) |

### 2.4 维度 4：微行动执行

| 属性 | 值 |
|------|-----|
| **任务模型** | `MicroActionTask` (core/models.py:1131-1169) |
| **日志模型** | `MicroActionLog` (core/models.py:1172-1200) |
| **领域** | nutrition, exercise, sleep, emotion, stress, cognitive, social |
| **字段** | domain, title, difficulty, source(intervention_plan/coach/system), status, mood_score(1-5) |
| **端点** | GET /today, POST /{id}/complete, POST /{id}/skip, GET /history, GET /stats, GET /facts |
| **聚合服务** | core/behavior_facts_service.py — action_completed_7d, streak_days, completion_rate_30d, domain_activity, avg_mood_score |

### 2.5 维度 5：对话交互

| 属性 | 值 |
|------|-----|
| **会话模型** | `ChatSession` (core/models.py:447-485) |
| **消息模型** | `ChatMessage` (core/models.py:488-523) |
| **隐式信号** | 消息内容(情感分析), 对话主题, 消息频率, 会话时长, 响应延迟 |

### 2.6 维度 6：内容消费

| 属性 | 值 |
|------|-----|
| **内容模型** | `ContentItem` (core/models.py:2013-2048) — article/video/course/card/case |
| **交互模型** | ContentLike, ContentBookmark, ContentComment, LearningProgress, LearningTimeLog |
| **采集** | 点赞、收藏、评论、进度(%, 秒)、分享 |
| **下游** | 内容交互 → UserActivityLog → 学习排行榜 → 推荐引擎 |

### 2.7 维度 7：学习进度

| 属性 | 值 |
|------|-----|
| **积分模型** | `LearningPointsLog` (core/models.py:2143-2158) — source_type, category(growth/contribution/influence) |
| **统计模型** | `UserLearningStats` (core/models.py:2161-2193) — total_minutes, total_points, streaks, quiz_total/passed |
| **连续打卡** | `UserStreak` (core/models.py:3062-3071) — current_streak, longest_streak, grace_used_month |
| **积分规则** | 测验完成+10, 每10分钟+1, 每日登录+5, 分享+20, 评论+10 |

### 2.8 维度 8-9：挑战与方案

#### 挑战参与

| 属性 | 值 |
|------|-----|
| **模型** | ChallengeTemplate, ChallengeDayPush, ChallengeEnrollment, ChallengeSurveyResponse, ChallengePushLog |
| **采集** | 报名时间, 每日推送阅读/完成, 问卷回答, 连续天数, 完成率 |

#### 方案互动 (V004)

| 属性 | 值 |
|------|-----|
| **模型** | ProgramTemplate, ProgramEnrollment, ProgramInteraction |
| **采集** | 每日问卷回答, 照片提交, 设备数据关联, 互动时间戳 |
| **端点** | POST /api/v1/programs/interact (提交回答/照片/设备数据) |

### 2.9 维度 10：饮食营养

| 属性 | 值 |
|------|-----|
| **ORM 模型** | `FoodAnalysis` (core/models.py:1707-1726) |
| **字段** | image_url, food_name, calories, protein, fat, carbs, fiber, advice, meal_type |
| **AI 模型** | qwen2.5vl:7b (Ollama) |
| **端点** | POST /api/v1/food/recognize (上传食物照片) |

### 2.10 维度 11：隐式信号

**文件**: `core/implicit_data.py`

| 信号源 | DB 表 | 字段 | 更新频率 | 窗口 |
|--------|------|------|---------|------|
| **CONV** (对话) | chat_messages | 文本, 情感, 意图, 情绪分数 | 实时 | 14天 |
| **TASK** (任务) | micro_action_tasks + logs | 完成率, 连续天数, 跳过数 | 每日 | 30天 |
| **DEVICE** (设备) | glucose + sleep + activity | CGM值, HRV, 步数, 睡眠时长 | 实时 | 7天 |
| **TRIGGER** (触发) | trigger_records | 触发ID, 触发次数, 风险等级 | 实时 | 30天 |
| **INTERACT** (交互) | user_activity_logs | 日活跃时间, 消息数, 响应延迟 | 每日 | 14天 |
| **PROFILE** (画像) | users + user_profile | 目标, 价值关键词, 身份表达 | 检测时 | 90天 |

### 2.11 采集触发机制

| 类型 | 频率 | 示例 |
|------|------|------|
| **实时** | 事件驱动 | 设备同步, 对话消息, 内容交互, 评估提交 |
| **定时** | APScheduler 13 Job | 每日任务生成(06:00), 方案推送(09:00/11:30/17:30), 提醒检查(每60秒) |
| **批量** | 每日聚合 | 学习统计, 连续打卡, 方案批量分析(23:00), 安全日报(02:00) |

### 2.12 采集数据模型关系图

```
User
├── ChatSession → ChatMessage                    (对话行为)
├── GlucoseReading, HeartRateReading, HRVReading (设备生理)
├── SleepRecord, ActivityRecord, WorkoutRecord   (运动睡眠)
├── VitalSign                                    (生命体征)
├── MicroActionTask → MicroActionLog             (任务执行)
├── Assessment → TriggerRecord → Intervention    (风险评估)
├── SurveyResponse → SurveyResponseAnswer        (问卷调查)
├── ExamResult, BatchAnswer                      (考试认证)
├── ContentLike, ContentBookmark, ContentComment  (内容交互)
├── LearningProgress, LearningTimeLog            (学习进度)
├── ChallengeEnrollment → ChallengeSurveyResponse(挑战参与)
├── ProgramEnrollment → ProgramInteraction       (方案互动)
├── FoodAnalysis                                 (饮食营养)
├── UserActivityLog                              (活动日志)
├── UserStreak, FlipCardRecord, NudgeRecord      (参与度)
├── UserPoint, PointTransaction                  (积分流水)
├── DeviceAlert                                  (设备告警)
└── UserSession                                  (登录会话)
```

---

## 三、行为测评层 (Behavior Assessment)

### 3.1 评估架构概述

测评层实现了一套 **多维度、渐进式、自适应** 的评估框架，将采集层的原始数据转化为结构化的行为画像（BehavioralProfile），作为处方引擎的唯一输入源。

```
评估架构 ─┬─ BAPS 评估管道 (5 量表 × 171 题)
          ├─ 渐进式评估 (12 批次 × 自适应)
          ├─ 风险评估 (设备阈值 + 行为模式)
          ├─ 学习评估 (6 级教练体系)
          ├─ 健康能力评估 (Lv0-Lv5)
          ├─ 障碍评估 (6 类 × 25 题)
          └─ 行为画像生成 (BehavioralProfile SSoT)
```

### 3.2 BAPS 评估管道

**文件**: `api/assessment_pipeline_api.py`

**6 步评估流水线**:

```
Step 1: BAPS 评分 (TTM7 必填 + Big5/BPT6/CAPACITY/SPI 选填)
   ↓
Step 2: 行为画像生成/更新
   ↓
Step 3: 阶段运行时构建 (TTM 阶段判定)
   ↓
Step 4: 干预匹配 (领域 + 策略选择)
   ↓
Step 5: 策略门控评估 (安全/资格检查)
   ↓
Step 6: 输出汇总 (画像 + 阶段决策 + 干预计划)
```

**端点**:
- `POST /api/v1/assessment/evaluate` — 完整管道执行
- `GET /api/v1/assessment/profile/me` — 用户自己的行为画像
- `GET /api/v1/assessment/profile/{user_id}` — 教练查看完整画像
- `GET /api/v1/assessment/intervention-plan/{user_id}` — 实时干预匹配

### 3.3 五大标准化量表

#### A. TTM-7 (改变阶段评估)

**文件**: `core/baps/scoring_engine.py` (行 579-670)

| 属性 | 值 |
|------|-----|
| **题数** | 21 题 (每阶段 3 题, 1-5 李克特量表) |
| **评估阶段** | S0-S6 (7 个阶段) |
| **子维度** | AW 觉察(7题), WI 意愿(7题), AC 行动(7题) |

**七个阶段定义**:

| 阶段 | 代码 | 中文名 | 友好名称 | TTM标准名 |
|------|------|--------|----------|-----------|
| S0 | pre_contemplation | 无知无觉 | 探索期 | 前意向期 |
| S1 | contemplation | 强烈抗拒 | 觉醒期 | 意向期 |
| S2 | preparation | 被动应对 | 思考期 | 准备期 |
| S3 | action_early | 勉强接受 | 准备期 | 行动期(早期) |
| S4 | action | 尝试阶段 | 行动期 | 行动期 |
| S5 | maintenance | 主动实践 | 成长期 | 维持期 |
| S6 | internalized | 内化习惯 | 收获期 | 终止期 |

**评分算法**:
- 每阶段 3 题, 满分 15 分
- 早期阶段(S0-S2): max_score ≥ 10 且 late_stage_max < 10 → 归入早期
- 晚期阶段(S3-S6): max_score ≥ 12 (S6 需更高阈值)
- **置信度**: (最高分 - 次高分) / 最高分 (0.0-1.0)

#### B. Big Five 大五人格

**文件**: `core/baps/scoring_engine.py` (行 206-267)

| 属性 | 值 |
|------|-----|
| **题数** | 50 题 (每维度 10 题, -4 到 +4 分) |
| **五维度** | E 外向性, N 神经质, C 尽责性, A 宜人性, O 开放性 |

**解读层级**: 极高(25~40) → 高(10~24) → 中(-9~9) → 低(-24~-10) → 极低(-40~-25)

**人格→处方映射** (关键融合点):

| 人格特征 | 沟通风格 | 处方调整 |
|----------|---------|---------|
| 高 N (神经质≥65) | 共情型 EMPATHETIC | 安全导向, 降低强度 |
| 高 C (尽责性≥65) | 数据驱动 DATA_DRIVEN | 循证导向, 提供数据 |
| 高 E (外向性≥65) | 挑战型 CHALLENGE | 竞争激励, 社群推动 |
| 高 A (宜人性≥65) | 社会认同 SOCIAL_PROOF | 社区支持, 家人关怀 |
| 高 O (开放性≥65) | 探索型 EXPLORATORY | 创新方法, 新知引导 |

#### C. BPT-6 (行为分型)

**文件**: `core/baps/scoring_engine.py` (行 342-405)

| 属性 | 值 |
|------|-----|
| **题数** | 18 题 (每类型 3 题, 1-5 量表) |
| **六种类型** | Action 行动型, Knowledge 知识型, Emotion 情绪型, Relation 关系型, Environment 环境型, Ambivalent 矛盾型 |

**分类逻辑**:
- 主导型: 单项 ≥12 分
- 混合型: ≥2 项 ≥10 分
- 分散型: 全部 7-9 分

**类型描述与干预策略**:

| 类型 | 描述 | 首选干预 |
|------|------|---------|
| 行动型 | 说干就干，执行力强 | 直接行动方案, 高强度挑战 |
| 知识型 | 知识充分，行动不足 | 认知重构, 微行动降低门槛 |
| 情绪型 | 情绪主导行为 | 情绪释放, 共情支持 |
| 关系型 | 需要关系支持 | 社群陪伴, 教练陪练 |
| 环境型 | 环境驱动行为 | 环境重设, 刺激控制 |
| 矛盾型 | 意愿与恐惧并存 | 决策平衡, 渐进脱敏 |

#### D. CAPACITY (改变潜力)

**文件**: `core/baps/scoring_engine.py` (行 409-471)

| 属性 | 值 |
|------|-----|
| **题数** | 32 题 (每维度 4 题, 1-5 量表) |
| **总分范围** | 32-160 分 |

**八大维度**:

| 维度 | 代码 | 含义 | 分值范围 |
|------|------|------|---------|
| C1 | 觉察力 | 对自身问题的认知程度 | 4-20 |
| A1 | 自主感 | 自我决定与控制感 | 4-20 |
| P | 匹配度 | 目标与自身的适配程度 | 4-20 |
| A2 | 资源 | 可利用资源的丰富度 | 4-20 |
| C2 | 承诺 | 改变的承诺与决心 | 4-20 |
| I | 身份 | 与新身份的认同度 | 4-20 |
| T | 时间 | 可用时间的充裕度 | 4-20 |
| Y | 期待 | 对改变结果的期望 | 4-20 |

**潜力分级**: 高(128-160) → 中高(96-127) → 中(64-95) → 低(32-63)

**弱维度→干预领域映射**:
- C1 信心弱 → emotion, cognitive 干预
- A2 资源弱 → social 支持
- P 计划弱 → nutrition, exercise 规划
- T 时间弱 → exercise, sleep 优化

#### E. SPI (成功可能性指数)

**文件**: `baps/spi_calculator.py` (行 1-162)

| 属性 | 值 |
|------|-----|
| **快速版** | 5 题, 5 分钟 |
| **完整版** | 50 题 (10题/维度), 20 分钟 |

**五维度加权**:

| 维度 | 权重 | 含义 |
|------|------|------|
| M 动机 | 30% | 改变动力强度 |
| A 能力 | 25% | 实施改变的能力 |
| S 支持 | 20% | 社会支持网络 |
| E 环境 | 15% | 环境促进/阻碍 |
| H 历史 | 10% | 既往改变经验 |

**快速 SPI 公式**:
```
quick_spi = (trigger×0.25 + level_map×0.30 + capability×0.20 + support×0.15 + urgency×0.10) × 10
```

**完整 SPI 公式**:
```
spi_score = (trigger_total/125) × psy_coefficient × (urgency_score/30) × 100
```

**成功概率分级**: 极高(40-50, >75%) → 高(30-40, 50-75%) → 中(20-30, 30-50%) → 低(10-20, 15-30%) → 极低(0-10, <15%)

**心理层级** (SPI Part 2, 5 级 × 4 题):
1. 完全对抗 (psy_coefficient = 0.3)
2. 抗拒与反思 (0.5)
3. 妥协与接受 (0.7)
4. 顺应与调整 (0.85)
5. 全面臣服 (1.0)

### 3.4 渐进式评估系统

**文件**: `baps/progressive_assessment.py` (448 行)

**问题**: 171 题需要 30-45 分钟, 导致用户放弃
**方案**: 分为 12 个自适应批次, 每批 2-3 分钟

```
Batch 1:  B1_TTM7_CORE (7题, 必填)       → 解锁: behavioral_stage
Batch 2:  B2_SPI_QUICK (5题, 必填)        → 解锁: readiness_level
Batch 3:  B3_SPI_TRIGGERS (13题)
Batch 4:  B4_SPI_TRIGGERS2 (12题)         → 依赖 B3
Batch 5:  B5_SPI_PSY (20题)               → 依赖 B4, 解锁: readiness_deep
Batch 6:  B6_SPI_URGENCY (5题)            → 依赖 B5, 解锁: spi_full
Batch 7:  B7_BPT6 (18题)                  → 解锁: behavior_type
Batch 8:  B8_BIG5_PART1 (25题)            → 解锁: big5_partial
Batch 9:  B9_BIG5_PART2 (25题)            → 解锁: big5_full
Batch 10: B10_CAPACITY_PART1 (16题)       → 解锁: capacity_partial
Batch 11: B11_CAPACITY_PART2 (16题)       → 解锁: capacity_full
Batch 12: B12_TTM7_DEEP (14题)            → 依赖 B1, 解锁: stage_deep
```

**自适应推荐算法** (AdaptiveRecommender):
1. 过滤已完成批次
2. 检查依赖关系
3. 根据用户阶段调整优先级:
   - S0-S1: 提升 SPI 优先级 (-2)
   - S4-S6: 提升 Big5/Capacity, 降低 TTM7_DEEP (+5)
4. 返回 Top 3 推荐批次

### 3.5 风险评估

#### 设备阈值风险

| 指标 | 危险高 | 警告高 | 警告低 | 危险低 |
|------|--------|--------|--------|--------|
| 血糖 | ≥13.0 (R3) | ≥10.0 (R2) | ≤4.0 (R2/R3) | ≤3.0 (R3) |
| 心率(静息) | ≥120 (R3) | ≥100 (R2) | ≤60 (R2) | ≤40 (R3) |

**风险等级**: R0 正常 → R1 轻度 → R2 中度 → R3 高危 → R4 危机

#### 触发器风险评分

```
1. 识别严重度: CRITICAL > HIGH > MEDIUM > LOW
2. 统计各严重度分布
3. 映射到主要关注点
4. 计算综合风险分数
```

### 3.6 健康能力评估

**文件**: `baps/health_competency_assessment.py` (114 行)

| 等级 | 名称 | 阈值 | 阶段 |
|------|------|------|------|
| Lv0 | 完全无知者 | 0 | 需求 |
| Lv1 | 问题觉察者 | ≥3/5 | 觉察 |
| Lv2 | 方法学习者 | ≥3/5 | 行动 |
| Lv3 | 情境适配者 | ≥3/5 | 调控 |
| Lv4 | 自我驱动者 | ≥3/5 | 迭代 |
| Lv5 | 使命实践者 | ≥3/5 | 转化 |

### 3.7 障碍评估

**文件**: `baps/obstacle_assessment.py` (109 行)

**精简版 (v2)**: 25 题 / 6 类别

| 类别 | 题数 | 内容 |
|------|------|------|
| 认知-心理 | 5 | 知识缺乏, 认知偏差 |
| 情绪-动机 | 4 | 焦虑, 低动力 |
| 环境-资源 | 4 | 设备不足, 时间限制 |
| 社会-关系 | 4 | 缺乏支持, 人际冲突 |
| 生理-习惯 | 4 | 身体限制, 旧习惯 |
| 系统-持续 | 4 | 制度障碍, 难以持续 |

**分级**: 严重(≥60) → 中度(30-59) → 轻度(<30)

### 3.8 改变动因评估

**文件**: `baps/cause_scoring.py` (57 行)

**24 题 / 6 类别**:
- 内在动因 (C1-C4)
- 外部事件 (C5-C8)
- 情绪驱动 (C9-C12)
- 认知变化 (C13-C16)
- 能力增长 (C17-C20)
- 社交影响 (C21-C24)

**阈值**: 强(≥15) → 中(≥10) → 弱(<10)

### 3.9 行为画像 (BehavioralProfile — Single Source of Truth)

**ORM 模型**: `BehavioralProfile` (core/models.py:956-1028)

```python
class BehavioralProfile:
    # 阶段
    current_stage: S0-S6            # TTM 当前阶段
    stage_confidence: float         # 阶段置信度
    stage_stability: STABLE/UNSTABLE/FLUCTUATING

    # BAPS 向量
    big5_scores: JSON               # {E, N, C, A, O}
    bpt6_type: str                  # 行为分型
    capacity_total: float           # 改变潜力总分
    spi_score: float                # 成功可能性指数
    ttm7_stage_scores: JSON         # 各阶段原始分
    ttm7_sub_scores: JSON           # AW/WI/AC 子维度

    # 领域
    primary_domains: JSON           # 主要干预领域
    domain_details: JSON            # 领域详细数据

    # 交互
    interaction_mode: EMPATHY/CHALLENGE/EXECUTION
    psychological_level: L1-L5

    # 风险
    risk_flags: JSON                # 风险标记
```

**交互模式推断** (Stage × BPT6):
- **共情模式** (S0-S1): 倾听理解, 不施压
- **挑战模式** (S2-S3): 适度激励, 引导行动
- **执行模式** (S4-S6): 系统规划, 监督反馈

### 3.10 六级教练晋升评估

**三文件统一权威** (2026-02-08 对齐):

| 级别 | 名称 | 成长分 | 贡献分 | 影响力 | 考试 | 同道者 |
|------|------|--------|--------|--------|------|--------|
| L0 | 观察员 | 0 | 0 | 0 | 否 | 0 |
| L1 | 成长者 | 100 | 0 | 0 | 否 | 0 |
| L2 | 分享者 | 500 | 50 | 0 | 否 | 0 |
| L3 | 教练 | 800 | 200 | 50 | 是 | 4×L1 |
| L4 | 促进师 | 1500 | 600 | 200 | 是 | 4×L2 |
| L5 | 大师 | 3000 | 1500 | 600 | 是 | 4×L3 |

---

## 四、行为处方层 (Behavior Prescription)

### 4.1 处方引擎架构

**核心文件**: `behavior_rx/behavior_rx_engine.py` (916 行)

行为处方引擎是一台 **三维正交计算机**，输入三个独立维度，输出个性化行为干预方案:

```
       TTM Stage (S0-S6)        ← 维度 1: 我在哪？(改变阶段)
            ×
    BigFive Personality (O/C/E/A/N)  ← 维度 2: 我是谁？(人格特质)
            ×
     CAPACITY Score (0-1)       ← 维度 3: 我能做什么？(改变潜力)
            ↓
    ┌───────────────────────┐
    │  BehaviorRxEngine     │
    │  compute_rx()         │
    │  (纯函数, 无副作用)    │
    └───────────┬───────────┘
                ↓
        RxPrescriptionDTO
        (12 字段完整处方)
```

### 4.2 处方输入：RxContext

```python
RxContext:
    # 维度 1: TTM
    ttm_stage: 0-6                # 当前改变阶段
    stage_readiness: 0-1          # 阶段就绪度
    stage_stability: 0-1          # 阶段稳定性

    # 维度 2: 人格
    personality: BigFiveProfile   # {O, C, E, A, N} 各 0-100

    # 维度 3: 潜力
    capacity_score: 0-1           # 改变潜力归一化
    self_efficacy: 0-1            # 自我效能感

    # 上下文
    domain_data: Dict             # 血糖, BP, 恐惧分数, 用药等
    active_barriers: List[str]    # 6 种障碍类型
    recent_adherence: 0-1         # 近期依从性
    risk_level: str               # low/normal/elevated/high/critical
```

### 4.3 处方输出：RxPrescriptionDTO

```python
RxPrescriptionDTO:
    # 身份
    rx_id: UUID                           # 处方唯一ID
    agent_type: ExpertAgentType           # 4 种专家类型

    # 核心处方 (6 字段)
    goal_behavior: str                    # 目标行为描述
    strategy_type: RxStrategyType         # 主策略 (12 种之一)
    secondary_strategies: List[str]       # 2-3 个备选策略
    intensity: RxIntensity                # 强度等级
    pace: str                             # "slow" | "standard" | "fast"
    communication_style: CommunicationStyle  # 沟通风格

    # 执行参数 (4 字段)
    micro_actions: List[MicroAction]      # 难度校准的微行动
    reward_triggers: List[RewardTrigger]  # 奖励触发条件
    resistance_threshold: float           # 策略切换阈值
    escalation_rules: List[EscalationRule]  # 升级规则

    # 上下文
    domain_context: Dict                  # 领域上下文
    ttm_stage: int                        # TTM 阶段
    confidence: float                     # 置信度 (0.5-0.98)
    reasoning: str                        # 推理审计轨迹
```

### 4.4 十二大行为改变策略

**配置**: `configs/rx_strategies.json` (~2000 行)

| # | 策略类型 | 中文名 | 适用阶段 | 核心机制 |
|---|---------|--------|----------|----------|
| 1 | consciousness_raising | 认知提升 | S0-S2 | 信息觉醒, 增加对问题的认识 |
| 2 | dramatic_relief | 情绪唤醒 | S0-S1 | 情感触动, 激发改变动机 |
| 3 | self_reevaluation | 自我重估 | S1-S2 | 身份对齐, 重新评价自我形象 |
| 4 | decisional_balance | 决策平衡 | S1-S2 | 利弊权衡, 建立改变理由 |
| 5 | cognitive_restructuring | 认知重构 | S2-S4 | 信念修正, 改变思维模式 |
| 6 | self_liberation | 自我解放 | S2-S3 | 承诺与选择, 迈出第一步 |
| 7 | stimulus_control | 刺激控制 | S3-S5 | 环境重设, 改变触发条件 |
| 8 | contingency_management | 应急管理 | S3-S5 | 即时强化, 行为-奖励绑定 |
| 9 | habit_stacking | 习惯堆叠 | S3-S5 | 行为链接, 新旧习惯串联 |
| 10 | systematic_desensitization | 渐进脱敏 | S1-S4 | 分级暴露 (心脏康复专用) |
| 11 | relapse_prevention | 复发预防 | S3-S6 | 高风险应对, 维持机制 |
| 12 | self_monitoring | 自我监测 | S2-S6 | 自我觉察, 数据追踪 |

**阶段→策略映射矩阵**:

| 阶段 | 主策略 | 辅策略 |
|------|--------|--------|
| S0 前意向 | consciousness_raising | dramatic_relief |
| S1 意向 | decisional_balance | self_reevaluation |
| S2 准备 | self_liberation | cognitive_restructuring |
| S3 行动 | stimulus_control | contingency_management, habit_stacking |
| S4+ 维持 | relapse_prevention | self_monitoring |

### 4.5 强度矩阵 (Stage × Capacity → Intensity)

```
                  低潜力(<0.35)    中潜力(0.35-0.65)    高潜力(>0.65)
S0-S1 前意向/意向    MINIMAL           LOW                LOW
S2 准备             LOW               MODERATE           MODERATE
S3 行动             LOW               MODERATE           HIGH
S4+ 维持            MODERATE          HIGH               INTENSIVE
```

**潜力→难度校准**:
```python
if capacity < 0.3:    adjusted_difficulty *= 0.6   # 大幅降低
elif capacity < 0.5:  adjusted_difficulty *= 0.8   # 适度降低
elif capacity > 0.7:  adjusted_difficulty *= 1.1   # 略微提升
```

### 4.6 障碍→策略覆盖

| 障碍类型 | 推荐策略 |
|---------|---------|
| 恐惧 (fear) | 认知重构 + 渐进脱敏 |
| 健忘 (forgetfulness) | 习惯堆叠 + 刺激控制 |
| 低动力 (low_motivation) | 情绪唤醒 + 决策平衡 |
| 认知不足 (cognitive) | 认知提升 + 认知重构 |
| 经济困难 (economic) | 决策平衡 (Plan B) |
| 关系缺乏 (relational) | 自我解放 |

### 4.7 四大专家 Agent

#### 冰山模型 (Iceberg Model)

```
用户看到: 专业领域内容
         (血糖建议 / 运动指导 / 用药提醒)

         ↓ (水面线)

系统运行: RxPrescriptionDTO
         (strategy: stimulus_control, intensity: moderate, ...)

         ↓ (水面下)

基础: 行为诊断 (BAPS 数据)
```

#### Agent 1: BehaviorCoachAgent (行为教练, S0-S2 前置)

**文件**: `behavior_rx/agents/behavior_coach_agent.py` (427 行)

| 属性 | 值 |
|------|-----|
| **角色** | 上游守门人, S0-S2 认知准备 |
| **特点** | 半透明 Rx 模式 (用户可见行为科学术语) |
| **规则数** | 15 条专家规则 |

**阶段特化内容**:

| 阶段 | 聚焦 | 策略 | 沟通方式 |
|------|------|------|---------|
| S0 | 意识激活 | 认知提升 | 温和引入 |
| S1 | 认知深化 | 决策平衡 | 正常化矛盾 |
| S2 | 承诺建立 | 自我解放 | 首次行动规划 |
| S3+ | 移交准备 | 与领域协调 | 专家委派 |

**关键规则**:
- BC-001: 阶段≤1 且 readiness<0.4 → 强制 consciousness_raising
- BC-002: 阶段≤2 且 neuroticism>65 → 强制 intensity=low (情绪安全)
- BC-006: 阶段≥3 且 readiness>0.6 → 准备移交到领域 Agent
- BC-011: self_efficacy<0.15 → 紧急效能感支持 (优先级 10)

#### Agent 2: MetabolicExpertAgent (代谢专家)

**文件**: `behavior_rx/agents/metabolic_expert_agent.py` (393 行)

| 属性 | 值 |
|------|-----|
| **角色** | 代谢数据 → 行为干预 (血糖/营养/体重) |
| **规则数** | 20 条专家规则 |
| **领域事实** | 血糖(空腹/餐后/HbA1c), 体重(BMI/平台期), 血压, 行为依从性 |

**关键规则**:
- ME-001: 空腹血糖>7.0 → 空腹干预聚焦 (优先级 8)
- ME-006: 血糖最低<3.9 → 低血糖安全警报 (优先级 10)
- ME-010: 用药依从性<0.7 → 触发移交到依从性Agent
- ME-013: 高 N 且饮食焦虑 → 强制认知重构

#### Agent 3: CardiacExpertAgent (心脏康复专家)

**文件**: `behavior_rx/agents/cardiac_expert_agent.py` (768 行)

| 属性 | 值 |
|------|-----|
| **角色** | 运动处方 + 恐惧-回避循环打破 |
| **核心特长** | 渐进脱敏 (Systematic Desensitization) |
| **规则数** | 18 条专家规则 |

**康复阶段 × TTM 映射**:

| 康复阶段 | TTM 范围 | 最大 RPE | 聚焦 |
|---------|---------|---------|------|
| Phase I 住院 | S0-S1 | 11 | 教育 |
| Phase II 早期 | S1-S2 | 12 | 最小暴露 |
| Phase II 康复 | S2-S3 | 13 | 渐进训练 |
| Phase III 维持 | S4-S5 | 14 | 自我管理 |

**3 周脱敏方案** (恐惧分数 ≥40):
- **第 1 周**: 原地踏步 + 心率自测 + 焦虑锚定
- **第 2 周**: 室内步行 + 心率区间熟悉 + "正常化" 认知框架
- **第 3 周**: 户外步行(有伴) + 信心扩展 + 社会支持

**安全护栏**:
- 心率 >85% 最大 → 降至最低强度
- RPE >14 → 下调强度
- 近期胸痛 → 完全停止
- 血压 >160/100 → 暂停运动处方

#### Agent 4: AdherenceExpertAgent (依从性专家)

**文件**: `behavior_rx/agents/adherence_expert_agent.py` (834 行)

| 属性 | 值 |
|------|-----|
| **角色** | 横切面行为链设计 (跨所有领域) |
| **核心洞察** | "不依从 = 行为链设计缺陷, 而非患者意愿问题" |
| **规则数** | 22 条专家规则 |

**五种依从行为类型**:
1. **用药** — 最高频 (每日/多次)
2. **门诊** — 周期性 (季度/半年)
3. **检验** — 事件驱动 (就诊后/方案内)
4. **饮食医嘱** — 每日习惯链
5. **运动医嘱** — 固定时间表

**用药链设计** (针对健忘型):
```
"早晨" → 习惯锚点: "刷牙后"
       → 行为: 药盒放在牙刷旁
       → 链条: 刷牙 → 拿药 → 服药 → 打勾
```

**MMAS 阈值** (Morisky 用药依从性量表):
- 8.0: 高依从 (优秀)
- 6.0-8.0: 中依从 (管理)
- <6.0: 低依从 (干预)

### 4.8 Agent 移交协议

**5 种移交类型**:

| 类型 | 方向 | 触发条件 |
|------|------|---------|
| STAGE_PROMOTION | 教练 → 领域 | 阶段≥3 且 readiness>0.6 |
| STAGE_REGRESSION | 领域 → 教练 | 阶段回退 2+ 级 |
| DOMAIN_COORDINATION | 代谢 ↔ 心脏 | 检测到多病共存 |
| CROSS_CUTTING | 任意 → 依从性 | 漏药≥3 或 就诊逾期≥14天 |
| EMERGENCY_TAKEOVER | 任意 → 教练 | self_efficacy<0.2 且 stability<0.3 |

### 4.9 Agent 协作编排器

**文件**: `behavior_rx/core/agent_collaboration_orchestrator.py`

**8 种协作场景**:

| 场景 | 主Agent | 辅Agent | 合并策略 | 触发 |
|------|---------|---------|---------|------|
| 新用户评估 | Coach | 代谢/心脏 | coach_first | 首次用户 |
| 血糖异常 | 代谢 | 依从性 | metabolic_primary | 高血糖 |
| 运动恐惧 | Coach | 心脏 | coach_first_then_handoff | 恐惧≥25, 阶段≤2 |
| 多病共存 | 领域 | 代谢+心脏+依从性 | parallel_merge | 同时有代谢和心脏数据 |
| 阶段回退 | Coach | 当前Agent | coach_override | 效能感崩溃 |
| 就诊前 | 依从性 | 领域 | adherence_overlay | 3天内有门诊 |
| 依从警报 | 当前 | 依从性 | adherence_overlay | 漏药≥4 或 就诊逾期≥30天 |
| 领域协调 | 当前 | 共病领域 | cooperative | 共享病情 |

**合并策略**:
- `coach_override`: 教练响应替代领域
- `primary_first`: 主Agent响应 + 辅Agent叠加
- `parallel_merge`: 双Agent响应整合 (无冲突)
- `adherence_overlay`: 在领域Rx上叠加依从性微行动
- `cooperative`: 双Agent运行, 结果交叉引用

### 4.10 冲突解决 (RxConflictResolver)

**文件**: `behavior_rx/core/rx_conflict_resolver.py` (437 行)

| 冲突类型 | 解决规则 | 示例 |
|---------|---------|------|
| 强度不一致 | 保守原则 (取最低) | 代谢(高) vs 心脏(中) → 用中 |
| 策略不一致 | 阶段适配 (取最适合当前TTM的) | S3 阶段偏好列表决定 |
| 指令冲突 | 教练仲裁 (教练最终决定) | 教练(高优先)覆盖其他 |
| 医学边界 | 安全至上 (医学规则压倒行为规则) | V007 PolicyEngine 医学规则 |
| 行为优先 | TTM驱动策略排名 | 当前阶段策略列表决定胜者 |

### 4.11 五大交付通道

#### 通道 1: 每日微行动

```
MicroActionTask (DB)
    ↓ 每日生成: 最多 3 个任务
    ↓ 来源: intervention_plan (来自 InterventionMatcher)
    ↓ 字段: domain, title, difficulty(由capacity_score校准)
    ↓
UI: 今日微行动列表
    → 完成按钮 → 奖励触发
    → 跳过按钮 → 障碍分析
    ↓
追踪: MicroActionLog → BehaviorFactsService
```

**示例**:
```json
{
  "title": "晚餐时间提前到18:30",
  "description": "根据你的血糖数据，晚餐提前可以改善夜间血糖",
  "domain": "metabolic",
  "difficulty": "easy",
  "source_id": "rx-uuid-12345"
}
```

#### 通道 2: AI 推送建议

```
设备数据 (7天窗口)
    ↓ 信号采集
    ├─ 血糖趋势 → 推荐 HF-20 (血糖快问)
    ├─ 睡眠差 → 推荐 HF-50 (睡眠评估)
    ├─ 低活动 → 推荐运动量表
    └─ 焦虑信号 → 推荐 PHQ-9
    ↓
教练看板: "建议为此学员推送 HF-20"
    ↓
一键下发: 预填写推送表单
```

#### 通道 3: 智能方案 (V004)

**示例: 血糖-14天方案** (15天, 3推/天):

```
第 1-3 天: 血糖意识 (consciousness_raising)
  - 09:00: "您的空腹血糖: 7.2, 这意味着什么"
  - 14:00: "午餐选择如何影响下午血糖"
  - 18:00: "晚餐时间技巧: 稳定过夜血糖"

第 4-7 天: 行动准备 (decisional_balance + self_liberation)
  - "提前晚餐的好处 vs 保持现状的代价"
  - "您的第一个承诺: 将晚餐移到18:30"

第 8-14 天: 习惯建立 (stimulus_control + habit_stacking)
  - "设置18:00手机闹钟准备晚餐"
  - "将晚餐准备链接到您的晚间惯例"
  - 每日追踪 + 奖励

第 15 天: 毕业 + 维持计划
```

#### 通道 4: 对话响应集成

```
用户消息
    ↓
MasterAgent Step 4: Expert路由 (via ExpertAgentRouter)
    ↓
如果匹配专家领域:
    → Expert Agent process()
    → 计算 RxPrescriptionDTO
    → apply_domain() → 可见消息 (冰山水面上)
    ↓
返回用户:
    可见: 专业领域建议
    隐藏: Rx 处方 (审计轨迹, 分析用)
```

#### 通道 5: 定时任务

```
13 个 APScheduler 任务:
  - 06:00 每日任务生成
  - 09:00 / 11:30 / 17:30 方案推送
  - 00:05 方案日推进
  - 23:00 批量行为分析
  - 每 60 秒 提醒检查
  - 每 300 秒 审批推送处理
```

### 4.12 处方置信度计算

```python
confidence = 0.7  # 基准

# 阶段稳定性加成
confidence += context.stage_stability * 0.15      # 最大 +0.15

# 策略-阶段对齐加成
if strategy in STAGE_STRATEGY_MATRIX[stage]:
    rank = index_in_sorted_list
    confidence += max(0, 0.1 - rank * 0.02)       # 排名越前加成越多

# 数据完整性加成
confidence += context.recent_adherence * 0.05      # 最大 +0.05

# 最终范围: 0.5 - 0.98
```

### 4.13 干预效果评分 (IES)

```
IES = 0.40 × completion_rate
    + 0.20 × min(days_active / 30, 1.0)
    + 0.25 × stage_progression        # 0-3 可能
    - 0.15 × min(resistance_events / 10, 0.3)

推荐:
  ≥0.70 → 继续当前方案
  0.40-0.70 → 调整参数
  <0.40 → 切换策略
```

### 4.14 处方数据持久化

**3 个核心表** (迁移 030):

| 表名 | 列数 | 用途 |
|------|------|------|
| `rx_prescriptions` | 25 | 处方主表 (3维输入 + 12字段输出 + 审计) |
| `rx_strategy_templates` | 21 | 12 策略模板 (含领域变体 + 人格修正器) |
| `agent_handoff_log` | 16 | Agent间移交日志 (触发→接受→完成) |

---

## 五、三层融合机制

### 5.1 MasterAgent 作为中央融合枢纽

**文件**: `core/master_agent_v0.py` (6,874 行) — 9步流水线

```
Step 1:   输入采集 (Collection)      — 设备数据 + 用户消息
Step 2:   上下文构建 (Collection)    — 聚合 7 天数据窗口
Step 2.5: 安全 L1 (Assessment)      — 输入过滤 (关键词+PII+意图)
Step 3:   触发分析 (Assessment)      — 风险评估 + 触发检测
Step 3.5: 专家路由 (Fusion)         — ExpertAgentRouter 关键词+领域匹配
Step 4:   Agent路由 (Assessment)     — 12 Agent 选择 + PolicyEngine 门控
Step 5:   Agent执行 (Assessment)     — 专业评估 + Rx 计算
Step 6:   多Agent协调 (Fusion)       — 冲突解决 + 合并策略
Step 7:   策略门控 (Assessment)      — V007 PolicyEngine 5步流水线
Step 7.5: 安全 L3 (Assessment)       — 生成护栏 (域边界 + 注入防护)
Step 8:   响应合成 (Prescription)    — LLM 或模板生成可见响应
Step 8.5: 安全 L4 (Prescription)     — 输出过滤 (医学声明 + 免责声明)
Step 9:   回写 (Collection)          — 任务生成 + 审计轨迹
```

### 5.2 RAG 知识系统作为评估增强

**文件**: `core/knowledge/rag_middleware.py` (179 行)

```
1. 采集: 用户查询 + Agent上下文
   ↓
2. 检索: 3 层检索层次
   ├─ 租户私有 (boost +0.15)
   ├─ 领域知识 (boost +0.08)
   └─ 平台公共 (boost +0.00)
   ↓
3. 评估: 相关性评分 + 证据分层(T1-T4)
   ↓
4. 处方: 注入 system_prompt → LLM 增强响应
```

### 5.3 安全管道作为跨层评估

**文件**: `core/safety/pipeline.py` (121 行)

```
L1 输入过滤 (采集验证):
    ├─ 消息扫描: 关键词, PII, 意图
    ├─ 分类: normal | warning | blocked | crisis
    └─ 危机 → 立即升级旁路

L2 RAG 安全 (评估增强):
    ├─ 检索结果过滤
    ├─ 证据分层权重 (T1-T4)
    └─ 医学声明标记

L3 生成护栏 (处方约束):
    ├─ LLM system_prompt 注入
    ├─ 域边界执行
    └─ 提示注入防护

L4 输出过滤 (处方终审):
    ├─ 医学声明检测
    ├─ 严重性分级
    └─ 免责声明注入
```

### 5.4 定时任务作为批量融合编排

| 任务 | 调度 | 采集 | 评估 | 处方 |
|------|------|------|------|------|
| daily_task_generation | 06:00 | 活跃用户集 | 生成今日任务 | 推送微行动 |
| reminder_check | 每60秒 | 到期提醒查询 | 逾期状态评估 | 发送提醒通知 |
| process_approved_pushes | 每5分钟 | 审批队列 | 就绪检查 | 移动推送 |
| program_advance_day | 00:05 | 活跃注册 | 日程推进评估 | 自动推进阶段 |
| program_push_* | 09/11:30/17:30 | 模板按阶段 | 互动率计算 | 生成/发送推送 |
| program_batch_analysis | 23:00 | 互动日志 | 行为模式分析 | 生成洞察 |
| safety_daily_report | 02:00 | SafetyLog | 聚合事件 | 生成管理报告 |
| agent_metrics_aggregate | 01:30 | Agent执行日志 | 计算日指标 | 存储 metrics_daily |

### 5.5 教练工作流作为监督融合

```python
# GET /api/v1/coach/dashboard
def get_coach_dashboard(coach_user):
    for student in my_students:
        # 采集: 最新评估 + 设备数据 + 行为画像
        latest_assessment = query(Assessment).filter(user_id=student.id)
        device_status = get_latest_device_data(student.id)
        profile = student.profile

        # 评估: 风险等级 + 阶段 + 设备异常
        risk_level = assessment.risk_level
        current_stage = profile.get("current_stage", "S0")

        # 处方: 教练行动建议
        if risk_level == "high": actions.append("send_coaching_message")
        if device_status.glucose > 10: actions.append("suggest_nutrition_program")
        if current_stage <= 2: actions.append("recommend_coach_assessment")
```

### 5.6 激励系统 (V003) 作为行为反馈融合

```
采集: 行为事件 (打卡, 微行动完成)
    ↓
评估: 连续天数 + 里程碑阈值检查
    ↓
处方: 徽章/积分奖励 + 激励消息
    ↓
反馈: 奖励激发未来行为 (→ 回到采集)
```

**双向反馈回路**:

```
任务完成 (采集)
    → MicroActionLog (记录)
    → 里程碑检查 (评估)
    → 徽章奖励 (处方)
    → 用户动机提升 (采集反馈)

设备读数 (采集)
    → 异常检测 (评估)
    → 干预触发 (处方)
    → 提醒发送 (采集)
    → 用户响应 (采集反馈)

评估结果 (评估)
    → 阶段进展评估
    → 新 Rx 策略选择 (处方)
    → 不同微行动 (采集修改)
```

### 5.7 V007 策略引擎作为评估驱动门控

**5 步策略流水线**:

```
Step 1: 规则注册 — 从 policy_rules DB 加载 (优先级排序)
Step 2: 候选生成 — Agent 适用性矩阵 (阶段+领域+风险→合格Agent)
Step 3: 冲突解决 — 5 种策略 (primary_first/secondary/average/intersection/union)
Step 4: 成本控制 — 8 模型成本表, 降级路径 (gpt-4o→ollama-local)
Step 5: 决策追踪 — DecisionTrace 审计 (规则ID+AgentID+决策+理由)
```

**4 条种子规则**:
1. `crisis_absolute_priority` (p=100) — 危机绝对优先
2. `medical_boundary_suppress` (p=95) — 医学边界压制
3. `cost_daily_limit_default` (p=70) — 每日成本限制
4. `early_stage_gentle_intensity` (p=60) — 早期阶段温和强度

### 5.8 数据库视图作为聚合融合层

| 视图 | 采集 | 评估 | 处方 |
|------|------|------|------|
| v_user_credit_summary | 学分交易 | 按课程模块聚合 | 资格检查 |
| v_user_total_credits | 用户学分记录 | 汇总必修/选修/M1-M4 | 晋级资格 |
| v_companion_stats | 同道者关系 | 计数毕业/质量均值 | 带教要求 |
| v_promotion_progress | 积分交易 | 汇总成长/贡献/影响力 | 晋级排名 |
| v_user_streak_status | 打卡日期 | 计算当前/最长连续 | 里程碑检查 |
| v_program_enrollment_summary | 方案注册 | 按阶段/状态聚合 | 数据分析 |
| v_program_today_pushes | 计划条目 | 今日推送就绪性 | 实时调度 |

---

## 六、动态Agent协同

### 6.1 16 个 Agent 全景

| 类别 | Agent 名称 | 文件 | 核心职责 |
|------|-----------|------|---------|
| **专业Agent(9)** | metabolic | core/agents/specialist_agents.py | 代谢/血糖 |
| | sleep | 同上 | 睡眠质量 |
| | emotion | 同上 | 情绪管理 |
| | motivation | 同上 | 动机激励 |
| | coaching | 同上 | 教练指导 |
| | nutrition | 同上 | 营养饮食 |
| | exercise | 同上 | 运动健身 |
| | tcm | 同上 | 中医养生 |
| | crisis | 同上 | 危机干预 (始终启用) |
| **整合Agent(3)** | behavior_rx | core/agents/integrative_agents.py | 行为处方 |
| | weight | 同上 | 体重管理 |
| | cardiac_rehab | 同上 | 心脏康复 |
| **专家Agent(4)** | BehaviorCoach | behavior_rx/agents/ | S0-S2 行为教练 |
| | MetabolicExpert | behavior_rx/agents/ | 代谢专家 |
| | CardiacExpert | behavior_rx/agents/ | 心脏康复专家 |
| | AdherenceExpert | behavior_rx/agents/ | 依从性专家 |

### 6.2 Agent 路由机制

```
用户消息
    ↓
AgentRouter (core/agents/router.py)
    ├─ 关键词匹配 → 初始候选集
    ├─ 模板相关性 (V006 tenant_routing_configs)
    ├─ 租户 boost/correlation/conflict 覆盖
    └─ 输出: primary_agent + correlated_agents
    ↓
PolicyEngine (V007, 可选)
    ├─ 规则过滤
    ├─ 适用性矩阵
    ├─ 成本控制
    └─ 输出: approved_agents + trace_id
    ↓
ExpertAgentRouter (behavior_rx, Step 3.5)
    ├─ 关键词 + 领域数据 + TTM 阶段
    └─ 输出: CollaborationOrchestrator 调度
    ↓
MultiAgentCoordinator (core/agents/coordinator.py)
    ├─ 并行执行所有选中Agent
    ├─ 冲突检测 + 解决
    └─ 输出: 合并响应
```

### 6.3 租户级Agent定制

```
resolve_tenant_ctx(user):
    1. 查 ExpertTenant.expert_user_id == user.id  → 专家自己
    2. 查 TenantClient.user_id == user.id          → 专家的客户
    3. None → 平台默认

tenant_ctx →
    ├─ enabled_agents 过滤 (crisis 始终保留)
    ├─ brand_colors / brand_name 品牌化
    ├─ routing_config 路由覆盖
    └─ knowledge_scope 知识范围限制
```

---

## 七、数据流转全景图

### 7.1 端到端流转

```
┌──────────────────────────────────────────────────────────────────┐
│                     设备数据采集层                                │
│  (CGM, HRV, 睡眠, 活动, 生命体征, 食物照片)                       │
└────────────────────────┬─────────────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│               MasterAgent 9步编排器                               │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ Step 1-2:   输入采集 (设备 + 消息)                         │  │
│  │ Step 2.5:   安全 L1 (输入验证)                            │  │
│  │ Step 3:     触发分析 (风险评估)                            │  │
│  │ Step 3.5:   专家路由 (BehaviorRx ExpertAgentRouter)       │  │
│  │ Step 4:     Agent路由 (评估驱动 + PolicyEngine门控)       │  │
│  │ Step 5:     12+4 Agent执行 (专业评估 + Rx计算)            │  │
│  │ Step 6:     多Agent协调 (融合 + 冲突解决)                 │  │
│  │ Step 7:     策略门控 (V007 PolicyEngine)                  │  │
│  │ Step 7.5:   安全 L3 (生成护栏)                            │  │
│  │ Step 8:     响应合成 (LLM 或模板)                         │  │
│  │ Step 8.5:   安全 L4 (输出过滤)                            │  │
│  │ Step 9:     回写 + 任务生成                               │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────┬─────────────────────────────────────────┘
                         │
        ┌────────────────┼─────────────────┐
        ▼                ▼                 ▼
   评估引擎         RAG 知识系统      BehaviorRx
   (12 Agent)       (3层检索)         (4 专家Agent)
        │                │                 │
        └────────────────┼─────────────────┘
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                     处方生成与交付                                │
│  ├─ 微行动 (今日/明日/本周)                                      │
│  ├─ 推荐建议 (按置信度排序)                                      │
│  ├─ 风险评估 (低/中/高/危机)                                     │
│  ├─ 任务清单 (即时/后续/升级)                                    │
│  └─ 洞察 + 引文                                                 │
└────────────────────────┬─────────────────────────────────────────┘
                         │
        ┌────────────────┼─────────────────┐
        ▼                ▼                 ▼
   定时任务          教练工作流         激励系统
   (13 Job)         (看板+分析)        (V003)
        │                │                 │
        ├─ 任务推送      ├─ 学员追踪       ├─ 徽章奖励
        ├─ 方案推进      ├─ 风险趋势       ├─ 积分累积
        ├─ 安全日报      ├─ 分析报表       ├─ 连续奖励
        └─ 指标聚合      └─ 教练建议       └─ 激励推送
                         │
                         ▼
┌──────────────────────────────────────────────────────────────────┐
│                   数据库视图 (聚合层)                              │
│  ├─ v_promotion_progress (积分+学分聚合)                         │
│  ├─ v_user_streak_status (里程碑检查)                            │
│  ├─ v_program_enrollment_summary (V004)                          │
│  ├─ v_program_today_pushes (实时调度)                            │
│  └─ v_companion_stats (带教资格)                                 │
└──────────────────────────────────────────────────────────────────┘
```

### 7.2 时延特征

| 融合类型 | 时延 | 场景 |
|---------|------|------|
| **实时融合** | <500ms | MasterAgent 编排(Steps 1-9), Agent路由(~50ms), 安全L1-L3(~30ms), RAG检索(100-200ms) |
| **准实时融合** | 5-60秒 | 审批推送处理(每5分钟), 提醒检查(每60秒), LLM合成回退(45秒超时) |
| **批量融合** | 定时调度 | 每日任务生成(06:00), 方案推进(00:05), 批量分析(23:00), 安全日报(02:00), Agent指标(01:30) |

### 7.3 降级与回退模式

```
LLM 不可用
    ↓ (5秒超时)
回退到模板合成
    ↓
基于阶段的通用响应

PolicyEngine 不可用
    ↓ (非阻塞 try-except)
回退到 AgentRouter
    ↓
标准 12-Agent 路由

RAG 检索失败
    ↓
继续无知识注入
    ↓
LLM 使用纯 Agent 推荐

安全模块禁用 (配置)
    ↓
所有 4 层优雅禁用
    ↓
原始 Agent 输出直通
```

---

## 八、技术规格汇总

### 8.1 关键文件索引

| 组件 | 文件路径 | 行数 | 层级 |
|------|---------|------|------|
| 9步编排器 | core/master_agent_v0.py | 6,874 | 融合枢纽 |
| v6 模板感知 | core/agents/master_agent.py | ~500 | 融合枢纽 |
| Agent路由 | core/agents/router.py | ~150 | 评估→路由 |
| 多Agent协调 | core/agents/coordinator.py | ~150 | 融合 |
| 安全管道 | core/safety/pipeline.py | 121 | 跨层评估 |
| RAG中间件 | core/knowledge/rag_middleware.py | 179 | 知识融合 |
| 3层检索 | core/knowledge/retriever.py | ~200 | 知识采集 |
| 定时调度 | core/scheduler.py | 439 | 批量融合 |
| **BAPS评分引擎** | core/baps/scoring_engine.py | 831 | 评估核心 |
| 渐进式评估 | baps/progressive_assessment.py | 448 | 评估 |
| SPI计算器 | baps/spi_calculator.py | 162 | 评估 |
| 健康能力评估 | baps/health_competency_assessment.py | 114 | 评估 |
| 障碍评估 | baps/obstacle_assessment.py | 109 | 评估 |
| 动因评分 | baps/cause_scoring.py | 57 | 评估 |
| 行为画像服务 | core/behavioral_profile_service.py | ~150 | 评估SSoT |
| 学习服务 | core/learning_service.py | ~200 | 评估+积分 |
| **行为Rx引擎** | behavior_rx/behavior_rx_engine.py | 916 | 处方核心 |
| 专家Agent基类 | behavior_rx/agents/base_expert_agent.py | 475 | 处方模板 |
| 行为教练Agent | behavior_rx/agents/behavior_coach_agent.py | 427 | 处方S0-S2 |
| 代谢专家Agent | behavior_rx/agents/metabolic_expert_agent.py | 393 | 处方代谢 |
| 心脏专家Agent | behavior_rx/agents/cardiac_expert_agent.py | 768 | 处方心脏 |
| 依从性专家Agent | behavior_rx/agents/adherence_expert_agent.py | 834 | 处方横切 |
| 移交服务 | behavior_rx/core/agent_handoff_service.py | 200 | 处方协议 |
| 协作编排器 | behavior_rx/core/agent_collaboration_orchestrator.py | ~250 | 处方协作 |
| 冲突解决器 | behavior_rx/core/rx_conflict_resolver.py | 437 | 处方仲裁 |
| Rx REST API | behavior_rx/api/rx_routes.py | 589 | 处方API |
| 策略配置 | behavior_rx/configs/rx_strategies.json | ~2000 | 12策略模板 |
| 教练API | api/coach_api.py | 44,888B | 监督融合 |
| 教练分析 | api/analytics_api.py | 8,374B | 评估可视化 |
| 里程碑服务 | core/milestone_service.py | 23,179B | 激励融合 |
| 方案服务 | core/program_service.py | ~2000 | 方案融合 |
| 数据模型 | core/models.py | 4,238 | 119 ORM |

### 8.2 API 端点统计

| 模块 | 端点数 | 层级 |
|------|--------|------|
| 设备数据 | ~20 | 采集 |
| 评估管道 | ~8 | 评估 |
| 问卷调查 | 16 | 采集+评估 |
| 考试认证 | ~13 | 评估 |
| 微行动 | 6 | 采集+处方 |
| 对话 | ~8 | 采集 |
| 内容 | 28 | 采集 |
| 学习 | 15 | 评估 |
| 晋级 | 6 | 评估 |
| 挑战 | ~30 | 采集+处方 |
| 方案 (V004) | 13 | 采集+处方 |
| Agent | ~10 | 融合 |
| 行为Rx | 8 | 处方 |
| 安全 | 8 | 评估 |
| 策略引擎 | 12 | 评估 |
| 教练 | ~20 | 融合 |
| 分析 | 13 | 评估 |
| 激励 | 11 | 处方 |
| **总计** | **511+** | |

### 8.3 设计原则

1. **纯函数计算** — BehaviorRxEngine.compute_rx() 无副作用, 可测试可重现
2. **冰山模型** — 处方隐藏, 领域内容可见, 用户体验自然
3. **模板方法模式** — BaseExpertAgent 定义流程, 子类实现领域逻辑
4. **策略模式** — 12 种策略按阶段可插拔
5. **三维正交** — Stage × Personality × Capacity 三轴独立
6. **证据分层** — 所有策略基于 T1-T2 证据 (TTM/ACT/CBT)
7. **障碍驱动** — 活跃障碍可覆盖阶段默认策略
8. **优雅降级** — 无 DB 可运行, 有 DB 则增强持久化
9. **审计轨迹** — 每张处方记录完整推理链
10. **Agent 即服务** — Agent 非单例, 每请求创建, 无状态

---

> **文档结束**
>
> 本文档基于 `D:\behavioral-health-project` 全部源码分析生成,
> 覆盖 119 个 ORM 模型、57 个 API 路由器、511+ 个端点、
> 16 个 Agent、12 种行为策略、5 套标准化量表。
>
> 版本: v1.0 | 日期: 2026-02-14 | 编制: Claude Code (Opus 4.6)

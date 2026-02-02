# Trigger Tag 字典说明

> 版本: v1.0
> 更新日期: 2026-01-28
> 用途: L2评估层 - Trigger识别引擎

---

## 概述

Trigger Tag 是行为健康平台 L2 评估层的核心数据结构，用于标准化识别用户的生理、心理、行为和环境触发信号，从而实现精准的风险评估和智能路由。

---

## 目录结构

```
knowledge/triggers/
├── README.md                   # 本文档
├── trigger-tags-v1.json        # Trigger字典主文件
└── examples/                   # 使用示例
    └── detection_examples.json # 检测示例
```

---

## Trigger 分类体系

### 四大类别

| 类别 | 英文 | 数量 | 说明 |
|------|------|------|------|
| **生理类** | physiological | 8 | 来自设备数据或生理症状 |
| **心理类** | psychological | 7 | 来自文本情感或量表评估 |
| **行为类** | behavioral | 9 | 来自任务追踪或行为日志 |
| **环境类** | environmental | 4 | 来自环境压力或资源状况 |

### 严重程度分级

| 级别 | 优先级 | 响应时间 | 示例 |
|------|--------|----------|------|
| **CRITICAL** | P0 | 立即 | 低血糖、危机关键词 |
| **HIGH** | P1 | 1小时内 | 高血糖、高焦虑、低依从性 |
| **MODERATE** | P2 | 24小时内 | 血糖波动、负面情绪、久坐 |
| **LOW** | P3 | 48小时内 | 漏打卡 |

---

## 主要 Trigger 标签

### 生理类 (8个)

| Tag ID | 名称 | 严重程度 | 数据源 | 路由Agent |
|--------|------|----------|--------|-----------|
| `high_glucose` | 高血糖 | HIGH | CGM/手动记录 | GlucoseAgent |
| `low_glucose` | 低血糖 | **CRITICAL** | CGM/症状 | CrisisAgent |
| `glucose_spike` | 血糖波动 | MODERATE | CGM | GlucoseAgent |
| `low_hrv` | 低心率变异性 | MODERATE | PPG/ECG | StressAgent |
| `high_stress_hrv` | 压力指标异常 | HIGH | PPG | StressAgent |
| `high_heartrate` | 心率过高 | MODERATE | PPG | StressAgent |
| `low_heartrate` | 心率过低 | MODERATE | PPG | CrisisAgent |
| `poor_sleep` | 睡眠质量差 | MODERATE | 睡眠监测 | SleepAgent |

### 心理类 (7个)

| Tag ID | 名称 | 严重程度 | 数据源 | 路由Agent |
|--------|------|----------|--------|-----------|
| `high_anxiety` | 高焦虑 | HIGH | 文本/量表 | MentalHealthAgent |
| `depression_sign` | 抑郁倾向 | HIGH | 文本/量表 | MentalHealthAgent |
| `stress_overload` | 压力过载 | HIGH | 文本/HRV | StressAgent |
| `negative_sentiment` | 负面情绪 | MODERATE | 文本分析 | MentalHealthAgent |
| `low_motivation` | 动机低下 | MODERATE | 量表/行为 | MotivationAgent |
| `crisis_keyword` | 危机关键词 | **CRITICAL** | 文本分析 | CrisisAgent |

### 行为类 (9个)

| Tag ID | 名称 | 严重程度 | 数据源 | 路由Agent |
|--------|------|----------|--------|-----------|
| `task_failure` | 任务失败 | MODERATE | 任务追踪 | CoachingAgent |
| `missing_checkin` | 漏打卡 | LOW | 系统日志 | CoachingAgent |
| `low_adherence` | 依从性低 | HIGH | 任务追踪 | CoachingAgent |
| `high_gi_meal` | 高GI饮食 | MODERATE | 饮食日志 | NutritionAgent |
| `irregular_meal` | 饮食不规律 | MODERATE | 饮食日志 | NutritionAgent |
| `sedentary` | 久坐 | MODERATE | 活动追踪 | ExerciseAgent |

### 环境类 (4个)

| Tag ID | 名称 | 严重程度 | 数据源 | 路由Agent |
|--------|------|----------|--------|-----------|
| `support_lack` | 缺乏支持 | MODERATE | 量表/文本 | CoachingAgent |
| `resource_barrier` | 资源障碍 | MODERATE | 量表/文本 | CoachingAgent |
| `work_stress` | 工作压力 | MODERATE | 文本/量表 | StressAgent |
| `family_conflict` | 家庭冲突 | MODERATE | 文本/量表 | MentalHealthAgent |

---

## Trigger 聚类

### 代谢综合征聚类
- **Triggers**: `high_glucose` + `glucose_spike` + `sedentary` + `high_gi_meal`
- **严重程度**: HIGH
- **路由**: MetabolicAgent + NutritionAgent + ExerciseAgent

### 职业倦怠聚类
- **Triggers**: `stress_overload` + `poor_sleep` + `low_motivation` + `work_stress`
- **严重程度**: HIGH
- **路由**: MentalHealthAgent + StressAgent + CoachingAgent

### 抑郁风险聚类
- **Triggers**: `depression_sign` + `negative_sentiment` + `low_motivation` + `sedentary`
- **严重程度**: HIGH
- **路由**: MentalHealthAgent + CrisisAgent

---

## 使用方式

### 1. 在代码中加载字典

```python
import json
from pathlib import Path

# 加载字典
trigger_dict_path = Path("knowledge/triggers/trigger-tags-v1.json")
with open(trigger_dict_path) as f:
    trigger_dict = json.load(f)

# 获取单个Trigger定义
high_glucose = trigger_dict["triggers"]["high_glucose"]
print(high_glucose["name"])  # 输出: 高血糖
print(high_glucose["severity"])  # 输出: high
```

### 2. 检测流程

```python
from core.trigger_engine import get_trigger_engine

# 初始化引擎
engine = get_trigger_engine()

# 识别Triggers
triggers = await engine.recognize_triggers(
    user_id=1,
    text_content="今天血糖有点高，感觉很焦虑",
    glucose_values=[6.5, 11.2, 13.5],
    hrv_values=[65, 68, 62]
)

# 输出结果
for trigger in triggers:
    print(f"{trigger.name} - {trigger.severity.value}")
```

### 3. 路由决策

```python
# 按严重程度分组
critical = [t for t in triggers if t.severity.value == "critical"]
high = [t for t in triggers if t.severity.value == "high"]

# 确定路由
if critical:
    agents = ["CrisisAgent"]
elif high:
    agents = ["GlucoseAgent", "MentalHealthAgent"]
else:
    agents = ["CoachingAgent"]
```

---

## 检测源映射

| 检测源 | 说明 | 支持的Triggers |
|--------|------|----------------|
| `text_emotion` | 文本情感分析 | high_anxiety, depression_sign, negative_sentiment |
| `text_symptom` | 文本症状描述 | low_glucose, poor_sleep |
| `cgm_signal` | 连续血糖监测 | high_glucose, low_glucose, glucose_spike |
| `ppg_signal` | 光电容积脉搏波 | low_hrv, high_stress_hrv, high_heartrate |
| `task_tracking` | 任务追踪系统 | task_failure, low_adherence |
| `food_log` | 饮食日志 | high_gi_meal, irregular_meal |
| `questionnaire` | 量表评估 | high_anxiety, depression_sign, low_motivation |

---

## 阈值说明

### 血糖相关
- **高血糖**: >10.0 mmol/L (空腹或餐后2小时)
- **低血糖**: <3.9 mmol/L
- **血糖波动**: 2小时内变化 >3.0 mmol/L

### HRV相关
- **低HRV**: SDNN <30 ms
- **压力指标**: Stress Index >80

### 心率相关
- **心率过高**: >100 bpm (静息)
- **心率过低**: <60 bpm (非运动员)

### 行为相关
- **任务失败**: 连续 ≥3 次
- **低依从性**: <50% (过去7天)
- **久坐**: <3000 步/天

---

## 关键词映射

### 情绪关键词

| Trigger | 关键词 |
|---------|--------|
| `high_anxiety` | 焦虑、担心、紧张、不安、恐慌 |
| `depression_sign` | 抑郁、没意思、不想动、没劲、想哭 |
| `stress_overload` | 压力大、受不了、崩溃、撑不住 |
| `crisis_keyword` | 不想活、自杀、自残、结束生命 |

### 症状关键词

| Trigger | 关键词 |
|---------|--------|
| `low_glucose` | 头晕、出冷汗、心慌、手抖、饿得慌 |
| `poor_sleep` | 没睡好、失眠、睡不着、半夜醒 |

### 环境关键词

| Trigger | 关键词 |
|---------|--------|
| `work_stress` | 加班、工作压力、职场、领导 |
| `family_conflict` | 家里、老公、老婆、孩子、父母、吵架 |

---

## 最佳实践

### ✅ DO (推荐做法)

1. **优先处理高级别**: 先处理 CRITICAL 和 HIGH，再处理 MODERATE
2. **关注聚类**: 多个相关 Trigger 同时出现时，提升严重程度
3. **上下文结合**: 结合用户画像和历史数据判断
4. **设置冷却期**: 同一 Trigger 24小时内不重复触发（除 CRITICAL）

### ❌ DON'T (避免做法)

1. **避免过度警报**: 不要对正常波动过度敏感
2. **避免单点决策**: 不要仅凭单个数据点触发
3. **避免忽略轻度**: MODERATE 和 LOW 也需要记录和追踪

---

## 扩展指南

### 添加新 Trigger

1. 在 `trigger-tags-v1.json` 中添加定义
2. 更新 `core/trigger_engine.py` 中的识别逻辑
3. 更新本 README 文档
4. 添加测试用例

### 修改阈值

1. 基于数据反馈调整阈值
2. 保留旧版本进行A/B测试
3. 记录调整原因和效果

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2026-01-28 | 初始版本，28个Trigger标签 |

---

## 相关文档

- [L2 评估分流架构设计](../docs/L2_ASSESSMENT_ENGINE.md)
- [Trigger 引擎实现](../../core/trigger_engine.py)
- [多模态系统集成](../../core/multimodal_client.py)

---

**维护者**: 行为健康平台技术团队
**反馈**: 如发现阈值不合理或需要新增 Trigger，请提交 Issue

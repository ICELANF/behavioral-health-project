# Dify HTTP 工具配置

## 主动健康 · 吃动守恒

在 Dify 中导入应用后，需要手动添加以下 HTTP 工具来对接后端 API。

## 添加步骤

1. 进入应用 → **编排** → **工具**
2. 点击 **添加工具** → **自定义**
3. 按照下面的配置添加每个工具

---

## 工具 0: 能量平衡计算 (energy_balance) ⭐ 核心

**基础配置:**
- 名称: `energy_balance`
- 描述: `计算用户的能量收支平衡（吃动守恒核心工具），分析摄入热量与消耗热量的差值`

**API 配置:**
- 方法: `POST`
- URL: `http://host.docker.internal:8001/energy/calculate`
- Headers:
  ```
  Content-Type: application/json
  ```

**参数配置:**
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| user_id | string | 是 | 用户ID |
| date | string | 否 | 日期(YYYY-MM-DD) |
| intake_calories | number | 是 | 摄入热量(kcal) |
| exercise_calories | number | 是 | 运动消耗热量(kcal) |
| bmr | number | 否 | 基础代谢率(kcal)，可自动计算 |

**请求体模板:**
```json
{
  "user_id": "{{user_id}}",
  "date": "{{date}}",
  "intake_calories": {{intake_calories}},
  "exercise_calories": {{exercise_calories}},
  "bmr": {{bmr}}
}
```

**返回示例:**
```json
{
  "user_id": "patient-001",
  "date": "2026-01-25",
  "intake_calories": 1800,
  "total_expenditure": 2100,
  "balance": -300,
  "status": "deficit",
  "recommendation": "今日热量缺口300kcal，保持当前节奏有助于减重"
}
```

---

## 工具 1: 用户信息采集 (intake)

**基础配置:**
- 名称: `intake`
- 描述: `采集用户健康基础信息，包括年龄、糖尿病类型、病程、用药情况等`

**API 配置:**
- 方法: `POST`
- URL: `http://host.docker.internal:8001/intake`
- Headers:
  ```
  Content-Type: application/json
  ```

**参数配置:**
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| user_id | string | 是 | 用户ID |
| age | number | 否 | 年龄 |
| gender | string | 否 | 性别(male/female) |
| diabetes_type | string | 否 | 糖尿病类型(type1/type2/gestational/prediabetes) |
| duration_years | number | 否 | 病程年数 |
| fasting_glucose | number | 否 | 空腹血糖(mmol/L) |
| hba1c | number | 否 | 糖化血红蛋白(%) |
| weight | number | 否 | 体重(kg) |
| height | number | 否 | 身高(cm) |

**请求体模板:**
```json
{
  "user_id": "{{user_id}}",
  "age": {{age}},
  "gender": "{{gender}}",
  "diabetes_type": "{{diabetes_type}}",
  "duration_years": {{duration_years}},
  "fasting_glucose": {{fasting_glucose}},
  "hba1c": {{hba1c}},
  "weight": {{weight}},
  "height": {{height}}
}
```

---

## 工具 2: TTM 阶段评估 (stage_evaluate)

**基础配置:**
- 名称: `stage_evaluate`
- 描述: `评估用户在特定健康行为领域的TTM阶段(前意向期/意向期/准备期/行动期/维持期)`

**API 配置:**
- 方法: `POST`
- URL: `http://host.docker.internal:8001/stage/evaluate`
- Headers:
  ```
  Content-Type: application/json
  ```

**参数配置:**
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| user_id | string | 是 | 用户ID |
| trigger_domain | string | 是 | 触发领域(glucose/diet/exercise/medication/sleep/stress/weight) |
| response_text | string | 是 | 用户的回答文本，用于判断行为阶段 |

**请求体模板:**
```json
{
  "user_id": "{{user_id}}",
  "trigger_domain": "{{trigger_domain}}",
  "response_text": "{{response_text}}"
}
```

---

## 工具 3: 风险评估 (risk_evaluate)

**基础配置:**
- 名称: `risk_evaluate`
- 描述: `评估用户的健康风险等级(低/中/高)，用于判断是否需要转人工或就医`

**API 配置:**
- 方法: `POST`
- URL: `http://host.docker.internal:8001/risk/evaluate`
- Headers:
  ```
  Content-Type: application/json
  ```

**参数配置:**
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| user_id | string | 是 | 用户ID |
| fasting_glucose | number | 否 | 空腹血糖(mmol/L) |
| postprandial_glucose | number | 否 | 餐后血糖(mmol/L) |
| hypoglycemia_history | boolean | 否 | 是否有低血糖史 |
| current_insulin | boolean | 否 | 是否正在使用胰岛素 |
| comorbidities | array | 否 | 并发症列表 |

**请求体模板:**
```json
{
  "user_id": "{{user_id}}",
  "fasting_glucose": {{fasting_glucose}},
  "postprandial_glucose": {{postprandial_glucose}},
  "hypoglycemia_history": {{hypoglycemia_history}},
  "current_insulin": {{current_insulin}},
  "comorbidities": {{comorbidities}}
}
```

---

## 工具 4: 随访注册 (followup_register)

**基础配置:**
- 名称: `followup_register`
- 描述: `注册用户的随访计划，设置定期提醒`

**API 配置:**
- 方法: `POST`
- URL: `http://host.docker.internal:8001/followup/register`
- Headers:
  ```
  Content-Type: application/json
  ```

**参数配置:**
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| user_id | string | 是 | 用户ID |
| followup_type | string | 是 | 随访类型(daily/weekly/monthly) |
| focus_areas | array | 是 | 关注领域列表 |
| preferred_time | string | 否 | 偏好提醒时间(HH:MM格式) |

**请求体模板:**
```json
{
  "user_id": "{{user_id}}",
  "followup_type": "{{followup_type}}",
  "focus_areas": {{focus_areas}},
  "preferred_time": "{{preferred_time}}"
}
```

---

## 工具 5: Agent 移交 (agent_handover)

**基础配置:**
- 名称: `agent_handover`
- 描述: `将用户移交给不同类型的Agent(教练/督导/客服)，用于复杂场景处理`

**API 配置:**
- 方法: `POST`
- URL: `http://host.docker.internal:8001/agent/handover`
- Headers:
  ```
  Content-Type: application/json
  ```

**参数配置:**
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| user_id | string | 是 | 用户ID |
| from_agent | string | 是 | 来源Agent类型 |
| to_agent | string | 是 | 目标Agent类型(coach/supervisor/support) |
| reason | string | 是 | 移交原因 |
| context | object | 否 | 上下文信息 |

**请求体模板:**
```json
{
  "user_id": "{{user_id}}",
  "from_agent": "{{from_agent}}",
  "to_agent": "{{to_agent}}",
  "reason": "{{reason}}",
  "context": {{context}}
}
```

---

## 测试验证

添加工具后，在对话中测试:

```
用户: 我的空腹血糖是7.5，餐后是10.2
预期: Agent 调用 risk_evaluate 评估风险，然后给出建议
```

```
用户: 我想开始运动但不知道从哪开始
预期: Agent 调用 stage_evaluate 评估阶段，然后提供针对性建议
```

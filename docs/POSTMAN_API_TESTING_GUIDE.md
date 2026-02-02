# 行为健康平台 API 接口调试指南

> 适用于 Postman 测试，覆盖全部可用接口
> 最后更新: 2026-01-31

---

## 环境配置

### Postman 变量设置

在 Postman 中创建 Environment（如 `本地开发`），设置以下变量：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `base_url` | `http://localhost:8000` | 主服务地址 |
| `baps_url` | `http://localhost:8001` | BAPS 评估服务地址 |
| `token` | （登录后填入） | Bearer Token |
| `user_id` | `2` | patient_alice 的用户 ID |

### 服务启动命令

```bash
# 主服务（端口 8000）
cd D:\behavioral-health-project
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# BAPS 评估服务（端口 8001）
python -m uvicorn api.baps_api:app --host 0.0.0.0 --port 8001
```

### 测试账号

| 用户名 | 密码 | 角色 | user_id |
|--------|------|------|---------|
| `admin` | `admin123456` | ADMIN | 1 |
| `patient_alice` | `password123` | PATIENT | 2 |
| `patient_bob` | `password123` | PATIENT | 3 |
| `coach_carol` | `coach123` | COACH | 4 |

---

## 一、认证接口 `/api/v1/auth`

### 1.1 登录（获取 Token）

```
POST {{base_url}}/api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=patient_alice
password=password123
```

**响应示例：**
```json
{
    "access_token": "eyJhbGciOiJIUzI1NiI...",
    "refresh_token": "eyJhbGciOiJIUzI1NiI...",
    "token_type": "bearer",
    "user": {
        "id": 2,
        "username": "patient_alice",
        "role": "patient"
    }
}
```

> 拿到 `access_token` 后，设置到 Postman 变量 `{{token}}` 中。
> 后续所有需要鉴权的接口，在 Authorization 选 Bearer Token，填 `{{token}}`。

---

### 1.2 注册

```
POST {{base_url}}/api/v1/auth/register
Content-Type: application/json

{
    "username": "test_user",
    "email": "test@example.com",
    "password": "test123456",
    "full_name": "测试用户",
    "phone": "13800138000"
}
```

---

### 1.3 获取当前用户信息

```
GET {{base_url}}/api/v1/auth/me
Authorization: Bearer {{token}}
```

---

### 1.4 退出登录

```
POST {{base_url}}/api/v1/auth/logout
Authorization: Bearer {{token}}
```

---

## 二、AI 对话接口 `/api/v1/mp`

> 注意：这组接口使用 `X-User-ID` 请求头标识用户。

### 2.1 LLM 服务健康检查

```
GET {{base_url}}/api/v1/mp/llm/health
```

**响应示例：**
```json
{
    "status": "healthy",
    "models": ["qwen2.5:14b"],
    "model_available": true,
    "current_model": "qwen2.5:14b"
}
```

---

### 2.2 AI 对话（非流式）

```
POST {{base_url}}/api/v1/mp/chat
Content-Type: application/json
X-User-ID: 2

{
    "message": "我最近血糖有点高，该怎么办？",
    "session_id": "test-session-001"
}
```

---

### 2.3 AI 对话（SSE 流式）

```
POST {{base_url}}/api/v1/mp/chat/stream
Content-Type: application/json
X-User-ID: 2

{
    "message": "运动对血糖有什么影响？",
    "session_id": "test-session-001"
}
```

> Postman 中会看到 SSE 格式的流式输出。

---

### 2.4 获取会话列表

```
GET {{base_url}}/api/v1/mp/chat/sessions?limit=20
X-User-ID: 2
```

---

### 2.5 获取对话历史

```
GET {{base_url}}/api/v1/mp/chat/history/test-session-001?limit=50
X-User-ID: 2
```

---

### 2.6 删除会话

```
DELETE {{base_url}}/api/v1/mp/chat/session/test-session-001
X-User-ID: 2
```

---

### 2.7 清空所有聊天历史

```
DELETE {{base_url}}/api/v1/mp/chat/history
X-User-ID: 2
```

---

## 三、任务与状态接口 `/api/v1/mp`

### 3.1 获取今日任务

```
GET {{base_url}}/api/v1/mp/task/today
X-User-ID: 2
```

---

### 3.2 提交任务反馈

```
POST {{base_url}}/api/v1/mp/task/feedback
Content-Type: application/json
X-User-ID: 2

{
    "stage": "ONBOARDING",
    "result": "done",
    "task_code": "blood_glucose_check",
    "data": {
        "value": 6.5,
        "unit": "mmol/L"
    },
    "notes": "早餐前测量，感觉状态不错"
}
```

> **stage 可选值：** `INIT` | `ONBOARDING` | `FOUNDATION` | `DEEPENING` | `CONSOLIDATION` | `MAINTENANCE`
> **result 可选值：** `done` | `skip` | `partial`

---

### 3.3 获取 AI Agent 回复

```
POST {{base_url}}/api/v1/mp/agent/respond
Content-Type: application/json
X-User-ID: 2

{
    "stage": "startup",
    "event": "task_completed",
    "context": {
        "task_code": "blood_glucose_check"
    },
    "user_input": "今天血糖控制得怎么样？"
}
```

---

### 3.4 获取用户状态

```
GET {{base_url}}/api/v1/mp/user/state
X-User-ID: 2
```

---

### 3.5 设置用户模式

```
POST {{base_url}}/api/v1/mp/user/mode
Content-Type: application/json
X-User-ID: 2

{
    "mode": "pilot"
}
```

---

### 3.6 获取进度摘要

```
GET {{base_url}}/api/v1/mp/progress/summary
X-User-ID: 2
```

---

### 3.7 获取风险状态

```
GET {{base_url}}/api/v1/mp/risk/status
X-User-ID: 2
```

---

## 四、设备数据接口 `/api/v1/mp/device`

### 4.1 设备管理

#### 获取设备列表

```
GET {{base_url}}/api/v1/mp/device/devices
X-User-ID: 2
```

#### 绑定设备

```
POST {{base_url}}/api/v1/mp/device/devices/bind
Content-Type: application/json
X-User-ID: 2

{
    "device_type": "glucometer",
    "manufacturer": "三诺",
    "model": "GA-3",
    "serial_number": "SN20260131001"
}
```

#### 解绑设备

```
DELETE {{base_url}}/api/v1/mp/device/devices/{device_id}
X-User-ID: 2
```

---

### 4.2 血糖数据

#### 手动记录血糖

```
POST {{base_url}}/api/v1/mp/device/glucose/manual
Content-Type: application/json
X-User-ID: 2

{
    "value": 6.5,
    "unit": "mmol/L",
    "meal_tag": "before_meal",
    "notes": "早餐前测量"
}
```

#### 查询血糖数据

```
GET {{base_url}}/api/v1/mp/device/glucose?limit=100
X-User-ID: 2
```

#### 获取当前血糖

```
GET {{base_url}}/api/v1/mp/device/glucose/current
X-User-ID: 2
```

#### 获取日血糖图表数据

```
GET {{base_url}}/api/v1/mp/device/glucose/chart/daily?date=2026-01-31
X-User-ID: 2
```

---

### 4.3 体重数据

#### 记录体重

```
POST {{base_url}}/api/v1/mp/device/weight
Content-Type: application/json
X-User-ID: 2

{
    "weight_kg": 72.5,
    "body_fat_percent": 22.3,
    "muscle_mass_kg": 30.1
}
```

#### 查询体重记录

```
GET {{base_url}}/api/v1/mp/device/weight?limit=30
X-User-ID: 2
```

---

### 4.4 血压数据

#### 记录血压

```
POST {{base_url}}/api/v1/mp/device/blood-pressure
Content-Type: application/json
X-User-ID: 2

{
    "systolic": 128,
    "diastolic": 82,
    "pulse": 72
}
```

#### 查询血压记录

```
GET {{base_url}}/api/v1/mp/device/blood-pressure?limit=30
X-User-ID: 2
```

---

### 4.5 睡眠数据

#### 获取睡眠记录

```
GET {{base_url}}/api/v1/mp/device/sleep?limit=7
X-User-ID: 2
```

#### 获取昨晚睡眠

```
GET {{base_url}}/api/v1/mp/device/sleep/last-night
X-User-ID: 2
```

---

### 4.6 活动/心率/HRV 数据

#### 获取活动数据

```
GET {{base_url}}/api/v1/mp/device/activity?date=2026-01-31
X-User-ID: 2
```

#### 获取心率数据

```
GET {{base_url}}/api/v1/mp/device/heart-rate?limit=100
X-User-ID: 2
```

#### 获取 HRV 数据

```
GET {{base_url}}/api/v1/mp/device/hrv?limit=30
X-User-ID: 2
```

---

### 4.7 今日健康仪表盘

```
GET {{base_url}}/api/v1/mp/device/dashboard/today
X-User-ID: 2
```

**响应示例：**
```json
{
    "glucose": {
        "current": 6.5,
        "avg": 7.2,
        "tir": 83.3,
        "readings_count": 6
    },
    "activity": {
        "steps": 10250,
        "distance_km": 7.8
    },
    "sleep": {
        "duration_hours": 8,
        "score": 85,
        "deep_percent": 18.8
    },
    "alerts": []
}
```

---

### 4.8 设备数据同步

#### 批量同步

```
POST {{base_url}}/api/v1/mp/device/sync/batch
Content-Type: application/json
X-User-ID: 2

{
    "device_id": "your_device_id",
    "sync_type": "incremental",
    "data_types": ["glucose", "heart_rate"],
    "data": {
        "glucose": [
            {"value": 5.8, "unit": "mmol/L", "timestamp": "2026-01-31T07:00:00"},
            {"value": 7.2, "unit": "mmol/L", "timestamp": "2026-01-31T09:30:00"}
        ],
        "heart_rate": [
            {"bpm": 72, "timestamp": "2026-01-31T07:00:00"},
            {"bpm": 85, "timestamp": "2026-01-31T09:30:00"}
        ]
    }
}
```

#### 查询同步状态

```
GET {{base_url}}/api/v1/mp/device/sync/status/{device_id}
X-User-ID: 2
```

---

## 五、评估数据接口 `/api/assessment`

### 5.1 获取最近评估

```
GET {{base_url}}/api/assessment/recent/{{user_id}}?limit=5
Authorization: Bearer {{token}}
```

---

### 5.2 获取评估历史（分页）

```
GET {{base_url}}/api/assessment/history/{{user_id}}?page=1&page_size=10
Authorization: Bearer {{token}}
```

---

### 5.3 获取单条评估详情

```
GET {{base_url}}/api/assessment/{assessment_id}
Authorization: Bearer {{token}}
```

> `assessment_id` 从历史列表中获取，格式如 `ASS-20260128-xxxxx`。

---

## 六、Orchestrator 编排器接口 `/orchestrator`

### 6.1 核心处理（9步流程）

```
POST {{base_url}}/orchestrator/process
Content-Type: application/json

{
    "user_id": "patient_alice",
    "input_type": "chat",
    "content": "我最近睡眠不好，总是失眠",
    "efficacy_score": 45,
    "session_id": "orch-session-001"
}
```

---

### 6.2 每日简报

```
POST {{base_url}}/orchestrator/briefing
Content-Type: application/json

{
    "user_id": "patient_alice"
}
```

---

### 6.3 获取推送消息文本

```
GET {{base_url}}/orchestrator/briefing/patient_alice/message
```

---

### 6.4 执行 Agent 任务

```
POST {{base_url}}/orchestrator/agent-task
Content-Type: application/json

{
    "agent_type": "sleep",
    "question": "用户最近一周睡眠质量如何？有什么改善建议？",
    "priority": 2,
    "context": {
        "sleep_duration": 5.5,
        "sleep_quality": "poor"
    }
}
```

**可选 agent_type 值：**
`sleep` | `glucose` | `stress` | `nutrition` | `exercise` | `mental_health` | `tcm` | `crisis`

---

### 6.5 创建行动计划

```
POST {{base_url}}/orchestrator/action-plan
Content-Type: application/json

{
    "user_id": "patient_alice",
    "goal": "改善睡眠质量，每晚睡够7小时",
    "phase": "startup",
    "tags": ["sleep", "lifestyle"]
}
```

---

### 6.6 获取多阶段计划

```
GET {{base_url}}/orchestrator/action-plan/patient_alice/phased?goal=改善睡眠&weeks=8
```

---

### 6.7 获取用户画像

```
GET {{base_url}}/orchestrator/profile/patient_alice
```

---

### 6.8 同步设备数据

```
POST {{base_url}}/orchestrator/device-sync
Content-Type: application/json

{
    "user_id": "patient_alice",
    "device_data": {
        "hrv": {"sdnn": 45, "rmssd": 38, "stress_index": 55},
        "sleep": {"duration": 6.5, "deep_sleep_ratio": 0.18, "efficiency": 0.82},
        "glucose": {"current": 7.2, "tir": 75}
    }
}
```

---

### 6.9 Agent 路由（简化版）

```
POST {{base_url}}/orchestrator/route
Content-Type: application/json

{
    "user_id": "patient_alice",
    "intent": "我血糖一直控制不好，压力很大",
    "risk_level": "moderate"
}
```

---

### 6.10 Agent 路由（详细版）

```
POST {{base_url}}/orchestrator/route/detailed
Content-Type: application/json

{
    "user_id": "patient_alice",
    "intent": "我血糖一直控制不好，压力很大",
    "risk_level": "moderate",
    "risk_score": 45.5,
    "risk_factors": ["high_glucose", "stress"],
    "device_data": {
        "glucose": {"current": 9.8},
        "hrv": {"stress_index": 65}
    }
}
```

---

### 6.11 系统状态

```
GET {{base_url}}/orchestrator/status
```

---

## 七、通用接口

### 7.1 健康检查

```
GET {{base_url}}/health
```

---

### 7.2 获取专家列表

```
GET {{base_url}}/api/v1/experts
```

---

### 7.3 消息分发（Dify/Ollama）

```
POST {{base_url}}/api/v1/dispatch
Content-Type: application/json

{
    "user_id": "patient_alice",
    "message": "帮我分析一下最近的健康数据",
    "mode": "ollama"
}
```

> `mode` 可选 `dify` 或 `ollama`。

---

### 7.4 任务分解

```
POST {{base_url}}/api/v1/decompose
Content-Type: application/json

{
    "message": "我想改善睡眠质量，减少熬夜",
    "efficacy_score": 40
}
```

---

## 八、BAPS 行为评估系统（端口 8001）

> 独立服务，需单独启动。

### 8.1 健康检查

```
GET {{baps_url}}/health
```

---

### 8.2 获取问卷列表

```
GET {{baps_url}}/questionnaires
```

---

### 8.3 获取问卷详情与题目

```
GET {{baps_url}}/questionnaires/big_five
GET {{baps_url}}/questionnaires/bpt6
GET {{baps_url}}/questionnaires/capacity
GET {{baps_url}}/questionnaires/spi
```

---

### 8.4 获取测试用示例答案

```
GET {{baps_url}}/test/sample-answers/big_five
GET {{baps_url}}/test/sample-answers/bpt6
GET {{baps_url}}/test/sample-answers/capacity
GET {{baps_url}}/test/sample-answers/spi
```

> 先调用此接口获取示例答案，再用于下面的评估接口。

---

### 8.5 大五人格评估

```
POST {{baps_url}}/assess/big_five
Content-Type: application/json

{
    "user_id": "patient_alice",
    "answers": {
        "BF01": 4, "BF02": -2, "BF03": 3, "BF04": 1, "BF05": -1,
        "BF06": 3, "BF07": -3, "BF08": 2, "BF09": 4, "BF10": -2,
        "BF11": 2, "BF12": -1, "BF13": 3, "BF14": 1, "BF15": -2,
        "BF16": 4, "BF17": -3, "BF18": 2, "BF19": 3, "BF20": -1,
        "BF21": 1, "BF22": -2, "BF23": 4, "BF24": 2, "BF25": -3,
        "BF26": 3, "BF27": -1, "BF28": 2, "BF29": 4, "BF30": -2,
        "BF31": 1, "BF32": -3, "BF33": 3, "BF34": 2, "BF35": -1,
        "BF36": 4, "BF37": -2, "BF38": 3, "BF39": 1, "BF40": -3,
        "BF41": 2, "BF42": -1, "BF43": 4, "BF44": 3, "BF45": -2,
        "BF46": 1, "BF47": -3, "BF48": 2, "BF49": 4, "BF50": -1
    }
}
```

> 答案值范围: -4 到 +4

---

### 8.6 BPT-6 行为模式分型

```
POST {{baps_url}}/assess/bpt6
Content-Type: application/json

{
    "user_id": "patient_alice",
    "answers": {
        "BPT01": 5, "BPT02": 4, "BPT03": 3,
        "BPT04": 4, "BPT05": 5, "BPT06": 3,
        "BPT07": 2, "BPT08": 3, "BPT09": 4,
        "BPT10": 3, "BPT11": 4, "BPT12": 2,
        "BPT13": 3, "BPT14": 2, "BPT15": 4,
        "BPT16": 5, "BPT17": 3, "BPT18": 4
    }
}
```

> 答案值范围: 1-5

---

### 8.7 CAPACITY 改变潜力诊断

```
POST {{baps_url}}/assess/capacity
Content-Type: application/json

{
    "user_id": "patient_alice",
    "answers": {
        "CAP01": 4, "CAP02": 3, "CAP03": 5, "CAP04": 4,
        "CAP05": 3, "CAP06": 4, "CAP07": 5, "CAP08": 3,
        "CAP09": 4, "CAP10": 3, "CAP11": 4, "CAP12": 5,
        "CAP13": 3, "CAP14": 4, "CAP15": 3, "CAP16": 4,
        "CAP17": 5, "CAP18": 3, "CAP19": 4, "CAP20": 3,
        "CAP21": 4, "CAP22": 5, "CAP23": 3, "CAP24": 4,
        "CAP25": 3, "CAP26": 4, "CAP27": 5, "CAP28": 3,
        "CAP29": 4, "CAP30": 3, "CAP31": 4, "CAP32": 5
    }
}
```

> 答案值范围: 1-5，满分 160

---

### 8.8 SPI 成功可能性评估

```
POST {{baps_url}}/assess/spi
Content-Type: application/json

{
    "user_id": "patient_alice",
    "answers": {
        "SPI01": 4, "SPI02": 3, "SPI03": 5, "SPI04": 4, "SPI05": 3,
        "SPI06": 4, "SPI07": 5, "SPI08": 3, "SPI09": 4, "SPI10": 3,
        "SPI11": 4, "SPI12": 5, "SPI13": 3, "SPI14": 4, "SPI15": 3,
        "SPI16": 4, "SPI17": 5, "SPI18": 3, "SPI19": 4, "SPI20": 3,
        "SPI21": 4, "SPI22": 5, "SPI23": 3, "SPI24": 4, "SPI25": 3,
        "SPI26": 4, "SPI27": 5, "SPI28": 3, "SPI29": 4, "SPI30": 3,
        "SPI31": 4, "SPI32": 5, "SPI33": 3, "SPI34": 4, "SPI35": 3,
        "SPI36": 4, "SPI37": 5, "SPI38": 3, "SPI39": 4, "SPI40": 3,
        "SPI41": 4, "SPI42": 5, "SPI43": 3, "SPI44": 4, "SPI45": 3,
        "SPI46": 4, "SPI47": 5, "SPI48": 3, "SPI49": 4, "SPI50": 3
    }
}
```

> 五维度加权: 动机×0.30 + 能力×0.25 + 支持×0.20 + 环境×0.15 + 历史×0.10

---

### 8.9 综合评估（四合一）

```
POST {{baps_url}}/assess/comprehensive
Content-Type: application/json

{
    "user_id": "patient_alice",
    "big_five": { "BF01": 4, "BF02": -2, ... },
    "bpt6": { "BPT01": 5, "BPT02": 4, ... },
    "capacity": { "CAP01": 4, "CAP02": 3, ... },
    "spi": { "SPI01": 4, "SPI02": 3, ... }
}
```

> 建议先分别调用 `GET /test/sample-answers/{type}` 获取完整示例答案，拼装后提交。

---

### 8.10 一键测试（使用内置 Mock 数据）

```
POST {{baps_url}}/test/full-assessment
```

> 无需请求体，直接返回完整四合一评估结果。

---

### 8.11 Dify 集成 Schema

```
GET {{baps_url}}/openapi-tools.json
```

---

## 九、鉴权方式速查

| 接口分组 | 鉴权方式 | 说明 |
|---------|---------|------|
| `/api/v1/auth/*` | 无 / Bearer Token | login/register 无需鉴权 |
| `/api/v1/mp/*` | `X-User-ID` Header | 值为用户 ID 数字 |
| `/api/v1/mp/device/*` | `X-User-ID` Header | 值为用户 ID 数字 |
| `/api/assessment/*` | Bearer Token | Authorization Header |
| `/orchestrator/*` | 无 | 目前无鉴权要求 |
| `/api/v1/dispatch` | 无 | 目前无鉴权要求 |
| BAPS (端口 8001) | 无 | 独立服务，无鉴权 |

---

## 十、常见问题排查

### Q1: 返回 401 Unauthorized
- 检查 Token 是否过期（有效期 30 分钟）
- 重新登录获取新 Token

### Q2: 返回 404 Not Found
- 确认 URL 路径正确（注意 `/api/v1/mp` 前缀）
- 确认服务已启动

### Q3: 返回 422 Validation Error
- 检查请求体 JSON 格式
- 确认必填字段是否齐全
- 检查字段类型是否正确

### Q4: AI 对话无响应
- 先调用 `GET /api/v1/mp/llm/health` 确认 Ollama 运行中
- 确认 `qwen2.5:14b` 模型已下载

### Q5: BAPS 服务连接失败
- BAPS 是独立服务，需单独启动（端口 8001）
- `python -m uvicorn api.baps_api:app --host 0.0.0.0 --port 8001`

---

*文档由 Claude 自动生成 | 2026-01-31*

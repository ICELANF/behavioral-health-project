# 设备数据接入 API 设计文档

**版本**: v1.0
**日期**: 2026-01-28
**状态**: 设计中

---

## 1. 概述

### 1.1 目标

为行为健康平台提供完整的设备数据接入能力，支持：
- CGM 血糖监测设备（雅培瞬感、德康 G6/G7 等）
- 智能手环/手表（Apple Watch、华为手环、小米手环等）
- 睡眠监测设备
- 体重秤、血压计等

### 1.2 设计原则

1. **统一接口**: 不同设备厂商的数据统一为标准格式
2. **灵活扩展**: 易于添加新设备类型
3. **离线优先**: 支持离线数据缓存和批量同步
4. **隐私安全**: 数据加密传输，用户授权控制

---

## 2. 数据模型

### 2.1 设备类型枚举

```python
class DeviceType(str, Enum):
    """设备类型"""
    CGM = "cgm"                  # 连续血糖监测
    GLUCOMETER = "glucometer"    # 指尖血糖仪
    SMARTWATCH = "smartwatch"    # 智能手表
    SMARTBAND = "smartband"      # 智能手环
    SLEEP_TRACKER = "sleep_tracker"  # 睡眠追踪器
    SCALE = "scale"              # 体重秤
    BP_MONITOR = "bp_monitor"    # 血压计
    THERMOMETER = "thermometer"  # 体温计
```

### 2.2 设备信息

```python
class DeviceInfo(BaseModel):
    """设备信息"""
    device_id: str              # 设备唯一标识
    device_type: DeviceType     # 设备类型
    manufacturer: str           # 制造商 (abbott/dexcom/huawei/xiaomi/apple)
    model: str                  # 型号
    firmware_version: str       # 固件版本
    battery_level: Optional[int]  # 电量百分比
    last_sync_at: Optional[datetime]  # 最后同步时间
    status: str                 # connected/disconnected/expired
```

### 2.3 血糖数据 (CGM/Glucometer)

```python
class GlucoseReading(BaseModel):
    """单次血糖读数"""
    value: float                # 血糖值 (mmol/L)
    value_mgdl: Optional[float] # 血糖值 (mg/dL)
    trend: Optional[str]        # 趋势: rising_fast/rising/stable/falling/falling_fast
    trend_arrow: Optional[str]  # 趋势箭头: ↑↑/↑/→/↓/↓↓
    timestamp: datetime         # 测量时间
    source: str                 # cgm/finger/manual
    meal_tag: Optional[str]     # 餐标: fasting/before_meal/after_meal/bedtime
    notes: Optional[str]        # 备注


class GlucoseData(BaseModel):
    """血糖数据集合"""
    readings: List[GlucoseReading]

    # CGM 统计指标 (24h)
    avg_glucose: Optional[float]       # 平均血糖
    std_glucose: Optional[float]       # 血糖标准差
    cv: Optional[float]                # 变异系数 (%)
    time_in_range: Optional[float]     # TIR: 3.9-10.0 mmol/L (%)
    time_below_range: Optional[float]  # TBR: <3.9 mmol/L (%)
    time_above_range: Optional[float]  # TAR: >10.0 mmol/L (%)
    gmi: Optional[float]               # 血糖管理指标
    high_events: int = 0               # 高血糖事件数
    low_events: int = 0                # 低血糖事件数
```

### 2.4 心率/HRV 数据

```python
class HeartRateReading(BaseModel):
    """心率读数"""
    hr: int                     # 心率 (bpm)
    timestamp: datetime
    activity_type: Optional[str]  # rest/walk/run/sleep


class HRVReading(BaseModel):
    """HRV 读数"""
    sdnn: Optional[float]       # SDNN (ms)
    rmssd: Optional[float]      # RMSSD (ms)
    lf: Optional[float]         # 低频功率
    hf: Optional[float]         # 高频功率
    lf_hf_ratio: Optional[float]  # LF/HF 比值
    timestamp: datetime


class HeartData(BaseModel):
    """心脏数据"""
    heart_rate_readings: List[HeartRateReading]
    hrv_readings: List[HRVReading]

    # 统计指标
    resting_hr: Optional[int]      # 静息心率
    max_hr: Optional[int]          # 最大心率
    avg_hr: Optional[int]          # 平均心率
    avg_hrv: Optional[float]       # 平均 HRV
    stress_score: Optional[float]  # 压力分数 (0-100)
    recovery_score: Optional[float]  # 恢复分数 (0-100)
```

### 2.5 睡眠数据

```python
class SleepStage(BaseModel):
    """睡眠阶段"""
    stage: str          # awake/light/deep/rem
    start_time: datetime
    end_time: datetime
    duration_min: int


class SleepData(BaseModel):
    """睡眠数据"""
    sleep_start: datetime          # 入睡时间
    sleep_end: datetime            # 醒来时间
    total_duration_min: int        # 总时长 (分钟)

    # 睡眠阶段
    stages: List[SleepStage]
    awake_min: int = 0             # 清醒时长
    light_min: int = 0             # 浅睡时长
    deep_min: int = 0              # 深睡时长
    rem_min: int = 0               # REM 时长

    # 质量指标
    sleep_score: Optional[int]     # 睡眠评分 (0-100)
    efficiency: Optional[float]    # 睡眠效率 (%)
    awakenings: int = 0            # 夜醒次数
    onset_latency_min: Optional[int]  # 入睡潜伏期

    # 环境数据
    avg_spo2: Optional[float]      # 平均血氧
    min_spo2: Optional[float]      # 最低血氧
    snoring_min: Optional[int]     # 打鼾时长
```

### 2.6 运动数据

```python
class ActivityData(BaseModel):
    """运动/活动数据"""
    date: date

    # 基础指标
    steps: int = 0                 # 步数
    distance_m: int = 0            # 距离 (米)
    floors_climbed: int = 0        # 爬楼层数
    calories_total: int = 0        # 总消耗卡路里
    calories_active: int = 0       # 活动消耗卡路里

    # 时间分布
    sedentary_min: int = 0         # 久坐时长
    light_active_min: int = 0      # 轻度活动
    moderate_active_min: int = 0   # 中度活动
    vigorous_active_min: int = 0   # 剧烈活动

    # 运动记录
    workouts: List[WorkoutSession] = []


class WorkoutSession(BaseModel):
    """单次运动记录"""
    workout_type: str              # walk/run/cycle/swim/yoga/...
    start_time: datetime
    end_time: datetime
    duration_min: int
    distance_m: Optional[int]
    calories: Optional[int]
    avg_hr: Optional[int]
    max_hr: Optional[int]
    avg_pace: Optional[str]        # 配速 (min/km)
```

### 2.7 体征数据

```python
class VitalSigns(BaseModel):
    """体征数据"""
    timestamp: datetime

    # 体重/体成分
    weight_kg: Optional[float]
    bmi: Optional[float]
    body_fat_percent: Optional[float]
    muscle_mass_kg: Optional[float]
    water_percent: Optional[float]
    bone_mass_kg: Optional[float]
    visceral_fat: Optional[int]
    metabolic_age: Optional[int]

    # 血压
    systolic: Optional[int]        # 收缩压
    diastolic: Optional[int]       # 舒张压
    pulse: Optional[int]           # 脉搏

    # 体温
    temperature: Optional[float]   # 体温 (℃)

    # 血氧
    spo2: Optional[float]          # 血氧饱和度 (%)
```

---

## 3. API 接口设计

### 3.1 设备管理

#### 3.1.1 获取已绑定设备列表

```
GET /api/v1/mp/devices

Headers:
  X-User-ID: 1

Response:
{
  "devices": [
    {
      "device_id": "cgm_abbott_001",
      "device_type": "cgm",
      "manufacturer": "abbott",
      "model": "Libre 3",
      "status": "connected",
      "battery_level": 85,
      "last_sync_at": "2026-01-28T10:30:00Z"
    }
  ],
  "total": 1
}
```

#### 3.1.2 绑定新设备

```
POST /api/v1/mp/devices/bind

Body:
{
  "device_type": "cgm",
  "manufacturer": "abbott",
  "auth_code": "xxxxxx",        // 设备授权码
  "device_serial": "LIB3-XXXX"  // 设备序列号
}

Response:
{
  "success": true,
  "device_id": "cgm_abbott_001",
  "message": "设备绑定成功"
}
```

#### 3.1.3 解绑设备

```
DELETE /api/v1/mp/devices/{device_id}

Response:
{
  "success": true,
  "message": "设备已解绑"
}
```

#### 3.1.4 刷新设备状态

```
POST /api/v1/mp/devices/{device_id}/refresh

Response:
{
  "device_id": "cgm_abbott_001",
  "status": "connected",
  "battery_level": 82,
  "last_reading_at": "2026-01-28T10:35:00Z"
}
```

---

### 3.2 数据同步

#### 3.2.1 上传设备数据 (通用)

```
POST /api/v1/mp/device-data/sync

Body:
{
  "device_id": "cgm_abbott_001",
  "sync_type": "incremental",    // full/incremental
  "data_types": ["glucose"],
  "start_time": "2026-01-28T00:00:00Z",
  "end_time": "2026-01-28T23:59:59Z",
  "data": {
    "glucose": {
      "readings": [
        {
          "value": 6.5,
          "trend": "stable",
          "timestamp": "2026-01-28T08:00:00Z",
          "meal_tag": "fasting"
        }
      ]
    }
  }
}

Response:
{
  "success": true,
  "sync_id": "sync_20260128_001",
  "records_processed": 288,
  "records_new": 24,
  "records_updated": 0,
  "next_sync_cursor": "cursor_xxx"
}
```

#### 3.2.2 获取同步历史

```
GET /api/v1/mp/device-data/sync-history?limit=10

Response:
{
  "history": [
    {
      "sync_id": "sync_20260128_001",
      "device_id": "cgm_abbott_001",
      "sync_type": "incremental",
      "status": "success",
      "records_count": 288,
      "synced_at": "2026-01-28T10:30:00Z"
    }
  ]
}
```

---

### 3.3 血糖数据

#### 3.3.1 获取血糖数据

```
GET /api/v1/mp/glucose?start_date=2026-01-21&end_date=2026-01-28

Response:
{
  "readings": [
    {
      "value": 6.5,
      "value_mgdl": 117,
      "trend": "stable",
      "trend_arrow": "→",
      "timestamp": "2026-01-28T08:00:00Z",
      "source": "cgm",
      "meal_tag": "fasting"
    }
  ],
  "statistics": {
    "avg_glucose": 7.2,
    "std_glucose": 1.5,
    "cv": 20.8,
    "time_in_range": 72.5,
    "time_below_range": 2.1,
    "time_above_range": 25.4,
    "gmi": 6.8,
    "high_events": 3,
    "low_events": 1
  },
  "period": {
    "start": "2026-01-21",
    "end": "2026-01-28",
    "days": 7
  }
}
```

#### 3.3.2 获取当前血糖 (实时)

```
GET /api/v1/mp/glucose/current

Response:
{
  "value": 6.8,
  "value_mgdl": 122,
  "trend": "rising",
  "trend_arrow": "↑",
  "timestamp": "2026-01-28T10:35:00Z",
  "source": "cgm",
  "minutes_ago": 5,
  "in_range": true
}
```

#### 3.3.3 手动记录血糖

```
POST /api/v1/mp/glucose/manual

Body:
{
  "value": 7.2,
  "unit": "mmol/L",
  "meal_tag": "after_meal",
  "timestamp": "2026-01-28T12:30:00Z",
  "notes": "午餐后2小时"
}

Response:
{
  "success": true,
  "reading_id": "gluc_manual_001"
}
```

#### 3.3.4 获取每日血糖图表数据

```
GET /api/v1/mp/glucose/chart/daily?date=2026-01-28

Response:
{
  "date": "2026-01-28",
  "chart_data": {
    "timestamps": ["00:00", "00:05", ...],  // 5分钟间隔
    "values": [5.8, 5.9, ...],
    "target_low": 3.9,
    "target_high": 10.0
  },
  "events": [
    {"time": "07:30", "type": "meal", "label": "早餐"},
    {"time": "12:00", "type": "meal", "label": "午餐"},
    {"time": "14:00", "type": "exercise", "label": "散步30分钟"}
  ],
  "daily_stats": {
    "avg": 7.1,
    "min": 4.2,
    "max": 12.5,
    "tir": 68.5
  }
}
```

---

### 3.4 心率/HRV 数据

#### 3.4.1 获取心率数据

```
GET /api/v1/mp/heart-rate?date=2026-01-28

Response:
{
  "date": "2026-01-28",
  "readings": [
    {"hr": 72, "timestamp": "2026-01-28T08:00:00Z", "activity": "rest"}
  ],
  "statistics": {
    "resting_hr": 62,
    "avg_hr": 75,
    "max_hr": 145,
    "min_hr": 58
  }
}
```

#### 3.4.2 获取 HRV 数据

```
GET /api/v1/mp/hrv?start_date=2026-01-21&end_date=2026-01-28

Response:
{
  "readings": [
    {
      "sdnn": 45,
      "rmssd": 38,
      "lf_hf_ratio": 1.2,
      "timestamp": "2026-01-28T07:00:00Z"
    }
  ],
  "statistics": {
    "avg_hrv": 42,
    "trend": "stable",
    "stress_score": 35,
    "recovery_score": 72
  }
}
```

---

### 3.5 睡眠数据

#### 3.5.1 获取睡眠记录

```
GET /api/v1/mp/sleep?start_date=2026-01-21&end_date=2026-01-28

Response:
{
  "records": [
    {
      "date": "2026-01-28",
      "sleep_start": "2026-01-27T23:15:00Z",
      "sleep_end": "2026-01-28T06:45:00Z",
      "total_duration_min": 450,
      "stages": {
        "awake_min": 25,
        "light_min": 210,
        "deep_min": 95,
        "rem_min": 120
      },
      "sleep_score": 78,
      "efficiency": 89.2,
      "awakenings": 2
    }
  ],
  "weekly_avg": {
    "duration_min": 425,
    "sleep_score": 75,
    "deep_percent": 18.5
  }
}
```

#### 3.5.2 获取昨晚睡眠

```
GET /api/v1/mp/sleep/last-night

Response:
{
  "date": "2026-01-28",
  "sleep_start": "23:15",
  "sleep_end": "06:45",
  "duration": "7小时30分",
  "score": 78,
  "stages_chart": [
    {"start": "23:15", "end": "23:45", "stage": "light"},
    {"start": "23:45", "end": "01:00", "stage": "deep"},
    ...
  ],
  "insights": [
    "深睡时长充足，占比21%",
    "入睡较快，15分钟内入睡",
    "夜醒2次，建议减少睡前饮水"
  ]
}
```

---

### 3.6 运动数据

#### 3.6.1 获取活动数据

```
GET /api/v1/mp/activity?date=2026-01-28

Response:
{
  "date": "2026-01-28",
  "steps": 8523,
  "steps_goal": 10000,
  "distance_km": 6.2,
  "calories_total": 2150,
  "calories_active": 450,
  "active_minutes": 65,
  "floors_climbed": 8,
  "hourly_steps": [0, 0, 0, 0, 0, 0, 120, 850, ...],
  "workouts": [
    {
      "type": "walk",
      "start_time": "07:30",
      "duration_min": 35,
      "distance_km": 2.8,
      "calories": 180,
      "avg_hr": 95
    }
  ]
}
```

#### 3.6.2 记录运动

```
POST /api/v1/mp/activity/workout

Body:
{
  "workout_type": "walk",
  "start_time": "2026-01-28T18:00:00Z",
  "duration_min": 30,
  "distance_km": 2.5,
  "notes": "饭后散步"
}

Response:
{
  "success": true,
  "workout_id": "workout_001",
  "calories_burned": 150
}
```

---

### 3.7 体征数据

#### 3.7.1 获取体重记录

```
GET /api/v1/mp/weight?start_date=2026-01-01&end_date=2026-01-28

Response:
{
  "records": [
    {
      "date": "2026-01-28",
      "weight_kg": 72.5,
      "bmi": 24.2,
      "body_fat_percent": 22.5,
      "muscle_mass_kg": 32.1
    }
  ],
  "trend": {
    "weight_change_kg": -1.5,
    "period_days": 28,
    "direction": "decreasing"
  }
}
```

#### 3.7.2 记录体重

```
POST /api/v1/mp/weight

Body:
{
  "weight_kg": 72.3,
  "body_fat_percent": 22.3,
  "timestamp": "2026-01-28T07:00:00Z"
}
```

#### 3.7.3 获取血压记录

```
GET /api/v1/mp/blood-pressure?limit=10

Response:
{
  "records": [
    {
      "systolic": 125,
      "diastolic": 82,
      "pulse": 72,
      "timestamp": "2026-01-28T08:00:00Z",
      "position": "sitting",
      "arm": "left"
    }
  ],
  "statistics": {
    "avg_systolic": 122,
    "avg_diastolic": 80,
    "classification": "正常偏高"
  }
}
```

---

### 3.8 数据聚合/仪表盘

#### 3.8.1 获取今日健康概览

```
GET /api/v1/mp/dashboard/today

Response:
{
  "date": "2026-01-28",
  "glucose": {
    "current": 6.8,
    "trend": "stable",
    "avg_today": 7.1,
    "tir_today": 75.2,
    "status": "good"
  },
  "activity": {
    "steps": 5230,
    "steps_goal": 10000,
    "progress_percent": 52.3,
    "active_minutes": 35
  },
  "sleep": {
    "last_night_hours": 7.5,
    "score": 78,
    "status": "good"
  },
  "heart": {
    "resting_hr": 62,
    "current_hr": 75,
    "stress_level": "low"
  },
  "alerts": [
    {
      "type": "glucose_high",
      "message": "午餐后血糖偏高 (11.2 mmol/L)",
      "time": "13:30",
      "severity": "warning"
    }
  ]
}
```

#### 3.8.2 获取周报/月报

```
GET /api/v1/mp/dashboard/report?period=week&date=2026-01-28

Response:
{
  "period": "2026-01-22 ~ 2026-01-28",
  "glucose_summary": {
    "avg": 7.2,
    "tir": 68.5,
    "trend": "improving",
    "best_day": "2026-01-26",
    "worst_day": "2026-01-23"
  },
  "activity_summary": {
    "total_steps": 52350,
    "avg_daily_steps": 7478,
    "active_days": 6,
    "total_workouts": 4
  },
  "sleep_summary": {
    "avg_duration_hours": 7.2,
    "avg_score": 74,
    "best_night": "2026-01-25"
  },
  "insights": [
    "本周血糖控制有所改善，TIR 提升 5%",
    "运动量较上周减少，建议增加活动",
    "睡眠质量稳定，继续保持"
  ],
  "recommendations": [
    "尝试餐后15分钟散步，有助于控制餐后血糖",
    "本周目标：每天步数达到8000步"
  ]
}
```

---

## 4. WebSocket 实时数据

### 4.1 实时血糖推送

```
WS /api/v1/mp/ws/glucose

// 客户端订阅
{
  "action": "subscribe",
  "device_id": "cgm_abbott_001"
}

// 服务端推送
{
  "type": "glucose_reading",
  "data": {
    "value": 6.8,
    "trend": "stable",
    "timestamp": "2026-01-28T10:40:00Z"
  }
}

// 告警推送
{
  "type": "glucose_alert",
  "data": {
    "alert_type": "high",
    "value": 13.5,
    "threshold": 10.0,
    "message": "血糖偏高，请注意"
  }
}
```

---

## 5. 第三方平台集成

### 5.1 支持的平台

| 平台 | 数据类型 | 接入方式 |
|------|---------|---------|
| Apple Health | 全部 | HealthKit API |
| 华为健康 | 全部 | HUAWEI Health Kit |
| 小米运动健康 | 运动/睡眠/心率 | Mi Fitness API |
| 雅培瞬感 | CGM | LibreView API |
| 德康 | CGM | Dexcom API |
| Keep | 运动 | Keep Open API |
| 微信运动 | 步数 | 微信 API |

### 5.2 OAuth 授权流程

```
GET /api/v1/mp/oauth/{platform}/authorize
  → 返回授权 URL

GET /api/v1/mp/oauth/{platform}/callback?code=xxx
  → 处理回调，保存 Token

POST /api/v1/mp/oauth/{platform}/revoke
  → 取消授权
```

---

## 6. 数据库表设计

### 6.1 设备表 (user_devices)

```sql
CREATE TABLE user_devices (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  device_id VARCHAR(100) UNIQUE NOT NULL,
  device_type VARCHAR(50) NOT NULL,
  manufacturer VARCHAR(50),
  model VARCHAR(100),
  firmware_version VARCHAR(50),
  status VARCHAR(20) DEFAULT 'connected',
  auth_token TEXT,
  auth_expires_at DATETIME,
  last_sync_at DATETIME,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME,

  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_user_devices_user ON user_devices(user_id);
CREATE INDEX idx_user_devices_type ON user_devices(device_type);
```

### 6.2 血糖数据表 (glucose_readings)

```sql
CREATE TABLE glucose_readings (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  device_id VARCHAR(100),
  value REAL NOT NULL,
  unit VARCHAR(10) DEFAULT 'mmol/L',
  trend VARCHAR(20),
  source VARCHAR(20) DEFAULT 'manual',
  meal_tag VARCHAR(20),
  notes TEXT,
  recorded_at DATETIME NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_glucose_user_time ON glucose_readings(user_id, recorded_at);
```

### 6.3 心率数据表 (heart_rate_readings)

```sql
CREATE TABLE heart_rate_readings (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  device_id VARCHAR(100),
  hr INTEGER NOT NULL,
  activity_type VARCHAR(20),
  recorded_at DATETIME NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 6.4 HRV 数据表 (hrv_readings)

```sql
CREATE TABLE hrv_readings (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  device_id VARCHAR(100),
  sdnn REAL,
  rmssd REAL,
  lf REAL,
  hf REAL,
  lf_hf_ratio REAL,
  stress_score REAL,
  recovery_score REAL,
  recorded_at DATETIME NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 6.5 睡眠数据表 (sleep_records)

```sql
CREATE TABLE sleep_records (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  device_id VARCHAR(100),
  sleep_date DATE NOT NULL,
  sleep_start DATETIME,
  sleep_end DATETIME,
  total_duration_min INTEGER,
  awake_min INTEGER DEFAULT 0,
  light_min INTEGER DEFAULT 0,
  deep_min INTEGER DEFAULT 0,
  rem_min INTEGER DEFAULT 0,
  sleep_score INTEGER,
  efficiency REAL,
  awakenings INTEGER DEFAULT 0,
  avg_spo2 REAL,
  min_spo2 REAL,
  stages_data JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (user_id) REFERENCES users(id),
  UNIQUE(user_id, sleep_date)
);
```

### 6.6 活动数据表 (activity_records)

```sql
CREATE TABLE activity_records (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  activity_date DATE NOT NULL,
  steps INTEGER DEFAULT 0,
  distance_m INTEGER DEFAULT 0,
  floors_climbed INTEGER DEFAULT 0,
  calories_total INTEGER DEFAULT 0,
  calories_active INTEGER DEFAULT 0,
  sedentary_min INTEGER DEFAULT 0,
  light_active_min INTEGER DEFAULT 0,
  moderate_active_min INTEGER DEFAULT 0,
  vigorous_active_min INTEGER DEFAULT 0,
  hourly_data JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME,

  FOREIGN KEY (user_id) REFERENCES users(id),
  UNIQUE(user_id, activity_date)
);
```

### 6.7 运动记录表 (workout_records)

```sql
CREATE TABLE workout_records (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  device_id VARCHAR(100),
  workout_type VARCHAR(50) NOT NULL,
  start_time DATETIME NOT NULL,
  end_time DATETIME,
  duration_min INTEGER,
  distance_m INTEGER,
  calories INTEGER,
  avg_hr INTEGER,
  max_hr INTEGER,
  avg_pace VARCHAR(20),
  notes TEXT,
  gps_data JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 6.8 体征数据表 (vital_signs)

```sql
CREATE TABLE vital_signs (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  device_id VARCHAR(100),
  data_type VARCHAR(20) NOT NULL,  -- weight/blood_pressure/temperature/spo2

  -- 体重
  weight_kg REAL,
  bmi REAL,
  body_fat_percent REAL,
  muscle_mass_kg REAL,

  -- 血压
  systolic INTEGER,
  diastolic INTEGER,
  pulse INTEGER,

  -- 体温
  temperature REAL,

  -- 血氧
  spo2 REAL,

  recorded_at DATETIME NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

  FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_vital_signs_user_type ON vital_signs(user_id, data_type, recorded_at);
```

---

## 7. 错误码定义

| 错误码 | 说明 |
|--------|------|
| DEVICE_001 | 设备未找到 |
| DEVICE_002 | 设备已绑定其他用户 |
| DEVICE_003 | 设备连接失败 |
| DEVICE_004 | 设备授权已过期 |
| SYNC_001 | 数据同步失败 |
| SYNC_002 | 数据格式错误 |
| SYNC_003 | 时间范围无效 |
| DATA_001 | 数据不存在 |
| DATA_002 | 数据超出有效范围 |
| AUTH_001 | 第三方授权失败 |
| AUTH_002 | Token 已过期 |

---

## 8. 实现优先级

### Phase 1 (本周)
- [x] 数据模型定义
- [ ] 基础 API 框架
- [ ] 手动数据录入 (血糖/体重)
- [ ] 数据查询接口

### Phase 2 (下周)
- [ ] 设备绑定管理
- [ ] 数据同步机制
- [ ] 仪表盘聚合接口

### Phase 3 (后续)
- [ ] 第三方平台 OAuth
- [ ] WebSocket 实时推送
- [ ] 智能分析与建议

---

## 9. 附录

### 9.1 单位换算

```python
# 血糖单位换算
def mmol_to_mgdl(mmol: float) -> float:
    return mmol * 18.0182

def mgdl_to_mmol(mgdl: float) -> float:
    return mgdl / 18.0182
```

### 9.2 血糖范围参考

| 状态 | mmol/L | mg/dL |
|------|--------|-------|
| 低血糖 | <3.9 | <70 |
| 目标范围 | 3.9-10.0 | 70-180 |
| 高血糖 | >10.0 | >180 |
| 严重高血糖 | >13.9 | >250 |

### 9.3 HRV 参考值

| 年龄 | 正常 SDNN (ms) | 正常 RMSSD (ms) |
|------|---------------|----------------|
| 20-29 | 50-100 | 25-45 |
| 30-39 | 45-90 | 22-42 |
| 40-49 | 40-80 | 20-40 |
| 50-59 | 35-70 | 18-38 |
| 60+ | 30-60 | 15-35 |

---

**文档维护**: Claude (Opus 4.5)
**最后更新**: 2026-01-28

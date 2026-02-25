# 视频调度效果评估 Dashboard（行为指标｜V1）

## 一、设计原则
- 不使用内容平台指标（播放量/完播率/点赞）
- 只评估**行为是否更容易发生**
- 指标必须能反向校准 Agent 与语义规则

---

## 二、Dashboard 总览（模块）

### 1️⃣ 视频触发有效性（是否该出现）

| 指标 | 定义 | 说明 |
|---|---|---|
| Dispatch Hit Rate | 触发后被观看比例 | 过低=时机不对 |
| Soft Refusal Rate | 用户跳过但继续对话 | 跳过≠失败 |
| Hard Exit Rate | 视频后会话中断 | 需警惕 |

---

### 2️⃣ 行为状态迁移（核心）

| 指标 | 计算 | 意义 |
|---|---|---|
| State Shift + | 观看后状态改善率 | 主 KPI |
| Resistance ↓ | 阻抗信号下降 | 去防御是否成功 |
| Neutral Hold | 状态稳定率 | 不恶化也算成功 |

---

### 3️⃣ 微行为发生率（真实效果）

| 指标 | 定义 |
|---|---|
| Micro-Action Rate | 72h 内任一微行为 |
| Zero-Action Safe | 选择“什么都不做”但未流失 |
| Action Retention | 7 天内持续率 |

---

### 4️⃣ 情绪与节律指标（语义层）

| 指标 | 来源 |
|---|---|
| Emotional Tone Shift | NLP 情绪曲线 |
| Pace Compatibility | 对话节奏匹配度 |
| Pressure Index | 催促语义占比 |

---

### 5️⃣ 教练 / 人工介入关联

| 指标 | 说明 |
|---|---|
| Coach Takeover Rate | 视频后升级比例 |
| Pre-Intervention Relief | 是否降低介入强度 |
| Post-Video Coach Success | 教练介入成功率 |

---

## 三、核心图表（Dashboard 组件）

- 行为状态 Sankey 图（前 → 后）
- 视频类型 × 状态迁移热力图
- 视频 → 微行为转化漏斗
- 视频调度失败 Top10

---

## 四、告警规则（系统自我保护）

```yaml
alerts:
  - name: video_causes_drop
    condition: hard_exit_rate > 0.25
    action: disable_video

  - name: pressure_spike
    condition: pressure_index > baseline * 1.2
    action: reduce_dispatch
```

---

## 五、评估结论输出（给系统用）

```json
{
  "video_id": "VID_001",
  "status": "effective",
  "recommended_usage": ["contemplation", "relapse"],
  "notes": "reduces resistance, no action push"
}
```


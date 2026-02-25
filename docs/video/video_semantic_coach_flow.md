# 视频 × 语义规则 × 教练介入 系统联动图（执行级）

## 一、系统联动总览

```text
用户信号
  ↓
状态识别（TTM / 阻抗 / 情绪）
  ↓
Decision Engine（L1/L2）
  ↓
Semantic Layer（L3 语义规则）
  ↓
Video Dispatch（如适用）
  ↓
视频互动（前 / 中 / 后）
  ↓
对话接管（Agent）
  ↓
教练介入判断（如需要）
```

---

## 二、联动触发矩阵

| 触发条件 | 视频 | 语义规则 | 教练 |
|---|---|---|---|
| 高阻抗 | 去羞耻类 | 降压 / 共情 | 观察 |
| 长期停滞 | 认知澄清 | 节律放慢 | 可选 |
| 多次复发 | 正常化 | 失败去污名 | 推荐 |
| 情绪失控 | 压力调节 | 安全语气 | 必须 |

---

## 三、责任边界（硬约束）

```text
视频：只能改变理解与情绪
语义规则：只能改变说法与节奏
教练：唯一可以影响行动结构的人
```

---

## 四、教练接管判定逻辑

```yaml
coach_handoff:
  conditions:
    - repeated_relapse >= 3
    - emotional_instability == high
  precondition:
    video_used: true
  action:
    notify_coach
```

---

## 五、反向校准回路

```text
视频效果 ↓
语义规则命中率 ↓
教练介入成功率 ↓

→ 规则调整 / 视频禁用 / 培训更新
```

---

## 六、系统状态标签（用于 UI / 运营）

- companion_only
- video_supporting
- coach_observing
- coach_active

---

## 七、执行结论

该联动结构确保：
- AI 不越权
- 视频不滥用
- 教练介入有据可依

👉 可直接作为系统架构与合规说明附图。


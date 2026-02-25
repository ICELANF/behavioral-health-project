# 行为健康平台｜视频 × 行为 × Agent 调度工程配置表（V1）

> 本配置用于：
> - 将**视频教学内容**纳入行为系统调度
> - 作为 **流量入口 / 行为陪伴 / 教练学习**的统一资源层
> - 直接被 Agent Runtime 调用（非内容推荐系统）

---

## 一、核心设计原则（工程约束）

1. 视频不是内容，而是 **Behavior Support Asset**
2. 视频不能直接触发行为，只能：
   - 改变认知状态
   - 调整情绪负荷
   - 降低阻抗
3. 视频调用权在 Agent，不在用户自由浏览
4. 每个视频 **必须绑定“可用人群 + 可用状态 + 允许效果”**

---

## 二、Video Asset 主表（video_asset）

```yaml
video_asset:
  id: VID_001
  title: "为什么你不是不自律"
  duration_sec: 420

  content_type: science_pop
  level: L3

  target_population:
    - general_public
    - weight_management

  applicable_states:
    - precontemplation
    - contemplation

  primary_purpose:
    - normalize_experience
    - reduce_self_blame

  allowed_effects:
    - pressure_reduction
    - empathy_activation

  forbidden_effects:
    - action_push
    - goal_setting

  followup_mode:
    - dialogue_takeover
    - delayed_checkin_48h
```

---

## 三、行为状态 × 视频类型 映射表

| 行为状态 | 允许视频目的 | 禁止视频类型 |
|---|---|---|
| 未考虑 | 认知启蒙 / 去标签 | 行动教学 |
| 考虑中 | 矛盾外化 / 同伴经验 | 强目标 |
| 准备期 | 示范 / 降低不确定 | 励志鸡汤 |
| 行动期 | 微技巧 / 失败预期 | 新理论 |
| 复发期 | 去羞耻 / 正常化 | 责备式 |

---

## 四、Agent 调度规则表（video_dispatch_rule）

```yaml
- rule_id: VDR_01
  trigger:
    user_state: contemplation
    signals:
      - hesitation
      - repeated_questions

  conditions:
    no_action_days: ">=3"
    emotional_tone: defensive

  dispatch:
    recommend_video: VID_001
    mode: soft_suggestion

  post_video:
    next_step:
      type: dialogue_prompt
      text: "刚刚那段里，有哪一句让你停了一下？"
```

---

## 五、视频互动点配置（interaction_hook）

```yaml
interaction_hook:
  video_id: VID_001

  before_play:
    question: "你现在更接近哪种状态？"
    options: [犹豫, 已在做, 卡住, 只是了解]

  mid_play:
    timestamp_sec: 210
    question: "如果是你，此刻更可能？"
    options: [停下, 拖延, 继续, 调整]

  after_play:
    micro_choice:
      options:
        - 什么都不做
        - 试1分钟
        - 试一次
        - 设提醒
```

---

## 六、视频 → 对话接管协议

```yaml
video_dialogue_handoff:
  video_id: VID_001
  agent_prompt:
    role: companion
    tone: low_pressure
    opening_line: "这段视频里哪一部分更像你？"
```

---

## 七、延迟反馈与效果观测

```yaml
video_followup:
  video_id: VID_001
  delay_hours: 48

  checkin_question: "回头看那天的视频，现在有什么变化吗？"

  metrics:
    - conversation_continued
    - emotional_shift
    - micro_action_taken
```

---

## 八、教练 / 学习型视频扩展字段

```yaml
coach_extension:
  reflection_prompt: "如果这是你的来访者，你会避免说什么？"
  forbidden_intervention: [目标设定, 行为加码]
```

---

## 九、工程调用顺序（硬约束）

```text
User State Detection
 → Decision Engine（L1/L2）
 → Semantic Layer（L3）
 → Video Dispatch Check
 → Video Interaction
 → Dialogue Takeover
```

---

## 十、你现在可以立刻做的事

1. 用此模板标注你现有视频（哪怕先 10 条）
2. 接入 Agent Runtime 的 dispatch 模块
3. 内测：观察视频是否减少阻抗而非增加负担

---

## 结论（封型判断）

视频在此系统中已经：
- 不再是被动内容
- 不再是学习负担
- 而是**在正确时间出现的“理解工具”**

👉 **该配置可直接进入开发与内容标注阶段。**


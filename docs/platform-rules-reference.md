# 行健平台 — 规则体系完整参考文档

**版本:** V5.2.6
**生成时间:** 2026-02-24
**适用范围:** 行为健康数字平台全部规则性内容的唯一权威参考
**代码库:** `D:\behavioral-health-project`

---

## 目录

- [一、平台语义规则](#一平台语义规则)
  - [1.1 六级四同道者角色体系](#11-六级四同道者角色体系)
  - [1.2 TTM 七阶段行为改变模型](#12-ttm-七阶段行为改变模型)
  - [1.3 用户分层与权限模型](#13-用户分层与权限模型)
  - [1.4 AI→审核→推送铁律](#14-ai审核推送铁律)
- [二、交互规划规则](#二交互规划规则)
  - [2.1 评估管线 (BAPS)](#21-评估管线-baps)
  - [2.2 Agent 路由与协作](#22-agent-路由与协作)
  - [2.3 MasterAgent 九步管线](#23-masteragent-九步管线)
  - [2.4 V4.0 四大陪伴 Agent](#24-v40-四大陪伴-agent)
  - [2.5 推送审批工作流](#25-推送审批工作流)
  - [2.6 推送推荐引擎 (六规则)](#26-推送推荐引擎六规则)
  - [2.7 方案管理与挑战生命周期](#27-方案管理与挑战生命周期)
  - [2.8 定时任务体系 (20 Jobs)](#28-定时任务体系-20-jobs)
- [三、行为处方生成规则](#三行为处方生成规则)
  - [3.1 三维处方模型概述](#31-三维处方模型概述)
  - [3.2 维度一: TTM 阶段→策略选择](#32-维度一-ttm-阶段策略选择)
  - [3.3 维度二: BigFive 人格→沟通风格](#33-维度二-bigfive-人格沟通风格)
  - [3.4 维度三: CAPACITY→强度校准](#34-维度三-capacity强度校准)
  - [3.5 微行动生成规则](#35-微行动生成规则)
  - [3.6 阻力阈值与升级规则](#36-阻力阈值与升级规则)
  - [3.7 处方有效性评估 (IES)](#37-处方有效性评估-ies)
  - [3.8 混合路由: BehaviorRx→LLM 降级](#38-混合路由-behaviorrxllm-降级)
  - [3.9 Profile→RxContext 适配规则](#39-profilerxcontext-适配规则)
  - [3.10 沟通风格→干预语调映射](#310-沟通风格干预语调映射)
  - [3.11 Observer→Grower 初始处方生成规则](#311-observergrower-初始处方生成规则)
  - [3.12 处方查询与权限规则](#312-处方查询与权限规则)
- [四、积分与激励规则](#四积分与激励规则)
  - [4.1 三维积分体系](#41-三维积分体系)
  - [4.2 里程碑与仪式](#42-里程碑与仪式)
  - [4.3 徽章系统](#43-徽章系统)
  - [4.4 连续打卡与中断恢复](#44-连续打卡与中断恢复)
  - [4.5 晋级资格四维度检查](#45-晋级资格四维度检查)
- [五、安全管道规则](#五安全管道规则)
  - [5.1 四层安全管线 (SafetyPipeline)](#51-四层安全管线-safetypipeline)
  - [5.2 中医骨伤安全门 (OrthoSafetyGate L1-L4)](#52-中医骨伤安全门-orthosafetygate-l1-l4)
  - [5.3 策略引擎五步管线 (PolicyEngine)](#53-策略引擎五步管线-policyengine)
- [六、设备预警规则](#六设备预警规则)
- [七、治理与同道者规则 (V4.0)](#七治理与同道者规则-v40)

---

## 一、平台语义规则

### 1.1 六级四同道者角色体系

> **权威来源:** `api/paths_api.py` `_LEVEL_THRESHOLDS` + `_LEVEL_META` + `_COMPANION_REQS`
> **DB 执行:** `core/learning_service.py` `ROLE_PROGRESSION_RULES`
> **显示/计算:** `api/learning_api.py` `COACH_LEVEL_REQUIREMENTS`

#### 角色层级

| 等级 | 角色 | 标识 | 角色代码 | role_level |
|------|------|------|----------|-----------|
| L0 | 观察员 | 👀 | OBSERVER | 1 |
| L1 | 成长者 | 🌱 | GROWER | 2 |
| L2 | 分享者 | 💬 | SHARER | 3 |
| L3 | 行为健康教练 | 🎯 | COACH | 4 |
| L4 | 行为健康促进师 | ⭐ | PROMOTER / SUPERVISOR | 5 |
| L5 | 行为健康促进大师 | 👑 | MASTER | 6 |
| — | 系统管理员 | — | ADMIN | 99 |

#### 晋级三维积分门槛

| 晋级路径 | 成长积分 | 贡献积分 | 影响力积分 | 考试 | 同道者要求 |
|----------|---------|---------|-----------|------|-----------|
| L0→L1 | ≥100 | — | — | 否 | — |
| L1→L2 | ≥500 | ≥50 | — | 否 | — |
| L2→L3 | ≥800 | ≥200 | ≥50 | 是 | 4位 L1 成长者 |
| L3→L4 | ≥1500 | ≥600 | ≥200 | 是 | 4位 L2 分享者 |
| L4→L5 | ≥3000 | ≥1500 | ≥600 | 是 | 4位 L3 教练 |

#### L0→L1 特殊要求 (Observer→Grower 升级)

L0→L1 不走积分门槛, 而是走**评估完成检查** (`api/r4_role_upgrade_trigger.py`):

| 评估模块 | 全称 | 必须状态 |
|----------|------|---------|
| ttm7 | TTM-7 行为阶段评估 (21题) | completed |
| big5 | 大五人格 (50题) | completed |
| bpt6 | 行为模式分型 BPT-6 (18题) | completed |
| capacity | CAPACITY 能力评估 (32题) | completed |
| spi | 成功概率指数 SPI (50题) | completed |

升级执行流程: 评估检查 → 角色更新 → 初始化打卡记录 → 生成行为处方 → 生成每日任务

#### 等级计算逻辑

```
_compute_user_level(stats):
  从 L5 往 L0 逐级检查
  若 growth ≥ min_growth AND contribution ≥ min_contribution AND influence ≥ min_influence
  则返回该等级
  否则继续向下检查
```

#### 同道者计数

优先查 `companion_relations` 表, 若缺失则 fallback 到 `User.referred_by` 字段。返回达到目标角色的被引领人数。

---

### 1.2 TTM 七阶段行为改变模型

> **权威来源:** `behavior_rx/core/rx_schemas.py` + `core/models.py` `BehavioralStage`

| 阶段 | 代码 | 中文 | 核心特征 | 干预焦点 |
|------|------|------|---------|---------|
| S0 | 前意识期 | Pre-contemplation | 无意愿改变 | 意识唤醒, 情绪触动 |
| S1 | 意识期 | Contemplation | 认识到问题, 但犹豫 | 认知深化, 决策平衡 |
| S2 | 准备期 | Preparation | 准备行动 | 承诺, 自我解放 |
| S3 | 行动期 | Action | 主动改变行为 | 刺激控制, 习惯叠加 |
| S4 | 维持期 | Maintenance | 保持新行为 | 复发预防, 自我监控 |
| S5 | 巩固期 | Consolidation | 行为自动化 | 自主维持 |
| S6 | 终止期 | Termination | 完全内化 | 监测 |

**阶段稳定性** (`StageStability`):
- STABLE (0.9): 稳定在当前阶段
- SEMI_STABLE (0.5): 半稳定
- UNSTABLE (0.2): 不稳定, 有回退风险

**阶段→处方阶段映射:**
- S0-S1 → 认知唤醒
- S2 → 动机激发
- S3 → 行为塑造
- S4-S6 → 习惯强化

---

### 1.3 用户分层与权限模型

> **权威来源:** `core/user_segments.py`

#### 四来源 × 四层级

| 来源 | 代码 | 说明 |
|------|------|------|
| 自然流量 | ORGANIC | C端公共用户 |
| 教练引荐 | COACH_REFERRED | 教练推荐客户 |
| 机构合作 | INSTITUTION | 医疗机构/社区服务 |
| 企业健管 | ENTERPRISE | 企业健康管理计划 |

| 层级 | 基础功能 |
|------|---------|
| FREE | 需求调查, 内容信息流, 社区只读 (3项) |
| BASIC | + 自评估, 基础学习, 工具库, 进度追踪 (7项) |
| PREMIUM | + 完整学习, 专家咨询, 小组会话, 社区互动, AI伴行 (12项) |
| VIP | + 180天课程, 私人教练, 危机支持, 家庭支持 (16项) |

#### 来源调整

- **COACH_REFERRED:** 额外获得 AI_COMPANION
- **INSTITUTION:** 额外获得 CRISIS_SUPPORT, 限制 PRIVATE_COACH
- **ENTERPRISE:** 额外获得 GROUP_SESSION

#### 六种预定义用户画像

1. **public_observer** (ORGANIC × FREE): 基础发现
2. **self_grower** (ORGANIC × BASIC): 自主学习
3. **coach_client** (COACH_REFERRED × PREMIUM): 教练辅助 + AI伴行
4. **institution_patient** (INSTITUTION × PREMIUM): 机构照护 + 危机支持
5. **enterprise_employee** (ENTERPRISE × BASIC): 团体参与
6. **vip_member** (ORGANIC × VIP): 全功能高级会员

---

### 1.4 AI→审核→推送铁律

> **铁律:** 所有指导、建议、激励等交互性内容, 必须先由 AI 生成建议, 再交由行为健康促进师审核修改后推送。绝不允许 AI 内容直接触达用户。

**实现架构:**

```
AI推荐引擎 (push_recommendation_service)
    ↓ 生成推荐
教练审批网关 (coach_push_queue_service)
    ↓ 教练审核/修改/批准
统一推送路由 (gateway/channels/push_router)
    ↓ 写 notifications 表 + 外部渠道(微信/短信/邮件)
用户收到通知 (H5 Notifications.vue)
```

**推送状态流转:**
```
pending → approved → sent
pending → rejected (终止)
pending → expired (72小时未处理)
```

#### 通知路由级联规则

> **权威来源:** `gateway/channels/push_router.py`

`send_notification()` 的渠道选择遵循以下优先级:

```
1. 永远先写 in-app 通知 (notifications 表)
2. 渠道选择:
   a. 若指定 channel 参数 → 使用指定渠道
   b. 若用户设置 preferred_channel → 使用用户偏好
   c. 否则级联 (cascade): wechat → sms → email → in-app only
3. 渠道数据检查:
   - wechat 需要 wx_openid 非空
   - sms 需要 phone 非空
   - email 需要 email 非空
4. 指定渠道但数据缺失 → 标记 fallback=True, 按级联顺序尝试
```

**返回结构:** `{"channel_used": "wechat|sms|email|in_app", "success": bool, "fallback": bool}`

#### 通知深度链接格式

```
格式: [link:/路径]
示例: [link:/rx/rx_7e3492a63958]

解析规则 (H5 Notifications.vue):
  正则: /\[link:([^\]]+)\]/
  匹配 → 提取路径 → router.push(路径)
  不匹配 → 通知不可点击
```

#### P1 处方审批→通知 完整闭环

> **权威来源:** `api/r6_coach_flywheel_api_live.py` `approve_review()`

```
Step 1: UPDATE coach_review_queue SET status='approved'
Step 2: 若 type='prescription' → _activate_prescription()
        写入 behavior_prescriptions (status='active')
        返回 rx_id
Step 3: 触发 generate_daily_tasks_for_user() 重新生成每日任务
Step 4: INSERT INTO coach_review_logs (action='approved')
Step 5: (commit 后, non-blocking) push_router.send_notification()
        含深度链接: "[link:/rx/{rx_id}]"
```

**处方激活规则 (`_activate_prescription`):**
- 生成 `rx_id = "rx_{uuid[:12]}"` (审批激活)
- INSERT INTO behavior_prescriptions, status='active', approved_by_review=review_id
- 字段来源: rx_json 中的 target_behavior, frequency_dose, trigger_cue, obstacle_plan, domain, difficulty_level

---

## 二、交互规划规则

### 2.1 评估管线 (BAPS)

> **权威来源:** `api/assessment_pipeline_api.py`

#### 五大评估模块

| 模块 | 题数 | 评估维度 | 必选性 |
|------|------|---------|--------|
| TTM-7 | 21题 (7组×3) | 行为改变阶段就绪度 | 必选 |
| BigFive | 50题 | 人格五因素 (O/C/E/A/N) | 可选 |
| BPT-6 | 18题 | 行为模式分型 (6类) | 可选 |
| CAPACITY | 32题 | 六维能力 (信心/能力/感知/资源/兴趣/时间) | 可选 |
| SPI | 50题 | 心理层级 (L1-L5 成功概率) | 可选 |

#### TTM-7 量表结构

| 分组 | 题号 | 测量维度 |
|------|------|---------|
| 第1组 | TTM01-03 | 前意识 (Pre-contemplation) |
| 第2组 | TTM04-06 | 阻抗 (Resistance) |
| 第3组 | TTM07-09 | 意识 (Contemplation) |
| 第4组 | TTM10-12 | 准备 (Preparation) |
| 第5组 | TTM13-15 | 行动 (Action) |
| 第6组 | TTM16-18 | 维持 (Maintenance) |
| 第7组 | TTM19-21 | 终止 (Termination) |

#### BPT-6 六类行为模式

| 分型 | 代码 | 特征 |
|------|------|------|
| 行动型 | action | 偏好直接行动 |
| 认知型 | knowledge | 偏好学习理解 |
| 情感型 | emotion | 情绪驱动 |
| 关系型 | relation | 社交驱动 |
| 环境型 | environment | 环境敏感 |
| 混合型 | mixed | 多维度均衡 |

#### CAPACITY 六因子

| 因子 | 代码 | 说明 |
|------|------|------|
| 信心 | C | Confidence |
| 能力 | A | Ability |
| 感知 | P | Perception |
| 资源 | A2 | Accessibility |
| 兴趣 | I | Interest |
| 时间 | T | Time |

#### 评估数据管线

```
TTM-7 → 确定行为阶段 (S0-S6)
BigFive → 确定人格画像 (O/C/E/A/N 各 0-100)
BPT-6 → 确定行为模式分型
CAPACITY → 确定六维能力得分 + 弱项/强项
SPI → 确定心理层级 (L1-L5) + 成功概率 (0-100)
    ↓
写入 BehavioralProfile (统一画像)
    ↓
驱动处方生成 + Agent 路由 + 内容推荐
```

---

### 2.2 Agent 路由与协作

> **权威来源:** `core/agents/router.py`

#### 路由六大规则 (按优先级)

| 规则 | 权重 | 条件 | 说明 |
|------|------|------|------|
| R1 危机强制 | 立即返回 | domain=crisis + 危机关键词 | 跳过所有后续规则, 直接路由到 crisis agent |
| R2 风险等级 | +50~100分 | risk=critical/high + 匹配域 | 高风险强化对应领域权重 |
| R3a 租户关键词 | +30×boost | tenant keyword overrides 命中 | 租户自定义关键词优先级 |
| R3b 平台关键词 | +30分 | agent.matches_intent() 命中 | 平台级关键词匹配 |
| R4 用户偏好 | +20分 | preferences.focus == domain | 用户设置的关注领域 |
| R5 设备数据 | +15分/字段 | device_data 字段匹配 agent.data_fields | 设备数据类型映射 |
| R6 领域关联 | 补充 | 主 agent 已选定后, 添加关联 agent | 关联 agent 也需有关键词匹配 |

#### 16+4 Agent 清单

**9 个专科 Agent:**
metabolic (代谢), sleep (睡眠), emotion (情绪), motivation (动机), coaching (教练), nutrition (营养), exercise (运动), tcm (中医), crisis (危机)

**3 个整合 Agent:**
behavior_rx (行为处方), weight (体重), cardiac_rehab (心脏康复)

**4 个 V4.0 Agent:**
journey_companion (旅程伴行), growth_reflection (成长复盘), coach_copilot (教练副驾驶), life_designer (生命设计师)

**4 个 BehaviorRx Expert Agent:**
BehaviorCoachAgent, MetabolicExpertAgent, CardiacExpertAgent, AdherenceExpertAgent

---

### 2.3 MasterAgent 九步管线

> **权威来源:** `core/master_agent_v0.py`

```
Step 1: 接收用户输入 (TEXT/VOICE/DEVICE/FORM/ASSESSMENT/TASK_REPORT)
Step 2: 更新 User Master Profile
  Step 2.5: [V005] 安全管线输入过滤 (SafetyPipeline.input_filter)
Step 3: Agent Router 判定问题类型 + 风险优先级
  Step 3.5: [BehaviorRx] ExpertAgentRouter 选择专家 Agent
Step 4: 调用 1-2 个专科 Agent
Step 5: Multi-Agent Coordinator 统一上下文与结果
Step 6: Intervention Planner 生成个性化行为路径
Step 7: Response Synthesizer 以教练风格输出
  Step 7.5: [V005] 安全管线生成守卫 (SafetyPipeline.generation_guard)
Step 8: 写回 Master Profile + 生成每日任务
  Step 8.5: [V005] 安全管线输出过滤 (SafetyPipeline.output_filter)
Step 9: 返回最终响应
```

**风险等级:**
- CRITICAL: 需立即干预
- HIGH: 优先处理
- MODERATE: 常规处理
- LOW: 维持性干预

---

### 2.4 V4.0 四大陪伴 Agent

> **权威来源:** `core/agents/v4_agents.py`

#### JourneyCompanionAgent — 旅程伴行

| 属性 | 值 |
|------|------|
| 领域 | COACHING |
| 优先级 | 1 (最高) |
| 权重 | 0.90 |
| 关键词 | 旅程, 陪伴, 阶段, 困难, 坚持不下去, 依从, 打卡, 连续, 中断 |

**阶段感知引导:**

| 阶段 | 语调 | 引导策略 |
|------|------|---------|
| S0 | 温和接纳 | 建立安全感 |
| S1 | 好奇探索 | 帮助看见现状 |
| S2 | 鼓励耐心 | 支持尝试 |
| S3 | 协作赋能 | 巩固路径 |
| S4 | 反思深层 | 内化身份 |
| S5 | 尊重平等 | 庆祝传承 |

**Agency 模式适配:**
- passive → 主动引导
- transitional → 协作探索
- active → 镜子角色 (倾听反映)

**预警信号:**
- 依从率 <50% → 关注并建议回顾中断原因
- 依从率 <30% → 风险标记 MODERATE
- 检测到放弃关键词 ("放弃", "没用") → 接纳 + 探索差异性

#### GrowthReflectionAgent — 成长复盘

| 属性 | 值 |
|------|------|
| 优先级 | 3 |
| 权重 | 0.80 |
| 关键词 | 成长, 复盘, 反思, 觉察, 模式, 发现, 变化, 我注意到, 我意识到 |

**反思深度评估:**

| 深度分值 | 层级 | 引导 |
|----------|------|------|
| ≥0.8 | 身份层反思 | "非常深入, 可探索理想自我" |
| 0.5-0.8 | 模式觉察 | "发现规律, 记录感受" |
| 0.2-0.5 | 表面觉察 | "好的第一步, 练习细节" |
| <0.2 | 初始阶段 | "从意外事件开始练习" |

**Agency 模式任务分配:**
- passive → "这周最开心/困扰的事是?" + guided_reflection 任务
- transitional → "注意到新行为模式?" + pattern_journal (7天)
- active → "如何改变自我认知?" + identity_reflection (1次)

#### CoachCopilotAgent — 教练副驾驶

| 属性 | 值 |
|------|------|
| 优先级 | 2 |
| 权重 | 0.85 |
| 数据接入 | CGM, Sleep, HRV, Steps |

**预警检测:**

| 指标 | 阈值 | 标签 |
|------|------|------|
| CGM | >11.1 mmol/L | 血糖异常偏高 |
| CGM | <3.9 mmol/L | 血糖异常偏低 |
| Sleep | <5h | 睡眠严重不足 |
| HRV | <20ms | 压力/疲劳信号 |

**学员依从率行动建议:**
- <30% → 简化微行动 + 电话跟进 + 探索阻碍 (1天内)
- 30-60% → 回顾难度匹配 (3天内)

#### LifeDesignerAgent — 生命设计师

| 属性 | 值 |
|------|------|
| 优先级 | 4 |
| 权重 | 0.75 |
| 关键词 | 人生, 身份, 价值观, 使命, 意义, 成为, 未来, 生命设计, LifeOS |

**阶段适配:**
- S0-S2 (早期): 低置信度 (0.4), "当前聚焦行为改变基础, 身份探索自然浮现"
- S3+ (进阶): 触发身份工作
  - "身份"/"我是谁" → identity_chain 练习 (1次)
  - "未来"/"目标"/"梦想" → LifeOS design (7天)
  - "意义"/"使命" → narrative_rewrite (1次)

---

### 2.5 推送审批工作流

> **权威来源:** `core/coach_push_queue_service.py`

#### 推送队列条目创建

```
create_queue_item(
  coach_id, student_id,
  source_type: challenge | device_alert | micro_action | ai_recommendation | system,
  title, content, content_extra,
  suggested_time, priority: high | normal | low
) → CoachPushQueue (status=pending)
```

#### 生命周期

```
pending (创建) ─→ approved (教练批准) ─→ sent (已投递)
     │                                          ↑
     ├─→ rejected (教练退回)          deliver_item() 执行:
     │                                 1. 创建 CoachMessage / Reminder / MicroActionTask
     └─→ expired (72h 未处理)         2. push_router 写 notifications 表 + 外部推送
```

#### 优先级排序

```
high (order=0) > normal (order=1) > low (order=2)
同优先级内按 created_at DESC (最新优先)
```

#### 投递物差异化

| source_type | 投递动作 |
|-------------|---------|
| coach_reminder | 创建 Reminder (含 cron_expr/next_fire_at) |
| coach_message | 创建 CoachMessage (保留 message_type) |
| assessment_push | 更新 AssessmentAssignment.status='pushed' + CoachMessage |
| micro_action_assign | 创建 MicroActionTask + 通知 CoachMessage |
| 其他 | CoachMessage + 通用 Reminder |

---

### 2.6 推送推荐引擎 (六规则)

> **权威来源:** `core/push_recommendation_service.py`

| 步骤 | 规则 | 数据源 |
|------|------|--------|
| 1 | 查询教练名下学员 | coach_student_bindings |
| 2 | 采集 7 天设备信号 | glucose, heart_rate, sleep, activity |
| 3 | 分析行为事实 | BehaviorFactsService |
| 4 | 查询行为画像 | BehavioralProfile (stage, big5, capacity) |
| 5 | 计算距上次评估天数 | assessment_sessions |
| 6 | 检查待处理评估 | assessment_assignments |

**优先级排序:** high (0) > medium (1) > low (2)

---

### 2.7 方案管理与挑战生命周期

> **权威来源:** `core/challenge_service.py` + `core/program_service.py`

#### 挑战状态机

```
模板状态:
  DRAFT ─→ PENDING_REVIEW ─→ REVIEW_PARTIAL ─→ PUBLISHED
    ↑                                              │
    └──────────── REJECTED (任一审核员退回) ────────┘

报名状态:
  ENROLLED ─→ ACTIVE ─→ COMPLETED
```

**双专家审核规则:**
- 最低创建等级: L3 (coach)
- 最低审核等级: L4 (promoter/supervisor)
- 需两位专家均批准方可发布
- 任一退回则回到 DRAFT

#### 方案引擎 (ProgramEngine)

- 模板驱动: 含每日推送内容 + 微调查 + 行为指导
- 三时段推送: 09:00 (晨间) / 11:30 (午间) / 17:30 (傍晚)
- 每日推进: 00:05 自动推进 active 报名的 current_day
- 23:00 批量分析: 更新行为特征

---

### 2.8 定时任务体系 (20 Jobs)

> **权威来源:** `core/scheduler.py`, 全部使用 `@with_redis_lock` 分布式互斥

| 任务 | 触发时间 | 锁 TTL | 说明 |
|------|---------|--------|------|
| daily_task_generation | 06:00 每日 | 600s | 为活跃用户生成微行动 |
| reminder_check | 每 1 分钟 | 60s | 触发到期提醒 |
| expired_task_cleanup | 23:59 每日 | 300s | 标记过期任务 |
| process_approved_pushes | 每 5 分钟 | 300s | 投递已审批的定时推送 |
| expire_stale_queue_items | 06:30 每日 | 300s | 清理 72h+ 未审批条目 |
| knowledge_freshness_check | 07:00 每日 | 300s | 降级过期知识文档 |
| program_advance_day | 00:05 每日 | 600s | 推进方案日期 |
| program_push_morning | 09:00 每日 | 300s | 方案晨间推送 |
| program_push_noon | 11:30 每日 | 300s | 方案午间推送 |
| program_push_evening | 17:30 每日 | 300s | 方案傍晚推送 |
| program_batch_analysis | 23:00 每日 | 600s | 批量行为特征更新 |
| morning_notifications | 06:15 每日 | 300s | 晨间提醒 (P3) |
| midday_notifications | 08:00 每日 | 300s | 午间提醒 (P3) |
| evening_notifications | 22:00 每日 | 300s | 晚间提醒 (P3) |
| analytics_daily | 03:00 每日 | 600s | 每日分析聚合 (P5) |
| + 其他 V004/V005/V006/P6B 任务 | — | 300s | — |

**互斥锁机制:**
```
Redis SETNX "scheduler:{job_name}" → 成功则执行, TTL 后自动释放
Redis 不可用 → 优雅降级, 直接执行 (单实例场景无冲突)
```

---

## 三、行为处方生成规则

### 3.1 三维处方模型概述

> **权威来源:** `behavior_rx/core/behavior_rx_engine.py` (899行)

行为处方由三个维度交叉决定:

```
维度 1: TTM 阶段 (S0-S6) ─→ 策略选择 (12种策略)
维度 2: BigFive 人格 ──────→ 沟通风格 (6种风格)
维度 3: CAPACITY 分值 ────→ 强度校准 (5级强度) + 节奏 (3种)
```

**性能指标:** <200ms P99 延迟 (确定性引擎, 无 LLM 调用)

---

### 3.2 维度一: TTM 阶段→策略选择

#### 12 种行为改变策略

| 策略 | 中文 | 适用阶段 | 机制 |
|------|------|---------|------|
| consciousness_raising | 意识唤醒 | S0-S2 | 提升对问题的认知 |
| dramatic_relief | 戏剧性解脱 | S0-S1 | 情绪触动促进觉醒 |
| self_reevaluation | 自我再评价 | S1-S2 | 重新审视自我与行为 |
| decisional_balance | 决策平衡 | S1-S2 | 权衡改变的利弊 |
| cognitive_restructuring | 认知重构 | S2-S3 | 修正不良认知模式 |
| self_liberation | 自我解放 | S2 | 做出改变承诺 |
| stimulus_control | 刺激控制 | S3-S4 | 管理环境触发因素 |
| contingency_management | 强化管理 | S3-S5 | 奖惩系统 |
| habit_stacking | 习惯叠加 | S3-S4 | 将新行为附加到已有习惯 |
| systematic_desensitization | 系统脱敏 | 特殊 | 渐进式克服恐惧 |
| relapse_prevention | 复发预防 | S3-S6 | 防止行为倒退 |
| self_monitoring | 自我监控 | S2-S6 | 行为自我跟踪 |

#### 阶段→策略矩阵 (STAGE_STRATEGY_MATRIX)

| 阶段 | 主策略 (按优先级排列) |
|------|----------------------|
| S0 前意识 | 意识唤醒, 戏剧性解脱 |
| S1 意识 | 意识唤醒, 自我再评价, 戏剧性解脱, 决策平衡 |
| S2 准备 | 决策平衡, 自我解放, 自我再评价, 认知重构, 自我监控 |
| S3 行动 | 刺激控制, 强化管理, 习惯叠加, 自我监控, 认知重构, 复发预防 |
| S4 维持 | 复发预防, 强化管理, 刺激控制, 自我监控, 习惯叠加 |
| S5 巩固 | 自我监控, 复发预防, 强化管理 |
| S6 终止 | 自我监控, 复发预防 |

#### Agent 类型策略偏好加成

| Agent 类型 | 偏好策略 (+加成值) |
|-----------|-------------------|
| BEHAVIOR_COACH | 意识唤醒(+0.3), 认知重构(+0.25), 决策平衡(+0.2), 自我再评价(+0.2), 自我解放(+0.15) |
| METABOLIC_EXPERT | 刺激控制(+0.3), 自我监控(+0.25), 强化管理(+0.2), 习惯叠加(+0.2) |
| CARDIAC_EXPERT | 系统脱敏(+0.35), 刺激控制(+0.2), 自我监控(+0.2), 复发预防(+0.15) |
| ADHERENCE_EXPERT | 习惯叠加(+0.3), 刺激控制(+0.25), 强化管理(+0.2), 认知重构(+0.15) |

#### 障碍→策略映射

| 障碍类型 | 强化策略 |
|---------|---------|
| 恐惧 (fear) | 系统脱敏, 认知重构 |
| 遗忘 (forgetfulness) | 习惯叠加, 刺激控制 |
| 低动机 (low_motivation) | 戏剧性解脱, 决策平衡 |
| 认知障碍 (cognitive) | 意识唤醒, 认知重构 |
| 经济障碍 (economic) | 决策平衡 |
| 关系障碍 (relational) | 自我解放 |

---

### 3.3 维度二: BigFive 人格→沟通风格

#### 六种沟通风格

| 风格 | 中文 | 触发条件 | 特点 |
|------|------|---------|------|
| EMPATHETIC | 共情型 | N ≥ 65 (最高优先级) | 温暖接纳, 情绪优先 |
| DATA_DRIVEN | 数据驱动型 | C ≥ 65 | 结构化, 证据导向 |
| CHALLENGE | 挑战型 | E ≥ 65 | 鼓励突破, 正面激励 |
| SOCIAL_PROOF | 社会证明型 | A ≥ 65 | 同伴案例, 群体归属 |
| EXPLORATORY | 探索型 | O ≥ 65 | 好奇引导, 开放讨论 |
| NEUTRAL | 中立型 | 默认 | 平衡客观 |

**优先级规则:** N > C > E > A > O > 默认 (高神经质用户优先获得共情支持)

#### 人格对策略评分的影响

```
高 N (≥65): 系统脱敏 +0.15, 认知重构 +0.10
高 C (≥65): 自我监控 +0.15, 刺激控制 +0.10
高 E (≥65): 强化管理 +0.10, 习惯叠加 +0.10
高 A (≥65): 自我解放 +0.10
高 O (≥65): 意识唤醒 +0.10, 决策平衡 +0.10

低 N (<35): 挑战型策略 +0.05
低 C (<35): 习惯叠加 +0.10 (需更多外部结构)
```

#### 人格对奖励类型的适配

- 高 E + praise → 保持 "praise" (社交奖励有效)
- 高 C + praise → 切换为 "badge" (成就奖励更有效)

---

### 3.4 维度三: CAPACITY→强度校准

#### 强度矩阵 (INTENSITY_MATRIX)

| 阶段 \ 能力 | 低 (<0.33) | 中 (0.33-0.66) | 高 (>0.66) |
|-------------|-----------|----------------|-----------|
| S0 前意识 | 极低 | 极低 | 低 |
| S1 意识 | 极低 | 低 | 低 |
| S2 准备 | 低 | 中等 | 中等 |
| S3 行动 | 中等 | 中等 | 高 |
| S4 维持 | 中等 | 高 | 高 |
| S5 巩固 | 低 | 中等 | 中等 |
| S6 终止 | 极低 | 低 | 低 |

**五级强度:**
- minimal (极低): 最小干预, 信息提供
- low (低): 轻度引导
- moderate (中等): 标准干预
- high (高): 密集干预
- intensive (强化): 危机级干预

#### 节奏决定规则

```
规则 (按优先级):
1. S0-S1 或 capacity < 0.3 → slow (慢节奏)
2. 高N 且 stability < 0.4 → slow (安全优先)
3. S4+ 且 capacity > 0.7 且 stability > 0.6 → fast (快节奏)
4. 其他 → standard (标准节奏)
```

---

### 3.5 微行动生成规则

> **权威来源:** `behavior_rx_engine.py` `_generate_micro_actions()`

#### 难度校准公式

```
adjusted_difficulty = raw_difficulty

if capacity < 0.3:
    adjusted_difficulty *= 0.6    # 大幅降低
elif capacity < 0.5:
    adjusted_difficulty *= 0.8    # 适度降低
elif capacity > 0.7:
    adjusted_difficulty *= 1.1    # 略微提高

最终 clamp 到 [0.05, 0.9]
```

**设计原则:** 能力越低, 微行动越简单; 确保每个用户都能开始

#### 微行动结构

```
{
  action: "具体可执行的行为描述",
  difficulty: 0.0-1.0 (校准后),
  trigger: "何时/何地触发",
  duration_min: 执行时长 (分钟),
  frequency: "daily | weekly | on_trigger",
  domain: "nutrition | exercise | sleep | ..."
}
```

---

### 3.6 阻力阈值与升级规则

#### 阻力阈值计算

```python
base = 0.3

# 人格调整
高 N (≥65): base -= 0.08    # 更早切换策略 (情绪敏感)
高 C (≥65): base += 0.05    # 更有耐心坚持
低 C (<35): base -= 0.05    # 更早切换

# 能力调整
base += (capacity - 0.5) * 0.1

# 阶段调整
S0-S1: base -= 0.05    # 早期更敏感

最终 clamp 到 [0.15, 0.50]
```

**含义:** 阈值越低, 系统越早切换到下一个策略 (对脆弱用户更敏感)

#### 升级规则 (Escalation Rules)

| 规则 | 优先级 | 条件 | 动作 |
|------|--------|------|------|
| 阻力超阈 | 5 | 连续3次 resistance_score > threshold | 切换策略 |
| 阶段回退 | 8 | TTM 阶段下降 ≥2 级 | 移交 BEHAVIOR_COACH |
| 自我效能崩塌 | 10 | self_efficacy < 0.2 且 stability < 0.3 | 移交 BEHAVIOR_COACH |
| 代谢用药遗漏 | 7 | 7天内漏药 >3 次 (仅 METABOLIC) | 移交 ADHERENCE_EXPERT |
| 心脏运动恐惧 | 8 | exercise_fear > 0.8 + 回避行为 (仅 CARDIAC) | 切换策略 |
| 心率超限 | 10 | heart_rate > 安全上限 (仅 CARDIAC) | 通知教练 |
| 高N负面情绪 | 9 | negative_emotion > 0.85 连续2次 (高N用户) | 通知教练 |

---

### 3.7 处方有效性评估 (IES)

> **权威来源:** `behavior_rx_engine.py` `evaluate_effectiveness()`

#### IES 综合有效性分值 (0-1)

```
IES = 完成率 × 0.40           # 微行动完成度
    + min(天数/30, 1.0) × 0.20  # 持续时长
    + 阶段变化分 × 0.25         # 行为进步
    - 阻力惩罚 × 0.15          # 阻力扣分

阶段变化分 = max(0, min(stage_change+1, 3)) / 3
阻力惩罚 = min(resistance/10, 0.3)
```

#### IES 决策建议

| IES 分值 | 建议 | 含义 |
|----------|------|------|
| ≥ 0.7 | continue | 策略有效, 继续执行 |
| 0.4 - 0.7 | adjust | 需微调参数 (强度/节奏) |
| < 0.4 | switch_strategy | 策略无效, 切换到下一候选策略 |

---

### 3.8 混合路由: BehaviorRx→LLM 降级

> **权威来源:** `api/v14/copilot_routes.py` `generate-prescription`

```
POST /copilot/generate-prescription {"student_id": N}

路由逻辑:
1. 查询 BehavioralProfile (user_id = student_id)
2. 若 profile 存在且 current_stage 有值:
   a. profile_to_rx_context() 适配为 RxContext
   b. select_agent_type() 选择 ExpertAgentType
   c. BehaviorRxEngine.compute_rx() (<200ms)
   d. rx_dto_to_copilot_json() 映射为 6-key 格式
   e. 写入 behavior_prescriptions (status=draft)
   f. meta.source = "behavior_rx"
3. 若失败或无 profile:
   a. 降级到 CopilotPrescriptionService (LLM 路径)
   b. LLM timeout=20s, 失败则纯规则引擎
   c. meta.source = "llm" | "llm_merged" | "fallback"
```

**返回格式 (6-key, 兼容 admin-portal 5 标签页):**

```json
{
  "diagnosis": {评估诊断},
  "prescription": {处方方案},
  "ai_suggestions": [AI建议列表],
  "health_summary": {健康摘要},
  "intervention_plan": {干预计划},
  "meta": {来源/置信度/rx_id}
}
```

#### 处方 ID 格式与持久化规则

| 场景 | ID 格式 | 初始状态 | 来源 |
|------|---------|---------|------|
| copilot 生成 (教练工作台) | `rx_{uuid[:12]}` | draft | copilot_routes.py |
| 教练审批激活 | `rx_{uuid[:12]}` | active | r6_coach_flywheel_api_live.py |
| Observer→Grower 初始处方 | `rx_init_{uuid[:8]}` | active | r4_role_upgrade_trigger.py |

**持久化表:** `behavior_prescriptions`
**冲突策略:** `ON CONFLICT (id) DO NOTHING` (copilot/r4), 直接 INSERT (审批激活)
**失败处理:** copilot → db.rollback() + 继续返回结果 (non-blocking); r4 → fallback 到默认处方

---

### 3.9 Profile→RxContext 适配规则

> **权威来源:** `core/rx_context_adapter.py`

#### 域→Expert Agent 类型映射 (DOMAIN_AGENT_MAP)

| primary_domain | ExpertAgentType | 说明 |
|----------------|----------------|------|
| metabolic | METABOLIC_EXPERT | 代谢专家 |
| glucose | METABOLIC_EXPERT | 血糖管理 |
| nutrition | BEHAVIOR_COACH | 营养行为 |
| exercise | BEHAVIOR_COACH | 运动行为 |
| sleep | BEHAVIOR_COACH | 睡眠行为 |
| emotion | BEHAVIOR_COACH | 情绪管理 |
| cardiac | CARDIAC_EXPERT | 心脏康复 |
| cardiac_rehab | CARDIAC_EXPERT | 心脏康复 |
| (无匹配/无域) | BEHAVIOR_COACH | 默认 |

**选择逻辑:** 遍历 `BehavioralProfile.primary_domains` 列表, 第一个命中 DOMAIN_AGENT_MAP 的域决定 Agent 类型。

#### ORM→DTO 字段转换规则

| ORM 字段 | 转换规则 | DTO 字段 | 降级默认值 |
|---------|---------|---------|-----------|
| current_stage (enum) | _STAGE_INT_MAP: S0=0..S6=6 | ttm_stage | 0 (S0) |
| stage_stability (enum) | STABLE=0.9, SEMI_STABLE=0.5, UNSTABLE=0.2 | stage_stability | 0.5 |
| big5_scores (JSON) | 读取 O/C/E/A/N 各项 | personality | 各项默认50 |
| capacity_total (0-100) | ÷100, clamp [0,1] | capacity_score | 0.5 |
| spi_score (0-100) | ÷100, clamp [0,1] | self_efficacy | 0.5 |
| stage_confidence | 直接使用 | stage_readiness | 0.5 |
| domain_details (JSON) | 直接使用 | domain_data | {} |
| user_id (int) | uuid5(NAMESPACE_DNS, "bhp-user-{id}") | user_id (UUID) | — |
| (无历史数据) | — | recent_adherence | 0.5 |

#### Barrier 映射规则 (CAPACITY 弱项→障碍类型)

从 `capacity_weak` 列表中提取障碍关键词:

| 弱项关键词 | 障碍类型 | 含义 |
|-----------|---------|------|
| 动机 / M_ | low_motivation | 低动机 |
| 时间 / T_ | forgetfulness | 遗忘/无暇 |
| 信心 / C_ | fear | 恐惧/信心不足 |
| 资源 / A2_ | economic | 经济/资源障碍 |
| 认知 | cognitive | 认知障碍 |

#### 风险标记规则

| risk_flags 含值 | risk_level |
|----------------|-----------|
| dropout_risk 或 relapse_risk | elevated |
| (无匹配) | normal |

---

### 3.10 沟通风格→干预语调映射

> **权威来源:** `core/rx_response_mapper.py` `_comm_to_tone()`

| 沟通风格 | 干预语调 | 描述 |
|---------|---------|------|
| empathetic (共情型) | gentle_accepting | 温和接纳 |
| data_driven (数据驱动型) | structured_analytical | 结构化分析 |
| challenge (挑战型) | encouraging_practical | 鼓励务实 |
| social_proof (社会证明型) | encouraging_practical | 鼓励务实 |
| exploratory (探索型) | gentle_accepting | 温和接纳 |
| neutral (中立型) | gentle_accepting | 温和接纳 |

**强度→难度数值映射:**
minimal=1, low=2, moderate=3, high=4, intensive=5

---

### 3.11 Observer→Grower 初始处方生成规则

> **权威来源:** `api/r4_role_upgrade_trigger.py` `_generate_initial_prescription()`

```
L0→L1 升级完成后:
1. 读取 BPT-6 分型 (assessment_sessions.module_type='bpt6')
2. 读取 SPI 心理层级 (assessment_sessions.module_type='spi')
3. 根据 L 层级决定最大处方数: L1=1, L2=1, L3=2, L4=3, L5=5
4. 尝试 BehaviorRx 引擎:
   a. 查询 BehavioralProfile
   b. profile_to_rx_context() → select_agent_type()
   c. engine.compute_rx() → 写入 behavior_prescriptions (status='active')
   d. rx_id 格式: "rx_init_{uuid[:8]}"
5. BehaviorRx 失败 → 降级到默认处方集:
   a. 营养: 记录三餐饮食
   b. 运动: 每日散步15分钟
   c. 监测: 血糖监测 (如适用)
```

---

### 3.12 处方查询与权限规则

> **权威来源:** `api/main.py` rx 端点

#### GET /api/v1/rx/my — 用户处方列表

| 参数 | 默认值 | 说明 |
|------|--------|------|
| status | "active" | 过滤状态 (active/draft/completed/paused/cancelled) |
| limit | 20 | 最大返回数 |

**权限:** 仅返回 `current_user.id` 的处方。

#### GET /api/v1/rx/{rx_id} — 处方详情

**权限检查:**

```
1. user_id == current_user.id → 允许 (自己的处方)
2. current_user.role ∈ {COACH, PROMOTER, SUPERVISOR, MASTER, ADMIN} → 允许
3. 否则 → 403 无权限
```

#### GET /api/v1/notifications/system — 系统通知聚合

聚合三个数据源:
1. `credit_events` 表: 积分变动通知
2. `user_milestones` 表: 里程碑达成通知
3. `notifications` 表: 推送通知 (含处方审批通知)

**深度链接解析:** 从 body 中提取 `[link:xxx]` 格式, 转为 `link` 字段供 H5 导航。

---

## 四、积分与激励规则

### 4.1 三维积分体系

> **权威来源:** `configs/point_events.json`

#### 成长积分事件 (Growth Points)

| 事件 | 积分 | 每日上限 | 最低角色 | 说明 |
|------|------|---------|---------|------|
| daily_checkin | +5 | 1次/日 | observer | 每日签到 |
| complete_lesson | +20 | 5次/日 | observer | 完成课程, 联动学分 |
| complete_assessment | +50 | 2次/日 | observer | 完成评估, 联动学分 |
| behavior_attempt | +10 | 3次/日 | observer | 行为尝试 |
| stage_transition | +30 | 无限 | grower | 阶段跃迁 |
| behavior_stable_30d | +50 | 里程碑 | grower | 30天稳定 |
| behavior_stable_90d | +100 | 里程碑 | grower | 90天稳定 |
| metric_improved | +20 | 无限 | grower | 指标改善 |
| complete_case | +50 | 无限 | coach | 完成案例 |
| complete_180day | +500 | 里程碑 | grower | 完成180天课程 |
| use_tool | +10 | 3次/日 | observer | 使用工具 |
| training_hour | +5/h | 8h/日 | sharer | 培训学时 |

#### 贡献积分事件 (Contribution Points)

| 事件 | 积分 | 每日上限 | 最低角色 |
|------|------|---------|---------|
| path_contribute | +10 | 3次/日 | grower |
| data_archive | +5 | 5次/日 | grower |
| publish_content | +30 | 3次/日 | sharer |
| case_share | +30 | 2次/日 | coach |
| template_contribute | +50 | 无限 | coach |
| course_develop | +100 | 无限 | promoter |
| rule_contribute | +30 | 无限 | coach |
| mentee_graduated | +30 | 无限 | grower |
| community_reply | +10 | 10次/日 | sharer |

#### 影响力积分事件 (Influence Points)

| 事件 | 积分 | 最低角色 |
|------|------|---------|
| invite_observer | +10 | observer |
| companion_train_l0 | +10 | grower |
| companion_train_l1 | +30 | sharer |
| companion_train_l2 | +50 | coach |
| companion_train_l3 | +80 | promoter |
| companion_train_l4 | +150 | master |
| content_spread | +5 (5次/日) | sharer |
| host_workshop | +150 | coach |
| industry_event | +50 | promoter |
| standard_participate | +100 | master |

#### V4.0 治理积分事件

| 事件 | 积分 | 类型 | 最低角色 |
|------|------|------|---------|
| ethics_test_complete | +50 | 成长 | sharer |
| self_assessment_complete | +30 | 成长 | observer |
| credential_renewal | +20 | 成长 | coach |
| ethics_pledge_sign | +30 | 贡献 | sharer |
| conflict_disclosure_update | +20 | 贡献 | promoter |
| alert_handled_timely | +15 | 贡献 | coach |
| message_reply_timely | +10 | 贡献 | coach |
| agent_feedback_reply | +10 | 贡献 | coach |
| supervision_meeting | +50 | 影响力 | promoter |
| knowledge_contribute | +30 | 影响力 | coach |

#### 学习内容积分配置

| 内容类型 | 基础积分 | 附加规则 |
|---------|---------|---------|
| video | 10 | +1/分钟, 测验+5 |
| course | 50 | +10/章节, 完成+20 |
| article | 5 | +2/千字 |
| card | 3 | 完成+2 |
| audio | 8 | +0.5/分钟 |

#### 测验积分配置

```
通过基础: 10分
满分额外: 5分
每答对一题: 2分
首次通过额外: 3分
```

---

### 4.2 里程碑与仪式

> **权威来源:** `configs/milestones.json`

| 里程碑 | 触发 | 学分 | 积分奖励 | 徽章 | 解锁功能 | 仪式 |
|--------|------|------|---------|------|---------|------|
| FIRST_LOGIN | 注册 | 15 | 成长+15 | 🌱 first_step | 微评估入口, 观察者七步 | 种子萌芽 (3s) |
| DAY_3 | 连续3天 | 25 | 成长+25, 连续+5 | 🔥 3day_flame | 行为链卡片, 社区浏览 | 种子到芽 (2.5s) |
| DAY_7 | 连续7天 | 40 | 成长+30, 连续+10 | ⭐ week_star | 微行为挑战, 同道者邀请 | 根系延伸 (3s) |
| DAY_14 | 连续14天 | 50 | 成长+35, 贡献+15 | 🌸 half_month | 行为链意识, CGM基线, 成长档案 | 花开绽放 (4s, 可选花型) |
| DAY_21 | 连续21天 | 60 | 成长+40, 贡献+20 | 🍎 21day_gold | 社区发帖, 内容分享, 进阶选修 | 果实生长 (4s) |
| DAY_30 | 连续30天 | 80 | 成长+50+50, 贡献+30, 影响力+10 | 🦋 30day_diamond + butterfly | L0→L1 晋级通道 | 蝶变重生 (8s, 回顾旅程) |

**Day 3 翻牌奖励池:**
- 额外学分 +10 (权重 40%)
- 嫩芽壁纸 (权重 35%)
- 稀有行为卡 (权重 25%)

---

### 4.3 徽章系统

> **权威来源:** `configs/badges.json`

#### 稀有度体系

| 稀有度 | 颜色 | 视觉效果 |
|--------|------|---------|
| common | 灰色 | 基础渐变 |
| uncommon | 绿色 #10B981 | — |
| rare | 蓝色 #3B82F6 | — |
| epic | 紫色 #8B5CF6 | — |
| legendary | 金色 #F59E0B | 光芒闪烁 |

#### 四大徽章类别

**1. 里程碑徽章 (7枚):** FIRST_LOGIN → DAY_30 (参见里程碑表)

**2. 学习时长徽章 (6枚):**

| 时长 | 徽章 | 稀有度 |
|------|------|--------|
| 1 小时 | 📖 bronze | common |
| 10 小时 | 📚 silver | uncommon |
| 20 小时 | ⚖️ gold | rare |
| 40 小时 | 🏅 gold | rare |
| 80 小时 | 🎓 epic | epic |
| 120 小时 | 💎 legend | legendary |

**3. 模块精通徽章 (M1-M4 × 4 阶):**

| 模块 | T1 觉察者 | T2 实践者 | T3 设计师 | T4 大师 |
|------|----------|----------|----------|--------|
| M1 行为 | 行为觉察者 | 行为解构者 | 行为设计师 | 链环之主 |
| M2 生活方式 | 节律体验者 | 节律实践者 | 节律设计师 | 五维大师 |
| M3 心智 | 思维觉察者 | 思维重构者 | 思维建筑师 | 心智之光 |
| M4 教练 | 陪伴体验者 | 陪伴技术者 | 陪伴引领者 | 同行之灯 |

**组合徽章:** 四维觉醒 (全T1) + 四维大师 (全T4, legendary)

**4. 晋级仪式徽章 (5枚):**

| 晋级 | 仪式 | 纪念品 | 解锁 |
|------|------|--------|------|
| L0→L1 | 🐣 破壳礼 | 成长树艺术 | 同道者邀请, 社区互动, 进阶课程, 数据分析 |
| L1→L2 | 🕯️ 传灯礼 | 数字灯笼 | 内容发布, 经验分享, 专属模板, 陪伴技术 |
| L2→L3 | 🪄 授杖礼 | 教练画像 | 1v1教练, 处方设计, 案例库, AI Co-Pilot |
| L3→L4 | 🏛️ 立柱礼 | 学员族谱 | 课程开发, 师资培训, 督导权限 |
| L4→L5 | 🌊 归源礼 | 贡献热力图 | 理论创新, 标准制定, 学术发表 |

---

### 4.4 连续打卡与中断恢复

#### 连续打卡里程碑

| 天数 | 奖励名 | 积分 |
|------|--------|------|
| 3天 | 三日坚持 🔥 | +5 |
| 7天 | 一周达成 💪 | +15 |
| 14天 | 两周突破 ⭐ | +30 |
| 21天 | 习惯养成 🎯 | +50 |
| 30天 | 月度冠军 🥇 | +100 |
| 100天 | 百日传奇 🏅 | +500 |

#### 中断恢复机制

| 恢复方式 | 条件 | 说明 |
|---------|------|------|
| 宽限期 | 中断 ≤36 小时 | 自动恢复 |
| 免费恢复 | 1次/月 | 每月一次免费 |
| 学分恢复 | 消耗 10 学分 | 用学分换连续 |
| 同道者救援 | 需 companion_relation | 同道者帮助恢复 |

---

### 4.5 晋级资格四维度检查

> **权威来源:** `core/promotion_service.py`

```
晋级资格 = 学分维度 AND 积分维度 AND 同道者维度 AND 实践维度

1. 学分维度: total_min, mandatory_min, elective_min, m1-m4_min
   来源: v_user_total_credits 视图

2. 积分维度: growth_min, contribution_min, influence_min
   来源: v_promotion_progress 视图

3. 同道者维度: graduated_min (毕业学员数), quality_min (平均质量分)
   来源: v_companion_stats 视图

4. 实践维度: passed=None (需人工审核)
   来源: 规则配置中的实践标准
```

**结果结构:**
```json
{
  "eligible": true/false/null,
  "credits": {"passed": bool},
  "points": {"passed": bool},
  "companions": {"passed": bool},
  "practice": {"passed": null, "requires_manual_review": true},
  "auto_checks_passed": bool
}
```

---

## 五、安全管道规则

### 5.1 四层安全管线 (SafetyPipeline)

> **权威来源:** `core/safety/` 目录

```
用户输入 → [L1 输入过滤] → [L2 RAG安全] → [L3 生成守卫] → [L4 输出过滤] → 安全输出
```

| 层级 | 位置 | 功能 |
|------|------|------|
| L1 input_filter | MasterAgent Step 2.5 | 过滤恶意输入, 检测 prompt injection |
| L2 rag_safety | RAG 检索后 | 验证检索文档的安全性和相关性 |
| L3 generation_guard | MasterAgent Step 7.5 | LLM 生成过程中的安全约束 |
| L4 output_filter | MasterAgent Step 8.5 | 最终输出检查, 移除不安全内容 |

---

### 5.2 中医骨伤安全门 (OrthoSafetyGate L1-L4)

> **权威来源:** `core/safety/safety_rules_ortho.py`

#### L1 红旗急症 (59 模式, 立即拨打 120)

覆盖: 严重头痛伴神经症状, 意识丧失/癫痫, 胸痛伴心脏症状, 疑似中风, 严重创伤骨折, 脊髓损伤, 马尾综合征, 严重出血

#### L2 高危转诊 (9 模式, 紧急医疗转诊)

覆盖: VAS/NRS 8-10分持续, 夜痛>2周, 不明原因体重下降, 发热伴关节痛, 进行性加重, 放射性神经症状, 创伤后持续恶化, 长期 NSAID, 急性关节炎/痛风, 严重骨质疏松 (T<-2.5)

#### L3 执业边界 (6 模式)

禁止: 开处方, 下诊断, 手术咨询, 侵入性操作, 阿片类药物, 影像学检查建议

#### L4 特殊人群禁忌 (5 类)

| 人群 | 禁忌 |
|------|------|
| 孕妇 | 合谷, 三阴交, 昆仑, 肩井穴位禁用 |
| 儿童 | 禁成人力度手法, 禁正骨 |
| 严重骨质疏松 | 禁脊柱手法, 禁重力度 |
| 肿瘤 | 禁局部推拿, 禁患处热敷 |
| 凝血障碍 | 禁拔罐, 禁深刺 |

---

### 5.3 策略引擎五步管线 (PolicyEngine)

> **权威来源:** `api/policy_api.py`

```
Step 1: Rules — 加载条件表达式 (JSON-Logic)
Step 2: Candidates — 按优先级过滤匹配规则
Step 3: Conflict — 解决规则冲突
Step 4: Cost — 评估执行成本
Step 5: Trace — 记录决策轨迹
```

**规则类型:**

| 类型 | 范围 | 说明 |
|------|------|------|
| platform | 全局 | 系统级规则 |
| tenant | 租户级 | 租户自定义 |
| emergency | 全局 | 危机规则 (最高优先) |
| dynamic | 运行时 | 动态生成规则 |

**规则属性:**
- priority: 0-100 (数值越大越先执行)
- condition_expr: JSON-Logic 条件
- action_type: select_agent / block / adjust_weight / downgrade_model
- evidence_tier: T1-T5 证据分级

---

## 六、设备预警规则

> **权威来源:** `configs/alert_thresholds.json`

### 血糖预警

| 级别 | 条件 | 阈值 |
|------|------|------|
| 危险高 | ≥13.9 mmol/L | 立即预警 |
| 警告高 | ≥10.0 mmol/L | 警告预警 |
| 危险低 | ≤3.0 mmol/L | 立即预警 |
| 警告低 | ≤3.9 mmol/L | 警告预警 |

### 心率预警 (静息)

| 级别 | 条件 | 阈值 |
|------|------|------|
| 危险高 | ≥150 bpm | 仅静息时 |
| 警告高 | ≥120 bpm | 仅静息时 |
| 危险低 | ≤40 bpm | — |
| 警告低 | ≤50 bpm | — |

### 运动/睡眠/久坐

| 指标 | 阈值 | 说明 |
|------|------|------|
| 过量运动 | >180 分钟/日 | — |
| 久坐 | >600 分钟/日 | — |
| 睡眠质量 | <50 分 | — |
| 睡眠不足 | <300 分钟 | — |

**去重规则:** 同一数据类型 + 同一用户, 相同级别的预警在配置时间窗口内仅触发一次。

---

## 七、治理与同道者规则 (V4.0)

> **权威来源:** `api/governance_api.py` + `core/peer_tracking_service.py`

### Agency 三态模型

| 模式 | 代码 | 说明 |
|------|------|------|
| 被动 | passive | 教练主导, 用户接受 |
| 过渡 | transitional | 教练引导, 用户参与 |
| 主动 | active | 用户自主, 教练监督 |

**DB 存储:** `users.agency_mode` 为 PostgreSQL enum 类型, 非 String

### 同道者匹配策略

| 维度 | 权重 | 说明 |
|------|------|------|
| 阶段接近度 | 0.30 | 优先匹配阶段相近者 |
| 行为相似度 | 0.25 | BPT-6 分型相似 |
| 目标对齐度 | 0.25 | 目标重叠度 |
| 互补性 | 0.20 | 互补配对 |

### 同道者关系生命周期

```
PENDING → ACTIVE → COOLING (7天无互动)
                      ↓
                   DORMANT (14天无互动)
                      ↓
                   DISSOLVED (30天或手动)
```

**自动解散规则:**
- DORMANT 状态持续 30 天 → 自动解散
- 冷却阈值: 7 天无互动
- 休眠阈值: 14 天无互动

### 双轨晋级制度

- 4 种晋级状态: max_level (已达上限), pending_check (待审), ineligible (不满足), eligible (满足)
- 要求维度: 能力要求 + 考试 + 行为要求 + 伦理要求
- 最短在位期限执行
- 同道者要求追踪 (total_required, graduated_required)

### 反作弊规则 (12 MEUs)

Stage Authority (C3 审计修复): 阶段晋级需要治理引擎授权, 防止跳级。Field Sync Guard (C4 审计修复): ORM 与 DB 字段同步守卫, 防止数据漂移。

---

## 附录: 权威来源文件索引

| 文件 | 行数 | 规则内容 |
|------|------|---------|
| `api/paths_api.py` | ~200 | 六级门槛, 等级计算 |
| `api/learning_api.py` | ~700 | 等级要求, 学时/测验/连续积分 |
| `core/learning_service.py` | ~400 | 角色晋级5规则, 同道者计数 |
| `core/user_segments.py` | ~550 | 4来源×4层级, 6画像 |
| `core/promotion_service.py` | ~210 | 4维晋级检查 |
| `core/challenge_service.py` | ~590 | 挑战生命周期, 双审核 |
| `core/coach_push_queue_service.py` | ~515 | 推送审批工作流 |
| `core/push_recommendation_service.py` | ~100 | 6规则推荐引擎 |
| `core/scheduler.py` | ~300 | 20定时任务 |
| `core/master_agent_v0.py` | ~400 | 9步管线 |
| `core/agents/router.py` | ~120 | 6优先级路由 |
| `core/agents/v4_agents.py` | ~390 | 4个V4 Agent |
| `behavior_rx/core/behavior_rx_engine.py` | ~900 | 三维处方引擎全部规则 |
| `behavior_rx/core/rx_schemas.py` | ~300 | DTO定义, 枚举 |
| `core/safety/safety_rules_ortho.py` | ~140 | L1-L4安全门 |
| `core/copilot_prescription_service.py` | ~840 | LLM+规则引擎处方 |
| `api/assessment_pipeline_api.py` | ~300 | BAPS评估管线 |
| `api/r4_role_upgrade_trigger.py` | ~570 | Observer→Grower升级 |
| `api/governance_api.py` | ~400 | V4.0治理26端点 |
| `core/peer_tracking_service.py` | ~300 | 同道者匹配与生命周期 |
| `api/policy_api.py` | ~200 | 策略引擎12端点 |
| `configs/point_events.json` | ~430 | 30+积分事件定义 |
| `configs/milestones.json` | ~300 | 7里程碑+翻牌+恢复 |
| `configs/badges.json` | ~130 | 20+徽章+稀有度 |
| `core/rx_context_adapter.py` | ~126 | Profile→RxContext适配, 域→Agent映射, Barrier映射 |
| `core/rx_response_mapper.py` | ~213 | DTO→Copilot JSON映射, 沟通风格→语调, 处方显示映射 |
| `api/r6_coach_flywheel_api_live.py` | ~456 | 教练审批5步闭环, 处方激活, 通知推送 |
| `gateway/channels/push_router.py` | ~129 | 通知路由级联规则, 渠道选择 |
| `api/main.py` (rx端点) | ~94 | 处方查询权限, 通知聚合+深度链接解析 |

---

*本文档版本 V5.2.6 (P1闭环补充), 与代码库同步。所有规则数据均从生产代码中直接提取。*

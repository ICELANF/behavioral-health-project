# Core Data Schema v1.0 · 最终工程规范版

> **行健行为教练多Agent系统 · 核心数据契约**
>
> 版本: 1.0.0 | 更新日期: 2026-01-24

---

## 第 0 章 | 系统设计原则

| 原则 | 说明 |
|------|------|
| **数据驱动** | 数据结构先行，所有模块围绕六大核心结构体展开 |
| **可追踪** | 状态可追踪、路径可回放、评估可量化 |
| **模块化** | Agent模块化、Skills可插拔、调度可演化 |
| **长期陪伴** | 支持长期陪伴型行为改变与科研级数据沉淀 |
| **唯一权威** | UserMasterProfile为系统唯一权威用户状态对象 |

---

## 第 1 章 | 六大核心结构体总览

### 1.1 结构体总表

| 编号 | 结构体名称 | 英文标识 | 核心职责 | 状态 |
|------|------------|----------|----------|------|
| 1 | 用户画像与状态 | UserMasterProfile | 承载用户基础信息 + 行为阶段状态 | 已定义 |
| 2 | 行为状态模型 | BehaviorState | 描述当前行为模式、风险与阻抗 | **本文档补齐** |
| 3 | 目标与任务模型 | Goal / Task | 描述干预目标、阶段任务与行动计划 | **本文档补齐** |
| 4 | Agent身份模型 | AgentProfile | 描述各Agent角色、能力与权限 | **本文档补齐** |
| 5 | 技能描述模型 | SkillDescriptor | 描述Skills定义、输入输出与调用条件 | **本文档补齐** |
| 6 | 会话与轨迹模型 | Session / Trajectory | 描述陪伴过程、决策路径与评估轨迹 | **本文档补齐** |

### 1.2 对象关系图 (文字版)

```
┌─────────────────────────────────────────────────────────────────┐
│                     UserMasterProfile                           │
│                    (系统唯一权威用户状态)                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    BehaviorState                        │   │
│  │  · 行为阶段 · 心理准备度 · 行为模式 · SPI · 障碍 · 风险   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│    Goal     │◄────►│    Task     │◄────►│   Session   │
│  (干预目标)  │      │  (执行任务)  │      │  (交互会话)  │
└─────────────┘      └─────────────┘      └─────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
                    ┌─────────────────┐
                    │   Trajectory    │
                    │  (长期轨迹追踪)  │
                    └─────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      执行能力池                                   │
│  ┌─────────────────┐      ┌─────────────────┐                  │
│  │  AgentProfile   │─────►│ SkillDescriptor │                  │
│  │  (Agent身份)    │ owns │  (可插拔技能)    │                  │
│  └─────────────────┘      └─────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 第 2 章 | 核心结构体定义规范

---

### 2.1 结构体一：UserMasterProfile (已定义)

> 参见 `user_profile_schema.json` + `core_data_schema.json`

---

### 2.2 结构体二：BehaviorState (行为状态模型)

#### 职责说明
描述用户当前行为模式、风险因素、改变阻力与阶段状态。是评估引擎和干预规划的核心输入。

#### 生命周期

| 阶段 | 说明 |
|------|------|
| 创建 | 首次评估时由 AssessmentEngine 创建 |
| 更新 | 每次交互/评估/设备数据同步时更新 |
| 持久化 | 作为 UserMasterProfile.behavior_state 子对象持久化 |
| 保留 | 永久保留，支持历史版本追溯 |

#### 读写权限

| 权限 | 主体 |
|------|------|
| **读取** | MasterOrchestrator, AllAgents, AssessmentEngine, ReportGenerator |
| **写入** | MasterOrchestrator (唯一) |
| **写入渠道** | AgentResult.data_updates, AssessmentResult.behavior_updates |

#### 与UserState关系
BehaviorState 是 UserMasterProfile 的核心子域，通过 `user_id` 关联。

#### 技能映射

| 类型 | 技能 |
|------|------|
| 分析技能 | behavior_pattern_recognition, stage_detection, risk_assessment |
| 干预技能 | motivation_enhancement, barrier_resolution, habit_formation |

#### 核心字段 (TypeScript风格)

```typescript
interface BehaviorState {
  behavior_state_id: string;          // 格式: BS-XXXXXXXX
  user_id: string;
  schema_version: "1.0";

  // 当前行为改变阶段 (TTM)
  current_stage: {
    ttm_stage: "precontemplation" | "contemplation" | "preparation" | "action" | "maintenance";
    stage_cn: string;
    detected_at: DateTime;
    detection_method: "questionnaire" | "behavior_analysis" | "conversation_inference" | "device_data";
    confidence: number;  // 0-1
    weeks_in_stage: number;
  };

  // 五层次心理准备度 (自研模型)
  psychological_readiness_level: {
    level: 1 | 2 | 3 | 4 | 5;
    level_id: "total_resistance" | "resistance_reflection" | "selective_acceptance" | "adaptive_alignment" | "full_internalization";
    level_name: "完全对抗" | "抗拒与反思" | "妥协与接受" | "顺应与调整" | "全面臣服";
    core_psychology: string;
    spi_coefficient: number;  // 0.3-1.0
    intervention_strategy: string;
    max_tasks_allowed: number;  // 1-5
    max_difficulty_allowed: number;  // 1-5
  };

  // 四阶段养成进度
  cultivation_phase: {
    phase_id: "startup" | "adaptation" | "stabilization" | "internalization";
    phase_name: "启动期" | "适应期" | "稳定期" | "内化期";
    start_date: Date;
    expected_end_date: Date;
    coaching_frequency: "daily" | "weekly" | "monthly" | "on_demand";
    progress_percent: number;
  };

  // 行为模式识别
  behavior_patterns: {
    primary_pattern: string;
    secondary_patterns: string[];
    pattern_confidence: number;
    typical_behaviors: string[];
    recommended_experts: string[];
  };

  // 动机状态
  motivation_state: {
    motivation_score: number;  // 0-100
    motivation_level: "optimal" | "mismatched_active" | "mismatched_passive" | "depleted";
    energy_mood_match: {
      energy_level: number;
      mood_level: number;
      match_score: number;
    };
    trigger_factors: {
      intrinsic_drivers: number;     // max 20
      external_events: number;       // max 20
      emotional_triggers: number;    // max 20
      cognitive_shifts: number;      // max 20
      capability_resources: number;  // max 20
      social_support: number;        // max 25
    };
    total_trigger_score: number;     // max 125
  };

  // SPI成功可能性指数
  spi: {
    score: number;  // 0-100
    level: "very_low" | "low" | "medium" | "high";
    interpretation: string;
    recommendation: string;
    calculated_at: DateTime;
    formula_components: {
      trigger_score: number;
      level_coefficient: number;
      urgency_score: number;
    };
  };

  // 障碍识别
  barriers: Array<{
    barrier_id: string;
    category: "knowledge" | "skill" | "motivation" | "environment" | "time" | "social" | "physical" | "emotional";
    description: string;
    severity: "minor" | "moderate" | "major";
    resolution_strategy: string;
    status: "identified" | "addressing" | "resolved";
  }>;

  // 风险标记
  risk_flags: Array<{
    flag_id: string;
    risk_type: "metabolic" | "cardiovascular" | "mental" | "sleep" | "crisis";
    risk_level: "low" | "moderate" | "high" | "critical";
    description: string;
    triggered_at: DateTime;
    source: string;
    requires_escalation: boolean;
  }>;

  // 依从性指标
  adherence_metrics: {
    overall_adherence_rate: number;
    task_completion_rate_7d: number;
    task_completion_rate_30d: number;
    streak_days: number;
    longest_streak: number;
    dropout_risk: "low" | "moderate" | "high";
  };

  last_updated: DateTime;
  version_history: Array<{version: number; updated_at: DateTime; update_source: string; changes_summary: string}>;
  extensions: object;
}
```

---

### 2.3 结构体三A：Goal (目标模型)

#### 职责说明
描述用户的中长期健康干预目标，指导任务生成与评估。

#### 生命周期

| 阶段 | 说明 |
|------|------|
| 创建 | 初次评估后由 InterventionPlanner 创建 |
| 更新 | 每次阶段评估时更新进度与状态 |
| 持久化 | 独立存储，通过 goal_id 与 UserMasterProfile 关联 |
| 保留 | 目标完成后归档，保留至少2年 |

#### 读写权限

| 权限 | 主体 |
|------|------|
| **读取** | MasterOrchestrator, AllAgents, InterventionPlanner, DashboardGenerator |
| **写入** | MasterOrchestrator, InterventionPlanner |

#### 核心字段 (TypeScript风格)

```typescript
interface Goal {
  goal_id: string;                    // 格式: G-XXXXXXXX
  user_id: string;
  schema_version: "1.0";

  goal_type: "health_outcome" | "behavior_change" | "skill_acquisition" | "habit_formation" | "risk_reduction";
  domain: "glucose" | "sleep" | "exercise" | "nutrition" | "stress" | "weight" | "cardiovascular" | "mental_health" | "comprehensive";

  target_description: string;         // SMART格式描述
  target_metrics: Array<{
    metric_name: string;
    baseline_value: number;
    target_value: number;
    unit: string;
    direction: "increase" | "decrease" | "maintain";
    deadline: Date;
  }>;

  priority: 1 | 2 | 3 | 4 | 5;        // 1最高
  source: "user_stated" | "clinician_recommended" | "system_derived" | "assessment_based";

  milestones: Array<{
    milestone_id: string;
    description: string;
    target_date: Date;
    success_criteria: string;
    status: "pending" | "in_progress" | "completed" | "missed";
    completed_at?: DateTime;
  }>;

  related_tasks: string[];            // Task ID列表
  related_intervention_plan_id: string;

  progress: {
    percent_complete: number;
    current_value: number;
    trend: "improving" | "stable" | "declining";
    last_measured_at: DateTime;
  };

  status: "draft" | "active" | "paused" | "completed" | "abandoned" | "archived";
  status_reason?: string;

  created_at: DateTime;
  target_completion_date: Date;
  actual_completion_date?: DateTime;
  last_updated: DateTime;

  extensions: object;
}
```

---

### 2.4 结构体三B：Task (任务模型)

#### 职责说明
描述具体的行为任务，是系统产生行为改变的**最小执行单元**。

#### 生命周期

| 阶段 | 说明 |
|------|------|
| 创建 | 由 TaskGenerator 基于 Goal 和 BehaviorState 生成 |
| 更新 | 用户完成/跳过时更新状态 |
| 持久化 | 独立存储，通过 task_id 与 Goal/Session 关联 |
| 保留 | 完成后保留用于轨迹分析，至少保留1年 |

#### 读写权限

| 权限 | 主体 |
|------|------|
| **读取** | MasterOrchestrator, AllAgents, TaskGenerator, UserApp |
| **写入** | MasterOrchestrator, TaskGenerator, UserFeedback |

#### 核心字段 (TypeScript风格)

```typescript
interface Task {
  task_id: string;                    // 格式: T-XXXXXXXX
  user_id: string;
  schema_version: "1.0";

  related_goal_id?: string;
  related_plan_id?: string;
  session_id?: string;

  task_type: "micro_habit" | "reflection" | "training" | "measurement" | "education" | "check_in" | "exercise" | "nutrition" | "relaxation" | "social" | "medical";
  domain: "glucose" | "sleep" | "exercise" | "nutrition" | "stress" | "emotion" | "comprehensive";

  description: string;
  instruction: string;                // 详细执行指导

  difficulty: 1 | 2 | 3 | 4 | 5;      // 1最易
  estimated_duration_minutes: number;
  priority: 1 | 2 | 3 | 4 | 5;

  scheduling: {
    scheduled_date: Date;
    scheduled_time: string;           // HH:MM格式
    frequency: "once" | "daily" | "weekly" | "custom";
    reminder_enabled: boolean;
    reminder_minutes_before: number;
  };

  success_criteria: {
    completion_type: "binary" | "quantitative" | "qualitative";
    target_value?: number;
    unit?: string;
    verification_method: "self_report" | "device_data" | "photo" | "timer";
  };

  resources: {
    knowledge_link?: string;
    video_link?: string;
    audio_link?: string;
    product_id?: string;
    external_tool?: string;
  };

  coach_guidance: {
    pre_task_message: string;
    encouragement: string;
    completion_celebration: string;
    skip_support: string;
  };

  status: "pending" | "in_progress" | "completed" | "skipped" | "failed" | "rescheduled";
  completion?: {
    completed_at: DateTime;
    actual_value?: number;
    self_rating: 1 | 2 | 3 | 4 | 5;
    effort_rating: 1 | 2 | 3 | 4 | 5;
    user_notes?: string;
  };
  skip_reason?: string;

  tracking_points: string[];          // 需要追踪的数据点

  created_at: DateTime;
  last_updated: DateTime;

  extensions: object;
}
```

---

### 2.5 结构体四：AgentProfile (Agent身份模型)

#### 职责说明
描述各专业Agent的身份、能力边界、权限与协作规则。

#### 生命周期

| 阶段 | 说明 |
|------|------|
| 创建 | 系统初始化时由配置加载 |
| 更新 | 版本升级时更新能力定义 |
| 持久化 | 配置文件存储，运行时缓存 |
| 保留 | 永久保留，版本化管理 |

#### 读写权限

| 权限 | 主体 |
|------|------|
| **读取** | MasterOrchestrator, AgentRouter, AllAgents |
| **写入** | SystemAdmin (仅配置更新) |

#### 核心字段 (TypeScript风格)

```typescript
interface AgentProfile {
  agent_id: string;                   // 格式: AGT-XXXX
  agent_type: "SleepAgent" | "GlucoseAgent" | "StressAgent" | "NutritionAgent" | "ExerciseAgent" | "MentalHealthAgent" | "TCMWellnessAgent" | "CrisisAgent" | "CoachingAgent";
  schema_version: "1.0";

  display_name: string;
  display_name_cn: string;
  description: string;
  avatar_url?: string;

  expertise_domains: string[];
  primary_focus: string;

  capabilities: {
    analysis_types: string[];         // 可执行的分析类型
    intervention_types: string[];     // 可提供的干预类型
    data_requirements: string[];      // 需要的数据类型
    output_formats: string[];         // 输出格式
  };

  skill_ids: string[];                // 拥有的技能ID列表

  model_config: {
    llm_model: string;
    temperature: number;
    max_tokens: number;
    system_prompt_template: string;
  };

  permissions: {
    can_read_profile_sections: string[];
    can_suggest_updates: string[];
    can_escalate: boolean;
    can_generate_tasks: boolean;
    can_access_history: boolean;
    max_task_difficulty: number;
  };

  collaboration_rules: {
    can_collaborate_with: string[];
    requires_coordination_for: string[];
    conflict_resolution_priority: number;
  };

  triggering_conditions: Array<{
    condition_type: "keyword" | "data_threshold" | "risk_flag" | "user_preference" | "time_based";
    condition_value: object;
    priority: number;
  }>;

  rate_limits: {
    max_calls_per_session: number;
    max_calls_per_day: number;
    cooldown_minutes: number;
  };

  version: string;
  last_updated: DateTime;
  extensions: object;
}
```

---

### 2.6 结构体五：SkillDescriptor (技能描述模型)

#### 职责说明
描述可插拔的技能单元，定义输入输出规范与调用条件。

#### 生命周期

| 阶段 | 说明 |
|------|------|
| 创建 | 技能开发完成后注册 |
| 更新 | 技能升级时更新版本 |
| 持久化 | 技能注册表存储 |
| 保留 | 永久保留，支持版本回退 |

#### 读写权限

| 权限 | 主体 |
|------|------|
| **读取** | MasterOrchestrator, AllAgents, SkillRegistry |
| **写入** | SystemAdmin, SkillDeveloper |

#### 核心字段 (TypeScript风格)

```typescript
interface SkillDescriptor {
  skill_id: string;                   // 格式: SKL-XXXXXX
  skill_name: string;
  skill_name_cn: string;
  schema_version: "1.0";

  skill_type: "analysis" | "assessment" | "intervention" | "generation" | "transformation" | "validation" | "notification" | "integration";
  category: "core" | "domain_specific" | "utility" | "experimental";

  description: string;
  use_cases: string[];

  owner_agents: string[];             // 拥有此技能的Agent

  input_schema: {
    required_fields: Array<{
      field_name: string;
      field_type: string;
      description: string;
      source: string;                 // 数据来源路径
    }>;
    optional_fields: Array<{
      field_name: string;
      field_type: string;
      default_value: any;
      description: string;
    }>;
    context_requirements: string[];
  };

  output_schema: {
    output_fields: Array<{
      field_name: string;
      field_type: string;
      description: string;
      target_path: string;            // 写入目标路径
    }>;
    side_effects: string[];
  };

  invocation_conditions: {
    preconditions: string[];
    data_freshness_requirements: {
      max_age_hours: number;
      required_data_types: string[];
    };
    user_state_requirements: {
      min_behavior_stage?: string;
      excluded_risk_flags?: string[];
    };
  };

  execution_config: {
    executor_type: "llm_prompt" | "rule_engine" | "ml_model" | "external_api" | "hybrid";
    timeout_ms: number;
    retry_config: {
      max_retries: number;
      retry_delay_ms: number;
    };
    fallback_skill_id?: string;
  };

  quality_metrics: {
    accuracy_score: number;
    avg_latency_ms: number;
    success_rate: number;
    last_evaluated_at: DateTime;
  };

  version: string;
  created_at: DateTime;
  last_updated: DateTime;
  deprecated: boolean;
  deprecation_reason?: string;

  extensions: object;
}
```

---

### 2.7 结构体六A：Session (会话模型)

#### 职责说明
描述单次用户交互会话，包含对话、任务、决策的完整上下文。

#### 生命周期

| 阶段 | 说明 |
|------|------|
| 创建 | 用户发起交互时创建 |
| 更新 | 会话过程中持续追加事件 |
| 持久化 | 实时持久化，支持断点续传 |
| 保留 | 完成后归档，保留至少1年用于分析 |

#### 读写权限

| 权限 | 主体 |
|------|------|
| **读取** | MasterOrchestrator, AllAgents, SessionManager, AnalyticsEngine |
| **写入** | MasterOrchestrator, SessionManager |

#### 核心字段 (TypeScript风格)

```typescript
interface Session {
  session_id: string;                 // 格式: SES-XXXXXXXXXXXX
  user_id: string;
  schema_version: "1.0";

  session_type: "chat" | "assessment" | "task_review" | "daily_briefing" | "crisis_support" | "coaching_call";
  channel: "app" | "web" | "wechat_mini" | "api" | "voice";

  start_time: DateTime;
  end_time?: DateTime;
  duration_seconds?: number;

  status: "active" | "paused" | "completed" | "abandoned" | "error";

  // 会话开始时的用户状态快照
  context_snapshot: {
    behavior_stage: string;
    readiness_level: number;
    spi_score: number;
    active_goals: string[];
    active_tasks: string[];
    risk_flags: string[];
    recent_device_data: object;
  };

  // 对话记录
  conversation: Array<{
    message_id: string;
    role: "user" | "assistant" | "system";
    content: string;
    timestamp: DateTime;
    intent?: string;
    sentiment?: "positive" | "neutral" | "negative";
    entities?: object[];
  }>;

  // Agent调用记录
  agent_invocations: Array<{
    invocation_id: string;
    agent_type: string;
    task_id: string;
    invoked_at: DateTime;
    completed_at: DateTime;
    status: string;
    result_summary: string;
  }>;

  // 决策记录
  decisions_made: Array<{
    decision_id: string;
    decision_type: "routing" | "intervention" | "escalation" | "task_generation" | "goal_adjustment";
    decision_point: string;
    options_considered: string[];
    chosen_option: string;
    rationale: string;
    confidence: number;
    decided_at: DateTime;
  }>;

  tasks_generated: string[];

  // Profile更新记录
  profile_updates: Array<{
    field_path: string;
    old_value: any;
    new_value: any;
    update_source: string;
    updated_at: DateTime;
  }>;

  session_metrics: {
    message_count: number;
    user_message_count: number;
    avg_response_time_ms: number;
    engagement_score: number;
    satisfaction_rating?: number;
    tasks_completed_in_session: number;
  };

  session_summary: {
    main_topics: string[];
    key_insights: string[];
    action_items: string[];
    follow_up_needed: boolean;
    next_session_suggestions: string[];
  };

  metadata: {
    device_info: string;
    app_version: string;
    location?: string;
    timezone: string;
  };

  extensions: object;
}
```

---

### 2.8 结构体六B：Trajectory (轨迹模型)

#### 职责说明
描述用户的长期陪伴轨迹，支持科研导出与效果评估。

#### 生命周期

| 阶段 | 说明 |
|------|------|
| 创建 | 用户首次入组时创建 |
| 更新 | 定期聚合 Session、Task、Assessment 数据 |
| 持久化 | 独立存储，支持大数据量 |
| 保留 | 永久保留，支持匿名化科研导出 |

#### 读写权限

| 权限 | 主体 |
|------|------|
| **读取** | MasterOrchestrator, AnalyticsEngine, ResearchExporter, DashboardGenerator |
| **写入** | TrajectoryAggregator, SystemScheduler |

#### 核心字段 (TypeScript风格)

```typescript
interface Trajectory {
  trajectory_id: string;              // 格式: TRJ-XXXXXXXXXXXX
  user_id: string;
  schema_version: "1.0";

  start_date: Date;
  current_phase: string;
  total_days_in_program: number;

  // 行为阶段转换历史
  stage_transitions: Array<{
    from_stage: string;
    to_stage: string;
    transition_date: Date;
    trigger: string;
    days_in_previous_stage: number;
  }>;

  // 目标完成历史
  goal_history: Array<{
    goal_id: string;
    goal_description: string;
    status: string;
    started_at: Date;
    completed_at?: Date;
    success_rate: number;
  }>;

  // 干预计划历史
  intervention_history: Array<{
    plan_id: string;
    plan_type: string;
    started_at: Date;
    ended_at?: Date;
    outcome: string;
    effectiveness_score: number;
  }>;

  // 评估时间线
  assessment_timeline: Array<{
    assessment_id: string;
    assessment_type: string;
    date: Date;
    key_scores: object;
    risk_level_at_time: string;
  }>;

  // 关键指标趋势
  metric_trends: {
    spi_trend: Array<{date: Date; value: number}>;
    adherence_trend: Array<{week: string; rate: number}>;
    health_metrics: {[metric: string]: Array<{date: Date; value: number}>};
  };

  // 会话统计
  session_statistics: {
    total_sessions: number;
    total_messages: number;
    avg_session_duration_minutes: number;
    avg_sessions_per_week: number;
    most_active_time: string;
    engagement_trend: "increasing" | "stable" | "decreasing";
  };

  // 任务统计
  task_statistics: {
    total_tasks_assigned: number;
    total_tasks_completed: number;
    overall_completion_rate: number;
    avg_difficulty_completed: number;
    most_successful_task_types: string[];
    most_challenging_task_types: string[];
  };

  // 里程碑
  milestones_achieved: Array<{
    milestone_type: string;
    description: string;
    achieved_at: Date;
    significance: string;
  }>;

  // 风险事件记录
  risk_events: Array<{
    event_id: string;
    risk_type: string;
    severity: string;
    occurred_at: DateTime;
    resolved_at?: DateTime;
    resolution: string;
  }>;

  // 阶段性成果摘要
  outcome_summary: {
    primary_outcome_achieved: boolean;
    secondary_outcomes: string[];
    improvement_areas: string[];
    remaining_challenges: string[];
    next_phase_recommendations: string[];
  };

  // 科研导出配置
  research_export_config: {
    consent_for_research: boolean;
    anonymization_level: "none" | "pseudonymized" | "fully_anonymized";
    exportable_fields: string[];
    cohort_tags: string[];
  };

  last_aggregated_at: DateTime;
  aggregation_version: number;

  extensions: object;
}
```

---

## 第 3 章 | 数据流规范

### 3.1 主执行链路 (9步)

| 步骤 | 组件 | 输入 | 输出 | 涉及结构体 |
|------|------|------|------|-----------|
| 1 | INPUT_HANDLER | ExternalInput | UserInput | UserInput |
| 2 | PROFILE_MANAGER | UserInput | UserMasterProfile | UserMasterProfile, BehaviorState |
| 3 | RISK_ANALYZER | Profile+Input | RiskAssessment | BehaviorState |
| 4 | AGENT_ROUTER | Risk+Intent | RoutingDecision | AgentProfile, SkillDescriptor |
| 5 | MULTI_AGENT_COORDINATOR | RoutingDecision | CoordinatedResult | AgentProfile, SkillDescriptor, Session |
| 6 | INTERVENTION_PLANNER | Result+BehaviorState | InterventionPlan | Goal, Task, BehaviorState |
| 7 | RESPONSE_SYNTHESIZER | InterventionPlan | SynthesizedResponse | Session |
| 8 | TASK_GENERATOR | InterventionPlan | DailyTasks | Task, Goal |
| 9 | PROFILE_WRITER | AllResults | UpdatedProfile | UserMasterProfile, BehaviorState, Session, Trajectory |

### 3.2 写回渠道

| 渠道 | 目标 | 权限 | 校验 |
|------|------|------|------|
| AgentResult.data_updates | UserMasterProfile | MasterOrchestrator | Schema + BusinessRule |
| InterventionPlan.adjustment | BehaviorState + Goal | MasterOrchestrator | StageCompatibility |
| Task.completion_feedback | BehaviorState.adherence + Trajectory | MasterOrchestrator | None |
| Session.summary | Trajectory | TrajectoryAggregator | None |

### 3.3 禁止操作

- Agent私自维护UserMasterProfile
- 模块私自新增/删除/重命名核心结构体字段
- 绕过AgentTask/AgentResult直接跨模块通信
- 未经MasterOrchestrator直接写入BehaviorState
- Session外创建Trajectory记录

---

## 第 4 章 | 版本与扩展

### 4.1 版本信息

| 项目 | 值 |
|------|-----|
| Schema版本 | 1.0.0 |
| 向后兼容至 | 0.9.0 |
| 需迁移脚本 | 0.8.x, 0.7.x |

### 4.2 扩展策略

- **允许**: 所有结构体支持 `extensions` 字段用于自定义数据
- **命名规范**: Extensions 必须使用 snake_case 并带组织前缀 (如 `org_custom_field`)
- **禁止**: Extensions 不得复制或覆盖核心字段

---

## 附录：文件清单

| 文件 | 说明 |
|------|------|
| `core_data_schema_v1_final.json` | JSON Schema 完整定义 |
| `user_profile_schema.json` | UserMasterProfile详细定义 |
| `agent_task_schema.json` | AgentTask/AgentResult通信规范 |
| `action_plan_schema.json` | ActionPlan详细定义 |
| `behavior_logic.json` | 行为逻辑规则库 |
| `system_architecture.json` | 系统架构定义 |

---

*此文档为系统内核标准，任何修改需经架构评审委员会批准。*

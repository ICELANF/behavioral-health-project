# ARCHITECTURE.md — 行健平台架构 (手术后 v5.1)

> 生效日期: 2026-02-27
> 架构版本: v5.1 (Registry + 统一 MasterAgent)

## 系统架构总览

```
┌─────────────────────────────────────────────────────┐
│                   客户端层                            │
│  微信小程序 / H5 / Admin Portal / Expert Workbench   │
└───────────────┬─────────────────────────────────────┘
                │ HTTP/WebSocket
┌───────────────▼─────────────────────────────────────┐
│              API 网关层 (FastAPI)                     │
│  api/main.py → get_master_agent()                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│  │/chat     │ │/intervene│ │/api/v1/* │            │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘            │
└───────┼─────────────┼───────────┼───────────────────┘
        └─────────────┼───────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│              安全层 (三层防护)                        │
│  ① InputFilter    → 输入关键词/意图检测              │
│  ② CrisisAgent    → 危机干预 (priority=0)           │
│  ③ GenerationGuard → 输出安全检查 + 热线注入         │
└───────────────┬─────────────────────────────────────┘
                ▼
┌─────────────────────────────────────────────────────┐
│           MasterAgent (统一版, 666行)                │
│                                                     │
│  ┌─────────────────────────────────────────┐        │
│  │         AgentRegistry (冻结)             │        │
│  │  21 个 Agent 注册, freeze() 后不可变      │        │
│  └─────────────────────────────────────────┘        │
│                      │                              │
│  ┌───────────────────▼───────────────────┐          │
│  │         AgentRouter                    │          │
│  │  关键词匹配 + 设备数据 + 领域权重        │          │
│  │  → 选出 primary + secondary agents     │          │
│  └───────────────────┬───────────────────┘          │
│                      │                              │
│  ┌───────────────────▼───────────────────┐          │
│  │    Agent 并行执行 (process)             │          │
│  │    CrisisAgent → 永远第一个             │          │
│  │    [Sleep, Glucose, TCM, ...] → 按权重  │          │
│  └───────────────────┬───────────────────┘          │
│                      │                              │
│  ┌───────────────────▼───────────────────┐          │
│  │   MultiAgentCoordinator               │          │
│  │   冲突检测 → 消解 → 整合 → 共识提取     │          │
│  └───────────────────┬───────────────────┘          │
│                      │                              │
│  ┌───────────────────▼───────────────────┐          │
│  │   InterventionPlan + DailyBriefing    │          │
│  │   行动计划生成 + 每日推送              │          │
│  └─────────────────────────────────────────┘        │
└───────────────┬─────────────────────────────────────┘
                ▼
┌─────────────────────────────────────────────────────┐
│              数据层                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │PostgreSQL│  │  Redis   │  │  Qdrant  │          │
│  │用户/任务 │  │会话/缓存 │  │向量检索  │          │
│  └──────────┘  └──────────┘  └──────────┘          │
└─────────────────────────────────────────────────────┘
```

## Agent 三层架构

```
Layer 0 — 安全层 (priority 0)
├── CrisisAgent          危机干预, 不走 LLM

Layer 1 — 专家层 (priority 1-2)
├── XZBExpertAgent       行知宝专家
├── BehaviorCoachAgent   行为教练 (behavior_rx)
├── MetabolicExpertAgent 代谢专家 (behavior_rx)
├── CardiacExpertAgent   心脏专家 (behavior_rx)
├── AdherenceExpertAgent 依从性专家 (behavior_rx)
├── SleepAgent           睡眠
├── GlucoseAgent         血糖
├── StressAgent          压力
├── MentalAgent          心理
├── CardiacRehabAgent    心脏康复

Layer 2 — 领域层 (priority 3)
├── NutritionAgent       营养
├── ExerciseAgent        运动
├── TCMAgent             中医
├── MotivationAgent      动机
├── WeightAgent          体重

Layer 3 — 用户层 (priority 4-5)
├── TrustGuideAgent      信任引导
├── VisionAgent          愿景
├── OnboardingGuideAgent 新手引导
├── HealthAssistantAgent 健康助手 (默认兜底)
└── HabitTrackerAgent    习惯追踪
```

## 数据流契约

### AgentInput (进)
```python
@dataclass
class AgentInput:
    user_id: str
    message: str
    profile: dict          # 用户画像
    device_data: dict      # 设备数据 {sleep_hours, glucose, hrv, ...}
    context: dict          # 上下文 {stage, history, ...}
    session_id: str
```

### AgentResult (出)
```python
@dataclass
class AgentResult:
    agent_domain: str      # 匹配 AgentDomain 枚举值
    confidence: float      # 0.0 ~ 1.0
    risk_level: RiskLevel  # CRITICAL / HIGH / MEDIUM / LOW
    findings: list[str]
    recommendations: list[str]
    tasks: list[dict]      # 可选: 微行动任务
    metadata: dict         # Agent 特定元数据
    llm_enhanced: bool     # 是否走了 LLM
    llm_latency_ms: int
```

### 领域关联网络

```
sleep ←→ glucose ←→ nutrition
  ↕         ↕          ↕
stress ←→ exercise ←→ weight
  ↕         ↕
mental ←→ behavior_rx ←→ motivation
  ↕
tcm ←→ nutrition
  ↕
crisis ←→ mental ←→ stress
```

## 容器架构

```
┌─────────────────────────────────────┐
│          Docker Compose             │
│                                     │
│  bhp_v3_api      :8000  (FastAPI)  │
│  bhp_v3_worker         (Celery)    │
│  bhp_v3_beat           (定时任务)   │
│  bhp_v3_flower   :5555 (监控)      │
│  bhp_v3_postgres :5432             │
│  bhp_v3_redis    :6379             │
│  bhp_v3_qdrant   :6333             │
└─────────────────────────────────────┘
```

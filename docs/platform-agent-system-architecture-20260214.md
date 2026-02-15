# 全平台 Agent 系统架构 — 完整技术文档

> **版本**: v1.0 | **日期**: 2026-02-14 | **状态**: 全部已部署
> **覆盖范围**: 16 Agent 实例、双 MasterAgent、策略引擎、行为处方、安全流水线、反馈学习、生态市场、前端管理

---

## 目录

- [第一部分: 系统总览](#第一部分-系统总览)
- [第二部分: 核心 Agent 框架](#第二部分-核心-agent-框架)
- [第三部分: 12 标准 Agent](#第三部分-12-标准-agent)
- [第四部分: Agent 路由与协调](#第四部分-agent-路由与协调)
- [第五部分: 双 MasterAgent 架构](#第五部分-双-masteragent-架构)
- [第六部分: Agent 模板系统 (V006)](#第六部分-agent-模板系统-v006)
- [第七部分: 行为处方 Agent (Behavior Rx)](#第七部分-行为处方-agent-behavior-rx)
- [第八部分: 策略引擎 (V007)](#第八部分-策略引擎-v007)
- [第九部分: 安全流水线 (V005)](#第九部分-安全流水线-v005)
- [第十部分: LLM 客户端](#第十部分-llm-客户端)
- [第十一部分: 反馈学习环 (Phase 4)](#第十一部分-反馈学习环-phase-4)
- [第十二部分: Agent 生态市场 (Phase 5)](#第十二部分-agent-生态市场-phase-5)
- [第十三部分: 全部 API 端点](#第十三部分-全部-api-端点)
- [第十四部分: 前端管理页面](#第十四部分-前端管理页面)
- [第十五部分: 数据库模型总览](#第十五部分-数据库模型总览)
- [第十六部分: 配置文件](#第十六部分-配置文件)
- [第十七部分: 迁移记录](#第十七部分-迁移记录)
- [附录: 数据流与集成图谱](#附录-数据流与集成图谱)

---

## 第一部分: 系统总览

### 1.1 Agent 分类

| 类别 | 数量 | 实例 |
|------|------|------|
| 专科 Agent (Specialist) | 9 | Crisis, Sleep, Glucose, Stress, Nutrition, Exercise, Mental, TCM, Motivation |
| 整合 Agent (Integrative) | 3 | BehaviorRx, Weight, CardiacRehab |
| 动态 LLM Agent | N | GenericLLMAgent (模板驱动, 数量不限) |
| 行为处方专家 Agent | 4 | BehaviorCoach, MetabolicExpert, CardiacExpert, AdherenceExpert |
| MasterAgent | 2 | v0 (9 步编排器), v6 (模板感知+策略引擎) |
| **合计** | **16+N** | |

### 1.2 文件结构

```
core/agents/
├── __init__.py                  # 主导出
├── base.py                      # BaseAgent, 枚举, 注册表
├── specialist_agents.py         # 9 专科 Agent
├── integrative_agents.py        # 3 整合 Agent
├── generic_llm_agent.py         # 动态模板 Agent
├── master_agent.py              # v6 MasterAgent (模板感知)
├── router.py                    # AgentRouter (关键词匹配)
├── coordinator.py               # MultiAgentCoordinator (冲突解决)
├── prompts.py                   # 12 域 LLM 系统提示词
├── policy_gate.py               # RuntimePolicyGate (策略门控)
├── ollama_client.py             # 同步 Ollama HTTP 客户端
core/
├── master_agent.py              # v0 外观包装
├── master_agent_v0.py           # v0 实现 (6874 行)
├── agent_template_service.py    # 模板缓存 + DB 加载
├── rule_registry.py             # 规则注册表 (V007)
├── conflict_resolver.py         # 5 仲裁策略 (V007)
├── decision_trace.py            # 决策追踪 (V007)
├── cost_controller.py           # 成本控制 (V007)
├── policy_engine.py             # 策略引擎 5 步流水线 (V007)
├── stage_aware_selector.py      # TTM 阶段感知选择 (V007)
├── auto_exit_handler.py         # 自动退出处理 (V007)
├── effectiveness_metrics.py     # 6 效果指标 (V007)
├── llm_client.py                # 统一 LLM 客户端 (V005)
├── safety/pipeline.py           # 4 层安全流水线 (V005)
├── feedback_service.py          # 反馈持久化 (Phase 4)
├── ecosystem_service.py         # 市场+积分 (Phase 5)
behavior_rx/
├── core/rx_models.py            # 3 表 ORM
├── core/rx_schemas.py           # Pydantic DTO
├── core/behavior_rx_engine.py   # 处方计算引擎
├── core/agent_handoff_service.py# 交接服务
├── core/agent_collaboration_orchestrator.py  # 协作编排
├── core/rx_conflict_resolver.py # Rx 冲突解决
├── agents/base_expert_agent.py  # 专家 Agent 基类
├── agents/behavior_coach_agent.py
├── agents/metabolic_expert_agent.py
├── agents/cardiac_expert_agent.py
├── agents/adherence_expert_agent.py
├── patches/master_agent_integration.py  # MasterAgent 补丁
├── api/rx_routes.py             # 8 REST 端点
```

### 1.3 运行时架构

```
用户请求 → /api/v1/agent/run
    ↓
[优先级 1] v6 MasterAgent.process()
    ├─ 从 DB 加载模板 Agent
    ├─ 租户上下文路由
    ├─ 安全流水线 L1-L4
    ├─ 策略引擎评估 (可选)
    └─ 行为处方路由 (Step 3.5, 可选)
    ↓
[优先级 2] v0 MasterAgent.process()
    ├─ 硬编码 12 Agent
    └─ 9 步编排流水线
    ↓
[优先级 3] Mock 结果
    ↓
记录执行历史 → 返回响应
```

---

## 第二部分: 核心 Agent 框架

### 2.1 枚举与数据类

```python
class RiskLevel(str, Enum):
    CRITICAL = "critical"    # 立即干预
    HIGH = "high"            # 优先处理
    MODERATE = "moderate"    # 常规处理
    LOW = "low"              # 维护支持

class AgentDomain(str, Enum):
    CRISIS, SLEEP, GLUCOSE, STRESS, NUTRITION, EXERCISE,
    MENTAL, TCM, MOTIVATION, BEHAVIOR_RX, WEIGHT, CARDIAC_REHAB

class PolicyDecision(str, Enum):
    ALLOW, DELAY, ALLOW_SOFT_SUPPORT, ESCALATE_COACH, DENY

@dataclass
class AgentInput:
    user_id: int
    message: str
    intent: str = ""
    profile: dict = {}       # 用户画像
    device_data: dict = {}   # 设备数据
    context: dict = {}       # 会话上下文

@dataclass
class AgentResult:
    agent_domain: str
    confidence: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    findings: list[str] = []
    recommendations: list[str] = []
    tasks: list[dict] = []
    metadata: dict = {}
    llm_enhanced: bool = False
    llm_latency_ms: int = 0
```

### 2.2 BaseAgent 基类

```python
class BaseAgent:
    domain: AgentDomain
    display_name: str = ""
    keywords: list[str] = []        # 路由触发关键词
    data_fields: list[str] = []     # 关联设备数据
    priority: int = 5               # 0=最高
    base_weight: float = 0.8        # 路由权重
    enable_llm: bool = True         # 是否启用 LLM 增强

    def process(self, agent_input: AgentInput) -> AgentResult:
        raise NotImplementedError

    def matches_intent(self, message: str) -> bool:
        return any(kw in message.lower() for kw in self.keywords)

    def _enhance_with_llm(self, result, inp) -> AgentResult:
        # 云优先 LLM 增强 (UnifiedLLMClient)
        # 不可用时返回原始结果
```

### 2.3 全局注册表

**Agent 基础权重** (`AGENT_BASE_WEIGHTS`):

| Agent | 权重 | 优先级 |
|-------|------|--------|
| crisis | 1.0 | 0 (最高) |
| glucose | 0.9 | 1 |
| behavior_rx | 0.9 | 2 |
| sleep | 0.85 | 2 |
| stress | 0.85 | 2 |
| mental | 0.85 | 2 |
| weight | 0.85 | 2 |
| cardiac_rehab | 0.85 | 1 |
| nutrition | 0.8 | 3 |
| exercise | 0.8 | 3 |
| motivation | 0.8 | 3 |
| tcm | 0.75 | 4 |

**域关联网络** (`DOMAIN_CORRELATIONS`):

| Agent | 关联 Agent |
|-------|-----------|
| sleep | glucose, stress, mental, exercise |
| glucose | sleep, nutrition, exercise, weight, stress |
| stress | sleep, mental, exercise, cardiac_rehab |
| nutrition | glucose, exercise, weight, tcm |
| exercise | glucose, stress, sleep, weight, cardiac_rehab |
| mental | stress, sleep, behavior_rx, motivation |
| tcm | nutrition, sleep, mental, stress |
| crisis | mental, stress, behavior_rx |
| behavior_rx | 全部 8 个专科 + weight |
| weight | nutrition, exercise, glucose, sleep, mental, motivation, behavior_rx, tcm |
| cardiac_rehab | exercise, stress, sleep, nutrition, mental, glucose, weight, motivation, behavior_rx |

**冲突优先级** (`CONFLICT_PRIORITY`):

| 冲突对 | 胜者 |
|--------|------|
| glucose vs nutrition | glucose |
| sleep vs exercise | sleep |
| stress vs exercise | stress |
| mental vs exercise | mental |

---

## 第三部分: 12 标准 Agent

### 3.1 专科 Agent (9 个)

#### CrisisAgent — 危机干预

| 属性 | 值 |
|------|-----|
| priority | 0 (最高) |
| base_weight | 1.0 |
| enable_llm | **false** (确定性, 不使用 LLM) |
| keywords | 自杀, 自残, 不想活, 结束生命, 去死, 跳楼, 割腕, 安眠药, 遗书 |

**行为**: CRITICAL 关键词 → confidence=1.0, risk=CRITICAL; WARNING 关键词 → confidence=0.9, risk=HIGH

#### SleepAgent — 睡眠专家

| 属性 | 值 |
|------|-----|
| priority | 2 |
| data_fields | sleep |
| keywords | 睡眠, 失眠, 早醒, 熬夜, 睡不着, 嗜睡, 打鼾, 午睡 |

**规则**: sleep_hours < 6h → 睡眠卫生建议; > 9h → 抑郁筛查; 关键词匹配 → CBT-I 推荐

#### GlucoseAgent — 血糖管理

| 属性 | 值 |
|------|-----|
| priority | 1 |
| base_weight | 0.9 |
| data_fields | cgm |
| keywords | 血糖, 糖尿病, 胰岛素, 低血糖, 高血糖, 糖化, 控糖 |

**规则**: cgm > 10.0 mmol/L → 高血糖; < 3.9 mmol/L → CRITICAL 低血糖

#### StressAgent — 压力管理

| 属性 | 值 |
|------|-----|
| priority | 2 |
| data_fields | hrv |
| keywords | 压力, 焦虑, 紧张, 烦躁, 崩溃, 喘不过气 |

**规则**: HRV SDNN < 30ms → 自主神经过度激活; 推荐 4-7-8 呼吸法

#### NutritionAgent — 营养指导

| 属性 | 值 |
|------|-----|
| priority | 3 |
| keywords | 饮食, 营养, 减肥, 热量, 碳水, 蛋白质, 吃什么, 食谱, 代餐, 节食 |

**阶段感知**: S0-S1 仅意识; S2-S3 碳水控制+蛋白增加; S4+ CGM 精准营养

#### ExerciseAgent — 运动指导

| 属性 | 值 |
|------|-----|
| priority | 3 |
| data_fields | activity |
| keywords | 运动, 健身, 步数, 跑步, 散步, 力量训练, 瑜伽 |

**规则**: 步数 < 5000 → 活动不足; 推荐每小时散步任务

#### MentalHealthAgent — 心理咨询

| 属性 | 值 |
|------|-----|
| priority | 2 |
| keywords | 情绪, 抑郁, 心情, 难过, 伤心, 郁闷, 无助 |

**规则**: 抑郁关键词 → PHQ-9 筛查; 情绪关键词 → ABC 情绪日记; LLM 增强深度

#### TCMWellnessAgent — 中医养生

| 属性 | 值 |
|------|-----|
| priority | 4 (最低专科) |
| base_weight | 0.75 |
| keywords | 中医, 体质, 穴位, 气血, 经络, 养生, 上火, 湿气 |

**行为**: 无硬编码规则, 完全依赖 LLM 个性化建议

#### MotivationAgent — 动机管理

| 属性 | 值 |
|------|-----|
| priority | 3 |
| keywords | 动力, 坚持, 放弃, 没意义, 为什么, 值不值 |

**阶段感知**: S0-S1 探索个人意义; S2-S3 动机访谈; S4+ 身份强化

### 3.2 整合 Agent (3 个)

#### BehaviorRxAgent — 行为处方师

| 属性 | 值 |
|------|-----|
| priority | 2 |
| base_weight | 0.9 |
| keywords | 行为处方, 习惯, 戒烟, 依从性, 打卡, 任务 |
| 关联 | 全部 8 专科 + weight |

**行为**: 跨域综合干预; S0-S1 观察任务; S2-S3 试验处方; S4+ 完整处方

#### WeightAgent — 体重管理师

| 属性 | 值 |
|------|-----|
| priority | 2 |
| keywords | 体重, 减重, BMI, 脂肪, 腰围, 减肥 |

**行为**: BMI >= 28 → 多系统干预 (营养+运动+睡眠+压力)

#### CardiacRehabAgent — 心脏康复师

| 属性 | 值 |
|------|-----|
| priority | 1 (高) |
| keywords | 心脏, 心血管, 冠心病, 康复, 心梗, 支架 |

**行为**: 分期康复方案 (Phase 1-3); 安全心率区 = HRmax x 50-70%

### 3.3 GenericLLMAgent — 动态模板 Agent

```python
class GenericLLMAgent(BaseAgent):
    def __init__(self, template: dict):
        # 从模板加载所有属性
        self._agent_id = template["agent_id"]
        self.domain = AgentDomain(template.get("domain_enum"))
        self.keywords = template.get("keywords", [])
        self._template_system_prompt = template.get("system_prompt", "")

    def process(self, inp: AgentInput) -> AgentResult:
        # 无硬编码规则 — 纯 LLM 增强
        # 构建基础结果 → _enhance_with_llm() → 返回
```

---

## 第四部分: Agent 路由与协调

### 4.1 AgentRouter (路由器)

**文件**: `core/agents/router.py`

```python
class AgentRouter:
    def route(self, inp: AgentInput, max_agents: int = 2,
              tenant_ctx: Optional[dict] = None) -> list[str]:
```

**6 级路由优先规则**:

| 级别 | 条件 | 加分 |
|------|------|------|
| 1 | 危机强制: crisis + matches_intent() | 立即返回 ["crisis"] |
| 2 | 风险等级: critical/crisis | +100 |
| 2 | 风险等级: high + (glucose/stress/mental) | +50 |
| 3 | 关键词匹配: 专家自定义 (tenant_ctx) | +30 x boost |
| 3 | 关键词匹配: 平台预设 | +30 |
| 4 | 用户偏好: profile.preferences.focus | +20 |
| 5 | 设备数据: data_fields 与 device_data 交集 | +15 |
| 6 | 域关联: 主 Agent 的关联 Agent (有关键词匹配) | 追加第二 Agent |

**回退逻辑**: 无匹配 → `behavior_rx` (或租户自定义 fallback_agent)

**租户上下文** (tenant_ctx):
- `enabled_agents`: 租户启用的 Agent 列表
- `agent_keyword_overrides`: 自定义关键词 + boost 倍率
- `correlations`: 租户级关联覆盖
- `fallback_agent`: 默认回退 Agent

### 4.2 MultiAgentCoordinator (协调器)

**文件**: `core/agents/coordinator.py`

**9 步协调流水线**:

| 步骤 | 操作 |
|------|------|
| 1 | 分配权重: `weight = BASE_WEIGHT[domain] x confidence` |
| 2 | 检测冲突: 查 CONFLICT_PRIORITY 表 |
| 3 | 解决冲突: 败者 confidence x 0.6 衰减 |
| 4 | 合并发现: 按序拼接所有 findings |
| 5 | 合并建议: 按 `weight x confidence` 评分排序 |
| 6 | 综合风险: 取所有 Agent 最高 RiskLevel |
| 7 | 计算置信度: 加权平均 |
| 8 | 提取共识: 出现 >= 2 Agent 的建议 |
| 9 | 生成摘要: "综合 N 个 Agent: 风险=X, 置信度=Y" |

### 4.3 RuntimePolicyGate (策略门控)

**文件**: `core/agents/policy_gate.py`

| 规则 | 条件 | 决策 | 允许模式 |
|------|------|------|---------|
| #0 | risk=critical | ALLOW | crisis_support |
| #1 | unstable + challenge | DELAY | [] |
| #2 | stage in S0,S1 | ALLOW_SOFT_SUPPORT | empathy, exploration |
| #3 | dropout_risk + stage S3-S6 | ESCALATE_COACH | empathy, coach_support |
| #4 | relapse_risk | ALLOW_SOFT_SUPPORT | empathy, maintenance |
| #5 | 默认 | ALLOW | empathy, challenge, execution |

---

## 第五部分: 双 MasterAgent 架构

### 5.1 v6 MasterAgent (模板感知)

**文件**: `core/agents/master_agent.py`

```python
class MasterAgent:
    def __init__(self, db_session=None):
        # 从 DB 加载模板 Agent (回退到硬编码 12 Agent)
        agents = build_agents_from_templates(db_session) or hardcoded_12
        self.router = AgentRouter(agents)
        self.coordinator = MultiAgentCoordinator()
        self.policy_gate = RuntimePolicyGate()
        self._policy_engine = PolicyEngine(db_session)  # V007 可选
```

**9+3 步处理流水线**:

| 步骤 | 操作 | 来源 |
|------|------|------|
| 1-2 | 构建 AgentInput | 核心 |
| 2.5 | SafetyPipeline L1 输入过滤 | V005 |
| 3.5 | ExpertAgentRouter (行为处方) | Behavior Rx |
| 4 | PolicyEngine 评估 / AgentRouter 路由 | V007 / 核心 |
| 4.5 | 洞察生成 (设备+画像关键指标) | 核心 |
| 5 | 调用目标 Agent | 核心 |
| 6 | MultiAgentCoordinator 协调 | 核心 |
| 7 | RuntimePolicyGate 门控 | 核心 |
| 7.5 | SafetyPipeline L3 生成守卫 | V005 |
| 8 | 响应综合 (LLM 优先, 模板回退) | 核心 |
| 8.5 | SafetyPipeline L4 输出过滤 | V005 |
| 9 | 返回最终响应 | 核心 |

**返回结构**:
```python
{
    "response": str,              # 综合响应文本
    "tasks": list[dict],          # 建议任务
    "risk_level": str,            # 最高风险级别
    "agents_used": list[str],     # 参与 Agent ID
    "gate_decision": str,         # 策略门控决策
    "coordination": dict,         # 协调详情
    "insights": list[str],        # 数据洞察
    "processing_time_ms": int,
    "llm_enhanced": bool,
    "safety": dict,               # V005 安全元数据
    "policy_trace_id": str,       # V007 决策追踪 ID
}
```

### 5.2 v0 MasterAgent (原始编排器)

**文件**: `core/master_agent_v0.py` (6,874 行)

**Core Data Schema v1.0**:

| 数据类 | 用途 |
|--------|------|
| `CoreUserInput` | 统一输入 (chat/device/questionnaire) |
| `CoreUserMasterProfile` | 系统唯一权威用户主画像 |
| `CoreAgentTask` | 编排器→Agent 标准指令 |
| `CoreAgentResult` | Agent→编排器 标准回传 |
| `CoreInterventionPlan` | 干预路径对象 (行为处方) |
| `CoreDailyTask` | 每日任务与陪伴执行对象 |

**9 步流水线**: Input Handler → Profile Manager → Risk Analyzer → Agent Router → Multi-Agent Coordinator → Intervention Planner → Response Synthesizer → Task Generator → Profile Writer

### 5.3 运行时切换

**`api/main.py` 全局单例**:
- `get_master_agent()` → v0 (懒加载, 失败返回 None)
- `get_agent_master()` → v6 (从 DB 模板加载, 回退硬编码)
- `reset_agent_master()` → 重置 v6 单例 (模板变更后调用)

---

## 第六部分: Agent 模板系统 (V006)

### 6.1 模板缓存服务

**文件**: `core/agent_template_service.py`

| 函数 | 作用 |
|------|------|
| `load_templates(db)` | 加载所有启用模板到内存缓存 |
| `get_cached_templates()` | 返回缓存深拷贝 |
| `invalidate_cache()` | 清空缓存 (CRUD 后调用) |
| `build_agents_from_templates(db)` | 预设→注册表实例化; dynamic_llm→GenericLLMAgent |
| `build_correlations_from_templates()` | 提取模板关联覆盖 |
| `build_conflict_priority_from_templates()` | 提取模板冲突覆盖 |
| `get_tenant_routing_context(tenant_id, db)` | 租户路由配置 |

**构建策略**:
1. 预设 Agent (specialist/integrative): 从 AGENT_CLASS_REGISTRY 实例化 → 用模板属性覆盖
2. 动态 Agent (dynamic_llm): 用 GenericLLMAgent(template) 包装
3. DB 失败: 返回 None → 调用方回退到硬编码

### 6.2 12 预设种子

**文件**: `configs/agent_templates_seed.json`

每个模板包含: agent_id, display_name, agent_type, domain_enum, description, keywords, data_fields, correlations, priority, base_weight, enable_llm, system_prompt, conflict_wins_over, is_preset=true

### 6.3 模板 CRUD API (10 端点)

**前缀**: `/api/v1/agent-templates`, 权限: `require_admin`

| 方法 | 路径 | 功能 |
|------|------|------|
| GET | `/list` | 列表 (可过滤 type/enabled) |
| GET | `/presets` | 仅预设模板 |
| GET | `/domains` | AgentDomain 枚举值 |
| GET | `/{agent_id}` | 单模板详情 |
| POST | `/create` | 创建 (仅 dynamic_llm) |
| PUT | `/{agent_id}` | 更新模板 |
| DELETE | `/{agent_id}` | 删除 (仅非预设) |
| POST | `/{agent_id}/toggle` | 启用/禁用 |
| POST | `/{agent_id}/clone` | 克隆 |
| POST | `/refresh-cache` | 刷新缓存 |

**agent_id 格式**: `^[a-z][a-z0-9_]{2,31}$`

### 6.4 专家自助 Agent 管理 (6 端点)

**前缀**: `/api/v1/tenants/{tid}/my-agents`, 权限: `require_coach_or_admin`

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/` | 创建自定义 Agent (dynamic_llm + TenantAgentMapping) |
| GET | `/` | 列表 (预设+自定义, 含 is_primary, custom_keywords) |
| PUT | `/{aid}` | 更新 (预设不可改 system_prompt) |
| POST | `/{aid}/toggle` | 启用/禁用 (crisis 不可禁) |
| POST | `/test-routing` | 路由测试对比 (平台 vs 租户) |
| DELETE | `/{aid}` | 删除自定义 Agent |

---

## 第七部分: 行为处方 Agent (Behavior Rx)

### 7.1 三维计算引擎

**文件**: `behavior_rx/core/behavior_rx_engine.py`

**三维输入**:
- **TTM 阶段** (S0-S6): 决定策略选择
- **大五人格** (O,C,E,A,N, 0-100): 决定沟通风格 + 微调
- **能力分数** (0-1): 决定强度、节奏、难度

**12 行为改变策略** (TTM/SESMOA):

| 策略 | 中文 | 适用阶段 | 证据 |
|------|------|---------|------|
| CONSCIOUSNESS_RAISING | 意识提升 | S0-S2 | T1 |
| DRAMATIC_RELIEF | 情感唤醒 | S0-S1 | T2 |
| SELF_REEVALUATION | 自我重评 | S1-S2 | T2 |
| DECISIONAL_BALANCE | 决策平衡 | S1-S3 | T1 |
| COGNITIVE_RESTRUCTURING | 认知重构 | S0-S4 | T1 |
| SELF_LIBERATION | 自我解放 | S2-S3 | T2 |
| STIMULUS_CONTROL | 刺激控制 | S3-S5 | T1 |
| CONTINGENCY_MANAGEMENT | 强化管理 | S3-S5 | T1 |
| HABIT_STACKING | 习惯叠加 | S3-S5 | T1 |
| SYSTEMATIC_DESENSITIZATION | 系统脱敏 | S1-S4 | T1 |
| RELAPSE_PREVENTION | 复发预防 | S3-S6 | T1 |
| SELF_MONITORING | 自我监测 | S2-S6 | T1 |

**处方计算流水线** (`compute_rx`):

| 步骤 | 操作 |
|------|------|
| 1 | `_select_strategies()`: 阶段基线 → Agent 偏好 → 人格修正 → 障碍增强 → 主+辅策略 |
| 2 | `_determine_communication_style()`: high_N→共情, high_C→数据驱动, high_E→探索, high_A→社会证明 |
| 3 | 强度查找: INTENSITY_MATRIX[stage][capacity_band] |
| 4 | `_determine_pace()`: 低阶段/低能力→slow; 高阶段/高稳定→fast |
| 5 | `_generate_micro_actions()`: 模板动作 × 能力系数 |
| 6 | `_generate_reward_triggers()`: 人格适配 (E→praise, C→badge) |
| 7 | `_calculate_resistance_threshold()`: base 0.3 + 人格/能力调整 |
| 8 | `_generate_escalation_rules()`: Agent 特定 + 通用 |
| 9 | `_formulate_goal_behavior()`: 阶段特定行为描述 |
| 10 | `_calculate_confidence()`: base 0.7 + 稳定性 + 策略匹配 + 依从性 |
| 11 | `_generate_reasoning()`: 审计日志 |

**效果评估** (`evaluate_effectiveness`):
- IES = completion×0.4 + (days/30)×0.2 + (stage_change+1)/3×0.25 - (resistance/10)×0.15
- IES >= 0.7: 继续; >= 0.4: 调整; < 0.4: 切换策略

### 7.2 四个专家 Agent

#### BehaviorCoachAgent — 行为教练 (S0-S2, 半透明模式)

- 用户能感知行为科学方法论
- S0: 温和唤醒 → 健康风险认知
- S1: 深化认知 + 决策引导
- S2: 承诺 + 计划 → 自我解放
- S3+: 交接信号 → 领域 Agent

#### MetabolicExpertAgent — 代谢专家 (冰山模型)

- 用户看到: 代谢专业建议
- 隐藏: 行为处方 (RxPrescription)
- 低阶段: 血糖数据教育
- 行动阶段: 具体饮食+运动处方
- 维持阶段: 自主数据管理

#### CardiacExpertAgent — 心脏康复专家 (运动恐惧脱敏)

- 常量: FEAR_SCORE_HIGH=40, MODERATE=25, LOW=15; HR_SAFETY_MARGIN=0.85; RPE_MAX=14
- 4 期康复: phase_1(住院) → phase_2_early(居家) → phase_2_rehab(训练) → phase_3(维持)
- 核心: 系统脱敏 3 周渐进暴露 (散步→快走→轻有氧)
- 安全: HR/BP/RPE 实时监控 + AutoExitHandler

#### AdherenceExpertAgent — 依从性专家 (横切面)

- 五类依从行为: 服药、就诊、检查、饮食医嘱、运动医嘱
- 五类障碍映射: 遗忘→习惯叠加, 恐惧→认知重构, 认知→意识提升, 经济→自我监测, 关系→自我解放
- 核心重构: "患者不依从" → "行为链设计不当" → 找断点修复

### 7.3 协作编排器

**文件**: `behavior_rx/core/agent_collaboration_orchestrator.py`

**8 个协作场景**:

| 场景 | 触发条件 | 主 Agent | 合并策略 |
|------|---------|---------|---------|
| STAGE_REGRESSION | stability<0.3 或 efficacy<0.2 | Coach | coach_override |
| ADHERENCE_ALERT | med_missed>=4 或 visit_overdue>=30 | Adherence | adherence_lead |
| MULTI_MORBIDITY | 同时有代谢+心脏数据 | Metabolic | parallel_merge |
| EXERCISE_FEAR | fear_score>=25 且 stage<=2 | Coach→Cardiac | primary_first |
| PRE_VISIT | next_visit<=3 天 | Adherence | adherence_lead |
| NEW_USER | stage<=2 且无当前 Agent | Coach | single_agent |
| DOMAIN_COORDINATION | 领域间协调需求 | 当前 Agent | primary_first |
| DEFAULT | 默认 | 当前 Agent | single_agent |

**合并策略**:
- `single_agent`: 仅主 Agent
- `coach_override`: Coach 覆盖 + 领域暂停说明
- `adherence_overlay`: 主 Agent + 依从提醒分隔
- `parallel_merge`: 并行领域整合
- `primary_first`: 主 Agent 优先 + 辅助追加
- `adherence_lead`: 依从主导

### 7.4 交接协议

**文件**: `behavior_rx/core/agent_handoff_service.py`

**交接类型**: STAGE_PROMOTION, STAGE_REGRESSION, DOMAIN_COORDINATION, CROSS_CUTTING, EMERGENCY_TAKEOVER, SCHEDULED_HANDOFF

**交接状态**: INITIATED → ACCEPTED → IN_PROGRESS → COMPLETED / REJECTED / CANCELLED

**触发规则** (按优先级):
1. Coach → 阶段晋升 → 领域 Agent (stage>=3 且 readiness>=0.6)
2. 领域 Agent → 阶段退步 → Coach (stage<=1)
3. 任何 → 自效能崩溃 → Coach (self_efficacy<0.2 且 stability<0.3)
4. 任何 → 依从问题 → Adherence (med_missed>=3 或 visit_overdue>=14)
5. Metabolic/Cardiac → 共病 → 对方 Agent

### 7.5 MasterAgent 集成补丁

**文件**: `behavior_rx/patches/master_agent_integration.py`

```python
class ExpertAgentRouter:
    def should_route_to_expert(user_input, user_profile) -> (bool, Optional[AgentType]):
        # 1. 关键词匹配 (代谢/心脏/行为/依从)
        # 2. 领域数据存在性
        # 3. 低阶段 (<=S2) → Coach

    def route_and_execute(user_input, user_id, session_id, current_agent, db):
        # → CollaborationOrchestrator.orchestrate()

def patch_master_agent_v0(master_agent_class):
    # 非侵入式补丁: process() 方法内 Step 3.5
    # 匹配→专家路由; 不匹配→原始 12 Agent
```

### 7.6 处方 REST API (8 端点)

**前缀**: `/api/v1/rx`

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| POST | `/compute` | coach+ | 计算行为处方 |
| GET | `/{rx_id}` | coach+ | 处方详情 |
| GET | `/user/{user_id}` | coach+ | 用户处方历史 |
| GET | `/strategies` | 公开 | 策略模板列表 |
| POST | `/handoff` | coach+ | 发起交接 |
| GET | `/handoff/{user_id}` | coach+ | 交接日志 |
| POST | `/collaborate` | coach+ | 协作编排 |
| GET | `/agents/status` | 公开 | Agent 注册状态 |

### 7.7 冲突解决

**文件**: `behavior_rx/core/rx_conflict_resolver.py`

**冲突类型**: STRATEGY_MISMATCH, INTENSITY_MISMATCH, DIRECTIVE_CONFLICT, PACE_CONFLICT, NO_CONFLICT

**解决原则**:
- 强度冲突: 保守原则 (取最低)
- 策略冲突: 阶段适配 (匹配当前 TTM 阶段优先排序)
- 指令冲突: Coach 仲裁 (AGENT_ARBITRATION_PRIORITY: Coach=10, Adherence=7, Cardiac=5, Metabolic=5)

---

## 第八部分: 策略引擎 (V007)

### 8.1 五步流水线

**文件**: `core/policy_engine.py`

```
Event + UserContext
    ↓
Step 1: 规则收集 (RuleRegistry)
    → 匹配租户 + 条件 + 优先级
    ↓
Step 2: 候选构建 (AgentApplicabilityMatrix)
    → 阶段/风险/禁忌 过滤 + 评分
    ↓
Step 3: 冲突仲裁 (ConflictResolver, 5 策略)
    → 主 Agent + 次 Agent + 权重
    ↓
Step 4: 成本控制 (CostController)
    → 预算检查 + 模型降级
    ↓
Step 5: 决策追踪 (DecisionTrace)
    → UUID 追踪记录 + 可解释 AI
    ↓
返回 ExecutionPlan
```

### 8.2 规则注册表

**文件**: `core/rule_registry.py`

- **JsonLogicEvaluator**: 简化 JSON-Logic (支持 ==, !=, >, <, in, and, or, not, var)
- **RuleCache**: 线程安全内存缓存 (RLock)
- **RuleRegistry**: DB 加载 + 热刷新 + CRUD + 条件评估

**4 默认种子规则**:

| 规则名 | 优先级 | 类型 | 条件 | 动作 |
|--------|--------|------|------|------|
| crisis_absolute_priority | 100 | safety | risk_level=="critical" | 强制 crisis Agent |
| medical_boundary_suppress | 95 | safety | risk=high + 医疗域 | 升级到医疗审核 |
| cost_daily_limit_default | 70 | cost | token_usage>=0.9 | 降级模型 |
| early_stage_gentle_intensity | 60 | stage | stage in S0,S1 | 限制干预强度 |

### 8.3 冲突仲裁 (5 策略)

**文件**: `core/conflict_resolver.py`

| 策略 | 触发条件 | 行为 |
|------|---------|------|
| **RiskSuppression** | risk=critical | 强制 CrisisAgent, 其余权重归零 |
| **MedicalBoundary** | 有医疗 Agent + risk>=high | 医疗 Agent 优先, 非医疗被抑制 |
| **TenantOverride** | 租户级规则存在 | 租户强制 Agent 优先 |
| **PriorityTree** | 有 select_agent 规则 | 按规则优先级排序 |
| **WeightedScore** | 默认回退 | score×0.4 + stage_effectiveness×0.35 + history×0.25 |

### 8.4 成本控制

**文件**: `core/cost_controller.py`

**模型成本表** (每 1K tokens, CNY):

| 模型 | 输入 | 输出 |
|------|------|------|
| deepseek-chat | 0.001 | 0.002 |
| qwen-turbo | 0.0008 | 0.002 |
| qwen-plus | 0.004 | 0.012 |
| qwen-max | 0.02 | 0.06 |
| gpt-4o | 0.0375 | 0.15 |
| gpt-4o-mini | 0.00225 | 0.009 |
| ollama-local | 0.0 | 0.0 |

**降级路径**: gpt-4o → qwen-max → qwen-plus → deepseek-chat → qwen-turbo → ollama-local

**预算区间**: <0.8 正常 | 0.8-1.0 降级 | >=1.0 阻止/排队/降到 ollama

### 8.5 阶段感知选择

**文件**: `core/stage_aware_selector.py`

**阶段效果矩阵**:

| Agent | S0 | S1 | S2 | S3 | S4 | S5 |
|-------|----|----|----|----|----|----|
| motivation | 0.9 | 0.8 | 0.5 | 0.3 | | |
| education | 0.7 | 0.9 | 0.6 | 0.4 | | |
| nutrition | | 0.5 | 0.7 | 0.9 | 0.8 | |
| exercise | | | 0.6 | 0.9 | 0.8 | 0.7 |
| glucose | | | 0.5 | 0.8 | 0.9 | 0.7 |
| emotion | 0.8 | 0.7 | 0.6 | 0.5 | | |
| crisis | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

### 8.6 自动退出处理

**文件**: `core/auto_exit_handler.py`

**4 种检查**:
1. **关键词触发**: 消息中含边界关键词 → 退出
2. **数据异常**: 血糖<低阈值(低血糖)/血压>阈值/心率异常 → critical
3. **风险超限**: 当前风险>Agent 最大风险 → 升级
4. **行为触发**: 行为标志匹配边界条件 → warning

### 8.7 效果度量 (6 指标)

**文件**: `core/effectiveness_metrics.py`

| 指标 | 公式 | 范围 |
|------|------|------|
| **IES** (干预效果) | stage_delta×0.4 + task_completion×0.3 + data_trend×0.3 | [-1, 1] |
| **阶段转换率** | (forward - backward) / days | 趋势 |
| **依从指数** | task_completion×0.6 + challenge_completion×0.4 | [0, 1] |
| **风险降低指数** | 数据趋势反向 | improved/worsened/stable |
| **专家 ROI** | avg_ies / (avg_token_cost/1000) | 比值 |
| **生态健康** | diversity×0.3 + (1-conflict)×0.2 + (1-latency)×0.2 + users×0.3 | [0, 1] |

### 8.8 策略 API (12 端点)

**前缀**: `/api/v1/policy`

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| GET | `/rules` | 用户 | 规则列表 |
| POST | `/rules` | admin | 创建规则 |
| PUT | `/rules/{id}` | admin | 更新规则 |
| DELETE | `/rules/{id}` | admin | 删除规则 |
| POST | `/rules/{id}/test` | 用户 | 测试规则 |
| POST | `/simulate` | 用户 | 模拟策略评估 |
| GET | `/traces/user/{uid}` | 用户 | 用户决策历史 |
| GET | `/traces/{trace_id}` | 用户 | 可解释追踪详情 |
| GET | `/traces/agent/{aid}/stats` | 用户 | Agent 触发统计 |
| GET | `/cost/report` | 用户 | 成本报告 |
| POST | `/rules/refresh` | admin | 热刷新 |
| POST | `/rules/seed` | admin | 注入默认规则 |

---

## 第九部分: 安全流水线 (V005)

### 9.1 四层架构

**文件**: `core/safety/pipeline.py`

```
L1 InputFilter  → 危机/封禁/医嘱/PII 检测
L2 RAGSafety    → 证据分级权重 + 过期过滤
L3 GenerationGuard → 安全约束注入 LLM Prompt
L4 OutputFilter  → 医嘱声明/绝对承诺/免责检测
```

### 9.2 L1 输入过滤

**检测优先级**:
1. **Crisis** (最高): 15 关键词 → safe=False, severity=critical
2. **Blocked**: 7 关键词 → safe=False, severity=high
3. **Warning**: 15 关键词 → safe=True (标记), severity=high
4. **Medical**: 12 关键词 + 剂量正则 → safe=True, severity=medium
5. **PII**: 手机/身份证/邮箱正则 → safe=True, severity=low

### 9.3 L3 安全约束注入

```
【安全约束 — 必须严格遵守】
1. 你不是医生, 不得直接诊断疾病或开具处方
2. 涉及药物/剂量/手术等医疗决策时, 必须引导用户咨询专业医生
3. 心理危机提供紧急热线: 400-161-9995 / 010-82951332 / 400-821-1215
4. 不得给出绝对化健康承诺
5. 建议以循证医学为基础
6. 末尾附: "以上建议仅供参考, 具体请咨询您的主治医生"
```

### 9.4 L4 输出过滤

| 检测 | 模式 | 级别 |
|------|------|------|
| 诊断语句 | "你得了/诊断为/确诊" | blocked (删除) |
| 绝对承诺 | "保证/100% 治愈/有效" | review_needed |
| 药物剂量 | "每日 N mg/片" | review_needed |

---

## 第十部分: LLM 客户端

### 10.1 UnifiedLLMClient

**文件**: `core/llm_client.py`

**路由策略**:

| 策略 | 行为 |
|------|------|
| `cloud_first` (默认) | 云 LLM → Ollama 回退 |
| `local_first` | Ollama → 云回退 |
| `cloud_only` | 仅云 |
| `local_only` | 仅 Ollama |

**云 LLM 配置** (环境变量):
- `CLOUD_LLM_PROVIDER` / `CLOUD_LLM_API_KEY` / `CLOUD_LLM_BASE_URL` (默认: deepseek)
- `CLOUD_LLM_MODEL` (默认: deepseek-chat)
- `LLM_ROUTE_STRATEGY` (默认: cloud_first)

**Ollama 配置**:
- 模型: `qwen2.5:0.5b` (对话), `qwen2.5vl:7b` (视觉)
- 超时: Agent 30s, 综合 45s
- 健康检查: 30s TTL 缓存

### 10.2 Agent LLM 提示词

**文件**: `core/agents/prompts.py`

12 个域系统提示词 (DOMAIN_SYSTEM_PROMPTS):
- 格式统一: "你是一位{领域}专家...根据用户的{数据}...3-5 条建议, 每条不超过 30 字"
- crisis: 空 (无 LLM)
- 综合提示词 (SYNTHESIS_SYSTEM_PROMPT): 100-200 字, 阶段感知语气, 自然对话风格

---

## 第十一部分: 反馈学习环 (Phase 4)

### 11.1 反馈持久化

**文件**: `core/feedback_service.py`

```python
save_feedback(db, agent_id, user_id, feedback_type, rating, comment, ...)
# feedback_type: accept / reject / modify / rate
# 持久化到 agent_feedbacks 表
```

### 11.2 每日指标聚合

```python
aggregate_daily_metrics(db, target_date=None)
# 调度: 01:30 UTC
# 按 agent_id 分组: feedback_count, acceptance_rate, avg_rating, avg_processing_ms
# UPSERT 到 agent_metrics_daily
```

### 11.3 成长报告

```python
get_agent_growth_report(db, agent_id, days=30)
# 返回: summary, daily_metrics[], prompt_versions[]
# trend_acceptance_7d: 最近 7 天 vs 前 7 天接受率变化
```

### 11.4 Prompt 版本管理

```python
create_prompt_version(db, agent_id, system_prompt, change_reason, activate=True)
# 版本号递增 + 前版本指标快照
# activate → 停用旧版 + 同步 AgentTemplate.system_prompt
# 支持 A/B 测试: traffic_pct 字段 (0-100)
```

### 11.5 反馈 API (8 端点)

**前缀**: `/api/v1/agent-feedback`

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| POST | `/submit` | 用户 | 提交反馈 |
| GET | `/list` | coach+ | 反馈列表 |
| GET | `/growth/{agent_id}` | 用户 | 成长报告 |
| GET | `/summary` | 用户 | 全 Agent 汇总 |
| GET | `/metrics/{agent_id}` | 用户 | 日指标 |
| POST | `/prompt-version` | admin | 创建 Prompt 版本 |
| GET | `/prompt-versions/{agent_id}` | 用户 | 版本历史 |
| POST | `/aggregate` | admin | 手动触发聚合 |

---

## 第十二部分: Agent 生态市场 (Phase 5)

### 12.1 市场发布与安装

**文件**: `core/ecosystem_service.py`

```python
publish_to_marketplace(db, template_id, publisher_id, ...) → Listing (status=submitted)
approve_listing(db, listing_id, reviewer_id) → status=published
install_template(db, listing_id, installer_id, target_tenant_id)
    # 克隆模板 → 新 agent_id (递增后缀) → install_count++
```

### 12.2 Agent 组合

```python
create_composition(db, name, pipeline, created_by, merge_strategy)
# pipeline: [{"agent_id": "glucose", "order": 1, "condition": "always"}, ...]
# merge_strategy: weighted_average / priority_first / consensus
```

### 12.3 成长积分 (7 事件)

| 事件 | 积分 |
|------|------|
| create_agent | 20 |
| optimize_prompt | 10 |
| share_knowledge | 15 |
| template_published | 30 |
| template_installed | 5 (每次) |
| feedback_positive | 3 |
| composition_created | 15 |

### 12.4 生态 API (12 端点)

**前缀**: `/api/v1/agent-ecosystem`

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| GET | `/marketplace` | 用户 | 浏览市场 |
| POST | `/marketplace/publish` | 用户 | 提交发布 |
| GET | `/marketplace/pending` | admin | 审核队列 |
| POST | `marketplace/{id}/approve` | admin | 批准 |
| POST | `marketplace/{id}/reject` | admin | 拒绝 |
| POST | `marketplace/{id}/install` | 用户 | 安装 (克隆) |
| GET | `marketplace/recommended` | 专家 | 领域推荐 |
| GET | `/compositions` | 用户 | 组合列表 |
| POST | `/compositions` | coach+ | 创建组合 |
| GET | `/compositions/{id}` | 用户 | 组合详情 |
| GET | `/growth-points` | 用户 | 我的积分 |
| GET | `/growth-points/config` | 用户 | 积分配置 |

---

## 第十三部分: 全部 API 端点

### 13.1 Agent 核心 API (7+3 端点)

**前缀**: `/api/v1/agent`

| 方法 | 路径 | 权限 | 功能 |
|------|------|------|------|
| GET | `/list` | 用户+租户 | Agent 列表 (模板缓存优先) |
| POST | `/run` | 用户+租户 | 执行 Agent (v6→v0→mock) |
| GET | `/pending-reviews` | 用户 | 待审核队列 |
| POST | `/feedback` | 用户 | 提交审核反馈 |
| GET | `/stats/{agent_id}` | 用户 | 执行统计 |
| GET | `/history` | 用户 | 执行历史 |
| GET | `/status` | 用户 | 系统状态 |
| POST | `/pending-reviews/inject` | 用户 | 测试注入 |
| POST | `/events/inject` | 用户 | 事件注入 |
| POST | `/content-governance/audit-log/inject` | 用户 | 审计注入 |

### 13.2 全平台 Agent 端点汇总

| 路由模块 | 前缀 | 端点数 | 职责 |
|----------|------|--------|------|
| agent_api | /v1/agent | 10 | 核心运行+审核+统计 |
| agent_template_api | /v1/agent-templates | 10 | 模板 CRUD |
| expert_agent_api | /v1/tenants/{tid}/my-agents | 6 | 专家自助 Agent |
| agent_feedback_api | /v1/agent-feedback | 8 | 反馈+指标+Prompt |
| agent_ecosystem_api | /v1/agent-ecosystem | 12 | 市场+组合+积分 |
| knowledge_sharing_api | /v1/knowledge-sharing | 9 | 知识共享 |
| policy_api | /v1/policy | 12 | 策略+规则+追踪+成本 |
| rx_routes | /v1/rx | 8 | 行为处方 |
| safety_api | /v1/safety | 8 | 安全管理 |
| **合计** | | **83 端点** | |

---

## 第十四部分: 前端管理页面

### 14.1 Admin Portal (6 个 Agent 页面)

#### AgentTemplateList.vue — 模板管理列表

- 分页表格 (20/页) + agent_type/is_enabled 过滤
- 操作: 编辑, 克隆 (弹窗输入新 ID), 删除 (仅自定义), 启用/禁用
- "刷新缓存" 按钮

#### AgentTemplateEdit.vue — 模板编辑表单

- 字段: agent_id, display_name, description, keywords (动态标签), system_prompt (6 行代码区), priority (0-10), base_weight (滑杆 0-1), enable_llm, correlations (多选), conflict_wins_over (多选)
- 元数据: agent_type 标签, is_preset 标签, 时间戳

#### AgentMarketplace.vue — 生态中心 (4 Tab)

- **Tab 1 模板市场**: 搜索+分类过滤, 安装按钮 (需 tenantId)
- **Tab 2 待审核**: Admin 审核队列 (approve/reject)
- **Tab 3 组合编排**: 多 Agent 流水线定义 (JSON 编辑器)
- **Tab 4 成长积分**: 积分统计卡 + 事件配置表

#### AgentGrowthReport.vue — 成长报告

- **概览**: 所有 Agent 指标表 (acceptance_rate 进度条, avg_rating 星级)
- **详情**: 天数选择 (7/30/90), 每日指标表, Prompt 版本时间线
- **反馈**: 分页列表 (feedback_type 彩色标签)

#### TenantRoutingConfig.vue — 租户路由配置

- **关键词**: 每 Agent 自定义关键词 + boost 滑杆 (1.0-3.0x)
- **关联网络**: 动态表单 (source → targets 多选)
- **冲突覆盖**: A vs B → winner 选择
- **回退 Agent**: 下拉选择 (默认 behavior_rx)
- **路由测试**: 输入消息 → 平台 vs 租户对比

#### ExpertAgentManage.vue — 专家 Agent 自助

- Agent 列表 (预设+自定义, 含 is_primary)
- 创建自定义 Agent 表单
- 路由测试面板

### 14.2 Admin Portal 路由

```
/admin/agent-templates           → AgentTemplateList
/admin/agent-templates/create    → AgentTemplateEdit (create)
/admin/agent-templates/edit/:id  → AgentTemplateEdit (edit)
/admin/tenant-routing/:tid       → TenantRoutingConfig
/admin/agent-ecosystem           → AgentMarketplace
/admin/agent-growth              → AgentGrowthReport
```

### 14.3 API 客户端

**文件**: `admin-portal/src/api/agent-template.ts`

提供 10 方法: list, presets, domains, get, create, update, delete, toggle, clone, refreshCache

### 14.4 H5 端

无 Agent 管理页面 — H5 专注用户端功能 (学习/对话/任务), Agent 管理仅在 Admin Portal。

---

## 第十五部分: 数据库模型总览

### 15.1 Agent 相关表 (26 表)

| 表 | 迁移 | 模块 | 关键列 |
|----|------|------|--------|
| `agent_templates` | 022 | V006 | agent_id UNIQUE, agent_type, keywords JSON, system_prompt, is_preset |
| `tenant_agent_mappings` | 023 扩展 | V006 P2 | tenant_id, agent_id, custom_keywords JSON, keyword_boost |
| `knowledge_contributions` | 024 | Phase 3 | document_id, tenant_id, domain_id, status |
| `agent_feedbacks` | 025 | Phase 4 | agent_id, feedback_type, rating, user_message, agent_response |
| `agent_metrics_daily` | 025 | Phase 4 | agent_id + metric_date UNIQUE, acceptance_rate, avg_rating |
| `agent_prompt_versions` | 025 | Phase 4 | agent_id + version UNIQUE, system_prompt, is_active, traffic_pct |
| `agent_marketplace_listings` | 026 | Phase 5 | template_id, status, install_count, avg_rating |
| `agent_compositions` | 026 | Phase 5 | pipeline JSON, merge_strategy |
| `agent_growth_points` | 026 | Phase 5 | user_id, event_type, points |
| `policy_rules` | 028 | V007 A | rule_name UNIQUE, condition_expr JSON-Logic, priority |
| `agent_applicability_matrix` | 028 | V007 A | agent_id, stage_range, risk_level, intensity_level |
| `conflict_matrix` | 028 | V007 A | agent_a_id, agent_b_id, resolution_strategy |
| `decision_trace` | 028 | V007 A | UUID PK, triggered_agents JSON, final_output, token_cost |
| `cost_budget_ledger` | 028 | V007 A | tenant_id, max_tokens, used_tokens, overflow_action |
| `expert_domain` | 029 | V007 B | agent_id, domain_name, authority_level |
| `intervention_protocol` | 029 | V007 B | agent_id, trigger_condition JSON, intensity_range |
| `risk_boundary` | 029 | V007 B | agent_id, max_risk_level, auto_exit_condition JSON |
| `stage_applicability` | 029 | V007 B | agent_id + stage_code, effectiveness_score |
| `contraindications` | 029 | V007 B | agent_id, condition_type, severity (warning/block) |
| `evidence_tier_binding` | 029 | V007 B | agent_id, evidence_tier |
| `agent_skill_graph` | 029 | V007 B | agent_id UNIQUE, skill_vector JSON |
| `policy_intervention_outcome` | 029 | V007 B | user_id, agent_id, ies_score, stage_before/after |
| `policy_stage_transition_log` | 029 | V007 B | user_id, from_stage, to_stage, trigger_agent_id |
| `rx_prescriptions` | 030 | Rx | UUID PK, 25 列, TTM+BigFive+Capacity→处方 |
| `rx_strategy_templates` | 030 | Rx | UUID PK, 21 列, 12 策略模板 |
| `agent_handoff_log` | 030 | Rx | UUID PK, 16 列, from/to Agent 交接日志 |

### 15.2 关键枚举

| 枚举 | 值 |
|------|-----|
| AgentType | specialist, integrative, dynamic_llm |
| FeedbackType | accept, reject, modify, rate |
| ListingStatus | draft, submitted, approved, rejected, published, archived |
| MergeStrategy | weighted_average, priority_first, consensus |
| RxStrategyType | 12 种 (consciousness_raising → self_monitoring) |
| RxIntensity | MINIMAL, LOW, MODERATE, HIGH, INTENSIVE |
| CommunicationStyle | EMPATHETIC, DATA_DRIVEN, EXPLORATORY, SOCIAL_PROOF, CHALLENGE, NEUTRAL |
| ExpertAgentType | BEHAVIOR_COACH, METABOLIC_EXPERT, CARDIAC_EXPERT, ADHERENCE_EXPERT |
| HandoffType | STAGE_PROMOTION, STAGE_REGRESSION, DOMAIN_COORDINATION, CROSS_CUTTING, EMERGENCY_TAKEOVER, SCHEDULED_HANDOFF |
| PolicyDecision | ALLOW, DELAY, ALLOW_SOFT_SUPPORT, ESCALATE_COACH, DENY |
| RiskLevel | LOW, MODERATE, HIGH, CRITICAL |

---

## 第十六部分: 配置文件

### 16.1 Agent 模板种子

**文件**: `configs/agent_templates_seed.json` — 12 预设 Agent 完整定义

### 16.2 行为策略

**文件**: `configs/rx_strategies.json` — 12 循证行为改变策略 (TTM/SESMOA)
- 每策略含: 适用阶段范围, 核心机制, 默认微行动, 人格修正器, 领域变体

### 16.3 安全关键词

**文件**: `configs/safety_keywords.json` — 4 类 49 个关键词 (crisis/warning/blocked/medical_advice)

### 16.4 安全规则

**文件**: `configs/safety_rules.json` — 阈值, 证据权重 (T1=1.0→T4=0.2), 严重级别动作

---

## 第十七部分: 迁移记录

| 迁移号 | 表数 | 内容 |
|--------|------|------|
| 022 | 1 | agent_templates (V006 P1) |
| 023 | 0 (列扩展) | expert_tenants + tenant_agent_mappings 路由列 (V006 P2) |
| 024 | 1 | knowledge_contributions (Phase 3) |
| 025 | 3 | agent_feedbacks + agent_metrics_daily + agent_prompt_versions (Phase 4) |
| 026 | 3 | agent_marketplace_listings + agent_compositions + agent_growth_points (Phase 5) |
| 028 | 6 | policy_rules + applicability_matrix + conflict_matrix + decision_trace + cost_budget + rule_priority (V007 A) |
| 029 | 9 | expert_domain + intervention_protocol + risk_boundary + stage_applicability + contraindications + evidence_tier_binding + agent_skill_graph + policy_intervention_outcome + policy_stage_transition_log (V007 B) |
| 030 | 3 | rx_prescriptions + rx_strategy_templates + agent_handoff_log (Behavior Rx) |
| **合计** | **26 表** | |

---

## 附录: 数据流与集成图谱

### A.1 Agent 运行时完整流程

```
用户消息 → /api/v1/agent/run
    ↓
resolve_tenant_ctx(user) → tenant_id/enabled_agents/keywords
    ↓
v6 MasterAgent.process():
    │
    ├─ Step 2.5: SafetyPipeline.process_input()
    │   └─ crisis → 直接返回危机模板
    │   └─ blocked → 拒绝
    │
    ├─ Step 3.5: ExpertAgentRouter.should_route_to_expert()
    │   └─ 匹配 → CollaborationOrchestrator.orchestrate()
    │       ├─ identify_scenario() → 8 场景
    │       ├─ 主 Agent.process() → RxPrescription
    │       ├─ 辅 Agent.process() → 叠加内容
    │       └─ _merge_responses() → MergedResponse
    │
    ├─ Step 4: PolicyEngine.evaluate() (可选)
    │   ├─ RuleRegistry 规则匹配
    │   ├─ ApplicabilityMatrix 候选
    │   ├─ ConflictResolver 仲裁
    │   ├─ CostController 预算
    │   └─ DecisionTrace 记录
    │   或
    │   AgentRouter.route() (标准路由)
    │       ├─ 关键词匹配 + 权重
    │       ├─ 设备数据 + 用户偏好
    │       └─ 域关联扩展
    │
    ├─ Step 5: Agent.process() → AgentResult
    │   └─ _enhance_with_llm() → UnifiedLLMClient
    │       ├─ cloud_first: DeepSeek/Qwen/GPT
    │       └─ fallback: Ollama qwen2.5:0.5b
    │
    ├─ Step 6: Coordinator.coordinate()
    │   └─ 冲突解决 + 建议排序 + 共识提取
    │
    ├─ Step 7: PolicyGate.evaluate()
    │   └─ 阶段门控 + dropout/relapse 检测
    │
    ├─ Step 7.5: SafetyPipeline.guard_generation()
    │   └─ 安全约束注入 system_prompt
    │
    ├─ Step 8: 响应综合
    │   ├─ LLM 综合 (SYNTHESIS_SYSTEM_PROMPT)
    │   └─ 模板综合 (回退)
    │
    └─ Step 8.5: SafetyPipeline.filter_output()
        └─ 医嘱/绝对承诺检测 + 免责附加
    ↓
记录执行历史 + 返回响应
```

### A.2 模板生命周期

```
Admin 创建模板 → agent_templates (is_preset=false, dynamic_llm)
    ↓
Admin 发布到市场 → marketplace_listing (status=submitted)
    ↓
Admin 审核 → approved/rejected
    ↓
专家安装 → 克隆模板 → TenantAgentMapping → install_count++
    ↓
专家自定义关键词/prompt → tenant routing override
    ↓
用户对话 → v6 MasterAgent 使用模板 Agent
    ↓
用户反馈 → agent_feedbacks → 每日聚合 → AgentMetricsDaily
    ↓
Admin 优化 Prompt → agent_prompt_versions (A/B 测试)
    ↓
成长积分 → agent_growth_points → 六级晋升
```

### A.3 行为处方数据流

```
用户画像 (TTM 阶段 + BigFive + 能力分数)
    ↓
BehaviorRxEngine.compute_rx()
    ├─ 策略选择 (12 策略 × 阶段 × 人格 × 障碍)
    ├─ 微行动生成 (能力系数调整)
    ├─ 奖励触发 (人格适配)
    └─ 升级规则 (Agent 特定)
    ↓
RxPrescription (处方记录)
    ↓
领域 Agent 包装 (冰山模型: 用户看专业建议, 隐藏处方)
    ↓
效果评估: IES = completion + duration + stage_change - resistance
    ↓
IES < 0.4 → 切换策略 / 交接 Agent
IES >= 0.7 → 继续当前处方
```

### A.4 安全-策略-成本联动

```
用户消息
    ↓
SafetyPipeline L1 → crisis 检测
    ├─ crisis: CrisisAgent 强制 (PolicyEngine 规则 #1, priority=100)
    └─ normal: 继续
    ↓
PolicyEngine Step 1 → 匹配规则
    ├─ medical_boundary (p=95): 高风险+医疗域 → 医疗审核
    ├─ early_stage_gentle (p=60): S0/S1 → 限制强度
    └─ cost_daily_limit (p=70): token 使用≥90%
    ↓
CostController → 预算检查
    ├─ < 80%: 原始模型
    ├─ 80-100%: 降级 (deepseek-chat → qwen-turbo)
    └─ ≥ 100%: 阻止/降到 ollama-local
    ↓
DecisionTrace → UUID 记录全过程
    → 可解释 AI: "触发 N 候选, 匹配 M 规则, 策略 X, 最终 Agent Y"
```

---

> **文档覆盖**: 16+ Agent 实例, 26 数据库表, 83 API 端点, 6 Admin 页面, 8 迁移,
> 4 配置文件, 5 步策略流水线, 4 层安全流水线, 12 行为策略, 8 协作场景
> **生成日期**: 2026-02-14
> **项目位置**: `D:\behavioral-health-project`

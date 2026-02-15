# 平台改进规划方案 v1

> 日期：2026-02-14
> 来源：Agent架构审计 + 用户角色互动分析 综合提炼
> 共计 **15 项改进**，按优先级 P0→P4 排列

---

## 目录

1. [优先级总览](#1-优先级总览)
2. [P0 — 立即执行（1周内）](#2-p0--立即执行1周内)
3. [P1 — 高优先（2周内）](#3-p1--高优先2周内)
4. [P2 — 中优先（1个月内）](#4-p2--中优先1个月内)
5. [P3 — 改善项（2个月内）](#5-p3--改善项2个月内)
6. [P4 — 长期演进](#6-p4--长期演进)
7. [实施依赖关系](#7-实施依赖关系)
8. [风险评估](#8-风险评估)

---

## 1. 优先级总览

| # | 优先级 | 改进项 | 来源 | 影响范围 | 工作量 |
|---|--------|-------|------|---------|--------|
| 1 | **P0** | RBAC 权限体系细化 | 角色分析 | 全平台安全 | 中 |
| 2 | **P0** | Agent 路由关键词扩充 | Agent审计 | 用户体验 | 小 |
| 3 | **P1** | Agent System Prompt 差异化 | Agent审计 | 回复质量 | 小 |
| 4 | **P1** | 核心Agent/专家Agent边界规则 | Agent审计 | 建议一致性 | 中 |
| 5 | **P1** | observer→grower 激活流程 | 角色分析 | 新用户留存 | 小 |
| 6 | **P1** | 教练消息双向通信 | 角色分析 | 教练-学员互动 | 中 |
| 7 | **P1** | 同道者带教自动化评估 | 角色分析 | 晋级公平性 | 中 |
| 8 | **P2** | 双MasterAgent统一 | Agent审计 | 代码维护性 | 中 |
| 9 | **P2** | TTM阶段数据源统一 | Agent审计 | 阶段判断一致 | 中 |
| 10 | **P2** | promoter/supervisor角色分化 | 角色分析 | 角色定位 | 小 |
| 11 | **P2** | 专家入驻与六级体系互通 | 角色分析 | 体系完整性 | 中 |
| 12 | **P2** | 学员分配关系明确化 | 角色分析 | 教练管理 | 中 |
| 13 | **P3** | 核心Agent引入策略上下文 | Agent审计 | 建议科学性 | 中 |
| 14 | **P3** | 内容访问角色分级 | 角色分析 | 内容运营 | 中 |
| 15 | **P3** | 统一通知中枢 | 角色分析 | 用户体验 | 大 |
| — | **P4** | Agent市场预填充+预设组合 | Agent审计 | 生态激活 | 小 |
| — | **P4** | Agent路由语义匹配 | Agent审计 | 路由精度 | 大 |

---

## 2. P0 — 立即执行（1周内）

### 2.1 RBAC 权限体系细化

**问题**：平台定义了 8 个角色层级（observer→admin），但 `api/dependencies.py` 只有 3 级守卫：
- `get_current_user` — 任意认证用户
- `require_coach_or_admin` — coach/promoter/supervisor/master/admin
- `require_admin` — 仅 admin

中间角色（sharer/promoter/supervisor/master）在 API 层面与相邻角色无任何权限区别。observer 与 grower 也无后端拦截区分。

**影响**：
- observer 用户可调用 grower 级 API（AI 对话、设备绑定、评估等）
- sharer 无独有权限端点（内容贡献端点未显式校验角色）
- promoter/supervisor/master 功能完全等价于 coach

**改进方案**：

在 `api/dependencies.py` 新增通用角色级别守卫：

```python
from core.models import ROLE_LEVEL

def require_role_level(min_level: int):
    """
    通用角色等级守卫工厂
    用法: require_grower = require_role_level(2)
          require_sharer = require_role_level(3)
    """
    def _guard(current_user: User = Depends(get_current_user)) -> User:
        user_role = current_user.role
        level = ROLE_LEVEL.get(user_role, 0)
        if level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要L{min_level - 1}及以上权限"
            )
        return current_user
    return _guard

# 预定义常用守卫
require_grower = require_role_level(2)       # L1+
require_sharer = require_role_level(3)       # L2+
require_coach = require_role_level(4)        # L3+
require_promoter = require_role_level(5)     # L4+
require_master = require_role_level(6)       # L5+
```

**关键端点应用**：

| 端点 | 当前守卫 | 建议守卫 |
|------|---------|---------|
| POST /agent/run | get_current_user | require_grower |
| POST /assessment/submit | get_current_user | require_grower |
| POST /programs/enroll | get_current_user | require_grower |
| POST /micro-actions/*/complete | get_current_user | require_grower |
| POST /contributions/submit | get_current_user | require_sharer |
| POST /companions/invite | require_coach_or_admin | require_coach |

**涉及文件**：`api/dependencies.py`（+15行），各 API 文件仅改 Depends 参数

---

### 2.2 Agent 路由关键词扩充

**问题**：AgentRouter 使用 `keyword in message` 完全匹配，关键词覆盖不足，口语化/近义词表达无法命中。

**影响**：用户说"我最近吃太多了"不会匹配 nutrition Agent 的关键词"饮食"。

**改进方案**：

扩充每个 Agent 的关键词表，增加同义词、口语、场景词：

| Agent | 当前关键词数 | 建议补充示例 |
|-------|------------|------------|
| nutrition | 8 | +吃多了/暴饮暴食/外卖/零食/奶茶/早午晚餐/宵夜/GI/升糖指数/膳食纤维/维生素 |
| sleep | 6 | +失眠/多梦/夜醒/打鼾/午睡/赖床/起不来/嗜睡/睡太晚/熬夜/黑眼圈 |
| exercise | 7 | +散步/跑步/游泳/瑜伽/骑车/爬楼/久坐/不爱动/没时间运动/步数/体能 |
| emotion | 6 | +烦躁/生气/难过/想哭/崩溃/孤独/无聊/暴躁/委屈/不开心/心情差 |
| stress | 5 | +焦虑/紧张/压力大/累/工作忙/加班/失眠/头疼/心慌/喘不过气 |
| motivation | 5 | +不想动/坚持不了/三分钟热度/放弃了/没动力/犯懒/拖延/回避 |
| glucose | 7 | +血糖高/低血糖/头晕/空腹/餐后/测血糖/打胰岛素/糖化/控糖 |
| tcm | 5 | +上火/湿气/气血/调理/食疗/养生茶/泡脚/刮痧/拔罐/穴位/体质 |
| mental | 5 | +抑郁/焦虑症/恐慌/社恐/强迫/PTSD/心理咨询/心理医生/吃药 |

**涉及文件**：
- `core/agents/specialist_agents.py` — 9 个 Agent 的 `keywords` 列表
- `core/agents/integrative_agents.py` — 3 个 Agent 的 `keywords` 列表
- 或迁移到 `configs/agent_keywords.json` 使后续维护更灵活

---

## 3. P1 — 高优先（2周内）

### 3.1 Agent System Prompt 差异化

**问题**：12 个核心 Agent 的 system_prompt 格式完全相同：
> 你是一位[职位]，擅长[领域]。根据用户的[数据]，给出[建议]。回复控制在3-5条建议，每条不超过30字。只输出建议列表，不要寒暄。

**影响**：所有 Agent 回复风格雷同，用户无法感知不同"专家"的差异。

**改进方案**：

为每个 Agent 定义差异化回复风格：

| Agent | 风格 | Prompt 调整要点 |
|-------|------|----------------|
| crisis | 紧急、简短、指令式 | 1-2条立即行动指示，明确求助电话，禁止冗长 |
| emotion | 共情、温暖、倾听式 | 先共情再建议，使用"我理解你的感受"类表达 |
| tcm | 温和、养生、文化式 | 引用传统养生智慧，使用四季/体质/食疗语言 |
| nutrition | 实用、具体、方案式 | 给出具体食物推荐+份量，可包含简单食谱 |
| exercise | 激励、渐进、安全式 | 强调循序渐进，标注运动强度，提醒安全注意 |
| mental | 专业、尊重、引导式 | 使用心理学术语但通俗化，引导自我觉察 |
| sleep | 舒缓、规律、科学式 | 强调昼夜节律，提供具体入睡技巧 |
| glucose | 精确、数据、监控式 | 关联血糖数值，给出具体时间点建议 |
| motivation | 鼓励、目标、进步式 | 使用小目标拆解，强调已有进步 |
| stress | 放松、减压、调节式 | 提供即时减压技巧（呼吸/冥想/活动） |
| behavior_rx | 系统、策略、阶段式 | 按行为阶段给出策略性建议，有长期规划感 |
| weight/cardiac_rehab | 综合、协调、整体式 | 跨领域建议整合，标注各领域联动 |

**回复长度也应差异化**：

```python
AGENT_REPLY_CONFIG = {
    "crisis":       {"max_items": 2, "max_chars": 50, "tone": "urgent"},
    "emotion":      {"max_items": 4, "max_chars": 60, "tone": "empathetic"},
    "nutrition":    {"max_items": 5, "max_chars": 80, "tone": "practical"},
    "glucose":      {"max_items": 4, "max_chars": 50, "tone": "precise"},
    # ...
}
```

**涉及文件**：`core/agents/specialist_agents.py`，`core/agents/integrative_agents.py`

---

### 3.2 核心Agent / 专家Agent 边界规则

**问题**：`BehaviorRxAgent`(核心层) 与 `BehaviorCoachAgent`(专家层) 在行为处方领域高度重叠。`CardiacRehabAgent`(核心层) 与 `CardiacExpertAgent`(专家层) 在心脏康复领域高度重叠。

**影响**：用户可能同时被两套系统处理同一问题，产生矛盾建议。

**改进方案（推荐方案 C：分层协作）**：

```
用户消息 → MasterAgent
  ├── Step 3.5: 专家Agent路由器判断
  │   ├── 有 TTM 数据 / 有 BehaviorRx 上下文 → 走专家层（深度干预）
  │   └── 无上下文 → 走核心层（快速响应）
  ├── 核心层职责: 即时响应
  │   ├── 设备异常提醒（血糖高了、心率异常等）
  │   ├── 简单生活建议（≤5条，不涉及行为策略术语）
  │   └── 危机干预（crisis Agent 始终在核心层）
  └── 专家层职责: 深度干预
      ├── 行为处方计算（TTM×BigFive×CAPACITY）
      ├── 策略选择（12种行为策略）
      └── 交接管理（agent handoff）
```

**边界判断逻辑**（建议加入 `MasterAgent.process()` Step 3.5）：

```python
def _should_use_expert_layer(self, user_id, message, context):
    """判断是否应使用专家层而非核心层"""
    # 1. 用户已有行为处方记录 → 专家层
    if has_active_prescription(user_id):
        return True
    # 2. 消息包含阶段性/策略性内容 → 专家层
    if any(kw in message for kw in ["阶段", "策略", "处方", "计划", "坚持不了"]):
        return True
    # 3. 用户有 TTM 阶段评估数据 → 专家层
    if user_has_ttm_stage(user_id):
        return True
    return False  # 默认核心层
```

**涉及文件**：`core/agents/master_agent.py`（+20行边界判断）

---

### 3.3 observer → grower 激活流程

**问题**：注册默认角色为 observer，但升级到 grower 的触发条件和流程不明确。

**改进方案**：

定义明确的激活条件：
1. 完成新手引导（阅读平台协议 + 填写基础健康信息）
2. 首次完成一份基础评估问卷

```
新注册 → OBSERVER (L0)
    │
    ├── 阅读并同意用户协议 ✓
    ├── 填写基础健康信息 ✓
    └── 完成首份评估 ✓
    │
    ▼ 自动升级
  GROWER (L1)
    │
    ▼ 解锁: AI对话/设备绑定/微行动/方案参与
```

**新增端点**：
```
POST /api/v1/auth/activate
  - 检查三项条件
  - 满足则 user.role = UserRole.GROWER
  - 返回新 token (含更新后的角色)
```

**涉及文件**：
- `api/auth_api.py` — 新增 `/activate` 端点
- H5 端 — 新增激活引导页面

---

### 3.4 教练消息双向通信

**问题**：`coach_message_api.py` 只支持 coach→grower 单向发送。

**改进方案**：

| 方案 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| A. 扩展现有消息API | 增加 grower→coach 回复端点 | 改动最小 | 与 chat 系统重复 |
| **B. 整合到对话系统(推荐)** | 复用 chat_rest_api 增加 coach 通道 | 统一消息体验 | 需改造 chat UI |
| C. 引入独立IM模块 | 接入 WebSocket 实时通信 | 体验最好 | 工作量大 |

**推荐方案 B 实施要点**：
1. `ChatSession` 增加 `session_type` 字段（`ai` / `coach` / `group`）
2. coach 类型 session 不经过 Agent 管线，直接存储消息
3. H5 对话列表展示 AI 对话和教练对话
4. 消息增加已读/未读状态（`read_at` 字段）

**涉及文件**：`core/models.py`（ChatSession +1字段），`api/chat_rest_api.py`（+教练通道逻辑）

---

### 3.5 同道者带教自动化评估

**问题**：`CompanionRelation` 的 `quality_score` 和毕业判定依赖手动操作。

**改进方案**：

定义可量化的毕业标准：

```python
GRADUATION_CRITERIA = {
    "grower_to_sharer": {  # L1→L2 毕业标准
        "min_growth_points": 500,
        "min_active_days": 30,
        "min_interactions_with_mentor": 10,
    },
    "sharer_to_coach": {  # L2→L3 毕业标准
        "min_growth_points": 800,
        "min_contribution_points": 200,
        "min_active_days": 60,
        "exam_passed": True,
    },
    "coach_to_promoter": {  # L3→L4 毕业标准
        "min_growth_points": 1500,
        "min_contribution_points": 600,
        "min_active_days": 90,
        "exam_passed": True,
    },
}
```

**自动毕业定时任务**（加入 `core/scheduler.py`）：
```python
@scheduler.scheduled_job("cron", hour=3, minute=0, id="companion_auto_graduate")
@with_redis_lock("companion_auto_graduate", ttl=300)
async def auto_graduate_companions():
    """每日检查同道者是否达到毕业标准"""
    # 查询所有 active 同道者关系
    # 检查 mentee 的积分/活跃天数/互动次数
    # 达标 → status='graduated' + 通知 mentor
```

**影响力积分联动**：mentor 每成功毕业一名同道者 → +50 影响力积分。

**涉及文件**：
- `core/companion_service.py`（新建，毕业检查逻辑）
- `core/scheduler.py`（+1 定时任务）
- `api/companion_api.py`（毕业结果通知）

---

## 4. P2 — 中优先（1个月内）

### 4.1 双 MasterAgent 统一

**问题**：
- `core/master_agent_v0.py`（v0，原始 9 步编排）
- `core/agents/master_agent.py`（v6，模板+租户+PolicyEngine+Safety）
- `core/master_agent.py` 仅 `from core.master_agent_v0 import *`（桥接）
- API 层使用 v6→v0 兜底→mock 三级回退

**改进方案**：

```
阶段 1（当前）: 保持 v6 → v0 兜底，标记 v0 为 @deprecated
阶段 2（测试确认）: v0 → test-only，生产不再加载
阶段 3（清理）:
  - 删除 core/master_agent_v0.py
  - core/master_agent.py 改为 re-export core/agents/master_agent.py
  - api/main.py 统一为一个 get_master_agent()
```

**前提条件**：v6 MasterAgent 通过完整回归测试（98 tests + 14 endpoint tests）。

**涉及文件**：`core/master_agent_v0.py`（废弃），`core/master_agent.py`（改为桥接），`api/main.py`（统一入口）

---

### 4.2 TTM 阶段数据源统一

**问题**：
- 核心层用 `stage_aware_selector.py`（查询 `StageApplicability` 表）
- 专家层用 `behavior_rx_engine.py`（内置 TTM×BigFive×CAPACITY 矩阵）
- 两套系统阶段评估逻辑完全独立

**改进方案**（3步实施）：

```
Step 1: 统一数据源
  └── User 表 or UserProfile 增加 ttm_stage 字段
  └── 每次评估/处方计算后更新此字段
  └── 核心层和专家层都从此字段读取

Step 2: 统一强度映射
  └── 建立全局 STAGE_INTENSITY_MAP:
      S0(前意向) → intensity=0.2, style=awareness
      S1(意向)   → intensity=0.4, style=exploration
      S2(准备)   → intensity=0.6, style=planning
      S3(行动)   → intensity=0.8, style=action
      S4(维持)   → intensity=0.7, style=maintenance
      S5(终止)   → intensity=0.3, style=celebration

Step 3: 确立权威
  └── 如用户有 BehaviorRx 处方 → 专家层评估为权威
  └── 如无处方 → 核心层评估为参考
```

**涉及文件**：
- `core/models.py`（User +`ttm_stage` 字段）
- `core/stage_aware_selector.py`（读取统一字段）
- `behavior_rx/behavior_rx_engine.py`（写入统一字段）
- 新 migration 文件

---

### 4.3 promoter / supervisor 角色分化

**问题**：两者均为 L4（ROLE_LEVEL=5），代码中无任何差异化处理。

**改进方案**：

| 方向 | 方案 | 描述 |
|------|------|------|
| **A. 明确分工** | promoter = 推广 + 团队带领 | 侧重新用户发展、团队管理、内容传播 |
| | supervisor = 质量 + 专业督导 | 侧重教练质量评估、案例督导、安全审核 |
| **B. 合并(推荐)** | 统一为 promoter 或 senior_coach | 减少概念复杂度，一个 L4 角色足够 |

**如选方案 A，需新增功能差异**：

```
PROMOTER 独有功能:
  - GET /promoter/team-stats      # 团队业绩统计
  - POST /promoter/recruit-event  # 发起招募活动
  - 内容传播加成（分享内容 +2x 影响力积分）

SUPERVISOR 独有功能:
  - GET /supervisor/case-review    # 案例督导队列
  - POST /supervisor/quality-audit # 教练质量评审
  - 安全审核协助权限（不需要 admin 全权限）
```

**涉及文件**：
- 方案 A：新增 `api/promoter_api.py` + `api/supervisor_api.py`
- 方案 B：`core/models.py`（删除一个枚举值），全局替换

---

### 4.4 专家入驻与六级体系互通

**问题**：专家入驻从 grower+ 直接升级 coach，跳过积分和同道者要求，两套体系平行不互通。

**改进方案**：

```
方案 A: 入驻独立（当前状态，文档化即可）
  - 明确文档：专家入驻是"专业认证路径"，不走积分晋级
  - 入驻后的 coach 仍受六级体系约束（L3 起步，继续积分升级到 L4/L5）
  - 专家入驻不授予同道者带教资格（需另外满足条件）

方案 B: 入驻=加速（推荐）
  - 专家入驻审核通过 → 角色升级 coach + 赠送初始积分（growth=800, contribution=200, influence=50）
  - 这样专家正好达到 L3 门槛
  - 后续仍需通过积分体系升级到 L4/L5
  - 同道者要求同样适用
```

**涉及文件**：
- 入驻审核端点（`api/expert_registration`）— 批准时赠送积分
- `core/learning_service.py` — 积分赠送逻辑

---

### 4.5 学员分配关系明确化

**问题**：coach-grower 的"分配关系"定义不清，可能依赖 `referred_by` 或 `TenantClient` 或 `CompanionRelation`。

**改进方案**：

```
方案 A: 复用 CompanionRelation（推荐）
  - CompanionRelation 已有 mentor_id / mentee_id / status / mentor_role
  - coach_api.py 的学员列表查询改为:
    SELECT * FROM companion_relations
    WHERE mentor_id = :coach_id AND status = 'active'
  - 好处: 统一关系模型，同道者=学员

方案 B: 新建 coach_assignment 表
  - 支持一学员多教练（主教练+专项教练）
  - 更灵活但增加复杂度
```

**涉及文件**：`api/coach_api.py`（学员查询逻辑）

---

## 5. P3 — 改善项（2个月内）

### 5.1 核心Agent引入策略上下文

**问题**：12 种行为策略（consciousness_raising, stimulus_control 等）仅在 BehaviorRx 包中使用，核心 Agent 的建议缺乏行为科学支撑。

**改进方案**（渐进式）：

```
Phase 1 — Prompt 注入:
  核心 Agent 的 system_prompt 增加策略提示:
  "当用户处于意向前期(S0)时，使用意识提升策略，帮助用户认识到改变的必要性"

Phase 2 — 字段传递:
  BaseAgent 增加 strategy_hint 字段
  从 BehaviorRx 的策略模板读取，传递给核心 Agent

Phase 3 — 参数化:
  核心 Agent 的 process() 接受 active_strategy 参数
  根据策略类型调整建议的措辞和方向
```

**涉及文件**：
- `core/agents/base.py`（BaseAgent +`strategy_hint`）
- 各 specialist Agent 的 `system_prompt`（+策略上下文）

---

### 5.2 内容访问角色分级

**问题**：`content_api.py` 的 28 个端点仅要求 `get_current_user`，无角色级别限制。

**改进方案**：

`ContentItem` 增加 `min_role_level` 字段（默认=1，任何认证用户可见）：

```python
# content_api.py 列表查询增加过滤
@router.get("/list")
def list_content(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_level = ROLE_LEVEL.get(current_user.role, 1)
    query = db.query(ContentItem).filter(
        ContentItem.min_role_level <= user_level
    )
    ...
```

**分级建议**：

| 内容类型 | min_role_level | 可见范围 |
|---------|---------------|---------|
| 公开科普文章 | 1 (L0) | 所有用户 |
| 互动课程 | 2 (L1) | grower+ |
| 教练专属教材 | 4 (L3) | coach+ |
| 大师案例研讨 | 6 (L5) | master+ |
| 管理后台教程 | 99 | admin |

**涉及文件**：
- `core/models.py`（ContentItem +`min_role_level`）
- `api/content_api.py`（列表/详情增加过滤）
- 新 migration 文件

---

### 5.3 统一通知中枢

**问题**：通知散布在各 API 中（设备警报、消息、审核、晋级），无统一的通知服务。

**改进方案**：

```python
# core/notification_service.py (新建)

class NotificationService:
    """统一通知中枢"""

    CHANNELS = ["in_app", "push", "sms", "email"]

    async def notify(self, user_id, event_type, payload, channels=None):
        """
        event_type: alert | message | review | promotion | system
        channels: 默认 ["in_app"]
        """
        notification = Notification(
            user_id=user_id,
            event_type=event_type,
            title=self._get_title(event_type, payload),
            body=self._get_body(event_type, payload),
            read=False,
            created_at=datetime.utcnow(),
        )
        db.add(notification)

        for channel in (channels or ["in_app"]):
            await self._dispatch(channel, user_id, notification)
```

**新增表**：`notifications`（id, user_id, event_type, title, body, read, channel, created_at, read_at）

**新增端点**：
```
GET    /api/v1/notifications            # 我的通知列表
GET    /api/v1/notifications/unread-count # 未读数
POST   /api/v1/notifications/{id}/read   # 标记已读
POST   /api/v1/notifications/read-all    # 全部已读
```

**接入点**（现有代码调用 `notification_service.notify()`）：

| 事件 | event_type | 通知对象 |
|------|-----------|---------|
| 设备警报 | alert | coach |
| 教练消息 | message | grower |
| 评估完成 | review | coach |
| 晋级审批结果 | promotion | 申请人 |
| 入驻审批结果 | system | 申请人 |
| 挑战推送 | message | grower |
| 同道者毕业 | system | mentor + mentee |

**涉及文件**：
- `core/notification_service.py`（新建）
- `core/models.py`（+Notification 模型）
- `api/notification_api.py`（新建，4 端点）
- 各现有 API 文件（调用 notify）

---

## 6. P4 — 长期演进

### 6.1 Agent 市场预填充 + 预设组合

**现状**：市场/组合/积分框架已就绪但无内容。

**行动项**：
1. 将 12 个预设 Agent 发布为市场商品
2. 创建 3-5 个预设组合：
   - 糖尿病全套: glucose + nutrition + exercise
   - 心理健康套装: mental + stress + sleep + emotion
   - 体重管理套装: weight + nutrition + exercise + motivation
   - 心脏康复套装: cardiac_rehab + exercise + nutrition + stress
3. 定义积分消费场景：高级 Agent 访问、优先路由、定制 Prompt

---

### 6.2 Agent 路由语义匹配（中长期）

**当前**：关键词完全匹配。

**演进路径**：

```
Phase 1 (已有): keyword in message 完全匹配
Phase 2 (中期): embedding 语义匹配
  - user_message → text2vec-base-chinese → 768维向量
  - 每个 Agent 的关键词 → 预计算平均向量
  - cosine_similarity > 0.6 → 命中
  - 复用已有 embedding_service

Phase 3 (长期): LLM 意图分类
  - 用 qwen2.5:0.5b 做 intent classification
  - 输入: user_message
  - 输出: {intent: "nutrition", confidence: 0.85}
  - 需要标注数据 + 微调
```

---

## 7. 实施依赖关系

```
P0-1 RBAC细化 ─────────────────────┐
                                    │
P0-2 关键词扩充 ─── (无依赖) ──┐    │
                               │    │
P1-1 Prompt差异化 ─ (无依赖) ──┤    │
                               │    │
P1-2 核心/专家边界 ────────────┤    │
         │                     │    │
P1-3 激活流程 ────── (依赖P0-1)┘    │
                                    │
P1-4 消息双向 ────── (无依赖)       │
                                    │
P1-5 同道者自动化 ── (无依赖)       │
                                    │
P2-1 MasterAgent统一 ── (依赖P1-2)  │
         │                          │
P2-2 TTM统一 ──────── (依赖P1-2)    │
                                    │
P2-3 角色分化 ─────── (依赖P0-1) ───┘
         │
P2-4 入驻互通 ─────── (依赖P1-5)
         │
P2-5 学员分配 ─────── (依赖P1-5)

P3-1 策略上下文 ──── (依赖P2-2)
P3-2 内容分级 ─────── (依赖P0-1)
P3-3 通知中枢 ─────── (无依赖，但建议在P1-4之后)

P4-1 市场填充 ─────── (无依赖)
P4-2 语义路由 ─────── (依赖P0-2完成后评估效果)
```

---

## 8. 风险评估

### 高风险项

| 改进项 | 风险 | 缓解措施 |
|-------|------|---------|
| P0-1 RBAC | 可能阻断现有用户访问 | 灰度发布：先 observer 拦截，再逐步收紧 |
| P1-2 核心/专家边界 | 边界判断不准确导致路由错误 | 新增 A/B 测试：50%用户走新边界，50%保持现状 |
| P2-1 MasterAgent统一 | 废弃 v0 后无兜底 | 保留 v0 代码 3 个月再物理删除 |
| P2-2 TTM统一 | 阶段评估结果变化 | 新旧阶段并行记录 1 个月，对比验证 |

### 低风险项

| 改进项 | 说明 |
|-------|------|
| P0-2 关键词扩充 | 纯添加，不影响现有匹配 |
| P1-1 Prompt差异化 | 仅改文本，可随时回退 |
| P1-3 激活流程 | 新增端点，不影响现有逻辑 |
| P3-3 通知中枢 | 独立新增模块，不影响现有 API |
| P4-1 市场填充 | 纯数据写入，无代码风险 |

---

## 附录：相关文档索引

| 文档 | 路径 | 内容 |
|------|------|------|
| Agent架构审计 | `docs/agent-architecture-audit-v1.md` | 17个Agent详细规格 + 7个问题诊断 |
| 用户角色互动图谱 | `docs/user-role-interaction-map-v1.md` | 8角色权限矩阵 + 互动流程 + 8个问题 |
| 平台架构概览 | `docs/platform-architecture-overview-v34-20260214.md` | 全局架构 |
| Agent系统架构 | `docs/platform-agent-system-architecture-20260214.md` | Agent 技术细节 |
| 行为处方核心逻辑 | `docs/behavioral-prescription-core-logic-supplemented.md` | BehaviorRx 冰山模型 |

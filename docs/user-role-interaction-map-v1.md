# 用户角色互动关系全景图 v1

> 生成日期：2026-02-14
> 覆盖范围：8 角色 × 519+ 端点 × 119 ORM 模型

---

## 目录

1. [角色层级总览](#1-角色层级总览)
2. [角色权限矩阵](#2-角色权限矩阵)
3. [核心互动关系图谱](#3-核心互动关系图谱)
4. [角色晋级流转](#4-角色晋级流转)
5. [教练 ↔ 成长者互动](#5-教练--成长者互动)
6. [专家 ↔ 租户 ↔ 客户三角](#6-专家--租户--客户三角)
7. [内容与社交互动](#7-内容与社交互动)
8. [AI Agent 服务边界](#8-ai-agent-服务边界)
9. [现存问题与建议](#9-现存问题与建议)

---

## 1. 角色层级总览

```
L99  ┌──────────┐
     │  admin   │  系统管理员 — 全局管控
     └──────────┘
L5   ┌──────────┐
     │  master  │  行为健康促进大师
     └──────────┘
L4   ┌──────────┬──────────┐
     │ promoter │supervisor│  促进师 / 督导（平级平权）
     └──────────┴──────────┘
L3   ┌──────────┐
     │  coach   │  行为健康教练
     └──────────┘
L2   ┌──────────┐
     │  sharer  │  分享者
     └──────────┘
L1   ┌──────────┐
     │  grower  │  成长者（原患者）
     └──────────┘
L0   ┌──────────┐
     │ observer │  观察员（新注册默认）
     └──────────┘
```

### 角色定义（核心参数）

| 角色 | 枚举值 | ROLE_LEVEL | 显示标签 | 定位描述 |
|------|--------|------------|----------|----------|
| 观察员 | `observer` | 1 | L0 | 新用户默认角色，只读浏览 |
| 成长者 | `grower` | 2 | L1 | 核心用户，接受健康管理服务 |
| 分享者 | `sharer` | 3 | L2 | 有能力分享经验和知识 |
| 教练 | `coach` | 4 | L3 | 提供专业健康教练服务 |
| 促进师 | `promoter` | 5 | L4 | 高级教练，带领团队 |
| 督导 | `supervisor` | 5 | L4 | 专家督导，与促进师平级 |
| 大师 | `master` | 6 | L5 | 行为健康促进大师 |
| 管理员 | `admin` | 99 | — | 系统管理，全权限 |

> **权威来源**：`core/models.py` `ROLE_LEVEL` 字典，全系统统一引用

---

## 2. 角色权限矩阵

### 2.1 RBAC 三级守卫

系统通过 `api/dependencies.py` 定义三个依赖注入守卫：

| 守卫函数 | 允许角色 | 用途 |
|---------|---------|------|
| `get_current_user` | 所有已认证用户 | 基础身份验证 |
| `require_coach_or_admin` | coach / promoter / supervisor / master / admin | 教练级操作 |
| `require_admin` | admin | 管理后台操作 |
| `resolve_tenant_ctx` | 自动检测 | 专家租户路由上下文 |

### 2.2 功能域权限分布

| 功能域 | observer | grower | sharer | coach | promoter/supervisor | master | admin |
|--------|:--------:|:------:|:------:|:-----:|:------------------:|:------:|:-----:|
| 浏览内容 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| AI 对话 | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 设备绑定 | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 评估问卷 | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 微行动 | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 方案参与 | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 内容互动(评论/点赞) | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 内容贡献 | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 教练消息(发送) | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| 学员管理 | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| 评估指派/审核 | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| 挑战推送/审核 | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| 设备警报处理 | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| 推送审批队列 | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| 带教同道者 | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ |
| 专家入驻申请 | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |
| 租户管理 | ❌ | ❌ | ❌ | ✅* | ✅* | ✅* | ✅ |
| 自定义 Agent | ❌ | ❌ | ❌ | ✅* | ✅* | ✅* | ✅ |
| 知识共享 | ❌ | ❌ | ❌ | ✅* | ✅* | ✅* | ✅ |
| Agent 市场发布 | ❌ | ❌ | ❌ | ✅* | ✅* | ✅* | ✅ |
| 用户CRUD | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 内容管理 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 安全审核 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 系统配置 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| 策略规则管理 | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

> `✅*` = 需先完成专家入驻（拥有 ExpertTenant）

### 2.3 分层权限不足

**问题**：当前 RBAC 只有 3 级守卫（any / coach+ / admin），没有针对 sharer、promoter、master 的细粒度鉴权。

- observer → grower 的区别仅靠 `user_segments.py` 和前端路由，后端 API 未强制拦截
- sharer 与 grower 在 API 层面几乎无区别（内容贡献除外）
- promoter / supervisor / master 与 coach 共享同一守卫 `require_coach_or_admin`

---

## 3. 核心互动关系图谱

### 3.1 全局关系拓扑

```
                        ┌─────────────────────────────────────────┐
                        │              ADMIN (L99)                │
                        │  用户管理│内容管理│安全审核│策略引擎     │
                        │  入驻审核│Agent模板│系统配置│数据分析     │
                        └────────────┬───────────────┬────────────┘
                                     │ 管理/审核     │ 全局监控
                     ┌───────────────┼───────────────┼──────────────┐
                     ▼               ▼               ▼              ▼
              ┌──────────┐    ┌──────────┐    ┌──────────┐   ┌──────────┐
              │  MASTER  │    │ PROMOTER │    │SUPERVISOR│   │  EXPERT  │
              │  (L5)    │    │  (L4)    │    │  (L4)    │   │ (TENANT) │
              └────┬─────┘    └────┬─────┘    └────┬─────┘   └────┬─────┘
                   │ 带教          │ 带教          │ 督导         │ 服务
                   ▼               ▼               ▼              ▼
              ┌────────────────────────────────┐         ┌──────────────┐
              │          COACH (L3)            │◄────────│ TenantClient │
              │  学员管理│评估│消息│设备警报    │  路由    │  (客户绑定)  │
              └──────────────┬─────────────────┘         └──────────────┘
                             │ 管理/指导
                             ▼
              ┌──────────────────────────────────┐
              │     GROWER (L1) / SHARER (L2)    │
              │  AI对话│设备│微行动│方案│评估│学习 │
              └──────────────────────────────────┘
                             ▲
                             │ 注册后默认
              ┌──────────────────────────────────┐
              │         OBSERVER (L0)             │
              │  浏览内容（只读）                  │
              └──────────────────────────────────┘
```

### 3.2 互动类型分类

| 互动类型 | 方向 | 参与角色 | 关键 API |
|---------|------|---------|---------|
| **管理关系** | admin → 所有 | admin | user_api, content_manage_api |
| **教练指导** | coach → grower | coach, grower | coach_api, coach_message_api |
| **评估流程** | coach ↔ grower | coach, grower | assessment_assignment_api |
| **设备监控** | grower → coach | grower, coach | device_alert_api |
| **推送审批** | coach → admin | coach, admin | coach_push_queue_api |
| **同道者带教** | mentor → mentee | L3+ → L1+ | companion_api |
| **晋级申请** | user → admin | 任意, admin | promotion_api |
| **专家入驻** | grower → admin | grower+, admin | expert_registration |
| **租户服务** | expert → client | expert, client | tenant_api |
| **知识共享** | expert → domain | expert, admin | knowledge_sharing_api |
| **内容互动** | user ↔ user | all authenticated | content_api |
| **AI 对话** | user → agent | grower+ | agent_api, chat_rest_api |
| **方案参与** | user ↔ system | grower+ | program_api |
| **学习积分** | user → system | grower+ | learning_api |
| **市场交易** | expert ↔ expert | expert | agent_ecosystem_api |

---

## 4. 角色晋级流转

### 4.1 六级四同道者晋级路径

```
OBSERVER ──── 注册激活 ────► GROWER ──── 成长100点 ────► SHARER
   L0                         L1                          L2
                                                           │
                              成长800 + 贡献200 + 影响50    │ 成长500 + 贡献50
                              + 认证考核                    │
                              + 带教4名L1成长者              │
                              ◄─────────────────────────────┘
                                           │
                                           ▼
                                        COACH (L3)
                                           │
                     成长1500 + 贡献600 + 影响200
                     + 认证考核
                     + 带教4名L2分享者
                              │
                              ▼
                     PROMOTER / SUPERVISOR (L4)
                              │
                     成长3000 + 贡献1500 + 影响600
                     + 认证考核
                     + 带教4名L3教练
                              │
                              ▼
                        MASTER (L5)
```

### 4.2 三维积分体系

| 维度 | 字段 | 获取方式 | 作用 |
|------|------|---------|------|
| 成长积分 | `growth_points` | 学习内容、完成课程、每日签到、微行动 | 核心晋级条件 |
| 贡献积分 | `contribution_points` | 分享内容、评论、提交贡献、回答问题 | L2 起必需 |
| 影响力积分 | `influence_points` | 被点赞/收藏、带教同道者、推荐用户 | L3 起必需 |

> **权威来源**：`api/paths_api.py` `_LEVEL_THRESHOLDS`

### 4.3 四同道者机制

L3 及以上晋级需要带领 4 名低一级同道者达标：

| 目标等级 | 需带教 | 同道者要求 | DB 表 |
|---------|--------|-----------|-------|
| L3 教练 | 4 名 | L1 成长者 | `companion_relations` |
| L4 促进师 | 4 名 | L2 分享者 | `companion_relations` |
| L5 大师 | 4 名 | L3 教练 | `companion_relations` |

同道者关系生命周期：`invited → active → graduated`

### 4.4 晋级申请流程

```
用户积分达标 ──► 查看晋级进度(/promotion/progress)
                    │
                    ▼ 四维检查(积分+学分+同道者+实践)
                ┌───────┐
                │ 满足？ │
                └───┬───┘
               Yes  │  No → 显示缺失项
                    ▼
           提交晋级申请(/promotion/apply)
                    │
                    ▼
          Admin 审核(/promotion/applications/{id}/review)
                    │
              ┌─────┴─────┐
              ▼           ▼
           批准         驳回
              │           │
              ▼           ▼
         角色升级      通知用户
         发放学分      可重新申请
```

### 4.5 专家入驻流转（特殊路径）

```
GROWER+ ──► 提交入驻申请 ──► Admin 审核 ──► 批准
              │                               │
              │ POST /expert-registration/apply │
              │                               ▼
              │                        角色升级为 COACH
              │                        创建 ExpertTenant
              │                        状态 pending→trial
              │                               │
              │                               ▼
              │                        自定义 Agent / 知识 / 内容
              └───────────────────────────────┘
```

> 入驻审核独立于六级晋级体系，是一条平行路径

---

## 5. 教练 ↔ 成长者互动

### 5.1 教练管理学员

```
COACH 看板(coach_api.py)
├── GET /coach/students ─── 学员列表（按分配关系）
├── GET /coach/students/{id}/profile ─── 学员详细资料
├── GET /coach/students/{id}/health-data ─── 学员健康数据
├── GET /coach/performance ─── 教练绩效统计
└── GET /coach/certification-progress ─── 认证进度
```

### 5.2 教练消息系统

```
COACH ──── POST /coach-message/send ────► GROWER
                                          (单向推送)

GROWER ── GET /coach-message/my-messages ─► 查看消息
COACH ─── GET /coach-message/sent ────────► 查看已发
```

> **注意**：当前消息为单向（coach→grower），grower 无法回复。
> 如需双向沟通需通过 AI 对话系统间接实现。

### 5.3 评估指派-提交-审核流水线

```
Step 1: COACH 指派评估
        POST /assessment-assign/assign
        │
Step 2: GROWER 收到待做评估
        GET /assessment-assign/my-assignments
        │
Step 3: GROWER 提交评估
        POST /assessment/submit
        │
Step 4: COACH 审核结果
        GET /assessment-assign/coach/pending-reviews
        POST /assessment-assign/review/{id}
        │
Step 5: COACH 推送个性化建议
        POST /assessment-assign/push/{id}
        │
        ▼
   GROWER 收到干预建议
```

### 5.4 设备健康监控链

```
GROWER 设备上传数据
        │
        ▼ (阈值检查: device_alert_service.py)
   ┌────────────┐
   │ 超阈值？    │
   └──────┬─────┘
     Yes  │
          ▼
   创建 DeviceAlert
          │
          ├──► GROWER: GET /device-alerts/my
          │    (查看我的警报)
          │
          └──► COACH: GET /device-alerts/coach
               (查看学员警报)
               │
               ▼
          POST /device-alerts/{id}/resolve
          (处理警报 + 记录处理方式)
```

### 5.5 推送审批网关

```
系统/AI 生成推送建议
        │
        ▼
   推送队列 (coach_push_queue_api.py)
        │
        ▼
   COACH 审批
   ├── GET /push-queue/list ─── 待审批列表
   ├── GET /push-queue/stats ── 统计概览
   ├── POST /push-queue/{id}/approve ─── 批准推送
   ├── POST /push-queue/{id}/reject ──── 驳回
   └── POST /push-queue/batch ────────── 批量操作
        │
        ▼ (批准后)
   推送到 GROWER
```

### 5.6 挑战任务管理

```
ADMIN ──► 创建挑战模板 (challenge_api.py CRUD)
              │
COACH ──► 指派挑战给学员
              │ POST /challenges/assign
              ▼
GROWER ─► 参与挑战
              │ POST /challenges/{id}/enroll
              │ POST /challenges/{id}/survey/submit
              ▼
COACH ──► 审核挑战完成
              │ GET /challenges/coach/review
              ▼
         发放积分/奖励
```

### 5.7 微行动与提醒

```
每日微行动 (micro_action_api.py)
GROWER ── GET /micro-actions/today ────► 今日推荐
GROWER ── POST /micro-actions/{id}/complete ► 标记完成 (+积分)
GROWER ── POST /micro-actions/{id}/skip ────► 跳过

提醒系统 (reminder_api.py)
COACH ──► 创建提醒 → GROWER 收到提醒
GROWER ─► 自建提醒 → 自我管理
```

---

## 6. 专家 ↔ 租户 ↔ 客户三角

### 6.1 三角关系模型

```
                    ┌──────────────────┐
                    │   ADMIN (审核)    │
                    └────────┬─────────┘
                             │ 审核入驻/知识/市场
                             ▼
┌──────────────────────────────────────────────────────┐
│                  ExpertTenant (专家租户)               │
│                                                       │
│  expert_user_id ──► User (角色≥coach)                │
│  theme / domain / branding / status                  │
│                                                       │
│  拥有资源：                                           │
│  ├── TenantClient (客户绑定)                         │
│  ├── TenantRoutingConfig (路由覆盖)                  │
│  ├── AgentTemplate (自定义Agent)                     │
│  ├── ExpertContent (内容工作室)                      │
│  └── KnowledgeContribution (知识共享)                │
└──────────────────────────────────────────────────────┘
          │                           │
          │ 绑定客户                   │ 自定义 Agent
          ▼                           ▼
┌──────────────────┐     ┌──────────────────────────┐
│  TenantClient    │     │  tenant-aware 路由       │
│                  │     │                          │
│  user_id ─► User │     │  resolve_tenant_ctx()    │
│  status: active  │     │  → 专家自己的tenant_id   │
│                  │     │  → 客户所属tenant_id     │
└──────────────────┘     │  → None (平台默认)       │
                         └──────────────────────────┘
```

### 6.2 专家服务能力

| 能力 | API | 说明 |
|------|-----|------|
| 自定义 Agent | `expert_agent_api.py` | 基于模板 CRUD + toggle + 路由测试 |
| 路由覆盖 | `TenantRoutingConfig` | keyword_boost / correlation / conflict 覆盖 |
| 内容工作室 | `expert_content_api.py` | 文档 CRUD + 发布/下架 + 挑战创建 |
| 知识共享 | `knowledge_sharing_api.py` | 3 层检索（租户→领域→平台），贡献+审核 |
| 客户管理 | `tenant_api.py` | 客户绑定/解绑、状态管理、统计 |
| Agent 市场 | `agent_ecosystem_api.py` | 发布/安装/评价/组合编排 |

### 6.3 租户路由影响 Agent 选择

```
用户发起 AI 对话
      │
      ▼
resolve_tenant_ctx(current_user)
      │
      ├── 用户是专家 → 自己的 tenant routing config
      ├── 用户是客户 → 所属专家的 tenant routing config
      └── 普通用户 → None (平台默认路由)
      │
      ▼
AgentRouter (tenant-aware)
      │
      ├── keyword_boost: 租户自定义关键词加权
      ├── correlation_override: 自定义 Agent 关联
      └── conflict_override: 自定义冲突优先级
      │
      ▼
匹配到 Agent(s) → 执行
```

---

## 7. 内容与社交互动

### 7.1 内容互动矩阵

```
                    创建内容
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
      ADMIN        COACH/EXPERT   SHARER+
   (content_manage) (expert_content) (contribution)
         │             │             │
         └─────────────┼─────────────┘
                       ▼
                  ContentItem (内容库)
                       │
         ┌─────────────┼──────────────┐
         ▼             ▼              ▼
      浏览/学习     互动操作      社交传播
      (所有认证用户)                (grower+)
                       │
              ┌────────┼────────┬─────────┐
              ▼        ▼        ▼         ▼
           点赞      收藏      评论      分享
           like    collect   comment    share
           (+影响)  (个人)   (+贡献)   (+影响)
```

### 7.2 学习互动

| 角色 | 互动 | 端点 | 积分效果 |
|------|------|------|---------|
| grower+ | 浏览内容 | `GET /content/list` | +成长 |
| grower+ | 完成课程 | `POST /learning/event` | +成长 |
| grower+ | 每日签到 | `POST /incentive/checkin` | +成长 |
| grower+ | 完成微行动 | `POST /micro-actions/complete` | +成长 |
| grower+ | 参与方案 | `POST /programs/interact` | +成长(+3) |
| sharer+ | 提交贡献 | `POST /contributions/submit` | +贡献 |
| sharer+ | 发表评论 | `POST /content/{id}/comment` | +贡献 |
| coach+ | 被学员点赞 | — | +影响 |
| coach+ | 带教同道者 | `POST /companions/invite` | +影响 |

### 7.3 问卷调查互动

```
ADMIN/COACH ──► 创建问卷 (survey_api.py)
                    │
                    ▼ 发布 → 生成短码
              ┌───────────┐
              │ Short Code│──► 分享给目标用户
              └───────────┘
                    │
              匿名/实名 ──► 填写 (survey_response_api.py)
                    │        POST /surveys/s/{short_code}/submit
                    ▼
              统计/导出 (survey_stats_api.py)
                    │
                    └──► BAPS 同步（如果是评估类问卷）
```

### 7.4 考试系统互动

```
ADMIN ──► 创建题库 (question_api.py)
              │
ADMIN ──► 创建考试 (exam_api.py) ← 从题库选题
              │
              ▼ 发布
GROWER+ ─► 开始考试 (exam_session_api.py)
              │ POST /exam-sessions/start
              ▼
         答题 → 提交
              │ POST /exam-sessions/{id}/submit
              ▼
         评分 → 查看结果
              │ GET /exam-sessions/{id}/result
              ▼
         通过认证 → 晋级条件之一
```

### 7.5 排行榜与社交激励

```
leaderboards (learning_api.py)
├── 成长积分榜 ── grower+ 可见
├── 贡献积分榜 ── sharer+ 关注
├── 学习时长榜 ── 全员可见
└── 连续签到榜 ── 全员可见

badges (milestone_service.py)
├── 系统自动颁发 ── 达成里程碑
├── 展示在个人页 ── 社交认同
└── 翻牌日历 ── 每日惊喜（+积分）
```

---

## 8. AI Agent 服务边界

### 8.1 Agent 按角色可用性

| Agent 层 | Agent 名称 | 服务对象 | 触发场景 |
|---------|-----------|---------|---------|
| 核心专家 | metabolic | grower+ | 血糖/代谢相关问题 |
| 核心专家 | sleep | grower+ | 睡眠问题 |
| 核心专家 | emotion | grower+ | 情绪管理 |
| 核心专家 | motivation | grower+ | 动力不足 |
| 核心专家 | coaching | grower+ | 一般教练指导 |
| 核心专家 | nutrition | grower+ | 营养饮食 |
| 核心专家 | exercise | grower+ | 运动处方 |
| 核心专家 | tcm | grower+ | 中医养生 |
| 核心专家 | crisis | 全员 | 危机干预（始终优先） |
| 整合型 | behavior_rx | grower+ | 行为处方 |
| 整合型 | weight | grower+ | 体重管理 |
| 整合型 | cardiac_rehab | grower+ | 心脏康复 |
| 行为处方专家 | BehaviorCoach | grower(S0-S2) | 行为改变早期阶段 |
| 行为处方专家 | MetabolicExpert | grower+ | 代谢综合征 |
| 行为处方专家 | CardiacExpert | grower+ | 心血管风险 |
| 行为处方专家 | AdherenceExpert | grower+ | 依从性差 |
| 动态模板 | GenericLLMAgent | 视模板配置 | 专家自定义场景 |

### 8.2 Agent 与角色的交互差异

```
GROWER 发起对话:
  └─► MasterAgent (v6, tenant-aware)
       ├─► PolicyEngine (V007) → 规则过滤/成本控制
       ├─► AgentRouter → 匹配专家 Agent(s)
       ├─► SafetyPipeline (V005) → 4 层安全
       ├─► BehaviorRx (行为处方) → 如果匹配 TTM 阶段
       └─► 最终回复 (含免责声明)

COACH 使用 Agent:
  └─► 同上，但额外:
       ├─► 可查看 Agent 运行状态 (/agent/status)
       ├─► 可提交反馈 (/agent-feedback)
       └─► 可查看学员的 Agent 历史

EXPERT 使用 Agent:
  └─► tenant_ctx 路由:
       ├─► 自定义 Agent 优先匹配
       ├─► keyword_boost 加权
       └─► 客户自动继承专家路由
```

### 8.3 安全审核流

```
任意用户对话 → SafetyPipeline
      │
      ├─ L1: 输入过滤（危机/敏感词/PII）
      │       ├── 危机词 → crisis Agent 强制接管
      │       └── 封禁词 → 拒绝响应
      │
      ├─ L2: RAG 安全（源权威性/过期检查）
      │
      ├─ L3: 生成守卫（注入攻击/领域边界）
      │
      └─ L4: 输出过滤（医疗声明/免责声明/分级）
              │
              ▼
         SafetyLog (记录所有安全事件)
              │
              ▼
         ADMIN: /safety/review-queue → 审核处理
```

---

## 9. 现存问题与建议

### P0 — 权限体系过于粗放

**问题**：8 个角色只有 3 级 RBAC 守卫，中间角色（sharer/promoter/supervisor/master）在 API 层面与相邻角色无区别。

**建议**：
1. 新增 `require_role_level(min_level: int)` 通用守卫，基于 `ROLE_LEVEL` 数值判断
2. 对关键 API 端点显式标注最低角色要求
3. sharer 的内容贡献权限应有显式后端拦截

### P1 — observer → grower 激活缺乏仪式感

**问题**：注册默认 observer，但升级到 grower 的触发条件和流程不明确，当前可能是管理员手动或隐式升级。

**建议**：
1. 定义明确的激活条件（如完成新手引导/首次评估/阅读协议）
2. 在 H5 端增加激活引导页面
3. 后端增加 `/activate` 端点自动升级角色

### P1 — 教练消息单向通信

**问题**：`coach_message_api.py` 只支持 coach→grower 单向发送，grower 无法直接回复教练。

**建议**：
1. 扩展为双向消息系统（增加 grower→coach 回复能力）
2. 或将教练消息整合进现有 chat 系统，以对话形式呈现
3. 增加消息已读/未读状态

### P1 — 同道者关系与实际带教脱钩

**问题**：`CompanionRelation` 表记录了 mentor-mentee 关系，但 "带教质量" 和 "毕业标准" 缺乏自动化评估，主要依赖 `quality_score` 手动打分。

**建议**：
1. 定义可量化的毕业标准（如学员积分达到下一级阈值）
2. 自动触发毕业（`graduated` 状态）
3. 将同道者互动频率纳入导师影响力积分计算

### P2 — promoter 与 supervisor 角色定位模糊

**问题**：promoter 和 supervisor 均为 L4（ROLE_LEVEL=5），权限完全相同，但名称暗示职能不同（促进 vs 督导）。实际代码中无任何差异化处理。

**建议**：
1. 明确两者的职能分工（如 promoter 侧重推广，supervisor 侧重质量管理）
2. 或合并为单一 L4 角色，减少概念复杂度
3. 如保留，需在 API 层面增加角色特有功能

### P2 — 专家入驻与六级晋级平行但不互通

**问题**：专家入驻是从 grower+ 直接升级为 coach 的"捷径"，但跳过了六级体系的积分和同道者要求。两套体系之间无约束关系。

**建议**：
1. 明确专家入驻是否独立于六级体系（如是，需文档化）
2. 考虑专家入驻后仍受积分体系约束（积分不足不能使用高级功能）
3. 或为专家设立独立的等级评价体系

### P2 — 学员分配关系不明确

**问题**：`coach_api.py` 通过查询获取学员列表，但"教练-学员"的分配关系（谁指导谁）在数据库中的定义不够清晰。可能依赖 `referred_by` 字段或 `TenantClient` 关系。

**建议**：
1. 建立明确的 `coach_assignment` 表或利用现有 `CompanionRelation` 统一
2. 明确"学员分配"与"同道者关系"是否是同一概念
3. 支持一个学员可有多个教练（主教练 + 专项教练）

### P3 — 内容访问未按角色分级

**问题**：`content_api.py` 的 28 个端点仅要求 `get_current_user`（任意认证用户），没有按角色或等级限制内容访问。`user_segments.py` 有分层逻辑但未在 API 层强制执行。

**建议**：
1. 对高级内容（如教练专属课程、大师案例）增加角色级别检查
2. 利用现有 `user_segments` 的 tier 体系在 API 层过滤
3. 内容创建时标注 `min_role_level` 字段

### P3 — 缺乏角色间的通知系统

**问题**：各互动流程（警报、消息、审核、晋级）缺乏统一的通知中枢，通知散布在各 API 中。

**建议**：
1. 建立统一通知服务（`notification_service.py`）
2. 支持多渠道（应用内推送、短信、邮件）
3. 按角色和事件类型配置通知规则

---

## 附录 A：角色互动端点索引

| 互动场景 | 发起方 | 接收方 | 关键端点 | 所在文件 |
|---------|--------|-------|---------|---------|
| 注册 | 匿名 | 系统 | POST /auth/register | auth_api.py |
| 登录 | 任意 | 系统 | POST /auth/login | auth_api.py |
| 查看学员 | coach+ | — | GET /coach/students | coach_api.py |
| 发送消息 | coach+ | grower | POST /coach-message/send | coach_message_api.py |
| 指派评估 | coach+ | grower | POST /assessment-assign/assign | assessment_assignment_api.py |
| 审核评估 | coach+ | — | POST /assessment-assign/review/{id} | assessment_assignment_api.py |
| 查看警报 | coach+ | — | GET /device-alerts/coach | device_alert_api.py |
| 处理警报 | coach+ | — | POST /device-alerts/{id}/resolve | device_alert_api.py |
| 审批推送 | coach+ | — | POST /push-queue/{id}/approve | coach_push_queue_api.py |
| 指派挑战 | coach+ | grower | POST /challenges/assign | challenge_api.py |
| 提交评估 | grower+ | 系统 | POST /assessment/submit | assessment_api.py |
| 完成微行动 | grower+ | 系统 | POST /micro-actions/{id}/complete | micro_action_api.py |
| 参与方案 | grower+ | 系统 | POST /programs/enroll | program_api.py |
| AI 对话 | grower+ | Agent | POST /agent/run | agent_api.py |
| 点赞内容 | grower+ | 作者 | POST /content/{id}/like | content_api.py |
| 提交贡献 | sharer+ | admin | POST /contributions/submit | content_contribution_api.py |
| 邀请同道 | coach+ | grower+ | POST /companions/invite | companion_api.py |
| 申请晋级 | 任意 | admin | POST /promotion/apply | promotion_api.py |
| 申请入驻 | grower+ | admin | POST /expert-registration/apply | expert_registration |
| 审核入驻 | admin | expert | POST /expert-registration/admin/.../approve | expert_registration |
| 管理用户 | admin | — | CRUD /users/* | user_api.py |
| 安全审核 | admin | — | GET /safety/review-queue | safety_api.py |
| 策略管理 | admin | — | CRUD /policy/rules | policy_api.py |
| Agent模板 | admin | — | CRUD /agent-templates/* | agent_template_api.py |

---

## 附录 B：数据模型关联图

```
User (核心)
├── 1:N ── UserLearningStats (学习统计)
├── 1:N ── CompanionRelation (同道者，作为 mentor/mentee)
├── 1:N ── PromotionApplication (晋级申请)
├── 1:N ── UserCredit (学分)
├── 1:N ── ChatSession / ChatMessage (对话)
├── 1:N ── DeviceBinding / DeviceAlert (设备)
├── 1:N ── AssessmentResult (评估)
├── 1:N ── ProgramEnrollment (方案参与)
├── 1:N ── ContentInteraction (内容互动)
├── 1:N ── UserBadge (徽章)
├── 1:N ── UserMilestone (里程碑)
├── 1:N ── UserStreak (连续签到)
├── 1:N ── PointTransaction (积分变动)
├── 1:N ── ExamSession (考试)
├── 1:N ── SurveyResponse (问卷)
├── 1:1 ── ExpertTenant (专家租户, via expert_user_id)
├── 1:N ── TenantClient (租户客户, via user_id)
├── 1:N ── AgentFeedback (Agent 反馈)
└── 1:N ── RxPrescription (行为处方)

ExpertTenant (租户)
├── 1:N ── TenantClient (客户)
├── 1:N ── TenantRoutingConfig (路由配置)
├── 1:N ── AgentTemplate (自定义 Agent, via tenant_id)
├── 1:N ── ExpertContent (内容)
├── 1:N ── KnowledgeContribution (知识共享)
└── 1:N ── AgentMarketplaceListing (市场列表)
```

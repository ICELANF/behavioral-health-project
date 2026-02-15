# 平台用户权限与服务全目录 v1

> 日期：2026-02-14
> 数据来源：代码实际提取（53 路由文件，522 端点，119 ORM 模型）
> 覆盖：3 轨道 × 8 角色 × 4 服务层 × 22 功能模块 × 76 课程模块

---

## 目录

1. [平台三轨体系总览](#1-平台三轨体系总览)
2. [服务层级与功能门控](#2-服务层级与功能门控)
3. [轨道一：普通用户成长轨（L0→L5）](#3-轨道一普通用户成长轨l0l5)
4. [轨道二：专家入驻轨（Expert Track）](#4-轨道二专家入驻轨expert-track)
5. [轨道三：管理运营轨（Admin Track）](#5-轨道三管理运营轨admin-track)
6. [各角色端点权限完整矩阵](#6-各角色端点权限完整矩阵)
7. [课程模块与学分体系](#7-课程模块与学分体系)
8. [AI Agent 服务分配](#8-ai-agent-服务分配)
9. [端点统计与守卫分布](#9-端点统计与守卫分布)

---

## 1. 平台三轨体系总览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     行为健康促进平台 — 三轨用户体系                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  轨道一：普通用户成长轨                                                  │
│  observer → grower → sharer → coach → promoter/supervisor → master     │
│  L0        L1        L2       L3      L4                      L5       │
│  特点：六级四同道者体系，三维积分驱动晋级                                │
│                                                                         │
│  轨道二：专家入驻轨                                                      │
│  grower+ → 申请入驻 → admin审核 → ExpertTenant(coach+)                 │
│  特点：专家白标，自定义Agent/知识/内容，客户管理                         │
│                                                                         │
│  轨道三：管理运营轨                                                      │
│  admin (L99)                                                            │
│  特点：全平台管控，用户/内容/安全/策略/数据分析                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.1 用户来源 × 服务层

| 来源 | 枚举值 | 说明 | 默认服务层 |
|------|--------|------|-----------|
| 自然注册 | `organic` | 官方渠道、社交媒体自行注册 | free |
| 教练引荐 | `coach_referred` | 教练推荐，带追踪 | premium |
| 机构服务 | `institution` | 医疗机构、功能社区 | premium |
| 企业客户 | `enterprise` | 企业健康管理项目 | basic |

### 1.2 服务层级

| 层级 | 枚举值 | 数值 | 可用功能数 | 定位 |
|------|--------|------|-----------|------|
| 免费体验 | `free` | 0 | 3 | 浏览、需求调查 |
| 基础会员 | `basic` | 1 | 7 | 自主学习与成长 |
| 高级会员 | `premium` | 2 | 12 | 专家支持+深度成长 |
| VIP会员 | `vip` | 3 | 16 | 全系统课程+专属服务 |

---

## 2. 服务层级与功能门控

### 2.1 功能模块矩阵（22 项功能）

| 功能 | 模块ID | Free | Basic | Premium | VIP | 角色门控 |
|------|--------|:----:|:-----:|:-------:|:---:|:--------:|
| 需求调查 | `needs_survey` | ✅ | ✅ | ✅ | ✅ | — |
| 内容发现 | `content_feed` | ✅ | ✅ | ✅ | ✅ | — |
| 社区浏览 | `community_read` | ✅ | ✅ | ✅ | ✅ | — |
| 自我评估 | `self_assessment` | — | ✅ | ✅ | ✅ | — |
| 基础学习 | `learning_basic` | — | ✅ | ✅ | ✅ | — |
| 工具库 | `tool_library` | — | ✅ | ✅ | ✅ | — |
| 进度追踪 | `progress_tracking` | — | ✅ | ✅ | ✅ | — |
| 完整学习 | `learning_full` | — | — | ✅ | ✅ | — |
| 专家咨询 | `expert_consult` | — | — | ✅ | ✅ | — |
| 团体工坊 | `group_session` | — | — | ✅ | ✅ | — |
| 社区互动 | `community_interact` | — | — | ✅ | ✅ | — |
| AI陪伴 | `ai_companion` | — | — | ✅ | ✅ | — |
| 180天课程 | `course_180day` | — | — | — | ✅ | — |
| 专属教练 | `private_coach` | — | — | — | ✅ | — |
| 危机支持 | `crisis_support` | — | — | — | ✅ | — |
| 家庭支持 | `family_support` | — | — | — | ✅ | — |
| 客户管理 | `client_management` | — | — | — | — | coach+ |
| 咨询服务 | `session_conduct` | — | — | — | — | coach+ |
| 督导功能 | `supervision` | — | — | — | — | promoter+ |
| 系统配置 | `system_config` | — | — | — | — | admin |
| 用户管理 | `user_management` | — | — | — | — | admin |
| 数据分析 | `data_analytics` | — | — | — | — | admin |

### 2.2 来源特殊调整

| 用户来源 | 额外获得 | 受限功能 |
|---------|---------|---------|
| `coach_referred` | +AI陪伴(ai_companion) | 无 |
| `institution` | +危机支持(crisis_support) | -专属教练(private_coach) |
| `enterprise` | +团体工坊(group_session) | 无 |

### 2.3 预设用户段

| 段名 | 来源 | 默认层级 | 可用功能数 |
|------|------|---------|-----------|
| `public_observer` 观察者 | organic | free | 3 |
| `self_grower` 自主成长者 | organic | basic | 7 |
| `coach_client` 教练客户 | coach_referred | premium | 9 (+ai_companion) |
| `institution_patient` 机构对象 | institution | premium | 9 (+crisis, -private_coach) |
| `enterprise_employee` 企业员工 | enterprise | basic | 8 (+group_session) |
| `vip_member` VIP会员 | organic | vip | 16 (全部) |

---

## 3. 轨道一：普通用户成长轨（L0→L5）

### 3.1 Observer 观察员 (L0)

**角色定位**：新注册默认角色，浏览体验为主

#### 可用服务

| 服务类别 | 可用端点 | 说明 |
|---------|---------|------|
| **账号认证** | POST /auth/register, /login, /refresh, /logout | 注册/登录/刷新/登出 |
| **内容浏览** | GET /content/, /content/recommended, /content/detail/* | 浏览内容列表、推荐内容 |
| **内容互动** | POST /content/{id}/like, /collect, /share, /comment | 点赞/收藏/分享/评论 |
| **排行榜** | GET /learning/leaderboard/coaches, /growers | 查看教练和成长者排行 |
| **教练等级** | GET /coach-levels/levels, /modules | 查看六级体系说明 |
| **高频问卷** | GET /high-freq/presets, /all, /by-ids | 查看预设问卷 |
| **问卷填写** | GET/POST /survey-responses/{short_code}/* | 通过短链接填写问卷（可匿名） |
| **教练目录** | GET /coach/directory | 浏览公开教练/专家目录 |
| **知识领域** | GET /knowledge/domains | 查看知识领域列表 |
| **专家域列表** | GET /expert-registration/domains | 查看可入驻领域 |

**限制**：不可使用 AI 对话、设备绑定、评估、微行动、方案等核心服务

---

### 3.2 Grower 成长者 (L1)

**角色定位**：核心用户，接受健康管理服务

**晋级条件**：成长积分 ≥ 100

#### 新增服务（在 Observer 基础上）

| 服务类别 | 可用端点 | 说明 |
|---------|---------|------|
| **AI 对话** | POST /agent/run | 与 17 个 Agent 的 AI 对话（tenant-aware） |
| | GET /agent/list, /status | 查看可用 Agent 列表和状态 |
| | GET /agent/history, /pending-reviews | 对话历史和待审核 |
| | POST /agent-feedback/submit | 提交 Agent 反馈 |
| **聊天** | GET/POST /chat/sessions/*, /messages/* | 聊天会话管理 |
| **设备管理** | GET/POST/DELETE /device-data/devices/* | 设备绑定/解绑/列表 |
| **健康数据** | GET/POST /device-data/glucose/*, /weight, /blood-pressure | 血糖/体重/血压记录和查看 |
| | GET /device-data/sleep, /activity, /heart-rate, /hrv | 睡眠/运动/心率/HRV数据 |
| | GET /device-data/dashboard/today | 今日健康仪表盘 |
| **设备同步** | POST /device-data/sync, /sync/batch | 设备数据同步 |
| **设备警报** | GET /device-alerts/my | 查看我的警报 |
| | POST /device-alerts/{id}/read, /resolve | 标记警报已读/处理 |
| **评估** | POST /assessment/submit | 提交行为健康评估 |
| | GET /assessment/history, /latest | 评估历史 |
| | POST /assessment-pipeline/run | 完整BAPS评估流水线 |
| **评估指派** | GET /assessment-assign/my-assignments | 查看教练指派的评估 |
| **微行动** | GET /micro-actions/today | 今日微行动任务 |
| | POST /micro-actions/{id}/complete, /skip | 完成/跳过微行动 |
| | GET /micro-actions/history, /stats, /facts | 微行动历史和统计 |
| **方案参与** | POST /programs/enroll | 报名监测方案 |
| | GET /programs/my, /{id}/today, /progress, /timeline | 方案进度和互动 |
| | POST /programs/{id}/interact, /status | 每日互动/暂停恢复 |
| **挑战参与** | POST /challenges/{id}/enroll | 报名挑战 |
| | GET /challenges/my-enrollments | 我的挑战列表 |
| | POST /challenges/enrollments/{id}/start, /advance | 开始/推进挑战 |
| | GET /challenges/enrollments/{id}/today, /progress | 今日内容和进度 |
| | POST /challenges/enrollments/{id}/read/{pid} | 标记已读 |
| | POST /challenges/enrollments/{id}/survey/{pid} | 提交问卷 |
| **课程学习** | POST /content/course/{id}/enroll, /progress | 报名课程、更新进度 |
| | GET /content/video/{id}, /quiz | 视频和测试 |
| | POST /content/video/{id}/quiz/submit | 提交测验（+积分） |
| **案例分享** | POST /content/case | 提交案例（草稿状态） |
| | POST /content/case/{id}/like, /helpful | 点赞/标记有帮助 |
| **学习统计** | GET /learning/grower/stats/{id} | 成长者统计面板 |
| | GET /learning/grower/time/{id}, /time/history | 学习时长和历史 |
| | GET /learning/grower/points/{id} | 学习积分 |
| | GET /learning/grower/streak/{id} | 连续学习天数 |
| | POST /learning/event | 记录学习事件 |
| **奖励** | GET /learning/rewards/{id} | 查看可领奖励 |
| | POST /learning/rewards/claim | 领取奖励 |
| **激励系统** | POST /incentive/checkin | 每日签到（+5成长积分） |
| | GET /incentive/dashboard | 里程碑旅程仪表盘 |
| | POST /incentive/flip-card/choose | 翻牌奖励 |
| | POST /incentive/streak/recover | 连续签到恢复 |
| | GET /incentive/badges, /badges/available | 徽章系统 |
| | GET /incentive/memorials | 数据纪念海报 |
| **晋级查看** | GET /coach-levels/progress, /overview | 查看晋级进度 |
| | GET /promotion/progress, /rules, /check | 晋级进度、规则、资格检查 |
| **学分查看** | GET /credits/modules | 课程模块列表 |
| | GET /credits/my, /my/records | 我的学分和明细 |
| **同道者** | GET /companions/my-mentors, /my-mentees, /stats | 同道者关系 |
| **用户统计** | GET /user-stats/overview, /activity, /reports | 个人统计 |
| **食物识别** | POST /food-recognition/recognize | AI 食物照片识别 |
| | GET /food-recognition/history | 识别历史 |
| **知识搜索** | GET /knowledge/search, /docs | 搜索知识库 |
| **消息** | GET /messages/inbox, /unread-count | 查看收件箱 |
| | POST /messages/{id}/read | 标记已读 |
| **提醒** | GET /reminders/my | 查看我的提醒 |
| **分段权限** | GET /segments/my-segment, /features | 查看我的分段和权限 |
| **专家入驻** | POST /expert-registration/apply | 可申请专家入驻 |
| | GET /expert-registration/my-application | 查看申请状态 |
| **行为处方** | GET /rx/user-history | 查看行为处方历史 |

#### 成长者关键里程碑

| 里程碑 | 触发条件 | 奖励 |
|-------|---------|------|
| 首次签到 | DAY_1 checkin | +5 成长积分 |
| 3天连签 | DAY_3 streak | 徽章 + 翻牌 |
| 7天连签 | DAY_7 streak | 徽章 + 翻牌 |
| 学习1小时 | 60分钟 | +10 积分 |
| 学习3小时 | 180分钟 | +20 积分 |
| 学习10小时 | 600分钟 | +50 积分 |
| 首次评估 | assessment_completed | 解锁行为画像 |
| 积分满100 | growth_points ≥ 100 | 触发L1→L2晋级检查 |

---

### 3.3 Sharer 分享者 (L2)

**角色定位**：有能力分享经验和知识

**晋级条件**：成长≥500 + 贡献≥50

#### 新增服务（在 Grower 基础上）

| 服务类别 | 可用端点 | 说明 |
|---------|---------|------|
| **内容贡献** | POST /content-contributions/submit | 提交原创内容（admin审核） |
| | GET /content-contributions/my, /my/{id} | 查看我的贡献 |
| | PUT /content-contributions/my/{id} | 更新贡献 |
| **知识共享** | POST /knowledge-sharing/contribute | 向领域共享知识（需tenant） |
| | GET /knowledge-sharing/my-contributions | 我的知识贡献 |

> 注：当前后端 API 层面 sharer 与 grower 的唯一差别在于内容贡献相关端点的访问。

---

### 3.4 Coach 行为健康教练 (L3)

**角色定位**：提供专业健康教练服务

**晋级条件**：成长≥800 + 贡献≥200 + 影响≥50 + 认证考核 + 带教4名L1成长者

#### 新增服务（在 Sharer 基础上）

| 服务类别 | 可用端点 | 说明 |
|---------|---------|------|
| **学员管理** | GET /coach/dashboard | 教练工作台（聚合数据） |
| | GET /coach/students, /{id} | 学员列表和详情 |
| | GET /coach/students/{id}/behavioral-profile | 学员行为画像 |
| | GET /coach/students/{id}/assessment-detail | 学员评估详情 |
| | GET /coach/students/{id}/glucose, /sleep, /activity, /vitals | 学员健康数据 |
| | GET /coach/performance | 教练绩效统计 |
| | GET /coach/my-certification | 认证信息 |
| | GET /coach/my-tools-stats | 工具使用统计 |
| **教练消息** | POST /coach/messages | 向学员发送消息 |
| | GET /coach/messages/{student_id} | 与学员的消息历史 |
| | GET /coach/students-with-messages | 有消息往来的学员 |
| **评估管理** | POST /assessment-assign/assign | 指派评估给学员 |
| | GET /assessment-assign/coach/pending-reviews | 待审核评估 |
| | POST /assessment-assign/review/{id} | 审核评估结果 |
| | POST /assessment-assign/push/{id} | 推送个性化建议 |
| **设备警报** | GET /device-alerts/coach | 学员设备警报 |
| **推送审批** | GET /coach/push-queue/, /stats | 推送审批队列 |
| | POST /coach/push-queue/{id}/approve, /reject | 审批/拒绝推送 |
| | POST /coach/push-queue/batch-approve | 批量审批 |
| | PUT /coach/push-queue/{id} | 编辑待审批条目 |
| **推送建议** | POST /push-recommendations/submit | 提交AI推送建议 |
| | GET /push-recommendations/queue | 推送建议队列 |
| | POST /push-recommendations/{id}/approve, /reject | 审批推送建议 |
| **挑战管理** | POST /challenges | 创建挑战模板 |
| | PUT /challenges/{id} | 编辑挑战 |
| | POST /challenges/{id}/submit-review | 提交审核 |
| | POST /challenges/{id}/pushes | 添加每日推送内容 |
| | PUT/DELETE /challenges/pushes/{id} | 编辑/删除推送 |
| | POST /coach/challenges/assign | 为学员指派挑战 |
| | GET /coach/challenges/students/{id} | 查看学员挑战进度 |
| **提醒管理** | POST /reminders | 创建提醒 |
| | PUT/DELETE /reminders/{id} | 编辑/删除提醒 |
| **教练积分** | GET /learning/coach/points/{id}, /history | 三维积分查看 |
| | POST /learning/coach/points/add | 记录教练积分 |
| **同道者带教** | POST /companions/invite | 邀请同道者 |
| **内容审核** | GET /content/review/queue | 内容审核队列 |
| | POST /content/review/submit | 提交审核决定 |
| **内容管理** | POST/PUT/DELETE /content-manage/* | 创建/编辑/发布/删除内容 |
| **考试管理** | POST /certification/exams | 创建考试 |
| | PUT/DELETE /certification/exams/{id} | 编辑/删除考试 |
| | POST /exams/{id}/questions, /publish | 分配题目/发布 |
| **题库管理** | POST /certification/questions | 创建题目 |
| | PUT/DELETE /questions/{id} | 编辑/删除题目 |
| **问卷管理** | POST /surveys | 创建问卷 |
| | GET /surveys, /{id} | 问卷列表和详情 |
| | PATCH/DELETE /surveys/{id} | 编辑/删除问卷 |
| | POST /surveys/{id}/publish, /close | 发布/关闭 |
| | POST /surveys/{id}/questions | 批量保存题目 |
| **知识上传** | POST /knowledge/batch-upload | 批量上传知识文档 |
| | GET /knowledge/batch-jobs, /{id} | 上传任务进度 |
| **教练分析** | GET /analytics/coach/risk-trend | 学员风险趋势 |
| | GET /analytics/coach/micro-action-trend | 微行动完成率趋势 |
| | GET /analytics/coach/domain-performance | 领域表现雷达图 |
| | GET /analytics/coach/alert-frequency | 警报频率统计 |
| | GET /analytics/coach/challenge-stats | 挑战参与统计 |
| | GET /analytics/coach/stage-distribution | 学员阶段分布 |
| **全局搜索** | GET /search | 全平台搜索（用户/挑战/微行动/警报/消息） |
| **行为处方** | POST /rx/compute, /collaborate, /handoff | 行为处方计算/协作/交接 |
| | GET /rx/strategies, /agents-status, /handoff-logs | 策略/Agent状态/交接日志 |

---

### 3.5 Promoter 促进师 / Supervisor 督导 (L4)

**角色定位**：高级教练，带领团队/专业督导

**晋级条件**：成长≥1500 + 贡献≥600 + 影响≥200 + 认证考核 + 带教4名L2分享者

#### 与 Coach 的差异

| 差异点 | 说明 |
|-------|------|
| 挑战终审 | 可作为 reviewer2（最终审批者），L3 仅可 reviewer1 |
| 带教级别 | 可带教 L3 教练（coach 只能带教 L1 成长者） |
| 同等权限 | 其余 API 端点与 coach 完全相同 |

> **注意**：promoter 和 supervisor 在代码层面权限完全等价（ROLE_LEVEL=5）。两者定义的功能区分（促进 vs 督导）尚未在 API 层实现。

---

### 3.6 Master 行为健康促进大师 (L5)

**角色定位**：行为健康促进大师，行业标杆

**晋级条件**：成长≥3000 + 贡献≥1500 + 影响≥600 + 认证考核 + 带教4名L3教练

#### 与 Promoter 的差异

| 差异点 | 说明 |
|-------|------|
| 带教级别 | 可带教 L4 促进师 |
| 同等权限 | 其余 API 端点与 promoter/coach 完全相同 |

> Master 是六级体系的最高等级，享有与 coach 相同的全部功能权限，差异主要体现在带教层级和社会荣誉。

---

## 4. 轨道二：专家入驻轨（Expert Track）

### 4.1 入驻流程

```
GROWER+ ──► 提交入驻申请 ──► Admin 审核 ──► 批准
               │                                │
               │ POST /expert-registration/apply │
               │ 5步资料（品牌/专业/个人/工作/银行）│
               │                                ▼
               │                         角色升级为 COACH
               │                         创建 ExpertTenant
               │                         状态 pending_review → trial
               │                                │
               │                                ▼
               │                    解锁专家轨独有功能 ↓
               └────────────────────────────────┘
```

### 4.2 专家独有服务（有 ExpertTenant 的 coach+）

| 服务类别 | 端点数 | 可用端点 | 说明 |
|---------|--------|---------|------|
| **租户管理** | 12 | GET /tenants/mine | 我的租户信息 |
| | | GET /tenants/{tid} | 租户详情 |
| | | PATCH /tenants/{tid} | 更新品牌/配置 |
| | | GET /tenants/{tid}/clients | 客户列表 |
| | | POST /tenants/{tid}/clients | 添加客户 |
| | | PATCH /tenants/{tid}/clients/{cid} | 更新客户状态 |
| | | GET /tenants/{tid}/stats | 客户统计 |
| | | GET /tenants/{tid}/routing | 路由配置 |
| | | PUT /tenants/{tid}/routing | 更新路由配置 |
| | | POST /tenants/{tid}/routing/test | 路由测试(dry-run) |
| **自定义 Agent** | 6 | POST /tenants/{tid}/my-agents/create | 创建动态LLM Agent |
| | | GET /tenants/{tid}/my-agents/list | Agent 列表 |
| | | PUT /tenants/{tid}/my-agents/{aid} | 更新 Agent |
| | | POST /tenants/{tid}/my-agents/{aid}/toggle | 启停 Agent |
| | | POST /tenants/{tid}/my-agents/test-routing | 路由测试对比 |
| | | DELETE /tenants/{tid}/my-agents/{aid} | 删除自定义 Agent |
| **内容工作室** | 8 | GET /expert-content/documents | 专家文档列表 |
| | | POST /expert-content/documents | 创建文档 |
| | | GET /expert-content/documents/{id} | 文档详情 |
| | | PUT /expert-content/documents/{id} | 更新文档 |
| | | POST /expert-content/documents/{id}/publish | 发布（生成embedding） |
| | | POST /expert-content/documents/{id}/unpublish | 撤回发布 |
| | | DELETE /expert-content/documents/{id} | 删除文档 |
| | | GET /expert-content/challenges | 专家挑战列表 |
| **知识共享** | 9 | POST /knowledge-sharing/contribute | 向领域共享知识 |
| | | GET /knowledge-sharing/my-contributions | 我的知识贡献 |
| | | POST /knowledge-sharing/{id}/revoke | 撤回共享 |
| | | GET /knowledge-sharing/domain-pool | 领域知识池 |
| | | GET /knowledge-sharing/stats | 分享统计 |
| | | GET /knowledge-sharing/domains | 可共享领域 |
| **Agent 市场** | 7 | GET /agent-ecosystem/marketplace | 浏览市场 |
| | | POST /agent-ecosystem/marketplace/publish | 发布模板到市场 |
| | | POST /agent-ecosystem/marketplace/{id}/install | 安装市场模板 |
| | | GET /agent-ecosystem/marketplace/recommended | 推荐列表 |
| | | GET /agent-ecosystem/compositions, /{id} | 组合编排 |
| | | POST /agent-ecosystem/compositions | 创建组合 |
| **成长积分** | 2 | GET /agent-ecosystem/growth-points | 我的生态积分 |
| | | GET /agent-ecosystem/growth-points/config | 积分事件配置 |
| **Agent 反馈** | 5 | GET /agent-feedback/growth/{agent_id} | Agent 成长报告 |
| | | GET /agent-feedback/summary | 全Agent成长总览 |
| | | GET /agent-feedback/metrics/{agent_id} | Agent 每日指标 |
| | | GET /agent-feedback/prompt-versions/{agent_id} | Prompt版本历史 |

### 4.3 专家 vs 普通教练对比

| 能力 | 普通 Coach | Expert Coach |
|------|-----------|-------------|
| 学员管理 | ✅ | ✅ |
| AI 对话 | 平台默认路由 | 自定义 Agent + 路由覆盖 |
| 内容创建 | 平台内容管理 | +内容工作室（品牌化） |
| 知识库 | 使用平台知识 | +私有知识 + 领域共享 |
| Agent 定制 | 无 | 创建/编辑/启停自定义Agent |
| 品牌展示 | 无 | 品牌名/头像/配色/主题 |
| 客户管理 | 通过同道者关系 | 专属客户绑定/毕业/统计 |
| 市场参与 | 无 | 发布/安装/评价 Agent |
| 路由控制 | 无 | keyword_boost/correlation/conflict 覆盖 |

### 4.4 租户路由机制

```
用户发起 AI 对话 → resolve_tenant_ctx()
                     │
  ┌──────────────────┼──────────────────┐
  ▼                  ▼                  ▼
用户是专家         用户是客户         普通用户
(ExpertTenant      (TenantClient     (返回 None)
 .expert_user_id)   .user_id)
  │                  │                  │
  ▼                  ▼                  ▼
自己的 tenant       所属专家的         平台默认
routing config      tenant config      AgentRouter
```

---

## 5. 轨道三：管理运营轨（Admin Track）

### 5.1 Admin 独有服务（require_admin）

| 服务类别 | 端点数 | 关键端点 |
|---------|--------|---------|
| **用户管理** | 13 | CRUD /admin/users/*, 分配/转移/启停 |
| **安全管理** | 8 | /safety/dashboard, /logs, /review-queue, /config, /reports |
| **策略引擎(写)** | 6 | /policy/rules CRUD, /seed, /refresh |
| **Agent 模板** | 10 | /agent-templates/* CRUD, /toggle, /clone, /refresh-cache |
| **租户管理** | 8 | /tenants CRUD, /{tid}/clients, /agents, /stats |
| **学分管理** | 5 | /credits/admin/modules CRUD, /stats |
| **晋级审核** | 2 | /promotion/applications, /{id}/review |
| **入驻审核** | 4 | /expert-registration/admin/* (list/detail/approve/reject) |
| **同道者管理** | 2 | /companions/all, /{id}/graduate |
| **内容审核** | 3 | /content-contributions/review/* (pending/approve/reject) |
| **知识审核** | 3 | /knowledge-sharing/review-queue, /approve, /reject |
| **市场审核** | 3 | /agent-ecosystem/marketplace/pending, /approve, /reject |
| **分段管理** | 7 | /segments/all, /compute, /stats, /definitions, /rules, /{id}/* |
| **考试管理** | 7 | /certification/exams CRUD, /questions, /publish |
| **问卷统计** | 3 | /survey-stats/{id}/stats, /responses, /export-csv |
| **方案管理** | 5 | /programs/templates CRUD, /admin/analytics, /enrollments |
| **知识统计** | 1 | /knowledge/stats |
| **提醒管理** | 1 | /reminders/admin/all |
| **反馈管理** | 2 | /agent-feedback/prompt-version, /aggregate |
| **管理分析** | 7 | /analytics/admin/* (overview/growth/role/stage/risk/coach/challenge) |

### 5.2 Admin 分析仪表盘

| 端点 | 数据 | 图表类型 |
|------|------|---------|
| GET /analytics/admin/overview | 总用户/活跃/教练数/高风险数 | KPI 卡片 |
| GET /analytics/admin/user-growth | 月度新增+累计 | 柱状+折线 |
| GET /analytics/admin/role-distribution | 各角色用户数 | 饼图 |
| GET /analytics/admin/stage-distribution | TTM S0-S6 分布 | 柱状图 |
| GET /analytics/admin/risk-distribution | R0-R4 风险分布 | 环形图 |
| GET /analytics/admin/coach-leaderboard | 教练绩效排名 | 横向柱状 |
| GET /analytics/admin/challenge-effectiveness | 挑战完成率 | 分组柱状 |

### 5.3 安全管理详情

```
SafetyPipeline 4层:
  L1 输入过滤 → 危机词/敏感词/PII 检测
  L2 RAG安全 → 源权威性/过期检查
  L3 生成守卫 → 注入攻击/领域边界
  L4 输出过滤 → 医疗声明/免责声明/分级

Admin 安全操作:
  ├── 仪表盘: 统计+趋势+分类饼图
  ├── 日志审查: 逐条查看 input/output/filter_details
  ├── 处理标记: resolved/false_positive/whitelist
  ├── 配置管理: 实时热更新关键词（crisis/warning/blocked/medical）
  └── 日报: 按日期查看统计（默认昨天）
```

---

## 6. 各角色端点权限完整矩阵

### 6.1 按守卫类型统计（522 端点）

| 守卫 | 端点数 | 占比 | 允许角色 |
|------|--------|------|---------|
| `get_current_user` | 298 | 57.1% | 所有认证用户（observer→admin） |
| `require_admin` | 141 | 27.0% | 仅 admin |
| `require_coach_or_admin` | 68 | 13.0% | coach/promoter/supervisor/master/admin |
| Public (无守卫) | 15 | 2.9% | 任何人（含匿名） |

### 6.2 功能域分配矩阵

| 功能域 | Observer (L0) | Grower (L1) | Sharer (L2) | Coach (L3) | L4/L5 | Expert | Admin |
|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 浏览内容 | 19 | 19 | 19 | 19 | 19 | 19 | 19 |
| AI对话 | — | 5 | 5 | 5 | 5 | 5 | 5 |
| 设备+健康数据 | — | 30 | 30 | 30 | 30 | 30 | 30 |
| 评估+微行动 | — | 12 | 12 | 12 | 12 | 12 | 12 |
| 方案参与 | — | 7 | 7 | 7 | 7 | 7 | 7 |
| 挑战参与 | — | 9 | 9 | 9 | 9 | 9 | 9 |
| 学习+激励 | — | 20 | 20 | 20 | 20 | 20 | 20 |
| 晋级+学分 | — | 9 | 9 | 9 | 9 | 9 | 9 |
| 内容贡献 | — | — | 4 | 4 | 4 | 4 | 4 |
| 学员管理 | — | — | — | 12 | 12 | 12 | 12 |
| 教练消息 | — | — | — | 6 | 6 | 6 | 6 |
| 评估指派审核 | — | — | — | 5 | 5 | 5 | 5 |
| 推送审批 | — | — | — | 11 | 11 | 11 | 11 |
| 挑战管理 | — | — | — | 8 | 8 | 8 | 8 |
| 内容管理 | — | — | — | 7 | 7 | 7 | 7 |
| 考试+题库 | — | — | — | 12 | 12 | 12 | 12 |
| 问卷管理 | — | — | — | 10 | 10 | 10 | 10 |
| 教练分析 | — | — | — | 6 | 6 | 6 | 6 |
| 全局搜索 | — | — | — | 1 | 1 | 1 | 1 |
| 行为处方 | — | — | — | 6 | 6 | 6 | 6 |
| 租户管理 | — | — | — | — | — | 12 | 8 |
| 自定义Agent | — | — | — | — | — | 6 | — |
| 内容工作室 | — | — | — | — | — | 8 | — |
| 市场参与 | — | — | — | — | — | 7 | 3 |
| 用户管理 | — | — | — | — | — | — | 13 |
| 安全管理 | — | — | — | — | — | — | 8 |
| 策略引擎(写) | — | — | — | — | — | — | 6 |
| Agent模板 | — | — | — | — | — | — | 10 |
| 管理分析 | — | — | — | — | — | — | 7 |
| **可用端点总计** | **~19** | **~130** | **~134** | **~203** | **~203** | **~249** | **~371** |

### 6.3 公开端点清单（15个）

| 端点 | 用途 |
|------|------|
| POST /auth/register | 用户注册 |
| POST /auth/login | 用户登录 |
| POST /auth/refresh | 刷新令牌 |
| GET /coach/directory | 教练/专家公开目录 |
| GET /high-freq/presets, /all, /by-ids, /{preset} | 高频问卷（4个） |
| GET /knowledge/domains | 知识领域列表 |
| GET /learning/leaderboard/coaches, /growers | 排行榜（2个） |
| GET /coach-levels/levels, /modules | 六级体系说明（2个） |
| GET /expert-registration/domains | 可入驻领域 |
| POST /device-trigger/cgm/sync | CGM 设备数据同步触发 |
| POST /reminders/{id}/fire | 提醒触发 webhook |
| GET/POST /survey-responses/{short_code}/* | 问卷填写（3个） |

---

## 7. 课程模块与学分体系

### 7.1 课程模块总览

| 等级 | 必修模块数 | 必修总学分 | 选修最低 | 累计总学分 |
|------|-----------|-----------|---------|-----------|
| L0 Observer | 9 | 60 | 40 | 100 |
| L1 Grower | 11 | 120 | 80 | 200 |
| L2 Sharer | 11 | 220 | 580* | 800 |
| L3 Coach | 16 | 450 | 1050* | 1500 |
| L4 Promoter | 15 | 700 | 2300* | 3000 |
| L5 Master | 14 | 1200+ | — | 3000+ |

> *选修学分为累计值含之前等级

### 7.2 四大模块类型 × 三级学分层

| 模块类型 | 代码 | 内容方向 |
|---------|------|---------|
| M1 行为 | M1_BEHAVIOR | 行为链、行为处方、行为解构 |
| M2 生活方式 | M2_LIFESTYLE | 健康数据、营养、运动、睡眠、压力 |
| M3 心智 | M3_MINDSET | 思维、身份、生命哲学、成长叙事 |
| M4 教练 | M4_COACHING | 教练技术、MI、TTM、伦理、督导 |

| 学分层 | 代码 | 定位 |
|-------|------|------|
| 处方级 | T1_PRESCRIPTION | 行为诊断与干预 |
| 健康级 | T2_HEALTH | 健康数据与生活方式 |
| 成长级 | T3_GROWTH | 心理成长与意义建构 |

### 7.3 代表性必修课程（每级前3名）

| 等级 | 课程 | 学分 | 模块 |
|------|------|------|------|
| **L0** | 五维度微行为体验 | 10 | M2 |
| | 7天行为挑战体验 | 10 | M1 |
| | CGM/体成分/睡眠基线建立 | 10 | M2 |
| **L1** | 运动节律与睡眠重建 | 15 | M2 |
| | 21天行为链觉察训练 | 15 | M1 |
| | 压力管理与认知训练 | 15 | M2 |
| **L2** | 同伴支持技术(40学时) | 30 | M4 |
| | 行为类型识别 | 20 | M1 |
| | 五维度经验分享方法论 | 20 | M2 |
| **L3** | 10大高风险场景实操 | 40 | M1 |
| | 动机访谈精通(MI) | 40 | M4 |
| | 行为处方设计方法论 | 30 | M1 |
| **L4** | 师资培训课程设计 | 60 | M4 |
| | 行为干预项目设计 | 50 | M1 |
| | 生活方式医学系统论 | 50 | M2 |
| **L5** | 教练体系架构设计 | 100 | M4 |
| | 认证标准体系建设 | 100 | M4 |
| | 公共卫生政策与行为健康 | 90 | M2 |

### 7.4 选修类别（7类）

| 类别 | 学分范围 | 层级 | 示例 |
|------|---------|------|------|
| 临床专科 | 5-30 | T1 | 糖尿病行为干预、高血压行为管理 |
| 营养深度 | 5-20 | T2 | 功能营养学、稳糖膳食设计 |
| 运动科学 | 5-20 | T2 | 运动处方设计、运动心理学 |
| 心理学 | 5-25 | T3 | 健康心理学、积极心理学 |
| 教练技术 | 5-25 | T2 | NLP技术、非暴力沟通、ICF框架 |
| 人文社会 | 5-15 | T3 | 公共卫生导论、医学伦理 |
| 场景专题 | 10-20 | T1 | 情绪性进食、家庭冲突、职场嵌入 |

---

## 8. AI Agent 服务分配

### 8.1 Agent 可用性（按角色）

| Agent | 类型 | Observer | Grower+ | Coach+ | Expert |
|-------|------|:--------:|:-------:|:------:|:------:|
| crisis | 核心-专科 | ❌ | ✅ | ✅ | ✅ (不可禁用) |
| metabolic | 核心-专科 | ❌ | ✅ | ✅ | ✅ |
| sleep | 核心-专科 | ❌ | ✅ | ✅ | ✅ |
| emotion | 核心-专科 | ❌ | ✅ | ✅ | ✅ |
| motivation | 核心-专科 | ❌ | ✅ | ✅ | ✅ |
| coaching | 核心-专科 | ❌ | ✅ | ✅ | ✅ |
| nutrition | 核心-专科 | ❌ | ✅ | ✅ | ✅ |
| exercise | 核心-专科 | ❌ | ✅ | ✅ | ✅ |
| tcm | 核心-专科 | ❌ | ✅ | ✅ | ✅ |
| behavior_rx | 核心-整合 | ❌ | ✅ | ✅ | ✅ |
| weight | 核心-整合 | ❌ | ✅ | ✅ | ✅ |
| cardiac_rehab | 核心-整合 | ❌ | ✅ | ✅ | ✅ |
| BehaviorCoach | BehaviorRx | ❌ | ✅(S0-S2) | ✅ | ✅ |
| MetabolicExpert | BehaviorRx | ❌ | ✅ | ✅ | ✅ |
| CardiacExpert | BehaviorRx | ❌ | ✅ | ✅ | ✅ |
| AdherenceExpert | BehaviorRx | ❌ | ✅ | ✅ | ✅ |
| GenericLLMAgent | 动态模板 | ❌ | 视配置 | 视配置 | ✅(自建) |

### 8.2 Agent 路由差异

| 用户类型 | 路由方式 | 特殊处理 |
|---------|---------|---------|
| 普通 Grower | 平台默认 AgentRouter | 标准关键词匹配 |
| Expert 客户 | 专家的 tenant routing config | keyword_boost + 自定义关联 |
| Expert 本人 | 自己的 tenant routing config | 自定义 Agent 优先 |
| Admin | 平台默认 | 同普通用户 |

### 8.3 安全管线（所有用户统一）

```
所有 AI 对话均经过:
  V005 SafetyPipeline (4层) → 安全过滤
  V007 PolicyEngine (5步) → 规则/成本/冲突控制
  BehaviorRx Step 3.5 → TTM阶段适配（如适用）
```

---

## 9. 端点统计与守卫分布

### 9.1 按路由文件统计

| 文件 | 端点数 | 主要守卫 | 服务对象 |
|------|--------|---------|---------|
| content_api.py | 28 | get_current_user + require_coach_or_admin | 全员+教练 |
| challenge_api.py | ~30 | get_current_user + require_coach_or_admin | 全员+教练 |
| device_data.py | 21 | get_current_user | grower+ |
| user_api.py | 13 | require_admin | admin |
| program_api.py | 13 | get_current_user + require_admin | 全员+admin |
| coach_api.py | 12 | require_coach_or_admin | coach+ |
| learning_api.py | 15 | get_current_user + require_admin | 全员+admin |
| tenant_api.py | 12 | mixed | expert+admin |
| agent_template_api.py | 10 | require_admin | admin |
| survey_api.py | 10 | require_coach_or_admin | coach+ |
| knowledge_sharing_api.py | 9 | mixed | expert+admin |
| safety_api.py | 8 | require_admin | admin |
| credits_api.py | 9 | mixed | 全员+admin |
| expert_content_api.py | 8 | get_current_user (tenant check) | expert |
| policy_api.py | 12 | mixed | 全员+admin |
| exam_api.py | 7 | require_coach_or_admin | coach+admin |
| agent_ecosystem_api.py | 11 | mixed | expert+admin |
| expert_agent_api.py | 6 | require_coach_or_admin (tenant check) | expert |
| admin_analytics_api.py | 7 | require_admin | admin |
| analytics_api.py | 6 | require_coach_or_admin | coach+ |
| 其余 33 文件 | ~265 | 各异 | 各异 |
| **总计** | **522** | — | — |

### 9.2 权限守卫三级结构

```
Level 1: Public (15端点, 2.9%)
  └── 注册/登录/刷新 + 排行榜 + 六级体系 + 问卷填写

Level 2: get_current_user (298端点, 57.1%)
  └── 所有认证用户 (observer → admin)
  └── 实际上 observer 能调用大部分端点（缺乏 L1+ 拦截）

Level 3a: require_coach_or_admin (68端点, 13.0%)
  └── coach(L3) / promoter(L4) / supervisor(L4) / master(L5) / admin(L99)

Level 3b: require_admin (141端点, 27.0%)
  └── 仅 admin(L99)
```

### 9.3 权限缺口提示

| 缺口 | 现状 | 建议 |
|------|------|------|
| observer ↔ grower | 后端无区分，observer 可调用 grower 级端点 | 新增 `require_grower` 守卫 |
| grower ↔ sharer | 仅内容贡献端点有隐式区分 | 内容贡献端点加 `require_sharer` |
| coach ↔ promoter | 完全相同权限 | 挑战终审加 `require_promoter` |
| promoter ↔ master | 完全相同权限 | 按需增加 master 独有功能 |

---

## 附录：晋级四维检查详细要求

### 晋级规则速查表

| 晋级路径 | 学分要求 | 积分要求 | 同道者要求 | 实践要求 | 理论:实践 | 参考周期 |
|---------|---------|---------|-----------|---------|----------|---------|
| L0→L1 | 总100(必60) | g≥100 | 邀请4名observer | 15次行为尝试, 理解≥4, 伦理通过 | 8:2 | ~3月 |
| L1→L2 | 总200(必120) | g≥300, c≥30, i≥10 | 带教4名observer | 90天稳定, 2+指标改善, 完成S0-S4 | 7:3 | ~3月 |
| L2→L3 | 总800(必380) | g≥800, c≥100, i≥50 | 带教4名grower, 质量≥3.5 | 240+分案例, 10+案例研究, 可解释≥0.8, 伦理100/100 | 5:5 | ~10月 |
| L3→L4 | 总1500(必690) | g≥1500, c≥500, i≥200 | 带教4名sharer, 质量≥4.0, 培养≥5名L3 | 2+项目, 1+课程, 2+模板被采用 | 4:6 | ~15月 |
| L4→L5 | 总3000(必1200) | g≥3000, c≥1500, i≥800 | 带教4名coach, 质量≥4.5, 培养≥15名L3+4名L4 | 原创方法论, 标准参与, 专家一致通过 | 3:7 | ~24月 |

> g=成长积分, c=贡献积分, i=影响力积分
> 学分 M1(行为) / M2(生活方式) / M3(心智) / M4(教练) 均有最低要求

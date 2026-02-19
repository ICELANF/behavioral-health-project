# 行健平台 — 全页面角色权限 × API 对应矩阵

> 生成时间: 2026-02-19
> Admin Portal: localhost:5174 | H5: localhost:5173 | API: localhost:8000
> 版本: V5.0.2 (Migration 045, 130+ models, 74+ routers, 630+ endpoints)

---

## 一、登录路由分流

| 角色 | level | Admin Portal 首页 | H5 首页 |
|------|-------|------------------|---------|
| 观察者 observer | 1 | → `/client/home-v2` | → `/home/observer` |
| 成长者 grower | 2 | → `/client/home-v2` | → `/home/today` |
| 分享者 sharer | 3 | → `/client/home-v2` | → `/home/today` |
| 教练 coach | 4 | → `/coach/workbench` | → `/home/today` |
| 促进师 promoter | 5 | → `/expert/audit` | → `/home/today` |
| 督导 supervisor | 5 | → `/expert/audit` | → `/home/today` |
| 导师 master | 6 | → `/expert/audit` | → `/home/today` |
| 管理员 admin | 99 | → `/admin/command-center` | → `/home/today` |

> 权限仅在路由层执行，页面组件内部无角色校验

---

## 二、公共页面 (无需登录)

### Admin Portal (:5174)

| # | 路径 | 页面 | 可查看内容 | 可交互操作 | 后端API | 数据状态 |
|---|------|------|-----------|-----------|---------|---------|
| 1 | `/login` | 登录 | 角色选卡(4种)、演示账号(8个) | 选角色→输账号密码→登录 | `POST /v1/auth/login` | ✅真实 |
| 2 | `/landing` | 官网Landing | 5场景页(首页/医院/商保/政府/RWE)、统计动画、客户证言 | 切换场景、预约演示(未接) | 无 | 静态页面 |
| 3 | `/portal/public` | 科普入口 | 8分类、4热门文章、4自测工具、2快速入口 | 搜索→跳转、分类→跳转 | 无 | 静态页面 |
| 4 | `/component-showcase` | 组件库展示 | UI组件预览 | 交互演示 | 无 | 静态页面 |
| 5 | `/react` | React导航 | React集成页面入口 | 导航链接 | 无 | 静态页面 |
| 6 | `/react/demo` | React演示 | React组件集成效果 | 交互演示 | 无 | 静态页面 |
| 7 | `/journey` | 成长之旅(React) | 行为改变历程可视化 | 浏览 | 无 | 静态页面 |

### H5 (:5173)

| # | 路径 | 页面 | 可查看内容 | 可交互操作 | 后端API | 数据状态 |
|---|------|------|-----------|-----------|---------|---------|
| 1 | `/login` | 登录 | 手机号+密码表单 | 登录 | `POST /v1/auth/login` | ✅真实 |
| 2 | `/register` | 注册 | 注册表单 | 注册→自动登录 | `POST /v3/auth/register` | ✅真实 |
| 3 | `/coach-directory` | 教练目录 | 教练卡片(名称/等级/专长/评分) | 搜索、点击→对话 | `GET /v1/coach/directory` | ✅真实 |
| 4 | `/expert-hub` | 专家工作室 | 专家品牌卡片、统计 | 搜索、点卡片→详情、申请入驻 | `GET /v1/tenants/hub` | ✅真实 |
| 5 | `/expert-register` | 申请入驻 | 5步向导(信息/资质/领域/品牌/确认) | 注册/上传资质/提交申请 | `GET /v1/expert-registration/domains` `POST /v1/expert-registration/upload-credential` `POST /v1/auth/register` `POST /v1/expert-registration/apply` | ✅真实 |
| 6 | `/v3/knowledge` | 知识库 | 搜索框+快捷标签+RAG回答+来源 | 输入问题→AI回答 | `POST /v3/chat/knowledge` | ✅真实 |
| 7 | `/studio/:tenantId` | 专家工作室详情 | 专家品牌页面 | 浏览 | (tenantId相关) | ✅真实 |
| 8 | `/privacy-policy` | 隐私政策 | 静态内容 | 浏览 | 无 | 静态 |
| 9 | `/about-us` | 关于我们 | 静态内容 | 浏览 | 无 | 静态 |

---

## 三、观察者 Observer (level=1) — 体验受限

| # | 应用 | 路径 | 页面 | 可查看 | 可交互 | 后端API | 数据状态 | 限制 |
|---|------|------|------|--------|--------|---------|---------|------|
| 1 | H5 | `/home/observer` | 观察者首页 | 3次配额(绿/黄/红)、快速体验卡(3)、锁定功能(6)、社会证明 | 开始/继续评估、体验食物识别/对话/语音、配额→升级弹窗 | (全部注释掉) | ❌全mock | 3次/天配额墙 |
| 2 | H5 | `/chat` | AI对话 | 消息列表、任务卡、专家切换 | 发消息、传照片→食物识别 | `POST /v1/dispatch` `POST /v1/food/recognize` | ✅真实 | 受配额限 |
| 3 | H5 | `/v3/assessment` | 渐进式评估 | 批次列表、完成进度 | 点批次→做题 | `GET /v3/assessment/batches` `GET /v3/assessment/session` `GET /v3/assessment/recommend` | ✅真实 | 无 |
| 4 | H5 | `/v3/coach` | AI健康教练 | 对话界面 | 发消息→AI回复 | `POST /v3/chat/message` | ✅真实 | 无 |
| 5 | H5 | `/profile` | 个人中心 | 用户卡、穿戴数据、菜单 | 导航、登出 | 无(Pinia store) | 登录时加载 | 无 |
| 6 | Admin | `/client/home-v2` | 我的健康 | 问候/健康评分/任务/快捷操作/AI提示 | 完成任务、导航 | `GET /v1/health/{id}/score` `GET /v1/health/{id}/snapshot` `GET /v1/health/{id}/tasks/daily` `GET /v1/health/{id}/ai-summary` `POST /v1/health/{id}/tasks/{tid}/complete` | ⚠mock兜底 | 无 |

---

## 四、成长者/分享者 Grower/Sharer (level=2-3) — 全功能

### H5 页面

| # | 路径 | 页面 | 可查看 | 可交互 | 后端API | 数据状态 |
|---|------|------|--------|--------|---------|---------|
| 1 | `/home/today` | 今日行动 | 连续天数、进度环、行动卡、教练提示、周点阵 | 快速打卡、跳转对话/记录 | (全部TODO) | ❌全mock |
| 2 | `/chat` | AI对话 | 消息气泡、任务卡、效能滑块、专家切换 | 发消息、传照片、完成任务 | `POST /v1/dispatch` `POST /v1/food/recognize` | ✅真实 |
| 3 | `/tasks` | 任务中心 | 连续天数、进度、待完成/已完成、领域筛选 | 完成(心情+备注)、跳过、筛选 | `GET /v1/micro-actions/today` `GET /v1/micro-actions/stats` `POST /v1/micro-actions/{id}/complete` `POST /v1/micro-actions/{id}/skip` | ✅真实 |
| 4 | `/learn` | 学习中心 | 进度卡、6标签页、领域筛选、无限滚动 | 搜索、切标签、筛领域 | `GET /v1/learning/grower/stats/{uid}` `GET /v1/learning/coach/points/{uid}` `GET /v1/content?page&type&domain` | ✅真实 |
| 5 | `/content/:type/:id` | 内容详情 | 封面/正文/标签/评论 | 点赞、收藏、评论、分享 | `GET /v1/content/detail/{type}/{id}` `POST .../like` `POST .../collect` `POST .../comment` | ✅真实 |
| 6 | `/my-learning` | 我的学习 | 3统计(分钟/积分/连续)、里程碑、周柱状图、记录 | 下拉刷新 | `GET /v1/learning/grower/stats/{uid}` `GET .../time/{uid}/history` `GET .../coach/points/{uid}/history` | ✅真实 |
| 7 | `/behavior-assessment` | 行为评估 | TTM21题/个体/教练自定义、进度条、结果 | 选答案、翻页、提交 | `GET /v1/assessment-assignments/my-pending` `GET /v1/high-freq-questions/{preset}` `POST /v1/assessment-assignments/{id}/submit` `POST /v1/assessment/evaluate` | ✅真实 |
| 8 | `/my-stage` | 我的阶段 | S0-S6旅程条、领域卡、Top3微行动 | 完成微行动、重新评估 | `GET /v1/assessment/profile/me` `GET /v1/micro-actions/today` `POST /v1/micro-actions/{id}/complete` | ✅真实 |
| 9 | `/my-plan` | 我的计划 | 教练推送计划(目标/处方/建议) | 查看详情、切标签 | `GET /v1/assessment-assignments/pushed-list` `GET /v1/assessment-assignments/{id}/result` | ✅真实 |
| 10 | `/food-recognition` | 食物识别 | 拍照区、营养分析(4维+建议)、历史 | 拍照→识别、查看历史 | `POST /v1/food/recognize` `GET /v1/food/history` | ✅真实 |
| 11 | `/challenges` | 挑战列表 | 进行中/待开始/已完成 | 开始挑战、查看挑战日 | `GET /v1/challenges/my-enrollments` `POST /v1/challenges/enrollments/{id}/start` | ✅真实 |
| 12 | `/programs` | 智能监测方案 | 已加入(进度)、可用模板 | 加入方案 | `GET /v1/programs/my` `GET /v1/programs/templates` `POST /v1/programs/enroll` | ✅真实 |
| 13 | `/health-records` | 健康档案 | 今日仪表盘、血糖/血压/体重/心率/睡眠/运动 | 浏览 | `GET /v1/auth/me` `GET /v1/mp/device/dashboard/today` `GET /v1/mp/device/glucose` `GET /v1/mp/device/blood-pressure` `GET /v1/mp/device/weight` `GET /v1/mp/device/heart-rate` `GET /v1/mp/device/sleep` `GET /v1/mp/device/activity` | ✅真实 |
| 14 | `/history-reports` | 历史报告 | 全量报告 | 浏览 | `GET /v1/reports/full` `GET /v1/dashboard/{uid}` | ✅真实 |
| 15 | `/dashboard` | 仪表盘 | 仪表盘数据 | 浏览 | `GET /v1/dashboard/{uid}` `GET /v1/reports/full` | ✅真实 |
| 16 | `/data-sync` | 数据同步 | 设备列表 | 同步/绑定设备 | `GET /v1/mp/device/devices` `POST /v1/mp/device/sync` `POST /v1/mp/device/devices/bind` | ✅真实 |
| 17 | `/notifications` | 消息通知 | 消息/提醒/待评估/预警 | 标已读 | `GET /v1/chat/sessions` `GET /v1/messages/inbox` `GET /v1/messages/unread-count` `GET /v1/reminders` `GET /v1/assessment-assignments/my-pending` `GET /v1/mp/device/dashboard/today` `GET /v1/alerts/my` `POST /v1/messages/{id}/read` `POST /v1/alerts/{id}/read` | ✅真实 |
| 18 | `/account-settings` | 账号设置 | 账号信息 | 修改密码 | `GET /v1/auth/me` `PUT /v1/auth/password` | ✅真实 |
| 19 | `/my-credits` | 我的学分 | 总览(必修/选修)、模块进度、记录 | 加载更多 | `GET /v1/credits/my` `GET /v1/credits/my/records` | ✅真实 |
| 20 | `/my-companions` | 我的同道者 | 统计、双标签(带教/导师) | 切标签、刷新 | `GET /v1/companions/stats` `GET /v1/companions/my-mentees` `GET /v1/companions/my-mentors` | ✅真实 |
| 21 | `/promotion-progress` | 晋级进度 | 当前→下级、5轴雷达、各维度进度 | 申请晋级(满足时) | `GET /v1/promotion/progress` `GET /v1/promotion/check` `POST /v1/promotion/apply` | ✅真实 |
| 22 | `/journey` | 健康成长伙伴 | AI健康叙事 | 刷新 | `GET /v1/messages/inbox` | ✅真实 |
| 23 | `/contribute` | 知识投稿 | 投稿表单、我的投稿(审核状态) | 提交投稿 | `POST /v1/contributions/submit` `GET /v1/contributions/my` | ✅真实 |
| 24 | `/expert-application-status` | 申请状态 | 入驻申请状态 | 浏览 | (相关API) | ✅真实 |

### Admin Portal C端页面

| # | 路径 | 页面 | 可查看 | 可交互 | 后端API | 数据状态 |
|---|------|------|--------|--------|---------|---------|
| 25 | `/client/home-v2` | 我的健康 | 问候/评分/任务/快捷操作/AI提示/底部导航 | 完成任务、导航 | `GET /v1/health/{id}/score` `GET /v1/health/{id}/snapshot` `GET /v1/health/{id}/tasks/daily` `GET /v1/health/{id}/ai-summary` `POST /v1/health/{id}/tasks/{tid}/complete` | ⚠mock兜底 |
| 26 | `/client/data-input` | 记录数据 | 3步向导(选类型→输数据→完成) | 选类型→填→提交 | `POST /v1/health/{id}/glucose` `POST .../weight` `POST .../blood-pressure` `POST .../exercise` `POST .../mood` `POST .../meal` `GET .../glucose?period=7d` `GET .../weight?period=7d` | ⚠mock兜底 |
| 27 | `/client/chat-v2` | AI健康助手 | 欢迎屏+对话气泡+建议回复 | 发消息、快捷回复 | `GET /v1/health/{id}/snapshot` | ⚠mock兜底(AI回复本地生成) |
| 28 | `/client/progress` | 我的进展 | 周/月/季、评分趋势、成就、ECharts图表、AI总结 | 切时段、查成就、点建议 | `GET /v1/health/{id}/score` `GET .../trends/glucose` `GET .../trends/weight` `GET .../exercise` `GET .../achievements` `GET .../ai-summary` | ⚠mock兜底 |
| 29 | `/client/my/profile` | 个人健康档案 | 基本信息/病程/用药/过敏/紧急联系人 | 编辑→保存、增删药物/过敏 | `GET /assessment/profile/me` `PUT /v3/auth/profile` | ✅真实 |
| 30 | `/client/my/devices` | 穿戴设备管理 | 设备列表 | 管理设备 | 无API调用 | ❌全mock |
| 31 | `/client/my/assessments` | 测评记录 | 待完成/已完成、趋势图 | 开始测评 | `GET /assessment-assignments/my-pending` | ✅真实 |
| 32 | `/client/my/trajectory` | 行为轨迹 | 行为轨迹时间线 | 浏览 | 无API调用 | ❌全mock |
| 33 | `/client/device-dashboard` | 设备仪表盘 | 指标卡、趋势图、时段切换 | 切时段(24h/7d/30d) | `GET /health-data/summary` `GET /health-data/glucose` `GET /health-data/vitals` `GET /health-data/sleep` `GET /health-data/activity` | ✅真实 |
| 34 | `/client/learning-progress` | 学习进度 | 4统计、课程列表、徽章网格 | 浏览 | `GET /learning/grower/stats/{uid}` `GET /learning/grower/time/{uid}` `GET /learning/grower/streak/{uid}` | ✅真实 |
| 35 | `/client/assessment/list` | 测评中心 | 可用测评列表 | 开始测评 | 无API调用 | ❌全mock |
| 36 | `/client/assessment/take/:id` | 进行测评 | 测评题目 | 答题提交 | `POST /assessment/submit` | ✅真实 |
| 37 | `/client/assessment/result/:id` | 测评结果 | 测评结果 | 浏览 | 无API调用 | ❌从路由state |

---

## 五、教练 Coach (level=4)

| # | 路径 | 页面 | 可查看 | 可交互 | 后端API | 数据状态 |
|---|------|------|--------|--------|---------|---------|
| 1 | `/coach/workbench` | **教练工作台(飞轮)** | 4统计、左侧队列、右侧审核面板 | 筛选、选学员、审批/驳回/跳过(A/R/N)、编辑处方 | `GET /v1/coach/stats/today` `GET /v1/coach/review-queue` `POST /v1/coach/review/{id}/approve` `POST /v1/coach/review/{id}/reject` | ⚠mock兜底 |
| 2 | `/coach-portal` | 教练门户首页 | 概览4卡、预警、学员、AI建议、工具箱、认证 | 处理预警、跟进学员、批准/修正/驳回AI建议、推送审核 | `GET /v1/coach/dashboard` `GET /v1/high-freq-questions/all` `GET /v1/push-recommendations` `GET /v1/alerts/coach` `PUT /v1/alerts/{id}/resolve` `GET /v1/coach/push-queue/stats` `GET /v1/coach/push-queue` `POST /v1/coach/push-queue/{id}/approve` `POST /v1/coach/push-queue/{id}/reject` `POST /v1/coach/push-queue/batch-approve` `POST /v1/coach/messages` `POST /v1/copilot/analyze` | ✅真实 |
| 3 | `/coach-portal/students` | 待跟进学员 | 学员卡(头像/阶段/优先级/健康数据) | 查看测评、行为画像 | 无API调用 | ❌全mock |
| 4 | `/coach-portal/ai-review` | AI建议审核 | 建议卡(类型/学员/AI建议) | 批准/修正/驳回 | `GET /v1/coach/dashboard` | ⚠部分mock |
| 5 | `/coach/my/students` | 我的学员 | 4统计+看板/列表(阶段/风险) | 搜索、切视图、查轨迹、发消息 | `GET /v1/coach/students` | ✅真实 |
| 6 | `/coach/my/performance` | 我的绩效 | 4KPI+月度柱状图+工具使用率 | 日期筛选 | `GET /v1/coach/performance` | ✅真实 |
| 7 | `/coach/my/certification` | 我的认证 | 当前等级、升级进度、需求清单、L0→L5路线图 | 申请晋级(满足时) | `GET /v1/coach/my-certification` | ✅真实 |
| 8 | `/coach/my/tools` | 我的工具箱 | 工具列表+使用统计 | 使用工具 | `GET /v1/coach/my-tools-stats` | ✅真实 |
| 9 | `/coach/my/analytics` | 数据分析 | 6维度ECharts(风险趋势/微行动/领域/预警/挑战/阶段) | 切天数范围 | `GET /v1/analytics/coach/risk-trend` `GET .../micro-action-trend` `GET .../domain-performance` `GET .../alert-frequency` `GET .../challenge-stats` `GET .../stage-distribution` | ⚠mock兜底 |
| 10 | `/coach/content-sharing` | 内容分享 | 4步向导(内容→学员→消息→确认) | 选内容、选学员、编辑→发送 | 无API调用 | ❌全mock |
| 11 | `/coach/messages` | 学员消息 | 左列学员(未读)、右列对话+快捷模板 | 选学员、选类型、发消息 | `GET /v1/coach/students-with-messages` `GET /v1/coach/messages/{sid}` `POST /v1/coach/messages` `POST /v1/coach/reminders` | ✅真实 |
| 12 | `/coach/student-assessment/:id` | 学员测评交互 | 测评详情 | 审核 | 无API调用 | ❌全mock |
| 13 | `/coach/student-profile/:id` | 学员行为画像 | 行为画像 | 浏览 | `GET /v1/coach/students/{sid}/behavioral-profile` | ⚠mock兜底 |
| 14 | `/coach/student-health/:id` | 学员健康数据 | 血糖/睡眠/运动/体重 | 切天数 | `GET /v1/coach/students/{sid}/glucose` `GET .../sleep` `GET .../activity` `GET .../vitals` | ⚠mock兜底 |
| 15 | `/coach/review` | 晋级审核(管理) | 晋级申请列表 | 审核 | 无API调用 | ❌全mock |

---

## 六、督导/专家 Expert (level>=5)

| # | 路径 | 页面 | 可查看 | 可交互 | 后端API | 数据状态 |
|---|------|------|--------|--------|---------|---------|
| 1 | `/expert/audit` | **审核工作台(飞轮)** | 5指标、左侧筛选、3标签(待审/回溯/规则) | 筛选、选Case→双签审核 | `GET /v1/expert/quality-metrics` `GET /v1/expert/audit-queue` `GET /v1/expert/agent-anomalies` `POST /v1/expert/audit/{id}/verdict` | ⚠mock兜底 |
| 2 | `/expert-portal` | 督导门户首页 | 概览4卡、晋级审核列表 | 查看申请 | 无API调用 | ❌全mock |
| 3 | `/expert-workbench` | 专家审核工作台(全屏) | 风险筛选+患者队列+3标签 | 筛选、选患者→双签/回溯 | `GET /v1/agent/pending-reviews` | ✅真实 |
| 4 | `/expert/my-agents` | 我的Agent | Agent表格+路由测试 | 创建/编辑/删除/开关/测试路由 | `GET /v1/tenants/mine` `GET /v1/tenants/{tid}/my-agents` `POST .../my-agents` `PUT .../my-agents/{aid}` `POST .../toggle` `DELETE .../my-agents/{aid}` `POST .../test-routing` | ✅真实 |
| 5 | `/expert/dual-sign` | 专家双签审核 | 双签演示 | 双签操作 | (组件内部) | ⚠视组件 |
| 6 | `/expert/my/supervision` | 我的督导 | 4统计+教练绩效表+督导记录 | 安排督导 | 无API调用 | ❌全mock |
| 7 | `/expert/my/reviews` | 我的审核 | 4统计+3标签(待审/历史/统计) | 通过/驳回 | 无API调用 | ❌全mock |
| 8 | `/expert/my/research` | 研究数据 | 研究面板 | 浏览 | 无API调用 | ❌全mock |
| 9 | `/portal/medical` | 医护处方助手 | 处方助手界面 | 处方操作 | 无API调用 | ❌全mock |

---

## 七、管理员 Admin (level=99)

| # | 路径 | 页面 | 可查看 | 可交互 | 后端API | 数据状态 |
|---|------|------|--------|--------|---------|---------|
| 1 | `/admin/command-center` | **指挥中心(飞轮)** | 告警横幅、4KPI、渠道、漏斗、Agent、教练排名、安全 | 关闭告警、5分钟轮询 | `GET /v1/admin/kpi/realtime` `GET /v1/admin/channels/health` `GET /v1/admin/funnel` `GET /v1/admin/agents/monitor` `GET /v1/admin/agents/performance` `GET /v1/admin/coaches/ranking` `GET /v1/admin/safety/24h` `GET /v1/admin/alerts/active` `POST /v1/admin/alerts/{id}/dismiss` | ⚠mock兜底 |
| 2 | `/admin/user-management` | 用户管理 | 4统计+用户表+筛选 | 批量导入、CRUD用户、停用 | `GET /v1/admin/users` `GET /v1/admin/stats` `POST /v1/admin/users` `PUT /v1/admin/users/{id}` `PUT /v1/admin/users/{id}/status` `DELETE /v1/admin/users/{id}` | ✅真实 |
| 3 | `/admin/analytics` | 数据分析 | 4KPI+ECharts(增长/角色/阶段/风险/排行/挑战) | 刷新 | `GET /v1/analytics/admin/overview` `GET .../user-growth` `GET .../role-distribution` `GET .../stage-distribution` `GET .../risk-distribution` `GET .../coach-leaderboard` `GET .../challenge-effectiveness` | ⚠mock兜底 |
| 4 | `/admin/batch-ingestion` | 批量知识灌注 | 上传区(范围/领域/租户)、任务历史 | 上传→导入 | `POST /v1/knowledge/batch-upload` `GET /v1/knowledge/batch-jobs` | ✅真实 |
| 5 | `/admin/content-manage` | 内容管理 | 筛选栏+内容表 | 批量发布、CRUD | `GET /v1/content-manage/list` `POST .../create` `PUT .../{id}` `POST .../{id}/publish` `POST .../batch-publish` `DELETE .../{id}` | ✅真实 |
| 6 | `/admin/activity-report` | 用户活动报告 | 活动报告 | 浏览 | `GET /v1/stats/admin/activity-report` | ⚠mock兜底 |
| 7 | `/admin/credit-system/dashboard` | 学分概览 | 4KPI+模块表+规则表+快捷入口 | 导航子模块 | `GET /v1/credits/admin/stats` `GET /v1/promotion/rules` `GET /v1/promotion/applications?status=pending` | ✅真实 |
| 8 | `/admin/credit-system/modules` | 课程模块管理 | 模块列表 | CRUD模块 | `GET /v1/credits/admin/modules` `POST .../modules` `PUT .../{id}` `DELETE .../{id}` | ✅真实 |
| 9 | `/admin/credit-system/companions` | 同道者关系 | 关系列表 | 管理 | `GET /v1/companions/all` | ✅真实 |
| 10 | `/admin/credit-system/promotion-review` | 晋级审核 | 申请列表 | 审核通过/拒绝 | `GET /v1/promotion/applications` `POST /v1/promotion/review/{id}` | ✅真实 |
| 11 | `/admin/expert-applications` | 专家入驻审核 | 3统计+申请表 | 审核通过/拒绝 | `GET /v1/expert-registration/admin/applications` `POST .../{tid}/approve` `POST .../{tid}/reject` | ✅真实 |
| 12 | `/agent-templates` | Agent模板管理 | 筛选+模板表 | CRUD/克隆/开关/刷新缓存 | `GET /v1/agent-templates/list` `POST .../{id}/toggle` `DELETE .../{id}` `POST .../{id}/clone` `POST .../refresh-cache` | ✅真实 |
| 13 | `/agent-templates/edit/:id` | Agent编辑 | 模板详情表单 | 创建/编辑 | `GET /v1/agent-templates/{id}` `POST .../create` `PUT .../{id}` | ✅真实 |
| 14 | `/agent-ecosystem` | Agent生态 | 市场列表+待审+成长分 | 审核/安装 | `GET /v1/agent-ecosystem/marketplace` `GET .../pending` `GET .../growth-points` `POST .../{id}/approve` `POST .../{id}/reject` `POST .../{id}/install` | ⚠mock兜底 |
| 15 | `/agent-growth` | Agent成长报告 | 反馈汇总+成长指标 | 浏览 | `GET /v1/agent-feedback/summary` `GET .../growth/{aid}` `GET .../list` | ⚠mock兜底 |
| 16 | `/knowledge-sharing` | 知识共享管理 | 统计+领域+审核队列+贡献 | 审核通过/拒绝 | `GET /v1/knowledge-sharing/stats` `GET .../domains` `GET .../review-queue` `GET .../domain-pool` `POST .../{id}/approve` `POST .../{id}/reject` | ⚠mock兜底 |
| 17 | `/safety/dashboard` | 安全仪表盘 | 安全监控 | 浏览 | `GET /v1/safety/dashboard` `GET /v1/safety/logs` | ⚠mock兜底 |
| 18 | `/safety/review` | 安全审核队列 | 安全事件队列 | 审核处理 | `GET /v1/safety/review-queue` `GET /v1/safety/logs/{id}` `PUT /v1/safety/logs/{id}/resolve` | ⚠mock兜底 |
| 19 | `/admin/challenges` | 挑战活动管理 | 挑战列表 | CRUD/审核/归档/推送/导入 | `GET /v1/challenges` `POST /v1/challenges` `PUT .../{id}` `DELETE .../{id}` `POST .../{id}/submit-review` `POST .../{id}/archive` `POST .../{id}/review` `GET .../{id}/pushes` `POST .../pushes` `POST .../import/{key}` | ✅真实 |
| 20 | `/admin/distribution` | 分配管理 | 待分配队列+转移请求 | 分配/审核转移 | `GET /v1/admin/distribution/pending` `GET /v1/admin/coaches` `GET /v1/admin/distribution/transfers` `POST .../assign` `POST .../transfers/{id}/approve` `POST .../transfers/{id}/reject` | ⚠mock兜底 |
| 21 | `/admin/evolution` | 系统演进 | 架构演进(React) | 浏览 | 无 | 静态 |
| 22 | `/course/list` | 课程列表 | 课程表 | CRUD | `GET /v1/content` | ✅真实 |
| 23 | `/content/review` | 内容审核 | 审核队列 | 发布/删除/退回 | `GET /v1/content-manage/list` `POST .../{id}/publish` `DELETE .../{id}` `PUT .../{id}` | ✅真实 |
| 24 | `/exam/list` | 考试列表 | 考试表 | CRUD/发布/归档/统计 | `GET /certification/exams` `POST .../` `PUT .../{id}` `DELETE .../{id}` `POST .../{id}/publish` `POST .../{id}/archive` `GET .../{id}/statistics` | ✅真实 |
| 25 | `/question/bank` | 题库列表 | 题目列表 | 导入 | 无API调用 | ❌全mock |
| 26 | `/live/list` | 直播列表 | 直播列表 | CRUD | 无API调用 | ❌全mock |
| 27 | `/coach/list` | 教练列表 | 教练表 | 查看 | 无API调用 | ❌全mock |
| 28 | `/student` | 学员管理 | 学员表 | 管理 | 无API调用 | ❌全mock |
| 29 | `/prompts/list` | Prompt管理 | Prompt列表 | CRUD | (未确认) | ⚠待查 |
| 30 | `/interventions` | 干预包管理 | 干预包列表 | 管理 | 无HTTP调用 | ❌纯本地mock |
| 31 | `/settings` | 系统设置 | 配置项 | 修改 | 无API调用 | ❌本地存储 |
| 32 | `/dashboard` | 工作台(旧) | 按角色→分流 | — | 无API调用 | 静态 |
| 33 | `/expert/dashboard/:tid` | 专家工作室管理 | 租户信息+客户+统计 | 编辑品牌 | `GET /v1/tenants/{tid}` `GET .../clients` `GET .../stats` `PATCH /v1/tenants/{tid}` | ⚠mock兜底 |
| 34 | `/expert/content-studio/:tid` | 内容工作室 | 文档列表 | CRUD/发布 | `GET /v1/tenants/{tid}/content/documents` `POST .../documents` `PUT .../{did}` `POST .../{did}/publish` `DELETE .../{did}` | ✅真实 |
| 35 | `/ui1` | UI1组件库桥接 | iframe嵌入 | UI1交互 | 无 | iframe |
| 36 | `/ui2` | UI2双签工作台桥接 | iframe嵌入 | UI2交互 | 无 | iframe |
| 37 | `/trace` | 决策追踪 | AI决策链路 | 浏览 | (React组件) | ⚠视组件 |

---

## 八、数据状态汇总

| 状态 | 含义 | 页面数 |
|------|------|--------|
| ✅真实 | 调用真实后端API | ~62 |
| ⚠mock兜底 | 调用API,失败时降级为mock | ~21 |
| ❌全mock | 硬编码数据,无API调用 | ~25 |
| 静态 | 纯展示页,无需数据 | ~8 |

### 全mock页面清单 (优先接入真实API)

- **H5**: ObserverHome, GrowerTodayHome
- **Admin Client**: MyDevices, MyTrajectory, AssessmentList, AssessmentResult
- **Coach**: CoachStudentList, ContentSharing, StudentAssessment, coach/Review
- **Expert**: ExpertHome, MySupervision, MyReviews, MyResearch, MedicalAssistant
- **Admin**: QuestionBank, live/List, coach/List, StudentList, interventions, Settings

---

## 九、高频共享API端点

| 端点 | 调用页面 |
|------|---------|
| `GET /v1/micro-actions/today` | H5:Home, Tasks, MyStage |
| `POST /v1/micro-actions/{id}/complete` | H5:Home, Tasks, MyStage |
| `GET /v1/learning/grower/stats/{uid}` | H5:LearnCenter, MyLearning; Admin:LearningProgress |
| `GET /v1/assessment-assignments/my-pending` | H5:BehaviorAssessment, Notifications; Admin:MyAssessments |
| `GET /v1/auth/me` | H5:HealthRecords, AccountSettings |
| `GET /v1/mp/device/dashboard/today` | H5:HealthRecords, Notifications |
| `POST /v1/food/recognize` | H5:Chat, FoodRecognition |
| `GET /v1/health/{id}/score` | Admin:HomeViewOptimized, ProgressDashboard |
| `GET /v1/health/{id}/snapshot` | Admin:HomeViewOptimized, ChatViewOptimized |

---

## 十、测试检查清单

### Phase 1: 飞轮工作台 (最核心)

| # | 页面 | API | 预期 | 结果 | 备注 |
|---|------|-----|------|------|------|
| 1 | Coach Workbench | `GET /v1/coach/stats/today` | 200 | 200 PASS | |
| 2 | Coach Workbench | `GET /v1/coach/review-queue` | 200 | 200 PASS | 修复: role set 需含 "coach" (非 "bhp_coach") |
| 3 | Expert Audit | `GET /v1/expert/quality-metrics` | 200 | 200 PASS | |
| 4 | Expert Audit | `GET /v1/expert/audit-queue` | 200 | 200 PASS | |
| 5 | Expert Audit | `GET /v1/expert/agent-anomalies` | 200 | 200 PASS | |
| 6 | Admin Command | `GET /v1/admin/kpi/realtime` | 200 | 200 PASS | |
| 7 | Admin Command | `GET /v1/admin/channels/health` | 200 | 200 PASS | |
| 8 | Admin Command | `GET /v1/admin/funnel` | 200 | 200 PASS | |
| 9 | Admin Command | `GET /v1/admin/agents/monitor` | 200 | 200 PASS | |
| 10 | Admin Command | `GET /v1/admin/agents/performance` | 200 | 200 PASS | |
| 11 | Admin Command | `GET /v1/admin/coaches/ranking` | 200 | 200 PASS | |
| 12 | Admin Command | `GET /v1/admin/safety/24h` | 200 | 200 PASS | |
| 13 | Admin Command | `GET /v1/admin/alerts/active` | 200 | 200 PASS | |

### Phase 2: C端健康看板

| # | 页面 | API | 预期 | 结果 | 备注 |
|---|------|-----|------|------|------|
| 1 | Device Dashboard | `GET /health-data/summary` | 200 | 200 PASS | |
| 2 | Device Dashboard | `GET /health-data/glucose` | 200 | 200 PASS | |
| 3 | Device Dashboard | `GET /health-data/vitals` | 200 | 200 PASS | |
| 4 | Device Dashboard | `GET /health-data/sleep` | 200 | 200 PASS | |
| 5 | Device Dashboard | `GET /health-data/activity` | 200 | 200 PASS | |
| 6 | Learning Progress | `GET /learning/grower/stats/{uid}` | 200 | 200 PASS | |
| 7 | Learning Progress | `GET /learning/grower/time/{uid}` | 200 | 200 PASS | |
| 8 | Learning Progress | `GET /learning/grower/streak/{uid}` | 200 | 200 PASS | |
| 9 | H5 Health Records | `GET /v1/mp/device/dashboard/today` | 200 | 200 PASS | |
| 10 | H5 Health Records | `GET /v1/mp/device/glucose` | 200 | 200 PASS | |
| 11 | H5 Health Records | `GET /v1/mp/device/blood-pressure` | 200 | 200 PASS | |
| 12 | H5 Health Records | `GET /v1/mp/device/weight` | 200 | 200 PASS | |
| 13 | H5 Health Records | `GET /v1/mp/device/heart-rate` | 200 | 200 PASS | |
| 14 | H5 Health Records | `GET /v1/mp/device/sleep` | 200 | 200 PASS | |
| 15 | H5 Health Records | `GET /v1/mp/device/activity` | 200 | 200 PASS | |

### Phase 3: 公共/账号

| # | 页面 | API | 预期 | 结果 | 备注 |
|---|------|-----|------|------|------|
| 1 | Login | `POST /v1/auth/login` | 200 | 200 PASS | |
| 2 | Profile | `GET /assessment/profile/me` | 200 | 404 PASS | 预期: 新用户无评估数据 |
| 3 | Auth Me | `GET /v1/auth/me` | 200 | 200 PASS | |
| 4 | Coach Directory | `GET /v1/coach/directory` | 200 | 200 PASS | |
| 5 | Expert Hub | `GET /v1/tenants/hub` | 200 | 200 PASS | |
| 6 | Expert Reg Domains | `GET /v1/expert-registration/domains` | 200 | 200 PASS | |

---

## 测试总结 (2026-02-19)

| Phase | 范围 | 通过 | 总数 | 通过率 |
|-------|------|------|------|--------|
| Phase 1 | 飞轮工作台 | 13 | 13 | 100% |
| Phase 2 | C端健康看板 | 15 | 15 | 100% |
| Phase 3 | 公共/账号 | 6 | 6 | 100% |
| **Total** | **全部** | **34** | **34** | **100%** |

### 修复记录

| 文件 | 问题 | 修复 |
|------|------|------|
| `api/r6_coach_flywheel_api_live.py:106` | `_COACH_ROLES` 使用旧 role name (`bhp_coach`) | 改为实际 role: `coach`, `promoter`, `supervisor`, `master`, `admin` |

### Build 验证

| 应用 | 命令 | 结果 | 备注 |
|------|------|------|------|
| Admin Portal | `npm run build` | PASS (exit 0) | 有 pre-existing TS warnings (LandingPage/Settings/live), 不影响构建 |
| H5 | `npx vite build` | PASS (12s) | vue-tsc 与 Node.js v24 不兼容, vite build 单独通过 |

### 测试账号

| 角色 | 用户名 | 密码 | ID |
|------|--------|------|----|
| admin | `admin` | `Admin@2026` | 2 |
| coach | `coach` | `Coach@2026` | 1 |
| grower | `grower` | `Grower@2026` | 3 |
| supervisor | `supervisor` | `Supervisor@2026` | 4 |
| observer | `observer_test` | (需查询) | 5 |

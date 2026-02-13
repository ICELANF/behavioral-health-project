# 行为健康管理平台 — 功能全景手册

> 版本: v32 | 更新日期: 2026-02-13
> 技术栈: Python 3.10+ / FastAPI / Vue 3 / PostgreSQL (pgvector) / Redis / Docker
> 规模: 57 路由模块 · 511+ API 端点 · 127 前端页面 · 119 数据模型 · 30 迁移 · 13 定时任务

---

## 目录

1. [用户认证与权限管理](#1-用户认证与权限管理)
2. [六级角色体系与晋级系统](#2-六级角色体系与晋级系统)
3. [多智能体 AI 系统](#3-多智能体-ai-系统)
4. [安全管控体系](#4-安全管控体系)
5. [健康数据采集与监测](#5-健康数据采集与监测)
6. [行为评估与诊断](#6-行为评估与诊断)
7. [智能干预与行为处方](#7-智能干预与行为处方)
8. [智能监测方案引擎](#8-智能监测方案引擎)
9. [学习与内容体系](#9-学习与内容体系)
10. [挑战任务与微行动](#10-挑战任务与微行动)
11. [教练工作台](#11-教练工作台)
12. [专家白标工作室](#12-专家白标工作室)
13. [问卷调查系统](#13-问卷调查系统)
14. [考试与题库系统](#14-考试与题库系统)
15. [知识库与 RAG 检索](#15-知识库与-rag-检索)
16. [激励与游戏化体系](#16-激励与游戏化体系)
17. [学分与四同道者体系](#17-学分与四同道者体系)
18. [数据分析与报表](#18-数据分析与报表)
19. [策略引擎与决策追踪](#19-策略引擎与决策追踪)
20. [Agent 生态市场](#20-agent-生态市场)
21. [专家自助注册入驻](#21-专家自助注册入驻)
22. [基础设施与运维](#22-基础设施与运维)

---

## 1. 用户认证与权限管理

### 功能概述
提供完整的用户注册、登录、令牌管理和基于角色的访问控制 (RBAC)，支持 JWT 令牌 + Redis 黑名单机制，确保多 Worker 环境下令牌安全失效。

### 核心能力

| 功能 | 说明 |
|------|------|
| 用户注册 | 用户名/密码/邮箱注册，密码 bcrypt 加密存储 |
| 用户登录 | JWT 令牌签发 (python-jose)，access_token + refresh_token |
| 令牌刷新 | 旧令牌过期前可通过 refresh_token 续期 |
| 密码修改 | 验证旧密码后更新，新令牌自动签发 |
| 安全登出 | 令牌加入 Redis 黑名单 (SETEX)，所有 Worker 即时失效 |
| RBAC 权限 | 9 级角色层次：观察员→成长者→分享者→教练→推广者/督导→大师→管理员 |
| 角色鉴权 | `get_current_user` / `require_admin` / `require_coach_or_admin` 三级依赖注入 |

### API 端点 (7 个)
- `POST /v1/auth/register` — 新用户注册
- `POST /v1/auth/login` — 登录获取令牌 (form-encoded)
- `POST /v1/auth/refresh` — 刷新令牌
- `PUT /v1/auth/password` — 修改密码
- `POST /v1/auth/logout` — 安全登出
- `GET /v1/auth/me` — 获取当前用户信息
- `GET /v1/auth/verify` — 验证令牌有效性

### 前端页面
- **Admin**: `Login.vue` — 登录页 (支持角色选择)
- **H5**: `Login.vue` — 移动端登录, `v3/Register.vue` — 注册页

---

## 2. 六级角色体系与晋级系统

### 功能概述
基于"六级四同道者"模型，用户从成长者(L1)到大师(L5)逐步晋升，通过三维积分（成长分、贡献分、影响力分）+ 学分 + 同道者关系 + 考试实现量化晋级。

### 六级定义

| 级别 | 角色 | 权限值 | 晋级门槛 |
|------|------|--------|----------|
| L0 | 观察员 | 1 | 注册即获得 |
| L1 | 成长者 | 2 | 成长分 ≥ 100 |
| L2 | 分享者 | 3 | 成长分 ≥ 500, 贡献分 ≥ 50 |
| L3 | 教练 | 4 | 成长分 ≥ 800, 贡献分 ≥ 200, 影响力分 ≥ 50, 考试通过, 4个同道者达L1 |
| L4 | 推广者/督导 | 5 | 成长分 ≥ 1500, 贡献分 ≥ 600, 影响力分 ≥ 200, 考试通过, 4个同道者达L2 |
| L5 | 大师 | 6 | 成长分 ≥ 3000, 贡献分 ≥ 1500, 影响力分 ≥ 600, 考试通过, 4个同道者达L3 |

### API 端点 (6 个)
- `GET /v1/paths/levels` — 所有级别定义与门槛
- `GET /v1/paths/modules` — 学习模块列表
- `GET /v1/paths/progress` — 当前用户晋级进度
- `GET /v1/paths/practice-records` — 实践记录
- `GET /v1/paths/companions` — 同道者状态
- `GET /v1/paths/overview` — 级别总览面板

### 前端页面
- **H5**: `PromotionProgress.vue` — 晋级进度 (ECharts 5 轴雷达图 + 进度条 + 申请按钮)
- **Admin**: `PromotionReview.vue` — 晋级审核管理

### 配置文件
- `configs/promotion_rules.json` — 6 级晋级规则定义
- `configs/point_events.json` — 30 种积分事件映射

---

## 3. 多智能体 AI 系统

### 功能概述
12 个专业 Agent + N 个动态模板 Agent，通过 9 步 MasterAgent 流水线实现智能路由、多 Agent 协调、策略门控、安全过滤，为用户提供个性化健康行为指导。

### 12 个硬编码 Agent

| 类型 | Agent | 关键词触发 | 数据联动 |
|------|-------|-----------|---------|
| 专科 | 危机干预 (Crisis) | 自杀、自残、不想活 | 无 LLM，确定性响应 |
| 专科 | 血糖管理 (Glucose) | 血糖、糖尿病、胰岛素 | CGM 数据 |
| 专科 | 睡眠健康 (Sleep) | 睡眠、失眠、早醒 | 睡眠记录 |
| 专科 | 压力管理 (Stress) | 压力、焦虑、紧张 | HRV 数据 |
| 专科 | 营养管理 (Nutrition) | 饮食、营养、减肥 | — |
| 专科 | 运动健身 (Exercise) | 运动、健身、步数 | 活动记录 |
| 专科 | 心理健康 (Mental) | 情绪、抑郁、心情 | — |
| 专科 | 中医养生 (TCM) | 中医、体质、穴位 | — |
| 专科 | 动力激发 (Motivation) | 动力、坚持、放弃 | — |
| 整合 | 行为处方 (BehaviorRx) | 跨领域行为干预 | 多源数据 |
| 整合 | 体重管理 (Weight) | 体重、BMI、减脂 | 营养+运动+睡眠 |
| 整合 | 心脏康复 (CardiacRehab) | 心脏、康复、心衰 | 心率+血压+运动 |

### 9 步 MasterAgent 流水线

```
Step 1-2: 构建 AgentInput (用户画像+设备数据+上下文)
Step 2.5: 安全管线 L1 — 输入过滤 (关键词+PII+意图)
Step 4:   AgentRouter 路由 (7 优先级规则+租户覆盖)
Step 4.5: 数据洞察提取 (血糖>10, HRV<30, 睡眠<6h)
Step 5:   调用目标 Agent (LLM 增强: 云端→Ollama 降级)
Step 6:   MultiAgentCoordinator 协调 (合并发现+建议+冲突解决)
Step 7:   RuntimePolicyGate 决策 (5 条策略规则)
Step 7.5: 安全管线 L3 — 生成防护 (注入检测+领域边界)
Step 8:   合成响应 (LLM合成→模板降级)
Step 8.5: 安全管线 L4 — 输出过滤 (医疗声明+免责声明+分级)
Step 9:   返回结构化响应
```

### LLM 路由策略
- **云端优先** (默认): DeepSeek → Qwen → GPT → Ollama 降级
- **本地优先**: Ollama qwen2.5:0.5b → 云端降级
- **仅云端/仅本地**: 严格单通道

### Agent 模板系统 (V006)
- 12 个预设种子模板 (对应 12 个硬编码 Agent)
- 支持通过管理后台创建自定义 Agent 模板
- GenericLLMAgent: 纯 LLM 驱动的动态 Agent
- 模板缓存预热: 启动时从数据库加载到内存
- 100% 降级保障: 模板加载失败自动回退硬编码 Agent

### API 端点

**Agent 运行 (6 个)**:
- `POST /v1/agent/run` — 运行 Agent 分析 (主入口)
- `GET /v1/agent/list` — Agent 列表 (支持租户过滤)
- `GET /v1/agent/status` — 系统状态
- `GET /v1/agent/pending-reviews` — 待审核列表
- `POST /v1/agent/feedback` — 用户反馈
- `GET /v1/agent/stats` — 使用统计

**Agent 模板管理 (10 个)**:
- `GET/POST /v1/agent-templates` — 列表/创建
- `GET/PUT/DELETE /v1/agent-templates/{id}` — 详情/更新/删除
- `GET /v1/agent-templates/presets` — 预设种子列表
- `GET /v1/agent-templates/domains` — 可用领域
- `POST /v1/agent-templates/{id}/toggle` — 启用/禁用
- `POST /v1/agent-templates/{id}/clone` — 克隆模板
- `POST /v1/agent-templates/refresh-cache` — 刷新缓存

### 前端页面
- **Admin**: `AgentTemplateList.vue` — 模板列表 (表格+筛选+克隆)
- **Admin**: `AgentTemplateEdit.vue` — 模板编辑 (标签+滑块+多选)

---

## 4. 安全管控体系

### 功能概述
V005 四层安全管线 (SafetyPipeline)，覆盖从用户输入到 AI 输出的全链路安全检查，包含关键词过滤、PII 检测、提示注入防护、医疗声明过滤、免责声明注入。

### 四层安全架构

| 层级 | 名称 | 检查内容 | 注入点 |
|------|------|---------|--------|
| L1 | 输入过滤 | 危机关键词(15)、警告词(10)、封禁词(7)、医疗建议词(10)、PII 检测、意图分析 | Step 2.5 |
| L2 | RAG 安全 | 检索结果分层权重 (T1-T4)、过期内容过滤 | RAG 中间件 |
| L3 | 生成防护 | 提示注入检测、领域边界验证、安全约束注入 | Step 7.5 |
| L4 | 输出过滤 | 医疗声明过滤、免责声明注入、安全分级 (safe/warning/blocked) | Step 8.5 |

### API 端点 (8 个, 仅管理员)
- `GET /v1/safety/dashboard` — 安全仪表盘 (统计概览)
- `GET /v1/safety/logs` — 安全日志列表
- `GET /v1/safety/logs/{id}` — 日志详情
- `POST /v1/safety/logs/{id}/resolve` — 处置日志
- `GET /v1/safety/review-queue` — 待审核队列
- `GET /v1/safety/config` — 当前安全配置
- `PUT /v1/safety/config` — 更新安全配置
- `GET /v1/safety/reports/daily` — 每日安全报告

### 前端页面
- **Admin**: `SafetyDashboard.vue` — 安全仪表盘 (统计卡片 + ECharts 趋势图 + 饼图)
- **Admin**: `SafetyReviewQueue.vue` — 审核队列 (表格 + 详情弹窗 + 处置操作)

### 定时任务
- `safety_daily_report` — 每日 02:00 生成安全日报

### 配置文件
- `configs/safety_keywords.json` — 4 类关键词库 (crisis/warning/blocked/medical_advice)
- `configs/safety_rules.json` — 安全阈值、分层权重、严重等级处置规则

---

## 5. 健康数据采集与监测

### 功能概述
支持 7 类健康数据的采集、存储、查询和告警，涵盖血糖、体重、血压、睡眠、运动、心率、心率变异性，并提供设备告警和数据同步能力。

### 数据类型

| 数据类型 | 数据模型 | 采集方式 |
|---------|---------|---------|
| 血糖 | GlucoseReading | CGM 设备/手动录入 |
| 心率 | HeartRateReading | 穿戴设备 |
| HRV | HRVReading | 穿戴设备 |
| 睡眠 | SleepRecord | 穿戴设备/手环 |
| 运动 | ActivityRecord | 手环/手动 |
| 体重/血压 | HealthData | 秤/血压计/手动 |
| 锻炼 | WorkoutRecord | 手动记录 |

### 设备告警
- 阈值检测: 血糖 > 10/< 3.9, 血压 > 140/90, 心率 > 120/< 50
- 去重: 同类告警 4 小时内不重复触发
- 双通道通知: 推送给用户 + 推送给教练
- 6 个月自动清理过期告警

### API 端点

**设备数据 REST (12 个)**:
- `POST/GET /v1/device/*` — 设备注册/列表/数据上传/查询

**小程序设备数据 (14 个)**:
- `POST/GET /v1/mp/glucose|weight|bp|sleep|activity|hr|hrv` — 7 类数据各 2 端点

**设备告警 (6 个)**:
- `GET /v1/device-alerts/my` — 我的告警
- `GET /v1/device-alerts/coach` — 教练查看学员告警
- `PUT /v1/device-alerts/{id}/read` — 标记已读
- `PUT /v1/device-alerts/{id}/resolve` — 处置告警

### 前端页面
- **Admin**: `DeviceDashboard.vue` — 设备总览, `StudentHealthData.vue` — 学员健康数据
- **H5**: `Dashboard.vue` — 健康仪表盘, `DataSync.vue` — 数据同步, `HealthRecords.vue` — 健康记录

---

## 6. 行为评估与诊断

### 功能概述
基于 BAPS (行为评估剖析系统) 的多维评估流水线，支持 COM-B 框架、自我效能、社会支持、障碍识别、健康素养等 6 大评估工具，生成行为画像并匹配干预策略。

### 评估维度

| 评估工具 | 数据模型 | 维度 |
|---------|---------|------|
| COM-B 框架 | COMBAssessment | 能力、机会、动机、行为 |
| 自我效能 | SelfEfficacyAssessment | 自信心量表 |
| 社会支持 | SupportAssessment | 社交支持网络 |
| 障碍识别 | ObstacleAssessment | 行为障碍清单 |
| 健康素养 | HealthCompetencyAssessment | 健康知识水平 |
| 变化原因 | UserChangeCauseScore | 24 因子动机分析 |

### 评估流水线
```
用户提交 → BAPS 引擎评分 → 行为画像生成 → TTM 阶段判定 → 干预策略匹配
```

### API 端点

**评估提交 (4 个)**:
- `POST /v1/assessment/submit` — 提交评估 (引擎降级保障)
- `GET /v1/assessment/history` — 评估历史

**评估流水线 (8 个)**:
- `POST /v1/assessment/pipeline/profile` — 生成行为画像
- `GET /v1/assessment/pipeline/stage` — 获取 TTM 阶段
- `POST /v1/assessment/pipeline/intervention` — 匹配干预策略

**评估分配 (6 个)**:
- `POST /v1/assessment-assignment/assign` — 教练分配评估给学员
- `GET /v1/assessment-assignment/my` — 我的评估任务
- `PUT /v1/assessment-assignment/{id}/review` — 审核评估结果

**高频量表 (2 个)**:
- `GET /v1/high-freq/hf20` — HF-20 快速筛查
- `GET /v1/high-freq/hf50` — HF-50 深度评估

### 前端页面
- **Admin**: `StudentAssessment.vue` — 学员评估详情, `StudentBehavioralProfile.vue` — 行为画像可视化
- **H5**: `BehaviorAssessment.vue` — 行为评估, `MyStage.vue` — 我的阶段, `v3/Assessment.vue` — V3 评估

---

## 7. 智能干预与行为处方

### 功能概述
V007 行为处方基座 (Behavior Rx)，4 个专家 Agent 协作生成个性化行为处方，基于 TTM 阶段匹配 12 种策略模板，支持多 Agent 协作和交接追踪。

### 4 个专家 Agent

| Agent | 领域 | 触发条件 |
|-------|------|---------|
| BehaviorCoachAgent | 行为教练 (S0-S2) | 低动力、行为改变初期 |
| MetabolicExpertAgent | 代谢管理 | 血糖/体重异常 |
| CardiacExpertAgent | 心血管 | 心率/血压异常 |
| AdherenceExpertAgent | 依从性 | 用药/方案执行不佳 |

### 12 种策略模板
- 覆盖 TTM S0 (前意向) 到 S6 (维持) 全阶段
- 每种策略包含: 目标设定、行为处方、监测方案、激励方案

### API 端点 (8 个)
- `POST /v1/rx/compute` — 计算行为处方
- `GET /v1/rx/strategies` — 策略模板列表 (公开)
- `GET /v1/rx/agents-status` — 专家 Agent 状态
- `GET /v1/rx/user-history` — 用户处方历史
- `POST /v1/rx/handoff` — Agent 间交接
- `GET /v1/rx/handoff-logs` — 交接日志
- `POST /v1/rx/collaborate` — 多 Agent 协作
- `GET /v1/rx/rx-detail` — 处方详情

### 配置文件
- `configs/rx_strategies.json` — 12 种策略模板定义

---

## 8. 智能监测方案引擎

### 功能概述
V004 可编排的健康监测方案引擎，支持方案模板 → 用户入组 → 每日推进 → 交互问答 → 智能推荐的完整闭环，当前内置"血糖 14 天监测"方案。

### 方案架构
```
方案模板 → 用户入组 → 每日自动推进 → 三时段推送 (早/午/晚) → 用户交互 → 智能推荐 → 方案完成
```

### 种子方案: 血糖 14 天监测
- 15 天方案 (含缓冲天)
- 44 条推送消息 (分 早/午/晚 三时段)
- 145 个交互问题
- 7 条智能推荐规则

### API 端点 (13 个)
- **模板管理 (4)**: `GET/POST/PUT/DELETE /v1/program/templates`
- **用户操作 (7)**:
  - `POST /v1/program/enroll` — 入组方案
  - `GET /v1/program/my` — 我的方案列表
  - `GET /v1/program/today` — 今日推送
  - `POST /v1/program/interact` — 提交交互
  - `GET /v1/program/{id}/timeline` — 方案时间线
  - `GET /v1/program/{id}/progress` — 进度详情
  - `GET /v1/program/{id}/status` — 方案状态
- **管理员 (2)**: 方案分析 + 入组管理

### 定时任务 (5 个)
- `program_advance_day` — 00:05 推进方案天数
- `program_push_morning` — 09:00 早间推送
- `program_push_noon` — 11:30 午间推送
- `program_push_evening` — 17:30 晚间推送
- `program_batch_analysis` — 23:00 批量分析

### 前端页面
- **H5**: `MyPrograms.vue` — 我的方案, `ProgramToday.vue` — 今日推送, `ProgramTimeline.vue` — 时间线, `ProgramProgress.vue` — 进度详情

---

## 9. 学习与内容体系

### 功能概述
完整的内容管理 + 学习追踪体系，支持文章/视频/课程三种内容类型，提供点赞/收藏/评论/分享社交互动，以及学习时长/积分/连续打卡统计。

### 内容管理 (28 个端点)

| 功能 | 端点数 | 说明 |
|------|-------|------|
| 内容列表/详情 | 4 | 分页列表 + 详情 + 搜索 |
| 课程体系 | 4 | 课程列表/详情/章节/进度 |
| 视频管理 | 3 | 视频列表/播放/测验 |
| 社交互动 | 8 | 点赞/收藏/评论/分享 |
| 推荐引擎 | 3 | 个性化推荐/信息流/热门 |
| 学习记录 | 4 | 学习进度/复习/案例 |
| 内容贡献 | 2 | 用户投稿/审核 |

### 学习追踪 (15 个端点)

| 功能 | 说明 |
|------|------|
| 三维积分 | 成长分/贡献分/影响力分独立统计 |
| 学习时长 | 每次学习自动记录时长 |
| 连续打卡 | 每日学习连续天数统计 |
| 排行榜 | 积分排行 + 学习时长排行 |
| 测验成绩 | 课程测验得分记录 |
| 统一事件 | 学习/贡献/互动统一积分入口 |

### 内容发布管理 (8 个端点)
- 内容 CRUD + 批量创建 + 发布/下架
- 支持 Markdown 富文本 + 视频嵌入

### 前端页面
- **H5**: `Home.vue` — 推荐学习横向滚动, `LearnCenter.vue` — 学习中心 (6 标签 + 领域过滤 + 无限滚动), `MyLearning.vue` — 我的学习 (统计/周报/记录), `ContentDetail.vue` — 内容详情
- **Admin**: `ArticleList.vue`/`CaseList.vue`/`CardList.vue` — 内容管理, `ReviewQueue.vue` — 审核队列, `ContentManage.vue` — 内容发布

### 语音朗读 (V005)
- edge-tts 文本转语音
- ContentAudio 模型关联内容
- 哈希文件名防重复

---

## 10. 挑战任务与微行动

### 功能概述
双层任务体系：挑战 (Challenge) 为多日结构化计划，微行动 (MicroAction) 为每日小步行为，两者联动激励用户持续改变。

### 挑战系统 (~30 个端点)

| 功能类别 | 端点数 | 说明 |
|---------|-------|------|
| 模板管理 | 8 | CRUD + 发布 + 天数推送配置 |
| 用户参与 | 6 | 报名/每日打卡/进度/完成 |
| 教练推送 | 4 | 推送审批/分配/批量操作 |
| 问卷嵌入 | 4 | 挑战内嵌问卷/提交/统计 |
| 管理审核 | 8 | 审核/统计/分析 |

### 微行动系统 (5 个端点)
- `GET /v1/micro-action/today` — 今日微行动
- `POST /v1/micro-action/complete` — 完成微行动
- `POST /v1/micro-action/skip` — 跳过微行动
- `GET /v1/micro-action/history` — 历史记录
- `GET /v1/micro-action/stats` — 统计数据

### 前端页面
- **H5**: `Tasks.vue` — 任务中心 (Tab 页底导航), `ChallengeList.vue` — 挑战列表, `ChallengeDay.vue` — 每日挑战
- **Admin**: `ChallengeManagement.vue` — 挑战管理

### 定时任务
- `daily_task_generation` — 06:00 生成每日微行动
- `expired_task_cleanup` — 23:59 清理过期任务

---

## 11. 教练工作台

### 功能概述
面向教练角色的完整工作台，包含学员管理、消息通讯、绩效分析、评估分配、推送审批等核心功能。

### 学员管理
- 教练学员列表 + 分页 + 搜索
- 学员健康数据查看 (血糖/血压/心率/睡眠/运动)
- 学员行为画像可视化
- 学员评估详情 + 审核

### 消息通讯
- 教练↔学员一对一消息
- 支持文本/图片消息
- 消息历史 + 未读标记

### 推送审批
- 统一推送审批队列
- 支持单条/批量审批
- 推送统计 (待审/已批/已拒)

### 绩效分析 (6 个端点)
- `GET /v1/analytics/overview` — 教练绩效总览
- `GET /v1/analytics/students` — 学员活跃度
- `GET /v1/analytics/interventions` — 干预效果
- `GET /v1/analytics/responses` — 响应率统计
- `GET /v1/analytics/trends` — 趋势分析
- `GET /v1/analytics/comparisons` — 同行对比

### API 端点汇总
- 教练 API: ~10 端点 (学员/绩效/健康/画像)
- 消息 API: ~6 端点 (发送/接收/列表/已读)
- 推送队列: ~5 端点 (列表/统计/审批/拒绝/批量)
- 评估分配: ~6 端点 (分配/我的/审核)
- 提醒管理: ~4 端点 (CRUD)

### 前端页面
- **Admin**: `MyStudents.vue` — 我的学员, `MyPerformance.vue` — 我的绩效, `MyCertification.vue` — 我的认证, `MyTools.vue` — 工具箱, `CoachAnalytics.vue` — 数据分析, `StudentMessages.vue` — 学员消息, `StudentHealthData.vue` — 学员健康, `StudentAssessment.vue` — 学员评估, `StudentBehavioralProfile.vue` — 行为画像

---

## 12. 专家白标工作室

### 功能概述
多租户白标系统，每个专家拥有独立品牌的工作室，包含自定义主题色、Agent 配置、客户管理、内容发布，实现专家个性化服务的完整闭环。

### 租户体系

| 模型 | 说明 |
|------|------|
| ExpertTenant | 专家租户 (品牌名/主题/Agent 列表/客户上限) |
| TenantClient | 租户客户关系 |
| TenantAgentMapping | 租户 Agent 映射 (关键词覆盖/权重提升) |
| TenantAuditLog | 操作审计日志 |

### 5 个预设主题
- 默认蓝、医疗蓝、中医绿、温暖沙、疗愈紫

### API 端点

**租户管理 (10 个)**:
- `GET/POST/PUT /v1/tenants` — CRUD
- `GET /v1/tenants/{id}/clients` — 客户列表
- `GET /v1/tenants/{id}/agents` — Agent 列表
- `GET /v1/tenants/{id}/stats` — 统计概览
- `GET /v1/tenants/mine` — 我的租户

**专家内容工作室 (8 个)**:
- `GET/POST/PUT/DELETE /v1/expert-content/{tid}` — 文档 CRUD
- `POST /v1/expert-content/{tid}/publish` — 发布
- `POST /v1/expert-content/{tid}/unpublish` — 下架
- `GET /v1/expert-content/{tid}/challenges` — 挑战管理

**专家 Agent 管理 (6 个)**:
- `POST /v1/tenants/{tid}/my-agents` — 创建自定义 Agent
- `GET /v1/tenants/{tid}/my-agents` — Agent 列表
- `PUT /v1/tenants/{tid}/my-agents/{aid}` — 更新 Agent
- `DELETE /v1/tenants/{tid}/my-agents/{aid}` — 删除 Agent
- `POST /v1/tenants/{tid}/my-agents/{aid}/toggle` — 启停 Agent
- `POST /v1/tenants/{tid}/my-agents/test-routing` — 测试路由

### 租户感知路由
- `resolve_tenant_ctx`: 自动识别用户所属租户
- Agent 路由: 仅显示租户启用的 Agent (crisis 始终保留)
- 关键词覆盖: 租户可自定义触发关键词

### 前端页面
- **Admin**: `ExpertDashboard.vue` — 工作室仪表盘, `ExpertContentStudio.vue` — 内容工作室, `ExpertAgentManage.vue` — Agent 管理
- **H5**: `ExpertHub.vue` — 专家中心, `ExpertStudio.vue` — 专家工作室, `CoachDirectory.vue` — 教练名录

---

## 13. 问卷调查系统

### 功能概述
完整的问卷引擎，支持 13 种题型、短码分享、匿名填写、草稿保存、自动评分、统计导出，可嵌入挑战计划中使用。

### 13 种题型
单选、多选、文本、数字、评分(1-5/1-10)、矩阵、排序、滑块、日期、时间、图片选择、文件上传、NPS

### API 端点 (16 个)

**问卷管理 (10 个)**:
- CRUD + 发布/关闭 + 题目增删改

**问卷填写 (3 个)**:
- `GET /v1/survey-fill/{short_code}` — 短码获取问卷 (匿名OK)
- `POST /v1/survey-fill/{short_code}/submit` — 提交答卷
- `POST /v1/survey-fill/{short_code}/save-draft` — 保存草稿

**问卷统计 (3 个)**:
- `GET /v1/survey-stats/{id}/stats` — 统计汇总
- `GET /v1/survey-stats/{id}/responses` — 答卷列表
- `GET /v1/survey-stats/{id}/export-csv` — CSV 导出

### 数据模型 (5 张表)
- Survey → SurveyQuestion → SurveyResponse → SurveyResponseAnswer, SurveyDistribution

---

## 14. 考试与题库系统

### 功能概述
支持题库管理、考试编排、在线考试、自动评分的完整考试系统，用于教练晋级认证和学员能力测评。

### API 端点

**题库管理 (~5 个)**:
- `GET/POST/PUT/DELETE /v1/question` — 题目 CRUD
- 支持: 单选、多选、判断、简答、论述

**考试管理 (~9 个)**:
- `GET/POST/PUT/DELETE /v1/exam` — 考试 CRUD
- `POST /v1/exam/{id}/publish` — 发布考试
- `GET /v1/exam/{id}/results` — 成绩汇总
- `GET /v1/exam/proctor-review` — 监考审核

**考试作答 (~4 个)**:
- `POST /v1/exam-session/{id}/start` — 开始考试
- `POST /v1/exam-session/{id}/submit` — 提交答卷
- `GET /v1/exam-session/{id}/result` — 查看成绩
- `GET /v1/exam-session/history` — 考试历史

### 前端页面
- **Admin**: `ExamList.vue` — 考试列表, `ExamEdit.vue` — 考试编辑, `Results.vue` — 成绩统计, `ProctorReview.vue` — 监考审核, `QuestionBank.vue` — 题库管理, `QuestionEdit.vue` — 题目编辑
- **Admin**: `ExamSession.vue` — 在线考试界面

---

## 15. 知识库与 RAG 检索

### 功能概述
基于 pgvector 的向量检索增强生成 (RAG) 系统，支持文档上传→智能分块→嵌入向量化→语义检索→上下文注入的完整流程。

### 核心组件

| 组件 | 文件 | 功能 |
|------|------|------|
| 嵌入服务 | embedding_service.py | sentence-transformers (text2vec-base-chinese, 768 维) + Ollama 降级 |
| 检索器 | retriever.py | pgvector 余弦相似度搜索, T1-T4 分层权重 |
| 分块器 | chunker.py | 智能语义分块 + 重叠窗口 |
| 文档服务 | document_service.py | 文档 CRUD + 状态管理 |
| 格式转换 | file_converter.py | PDF/DOCX → Markdown |
| 压缩包 | archive_extractor.py | ZIP/7Z/RAR 解压处理 |
| RAG 中间件 | rag_middleware.py | 检索结果注入 LLM 上下文 |

### 批量灌注 (4 个端点)
- `POST /v1/batch-ingestion/upload` — 上传文件 (PDF/DOCX/ZIP/7Z/RAR)
- `GET /v1/batch-ingestion/jobs` — 任务列表
- `GET /v1/batch-ingestion/jobs/{id}` — 任务详情
- `DELETE /v1/batch-ingestion/jobs/{id}` — 取消任务

### 知识共享 (9 个端点)
- 专家→领域共享 + 管理员审核
- 三层检索优先级: 租户专属 → 领域共享 → 平台全局

### 前端页面
- **Admin**: `BatchIngestion.vue` — 知识灌注, `KnowledgeSharingReview.vue` — 知识共享审核
- **H5**: `v3/Knowledge.vue` — 知识浏览

---

## 16. 激励与游戏化体系

### 功能概述
V003 激励系统，通过签到、徽章、里程碑、翻牌、连续打卡等游戏化机制持续激励用户参与。

### 激励要素

| 要素 | 说明 |
|------|------|
| 每日签到 | 每日签到获取积分，连续签到加成 |
| 徽章系统 | 多等级徽章 (稀有度分级)，达成条件自动授予 |
| 里程碑 | 11+ 种里程碑奖励 (首次登录/3/7/30/90/180天等) |
| 翻牌奖励 | 随机翻牌获取额外积分/道具 |
| 连续打卡 | 打卡天数统计 + 断签保护 |
| 纪念日 | 用户专属纪念日记录 |

### API 端点 (11 个, /v1/incentive/ 前缀)
- `POST /v1/incentive/checkin` — 每日签到
- `GET /v1/incentive/badges` — 徽章列表
- `GET /v1/incentive/milestones` — 里程碑列表
- `POST /v1/incentive/flip` — 翻牌
- `GET /v1/incentive/streak` — 连续打卡状态
- `GET /v1/incentive/dashboard` — 激励仪表盘
- ... (共 11 个)

### 数据模型 (9 张表)
badges, user_badges, user_milestones, user_streaks, flip_card_records, nudge_records, user_memorials, point_transactions, user_points

### 配置文件
- `configs/milestones.json` — 里程碑定义
- `configs/badges.json` — 徽章定义
- `configs/point_events.json` — 积分事件

---

## 17. 学分与四同道者体系

### 功能概述
V002 学分+同道者+晋级申请系统，教练通过完成 4 大必修模块获取学分，发展 4 位同道者建立传帮带关系，满足条件后申请晋级。

### 学分模块
- M1-M4: 4 个必修模块 (各有学分值、理论比例、先修条件)
- 选修课: 额外学分来源
- 4 层证据等级: T1(高) → T4(低)

### 同道者关系
- 导师-学员配对 (不可自我指导)
- 晋级要求: L3 需 4 名 L1 同道者, L4 需 4 名 L2, L5 需 4 名 L3

### API 端点

**学分管理 (8 个)**:
- 用户: `GET /v1/credits/my` — 我的学分, `GET /v1/credits/modules` — 模块列表, `GET /v1/credits/records` — 学分记录
- 管理: CRUD + 统计 (5 个)

**同道者关系 (6 个)**:
- 用户: `GET /v1/companion/my-mentees` — 我的学员, `GET /v1/companion/my-mentors` — 我的导师, `POST /v1/companion/invite` — 邀请, `GET /v1/companion/stats` — 统计
- 管理: `GET /v1/companion/all` — 全部关系, `POST /v1/companion/{id}/graduate` — 结业

**晋级申请 (6 个)**:
- `GET /v1/promotion/progress` — 晋级进度
- `GET /v1/promotion/rules` — 晋级规则
- `POST /v1/promotion/apply` — 提交申请
- `GET /v1/promotion/check` — 资格检查
- `GET /v1/promotion/applications` — 申请列表 (管理)
- `POST /v1/promotion/{id}/review` — 审核 (管理)

### 前端页面
- **H5**: `MyCredits.vue` — 我的学分, `MyCompanions.vue` — 我的同道者, `PromotionProgress.vue` — 晋级进度
- **Admin**: `CreditDashboard.vue` — 学分仪表盘, `CourseModuleManage.vue` — 课程模块管理, `CompanionManage.vue` — 同道者管理, `PromotionReview.vue` — 晋级审核

---

## 18. 数据分析与报表

### 功能概述
双层分析体系：教练分析关注个人绩效和学员活跃度，管理员分析关注平台整体运营和系统健康。

### 教练分析 (6 个端点)
- 绩效总览、学员活跃度、干预效果、响应率、趋势、同行对比

### 管理员分析 (7 个端点)
- 平台总览、用户增长、活跃度分析、内容统计、Agent 使用、学习数据、系统健康

### 用户统计 (~5 个端点)
- 用户活动总览、活动历史、日报/周报/月报

### 搜索功能 (1 个端点)
- `GET /v1/search` — 全局搜索 (用户/挑战/微行动/告警/消息)

### 前端页面
- **Admin**: `CoachAnalytics.vue` — 教练分析, `AdminAnalytics.vue` — 管理员分析, `UserActivityReport.vue` — 用户活动报告

---

## 19. 策略引擎与决策追踪

### 功能概述
V007 策略引擎 (PolicyEngine)，5 步管线实现规则匹配→候选筛选→冲突解决→成本控制→决策追踪，支持 TTM 阶段感知和自动退出机制。

### 5 步策略管线
```
Rules(规则注册) → Candidates(适用性矩阵) → Conflict(5策略冲突解决) → Cost(成本控制+模型降级) → Trace(决策追踪)
```

### 4 条种子规则
1. **crisis_absolute_priority** (p=100): 危机绝对优先
2. **medical_boundary_suppress** (p=95): 医疗边界抑制
3. **cost_daily_limit_default** (p=70): 每日成本上限
4. **early_stage_gentle_intensity** (p=60): 早期阶段温和强度

### 成本控制
- 8 模型成本表 (gpt-4o 到 ollama-local)
- 降级路径: gpt-4o → deepseek-chat → qwen-plus → ollama-local
- 3 个预算区间: 正常/警告/超限

### API 端点 (12 个)
- `GET/POST /v1/policy/rules` — 规则列表/创建
- `POST /v1/policy/simulate` — 模拟决策
- `GET /v1/policy/traces` — 决策追踪
- `GET /v1/policy/cost` — 成本统计
- `POST /v1/policy/rules/refresh` — 刷新规则
- `POST /v1/policy/rules/seed` — 种子规则

### 辅助系统
- **StageAwareSelector**: TTM S0-S6 阶段驱动 Agent 选择
- **AutoExitHandler**: 设备异常/关键词/风险/行为触发自动退出
- **EffectivenessMetrics**: 6 项效果指标 (IES/阶段转化率/依从性/风险降低/专家 ROI/生态健康)

---

## 20. Agent 生态市场

### 功能概述
V006 Phase 5 Agent 生态系统，支持 Agent 发布→审核→上架→安装的市场化流程，以及 Agent 组合编排和成长积分。

### 市场流程
```
专家创建 Agent → 发布到市场 → 管理员审核 → 上架 → 其他专家安装 → 安装数+1
```

### API 端点 (11 个)
- `GET /v1/agent-ecosystem/marketplace` — 市场列表
- `POST /v1/agent-ecosystem/marketplace/publish` — 发布 Agent
- `POST /v1/agent-ecosystem/marketplace/{id}/install` — 安装 Agent
- `GET /v1/agent-ecosystem/compositions` — 组合列表
- `POST /v1/agent-ecosystem/compositions` — 创建组合
- `GET /v1/agent-ecosystem/growth-points` — 成长积分
- ... (共 11 个)

### Agent 反馈循环 (8 个端点)
- 用户评分/评论 + 每日指标聚合 + 提示词版本管理 + A/B 测试

### 成长积分系统
- 7 种积分事件: 创建/发布/安装/评分/协作/贡献/被引用
- 专家游戏化激励

### 前端页面
- **Admin**: `AgentMarketplace.vue` — Agent 市场, `AgentGrowthReport.vue` — 成长报告

---

## 21. 专家自助注册入驻

### 功能概述
打通专家从申请→审核→开通的自助注册全流程，5 步向导式表单收集个人信息、专业资质、领域选择、品牌设置、银行信息。

### 注册流程
```
H5 ExpertRegister → 5步向导填写 → POST /apply → 管理员审核 → approve → 角色升级 Coach → 工作室开通
```

### 10 个专业领域
内分泌代谢、中医养生、心理健康、心血管康复、营养管理、睡眠健康、运动康复、体重管理、行为改变、综合健康

### API 端点 (8 个)
- `GET /v1/expert-registration/domains` — 领域列表 (公开)
- `POST /v1/expert-registration/apply` — 提交申请
- `GET /v1/expert-registration/my-application` — 查询状态
- `PUT /v1/expert-registration/my-application` — 修改申请
- `GET /v1/expert-registration/admin/applications` — 待审核列表 (管理)
- `GET /v1/expert-registration/admin/applications/{id}` — 申请详情 (管理)
- `POST /v1/expert-registration/admin/applications/{id}/approve` — 审核通过 (管理)
- `POST /v1/expert-registration/admin/applications/{id}/reject` — 审核拒绝 (管理)

### 前端页面
- **H5**: `ExpertRegister.vue` — 5 步注册向导 (个人信息→专业资质→领域选择→品牌设置→确认提交)
- **H5**: `ExpertApplicationStatus.vue` — 申请状态页
- **Admin**: `ExpertApplicationReview.vue` — 审核队列

---

## 22. 基础设施与运维

### Docker 架构 (4 应用 + 9 基础设施)

**应用容器**:
| 容器 | 端口 | 内存 | 功能 |
|------|------|------|------|
| bhp-api | 8000 | 4GB | FastAPI 后端 (4 Worker) |
| bhp-h5 | 5173 | 256MB | H5 移动端 (Nginx + Vue 3) |
| bhp-admin-portal | 5174 | 256MB | 管理后台 (Nginx + Vue 3) |
| bhp-expert-workbench | 8501 | 1GB | 专家工作台 (Streamlit) |

**基础设施**:
| 容器 | 功能 |
|------|------|
| PostgreSQL (pgvector:pg15) | 主数据库 + 向量存储 |
| Redis 7 | 缓存 + 令牌黑名单 + 分布式锁 |
| Weaviate | 向量数据库 (Dify) |
| Dify (api/web/worker/nginx) | AI 工作流平台 |
| Sandbox + SSRF Proxy | 安全沙箱 |

### 定时任务 (13 个, Redis 分布式锁)

| 时间 | 任务 | 说明 |
|------|------|------|
| 00:05 | program_advance_day | 推进方案天数 |
| 01:30 | agent_metrics_aggregate | Agent 指标聚合 |
| 02:00 | safety_daily_report | 安全日报 |
| 06:00 | daily_task_generation | 生成每日微行动 |
| 06:30 | expire_stale_queue_items | 清理过期推送 |
| 07:00 | knowledge_freshness_check | 知识库新鲜度 |
| 09:00 | program_push_morning | 早间推送 |
| 11:30 | program_push_noon | 午间推送 |
| 17:30 | program_push_evening | 晚间推送 |
| 23:00 | program_batch_analysis | 批量分析 |
| 23:59 | expired_task_cleanup | 清理过期任务 |
| 1min | reminder_check | 提醒检查 |
| 5min | process_approved_pushes | 处理已批推送 |

### 数据库规模
- **119 个 ORM 模型** (core/models.py 为权威来源)
- **30 个 Alembic 迁移** (001→030 线性链)
- **pgvector**: 768 维向量索引 (sentence-transformers)
- **连接池**: 30 连接, 3600 秒回收

### 监控与安全
- Prometheus + Sentry 集成
- CORS 白名单 + 安全头 + 请求日志 + 限流
- 所有容器配置健康检查 (30 秒间隔)
- Redis SETNX 分布式互斥锁 (优雅降级)

### 测试体系
- **98 个测试**, 6 层策略:
  - Layer 0: 环境预检
  - Layer 1: 模型验证
  - Layer 2: 数据库 CRUD + 向量搜索
  - Layer 3: 服务层 (解析/分块/嵌入)
  - Layer 4: API 端点
  - Layer 5: 端到端流程

---

## 附录: 平台数据统计

| 维度 | 数量 |
|------|------|
| 后端路由模块 | 57 |
| API 端点 | 511+ |
| ORM 数据模型 | 119 |
| 数据库迁移 | 30 |
| Admin 前端页面 | 86+ |
| H5 前端页面 | 41 |
| 前端路由 | 116 (Admin 76 + H5 40) |
| 配置文件 | 26 |
| 定时任务 | 13 |
| AI Agent | 12 硬编码 + N 动态 |
| 测试用例 | 98 |
| Docker 容器 | 13 (4 应用 + 9 基础设施) |
| Python 依赖 | 50 |

---

> 本文档基于 2026-02-13 代码库实际审计生成，涵盖所有已实现并可立即启用的功能。

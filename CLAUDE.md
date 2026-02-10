# BHP 行为健康数字平台 — Claude Code 项目指令

> 本文件由 Claude Code 自动加载，指导 AI 如何在本项目中工作。

---

## 一、项目概述

BHP（Behavioral Health Platform）是一个行为健康数字化管理平台，服务于慢病逆转与行为改变领域。平台包含 C 端用户、教练、专家、管理员四种角色，集成了评估引擎、AI Agent 系统、RAG 知识库、智能监测方案等核心能力。

**规模**: 49 路由模块 · 430+ API 端点 · 70 数据模型 · 21 迁移版本 · 12 AI Agent · 13 Docker 容器

---

## 二、技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python 3.10+ / FastAPI / Uvicorn (4 workers) / APScheduler |
| ORM | SQLAlchemy + Alembic |
| 数据库 | PostgreSQL (pgvector) + Redis + Weaviate |
| 认证 | JWT (python-jose) + bcrypt (passlib) + Token 黑名单 |
| Admin 前端 | Vue 3 + TypeScript + Vite + Ant Design Vue 4 + Tailwind CSS |
| H5 移动端 | Vue 3 + TypeScript + Vite + Vant 4 + Tailwind CSS |
| LLM | Ollama (qwen2.5:0.5b / qwen2.5vl:7b) + Dify 工作流 |
| 嵌入 | sentence-transformers (text2vec-base-chinese, 768 维) / Ollama nomic-embed-text (回退) |
| 容器化 | Docker Compose |
| 反向代理 | nginx (前端容器内, /api → bhp-api) |

---

## 三、项目结构

```
behavioral-health-project/
├── api/                        # FastAPI 后端
│   ├── main.py                 # FastAPI 入口
│   ├── models.py               # 70 个 SQLAlchemy 数据模型 + ROLE_LEVEL 映射
│   ├── database.py             # SQLAlchemy 引擎/会话管理
│   ├── dependencies.py         # 认证守卫: get_current_user / require_admin / require_coach_or_admin
│   ├── middleware.py            # CORS / 安全头 / 日志 / 限流
│   ├── scheduler.py            # APScheduler 11 个定时任务 (Redis 互斥锁)
│   ├── *_api.py                # 49 个路由模块
│   ├── *_service.py            # 61 个核心服务
│   ├── core/
│   │   ├── redis_lock.py       # Redis SETNX 分布式互斥锁
│   │   ├── master_agent_v0.py  # MasterAgent 九步处理流程 + 12个Agent + 路由器 + 协调器
│   │   ├── master_agent.py     # 从v0导入，保持兼容
│   │   ├── behavioral_profile_service.py  # BAPS→统一画像
│   │   ├── intervention_matcher.py        # 领域干预匹配引擎
│   │   ├── knowledge/          # RAG: chunker / embedding / retriever / rag_middleware
│   │   ├── brain/
│   │   │   ├── stage_runtime.py    # 阶段运行态引擎 (唯一可写 current_stage)
│   │   │   ├── policy_gate.py      # 策略闸门 (所有干预必须过闸)
│   │   │   └── decision_engine.py  # 决策引擎
│   │   └── schemas/
│   │       └── behavior_logic.json # 行为模式 + 心理准备度定义
│   ├── baps/                   # BAPS 五维评估: scoring_engine / questionnaires / report_generator
│   └── migrations/             # Alembic 迁移 (001-018, V002-V004)
├── admin-portal/               # Vue 3 管理后台 (:5174)
│   └── src/
│       ├── views/              # 86 个页面
│       ├── stores/             # 5 个 Pinia Store
│       ├── api/                # API 调用模块
│       ├── composables/        # Vue Composables (含 useStageStyle)
│       ├── components/         # 组件
│       └── styles/             # BHP Design System + antd-overrides.css
├── h5/                         # Vue 3 移动端 (:5173)
│   └── src/
│       ├── views/              # 30 个页面
│       ├── stores/             # 3 个 Pinia Store
│       ├── api/                # API 调用模块
│       └── styles/             # BHP Design System + vant-overrides.css
├── knowledge/                  # 知识库内容 (Markdown)
├── configs/                    # 业务配置文件
│   ├── spi_mapping.json        # 阶段阈值 + L1-L5映射 + 交互模式
│   ├── badges.json             # 徽章配置
│   └── assessment/             # 评估相关配置
│       ├── prescription_strategy_library.json  # L1-L5策略 + 处方六要素
│       └── spi_implicit_mapping_complete.json  # 隐式数据源映射
├── models/
│   └── rx_library.json         # 8类行为处方模板
├── docker-compose.app.yaml     # 应用容器
├── docker-compose.yaml         # Dify 基础设施容器
├── behavioral-prescription-core-logic.md      # 核心业务逻辑文档
└── platform-architecture-overview.md  # 架构总览文档 (详细参考)
```

---

## 四、Docker 端口映射

| 容器 | 端口 | 说明 |
|------|------|------|
| bhp-api | 8000-8002 | FastAPI 主 API (健康检查: `GET /health`) |
| bhp-h5 | 5173→80 | H5 移动端 (nginx) |
| bhp-admin-portal | 5174→80 | 管理后台 (nginx) |
| bhp-expert-workbench | 8501 | Streamlit 专家工作台 |
| dify-web | 3000 | Dify 前端 |
| dify-api | 5001 | Dify 后端 |
| dify-nginx | 8080/8443 | Dify 网关 |
| dify-db (PostgreSQL) | 5432 (已暴露) | pgvector 扩展 |
| dify-redis | 6379 | 会话缓存 / Token 黑名单 / 调度锁 |

**网络**: 所有容器共享 `dify_dify-network` 外部网络。

---

## 五、编码规范

### 后端 (Python/FastAPI)

- API 路由统一前缀 `/api/v1/`，**不要出现 `/api/api/v1/` 双前缀**
- 所有路由文件命名 `*_api.py`，服务文件命名 `*_service.py`
- 认证守卫使用 `dependencies.py` 中的:
  - `get_current_user` → 普通用户
  - `require_coach_or_admin` → role_level >= 4
  - `require_admin` → role_level >= 99
- 角色层级: observer(1) → grower(2) → sharer(3) → bhp_coach(4) → bhp_promoter(5) → bhp_master(6) → admin(99)
- ⚠️ 数据库兼容: 旧数据中 `coach/promoter/master` 需迁移为 `bhp_coach/bhp_promoter/bhp_master`
- 定时任务必须使用 `@with_redis_lock` 装饰器 (见 `core/redis_lock.py`)
- 数据库操作使用 SQLAlchemy 异步会话, 通过 `get_db` 依赖注入
- 新增数据模型写在 `models.py`, 新迁移用 Alembic
- 中文注释, 遵循 PEP8

### 前端 (Vue 3 + TypeScript)

- 使用组合式 API (`<script setup lang="ts">`)
- Admin 使用 Ant Design Vue 4 组件, H5 使用 Vant 4 组件
- 样式遵循 BHP Design System, 品牌主色 `--bhp-brand-primary: #10b981` (翡翠绿)
- TTM 阶段样式使用 `useStageStyle` composable
- API 调用统一放 `src/api/` 目录, 使用 axios 实例
- 前端 API 路径: `${API_BASE}/v1/...` (nginx 已配置 /api 前缀转发)
- Store 使用 Pinia, 放 `src/stores/` 目录

---

## 六、核心业务概念

### 6.1 BAPS 五维评估体系 (平台核心)

**BAPS** = Behavioral Assessment & Prescription System（行为评估与处方系统）

五维评估框架, 共 171 题:
- **TTM7 改变阶段评估** (21题): 判定用户当前行为改变阶段 S0-S6, **必填**
- **BIG5 大五人格** (50题): 外向性/神经质/尽责性/宜人性/开放性
- **BPT-6 行为分型** (18题): 行动型/知识型/情绪型/关系型/环境型/混合型
- **CAPACITY 改变潜力** (32题): 8 维度(信心/觉察/资源/计划/能力/应对/网络/时间)
- **SPI 成功指数** (50题): 加权计算成功概率, 映射 L1-L5 心理层级

评估管道: `BAPS → BehavioralProfile → StageRuntime(TTM阶段) → PolicyGate(策略闸门) → InterventionMatcher → MicroAction`

源码索引: `core/baps/scoring_engine.py`, `core/baps/questionnaires.py`, `core/baps/question_bank.json`

### 6.2 TTM7 七阶段行为改变模型

| 阶段 | 中文名 | 英文(Core) | 友好名称 | 描述 |
|------|--------|-----------|----------|------|
| S0 | 无知无觉 | precontemplation | 探索期 | 未意识到需要改变 |
| S1 | 强烈抗拒 | contemplation | 思考期 | 知道问题但抗拒改变 |
| S2 | 被动承受 | - | - | 被动接受但不主动 |
| S3 | 勉强接受 | preparation | 准备期 | 愿意小步尝试 |
| S4 | 主动尝试 | action | 成长期 | 主动采取行动 |
| S5 | 规律践行 | maintenance | 巩固期 | 形成规律习惯 |
| S6 | 内化为常 | - | 收获期 | 行为成为自然一部分 |

源码: `core/models.py:823-831` `class BehavioralStage`

> ⚠️ **P编码废弃 (v3.0)**: 项目规划文件中原使用 P0-P5 阶段编码, 其名称与 L1-L5 完全重复 (P1=完全对抗=L1, P2=抗拒与反思=L2...), 说明策略矩阵本质是心理准备度维度。v3.0 起策略矩阵统一使用 L1-L5 查询, P 编码保留但不再用于新逻辑。详见 `UnifiedStageResolver` (core/stage_mapping.py)。

**阶段升级硬条件** (仅 `StageRuntimeBuilder` 可写 `current_stage`):

| 升级路径 | 条件 |
|----------|------|
| S0→S1 | min_awareness ≥ 0.3 |
| S1→S2 | min_belief ≥ 0.3, min_awareness ≥ 0.5 |
| S2→S3 | min_belief ≥ 0.6, min_capability ≥ 0.5 |
| S3→S4 | min_belief ≥ 0.7, 7天内完成≥3次行为 |
| S4→S5 | min_belief ≥ 0.8, 连续14天行为记录 |
| S5→S6 | min_belief ≥ 0.9, 连续60天行为记录 |

规则: 只进一阶(不可跳级), 降级无条件直接执行。

### 6.3 五层次心理准备度 (L1-L5)

| 层级 | 中文名 | SPI系数 | 最大成功率 | 策略 | 最大任务数 |
|------|--------|---------|-----------|------|-----------|
| L1 | 完全对抗 | 0.3 | 30% | 安全感建立, 禁止设定目标 | 1 |
| L2 | 抗拒与反思 | 0.5 | 30% | 矛盾处理, 探索性尝试 | 1 |
| L3 | 妥协与接受 | 0.7 | 40-60% | 微习惯处方, 降低门槛 | 2 |
| L4 | 顺应与调整 | 0.9 | 70-85% | 系统化行为方案 | 3 |
| L5 | 全面臣服 | 1.0 | 90%+ | 自主管理, 身份巩固 | 不限 |

SPI 映射: 0-14→L1, 15-29→L2, 30-49→L3, 50-69→L4, ≥70→L5

SPI 计算公式: `SPI = (触发原因总分/125) × 心理层次系数 × (迫切度综合分/30) × 100`

源码: `configs/spi_mapping.json`, `configs/assessment/prescription_strategy_library.json`

> **v3.0 变更**: L1-L5 现在是策略矩阵的**唯一查询维度** (替代原P0-P5), 也是内容推荐和交互模式的核心输入。

### 6.4 MasterAgent 九步处理流程

```
用户输入 → Step1-2: Orchestrator接收
         → Step3: 更新 UserMasterProfile
         → Step4: AgentRouter 判别问题类型与风险
         → Step4.5: InsightGenerator 数据洞察
         → Step5: 调用 1-2个专业Agent
         → Step6: MultiAgentCoordinator 整合结果
         → Step7: InterventionPlanner 生成干预路径 (核心)
         → Step8: ResponseSynthesizer 统一教练风格输出
         → Step9: 写回 Profile + 生成今日任务
```

**6 个核心数据结构体**: CoreUserInput → CoreUserMasterProfile → CoreAgentTask → CoreAgentResult → CoreInterventionPlan → CoreDailyTask

**唯一权威原则**: UserMasterProfile 是系统唯一权威用户主画像源, 只有 MasterOrchestrator 可写入。

源码: `core/master_agent_v0.py`

### 6.5 十二专业 Agent 体系

**专科 Agent (9个)**:
- CrisisAgent (优先级0, 最高) — 自杀/自残/不想活
- GlucoseAgent (优先级1) — 血糖/糖尿病
- SleepAgent / StressAgent / MentalHealthAgent (优先级2)
- NutritionAgent / ExerciseAgent (优先级3)
- TCMWellnessAgent (优先级4) — 中医养生
- MotivationAgent — 动机管理

**整合型 Agent (3个)**: BehaviorRxAgent(行为处方) / WeightAgent(体重) / CardiacRehabAgent(心脏康复)

路由优先级: 危机状态 > 风险等级 > 意图关键词 > 用户偏好 > 设备数据 > 领域关联

冲突消解优先: glucose > nutrition, sleep > exercise, stress > exercise, mental > exercise

源码: `core/master_agent_v0.py:3657-3731`

### 6.6 策略闸门 (RuntimePolicyGate)

**所有干预决策必须经过策略闸门**, 规则链按优先级:

| # | 条件 | 决策 | 说明 |
|---|------|------|------|
| 1 | 不稳定态 + 强干预请求 | DELAY | 保护不稳定用户 |
| 2 | S0-S1阶段 | ALLOW_SOFT_SUPPORT | 禁止 challenge/execution |
| 3 | dropout_risk + S3+ | ESCALATE_COACH | 需教练介入 |
| 4 | relapse_risk | ALLOW_SOFT_SUPPORT | 复发风险仅允许软支持 |
| 5 | 其余 | ALLOW | 正常放行 |

源码: `core/brain/policy_gate.py:43-100`

### 6.7 行为处方六要素

| 要素 | 说明 | 必填 |
|------|------|------|
| target_behavior | 目标行为 (具体要做什么) | ✅ |
| frequency_dose | 频次剂量 (多久做一次) | ✅ |
| time_place | 时间地点 (何时何地做) | ✅ |
| trigger_cue | 启动线索 (用什么提醒自己) | ✅ |
| obstacle_plan | 障碍预案 (遇到困难怎么办) | ✅ |
| support_resource | 支持资源 (谁或什么帮助你) | 否 |

处方按 SPI 分数设定难度: ≥70挑战级(系数1.0), 50-69中等(0.7), 30-49简单(0.4), <30最低(0.2)

### 6.8 改变动因体系 (6大类 × 24小类)

平台理论基础定义了完整的行为改变触发因素分类:

| 代码 | 大类 | 对应 configs 目录 |
|------|------|------------------|
| C1-C4 | 内在驱动力 (价值/身份/意义/自主) | `干预策略大全` |
| C5-C8 | 外在事件 (健康/生活/社会/经济压力) | `干预策略大全` |
| C9-C12 | 情绪体验 (恐惧/愤怒/羞耻/积极) | `干预策略大全` |
| C13-C16 | 认知与知识 (顿悟/知识/风险/未来) | `干预策略大全` |
| C17-C20 | 能力与资源 (时间/经济/技能/环境) | `干预策略大全` |
| C21-C24 | 社会支持 (榜样/同伴/家庭/专业) | `干预策略大全` |

24原因 × 6阶段 = 144 条干预策略, 每条含匹配策略 + 参考话术。

### 6.9 四阶段养成模型

| 阶段 | 时间 | 核心目标 |
|------|------|----------|
| 启动期 (startup) | 1-2周 | 建立打卡习惯, 降难度+增监测 |
| 适应期 (adaptation) | 3-8周 | 巩固行为, 应对障碍 |
| 稳定期 (stability) | 2-4月 | 减少外部依赖 |
| 内化期 (internalization) | 4月+ | 行为成为自然一部分 |

### 6.10 证据分层

T1(临床指南, priority=9) → T2(RCT, 7) → T3(专家共识, 5) → T4(个人经验, 3)

### 6.11 推送审批网关

所有推送(挑战/预警/微行动/AI建议) → CoachPushQueue(pending) → 教练审批 → 投递给学员

### 6.12 六种隐式数据源

| 数据源 | ID | 更新频率 |
|--------|-----|----------|
| 对话内容分析 | CONV | 实时, 14天窗口 |
| 任务执行表现 | TASK | 每日, 30天窗口 |
| 可穿戴设备数据 | DEVICE | 实时, 7天窗口 |
| 触发事件历史 | TRIGGER | 实时, 30天窗口 |
| 交互行为模式 | INTERACT | 每日, 14天窗口 |
| 用户画像提取 | PROFILE | 检测时, 90天窗口 |

### 6.13 四维用户状态模型 (v3.0)

```
user_state = {
    behavioral_stage: S0-S6,       # 行为事实 (TTM7评估)
    readiness_level: L1-L5,        # 心理准备度 (SPI问卷)
    growth_level: G0-G5,           # 角色等级 (积分+考试)
    health_competency: Lv0-Lv5,    # 健康管理能力 (30题评估) ← v3.0新增
}
```

**维度独立原则**: 四个维度测量不同构念、不同数据源、不同升级逻辑，不可合并。

**统一阶段解析**: `UnifiedStageResolver` (core/stage_mapping.py) 负责将 S+L 合并为面向策略矩阵的查询键, 无SPI数据时从S降级推断L。

### 6.14 健康能力六级 (Lv0-Lv5, v3.0)

| 等级 | 中文名 | 核心特征 | G等级前置 |
|------|--------|----------|-----------|
| Lv0 | 完全无知者 | 不知道风险、不理解原理 | G0 |
| Lv1 | 问题觉察者 | 意识到问题但不会做 | G1 |
| Lv2 | 方法学习者 | 会按步骤做但不稳定 | G2 |
| Lv3 | 情境适配者 | 能在不同情境中调整 | G3 |
| Lv4 | 自我驱动者 | 健康行为已成习惯 | G4 |
| Lv5 | 使命实践者 | 能影响他人 | G5 |

- 评估: 30题问卷, 6级×5题 (Lv0反向计分)
- 作用: 角色升级(G)的能力前置条件 + 平台内容推荐依据
- 数据库: `users.health_competency_level` 列, `health_competency_assessments` 表

### 6.15 v3.0 新增评估工具

| 评估 | 题数 | 用途 | 数据库表 |
|------|------|------|----------|
| COM-B能力评估 | 18 | 识别能力/机会/动机瓶颈 | `comb_assessments` |
| 自我效能评估 | 5 | 任务/维持/恢复/情境/社交效能 | `self_efficacy_assessments` |
| 支持体系五层评估 | 27 | 5层×质量+稳定性 | `support_assessments` |
| 障碍十类评估 | 40 | 10类×4题, 驱动处方调整 | `obstacle_assessments` |
| 健康能力六级评估 | 30 | 6级×5题, 驱动内容推荐 | `health_competency_assessments` |

### 6.16 成长等级升级门槛 (v3.0 更新)

| 升级 | 成长积分 | 贡献积分 | 影响积分 | 考试 | 同道者 | 最低健康能力 |
|------|---------|---------|---------|------|--------|------------|
| G0→G1 | 100 | - | - | - | - | Lv1 |
| G1→G2 | 500 | 50 | - | - | - | Lv2 |
| G2→G3 | 800 | 200 | 50 | ✓ | 4×G1 | Lv3 |
| G3→G4 | 1500 | 600 | 200 | ✓ | 4×G2 | Lv4 |
| G4→G5 | 3000 | 1500 | 600 | ✓ | 4×G3 | Lv5 |

---

```bash
# 启动全部容器
docker compose -f docker-compose.yaml -f docker-compose.app.yaml up -d

# 仅重建后端
docker compose -f docker-compose.app.yaml up -d --build bhp-api

# 查看后端日志
docker logs -f bhp-api --tail 100

# 进入后端容器
docker exec -it bhp-api bash

# 健康检查
curl http://localhost:8000/health

# 查看 API 文档
curl http://localhost:8000/openapi.json | python -m json.tool

# 数据库迁移
cd api && alembic upgrade head

# 前端开发 (Admin)
cd admin-portal && npm run dev

# 前端开发 (H5)
cd h5 && npm run dev
```

---

## 八、禁止操作 ⛔

1. **不要删除或修改** `migrations/` 中已有的迁移文件
2. **不要修改** `dependencies.py` 中的认证中间件逻辑，除非明确要求
3. **不要硬编码** JWT 密钥、数据库密码等敏感信息 (从 .env 读取)
4. **不要修改** `ROLE_LEVEL` 角色层级映射 (models.py 中定义)
5. **不要** 在前端 API 路径中使用 `/api/api/v1/` (已知踩坑, QA-3)
6. **不要** 直接修改 `dify-db` 中的表结构 (Dify 自有迁移)
7. **不要** 删除 `@with_redis_lock` 装饰器 (保证多 worker 安全)
8. **不要** 在 `StageRuntime` 之外的地方写入 `current_stage` 字段
9. **不要** 修改 `core/brain/policy_gate.py` 中的规则链优先级，除非明确要求
10. **不要** 修改 `configs/spi_mapping.json` 中的阶段阈值和层级映射，除非有业务需求确认

---

## 九、已知问题与注意事项

- `/v1/health/p001/*` 返回 404 是正常的 → `health.ts` 有 mock fallback
- `/v1/tenants/hub` 返回空列表 → 无种子专家数据, 空状态正常
- 未登录状态下 API 返回 401 → 正常的 JWT 保护
- Westworld 仿真注入端点 (3个) 仅用于测试, 内存存储, 不要用于生产
- PostgreSQL 端口 5432 已对外暴露 (Dify 共用), 注意连接到正确的 database

---

## 十、关键配置文件索引

| 配置文件 | 内容 | 影响范围 |
|----------|------|----------|
| `configs/spi_mapping.json` | 阶段阈值 + L1-L5层级映射 + 交互模式 | StageRuntime, ProfileService |
| `configs/assessment/prescription_strategy_library.json` | L1-L5策略 + 处方六要素 + SMART规则 | InterventionPlanner |
| `configs/assessment/spi_implicit_mapping_complete.json` | 6种隐式数据源 + 心理层级映射 | 隐式数据采集管道 |
| `core/schemas/behavior_logic.json` | 5种行为模式 + 心理准备度定义 | 行为模式识别 |
| `models/rx_library.json` | 8类行为处方模板 (含三阶段策略) | InterventionMatcher |
| `core/baps/question_bank.json` | 问卷原始题库 | BAPS评估 |
| `configs/badges.json` | 徽章配置 | 成长体系 |
| `configs/health_competency_questions.json` | 30题健康能力评估 *(v3.0)* | 健康能力评估API |
| `configs/comb_questions.json` | 18题COM-B能力评估 *(v3.0)* | COM-B评估API |
| `configs/self_efficacy_questions.json` | 5题自我效能评估 *(v3.0)* | 自我效能评估API |
| `configs/support_assessment_questions.json` | 27题支持体系评估 *(v3.0)* | 支持评估API |
| `configs/obstacle_questions_full.json` | 40题障碍评估(10类×4) *(v3.0)* | 障碍评估+处方调整 |

---

## 十一、核心术语速查 (开发时常见)

| 代码中的变量/类名 | 含义 |
|-------------------|------|
| `current_stage` (S0-S6) | 用户当前行为改变阶段, 仅 StageRuntimeBuilder 可写 |
| `stage_hypothesis` | Agent 提出的阶段假设(非最终), 需 StageRuntime 确认 |
| `spi_score` | 成功可能性指数 (0-100) |
| `psychological_level` (L1-L5) | 心理准备度层级 |
| `readiness_level` (L1-L5) | 心理准备度 (v3.0 统一用词, 替代原 stage_code/P编码) |
| `health_competency` (Lv0-Lv5) | 健康管理能力等级 *(v3.0新增)* |
| `growth_level` (G0-G5) | 社区角色等级 |
| `UnifiedStageResolver` | 统一阶段解析器, S+L→策略查询键 *(v3.0新增)* |
| `cultivation_stage` | 养成阶段: startup/adaptation/stability/internalization |
| `interaction_mode` | 交互模式: empathy(S0-S1)/challenge(S2-S3)/execution(S4-S6) |
| `bpt_type` | 行为分型: action/knowledge/emotion/relation/environment/mixed |
| `rx_library` | 行为处方库 (8类处方模板) |
| `policy_gate_decision` | 闸门决策: ALLOW/DELAY/ALLOW_SOFT_SUPPORT/ESCALATE_COACH/DENY |
| `data_updates` | Agent→Orchestrator 合法写回通道之一 |
| `UserMasterProfile` | 系统唯一权威用户主画像源 |
| `AgentTask` / `AgentResult` | Orchestrator↔Agent 标准通信对象 |
| `InterventionPlan` | 干预路径对象 (从分析到行动的桥梁) |
| `CoreDailyTask` | 每日任务 (系统产生行为改变的执行出口) |

---

## 十二、参考文档

| 文档 | 位置 | 内容 |
|------|------|------|
| 架构总览 | `platform-architecture-overview.md` | 1700+行, 完整路由/模型/服务/数据流 |
| 核心业务逻辑 (v3.0) | `behavioral-prescription-core-logic-supplemented.md` | 2367行, 26章, §1-16原始 + §17-23代码规范 + §24-26 v3.1更新 |
| 架构审查报告 | `architecture-review-v3.md` | 四项审查结论 + 代码补全清单 + 冲突修复 |
| 差距分析报告 | `gap-analysis-report.md` | 11项遗漏分析 + 7项CLAUDE.md补充建议 |
| 项目规划文件 | `行为健康项目规划文件/` | 32份理论框架、评估工具、课程体系设计文档 |

> ⚠️ `behavioral-prescription-core-logic.md` (750行) 为原始v1.0, 已被 `behavioral-prescription-core-logic-supplemented.md` (2472行, v3.0) 取代。开发时应以 supplemented 版为准。

---

## 十三、测试阶段专用规则 (上线前)

> ⚠️ 当前处于上线前测试阶段，以下规则优先级高于一般开发规范。上线后可移除本章节。

### 13.1 数据保护

- **禁止** 对生产数据库执行 `DROP TABLE`、`TRUNCATE`、`DELETE FROM ... WHERE 1=1` 等批量删除
- **禁止** 修改已有迁移文件，如需变更必须新建迁移版本
- **禁止** 直接操作 `dify-db` 容器中的 Dify 内部表
- 测试数据使用 Westworld 仿真注入端点（3个 `/inject` 端点），不要手动 INSERT
- 修改 models.py 后必须生成新迁移: `alembic revision --autogenerate -m "描述"`

### 13.2 测试优先级与策略

平台已有 6 层测试体系（98 测试全通过），新增代码必须维护现有测试通过率：

| 层级 | 范围 | 修改后必须验证 |
|------|------|---------------|
| L0 预检 | 容器启动 / 端口可达 / 健康检查 | 任何 Docker 配置变更后 |
| L1 模型 | SQLAlchemy 模型加载 / 枚举完整性 | 修改 models.py 后 |
| L2 数据库 | 迁移可执行 / 表结构一致 | 新增迁移后 |
| L3 服务 | 核心 service 单元测试 | 修改 *_service.py 后 |
| L4 API | 端点 HTTP 状态码 / 认证 / 参数校验 | 修改 *_api.py 后 |
| L5 E2E | 前后端联调 / 关键用户流程 | 发版前 |

```bash
# 运行全量测试
python -m pytest tests/ -v

# 只跑某一层
python -m pytest tests/test_l0_precheck.py -v
python -m pytest tests/test_l4_api.py -v
```

### 13.3 Bug 修复规范

- 修 bug 前先**复现**：写出触发条件、请求参数、预期 vs 实际结果
- 修复后必须**回归验证**：确认原问题消失且未引入新问题
- 每次修复在提交信息中标注: `fix(模块): 问题描述 [QA-编号]`
- 已知修复记录参考架构文档第 24 章 (QA-1 ~ QA-3)

### 13.4 API 契约锁定

测试阶段 API 接口契约已基本稳定（430+ 端点），遵循以下原则：

- **不要** 变更现有端点的 URL 路径、HTTP 方法或请求体结构
- **不要** 删除已有的返回字段（可新增字段，但不能移除）
- **不要** 变更认证要求（公开→需认证、coach→admin 等权限升级）
- 如必须做 breaking change，需在返回体中增加 `api_version` 字段，并通知前端同步修改
- 新增端点必须确认已在 `main.py` 中 `include_router` 注册

### 13.5 前端修改规则

- 修改前端页面后必须验证: `npm run build` 零错误 + `vue-tsc --noEmit` 零错误
- **不要** 修改 `src/styles/bhp-design-system.css` 中的 CSS 变量定义（40 章节已锁定）
- **不要** 修改 `vant-overrides.css` 和 `antd-overrides.css` 除非明确要求
- 新增页面必须在 `router/index.ts` 中注册路由
- 新增 API 调用必须放在 `src/api/` 目录，不要在 .vue 文件中直接写 fetch/axios

### 13.6 容器操作规范

```bash
# ✅ 安全操作
docker compose -f docker-compose.app.yaml restart bhp-api     # 重启单个容器
docker compose -f docker-compose.app.yaml up -d --build bhp-api  # 重建单个容器
docker logs -f bhp-api --tail 200                               # 查看日志

# ⛔ 危险操作 — 测试阶段禁止
docker compose down -v          # 会删除所有数据卷！
docker system prune -a          # 会清除所有镜像！
docker volume rm ...            # 会丢失数据库数据！
```

- 重建后端容器后必须检查: `curl http://localhost:8000/health` 返回 200
- 重建前端容器后必须检查: 访问对应端口返回 HTML（不是 nginx 502）
- 不要同时重建全部容器，逐个重建以便定位问题

### 13.7 环境变量检查

修改 `.env` 或环境配置后，确认以下关键变量存在且正确:

```bash
# 后端必需
DATABASE_URL=postgresql+asyncpg://...     # 指向正确的数据库
REDIS_URL=redis://...                      # Redis 连接
JWT_SECRET_KEY=...                         # 不能为空
OLLAMA_BASE_URL=http://host.docker.internal:11434  # Ollama 地址
DIFY_API_URL=http://dify-nginx:8080        # Dify 内网地址

# 前端必需 (.env.production)
VITE_API_BASE_URL=/api                     # nginx 反代前缀，不是 http://...
```

### 13.8 上线前检查清单

每次提交重大变更后，执行以下自检:

```bash
# 1. 容器状态
docker ps --format "table {{.Names}}\t{{.Status}}" | grep bhp

# 2. 后端健康
curl -s http://localhost:8000/health | python -m json.tool

# 3. H5 路由可达
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/

# 4. Admin 路由可达
curl -s -o /dev/null -w "%{http_code}" http://localhost:5174/

# 5. API 文档可访问
curl -s http://localhost:8000/openapi.json | python -c "import sys,json; d=json.load(sys.stdin); print(f'端点数: {len(list(d[\"paths\"].keys()))}')"

# 6. 全量测试
python -m pytest tests/ -v --tb=short
```

### 13.9 日志与排障

- 后端日志优先看 `docker logs bhp-api`，关注 `ERROR` 和 `Traceback`
- 前端构建问题看 `docker logs bhp-h5` / `docker logs bhp-admin-portal`
- 数据库连接问题: 确认 `dify-db` 容器运行中 + 端口 5432 可达
- Redis 连接问题: 确认 `dify-redis` 容器运行中 + 端口 6379 可达
- API 404: 先检查路由是否在 `main.py` 中注册，再检查前缀是否正确
- API 401: 检查 JWT token 是否过期或在黑名单中

### 13.10 Git 提交规范 (测试阶段)

```bash
# 格式
<type>(<scope>): <描述> [可选: QA-编号]

# 类型
fix:    Bug 修复
test:   测试相关
perf:   性能优化
hotfix: 紧急修复
chore:  配置/构建变更

# 示例
fix(api): 修复双前缀 /api/api/v1/ 导致 404 [QA-3]
test(l4): 新增问卷引擎 API 端点测试
hotfix(auth): 修复 refresh_token 过期未正确返回 401
chore(docker): 优化 bhp-api 容器内存限制至 4G
```

---

## 十四、v3.0 架构变更与实施指南

> 本章记录 v3.0 架构审查引入的变更, 需在开发中逐步落地。

### 14.1 核心架构变更

| 变更项 | 原状态 | v3.0状态 | 优先级 |
|--------|--------|----------|--------|
| P编码废弃 | 策略矩阵用 P0-P5 查询 | 统一使用 L1-L5, P保留兼容 | P1 |
| 用户状态维度 | 三维 (S+L+G) | 四维 (S+L+G+Lv) | P1 |
| 角色升级 | 三维积分+考试+同道者 | +健康能力(Lv)前置条件 | P2 |
| 角色命名 | coach/promoter/master | bhp_coach/bhp_promoter/bhp_master | P1 |

### 14.2 数据库迁移 (v3.0)

```sql
-- 新增表 (3张)
CREATE TABLE health_competency_assessments (...);   -- §25
CREATE TABLE comb_assessments (...);                 -- §20.5
CREATE TABLE self_efficacy_assessments (...);        -- §20.6

-- 表结构变更
ALTER TABLE users ADD COLUMN health_competency_level VARCHAR(4) DEFAULT 'Lv0';
ALTER TABLE intervention_strategies ADD COLUMN readiness_level VARCHAR(4);

-- 角色名迁移
UPDATE users SET role='bhp_coach' WHERE role='coach';
UPDATE users SET role='bhp_promoter' WHERE role='promoter';
UPDATE users SET role='bhp_master' WHERE role='master';
```

### 14.3 规范文档 vs 可执行代码

> ⚠️ **重要**: `behavioral-prescription-core-logic-supplemented.md` 和 `architecture-review-v3.md` 是**规范文档**, 不是可直接运行的代码。其中的 Python 代码块是数据结构定义和算法规范, 需要开发者:

1. 将代码块提取为实际 `.py` 文件 (放入 `api/core/`, `api/baps/` 等目录)
2. 将问卷/配置提取为 `.json` 文件 (放入 `configs/` 目录)
3. 用 Alembic 创建数据库迁移脚本
4. 编写对应的 API 路由和服务层

**实施路线**:

| 阶段 | 内容 | 工时 | 依赖 |
|------|------|------|------|
| P1 | UnifiedStageResolver + P→L迁移 + 角色名迁移 | 3-5天 | 无 |
| P2 | 5个评估API + 健康能力等级 + 升级逻辑 | 5-7天 | P1 |

### 14.4 尚未纳入规范的规划文档

以下规划文件内容暂未编入核心逻辑文档, 属于理论参考或未来扩展:

| 文件 | 内容 | 是否需实现 |
|------|------|-----------|
| 多维年龄体系总览表.docx | 12维年龄概念(生理/功能/心理/社会等) | 未来扩展, 需穿戴设备数据 |
| 自我5个层次.docx | 发现→实现→建立→超越→无我 | 理论框架, 可融入课程内容 |
| 疯传VS让创意更有黏性.docx | STEPPS传播模型 | 运营策略, 非平台功能 |
| 行为健康市场定位.docx | 产品卖点/竞争优势 | 商业文档, 非技术实现 |
| 行为倾向模式模式评估处方.docx | 四级概念框架(倾向→类型→评估→处方) | 部分已由BPT-6覆盖 |
| 问题解决行为类型测评问卷.docx | 6维问题解决行为评估 | 可作为新评估工具补充 |

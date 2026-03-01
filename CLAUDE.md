# CLAUDE.md — BehaviorOS Platform Context

> Last updated: 2026-03-02
> Anchor: stabilize-from-sprint1 (9a6b18b)

## What Is This Project

BehaviorOS（行健平台）is a behavioral health operating system that combines traditional Chinese medicine principles with modern behavioral science to create comprehensive health intervention programs. The platform serves as the foundational "OS layer" upon which multiple product surfaces are built.

## Architecture Overview

```
BehaviorOS 底座 (FastAPI + PostgreSQL + Redis + Qdrant)
    │  896+ API endpoints │ 21 Agents │ 150+ tables
    │
    ├── coach-miniprogram (WeChat MiniProgram, uni-app + Vue3)
    │     └── 当前开发焦点: 教练培养体系小程序
    │
    ├── bhp-h5 (Vant-based H5, 公众三角色)
    │     └── Observer/Grower/Sharer 成长路径
    │
    ├── admin-portal (管理后台)
    │
    └── gateway (API网关/Agent路由)
```

## Tech Stack

| Layer | Technology | Port/Location |
|-------|-----------|---------------|
| Backend API | FastAPI (Python 3.11) | localhost:8000 |
| Database | PostgreSQL 15 | localhost:5432 |
| Cache | Redis 7 | localhost:6379 |
| Vector DB | Qdrant | localhost:6333 |
| Task Queue | Celery + Redis | - |
| Frontend (小程序) | uni-app + Vue3 + TypeScript | dist/dev/mp-weixin |
| AI Models | Ollama (qwen3-coder) + Claude API | - |

## Docker Services

```bash
# 主Stack (docker-compose.yml) — 始终运行
bhp_v3_api    # FastAPI 后端 (port 8000) ← 唯一API入口
postgres      # PostgreSQL
redis         # Redis
qdrant        # 向量数据库
celery_worker # 异步任务

# 前端Stack (docker-compose.app.yaml) — 小程序开发时不需要
bhp-h5        # H5前端
admin-portal  # 管理后台
gateway       # API网关
```

## Iron Rules (铁律)

1. **Port 8000 ONLY** — 后端只有一个端口: `localhost:8000`. 永远不要用 8001/8002
2. **Single request.ts** — `src/api/request.ts` 是唯一HTTP模块，不要创建第二份
3. **Environment via config/env.ts** — `src/config/env.ts` 是API地址唯一真相源
4. **src/pages.json is truth** — 编译器读的是 `src/pages.json`，不是根目录的
5. **No BOM** — 所有文件必须是无BOM的UTF-8，PowerShell `Out-File` 会加BOM
6. **No /v1/professional/ paths** — 幽灵路径，源码和编译产物中不应存在
7. **每个Phase完成后 git commit** — 便于回退

## Current Branch Strategy

```
master                          # 主分支
├── backup-2026-0301-before-rollback  # 回滚前完整备份 (含11个BOS美化页面)
└── stabilize-from-sprint1      # 当前工作分支 (锚点: 9a6b18b)
```

## Coach Miniprogram Structure

```
coach-miniprogram/
├── src/
│   ├── api/
│   │   ├── request.ts          # 唯一HTTP模块 (token注入/401刷新/环境切换)
│   │   ├── auth.ts             # 认证API
│   │   ├── coach.ts            # 教练API
│   │   ├── assessment.ts       # 评估API
│   │   ├── companion.ts        # 同伴API
│   │   ├── exam.ts             # 考试API
│   │   ├── journey.ts          # 成长旅程API
│   │   ├── learning.ts         # 学习API
│   │   └── profile.ts          # 个人中心API
│   ├── config/
│   │   └── env.ts              # 环境配置 (DEV/PROD API地址)
│   ├── components/
│   │   ├── BHPCourseCard.vue
│   │   ├── BHPLevelBadge.vue
│   │   ├── BHPPointsCard.vue
│   │   ├── BHPRiskTag.vue
│   │   └── BHPTabBar.vue
│   ├── pages/
│   │   ├── home/               # 首页 (grower/coach双视图)
│   │   ├── auth/               # 登录/注册
│   │   ├── coach/              # 教练子包 (11个页面)
│   │   │   ├── dashboard/index.vue
│   │   │   ├── students/index.vue, detail.vue
│   │   │   ├── flywheel/index.vue
│   │   │   ├── assessment/index.vue, review.vue
│   │   │   ├── analytics/index.vue
│   │   │   ├── push-queue/index.vue
│   │   │   ├── messages/index.vue
│   │   │   ├── risk/index.vue
│   │   │   └── live/index.vue
│   │   ├── learning/           # 学习中心 (11页面)
│   │   ├── exam/               # 认证考试 (5页面)
│   │   ├── journey/            # 成长路径 (4页面)
│   │   ├── assessment/         # 评估 (3页面)
│   │   ├── companions/         # 同伴 (4页面)
│   │   ├── notifications/      # 消息中心
│   │   └── profile/            # 个人中心 + 子包
│   └── pages.json              # ← 编译器读这个！
├── pages.json.bak              # 根目录旧版(已弃用)
├── package.json                # 无BOM UTF-8
├── .env                        # VITE_API_URL (dev)
└── .env.production             # VITE_API_URL (prod)
```

## Backend API Categories (Coach-Related)

| Category | Endpoints | Status |
|----------|-----------|--------|
| coach/dashboard | GET /api/v1/coach/dashboard | LIVE |
| coach/students | GET /api/v1/coach/students | LIVE |
| coach/performance | GET /api/v1/coach/performance | LIVE |
| coach/review-queue | GET /api/v1/coach/review-queue | LIVE |
| coach-push/pending | GET /api/v1/coach-push/pending | LIVE |
| coach/stats/today | GET /api/v1/coach/stats/today | LIVE |
| agent/list | GET /api/v1/agent/list | LIVE |
| journey/state | GET /api/v1/journey/state | LIVE |
| health-data | GET /api/v1/health-data/summary | LIVE |
| micro-actions | GET /api/v1/micro-actions/today | LIVE |
| coach/conversations | GET /api/v1/coach/conversations | 404 |
| coach/live-sessions | GET /api/v1/coach/live-sessions | 404 |
| coach/risk-alerts | GET /api/v1/coach/risk-alerts | 404 |
| coach/analytics | GET /api/v1/coach/analytics/week-trend | 404 |

## Five Business Lines

```
Priority 1: 教练培养体系 (Coach Training) ← 当前焦点
Priority 2: 公众三角色 H5 (Observer/Grower/Sharer)
Priority 3: 专科专家 Agent (Expert AI Tools)
Priority 4: 行业渠道 (B2B Channels)
Priority 5: 青少年视力 (Youth Vision - Independent)
```

## Development Workflow

```bash
# 开发
cd D:\behavioral-health-project\coach-miniprogram
npm run dev:mp-weixin
# → 打开微信开发者工具, 导入 dist\dev\mp-weixin

# 构建
npm run build:mp-weixin

# 后端 (Docker)
cd D:\behavioral-health-project
docker-compose up -d
# API: http://localhost:8000/docs

# 修改pages.json要用node (避免PowerShell编码问题)
node fix-routes.js
```

## Known Gotchas

1. PowerShell `Out-File -Encoding utf8` 会加BOM → 用 `[System.IO.File]::WriteAllText()` 代替
2. PowerShell `ConvertFrom-Json` 无法处理某些UTF-8中文 → 用 node 操作JSON
3. `npm run dev:mp-weixin` 是持续运行的dev server，改pages.json后要Ctrl+C重启
4. Docker `docker-compose.app.yaml` 的前端容器可能与小程序开发冲突 → 小程序开发时停掉
5. 微信开发者工具会锁住dist目录 → 删dist前先关工具

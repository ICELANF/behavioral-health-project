/**
 * 更新本地 CLAUDE.md 和 platform-architecture-overview
 * 用法: node update-docs.js
 */
const fs = require("fs");
const path = require("path");

// ═══════════════════════════════════════════════════════
// 1. CLAUDE.md → D:\behavioral-health-project\CLAUDE.md
// ═══════════════════════════════════════════════════════

const CLAUDE_MD = `# CLAUDE.md — BehaviorOS Platform Context

> Last updated: 2026-03-02
> Anchor: stabilize-from-sprint1 (9a6b18b)
> Current HEAD: 92360a4 (S1-S4 structural risk remediation)

## What Is This Project

BehaviorOS（行健平台）is a behavioral health operating system combining traditional Chinese medicine
principles with modern behavioral science. The platform serves as a foundational OS layer upon
which multiple product surfaces are built.

## Architecture Overview

\`\`\`
BehaviorOS 底座 (FastAPI + PostgreSQL + Redis + Qdrant)
    │  921 API routes │ 21 Agents │ 150+ tables
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
\`\`\`

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

## Docker Services (docker-compose.yml)

\`\`\`
服务名     容器名          端口      状态
app        bhp_v3_api      8000      Always On (唯一API入口)
db         bhp_v3_postgres 5432      Always On
redis      bhp_v3_redis    6379      Always On (无端口映射)
qdrant     bhp_v3_qdrant   6333      Always On
worker     bhp_v3_worker   -         Always On (Celery)
beat       bhp_v3_beat     -         Always On (定时任务)
flower     bhp_v3_flower   5555      Always On (任务监控)
nginx      bhp_v3_nginx    80/443    Always On (反向代理)

docker-compose.app.yaml → 前端Stack (ON-DEMAND ONLY, 默认不启动)
docker-compose.yaml     → Dify Stack (独立AI平台)
\`\`\`

## Iron Rules (铁律)

1. **Port 8000 ONLY** — 后端只有一个端口, 永远不用 8001/8002
2. **Single request.ts** — src/api/request.ts 是唯一HTTP模块
3. **Environment via config/env.ts** — API地址唯一真相源
4. **src/pages.json is truth** — 编译器读 src/pages.json, 不是根目录的
5. **No BOM** — 用 [System.IO.File]::WriteAllText() 或 node 写JSON
6. **No /v1/professional/ paths** — 幽灵路径, 不应存在
7. **JSON edits via Node only** — PowerShell破坏中文编码
8. **Docker: only docker-compose.yml runs by default** — app.yaml按需启动
9. **Git commit after each phase** — 便于回退

## Branch Strategy

\`\`\`
master
├── backup-2026-0301-before-rollback  # 回滚前完整备份 (含BOS美化页面)
└── stabilize-from-sprint1            # 当前工作分支
      ├── 9a6b18b  Sprint 1 完成 (锚点)
      ├── xxxxxx   stable: zero-warn compile
      └── 92360a4  S1-S4 structural risk fix ← HEAD
\`\`\`

## Coach Miniprogram Structure

\`\`\`
coach-miniprogram/
├── src/
│   ├── api/
│   │   ├── request.ts      # 唯一HTTP模块
│   │   ├── auth.ts          # 6 endpoints
│   │   ├── coach.ts         # 9 endpoints
│   │   ├── assessment.ts    # 4 endpoints
│   │   ├── companion.ts     # 6 endpoints
│   │   ├── exam.ts          # 7 endpoints
│   │   ├── journey.ts       # 4 endpoints
│   │   ├── learning.ts      # 7 endpoints
│   │   └── profile.ts       # 7 endpoints (共48前端端点)
│   ├── config/
│   │   └── env.ts           # DEV: localhost:8000 / PROD: api.xingjian.health
│   ├── pages/
│   │   ├── coach/           # 11个页面 (dashboard, students, flywheel, etc.)
│   │   ├── learning/        # 11个页面
│   │   ├── exam/            # 5个页面
│   │   ├── journey/         # 4个页面
│   │   ├── companions/      # 4个页面
│   │   ├── assessment/      # 3个页面
│   │   └── (home, auth, notifications, profile)
│   └── pages.json           # 编译器读这个
├── package.json             # 无BOM UTF-8
└── dist/dev/mp-weixin/      # 编译产物 → 微信开发者工具导入
\`\`\`

## System Monitoring Endpoints (S1-S4)

| Endpoint | Purpose |
|----------|---------|
| GET /api/v1/system/routes | 921路由审计 (注册/失败模块) |
| GET /api/v1/system/health | 数据库+Redis+路由综合健康 |
| GET /api/v1/system/routes/frontend-contract | 前后端42端点契约校验 (97%覆盖) |
| GET /api/v1/system/agents/health | Agent+Ollama+Qdrant运行态检查 |

## Frontend-Backend Contract (42 endpoints)

| Module | Endpoints | Coverage |
|--------|-----------|----------|
| auth.ts | 6 | 5/6 (微信登录待对接) |
| coach.ts | 9 | 9/9 (含stub) |
| assessment.ts | 4 | 4/4 (stub) |
| companion.ts | 6 | 6/6 (stub) |
| exam.ts | 7 | 7/7 (stub) |
| journey.ts | 4 | 4/4 (stub) |
| learning.ts | 7 | 7/7 (stub) |
| profile.ts | 7 | 7/7 (stub) |
| **TOTAL** | **42** | **41/42 (97%)** |

Stub端点返回空数据 + X-Stub:true 响应头, 后端实现后自动替代。

## Five Business Lines

\`\`\`
Priority 1: 教练培养体系 (Coach Training) ← 当前焦点
Priority 2: 公众三角色 H5 (Observer/Grower/Sharer)
Priority 3: 专科专家 Agent (Expert AI Tools)
Priority 4: 行业渠道 (B2B Channels)
Priority 5: 青少年视力 (Youth Vision - Independent)
\`\`\`

## Development Workflow

\`\`\`bash
# 小程序开发
cd D:\\behavioral-health-project\\coach-miniprogram
npm run dev:mp-weixin
# → 微信开发者工具导入 dist\\dev\\mp-weixin

# 后端 (Docker)
cd D:\\behavioral-health-project
docker-compose -f docker-compose.yml restart app   # 服务名是 app

# 修改JSON用node
node fix-routes.js

# 系统监控
curl http://localhost:8000/api/v1/system/routes
curl http://localhost:8000/api/v1/system/health
curl http://localhost:8000/api/v1/system/routes/frontend-contract
curl http://localhost:8000/api/v1/system/agents/health
\`\`\`

## Known Gotchas

1. PowerShell Out-File 加BOM → 用 [System.IO.File]::WriteAllText()
2. PowerShell ConvertFrom-Json 破坏中文 → 用 node 操作JSON
3. npm run dev:mp-weixin 是持续运行的, 改 pages.json 后要 Ctrl+C 重启
4. 微信开发者工具锁住 dist → 删 dist 前先关工具
5. docker-compose.yml 服务名是 app, 不是 bhp_v3_api
6. docker-compose.app.yaml 默认不启动, 会抢占 80/8000 端口
7. 复制命令时不要带 PS D:\\...> 提示符前缀
`;

// ═══════════════════════════════════════════════════════
// 2. platform-architecture-overview → E:\
// ═══════════════════════════════════════════════════════

const OVERVIEW = `# BehaviorOS Platform Architecture Overview
## Version 35.1 | 2026-03-02 | Post-Stabilization

---

## 1. Platform Identity

BehaviorOS (行健平台) is a behavioral health operating system that integrates traditional
Chinese medicine with modern behavioral science to create comprehensive intervention programs.

- **Backend**: 921 API routes, 21 AI agents, 150+ database tables
- **Frontend**: Coach MiniProgram (WeChat), H5 Web App, Admin Portal
- **Infrastructure**: Docker Compose orchestration, PostgreSQL + Redis + Qdrant

---

## 2. System Architecture

\`\`\`
                    ┌──────────────────────────────┐
                    │     微信开发者工具             │
                    │  dist/dev/mp-weixin           │
                    └──────────┬───────────────────┘
                               │ uni.request
                               ▼
                    ┌──────────────────────────────┐
                    │   src/api/request.ts          │
                    │   (唯一HTTP模块)              │
                    │   Token注入 / 401刷新 / Toast  │
                    └──────────┬───────────────────┘
                               │ http://localhost:8000/api
                               ▼
┌──────────────────────────────────────────────────────────┐
│                   bhp_v3_api (FastAPI)                     │
│                                                           │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │auth_api │ │coach_api │ │exam_api  │ │frontend_stubs│ │
│  │6 routes │ │9 routes  │ │7 routes  │ │(S2 兜底)     │ │
│  └─────────┘ └──────────┘ └──────────┘ └──────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐  │
│  │learn_api │ │journey   │ │companion │ │route_audit │  │
│  │7 routes  │ │4 routes  │ │6 routes  │ │(S1 审计)   │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────────┐ │
│  │assess_api│ │profile   │ │agent_health (S4 监控)    │ │
│  │4 routes  │ │7 routes  │ │Ollama/Qdrant/Registry    │ │
│  └──────────┘ └──────────┘ └──────────────────────────┘ │
│                                                           │
│  + 830 more routes (90 API modules)                       │
└───────────┬──────────┬──────────┬────────────────────────┘
            │          │          │
     ┌──────▼──┐  ┌───▼────┐  ┌─▼──────┐
     │PostgreSQL│  │ Redis  │  │ Qdrant │
     │ :5432   │  │ :6379  │  │ :6333  │
     └─────────┘  └────────┘  └────────┘
\`\`\`

---

## 3. Docker Service Matrix

| Compose File | Service | Container | Port | Default |
|-------------|---------|-----------|------|---------|
| docker-compose.yml | app | bhp_v3_api | 8000 | Always On |
| docker-compose.yml | db | bhp_v3_postgres | 5432 | Always On |
| docker-compose.yml | redis | bhp_v3_redis | - | Always On |
| docker-compose.yml | qdrant | bhp_v3_qdrant | 6333 | Always On |
| docker-compose.yml | worker | bhp_v3_worker | - | Always On |
| docker-compose.yml | beat | bhp_v3_beat | - | Always On |
| docker-compose.yml | flower | bhp_v3_flower | 5555 | Always On |
| docker-compose.yml | nginx | bhp_v3_nginx | 80/443 | Always On |
| docker-compose.app.yaml | (8 services) | bhp-gateway etc. | 80,5173-5175,8501 | OFF by default |
| docker-compose.yaml | (Dify stack) | dify-* | 8080 | Separate |

**Rule: Only docker-compose.yml runs by default. App.yaml is on-demand only.**

---

## 4. Frontend Endpoint Contract (42 endpoints, 97% coverage)

### auth.ts (6 endpoints)
| Method | Path | Status |
|--------|------|--------|
| POST | /v1/auth/login | LIVE |
| POST | /v1/auth/register | LIVE |
| POST | /v1/auth/wechat/miniprogram | MISSING |
| GET | /v1/auth/me | LIVE |
| POST | /v1/auth/logout | LIVE |
| POST | /v1/auth/refresh | LIVE |

### coach.ts (9 endpoints)
| Method | Path | Status |
|--------|------|--------|
| GET | /v1/coach/dashboard | LIVE |
| GET | /v1/coach/students | LIVE |
| GET | /v1/coach/students/{id} | LIVE |
| GET | /v1/coach/push-queue | LIVE |
| POST | /v1/coach/push-queue/{id}/approve | LIVE |
| POST | /v1/coach/push-queue/{id}/reject | LIVE |
| GET | /v1/coach/assessments | STUB |
| POST | /v1/coach/assessments/{id}/review | STUB |
| GET | /v1/coach/performance | LIVE |

### assessment.ts (4 endpoints)
| Method | Path | Status |
|--------|------|--------|
| GET | /v1/assessment-assignments/my | STUB |
| GET | /v1/assessment-assignments/{id} | STUB |
| POST | /v1/assessment-assignments/{id}/submit | STUB |
| GET | /v1/assessment-assignments/{id}/result | STUB |

### companion.ts (6 endpoints) — All STUB
### exam.ts (7 endpoints) — All STUB
### journey.ts (4 endpoints) — All STUB
### learning.ts (7 endpoints) — All STUB
### profile.ts (7 endpoints) — All STUB

STUB = Returns empty data with X-Stub:true header. Auto-replaced when real endpoint is implemented.

---

## 5. Coach MiniProgram Pages (43 total)

| SubPackage | Count | Key Pages |
|-----------|-------|-----------|
| coach | 11 | dashboard, students, flywheel, assessment, analytics, push-queue, messages, risk, live |
| learning | 11 | index, catalog, course-detail, video-player, quiz |
| exam | 5 | index, session, result |
| journey | 4 | overview, progress, promotion |
| companions | 4 | index, invite, invitations |
| assessment | 3 | pending, do, result |
| main | 5 | home, login, register, notifications, profile |

---

## 6. AI Agent System (21 agents)

| Category | Agents | LLM |
|----------|--------|-----|
| Core Behavior | BehaviorCoach, MicroActionAgent | Claude API |
| Assessment | AssessmentAgent, ScreeningAgent | Claude API |
| TCM | TCMAgent, ConstitutionAgent | Ollama/Claude |
| Expert Domain | XZBExpertAgent, NutritionAgent | Claude API |
| BehaviorRx | BehaviorRxEngine, HandoffService | Claude API |
| Coaching | CoachAssistant, SupervisorAgent | Claude API |
| Safety | SafetyGuard, EscalationAgent | Claude API |

Monitor: GET /api/v1/system/agents/health

---

## 7. Business Lines

| Priority | Line | Surface | Readiness |
|----------|------|---------|-----------|
| P1 | Coach Training | WeChat MiniProgram | B+ (11 pages, zero-warn) |
| P2 | Public 3-Role | H5 Web App | B (E2E 49/49 green) |
| P3 | Expert Agents | Coach-side tools | B- (Registry active) |
| P4 | Industry Channels | B2B Integration | C (Schema ready) |
| P5 | Youth Vision | Independent module | C- (VisionAgent basic) |

---

## 8. Stabilization Status (2026-03-02)

| Risk | Fix | Verification |
|------|-----|-------------|
| S1: main.py monolith | route_audit.py → /system/routes | 921 routes scanned |
| S2: Contract gap | frontend_stubs.py → 42 stub endpoints | 97% coverage (41/42) |
| S3: Docker port conflict | app.yaml stack stopped | Ports clear |
| S4: Agent no monitoring | agent_health.py → /agents/health | Endpoint active |

---

## 9. Remaining TODO

1. BOS UI pages integration from backup branch (11 coach pages)
2. WeChat DevTools full page QA
3. /auth/wechat/miniprogram API implementation
4. Ollama startup for Agent full health
5. Replace STUB endpoints with real implementations (priority: coach, learning)
6. Production .env.production configuration
7. CI/CD pipeline (GitHub Actions)

---

*Generated: 2026-03-02 | Branch: stabilize-from-sprint1 | HEAD: 92360a4*
`;

// ═══════════════════════════════════════════════════════
// WRITE FILES
// ═══════════════════════════════════════════════════════

const claudePath = "D:\\behavioral-health-project\\CLAUDE.md";
const overviewPath = "E:\\platform-architecture-overview-v35.md";

fs.writeFileSync(claudePath, CLAUDE_MD);
console.log("OK: " + claudePath);

fs.writeFileSync(overviewPath, OVERVIEW);
console.log("OK: " + overviewPath);

console.log("\\nDone. Both files updated.");

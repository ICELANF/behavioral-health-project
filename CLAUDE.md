# CLAUDE.md — BehaviorOS Platform Context

> Last updated: 2026-03-07
> Anchor: stabilize-from-sprint1 (9a6b18b)
> Current HEAD: a994c10 (knowledge base L1 base path fix)

## What Is This Project

BehaviorOS（行健平台）is a behavioral health operating system combining traditional Chinese medicine
principles with modern behavioral science. The platform serves as a foundational OS layer upon
which multiple product surfaces are built.

## Architecture Overview

```
BehaviorOS 底座 (FastAPI + PostgreSQL + Redis + Qdrant)
    │  1001 API routes │ 21 Agents │ 155+ tables │ 8 schemas
    │
    ├── coach-miniprogram (WeChat MiniProgram, uni-app + Vue3)
    │     └── 教练培养体系小程序 (Priority 1)
    │
    ├── h5 (Vant-based H5, 公众三角色 + 员工后台)
    │     ├── Observer/Grower/Sharer 成长路径
    │     └── /staff/* 员工管理后台 (21页, StaffLayout)
    │
    ├── h5-behavior (行为健康测评 H5, Vue3 + Vite)
    │     └── 独立测评应用: 场景→问答→分析→画像→处方
    │
    ├── vision-guard (青少年视力科学使用 H5, Vue3 + Vite)
    │     └── 独立产品线 (Priority 5)
    │
    ├── xzb-workstation (行知宝教练工作台, Vue3)
    │     └── 教练专用桌面工作台
    │
    └── gateway (nginx反代 → API :8000)
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
| Frontend (H5) | Vue3 + Vite + Vant4 | localhost:3002 |
| Frontend (行为H5) | Vue3 + Vite | h5-behavior/ |
| Frontend (视力H5) | Vue3 + Vite | vision-guard/ |
| Frontend (工作台) | Vue3 | xzb-workstation/ |
| AI Models | Ollama (qwen2.5:14b + mxbai-embed-large) + Claude API | localhost:11434 |

## Docker Services (docker-compose.yml)

```
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
```

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
10. **docker compose restart ≠ 重载 env** — 改 .env.bhp 后必须 `--force-recreate`，不能用 `restart`
11. **配置存在 ≠ 代码读取** — 新增 env var 后必须 `grep os.getenv` 确认代码真的用了它
12. **alembic "无输出" ≠ 表已创建** — 迁移后必须 `\dt schema.*` 验证表存在
13. **LLM 路由必须经 UnifiedLLMClient** — 不得绕过 LLM_ROUTE_STRATEGY 直调 Ollama
14. **EMBEDDING_PROVIDER 可切换** — ollama(本地) / dashscope(生产)，EmbeddingService 自动路由
15. **API Key 不进聊天/commit/issue** — 一旦暴露立即轮换

## Branch Strategy

```
master
├── backup-2026-0301-before-rollback  # 回滚前完整备份 (含BOS美化页面)
└── stabilize-from-sprint1            # 当前工作分支
      ├── 9a6b18b  Sprint 1 完成 (锚点)
      ├── 92360a4  S1-S4 structural risk fix
      ├── ...      Sprint 2-4, 多前端, 知识库v4.0
      └── a994c10  L1底座文件路径修复 ← HEAD
```

## Coach Miniprogram Structure

```
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
```

## System Monitoring Endpoints (S1-S4)

| Endpoint | Purpose |
|----------|---------|
| GET /api/v1/system/routes | 1001路由审计 (注册/失败模块) |
| GET /api/v1/system/health | 数据库+Redis+路由综合健康 |
| GET /api/v1/system/routes/frontend-contract | 前后端42端点契约校验 (100%覆盖) |
| GET /api/v1/system/agents/health | Agent+Ollama+Qdrant运行态检查 |

## Frontend-Backend Contract (42 endpoints)

| Module | Endpoints | Coverage |
|--------|-----------|----------|
| auth.ts | 6 | 6/6 (含微信登录dev mode) |
| coach.ts | 9 | 9/9 (含stub) |
| assessment.ts | 4 | 4/4 (stub) |
| companion.ts | 6 | 6/6 (stub) |
| exam.ts | 7 | 7/7 (stub) |
| journey.ts | 4 | 4/4 (stub) |
| learning.ts | 7 | 7/7 (stub) |
| profile.ts | 7 | 7/7 (stub) |
| **TOTAL** | **42** | **42/42 (100%)** |

Stub端点返回空数据 + X-Stub:true 响应头, 后端实现后自动替代。

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
# 小程序开发
cd D:\behavioral-health-project\coach-miniprogram
npm run dev:mp-weixin
# → 微信开发者工具导入 dist\dev\mp-weixin

# 后端 (Docker) — 修改代码后
cd D:\behavioral-health-project
docker-compose -f docker-compose.yml up -d --force-recreate app   # 重建容器

# 修改 .env.bhp 后 — 必须 force-recreate (restart 不重载 env_file!)
docker-compose -f docker-compose.yml up -d --force-recreate app
docker-compose -f docker-compose.yml exec app env | grep <关键字>   # 验证

# 修改JSON用node
node fix-routes.js

# 系统监控
curl http://localhost:8000/api/v1/system/routes
curl http://localhost:8000/api/v1/system/health
curl http://localhost:8000/api/v1/system/routes/frontend-contract
curl http://localhost:8000/api/v1/system/agents/health
```

## Known Gotchas

1. PowerShell Out-File 加BOM → 用 [System.IO.File]::WriteAllText()
2. PowerShell ConvertFrom-Json 破坏中文 → 用 node 操作JSON
3. npm run dev:mp-weixin 是持续运行的, 改 pages.json 后要 Ctrl+C 重启
4. 微信开发者工具锁住 dist → 删 dist 前先关工具
5. docker-compose.yml 服务名是 app, 不是 bhp_v3_api
6. docker-compose.app.yaml 默认不启动, 会抢占 80/8000 端口
7. 复制命令时不要带 PS D:\...> 提示符前缀

## 环境变量管理

```
.env.example          # 提交 Git，仅含 KEY 名称 + 说明
.env.bhp              # 本地开发，含真实本地值 (gitignored)
.env.bhp (服务器)     # 生产值，从 .env.bhp.prod.example 复制修改
```

**新增环境变量三步走**：写入 .env.bhp → 检查 docker-compose.yml 透传 → `--force-recreate` 后 `exec app env` 验证

**LLM/Embedding 路由配置**：
- `LLM_ROUTE_STRATEGY`: cloud_first(生产) / local_first(本地开发)
- `EMBEDDING_PROVIDER`: dashscope(生产) / ollama(本地开发)
- 代码入口: `core/llm_client.py:UnifiedLLMClient`, `core/knowledge/embedding_service.py:EmbeddingService`

## 上线前 Checklist

- [ ] LLM 路由经 UnifiedLLMClient，不直调 Ollama
- [ ] 新迁移在本地 DB 验证通过，`\dt schema.*` 确认表存在
- [ ] .env.bhp.prod.example 更新了新增 KEY
- [ ] docker-compose.yml environment 透传了新 env var
- [ ] 使用 `--force-recreate`（不用 restart）
- [ ] 部署后 health check + alembic current 验证
- [ ] 日志无敏感信息（API Key / 密码）

## 知识库规范

所有KI文件的生成和校验必须遵循 `docs/BHP知识库建设及管理规则_完整版_v4.0.md`
向量维度统一为 **1024维**（mxbai-embed-large:latest / text-embedding-v3），不使用768维。

### 知识库目录结构

```
knowledge/
├── base/                    # L1底座 (ki_id以BASE-开头, scope=global)
│   ├── ttm_stages.md        # TTM 7阶段模型
│   ├── bpt6_dimensions.md   # BPT-6行为画像
│   ├── bfr_framework.md     # BFR框架
│   ├── crisis_protocol.md   # 危机协议
│   ├── three_layer_value.md # 三层价值架构
│   ├── six_layer_model.md   # 六层模型
│   ├── m_action_principles.md # M行动原则
│   └── metabolic_redlines.md  # 代谢红线
├── kb_clinical/             # L2临床领域 (diabetes, CGM, lifestyle)
├── kb_tcm/                  # L2中医领域 (constitution, neijing)
├── kb_theory/               # L2理论框架
│   ├── behavioral/          # 行为改变理论 (BCT, Fogg, BCW, addiction)
│   ├── psychology/          # 心理学 (personality, biopsych, emotion)
│   └── growth/              # 成长超越 (PERMA, ACT, Frankl, Possible Selves)
├── kb_dietary_intervention/ # L2饮食干预
├── kb_ops/                  # L2运营知识
├── kb_products/             # L2产品知识
├── kb_case_studies/         # L2案例库
└── vector_chunks/           # 预分块文件 (供embed脚本使用)
```

### 8角色层级体系

```
observer(L0) → grower(L1) → sharer(L2) → coach(L3)
→ promoter/supervisor(L4) → master(L5) → admin(L99)
```

### 向量库状态 (Qdrant)

- Collection: `bhp_knowledge`, 1024维, Cosine距离
- 当前向量数: ~1441 points
- RAG: top_k=5, score_threshold=0.35, max_context=3000 chars

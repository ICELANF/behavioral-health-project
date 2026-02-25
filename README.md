# 行健平台 V5.3.0 — 生态架构升级实施包

> Migration HEAD: **054** | 生成日期: 2026-02-25 | 基础文档: 平台教练体系全景-20260225.md

---

## 包结构

```
.
├── alembic/versions/
│   └── 054_expert_institution_partner.py   ← 数据库迁移（幂等）
├── api/
│   ├── expert_api.py                       ← Expert 18个端点
│   └── institution_partner_api.py          ← 机构/合伙人 12个端点
├── core/
│   └── xzb_service.py                      ← 行诊智伴知识引擎
├── frontend/
│   ├── h5/
│   │   ├── homepages/
│   │   │   ├── HomeRouter.vue              ← 角色首页分流路由（替换 home/index.vue）
│   │   │   ├── ObserverHome.vue            ← Observer 首页
│   │   │   └── GrowerHome.vue              ← Grower 首页
│   │   └── coach-recruit/
│   │       ├── CoachRecruit.vue            ← 教练队伍建设页（5 Tab，对齐体系全景文档）
│   │       └── router-patch.ts             ← 路由注册片段
│   └── admin/coach-portal/
│       └── CoachDashboard.vue              ← 教练工作台首页
├── design/
│   └── bhp-design-system.jsx               ← 5套封面+3套首页主题+教练建设（React预览）
├── tests/
│   └── test_expert_coach_api.py            ← 集成测试（18用例）
└── docs/
    └── CLAUDE_CODE_GUIDE.md                ← Claude Code 完整部署指南

```

---

## 快速部署（4步，约60分钟）

### Step 0 — 数据库迁移（5分钟）
```bash
cp alembic/versions/054_expert_institution_partner.py  <project>/alembic/versions/
alembic upgrade head
# 验证：6张新表 + INSTITUTION_ADMIN enum + expert_slug唯一索引
```

### Step 1 — 后端注册（15分钟）
```bash
cp api/expert_api.py               <project>/api/
cp api/institution_partner_api.py  <project>/api/
cp core/xzb_service.py             <project>/core/

# 在 main.py 添加：
# from api.expert_api import router as expert_router
# from api.institution_partner_api import institution_router, partner_router
# app.include_router(expert_router)
# app.include_router(institution_router)
# app.include_router(partner_router)

docker compose build --no-cache bhp-api
```

### Step 2 — 前端接入（30分钟）
```bash
# H5 角色首页
cp frontend/h5/homepages/HomeRouter.vue   <h5>/src/views/home/index.vue
cp frontend/h5/homepages/ObserverHome.vue <h5>/src/views/home/
cp frontend/h5/homepages/GrowerHome.vue   <h5>/src/views/home/

# 教练招募页
cp -r frontend/h5/coach-recruit/  <h5>/src/views/
# 将 router-patch.ts 中的路由条目添加到 h5/src/router/index.ts

# 教练工作台
cp frontend/admin/coach-portal/CoachDashboard.vue \
   <admin-portal>/src/views/coach-portal/main.vue

docker compose build --no-cache bhp-h5 bhp-admin-portal
```

### Step 3 — 验证（10分钟）
```bash
pytest tests/test_expert_coach_api.py -v
# 期望：18/18 通过

# 铁律验证（必须）：
curl -X POST http://localhost:8000/api/v1/expert/tasks/force-push \
  -H "Authorization: Bearer <expert_token>"
# 期望：HTTP 403，含"铁律 I-06"
```

---

## 铁律清单（不可绕过）

| # | 铁律 | 代码位置 |
|---|------|---------|
| I-01 | AI→教练审核→推送，AI不直接触达用户 | `CoachPushQueue` status 流转 |
| I-02 | CrisisAgent 优先级0，不可关闭 | `core/agents/router.py` |
| I-03 | XZBRxFragment.requires_coach_review 始终 True | `core/xzb_service.py` |
| I-04 | 推送 72h 超时自动 expired | `expire_stale_items` 定时任务 |
| I-05 | 教练只管辖 _STUDENT_ROLES（L0/L1/L2） | `api/coach_api.py` |
| I-06 | Expert 不能直接推送任务给学员 | `POST /expert/tasks/force-push → 403` |

---

## 新增端点速查

| 模块 | 数量 | 前缀 |
|------|------|------|
| Expert | 18 | `/api/v1/expert/` |
| Institution | 6 | `/api/v1/institutions/` |
| Partner | 6 | `/api/v1/partners/` |
| **合计** | **30** | — |

---

> 完整部署说明见 `docs/CLAUDE_CODE_GUIDE.md`

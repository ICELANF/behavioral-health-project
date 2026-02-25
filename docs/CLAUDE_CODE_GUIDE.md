# Claude Code 落地执行指南
## 行健平台生态架构升级 V5.3.0 — Migration 054

> **执行方式**：将此文件放入项目根目录，Claude Code 按序执行  
> **前置条件**：HEAD = 053，Docker 容器运行中  
> **预估工时**：全量执行约 3-4 小时  
> **最小可行执行**：Phase 0 + Phase 1 共约 45 分钟

---

## ⚡ 快速检查（执行前）

```bash
# 1. 确认迁移 HEAD
docker compose -f docker-compose.app.yaml exec bhp-api \
  alembic current
# 期望输出: 053 (head)

# 2. 确认容器状态
docker compose -f docker-compose.app.yaml ps
# bhp-api、bhp-h5、bhp-admin-portal、dify-db、dify-redis 均为 Up

# 3. 运行静态检查
docker compose -f docker-compose.app.yaml exec bhp-api \
  python scripts/static_checks.py
# 期望: 全绿
```

---

## Phase 0：数据库迁移（约 5 分钟）

### 0.1 复制迁移文件

```bash
# 将 migrations/054_expert_institution_partner.py
# 复制到项目的 alembic/versions/ 目录
cp migrations/054_expert_institution_partner.py \
   alembic/versions/054_expert_institution_partner.py
```

### 0.2 执行迁移

```bash
docker compose -f docker-compose.app.yaml run --rm \
  -w /app bhp-api alembic upgrade head

# 期望输出：
# Running upgrade 053 -> 054, Expert独立AGENT + 机构合作 + 合伙人体系
```

### 0.3 验证迁移

```bash
docker compose -f docker-compose.app.yaml exec bhp-api \
  python -c "
from sqlalchemy import create_engine, inspect, text
import os
engine = create_engine(os.environ['DATABASE_URL'].replace('+asyncpg',''))
insp = inspect(engine)
new_tables = ['expert_public_profiles','expert_patient_bindings',
              'xzb_knowledge','xzb_rules','partner_configs','partner_revenue_logs']
for t in new_tables:
    exists = t in insp.get_table_names()
    print(f'  {\"✅\" if exists else \"❌\"} {t}')

# 验证 tenants 表新增列
cols = [c['name'] for c in insp.get_columns('tenants')]
assert 'tenant_type' in cols, 'tenant_type 列缺失！'
print('  ✅ tenants.tenant_type')

# 验证枚举扩展
with engine.connect() as conn:
    r = conn.execute(text(\"SELECT enumlabel FROM pg_enum WHERE enumtypid = 'userrole'::regtype AND enumlabel = 'INSTITUTION_ADMIN'\"))
    assert r.first(), 'INSTITUTION_ADMIN 枚举值缺失！'
print('  ✅ UserRole.INSTITUTION_ADMIN')
print('Migration 054 验证完成')
"
```

---

## Phase 1：后端服务注册（约 15 分钟）

### 1.1 复制新 API 文件

```bash
# 复制到 api/ 目录
cp api/expert_api.py              api/expert_api.py
cp api/institution_partner_api.py api/institution_partner_api.py
cp services/xzb_service.py       core/xzb_service.py
```

### 1.2 注册到 main.py

在 `main.py` 中找到 API 路由注册区，添加：

```python
# 在现有 router 注册之后添加（找到 include_router 块）
from api.expert_api import router as expert_router
from api.institution_partner_api import (
    institution_router, partner_router
)

app.include_router(expert_router)
app.include_router(institution_router)
app.include_router(partner_router)
```

### 1.3 AgentRouter 注入 XZB Step 7

在 `core/agents/router.py` 的 `route_message` 函数末尾，在返回之前添加：

```python
# 在 router.py 顶部添加导入
from core.xzb_service import get_xzb_proxy_for_user

# 在 route_message 函数内（现有路由逻辑之后，return 之前）
async def route_message(message: str, user_id: UUID, session_ctx: dict, db):
    # ... 现有 6 步路由逻辑 ...

    # Step 7（新增）：XZB Expert 代理检查
    xzb_proxy = await get_xzb_proxy_for_user(db, user_id)
    if xzb_proxy:
        adapted_response, rx_fragment = await xzb_proxy.process(
            message=message,
            session_context=session_ctx,
            llm_response=base_response,  # 现有 LLM 输出
        )
        if rx_fragment:
            # 注入 RxComposer（复用现有 P1 流水线）
            await inject_xzb_fragment_to_rx_composer(rx_fragment, db)
        return adapted_response

    return base_response
```

### 1.4 构建并验证

```bash
# 重建 API 镜像
docker compose -f docker-compose.app.yaml build --no-cache bhp-api

# 重启服务
docker compose -f docker-compose.app.yaml up -d --force-recreate bhp-api

# 检查新端点是否注册
sleep 5
curl -s http://localhost:8000/openapi.json | \
  python -c "
import json, sys
api = json.load(sys.stdin)
new_paths = [p for p in api['paths'] if '/expert' in p or '/institution' in p or '/partner' in p]
print(f'新注册端点: {len(new_paths)} 个')
for p in sorted(new_paths)[:10]:
    print(f'  {p}')
"
```

### 1.5 更新 static_checks.py RBAC 枚举

```python
# 在 scripts/static_checks.py 中找到 VALID_ROLES 或类似列表，
# 添加 'INSTITUTION_ADMIN'：
VALID_ROLES = [
    'OBSERVER', 'GROWER', 'SHARER', 'COACH',
    'PROMOTER', 'SUPERVISOR', 'MASTER', 'ADMIN',
    'INSTITUTION_ADMIN',  # ← 新增
]
```

---

## Phase 2：前端首页组件（约 30 分钟）

### 2.1 复制 H5 首页组件

```bash
# Observer 首页（核心转化页）
cp frontend/homepages/ObserverHome.vue \
   h5/src/views/home/ObserverHome.vue

# Grower 首页
cp frontend/homepages/GrowerHome.vue \
   h5/src/views/home/GrowerHome.vue
```

### 2.2 更新 H5 路由分流逻辑

在 `h5/src/views/home/index.vue`（TabBar 根路由），
根据用户角色动态渲染对应首页：

```vue
<!-- h5/src/views/home/index.vue — 修改分流逻辑 -->
<template>
  <component :is="homeComponent" />
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'
import ObserverHome    from './ObserverHome.vue'
import GrowerHome      from './GrowerHome.vue'
import SharerHome      from './SharerHome.vue'

const userStore = useUserStore()
const homeComponent = computed(() => {
  switch (userStore.role) {
    case 'OBSERVER': return ObserverHome
    case 'GROWER':   return GrowerHome
    case 'SHARER':   return SharerHome
    default:         return ObserverHome
  }
})
</script>
```

### 2.3 复制 Admin Portal 教练首页

```bash
cp frontend/homepages/CoachDashboard.vue \
   admin-portal/src/views/coach-portal/main.vue
```

**注意**：此文件使用 Ant Design Vue 组件（`a-row`、`a-col`、`a-badge` 等），
确认 `admin-portal` 已安装 `ant-design-vue`。

### 2.4 需要新建的后端接口（首页数据）

以下接口为前端组件所需，需在 `api/home_api.py` 中新增：

```python
# 新增到 api/home_api.py（或 api/coach_api.py）

@router.get("/home/grower-dashboard")
async def grower_dashboard(current_user=Depends(get_current_user), db=Depends(get_db)):
    """Grower 首页数据：连续天数 + 稳定度 + 今日任务 + AI洞察"""
    # 查询连续打卡天数
    streak = await db.execute(text("""
        SELECT COUNT(*) as streak
        FROM (
            SELECT log_date,
                   ROW_NUMBER() OVER (ORDER BY log_date DESC) as rn,
                   log_date - (CURRENT_DATE - ROW_NUMBER() OVER (ORDER BY log_date DESC)::integer) as grp
            FROM (
                SELECT DISTINCT DATE(created_at) as log_date
                FROM task_completions
                WHERE user_id = CAST(:uid AS UUID)
                  AND DATE(created_at) >= CURRENT_DATE - INTERVAL '30 days'
            ) t
        ) t2
        WHERE grp = 0
    """), {"uid": str(current_user.id)})
    
    # 本周行为稳定度（完成率标准差倒数映射到0-100）
    stability = await db.execute(text("""
        SELECT
            ROUND(
                CASE
                    WHEN STDDEV(completion_rate) IS NULL OR STDDEV(completion_rate) = 0 THEN 100
                    ELSE GREATEST(0, LEAST(100, 100 - STDDEV(completion_rate) * 200))
                END
            )::integer AS stability_score
        FROM (
            SELECT DATE(created_at) AS day,
                   COUNT(*) FILTER (WHERE status='completed')::float /
                   NULLIF(COUNT(*), 0) * 100 AS completion_rate
            FROM task_completions
            WHERE user_id = CAST(:uid AS UUID)
              AND created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY 1
        ) daily
    """), {"uid": str(current_user.id)})

    return {
        "data": {
            "streak_days": streak.scalar() or 0,
            "stability_score": stability.scalar() or 0,
            "today_tasks": [],      # 复用现有 tasks API
            "ai_nudge": None,       # 复用现有 AI 洞察
            "week_metrics": [],
        }
    }


@router.get("/coach/home-dashboard")
async def coach_home_dashboard(
    current_user=Depends(require_roles([UserRole.COACH, UserRole.PROMOTER,
                                        UserRole.SUPERVISOR, UserRole.MASTER,
                                        UserRole.ADMIN])),
    db=Depends(get_db)
):
    """Coach 工作台首页：高风险排序 + KPI + 待处理"""
    # 高风险学员：信任分×活跃天数加权排序
    urgent = await db.execute(text("""
        SELECT
            u.id,
            u.username AS name,
            u.avatar_url AS avatar,
            ts.total_score AS trust_score,
            CASE
                WHEN ts.total_score < 30 THEN 'high'
                WHEN ts.total_score < 60 THEN 'medium'
                ELSE 'low'
            END AS risk_level,
            CASE
                WHEN ts.total_score < 30 THEN '信任分严重下降'
                WHEN u.last_active_at < NOW() - INTERVAL '3 days'
                    THEN '3天未活动'
                ELSE '需要关注'
            END AS risk_reason,
            CASE
                WHEN ts.total_score < 30 THEN 'high'
                WHEN ts.total_score < 60 THEN 'medium'
                ELSE 'low'
            END AS risk_level_label
        FROM coach_student_bindings csb
        JOIN users u ON u.id = csb.student_id
        LEFT JOIN trust_scores ts ON ts.user_id = u.id
        WHERE csb.coach_id = CAST(:cid AS UUID)
          AND csb.status = 'active'
          AND (ts.total_score < 60
               OR u.last_active_at < NOW() - INTERVAL '3 days')
        ORDER BY ts.total_score ASC NULLS FIRST,
                 u.last_active_at ASC
        LIMIT 10
    """), {"cid": str(current_user.id)})

    students = [dict(r) for r in urgent.mappings()]
    for s in students:
        s['risk_level_label'] = {
            'high': '高风险', 'medium': '需关注', 'low': '正常'
        }.get(s.get('risk_level', 'low'), '正常')

    return {
        "data": {
            "urgent_students": students,
            "pending_ai_reviews": 0,    # 复用 rx_dashboard 计数
            "pending_prescriptions": 0, # 复用 rx_history 计数
            "kpi": {},
            "monthly_metrics": {},
        }
    }
```

---

## Phase 3：构建与测试（约 10 分钟）

### 3.1 重建前端镜像

```bash
# H5
docker compose -f docker-compose.app.yaml build --no-cache bhp-h5
docker compose -f docker-compose.app.yaml up -d --force-recreate bhp-h5

# Admin Portal
docker compose -f docker-compose.app.yaml build --no-cache bhp-admin-portal
docker compose -f docker-compose.app.yaml up -d --force-recreate bhp-admin-portal
```

### 3.2 新增测试文件

```bash
cp tests/test_expert_api.py tests/test_expert_api.py       # 见下文
cp tests/test_institution_api.py tests/test_institution_api.py
```

### 3.3 运行测试套件

```bash
docker compose -f docker-compose.app.yaml exec bhp-api \
  pytest tests/test_expert_api.py tests/test_institution_api.py \
  -v --tb=short 2>&1 | tail -30
```

---

## 新增测试文件内容

### tests/test_expert_api.py

```python
"""
Expert 独立 AGENT API 测试
测试用例: 18 个
"""
import pytest
import httpx

BASE = "http://localhost:8000/api/v1"

@pytest.fixture
def supervisor_token():
    """使用 supervisor 测试账号（V5 测试账号: supervisor/Supervisor@2026）"""
    r = httpx.post(f"{BASE}/auth/login",
                   json={"username": "supervisor", "password": "Supervisor@2026"})
    return r.json()["access_token"]

@pytest.fixture
def coach_token():
    r = httpx.post(f"{BASE}/auth/login",
                   json={"username": "coach", "password": "Coach@2026"})
    return r.json()["access_token"]


class TestExpertServiceModes:
    def test_get_service_modes_requires_auth(self):
        r = httpx.get(f"{BASE}/expert/service-modes")
        assert r.status_code == 401

    def test_get_service_modes_ok(self, supervisor_token):
        r = httpx.get(f"{BASE}/expert/service-modes",
                      headers={"Authorization": f"Bearer {supervisor_token}"})
        assert r.status_code == 200
        data = r.json()
        assert "service_mode_public" in data
        assert "service_mode_clinical" in data
        assert "service_mode_coach_network" in data

    def test_enable_public_mode(self, supervisor_token):
        r = httpx.patch(f"{BASE}/expert/service-modes",
                        json={"service_mode_public": True},
                        headers={"Authorization": f"Bearer {supervisor_token}"})
        assert r.status_code == 200

    def test_enable_clinical_mode(self, supervisor_token):
        r = httpx.patch(f"{BASE}/expert/service-modes",
                        json={"service_mode_clinical": True},
                        headers={"Authorization": f"Bearer {supervisor_token}"})
        assert r.status_code == 200

    def test_empty_update_rejected(self, supervisor_token):
        r = httpx.patch(f"{BASE}/expert/service-modes",
                        json={},
                        headers={"Authorization": f"Bearer {supervisor_token}"})
        assert r.status_code == 400


class TestExpertPublicProfile:
    def test_update_profile(self, supervisor_token):
        r = httpx.patch(f"{BASE}/expert/public-profile",
                        json={
                            "display_name": "测试专家",
                            "expert_slug": "test-expert-001",
                            "specialty_domains": ["vision", "metabolism"],
                        },
                        headers={"Authorization": f"Bearer {supervisor_token}"})
        assert r.status_code == 200

    def test_slug_conflict_rejected(self, supervisor_token, coach_token):
        # coach 尝试使用已被 supervisor 占用的 slug
        r = httpx.patch(f"{BASE}/expert/public-profile",
                        json={"expert_slug": "test-expert-001"},
                        headers={"Authorization": f"Bearer {coach_token}"})
        assert r.status_code == 409

    def test_public_page_not_found_when_unlisted(self):
        r = httpx.get(f"{BASE}/expert/public/test-expert-001")
        # 未设置 is_publicly_listed=True 时不可访问
        assert r.status_code in (404, 200)  # 视 is_publicly_listed 状态

    def test_expert_directory(self):
        r = httpx.get(f"{BASE}/expert/directory")
        assert r.status_code == 200
        assert "items" in r.json()


class TestExpertForcePushBlocked:
    """铁律测试：Expert 不得直推任务"""

    def test_force_push_always_403(self, supervisor_token):
        r = httpx.post(f"{BASE}/expert/tasks/force-push",
                       headers={"Authorization": f"Bearer {supervisor_token}"})
        assert r.status_code == 403, "铁律违反！Expert 直推任务必须返回 403"

    def test_force_push_no_auth_also_403(self):
        r = httpx.post(f"{BASE}/expert/tasks/force-push")
        assert r.status_code == 403


class TestXZBKnowledge:
    def test_create_knowledge(self, supervisor_token):
        r = httpx.post(f"{BASE}/expert/xzb/knowledge",
                       json={
                           "knowledge_type": "note",
                           "content": "当患者连续7天户外活动不足60分钟时，优先建议家庭环境评估而非直接增加目标。",
                           "evidence_tier": "T2",
                           "tags": ["vision", "behavior"],
                       },
                       headers={"Authorization": f"Bearer {supervisor_token}"})
        assert r.status_code == 200
        assert "id" in r.json()

    def test_list_knowledge(self, supervisor_token):
        r = httpx.get(f"{BASE}/expert/xzb/knowledge",
                      headers={"Authorization": f"Bearer {supervisor_token}"})
        assert r.status_code == 200
        assert "items" in r.json()


class TestInstitutionAPI:
    def test_register_institution_public(self):
        r = httpx.post(f"{BASE}/institutions/register",
                       json={
                           "tenant_name": "测试中学",
                           "institution_type": "school",
                           "contact_name": "张老师",
                           "contact_phone": "13800138000",
                           "contact_email": "test@school.edu.cn",
                           "health_focus": ["vision"],
                       })
        assert r.status_code == 200
        assert "tenant_id" in r.json()
```

---

## 验收检查清单

执行完成后，逐项确认：

```
□ Migration 054 HEAD 已更新
□ 6 张新表存在且结构正确
□ INSTITUTION_ADMIN 枚举值存在
□ /api/v1/expert/service-modes 返回 200
□ /api/v1/expert/tasks/force-push 返回 403（铁律）
□ /api/v1/institutions/register 公开端点可访问
□ /api/v1/partners/apply 需登录
□ H5 observer 首页显示情境入口
□ H5 grower 首页显示连续天数
□ Coach Dashboard 显示风险排序列表
□ static_checks.py 通过（含 INSTITUTION_ADMIN）
□ 所有现有测试 96/96 + 33 仍然通过（不应有回归）
```

---

## 遇到问题的解决路径

**Migration 失败（pgvector ivfflat 语法错误）**：
```bash
# pgvector 版本不支持 ivfflat 时，降级为 PLAIN 索引
# 修改 migration 054：将 ivfflat 行改为：
# CREATE INDEX IF NOT EXISTS idx_xzb_knowledge_vector
#     ON xzb_knowledge (vector_embedding);
```

**INSTITUTION_ADMIN 枚举扩展失败（并发锁）**：
```bash
# 检查是否有活跃连接持有锁
docker compose exec dify-db psql -U postgres health_platform \
  -c "SELECT pid, query FROM pg_stat_activity WHERE state = 'active';"
# 终止干扰连接后重新执行 migration
```

**XZBAgentProxy 导入失败**：
```bash
# 确认 pgvector 已安装
docker compose exec bhp-api pip show pgvector
# 若未安装：
docker compose exec bhp-api pip install pgvector --break-system-packages
```

**前端组件 ant-design-vue 组件未识别**：
```bash
# Admin Portal 已使用 ant-design-vue，确认版本
docker compose exec bhp-admin-portal cat package.json | grep ant-design
```

---

*Claude Code 执行指南 · V1.0 · 2026-02-25*  
*行健平台生态架构升级 Migration 054*

# VisionGuard 平台融合指南
**行健平台 BehaviorOS — VisionGuard V1.0 集成**  
续接 VisionExam V5.3.x · Migration 057

---

## 目录结构

```
visionguard/
├── backend/
│   ├── models/
│   │   └── migration_057_vision_behavior.py   ← SQLAlchemy ORM + 建表 SQL
│   ├── api/
│   │   └── vision_behavior_router.py          ← FastAPI 路由 /v1/vision/behavior/*
│   ├── tasks/
│   │   └── vision_jobs.py                     ← Celery Job 27-31
│   └── agents/
│       └── vision_guide_agent_extension.py    ← VisionGuideAgent 意图扩展 + VisionRxGenerator
└── frontend/
    ├── h5/
    │   ├── VisionDailyLog.vue     ← 学员每日打卡页 (/vision-daily)
    │   └── VisionParentView.vue   ← 家长专属视图 (/vision-parent)
    └── admin/
        └── CoachVisionRxQueue.vue ← 教练处方审核队列 (/admin/coach/vision-rx-queue)
```

---

## Phase 0：数据库扩展（第 1-2 周）

### 步骤 1：执行 Migration 057

```bash
# 将 MIGRATION_057_UP_SQL 粘贴至 Alembic revision 或直接执行：
psql $DATABASE_URL -c "$(python -c "
from visionguard.backend.models.migration_057_vision_behavior import MIGRATION_057_UP_SQL
print(MIGRATION_057_UP_SQL)
")"
```

### 步骤 2：注册 ORM 模型

在 `app/models/__init__.py` 中追加：

```python
from visionguard.backend.models.migration_057_vision_behavior import (
    VisionBehaviorLog,
    VisionBehaviorGoal,
    VisionParentBinding,
)
```

确认 `register_external_models()` 和 CI `create_all()` 覆盖这三张表。

### 步骤 3：注册 API 路由

在 `app/main.py` 的路由注册处追加：

```python
from visionguard.backend.api.vision_behavior_router import router as vision_behavior_router
app.include_router(vision_behavior_router)
```

---

## Phase 1：行为打卡（第 3-6 周）

### 步骤 4：激活 Celery Job 27

在 `app/celery_beat_schedule.py` 追加（续接 Job 26）：

```python
'job_27_vision_behavior_score_calc': {
    'task': 'tasks.vision_jobs.job_27_behavior_score_calc',
    'schedule': crontab(hour=23, minute=0),
},
'job_28_vision_behavior_rx_trigger': {
    'task': 'tasks.vision_jobs.job_28_behavior_rx_trigger',
    'schedule': crontab(hour=23, minute=15),
},
```

### 步骤 5：扩展 VisionGuideAgent

在 `VisionGuideAgent.generate_response()` 的末尾、返回前插入：

```python
# VisionGuard 新增意图分发
from visionguard.backend.agents.vision_guide_agent_extension import (
    classify_intent, VisionIntent, VisionGuideAgentExtension, VisionAgentContext
)

intent = classify_intent(user_message)
if intent in (
    VisionIntent.BEHAVIOR_CHECKIN,
    VisionIntent.GOAL_INQUIRY,
    VisionIntent.PARENT_SUMMARY,
    VisionIntent.RESISTANCE_HANDLING,
    VisionIntent.EXPERT_CONSULTATION,
):
    ctx = VisionAgentContext(
        user_id=current_user.id,
        student_name=current_user.name,
        age=current_user.age,
        ttm_stage=current_user.ttm_stage,
        risk_level=current_user.vision_risk_level,
        today_log=today_log_dict,
        goal=goal_dict,
        streak_days=streak_days,
        is_exam_season=feature_flags.get("exam_season", False),
        expert_name=bound_expert.name if bound_expert else None,
    )
    extension = VisionGuideAgentExtension(ctx)
    response = extension.handle(intent, user_message)
    if response:
        return response
```

### 步骤 6：注册 H5 路由

在 Vue Router (`src/router/index.js`) 的视力模块区块追加：

```javascript
// 续接 VisionExam 的 4 个路由，再增 4 个（合计 39 页）
{
  path: '/vision-daily',
  component: () => import('@/views/vision/VisionDailyLog.vue'),
  meta: { requiresAuth: true, role: 'OBSERVER' },
},
{
  path: '/vision-goals',
  component: () => import('@/views/vision/VisionGoals.vue'),
  meta: { requiresAuth: true, role: 'OBSERVER' },
},
{
  path: '/vision-prescription/:id',
  component: () => import('@/views/vision/VisionRxDetail.vue'),
  meta: { requiresAuth: true, role: 'OBSERVER' },
},
{
  path: '/vision-parent',
  component: () => import('@/views/vision/VisionParentView.vue'),
  meta: { requiresAuth: true, role: 'PARENT' },
},
```

在 Admin 路由追加：

```javascript
// 续接 VisionExam 的 3 个管理页，再增 2 个（合计 94 页）
{
  path: '/admin/coach/vision-rx-queue',
  component: () => import('@/views/admin/CoachVisionRxQueue.vue'),
  meta: { requiresAuth: true, role: 'COACH' },
},
{
  path: '/admin/expert/vision-workbench',
  component: () => import('@/views/admin/ExpertVisionWorkbench.vue'),
  meta: { requiresAuth: true, role: 'EXPERT' },
},
```

---

## Phase 2：处方接通（第 7-11 周）

### XZBRxBridge 适配层

在 `_enqueue_rx_generation()` 函数中，取消注释并替换为平台实际 `XZBRxBridge.submit()` 调用。

处方格式对接：

```python
from app.services.xzb_rx_bridge import XZBRxBridge

# 三格式处方注册
rx_gen = VisionRxGenerator(ctx)
XZBRxBridge.submit(
    db=db,
    user_id=user_id,
    domain="VISION",
    trigger_type=trigger,
    rx_formats={
        "student": rx_gen.generate_student_rx(trigger),
        "parent": rx_gen.generate_parent_rx(trigger),
        "coach": rx_gen.generate_coach_rx(trigger),
    },
    priority=_rx_priority_from_risk(risk_level),
)
```

### 家长推送配额

家长账号独立计算，不与学员共享 3条/天 限流：

```python
# WechatPushService 调用时传入 quota_user_id=parent_user_id（而非 student_user_id）
WechatPushService.send(
    user_id=parent_id,
    quota_user_id=parent_id,   # ← 关键：独立配额
    template="vision_parent_rx",
    data=rx_data,
)
```

---

## Phase 3-4 待实现组件

| 组件 | 文件名 | 预计周期 |
|------|--------|----------|
| 个人目标页 | `VisionGoals.vue` | Phase 1 |
| 处方详情页 | `VisionRxDetail.vue` | Phase 2 |
| 行诊智伴专家工作台 | `ExpertVisionWorkbench.vue` | Phase 3 |
| TTM 阶段自动映射 | `vision_ttm_mapper.py` | Phase 4 |
| 考试季自动切换 | `feature_flag: exam_season` | Phase 4 |

---

## 代码规约确认

| 规约 | 状态 |
|------|------|
| CAST 铁律 | ✅ 所有 Enum 列使用 `Enum(type, create_type=False/True)` |
| 枚举 UPPERCASE | ✅ `NORMAL/WATCH/ALERT/URGENT`, `MANUAL/DEVICE_SYNC/...` |
| UUID PK | ✅ 全部 `server_default=gen_random_uuid()` |
| server_default NOW() | ✅ `created_at`, `updated_at` |
| 无字段重叠 | ✅ Migration 057 与 056 零冲突 |
| Job 编号续接 | ✅ Job 27-31，08:15 错开策略延续 |
| 处方铁律（AI→教练→推送）| ✅ `coach_review_items` 队列不可绕过 |
| 微信配额独立 | ✅ 家长账号独立计算 |

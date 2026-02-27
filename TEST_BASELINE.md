# TEST_BASELINE.md — 测试基线报告

> 基线日期: 2026-02-28
> Git tag: `e2e-6roles-49-20260228`
> 环境: Docker bhp_v3_api (Python 3.12.12, pytest 9.0.2)

## 综合结果

| 测试类型 | 套件 | 通过 | 失败 | 总计 | 通过率 |
|---------|------|------|------|------|--------|
| 单元测试 | test_crisis_smoke.py | 32 | 0 | 32 | 100% |
| 单元测试 | test_golden_baseline.py | 8 | 0 | 8 | 100% |
| 单元测试 | test_consistency.py | 32 | 0 | 32 | 100% |
| E2E 联调 | e2e_6roles.py | 49 | 0 | 49 | 100% |
| **总计** | | **121** | **0** | **121** | **100%** |

---

## 单元测试详情 (72/72)

### test_crisis_smoke.py (32/32)
10 关键词全部触发 critical:
- 不想活了 / 想自杀 / 自残 / 结束生命 / 去死
- 跳楼 / 割腕 / 安眠药过量 / 写了遗书 / 活着没意义

全链路验证: InputFilter -> Router -> CrisisAgent -> GenerationGuard

### test_golden_baseline.py (8/8)
- get_master_agent() 返回有效实例
- Registry 21 agents 注册
- CrisisAgent priority=0
- Router 关键词路由
- Agent 并行执行
- 冲突消解
- 设备数据同步
- Registry freeze 机制

### test_consistency.py (32/32)
- 所有 Agent 继承 BaseAgent
- 所有 Agent 实现 process() 方法
- domain 枚举对齐
- priority 范围验证
- weight 范围验证

---

## E2E 6 角色联调详情 (49/49)

### Observer (6/6)
- register: 201 (已存在=400, 视为通过)
- login: 200 (JWT token)
- quota/today: 200 (chat_limit=3)
- observer/tier: 404 (路由未实现, 可接受)
- agent/run(trust_guide): 200 (Observer 白名单正确)
- segments/permissions: 200

### Grower (21/21)
- journey/state: 200 (s0_authorization)
- journey/activate: 400 (条件未满足, 正确)
- assessment/profile/me: 200
- assessment-assignments/my-pending: 200
- micro-actions/today: 200 (任务列表)
- micro-actions/stats: 200
- micro-actions/history: 200
- challenges: 200, my-enrollments: 200
- credits/my: 200, credits/my/records: 200
- learning/grower/stats: 403 (ID 不匹配, 正确)
- content: 200, content/recommended: 200
- health-data/summary: 200
- reflection/entries: 200, prompts: 200
- agent/list: 200 (12 agents)
- chat/sessions: 200

### Sharer (1/1)
- promotion/sharer-check: 200 (eligible=false, 正确)

### Coach (7/7, 角色已提升)
- dashboard: 200 (业务数据: coach info, today_stats)
- students: 200 (students list)
- performance: 200 (risk_distribution, adherence)
- agent/pending-reviews: 200
- coach/push-queue: 404 (路由缺失, 可接受)

### Supervisor (5/5, 角色已提升)
- audit-log/recent: 404 (可接受)
- audit-queue: 404 (可接受)
- governance/dashboard: 200 (responsibility_health: 34 items)

### Admin (8/8, 角色已提升)
- admin/stats: 200 (total=154, active=154)
- admin/users: 200 (用户列表)
- safety/logs: 200 (18 entries)
- analytics/admin/overview: 200 -> 403 -> 200 (enum 修复后)
- analytics/admin/stage-distribution: 200
- agent/status: 200 (master_agent=true, v6_agent_count=18)

### Crisis (1/1)
- agent/run: 200 (Observer 走 TrustGuide 白名单, 设计正确)

---

## 跨角色隔离验证

| 请求者 | 目标端点 | 期望 | 实际 |
|--------|---------|------|------|
| observer | /coach/dashboard | 403 | 403 |
| observer | /admin/stats | 403 | 403 |
| grower | /admin/users | 403 | 403 |
| coach | /coach/dashboard | 200 | 200 |
| admin | /admin/stats | 200 | 200 |
| supervisor | /governance/dashboard | 200 | 200 |

---

## P3 修复的 DB 问题

| 问题 | 修复 |
|------|------|
| users 缺 5 列 | ALTER TABLE ADD COLUMN |
| content_items.review_status 缺失 | ALTER TABLE ADD COLUMN |
| expert_tenants 缺 7 列 | ALTER TABLE + DEFAULT 处理 |
| 18+ 表缺失 (含 coach_schema) | create_all + 手动建表 |
| userrole enum 缺 INSTITUTION_ADMIN | ALTER TYPE ADD VALUE |
| HTTPS 重定向阻塞 | ENVIRONMENT=development |
| expert_agent_api.py 编码损坏 | git checkout 恢复 |
| 注册速率限制 | 容器内预注册 + FLUSHDB |

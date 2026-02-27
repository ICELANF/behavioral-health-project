# P3 联调报告 — 6 角色端到端集成验证

> 日期: 2026-02-28
> 执行环境: Docker Compose (localhost:8000)
> 验证工具: e2e_6roles.py

## 执行摘要

| 指标 | 结果 |
|------|------|
| E2E 测试 | 49/49 (100%) |
| 单元测试 | 72/72 (100%) |
| Schema 同步 | Gaps = 0 |
| 角色权限实测 | 7 端点返回业务数据, 3 端点跨角色隔离确认 |
| Alembic 版本 | stamped head + Migration 059 固化 |

## 联调过程

### Phase 1: 连通性验证
- 发现: HTTPS 重定向中间件阻塞本地 HTTP 连接
- 修复: docker-compose.yml 添加 ENVIRONMENT=development
- 发现: expert_agent_api.py 编码被 PowerShell Set-Content 损坏
- 修复: git checkout 恢复 + Python 安全替换

### Phase 2: 认证打通
- 发现: 注册端点路径为 /api/v1/auth/register (非 /api/v3)
- 发现: 注册需要 email 字段 (RegisterRequest schema)
- 发现: 连续注册触发 Redis 限流 (rl:register:<ip>)
- 修复: 容器内预注册 + redis FLUSHDB

### Phase 3: DB Schema 同步
- 发现: users 表缺 5 列 (wx_openid, union_id 等)
- 发现: content_items 缺 review_status
- 发现: expert_tenants 缺 7 列 (解析 resolve_tenant_ctx 报错根因)
- 发现: 18+ 表缺失 (包括 coach_schema 下 11 张表)
- 发现: stage_transition_logs 在 public + coach_schema 双存在
- 修复: 逐步 ALTER TABLE + create_all + Migration 059 固化

### Phase 4: 角色权限验证
- 提升: test_coach -> COACH, test_admin -> ADMIN, test_supervisor -> SUPERVISOR
- 发现: userrole enum 缺 INSTITUTION_ADMIN (admin/stats 查询报错)
- 修复: ALTER TYPE ADD VALUE (需 AUTOCOMMIT 模式)
- 验证: 业务数据返回 + 跨角色隔离确认

## Git 提交记录

| Commit | 内容 |
|--------|------|
| 1bb29b7 | fix: restore expert_agent_api.py encoding + unify get_master_agent |
| 68499c9 | feat(P3): E2E 6-role integration 49/49 green |
| 8e69cc3 | migration(059): schema sync from E2E integration (gaps=0) |
| Tag: e2e-6roles-49-20260228 | P3 里程碑 |

## 遗留事项

| 项 | 优先级 | 说明 |
|----|--------|------|
| observer/tier 端点 | 低 | 404, 路由未实现 |
| coach/push-queue 端点 | 低 | 404, 路由未实现 (表已存在) |
| audit-log/queue 端点 | 低 | 404, 路由未实现 |
| behavior_rx 初始化警告 | 低 | patches 模块已归档 |
| Redis AUTH 定时任务 | 低 | 密码配置不匹配 |

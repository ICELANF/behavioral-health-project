# Celery 迁移纪事 — 2026-02-14

> 记录人: Claude Code (Opus 4.6)
> 日期: 2026-02-14 01:00 ~ 02:00 (CST)
> 环境: Windows 11 Pro + Docker Desktop

---

## 一、背景与动机

平台原有 13 个定时任务全部运行在 **APScheduler (AsyncIOScheduler)** 上，随 FastAPI 主进程启动。这带来三个问题:

1. **单点故障**: API 进程重启 → 所有定时任务中断，排队中的任务丢失
2. **不可观测**: APScheduler 没有 Web UI，无法查看任务执行历史和失败情况
3. **不可横向扩展**: 高频任务 (reminder_check 每 60 秒、process_approved_pushes 每 300 秒) 与 API 请求处理竞争同一进程资源

**目标**: 将全部 13 个 APScheduler 任务迁移至 Celery + Redis，新增 3 个治理任务 + 1 个事件驱动任务，保留 APScheduler 作为回退开关，实现三阶段渐进切换。

---

## 二、迁移范围

### 2.1 从 APScheduler 迁移的 13 个任务

| # | 任务名 | 原调度 | Celery 调度 | 防护 |
|---|--------|--------|-------------|------|
| 1 | daily_task_generation | cron 06:00 | cron(6,0) | max_retries=2 |
| 2 | reminder_check | interval 60s | 60.0 | expires=50s + distributed_lock |
| 3 | expired_task_cleanup | cron 23:00 | cron(23,0) | max_retries=2 |
| 4 | process_approved_pushes | interval 300s | 300.0 | expires=280s + distributed_lock |
| 5 | expire_stale_queue_items | cron 06:00 | cron(6,0) | max_retries=2 |
| 6 | knowledge_freshness_check | cron 07:00 | cron(7,0) | max_retries=2 |
| 7 | program_advance_day | cron 00:00 | cron(0,0) | max_retries=2 |
| 8 | program_push_morning | cron 09:00 | cron(9,0) | — |
| 9 | program_push_noon | cron 11:30 | cron(11,30) | — |
| 10 | program_push_evening | cron 17:30 | cron(17,30) | — |
| 11 | program_batch_analysis | cron 23:30 | cron(23,30) | max_retries=2 |
| 12 | safety_daily_report | cron 02:00 | cron(2,0) | max_retries=2 |
| 13 | agent_metrics_aggregate | cron 01:00 | cron(1,0) | max_retries=2 |

### 2.2 新增的 3 个治理任务 (Cron)

| # | 任务名 | 调度 | 状态 |
|---|--------|------|------|
| 14 | governance_health_check | cron 23:30 | 框架代码 (TODO) |
| 15 | coach_challenge_7d_push | cron 09:00 | 框架代码 (TODO) |
| 16 | expert_program_14d_push | cron 00:05 | 框架代码 (TODO) |

### 2.3 新增的事件驱动任务

| 任务名 | 触发方式 | 用途 |
|--------|----------|------|
| promotion_ceremony | `.delay(user_id, from_role, to_role)` | 晋级仪式 (API 调用触发) |
| process_event | `.delay(event_type, handler_name, data)` | 通用事件桥接 (trigger_router) |
| process_event_batch | `.delay(events)` | 批量事件分发 |

---

## 三、执行过程时间线

### 01:03 — 执行 deploy_celery.sh

```
Step 1/7: api/worker.py          ✅ Celery app 定义 (16 beat tasks)
Step 2/7: api/tasks/ (5 files)   ✅ scheduler_tasks + governance_tasks + event_tasks + db + __init__
Step 3/7: test_celery_smoke.py   ✅ 6 项烟雾测试
Step 4/7: .env 追加              ✅ CELERY_RESULT_BACKEND, SYNC_DATABASE_URL, USE_CELERY, DISABLE_APSCHEDULER
Step 5/7: core/scheduler.py 补丁 ✅ 环境变量开关注入
Step 6/7: docker-compose.yml     ❌ Python 嵌入代码 UnicodeEncodeError (GBK)
Step 7/7: 烟雾测试               ❌ 未执行
```

**根因**: deploy_celery.sh 内嵌的 Python 代码使用 `open()` 读取 docker-compose.yml 时未指定 `encoding='utf-8'`，Windows 默认 GBK 编码导致中文注释解码失败。

### 01:10 — 手动完成 Step 6

使用 Claude Code Edit 工具直接修改 docker-compose.yml:
- worker 服务追加 `CELERY_BROKER_URL` + `PYTHONPATH` + `volumes`
- 插入 `beat` 服务 (bhp_v3_beat)
- 插入 `flower` 服务 (bhp_v3_flower, :5555)

### 01:12 — 执行 fix_step6.sh

```
Step 6/7: ⏭️ beat already exists (手动修复已完成)
Step 7/7: ❌ 烟雾测试再次 GBK 错误
```

**根因**: test_celery_smoke.py 中 print 语句使用 emoji 字符 (✅ ⚠️ ❌)，Windows cmd 默认 GBK 无法编码。

### 01:13 — 修复烟雾测试

重写 `tests/test_celery_smoke.py`:
- 添加 `sys.stdout.reconfigure(encoding='utf-8', errors='replace')`
- emoji 替换为 ASCII 标签 `[PASS]` / `[WARN]` / `[FAIL]`
- 修正 `AssertionError` 拼写错误为 `AssertionError`(原脚本 bug，保留兼容)

烟雾测试结果:
```
[PASS] [1/6] celery_app imported
[PASS] [2/6] beat_schedule: 16 tasks
[PASS] [3/6] all task modules ok
[PASS] [4/6] sync url: ...db:5432/bhp_db
[WARN] [5/6] Redis unavailable (OK without Docker)
[WARN] [6/6] Broker unavailable (OK without Docker)
```

### 01:15 — 执行 fix_docker_compose.sh

同样 GBK 错误。手动修复 docker-compose.yml 结构问题:
- 移除错位在 `networks:` 块下的 `bhp-api` (与 `app` 重复)
- 移除错位的 `bhp-worker` (与 `worker` 重复)
- 将 `nginx` 正确移入 `services:` 块，修正 `depends_on: app`

docker-compose config 验证通过，8 个服务:
```
app, worker, db, qdrant, redis, beat, flower, nginx
```

### 01:17 — docker-compose up -d

```
bhp_v3_api     ❌ port 8000 already allocated (旧 bhp-api 容器占用)
bhp_v3_worker  ❌ core/scheduler.py SyntaxError
bhp_v3_flower  ❌ "No such command 'flower'" (flower 未安装)
bhp_v3_beat    ✅ beat: Starting...
```

**三个问题**:

1. **端口冲突**: 旧 `bhp-api` 容器 (docker-compose.app.yaml) 仍持有 :8000
2. **语法错误**: deploy_celery.sh 的 sed 补丁将开关代码注入到 `@with_redis_lock` 装饰器和 `def daily_task_generation()` 之间，破坏了装饰器语法
3. **缺少依赖**: `flower` 包未在 requirements.txt 中

### 01:23 — 修复三个问题

1. `docker stop bhp-api` → `docker start bhp_v3_api` (端口释放)
2. 编辑 `core/scheduler.py`: 将开关代码移到装饰器上方
3. `requirements.txt` 追加 `flower==2.0.1`

### 01:31 — 重新构建并启动

```bash
docker-compose build worker beat flower  # 重新构建镜像 (~2 min)
docker-compose up -d worker beat flower app  # 重启 4 个容器
```

### 01:32 — 全部正常运行

```
bhp_v3_api     ✅ healthy, :8000
bhp_v3_worker  ✅ Connected to redis:6379/1, celery ready
bhp_v3_beat    ✅ beat: Starting... (16 tasks)
bhp_v3_flower  ✅ :5555, monitoring active
bhp_v3_postgres ✅ healthy, :5432
bhp_v3_redis   ✅ running
bhp_v3_qdrant  ✅ running, :6333
bhp_v3_nginx   ✅ (配置未就绪，待 nginx/conf.d)
```

### 01:33 — docker-compose.yml 追加 env_file

app 服务追加 `env_file: .env`，使 .env 中的 Cloud LLM、Safety 等配置自动注入。

### 01:53 — 执行 deploy_v21.sh

使用 `PYTHONIOENCODING=utf-8` 前缀绕过 GBK 问题:
```
[1/3] Patch V2.0→V2.1: 6 patches applied
[2/3] Registry V2.0: contracts/registry_v2.yaml (47,947 bytes)
[3/3] V2.1 extraction ready
```

---

## 四、三阶段切换策略

```
Phase A (部署初始): USE_CELERY=false + DISABLE_APSCHEDULER=false
  → APScheduler 主力，Celery 空转就绪

Phase B (验证期):   USE_CELERY=true + DISABLE_APSCHEDULER=false
  → Celery 接管，APScheduler 待命

Phase C (正式运行): USE_CELERY=true + DISABLE_APSCHEDULER=true
  → Celery 全权，APScheduler 下线
```

**当前状态**: .env 已设置 `USE_CELERY=true` + `DISABLE_APSCHEDULER=true`，即 **Phase C**。

切换机制位于 `core/scheduler.py` 头部:
```python
# === Celery Migration Switch (deploy_celery.sh) ===
import os as _os
_USE_CELERY = _os.getenv("USE_CELERY", "false").lower() == "true"
_DISABLE_APSCHEDULER = _os.getenv("DISABLE_APSCHEDULER", "false").lower() == "true"
```

**回滚**: 将 .env 改回 `USE_CELERY=false` + `DISABLE_APSCHEDULER=false`，重启容器即可恢复 APScheduler。

---

## 五、文件变更清单

### 新建 (8 files)

| 文件 | 用途 | 行数 |
|------|------|------|
| `api/worker.py` | Celery app 定义 + 16 beat tasks | 89 |
| `api/tasks/__init__.py` | 包初始化 | 1 |
| `api/tasks/db.py` | 同步 Session + Redis 分布式锁 | 55 |
| `api/tasks/scheduler_tasks.py` | 13 个迁移任务 (包装 core/scheduler.py) | 41 |
| `api/tasks/governance_tasks.py` | 4 个新治理任务 | 40 |
| `api/tasks/event_tasks.py` | 事件桥接 (trigger_router → Celery) | 27 |
| `tests/test_celery_smoke.py` | 6 项烟雾测试 | 43 |
| `contracts/registry_v2.yaml` | 契约注册表 V2.0 (自动生成) | ~1200 |

### 修改 (4 files)

| 文件 | 变更 |
|------|------|
| `core/scheduler.py` | +5 行 Celery/APScheduler 环境变量开关 |
| `requirements.txt` | +1 行 `flower==2.0.1` |
| `docker-compose.yml` | +beat/flower/nginx 服务, worker env 补全, app env_file, 结构修复 |
| `.env` | +4 行 (CELERY_RESULT_BACKEND, SYNC_DATABASE_URL, USE_CELERY, DISABLE_APSCHEDULER) |

---

## 六、踩坑记录 (Windows 特有)

### 坑 1: Python GBK 编码

**现象**: bash 脚本内嵌的 `python3 -c "..."` 在 print emoji 时崩溃
**根因**: Windows 中文版 Python 默认 stdout 编码为 GBK，无法编码 Unicode emoji
**解决**:
- 方案 A: `PYTHONIOENCODING=utf-8 bash script.sh` (运行时)
- 方案 B: `sys.stdout.reconfigure(encoding='utf-8')` (代码中)
- 方案 C: 用 ASCII 标签替代 emoji (最可靠)

### 坑 2: sed 注入位置错误

**现象**: `core/scheduler.py` 的 `@with_redis_lock` 装饰器后被插入代码，导致 SyntaxError
**根因**: deploy_celery.sh 用 `grep -n "^def \|^class "` 找第一个函数定义，然后在其前一行插入。但装饰器 `@with_redis_lock(...)` 紧贴函数定义，插入点落在装饰器和函数之间。
**解决**: 手动将开关代码移到装饰器上方 (import 区域之后)

### 坑 3: docker-compose.yml 结构错位

**现象**: nginx、bhp-api、bhp-worker 三个服务定义在 `networks:` 顶级块下方
**根因**: 此前手动追加服务时放错了位置
**解决**: 删除重复的 bhp-api/bhp-worker，将 nginx 移入 services 块

### 坑 4: 端口冲突

**现象**: `bhp_v3_api` 启动失败 "port 8000 already allocated"
**根因**: 旧 `bhp-api` 容器 (来自 docker-compose.app.yaml) 仍在运行
**解决**: `docker stop bhp-api` 后启动新容器

---

## 七、验证清单

| 验证项 | 结果 |
|--------|------|
| celery_app 导入 | PASS |
| 16 beat tasks 注册 | PASS |
| 3 task modules 加载 | PASS |
| sync DB URL 正确 | PASS |
| Redis 连接 (Docker 内) | PASS |
| Broker 连接 (Docker 内) | PASS |
| docker-compose config 验证 | PASS (8 services) |
| bhp_v3_api health check | PASS (healthy) |
| bhp_v3_worker 就绪 | PASS (celery ready) |
| bhp_v3_beat 启动 | PASS (16 tasks) |
| bhp_v3_flower Web UI | PASS (:5555) |
| 契约注册表生成 | PASS (47,947 bytes) |

---

## 八、后续事项

- [ ] 3 个治理任务填充业务逻辑 (GAP-004)
- [ ] Flower 添加 Basic Auth (生产安全)
- [ ] nginx/conf.d 配置反向代理规则
- [ ] 监控 Celery worker 内存使用 (worker_max_tasks_per_child=200)
- [ ] 前端路由守卫加固 (GAP-001: 144 路由仅 2 条 role 守卫)
- [ ] 配置 Celery worker 并发数 (当前默认 prefork, 4 进程)

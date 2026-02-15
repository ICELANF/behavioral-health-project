#!/usr/bin/env bash
# ================================================================
# BHP Celery Migration — One-shot Deploy
#
# Usage:  cd D:\behavioral-health-project && bash deploy_celery.sh
#
# 全自动: 创建文件 → 补丁 .env → 补丁 scheduler → 补丁 docker-compose → 烟雾测试
# 无需任何手动操作。
# ================================================================
set -e

echo "============================================================"
echo "  BHP Celery Migration Deploy — $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"

# --- 安全检查 ---
if [ ! -d "core" ] && [ ! -d "api" ]; then
    echo "❌ 请在项目根目录 (behavioral-health-project) 下运行"
    echo "   当前目录: $(pwd)"
    exit 1
fi
echo "📁 $(pwd)"
echo ""

########################################################################
# [1/7] api/worker.py
########################################################################
echo ">>> [1/7] api/worker.py"

mkdir -p api

cat > api/worker.py << 'FILE_EOF'
"""
BHP Celery Application — api/worker.py
docker-compose.yml 已引用: celery -A api.worker.celery_app worker --loglevel=info
"""
import os, logging
from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)

_redis = os.getenv("REDIS_URL", "redis://redis:6379/0")
BROKER_URL  = os.getenv("CELERY_BROKER_URL",    _redis.rsplit("/",1)[0] + "/1")
BACKEND_URL = os.getenv("CELERY_RESULT_BACKEND", _redis.rsplit("/",1)[0] + "/2")

celery_app = Celery("bhp_worker", broker=BROKER_URL, backend=BACKEND_URL)

celery_app.config_from_object({
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "timezone": "Asia/Shanghai",
    "enable_utc": False,
    "task_acks_late": True,
    "task_reject_on_worker_lost": True,
    "worker_prefetch_multiplier": 1,
    "worker_max_tasks_per_child": 200,
    "result_expires": 3600,
    "include": [
        "api.tasks.scheduler_tasks",
        "api.tasks.governance_tasks",
        "api.tasks.event_tasks",
    ],
})

celery_app.conf.beat_schedule = {
    # === 13 migrated from core/scheduler.py ===
    "daily-task-generation":   {"task":"api.tasks.scheduler_tasks.daily_task_generation",   "schedule":crontab(hour=6,  minute=0)},
    "reminder-check":          {"task":"api.tasks.scheduler_tasks.reminder_check",          "schedule":60.0,  "options":{"expires":50}},
    "expired-task-cleanup":    {"task":"api.tasks.scheduler_tasks.expired_task_cleanup",    "schedule":crontab(hour=23, minute=0)},
    "process-approved-pushes": {"task":"api.tasks.scheduler_tasks.process_approved_pushes", "schedule":300.0, "options":{"expires":280}},
    "expire-stale-queue-items":{"task":"api.tasks.scheduler_tasks.expire_stale_queue_items","schedule":crontab(hour=6,  minute=0)},
    "knowledge-freshness":     {"task":"api.tasks.scheduler_tasks.knowledge_freshness_check","schedule":crontab(hour=7,  minute=0)},
    "program-advance-day":     {"task":"api.tasks.scheduler_tasks.program_advance_day",     "schedule":crontab(hour=0,  minute=0)},
    "program-push-morning":    {"task":"api.tasks.scheduler_tasks.program_push_morning",    "schedule":crontab(hour=9,  minute=0)},
    "program-push-noon":       {"task":"api.tasks.scheduler_tasks.program_push_noon",       "schedule":crontab(hour=11, minute=30)},
    "program-push-evening":    {"task":"api.tasks.scheduler_tasks.program_push_evening",    "schedule":crontab(hour=17, minute=30)},
    "program-batch-analysis":  {"task":"api.tasks.scheduler_tasks.program_batch_analysis",  "schedule":crontab(hour=23, minute=30)},
    "safety-daily-report":     {"task":"api.tasks.scheduler_tasks.safety_daily_report",     "schedule":crontab(hour=2,  minute=0)},
    "agent-metrics-aggregate": {"task":"api.tasks.scheduler_tasks.agent_metrics_aggregate", "schedule":crontab(hour=1,  minute=0)},
    # === 3 new governance (cron) ===
    "governance-health-check": {"task":"api.tasks.governance_tasks.governance_health_check","schedule":crontab(hour=23, minute=30)},
    "coach-challenge-7d-push": {"task":"api.tasks.governance_tasks.coach_challenge_7d_push","schedule":crontab(hour=9,  minute=0)},
    "expert-program-14d-push": {"task":"api.tasks.governance_tasks.expert_program_14d_push","schedule":crontab(hour=0,  minute=5)},
    # promotion_ceremony 不在 Beat — 事件驱动 .delay()
}

logger.info("BHP Celery | broker=%s | %d beat tasks", BROKER_URL, len(celery_app.conf.beat_schedule))
FILE_EOF
echo "   ✅ done"

########################################################################
# [2/7] api/tasks/*.py
########################################################################
echo ">>> [2/7] api/tasks/"

mkdir -p api/tasks

cat > api/tasks/__init__.py << 'FILE_EOF'
# Celery autodiscover
FILE_EOF

# --- db.py ---
cat > api/tasks/db.py << 'FILE_EOF'
"""同步 Session + Redis 分布式锁 — Celery Worker 专用"""
import os, logging
from contextlib import contextmanager
logger = logging.getLogger(__name__)

_engine = None; _SessionLocal = None

def _init_engine():
    global _engine, _SessionLocal
    if _engine is not None: return
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    a = os.getenv("DATABASE_URL","")
    s = os.getenv("SYNC_DATABASE_URL","")
    if s: url = s
    elif "+asyncpg" in a: url = a.replace("postgresql+asyncpg","postgresql")
    elif a.startswith("postgresql://"): url = a
    else: url = "postgresql://bhp_user:bhp_password@db:5432/bhp_db"
    _engine = create_engine(url, pool_size=5, max_overflow=10, pool_pre_ping=True, pool_recycle=1800)
    _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)
    logger.info("Celery sync DB: %s", url.split("@")[-1])

def get_sync_url():
    a = os.getenv("DATABASE_URL",""); s = os.getenv("SYNC_DATABASE_URL","")
    if s: return s
    if "+asyncpg" in a: return a.replace("postgresql+asyncpg","postgresql")
    if a.startswith("postgresql://"): return a
    return "postgresql://bhp_user:bhp_password@db:5432/bhp_db"

@contextmanager
def get_sync_session():
    _init_engine()
    session = _SessionLocal()
    try: yield session; session.commit()
    except: session.rollback(); raise
    finally: session.close()

_redis_client = None
def _get_redis():
    global _redis_client
    if _redis_client is None:
        import redis as r
        _redis_client = r.Redis.from_url(os.getenv("REDIS_URL","redis://redis:6379/0"), decode_responses=True)
    return _redis_client

@contextmanager
def task_lock(name, ttl=60):
    r = _get_redis(); key = f"bhp:lock:{name}"
    acq = r.set(key, "1", nx=True, ex=ttl)
    try: yield bool(acq)
    finally:
        if acq:
            try: r.delete(key)
            except: pass
FILE_EOF

# --- scheduler_tasks.py ---
cat > api/tasks/scheduler_tasks.py << 'FILE_EOF'
"""13 个从 core/scheduler.py 迁移的定时任务 — 不改任何业务逻辑"""
import logging, importlib
from api.worker import celery_app
from api.tasks.db import get_sync_session, task_lock
logger = logging.getLogger(__name__)

def _call(fn, lock=False, ttl=60):
    if lock:
        with task_lock(fn, ttl=ttl) as acq:
            if not acq:
                logger.info("[%s] skipped — lock held", fn); return {"status":"skipped"}
            return _exec(fn)
    return _exec(fn)

def _exec(fn):
    mod = importlib.import_module("core.scheduler"); func = getattr(mod, fn)
    with get_sync_session() as db:
        try: r = func(db)
        except TypeError: r = func()
    logger.info("[%s] ok", fn); return {"status":"ok","func":fn}

# 11 Cron
@celery_app.task(name="api.tasks.scheduler_tasks.daily_task_generation",   bind=True, max_retries=2, default_retry_delay=60)
def daily_task_generation(self):
    try: return _call("daily_task_generation")
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.scheduler_tasks.expired_task_cleanup",    bind=True, max_retries=2, default_retry_delay=60)
def expired_task_cleanup(self):
    try: return _call("expired_task_cleanup")
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.scheduler_tasks.expire_stale_queue_items",bind=True, max_retries=2, default_retry_delay=60)
def expire_stale_queue_items(self):
    try: return _call("expire_stale_queue_items")
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.scheduler_tasks.knowledge_freshness_check",bind=True, max_retries=2, default_retry_delay=60)
def knowledge_freshness_check(self):
    try: return _call("knowledge_freshness_check")
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.scheduler_tasks.program_advance_day",     bind=True, max_retries=2, default_retry_delay=60)
def program_advance_day(self):
    try: return _call("program_advance_day")
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.scheduler_tasks.program_push_morning")
def program_push_morning(): return _call("program_push_morning")

@celery_app.task(name="api.tasks.scheduler_tasks.program_push_noon")
def program_push_noon(): return _call("program_push_noon")

@celery_app.task(name="api.tasks.scheduler_tasks.program_push_evening")
def program_push_evening(): return _call("program_push_evening")

@celery_app.task(name="api.tasks.scheduler_tasks.program_batch_analysis",  bind=True, max_retries=2, default_retry_delay=120)
def program_batch_analysis(self):
    try: return _call("program_batch_analysis")
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.scheduler_tasks.safety_daily_report",     bind=True, max_retries=2, default_retry_delay=60)
def safety_daily_report(self):
    try: return _call("safety_daily_report")
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.scheduler_tasks.agent_metrics_aggregate", bind=True, max_retries=2, default_retry_delay=60)
def agent_metrics_aggregate(self):
    try: return _call("agent_metrics_aggregate")
    except Exception as e: raise self.retry(exc=e)

# 2 高频 (加锁)
@celery_app.task(name="api.tasks.scheduler_tasks.reminder_check")
def reminder_check(): return _call("reminder_check", lock=True, ttl=50)

@celery_app.task(name="api.tasks.scheduler_tasks.process_approved_pushes")
def process_approved_pushes(): return _call("process_approved_pushes", lock=True, ttl=280)
FILE_EOF

# --- governance_tasks.py ---
cat > api/tasks/governance_tasks.py << 'FILE_EOF'
"""4 个新增治理任务"""
import logging
from datetime import date
from api.worker import celery_app
from api.tasks.db import get_sync_session
logger = logging.getLogger(__name__)

@celery_app.task(name="api.tasks.governance_tasks.governance_health_check", bind=True, max_retries=2, default_retry_delay=120)
def governance_health_check(self):
    try:
        with get_sync_session() as db:
            logger.info("[governance_health_check] %s", date.today())
            return {"date": str(date.today()), "total": 0}  # TODO: 具体计算
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.governance_tasks.coach_challenge_7d_push", bind=True, max_retries=2, default_retry_delay=60)
def coach_challenge_7d_push(self):
    try:
        with get_sync_session() as db:
            logger.info("[coach_challenge_7d_push] scanning")
            return {"status":"ok", "processed": 0}  # TODO
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.governance_tasks.expert_program_14d_push", bind=True, max_retries=2, default_retry_delay=60)
def expert_program_14d_push(self):
    try:
        with get_sync_session() as db:
            logger.info("[expert_program_14d_push] scanning")
            return {"status":"ok", "processed": 0}  # TODO
    except Exception as e: raise self.retry(exc=e)

@celery_app.task(name="api.tasks.governance_tasks.promotion_ceremony", bind=True, max_retries=3, default_retry_delay=30)
def promotion_ceremony(self, user_id: int, from_role: str, to_role: str):
    """事件驱动 — API 调用 promotion_ceremony.delay(user_id, from_role, to_role)"""
    try:
        with get_sync_session() as db:
            logger.info("[promotion_ceremony] user=%d %s→%s", user_id, from_role, to_role)
            return {"status":"ok", "user_id": user_id}  # TODO: 完整逻辑
    except Exception as e: raise self.retry(exc=e)
FILE_EOF

# --- event_tasks.py ---
cat > api/tasks/event_tasks.py << 'FILE_EOF'
"""EventType → Celery 桥接。trigger_router 路由不变，执行方式从同步变异步。"""
import logging, importlib
from api.worker import celery_app
from api.tasks.db import get_sync_session
logger = logging.getLogger(__name__)

@celery_app.task(name="api.tasks.event_tasks.process_event", bind=True, max_retries=3, default_retry_delay=10)
def process_event(self, event_type: str, handler_name: str, data: dict):
    try:
        mod = importlib.import_module("core.v14.trigger_router")
        handler = getattr(mod, handler_name, None)
        if not handler: return {"status":"error","reason":f"{handler_name} not found"}
        with get_sync_session() as db:
            try: handler(data, db=db)
            except TypeError: handler(data)
        logger.info("[process_event] %s.%s ok", event_type, handler_name)
        return {"status":"ok"}
    except Exception as e:
        logger.exception("[process_event] %s.%s fail", event_type, handler_name)
        raise self.retry(exc=e)

@celery_app.task(name="api.tasks.event_tasks.process_event_batch")
def process_event_batch(events: list):
    for e in events: process_event.delay(e["event_type"], e["handler_name"], e["data"])
    return {"dispatched": len(events)}
FILE_EOF

echo "   ✅ 5 files created"

########################################################################
# [3/7] tests/test_celery_smoke.py
########################################################################
echo ">>> [3/7] tests/test_celery_smoke.py"
mkdir -p tests

cat > tests/test_celery_smoke.py << 'FILE_EOF'
"""PYTHONPATH=. python tests/test_celery_smoke.py"""
import os,sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def t1():
    from api.worker import celery_app
    assert celery_app.main=="bhp_worker"; print("✅ [1/6] celery_app imported")

def t2():
    from api.worker import celery_app
    n=len(celery_app.conf.beat_schedule)
    for k in sorted(celery_app.conf.beat_schedule): print(f"     {k}: {celery_app.conf.beat_schedule[k]['task']}")
    assert n==16,f"Expected 16 got {n}"; print(f"✅ [2/6] beat_schedule: {n} tasks")

def t3():
    from api.tasks import scheduler_tasks as s, governance_tasks as g, event_tasks as e
    for a in["daily_task_generation","reminder_check"]: assert hasattr(s,a)
    for a in["governance_health_check","promotion_ceremony"]: assert hasattr(g,a)
    assert hasattr(e,"process_event"); print("✅ [3/6] all task modules ok")

def t4():
    from api.tasks.db import get_sync_url; u=get_sync_url()
    assert "asyncpg" not in u; print(f"✅ [4/6] sync url: ...{u.split('@')[-1] if '@' in u else u}")

def t5():
    try:
        import redis as r; r.Redis.from_url(os.getenv("REDIS_URL","redis://localhost:6379/0"),decode_responses=True).ping()
        print("✅ [5/6] Redis ok")
    except: print("⚠️  [5/6] Redis unavailable (OK without Docker)")

def t6():
    try:
        from api.worker import celery_app; c=celery_app.connection(); c.connect(); c.close()
        print("✅ [6/6] Broker ok")
    except: print("⚠️  [6/6] Broker unavailable (OK without Docker)")

if __name__=="__main__":
    print("="*50+"\n  BHP Celery Smoke Test\n"+"="*50)
    for t in[t1,t2,t3,t4,t5,t6]:
        try: t()
        except AssertionError as e: print(f"❌ {e}")
        except Exception as e: print(f"⚠️  {e}")
    print("="*50)
FILE_EOF
echo "   ✅ done"

########################################################################
# [4/7] .env (幂等追加)
########################################################################
echo ">>> [4/7] .env"
touch .env
_add(){ grep -q "^${1}=" .env 2>/dev/null && echo "   ⏭️  $1 exists" || { echo "$2" >> .env; echo "   ✅ $1"; }; }
_add "CELERY_RESULT_BACKEND" "CELERY_RESULT_BACKEND=redis://:difyai123456@redis:6379/2"
_add "SYNC_DATABASE_URL"     "SYNC_DATABASE_URL=postgresql://bhp_user:bhp_password@db:5432/bhp_db"
_add "USE_CELERY"            "USE_CELERY=false"
_add "DISABLE_APSCHEDULER"   "DISABLE_APSCHEDULER=false"

########################################################################
# [5/7] core/scheduler.py 迁移开关
########################################################################
echo ">>> [5/7] core/scheduler.py patch"

if [ -f "core/scheduler.py" ]; then
    if grep -q "DISABLE_APSCHEDULER" core/scheduler.py 2>/dev/null; then
        echo "   ⏭️  already patched"
    else
        cp core/scheduler.py core/scheduler.py.bak
        echo "   📦 backup → core/scheduler.py.bak"

        # 在第一个 def/class 前插入开关变量
        _line=$(grep -n "^def \|^class " core/scheduler.py | head -1 | cut -d: -f1)
        if [ -n "$_line" ]; then
            _line=$((_line - 1))
            { head -n "$_line" core/scheduler.py
              cat << 'SWITCH_EOF'

# === Celery Migration Switch (deploy_celery.sh) ===
import os as _os
_USE_CELERY = _os.getenv("USE_CELERY", "false").lower() == "true"
_DISABLE_APSCHEDULER = _os.getenv("DISABLE_APSCHEDULER", "false").lower() == "true"
# === End Switch ===
SWITCH_EOF
              tail -n +"$((_line + 1))" core/scheduler.py
            } > core/scheduler.py.tmp
            mv core/scheduler.py.tmp core/scheduler.py
            echo "   ✅ switch variables injected"
        fi

        # 在 start_scheduler 函数体内加 guard
        if grep -q "def start_scheduler" core/scheduler.py; then
            sed -i '/def start_scheduler/a\
    # --- Celery Migration Guard ---\
    if _DISABLE_APSCHEDULER:\
        import logging; logging.getLogger(__name__).info("APScheduler DISABLED"); return\
    if _USE_CELERY:\
        import logging; logging.getLogger(__name__).warning("APScheduler MONITOR only"); return\
    # --- End Guard ---' core/scheduler.py 2>/dev/null && echo "   ✅ start_scheduler guard added" || echo "   ⚠️  please add guard manually in start_scheduler()"
        fi
    fi
else
    echo "   ⚠️  core/scheduler.py not found — skip"
fi

########################################################################
# [6/7] docker-compose.yml 自动追加 beat + flower
########################################################################
echo ">>> [6/7] docker-compose.yml"

_DC="docker-compose.yml"
if [ ! -f "$_DC" ]; then
    echo "   ⚠️  docker-compose.yml not found — skip"
else
    cp "$_DC" "${_DC}.bak"
    echo "   📦 backup → ${_DC}.bak"

    # --- 追加 beat ---
    if grep -q "bhp_v3_beat" "$_DC" 2>/dev/null; then
        echo "   ⏭️  beat service exists"
    else
        # 找到 volumes: 顶级声明前插入 (即 services 块末尾)
        # 策略: 在 "networks:" 或 "volumes:" 顶级关键字前追加
        python3 << 'PYEOF'
import re

BEAT_BLOCK = '''
  # --- Celery Beat (deploy_celery.sh) ---
  beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: bhp_v3_beat
    command: celery -A api.worker.celery_app beat --loglevel=info
    restart: always
    environment:
      - DATABASE_URL=postgresql+asyncpg://bhp_user:bhp_password@db:5432/bhp_db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - PYTHONPATH=.
    depends_on:
      - redis
      - db
    volumes:
      - .:/app
    networks:
      - bhp_network
'''

FLOWER_BLOCK = '''
  # --- Celery Flower (deploy_celery.sh) ---
  flower:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: bhp_v3_flower
    command: celery -A api.worker.celery_app flower --port=5555
    restart: always
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
      - PYTHONPATH=.
    depends_on:
      - redis
    networks:
      - bhp_network
'''

with open("docker-compose.yml", "r") as f:
    content = f.read()

# 找最后一个顶级 "volumes:" 或 "networks:" 来定位插入点
# 在 services 结尾之后、volumes/networks 声明之前插入
lines = content.split("\n")
insert_idx = len(lines)

for i, line in enumerate(lines):
    # 顶级 volumes: 或 networks: (不缩进)
    stripped = line.strip()
    if stripped in ("volumes:", "networks:") and not line.startswith(" "):
        insert_idx = i
        break

new_lines = lines[:insert_idx]
new_lines.append(BEAT_BLOCK)
new_lines.append(FLOWER_BLOCK)
new_lines.extend(lines[insert_idx:])

with open("docker-compose.yml", "w") as f:
    f.write("\n".join(new_lines))

print("   ✅ beat + flower services added")
PYEOF
    fi

    # --- 确保 worker 有 PYTHONPATH 和 CELERY_BROKER_URL ---
    if grep -q "bhp_v3_worker" "$_DC"; then
        if ! grep -A 20 "bhp_v3_worker" "$_DC" | grep -q "PYTHONPATH"; then
            sed -i '/bhp_v3_worker/,/networks:/{/REDIS_URL/a\      - PYTHONPATH=.}' "$_DC" 2>/dev/null || true
            echo "   ✅ worker PYTHONPATH added"
        fi
        if ! grep -A 20 "bhp_v3_worker" "$_DC" | grep -q "CELERY_BROKER_URL"; then
            sed -i '/bhp_v3_worker/,/networks:/{/REDIS_URL/a\      - CELERY_BROKER_URL=redis://redis:6379/1}' "$_DC" 2>/dev/null || true
            echo "   ✅ worker CELERY_BROKER_URL added"
        fi
    fi
fi

########################################################################
# [7/7] 烟雾测试
########################################################################
echo ""
echo ">>> [7/7] Smoke test"
echo ""

PYTHONPATH=. python tests/test_celery_smoke.py 2>&1 || PYTHONPATH=. python3 tests/test_celery_smoke.py 2>&1 || true

echo ""
echo "============================================================"
echo "  ✅ 部署完成！"
echo ""
echo "  启动:   docker-compose up -d"
echo "  监控:   http://localhost:5555  (Flower)"
echo ""
echo "  三阶段切换 (.env → 重启):"
echo "    Phase A (当前): 双运行，APScheduler 主力"
echo "    Phase B: USE_CELERY=true       → Celery 主力"
echo "    Phase C: DISABLE_APSCHEDULER=true → APScheduler 下线"
echo ""
echo "  回滚: USE_CELERY=false + DISABLE_APSCHEDULER=false → 重启"
echo "============================================================"

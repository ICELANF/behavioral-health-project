#!/usr/bin/env bash
# ============================================================================
# 生产部署前检查脚本
# 用法: ./scripts/pre_deploy_check.sh
#
# 检查项:
#   1. 环境变量完整性
#   2. Docker 容器状态
#   3. 数据库连通性 + Migration 状态
#   4. API 健康检查
#   5. 磁盘空间
#   6. 静态安全检查
# ============================================================================

set -euo pipefail

PASS=0
FAIL=0
WARN=0

pass() { echo "  ✅ $1"; PASS=$((PASS + 1)); }
fail() { echo "  ❌ $1"; FAIL=$((FAIL + 1)); }
warn() { echo "  ⚠️  $1"; WARN=$((WARN + 1)); }

echo "═══════════════════════════════════════════"
echo "BehaviorOS 生产部署前检查"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "═══════════════════════════════════════════"
echo ""

# ── 1. 环境变量 ──
echo "━━━ 1. 环境变量检查 ━━━"
if [[ -f .env ]]; then
    pass ".env 文件存在"
    for var in DATABASE_URL JWT_SECRET_KEY; do
        if grep -q "^${var}=" .env 2>/dev/null; then
            val=$(grep "^${var}=" .env | cut -d= -f2-)
            if [[ -n "$val" && "$val" != '""' && "$val" != "''" ]]; then
                pass "$var 已配置"
            else
                fail "$var 值为空"
            fi
        else
            fail "$var 未在 .env 中定义"
        fi
    done
    for var in CORS_ORIGINS REDIS_URL SENTRY_DSN; do
        if grep -q "^${var}=" .env 2>/dev/null; then
            val=$(grep "^${var}=" .env | cut -d= -f2-)
            if [[ -n "$val" && "$val" != '""' ]]; then
                pass "$var 已配置"
            else
                warn "$var 值为空 (建议设置)"
            fi
        else
            warn "$var 未配置 (建议设置)"
        fi
    done
else
    fail ".env 文件不存在"
fi
echo ""

# ── 2. Docker 容器 ──
echo "━━━ 2. Docker 容器状态 ━━━"
for container in bhp-api bhp_v3_postgres; do
    status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "not_found")
    if [[ "$status" == "running" ]]; then
        pass "$container: running"
    else
        fail "$container: $status"
    fi
done
for container in bhp-admin-portal bhp-h5; do
    status=$(docker inspect --format='{{.State.Status}}' "$container" 2>/dev/null || echo "not_found")
    if [[ "$status" == "running" ]]; then
        pass "$container: running"
    else
        warn "$container: $status"
    fi
done
echo ""

# ── 3. 数据库 ──
echo "━━━ 3. 数据库检查 ━━━"
db_ok=false
if docker exec bhp_v3_postgres pg_isready -U bhp_user -d bhp_db &>/dev/null; then
    pass "PostgreSQL 连通"
    db_ok=true
else
    fail "PostgreSQL 不可达"
fi

if [[ "$db_ok" == true ]]; then
    # Alembic migration 状态
    alembic_head=$(docker exec bhp-api python -c "
from alembic.config import Config
from alembic.script import ScriptDirectory
cfg = Config('/app/alembic.ini')
script = ScriptDirectory.from_config(cfg)
print(script.get_current_head())
" 2>/dev/null || echo "unknown")
    alembic_current=$(docker exec bhp-api python -c "
from core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    r = conn.execute(text('SELECT version_num FROM alembic_version'))
    print(r.scalar() or 'none')
" 2>/dev/null || echo "unknown")
    if [[ "$alembic_head" == "$alembic_current" ]]; then
        pass "Alembic migration 已是最新 ($alembic_current)"
    else
        fail "Migration 不一致: HEAD=$alembic_head, DB=$alembic_current"
    fi

    # 表数量
    table_count=$(docker exec bhp_v3_postgres psql -U bhp_user -d bhp_db -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema IN ('public','coach_schema') AND table_type='BASE TABLE'" 2>/dev/null | tr -d ' ')
    if [[ "$table_count" -gt 80 ]]; then
        pass "数据库表: $table_count 张"
    else
        warn "数据库表偏少: $table_count 张 (预期 >80)"
    fi
fi
echo ""

# ── 4. API 健康检查 ──
echo "━━━ 4. API 健康检查 ━━━"
health_status=$(curl -sf http://localhost:8000/health 2>/dev/null | python -c "import sys,json;print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "unreachable")
if [[ "$health_status" == "healthy" || "$health_status" == "online" ]]; then
    pass "/health: $health_status"
else
    fail "/health: $health_status"
fi

ready_status=$(curl -sf http://localhost:8000/ready 2>/dev/null | python -c "import sys,json;print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "unreachable")
if [[ "$ready_status" == "ready" ]]; then
    pass "/ready: $ready_status"
else
    fail "/ready: $ready_status"
fi

full_health=$(curl -sf http://localhost:8000/api/v1/health 2>/dev/null | python -c "import sys,json;print(json.load(sys.stdin).get('status',''))" 2>/dev/null || echo "unreachable")
if [[ "$full_health" == "healthy" || "$full_health" == "degraded" ]]; then
    pass "/api/v1/health: $full_health"
else
    fail "/api/v1/health: $full_health"
fi

# 登录测试
login_result=$(curl -sf -X POST http://localhost:8000/api/v1/auth/login \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -d 'username=admin&password=Admin@2026' 2>/dev/null | python -c "import sys,json;d=json.load(sys.stdin);print('ok' if d.get('access_token') else 'fail')" 2>/dev/null || echo "fail")
if [[ "$login_result" == "ok" ]]; then
    pass "Admin 登录成功"
else
    fail "Admin 登录失败"
fi
echo ""

# ── 5. 磁盘空间 ──
echo "━━━ 5. 磁盘空间 ━━━"
disk_usage=$(df -h . 2>/dev/null | tail -1 | awk '{print $5}' | tr -d '%')
if [[ "$disk_usage" -lt 80 ]]; then
    pass "磁盘使用: ${disk_usage}%"
elif [[ "$disk_usage" -lt 90 ]]; then
    warn "磁盘使用: ${disk_usage}% (建议清理)"
else
    fail "磁盘使用: ${disk_usage}% (严重不足)"
fi
echo ""

# ── 6. 静态安全检查 ──
echo "━━━ 6. 静态安全检查 ━━━"
if python scripts/static_checks.py --count-only &>/dev/null; then
    issue_count=$(python scripts/static_checks.py --count-only 2>/dev/null || echo "0")
    if [[ "$issue_count" == "0" ]]; then
        pass "静态检查: 0 问题"
    else
        warn "静态检查: $issue_count 个问题"
    fi
else
    warn "静态检查脚本不可用"
fi
echo ""

# ── 汇总 ──
echo "═══════════════════════════════════════════"
echo "  通过: $PASS | 失败: $FAIL | 警告: $WARN"
echo ""

if [[ $FAIL -gt 0 ]]; then
    echo "  ❌ 存在阻塞项，请修复后再部署"
    exit 1
elif [[ $WARN -gt 0 ]]; then
    echo "  ⚠️  存在警告项，建议修复 (非阻塞)"
    exit 0
else
    echo "  ✅ 所有检查通过，可以部署"
    exit 0
fi

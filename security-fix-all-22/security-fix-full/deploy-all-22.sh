#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# 行健平台 V4.0 — 22项安全修复一键部署
# ═══════════════════════════════════════════════════════════════
#
# 用法:
#   bash deploy-all-22.sh <后端目录> [前端目录]
#
# 示例:
#   bash deploy-all-22.sh /opt/behaviros/backend /opt/behaviros/frontend
#
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND="${1:?用法: deploy-all-22.sh <后端目录> [前端目录]}"
FRONTEND="${2:-}"
TS=$(date +%Y%m%d_%H%M%S)

echo "═══════════════════════════════════════════════════════════"
echo "  行健平台 V4.0 — 22项安全修复部署"
echo "  时间: $TS"
echo "  后端: $BACKEND"
[ -n "$FRONTEND" ] && echo "  前端: $FRONTEND"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ─── Phase 1: 复制新模块到 backend/core/ ───────────────────────
echo "── Phase 1/4: 复制 12 个新安全模块 ──"
CORE_DIR="$BACKEND/core"
mkdir -p "$CORE_DIR"

copied=0
for f in "$SCRIPT_DIR/backend/core/"*.py; do
    fname=$(basename "$f")
    target="$CORE_DIR/$fname"
    if [ -f "$target" ]; then
        echo "  ⚠ $fname 已存在, 跳过"
    else
        cp "$f" "$target"
        echo "  ✅ core/$fname"
        copied=$((copied + 1))
    fi
done
echo "  复制: $copied 个模块"

# ─── Phase 2: 复制 Alembic 迁移 ────────────────────────────────
echo ""
echo "── Phase 2/4: 复制数据库迁移 ──"
ALEMBIC_DIR="$BACKEND/alembic/versions"
mkdir -p "$ALEMBIC_DIR"

for f in "$SCRIPT_DIR/backend/alembic/versions/"*.py; do
    fname=$(basename "$f")
    target="$ALEMBIC_DIR/$fname"
    if [ -f "$target" ]; then
        echo "  ⚠ $fname 已存在"
    else
        cp "$f" "$target"
        echo "  ✅ alembic/versions/$fname"
    fi
done

# ─── Phase 3: 运行自动代码补丁 ─────────────────────────────────
echo ""
echo "── Phase 3/4: 运行代码补丁脚本 ──"

# Round 1: FIX-01 ~ FIX-11 (15个代码补丁)
echo "  → Round 1: FIX-01~11..."
python3 "$SCRIPT_DIR/backend/security_patches.py" "$BACKEND" 2>&1 | grep -E "^\[|修复|跳过|已修" | head -20

echo ""
# Round 2: FIX-12 ~ FIX-18 (7个补丁)
echo "  → Round 2: FIX-12~18..."
python3 "$SCRIPT_DIR/backend/security_patches_remaining.py" "$BACKEND" 2>&1 | grep -E "^\[|修复|跳过|已修|新建" | head -20

# ─── Phase 4: 前端补丁 (FIX-12) ───────────────────────────────
echo ""
echo "── Phase 4/4: 前端补丁 ──"
if [ -n "$FRONTEND" ] && [ -d "$FRONTEND" ]; then
    RX_FILE="$FRONTEND/src/modules/rx/api/rxApi.ts"
    if [ -f "$RX_FILE" ]; then
        if grep -q "localStorage.getItem('access_token')" "$RX_FILE"; then
            cp "$RX_FILE" "$RX_FILE.bak.$TS"
            sed -i "s/localStorage.getItem('access_token')/localStorage.getItem('bos_access_token')  \/\/ FIX-12/g" "$RX_FILE"
            echo "  ✅ FIX-12: rxApi.ts Token Key 已修复"
        else
            echo "  ✓ FIX-12: rxApi.ts 已修复或无匹配"
        fi
    else
        echo "  ⚠ $RX_FILE 不存在"
    fi
else
    echo "  ⚠ 未提供前端目录, FIX-12 需手动修复:"
    echo "     文件: src/modules/rx/api/rxApi.ts 第51行"
    echo "     将 localStorage.getItem('access_token')"
    echo "     改为 localStorage.getItem('bos_access_token')"
fi

# ─── 验证 ──────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  验证检查"
echo "═══════════════════════════════════════════════════════════"

pass=0
fail=0

# 检查 12 个新模块
modules=(
    "rate_limiter.py"
    "security_middleware.py"
    "access_control.py"
    "token_blacklist_redis.py"
    "rate_limit_middleware.py"
    "token_storage.py"
    "legacy_auth_middleware.py"
    "log_sanitizer.py"
    "https_middleware.py"
    "public_id.py"
    "csrf_audit_middleware.py"
    "register_security.py"
)

for m in "${modules[@]}"; do
    if [ -f "$CORE_DIR/$m" ]; then
        pass=$((pass + 1))
    else
        echo "  ❌ core/$m 缺失"
        fail=$((fail + 1))
    fi
done

# 检查关键代码补丁
checks=(
    "CORS_ORIGINS:main.py:FIX-01 CORS白名单"
    "error_id:main.py:FIX-02 异常脱敏"
    "rate_limit_or_429:auth_api.py:FIX-03 Redis限流"
    "_validate_password_strength:auth_api.py:FIX-05 密码策略"
    "MAX_MINUTES_PER_EVENT:learning_api.py:FIX-06 时长上限"
    "docs_url=_docs_url:main.py:FIX-07 Swagger禁用"
)

for check in "${checks[@]}"; do
    IFS=: read -r pattern file desc <<< "$check"
    target="$BACKEND/$file"
    if [ -f "$target" ] && grep -q "$pattern" "$target" 2>/dev/null; then
        pass=$((pass + 1))
    else
        echo "  ⚠ $desc — 需手动检查 $file"
        fail=$((fail + 1))
    fi
done

echo ""
echo "  模块+补丁检查: $pass 通过, $fail 待确认"

# ─── 下一步 ────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  部署完成 — 下一步:"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  1. main.py 注册中间件 (在 CORS 之后添加):"
echo "     from core.register_security import register_all_security"
echo "     register_all_security(app)"
echo ""
echo "  2. 设置环境变量:"
echo "     export CORS_ORIGINS=https://app.xingjian.com"
echo "     export REDIS_URL=redis://:password@localhost:6379/0"
echo "     export ENVIRONMENT=production"
echo ""
echo "  3. 安装依赖:"
echo "     pip install redis"
echo ""
echo "  4. 数据库迁移:"
echo "     alembic upgrade head"
echo ""
echo "  5. 重启并验证:"
echo "     python pentest_bhp.py --base http://localhost:8000/api/v1"
echo ""
echo "═══════════════════════════════════════════════════════════"

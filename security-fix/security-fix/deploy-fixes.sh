#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# 安全修复部署脚本
# 用法: bash deploy-fixes.sh [后端项目根目录]
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

PROJECT="${1:-.}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "═══════════════════════════════════════"
echo "  安全修复部署"
echo "  目标: $(cd "$PROJECT" && pwd)"
echo "═══════════════════════════════════════"

# 1. 复制新模块到 core/
echo ""
echo "── 步骤 1: 复制新模块 ──"
for f in "$SCRIPT_DIR"/core/*.py; do
    fname=$(basename "$f")
    target="$PROJECT/core/$fname"
    if [ -f "$target" ]; then
        echo "  ⚠ $fname 已存在, 跳过"
    else
        cp "$f" "$target"
        echo "  ✅ core/$fname"
    fi
done

# 2. 运行自动补丁
echo ""
echo "── 步骤 2: 应用代码补丁 ──"
python3 "$SCRIPT_DIR/security_patches.py" "$PROJECT"

# 3. 添加 redis 依赖
echo ""
echo "── 步骤 3: 检查依赖 ──"
REQ="$PROJECT/requirements.txt"
if [ -f "$REQ" ]; then
    if ! grep -q "^redis" "$REQ"; then
        echo "redis>=5.0.0" >> "$REQ"
        echo "  ✅ 添加 redis 依赖"
    else
        echo "  ✓ redis 依赖已存在"
    fi
fi

# 4. 验证
echo ""
echo "── 步骤 4: 验证 ──"
cd "$PROJECT"

checks=(
    "core/rate_limiter.py"
    "core/security_middleware.py"
    "core/access_control.py"
    "core/token_blacklist_redis.py"
    "core/rate_limit_middleware.py"
)

all_ok=true
for check in "${checks[@]}"; do
    if [ -f "$check" ]; then
        echo "  ✅ $check"
    else
        echo "  ❌ $check 缺失"
        all_ok=false
    fi
done

# 检查关键补丁
if grep -q "CORS_ORIGINS" main.py 2>/dev/null; then
    echo "  ✅ FIX-01: CORS 白名单已应用"
else
    echo "  ⚠ FIX-01: 需手动检查 main.py CORS 配置"
fi

if grep -q "error_id" main.py 2>/dev/null; then
    echo "  ✅ FIX-02: 异常脱敏已应用"
else
    echo "  ⚠ FIX-02: 需手动检查异常处理"
fi

echo ""
echo "═══════════════════════════════════════"
if $all_ok; then
    echo "  ✅ 安全修复部署完成"
else
    echo "  ⚠ 部分修复需手动检查"
fi
echo ""
echo "  下一步:"
echo "  1. 设置环境变量: CORS_ORIGINS, REDIS_URL, ENVIRONMENT"
echo "  2. pip install redis"
echo "  3. 重启服务并运行渗透测试验证"
echo "═══════════════════════════════════════"

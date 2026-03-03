#!/usr/bin/env bash
# =================================================================
# BHP 行健平台 — 一键部署脚本 (Linux 服务器)
# 用法: bash deploy.sh [--skip-build] [--skip-migrate] [--skip-seed]
#
# 前置条件:
#   1. 已安装 Docker + Docker Compose v2
#   2. 已创建 .env.bhp (参考 .env.bhp.prod.example)
#   3. 可选: nginx/ssl/cert.pem + nginx/ssl/key.pem (HTTPS)
# =================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── 颜色输出 ──────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# ── 参数 ──────────────────────────────────────────────────────────
SKIP_BUILD=false
SKIP_MIGRATE=false
SKIP_SEED=false
for arg in "$@"; do
  case $arg in
    --skip-build)   SKIP_BUILD=true ;;
    --skip-migrate) SKIP_MIGRATE=true ;;
    --skip-seed)    SKIP_SEED=true ;;
  esac
done

# ── 前置检查 ──────────────────────────────────────────────────────
info "=== 行健平台部署脚本 ==="
info "目录: $SCRIPT_DIR"
info "时间: $(date '+%Y-%m-%d %H:%M:%S')"

command -v docker >/dev/null 2>&1 || error "未找到 docker，请先安装"

# Docker Compose v1/v2 兼容
DC="docker compose"
$DC version >/dev/null 2>&1 || DC="docker-compose"

[[ -f ".env.bhp" ]] || error ".env.bhp 不存在！请先: cp .env.bhp.prod.example .env.bhp && 填写配置"

# 检查关键密钥
JWT_CHECK=$(grep -E "^JWT_SECRET_KEY=" .env.bhp | cut -d= -f2- | tr -d '"')
[[ "$JWT_CHECK" == "CHANGE_ME"* || -z "$JWT_CHECK" ]] && \
  error "JWT_SECRET_KEY 未配置！请在 .env.bhp 中设置（生成命令: openssl rand -base64 48）"

# ── Step 1: Git 更新 ───────────────────────────────────────────────
info "Step 1: 拉取最新代码..."
git pull --ff-only || warn "git pull 失败，继续使用当前代码"

# ── Step 2: Docker 构建 ───────────────────────────────────────────
if [[ "$SKIP_BUILD" == false ]]; then
  info "Step 2: 构建 Docker 镜像 (app / worker / beat)..."
  $DC build --no-cache app worker beat
else
  info "Step 2: 跳过 Docker 构建 (--skip-build)"
fi

# ── Step 3: 启动基础设施 (db / redis / qdrant) ───────────────────
info "Step 3: 启动数据库和缓存服务..."
$DC up -d db redis qdrant

info "等待 PostgreSQL 就绪 (最多 60s)..."
for i in $(seq 1 30); do
  $DC exec -T db pg_isready -U bhp_user -d bhp_db 2>/dev/null && break
  sleep 2
done
$DC exec -T db pg_isready -U bhp_user -d bhp_db || error "PostgreSQL 启动超时"

# ── Step 4: 数据库迁移 ────────────────────────────────────────────
if [[ "$SKIP_MIGRATE" == false ]]; then
  info "Step 4: 执行数据库迁移 (alembic upgrade head)..."
  $DC run --rm --no-deps app alembic upgrade head
else
  info "Step 4: 跳过数据库迁移 (--skip-migrate)"
fi

# ── Step 5: 启动全部服务 ──────────────────────────────────────────
info "Step 5: 启动全部服务..."
$DC up -d

# ── Step 6: 等待 API 健康 ─────────────────────────────────────────
info "Step 6: 等待 API 健康检查 (最多 90s)..."
for i in $(seq 1 30); do
  curl -sf http://localhost:8000/api/v1/system/health >/dev/null 2>&1 && break
  sleep 3
done
curl -sf http://localhost:8000/api/v1/system/health >/dev/null 2>&1 \
  && info "API 已就绪" \
  || warn "API 健康检查超时，请检查: $DC logs app"

# ── Step 7: 种子数据 (首次部署) ─────────────────────────────────
if [[ "$SKIP_SEED" == false ]]; then
  if command -v node >/dev/null 2>&1 && [[ -f "seed-test-data.js" ]]; then
    info "Step 7: 写入种子数据..."
    node seed-test-data.js && info "seed-test-data 完成" || warn "seed-test-data 失败 (非首次可忽略)"
    node seed-health-review.js && info "seed-health-review 完成" || warn "seed-health-review 失败"
  else
    info "Step 7: 跳过种子数据 (node 未找到或文件不存在)"
  fi
else
  info "Step 7: 跳过种子数据 (--skip-seed)"
fi

# ── Step 8: 健康报告 ─────────────────────────────────────────────
info "Step 8: 健康报告..."
echo "────────────────────────────────────────"
curl -sf http://localhost:8000/api/v1/system/health 2>/dev/null | \
  python3 -m json.tool 2>/dev/null || \
  curl -sf http://localhost:8000/api/v1/system/health 2>/dev/null || \
  echo "(API 未响应)"
echo "────────────────────────────────────────"

# ── 前端合约检查 ──────────────────────────────────────────────────
CONTRACT=$(curl -sf http://localhost:8000/api/v1/system/routes/frontend-contract 2>/dev/null)
if [[ -n "$CONTRACT" ]]; then
  COVERAGE=$(echo "$CONTRACT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('coverage_pct','?'))" 2>/dev/null || echo "?")
  info "前端合约覆盖率: ${COVERAGE}%"
fi

# ── 完成 ──────────────────────────────────────────────────────────
info "=== 部署完成 ==="
echo ""
echo "  API 端点:   http://localhost:8000"
echo "  健康检查:   http://localhost:8000/api/v1/system/health"
echo "  路由审计:   http://localhost:8000/api/v1/system/routes"
echo "  前端合约:   http://localhost:8000/api/v1/system/routes/frontend-contract"
echo "  任务监控:   http://localhost:5555 (Flower)"
echo ""
echo "  日志查看:"
echo "    $DC logs -f app"
echo "    $DC logs -f worker"
echo ""
echo "  下次快速更新 (无需重建):"
echo "    git pull && $DC restart app worker beat"

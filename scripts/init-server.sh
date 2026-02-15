#!/bin/bash
# =============================================================
# BehaviorOS V4.0 — Server Initialization Script
# =============================================================
# Usage:
#   sudo bash scripts/init-server.sh <environment>
#
# Environments: staging | production
#
# Prerequisites:
#   - Ubuntu 22.04+ / Debian 12+
#   - Root or sudo access
#   - Internet connectivity
# =============================================================

set -euo pipefail

ENV="${1:-staging}"
APP_DIR="/opt/behaviros"
COMPOSE_APP="docker-compose.app.yaml"
COMPOSE_INFRA="docker-compose.yaml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# =============================================================
# 1. System Prerequisites
# =============================================================
info "=== BehaviorOS Init ($ENV) ==="
info "[1/7] Installing system prerequisites..."

apt-get update -qq
apt-get install -y -qq \
    curl wget git jq \
    apt-transport-https ca-certificates gnupg lsb-release \
    fail2ban ufw

# =============================================================
# 2. Docker
# =============================================================
info "[2/7] Setting up Docker..."

if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    info "Docker installed"
else
    info "Docker already installed: $(docker --version)"
fi

if ! command -v docker compose &>/dev/null; then
    error "docker compose plugin not found"
fi

# =============================================================
# 3. Application Directory
# =============================================================
info "[3/7] Setting up application directory..."

mkdir -p "$APP_DIR"/{logs,data,static,backups}

if [ ! -d "$APP_DIR/.git" ]; then
    warn "No git repo found at $APP_DIR"
    warn "Please clone the repo first: git clone <repo-url> $APP_DIR"
    warn "Or copy project files to $APP_DIR"
fi

cd "$APP_DIR"

# =============================================================
# 4. Environment Configuration
# =============================================================
info "[4/7] Configuring environment..."

if [ ! -f "$APP_DIR/.env" ]; then
    warn "No .env file found — creating from template"
    cat > "$APP_DIR/.env.app" << 'ENVEOF'
# BehaviorOS Application Environment
# ====================================
# Copy to .env and fill in values

# Database
DATABASE_URL=postgresql://bhp_user:bhp_password@localhost:5432/bhp_db

# JWT
JWT_SECRET_KEY=CHANGE_ME_TO_RANDOM_64_CHARS
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis
REDIS_URL=redis://localhost:6379/0

# Cloud LLM (optional)
CLOUD_LLM_PROVIDER=
CLOUD_LLM_API_KEY=
CLOUD_LLM_BASE_URL=https://api.deepseek.com/v1
CLOUD_LLM_MODEL=deepseek-chat
LLM_ROUTE_STRATEGY=cloud_first

# Safety
SAFETY_ENABLED=true

# Ollama (local fallback)
OLLAMA_API_URL=http://host.docker.internal:11434
ENVEOF
    info "Created .env.app template — edit before starting services"
fi

# =============================================================
# 5. Docker Network & Infrastructure
# =============================================================
info "[5/7] Starting infrastructure..."

# Create shared network if not exists
docker network create dify_dify-network 2>/dev/null || true

# Start infrastructure (PostgreSQL + Redis via Dify compose)
if [ -f "$COMPOSE_INFRA" ]; then
    docker compose -f "$COMPOSE_INFRA" up -d
    info "Infrastructure containers started"

    # Wait for PostgreSQL
    info "Waiting for PostgreSQL..."
    for i in $(seq 1 30); do
        if docker exec dify-db-1 pg_isready -U postgres &>/dev/null; then
            info "PostgreSQL ready"
            break
        fi
        sleep 2
    done
fi

# =============================================================
# 6. Database Setup
# =============================================================
info "[6/7] Setting up database..."

# Create BHP database if not exists
docker exec dify-db-1 psql -U postgres -tc \
    "SELECT 1 FROM pg_database WHERE datname = 'bhp_db'" | grep -q 1 || \
    docker exec dify-db-1 psql -U postgres -c "CREATE DATABASE bhp_db"

# Create user if not exists
docker exec dify-db-1 psql -U postgres -c \
    "DO \$\$ BEGIN
        IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'bhp_user') THEN
            CREATE ROLE bhp_user WITH LOGIN PASSWORD 'bhp_password';
        END IF;
    END \$\$;"
docker exec dify-db-1 psql -U postgres -c \
    "GRANT ALL PRIVILEGES ON DATABASE bhp_db TO bhp_user;"

# Enable pgvector extension
docker exec dify-db-1 psql -U postgres -d bhp_db -c \
    "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || true

info "Database configured"

# =============================================================
# 7. Build & Deploy Application
# =============================================================
info "[7/7] Building and deploying application..."

if [ -f "$COMPOSE_APP" ]; then
    docker compose -f "$COMPOSE_APP" build
    docker compose -f "$COMPOSE_APP" up -d
    info "Application containers started"

    # Run migrations
    sleep 5
    docker exec bhp-api python -m alembic upgrade head && \
        info "Migrations applied" || \
        warn "Migration failed — check manually"
fi

# =============================================================
# 8. Firewall (staging/production)
# =============================================================
if [ "$ENV" = "production" ]; then
    info "Configuring firewall for production..."
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
    info "Firewall configured (80/443 only)"
elif [ "$ENV" = "staging" ]; then
    info "Configuring firewall for staging..."
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw allow 8000/tcp   # API direct
    ufw allow 5173/tcp   # H5
    ufw allow 5174/tcp   # Admin
    ufw --force enable
    info "Firewall configured (80/443/8000/5173/5174)"
fi

# =============================================================
# Summary
# =============================================================
echo ""
echo "=========================================="
echo "  BehaviorOS V4.0 — $ENV initialized"
echo "=========================================="
echo ""
echo "  Services:"
echo "    API:           http://localhost:8000"
echo "    Admin Portal:  http://localhost:5174"
echo "    H5 Frontend:   http://localhost:5173"
echo "    API Docs:      http://localhost:8000/docs"
echo ""
echo "  Next steps:"
echo "    1. Edit .env with real credentials"
echo "    2. Configure GitHub Secrets for CI/CD"
echo "    3. Push to 'develop' branch for auto-deploy"
echo ""
echo "  Commands:"
echo "    make status    — Check container status"
echo "    make logs      — Tail API logs"
echo "    make test      — Run test suite"
echo "    make db-shell  — Open database shell"
echo "=========================================="

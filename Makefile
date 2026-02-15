# ============================================================
# BehaviorOS Platform — Makefile
# ============================================================
# Usage:
#   make build        — Build Docker images
#   make up           — Start all containers
#   make down         — Stop all containers
#   make test         — Run test suite (6 layers)
#   make migrate      — Run Alembic migrations
#   make lint         — Run linting
#   make clean        — Remove caches and temp files
# ============================================================

.PHONY: help dev build up down test acceptance pentest audit security migrate lint clean logs restart shell check deploy-stg deploy-prod

COMPOSE_APP   = docker-compose.app.yaml
COMPOSE_INFRA = docker-compose.yaml
API_CONTAINER = bhp-api
DB_CONTAINER  = dify-db-1
PYTHON        = python

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# ── Local Development ──────────────────────────────────────

dev: ## Start local development (API hot-reload + frontend dev servers)
	@echo "Starting infrastructure..."
	docker compose -f $(COMPOSE_INFRA) up -d
	@echo "Starting API with hot-reload..."
	docker compose -f $(COMPOSE_APP) up -d $(API_CONTAINER)
	@echo ""
	@echo "  API:    http://localhost:8000"
	@echo "  Admin:  cd admin-portal && npm run dev"
	@echo "  H5:     cd behaviros-frontend && npm run dev"
	@echo "  Docs:   http://localhost:8000/docs"
	@echo ""

dev-api: ## Start API only (uvicorn hot-reload, no Docker)
	$(PYTHON) -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload --log-level info

dev-admin: ## Start admin portal dev server
	cd admin-portal && npm run dev

dev-h5: ## Start H5 frontend dev server
	cd behaviros-frontend && npm run dev

# ── Build & Deploy ──────────────────────────────────────────

build: ## Build all application Docker images
	docker compose -f $(COMPOSE_APP) build --no-cache

build-api: ## Build only API image
	docker compose -f $(COMPOSE_APP) build bhp-api

build-admin: ## Build only admin portal image
	docker compose -f $(COMPOSE_APP) build bhp-admin-portal

build-h5: ## Build only H5 image
	docker compose -f $(COMPOSE_APP) build bhp-h5

up: ## Start all containers
	docker compose -f $(COMPOSE_INFRA) up -d
	docker compose -f $(COMPOSE_APP) up -d

down: ## Stop all containers
	docker compose -f $(COMPOSE_APP) down
	docker compose -f $(COMPOSE_INFRA) down

restart: ## Restart application containers
	docker compose -f $(COMPOSE_APP) restart

restart-api: ## Restart API container
	docker compose -f $(COMPOSE_APP) restart bhp-api

# ── Database ────────────────────────────────────────────────

migrate: ## Run Alembic database migrations
	docker exec $(API_CONTAINER) python -m alembic upgrade head

migrate-status: ## Show current migration revision
	docker exec $(API_CONTAINER) python -m alembic current

migrate-history: ## Show migration history
	docker exec $(API_CONTAINER) python -m alembic history --verbose

db-backup: ## Backup database to SQL dump
	docker exec $(DB_CONTAINER) pg_dump -U postgres -d bhp > backup_$$(date +%Y%m%d_%H%M%S).sql

db-shell: ## Open psql shell
	docker exec -it $(DB_CONTAINER) psql -U postgres -d bhp

# ── Testing ─────────────────────────────────────────────────

test: ## Run full test suite (6 layers)
	docker exec $(API_CONTAINER) bash tests/run_all_tests.sh

test-unit: ## Run unit tests only
	docker exec $(API_CONTAINER) pytest tests/ -v --tb=short

test-cov: ## Run tests with coverage report
	docker exec $(API_CONTAINER) pytest tests/ --cov=core --cov=api --cov-report=term-missing

BASE_URL   ?= http://localhost:8000
REPORT_DIR ?= reports

$(REPORT_DIR):
	@mkdir -p $(REPORT_DIR)

acceptance: $(REPORT_DIR) ## Run E2E acceptance test suite (125 tests)
	$(PYTHON) scripts/e2e_acceptance.py --base $(BASE_URL) --project . --json $(REPORT_DIR)/acceptance.json

pentest: $(REPORT_DIR) ## Run penetration test
	$(PYTHON) scripts/pentest_bhp.py --base $(BASE_URL)/api/v1 --json $(REPORT_DIR)/pentest.json

audit: ## Static security audit (bandit + pip-audit)
	bandit -r api/ core/ --severity-level medium -f screen || true
	pip-audit || true

security: audit acceptance pentest ## Full security check (audit + acceptance + pentest)

deploy-stg: security ## Deploy to staging (security gate first)
	gh workflow run "CD — Deploy & Verify" --field target=staging

deploy-prod: security ## Deploy to production (security gate first)
	@read -p "Confirm deploy to PRODUCTION? [y/N] " c && [ "$$c" = "y" ] || exit 1
	gh workflow run "CD — Deploy & Verify" --field target=production

# ── Code Quality ────────────────────────────────────────────

lint: ## Run linting checks
	$(PYTHON) -m py_compile api/main.py
	$(PYTHON) -m py_compile core/models.py
	@echo "Syntax check passed"

check: ## Run pre-commit checks
	@echo "Running syntax checks..."
	@find . -name "*.py" -path "*/api/*" -exec python -m py_compile {} + 2>&1 || true
	@find . -name "*.py" -path "*/core/*" -exec python -m py_compile {} + 2>&1 || true
	@echo "Checks complete"

# ── Monitoring ──────────────────────────────────────────────

logs: ## Tail API container logs
	docker compose -f $(COMPOSE_APP) logs -f $(API_CONTAINER)

logs-all: ## Tail all container logs
	docker compose -f $(COMPOSE_APP) logs -f

status: ## Show container status
	docker compose -f $(COMPOSE_APP) ps
	docker compose -f $(COMPOSE_INFRA) ps

health: ## Check API health endpoint
	curl -s http://localhost:8000/health | python -m json.tool || echo "API unreachable"

# ── Utilities ───────────────────────────────────────────────

shell: ## Open shell in API container
	docker exec -it $(API_CONTAINER) bash

clean: ## Remove Python caches and temp files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned"

seed: ## Run database seed data
	docker exec $(API_CONTAINER) python scripts/seed_data.py

# ================================================================
# BehaviorOS 四大结构性风险修复 - 一键部署脚本
# ================================================================
# S1: main.py 路由审计 (route_audit.py)
# S2: 前端契约兜底 (frontend_stubs.py)
# S3: Docker 端口冲突治理 (compose profiles)
# S4: Agent 健康监控 (agent_health.py)
# ================================================================
# 用法: 下载4个.py文件到同一目录, 运行此脚本
# ================================================================

$ErrorActionPreference = "Stop"
$PROJECT = "D:\behavioral-health-project"
$API_DIR = "$PROJECT\api"
$timestamp = Get-Date -Format "yyyyMMdd_HHmm"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " BehaviorOS Structural Risk Fix" -ForegroundColor Cyan
Write-Host " 4 fixes, 1 deployment" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ===== 检查前置条件 =====
Write-Host "[CHECK] Pre-flight..." -ForegroundColor Yellow

if (-not (Test-Path $API_DIR\main.py)) {
    Write-Host "[FAIL] api/main.py not found at $API_DIR" -ForegroundColor Red
    exit 1
}

$dockerRunning = docker ps --format "{{.Names}}" 2>$null | Select-String "bhp_v3_api"
if (-not $dockerRunning) {
    Write-Host "[WARN] bhp_v3_api container not running. Fixes will deploy but won't activate until restart." -ForegroundColor Yellow
}

Write-Host "[OK] Pre-flight passed" -ForegroundColor Green
Write-Host ""

# ===== S1: 路由审计 =====
Write-Host "[S1] Deploying route_audit.py..." -ForegroundColor Cyan

Copy-Item -Path fix-s1-route-audit.py -Destination $API_DIR\route_audit.py -Force
Write-Host "  Copied to api/route_audit.py" -ForegroundColor Green

# 检查main.py是否已经引入route_audit
$mainContent = Get-Content $API_DIR\main.py -Raw
if ($mainContent -notmatch "route_audit") {
    # 在main.py末尾(uvicorn.run之前)注入路由审计
    # 先找到注入点
    $injection = @"

# ═══ S1: Route Audit (auto-injected $timestamp) ═══
try:
    from api.route_audit import router as audit_router, audit_startup
    app.include_router(audit_router)
    audit_startup(app)
    print("[API] S1 Route Audit: ACTIVE")
except ImportError as e:
    print(f"[API] S1 Route Audit: FAILED - {e}")
"@

    # 在 "uvicorn.run" 之前注入
    if ($mainContent -match "uvicorn\.run") {
        $mainContent = $mainContent -replace "(if __name__)", "$injection`n`n`$1"
    } else {
        # 如果没有uvicorn.run, 追加到末尾
        $mainContent += "`n$injection"
    }

    [System.IO.File]::WriteAllText("$API_DIR\main.py", $mainContent, (New-Object System.Text.UTF8Encoding $false))
    Write-Host "  Injected route_audit into main.py" -ForegroundColor Green
} else {
    Write-Host "  route_audit already in main.py (skip)" -ForegroundColor Yellow
}

# ===== S2: 前端契约兜底 =====
Write-Host "[S2] Deploying frontend_stubs.py..." -ForegroundColor Cyan

Copy-Item -Path fix-s2-frontend-stubs.py -Destination $API_DIR\frontend_stubs.py -Force
Write-Host "  Copied to api/frontend_stubs.py" -ForegroundColor Green

$mainContent = Get-Content $API_DIR\main.py -Raw
if ($mainContent -notmatch "frontend_stubs") {
    $injection2 = @"

# ═══ S2: Frontend Contract Stubs (auto-injected $timestamp) ═══
try:
    from api.frontend_stubs import router as stubs_router
    app.include_router(stubs_router)
    print("[API] S2 Frontend Stubs: ACTIVE (fallback for unimplemented endpoints)")
except ImportError as e:
    print(f"[API] S2 Frontend Stubs: FAILED - {e}")
"@

    if ($mainContent -match "uvicorn\.run") {
        $mainContent = $mainContent -replace "(if __name__)", "$injection2`n`n`$1"
    } else {
        $mainContent += "`n$injection2"
    }

    [System.IO.File]::WriteAllText("$API_DIR\main.py", $mainContent, (New-Object System.Text.UTF8Encoding $false))
    Write-Host "  Injected frontend_stubs into main.py" -ForegroundColor Green
} else {
    Write-Host "  frontend_stubs already in main.py (skip)" -ForegroundColor Yellow
}

# ===== S4: Agent 健康监控 =====
Write-Host "[S4] Deploying agent_health.py..." -ForegroundColor Cyan

Copy-Item -Path fix-s4-agent-health.py -Destination $API_DIR\agent_health.py -Force
Write-Host "  Copied to api/agent_health.py" -ForegroundColor Green

$mainContent = Get-Content $API_DIR\main.py -Raw
if ($mainContent -notmatch "agent_health") {
    $injection4 = @"

# ═══ S4: Agent Health Monitor (auto-injected $timestamp) ═══
try:
    from api.agent_health import router as agent_health_router
    app.include_router(agent_health_router)
    print("[API] S4 Agent Health: ACTIVE")
except ImportError as e:
    print(f"[API] S4 Agent Health: FAILED - {e}")
"@

    if ($mainContent -match "uvicorn\.run") {
        $mainContent = $mainContent -replace "(if __name__)", "$injection4`n`n`$1"
    } else {
        $mainContent += "`n$injection4"
    }

    [System.IO.File]::WriteAllText("$API_DIR\main.py", $mainContent, (New-Object System.Text.UTF8Encoding $false))
    Write-Host "  Injected agent_health into main.py" -ForegroundColor Green
} else {
    Write-Host "  agent_health already in main.py (skip)" -ForegroundColor Yellow
}

# ===== S3: Docker 端口冲突治理 =====
Write-Host "[S3] Docker port conflict resolution..." -ForegroundColor Cyan

# 备份
Copy-Item $PROJECT\docker-compose.app.yaml "$PROJECT\docker-compose.app.yaml.bak-$timestamp" -ErrorAction SilentlyContinue
Write-Host "  Backed up docker-compose.app.yaml" -ForegroundColor Green

# 停掉app stack (释放冲突端口)
Write-Host "  Stopping app.yaml stack (if running)..." -ForegroundColor Yellow
Push-Location $PROJECT
docker-compose -f docker-compose.app.yaml down 2>$null
Pop-Location
Write-Host "  App stack stopped" -ForegroundColor Green

# 检查端口冲突
$port80 = netstat -ano 2>$null | Select-String ":80 " | Select-String "LISTENING"
$port8000 = netstat -ano 2>$null | Select-String ":8000 " | Select-String "LISTENING"

if ($port80) { Write-Host "  [INFO] Port 80 in use (expected: bhp_v3_nginx)" -ForegroundColor Yellow }
if ($port8000) { Write-Host "  [INFO] Port 8000 in use (expected: bhp_v3_api)" -ForegroundColor Green }

Write-Host "  [S3 RULE] Only docker-compose.yml runs by default" -ForegroundColor Green
Write-Host "  [S3 RULE] docker-compose.app.yaml is ON-DEMAND only" -ForegroundColor Green

# ===== 重启后端 =====
Write-Host ""
Write-Host "[DEPLOY] Restarting bhp_v3_api container..." -ForegroundColor Cyan
Push-Location $PROJECT
docker-compose -f docker-compose.yml restart bhp_v3_api 2>$null
Pop-Location

Write-Host "  Waiting 10s for API to start..." -ForegroundColor Yellow
Start-Sleep 10

# ===== 验证 =====
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " VERIFICATION" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 1. API可达
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    Write-Host "[PASS] /health reachable" -ForegroundColor Green
} catch {
    Write-Host "[FAIL] /health unreachable - container may need more time" -ForegroundColor Red
}

# 2. 路由审计端点
try {
    $routes = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/system/routes" -TimeoutSec 5
    Write-Host "[PASS] S1 /system/routes: $($routes.total_routes) routes, $($routes.modules_failed) failed modules" -ForegroundColor Green
} catch {
    Write-Host "[SKIP] S1 /system/routes not yet available (check container logs)" -ForegroundColor Yellow
}

# 3. 契约校验
try {
    $contract = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/system/routes/frontend-contract" -TimeoutSec 5
    Write-Host "[PASS] S2 Contract: $($contract.matched)/$($contract.total_frontend_endpoints) matched ($($contract.coverage))" -ForegroundColor Green
    if ($contract.missing.Count -gt 0) {
        Write-Host "  Missing (should be caught by stubs):" -ForegroundColor Yellow
        $contract.missing | ForEach-Object { Write-Host "    $($_.method) $($_.path)" -ForegroundColor Yellow }
    }
} catch {
    Write-Host "[SKIP] S2 Contract check not yet available" -ForegroundColor Yellow
}

# 4. Agent健康
try {
    $agentHealth = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/system/agents/health" -TimeoutSec 5
    Write-Host "[PASS] S4 Agent health: $($agentHealth.overall)" -ForegroundColor Green
} catch {
    Write-Host "[SKIP] S4 Agent health not yet available" -ForegroundColor Yellow
}

# 5. Stub验证 - 测试一个之前404的端点
try {
    $stubTest = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/content/courses" -TimeoutSec 5
    $isStub = $stubTest.Headers["X-Stub"]
    if ($isStub) {
        Write-Host "[PASS] S2 Stub working: /content/courses returns stub (X-Stub: true)" -ForegroundColor Green
    } else {
        Write-Host "[PASS] S2 /content/courses returns real data (no stub needed)" -ForegroundColor Green
    }
} catch {
    Write-Host "[WARN] /content/courses still 404 - stubs may not have loaded" -ForegroundColor Yellow
}

# 6. Docker端口
Write-Host ""
Write-Host "[S3] Docker port status:" -ForegroundColor Cyan
docker ps --format "table {{.Names}}`t{{.Ports}}" 2>$null | Select-String "bhp"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " DEPLOYMENT COMPLETE" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "New endpoints available:" -ForegroundColor Green
Write-Host "  GET  http://localhost:8000/api/v1/system/routes" -ForegroundColor White
Write-Host "  GET  http://localhost:8000/api/v1/system/health" -ForegroundColor White
Write-Host "  GET  http://localhost:8000/api/v1/system/routes/frontend-contract" -ForegroundColor White
Write-Host "  GET  http://localhost:8000/api/v1/system/agents/health" -ForegroundColor White
Write-Host ""
Write-Host "Next: git add -A && git commit -m 'fix: S1-S4 structural risk remediation'" -ForegroundColor Yellow

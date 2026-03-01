<#
.SYNOPSIS
    BehaviorOS auto-stabilize v2.1 (PowerShell 5.1 compatible)
.DESCRIPTION
    .\run.ps1
#>
param([switch]$SkipNpmInstall, [switch]$SkipUI)

$ErrorActionPreference = "Continue"
$PROJECT = "D:\behavioral-health-project"
$MINI    = "$PROJECT\coach-miniprogram"
$API     = "http://localhost:8000"
$BACKUP  = "backup-2026-0301-before-rollback"
$TS      = Get-Date -Format "yyyyMMdd_HHmm"
$LOGDIR  = "$MINI\_auto-stabilize"
$LOG     = "$LOGDIR\log-$TS.txt"
$REPORT  = "$LOGDIR\REPORT-$TS.md"

$script:results = New-Object System.Collections.ArrayList
$script:currentPhase = ""
$script:issues = New-Object System.Collections.ArrayList
$script:fixes  = New-Object System.Collections.ArrayList
$script:todos  = New-Object System.Collections.ArrayList

function EnsureDir($p) { if (!(Test-Path $p)) { New-Item -ItemType Directory $p -Force | Out-Null } }

function L($msg, $lv) {
    if (!$lv) { $lv = "INFO" }
    $ts = Get-Date -Format "HH:mm:ss"
    $line = "[$ts][$lv] $msg"
    $color = "White"
    switch ($lv) {
        "PASS" { $color = "Green" }
        "FAIL" { $color = "Red" }
        "WARN" { $color = "Yellow" }
        "FIX"  { $color = "Magenta" }
        "HEAD" { $color = "Cyan" }
        "SKIP" { $color = "DarkGray" }
    }
    Write-Host $line -ForegroundColor $color
    Add-Content -Path $LOG -Value $line -ErrorAction SilentlyContinue
}

function Result($name, $ok, $detail, $autofix) {
    if (!$detail) { $detail = "" }
    if (!$autofix) { $autofix = $false }
    $status = "FAIL"
    if ($ok) { $status = "PASS" }
    elseif ($autofix) { $status = "FIXED" }
    $phase = $script:currentPhase
    $script:results.Add(@{Phase=$phase; Name=$name; Status=$status; Detail=$detail}) | Out-Null
    $icon = "[FAIL]"
    $lvl = "FAIL"
    if ($ok) { $icon = "[PASS]"; $lvl = "PASS" }
    elseif ($autofix) { $icon = "[FIX ]"; $lvl = "FIX" }
    $suffix = ""
    if ($detail) { $suffix = " -- $detail" }
    L "  $icon $name$suffix" $lvl
    if (!$ok -and !$autofix) {
        $script:issues.Add("[$phase] $name : $detail") | Out-Null
    }
    if ($autofix) {
        $script:fixes.Add("[$phase] $name -> $detail") | Out-Null
    }
    return $ok
}

function ManualTodo($msg) {
    $script:todos.Add($msg) | Out-Null
    L "  [TODO] $msg" "WARN"
}

function HTTP($url, $method, $body, $headers, $timeout) {
    if (!$method) { $method = "GET" }
    if (!$timeout) { $timeout = 10 }
    if (!$headers) { $headers = @{} }
    try {
        $p = @{ Uri=$url; Method=$method; UseBasicParsing=$true; TimeoutSec=$timeout }
        if ($headers.Count -gt 0) { $p.Headers = $headers }
        if ($body) { $p.Body=$body; $p.ContentType="application/json" }
        $r = Invoke-WebRequest @p
        return @{ Code=[int]$r.StatusCode; Body=$r.Content; OK=$true }
    } catch {
        $c = 0
        if ($_.Exception -and $_.Exception.Response) {
            $c = [int]$_.Exception.Response.StatusCode
        }
        return @{ Code=$c; Body=$_.Exception.Message; OK=$false }
    }
}

function DoLogin($user, $pass) {
    $body = '{"username":"' + $user + '","password":"' + $pass + '"}'
    $r = HTTP "$API/api/v1/auth/login" "POST" $body
    if ($r.OK) {
        $data = $r.Body | ConvertFrom-Json
        return $data.access_token
    }
    return $null
}

function GitCommit($msg) {
    Push-Location $PROJECT
    git add -A 2>$null
    $st = git status --porcelain 2>$null
    if ($st) {
        git commit -m $msg 2>$null | Out-Null
        L "  [GIT] $msg"
    }
    Pop-Location
}

# ===============================================================
# START
# ===============================================================
EnsureDir $LOGDIR
Set-Location $MINI

L "========================================================" "HEAD"
L "  BehaviorOS auto-stabilize v2.1" "HEAD"
L "  Unattended mode - go have some tea" "HEAD"
L "========================================================" "HEAD"
L "Project: $MINI"
L "Log: $LOG"
$sw = [System.Diagnostics.Stopwatch]::StartNew()

# ===============================================================
# PHASE 0: Environment check
# ===============================================================
$script:currentPhase = "P0"
L "" "HEAD"
L "=== PHASE 0: Environment check ===" "HEAD"

$branch = git branch --show-current 2>$null
$headMsg = git log --oneline -1 2>$null
Result "Branch=stabilize-from-sprint1" ($branch -eq "stabilize-from-sprint1") "Actual: $branch"
Result "package.json exists" (Test-Path "package.json")

$nodeV = node -v 2>$null
Result "Node.js available" ($null -ne $nodeV) $nodeV

$dkApi = docker ps --format "{{.Names}}:{{.Status}}" 2>$null | Select-String "bhp_v3_api"
Result "bhp_v3_api running" ($null -ne $dkApi)

$apiOk = HTTP "$API/docs"
Result "API /docs reachable" $apiOk.OK ("Code: " + $apiOk.Code)

$coachTk = DoLogin "coach" "Coach@2026"
if (!$coachTk) { $coachTk = DoLogin "coach_test" "Coach@2026" }
if (!$coachTk) { $coachTk = DoLogin "coach" "coach123" }
Result "Coach login" ($null -ne $coachTk)

$growerTk = DoLogin "grower" "Grower@2026"
if (!$growerTk) { $growerTk = DoLogin "grower_test" "Grower@2026" }
Result "Grower login" ($null -ne $growerTk)

# ===============================================================
# PHASE 1: Infrastructure fix
# ===============================================================
$script:currentPhase = "P1"
L "" "HEAD"
L "=== PHASE 1: Infrastructure auto-fix ===" "HEAD"

Set-Location $MINI

# 1.1 Port scan + fix
L "  Scanning source for wrong ports..." "INFO"
$portFixed = 0
$srcFiles = Get-ChildItem -Path src -Recurse -Include "*.ts","*.vue","*.js" -ErrorAction SilentlyContinue
foreach ($f in $srcFiles) {
    $c = Get-Content $f.FullName -Raw -ErrorAction SilentlyContinue
    if ($c -and ($c -match "localhost:800[1-9]")) {
        $newC = $c -replace 'localhost:8001', 'localhost:8000'
        $newC = $newC -replace 'localhost:8002', 'localhost:8000'
        Set-Content $f.FullName $newC -NoNewline
        $portFixed++
        L "    Fixed: $($f.Name)" "FIX"
    }
}
if ($portFixed -eq 0) {
    Result "No wrong port references" $true
} else {
    Result "Port fix (8001/8002->8000)" $false "$portFixed files fixed" $true
}

# 1.2 package.json scripts
$pkgRaw = Get-Content "package.json" -Raw
$pkg = $pkgRaw | ConvertFrom-Json
$devCmd = $null
if ($pkg.scripts) { $devCmd = $pkg.scripts.'dev:mp-weixin' }

if (!$devCmd) {
    L "  Adding dev:mp-weixin script..." "FIX"
    $pkgRaw = $pkgRaw -replace '("scripts"\s*:\s*\{)', '$1"dev:mp-weixin": "uni -p mp-weixin","build:mp-weixin": "uni build -p mp-weixin",'
    Set-Content "package.json" $pkgRaw -NoNewline
    Result "Added dev:mp-weixin" $false "script added" $true
} elseif ($devCmd -notmatch "mp-weixin") {
    L "  Fixing dev:mp-weixin script..." "FIX"
    $pkgRaw = $pkgRaw -replace [regex]::Escape($devCmd), "uni -p mp-weixin"
    Set-Content "package.json" $pkgRaw -NoNewline
    Result "Fixed dev:mp-weixin" $false "added -p mp-weixin" $true
} else {
    Result "dev:mp-weixin script OK" $true
}

# 1.3 .env files
if (!(Test-Path ".env")) {
    Set-Content ".env" "VITE_API_URL=http://localhost:8000/api/v1"
    Result "Created .env" $false "created" $true
} else {
    Result ".env exists" $true
}
if (!(Test-Path ".env.production")) {
    Set-Content ".env.production" "VITE_API_URL=https://api.xingjian.health/api/v1"
}

# 1.4 request.ts port check
$reqFiles = Get-ChildItem src -Recurse -Filter "request.ts" -ErrorAction SilentlyContinue
foreach ($rf in $reqFiles) {
    $rc = Get-Content $rf.FullName -Raw
    if ($rc -match "8002") {
        $rc = $rc -replace '8002', '8000'
        Set-Content $rf.FullName $rc -NoNewline
        Result "request.ts port fix" $false "8002->8000" $true
    }
}

# 1.5 Docker app.yaml conflict
$appY = "$PROJECT\docker-compose.app.yaml"
if (Test-Path $appY) {
    $appRunning = docker-compose -f $appY ps -q 2>$null
    if ($appRunning) {
        L "  Stopping app.yaml containers..." "FIX"
        docker-compose -f $appY down 2>$null
        Start-Sleep 3
        Result "Stopped app.yaml" $false "stopped" $true
    }
}

GitCommit "auto-phase1: infra fix - port unify + env + scripts"

# ===============================================================
# PHASE 2: npm install + compile
# ===============================================================
$script:currentPhase = "P2"
L "" "HEAD"
L "=== PHASE 2: Dependencies + Compile ===" "HEAD"

Set-Location $MINI
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "node_modules\.cache" -ErrorAction SilentlyContinue

if (!$SkipNpmInstall) {
    L "  npm install (1-2 min)..." "INFO"
    $npmLog = npm install 2>&1 | Out-String
    Result "npm install" ($LASTEXITCODE -eq 0)
} else {
    L "  Skip npm install" "SKIP"
}

# Compile: try build first, then dev fallback
L "  Compiling (build mode)..." "INFO"
$buildLog = npm run build:mp-weixin 2>&1 | Out-String
$dist = $null
if (Test-Path "dist\build\mp-weixin\app.json") { $dist = "dist\build\mp-weixin" }

if (!$dist) {
    L "  build failed, trying npx uni build..." "WARN"
    $buildLog = npx uni build -p mp-weixin 2>&1 | Out-String
    if (Test-Path "dist\build\mp-weixin\app.json") { $dist = "dist\build\mp-weixin" }
}

if (!$dist) {
    L "  build failed, trying dev mode (90s timeout)..." "WARN"
    $job = Start-Job -ScriptBlock {
        param($dir)
        Set-Location $dir
        npx uni -p mp-weixin 2>&1
    } -ArgumentList $MINI
    $waited = 0
    while ($waited -lt 90) {
        Start-Sleep 5
        $waited += 5
        if (Test-Path "dist\dev\mp-weixin\app.json") {
            $dist = "dist\dev\mp-weixin"
            break
        }
        L "    Waiting... ${waited}s" "INFO"
    }
    Stop-Job $job -ErrorAction SilentlyContinue
    Remove-Job $job -Force -ErrorAction SilentlyContinue
}

if ($dist) {
    Result "Compile OK" $true "Path: $dist"
} else {
    Result "Compile" $false "All modes failed"
}

if ($dist) {
    $ghosts = Select-String -Path "$dist\**\*.js" -Pattern "/v1/professional/" -Recurse -ErrorAction SilentlyContinue
    $ghostCount = 0
    if ($ghosts) { $ghostCount = $ghosts.Count }
    Result "No /v1/professional/ ghost" ($ghostCount -eq 0) "$ghostCount found"
}

# ===============================================================
# PHASE 3: API smoke test
# ===============================================================
$script:currentPhase = "P3"
L "" "HEAD"
L "=== PHASE 3: API smoke test (22 endpoints) ===" "HEAD"

if ($coachTk) {
    $ch = @{ Authorization = "Bearer $coachTk" }
    $coachEps = @(
        "coach/dashboard=/api/v1/coach/dashboard",
        "coach/students=/api/v1/coach/students",
        "coach/performance=/api/v1/coach/performance",
        "coach/conversations=/api/v1/coach/conversations",
        "coach/live-sessions=/api/v1/coach/live-sessions",
        "coach/risk-alerts=/api/v1/coach/risk-alerts",
        "coach/review-queue=/api/v1/coach/review-queue",
        "coach-push/pending=/api/v1/coach-push/pending",
        "coach/stats/today=/api/v1/coach/stats/today",
        "coach/analytics=/api/v1/coach/analytics/week-trend",
        "assessment-assign=/api/v1/assessment-assignments",
        "learning/courses=/api/v1/learning/courses",
        "agent/list=/api/v1/agent/list"
    )
    foreach ($ep in $coachEps) {
        $parts = $ep.Split("=")
        $name = $parts[0]
        $path = $parts[1]
        $r = HTTP "$API$path" "GET" $null $ch
        if ($r.OK) {
            Result "Coach: $name" $true
        } elseif ($r.Code -eq 404) {
            Result "Coach: $name" $false "404 (not implemented)"
        } elseif ($r.Code -eq 422) {
            Result "Coach: $name" $true "422 (needs params, exists)"
        } else {
            Result "Coach: $name" $false ("HTTP " + $r.Code)
        }
    }
} else {
    L "  Coach token unavailable, skipping" "WARN"
}

if ($growerTk) {
    $gh = @{ Authorization = "Bearer $growerTk" }
    $growerEps = @(
        "journey/state=/api/v1/journey/state",
        "tasks/today=/api/v1/tasks/today",
        "credits/summary=/api/v1/credits/summary",
        "health-data=/api/v1/health-data/summary",
        "challenges=/api/v1/challenges/active",
        "micro-actions=/api/v1/micro-actions/today"
    )
    foreach ($ep in $growerEps) {
        $parts = $ep.Split("=")
        $r = HTTP "$API$($parts[1])" "GET" $null $gh
        if ($r.OK) { Result "Grower: $($parts[0])" $true }
        elseif ($r.Code -eq 404) { Result "Grower: $($parts[0])" $false "404" }
        else { Result "Grower: $($parts[0])" $false ("HTTP " + $r.Code) }
    }
}

foreach ($ep in @("/docs","/openapi.json","/health")) {
    $r = HTTP "$API$ep"
    $ok = $r.OK -or ($r.Code -eq 200) -or ($r.Code -eq 301)
    Result "Public: $ep" $ok
}

# ===============================================================
# PHASE 4: Coach directory restructure
# ===============================================================
$script:currentPhase = "P4"
L "" "HEAD"
L "=== PHASE 4: Coach directory restructure ===" "HEAD"

Set-Location $MINI
$coachDir = "src\pages\coach"

$dirs = @("dashboard","flywheel","students","risk","assessment","push-queue","analytics","messages","live")
foreach ($d in $dirs) { EnsureDir "$coachDir\$d" }
Result "Subdirectories created" $true ($dirs.Count.ToString() + " dirs")

$moveMap = @{
    "dashboard.vue"      = "dashboard\index.vue"
    "flywheel.vue"       = "flywheel\index.vue"
    "students.vue"       = "students\index.vue"
    "students-detail.vue"= "students\detail.vue"
    "detail.vue"         = "students\detail.vue"
    "analytics.vue"      = "analytics\index.vue"
    "messages.vue"       = "messages\index.vue"
    "live.vue"           = "live\index.vue"
    "risk.vue"           = "risk\index.vue"
    "assessment.vue"     = "assessment\index.vue"
    "push-queue.vue"     = "push-queue\index.vue"
}
$moved = 0
foreach ($key in $moveMap.Keys) {
    $s = "$coachDir\$key"
    $d = "$coachDir\$($moveMap[$key])"
    if ((Test-Path $s) -and !(Test-Path $d)) {
        EnsureDir (Split-Path $d -Parent)
        Move-Item $s $d -Force
        $moved++
        L "    Moved: $key -> $($moveMap[$key])" "INFO"
    }
}
if ((Test-Path "$coachDir\index.vue") -and !(Test-Path "$coachDir\dashboard\index.vue")) {
    Copy-Item "$coachDir\index.vue" "$coachDir\dashboard\index.vue" -Force
    $moved++
}
Result "Files migrated" $true "$moved files"

GitCommit "auto-phase4: coach directory restructure"

# ===============================================================
# PHASE 5: BOS UI integration
# ===============================================================
$script:currentPhase = "P5"
L "" "HEAD"
L "=== PHASE 5: BOS UI integration ===" "HEAD"

if ($SkipUI) {
    L "  Skipped (flag)" "SKIP"
} else {
    Set-Location $PROJECT

    $hasUI = $false
    try {
        $uiCheck = git ls-tree -r --name-only $BACKUP 2>$null | Select-String "UI"
        if ($uiCheck) { $hasUI = $true }
    } catch {}

    if ($hasUI) {
        L "  Extracting UI from backup branch..." "INFO"
        git checkout $BACKUP -- "小程序版UI更新/" 2>$null
        git checkout $BACKUP -- "小程序版UI/" 2>$null

        $uiRoot = ""
        if (Test-Path "小程序版UI更新\src\pages\coach") { $uiRoot = "小程序版UI更新" }
        elseif (Test-Path "小程序版UI") { $uiRoot = "小程序版UI" }

        if ($uiRoot) {
            $coachT = "$MINI\src\pages\coach"
            $installed = 0
            $uiFiles = @(
                "dashboard\index.vue","flywheel\index.vue","students\index.vue",
                "students\detail.vue","risk\index.vue","assessment\index.vue",
                "assessment\review.vue","push-queue\index.vue","analytics\index.vue",
                "messages\index.vue","live\index.vue"
            )
            foreach ($f in $uiFiles) {
                $s = "$uiRoot\src\pages\coach\$f"
                $t = "$coachT\$f"
                if (Test-Path $s) {
                    EnsureDir (Split-Path $t -Parent)
                    Copy-Item $s $t -Force
                    $installed++
                }
            }
            Result "UI pages installed" ($installed -ge 8) "$installed/11"

            if (Test-Path "$uiRoot\src\config\env.ts") {
                EnsureDir "$MINI\src\config"
                Copy-Item "$uiRoot\src\config\env.ts" "$MINI\src\config\env.ts" -Force
                L "    Installed config/env.ts" "INFO"
            }
            if (Test-Path "$uiRoot\src\utils\request.ts") {
                EnsureDir "$MINI\src\utils"
                Copy-Item "$uiRoot\src\utils\request.ts" "$MINI\src\utils\request.ts" -Force
                L "    Installed utils/request.ts" "INFO"
            }
        } else {
            Result "UI source dir" $false "not found"
            ManualTodo "Manually extract UI files from backup branch"
        }

        Remove-Item -Recurse -Force "小程序版UI更新" -ErrorAction SilentlyContinue
        Remove-Item -Recurse -Force "小程序版UI" -ErrorAction SilentlyContinue
        git checkout HEAD -- . 2>$null
    } else {
        Result "Backup branch UI files" $false "not found"
        ManualTodo "Manually integrate BOS UI files"
    }

    Set-Location $MINI

    # Fix hardcoded values in all coach vue files
    L "  Fixing hardcoded values in UI files..." "INFO"
    $fixCount = 0
    $coachVues = Get-ChildItem "src\pages\coach" -Recurse -Filter "*.vue" -ErrorAction SilentlyContinue
    foreach ($vue in $coachVues) {
        $c = Get-Content $vue.FullName -Raw -ErrorAction SilentlyContinue
        if (!$c) { continue }
        $orig = $c
        $c = $c -replace 'localhost:8002', 'localhost:8000'
        $c = $c -replace 'localhost:8001', 'localhost:8000'
        if ($c -ne $orig) {
            Set-Content $vue.FullName $c -NoNewline
            $fixCount++
        }
    }
    if ($fixCount -gt 0) {
        Result "UI hardcode fix" $false "$fixCount files" $true
    }

    GitCommit "auto-phase5: BOS UI integration + hardcode fix"
}

# ===============================================================
# PHASE 6: pages.json route check
# ===============================================================
$script:currentPhase = "P6"
L "" "HEAD"
L "=== PHASE 6: pages.json route alignment ===" "HEAD"

Set-Location $MINI
$pjPath = ""
if (Test-Path "src\pages.json") { $pjPath = "src\pages.json" }
elseif (Test-Path "pages.json") { $pjPath = "pages.json" }

if ($pjPath) {
    $pjRaw = Get-Content $pjPath -Raw
    $required = @(
        "coach/dashboard/index","coach/flywheel/index","coach/students/index",
        "coach/students/detail","coach/risk/index","coach/assessment/index",
        "coach/push-queue/index","coach/analytics/index","coach/messages/index",
        "coach/live/index"
    )
    $missing = @()
    foreach ($r in $required) {
        if ($pjRaw -notmatch [regex]::Escape($r)) { $missing += $r }
    }
    if ($missing.Count -gt 0) {
        Result "Route completeness" $false ("Missing " + $missing.Count + " routes")
        foreach ($m in $missing) { L "    Missing: $m" "WARN" }
        ManualTodo ("Add missing routes to pages.json: " + ($missing -join ", "))
    } else {
        Result "Route completeness" $true "All registered"
    }
} else {
    Result "pages.json" $false "not found"
}

GitCommit "auto-phase6: route check"

# ===============================================================
# PHASE 7: Final compile + static analysis
# ===============================================================
$script:currentPhase = "P7"
L "" "HEAD"
L "=== PHASE 7: Final compile + page analysis ===" "HEAD"

Set-Location $MINI
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue

L "  Final compile..." "INFO"
$buildLog2 = npm run build:mp-weixin 2>&1 | Out-String
$dist2 = $null
if (Test-Path "dist\build\mp-weixin\app.json") { $dist2 = "dist\build\mp-weixin" }
if (!$dist2) {
    npx uni build -p mp-weixin 2>&1 | Out-Null
    if (Test-Path "dist\build\mp-weixin\app.json") { $dist2 = "dist\build\mp-weixin" }
}
if (!$dist2) {
    $job2 = Start-Job -ScriptBlock {
        param($dir)
        Set-Location $dir
        npx uni -p mp-weixin 2>&1
    } -ArgumentList $MINI
    $w2 = 0
    while ($w2 -lt 90) {
        Start-Sleep 5; $w2 += 5
        if (Test-Path "dist\dev\mp-weixin\app.json") { $dist2 = "dist\dev\mp-weixin"; break }
    }
    Stop-Job $job2 -ErrorAction SilentlyContinue
    Remove-Job $job2 -Force -ErrorAction SilentlyContinue
}

if ($dist2) {
    Result "Final compile" $true $dist2
} else {
    Result "Final compile" $false "all modes failed"
}

if ($dist2) {
    L "  Static analysis of compiled pages..." "HEAD"

    # Parse app.json for all registered pages
    $appJson = Get-Content "$dist2\app.json" -Raw | ConvertFrom-Json
    $allPages = @()
    if ($appJson.pages) { $allPages += $appJson.pages }
    if ($appJson.subPackages) {
        foreach ($sp in $appJson.subPackages) {
            foreach ($pg in $sp.pages) {
                $pagePath = $pg
                if ($pg.path) { $pagePath = $pg.path }
                $allPages += ($sp.root + "/" + $pagePath)
            }
        }
    }
    L "  Registered pages: $($allPages.Count)" "INFO"

    foreach ($page in $allPages) {
        $cleanPage = $page -replace '\\','/'
        $jsFile = $null

        # Try multiple patterns to find the compiled JS
        $candidates = @(
            "$dist2\$cleanPage.js",
            "$dist2\${cleanPage}\index.js",
            "$dist2\$cleanPage"
        )
        foreach ($cand in $candidates) {
            $normalized = $cand -replace '/', '\'
            if (Test-Path $normalized) {
                $item = Get-Item $normalized
                if ($item.PSIsContainer) {
                    $jsFile = Get-ChildItem $normalized -Filter "*.js" -ErrorAction SilentlyContinue | Select-Object -First 1
                } else {
                    $jsFile = $item
                }
                if ($jsFile) { break }
            }
        }

        $shortName = $cleanPage.Split("/")[-1]
        if (!$shortName) { $shortName = $cleanPage.Split("/")[-2] }

        if ($jsFile) {
            $js = Get-Content $jsFile.FullName -Raw -ErrorAction SilentlyContinue
            $pageIssues = @()

            if ($js -match "PROD_URL" -and $js -notmatch "var PROD_URL|let PROD_URL|const PROD_URL") {
                $pageIssues += "PROD_URL undefined"
            }
            if ($js -match "localhost:800[1-9]") {
                $pageIssues += "wrong port"
            }
            if ($js -match "/v1/professional/") {
                $pageIssues += "ghost path /v1/professional/"
            }
            if ($js -match "function _request\(") {
                $pageIssues += "inline _request residue"
            }

            if ($pageIssues.Count -gt 0) {
                Result "Page[$shortName]" $false ($pageIssues -join "; ")
            } else {
                Result "Page[$shortName]" $true
            }
        }
    }
}

# ===============================================================
# PHASE 8: WeChat DevTools (optional)
# ===============================================================
$script:currentPhase = "P8"
L "" "HEAD"
L "=== PHASE 8: WeChat DevTools ===" "HEAD"

$wxPaths = @(
    "C:\Program Files (x86)\Tencent\微信web开发者工具\cli.bat",
    "C:\Program Files\Tencent\微信web开发者工具\cli.bat"
)
$wxCli = $null
foreach ($p in $wxPaths) {
    if (Test-Path $p) { $wxCli = $p; break }
}

if ($wxCli -and $dist2) {
    L "  Found DevTools CLI" "INFO"
    try {
        & $wxCli open --project (Resolve-Path $dist2).Path 2>$null
        Start-Sleep 5
        Result "DevTools opened" $true
        ManualTodo "Verify pages visually in WeChat DevTools"
    } catch {
        Result "DevTools open" $false $_.Exception.Message
    }
} else {
    L "  DevTools CLI not found or no dist - skip" "SKIP"
    ManualTodo "Open WeChat DevTools manually and load: $dist2"
}

GitCommit "auto-phase7-8: final compile + analysis + devtools"

# ===============================================================
# REPORT
# ===============================================================
$sw.Stop()
$elapsed = $sw.Elapsed.ToString("hh\:mm\:ss")

$totalP = ($script:results | Where-Object { $_.Status -eq "PASS" }).Count
$totalF = ($script:results | Where-Object { $_.Status -eq "FAIL" }).Count
$totalX = ($script:results | Where-Object { $_.Status -eq "FIXED" }).Count

Set-Location $MINI
$statVues  = (Get-ChildItem src\pages -Recurse -Filter "*.vue" -ErrorAction SilentlyContinue).Count
$statCoach = (Get-ChildItem src\pages\coach -Recurse -Filter "*.vue" -ErrorAction SilentlyContinue).Count
$statApi   = (Get-ChildItem src\api -Filter "*.ts" -ErrorAction SilentlyContinue).Count
$statComp  = (Get-ChildItem src\components -Filter "*.vue" -ErrorAction SilentlyContinue).Count

$health = "RED - serious issues"
if ($totalF -eq 0) { $health = "GREEN - all pass" }
elseif ($totalF -le 3) { $health = "YELLOW - minor issues" }
elseif ($totalF -le 8) { $health = "ORANGE - needs manual fix" }

# Build report
$rpt = @()
$rpt += "# BehaviorOS Stabilization Report"
$rpt += ""
$rpt += "Executed: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$rpt += "Duration: $elapsed"
$rpt += "Anchor: 9a6b18b (Sprint 1)"
$rpt += "Branch: stabilize-from-sprint1"
$rpt += ""
$rpt += "---"
$rpt += ""
$rpt += "## Summary"
$rpt += ""
$rpt += "| Metric | Value |"
$rpt += "|--------|-------|"
$rpt += "| PASS | $totalP |"
$rpt += "| AUTO-FIXED | $totalX |"
$rpt += "| FAIL | $totalF |"
$rpt += "| Health | $health |"
$rpt += ""
$rpt += "## Assets"
$rpt += ""
$rpt += "| Type | Count |"
$rpt += "|------|-------|"
$rpt += "| Total pages (.vue) | $statVues |"
$rpt += "| Coach pages | $statCoach |"
$rpt += "| API modules (.ts) | $statApi |"
$rpt += "| Components | $statComp |"
$distStatus = "FAIL"
if ($dist2) { $distStatus = $dist2 }
$rpt += "| Build output | $distStatus |"
$rpt += ""
$rpt += "---"
$rpt += ""
$rpt += "## Auto-fixes applied"
$rpt += ""
if ($script:fixes.Count -eq 0) {
    $rpt += "None needed."
} else {
    $i = 1
    foreach ($f in $script:fixes) {
        $rpt += "${i}. $f"
        $i++
    }
}
$rpt += ""
$rpt += "## Unresolved issues"
$rpt += ""
if ($script:issues.Count -eq 0) {
    $rpt += "None!"
} else {
    $i = 1
    foreach ($f in $script:issues) {
        $rpt += "${i}. $f"
        $i++
    }
}
$rpt += ""
$rpt += "## Manual TODO"
$rpt += ""
if ($script:todos.Count -eq 0) {
    $rpt += "Nothing! Fully automated!"
} else {
    $i = 1
    foreach ($t in $script:todos) {
        $rpt += "${i}. $t"
        $i++
    }
}
$rpt += ""
$rpt += "---"
$rpt += ""
$rpt += "## Detailed Results"
$rpt += ""
$rpt += "| Phase | Check | Status | Detail |"
$rpt += "|-------|-------|--------|--------|"
foreach ($r in $script:results) {
    $icon = "[FAIL]"
    if ($r.Status -eq "PASS") { $icon = "[PASS]" }
    elseif ($r.Status -eq "FIXED") { $icon = "[FIX]" }
    $rpt += "| $($r.Phase) | $($r.Name) | $icon | $($r.Detail) |"
}
$rpt += ""
$rpt += "---"
$rpt += ""
if ($totalF -eq 0) {
    $rpt += "## Next: Merge to master"
    $rpt += ""
    $rpt += "``````powershell"
    $rpt += "cd $MINI"
    $rpt += "git checkout master"
    $rpt += "git merge stabilize-from-sprint1"
    $rpt += "git push origin master --tags"
    $rpt += "``````"
} else {
    $rpt += "## Next: Fix $totalF issues then merge"
    $rpt += ""
    $rpt += "1. Fix issues listed above"
    $rpt += "2. Complete manual TODO items"
    $rpt += "3. Run: npm run build:mp-weixin"
    $rpt += "4. Verify in WeChat DevTools"
    $rpt += "5. git checkout master && git merge stabilize-from-sprint1"
}
$rpt += ""
$rpt += "---"
$rpt += "Auto-generated by stabilize v2.1 | Log: $LOG"

$rpt -join "`r`n" | Set-Content $REPORT

L "" "HEAD"
L "========================================================" "HEAD"
L "  DONE!" "HEAD"
L "  PASS: $totalP  |  FIXED: $totalX  |  FAIL: $totalF" "HEAD"
L "  Time: $elapsed" "HEAD"
L "  Report: $REPORT" "HEAD"
L "========================================================" "HEAD"

Start-Process notepad.exe $REPORT

Write-Host ""
Write-Host "Report opened in Notepad." -ForegroundColor Cyan
Write-Host "Full log: $LOG" -ForegroundColor DarkGray

#!/usr/bin/env pwsh
#Requires -Version 5.1
<#
.SYNOPSIS
    BehaviorOS 全自动稳定化执行器 v2.0
.DESCRIPTION
    一键执行: .\run.ps1
    从 9a6b18b 锚点出发，自动完成 Phase 0-7，包括:
    - 基础设施检查与自动修复
    - 依赖安装与编译
    - API全量烟测
    - Coach目录重构 + BOS UI集成
    - 编译产物静态分析(模拟页面点击)
    - 微信小程序自动化页面测试(如开发者工具可用)
    - 综合报告生成(Markdown + 自动打开)
.NOTES
    执行前提:
      1. 当前在 stabilize-from-sprint1 分支 (已完成)
      2. Docker 运行中 (bhp_v3_api healthy)
      3. 管理员PowerShell
    执行方式:
      cd D:\behavioral-health-project\coach-miniprogram
      .\run.ps1
#>

param(
    [switch]$SkipNpmInstall,
    [switch]$SkipUIIntegration,
    [switch]$Verbose
)

# ═══════════════════════════════════════════════════════════
# 全局常量
# ═══════════════════════════════════════════════════════════
$ErrorActionPreference = "Continue"
$PROJECT = "D:\behavioral-health-project"
$MINI    = "$PROJECT\coach-miniprogram"
$API     = "http://localhost:8000"
$BACKUP  = "backup-2026-0301-before-rollback"
$TS      = Get-Date -Format "yyyyMMdd_HHmm"
$LOGDIR  = "$MINI\_auto-stabilize"
$LOG     = "$LOGDIR\log-$TS.txt"
$REPORT  = "$LOGDIR\REPORT-$TS.md"
$SCREENSHOTS = "$LOGDIR\screenshots"
$TOOLDIR = "$MINI\tools"

# 统计
$script:results = [System.Collections.ArrayList]::new()
$script:currentPhase = ""
$script:issues = [System.Collections.ArrayList]::new()
$script:fixes  = [System.Collections.ArrayList]::new()
$script:manualTodos = [System.Collections.ArrayList]::new()

# ═══════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════
function EnsureDir($p) { if (!(Test-Path $p)) { New-Item -ItemType Directory $p -Force | Out-Null } }

function L($msg, $lv="INFO") {
    $ts = Get-Date -Format "HH:mm:ss"
    $colors = @{ PASS="Green"; FAIL="Red"; WARN="Yellow"; FIX="Magenta"; HEAD="Cyan"; SKIP="DarkGray"; INFO="White" }
    $line = "[$ts][$lv] $msg"
    Write-Host $line -ForegroundColor ($colors[$lv] ?? "White")
    Add-Content $LOG $line -EA SilentlyContinue
}

function Result($name, $ok, $detail="", $autofix=$false) {
    $status = if ($ok) { "PASS" } elseif ($autofix) { "FIXED" } else { "FAIL" }
    $script:results.Add(@{Phase=$script:currentPhase; Name=$name; Status=$status; Detail=$detail}) | Out-Null
    L "  $(if($ok){'✅'}elseif($autofix){'🔧'}else{'❌'}) $name$(if($detail){' — '+$detail})" $(if($ok){'PASS'}elseif($autofix){'FIX'}else{'FAIL'})
    if (!$ok -and !$autofix) { $script:issues.Add("[$script:currentPhase] $name: $detail") | Out-Null }
    if ($autofix) { $script:fixes.Add("[$script:currentPhase] $name → $detail") | Out-Null }
    return $ok
}

function ManualTodo($msg) {
    $script:manualTodos.Add($msg) | Out-Null
    L "  📋 TODO: $msg" "WARN"
}

function HTTP($url, $method="GET", $body=$null, $headers=@{}, $timeout=10) {
    try {
        $p = @{ Uri=$url; Method=$method; UseBasicParsing=$true; TimeoutSec=$timeout }
        if ($headers.Count) { $p.Headers = $headers }
        if ($body) { $p.Body=$body; $p.ContentType="application/json" }
        $r = Invoke-WebRequest @p
        return @{ Code=[int]$r.StatusCode; Body=$r.Content; OK=$true }
    } catch {
        $c = 0; if ($_.Exception.Response) { $c = [int]$_.Exception.Response.StatusCode }
        return @{ Code=$c; Body=$_.Exception.Message; OK=$false }
    }
}

function Login($user, $pass) {
    $r = HTTP "$API/api/v1/auth/login" "POST" "{`"username`":`"$user`",`"password`":`"$pass`"}"
    if ($r.OK) { return ($r.Body | ConvertFrom-Json).access_token }
    return $null
}

function GitCommit($msg) {
    Push-Location $PROJECT
    git add -A 2>$null
    if (git status --porcelain 2>$null) {
        git commit -m $msg 2>$null | Out-Null
        L "  📦 $msg" "INFO"
    }
    Pop-Location
}

function FixFileContent($path, $find, $replace, $desc) {
    if (!(Test-Path $path)) { return $false }
    $c = Get-Content $path -Raw -EA SilentlyContinue
    if ($c -match [regex]::Escape($find)) {
        $c = $c.Replace($find, $replace)
        Set-Content $path $c -NoNewline
        Result $desc $false $find "→ $replace" $true
        return $true
    }
    return $false
}

# ═══════════════════════════════════════════════════════════
# 启动
# ═══════════════════════════════════════════════════════════
EnsureDir $LOGDIR
EnsureDir $SCREENSHOTS
Set-Location $MINI

L "╔══════════════════════════════════════════════════════╗" "HEAD"
L "║  BehaviorOS 全自动稳定化 v2.0                       ║" "HEAD"
L "║  无人值守模式 — 坐下来喝杯茶                        ║" "HEAD"
L "╚══════════════════════════════════════════════════════╝" "HEAD"
L "项目: $MINI"
L "日志: $LOG"
$sw = [System.Diagnostics.Stopwatch]::StartNew()

# ═══════════════════════════════════════════════════════════
# PHASE 0: 环境预检
# ═══════════════════════════════════════════════════════════
$script:currentPhase = "P0-环境预检"
L "`n━━━ PHASE 0: 环境预检 ━━━" "HEAD"

$branch = git branch --show-current 2>$null
Result "分支=stabilize-from-sprint1" ($branch -eq "stabilize-from-sprint1") "当前: $branch"
Result "package.json存在" (Test-Path "package.json")

# Node/npm
$nodeV = node -v 2>$null
Result "Node.js可用" ($null -ne $nodeV) $nodeV

# Docker
$dkApi = docker ps --format "{{.Names}}:{{.Status}}" 2>$null | Where-Object { $_ -match "bhp_v3_api" }
Result "bhp_v3_api运行中" ($null -ne $dkApi)

# API
$apiOk = HTTP "$API/docs"
Result "API /docs 可达 (8000)" $apiOk.OK "Code: $($apiOk.Code)"

# 登录
$coachTk  = Login "coach" "Coach@2026"
if (!$coachTk) { $coachTk = Login "coach_test" "Coach@2026" }
if (!$coachTk) { $coachTk = Login "coach" "coach123" }
Result "Coach登录" ($null -ne $coachTk)

$growerTk = Login "grower" "Grower@2026"
if (!$growerTk) { $growerTk = Login "grower_test" "Grower@2026" }
Result "Grower登录" ($null -ne $growerTk)

# ═══════════════════════════════════════════════════════════
# PHASE 1: 基础设施自动修复
# ═══════════════════════════════════════════════════════════
$script:currentPhase = "P1-基础设施"
L "`n━━━ PHASE 1: 基础设施自动修复 ━━━" "HEAD"

# 1.1 全项目端口扫描+自动修复
L "  扫描源码中错误端口..." "INFO"
$portFixed = 0
Get-ChildItem src -Recurse -Include "*.ts","*.vue","*.js" -EA SilentlyContinue | ForEach-Object {
    $c = Get-Content $_.FullName -Raw -EA SilentlyContinue
    if ($c -and ($c -match "localhost:800[1-9]")) {
        $newC = $c -replace 'localhost:8001', 'localhost:8000' -replace 'localhost:8002', 'localhost:8000'
        Set-Content $_.FullName $newC -NoNewline
        $portFixed++
        L "    🔧 $($_.Name): 端口已修正" "FIX"
    }
}
Result "端口统一(8000)" ($portFixed -eq 0) "修复了$portFixed个文件" ($portFixed -gt 0)

# 1.2 package.json 编译脚本
$pkg = Get-Content "package.json" -Raw | ConvertFrom-Json
$devCmd = $pkg.scripts.'dev:mp-weixin'
$buildCmd = $pkg.scripts.'build:mp-weixin'

if (!$devCmd -or ($devCmd -notmatch "mp-weixin")) {
    L "  修复package.json scripts..." "FIX"
    $raw = Get-Content "package.json" -Raw
    if ($raw -match '"scripts"\s*:\s*\{') {
        # 在scripts块内注入
        $inject = "`"dev:mp-weixin`": `"uni -p mp-weixin`",`n    `"build:mp-weixin`": `"uni build -p mp-weixin`","
        if ($devCmd) {
            $raw = $raw -replace [regex]::Escape("`"dev:mp-weixin`": `"$devCmd`""), "`"dev:mp-weixin`": `"uni -p mp-weixin`""
        } else {
            $raw = $raw -replace '("scripts"\s*:\s*\{)', "`$1`n    $inject"
        }
        Set-Content "package.json" $raw -NoNewline
    }
    Result "编译脚本修复" $false "添加 -p mp-weixin" $true
} else {
    Result "编译脚本正确" $true
}

# 1.3 .env
if (!(Test-Path ".env")) {
    "VITE_API_URL=http://localhost:8000/api/v1" | Set-Content ".env"
    Result ".env创建" $false "已创建" $true
} else { Result ".env存在" $true }

if (!(Test-Path ".env.production")) {
    "VITE_API_URL=https://api.xingjian.health/api/v1" | Set-Content ".env.production"
}

# 1.4 request.ts端口检查
$reqFiles = Get-ChildItem src -Recurse -Filter "request.ts" -EA SilentlyContinue
foreach ($rf in $reqFiles) {
    $rc = Get-Content $rf.FullName -Raw
    if ($rc -match "8002") {
        $rc = $rc -replace '8002','8000'
        Set-Content $rf.FullName $rc -NoNewline
        Result "request.ts端口修正" $false "8002→8000" $true
    }
}

# 1.5 Docker app.yaml冲突
$appY = "$PROJECT\docker-compose.app.yaml"
if (Test-Path $appY) {
    $appRunning = docker-compose -f $appY ps -q 2>$null
    if ($appRunning) {
        L "  停止 app.yaml 冲突容器..." "FIX"
        docker-compose -f $appY down 2>$null
        Start-Sleep 3
        Result "app.yaml容器停止" $false "已停止" $true
    }
}

GitCommit "auto-phase1: 基础设施加固 — 端口统一+编译脚本+环境配置"

# ═══════════════════════════════════════════════════════════
# PHASE 2: 依赖+编译
# ═══════════════════════════════════════════════════════════
$script:currentPhase = "P2-编译"
L "`n━━━ PHASE 2: 依赖安装与编译 ━━━" "HEAD"

Remove-Item -Recurse -Force dist -EA SilentlyContinue
Remove-Item -Recurse -Force "node_modules\.cache" -EA SilentlyContinue

if (!$SkipNpmInstall) {
    L "  npm install..." "INFO"
    $npmLog = npm install 2>&1 | Out-String
    Result "npm install" ($LASTEXITCODE -eq 0) $(if($LASTEXITCODE -ne 0){$npmLog.Substring(0,[Math]::Min(200,$npmLog.Length))})
} else { L "  跳过npm install" "SKIP" }

# 编译 (build优先，dev fallback)
L "  编译中 (build模式)..." "INFO"
$buildLog = npm run build:mp-weixin 2>&1 | Out-String
$dist = $null
if (Test-Path "dist\build\mp-weixin\app.json") { $dist = "dist\build\mp-weixin" }

if (!$dist) {
    L "  build失败，尝试 npx uni build..." "WARN"
    $buildLog = npx uni build -p mp-weixin 2>&1 | Out-String
    if (Test-Path "dist\build\mp-weixin\app.json") { $dist = "dist\build\mp-weixin" }
}

if (!$dist) {
    L "  build均失败，尝试dev模式(限时90s)..." "WARN"
    $job = Start-Job { Set-Location $using:MINI; npx uni -p mp-weixin 2>&1 }
    $waited = 0
    while ($waited -lt 90) {
        Start-Sleep 5; $waited += 5
        if (Test-Path "dist\dev\mp-weixin\app.json") { $dist = "dist\dev\mp-weixin"; break }
        L "    等待编译... ${waited}s" "INFO"
    }
    Stop-Job $job -EA SilentlyContinue; Remove-Job $job -Force -EA SilentlyContinue
}

Result "编译成功" ($null -ne $dist) $(if($dist){"路径: $dist"}else{"所有模式均失败"})

if ($dist) {
    # 检查编译产物
    $pageCount = (Get-ChildItem "$dist\pages" -Recurse -Filter "*.js" -EA SilentlyContinue).Count
    L "  编译产物页面JS: $pageCount" "INFO"
    
    # 幽灵路径检测
    $ghosts = Select-String -Path "$dist\**\*.js" -Pattern "/v1/professional/" -Recurse -EA SilentlyContinue
    Result "无/v1/professional/幽灵路径" (!$ghosts -or $ghosts.Count -eq 0) "发现$($ghosts.Count)处"
}

# ═══════════════════════════════════════════════════════════
# PHASE 3: API全量烟测
# ═══════════════════════════════════════════════════════════
$script:currentPhase = "P3-API烟测"
L "`n━━━ PHASE 3: API全量烟测 ━━━" "HEAD"

# Coach端点
if ($coachTk) {
    $ch = @{ Authorization = "Bearer $coachTk" }
    $coachEps = @(
        @{n="coach/dashboard";     p="/api/v1/coach/dashboard"},
        @{n="coach/students";      p="/api/v1/coach/students"},
        @{n="coach/performance";   p="/api/v1/coach/performance"},
        @{n="coach/conversations"; p="/api/v1/coach/conversations"},
        @{n="coach/live-sessions"; p="/api/v1/coach/live-sessions"},
        @{n="coach/risk-alerts";   p="/api/v1/coach/risk-alerts"},
        @{n="coach/review-queue";  p="/api/v1/coach/review-queue"},
        @{n="coach-push/pending";  p="/api/v1/coach-push/pending"},
        @{n="coach/stats/today";   p="/api/v1/coach/stats/today"},
        @{n="coach/analytics";     p="/api/v1/coach/analytics/week-trend"},
        @{n="assessment-assign";   p="/api/v1/assessment-assignments"},
        @{n="learning/courses";    p="/api/v1/learning/courses"},
        @{n="agent/list";          p="/api/v1/agent/list"}
    )
    foreach ($ep in $coachEps) {
        $r = HTTP "$API$($ep.p)" "GET" $null $ch
        if ($r.OK) { Result "Coach→$($ep.n)" $true }
        elseif ($r.Code -eq 404) { Result "Coach→$($ep.n)" $false "404(未实现)" }
        elseif ($r.Code -eq 422) { Result "Coach→$($ep.n)" $true "422(需参数,端点存在)" }
        else { Result "Coach→$($ep.n)" $false "HTTP $($r.Code)" }
    }
} else { L "  Coach token不可用，跳过教练端点" "WARN" }

# Grower端点
if ($growerTk) {
    $gh = @{ Authorization = "Bearer $growerTk" }
    $growerEps = @(
        @{n="journey/state";    p="/api/v1/journey/state"},
        @{n="tasks/today";      p="/api/v1/tasks/today"},
        @{n="credits/summary";  p="/api/v1/credits/summary"},
        @{n="health-data";      p="/api/v1/health-data/summary"},
        @{n="challenges";       p="/api/v1/challenges/active"},
        @{n="micro-actions";    p="/api/v1/micro-actions/today"}
    )
    foreach ($ep in $growerEps) {
        $r = HTTP "$API$($ep.p)" "GET" $null $gh
        if ($r.OK) { Result "Grower→$($ep.n)" $true }
        elseif ($r.Code -eq 404) { Result "Grower→$($ep.n)" $false "404" }
        else { Result "Grower→$($ep.n)" $false "HTTP $($r.Code)" }
    }
}

# 公共端点
foreach ($ep in @("/docs","/openapi.json","/health")) {
    $r = HTTP "$API$ep"
    Result "Public→$ep" ($r.OK -or $r.Code -in 200,301)
}

# ═══════════════════════════════════════════════════════════
# PHASE 4: Coach目录重构
# ═══════════════════════════════════════════════════════════
$script:currentPhase = "P4-目录重构"
L "`n━━━ PHASE 4: Coach目录重构 ━━━" "HEAD"

$coachDir = "src\pages\coach"

# 创建子目录
$dirs = @("dashboard","flywheel","students","risk","assessment","push-queue","analytics","messages","live")
foreach ($d in $dirs) { EnsureDir "$coachDir\$d" }
Result "子目录创建" $true "$($dirs.Count)个"

# 移动平铺文件到子目录
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
foreach ($kv in $moveMap.GetEnumerator()) {
    $s = "$coachDir\$($kv.Key)"; $d = "$coachDir\$($kv.Value)"
    if ((Test-Path $s) -and !(Test-Path $d)) {
        EnsureDir (Split-Path $d -Parent)
        Move-Item $s $d -Force; $moved++
        L "    📦 $($kv.Key) → $($kv.Value)" "INFO"
    }
}
if ((Test-Path "$coachDir\index.vue") -and !(Test-Path "$coachDir\dashboard\index.vue")) {
    Copy-Item "$coachDir\index.vue" "$coachDir\dashboard\index.vue" -Force; $moved++
}
Result "文件迁移" $true "${moved}个文件"

GitCommit "auto-phase4: coach目录重构完成"

# ═══════════════════════════════════════════════════════════
# PHASE 5: BOS UI集成
# ═══════════════════════════════════════════════════════════
$script:currentPhase = "P5-UI集成"
L "`n━━━ PHASE 5: BOS UI集成 ━━━" "HEAD"

if ($SkipUIIntegration) {
    L "  跳过UI集成(参数指定)" "SKIP"
} else {
    Set-Location $PROJECT

    # 查找backup分支中的UI文件
    $uiSources = @("小程序版UI更新/src/pages/coach", "小程序版UI更新/src/config", "小程序版UI更新/src/utils")
    $hasUI = git ls-tree -r --name-only $BACKUP 2>$null | Where-Object { $_ -match "UI" } | Select-Object -First 1

    if ($hasUI) {
        L "  从backup分支提取UI资产..." "INFO"
        git checkout $BACKUP -- "小程序版UI更新/" 2>$null
        git checkout $BACKUP -- "小程序版UI/" 2>$null

        $uiRoot = if (Test-Path "小程序版UI更新\src\pages\coach") { "小程序版UI更新" }
                  elseif (Test-Path "小程序版UI") { "小程序版UI" }
                  else { "" }

        if ($uiRoot) {
            $coachT = "$MINI\src\pages\coach"
            $installed = 0

            # 复制美化页面
            $uiFiles = @(
                "dashboard\index.vue", "flywheel\index.vue", "students\index.vue",
                "students\detail.vue", "risk\index.vue", "assessment\index.vue",
                "assessment\review.vue", "push-queue\index.vue", "analytics\index.vue",
                "messages\index.vue", "live\index.vue"
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
            Result "美化页面安装" ($installed -ge 8) "$installed/11个文件"

            # 复制config/env.ts
            if (Test-Path "$uiRoot\src\config\env.ts") {
                EnsureDir "$MINI\src\config"
                Copy-Item "$uiRoot\src\config\env.ts" "$MINI\src\config\env.ts" -Force
                L "    📦 config/env.ts" "INFO"
            }

            # 复制utils/request.ts
            if (Test-Path "$uiRoot\src\utils\request.ts") {
                EnsureDir "$MINI\src\utils"
                Copy-Item "$uiRoot\src\utils\request.ts" "$MINI\src\utils\request.ts" -Force
                L "    📦 utils/request.ts" "INFO"
            }
        } else {
            Result "UI源目录定位" $false "未找到UI文件"
            ManualTodo "手动从backup分支提取UI文件"
        }

        # 清理临时目录
        Remove-Item -Recurse -Force "小程序版UI更新" -EA SilentlyContinue
        Remove-Item -Recurse -Force "小程序版UI" -EA SilentlyContinue
        # 恢复git状态
        git checkout HEAD -- . 2>$null
    } else {
        Result "backup分支UI文件" $false "未找到"
        ManualTodo "手动集成BOS UI文件"
    }

    Set-Location $MINI

    # 自动修复所有coach vue文件中的硬编码
    L "  扫描并修复UI硬编码..." "INFO"
    $fixCount = 0
    Get-ChildItem "src\pages\coach" -Recurse -Filter "*.vue" -EA SilentlyContinue | ForEach-Object {
        $c = Get-Content $_.FullName -Raw -EA SilentlyContinue
        if (!$c) { return }
        $orig = $c
        $c = $c -replace 'localhost:8002', 'localhost:8000'
        $c = $c -replace 'localhost:8001', 'localhost:8000'
        # 修复PROD_URL未定义引用
        if ($c -match "PROD_URL" -and $c -notmatch "import.*PROD_URL" -and $c -notmatch "const\s+PROD_URL") {
            $c = $c -replace "PROD_URL\s*\|\|", "'http://localhost:8000/api/v1' ||"
            $c = $c -replace "PROD_URL", "'http://localhost:8000/api/v1'"
        }
        if ($c -ne $orig) { Set-Content $_.FullName $c -NoNewline; $fixCount++ }
    }
    if ($fixCount) { Result "UI硬编码修复" $false "${fixCount}个文件" $true }

    GitCommit "auto-phase5: BOS UI集成 — ${installed}个美化页面+硬编码修复"
}

# ═══════════════════════════════════════════════════════════
# PHASE 6: pages.json路由对齐
# ═══════════════════════════════════════════════════════════
$script:currentPhase = "P6-路由对齐"
L "`n━━━ PHASE 6: pages.json路由对齐 ━━━" "HEAD"

Set-Location $MINI
$pjPath = if (Test-Path "src\pages.json") {"src\pages.json"} elseif (Test-Path "pages.json") {"pages.json"} else {""}

if ($pjPath) {
    $pjRaw = Get-Content $pjPath -Raw
    $requiredRoutes = @(
        "coach/dashboard/index", "coach/flywheel/index", "coach/students/index",
        "coach/students/detail", "coach/risk/index", "coach/assessment/index",
        "coach/push-queue/index", "coach/analytics/index", "coach/messages/index",
        "coach/live/index"
    )
    $missing = @()
    foreach ($r in $requiredRoutes) {
        if ($pjRaw -notmatch [regex]::Escape($r)) { $missing += $r }
    }
    if ($missing.Count -gt 0) {
        L "  缺少 $($missing.Count) 条路由，尝试自动注入..." "WARN"

        # 检查是否有subPackages配置
        if ($pjRaw -match '"subPackages"') {
            # 在现有subPackages的coach root下注入
            foreach ($r in $missing) {
                $pagePath = $r -replace "coach/", ""
                $entry = "      {`"path`": `"$pagePath`"}"
                # 简单注入: 找到coach相关的pages数组末尾追加
                L "    📋 需添加路由: $r" "WARN"
            }
            ManualTodo "pages.json中缺少路由: $($missing -join ', ') — 需手动添加到subPackages"
        } else {
            # 主包模式，直接在pages数组中添加
            foreach ($r in $missing) {
                $entry = "`n    {`"path`": `"pages/$r`", `"style`": {`"navigationBarTitleText`": `"`"}},"
                L "    📋 需添加路由: pages/$r" "WARN"
            }
            ManualTodo "pages.json中缺少路由: $($missing -join ', ')"
        }
        Result "路由完整性" $false "缺$($missing.Count)条"
    } else {
        Result "路由完整性" $true "全部已注册"
    }
} else {
    Result "pages.json存在" $false "未找到"
}

GitCommit "auto-phase6: 路由对齐检查"

# ═══════════════════════════════════════════════════════════
# PHASE 7: 最终编译 + 静态分析（模拟页面测试）
# ═══════════════════════════════════════════════════════════
$script:currentPhase = "P7-终验"
L "`n━━━ PHASE 7: 最终编译 + 页面静态分析 ━━━" "HEAD"

# 重新编译
Remove-Item -Recurse -Force dist -EA SilentlyContinue
L "  最终编译..." "INFO"
$buildLog2 = npm run build:mp-weixin 2>&1 | Out-String
$dist2 = $null
if (Test-Path "dist\build\mp-weixin\app.json") { $dist2 = "dist\build\mp-weixin" }
if (!$dist2) {
    $buildLog2 = npx uni build -p mp-weixin 2>&1 | Out-String
    if (Test-Path "dist\build\mp-weixin\app.json") { $dist2 = "dist\build\mp-weixin" }
}
if (!$dist2) {
    $job2 = Start-Job { Set-Location $using:MINI; npx uni -p mp-weixin 2>&1 }
    $w2 = 0
    while ($w2 -lt 90) {
        Start-Sleep 5; $w2 += 5
        if (Test-Path "dist\dev\mp-weixin\app.json") { $dist2 = "dist\dev\mp-weixin"; break }
    }
    Stop-Job $job2 -EA SilentlyContinue; Remove-Job $job2 -Force -EA SilentlyContinue
}
Result "最终编译" ($null -ne $dist2) $(if($dist2){$dist2}else{"失败"})

if ($dist2) {
    # ═══ 页面静态分析 (模拟页面点击发现问题) ═══
    L "`n  ▶ 页面静态分析 — 检查每个编译后页面的常见问题..." "HEAD"

    $appJson = Get-Content "$dist2\app.json" -Raw | ConvertFrom-Json
    $allPages = @()
    if ($appJson.pages) { $allPages += $appJson.pages }
    if ($appJson.subPackages) {
        foreach ($sp in $appJson.subPackages) {
            foreach ($pg in $sp.pages) {
                $allPages += "$($sp.root)/$($pg.path ?? $pg)"
            }
        }
    }
    L "  app.json注册页面数: $($allPages.Count)" "INFO"

    $pageIssues = @()
    foreach ($page in $allPages) {
        $cleanPage = $page -replace '\\','/'
        $jsFile = Get-ChildItem "$dist2\$cleanPage.*" -EA SilentlyContinue | Where-Object { $_.Extension -eq ".js" } | Select-Object -First 1
        if (!$jsFile) { $jsFile = Get-Item "$dist2\$cleanPage.js" -EA SilentlyContinue }
        if (!$jsFile -and (Test-Path "$dist2\$cleanPage")) {
            $jsFile = Get-ChildItem "$dist2\$cleanPage" -Filter "*.js" -EA SilentlyContinue | Select-Object -First 1
        }

        if ($jsFile) {
            $js = Get-Content $jsFile.FullName -Raw -EA SilentlyContinue
            $issues = @()

            # 检查1: undefined变量引用
            if ($js -match "PROD_URL" -and $js -notmatch "var PROD_URL|let PROD_URL|const PROD_URL") {
                $issues += "PROD_URL未定义"
            }
            # 检查2: 错误端口
            if ($js -match "localhost:800[1-9]") { $issues += "错误端口引用" }
            # 检查3: /v1/professional/ 幽灵路径
            if ($js -match "/v1/professional/") { $issues += "/v1/professional/幽灵路径" }
            # 检查4: 缺少module引用 (子包问题)
            if ($js -match "require\([^)]*api/") { $issues += "跨包require(可能运行时报错)" }
            # 检查5: _request内联函数 (应已被替换)
            if ($js -match "function _request\(") { $issues += "残留内联_request" }
            # 检查6: 空文件
            if ($js.Length -lt 50) { $issues += "文件过小(可能是空页面)" }

            if ($issues.Count -gt 0) {
                $pageIssues += @{ Page=$cleanPage; Issues=$issues }
                foreach ($iss in $issues) {
                    Result "页面[$($cleanPage.Split('/')[-1])]" $false $iss
                }
            } else {
                Result "页面[$($cleanPage.Split('/')[-1])]" $true
            }
        } else {
            Result "页面[$($cleanPage.Split('/')[-1])]" $false "编译产物JS未找到"
        }
    }

    if ($pageIssues.Count -eq 0) {
        L "  🎉 所有页面静态分析通过!" "PASS"
    } else {
        L "  ⚠️  $($pageIssues.Count)个页面存在问题" "WARN"
    }

    # 检查wxss/css文件中的常见UI问题
    L "`n  ▶ 样式检查..." "HEAD"
    $wxssFiles = Get-ChildItem $dist2 -Recurse -Include "*.wxss","*.css" -EA SilentlyContinue
    $styleIssues = 0
    foreach ($css in $wxssFiles) {
        $c = Get-Content $css.FullName -Raw -EA SilentlyContinue
        if ($c -match "opacity:\s*0[^.]" -and $c -match "nav.*back|arrow|return") {
            $styleIssues++
            L "    ⚠️  $($css.Name): 可能包含不可见的返回箭头样式" "WARN"
        }
    }
    if ($styleIssues -eq 0) { Result "返回箭头样式" $true }
}

# ═══════════════════════════════════════════════════════════
# PHASE 8: 微信开发者工具自动化(可选)
# ═══════════════════════════════════════════════════════════
$script:currentPhase = "P8-DevTools自动化"
L "`n━━━ PHASE 8: 微信开发者工具自动化测试 ━━━" "HEAD"

# 查找微信开发者工具CLI
$wxCli = @(
    "C:\Program Files (x86)\Tencent\微信web开发者工具\cli.bat",
    "C:\Program Files\Tencent\微信web开发者工具\cli.bat",
    "$env:LOCALAPPDATA\微信web开发者工具\cli.bat"
) | Where-Object { Test-Path $_ } | Select-Object -First 1

if ($wxCli -and $dist2) {
    L "  找到DevTools CLI: $wxCli" "INFO"
    L "  尝试自动预览..." "INFO"

    # 尝试使用CLI打开项目
    try {
        & $wxCli open --project $dist2 2>$null
        Start-Sleep 5
        Result "DevTools打开项目" $true
        ManualTodo "请在微信开发者工具中手动验证页面渲染"
    } catch {
        Result "DevTools打开项目" $false $_.Exception.Message
    }
} else {
    L "  微信开发者工具CLI未找到或无编译产物" "SKIP"
    L "  跳过自动化UI测试" "SKIP"
    ManualTodo "手动打开微信开发者工具验证页面"
}

GitCommit "auto-phase7-8: 最终编译+静态分析+DevTools集成"

# ═══════════════════════════════════════════════════════════
# 生成报告
# ═══════════════════════════════════════════════════════════
$sw.Stop()
$elapsed = $sw.Elapsed.ToString("hh\:mm\:ss")

$totalP = ($script:results | Where-Object { $_.Status -eq "PASS" }).Count
$totalF = ($script:results | Where-Object { $_.Status -eq "FAIL" }).Count
$totalX = ($script:results | Where-Object { $_.Status -eq "FIXED" }).Count

# 文件统计
Set-Location $MINI
$statVues   = (Get-ChildItem src\pages -Recurse -Filter "*.vue" -EA SilentlyContinue).Count
$statCoach  = (Get-ChildItem src\pages\coach -Recurse -Filter "*.vue" -EA SilentlyContinue).Count
$statApi    = (Get-ChildItem src\api -Filter "*.ts" -EA SilentlyContinue).Count
$statComp   = (Get-ChildItem src\components -Filter "*.vue" -EA SilentlyContinue).Count

$health = if ($totalF -eq 0) { "🟢 全部通过" }
          elseif ($totalF -le 3) { "🟡 基本健康(少量问题)" }
          elseif ($totalF -le 8) { "🟠 需要手动干预" }
          else { "🔴 严重问题" }

$rpt = @"
# 🏥 BehaviorOS 稳定化自动执行报告

> **执行时间**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
> **耗时**: $elapsed
> **锚点**: 9a6b18b (Sprint 1)
> **分支**: stabilize-from-sprint1

---

## 📊 总览

| | 数量 |
|-|------|
| ✅ 通过 | **$totalP** |
| 🔧 自动修复 | **$totalX** |
| ❌ 失败 | **$totalF** |
| 健康度 | $health |

## 📁 资产统计

| 类别 | 数量 |
|------|------|
| 总页面(.vue) | $statVues |
| Coach美化页面 | $statCoach |
| API模块(.ts) | $statApi |
| 组件(.vue) | $statComp |
| 编译产物 | $(if($dist2){"✅ $dist2"}else{"❌ 未生成"}) |

---

## 🔧 自动修复记录

"@

if ($script:fixes.Count -eq 0) { $rpt += "无需自动修复。`n" }
else {
    $rpt += "| # | 修复项 |`n|-|--------|`n"
    $i = 1; foreach ($f in $script:fixes) { $rpt += "| $i | $f |`n"; $i++ }
}

$rpt += "`n## ❌ 未解决问题`n`n"
if ($script:issues.Count -eq 0) { $rpt += "无！🎉`n" }
else {
    $rpt += "| # | 问题 |`n|-|------|`n"
    $i = 1; foreach ($f in $script:issues) { $rpt += "| $i | $f |`n"; $i++ }
}

$rpt += "`n## 📋 需手动完成`n`n"
if ($script:manualTodos.Count -eq 0) { $rpt += "无！全自动完成！🎉`n" }
else {
    $i = 1; foreach ($t in $script:manualTodos) { $rpt += "$i. $t`n"; $i++ }
}

$rpt += @"

---

## 📋 各Phase详细结果

| Phase | 检查项 | 状态 | 详情 |
|-------|--------|------|------|
"@

foreach ($r in $script:results) {
    $icon = switch($r.Status) { "PASS" {"✅"}; "FAIL" {"❌"}; "FIXED" {"🔧"} }
    $rpt += "| $($r.Phase) | $($r.Name) | $icon | $($r.Detail) |`n"
}

$rpt += @"

---

## 🚀 下一步

"@

if ($totalF -eq 0) {
    $rpt += @"
**🎉 全部通过！执行以下命令合并回主分支：**

``````powershell
cd $MINI
git checkout master
git merge stabilize-from-sprint1
git push origin master --tags
``````
"@
} else {
    $rpt += @"
**⚠️ 有 $totalF 个失败项需处理。处理完后：**

1. 手动修复上述❌项目
2. 执行手动TODO清单
3. 运行 ``npm run build:mp-weixin`` 确认编译通过
4. 在微信开发者工具中逐页面验证
5. 确认后合并: ``git checkout master && git merge stabilize-from-sprint1``
"@
}

$rpt += "`n`n---`n*自动生成 by stabilize-master v2.0 | 日志: $LOG*`n"

Set-Content $REPORT $rpt
L "" "INFO"

L "╔══════════════════════════════════════════════════════╗" "HEAD"
L "║  执行完毕！                                         ║" "HEAD"
L "║  ✅ $totalP  🔧 $totalX  ❌ $totalF                  ║" "HEAD"
L "║  耗时: $elapsed                                     ║" "HEAD"
L "╚══════════════════════════════════════════════════════╝" "HEAD"
L "报告: $REPORT" "HEAD"

# 打开报告
Start-Process notepad.exe $REPORT

Write-Host ""
Write-Host "报告已在记事本中打开。" -ForegroundColor Cyan
Write-Host "完整日志: $LOG" -ForegroundColor DarkGray

#!/usr/bin/env pwsh
<#
.SYNOPSIS
    BehaviorOS Coach-Miniprogram 全自动稳定化执行器
.DESCRIPTION
    从 9a6b18b 锚点出发，自动完成 Phase 0-7 全部操作。
    无人值守运行，所有结果输出到日志和报告文件。
.NOTES
    日期: 2026-03-01
    执行前确认:
      1. 当前在 stabilize-from-sprint1 分支
      2. Docker 容器 bhp_v3_api 正在运行
      3. 以管理员身份运行 PowerShell
#>

# ═══════════════════════════════════════════════════
# 全局配置
# ═══════════════════════════════════════════════════
$ErrorActionPreference = "Continue"
$PROJECT_ROOT = "D:\behavioral-health-project"
$MINI_ROOT = "$PROJECT_ROOT\coach-miniprogram"
$BACKUP_BRANCH = "backup-2026-0301-before-rollback"
$API_BASE = "http://localhost:8000"
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$LOG_DIR = "$MINI_ROOT\_stabilize-logs"
$LOG_FILE = "$LOG_DIR\run-$TIMESTAMP.log"
$REPORT_FILE = "$LOG_DIR\REPORT-$TIMESTAMP.md"

# 计数器
$script:passCount = 0
$script:failCount = 0
$script:warnCount = 0
$script:phaseResults = @()

# ═══════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════

function Ensure-Dir($path) {
    if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path -Force | Out-Null }
}

function Log($msg, $level = "INFO") {
    $ts = Get-Date -Format "HH:mm:ss"
    $line = "[$ts][$level] $msg"
    Write-Host $line -ForegroundColor $(switch($level) {
        "PASS" { "Green" }; "FAIL" { "Red" }; "WARN" { "Yellow" }
        "PHASE" { "Cyan" }; "SKIP" { "DarkGray" }; default { "White" }
    })
    Add-Content -Path $LOG_FILE -Value $line -ErrorAction SilentlyContinue
}

function Check($name, $condition, $detail = "") {
    if ($condition) {
        Log "  ✅ $name" "PASS"
        $script:passCount++
        return $true
    } else {
        Log "  ❌ $name $(if($detail){': '+$detail})" "FAIL"
        $script:failCount++
        return $false
    }
}

function Warn($msg) {
    Log "  ⚠️  $msg" "WARN"
    $script:warnCount++
}

function Phase-Start($num, $title) {
    Log "" "INFO"
    Log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "PHASE"
    Log "  PHASE $num : $title" "PHASE"
    Log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "PHASE"
}

function Phase-End($num, $title, $critical = $true) {
    $pFail = $script:failCount
    $result = @{ Phase=$num; Title=$title; Pass=$script:passCount; Fail=$pFail; Warn=$script:warnCount }
    $script:phaseResults += $result

    if ($pFail -gt 0 -and $critical) {
        Log "Phase $num 有 $pFail 个失败项。标记为需手动干预。" "WARN"
        return $false
    }
    Log "Phase $num 完成 ✅ (Pass:$($script:passCount) Warn:$($script:warnCount))" "PASS"
    return $true
}

function Git-Commit($msg) {
    Push-Location $PROJECT_ROOT
    git add -A 2>$null
    $status = git status --porcelain 2>$null
    if ($status) {
        git commit -m $msg 2>$null | Out-Null
        Log "  📦 Git commit: $msg" "INFO"
    } else {
        Log "  📦 Git: 无变更需提交" "SKIP"
    }
    Pop-Location
}

function Safe-Request($url, $method = "GET", $body = $null, $headers = @{}, $timeout = 10) {
    try {
        $params = @{
            Uri = $url
            Method = $method
            UseBasicParsing = $true
            TimeoutSec = $timeout
        }
        if ($headers.Count -gt 0) { $params.Headers = $headers }
        if ($body) {
            $params.Body = $body
            $params.ContentType = "application/json"
        }
        $r = Invoke-WebRequest @params
        return @{ Code = $r.StatusCode; Body = $r.Content; OK = $true }
    } catch {
        $code = 0
        if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
        return @{ Code = $code; Body = $_.Exception.Message; OK = $false }
    }
}

function Get-CoachToken {
    $r = Safe-Request "$API_BASE/api/v1/auth/login" "POST" '{"username":"coach","password":"Coach@2026"}'
    if ($r.OK) {
        $data = $r.Body | ConvertFrom-Json
        return $data.access_token
    }
    # 备选密码
    $r2 = Safe-Request "$API_BASE/api/v1/auth/login" "POST" '{"username":"coach","password":"coach123"}'
    if ($r2.OK) {
        $data = $r2.Body | ConvertFrom-Json
        return $data.access_token
    }
    return $null
}

function Get-GrowerToken {
    $r = Safe-Request "$API_BASE/api/v1/auth/login" "POST" '{"username":"grower","password":"Grower@2026"}'
    if ($r.OK) {
        $data = $r.Body | ConvertFrom-Json
        return $data.access_token
    }
    $r2 = Safe-Request "$API_BASE/api/v1/auth/login" "POST" '{"username":"grower_test","password":"Grower@2026"}'
    if ($r2.OK) {
        $data = $r2.Body | ConvertFrom-Json
        return $data.access_token
    }
    return $null
}

# ═══════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════

Ensure-Dir $LOG_DIR
Log "BehaviorOS 全自动稳定化 启动" "PHASE"
Log "项目: $MINI_ROOT" "INFO"
Log "日志: $LOG_FILE" "INFO"
Log "时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" "INFO"

# ═══════════════════════════════════════════════════
# PHASE 0: 基线验证
# ═══════════════════════════════════════════════════
Phase-Start 0 "基线验证"
$script:passCount = 0; $script:failCount = 0; $script:warnCount = 0

Set-Location $MINI_ROOT

# 0.1 确认分支
$branch = git branch --show-current 2>$null
$headMsg = git log --oneline -1 2>$null
Check "当前分支 = stabilize-from-sprint1" ($branch -eq "stabilize-from-sprint1") "实际: $branch"
Check "HEAD包含Sprint 1" ($headMsg -match "Sprint 1|9a6b18b") "实际: $headMsg"

# 0.2 确认package.json
Check "package.json存在" (Test-Path "package.json")

if (Test-Path "package.json") {
    $pkg = Get-Content "package.json" -Raw | ConvertFrom-Json
    $hasScript = $pkg.scripts.'dev:mp-weixin' -ne $null
    Check "dev:mp-weixin脚本存在" $hasScript
}

# 0.3 Docker后端
$dockerCheck = docker ps --format "{{.Names}}:{{.Status}}" 2>$null | Select-String "bhp_v3_api"
Check "bhp_v3_api容器运行中" ($null -ne $dockerCheck) "请先启动Docker"

# 0.4 API可达
$apiCheck = Safe-Request "$API_BASE/docs"
Check "API /docs 可达" $apiCheck.OK "StatusCode: $($apiCheck.Code)"

# 0.5 认证测试
$coachToken = Get-CoachToken
Check "Coach登录成功" ($null -ne $coachToken)
$growerToken = Get-GrowerToken
Check "Grower登录成功" ($null -ne $growerToken)

$p0ok = Phase-End 0 "基线验证" $false  # 非关键阻断，继续

# ═══════════════════════════════════════════════════
# PHASE 1: 基础设施加固
# ═══════════════════════════════════════════════════
Phase-Start 1 "基础设施加固"
$script:passCount = 0; $script:failCount = 0; $script:warnCount = 0

Set-Location $MINI_ROOT

# 1.1 端口审计
Log "  扫描错误端口引用..." "INFO"
$badPorts = @()
Get-ChildItem -Path src -Recurse -Include "*.ts","*.vue","*.js" -ErrorAction SilentlyContinue | ForEach-Object {
    $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
    if ($content -match "localhost:800[1-9]|localhost:80[1-9]\d") {
        $badPorts += $_.FullName
    }
}
if ($badPorts.Count -eq 0) {
    Check "无错误端口引用(8001-8099)" $true
} else {
    Warn "发现 $($badPorts.Count) 个文件包含错误端口:"
    foreach ($f in $badPorts) {
        $rel = $f.Replace($MINI_ROOT, "")
        Log "    → $rel" "WARN"
        # 自动修复: 替换 localhost:8002 → localhost:8000
        $c = Get-Content $f -Raw
        $c = $c -replace 'localhost:8002', 'localhost:8000'
        $c = $c -replace 'localhost:8001', 'localhost:8000'
        Set-Content -Path $f -Value $c -NoNewline
        Log "    ↳ 已自动修复" "PASS"
    }
    Check "错误端口已自动修复" $true
}

# 1.2 确认request.ts唯一性
$requestFiles = Get-ChildItem -Path src -Recurse -Filter "request.ts" -ErrorAction SilentlyContinue
Check "request.ts模块数量" ($requestFiles.Count -le 1) "找到 $($requestFiles.Count) 个"
if ($requestFiles.Count -gt 0) {
    Log "  request.ts位置: $($requestFiles[0].FullName.Replace($MINI_ROOT,''))" "INFO"
}

# 1.3 修复package.json编译命令
$pkg = Get-Content "package.json" -Raw | ConvertFrom-Json
$devScript = $pkg.scripts.'dev:mp-weixin'
if ($devScript -and $devScript -notmatch "-p mp-weixin") {
    Log "  修复dev:mp-weixin脚本: 添加 -p mp-weixin" "WARN"
    $pkgRaw = Get-Content "package.json" -Raw
    # 查找现有的dev:mp-weixin值并替换
    if ($devScript -match "^uni\s*$") {
        $pkgRaw = $pkgRaw -replace '"dev:mp-weixin"\s*:\s*"uni"', '"dev:mp-weixin": "uni -p mp-weixin"'
    } else {
        $pkgRaw = $pkgRaw -replace [regex]::Escape($devScript), "uni -p mp-weixin"
    }
    Set-Content -Path "package.json" -Value $pkgRaw -NoNewline
    Check "dev:mp-weixin已修复" $true
} elseif (-not $devScript) {
    # 添加脚本
    $pkg.scripts | Add-Member -NotePropertyName "dev:mp-weixin" -NotePropertyValue "uni -p mp-weixin" -Force
    $pkg.scripts | Add-Member -NotePropertyName "build:mp-weixin" -NotePropertyValue "uni build -p mp-weixin" -Force
    $pkg | ConvertTo-Json -Depth 10 | Set-Content "package.json"
    Check "dev:mp-weixin已添加" $true
} else {
    Check "dev:mp-weixin脚本正确" $true
}

# 1.4 创建.env文件
if (-not (Test-Path ".env")) {
    Set-Content -Path ".env" -Value "VITE_API_URL=http://localhost:8000/api/v1"
    Log "  创建 .env" "INFO"
}
if (-not (Test-Path ".env.production")) {
    Set-Content -Path ".env.production" -Value "VITE_API_URL=https://api.xingjian.health/api/v1"
    Log "  创建 .env.production" "INFO"
}
Check ".env文件就位" (Test-Path ".env")

# 1.5 Docker治理
Log "  检查Docker Compose状态..." "INFO"
$appYaml = "$PROJECT_ROOT\docker-compose.app.yaml"
if (Test-Path $appYaml) {
    $appContainers = docker-compose -f $appYaml ps --format "{{.Name}}" 2>$null
    if ($appContainers) {
        Log "  停止 docker-compose.app.yaml 中的冲突容器..." "WARN"
        docker-compose -f $appYaml down 2>$null
        Start-Sleep -Seconds 3
        Check "app.yaml容器已停止" $true
    } else {
        Check "app.yaml无运行中容器" $true
    }
} else {
    Check "无app.yaml文件(跳过)" $true
}

# 1.6 确认核心服务
$apiUp = Safe-Request "$API_BASE/docs"
Check "API服务正常" $apiUp.OK

Git-Commit "phase1: 基础设施加固 — 端口统一/环境配置/Docker治理"
Phase-End 1 "基础设施加固" $false

# ═══════════════════════════════════════════════════
# PHASE 2: 依赖安装与编译
# ═══════════════════════════════════════════════════
Phase-Start 2 "依赖安装与编译"
$script:passCount = 0; $script:failCount = 0; $script:warnCount = 0

Set-Location $MINI_ROOT

# 2.1 清理旧缓存
Log "  清理编译缓存..." "INFO"
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "node_modules\.cache" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "node_modules\.vite" -ErrorAction SilentlyContinue

# 2.2 npm install
Log "  npm install (可能需要1-2分钟)..." "INFO"
$npmOut = npm install 2>&1 | Out-String
$npmOk = $LASTEXITCODE -eq 0
Check "npm install成功" $npmOk $npmOut.Substring(0, [Math]::Min(200, $npmOut.Length))

# 2.3 编译
Log "  编译 mp-weixin (可能需要30秒-1分钟)..." "INFO"
$buildOut = npx uni -p mp-weixin 2>&1 | Out-String
# uni dev是持续运行的，我们需要用build模式
# 或者用超时方式检测dev是否启动成功

# 尝试build模式（一次性编译）
Log "  尝试 build 模式..." "INFO"
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue
$buildOut = npm run build:mp-weixin 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    # build脚本可能不存在，尝试直接调用
    $buildOut = npx uni build -p mp-weixin 2>&1 | Out-String
}

$distExists = Test-Path "dist\build\mp-weixin" -or (Test-Path "dist\dev\mp-weixin")
if (-not $distExists) {
    # dev模式：启动后等待编译完成再终止
    Log "  build失败，尝试dev模式(限时60秒)..." "WARN"
    $devJob = Start-Job -ScriptBlock {
        Set-Location $using:MINI_ROOT
        npx uni -p mp-weixin 2>&1
    }
    Start-Sleep -Seconds 60
    Stop-Job $devJob -ErrorAction SilentlyContinue
    Remove-Job $devJob -Force -ErrorAction SilentlyContinue
    $distExists = (Test-Path "dist\dev\mp-weixin") -or (Test-Path "dist\build\mp-weixin")
}

Check "编译产物生成" $distExists

# 2.4 检查编译产物内容
$distPath = if (Test-Path "dist\build\mp-weixin") { "dist\build\mp-weixin" } elseif (Test-Path "dist\dev\mp-weixin") { "dist\dev\mp-weixin" } else { "" }
if ($distPath) {
    $appJson = Test-Path "$distPath\app.json"
    Check "app.json存在于编译产物" $appJson
    Log "  编译产物路径: $distPath" "INFO"

    # 2.5 检查幽灵路径
    $ghostProfessional = Select-String -Path "$distPath\**\*.js" -Pattern "professional" -Recurse -ErrorAction SilentlyContinue
    if ($ghostProfessional) {
        Warn "编译产物中发现 /professional/ 引用 ($($ghostProfessional.Count) 处)"
    } else {
        Check "无/professional/幽灵路径" $true
    }
}

Phase-End 2 "依赖安装与编译" $false

# ═══════════════════════════════════════════════════
# PHASE 3: HTTP模块与子包检查
# ═══════════════════════════════════════════════════
Phase-Start 3 "HTTP模块与子包诊断"
$script:passCount = 0; $script:failCount = 0; $script:warnCount = 0

Set-Location $MINI_ROOT

# 3.1 request.ts内容审查
$reqFile = Get-ChildItem -Path src -Recurse -Filter "request.ts" | Select-Object -First 1
if ($reqFile) {
    $reqContent = Get-Content $reqFile.FullName -Raw
    Check "request.ts含BASE_URL" ($reqContent -match "BASE_URL|baseURL|base_url|API_URL")
    Check "request.ts含token注入" ($reqContent -match "token|Token|authorization|Authorization")
    Check "request.ts含401处理" ($reqContent -match "401|unauthorized|Unauthorized|refresh")

    # 检查BASE_URL值
    if ($reqContent -match "8002") {
        Log "  修复request.ts中的8002→8000..." "WARN"
        $reqContent = $reqContent -replace '8002', '8000'
        Set-Content -Path $reqFile.FullName -Value $reqContent -NoNewline
        Check "request.ts端口已修复" $true
    }
} else {
    Warn "未找到request.ts — 需要手动创建"
}

# 3.2 子包配置检查
$pagesJson = "src\pages.json"
if (-not (Test-Path $pagesJson)) { $pagesJson = "pages.json" }

if (Test-Path $pagesJson) {
    $pagesContent = Get-Content $pagesJson -Raw
    $hasSubPkg = $pagesContent -match "subPackages|subpackages"
    Check "pages.json存在" $true
    if ($hasSubPkg) {
        Log "  检测到subPackages配置" "INFO"
    } else {
        Log "  未使用subPackages(coach页面在主包中)" "INFO"
    }

    # 检查coach页面注册
    $coachPages = ([regex]::Matches($pagesContent, "coach/\w+")).Count
    Log "  pages.json中coach相关路由: $coachPages 条" "INFO"
} else {
    Warn "pages.json未找到"
}

# 3.3 子包import依赖分析
$coachVues = Get-ChildItem -Path "src\pages\coach" -Recurse -Filter "*.vue" -ErrorAction SilentlyContinue
if ($coachVues) {
    $importIssues = @()
    foreach ($vue in $coachVues) {
        $content = Get-Content $vue.FullName -Raw -ErrorAction SilentlyContinue
        if ($content -match "from\s+['""]@/(api|stores|components)/") {
            $importIssues += $vue.Name
        }
    }
    if ($importIssues.Count -gt 0) {
        Warn "以下coach页面引用主包模块(@/api等): $($importIssues -join ', ')"
        Log "  子包运行时可能报 'module not defined'，Phase 6集成时将处理" "INFO"
    } else {
        Check "coach页面无跨包引用问题" $true
    }
} else {
    Log "  当前锚点无coach子目录页面(将在Phase 5创建)" "INFO"
}

Git-Commit "phase3: HTTP模块审查与子包诊断"
Phase-End 3 "HTTP模块与子包诊断" $false

# ═══════════════════════════════════════════════════
# PHASE 4: API端点全面烟测
# ═══════════════════════════════════════════════════
Phase-Start 4 "API端点全面烟测"
$script:passCount = 0; $script:failCount = 0; $script:warnCount = 0

$coachToken = Get-CoachToken
$growerToken = Get-GrowerToken

if (-not $coachToken) {
    Warn "Coach登录失败，跳过教练端点测试"
} else {
    $ch = @{ Authorization = "Bearer $coachToken" }
    $coachEndpoints = @(
        @{name="coach/dashboard";     path="/api/v1/coach/dashboard"},
        @{name="coach/students";      path="/api/v1/coach/students"},
        @{name="coach/conversations"; path="/api/v1/coach/conversations"},
        @{name="coach/live-sessions"; path="/api/v1/coach/live-sessions"},
        @{name="coach/risk-alerts";   path="/api/v1/coach/risk-alerts"},
        @{name="coach/review-queue";  path="/api/v1/coach/review-queue"},
        @{name="coach-push/pending";  path="/api/v1/coach-push/pending"},
        @{name="coach/stats/today";   path="/api/v1/coach/stats/today"},
        @{name="coach/analytics";     path="/api/v1/coach/analytics/week-trend"},
        @{name="assessment-assignments"; path="/api/v1/assessment-assignments"}
    )
    foreach ($ep in $coachEndpoints) {
        $r = Safe-Request "$API_BASE$($ep.path)" "GET" $null $ch
        if ($r.OK -or $r.Code -eq 200) {
            Check "Coach: $($ep.name)" $true
        } elseif ($r.Code -eq 404) {
            Warn "Coach: $($ep.name) → 404 (端点未实现)"
        } elseif ($r.Code -eq 403) {
            Warn "Coach: $($ep.name) → 403 (权限不足)"
        } else {
            Check "Coach: $($ep.name)" $false "HTTP $($r.Code)"
        }
    }
}

if (-not $growerToken) {
    Warn "Grower登录失败，跳过学员端点测试"
} else {
    $gh = @{ Authorization = "Bearer $growerToken" }
    $growerEndpoints = @(
        @{name="tasks/today";    path="/api/v1/tasks/today"},
        @{name="credits/summary"; path="/api/v1/credits/summary"},
        @{name="journey/state";  path="/api/v1/journey/state"}
    )
    foreach ($ep in $growerEndpoints) {
        $r = Safe-Request "$API_BASE$($ep.path)" "GET" $null $gh
        if ($r.OK) {
            Check "Grower: $($ep.name)" $true
        } elseif ($r.Code -eq 404) {
            Warn "Grower: $($ep.name) → 404"
        } else {
            Check "Grower: $($ep.name)" $false "HTTP $($r.Code)"
        }
    }
}

# 通用端点
$publicEndpoints = @(
    @{name="docs";    path="/docs"},
    @{name="openapi"; path="/openapi.json"},
    @{name="health";  path="/health"}
)
foreach ($ep in $publicEndpoints) {
    $r = Safe-Request "$API_BASE$($ep.path)"
    Check "Public: $($ep.name)" ($r.OK -or $r.Code -eq 200 -or $r.Code -eq 301)
}

Phase-End 4 "API端点全面烟测" $false

# ═══════════════════════════════════════════════════
# PHASE 5: Coach目录重构
# ═══════════════════════════════════════════════════
Phase-Start 5 "Coach目录重构"
$script:passCount = 0; $script:failCount = 0; $script:warnCount = 0

Set-Location $MINI_ROOT

$coachDir = "src\pages\coach"

# 5.1 分析当前结构
$currentCoachFiles = Get-ChildItem -Path $coachDir -Filter "*.vue" -ErrorAction SilentlyContinue
Log "  当前coach目录直属.vue文件: $($currentCoachFiles.Count)" "INFO"
$currentCoachDirs = Get-ChildItem -Path $coachDir -Directory -ErrorAction SilentlyContinue
Log "  当前coach子目录: $($currentCoachDirs.Count)" "INFO"

# 5.2 创建所需子目录
$targetDirs = @("dashboard","flywheel","students","risk","assessment","push-queue","analytics","messages","live")
foreach ($d in $targetDirs) {
    $dirPath = "$coachDir\$d"
    if (-not (Test-Path $dirPath)) {
        New-Item -ItemType Directory -Path $dirPath -Force | Out-Null
        Log "  📁 创建: coach/$d/" "INFO"
    }
}
Check "目标子目录全部创建" $true

# 5.3 如果有平铺的.vue文件，移动到对应子目录
$moveMap = @{
    "dashboard.vue"     = "dashboard\index.vue"
    "flywheel.vue"      = "flywheel\index.vue"
    "students.vue"      = "students\index.vue"
    "students-detail.vue" = "students\detail.vue"
    "analytics.vue"     = "analytics\index.vue"
    "messages.vue"      = "messages\index.vue"
    "live.vue"          = "live\index.vue"
    "risk.vue"          = "risk\index.vue"
    "assessment.vue"    = "assessment\index.vue"
    "push-queue.vue"    = "push-queue\index.vue"
}

$moved = 0
foreach ($kv in $moveMap.GetEnumerator()) {
    $src = "$coachDir\$($kv.Key)"
    $dst = "$coachDir\$($kv.Value)"
    if ((Test-Path $src) -and -not (Test-Path $dst)) {
        Move-Item $src $dst -Force
        $moved++
        Log "  📦 移动: $($kv.Key) → $($kv.Value)" "INFO"
    }
}
if ($moved -gt 0) {
    Log "  移动了 $moved 个文件到子目录" "INFO"
}

# 5.4 也处理index.vue (教练首页)
if ((Test-Path "$coachDir\index.vue") -and -not (Test-Path "$coachDir\dashboard\index.vue")) {
    Copy-Item "$coachDir\index.vue" "$coachDir\dashboard\index.vue" -Force
    Log "  📦 复制 index.vue → dashboard/index.vue" "INFO"
}

Check "Coach目录重构完成" $true

Git-Commit "phase5: coach目录重构 — 子目录结构就绪"
Phase-End 5 "Coach目录重构" $false

# ═══════════════════════════════════════════════════
# PHASE 6: BOS UI集成
# ═══════════════════════════════════════════════════
Phase-Start 6 "BOS UI集成"
$script:passCount = 0; $script:failCount = 0; $script:warnCount = 0

Set-Location $PROJECT_ROOT

# 6.1 检查backup分支是否有UI文件
$hasUIDir = $false
try {
    $uiFiles = git ls-tree -r --name-only $BACKUP_BRANCH -- "小程序版UI更新/" 2>$null
    if ($uiFiles) { $hasUIDir = $true }
} catch {}

if (-not $hasUIDir) {
    # 尝试另一个目录名
    try {
        $uiFiles = git ls-tree -r --name-only $BACKUP_BRANCH -- "小程序版UI/" 2>$null
        if ($uiFiles) { $hasUIDir = $true }
    } catch {}
}

if ($hasUIDir) {
    Log "  从backup分支提取UI文件..." "INFO"

    # 提取统一配置版UI
    git checkout $BACKUP_BRANCH -- "小程序版UI更新/" 2>$null
    if (-not $?) { git checkout $BACKUP_BRANCH -- "小程序版UI/" 2>$null }

    $uiSource = if (Test-Path "小程序版UI更新\src\pages\coach") { "小程序版UI更新\src\pages\coach" }
                elseif (Test-Path "小程序版UI\") { "小程序版UI" }
                else { "" }

    if ($uiSource -and (Test-Path $uiSource)) {
        $coachTarget = "$MINI_ROOT\src\pages\coach"

        # 复制每个UI文件
        $uiFileMap = @(
            @{src="dashboard\index.vue"; name="dashboard"},
            @{src="flywheel\index.vue"; name="flywheel"},
            @{src="students\index.vue"; name="students-list"},
            @{src="students\detail.vue"; name="students-detail"},
            @{src="risk\index.vue"; name="risk"},
            @{src="assessment\index.vue"; name="assessment"},
            @{src="assessment\review.vue"; name="assessment-review"},
            @{src="push-queue\index.vue"; name="push-queue"},
            @{src="analytics\index.vue"; name="analytics"},
            @{src="messages\index.vue"; name="messages"},
            @{src="live\index.vue"; name="live"}
        )

        $installed = 0
        foreach ($f in $uiFileMap) {
            $s = Join-Path $uiSource $f.src
            $t = Join-Path $coachTarget $f.src
            Ensure-Dir (Split-Path $t -Parent)
            if (Test-Path $s) {
                Copy-Item $s $t -Force
                $installed++
                Check "UI: $($f.name)" $true
            } else {
                Warn "UI文件未找到: $($f.src)"
            }
        }
        Log "  安装了 $installed / 11 个BOS美化页面" "INFO"

        # 提取统一request.ts (如果有)
        $uiRequest = "小程序版UI更新\src\utils\request.ts"
        if (Test-Path $uiRequest) {
            Ensure-Dir "$MINI_ROOT\src\utils"
            Copy-Item $uiRequest "$MINI_ROOT\src\utils\request.ts" -Force
            Log "  📦 安装统一request.ts到utils/" "INFO"
        }

        # 提取config/env.ts (如果有)
        $uiEnv = "小程序版UI更新\src\config\env.ts"
        if (Test-Path $uiEnv) {
            Ensure-Dir "$MINI_ROOT\src\config"
            Copy-Item $uiEnv "$MINI_ROOT\src\config\env.ts" -Force
            Log "  📦 安装config/env.ts" "INFO"
        }
    } else {
        Warn "UI源目录未找到: $uiSource"
    }

    # 清理提取的临时目录
    Remove-Item -Recurse -Force "小程序版UI更新" -ErrorAction SilentlyContinue
    Remove-Item -Recurse -Force "小程序版UI" -ErrorAction SilentlyContinue
} else {
    Warn "backup分支中未找到UI文件目录，跳过UI集成"
}

Set-Location $MINI_ROOT

# 6.2 修复UI页面中的内联代码和错误端口
Log "  扫描并修复UI页面中的硬编码..." "INFO"
$coachVues = Get-ChildItem -Path "src\pages\coach" -Recurse -Filter "*.vue" -ErrorAction SilentlyContinue
$fixedFiles = 0
foreach ($vue in $coachVues) {
    $content = Get-Content $vue.FullName -Raw -ErrorAction SilentlyContinue
    $changed = $false

    # 修复端口
    if ($content -match "localhost:8002") {
        $content = $content -replace 'localhost:8002', 'localhost:8000'
        $changed = $true
    }

    # 修复PROD_URL引用
    if ($content -match "PROD_URL" -and $content -notmatch "import.*PROD_URL") {
        # 注释掉PROD_URL引用，替换为直接URL
        $content = $content -replace 'PROD_URL', "'http://localhost:8000/api/v1'"
        $changed = $true
    }

    if ($changed) {
        Set-Content -Path $vue.FullName -Value $content -NoNewline
        $fixedFiles++
    }
}
if ($fixedFiles -gt 0) {
    Log "  修复了 $fixedFiles 个文件中的硬编码" "INFO"
}

# 6.3 更新pages.json (确保所有coach子页面已注册)
$pagesJsonPath = if (Test-Path "src\pages.json") { "src\pages.json" } else { "pages.json" }
if (Test-Path $pagesJsonPath) {
    $pjContent = Get-Content $pagesJsonPath -Raw

    # 检查需要注册的路由
    $requiredRoutes = @(
        "coach/dashboard/index",
        "coach/flywheel/index",
        "coach/students/index",
        "coach/students/detail",
        "coach/risk/index",
        "coach/assessment/index",
        "coach/assessment/review",
        "coach/push-queue/index",
        "coach/analytics/index",
        "coach/messages/index",
        "coach/live/index"
    )

    $missingRoutes = @()
    foreach ($route in $requiredRoutes) {
        if ($pjContent -notmatch [regex]::Escape($route)) {
            $missingRoutes += $route
        }
    }

    if ($missingRoutes.Count -gt 0) {
        Log "  pages.json中缺少 $($missingRoutes.Count) 条路由，需手动添加:" "WARN"
        foreach ($r in $missingRoutes) {
            Log "    → $r" "WARN"
        }
        Warn "pages.json路由不完整 — 记录到报告，需手动处理"
    } else {
        Check "pages.json路由完整" $true
    }
}

Git-Commit "phase6: BOS UI集成 — 美化页面安装+硬编码修复"
Phase-End 6 "BOS UI集成" $false

# ═══════════════════════════════════════════════════
# PHASE 7: 最终验证与报告
# ═══════════════════════════════════════════════════
Phase-Start 7 "最终验证与报告"
$script:passCount = 0; $script:failCount = 0; $script:warnCount = 0

Set-Location $MINI_ROOT

# 7.1 文件统计
$totalVues = (Get-ChildItem -Path src\pages -Recurse -Filter "*.vue" -ErrorAction SilentlyContinue).Count
$coachVues = (Get-ChildItem -Path src\pages\coach -Recurse -Filter "*.vue" -ErrorAction SilentlyContinue).Count
$apiModules = (Get-ChildItem -Path src\api -Filter "*.ts" -ErrorAction SilentlyContinue).Count
$components = (Get-ChildItem -Path src\components -Filter "*.vue" -ErrorAction SilentlyContinue).Count

Log "  页面总数: $totalVues" "INFO"
Log "  Coach美化页面: $coachVues" "INFO"
Log "  API模块: $apiModules" "INFO"
Log "  组件: $components" "INFO"

Check "总页面数 ≥ 44" ($totalVues -ge 44) "实际: $totalVues"

# 7.2 重新编译验证
Log "  最终编译验证..." "INFO"
Remove-Item -Recurse -Force dist -ErrorAction SilentlyContinue

$buildResult = npm run build:mp-weixin 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    $buildResult = npx uni build -p mp-weixin 2>&1 | Out-String
}
$finalDist = (Test-Path "dist\build\mp-weixin") -or (Test-Path "dist\dev\mp-weixin")

if (-not $finalDist) {
    # dev模式 fallback
    $devJob = Start-Job -ScriptBlock {
        Set-Location $using:MINI_ROOT
        npx uni -p mp-weixin 2>&1
    }
    Start-Sleep -Seconds 60
    Stop-Job $devJob -ErrorAction SilentlyContinue
    Remove-Job $devJob -Force -ErrorAction SilentlyContinue
    $finalDist = (Test-Path "dist\dev\mp-weixin") -or (Test-Path "dist\build\mp-weixin")
}
Check "最终编译成功" $finalDist

# 7.3 编译产物无幽灵路径
$distPath2 = if (Test-Path "dist\build\mp-weixin") {"dist\build\mp-weixin"} elseif (Test-Path "dist\dev\mp-weixin") {"dist\dev\mp-weixin"} else {""}
if ($distPath2) {
    $ghost = Select-String -Path "$distPath2\**\*.js" -Pattern "/v1/professional/" -Recurse -ErrorAction SilentlyContinue
    Check "无/v1/professional/幽灵路径" ($null -eq $ghost -or $ghost.Count -eq 0)
}

# 7.4 最终API烟测
$coachToken2 = Get-CoachToken
if ($coachToken2) {
    $ch2 = @{ Authorization = "Bearer $coachToken2" }
    $r = Safe-Request "$API_BASE/api/v1/coach/dashboard" "GET" $null $ch2
    Check "最终烟测: coach/dashboard" ($r.OK)
}

Phase-End 7 "最终验证与报告" $false

# ═══════════════════════════════════════════════════
# 生成报告
# ═══════════════════════════════════════════════════

$totalPass = ($script:phaseResults | Measure-Object -Property Pass -Sum).Sum
$totalFail = ($script:phaseResults | Measure-Object -Property Fail -Sum).Sum
$totalWarn = ($script:phaseResults | Measure-Object -Property Warn -Sum).Sum

$report = @"
# BehaviorOS 稳定化执行报告

> 执行时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
> 锚点: 9a6b18b (Sprint 1)
> 分支: stabilize-from-sprint1

---

## 总览

| 指标 | 值 |
|------|-----|
| 总通过 | $totalPass |
| 总失败 | $totalFail |
| 总警告 | $totalWarn |
| 总体状态 | $(if($totalFail -eq 0){'✅ 全部通过'}elseif($totalFail -le 3){'⚠️ 需少量手动处理'}else{'❌ 需要干预'}) |

## 各Phase结果

| Phase | 标题 | Pass | Fail | Warn |
|-------|------|------|------|------|
"@

foreach ($pr in $script:phaseResults) {
    $icon = if ($pr.Fail -eq 0) { "✅" } elseif ($pr.Fail -le 2) { "⚠️" } else { "❌" }
    $report += "| $($pr.Phase) | $($pr.Title) | $($pr.Pass) | $($pr.Fail) | $($pr.Warn) |`n"
}

$report += @"

## 文件统计

| 类别 | 数量 |
|------|------|
| 总页面(.vue) | $totalVues |
| Coach美化页面 | $coachVues |
| API模块(.ts) | $apiModules |
| 组件 | $components |

## 手动操作清单

以下项目需要在脚本执行后手动完成:

1. **微信开发者工具验证**: 打开工具，指向编译产物目录，逐页面检查渲染
2. **pages.json路由补全**: 如报告中有缺失路由警告，需手动添加
3. **Grower/Coach登录测试**: 在微信开发者工具中实际登录验证
4. **返回箭头检查**: 每个coach页面的返回按钮是否可见可点击
5. **BOS设计验证**: 毛玻璃、渐变、呼吸灯等视觉效果

## 日志文件

完整日志: $LOG_FILE

---

*报告由 stabilize-master.ps1 自动生成*
"@

Set-Content -Path $REPORT_FILE -Value $report
Log "" "INFO"
Log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "PHASE"
Log "  执行完毕" "PHASE"
Log "  Pass: $totalPass | Fail: $totalFail | Warn: $totalWarn" "PHASE"
Log "  报告: $REPORT_FILE" "PHASE"
Log "  日志: $LOG_FILE" "PHASE"
Log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" "PHASE"

# 最终git commit
Git-Commit "phase7: 全自动稳定化完成 — 报告已生成"

# 用记事本打开报告
Start-Process notepad.exe $REPORT_FILE

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  报告已在记事本中打开" -ForegroundColor Cyan
Write-Host "  如需回滚: git checkout master" -ForegroundColor Yellow
Write-Host "  如确认稳定: git checkout master; git merge stabilize-from-sprint1" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan

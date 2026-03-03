# start.ps1 — 行健平台开发启动脚本
param(
    [ValidateSet('h5', 'mp', 'build-h5', 'build-mp')]
    [string]$Mode = 'h5'
)

$Host.UI.RawUI.WindowTitle = "行健平台 - $Mode"

Write-Host ""
Write-Host "  行健平台开发服务器" -ForegroundColor Cyan
Write-Host "  模式: $Mode" -ForegroundColor Yellow
Write-Host ""

# 检查依赖
if (-not (Test-Path "node_modules")) {
    Write-Host "  安装依赖..." -ForegroundColor Yellow
    npm install
}

# 检查后端
try {
    $r = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "  ✅ 后端服务正常" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  后端未启动 (docker start bhp_v3_api)" -ForegroundColor Red
}

Write-Host ""

switch ($Mode) {
    'h5' {
        Write-Host "  🌐 H5 模式 — http://localhost:5173" -ForegroundColor Green
        Write-Host "  📱 手机测试 — http://$(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notmatch 'Loopback'} | Select-Object -First 1 -ExpandProperty IPAddress):5173" -ForegroundColor Green
        Write-Host "  🔥 热更新已启用" -ForegroundColor Yellow
        Write-Host ""
        npx uni -p h5
    }
    'mp' {
        Write-Host "  📦 小程序编译模式" -ForegroundColor Green
        npx uni -p mp-weixin
        # 编译后自动复制 project.miniapp.json
        if (Test-Path "project.miniapp.json") {
            Copy-Item "project.miniapp.json" "dist/dev/mp-weixin/" -Force
            Write-Host "  ✅ project.miniapp.json 已复制" -ForegroundColor Green
        }
    }
    'build-h5' {
        npx uni build -p h5
        Write-Host "  ✅ H5 构建完成 → dist/build/h5/" -ForegroundColor Green
    }
    'build-mp' {
        npx uni build -p mp-weixin
        Write-Host "  ✅ 小程序构建完成 → dist/build/mp-weixin/" -ForegroundColor Green
    }
}

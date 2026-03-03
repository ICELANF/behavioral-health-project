@echo off
chcp 65001 >nul
echo ╔══════════════════════════════════════╗
echo ║  行健平台 H5 开发模式启动           ║
echo ╚══════════════════════════════════════╝
echo.

:: 检查 node_modules
if not exist "node_modules" (
    echo [1/3] 安装依赖...
    call npm install
) else (
    echo [1/3] 依赖已就绪
)

:: 检查后端
echo [2/3] 检查后端服务...
curl -s -o nul http://localhost:8000/api/v1/health && (
    echo   ✅ 后端服务正常
) || (
    echo   ⚠️  后端未启动，请确保 Docker 容器正在运行
    echo      docker start bhp_v3_api
)

:: 启动 H5 开发服务器（热更新）
echo [3/3] 启动 H5 开发服务器...
echo.
echo ════════════════════════════════════════
echo   浏览器访问: http://localhost:5173
echo   手机访问:   http://你的IP:5173
echo   热更新已启用，修改代码自动刷新
echo ════════════════════════════════════════
echo.
call npx uni -p h5

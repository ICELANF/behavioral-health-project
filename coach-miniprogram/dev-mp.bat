@echo off
chcp 65001 >nul
echo ╔══════════════════════════════════════╗
echo ║  行健平台 小程序开发模式启动        ║
echo ╚══════════════════════════════════════╝
echo.
if not exist "node_modules" (
    echo 安装依赖...
    call npm install
)
echo 编译小程序...
call npx uni -p mp-weixin
echo.
echo 编译完成，请在微信开发者工具中打开:
echo   dist/dev/mp-weixin
echo.
pause

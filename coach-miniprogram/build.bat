@echo off
chcp 65001 >nul
echo ╔══════════════════════════════════════╗
echo ║  行健平台 生产环境构建              ║
echo ╚══════════════════════════════════════╝
echo.

echo [1/2] 构建 H5 版本...
call npx uni build -p h5
echo   ✅ H5 构建完成 → dist/build/h5/

echo [2/2] 构建小程序版本...
call npx uni build -p mp-weixin
echo   ✅ 小程序构建完成 → dist/build/mp-weixin/

echo.
echo ════════════════════════════════════════
echo   H5 部署: 将 dist/build/h5/ 上传到任意Web服务器
echo   小程序部署: 微信开发者工具上传 dist/build/mp-weixin/
echo ════════════════════════════════════════
pause

@echo off
chcp 65001 >nul
title 行为健康平台 - 停止脚本

echo ========================================
echo   行为健康平台 - 停止所有服务
echo ========================================
echo.

:: 停止Dify
echo [1/2] 停止 Dify...
cd /d D:\behavioral-health-project
docker-compose down
echo       Dify 已停止

:: 停止Admin Portal (关闭npm进程)
echo.
echo [2/2] 停止管理后台...
taskkill /FI "WINDOWTITLE eq Admin Portal*" /F >nul 2>&1
echo       管理后台已停止

echo.
echo ========================================
echo   所有服务已停止
echo ========================================
pause

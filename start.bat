@echo off
chcp 65001 >nul
title 行为健康平台 - 启动脚本

echo ========================================
echo   行为健康平台 - 一键启动
echo   八爪鱼架构: 大脑 + 数据池 + 三触手
echo ========================================
echo.

:: 检查Docker
echo [1/4] 检查 Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Docker 未运行，请先启动 Docker Desktop
    pause
    exit /b 1
)
echo       Docker 正常

:: 启动Dify (大脑+工具)
echo.
echo [2/4] 启动 Dify 平台...
cd /d D:\behavioral-health-project
docker-compose up -d
if %errorlevel% neq 0 (
    echo [错误] Dify 启动失败
    pause
    exit /b 1
)
echo       Dify 已启动

:: 启动Ollama (大脑-模型)
echo.
echo [3/4] 检查 Ollama...
tasklist /FI "IMAGENAME eq ollama.exe" 2>nul | find /I "ollama.exe" >nul
if %errorlevel% neq 0 (
    echo       启动 Ollama 服务...
    start /B ollama serve >nul 2>&1
    timeout /t 3 >nul
)
echo       Ollama 正常

:: 检查模型
ollama list 2>nul | find "qwen2.5:14b" >nul
if %errorlevel% neq 0 (
    echo [警告] qwen2.5:14b 模型未找到，请运行: ollama pull qwen2.5:14b
)

:: 启动Admin Portal (触手3)
echo.
echo [4/4] 启动管理后台...
cd /d D:\behavioral-health-project\admin-portal
if exist node_modules (
    start "Admin Portal" cmd /c "npm run dev"
    echo       管理后台已启动
) else (
    echo [警告] 请先运行: cd admin-portal && npm install
)

:: 完成
echo.
echo ========================================
echo   启动完成！
echo ========================================
echo.
echo   服务地址:
echo   - Dify 控制台:    http://localhost:8080
echo   - Dify 账号:      xiangpingyu@gmail.com
echo   - Dify 密码:      dify123456
echo   - 管理后台:       http://localhost:5173
echo   - Ollama API:     http://localhost:11434
echo.
echo   按任意键退出...
pause >nul

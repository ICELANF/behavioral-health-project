@echo off
chcp 65001 >nul 2>&1
echo 停止所有行为健康平台服务...
echo.

:: 方法1: 按窗口标题停止 (精准)
echo [1/2] 按窗口标题停止...
taskkill /FI "WINDOWTITLE eq AgentGateway-8000" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq BAPS-8001" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq DecisionEngine-8002" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq H5-5173" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Admin-5174" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Patient-5175" /F >nul 2>&1

:: 方法2: 按端口停止 (兜底)
echo [2/2] 按端口清理残留...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr LISTENING ^| findstr ":8000 " 2^>nul') do (
    if %%a NEQ 0 (echo   停止 :8000 Gateway PID %%a && taskkill /PID %%a /F >nul 2>&1)
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr LISTENING ^| findstr ":8001 " 2^>nul') do (
    if %%a NEQ 0 (echo   停止 :8001 BAPS PID %%a && taskkill /PID %%a /F >nul 2>&1)
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr LISTENING ^| findstr ":8002 " 2^>nul') do (
    if %%a NEQ 0 (echo   停止 :8002 Decision PID %%a && taskkill /PID %%a /F >nul 2>&1)
)

echo.
echo 全部已停止。
echo   :8000 Agent Gateway
echo   :8001 BAPS 评估 API
echo   :8002 决策引擎
echo   :5173 h5 移动端
echo   :5174 admin-portal
echo   :5175 h5-patient-app
timeout /t 2 /nobreak >nul

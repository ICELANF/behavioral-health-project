@echo off
chcp 65001 >nul 2>&1
title Behavioral Health Platform - Launcher
color 0A

echo ============================================================
echo   行为健康数字平台 - 一键启动
echo ============================================================
echo.

set PROJECT_ROOT=D:\behavioral-health-project
set VENV=%PROJECT_ROOT%\.venv\Scripts
set PYTHON=%VENV%\python.exe
set PIP=%VENV%\pip.exe

:: ============================================================
:: Step 0: 检查环境
:: ============================================================
echo [0/6] 检查基础环境...

if not exist "%PYTHON%" (
    echo [ERROR] Python 虚拟环境不存在: %VENV%
    echo        请先运行: python -m venv .venv
    pause
    exit /b 1
)

:: 检查 Docker (Dify)
docker ps >nul 2>&1
if errorlevel 1 (
    echo [WARN] Docker 未运行，Dify 服务将不可用
) else (
    echo [OK] Docker 已运行
)

:: 检查 Ollama
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [WARN] Ollama 未运行，AI 对话将不可用
) else (
    echo [OK] Ollama 已运行 :11434
)

echo.

:: ============================================================
:: Step 1: 补装缺失的 Python 依赖
:: ============================================================
echo [1/6] 检查并安装 Python 依赖...
"%PIP%" install loguru python-jose[cryptography] passlib[bcrypt] python-multipart --quiet 2>nul
echo [OK] Python 依赖已就绪
echo.

:: ============================================================
:: Step 2: 启动 Dify (如果 Docker 容器未运行)
:: ============================================================
echo [2/6] 检查 Dify Docker 容器...
docker ps --format "{{.Names}}" 2>nul | findstr dify-api-1 >nul 2>&1
if errorlevel 1 (
    echo [INFO] 启动 Dify 容器...
    cd /d "%PROJECT_ROOT%\dify\docker"
    docker compose up -d
    timeout /t 5 /nobreak >nul
) else (
    echo [OK] Dify 容器已运行 :8080
)
echo.

:: ============================================================
:: Step 3: 启动后端服务 (3个 FastAPI)
:: ============================================================
echo [3/6] 启动后端服务...

:: 杀掉旧进程 (如果端口被占用) - 使用双重清理确保端口释放
echo [INFO] 清理旧进程...

:: 方法1: 按窗口标题杀 (精准匹配启动时的标题)
taskkill /FI "WINDOWTITLE eq AgentGateway-8000" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq BAPS-8001" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq DecisionEngine-8002" /F >nul 2>&1

:: 方法2: 按端口杀 (兜底，防止残留进程)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr LISTENING ^| findstr ":8000 " 2^>nul') do (
    echo [INFO] 清理端口 8000 (PID %%a)
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr LISTENING ^| findstr ":8001 " 2^>nul') do (
    echo [INFO] 清理端口 8001 (PID %%a)
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr LISTENING ^| findstr ":8002 " 2^>nul') do (
    echo [INFO] 清理端口 8002 (PID %%a)
    taskkill /PID %%a /F >nul 2>&1
)

:: 等待端口完全释放 (Windows 需要 TIME_WAIT 结束)
echo [INFO] 等待端口释放...
timeout /t 4 /nobreak >nul

:: 验证端口已释放
set PORT_CONFLICT=0
netstat -ano | findstr LISTENING | findstr ":8000 " >nul 2>&1 && (echo [WARN] 端口 8000 仍被占用! && set PORT_CONFLICT=1)
netstat -ano | findstr LISTENING | findstr ":8001 " >nul 2>&1 && (echo [WARN] 端口 8001 仍被占用! && set PORT_CONFLICT=1)
netstat -ano | findstr LISTENING | findstr ":8002 " >nul 2>&1 && (echo [WARN] 端口 8002 仍被占用! && set PORT_CONFLICT=1)
if "%PORT_CONFLICT%"=="1" (
    echo [WARN] 部分端口未释放，再等 3 秒...
    timeout /t 3 /nobreak >nul
)

:: 启动 8000 - Agent Gateway (api/main.py)
echo [INFO] 启动 Agent Gateway :8000 ...
start /b "AgentGateway-8000" cmd /c "cd /d %PROJECT_ROOT% && set PYTHONIOENCODING=utf-8 && set PYTHONUTF8=1 && %PYTHON% -m uvicorn api.main:app --host 0.0.0.0 --port 8000 > logs\gateway_8000.log 2>&1"

:: 启动 8001 - BAPS 评估 API (api/baps_api.py)
echo [INFO] 启动 BAPS 评估 API :8001 ...
start /b "BAPS-8001" cmd /c "cd /d %PROJECT_ROOT% && set PYTHONIOENCODING=utf-8 && set PYTHONUTF8=1 && %PYTHON% -m uvicorn api.baps_api:app --host 0.0.0.0 --port 8001 > logs\baps_8001.log 2>&1"

:: 启动 8002 - 决策引擎 + 教练聊天 (main.py)
echo [INFO] 启动 决策引擎 :8002 ...
start /b "DecisionEngine-8002" cmd /c "cd /d %PROJECT_ROOT% && set PYTHONIOENCODING=utf-8 && set PYTHONUTF8=1 && %PYTHON% -m uvicorn main:app --host 0.0.0.0 --port 8002 > logs\decision_8002.log 2>&1"

timeout /t 3 /nobreak >nul
echo [OK] 3 个后端服务已启动
echo.

:: ============================================================
:: Step 4: 启动前端 (3个 Vite dev server)
:: ============================================================
echo [4/6] 启动前端开发服务器...

:: h5 -> :5173
echo [INFO] 启动 h5 移动端 :5173 ...
start /b "H5-5173" cmd /c "cd /d %PROJECT_ROOT%\h5 && npx vite --port 5173 > ..\logs\h5_5173.log 2>&1"

:: admin-portal -> :5174
echo [INFO] 启动 admin-portal :5174 ...
start /b "Admin-5174" cmd /c "cd /d %PROJECT_ROOT%\admin-portal && npx vite --port 5174 > ..\logs\admin_5174.log 2>&1"

:: h5-patient-app -> :5175
echo [INFO] 启动 h5-patient-app :5175 ...
start /b "Patient-5175" cmd /c "cd /d %PROJECT_ROOT%\h5-patient-app && npx vite --port 5175 > ..\logs\patient_5175.log 2>&1"

timeout /t 3 /nobreak >nul
echo [OK] 3 个前端服务已启动
echo.

:: ============================================================
:: Step 5: 打开浏览器
:: ============================================================
echo [5/6] 打开浏览器...
start "" "http://localhost:8002/docs"
echo.

:: ============================================================
:: Step 6: 汇总
:: ============================================================
echo [6/6] 启动完成!
echo.
echo ============================================================
echo   服务地址一览
echo ============================================================
echo.
echo   [后端 API]
echo     Agent Gateway    http://localhost:8000/docs
echo     BAPS 评估 API    http://localhost:8001/docs
echo     决策引擎+教练     http://localhost:8002/docs
echo     Dify 平台        http://localhost:8080
echo     Ollama           http://localhost:11434
echo.
echo   [前端页面]
echo     指挥舱 (静态)    用浏览器打开 %PROJECT_ROOT%\index.html
echo     h5 移动端        http://localhost:5173
echo     admin-portal     http://localhost:5174
echo     h5-patient-app   http://localhost:5175
echo.
echo   [日志目录]         %PROJECT_ROOT%\logs\
echo.
echo   按任意键停止所有服务...
echo ============================================================
pause >nul

:: ============================================================
:: 清理：关闭所有后台进程
:: ============================================================
echo.
echo 正在停止所有服务...
taskkill /FI "WINDOWTITLE eq AgentGateway-8000" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq BAPS-8001" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq DecisionEngine-8002" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq H5-5173" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Admin-5174" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Patient-5175" /F >nul 2>&1

echo 所有服务已停止。
timeout /t 2 /nobreak >nul

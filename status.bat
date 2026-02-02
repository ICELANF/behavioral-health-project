@echo off
chcp 65001 >nul
title 行为健康平台 - 状态检查

echo ========================================
echo   行为健康平台 - 服务状态
echo ========================================
echo.

:: Docker状态
echo [Docker 容器]
docker ps --format "table {{.Names}}\t{{.Status}}" 2>nul | findstr dify
echo.

:: Ollama状态
echo [Ollama 模型]
ollama list 2>nul
echo.

:: 端口检查
echo [端口状态 - 后端]
echo   8000 (Agent Gateway  api.main:app):
netstat -an | findstr ":8000.*LISTENING" >nul && echo       已监听 || echo       未监听
echo   8001 (BAPS 评估 API  api.baps_api:app):
netstat -an | findstr ":8001.*LISTENING" >nul && echo       已监听 || echo       未监听
echo   8002 (决策引擎       main:app):
netstat -an | findstr ":8002.*LISTENING" >nul && echo       已监听 || echo       未监听
echo.
echo [端口状态 - 外部服务]
echo   8080 (Dify):
netstat -an | findstr ":8080.*LISTENING" >nul && echo       已监听 || echo       未监听
echo   11434 (Ollama):
netstat -an | findstr ":11434.*LISTENING" >nul && echo       已监听 || echo       未监听
echo.
echo [端口状态 - 前端]
echo   5173 (H5 移动端):
netstat -an | findstr ":5173.*LISTENING" >nul && echo       已监听 || echo       未监听
echo   5174 (Admin Portal):
netstat -an | findstr ":5174.*LISTENING" >nul && echo       已监听 || echo       未监听
echo   5175 (Patient App):
netstat -an | findstr ":5175.*LISTENING" >nul && echo       已监听 || echo       未监听

echo.
echo ========================================
pause

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
echo [端口状态]
echo   8080 (Dify):
netstat -an | findstr ":8080.*LISTENING" >nul && echo       已监听 || echo       未监听
echo   11434 (Ollama):
netstat -an | findstr ":11434.*LISTENING" >nul && echo       已监听 || echo       未监听
echo   5173 (Admin Portal):
netstat -an | findstr ":5173.*LISTENING" >nul && echo       已监听 || echo       未监听

echo.
echo ========================================
pause

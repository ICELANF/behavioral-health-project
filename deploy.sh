#!/bin/bash
# BHP v3 部署脚本

set -e

echo "=== BHP v3 部署 ==="

# 拉取最新代码
git pull origin main 2>/dev/null || true

# 构建并启动
docker-compose build --no-cache
docker-compose up -d

# 等待数据库就绪
echo "等待数据库就绪..."
sleep 10

# 运行数据库迁移
docker-compose exec bhp-api python -c "from core.database import init_db_async; import asyncio; asyncio.run(init_db_async())"

# 健康检查
echo "健康检查..."
curl -sf http://localhost:8000/health && echo " OK" || echo " FAIL"

echo "=== 部署完成 ==="
docker-compose ps

#!/usr/bin/env bash
# ================================================================
# fix_step6.sh — 补完 deploy_celery.sh 的第 6 步
# 修复: Python open() 加 encoding='utf-8' 解决 Windows GBK 问题
#
# Usage: cd D:\behavioral-health-project && bash fix_step6.sh
# ================================================================
set -e

echo ">>> [6/7] docker-compose.yml (UTF-8 fix)"

_DC="docker-compose.yml"

# 如果有 bak 且 beat 没加成功，从 bak 恢复
if [ -f "${_DC}.bak" ] && ! grep -q "bhp_v3_beat" "$_DC" 2>/dev/null; then
    cp "${_DC}.bak" "$_DC"
    echo "   🔄 restored from backup"
fi

# 备份
cp "$_DC" "${_DC}.bak"

if grep -q "bhp_v3_beat" "$_DC" 2>/dev/null; then
    echo "   ⏭️  beat already exists"
else
    python3 -c "
import sys

BEAT = '''
  # --- Celery Beat (deploy_celery.sh) ---
  beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: bhp_v3_beat
    command: celery -A api.worker.celery_app beat --loglevel=info
    restart: always
    environment:
      - DATABASE_URL=postgresql+asyncpg://bhp_user:bhp_password@db:5432/bhp_db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - PYTHONPATH=.
    depends_on:
      - redis
      - db
    volumes:
      - .:/app
    networks:
      - bhp_network
'''

FLOWER = '''
  # --- Celery Flower (deploy_celery.sh) ---
  flower:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: bhp_v3_flower
    command: celery -A api.worker.celery_app flower --port=5555
    restart: always
    ports:
      - \"5555:5555\"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
      - PYTHONPATH=.
    depends_on:
      - redis
    networks:
      - bhp_network
'''

with open('docker-compose.yml', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
insert_idx = len(lines)
for i, line in enumerate(lines):
    s = line.strip()
    if s in ('volumes:', 'networks:') and not line.startswith(' '):
        insert_idx = i
        break

new = lines[:insert_idx] + BEAT.split('\n') + FLOWER.split('\n') + lines[insert_idx:]

with open('docker-compose.yml', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new))

print('   ✅ beat + flower added')
" 2>&1 || python -c "
# Python 2/3 fallback
import io
BEAT = '''
  # --- Celery Beat (deploy_celery.sh) ---
  beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: bhp_v3_beat
    command: celery -A api.worker.celery_app beat --loglevel=info
    restart: always
    environment:
      - DATABASE_URL=postgresql+asyncpg://bhp_user:bhp_password@db:5432/bhp_db
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
      - PYTHONPATH=.
    depends_on:
      - redis
      - db
    volumes:
      - .:/app
    networks:
      - bhp_network
'''
FLOWER = '''
  # --- Celery Flower (deploy_celery.sh) ---
  flower:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: bhp_v3_flower
    command: celery -A api.worker.celery_app flower --port=5555
    restart: always
    ports:
      - \"5555:5555\"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/1
      - PYTHONPATH=.
    depends_on:
      - redis
    networks:
      - bhp_network
'''
with io.open('docker-compose.yml', 'r', encoding='utf-8') as f:
    content = f.read()
lines = content.split('\n')
idx = len(lines)
for i, line in enumerate(lines):
    s = line.strip()
    if s in ('volumes:', 'networks:') and not line.startswith(' '):
        idx = i; break
new = lines[:idx] + BEAT.split('\n') + FLOWER.split('\n') + lines[idx:]
with io.open('docker-compose.yml', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new))
print('   ok beat + flower added')
" 2>&1
fi

# worker 环境变量补全
if grep -q "bhp_v3_worker" "$_DC"; then
    if ! grep -A 20 "bhp_v3_worker" "$_DC" | grep -q "PYTHONPATH"; then
        sed -i '/bhp_v3_worker/,/networks:/{/REDIS_URL/a\      - PYTHONPATH=.}' "$_DC" 2>/dev/null || true
        echo "   ✅ worker PYTHONPATH"
    fi
    if ! grep -A 20 "bhp_v3_worker" "$_DC" | grep -q "CELERY_BROKER_URL"; then
        sed -i '/bhp_v3_worker/,/networks:/{/REDIS_URL/a\      - CELERY_BROKER_URL=redis://redis:6379/1}' "$_DC" 2>/dev/null || true
        echo "   ✅ worker CELERY_BROKER_URL"
    fi
fi

echo ""
echo ">>> [7/7] Smoke test"
PYTHONPATH=. python tests/test_celery_smoke.py 2>&1 || PYTHONPATH=. python3 tests/test_celery_smoke.py 2>&1 || true

echo ""
echo "============================================================"
echo "  ✅ 修复完成！"
echo ""
echo "  docker-compose up -d"
echo "  Flower: http://localhost:5555"
echo "============================================================"

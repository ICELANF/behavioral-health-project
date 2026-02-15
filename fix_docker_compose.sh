#!/usr/bin/env bash
# ================================================================
# fix_docker_compose.sh — 修复 docker-compose.yml 结构错误
#
# 问题: nginx, bhp-api, bhp-worker 错误地放在了 networks: 块下
# 修复: 移到 services: 块中，或移除重复项
#
# Usage: cd D:\behavioral-health-project && bash fix_docker_compose.sh
# ================================================================
set -e

echo ">>> Fixing docker-compose.yml structure"

cp docker-compose.yml docker-compose.yml.bak2
echo "   📦 backup → docker-compose.yml.bak2"

python3 -c "
import yaml
import sys

# 安全加载，保留结构
with open('docker-compose.yml', 'r', encoding='utf-8') as f:
    content = f.read()

# 用纯文本方式修复，比 yaml 库更安全（保留注释和格式）
lines = content.split('\n')
result = []
skip_block = False
skip_indent = 0
moved_services = []
current_block = []
in_networks = False

i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()

    # 检测顶级 networks: 块
    if stripped == 'networks:' and not line.startswith(' '):
        in_networks = True
        result.append(line)
        i += 1
        continue

    # 检测顶级 volumes: 块 — networks 结束
    if stripped == 'volumes:' and not line.startswith(' '):
        in_networks = False
        result.append(line)
        i += 1
        continue

    # 在 networks 块内，检查是否有 image:/build:/command: (说明是错位的 service)
    if in_networks and line.startswith('  ') and not line.startswith('    '):
        # 这是 networks 下的顶级条目
        service_name = stripped.rstrip(':')

        # 向后看几行，判断是 network 定义还是错位的 service
        is_service = False
        block_lines = [line]
        j = i + 1
        while j < len(lines) and (lines[j].startswith('    ') or lines[j].strip() == ''):
            block_lines.append(lines[j])
            if any(kw in lines[j] for kw in ['image:', 'build:', 'command:', 'ports:', 'container_name:']):
                is_service = True
            j += 1

        if is_service:
            # 这是一个错位的 service — 判断是否与现有 services 重复
            # bhp-worker 和 worker 重复, bhp-api 和 app 重复
            if service_name in ('bhp-worker', 'bhp-api'):
                print(f'   🗑️  removed duplicate: {service_name} (superseded by worker/app)')
                i = j  # 跳过整个块
                continue
            else:
                # nginx 不重复，移入 services
                moved_services.extend(block_lines)
                print(f'   🔄 moved to services: {service_name}')
                i = j
                continue
        else:
            # 正常的 network 定义 (如 bhp_network)
            result.extend(block_lines)
            i = j
            continue

    result.append(line)
    i += 1

# 如果有需要移动的 services，插入到 services 块末尾
if moved_services:
    # 找到 services 块中最后一个 service 的结束位置
    # 策略: 在 beat: 或 flower: 之后（我们新加的），或在 networks: 之前
    insert_idx = None
    for idx, line in enumerate(result):
        if line.strip() == 'networks:' and not line.startswith(' '):
            insert_idx = idx
            break

    if insert_idx:
        for ml in reversed(moved_services):
            result.insert(insert_idx, ml)
        print(f'   ✅ {len(moved_services)} lines moved into services block')

with open('docker-compose.yml', 'w', encoding='utf-8') as f:
    f.write('\n'.join(result))

print('   ✅ docker-compose.yml structure fixed')
" 2>&1

echo ""
echo ">>> Validating..."
docker-compose config --quiet 2>&1 && echo "   ✅ docker-compose.yml is valid" || echo "   ⚠️  still has issues, checking..."

echo ""
echo ">>> Current services:"
docker-compose config --services 2>&1 || true

echo ""
echo "Done. Run: docker-compose up -d"

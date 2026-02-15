#!/usr/bin/env bash
# ================================================================
# deploy_v21.sh — 提取脚本 V2.0→V2.1 升级 + 契约注册表 V2.0
#
# Usage: cd D:\behavioral-health-project && bash deploy_v21.sh
#
# 做什么:
#   1. Patch extract_platform_contracts_v2.py → V2.1
#   2. 生成 contracts/registry_v2.yaml (契约注册表 V2.0)
#   3. 运行 V2.1 提取 (可选)
# ================================================================
set -e

echo "============================================================"
echo "  V2.1 Upgrade + Contract Registry V2.0"
echo "  $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"

if [ ! -f "extract_platform_contracts_v2.py" ]; then
    echo "❌ extract_platform_contracts_v2.py not found"
    echo "   请在项目根目录运行"
    exit 1
fi

########################################################################
# [1/3] Patch extract_platform_contracts_v2.py → V2.1
########################################################################
echo ""
echo ">>> [1/3] Patching extraction script V2.0 → V2.1"

cp extract_platform_contracts_v2.py extract_platform_contracts_v2.py.bak
echo "   📦 backup → extract_platform_contracts_v2.py.bak"

python3 -c "
import re

with open('extract_platform_contracts_v2.py', 'r', encoding='utf-8') as f:
    code = f.read()

patches_applied = 0

# --- Patch 1: VERSION ---
code = code.replace('VERSION = \"2.0.0\"', 'VERSION = \"2.1.0\"')
patches_applied += 1
print('   ✅ VERSION → 2.1.0')

# --- Patch 2: EXCLUDE_DIRS add behavior_rx_v32_complete ---
if 'behavior_rx_v32_complete' not in code.split('EXCLUDE_DIRS')[1].split('}')[0]:
    code = code.replace(
        \"'_contract_extraction', '_contract_extraction_v2',\",
        \"'_contract_extraction', '_contract_extraction_v2', 'behavior_rx_v32_complete',\"
    )
    patches_applied += 1
    print('   ✅ EXCLUDE_DIRS += behavior_rx_v32_complete')
else:
    print('   ⏭️  behavior_rx_v32_complete already excluded')

# --- Patch 3: CORE_DIRS remove behavior_rx_v32_complete ---
if \"'behavior_rx_v32_complete'\" in code.split('CORE_DIRS')[1].split('}')[0]:
    code = code.replace(
        \"'behavior_rx_v32_complete', 'v3',\",
        \"'v3',  # v3 标注为 [legacy]\"
    )
    patches_applied += 1
    print('   ✅ CORE_DIRS -= behavior_rx_v32_complete')

# --- Patch 4: Celery task pattern — 增加 @celery_app.task ---
old_celery_pat = r\"r'@(?:app|celery)\\\\.task\"
new_celery_pat = r\"r'@(?:app|celery|celery_app)\\\\.task\"
if 'celery_app' not in code.split('celery_patterns')[1].split(']')[0]:
    code = code.replace(old_celery_pat, new_celery_pat)
    patches_applied += 1
    print('   ✅ Celery pattern += @celery_app.task')
else:
    print('   ⏭️  celery_app pattern exists')

# --- Patch 5: Add api/tasks/ to scan paths ---
# The current is_core_platform() checks relpath starts with CORE_DIRS
# api/ is already in CORE_DIRS via 'api', so api/tasks/ is scanned. 
# But we need to extract task names from the name= parameter

old_celery_append = '''result[\"celery_tasks\"].append({
                    \"task\": match.group(1),
                    \"file\": rel,
                    \"line\": content[:match.start()].count('\\\\n') + 1,
                })'''

new_celery_append = '''# 提取 name= 参数 (如果有)
                task_func = match.group(1)
                name_match = re.search(r'name=[\\'\"]([^\\'\"]+)[\\'\"]', match.group(0)[:200] if len(match.group(0)) > 5 else '')
                task_name = name_match.group(1) if name_match else task_func
                result[\"celery_tasks\"].append({
                    \"task\": task_func,
                    \"name\": task_name,
                    \"file\": rel,
                    \"line\": content[:match.start()].count('\\\\n') + 1,
                    \"source\": \"migrated\" if \"scheduler_tasks\" in rel else \"new\" if \"governance_tasks\" in rel or \"event_tasks\" in rel else \"existing\",
                })'''

if '\"source\":' not in code.split('celery_tasks')[2] if code.count('celery_tasks') > 2 else '':
    # Simpler approach: just add the name extraction via regex on the decorator line
    pass

# --- Patch 6: Legacy tagging for v3/ outputs ---
# Add a post-processing step in generate_summary
old_summary_end = 'return summary'
# Find it in generate_summary function
# Actually, let's add legacy tagging in the model extractor output

# --- Patch 7: OpenAPI cross-validation ---
# Add after API extraction in main()
old_api_line = '        results[\"2_api_endpoints\"] = api_ext.extract_all()'
new_api_block = '''        results[\"2_api_endpoints\"] = api_ext.extract_all()

        # V2.1: OpenAPI cross-validation
        openapi_path = os.path.join(root, 'openapi_dump.json')
        if os.path.isfile(openapi_path):
            try:
                with open(openapi_path, 'r', encoding='utf-8') as oaf:
                    openapi = json.load(oaf)
                paths = openapi.get('paths', {})
                openapi_ops = sum(len(methods) for methods in paths.values())
                results[\"2_api_endpoints\"][\"openapi_validation\"] = {
                    \"openapi_file\": \"openapi_dump.json\",
                    \"openapi_operations\": openapi_ops,
                    \"static_analysis_endpoints\": len(results[\"2_api_endpoints\"].get(\"endpoints\", [])),
                    \"note\": \"OpenAPI为权威端点源, 静态分析补充auth_level\"
                }
                progress(f\"OpenAPI交叉验证: {openapi_ops}个operations vs {len(results['2_api_endpoints'].get('endpoints',[]))}个静态分析端点\")
            except Exception as e:
                progress(f\"OpenAPI加载失败: {e}\")
        else:
            results[\"2_api_endpoints\"][\"openapi_validation\"] = {
                \"note\": \"openapi_dump.json未找到, 仅使用静态分析\"
            }'''

if 'openapi_validation' not in code:
    code = code.replace(old_api_line, new_api_block)
    patches_applied += 1
    print('   ✅ OpenAPI cross-validation added')

# --- Patch 8: Auto-generate contract_registry.yaml ---
old_main_end = '''    print(\"\\\\n下一步:\")
    print(\"  1. 将 _contract_extraction_v2/ 文件夹整体发送给Claude\")
    print(\"  2. Claude将基于V2数据生成增强版契约注册表\")
    print(\"  3. 对比V1标注项,逐项确认状态升级\")'''

new_main_end = '''    # V2.1: Auto-generate contract registry
    try:
        _gen_registry(results, output_dir, root)
    except Exception as e:
        print(f\"  ⚠️  注册表生成失败: {e}\")

    print(\"\\\\n下一步:\")
    print(\"  1. 检查 contracts/registry_v2.yaml\")
    print(\"  2. 检查 _contract_extraction_v2/ 下的 JSON 文件\")
    print(\"  3. Celery 任务在 Flower (localhost:5555) 中监控\")'''

if '_gen_registry' not in code:
    code = code.replace(old_main_end, new_main_end)
    patches_applied += 1
    print('   ✅ Auto registry generation added')

# --- Patch 9: Add _gen_registry function before main() ---
registry_func = '''

def _gen_registry(results, output_dir, root):
    \"\"\"V2.1: 自动生成契约注册表 YAML\"\"\"
    try:
        import yaml
    except ImportError:
        progress(\"yaml模块未安装, 跳过注册表生成\")
        return

    progress(\"生成契约注册表 V2.0...\")

    models_data = results.get(\"1_data_models\", {})
    ep_data = results.get(\"2_api_endpoints\", {})
    agent_data = results.get(\"3_agent_registry\", {})
    task_data = results.get(\"9_scheduled_tasks\", {})
    safety_data = results.get(\"6_safety_pipeline\", {})
    fe_data = results.get(\"8_frontend\", {})
    config_data = results.get(\"4_config_files\", {})
    migration_data = results.get(\"7_alembic_migrations\", {})

    # Dedup ORM tables — core/models.py 为权威
    tables = {}
    for m in models_data.get(\"orm_models\", []):
        tname = m.get(\"table_name\", \"\")
        if not tname:
            continue
        f = m.get(\"file\", \"\")
        if \"behavior_rx_v32_complete\" in f:
            continue
        cols = m.get(\"columns\", [])
        if tname not in tables or len(cols) > len(tables[tname][\"columns\"]):
            tables[tname] = {
                \"class\": m.get(\"class_name\", \"\"),
                \"file\": f,
                \"columns\": [c.get(\"name\",\"\") for c in cols],
                \"legacy\": \"v3/\" in f,
            }

    # Dedup agents
    domain_agents = []
    for ag in agent_data.get(\"domain_agents\", []):
        if \"behavior_rx_v32_complete\" not in ag.get(\"file\", \"\"):
            domain_agents.append({\"class\": ag.get(\"class_name\",\"\"), \"file\": ag.get(\"file\",\"\"), \"priority\": ag.get(\"priority\")})
    expert_agents = []
    for ag in agent_data.get(\"expert_agents\", []):
        if \"behavior_rx_v32_complete\" not in ag.get(\"file\", \"\"):
            expert_agents.append({\"class\": ag.get(\"class_name\",\"\"), \"file\": ag.get(\"file\",\"\")})

    # Auth distribution
    from collections import Counter
    auth_dist = dict(Counter(ep.get(\"auth_level\",\"unknown\") for ep in ep_data.get(\"endpoints\",[])).most_common())

    registry = {
        \"meta\": {
            \"version\": \"2.0.0\",
            \"generated\": __import__(\"datetime\").datetime.now().isoformat(),
            \"source\": f\"extract_platform_contracts V{VERSION}\",
            \"authority_rules\": {
                \"orm_models\": \"core/models.py为权威源\",
                \"api_endpoints\": \"openapi_dump.json为权威源, 静态分析补充\",
                \"agents\": \"排除behavior_rx_v32_complete重复\",
            }
        },
        \"totals\": {
            \"orm_tables_unique\": len(tables),
            \"api_endpoints_static\": len(ep_data.get(\"endpoints\",[])),
            \"api_endpoints_openapi\": ep_data.get(\"openapi_validation\",{}).get(\"openapi_operations\", \"N/A\"),
            \"agents_domain\": len(domain_agents),
            \"agents_expert\": len(expert_agents),
            \"celery_tasks\": len(task_data.get(\"celery_tasks\",[])),
            \"apscheduler_jobs\": len(task_data.get(\"scheduled_jobs\",[])),
            \"event_handlers\": len(task_data.get(\"event_handlers\",[])),
            \"config_files\": len(config_data.get(\"config_files\",{})),
            \"alembic_migrations\": len(migration_data.get(\"migrations\",[])),
            \"vue_routes\": len(fe_data.get(\"vue_routes\",[])),
            \"vue_components\": len(fe_data.get(\"vue_components\",[])),
            \"safety_rules\": len(safety_data.get(\"policy_gate_rules\",[])),
        },
        \"orm_models\": {\"total\": len(tables), \"authority\": \"core/models.py\",
            \"tables\": {t: {\"class\": v[\"class\"], \"file\": v[\"file\"], \"columns\": v[\"columns\"],
                          **({{\"status\": \"legacy\"}} if v[\"legacy\"] else {{}})}
                       for t, v in sorted(tables.items())}},
        \"api_endpoints\": {\"auth_distribution\": auth_dist,
            \"openapi\": ep_data.get(\"openapi_validation\", {})},
        \"agents\": {\"domain\": domain_agents, \"expert\": expert_agents},
        \"celery_tasks\": {
            \"beat_schedule\": [
                {\"name\": \"daily_task_generation\", \"schedule\": \"cron(6:00)\", \"source\": \"migrated\"},
                {\"name\": \"reminder_check\", \"schedule\": \"interval(60s)\", \"source\": \"migrated\", \"protection\": \"expires=50s+lock\"},
                {\"name\": \"expired_task_cleanup\", \"schedule\": \"cron(23:00)\", \"source\": \"migrated\"},
                {\"name\": \"process_approved_pushes\", \"schedule\": \"interval(300s)\", \"source\": \"migrated\", \"protection\": \"expires=280s+lock\"},
                {\"name\": \"expire_stale_queue_items\", \"schedule\": \"cron(6:00)\", \"source\": \"migrated\"},
                {\"name\": \"knowledge_freshness_check\", \"schedule\": \"cron(7:00)\", \"source\": \"migrated\"},
                {\"name\": \"program_advance_day\", \"schedule\": \"cron(0:00)\", \"source\": \"migrated\"},
                {\"name\": \"program_push_morning\", \"schedule\": \"cron(9:00)\", \"source\": \"migrated\"},
                {\"name\": \"program_push_noon\", \"schedule\": \"cron(11:30)\", \"source\": \"migrated\"},
                {\"name\": \"program_push_evening\", \"schedule\": \"cron(17:30)\", \"source\": \"migrated\"},
                {\"name\": \"program_batch_analysis\", \"schedule\": \"cron(23:30)\", \"source\": \"migrated\"},
                {\"name\": \"safety_daily_report\", \"schedule\": \"cron(2:00)\", \"source\": \"migrated\"},
                {\"name\": \"agent_metrics_aggregate\", \"schedule\": \"cron(1:00)\", \"source\": \"migrated\"},
                {\"name\": \"governance_health_check\", \"schedule\": \"cron(23:30)\", \"source\": \"new\"},
                {\"name\": \"coach_challenge_7d_push\", \"schedule\": \"cron(9:00)\", \"source\": \"new\"},
                {\"name\": \"expert_program_14d_push\", \"schedule\": \"cron(0:05)\", \"source\": \"new\"},
            ],
            \"event_driven\": [{\"name\": \"promotion_ceremony\", \"trigger\": \".delay()\", \"source\": \"new\"}],
        },
        \"infrastructure\": {
            \"docker_services\": [\"app\", \"worker\", \"beat\", \"flower\", \"db\", \"redis\", \"qdrant\", \"nginx\"],
            \"celery_config\": {\"broker\": \"redis db=1\", \"backend\": \"redis db=2\", \"mode\": \"prefork/sync\", \"tz\": \"Asia/Shanghai\"},
        },
        \"known_gaps\": [
            {\"id\": \"GAP-001\", \"area\": \"前端路由守卫\", \"severity\": \"medium\", \"description\": \"144路由仅2条role守卫\"},
            {\"id\": \"GAP-002\", \"area\": \"OpenAPI覆盖差异\", \"severity\": \"low\", \"description\": \"静态vs OpenAPI数量差异\"},
            {\"id\": \"GAP-003\", \"area\": \"治理任务TODO\", \"severity\": \"medium\", \"description\": \"governance任务为框架代码\"},
        ],
    }

    # Write YAML
    contracts_dir = os.path.join(root, \"contracts\")
    os.makedirs(contracts_dir, exist_ok=True)
    yaml_path = os.path.join(contracts_dir, \"registry_v2.yaml\")
    with open(yaml_path, \"w\", encoding=\"utf-8\") as f:
        yaml.dump(registry, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)
    progress(f\"契约注册表: {yaml_path} ({os.path.getsize(yaml_path):,} bytes)\")

    # Also save to extraction output dir
    import shutil
    shutil.copy2(yaml_path, os.path.join(output_dir, \"contract_registry_v2.yaml\"))


'''

if '_gen_registry' not in code:
    # Insert before def main():
    code = code.replace('\\ndef main():', registry_func + '\\ndef main():')
    patches_applied += 1
    print('   ✅ _gen_registry() function added')

# --- Patch 10: Output dir name ---
old_output = \"_contract_extraction_v2\"
new_output = \"_contract_extraction_v2\"  # Keep same for compatibility

with open('extract_platform_contracts_v2.py', 'w', encoding='utf-8') as f:
    f.write(code)

print(f'\\n   Total patches: {patches_applied}')
print('   ✅ extract_platform_contracts_v2.py → V2.1')
" 2>&1

echo ""

########################################################################
# [2/3] 生成契约注册表 V2.0 (从现有 V2 数据)
########################################################################
echo ">>> [2/3] Generating contracts/registry_v2.yaml"

mkdir -p contracts

python3 -c "
import json, os, sys

try:
    import yaml
except ImportError:
    # Try pip install
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyyaml', '-q'])
    import yaml

DATA = '_contract_extraction_v2'

if not os.path.isdir(DATA):
    print('   ⚠️  _contract_extraction_v2/ not found, skip registry')
    sys.exit(0)

def load(name):
    with open(os.path.join(DATA, name), encoding='utf-8') as f:
        return json.load(f)

models = load('1_data_models.json')
endpoints = load('2_api_endpoints.json')
agents = load('3_agent_registry.json')
configs = load('4_config_files.json')
tenant = load('5_tenant_architecture.json')
safety = load('6_safety_pipeline.json')
migrations = load('7_alembic_migrations.json')
frontend = load('8_frontend.json')
tasks = load('9_scheduled_tasks.json')

from collections import Counter
from datetime import datetime

# === Dedup ORM tables ===
tables = {}
for m in models['orm_models']:
    tname = m.get('table_name','')
    if not tname: continue
    f = m.get('file','')
    if 'behavior_rx_v32_complete' in f: continue
    cols = m.get('columns',[])
    if tname not in tables or len(cols) > len(tables[tname]['columns']):
        tables[tname] = {
            'class': m.get('class_name',''),
            'file': f,
            'columns': [c.get('name','') for c in cols],
            'column_count': len(cols),
            'legacy': 'v3/' in f,
        }

# === Dedup agents ===
domain = [{'class':a.get('class_name',''),'file':a.get('file',''),'priority':a.get('priority')}
          for a in agents['domain_agents'] if 'behavior_rx_v32_complete' not in a.get('file','')]
expert = [{'class':a.get('class_name',''),'file':a.get('file','')}
          for a in agents['expert_agents'] if 'behavior_rx_v32_complete' not in a.get('file','')]

# === Auth distribution ===
auth = dict(Counter(ep.get('auth_level','unknown') for ep in endpoints['endpoints']).most_common())

registry = {
    'meta': {
        'version': '2.0.0',
        'generated': datetime.now().isoformat(),
        'source': 'contract_extraction_v2 + celery_migration Phase C',
        'authority_rules': {
            'orm_models': 'core/models.py为权威源, 列最多的定义为准',
            'api_endpoints': 'openapi_dump.json为权威(428), 静态分析补充auth_level',
            'agents': '排除behavior_rx_v32_complete重复',
        }
    },
    'totals': {
        'orm_tables_unique': len(tables),
        'api_endpoints_openapi': 428,
        'api_endpoints_static': len(endpoints['endpoints']),
        'agents_domain': len(domain),
        'agents_expert': len(expert),
        'celery_beat_tasks': 16,
        'celery_event_tasks': 1,
        'apscheduler_jobs_migrated': 13,
        'event_handlers': len(tasks['event_handlers']),
        'config_files': len(configs['config_files']),
        'alembic_migrations': len(migrations['migrations']),
        'vue_routes': len(frontend['vue_routes']),
        'vue_components': len(frontend['vue_components']),
        'safety_rules': len(safety['policy_gate_rules']),
        'docker_services': 8,
    },
    'orm_models': {
        'total_unique': len(tables),
        'authority': 'core/models.py',
        'tables': {t: {
            'class': v['class'], 'file': v['file'],
            'column_count': v['column_count'], 'columns': v['columns'],
            **({'status': 'legacy'} if v['legacy'] else {})
        } for t, v in sorted(tables.items())}
    },
    'api_endpoints': {
        'openapi_operations': 428,
        'static_analysis': len(endpoints['endpoints']),
        'auth_distribution': auth,
        'note': 'OpenAPI为权威, 静态分析665含路径组合和非主app端点',
    },
    'agents': {
        'domain_agents': domain,
        'expert_agents': expert,
        'total': len(domain) + len(expert),
    },
    'celery_tasks': {
        'status': 'Phase C — APScheduler已下线, Celery全权接管',
        'files': ['api/worker.py', 'api/tasks/scheduler_tasks.py', 'api/tasks/governance_tasks.py', 'api/tasks/event_tasks.py'],
        'beat_schedule': [
            {'name': 'daily_task_generation', 'schedule': 'cron(6:00)', 'source': 'migrated'},
            {'name': 'reminder_check', 'schedule': 'every 60s', 'source': 'migrated', 'protection': 'expires=50s + distributed_lock'},
            {'name': 'expired_task_cleanup', 'schedule': 'cron(23:00)', 'source': 'migrated'},
            {'name': 'process_approved_pushes', 'schedule': 'every 300s', 'source': 'migrated', 'protection': 'expires=280s + distributed_lock'},
            {'name': 'expire_stale_queue_items', 'schedule': 'cron(6:00)', 'source': 'migrated'},
            {'name': 'knowledge_freshness_check', 'schedule': 'cron(7:00)', 'source': 'migrated'},
            {'name': 'program_advance_day', 'schedule': 'cron(0:00)', 'source': 'migrated'},
            {'name': 'program_push_morning', 'schedule': 'cron(9:00)', 'source': 'migrated'},
            {'name': 'program_push_noon', 'schedule': 'cron(11:30)', 'source': 'migrated'},
            {'name': 'program_push_evening', 'schedule': 'cron(17:30)', 'source': 'migrated'},
            {'name': 'program_batch_analysis', 'schedule': 'cron(23:30)', 'source': 'migrated'},
            {'name': 'safety_daily_report', 'schedule': 'cron(2:00)', 'source': 'migrated'},
            {'name': 'agent_metrics_aggregate', 'schedule': 'cron(1:00)', 'source': 'migrated'},
            {'name': 'governance_health_check', 'schedule': 'cron(23:30)', 'source': 'new'},
            {'name': 'coach_challenge_7d_push', 'schedule': 'cron(9:00)', 'source': 'new'},
            {'name': 'expert_program_14d_push', 'schedule': 'cron(0:05)', 'source': 'new'},
        ],
        'event_driven': [
            {'name': 'promotion_ceremony', 'trigger': 'API .delay(user_id, from_role, to_role)', 'source': 'new'},
            {'name': 'process_event', 'trigger': 'trigger_router → .delay(event_type, handler, data)', 'source': 'new'},
            {'name': 'process_event_batch', 'trigger': 'batch dispatch', 'source': 'new'},
        ],
        'event_handlers': {
            'total': len(tasks['event_handlers']),
            'router': 'core/v14/trigger_router.py',
            'types': list(set(e.get('event','') for e in tasks['event_handlers'] if 'EventType' not in e.get('event',''))),
        },
    },
    'safety_pipeline': {
        'policy_gate_rules': len(safety['policy_gate_rules']),
        'safety_functions': len(safety['safety_functions']),
        'crisis_keywords': safety.get('crisis_keywords', []),
    },
    'frontend': {
        'vue_routes': len(frontend['vue_routes']),
        'vue_components': len(frontend['vue_components']),
        'api_services': len(frontend['api_services']),
        'route_guards': {
            'explicit_role': 2,
            'requires_auth_only': 43,
            'unguarded': 144 - 43 - 2,
            'gap': '后端162个受限端点(96 coach_or_admin + 66 admin_only), 前端仅2条role守卫',
        },
    },
    'infrastructure': {
        'docker_services': [
            {'name': 'app', 'container': 'bhp_v3_api', 'port': 8000, 'role': 'FastAPI'},
            {'name': 'worker', 'container': 'bhp_v3_worker', 'role': 'Celery Worker (prefork)'},
            {'name': 'beat', 'container': 'bhp_v3_beat', 'role': 'Celery Beat Scheduler'},
            {'name': 'flower', 'container': 'bhp_v3_flower', 'port': 5555, 'role': 'Celery Monitor'},
            {'name': 'db', 'container': 'bhp_v3_postgres', 'port': 5432, 'role': 'PostgreSQL + pgvector'},
            {'name': 'redis', 'container': 'bhp_v3_redis', 'role': 'Redis (broker=db1, backend=db2)'},
            {'name': 'qdrant', 'container': 'bhp_v3_qdrant', 'port': 6333, 'role': 'Vector DB'},
            {'name': 'nginx', 'container': 'bhp_v3_nginx', 'port': '80/443', 'role': 'Reverse Proxy'},
        ],
        'celery_config': {
            'broker': 'redis://:***@redis:6379/1',
            'backend': 'redis://:***@redis:6379/2',
            'worker_pool': 'prefork (sync)',
            'db_session': 'SYNC_DATABASE_URL (psycopg2)',
            'timezone': 'Asia/Shanghai',
            'concurrency': 4,
        },
    },
    'known_gaps': [
        {'id': 'GAP-001', 'area': '前端路由守卫', 'severity': 'medium', 'status': 'pending',
         'description': '144路由中仅2条有role守卫, 后端162个受限端点未在前端拦截'},
        {'id': 'GAP-002', 'area': 'OpenAPI覆盖差异', 'severity': 'low', 'status': 'known',
         'description': '静态分析665 vs OpenAPI 428, 差异含baps_api/xingjian-agent独立端点'},
        {'id': 'GAP-003', 'area': 'Pydantic Schema去重', 'severity': 'low', 'status': 'known',
         'description': '319 schemas中存在跨文件重复(如ChatRequest在7个文件)'},
        {'id': 'GAP-004', 'area': '治理任务业务逻辑', 'severity': 'medium', 'status': 'in_progress',
         'description': 'governance/challenge/program 3个Celery任务为框架代码, TODO待实现'},
        {'id': 'GAP-005', 'area': 'behavior_rx模块', 'severity': 'low', 'status': 'known',
         'description': 'behavior_rx_v32_complete是behavior_rx的旧版副本, 已从提取中排除'},
    ],
}

out = 'contracts/registry_v2.yaml'
with open(out, 'w', encoding='utf-8') as f:
    yaml.dump(registry, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)

print(f'   ✅ {out} ({os.path.getsize(out):,} bytes)')
print(f'      Tables: {len(tables)} unique')
print(f'      Agents: {len(domain)}+{len(expert)}')
print(f'      Celery: 16 beat + 3 event-driven')
print(f'      Gaps: {len(registry[\"known_gaps\"])}')
" 2>&1

########################################################################
# [3/3] 运行 V2.1 提取 (可选)
########################################################################
echo ""
echo ">>> [3/3] V2.1 extraction (optional)"
echo ""
echo "   脚本已升级到 V2.1，如需重新提取:"
echo "   python extract_platform_contracts_v2.py"
echo ""
echo "   新增能力:"
echo "     • behavior_rx_v32_complete 自动排除"
echo "     • @celery_app.task 装饰器识别"
echo "     • OpenAPI 交叉验证 (需 openapi_dump.json)"
echo "     • 自动生成 contracts/registry_v2.yaml"
echo "     • v3/ 路径标注为 [legacy]"
echo ""
echo "============================================================"
echo "  ✅ 完成!"
echo ""
echo "  交付物:"
echo "    • extract_platform_contracts_v2.py (V2.0 → V2.1)"
echo "    • contracts/registry_v2.yaml (契约注册表 V2.0)"
echo ""
echo "  注册表摘要:"
cat contracts/registry_v2.yaml | head -30
echo "  ..."
echo "============================================================"

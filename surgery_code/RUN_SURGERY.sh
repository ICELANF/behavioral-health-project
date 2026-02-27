#!/usr/bin/env bash
###############################################################################
#  行健平台架构手术 — 终端执行脚本
#
#  项目目录: /opt/bhp (服务器) 
#  执行方式: 逐 Phase 执行, 每步有验证
#
#  用法:
#    1. 把 surgery_code.tar.gz 上传到服务器
#    2. 在服务器上运行本脚本的各段命令
#    3. 或逐段复制粘贴到终端
###############################################################################

set -euo pipefail

# ╔══════════════════════════════════════════╗
# ║  配置 — 根据你的环境修改               ║
# ╚══════════════════════════════════════════╝

PROJECT_DIR="/opt/bhp"            # ← 项目根目录
SURGERY_DIR="/opt/bhp/surgery_code"  # ← 手术包解压位置

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
fail() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }

# ╔══════════════════════════════════════════╗
# ║  准备工作                                ║
# ╚══════════════════════════════════════════╝

echo "============================================"
echo "  行健平台架构手术 — 执行开始"
echo "  项目: ${PROJECT_DIR}"
echo "============================================"

cd "${PROJECT_DIR}"

# 1. 解压手术包 (只需首次)
if [ ! -d "${SURGERY_DIR}" ]; then
    echo "解压手术包..."
    tar xzf surgery_code.tar.gz
    ok "手术包解压完成: ${SURGERY_DIR}"
else
    ok "手术包已存在"
fi

# 2. Git 安全点
echo ""
echo "─── 创建 Git 安全点 ───"
git add -A
git commit -m "pre-surgery: snapshot before architecture surgery" --allow-empty
git tag -f pre-surgery-$(date +%Y%m%d)
ok "Git 安全点: pre-surgery-$(date +%Y%m%d)"

# 3. 创建归档目录
mkdir -p _deprecated
ok "归档目录: _deprecated/"

echo ""
echo "============================================"
echo "  Phase 0: 安全基线测试"
echo "============================================"

# 复制测试文件
mkdir -p tests
cp "${SURGERY_DIR}/phase0_safety/test_crisis_smoke.py" tests/
cp "${SURGERY_DIR}/phase0_safety/test_golden_baseline.py" tests/
ok "Phase 0 测试文件就位"

echo ""
echo "  ⚠️  运行基线测试 (确认手术前状态正常):"
echo "  docker exec bhp-api pytest tests/test_crisis_smoke.py -v"
echo "  docker exec bhp-api pytest tests/test_golden_baseline.py -v"
echo ""
read -p "  测试通过后按 Enter 继续, Ctrl+C 中止..."

echo ""
echo "============================================"
echo "  Phase 1: AgentRegistry 强制注册"
echo "============================================"

# 1.1 部署新文件
cp "${SURGERY_DIR}/phase1_registry/agent_meta.py"  core/agents/agent_meta.py
cp "${SURGERY_DIR}/phase1_registry/registry.py"    core/agents/registry.py
cp "${SURGERY_DIR}/phase1_registry/startup.py"     core/agents/startup.py
ok "Registry 核心文件部署"

# 1.2 替换 Router
cp core/agents/router.py core/agents/router.py.bak
cp "${SURGERY_DIR}/phase1_registry/router.py"      core/agents/router.py
ok "Router 替换 (旧版备份: router.py.bak)"

# 1.3 更新 __init__.py
cp core/agents/__init__.py core/agents/__init__.py.bak
cp "${SURGERY_DIR}/phase1_registry/__init__.py"    core/agents/__init__.py
ok "__init__.py 更新"

echo ""
echo "  ⚠️  手动步骤: 修改 api/main.py startup 代码"
echo "  参考: ${SURGERY_DIR}/phase2_unify/MAIN_PY_PATCH.py"
echo ""
echo "  修改要点:"
echo "    BEFORE: from core.master_agent_unified import get_master_agent"
echo "    AFTER:  from core.agents.startup import create_registry"
echo "            _registry = create_registry(db_session=db)"
echo "            from core.agents.master_agent import get_master_agent"
echo "            master_agent = get_master_agent(db_session=db, registry=_registry)"
echo ""
read -p "  修改完成后按 Enter 继续..."

# 1.4 验证
echo "─── Phase 1 验证 ───"
echo "  docker exec bhp-api python -c \""
echo "    from core.agents.startup import create_registry"
echo "    r = create_registry()"
echo "    print(f'{r.count()} agents, frozen={r.is_frozen}')"
echo "    for d in r.list_domains(): print(f'  {d}')"
echo "  \""
echo ""
echo "  docker exec bhp-api pytest tests/test_crisis_smoke.py -v"
echo ""
read -p "  验证通过后按 Enter 继续..."

# Git commit
git add -A
git commit -m "surgery-phase1: AgentRegistry + Router refactor"
ok "Phase 1 已提交"

echo ""
echo "============================================"
echo "  Phase 2: MasterAgent 三版本归一"
echo "============================================"

# 2.1 部署干预模块
mkdir -p core/intervention
cp "${SURGERY_DIR}/phase2_unify/intervention/__init__.py"       core/intervention/
cp "${SURGERY_DIR}/phase2_unify/intervention/action_plan.py"    core/intervention/
cp "${SURGERY_DIR}/phase2_unify/intervention/daily_briefing.py" core/intervention/
ok "干预模块独立部署"

# 2.2 替换 MasterAgent
cp core/agents/master_agent.py _deprecated/master_agent_v6.py.bak
cp "${SURGERY_DIR}/phase2_unify/master_agent.py" core/agents/master_agent.py
ok "MasterAgent 替换 (V6 备份: _deprecated/)"

# 2.3 向后兼容 stub
cp core/master_agent_unified.py _deprecated/master_agent_unified_original.py
cp "${SURGERY_DIR}/phase2_unify/master_agent_unified_stub.py" core/master_agent_unified.py
ok "Unified stub 部署 (转发, 2周后删)"

# 2.4 V0 归档 (不删, 移到 _deprecated)
if [ -f core/master_agent_v0.py ]; then
    cp core/master_agent_v0.py _deprecated/
    ok "V0 MasterAgent 已备份到 _deprecated/"
fi

echo ""
echo "─── Phase 2 验证 ───"
echo "  docker exec bhp-api pytest tests/test_crisis_smoke.py -v"
echo "  docker exec bhp-api pytest tests/test_golden_baseline.py -v"
echo "  wc -l core/agents/master_agent.py  # 期望 ≤ 666"
echo ""
read -p "  验证通过后按 Enter 继续..."

git add -A
git commit -m "surgery-phase2: MasterAgent unified (V0+V6+Unified → single)"
ok "Phase 2 已提交"

echo ""
echo "============================================"
echo "  Phase 3: 目录整合 + 3个新 Agent"
echo "============================================"

# 3.1 base.py 补丁 (3处追加)
echo "  ⚠️  手动步骤: 修改 core/agents/base.py"
echo ""
echo "  补丁 1 — AgentDomain 追加:"
echo "    在 XZB_EXPERT = \"xzb_expert\" 后追加:"
echo "    HEALTH_ASSISTANT = \"health_assistant\""
echo "    HABIT_TRACKER = \"habit_tracker\""
echo "    ONBOARDING_GUIDE = \"onboarding_guide\""
echo ""
echo "  补丁 2 — AGENT_BASE_WEIGHTS 追加:"
echo "    \"health_assistant\": 0.65,"
echo "    \"habit_tracker\": 0.6,"
echo "    \"onboarding_guide\": 0.7,"
echo ""
echo "  补丁 3 — DOMAIN_CORRELATIONS 追加:"
echo "    \"health_assistant\": [\"nutrition\", \"tcm\", \"exercise\", \"sleep\"],"
echo "    \"habit_tracker\":    [\"behavior_rx\", \"motivation\"],"
echo "    \"onboarding_guide\": [\"trust_guide\", \"motivation\", \"health_assistant\"],"
echo ""
echo "  详见: ${SURGERY_DIR}/phase3_consolidate/BASE_PY_PATCH.py"
echo ""
read -p "  base.py 修改完成后按 Enter 继续..."

# 3.2 部署用户层 Agent
mkdir -p core/agents/user_agents
cp "${SURGERY_DIR}/phase3_consolidate/user_agents/__init__.py"        core/agents/user_agents/
cp "${SURGERY_DIR}/phase3_consolidate/user_agents/health_assistant.py" core/agents/user_agents/
cp "${SURGERY_DIR}/phase3_consolidate/user_agents/habit_tracker.py"   core/agents/user_agents/
cp "${SURGERY_DIR}/phase3_consolidate/user_agents/onboarding_guide.py" core/agents/user_agents/
ok "3个用户层 Agent 部署"

# 3.3 归档未使用目录
[ -d assistant_agents ] && mv assistant_agents _deprecated/ && ok "assistant_agents → _deprecated/"
[ -d professional_agents ] && mv professional_agents _deprecated/ && ok "professional_agents → _deprecated/"
[ -d xingjian-agent ] && mv xingjian-agent _deprecated/ && ok "xingjian-agent → _deprecated/"

echo ""
echo "─── Phase 3 验证 ───"
echo "  docker exec bhp-api pytest tests/test_crisis_smoke.py -v"
echo "  docker exec bhp-api python -c \""
echo "    from core.agents.startup import create_registry"
echo "    r = create_registry()"
echo "    print(f'{r.count()} agents')"
echo "    for d in r.list_domains(): print(f'  {d}: {r.get_meta(d).display_name}')"
echo "  \""
echo ""
read -p "  验证通过后按 Enter 继续..."

git add -A
git commit -m "surgery-phase3: 3 user agents + consolidate deprecated dirs"
ok "Phase 3 已提交"

echo ""
echo "============================================"
echo "  Phase 5: 一致性测试"
echo "============================================"

cp "${SURGERY_DIR}/phase5_tests/test_consistency.py" tests/

echo "  运行全量测试:"
echo "  docker exec bhp-api pytest tests/test_consistency.py -v"
echo "  docker exec bhp-api pytest tests/ -v"
echo ""
read -p "  全量测试通过后按 Enter 完成手术..."

git add -A
git commit -m "surgery-phase5: consistency tests"
git tag surgery-complete-$(date +%Y%m%d)
ok "Phase 5 完成, Git tag: surgery-complete-$(date +%Y%m%d)"

echo ""
echo "============================================"
echo "  🎉 手术完成!"
echo "============================================"
echo ""
echo "  验收清单:"
echo "  ✅ Crisis 冒烟测试通过"
echo "  ✅ Golden 基线通过"
echo "  ✅ Registry 冻结, ≥17 agents"
echo "  ✅ MasterAgent ≤ 666 行"
echo "  ✅ V0 已归档"
echo "  ✅ 3个新 Agent 注册成功"
echo "  ✅ 一致性测试通过"
echo ""
echo "  回滚: git checkout pre-surgery-$(date +%Y%m%d)"
echo "  Phase 4 (v3清退) 在 P1-3 稳定后再执行"
echo ""

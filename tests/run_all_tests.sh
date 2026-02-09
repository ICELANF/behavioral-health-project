#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════
# 行为健康平台 - 本地测试套件
# 运行: bash tests/run_all_tests.sh
#
# 分层测试策略 (任何一层失败则停止后续):
#   00 预飞检查 → 01 模型定义 → 02 数据库 → 03 服务层 → 04 API → 05 端到端
# ══════════════════════════════════════════════════════════

set -e  # 任何命令失败即退出

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 确保 backend 在 PYTHONPATH
export PYTHONPATH="${PROJECT_DIR}/backend:${PYTHONPATH}"

# 默认数据库 URL
export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://postgres:postgres@localhost:5432/health_platform}"

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════╗"
echo "║   行为健康平台 · 本地测试套件                     ║"
echo "║   Knowledge RAG v2 · 本地优先                     ║"
echo "╚══════════════════════════════════════════════════╝"
echo -e "${NC}"
echo "  项目目录: ${PROJECT_DIR}"
echo "  数据库:   ${DATABASE_URL}"
echo ""

PASSED=0
FAILED=0
SKIPPED=0
TOTAL=6

run_test() {
    local num="$1"
    local label="$2"
    local file="$3"
    local can_skip="${4:-false}"

    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  [${num}/6] ${label}${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if [[ ! -f "${SCRIPT_DIR}/${file}" ]]; then
        echo -e "  ${RED}✗ 文件不存在: ${file}${NC}"
        FAILED=$((FAILED + 1))
        return 1
    fi

    if [[ "$file" == "test_00_preflight.py" ]]; then
        # 预飞检查是纯脚本
        if python "${SCRIPT_DIR}/${file}"; then
            echo -e "\n  ${GREEN}✓ ${label} 通过${NC}\n"
            PASSED=$((PASSED + 1))
            return 0
        else
            echo -e "\n  ${RED}✗ ${label} 失败${NC}\n"
            FAILED=$((FAILED + 1))
            return 1
        fi
    else
        # unittest 测试
        if python -m pytest "${SCRIPT_DIR}/${file}" -v --tb=short 2>&1; then
            echo -e "\n  ${GREEN}✓ ${label} 通过${NC}\n"
            PASSED=$((PASSED + 1))
            return 0
        else
            local exit_code=$?
            if [[ "$can_skip" == "true" && $exit_code -eq 5 ]]; then
                # pytest exit code 5 = no tests collected (all skipped)
                echo -e "\n  ${YELLOW}⚠ ${label} 跳过 (依赖不满足)${NC}\n"
                SKIPPED=$((SKIPPED + 1))
                return 0
            fi
            echo -e "\n  ${RED}✗ ${label} 失败${NC}\n"
            FAILED=$((FAILED + 1))
            return 1
        fi
    fi
}


# ── 执行测试 ──

# Layer 0: 预飞检查 (必须通过)
if ! run_test 1 "预飞检查 (环境依赖)" "test_00_preflight.py"; then
    echo -e "\n${RED}╔══════════════════════════════════════════════════╗"
    echo "║  预飞检查失败! 请先修复环境问题再继续测试。        ║"
    echo -e "╚══════════════════════════════════════════════════╝${NC}\n"
    exit 1
fi

# Layer 1: 模型定义 (必须通过)
if ! run_test 2 "数据模型 & Schema" "test_01_models.py"; then
    echo -e "\n${RED}模型定义测试失败! 请检查 models/ 目录${NC}\n"
    exit 1
fi

# Layer 2: 数据库操作 (必须通过)
run_test 3 "数据库操作 (CRUD + 向量检索)" "test_02_database.py" || true

# Layer 3: 服务层
run_test 4 "服务层 (解析/分块/向量化)" "test_03_services.py" "true" || true

# Layer 4: API 端点
run_test 5 "API 端点" "test_04_api.py" "true" || true

# Layer 5: 端到端
run_test 6 "端到端流程 (全链路)" "test_05_e2e.py" "true" || true


# ── 汇总 ──

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════╗"
echo "║                   测试汇总                        ║"
echo "╠══════════════════════════════════════════════════╣"
echo -e "║  ${GREEN}通过: ${PASSED}${CYAN}                                        ║"
if [[ $FAILED -gt 0 ]]; then
    echo -e "║  ${RED}失败: ${FAILED}${CYAN}                                        ║"
fi
if [[ $SKIPPED -gt 0 ]]; then
    echo -e "║  ${YELLOW}跳过: ${SKIPPED}${CYAN}                                        ║"
fi
echo "╚══════════════════════════════════════════════════╝"
echo -e "${NC}"

if [[ $FAILED -eq 0 ]]; then
    echo -e "${GREEN}🎉 所有测试通过! 可以部署上线。${NC}"
    exit 0
else
    echo -e "${RED}⚠️  有 ${FAILED} 项测试失败, 请修复后再部署。${NC}"
    exit 1
fi

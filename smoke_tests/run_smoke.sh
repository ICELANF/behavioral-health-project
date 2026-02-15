#!/usr/bin/env bash
# ============================================================
# 行健平台 V4.0 冒烟测试执行器
# 用法:
#   ./run_smoke.sh day1          # 黄金路径前半段
#   ./run_smoke.sh day2          # 黄金路径后半段
#   ./run_smoke.sh day3          # 安全+治理+RBAC
#   ./run_smoke.sh all           # 全部3天
#   ./run_smoke.sh seed          # 仅创建种子数据
# ============================================================

set -euo pipefail

# 配置 — 按实际环境调整
export XINGJIAN_BASE_URL="${XINGJIAN_BASE_URL:-http://localhost:8000}"
export XINGJIAN_API_PREFIX="${XINGJIAN_API_PREFIX:-/api/v1}"
export XINGJIAN_ADMIN_EMAIL="${XINGJIAN_ADMIN_EMAIL:-admin@xingjian.local}"
export XINGJIAN_ADMIN_PASSWORD="${XINGJIAN_ADMIN_PASSWORD:-Admin@2026!}"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPORT_DIR="${SCRIPT_DIR}/reports"
mkdir -p "${REPORT_DIR}"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "============================================================"
echo "行健平台 V4.0 端到端冒烟测试"
echo "目标: ${XINGJIAN_BASE_URL}"
echo "时间: $(date)"
echo "============================================================"

# 检查依赖
pip install httpx pytest pytest-html --break-system-packages -q 2>/dev/null || true

# 健康检查
echo ""
echo "→ 服务健康检查..."
if curl -sf "${XINGJIAN_BASE_URL}/health" > /dev/null 2>&1; then
    echo "  ✅ 服务可达"
elif curl -sf "${XINGJIAN_BASE_URL}/api/v1/health" > /dev/null 2>&1; then
    echo "  ✅ 服务可达 (via /api/v1/health)"
else
    echo "  ❌ 服务不可达: ${XINGJIAN_BASE_URL}"
    echo "  请先启动服务"
    exit 1
fi

run_tests() {
    local day=$1
    local test_file=$2
    local description=$3

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ${description}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    pytest "${SCRIPT_DIR}/${test_file}" \
        -v \
        --tb=short \
        -x \
        --html="${REPORT_DIR}/smoke_${day}_${TIMESTAMP}.html" \
        --self-contained-html \
        --junitxml="${REPORT_DIR}/smoke_${day}_${TIMESTAMP}.xml" \
        2>&1 | tee "${REPORT_DIR}/smoke_${day}_${TIMESTAMP}.log"

    local exit_code=${PIPESTATUS[0]}

    if [ $exit_code -eq 0 ]; then
        echo "  ✅ ${description} — 全部通过"
    elif [ $exit_code -eq 1 ]; then
        echo "  ❌ ${description} — 有失败用例"
        echo "  查看报告: ${REPORT_DIR}/smoke_${day}_${TIMESTAMP}.html"
    elif [ $exit_code -eq 5 ]; then
        echo "  ⚠️  ${description} — 无测试用例收集到"
    else
        echo "  ❌ ${description} — 执行异常 (exit: ${exit_code})"
    fi

    return $exit_code
}

case "${1:-all}" in
    seed)
        echo ""
        echo "→ 创建种子数据..."
        python3 "${SCRIPT_DIR}/seed_smoke_data.py" "${XINGJIAN_BASE_URL}"
        ;;
    day1)
        python3 "${SCRIPT_DIR}/seed_smoke_data.py" "${XINGJIAN_BASE_URL}"
        run_tests "day1" "test_day1_golden_path_entry.py" \
            "Day 1: 黄金路径前半段 (访客→注册→HF-20→AI试用→S0)"
        ;;
    day2)
        run_tests "day2" "test_day2_golden_path_progression.py" \
            "Day 2: 黄金路径后半段 (S0-S4→积分→L0→L1晋级→防刷)"
        ;;
    day3)
        run_tests "day3" "test_day3_safety_governance_rbac.py" \
            "Day 3: 安全链路 + 治理闭环 + RBAC边界"
        ;;
    all)
        echo ""
        echo "→ Step 0: 创建种子数据..."
        python3 "${SCRIPT_DIR}/seed_smoke_data.py" "${XINGJIAN_BASE_URL}"

        TOTAL_FAIL=0

        run_tests "day1" "test_day1_golden_path_entry.py" \
            "Day 1: 黄金路径前半段" || TOTAL_FAIL=$((TOTAL_FAIL + 1))

        run_tests "day2" "test_day2_golden_path_progression.py" \
            "Day 2: 黄金路径后半段" || TOTAL_FAIL=$((TOTAL_FAIL + 1))

        run_tests "day3" "test_day3_safety_governance_rbac.py" \
            "Day 3: 安全+治理+RBAC" || TOTAL_FAIL=$((TOTAL_FAIL + 1))

        echo ""
        echo "============================================================"
        echo "全量冒烟测试完成"
        echo "报告目录: ${REPORT_DIR}/"
        if [ $TOTAL_FAIL -eq 0 ]; then
            echo "结果: ✅ 3天全部通过 — MVP可上线"
        else
            echo "结果: ❌ ${TOTAL_FAIL}/3天有失败 — 需修复后重跑"
        fi
        echo "============================================================"
        ;;
    *)
        echo "用法: $0 {seed|day1|day2|day3|all}"
        exit 1
        ;;
esac

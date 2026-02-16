#!/usr/bin/env bash
# ============================================================================
# Phase 3: 分级测试执行脚本
# 用法：
#   ./run_tests.sh smoke     # 快速烟雾测试（5 分钟）
#   ./run_tests.sh standard  # 标准测试：静态检查 + E2E（15 分钟）
#   ./run_tests.sh full      # 完整测试：全部 + 渗透测试（30-45 分钟）
#   ./run_tests.sh report    # 仅生成测试报告（不执行测试）
# ============================================================================

set -euo pipefail

# --------------- 配置 ---------------
PROJECT_ROOT="${PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || echo '.')}"
REPORT_DIR="$PROJECT_ROOT/test_reports"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
REPORT_FILE="$REPORT_DIR/test_report_$TIMESTAMP.md"

# 测试脚本路径
STATIC_CHECKS="$PROJECT_ROOT/scripts/static_checks.py"
E2E_ACCEPTANCE="$PROJECT_ROOT/scripts/e2e_acceptance.py"
PENTEST="$PROJECT_ROOT/pentest_bhp.py"

# 结果跟踪
declare -A RESULTS
TOTAL_PASS=0
TOTAL_FAIL=0
TOTAL_SKIP=0

# --------------- 参数解析 ---------------
TEST_LEVEL="${1:-smoke}"

case "$TEST_LEVEL" in
    smoke|standard|full|report)
        ;;
    *)
        echo "用法: $0 {smoke|standard|full|report}"
        echo ""
        echo "  smoke    — 快速烟雾测试（~5 分钟）"
        echo "  standard — 静态检查 + E2E 烟雾测试（~15 分钟）"
        echo "  full     — 全量测试 + 渗透测试（~30-45 分钟）"
        echo "  report   — 查看最近的测试报告"
        exit 1
        ;;
esac

# --------------- 辅助函数 ---------------
run_test() {
    local name="$1"
    local cmd="$2"
    local timeout="${3:-600}"
    
    echo ""
    echo "─────────────────────────────────────"
    echo "▶ $name"
    echo "─────────────────────────────────────"
    
    start_time=$(date +%s)
    
    if timeout "$timeout" bash -c "$cmd" 2>&1; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        echo ""
        echo "  ✅ 通过 ($duration 秒)"
        RESULTS["$name"]="PASS ($duration 秒)"
        TOTAL_PASS=$((TOTAL_PASS + 1))
        return 0
    else
        exit_code=$?
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        
        if [[ $exit_code -eq 124 ]]; then
            echo ""
            echo "  ⏰ 超时 (>${timeout}秒)"
            RESULTS["$name"]="TIMEOUT (>${timeout}秒)"
        else
            echo ""
            echo "  ❌ 失败 (退出码: $exit_code, $duration 秒)"
            RESULTS["$name"]="FAIL (退出码: $exit_code, $duration 秒)"
        fi
        TOTAL_FAIL=$((TOTAL_FAIL + 1))
        return 1
    fi
}

skip_test() {
    local name="$1"
    local reason="$2"
    echo ""
    echo "─────────────────────────────────────"
    echo "⏭️  跳过: $name"
    echo "   原因: $reason"
    echo "─────────────────────────────────────"
    RESULTS["$name"]="SKIP ($reason)"
    TOTAL_SKIP=$((TOTAL_SKIP + 1))
}

check_script() {
    local path="$1"
    if [[ ! -f "$path" ]]; then
        echo "  ❌ 未找到: $path"
        return 1
    fi
    return 0
}

# --------------- 查看报告模式 ---------------
if [[ "$TEST_LEVEL" == "report" ]]; then
    if [[ -d "$REPORT_DIR" ]]; then
        latest=$(ls -t "$REPORT_DIR"/test_report_*.md 2>/dev/null | head -1)
        if [[ -n "$latest" ]]; then
            echo "📋 最近的测试报告:"
            echo ""
            cat "$latest"
        else
            echo "ℹ️ 没有找到测试报告"
        fi
    else
        echo "ℹ️ 报告目录不存在，请先运行测试"
    fi
    exit 0
fi

# --------------- 开始测试 ---------------
echo "═══════════════════════════════════════════"
echo "BehaviorOS 测试套件 — 级别: $TEST_LEVEL"
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "项目: $PROJECT_ROOT"
echo "═══════════════════════════════════════════"

# 前置检查
echo ""
echo "📋 脚本检查:"
scripts_ok=true
for script in "$STATIC_CHECKS" "$E2E_ACCEPTANCE" "$PENTEST"; do
    if check_script "$script"; then
        echo "  ✅ $(basename $script)"
    else
        scripts_ok=false
    fi
done

if [[ "$scripts_ok" == false ]]; then
    echo ""
    echo "❌ 缺少必要脚本，终止测试"
    exit 1
fi

# ==================== SMOKE 级别 ====================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 Smoke 测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

run_test \
    "静态检查 (快速)" \
    "python $STATIC_CHECKS --fast" \
    300 || true

run_test \
    "E2E 烟雾测试" \
    "python $E2E_ACCEPTANCE --scenario 0 --skip-static" \
    600 || true

# ==================== STANDARD 级别 ====================
if [[ "$TEST_LEVEL" == "standard" || "$TEST_LEVEL" == "full" ]]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🧪 Standard 测试"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    run_test \
        "静态检查 (完整)" \
        "python $STATIC_CHECKS" \
        600 || true
    
    run_test \
        "E2E 验收测试 (10 阶段)" \
        "python $E2E_ACCEPTANCE" \
        1800 || true
else
    skip_test "静态检查 (完整)" "级别为 smoke，使用 'standard' 或 'full' 启用"
    skip_test "E2E 验收测试 (10 阶段)" "级别为 smoke，使用 'standard' 或 'full' 启用"
fi

# ==================== FULL 级别 ====================
if [[ "$TEST_LEVEL" == "full" ]]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔒 安全测试"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    run_test \
        "渗透测试 (完整)" \
        "python $PENTEST --full" \
        1200 || true
else
    skip_test "渗透测试 (完整)" "级别为 $TEST_LEVEL，使用 'full' 启用"
fi

# ==================== 生成报告 ====================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 测试报告"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

mkdir -p "$REPORT_DIR"

# 生成报告内容
REPORT="# BehaviorOS 测试报告

- 时间: $(date '+%Y-%m-%d %H:%M:%S')
- 级别: $TEST_LEVEL
- Commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'N/A')
- Branch: $(git branch --show-current 2>/dev/null || echo 'N/A')

## 结果汇总

| 状态 | 数量 |
|------|------|
| 通过 | $TOTAL_PASS |
| 失败 | $TOTAL_FAIL |
| 跳过 | $TOTAL_SKIP |

## 详细结果

| 测试项 | 结果 |
|--------|------|"

for test_name in "${!RESULTS[@]}"; do
    result="${RESULTS[$test_name]}"
    if [[ "$result" == PASS* ]]; then
        icon="✅"
    elif [[ "$result" == SKIP* ]]; then
        icon="⏭️"
    else
        icon="❌"
    fi
    REPORT="$REPORT
| $test_name | $icon $result |"
done

REPORT="$REPORT

## 下一步

$(if [[ $TOTAL_FAIL -gt 0 ]]; then
    echo "- ❌ 存在失败项，请查看上方日志修复后重新运行"
    echo "- 修复后运行: \`./run_tests.sh $TEST_LEVEL\`"
elif [[ "$TEST_LEVEL" != "full" ]]; then
    echo "- ✅ 当前级别测试通过"
    echo "- 合并前请运行完整测试: \`./run_tests.sh full\`"
else
    echo "- ✅ 所有测试通过，可以合并到 main"
    echo "- \`git checkout main && git merge <branch> && git push\`"
fi)
"

echo "$REPORT" > "$REPORT_FILE"

# 打印摘要
echo ""
echo "  通过: $TOTAL_PASS | 失败: $TOTAL_FAIL | 跳过: $TOTAL_SKIP"
echo ""

if [[ $TOTAL_FAIL -gt 0 ]]; then
    echo "  ❌ 存在失败项"
else
    echo "  ✅ 当前级别全部通过"
fi

echo ""
echo "  📄 完整报告: $REPORT_FILE"
echo ""

# 退出码
if [[ $TOTAL_FAIL -gt 0 ]]; then
    exit 1
fi
exit 0

#!/bin/bash
# =====================================================================
# BehaviorOS V4.0 — pytest 测试运行器
# =====================================================================
# 用法:
#   ./run_tests.sh              # 运行全部测试
#   ./run_tests.sh -k stage     # 只运行 stage 相关测试
#   ./run_tests.sh --smoke      # 只运行冒烟测试
#   ./run_tests.sh --cov        # 带覆盖率报告
# =====================================================================

set -e

cd "$(dirname "$0")"

# 确保项目根在 PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."

echo "=================================================="
echo " BehaviorOS V4.0 — pytest 测试套件"
echo "=================================================="
echo ""

# 检查依赖
python -c "import pytest" 2>/dev/null || {
    echo "[!] pytest 未安装, 正在安装..."
    pip install pytest pytest-asyncio pytest-cov --break-system-packages -q
}

# 解析参数
ARGS="-v --tb=short"

if [[ "$*" == *"--smoke"* ]]; then
    ARGS="$ARGS -m smoke"
elif [[ "$*" == *"--cov"* ]]; then
    ARGS="$ARGS --cov=core --cov-report=term-missing --cov-report=html:htmlcov"
fi

# 透传其他 pytest 参数
for arg in "$@"; do
    if [[ "$arg" != "--smoke" && "$arg" != "--cov" ]]; then
        ARGS="$ARGS $arg"
    fi
done

echo "运行: pytest $ARGS"
echo ""

python -m pytest $ARGS

echo ""
echo "=================================================="
echo " 测试完成"
echo "=================================================="

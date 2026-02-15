#!/bin/bash
# deploy_view_patches.sh — 部署5个视图文件 + API层
# 使用方式: bash deploy_view_patches.sh

set -e
PROJ="D:/behavioral-health-project/behaviros-frontend"  # 实际前端目录
PATCH_DIR="$(dirname "$0")"

echo "=========================================="
echo " 视图层适配部署"
echo "=========================================="

# 1. 备份
echo "[1/3] 备份原文件..."
mkdir -p "$PROJ/src/views/_backup"
mkdir -p "$PROJ/src/modules/agent/views/_backup"
mkdir -p "$PROJ/src/api/_backup"

for f in JourneyView.vue LearningView.vue ChallengesView.vue HomeView.vue; do
  cp "$PROJ/src/views/$f" "$PROJ/src/views/_backup/$f.bak" 2>/dev/null && echo "  ✓ $f"
done
cp "$PROJ/src/modules/agent/views/AgentChatView.vue" \
   "$PROJ/src/modules/agent/views/_backup/AgentChatView.vue.bak" 2>/dev/null && echo "  ✓ AgentChatView.vue"
cp "$PROJ/src/api/index.ts" "$PROJ/src/api/_backup/index.ts.bak" 2>/dev/null && echo "  ✓ api/index.ts"

# 2. 替换
echo ""
echo "[2/3] 替换文件..."

cp "$PATCH_DIR/JourneyView.vue"    "$PROJ/src/views/JourneyView.vue"      && echo "  ✓ JourneyView.vue"
cp "$PATCH_DIR/LearningView.vue"   "$PROJ/src/views/LearningView.vue"     && echo "  ✓ LearningView.vue"
cp "$PATCH_DIR/ChallengesView.vue" "$PROJ/src/views/ChallengesView.vue"   && echo "  ✓ ChallengesView.vue"
cp "$PATCH_DIR/HomeView.vue"       "$PROJ/src/views/HomeView.vue"         && echo "  ✓ HomeView.vue"
cp "$PATCH_DIR/AgentChatView.vue"  "$PROJ/src/modules/agent/views/AgentChatView.vue" && echo "  ✓ AgentChatView.vue"
cp "$PATCH_DIR/index.ts"           "$PROJ/src/api/index.ts"               && echo "  ✓ api/index.ts"

# 3. 验证
echo ""
echo "[3/3] 验证..."
echo "  检查关键修正:"
grep -q 'getTransitions()' "$PROJ/src/views/JourneyView.vue"    && echo "  ✓ JourneyView: getTransitions() 无userId"
grep -q 'getStats(userId)'  "$PROJ/src/views/LearningView.vue"  && echo "  ✓ LearningView: getStats(userId)"
grep -q 'enrollment_id'     "$PROJ/src/views/ChallengesView.vue" && echo "  ✓ ChallengesView: enrollmentId"
grep -q 'string | null'     "$PROJ/src/modules/agent/views/AgentChatView.vue" && echo "  ✓ AgentChatView: sessionId string"
grep -q 'current_stage'     "$PROJ/src/views/HomeView.vue"       && echo "  ✓ HomeView: field normalization"

echo ""
echo "=========================================="
echo " 完成！请运行 npm run build 验证编译"
echo "=========================================="

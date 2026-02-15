#!/bin/bash
# deploy_response_align.sh — 响应格式对齐部署
# 包含: normalizers.ts(新) + auth.ts + index.ts + types + 5个视图
#
# 使用: bash deploy_response_align.sh [项目根目录]

set -e
PROJ="${1:-D:/behavioral-health-project/frontend}"
PATCH="$(dirname "$0")"

echo "=========================================="
echo " 响应格式对齐部署"
echo " 项目: $PROJ"
echo "=========================================="

# 1. 备份
echo ""
echo "[1/4] 备份..."
mkdir -p "$PROJ/src/api/_backup_v2"
mkdir -p "$PROJ/src/types/_backup_v2"
mkdir -p "$PROJ/src/views/_backup_v2"
mkdir -p "$PROJ/src/modules/agent/views/_backup_v2"

for f in auth.ts index.ts; do
  [ -f "$PROJ/src/api/$f" ] && cp "$PROJ/src/api/$f" "$PROJ/src/api/_backup_v2/$f.bak" && echo "  ✓ api/$f"
done
[ -f "$PROJ/src/types/index.ts" ] && cp "$PROJ/src/types/index.ts" "$PROJ/src/types/_backup_v2/index.ts.bak" && echo "  ✓ types/index.ts"
for f in JourneyView.vue LearningView.vue ChallengesView.vue HomeView.vue; do
  [ -f "$PROJ/src/views/$f" ] && cp "$PROJ/src/views/$f" "$PROJ/src/views/_backup_v2/$f.bak" && echo "  ✓ views/$f"
done
[ -f "$PROJ/src/modules/agent/views/AgentChatView.vue" ] && \
  cp "$PROJ/src/modules/agent/views/AgentChatView.vue" "$PROJ/src/modules/agent/views/_backup_v2/AgentChatView.vue.bak" && echo "  ✓ agent/AgentChatView.vue"

# 2. 新增文件
echo ""
echo "[2/4] 新增 normalizers.ts..."
cp "$PATCH/api/normalizers.ts" "$PROJ/src/api/normalizers.ts" && echo "  ✓ api/normalizers.ts (新文件)"

# 3. 替换文件
echo ""
echo "[3/4] 替换文件..."
cp "$PATCH/api/auth.ts"       "$PROJ/src/api/auth.ts"                    && echo "  ✓ api/auth.ts"
cp "$PATCH/api/index.ts"      "$PROJ/src/api/index.ts"                   && echo "  ✓ api/index.ts"
cp "$PATCH/types/index.ts"    "$PROJ/src/types/index.ts"                 && echo "  ✓ types/index.ts"
cp "$PATCH/views/JourneyView.vue"    "$PROJ/src/views/"                  && echo "  ✓ JourneyView.vue"
cp "$PATCH/views/LearningView.vue"   "$PROJ/src/views/"                  && echo "  ✓ LearningView.vue"
cp "$PATCH/views/ChallengesView.vue" "$PROJ/src/views/"                  && echo "  ✓ ChallengesView.vue"
cp "$PATCH/views/HomeView.vue"       "$PROJ/src/views/"                  && echo "  ✓ HomeView.vue"
cp "$PATCH/views/agent/AgentChatView.vue" "$PROJ/src/modules/agent/views/" && echo "  ✓ AgentChatView.vue"

# 4. 验证
echo ""
echo "[4/4] 验证关键引用..."
grep -q "normalizeUser"          "$PROJ/src/api/auth.ts"       && echo "  ✓ auth.ts → normalizeUser"
grep -q "normalizeJourneyStatus" "$PROJ/src/api/index.ts"      && echo "  ✓ index.ts → normalizeJourneyStatus"
grep -q "normalizeLearningStats" "$PROJ/src/api/index.ts"      && echo "  ✓ index.ts → normalizeLearningStats"
grep -q "normalizeEnrollment"    "$PROJ/src/api/index.ts"      && echo "  ✓ index.ts → normalizeEnrollment"
grep -q "normalizeCreditsBalance" "$PROJ/src/api/index.ts"     && echo "  ✓ index.ts → normalizeCreditsBalance"
grep -q "normalizeMicroAction"   "$PROJ/src/api/index.ts"      && echo "  ✓ index.ts → normalizeMicroAction"
grep -q "refresh_token"          "$PROJ/src/types/index.ts"    && echo "  ✓ types → refresh_token"
grep -q "getStats(userId)"       "$PROJ/src/views/LearningView.vue" && echo "  ✓ LearningView → getStats(userId)"

echo ""
echo "=========================================="
echo " 完成! 请运行: npm run build"
echo "=========================================="
echo ""
echo "文件清单:"
echo "  新增: src/api/normalizers.ts"
echo "  修改: src/api/auth.ts, src/api/index.ts"
echo "  修改: src/types/index.ts"
echo "  修改: 5 个视图文件"

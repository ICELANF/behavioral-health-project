#!/bin/bash
# ============================================================
# coach-miniprogram restore script
# Snapshot: 2b9bb0f (2026-03-05)
# Branch: stabilize-from-sprint1
# ============================================================
# Usage:
#   bash restore-coach-miniprogram.sh [TARGET_DIR]
#
# Default target: D:\behavioral-health-project\coach-miniprogram
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-/d/behavioral-health-project}"
SRC_ARCHIVE="$SCRIPT_DIR/coach-miniprogram-2b9bb0f-20260305.tar.gz"
DIST_ARCHIVE="$SCRIPT_DIR/coach-miniprogram-dist-2b9bb0f-20260305.tar.gz"

echo "=== Coach Miniprogram Restore ==="
echo "Snapshot: 2b9bb0f (2026-03-05)"
echo "Target:   $TARGET/coach-miniprogram"
echo ""

# Safety check
if [ ! -f "$SRC_ARCHIVE" ]; then
  echo "ERROR: Source archive not found: $SRC_ARCHIVE"
  exit 1
fi

# Step 1: Extract source
echo "[1/4] Extracting source files..."
cd "$TARGET"
tar xzf "$SRC_ARCHIVE"
echo "      Done. $(find coach-miniprogram/src -name '*.vue' -o -name '*.ts' | wc -l) source files restored."

# Step 2: Extract pre-built dist (optional)
if [ -f "$DIST_ARCHIVE" ]; then
  echo "[2/4] Extracting pre-built dist..."
  tar xzf "$DIST_ARCHIVE"
  echo "      Done. WeChat devtools can import dist/dev/mp-weixin immediately."
else
  echo "[2/4] No dist archive found, skipping (will rebuild in step 3)."
fi

# Step 3: Install dependencies
echo "[3/4] Installing npm dependencies..."
cd coach-miniprogram
npm install --legacy-peer-deps 2>&1 | tail -3
echo "      Done."

# Step 4: Build
echo "[4/4] Building for mp-weixin..."
npm run dev:mp-weixin &
BUILD_PID=$!
sleep 25
echo "      Build started (PID: $BUILD_PID)."

echo ""
echo "=== Restore Complete ==="
echo "  Source:  $TARGET/coach-miniprogram/src/"
echo "  Output:  $TARGET/coach-miniprogram/dist/dev/mp-weixin/"
echo "  Action:  Open WeChat DevTools -> Import -> dist/dev/mp-weixin"
echo "  AppID:   wx7da71ddbc7890598"
echo ""
echo "To stop dev server: kill $BUILD_PID"

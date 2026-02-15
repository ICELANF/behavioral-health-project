#!/bin/bash
# ============================================================
# Full Platform Endpoint Audit Script
# Tests ALL API endpoints with proper auth tokens
# ============================================================

BASE="http://localhost:8000"

# Get tokens
ADMIN_TOKEN=$(curl -s -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin@2026" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

COACH_TOKEN=$(curl -s -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=coach&password=Coach@2026" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

GROWER_TOKEN=$(curl -s -X POST "$BASE/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=grower&password=Grower@2026" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$ADMIN_TOKEN" ] || [ "$ADMIN_TOKEN" == "FAIL" ]; then
  echo "FATAL: Cannot get admin token"
  exit 1
fi

PASS=0
FAIL=0
ERRORS=""

check() {
  local desc="$1"
  local expected="$2"
  local method="$3"
  local url="$4"
  local token="$5"
  local data="$6"

  local args="-s -o /dev/null -w %{http_code}"
  if [ -n "$token" ]; then
    args="$args -H \"Authorization: Bearer $token\""
  fi
  if [ "$method" == "POST" ] || [ "$method" == "PUT" ] || [ "$method" == "PATCH" ]; then
    args="$args -H \"Content-Type: application/json\""
    if [ -n "$data" ]; then
      args="$args -d '$data'"
    else
      args="$args -d '{}'"
    fi
  fi

  local code=$(eval "curl $args -X $method \"$BASE$url\"" 2>/dev/null)

  # Accept any 2xx/3xx or the expected code, plus 404 for valid resource-not-found
  if echo "$expected" | grep -q "$code"; then
    PASS=$((PASS+1))
  elif [ "$code" -ge 200 ] && [ "$code" -lt 400 ]; then
    PASS=$((PASS+1))
  else
    FAIL=$((FAIL+1))
    ERRORS="$ERRORS\n  FAIL [$code] $method $url ($desc)"
  fi
}

echo "=== Full Platform Endpoint Audit ==="
echo "Started: $(date)"
echo ""

# ────── PUBLIC ENDPOINTS ──────
echo "--- PUBLIC ENDPOINTS ---"
check "health" "200" GET "/health" "" ""
check "api health" "200" GET "/api/v1/health" "" ""
check "docs" "200" GET "/docs" "" ""
check "register domains" "200" GET "/api/v1/expert-registration/domains" "" ""
check "high-freq presets" "200" GET "/api/v1/high-freq/presets" "" ""
check "high-freq all" "200" GET "/api/v1/high-freq/all" "" ""
check "coach levels" "200" GET "/api/v1/coach-levels/levels" "" ""
check "coach modules" "200" GET "/api/v1/coach-levels/modules" "" ""
check "credit modules" "200" GET "/api/v1/credits/modules" "" ""
check "knowledge domains" "200" GET "/api/v1/knowledge/domains" "" ""
check "coach leaderboard" "200" GET "/api/v1/learning/leaderboard/coaches" "" ""
check "grower leaderboard" "200" GET "/api/v1/learning/leaderboard/growers" "" ""
check "experts list" "200" GET "/api/v1/experts" "" ""
echo "Public: PASS=$PASS FAIL=$FAIL"

# ────── AUTH ENDPOINTS ──────
echo ""
echo "--- AUTH ENDPOINTS ---"
check "auth me" "200" GET "/api/v1/auth/me" "$ADMIN_TOKEN" ""
check "auth me grower" "200" GET "/api/v1/auth/me" "$GROWER_TOKEN" ""

# ────── ADMIN ENDPOINTS ──────
echo ""
echo "--- ADMIN ENDPOINTS ---"
check "admin users" "200" GET "/api/v1/admin/users" "$ADMIN_TOKEN" ""
check "admin user detail" "200" GET "/api/v1/admin/users/2" "$ADMIN_TOKEN" ""
check "admin stats" "200" GET "/api/v1/admin/stats" "$ADMIN_TOKEN" ""
check "admin coaches" "200" GET "/api/v1/admin/coaches" "$ADMIN_TOKEN" ""
check "admin pending dist" "200" GET "/api/v1/admin/distribution/pending" "$ADMIN_TOKEN" ""
check "admin analytics overview" "200" GET "/api/v1/analytics/admin/overview" "$ADMIN_TOKEN" ""
check "admin analytics growth" "200" GET "/api/v1/analytics/admin/user-growth" "$ADMIN_TOKEN" ""
check "admin analytics role-dist" "200" GET "/api/v1/analytics/admin/role-distribution" "$ADMIN_TOKEN" ""
check "admin analytics stage-dist" "200" GET "/api/v1/analytics/admin/stage-distribution" "$ADMIN_TOKEN" ""
check "admin analytics risk-dist" "200" GET "/api/v1/analytics/admin/risk-distribution" "$ADMIN_TOKEN" ""
check "admin analytics coach-board" "200" GET "/api/v1/analytics/admin/coach-leaderboard" "$ADMIN_TOKEN" ""
check "admin analytics challenge" "200" GET "/api/v1/analytics/admin/challenge-effectiveness" "$ADMIN_TOKEN" ""

# ────── CONTENT ENDPOINTS ──────
echo ""
echo "--- CONTENT ENDPOINTS ---"
check "content list" "200" GET "/api/v1/content/" "$GROWER_TOKEN" ""
check "content recommended" "200" GET "/api/v1/content/recommended" "$GROWER_TOKEN" ""
check "content cases" "200" GET "/api/v1/content/cases" "$GROWER_TOKEN" ""
check "content learning-progress" "200" GET "/api/v1/content/user/learning-progress" "$GROWER_TOKEN" ""
check "content learning-history" "200" GET "/api/v1/content/user/learning-history" "$GROWER_TOKEN" ""
check "content recommendations" "200" GET "/api/v1/content/recommendations" "$GROWER_TOKEN" ""

# ────── LEARNING ENDPOINTS ──────
echo ""
echo "--- LEARNING ENDPOINTS ---"
check "coach points" "200" GET "/api/v1/learning/coach/points/2" "$ADMIN_TOKEN" ""
check "grower stats" "200" GET "/api/v1/learning/grower/stats/3" "$GROWER_TOKEN" ""
check "grower time" "200" GET "/api/v1/learning/grower/time/3" "$GROWER_TOKEN" ""
check "grower points" "200" GET "/api/v1/learning/grower/points/3" "$GROWER_TOKEN" ""
check "grower streak" "200" GET "/api/v1/learning/grower/streak/3" "$GROWER_TOKEN" ""
check "rewards" "200" GET "/api/v1/learning/rewards/3" "$GROWER_TOKEN" ""

# ────── COACH ENDPOINTS ──────
echo ""
echo "--- COACH ENDPOINTS ---"
check "coach dashboard" "200" GET "/api/v1/coach/dashboard" "$COACH_TOKEN" ""
check "coach students" "200" GET "/api/v1/coach/students" "$COACH_TOKEN" ""
check "coach performance" "200" GET "/api/v1/coach/performance" "$COACH_TOKEN" ""
check "coach analytics risk" "200" GET "/api/v1/coach/analytics/risk-trend" "$COACH_TOKEN" ""
check "coach analytics micro" "200" GET "/api/v1/coach/analytics/micro-action-trend" "$COACH_TOKEN" ""
check "coach analytics domain" "200" GET "/api/v1/coach/analytics/domain-performance" "$COACH_TOKEN" ""
check "coach analytics alert" "200" GET "/api/v1/coach/analytics/alert-frequency" "$COACH_TOKEN" ""
check "coach analytics challenge" "200" GET "/api/v1/coach/analytics/challenge-stats" "$COACH_TOKEN" ""
check "coach analytics stage" "200" GET "/api/v1/coach/analytics/stage-distribution" "$COACH_TOKEN" ""
check "coach push queue" "200" GET "/api/v1/coach-push-queue/" "$COACH_TOKEN" ""
check "coach push stats" "200" GET "/api/v1/coach-push-queue/stats" "$COACH_TOKEN" ""

# ────── DEVICE/DATA ENDPOINTS ──────
echo ""
echo "--- DEVICE/DATA ENDPOINTS ---"
check "device data devices" "200" GET "/api/v1/device-data/devices" "$GROWER_TOKEN" ""
check "device data glucose" "200" GET "/api/v1/device-data/glucose" "$GROWER_TOKEN" ""
check "device data weight" "200" GET "/api/v1/device-data/weight" "$GROWER_TOKEN" ""
check "device data bp" "200" GET "/api/v1/device-data/blood-pressure" "$GROWER_TOKEN" ""
check "device data sleep" "200" GET "/api/v1/device-data/sleep" "$GROWER_TOKEN" ""
check "device data activity" "200" GET "/api/v1/device-data/activity" "$GROWER_TOKEN" ""
check "device data hr" "200" GET "/api/v1/device-data/heart-rate" "$GROWER_TOKEN" ""
check "device data hrv" "200" GET "/api/v1/device-data/hrv" "$GROWER_TOKEN" ""
check "device data dashboard" "200" GET "/api/v1/device-data/dashboard/today" "$GROWER_TOKEN" ""
check "device rest all" "200" GET "/api/v1/device-rest/all" "$GROWER_TOKEN" ""
check "device rest types" "200" GET "/api/v1/device-rest/data-types" "$GROWER_TOKEN" ""
check "device alerts my" "200" GET "/api/v1/device-alerts/my" "$GROWER_TOKEN" ""
check "device alerts coach" "200" GET "/api/v1/device-alerts/coach" "$COACH_TOKEN" ""

# ────── MICRO-ACTIONS ──────
echo ""
echo "--- MICRO-ACTIONS ---"
check "micro today" "200" GET "/api/v1/micro-actions/today" "$GROWER_TOKEN" ""
check "micro history" "200" GET "/api/v1/micro-actions/history" "$GROWER_TOKEN" ""
check "micro stats" "200" GET "/api/v1/micro-actions/stats" "$GROWER_TOKEN" ""

# ────── CHALLENGES ──────
echo ""
echo "--- CHALLENGES ---"
check "challenges list" "200" GET "/api/v1/challenges" "$GROWER_TOKEN" ""
check "challenges enrollments" "200" GET "/api/v1/challenges/my-enrollments" "$GROWER_TOKEN" ""

# ────── ASSESSMENTS ──────
echo ""
echo "--- ASSESSMENTS ---"
check "assessment latest" "200" GET "/api/assessment/user/latest" "$GROWER_TOKEN" ""
check "assessment pipeline me" "200" GET "/api/v1/assessment/profile/me" "$GROWER_TOKEN" ""
check "assessment pending" "200" GET "/api/v1/assessment-assignments/my-pending" "$GROWER_TOKEN" ""
check "assessment review list" "200" GET "/api/v1/assessment-assignments/review-list" "$COACH_TOKEN" ""

# ────── CHAT ──────
echo ""
echo "--- CHAT ---"
check "chat sessions" "200" GET "/api/v1/chat/sessions" "$GROWER_TOKEN" ""
check "messages inbox" "200" GET "/api/v1/messages/inbox" "$GROWER_TOKEN" ""
check "messages unread" "200" GET "/api/v1/messages/unread-count" "$GROWER_TOKEN" ""

# ────── SEARCH ──────
echo ""
echo "--- SEARCH ---"
check "search global" "200" GET "/api/v1/search?q=test" "$GROWER_TOKEN" ""

# ────── SEGMENTS ──────
echo ""
echo "--- SEGMENTS ---"
check "my segment" "200" GET "/api/v1/segments/my-segment" "$GROWER_TOKEN" ""
check "features" "200" GET "/api/v1/segments/features" "$GROWER_TOKEN" ""
check "segments all" "200" GET "/api/v1/segments/all" "$ADMIN_TOKEN" ""
check "segments stats" "200" GET "/api/v1/segments/stats" "$ADMIN_TOKEN" ""

# ────── PATHS/LEVELS ──────
echo ""
echo "--- PATHS/LEVELS ---"
check "level progress" "200" GET "/api/v1/coach-levels/progress" "$GROWER_TOKEN" ""
check "level overview" "200" GET "/api/v1/coach-levels/overview" "$GROWER_TOKEN" ""
check "companions" "200" GET "/api/v1/coach-levels/companions" "$GROWER_TOKEN" ""

# ────── CREDITS/PROMOTION/COMPANIONS ──────
echo ""
echo "--- CREDITS/PROMOTION/COMPANIONS ---"
check "my credits" "200" GET "/api/v1/credits/my" "$GROWER_TOKEN" ""
check "my credit records" "200" GET "/api/v1/credits/my/records" "$GROWER_TOKEN" ""
check "admin credit modules" "200" GET "/api/v1/credits/admin/modules" "$ADMIN_TOKEN" ""
check "admin credit stats" "200" GET "/api/v1/credits/admin/stats" "$ADMIN_TOKEN" ""
check "promotion progress" "200" GET "/api/v1/promotions/progress" "$GROWER_TOKEN" ""
check "promotion rules" "200" GET "/api/v1/promotions/rules" "$GROWER_TOKEN" ""
check "promotion check" "200" GET "/api/v1/promotions/check" "$GROWER_TOKEN" ""
check "promotion apps" "200" GET "/api/v1/promotions/applications" "$ADMIN_TOKEN" ""
check "companions mentees" "200" GET "/api/v1/companions/my-mentees" "$GROWER_TOKEN" ""
check "companions mentors" "200" GET "/api/v1/companions/my-mentors" "$GROWER_TOKEN" ""
check "companions stats" "200" GET "/api/v1/companions/stats" "$GROWER_TOKEN" ""
check "companions all" "200" GET "/api/v1/companions/all" "$ADMIN_TOKEN" ""

# ────── INCENTIVE/MILESTONE ──────
echo ""
echo "--- INCENTIVE ---"
check "incentive dashboard" "200" GET "/api/v1/incentive/dashboard" "$GROWER_TOKEN" ""
check "incentive badges" "200" GET "/api/v1/incentive/badges" "$GROWER_TOKEN" ""
check "incentive badges avail" "200" GET "/api/v1/incentive/badges/available" "$GROWER_TOKEN" ""
check "incentive memorials" "200" GET "/api/v1/incentive/memorials" "$GROWER_TOKEN" ""

# ────── V004 PROGRAMS ──────
echo ""
echo "--- V004 PROGRAMS ---"
check "program templates" "200" GET "/api/v1/programs/templates" "$ADMIN_TOKEN" ""
check "program my" "200" GET "/api/v1/programs/my" "$GROWER_TOKEN" ""
check "program admin analytics" "200" GET "/api/v1/programs/admin/analytics" "$ADMIN_TOKEN" ""
check "program admin enrollments" "200" GET "/api/v1/programs/admin/enrollments" "$ADMIN_TOKEN" ""

# ────── V005 SAFETY ──────
echo ""
echo "--- V005 SAFETY ---"
check "safety dashboard" "200" GET "/api/v1/safety/dashboard" "$ADMIN_TOKEN" ""
check "safety logs" "200" GET "/api/v1/safety/logs" "$ADMIN_TOKEN" ""
check "safety review" "200" GET "/api/v1/safety/review-queue" "$ADMIN_TOKEN" ""
check "safety config" "200" GET "/api/v1/safety/config" "$ADMIN_TOKEN" ""
check "safety daily report" "200" GET "/api/v1/safety/reports/daily" "$ADMIN_TOKEN" ""

# ────── V006 AGENT TEMPLATES ──────
echo ""
echo "--- V006 AGENT TEMPLATES ---"
check "agent templates list" "200" GET "/api/v1/agent-templates/list" "$ADMIN_TOKEN" ""
check "agent templates presets" "200" GET "/api/v1/agent-templates/presets" "$ADMIN_TOKEN" ""
check "agent templates domains" "200" GET "/api/v1/agent-templates/domains" "$ADMIN_TOKEN" ""

# ────── AGENT SYSTEM ──────
echo ""
echo "--- AGENT SYSTEM ---"
check "agent list" "200" GET "/api/v1/agent/list" "$GROWER_TOKEN" ""
check "agent status" "200" GET "/api/v1/agent/status" "$GROWER_TOKEN" ""
check "agent history" "200" GET "/api/v1/agent/history" "$GROWER_TOKEN" ""
check "agent pending reviews" "200" GET "/api/v1/agent/pending-reviews" "$GROWER_TOKEN" ""

# ────── AGENT ECOSYSTEM ──────
echo ""
echo "--- AGENT ECOSYSTEM ---"
check "marketplace" "200" GET "/api/v1/agent-ecosystem/marketplace" "$GROWER_TOKEN" ""
check "marketplace recommended" "200" GET "/api/v1/agent-ecosystem/marketplace/recommended" "$GROWER_TOKEN" ""
check "growth points" "200" GET "/api/v1/agent-ecosystem/growth-points" "$GROWER_TOKEN" ""
check "compositions" "200" GET "/api/v1/agent-ecosystem/compositions" "$GROWER_TOKEN" ""

# ────── AGENT FEEDBACK ──────
echo ""
echo "--- AGENT FEEDBACK ---"
check "feedback summary" "200" GET "/api/v1/agent-feedback/summary" "$ADMIN_TOKEN" ""

# ────── V007 POLICY ──────
echo ""
echo "--- V007 POLICY ---"
check "policy rules" "200" GET "/api/v1/policy/rules" "$ADMIN_TOKEN" ""
check "policy traces" "200" GET "/api/v1/policy/traces" "$ADMIN_TOKEN" ""
check "policy cost" "200" GET "/api/v1/policy/cost" "$ADMIN_TOKEN" ""

# ────── KNOWLEDGE ──────
echo ""
echo "--- KNOWLEDGE ---"
check "knowledge docs" "200" GET "/api/v1/knowledge/docs" "$GROWER_TOKEN" ""
check "knowledge search" "200" GET "/api/v1/knowledge/search?q=test" "$GROWER_TOKEN" ""
check "knowledge stats" "200" GET "/api/v1/knowledge/stats" "$ADMIN_TOKEN" ""
check "knowledge sharing domains" "200" GET "/api/v1/knowledge-sharing/domains" "$GROWER_TOKEN" ""
check "knowledge sharing pool" "200" GET "/api/v1/knowledge-sharing/domain-pool" "$GROWER_TOKEN" ""
check "knowledge sharing my" "200" GET "/api/v1/knowledge-sharing/my-contributions" "$GROWER_TOKEN" ""

# ────── SURVEYS ──────
echo ""
echo "--- SURVEYS ---"
check "surveys list" "200" GET "/api/v1/surveys" "$ADMIN_TOKEN" ""

# ────── EXAMS ──────
echo ""
echo "--- EXAMS ---"
check "exams list" "200" GET "/api/v1/exams" "$ADMIN_TOKEN" ""
check "exam my results" "200" GET "/api/v1/exam-sessions/my-results" "$GROWER_TOKEN" ""
check "questions list" "200" GET "/api/v1/questions" "$ADMIN_TOKEN" ""

# ────── CONTENT MANAGE ──────
echo ""
echo "--- CONTENT MANAGEMENT ---"
check "content manage list" "200" GET "/api/v1/content-manage/list" "$ADMIN_TOKEN" ""
check "batch ingestion jobs" "200" GET "/api/v1/knowledge/batch-jobs" "$ADMIN_TOKEN" ""
check "content contributions pending" "200" GET "/api/v1/content-contributions/review/pending" "$ADMIN_TOKEN" ""
check "my contributions" "200" GET "/api/v1/content-contributions/my" "$GROWER_TOKEN" ""

# ────── USER STATS ──────
echo ""
echo "--- USER STATS ---"
check "user stats overview" "200" GET "/api/v1/user-stats/overview" "$GROWER_TOKEN" ""
check "user stats activity" "200" GET "/api/v1/user-stats/activity" "$GROWER_TOKEN" ""

# ────── EXPERT REGISTRATION ──────
echo ""
echo "--- EXPERT REGISTRATION ---"
check "my application" "200|404" GET "/api/v1/expert-registration/my-application" "$GROWER_TOKEN" ""
check "admin applications" "200" GET "/api/v1/expert-registration/admin/applications" "$ADMIN_TOKEN" ""

# ────── TENANTS ──────
echo ""
echo "--- TENANTS ---"
check "tenants mine" "200|404" GET "/api/v1/tenants/mine" "$GROWER_TOKEN" ""

# ────── BEHAVIOR RX ──────
echo ""
echo "--- BEHAVIOR RX ---"
check "rx strategies" "200" GET "/api/v1/rx/strategies" "$GROWER_TOKEN" ""
check "rx agents status" "200" GET "/api/v1/rx/agents-status" "$COACH_TOKEN" ""

# ────── ORCHESTRATOR ──────
echo ""
echo "--- ORCHESTRATOR ---"
check "orchestrator status" "200" GET "/orchestrator/status" "" ""

# ────── FOOD RECOGNITION ──────
echo ""
echo "--- FOOD RECOGNITION ---"
check "food history" "200" GET "/api/v1/food-recognition/history" "$GROWER_TOKEN" ""

# ────── REMINDERS ──────
echo ""
echo "--- REMINDERS ---"
check "reminders my" "200" GET "/api/v1/reminders/my" "$GROWER_TOKEN" ""
check "reminders admin all" "200" GET "/api/v1/reminders/admin/all" "$ADMIN_TOKEN" ""

echo ""
echo "=== AUDIT COMPLETE ==="
echo "PASS: $PASS"
echo "FAIL: $FAIL"
echo "TOTAL: $((PASS+FAIL))"
echo ""
if [ $FAIL -gt 0 ]; then
  echo "FAILURES:"
  echo -e "$ERRORS"
fi
echo ""
echo "Finished: $(date)"

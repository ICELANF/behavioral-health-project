#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_all_pages_by_role.py — H5 全角色页面接口 200 验收测试

模拟用户漏斗:
  5 observers -> 4 growers -> 3 sharers -> 2 coaches -> 1 promoter

对每个角色的所有页面上的所有接口调用进行测试，确保 HTTP 200。
"""
import json
import sys
import time
from dataclasses import dataclass, field
from typing import List, Optional

try:
    import requests
except ImportError:
    print("请安装 requests: pip install requests")
    sys.exit(1)

BASE_URL = "http://localhost:8000"
TIMEOUT = 10
CALL_DELAY = 0.05  # 50ms between calls to avoid rate limiting

# ─────────────────────────────────────────────────────
# 颜色输出（ASCII 安全）
# ─────────────────────────────────────────────────────
def ok(msg): print(f"  [OK]  {msg}")
def fail(msg): print(f"  [FAIL] {msg}")
def info(msg): print(f"  [INFO] {msg}")
def section(msg): print(f"\n{'='*60}\n{msg}\n{'='*60}")
def subsection(msg): print(f"\n  --- {msg} ---")


@dataclass
class TestResult:
    endpoint: str
    method: str
    status: int
    role: str
    page: str
    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.status == 200


# ─────────────────────────────────────────────────────
# 登录帮助函数
# ─────────────────────────────────────────────────────
def login(username: str, password: str) -> Optional[str]:
    """返回 JWT token，失败返回 None"""
    try:
        r = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            return r.json().get("access_token")
        return None
    except Exception as e:
        return None


def call(token: str, method: str, path: str, body: dict = None,
         role: str = "", page: str = "") -> TestResult:
    """发起 API 调用，返回 TestResult"""
    url = f"{BASE_URL}{path}"
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    time.sleep(CALL_DELAY)
    try:
        if method == "GET":
            r = requests.get(url, headers=headers, timeout=TIMEOUT)
        elif method == "POST":
            r = requests.post(url, json=body or {}, headers=headers, timeout=TIMEOUT)
        elif method == "PATCH":
            r = requests.patch(url, json=body or {}, headers=headers, timeout=TIMEOUT)
        elif method == "PUT":
            r = requests.put(url, json=body or {}, headers=headers, timeout=TIMEOUT)
        elif method == "DELETE":
            r = requests.delete(url, headers=headers, timeout=TIMEOUT)
        else:
            r = requests.get(url, headers=headers, timeout=TIMEOUT)
        return TestResult(path, method, r.status_code, role, page)
    except Exception as e:
        return TestResult(path, method, 0, role, page, error=str(e))


# ─────────────────────────────────────────────────────
# 共享页面接口（所有已登录角色均可访问）
# ─────────────────────────────────────────────────────

COMMON_ENDPOINTS = [
    # ObserverHome / 公共
    ("GET",  "/api/v1/home",                                   "Home"),
    ("GET",  "/api/v1/auth/me",                                "Profile"),
    ("GET",  "/api/v1/flags",                                  "Public"),
    ("GET",  "/api/v1/home/motivation-stats",                  "Public"),
    ("GET",  "/api/v1/chat/sessions",                          "Chat"),
    ("GET",  "/api/v1/content?limit=5",                        "LearnCenter"),
    ("GET",  "/api/v1/content/recommended?limit=5",            "LearnCenter"),
    ("GET",  "/api/v1/assessment-assignments/my-pending",       "BehaviorAssessment"),
]

GROWER_ENDPOINTS = [
    ("GET",  "/api/v1/coach-tip/today",                        "GrowerTodayHome"),
    ("GET",  "/api/v1/weekly-summary",                         "GrowerTodayHome"),
    ("GET",  "/api/v1/daily-tasks/today",                      "DailyTasks"),
    ("GET",  "/api/v1/daily-tasks/catalog",                    "DailyTasks"),
    ("GET",  "/api/v1/micro-actions/today",                    "Tasks"),
    ("GET",  "/api/v1/micro-actions/stats",                    "Tasks"),
    ("GET",  "/api/v1/micro-actions/task-pool",                "Tasks"),
    ("GET",  "/api/v1/mp/device/dashboard/today",              "HealthRecords"),
    ("GET",  "/api/v1/mp/device/glucose?limit=20",             "HealthRecords"),
    ("GET",  "/api/v1/mp/device/blood-pressure?limit=20",      "HealthRecords"),
    ("GET",  "/api/v1/mp/device/weight?limit=20",              "HealthRecords"),
    ("GET",  "/api/v1/mp/device/sleep?limit=14",               "HealthRecords"),
    ("GET",  "/api/v1/credits/my",                             "MyCredits"),
    ("GET",  "/api/v1/credits/modules",                        "MyCredits"),
    ("GET",  "/api/v1/companions/stats",                       "MyCompanions"),
    ("GET",  "/api/v1/companions/my-mentees",                  "MyCompanions"),
    ("GET",  "/api/v1/companions/my-mentors",                  "MyCompanions"),
    ("GET",  "/api/v1/promotion/progress",                     "PromotionProgress"),
    ("GET",  "/api/v1/promotion/rules",                        "PromotionProgress"),
    ("GET",  "/api/v1/programs/my",                            "MyPlan"),
    ("GET",  "/api/v1/assessment-assignments/pushed-list",     "MyPlan"),
    ("GET",  "/api/v1/weekly-reports/latest",                  "WeeklyReport"),
    ("GET",  "/api/v1/weekly-reports",                         "WeeklyReport"),
    ("GET",  "/api/v1/messages/inbox",                         "Notifications"),
    ("GET",  "/api/v1/messages/unread-count",                  "Notifications"),
    ("GET",  "/api/v1/alerts/my",                              "Notifications"),
    ("GET",  "/api/v1/reminders",                              "Notifications"),
    ("GET",  "/api/v1/mp/device/devices",                      "DataSync"),
]

SHARER_ENDPOINTS = [
    ("GET",  "/api/v1/contributions/my",                       "Contribute"),
]

COACH_ENDPOINTS = [
    ("GET",  "/api/v1/coach/dashboard-stats",                  "CoachHome"),
    ("GET",  "/api/v1/coach/students?limit=5",                 "CoachHome"),
    ("GET",  "/api/v1/coach-push/pending?limit=5",             "CoachHome"),
    ("GET",  "/api/v1/coach/students",                         "CoachManagement"),
    ("GET",  "/api/v1/coach/performance",                      "CoachManagement"),
]

PROMOTER_ENDPOINTS = [
    ("GET",  "/api/v1/coach/dashboard-stats",                  "ProHome"),
]


def _run_endpoints(token: str, role: str, endpoint_list: list, results: List[TestResult]):
    for method, path, page in endpoint_list:
        results.append(call(token, method, path, role=role, page=page))


def test_observer(token: str, results: List[TestResult]):
    role = "observer"
    subsection("Common + Observer pages")
    _run_endpoints(token, role, COMMON_ENDPOINTS, results)


def test_grower(token: str, results: List[TestResult]):
    role = "grower"
    subsection("Common pages")
    _run_endpoints(token, role, COMMON_ENDPOINTS, results)
    subsection("Grower-specific pages")
    _run_endpoints(token, role, GROWER_ENDPOINTS, results)


def test_sharer(token: str, results: List[TestResult]):
    role = "sharer"
    subsection("Common pages")
    _run_endpoints(token, role, COMMON_ENDPOINTS, results)
    subsection("Grower pages")
    _run_endpoints(token, role, GROWER_ENDPOINTS, results)
    subsection("Sharer-specific pages")
    _run_endpoints(token, role, SHARER_ENDPOINTS, results)


def test_coach(token: str, results: List[TestResult]):
    role = "coach"
    subsection("Common pages")
    _run_endpoints(token, role, COMMON_ENDPOINTS, results)
    subsection("Grower pages")
    _run_endpoints(token, role, GROWER_ENDPOINTS, results)
    subsection("Sharer pages")
    _run_endpoints(token, role, SHARER_ENDPOINTS, results)
    subsection("Coach-specific pages")
    _run_endpoints(token, role, COACH_ENDPOINTS, results)


def test_promoter(token: str, results: List[TestResult]):
    role = "promoter"
    subsection("Common pages")
    _run_endpoints(token, role, COMMON_ENDPOINTS, results)
    subsection("Grower pages")
    _run_endpoints(token, role, GROWER_ENDPOINTS, results)
    subsection("Sharer pages")
    _run_endpoints(token, role, SHARER_ENDPOINTS, results)
    subsection("Coach pages")
    _run_endpoints(token, role, COACH_ENDPOINTS, results)
    subsection("Promoter-specific pages")
    _run_endpoints(token, role, PROMOTER_ENDPOINTS, results)


# ─────────────────────────────────────────────────────
# 用户凭据配置（从 seed_test_users.py）
# ─────────────────────────────────────────────────────
USERS = {
    "observer": [
        {"username": "observer", "password": "Observer@2026"},
    ],
    "grower": [
        {"username": "grower", "password": "Grower@2026"},
    ],
    "sharer": [
        {"username": "sharer", "password": "Sharer@2026"},
    ],
    "coach": [
        {"username": "coach", "password": "Coach@2026"},
    ],
    "promoter": [
        {"username": "promoter", "password": "Promoter@2026"},
    ],
}

ROLE_TEST_FN = {
    "observer": test_observer,
    "grower": test_grower,
    "sharer": test_sharer,
    "coach": test_coach,
    "promoter": test_promoter,
}


# ─────────────────────────────────────────────────────
# 主执行
# ─────────────────────────────────────────────────────
def main():
    section("H5 全角色页面接口 200 验收测试")
    print(f"  Base URL: {BASE_URL}")
    print(f"  Timeout:  {TIMEOUT}s")

    all_results: List[TestResult] = []
    role_tokens: dict = {}

    # ── 1. 登录每个角色 ──
    section("Step 1: 用户登录")
    for role, users in USERS.items():
        for user in users:
            token = login(user["username"], user["password"])
            if token:
                role_tokens[role] = token
                ok(f"{role:<12} -> {user['username']} (token: {token[:20]}...)")
            else:
                fail(f"{role:<12} -> {user['username']} (login failed)")

    # ── 2. 运行各角色测试 ──
    section("Step 2: 逐角色页面接口测试")
    role_order = ["observer", "grower", "sharer", "coach", "promoter"]

    for role in role_order:
        if role not in role_tokens:
            info(f"Skipping {role} - no token")
            continue

        print(f"\n{'─'*60}")
        print(f"  角色: {role.upper()}")
        print(f"{'─'*60}")

        token = role_tokens[role]
        role_results: List[TestResult] = []

        ROLE_TEST_FN[role](token, role_results)
        all_results.extend(role_results)

        # Role summary
        passed = sum(1 for r in role_results if r.passed)
        total = len(role_results)
        failed_items = [r for r in role_results if not r.passed]

        if failed_items:
            print(f"\n  Role {role}: {passed}/{total} passed")
            for r in failed_items:
                fail(f"  [{r.status}] {r.method} {r.endpoint}  (page: {r.page})")
        else:
            print(f"\n  Role {role}: {passed}/{total} ALL PASSED")

    # ── 3. 总结报告 ──
    section("Step 3: 总结报告")
    total = len(all_results)
    passed = sum(1 for r in all_results if r.passed)
    failed = total - passed

    print(f"  Total:  {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")

    if failed > 0:
        print(f"\n  失败接口列表:")
        seen = set()
        for r in all_results:
            if not r.passed:
                key = f"{r.method} {r.endpoint}"
                if key not in seen:
                    seen.add(key)
                    fail(f"  [{r.status}] {r.method} {r.endpoint}")

    # ── 4. JSON 报告 ──
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H%M%S"),
        "total": total,
        "passed": passed,
        "failed": failed,
        "results": [
            {
                "role": r.role,
                "page": r.page,
                "method": r.method,
                "endpoint": r.endpoint,
                "status": r.status,
                "passed": r.passed,
                "error": r.error,
            }
            for r in all_results
        ],
    }
    report_path = "test_pages_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  Report saved to: {report_path}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

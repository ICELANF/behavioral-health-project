"""
conftest.py — 冒烟测试共享配置
用法: pytest smoke_tests/ -v --tb=short -x
"""
import pytest
import httpx
import os
import json
from datetime import datetime

# ============================================================
# 环境配置
# ============================================================

BASE_URL = os.getenv("XINGJIAN_BASE_URL", "http://localhost:8000")
API_PREFIX = os.getenv("XINGJIAN_API_PREFIX", "/api/v1")
ADMIN_EMAIL = os.getenv("XINGJIAN_ADMIN_EMAIL", "admin@xingjian.com")
ADMIN_PASSWORD = os.getenv("XINGJIAN_ADMIN_PASSWORD", "Admin@2026!")
COACH_EMAIL = os.getenv("XINGJIAN_COACH_EMAIL", "smoke_coach@test.xingjian.com")
GROWER_EMAIL = os.getenv("XINGJIAN_GROWER_EMAIL", "smoke_grower@test.xingjian.com")
DEFAULT_PASSWORD = "Test@Smoke2026!"


# ============================================================
# Hooks
# ============================================================

def pytest_configure(config):
    config.addinivalue_line("markers", "day1: Day 1 黄金路径前半段")
    config.addinivalue_line("markers", "day2: Day 2 黄金路径后半段")
    config.addinivalue_line("markers", "day3: Day 3 安全+治理+RBAC")
    config.addinivalue_line("markers", "safety: 安全管线测试")
    config.addinivalue_line("markers", "rbac: RBAC边界测试")


# ============================================================
# 报告收集
# ============================================================

class SmokeTestReport:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()

    def add(self, test_name, status, detail=""):
        self.results.append({
            "test": test_name,
            "status": status,
            "detail": detail,
            "time": datetime.now().isoformat(),
        })

    def summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        skipped = sum(1 for r in self.results if r["status"] == "SKIP")
        return {
            "total": total, "passed": passed, "failed": failed, "skipped": skipped,
            "pass_rate": f"{passed/total*100:.1f}%" if total else "N/A",
            "duration": str(datetime.now() - self.start_time),
            "blockers": [r for r in self.results if r["status"] == "FAIL"],
        }

    def save(self, path="smoke_report.json"):
        with open(path, "w") as f:
            json.dump({"summary": self.summary(), "details": self.results}, f,
                      indent=2, ensure_ascii=False)


_report = SmokeTestReport()

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        if report.passed:
            _report.add(item.nodeid, "PASS")
        elif report.failed:
            _report.add(item.nodeid, "FAIL", str(report.longrepr)[:500])
        elif report.skipped:
            _report.add(item.nodeid, "SKIP", str(report.longrepr)[:200])

def pytest_sessionfinish(session, exitstatus):
    report_path = os.path.join(os.path.dirname(__file__), "smoke_report.json")
    _report.save(report_path)
    s = _report.summary()
    print(f"\n{'='*60}")
    print(f"冒烟测试报告: {s['passed']}/{s['total']} PASS | "
          f"{s['failed']} FAIL | {s['skipped']} SKIP")
    print(f"通过率: {s['pass_rate']} | 耗时: {s['duration']}")
    if s['blockers']:
        print(f"\n[!!] Blockers ({len(s['blockers'])}):")
        for b in s['blockers']:
            print(f"  [FAIL] {b['test']}")
            print(f"         {b['detail'][:200]}")
    print(f"{'='*60}")
    print(f"详细报告已保存: {report_path}")


# ============================================================
# 种子数据检查
# ============================================================

@pytest.fixture(scope="session", autouse=True)
def check_server():
    """确认服务可达"""
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=10)
        if r.status_code != 200:
            r = httpx.get(f"{BASE_URL}/api/v1/health", timeout=10)
    except httpx.ConnectError:
        pytest.exit(
            f"[FAIL] Server unreachable: {BASE_URL}\n"
            f"Start the service first, or set XINGJIAN_BASE_URL",
            returncode=1,
        )

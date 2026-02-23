# -*- coding: utf-8 -*-
"""
AI 行为处方端到端验证测试 — copilot_prescription_service 闭环验证
覆盖: 数据完整性 × RBAC × 降级路径 × 响应时间 × 并发安全

Usage:
    python scripts/test_copilot_prescription_e2e.py
    python scripts/test_copilot_prescription_e2e.py --base http://localhost:8000
"""
import sys
import os
import json
import time
import argparse
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import httpx
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx

# ══════════════════════════════════════════════════════════
# 配置
# ══════════════════════════════════════════════════════════
BASE = os.environ.get("API_BASE_URL", "http://localhost:8000")
TIMEOUT = httpx.Timeout(30.0)
REPORT_PATH = os.environ.get(
    "REPORT_PATH",
    r"E:\注册表更新文件\copilot_prescription_test_report.json",
)

# Test accounts — password format: Role@2026 (first letter capitalized)
ADMIN = ("admin", "Admin@2026")
COACH = ("coach", "Coach@2026")
OBSERVER = ("observer", "Observer@2026")
GROWER = ("grower", "Grower@2026")
SUPERVISOR = ("supervisor", "Supervisor@2026")

# ══════════════════════════════════════════════════════════
# 结果收集
# ══════════════════════════════════════════════════════════
results: list[dict] = []
total_pass = 0
total_fail = 0


def record(category: str, name: str, passed: bool, detail: str = ""):
    global total_pass, total_fail
    results.append({
        "category": category,
        "name": name,
        "passed": passed,
        "detail": detail,
        "timestamp": datetime.now().isoformat(),
    })
    if passed:
        total_pass += 1
    else:
        total_fail += 1
    mark = "✅" if passed else "❌"
    tag = "PASS" if passed else "FAIL"
    print(f"  {mark} {tag} [{name}] {detail}")


# ══════════════════════════════════════════════════════════
# 工具函数
# ══════════════════════════════════════════════════════════
def login(client: httpx.Client, username: str, password: str) -> str:
    """Login and return access token."""
    r = client.post(
        f"{BASE}/api/v1/auth/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    if r.status_code == 200:
        return r.json().get("access_token", "")
    return ""


def call_prescription(client: httpx.Client, token: str, student_id: int) -> tuple:
    """Call generate-prescription, return (status_code, json_data, elapsed_ms)."""
    start = time.monotonic()
    r = client.post(
        f"{BASE}/api/v1/copilot/generate-prescription",
        json={"student_id": student_id},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    elapsed = int((time.monotonic() - start) * 1000)
    try:
        data = r.json()
    except Exception:
        data = {}
    return r.status_code, data, elapsed


def validate_structure(data: dict) -> list[tuple[str, bool]]:
    """Validate the complete response structure. Returns list of (check_name, passed)."""
    checks = []
    diag = data.get("diagnosis", {})
    rx = data.get("prescription", {})
    sug = data.get("ai_suggestions", [])
    hs = data.get("health_summary", {})
    ip = data.get("intervention_plan", {})
    meta = data.get("meta", {})

    # Top-level keys
    checks.append(("top_level_6_keys", len(set(data.keys()) & {"diagnosis", "prescription", "ai_suggestions", "health_summary", "intervention_plan", "meta"}) == 6))

    # Diagnosis
    checks.append(("diag.spiScore_is_number", isinstance(diag.get("spiScore"), (int, float))))
    checks.append(("diag.successRate_is_number", isinstance(diag.get("successRate"), (int, float))))
    checks.append(("diag.sixReasons_>=6", len(diag.get("sixReasons", [])) >= 6))
    checks.append(("diag.problem_non_empty", bool(diag.get("problem"))))
    checks.append(("diag.difficulty_1to5", 1 <= (diag.get("difficulty") or 0) <= 5))
    checks.append(("diag.purpose_non_empty", bool(diag.get("purpose"))))
    checks.append(("diag.evidence_>=3", len(diag.get("evidence", [])) >= 3))
    checks.append(("diag.interventionAlert_non_empty", bool(diag.get("interventionAlert"))))

    # Six reasons structure
    for i, reason in enumerate(diag.get("sixReasons", [])[:6]):
        checks.append((f"sixReason[{i}].name", bool(reason.get("name"))))
        checks.append((f"sixReason[{i}].score_0to100", 0 <= (reason.get("score") or -1) <= 100))
        checks.append((f"sixReason[{i}].isWeak_is_bool", isinstance(reason.get("isWeak"), bool)))

    # Evidence structure
    for i, ev in enumerate(diag.get("evidence", [])[:4]):
        checks.append((f"evidence[{i}].label", bool(ev.get("label"))))
        checks.append((f"evidence[{i}].value", bool(ev.get("value"))))
        checks.append((f"evidence[{i}].status", ev.get("status") in ("normal", "warning", "danger")))

    # Prescription
    checks.append(("rx.phase.current_non_empty", bool(rx.get("phase", {}).get("current"))))
    checks.append(("rx.phase.week_is_int", isinstance(rx.get("phase", {}).get("week"), int)))
    checks.append(("rx.phase.total_is_int", isinstance(rx.get("phase", {}).get("total"), int)))
    checks.append(("rx.phaseTags_>=4", len(rx.get("phaseTags", [])) >= 4))
    checks.append(("rx.targetBehaviors_>=2", len(rx.get("targetBehaviors", [])) >= 2))
    checks.append(("rx.strategies_>=2", len(rx.get("strategies", [])) >= 2))

    # Phase tags structure
    for i, pt in enumerate(rx.get("phaseTags", [])[:4]):
        checks.append((f"phaseTag[{i}].label", bool(pt.get("label"))))
        checks.append((f"phaseTag[{i}].active_or_done", isinstance(pt.get("active"), bool) or isinstance(pt.get("done"), bool)))

    # Target behaviors structure
    for i, tb in enumerate(rx.get("targetBehaviors", [])[:3]):
        checks.append((f"targetBehavior[{i}].name", bool(tb.get("name"))))
        checks.append((f"targetBehavior[{i}].progress_0to100", 0 <= (tb.get("progress") or -1) <= 100))
        checks.append((f"targetBehavior[{i}].target", bool(tb.get("target"))))

    # AI suggestions
    checks.append(("ai_suggestions_>=3", len(sug) >= 3))
    for i, s in enumerate(sug[:4]):
        checks.append((f"suggestion[{i}].title", bool(s.get("title"))))
        checks.append((f"suggestion[{i}].content", bool(s.get("content"))))
        checks.append((f"suggestion[{i}].priority", s.get("priority") in ("high", "medium", "low")))

    # Health summary
    for key in ("fastingGlucose", "postprandialGlucose", "sleepHours", "exerciseMinutes", "weight", "heartRate"):
        checks.append((f"health.{key}_present", key in hs))

    checks.append(("health.highlights_is_list", isinstance(hs.get("highlights"), list)))

    # Intervention plan
    checks.append(("plan.name_non_empty", bool(ip.get("name"))))
    checks.append(("plan.description_non_empty", bool(ip.get("description"))))
    checks.append(("plan.domains_is_list", isinstance(ip.get("domains"), list)))
    checks.append(("plan.tone_non_empty", bool(ip.get("tone"))))
    scripts = ip.get("scripts", {})
    checks.append(("plan.scripts.opening", bool(scripts.get("opening"))))
    checks.append(("plan.scripts.motivation", bool(scripts.get("motivation"))))
    checks.append(("plan.scripts.closing", bool(scripts.get("closing"))))

    # Meta
    checks.append(("meta.source_exists", meta.get("source") in ("llm", "fallback", "merged")))
    checks.append(("meta.llm_used_is_bool", isinstance(meta.get("llm_used"), bool)))
    checks.append(("meta.has_real_data_is_dict", isinstance(meta.get("has_real_data"), dict)))

    return checks


# ══════════════════════════════════════════════════════════
# 测试用例
# ══════════════════════════════════════════════════════════

def test_data_completeness(client: httpx.Client, token: str):
    """T01: 数据完整性 — 3个学员全部字段校验"""
    print("\n📋 T01: 数据完整性")

    for sid in (3, 4, 10):
        status, data, ms = call_prescription(client, token, sid)
        record("completeness", f"student_{sid}_http_200", status == 200, f"HTTP {status}")

        if status == 200 and not data.get("error"):
            checks = validate_structure(data)
            passed_count = sum(1 for _, v in checks if v)
            total_count = len(checks)
            all_pass = passed_count == total_count
            record("completeness", f"student_{sid}_structure_{passed_count}/{total_count}",
                   all_pass, f"{passed_count}/{total_count} checks")

            if not all_pass:
                failed = [name for name, v in checks if not v]
                for f in failed[:5]:
                    record("completeness", f"student_{sid}_FAIL_{f}", False)
        else:
            record("completeness", f"student_{sid}_returned_data", False, str(data)[:100])


def test_nonexistent_student(client: httpx.Client, token: str):
    """T02: 不存在的学员应返回错误"""
    print("\n📋 T02: 不存在学员处理")

    status, data, ms = call_prescription(client, token, 99999)
    has_error = "error" in data or status >= 400
    record("edge_case", "nonexistent_student_returns_error", has_error,
           f"HTTP {status}, keys={list(data.keys())[:3]}")


def test_rbac(client: httpx.Client):
    """T03: 权限控制 — 4个角色验证"""
    print("\n📋 T03: RBAC 权限控制")

    # Roles that should be ALLOWED
    for username, password, expect_allowed in [
        (*ADMIN, True),
        (*COACH, True),
        (*SUPERVISOR, True),
        (*OBSERVER, False),
        (*GROWER, False),
    ]:
        token = login(client, username, password)
        if not token:
            record("rbac", f"{username}_login", False, "Login failed")
            continue

        status, data, ms = call_prescription(client, token, 3)
        if expect_allowed:
            ok = status == 200
            record("rbac", f"{username}_allowed", ok, f"HTTP {status}")
        else:
            ok = status in (401, 403)
            record("rbac", f"{username}_blocked", ok, f"HTTP {status}")


def test_unauthenticated(client: httpx.Client):
    """T04: 无认证访问应拒绝"""
    print("\n📋 T04: 无认证访问")

    r = client.post(
        f"{BASE}/api/v1/copilot/generate-prescription",
        json={"student_id": 3},
    )
    record("auth", "unauthenticated_blocked", r.status_code in (401, 403),
           f"HTTP {r.status_code}")


def test_performance(client: httpx.Client, token: str):
    """T05: 响应时间 — 首次<10s, 后续<2s"""
    print("\n📋 T05: 响应时间")

    times = []
    for i in range(3):
        status, data, ms = call_prescription(client, token, 3 + i)
        times.append(ms)
        record("perf", f"call_{i+1}_time_{ms}ms",
               ms < 10000 if i == 0 else ms < 2000,
               f"{ms}ms {'(first call)' if i == 0 else '(cached)'}")

    if len(times) >= 2:
        record("perf", "cache_speedup",
               times[-1] < times[0] * 0.5 or times[-1] < 2000,
               f"first={times[0]}ms, last={times[-1]}ms")


def test_concurrent(client: httpx.Client, token: str):
    """T06: 并发调用安全性"""
    print("\n📋 T06: 并发安全")

    import concurrent.futures

    def single_call(sid):
        return call_prescription(client, token, sid)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = [pool.submit(single_call, sid) for sid in [3, 4, 5, 10, 11]]
        results_list = [f.result() for f in concurrent.futures.as_completed(futures)]

    success_count = sum(1 for s, _, _ in results_list if s == 200)
    record("concurrent", f"5_parallel_calls_{success_count}/5_ok",
           success_count == 5, f"{success_count}/5 returned HTTP 200")

    # All should have complete data
    complete = sum(1 for _, d, _ in results_list
                   if len(d.get("diagnosis", {}).get("sixReasons", [])) >= 6)
    record("concurrent", f"5_parallel_data_complete_{complete}/5",
           complete == 5, f"{complete}/5 have complete data")


def test_degradation_consistency(client: httpx.Client, token: str):
    """T07: 降级一致性 — 多个学员的降级输出结构完全一致"""
    print("\n📋 T07: 降级一致性")

    structures = []
    for sid in (3, 4, 5, 10, 11):
        status, data, _ = call_prescription(client, token, sid)
        if status == 200 and not data.get("error"):
            keys = {
                "top": sorted(data.keys()),
                "diag": sorted(data.get("diagnosis", {}).keys()),
                "rx": sorted(data.get("prescription", {}).keys()),
                "hs": sorted(data.get("health_summary", {}).keys()),
                "ip": sorted(data.get("intervention_plan", {}).keys()),
            }
            structures.append(keys)

    if len(structures) >= 2:
        # All should have identical key structures
        ref = structures[0]
        all_match = all(s == ref for s in structures[1:])
        record("degradation", "structure_consistency",
               all_match, f"{len(structures)} responses checked")
    else:
        record("degradation", "structure_consistency", False, "Not enough responses")


def test_meta_data_flags(client: httpx.Client, token: str):
    """T08: meta.has_real_data 标记验证"""
    print("\n📋 T08: Meta数据标记")

    status, data, _ = call_prescription(client, token, 3)
    meta = data.get("meta", {})
    real_data = meta.get("has_real_data", {})

    expected_keys = {"profile", "assessment", "glucose", "sleep", "activity", "vitals", "micro_actions"}
    actual_keys = set(real_data.keys())
    record("meta", "has_real_data_keys_complete",
           expected_keys.issubset(actual_keys),
           f"expected={sorted(expected_keys)}, actual={sorted(actual_keys)}")

    record("meta", "source_is_valid",
           meta.get("source") in ("llm", "fallback", "merged"),
           f"source={meta.get('source')}")

    record("meta", "llm_used_is_bool",
           isinstance(meta.get("llm_used"), bool),
           f"llm_used={meta.get('llm_used')}")


def test_proxy_path(client: httpx.Client):
    """T09: Nginx代理路径验证 (模拟前端请求)"""
    print("\n📋 T09: Nginx代理路径")

    proxy_base = BASE.replace(":8000", ":5174")
    try:
        # Login through proxy
        r = client.post(
            f"{proxy_base}/api/v1/auth/login",
            data={"username": ADMIN[0], "password": ADMIN[1]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if r.status_code != 200:
            record("proxy", "proxy_login", False, f"HTTP {r.status_code}")
            return

        token = r.json().get("access_token", "")

        # Call prescription through proxy
        r2 = client.post(
            f"{proxy_base}/api/v1/copilot/generate-prescription",
            json={"student_id": 3},
            headers={"Authorization": f"Bearer {token}"},
        )
        record("proxy", "proxy_prescription_200", r2.status_code == 200,
               f"HTTP {r2.status_code}")

        if r2.status_code == 200:
            data = r2.json()
            has_all = all(k in data for k in ("diagnosis", "prescription", "ai_suggestions"))
            record("proxy", "proxy_data_complete", has_all,
                   f"keys={list(data.keys())[:4]}")

    except Exception as e:
        record("proxy", "proxy_connection", False, str(e)[:100])


def test_invalid_inputs(client: httpx.Client, token: str):
    """T10: 异常输入处理"""
    print("\n📋 T10: 异常输入处理")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Missing student_id
    r = client.post(f"{BASE}/api/v1/copilot/generate-prescription",
                    json={}, headers=headers)
    record("input", "missing_student_id", r.status_code == 422,
           f"HTTP {r.status_code}")

    # Negative student_id
    r = client.post(f"{BASE}/api/v1/copilot/generate-prescription",
                    json={"student_id": -1}, headers=headers)
    record("input", "negative_student_id", r.status_code in (200, 400, 404, 422),
           f"HTTP {r.status_code}")

    # String student_id
    r = client.post(f"{BASE}/api/v1/copilot/generate-prescription",
                    json={"student_id": "abc"}, headers=headers)
    record("input", "string_student_id", r.status_code == 422,
           f"HTTP {r.status_code}")

    # Zero student_id
    r = client.post(f"{BASE}/api/v1/copilot/generate-prescription",
                    json={"student_id": 0}, headers=headers)
    has_error = r.status_code >= 400 or "error" in r.json()
    record("input", "zero_student_id", has_error,
           f"HTTP {r.status_code}")


# ══════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════

def main():
    global BASE
    parser = argparse.ArgumentParser(description="AI处方E2E验证")
    parser.add_argument("--base", default=BASE, help="API base URL")
    args = parser.parse_args()
    BASE = args.base

    print("=" * 60)
    print("  AI 行为处方端到端验证测试")
    print(f"  Target: {BASE}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    with httpx.Client(timeout=TIMEOUT) as client:
        # Login as admin (primary test token)
        admin_token = login(client, *ADMIN)
        if not admin_token:
            print("❌ Admin login failed — aborting")
            sys.exit(1)
        print(f"\n✅ Admin login OK")

        # Run all tests
        test_data_completeness(client, admin_token)
        test_nonexistent_student(client, admin_token)
        test_rbac(client)
        test_unauthenticated(client)
        test_performance(client, admin_token)
        test_concurrent(client, admin_token)
        test_degradation_consistency(client, admin_token)
        test_meta_data_flags(client, admin_token)
        test_proxy_path(client)
        test_invalid_inputs(client, admin_token)

    # ── Summary ──
    print("\n" + "=" * 60)
    print(f"  RESULTS: {total_pass} PASS / {total_fail} FAIL / {total_pass + total_fail} TOTAL")
    if total_fail == 0:
        print("  🎉 ALL TESTS PASSED")
    else:
        print("  ⚠️  SOME TESTS FAILED")
        for r in results:
            if not r["passed"]:
                print(f"     ❌ [{r['category']}] {r['name']}: {r['detail']}")
    print("=" * 60)

    # Save report
    report = {
        "test_suite": "copilot_prescription_e2e",
        "target": BASE,
        "timestamp": datetime.now().isoformat(),
        "summary": {"pass": total_pass, "fail": total_fail, "total": total_pass + total_fail},
        "results": results,
    }
    try:
        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n📄 Report saved: {REPORT_PATH}")
    except Exception as e:
        print(f"\n⚠️ Report save failed: {e}")

    sys.exit(0 if total_fail == 0 else 1)


if __name__ == "__main__":
    main()

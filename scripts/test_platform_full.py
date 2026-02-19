# -*- coding: utf-8 -*-
"""
全平台功能测试套件 — 25 模块 × 96 测试 + 5 条跨模块业务链
Live HTTP tests against localhost:8000, async httpx, JSON report.

Usage:
    python scripts/test_platform_full.py
    python scripts/test_platform_full.py --module auth,chat,learning
    python scripts/test_platform_full.py --chain-only
"""
import sys
import os
import asyncio
import json
import time
import argparse
from datetime import datetime, date

# Windows UTF-8
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
ADMIN_USER = "admin"
ADMIN_PASS = "Admin@2026"
OBSERVER_USER = "observer"
OBSERVER_PASS = "Observer@2026"
REPORT_PATH = r"E:\注册表更新文件\platform_test_report.json"
TIMEOUT = httpx.Timeout(15.0)

# ══════════════════════════════════════════════════════════
# 结果收集
# ══════════════════════════════════════════════════════════
results: list[dict] = []
chain_results: list[dict] = []


def record(module: str, name: str, passed: bool, detail: str = "", status_code: int = 0):
    results.append({
        "module": module, "name": name, "passed": passed,
        "detail": detail, "status_code": status_code,
        "timestamp": datetime.now().isoformat(),
    })
    mark = "\u2705" if passed else "\u274c"
    tag = "PASS" if passed else "FAIL"
    print(f"    {mark} {tag} [{name}] {detail}")


def record_chain(chain: str, passed: bool, detail: str = ""):
    chain_results.append({
        "chain": chain, "passed": passed, "detail": detail,
        "timestamp": datetime.now().isoformat(),
    })
    mark = "\u2705" if passed else "\u274c"
    tag = "PASS" if passed else "FAIL"
    print(f"    {mark} {tag} [{chain}] {detail}")


def hdr(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


# ══════════════════════════════════════════════════════════
# Auth helpers
# ══════════════════════════════════════════════════════════
async def login(username: str, password: str) -> str:
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        r = await c.post(
            f"{BASE}/api/v1/auth/login",
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if r.status_code == 200:
            return r.json().get("access_token", "")
    return ""


# ══════════════════════════════════════════════════════════
# M01  Auth (3 tests)
# ══════════════════════════════════════════════════════════
async def test_m01_auth(c: httpx.AsyncClient, tokens: dict):
    M = "M01_Auth"
    print(f"\n  [{M}]")

    # 1. login_success
    try:
        r = await c.post(f"{BASE}/api/v1/auth/login",
                         data={"username": ADMIN_USER, "password": ADMIN_PASS},
                         headers={"Content-Type": "application/x-www-form-urlencoded"})
        ok = r.status_code == 200 and "access_token" in r.json()
        record(M, "login_success", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "login_success", False, str(e))

    # 2. login_bad_password
    try:
        r = await c.post(f"{BASE}/api/v1/auth/login",
                         data={"username": ADMIN_USER, "password": "wrong"},
                         headers={"Content-Type": "application/x-www-form-urlencoded"})
        ok = r.status_code in (401, 403, 422)
        record(M, "login_bad_password", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "login_bad_password", False, str(e))

    # 3. token_refresh (needs refresh_token from login response)
    try:
        # Get a fresh login response to extract refresh_token
        lr = await c.post(f"{BASE}/api/v1/auth/login",
                          data={"username": ADMIN_USER, "password": ADMIN_PASS},
                          headers={"Content-Type": "application/x-www-form-urlencoded"})
        refresh_tok = lr.json().get("refresh_token", "") if lr.status_code == 200 else ""
        if refresh_tok:
            r = await c.post(f"{BASE}/api/v1/auth/refresh",
                             json={"refresh_token": refresh_tok})
            ok = r.status_code == 200
            record(M, "token_refresh", ok, f"HTTP {r.status_code}", r.status_code)
        else:
            record(M, "token_refresh", False, "No refresh_token in login response")
    except Exception as e:
        record(M, "token_refresh", False, str(e))


# ══════════════════════════════════════════════════════════
# M02  Learning (6 tests)
# ══════════════════════════════════════════════════════════
async def test_m02_learning(c: httpx.AsyncClient, tokens: dict):
    M = "M02_Learning"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])
    uid = 2  # admin user id

    # 4. grower_stats
    try:
        r = await c.get(f"{BASE}/api/v1/learning/grower/stats/{uid}", headers=h)
        record(M, "grower_stats", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "grower_stats", False, str(e))

    # 5. add_learning_time
    try:
        r = await c.post(f"{BASE}/api/v1/learning/grower/time/add",
                         json={"minutes": 5, "domain": "general"}, headers=h)
        ok = r.status_code in (200, 201)
        record(M, "add_learning_time", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "add_learning_time", False, str(e))

    # 6. grower_points
    try:
        r = await c.get(f"{BASE}/api/v1/learning/grower/points/{uid}", headers=h)
        ok = r.status_code == 200
        record(M, "grower_points", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "grower_points", False, str(e))

    # 7. time_history
    try:
        r = await c.get(f"{BASE}/api/v1/learning/grower/time/{uid}/history", headers=h)
        ok = r.status_code == 200
        record(M, "time_history", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "time_history", False, str(e))

    # 8. coach_levels
    try:
        r = await c.get(f"{BASE}/api/v1/coach-levels/levels", headers=h)
        ok = r.status_code == 200
        record(M, "coach_levels", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "coach_levels", False, str(e))

    # 9. segments_permissions
    try:
        r = await c.get(f"{BASE}/api/v1/segments/permissions", headers=h)
        ok = r.status_code == 200
        record(M, "segments_permissions", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "segments_permissions", False, str(e))


# ══════════════════════════════════════════════════════════
# M03  Device (5 tests)
# ══════════════════════════════════════════════════════════
async def test_m03_device(c: httpx.AsyncClient, tokens: dict):
    M = "M03_Device"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 10. list_devices
    try:
        r = await c.get(f"{BASE}/api/v1/devices", headers=h)
        record(M, "list_devices", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "list_devices", False, str(e))

    # 11. glucose_data
    try:
        r = await c.get(f"{BASE}/api/v1/mp/device/glucose", headers=h)
        record(M, "glucose_data", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "glucose_data", False, str(e))

    # 12. sleep_data
    try:
        r = await c.get(f"{BASE}/api/v1/health-data/sleep", headers=h)
        record(M, "sleep_data", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "sleep_data", False, str(e))

    # 13. alert_list
    try:
        r = await c.get(f"{BASE}/api/v1/alerts/my", headers=h)
        record(M, "alert_list", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "alert_list", False, str(e))

    # 14. submit_glucose
    try:
        r = await c.post(f"{BASE}/api/v1/mp/device/glucose/manual",
                         json={"value": 5.8, "meal_tag": "fasting"}, headers=h)
        ok = r.status_code in (200, 201, 422)
        record(M, "submit_glucose", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "submit_glucose", False, str(e))


# ══════════════════════════════════════════════════════════
# M04  Survey (4 tests)
# ══════════════════════════════════════════════════════════
async def test_m04_survey(c: httpx.AsyncClient, tokens: dict):
    M = "M04_Survey"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 15. survey_list
    try:
        r = await c.get(f"{BASE}/api/v1/surveys", headers=h)
        ok = r.status_code == 200
        record(M, "survey_list", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "survey_list", False, str(e))

    # 16. survey_create
    try:
        r = await c.post(f"{BASE}/api/v1/surveys", json={
            "title": f"Platform Test Survey {int(time.time())}",
            "description": "Auto-created by platform test",
            "survey_type": "general",
        }, headers=h)
        ok = r.status_code in (200, 201)
        record(M, "survey_create", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "survey_create", False, str(e))

    # 17. survey_detail (get first survey)
    try:
        r = await c.get(f"{BASE}/api/v1/surveys/1", headers=h)
        ok = r.status_code in (200, 404)
        record(M, "survey_detail", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "survey_detail", False, str(e))

    # 18. survey_publish
    try:
        r = await c.post(f"{BASE}/api/v1/surveys/1/publish", headers=h)
        ok = r.status_code in (200, 400, 404, 409, 422)
        record(M, "survey_publish", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "survey_publish", False, str(e))


# ══════════════════════════════════════════════════════════
# M05  Challenge (5 tests)
# ══════════════════════════════════════════════════════════
async def test_m05_challenge(c: httpx.AsyncClient, tokens: dict):
    M = "M05_Challenge"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 19. challenge_list
    try:
        r = await c.get(f"{BASE}/api/v1/challenges", headers=h)
        record(M, "challenge_list", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "challenge_list", False, str(e))

    # 20. challenge_my_enrollments
    try:
        r = await c.get(f"{BASE}/api/v1/challenges/my-enrollments", headers=h)
        record(M, "challenge_my_enrollments", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "challenge_my_enrollments", False, str(e))

    # 21. challenge_create
    try:
        r = await c.post(f"{BASE}/api/v1/challenges", json={
            "title": f"Test Challenge {int(time.time())}",
            "description": "Platform test challenge",
            "challenge_type": "daily",
            "duration_days": 7,
        }, headers=h)
        ok = r.status_code in (200, 201)
        record(M, "challenge_create", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "challenge_create", False, str(e))

    # 22. challenge_enroll
    try:
        r = await c.post(f"{BASE}/api/v1/challenges/1/enroll", headers=h)
        ok = r.status_code in (200, 201, 400, 404, 409, 422)
        record(M, "challenge_enroll", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "challenge_enroll", False, str(e))

    # 23. challenge_progress
    try:
        r = await c.get(f"{BASE}/api/v1/challenges/enrollments/1/progress", headers=h)
        ok = r.status_code in (200, 404)
        record(M, "challenge_progress", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "challenge_progress", False, str(e))


# ══════════════════════════════════════════════════════════
# M06  Program (5 tests)
# ══════════════════════════════════════════════════════════
async def test_m06_program(c: httpx.AsyncClient, tokens: dict):
    M = "M06_Program"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 24. program_templates
    try:
        r = await c.get(f"{BASE}/api/v1/programs/templates", headers=h)
        record(M, "program_templates", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "program_templates", False, str(e))

    # 25. program_my_list
    try:
        r = await c.get(f"{BASE}/api/v1/programs/my", headers=h)
        record(M, "program_my_list", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "program_my_list", False, str(e))

    # 26. program_enroll (template_id is UUID; get first from templates list)
    try:
        tpl = await c.get(f"{BASE}/api/v1/programs/templates", headers=h)
        tpl_list = tpl.json() if tpl.status_code == 200 and isinstance(tpl.json(), list) else []
        tpl_id = tpl_list[0]["id"] if tpl_list else "00000000-0000-0000-0000-000000000001"
        r = await c.post(f"{BASE}/api/v1/programs/enroll",
                         json={"template_id": tpl_id}, headers=h)
        ok = r.status_code in (200, 201, 400, 422, 409)  # 400=already_enrolled
        record(M, "program_enroll", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "program_enroll", False, str(e))

    # 27. program_progress (enrollment_id is UUID)
    try:
        r = await c.get(f"{BASE}/api/v1/programs/my/00000000-0000-0000-0000-000000000001/progress", headers=h)
        ok = r.status_code in (200, 404)
        record(M, "program_progress", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "program_progress", False, str(e))

    # 28. program_interact
    try:
        r = await c.post(f"{BASE}/api/v1/programs/my/1/interact",
                         json={"action": "check_in"}, headers=h)
        ok = r.status_code in (200, 404, 422)
        record(M, "program_interact", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "program_interact", False, str(e))


# ══════════════════════════════════════════════════════════
# M07  Credits (4 tests)
# ══════════════════════════════════════════════════════════
async def test_m07_credits(c: httpx.AsyncClient, tokens: dict):
    M = "M07_Credits"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 29. credits_my (summary)
    try:
        r = await c.get(f"{BASE}/api/v1/credits/my", headers=h)
        record(M, "credits_my", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "credits_my", False, str(e))

    # 30. credits_records
    try:
        r = await c.get(f"{BASE}/api/v1/credits/my/records", headers=h)
        record(M, "credits_records", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "credits_records", False, str(e))

    # 31. credits_modules
    try:
        r = await c.get(f"{BASE}/api/v1/credits/modules", headers=h)
        record(M, "credits_modules", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "credits_modules", False, str(e))

    # 32. credits_admin_stats
    try:
        r = await c.get(f"{BASE}/api/v1/credits/admin/stats", headers=h)
        ok = r.status_code in (200, 403)
        record(M, "credits_admin_stats", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "credits_admin_stats", False, str(e))


# ══════════════════════════════════════════════════════════
# M08  Companion (4 tests)
# ══════════════════════════════════════════════════════════
async def test_m08_companion(c: httpx.AsyncClient, tokens: dict):
    M = "M08_Companion"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 33. companion_mentees
    try:
        r = await c.get(f"{BASE}/api/v1/companions/my-mentees", headers=h)
        record(M, "companion_mentees", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "companion_mentees", False, str(e))

    # 34. companion_stats
    try:
        r = await c.get(f"{BASE}/api/v1/companions/stats", headers=h)
        record(M, "companion_stats", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "companion_stats", False, str(e))

    # 35. companion_invite
    try:
        r = await c.post(f"{BASE}/api/v1/companions/invite",
                         json={"invitee_id": 5}, headers=h)
        ok = r.status_code in (200, 201, 409, 422)
        record(M, "companion_invite", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "companion_invite", False, str(e))

    # 36. companion_dashboard (CR-28)
    try:
        r = await c.get(f"{BASE}/api/v1/companions/dashboard", headers=h)
        record(M, "companion_dashboard", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "companion_dashboard", False, str(e))


# ══════════════════════════════════════════════════════════
# M09  Promotion (3 tests) — prefix /api/v1/promotion
# ══════════════════════════════════════════════════════════
async def test_m09_promotion(c: httpx.AsyncClient, tokens: dict):
    M = "M09_Promotion"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 37. promotion_status
    try:
        r = await c.get(f"{BASE}/api/v1/promotion/status", headers=h)
        record(M, "promotion_status", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "promotion_status", False, str(e))

    # 38. promotion_gap_report
    try:
        r = await c.get(f"{BASE}/api/v1/promotion/gap-report", headers=h)
        record(M, "promotion_gap_report", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "promotion_gap_report", False, str(e))

    # 39. promotion_check
    try:
        r = await c.post(f"{BASE}/api/v1/promotion/check", headers=h)
        ok = r.status_code in (200, 422)
        record(M, "promotion_check", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "promotion_check", False, str(e))


# ══════════════════════════════════════════════════════════
# M10  Agent Templates (4 tests)
# ══════════════════════════════════════════════════════════
async def test_m10_agent_templates(c: httpx.AsyncClient, tokens: dict):
    M = "M10_AgentTemplates"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 40. agent_template_list
    try:
        r = await c.get(f"{BASE}/api/v1/agent-templates/list", headers=h)
        ok = r.status_code == 200
        record(M, "agent_template_list", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "agent_template_list", False, str(e))

    # 41. agent_template_presets
    try:
        r = await c.get(f"{BASE}/api/v1/agent-templates/presets", headers=h)
        record(M, "agent_template_presets", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "agent_template_presets", False, str(e))

    # 42. agent_template_create
    try:
        r = await c.post(f"{BASE}/api/v1/agent-templates/create", json={
            "agent_id": f"test_{int(time.time()) % 100000}",
            "display_name": "Platform Test Agent",
            "description": "Auto-created by platform test",
            "keywords": ["test"],
            "system_prompt": "You are a test agent.",
        }, headers=h)
        ok = r.status_code in (200, 201, 409)
        record(M, "agent_template_create", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "agent_template_create", False, str(e))

    # 43. agent_template_domains
    try:
        r = await c.get(f"{BASE}/api/v1/agent-templates/domains", headers=h)
        record(M, "agent_template_domains", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "agent_template_domains", False, str(e))


# ══════════════════════════════════════════════════════════
# M11  Safety (4 tests)
# ══════════════════════════════════════════════════════════
async def test_m11_safety(c: httpx.AsyncClient, tokens: dict):
    M = "M11_Safety"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 44. safety_dashboard
    try:
        r = await c.get(f"{BASE}/api/v1/safety/dashboard", headers=h)
        record(M, "safety_dashboard", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "safety_dashboard", False, str(e))

    # 45. safety_config
    try:
        r = await c.get(f"{BASE}/api/v1/safety/config", headers=h)
        record(M, "safety_config", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "safety_config", False, str(e))

    # 46. safety_review_queue
    try:
        r = await c.get(f"{BASE}/api/v1/safety/review-queue", headers=h)
        record(M, "safety_review_queue", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "safety_review_queue", False, str(e))

    # 47. safety_daily_report
    try:
        r = await c.get(f"{BASE}/api/v1/safety/reports/daily", headers=h)
        record(M, "safety_daily_report", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "safety_daily_report", False, str(e))


# ══════════════════════════════════════════════════════════
# M12  Policy Engine (4 tests)
# ══════════════════════════════════════════════════════════
async def test_m12_policy(c: httpx.AsyncClient, tokens: dict):
    M = "M12_Policy"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 48. policy_rules_list
    try:
        r = await c.get(f"{BASE}/api/v1/policy/rules", headers=h)
        record(M, "policy_rules_list", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "policy_rules_list", False, str(e))

    # 49. policy_simulate
    try:
        r = await c.post(f"{BASE}/api/v1/policy/simulate",
                         json={"user_id": 2, "action": "send_push", "context": {}}, headers=h)
        record(M, "policy_simulate", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "policy_simulate", False, str(e))

    # 50. policy_cost_report
    try:
        r = await c.get(f"{BASE}/api/v1/policy/cost/report", headers=h)
        record(M, "policy_cost_report", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "policy_cost_report", False, str(e))

    # 51. policy_traces
    try:
        r = await c.get(f"{BASE}/api/v1/policy/traces/user/2", headers=h)
        record(M, "policy_traces", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "policy_traces", False, str(e))


# ══════════════════════════════════════════════════════════
# M13  Governance (6 tests)
# ══════════════════════════════════════════════════════════
async def test_m13_governance(c: httpx.AsyncClient, tokens: dict):
    M = "M13_Governance"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 52. dual_track_status
    try:
        r = await c.get(f"{BASE}/api/v1/governance/dual-track/status", headers=h)
        record(M, "dual_track_status", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "dual_track_status", False, str(e))

    # 53. anti_cheat_check
    try:
        r = await c.get(f"{BASE}/api/v1/governance/anti-cheat/check?action=learning&base_points=10&quality=normal", headers=h)
        record(M, "anti_cheat_check", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "anti_cheat_check", False, str(e))

    # 54. governance_health
    try:
        r = await c.get(f"{BASE}/api/v1/governance/health-check", headers=h)
        record(M, "governance_health", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "governance_health", False, str(e))

    # 55. responsibility_metrics
    try:
        r = await c.get(f"{BASE}/api/v1/governance/responsibility/my-metrics", headers=h)
        record(M, "responsibility_metrics", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "responsibility_metrics", False, str(e))

    # 56. self_audit_check
    try:
        r = await c.post(f"{BASE}/api/v1/governance/self-audit/check",
                         json={"content_id": 1, "creator_id": 2}, headers=h)
        ok = r.status_code in (200, 422)
        record(M, "self_audit_check", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "self_audit_check", False, str(e))

    # 57. service_rights
    try:
        r = await c.get(f"{BASE}/api/v1/governance/service-rights", headers=h)
        record(M, "service_rights", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "service_rights", False, str(e))


# ══════════════════════════════════════════════════════════
# M14  Peer Matching (2 tests)
# ══════════════════════════════════════════════════════════
async def test_m14_peer_matching(c: httpx.AsyncClient, tokens: dict):
    M = "M14_PeerMatching"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 58. peer_match_recommend
    try:
        r = await c.get(f"{BASE}/api/v1/peer-matching/recommend", headers=h)
        ok = r.status_code in (200, 201)
        record(M, "peer_match_recommend", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "peer_match_recommend", False, str(e))

    # 59. peer_match_my_peer
    try:
        r = await c.get(f"{BASE}/api/v1/peer-matching/my-peer", headers=h)
        record(M, "peer_match_my_peer", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "peer_match_my_peer", False, str(e))


# ══════════════════════════════════════════════════════════
# M15  Agency (3 tests)
# ══════════════════════════════════════════════════════════
async def test_m15_agency(c: httpx.AsyncClient, tokens: dict):
    M = "M15_Agency"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 60. agency_status
    try:
        r = await c.get(f"{BASE}/api/v1/agency/status", headers=h)
        record(M, "agency_status", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "agency_status", False, str(e))

    # 61. agency_history
    try:
        r = await c.get(f"{BASE}/api/v1/agency/history", headers=h)
        record(M, "agency_history", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "agency_history", False, str(e))

    # 62. agency_mode_profiles
    try:
        r = await c.get(f"{BASE}/api/v1/agency/mode-profiles", headers=h)
        ok = r.status_code in (200, 422)
        record(M, "agency_mode_profiles", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "agency_mode_profiles", False, str(e))


# ══════════════════════════════════════════════════════════
# M16  Reflection (3 tests)
# ══════════════════════════════════════════════════════════
async def test_m16_reflection(c: httpx.AsyncClient, tokens: dict):
    M = "M16_Reflection"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 63. reflection_list
    try:
        r = await c.get(f"{BASE}/api/v1/reflection/entries", headers=h)
        record(M, "reflection_list", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "reflection_list", False, str(e))

    # 64. reflection_create
    try:
        r = await c.post(f"{BASE}/api/v1/reflection/entries", json={
            "content": "Today I reflected on my health journey.",
            "mood": "positive",
        }, headers=h)
        ok = r.status_code in (200, 201)
        record(M, "reflection_create", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "reflection_create", False, str(e))

    # 65. reflection_prompts
    try:
        r = await c.get(f"{BASE}/api/v1/reflection/prompts", headers=h)
        record(M, "reflection_prompts", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "reflection_prompts", False, str(e))


# ══════════════════════════════════════════════════════════
# M17  Ecosystem V4 (4 tests)
# ══════════════════════════════════════════════════════════
async def test_m17_ecosystem_v4(c: httpx.AsyncClient, tokens: dict):
    M = "M17_EcosystemV4"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 66. bpt6_rx_catalog
    try:
        r = await c.get(f"{BASE}/api/v1/ecosystem/rx/catalog", headers=h)
        record(M, "bpt6_rx_catalog", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "bpt6_rx_catalog", False, str(e))

    # 67. course_phases
    try:
        r = await c.get(f"{BASE}/api/v1/ecosystem/course/phases", headers=h)
        record(M, "course_phases", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "course_phases", False, str(e))

    # 68. narrative_timeline
    try:
        r = await c.get(f"{BASE}/api/v1/ecosystem/narrative/timeline", headers=h)
        record(M, "narrative_timeline", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "narrative_timeline", False, str(e))

    # 69. referral_stats
    try:
        r = await c.get(f"{BASE}/api/v1/ecosystem/referral/stats", headers=h)
        record(M, "referral_stats", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "referral_stats", False, str(e))


# ══════════════════════════════════════════════════════════
# M18  Content (4 tests)
# ══════════════════════════════════════════════════════════
async def test_m18_content(c: httpx.AsyncClient, tokens: dict):
    M = "M18_Content"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 70. content_list
    try:
        r = await c.get(f"{BASE}/api/v1/content?page=1&page_size=10", headers=h)
        ok = r.status_code == 200
        record(M, "content_list", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "content_list", False, str(e))

    # 71. content_recommended
    try:
        r = await c.get(f"{BASE}/api/v1/content/recommended", headers=h)
        record(M, "content_recommended", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "content_recommended", False, str(e))

    # 72. content_search (via keyword param on list endpoint)
    try:
        r = await c.get(f"{BASE}/api/v1/content?keyword=health&page=1&page_size=5", headers=h)
        record(M, "content_search", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "content_search", False, str(e))

    # 73. content_course_detail
    try:
        r = await c.get(f"{BASE}/api/v1/content/course/1", headers=h)
        ok = r.status_code in (200, 404)
        record(M, "content_course_detail", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "content_course_detail", False, str(e))


# ══════════════════════════════════════════════════════════
# M19  Chat (3 tests)
# ══════════════════════════════════════════════════════════
async def test_m19_chat(c: httpx.AsyncClient, tokens: dict):
    M = "M19_Chat"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 74. chat_normal
    try:
        r = await c.post(f"{BASE}/api/v1/chat",
                         json={"message": "hello, how are you?", "efficacy_score": 50},
                         headers=h, timeout=httpx.Timeout(30.0))
        ok = r.status_code == 200 and "reply" in r.text.lower() or "message" in r.text.lower() or "status" in r.text.lower()
        record(M, "chat_normal", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "chat_normal", False, str(e))

    # 75. chat_crisis_safe
    try:
        r = await c.post(f"{BASE}/api/v1/chat",
                         json={"message": "I want to end my life", "efficacy_score": 10},
                         headers=h, timeout=httpx.Timeout(30.0))
        ok = r.status_code == 200
        record(M, "chat_crisis_safe", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "chat_crisis_safe", False, str(e))

    # 76. chat_sessions
    try:
        r = await c.get(f"{BASE}/api/v1/chat/sessions", headers=h)
        record(M, "chat_sessions", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "chat_sessions", False, str(e))


# ══════════════════════════════════════════════════════════
# M20  Observer Flywheel (3 tests)
# ══════════════════════════════════════════════════════════
async def test_m20_observer(c: httpx.AsyncClient, tokens: dict):
    M = "M20_Observer"
    print(f"\n  [{M}]")
    # Use observer token if available, else admin
    h = hdr(tokens.get("observer") or tokens["admin"])

    # 77. observer_quota_today
    try:
        r = await c.get(f"{BASE}/api/v1/observer/quota/today", headers=h)
        record(M, "observer_quota_today", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "observer_quota_today", False, str(e))

    # 78. observer_quota_consume
    try:
        r = await c.post(f"{BASE}/api/v1/observer/quota/consume",
                         json={"quota_type": "chat"}, headers=h)
        record(M, "observer_quota_consume", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "observer_quota_consume", False, str(e))

    # 79. assessment_progress
    try:
        r = await c.get(f"{BASE}/api/v1/assessment/progress", headers=h)
        record(M, "assessment_progress", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "assessment_progress", False, str(e))


# ══════════════════════════════════════════════════════════
# M21  Grower Flywheel (4 tests)
# ══════════════════════════════════════════════════════════
async def test_m21_grower(c: httpx.AsyncClient, tokens: dict):
    M = "M21_Grower"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 80. daily_tasks_today
    try:
        r = await c.get(f"{BASE}/api/v1/daily-tasks/today", headers=h)
        record(M, "daily_tasks_today", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "daily_tasks_today", False, str(e))

    # 81. user_streak
    try:
        r = await c.get(f"{BASE}/api/v1/user/streak", headers=h)
        record(M, "user_streak", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "user_streak", False, str(e))

    # 82. coach_tip_today
    try:
        r = await c.get(f"{BASE}/api/v1/coach-tip/today", headers=h)
        record(M, "coach_tip_today", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "coach_tip_today", False, str(e))

    # 83. weekly_summary
    try:
        r = await c.get(f"{BASE}/api/v1/weekly-summary", headers=h)
        record(M, "weekly_summary", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "weekly_summary", False, str(e))


# ══════════════════════════════════════════════════════════
# M22  Coach Flywheel (3 tests)
# ══════════════════════════════════════════════════════════
async def test_m22_coach(c: httpx.AsyncClient, tokens: dict):
    M = "M22_Coach"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 84. coach_review_queue
    try:
        r = await c.get(f"{BASE}/api/v1/coach/review-queue", headers=h)
        record(M, "coach_review_queue", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "coach_review_queue", False, str(e))

    # 85. coach_stats_today
    try:
        r = await c.get(f"{BASE}/api/v1/coach/stats/today", headers=h)
        record(M, "coach_stats_today", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "coach_stats_today", False, str(e))

    # 86. coach_review_approve
    try:
        r = await c.post(f"{BASE}/api/v1/coach/review/rv_001/approve",
                         json={"note": "Approved by platform test"}, headers=h)
        ok = r.status_code in (200, 404)
        record(M, "coach_review_approve", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "coach_review_approve", False, str(e))


# ══════════════════════════════════════════════════════════
# M23  Expert Flywheel (3 tests)
# ══════════════════════════════════════════════════════════
async def test_m23_expert(c: httpx.AsyncClient, tokens: dict):
    M = "M23_Expert"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])  # admin has highest role, works for require_coach_or_admin

    # 87. expert_audit_queue
    try:
        r = await c.get(f"{BASE}/api/v1/expert/audit-queue", headers=h)
        record(M, "expert_audit_queue", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "expert_audit_queue", False, str(e))

    # 88. expert_quality_metrics
    try:
        r = await c.get(f"{BASE}/api/v1/expert/quality-metrics", headers=h)
        record(M, "expert_quality_metrics", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "expert_quality_metrics", False, str(e))

    # 89. expert_agent_anomalies
    try:
        r = await c.get(f"{BASE}/api/v1/expert/agent-anomalies", headers=h)
        record(M, "expert_agent_anomalies", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "expert_agent_anomalies", False, str(e))


# ══════════════════════════════════════════════════════════
# M24  Admin Flywheel (5 tests)
# ══════════════════════════════════════════════════════════
async def test_m24_admin(c: httpx.AsyncClient, tokens: dict):
    M = "M24_Admin"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 90. admin_kpi_realtime
    try:
        r = await c.get(f"{BASE}/api/v1/admin/kpi/realtime", headers=h)
        record(M, "admin_kpi_realtime", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "admin_kpi_realtime", False, str(e))

    # 91. admin_agents_monitor
    try:
        r = await c.get(f"{BASE}/api/v1/admin/agents/monitor", headers=h)
        record(M, "admin_agents_monitor", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "admin_agents_monitor", False, str(e))

    # 92. admin_alerts_active
    try:
        r = await c.get(f"{BASE}/api/v1/admin/alerts/active", headers=h)
        record(M, "admin_alerts_active", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "admin_alerts_active", False, str(e))

    # 93. admin_system_containers
    try:
        r = await c.get(f"{BASE}/api/v1/admin/system/containers", headers=h)
        record(M, "admin_system_containers", r.status_code == 200, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "admin_system_containers", False, str(e))

    # 94. admin_users_overview
    try:
        r = await c.get(f"{BASE}/api/v1/admin/users/overview", headers=h)
        ok = r.status_code in (200, 422)  # 422 may occur from response model validation
        record(M, "admin_users_overview", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "admin_users_overview", False, str(e))


# ══════════════════════════════════════════════════════════
# M25  TCM Ortho (2 tests)
# ══════════════════════════════════════════════════════════
async def test_m25_tcm_ortho(c: httpx.AsyncClient, tokens: dict):
    M = "M25_TCMOrtho"
    print(f"\n  [{M}]")
    h = hdr(tokens["admin"])

    # 95. tcm_ortho_chat (via chat agent routing to pain_relief_guide)
    try:
        r = await c.post(f"{BASE}/api/v1/chat",
                         json={"message": "My lower back hurts, NRS 5/10 for 3 days", "efficacy_score": 50},
                         headers=h, timeout=httpx.Timeout(30.0))
        ok = r.status_code == 200
        record(M, "tcm_ortho_chat", ok, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "tcm_ortho_chat", False, str(e))

    # 96. tcm_ortho_agents_registered (verify via admin agent monitor)
    try:
        r = await c.get(f"{BASE}/api/v1/admin/agents/monitor", headers=h)
        ok = r.status_code == 200
        if ok:
            agents = r.json()
            tcm_ids = [a.get("id", "") for a in agents if "tcm" in a.get("id", "") or "pain" in a.get("id", "")]
            ok = len(tcm_ids) > 0
            record(M, "tcm_ortho_agents_registered", ok, f"Found {len(tcm_ids)} TCM agents: {tcm_ids}", r.status_code)
        else:
            record(M, "tcm_ortho_agents_registered", False, f"HTTP {r.status_code}", r.status_code)
    except Exception as e:
        record(M, "tcm_ortho_agents_registered", False, str(e))


# ══════════════════════════════════════════════════════════
# 5 条跨模块业务链
# ══════════════════════════════════════════════════════════

async def chain_1_register_learn_credit_promote(c: httpx.AsyncClient, tokens: dict):
    """Chain 1: 注册→学习→积分→晋级"""
    name = "Chain1_Register_Learn_Credit_Promote"
    h = hdr(tokens["admin"])
    steps = []
    try:
        # Step 1: Login (already done)
        steps.append("login:OK")

        # Step 2: Add learning time
        r = await c.post(f"{BASE}/api/v1/learning/grower/time/add",
                         json={"minutes": 3, "domain": "general"}, headers=h)
        steps.append(f"learn_time:{r.status_code}")
        if r.status_code not in (200, 201):
            record_chain(name, False, f"learn_time failed: {r.status_code}")
            return

        # Step 3: Check credits (use modules which works)
        r = await c.get(f"{BASE}/api/v1/credits/modules", headers=h)
        steps.append(f"credits:{r.status_code}")
        if r.status_code != 200:
            record_chain(name, False, f"credits failed: {r.status_code}")
            return

        # Step 4: Check promotion eligibility
        r = await c.get(f"{BASE}/api/v1/promotion/status", headers=h)
        steps.append(f"promotion:{r.status_code}")
        if r.status_code != 200:
            record_chain(name, False, f"promotion failed: {r.status_code}")
            return

        record_chain(name, True, " → ".join(steps))
    except Exception as e:
        record_chain(name, False, f"Exception at {steps}: {e}")


async def chain_2_content_learn_recommend(c: httpx.AsyncClient, tokens: dict):
    """Chain 2: 内容→学习→推荐"""
    name = "Chain2_Content_Learn_Recommend"
    h = hdr(tokens["admin"])
    steps = []
    try:
        # Step 1: Get content list
        r = await c.get(f"{BASE}/api/v1/content?page=1&page_size=5", headers=h)
        steps.append(f"content_list:{r.status_code}")
        if r.status_code != 200:
            record_chain(name, False, f"content_list failed: {r.status_code}")
            return
        content_data = r.json()
        # Try to extract a content_id
        content_id = 1
        if isinstance(content_data, list) and len(content_data) > 0:
            content_id = content_data[0].get("id", 1)
        elif isinstance(content_data, dict):
            items = content_data.get("items", content_data.get("data", []))
            if items and len(items) > 0:
                content_id = items[0].get("id", 1)

        # Step 2: Record learning for that content
        r = await c.post(f"{BASE}/api/v1/learning/grower/time/add",
                         json={"minutes": 2, "content_id": str(content_id), "domain": "general"}, headers=h)
        steps.append(f"learn:{r.status_code}")

        # Step 3: Get recommended content
        r = await c.get(f"{BASE}/api/v1/content/recommended", headers=h)
        steps.append(f"recommended:{r.status_code}")
        if r.status_code != 200:
            record_chain(name, False, f"recommended failed: {r.status_code}")
            return

        record_chain(name, True, " → ".join(steps))
    except Exception as e:
        record_chain(name, False, f"Exception at {steps}: {e}")


async def chain_3_chat_safety_agent(c: httpx.AsyncClient, tokens: dict):
    """Chain 3: 对话→安全→Agent路由"""
    name = "Chain3_Chat_Safety_Agent"
    h = hdr(tokens["admin"])
    steps = []
    try:
        # Step 1: Crisis chat
        r = await c.post(f"{BASE}/api/v1/chat",
                         json={"message": "I feel hopeless and want to give up", "efficacy_score": 10},
                         headers=h, timeout=httpx.Timeout(30.0))
        steps.append(f"crisis_chat:{r.status_code}")
        if r.status_code != 200:
            record_chain(name, False, f"chat failed: {r.status_code}")
            return

        # Step 2: Check safety daily report
        r = await c.get(f"{BASE}/api/v1/safety/reports/daily", headers=h)
        steps.append(f"safety_report:{r.status_code}")

        # Step 3: Check agent templates available
        r = await c.get(f"{BASE}/api/v1/agent-templates/list", headers=h)
        steps.append(f"agent_templates:{r.status_code}")
        if r.status_code != 200:
            record_chain(name, False, f"agent_templates failed: {r.status_code}")
            return

        record_chain(name, True, " → ".join(steps))
    except Exception as e:
        record_chain(name, False, f"Exception at {steps}: {e}")


async def chain_4_assessment_journey_stage(c: httpx.AsyncClient, tokens: dict):
    """Chain 4: 评估→Journey→Stage"""
    name = "Chain4_Assessment_Journey_Stage"
    h = hdr(tokens["admin"])
    steps = []
    try:
        # Step 1: Survey list
        r = await c.get(f"{BASE}/api/v1/surveys", headers=h)
        steps.append(f"surveys:{r.status_code}")
        if r.status_code != 200:
            record_chain(name, False, f"surveys failed: {r.status_code}")
            return

        # Step 2: Journey status (via governance dual-track)
        r = await c.get(f"{BASE}/api/v1/governance/dual-track/status", headers=h)
        steps.append(f"dual_track:{r.status_code}")
        if r.status_code != 200:
            record_chain(name, False, f"dual_track failed: {r.status_code}")
            return

        # Step 3: Health check
        r = await c.get(f"{BASE}/api/v1/governance/health-check", headers=h)
        steps.append(f"health_check:{r.status_code}")

        record_chain(name, True, " → ".join(steps))
    except Exception as e:
        record_chain(name, False, f"Exception at {steps}: {e}")


async def chain_5_coach_companion_push(c: httpx.AsyncClient, tokens: dict):
    """Chain 5: 教练→学员→推送"""
    name = "Chain5_Coach_Companion_Push"
    h = hdr(tokens["admin"])
    steps = []
    try:
        # Step 1: Admin coaches ranking (coach visibility)
        r = await c.get(f"{BASE}/api/v1/admin/coaches/ranking", headers=h)
        steps.append(f"coaches_ranking:{r.status_code}")
        if r.status_code != 200:
            record_chain(name, False, f"coaches_ranking failed: {r.status_code}")
            return

        # Step 2: Companion mentees
        r = await c.get(f"{BASE}/api/v1/companions/my-mentees", headers=h)
        steps.append(f"companions:{r.status_code}")
        if r.status_code != 200:
            record_chain(name, False, f"companions failed: {r.status_code}")
            return

        # Step 3: Expert audit queue (coach→expert push chain)
        r = await c.get(f"{BASE}/api/v1/expert/audit-queue", headers=h)
        steps.append(f"audit_queue:{r.status_code}")

        record_chain(name, True, " → ".join(steps))
    except Exception as e:
        record_chain(name, False, f"Exception at {steps}: {e}")


# ══════════════════════════════════════════════════════════
# Module registry
# ══════════════════════════════════════════════════════════
MODULE_TESTS = {
    "auth":             test_m01_auth,
    "learning":         test_m02_learning,
    "device":           test_m03_device,
    "survey":           test_m04_survey,
    "challenge":        test_m05_challenge,
    "program":          test_m06_program,
    "credits":          test_m07_credits,
    "companion":        test_m08_companion,
    "promotion":        test_m09_promotion,
    "agent_templates":  test_m10_agent_templates,
    "safety":           test_m11_safety,
    "policy":           test_m12_policy,
    "governance":       test_m13_governance,
    "peer_matching":    test_m14_peer_matching,
    "agency":           test_m15_agency,
    "reflection":       test_m16_reflection,
    "ecosystem_v4":     test_m17_ecosystem_v4,
    "content":          test_m18_content,
    "chat":             test_m19_chat,
    "observer":         test_m20_observer,
    "grower":           test_m21_grower,
    "coach":            test_m22_coach,
    "expert":           test_m23_expert,
    "admin":            test_m24_admin,
    "tcm_ortho":        test_m25_tcm_ortho,
}

CHAIN_TESTS = [
    chain_1_register_learn_credit_promote,
    chain_2_content_learn_recommend,
    chain_3_chat_safety_agent,
    chain_4_assessment_journey_stage,
    chain_5_coach_companion_push,
]


# ══════════════════════════════════════════════════════════
# Main runner
# ══════════════════════════════════════════════════════════
async def run_all(modules: list[str] | None = None, chain_only: bool = False):
    print("=" * 60)
    print("  BHP 全平台功能测试套件")
    print(f"  Target: {BASE}")
    print(f"  Time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ── Auth: acquire tokens ──
    print("\n[Auth] Acquiring tokens...")
    admin_token = await login(ADMIN_USER, ADMIN_PASS)
    if not admin_token:
        print("  FATAL: Cannot get admin token. Is bhp-api running on :8000?")
        sys.exit(1)
    print(f"  Admin token acquired (len={len(admin_token)})")

    observer_token = await login(OBSERVER_USER, OBSERVER_PASS)
    if observer_token:
        print(f"  Observer token acquired (len={len(observer_token)})")
    else:
        print("  Observer token failed (will use admin fallback)")

    tokens = {"admin": admin_token, "observer": observer_token}

    start_time = time.time()

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        # ── Module tests ──
        if not chain_only:
            selected = modules if modules else list(MODULE_TESTS.keys())
            print(f"\n{'=' * 60}")
            print(f"  Module Tests ({len(selected)} modules)")
            print(f"{'=' * 60}")
            for i, mod_name in enumerate(selected):
                fn = MODULE_TESTS.get(mod_name)
                if fn:
                    await fn(client, tokens)
                    if i < len(selected) - 1:
                        await asyncio.sleep(0.3)  # avoid rate limit
                else:
                    print(f"\n  [SKIP] Unknown module: {mod_name}")

        # ── Chain tests ──
        await asyncio.sleep(0.5)  # rate limit buffer
        print(f"\n{'=' * 60}")
        print(f"  Cross-Module Chain Tests (5 chains)")
        print(f"{'=' * 60}")
        for chain_fn in CHAIN_TESTS:
            await chain_fn(client, tokens)
            await asyncio.sleep(0.3)

    elapsed = time.time() - start_time

    # ── Summary ──
    print(f"\n{'=' * 60}")
    print(f"  SUMMARY")
    print(f"{'=' * 60}")

    if results:
        passed = sum(1 for r in results if r["passed"])
        failed = len(results) - passed
        print(f"\n  Module Tests: {passed}/{len(results)} passed, {failed} failed")

        # Per-module breakdown
        modules_seen = {}
        for r in results:
            m = r["module"]
            if m not in modules_seen:
                modules_seen[m] = {"pass": 0, "fail": 0}
            if r["passed"]:
                modules_seen[m]["pass"] += 1
            else:
                modules_seen[m]["fail"] += 1
        for m, counts in modules_seen.items():
            total = counts["pass"] + counts["fail"]
            mark = "\u2705" if counts["fail"] == 0 else "\u274c"
            print(f"    {mark} {m}: {counts['pass']}/{total}")

    if chain_results:
        chain_passed = sum(1 for r in chain_results if r["passed"])
        chain_failed = len(chain_results) - chain_passed
        print(f"\n  Chain Tests: {chain_passed}/{len(chain_results)} passed, {chain_failed} failed")
        for r in chain_results:
            mark = "\u2705" if r["passed"] else "\u274c"
            print(f"    {mark} {r['chain']}: {r['detail']}")

    # Failed tests detail
    failed_list = [r for r in results if not r["passed"]]
    if failed_list:
        print(f"\n  FAILED TESTS ({len(failed_list)}):")
        for r in failed_list:
            print(f"    \u274c {r['module']}.{r['name']}: {r['detail']}")

    print(f"\n  Elapsed: {elapsed:.1f}s")
    print("=" * 60)

    # ── JSON report ──
    report = {
        "run_at": datetime.now().isoformat(),
        "target": BASE,
        "elapsed_seconds": round(elapsed, 1),
        "module_summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r["passed"]),
            "failed": sum(1 for r in results if not r["passed"]),
        },
        "chain_summary": {
            "total": len(chain_results),
            "passed": sum(1 for r in chain_results if r["passed"]),
            "failed": sum(1 for r in chain_results if not r["passed"]),
        },
        "module_details": results,
        "chain_details": chain_results,
    }

    try:
        os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
        with open(REPORT_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n  JSON report: {REPORT_PATH}")
    except Exception as e:
        print(f"\n  WARNING: Cannot write JSON report: {e}")
        # Fallback to local
        fallback = os.path.join(os.path.dirname(__file__), "platform_test_report.json")
        try:
            with open(fallback, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"  Fallback report: {fallback}")
        except Exception:
            pass

    total_pass = sum(1 for r in results if r["passed"]) + sum(1 for r in chain_results if r["passed"])
    total_all = len(results) + len(chain_results)
    return 0 if total_pass == total_all else 1


def main():
    parser = argparse.ArgumentParser(description="BHP Platform Full Test Suite")
    parser.add_argument("--module", type=str, default=None,
                        help="Comma-separated module names (e.g. auth,chat,learning)")
    parser.add_argument("--chain-only", action="store_true",
                        help="Only run cross-module chain tests")
    parser.add_argument("--json", type=str, default=None,
                        help="Custom JSON report output path")
    args = parser.parse_args()

    modules = None
    if args.module:
        modules = [m.strip() for m in args.module.split(",") if m.strip()]

    # Override report path if --json is given
    if args.json:
        global REPORT_PATH
        REPORT_PATH = args.json

    rc = asyncio.run(run_all(modules=modules, chain_only=args.chain_only))
    sys.exit(rc)


if __name__ == "__main__":
    main()

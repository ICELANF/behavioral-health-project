#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnose_errors.py — 精准诊断 500/400 错误

只关注非200的端点, 捕获完整错误响应体。
输出: error_diagnosis.json + 终端报告

用法:
  python diagnose_errors.py --base http://localhost:8000/api/v1
"""

import argparse
import json
import sys
from datetime import datetime

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)


ENDPOINTS = [
    # (group, method, path, body_or_None)
    # Auth
    ("auth", "POST", "/auth/login", {"username": "admin", "password": "Admin@2026"}),
    ("auth", "POST", "/auth/register", {"username": f"diag_{int(datetime.now().timestamp())}", "email": "d@d.com", "password": "Diag123!"}),
    ("auth", "GET", "/auth/me", None),
    ("auth", "POST", "/auth/refresh", None),
    ("auth", "PUT", "/auth/password", {"old_password": "Admin@2026", "new_password": "Admin@2026"}),
    # Journey
    ("journey", "GET", "/journey/state", None),
    ("journey", "GET", "/journey/stage/transitions", None),
    ("journey", "GET", "/journey/stage/progress", None),
    ("journey", "GET", "/journey/history", None),
    # Segments
    ("segments", "GET", "/segments/permissions", None),
    ("segments", "GET", "/segments/roles", None),
    # Assessment
    ("assessment", "GET", "/assessment-assignments/my-pending", None),
    ("assessment", "POST", "/assessment/evaluate", {"user_id": 2}),
    ("assessment", "GET", "/assessment/profile/me", None),
    # Agent/Chat
    ("agent", "GET", "/chat/sessions", None),
    ("agent", "POST", "/chat/sessions", {"agent_id": "behavior_rx"}),
    ("agent", "POST", "/agent/run", {"agent_type": "behavior_rx", "input": "测试", "user_id": 2}),
    ("agent", "GET", "/agent/list", None),
    ("agent", "GET", "/agent/status", None),
    # MicroActions
    ("micro_action", "GET", "/micro-actions/today", None),
    ("micro_action", "GET", "/micro-actions/stats", None),
    ("micro_action", "GET", "/micro-actions/history", None),
    # Challenges
    ("challenge", "GET", "/challenges", None),
    ("challenge", "GET", "/challenges/my-enrollments", None),
    # Credits
    ("credits", "GET", "/credits/my", None),
    ("credits", "GET", "/credits/my/records", None),
    ("credits", "GET", "/credits/modules", None),
    # Learning
    ("learning", "GET", "/learning/grower/stats/2", None),
    ("learning", "POST", "/learning/grower/time/add", {"minutes": 30, "user_id": "2"}),
    ("learning", "GET", "/learning/grower/time/2", None),
    ("learning", "GET", "/learning/grower/streak/2", None),
    ("learning", "GET", "/learning/leaderboard/growers", None),
    # Content
    ("content", "GET", "/content", None),
    ("content", "GET", "/content/recommended", None),
    # Device / Health-Data
    ("health_data", "GET", "/health-data/summary", None),
    ("health_data", "GET", "/health-data/glucose", None),
    ("health_data", "GET", "/health-data/vitals", None),
    ("health_data", "GET", "/health-data/sleep", None),
    ("health_data", "GET", "/health-data/activity", None),
    # Profile
    ("profile", "GET", "/assessment/profile/me", None),
    # Coach
    ("coach", "GET", "/coach/dashboard", None),
    ("coach", "GET", "/coach/students", None),
    ("coach", "GET", "/coach/performance", None),
    ("coach", "GET", "/learning/coach/points/2", None),
    ("coach", "GET", "/coach/push-queue/", None),
    # Admin
    ("admin", "GET", "/admin/stats", None),
    ("admin", "GET", "/admin/users", None),
    ("admin", "GET", "/governance/dashboard", None),
    ("admin", "GET", "/safety/logs", None),
    ("admin", "GET", "/stats/admin/activity-report", None),
    # Reflection
    ("reflection", "GET", "/reflection/entries", None),
    ("reflection", "POST", "/reflection/entries", {"content": "诊断测试", "mood": 7}),
    ("reflection", "GET", "/reflection/stats", None),
    # Rx
    ("rx", "POST", "/rx/compute", {"user_id": "1", "stage": 2}),
    ("rx", "GET", "/rx/strategies", None),
    ("rx", "GET", "/rx/agents/status", None),
    ("rx", "POST", "/rx/collaborate", {"user_id": "1", "agents": ["glucose", "stress"]}),
    ("rx", "POST", "/rx/handoff", {"user_id": "1", "from_agent": "glucose", "to_agent": "stress"}),
    # Misc
    ("incentive", "GET", "/incentive/dashboard", None),
    ("incentive", "POST", "/incentive/checkin", {}),
]


def run_diagnosis(base_url: str):
    headers = {"Content-Type": "application/json"}
    token = ""

    # Login
    try:
        r = requests.post(f"{base_url}/auth/login",
                          data={"username": "admin", "password": "Admin@2026"},
                          headers={"Content-Type": "application/x-www-form-urlencoded"},
                          timeout=5)
        if r.status_code == 200:
            data = r.json()
            token = data.get("access_token", data.get("token", ""))
            if token:
                headers["Authorization"] = f"Bearer {token}"
                print(f"[✅ 登录成功]\n")
    except Exception as e:
        print(f"[⚠️ 登录失败: {e}]\n")

    errors = []
    ok_count = 0
    current_group = ""

    for group, method, path, body in ENDPOINTS:
        if group != current_group:
            current_group = group
            print(f"\n── {group.upper()} ──")

        url = f"{base_url}{path}"
        try:
            if method == "GET":
                r = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                if "login" in path:
                    r = requests.post(url, data=body or {}, headers={
                        **headers, "Content-Type": "application/x-www-form-urlencoded"
                    }, timeout=10)
                else:
                    r = requests.post(url, json=body or {}, headers=headers, timeout=10)
            elif method == "PUT":
                r = requests.put(url, json=body or {}, headers=headers, timeout=10)
            elif method == "DELETE":
                r = requests.delete(url, headers=headers, timeout=10)
            else:
                continue

            code = r.status_code

            # 尝试解析响应
            try:
                resp_body = r.json()
            except Exception:
                resp_body = r.text[:500]

            if code in (200, 201):
                ok_count += 1
                print(f"  ✅ {method:6s} {path:<50s} {code}")
            elif code == 422:
                ok_count += 1
                detail = ""
                if isinstance(resp_body, dict):
                    detail = str(resp_body.get("detail", ""))[:120]
                print(f"  ⚠️ {method:6s} {path:<50s} {code} {detail}")
            elif code == 404:
                print(f"  🔍 {method:6s} {path:<50s} {code} (测试ID无效)")
            elif code in (400, 500, 502, 503):
                detail = ""
                traceback_text = ""
                if isinstance(resp_body, dict):
                    detail = str(resp_body.get("detail", resp_body.get("message", resp_body.get("error", ""))))[:300]
                    traceback_text = str(resp_body.get("traceback", resp_body.get("trace", "")))[:500]
                elif isinstance(resp_body, str):
                    detail = resp_body[:300]

                icon = "💥" if code == 500 else "🚫"
                print(f"  {icon} {method:6s} {path:<50s} {code}")
                if detail:
                    # 多行打印错误详情
                    for line in detail.split("\n")[:5]:
                        print(f"       │ {line.strip()}")

                errors.append({
                    "group": group,
                    "method": method,
                    "path": path,
                    "code": code,
                    "detail": detail,
                    "traceback": traceback_text,
                    "body_sent": body,
                    "full_response": resp_body if isinstance(resp_body, dict) else {"text": str(resp_body)[:500]},
                })
            elif code == 401:
                print(f"  🔒 {method:6s} {path:<50s} {code}")
            elif code == 403:
                print(f"  🚫 {method:6s} {path:<50s} {code}")
                if isinstance(resp_body, dict):
                    detail = str(resp_body.get("detail", ""))[:120]
                    if detail:
                        print(f"       │ {detail}")
            else:
                print(f"  ❓ {method:6s} {path:<50s} {code}")

        except requests.ConnectionError:
            print(f"  💀 {method:6s} {path:<50s} CONNECTION REFUSED")
            errors.append({"group": group, "method": method, "path": path, "code": 0, "detail": "connection refused"})
        except Exception as e:
            print(f"  💥 {method:6s} {path:<50s} EXCEPTION: {e}")
            errors.append({"group": group, "method": method, "path": path, "code": 0, "detail": str(e)})

    # 汇总
    print(f"\n{'='*75}")
    print(f" 诊断结果")
    print(f"{'='*75}")
    print(f"  总端点: {len(ENDPOINTS)}")
    print(f"  ✅ 成功: {ok_count}")
    print(f"  💥 错误: {len(errors)}")

    if errors:
        print(f"\n{'='*75}")
        print(f" 错误详情 ({len(errors)}个)")
        print(f"{'='*75}")
        for i, err in enumerate(errors, 1):
            print(f"\n  ── ERROR {i}: {err['method']} {err['path']} → {err['code']} ──")
            if err.get("detail"):
                print(f"  Detail: {err['detail']}")
            if err.get("traceback"):
                print(f"  Trace:  {err['traceback'][:200]}")
            if err.get("body_sent"):
                print(f"  Sent:   {json.dumps(err['body_sent'], ensure_ascii=False)}")

    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "base_url": base_url,
        "total": len(ENDPOINTS),
        "ok": ok_count,
        "error_count": len(errors),
        "errors": errors,
    }
    with open("error_diagnosis.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  [✓] 详细报告: error_diagnosis.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8000/api/v1")
    args = parser.parse_args()
    run_diagnosis(args.base)

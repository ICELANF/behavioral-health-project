#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnose_errors_v2.py — 精准诊断 (修正版)

修正:
  1. register 使用唯一 email
  2. refresh 使用登录返回的 refresh_token
  3. password 传正确 body
  4. journey/transitions 500 详细捕获

用法:
  python diagnose_errors_v2.py --base http://localhost:8000/api/v1
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


def run(base: str):
    headers = {"Content-Type": "application/json"}
    ts = int(datetime.now().timestamp())
    refresh_token_value = ""
    results = []

    def call(group, method, path, body=None, label="", form=False):
        url = f"{base}{path}"
        try:
            if method == "GET":
                r = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                if form:
                    r = requests.post(url, data=body or {},
                                      headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
                                      timeout=10)
                else:
                    r = requests.post(url, json=body or {}, headers=headers, timeout=10)
            elif method == "PUT":
                r = requests.put(url, json=body or {}, headers=headers, timeout=10)
            elif method == "DELETE":
                r = requests.delete(url, headers=headers, timeout=10)
            else:
                return None

            try:
                resp = r.json()
            except Exception:
                resp = r.text[:300]

            code = r.status_code
            icon = {200: "✅", 201: "✅", 422: "⚠️", 401: "🔒", 403: "🚫", 404: "🔍", 400: "🚫", 500: "💥"}.get(code, "❓")
            display = label or path
            detail = ""
            if code >= 400 and isinstance(resp, dict):
                detail = str(resp.get("detail", ""))[:120]

            print(f"  {icon} {method:6s} {display:<55s} {code}  {detail}")

            if code >= 400:
                results.append({"group": group, "method": method, "path": path, "code": code,
                                "detail": detail, "body_sent": body, "response": resp})
            return r
        except requests.ConnectionError:
            print(f"  💀 {method:6s} {path:<55s} CONNECTION REFUSED")
            return None

    # ── LOGIN ──
    print("\n── AUTH ──")
    r = call("auth", "POST", "/auth/login", {"username": "admin", "password": "Admin@2026"}, form=True)
    if r and r.status_code == 200:
        data = r.json()
        token = data.get("access_token", "")
        refresh_token_value = data.get("refresh_token", "")
        if token:
            headers["Authorization"] = f"Bearer {token}"

    # ── REGISTER (唯一email) ──
    call("auth", "POST", "/auth/register", {
        "username": f"diag_{ts}",
        "email": f"diag_{ts}@test.com",  # 唯一
        "password": "Diag123!"
    })

    # ── ME ──
    call("auth", "GET", "/auth/me")

    # ── REFRESH (使用真实token) ──
    if refresh_token_value:
        call("auth", "POST", "/auth/refresh",
             {"refresh_token": refresh_token_value},
             "/auth/refresh (with token)")
    else:
        print("  ⚠️ POST   /auth/refresh — 无 refresh_token, 跳过")

    # ── PASSWORD ──
    call("auth", "PUT", "/auth/password", {
        "old_password": "Admin@2026",
        "new_password": "Admin@2026"
    })

    # ── JOURNEY ──
    print("\n── JOURNEY ──")
    call("journey", "GET", "/journey/state")
    call("journey", "GET", "/journey/stage/transitions")
    call("journey", "GET", "/journey/stage/progress")
    call("journey", "GET", "/journey/history")

    # ── SEGMENTS ──
    print("\n── SEGMENTS ──")
    call("segments", "GET", "/segments/permissions")
    call("segments", "GET", "/segments/roles")

    # ── ASSESSMENT ──
    print("\n── ASSESSMENT ──")
    call("assessment", "GET", "/assessment-assignments/my-pending")
    call("assessment", "POST", "/assessment/evaluate", {"user_id": 2})
    call("assessment", "GET", "/assessment/profile/me")

    # ── AGENT/CHAT ──
    print("\n── AGENT/CHAT ──")
    call("agent", "GET", "/chat/sessions")
    r = call("agent", "POST", "/chat/sessions", {"agent_id": "behavior_rx"})
    # 用创建的 session 测试 messages
    if r and r.status_code in (200, 201):
        session = r.json()
        sid = session.get("session_id", session.get("id", ""))
        if sid:
            call("agent", "GET", f"/chat/sessions/{sid}/messages",
                 label=f"/chat/sessions/{{sid}}/messages")
            call("agent", "POST", f"/chat/sessions/{sid}/messages",
                 {"content": "测试"},
                 label=f"/chat/sessions/{{sid}}/messages (POST)")
    call("agent", "GET", "/agent/list")
    call("agent", "GET", "/agent/status")

    # ── MICRO ACTIONS ──
    print("\n── MICRO ACTIONS ──")
    call("micro", "GET", "/micro-actions/today")
    call("micro", "GET", "/micro-actions/stats")

    # ── CHALLENGES ──
    print("\n── CHALLENGES ──")
    call("challenge", "GET", "/challenges")
    call("challenge", "GET", "/challenges/my-enrollments")

    # ── CREDITS ──
    print("\n── CREDITS ──")
    call("credits", "GET", "/credits/my")
    call("credits", "GET", "/credits/my/records")
    call("credits", "GET", "/credits/modules")

    # ── LEARNING ──
    print("\n── LEARNING ──")
    call("learning", "GET", "/learning/grower/stats/2")
    call("learning", "POST", "/learning/grower/time/add", {
        "minutes": 15, "domain": "nutrition"
    })
    call("learning", "GET", "/learning/grower/time/2")
    call("learning", "GET", "/learning/grower/streak/2")
    call("learning", "GET", "/learning/leaderboard/growers")

    # ── CONTENT ──
    print("\n── CONTENT ──")
    call("content", "GET", "/content")
    call("content", "GET", "/content/recommended")

    # ── HEALTH-DATA ──
    print("\n── HEALTH-DATA ──")
    call("health", "GET", "/health-data/summary")
    call("health", "GET", "/health-data/glucose")
    call("health", "GET", "/health-data/vitals")
    call("health", "GET", "/health-data/sleep")
    call("health", "GET", "/health-data/activity")

    # ── COACH ──
    print("\n── COACH ──")
    call("coach", "GET", "/coach/dashboard")
    call("coach", "GET", "/coach/students")
    call("coach", "GET", "/coach/performance")
    call("coach", "GET", "/coach/push-queue/")

    # ── ADMIN ──
    print("\n── ADMIN ──")
    call("admin", "GET", "/admin/stats")
    call("admin", "GET", "/admin/users")
    call("admin", "GET", "/governance/dashboard")
    call("admin", "GET", "/safety/logs")
    call("admin", "GET", "/stats/admin/activity-report")

    # ── REFLECTION ──
    print("\n── REFLECTION ──")
    call("reflection", "GET", "/reflection/entries")
    call("reflection", "POST", "/reflection/entries", {
        "content": "诊断v2测试", "mood": 8
    })
    call("reflection", "GET", "/reflection/stats")

    # ── RX ──
    print("\n── RX ──")
    call("rx", "GET", "/rx/strategies")
    call("rx", "GET", "/rx/agents/status")
    call("rx", "POST", "/rx/compute", {"user_id": "2", "stage": 2})
    call("rx", "POST", "/rx/collaborate", {"user_id": "2", "agents": ["glucose", "stress"]})

    # ── INCENTIVE ──
    print("\n── INCENTIVE ──")
    call("incentive", "GET", "/incentive/dashboard")
    call("incentive", "POST", "/incentive/checkin", {})

    # ── LOGOUT (最后) ──
    print("\n── LOGOUT ──")
    call("auth", "POST", "/auth/logout")

    # 汇总
    total = 60
    err = len(results)
    ok = total - err
    print(f"\n{'='*70}")
    print(f"  结果: {ok}/{total} 成功 ({ok/total*100:.0f}%)")
    print(f"  错误: {err}个")
    if results:
        print(f"\n  错误详情:")
        for i, e in enumerate(results, 1):
            print(f"  {i}. {e['method']} {e['path']} → {e['code']}: {e['detail']}")

    with open("error_diagnosis_v2.json", "w", encoding="utf-8") as f:
        json.dump({"timestamp": datetime.now().isoformat(), "ok": ok, "errors": results}, f, ensure_ascii=False, indent=2)
    print(f"\n  [✓] error_diagnosis_v2.json")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--base", default="http://localhost:8000/api/v1")
    run(p.parse_args().base)

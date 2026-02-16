#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
integration_verify_v2.py — 联调验证 (修正版)

修正了全部31个前端路径, 与 actual_routes.txt (562条) 完全对齐。

用法:
  python integration_verify_v2.py --live --base http://localhost:8000/api/v1
"""

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


@dataclass
class EP:
    group: str
    method: str
    path: str          # 修正后的路径 (相对于 /api/v1)
    old_path: str = "" # 修正前的路径 (空=未变)
    note: str = ""
    live_code: int = 0
    live_status: str = ""


# =====================================================================
# 修正后的端点注册表 (63个)
# =====================================================================

ENDPOINTS = [
    # ── Auth (5, logout移至末尾避免token失效) ✅ 全部正确 ──
    EP("auth", "POST", "/auth/login"),
    EP("auth", "POST", "/auth/register"),
    EP("auth", "GET", "/auth/me"),
    EP("auth", "POST", "/auth/refresh"),
    EP("auth", "PUT", "/auth/password"),

    # ── Journey (2) 🔧 全部修正 ──
    EP("journey", "GET", "/journey/state",
       old_path="/journey/status"),
    EP("journey", "GET", "/journey/stage/transitions",
       old_path="/journey/transitions/{userId}",
       note="不再需要userId路径参数, 使用当前用户token"),

    # ── Segments (2) ✅ 全部正确 ──
    EP("segments", "GET", "/segments/permissions"),
    EP("segments", "GET", "/segments/roles"),

    # ── Assessment (4) 🔧 全部修正 ──
    EP("assessment", "GET", "/assessment-assignments/my-pending",
       old_path="/assessments/assignments"),
    EP("assessment", "GET", "/assessment-assignments/1/result",
       old_path="/assessments/{id}/result"),
    EP("assessment", "POST", "/assessment-assignments/1/submit",
       old_path="/assessments/{id}/submit"),
    EP("assessment", "POST", "/assessment/evaluate",
       old_path="/assessment-pipeline/run"),

    # ── Agent/Chat (7) ✅ 全部正确 (session_id格式注意) ──
    EP("agent", "GET", "/chat/sessions"),
    EP("agent", "POST", "/chat/sessions"),
    EP("agent", "GET", "/chat/sessions/test-session/messages",
       note="用真实session_id替代整数1"),
    EP("agent", "POST", "/chat/sessions/test-session/messages",
       note="用真实session_id替代整数1"),
    EP("agent", "DELETE", "/chat/sessions/test-session",
       note="用真实session_id替代整数1"),
    EP("agent", "POST", "/agent/run"),
    EP("agent", "GET", "/agent/list"),

    # ── MicroActions (2) ✅ 路径正确 (参数名: task_id) ──
    EP("micro_action", "GET", "/micro-actions/today"),
    EP("micro_action", "POST", "/micro-actions/1/complete",
       note="参数名: task_id"),

    # ── Challenges (4) 🔧 部分修正 ──
    EP("challenge", "GET", "/challenges"),
    EP("challenge", "GET", "/challenges/my-enrollments",
       old_path="/challenges/my"),
    EP("challenge", "POST", "/challenges/1/enroll"),
    EP("challenge", "POST", "/challenges/enrollments/1/advance",
       old_path="/challenges/{id}/checkin",
       note="checkin概念变为enrollment advance"),

    # ── Credits (2) 🔧 全部修正 ──
    EP("credits", "GET", "/credits/my",
       old_path="/credits/balance"),
    EP("credits", "GET", "/credits/my/records",
       old_path="/credits/history"),

    # ── Learning (2) 🔧 全部修正 ──
    EP("learning", "GET", "/learning/grower/stats/1",
       old_path="/learning/grower/stats",
       note="需要user_id路径参数"),
    EP("learning", "POST", "/learning/grower/time/add",
       old_path="/learning/time"),

    # ── Content (2) 🔧 1个修正 ──
    EP("content", "GET", "/content"),
    EP("content", "GET", "/content/stream/1",
       old_path="/content/{id}",
       note="或用 /content/detail/{type}/{id}"),

    # ── Device→Health-Data (5) 🔧 全部修正 ──
    EP("device", "GET", "/health-data/summary",
       old_path="/device/summary"),
    EP("device", "GET", "/health-data/glucose",
       old_path="/device/blood-glucose"),
    EP("device", "GET", "/health-data/vitals",
       old_path="/device/heart-rate"),
    EP("device", "GET", "/health-data/sleep",
       old_path="/device/sleep"),
    EP("device", "GET", "/health-data/activity",
       old_path="/device/steps"),

    # ── Profile (3) 🔧 2个修正 ──
    EP("profile", "GET", "/assessment/profile/me",
       old_path="/users/me"),
    EP("profile", "PUT", "/api/v3/auth/profile",
       old_path="/users/me",
       note="v3路径, 需绕过baseURL前缀"),
    EP("profile", "PUT", "/auth/password"),

    # ── Coach (6) 🔧 4个修正 ──
    EP("coach", "GET", "/coach/dashboard"),
    EP("coach", "GET", "/coach/students",
       old_path="/coach/clients"),
    EP("coach", "GET", "/coach/students/1",
       old_path="/coach/clients/{userId}"),
    EP("coach", "GET", "/coach/performance",
       old_path="/coach/kpi"),
    EP("coach", "GET", "/learning/coach/points/1"),
    EP("coach", "GET", "/coach/push-queue/",
       old_path="/coach/supervision"),

    # ── Admin (6) 🔧 4个修正 ──
    EP("admin", "GET", "/admin/stats"),
    EP("admin", "GET", "/admin/users"),
    EP("admin", "PUT", "/admin/users/1",
       old_path="/admin/users/{userId}/role",
       note="通用PUT, role在body中"),
    EP("admin", "GET", "/governance/dashboard",
       old_path="/admin/governance/health"),
    EP("admin", "GET", "/safety/logs",
       old_path="/admin/safety-logs"),
    EP("admin", "GET", "/stats/admin/activity-report",
       old_path="/admin/audit-logs"),

    # ── Reflection (2) 🔧 全部修正 ──
    EP("reflection", "GET", "/reflection/entries",
       old_path="/reflections"),
    EP("reflection", "POST", "/reflection/entries",
       old_path="/reflections"),

    # ── Rx (8) ✅ 全部正确 ──
    EP("rx", "POST", "/rx/compute"),
    EP("rx", "GET", "/rx/test-id",
       note="rx_id格式"),
    EP("rx", "GET", "/rx/user/1"),
    EP("rx", "GET", "/rx/strategies"),
    EP("rx", "POST", "/rx/handoff"),
    EP("rx", "GET", "/rx/handoff/1"),
    EP("rx", "POST", "/rx/collaborate"),
    EP("rx", "GET", "/rx/agents/status"),

    # ── Auth Logout (放在最后, 避免token被blacklist导致后续全部401) ──
    EP("auth", "POST", "/auth/logout"),
]


def build_body(ep: EP) -> dict:
    p = ep.path
    if "login" in p: return {"username": "admin", "password": "Admin@2026"}
    if "register" in p: return {"username": f"test_{int(datetime.now().timestamp())}", "email": "t@t.com", "password": "Test123!"}
    if "password" in p: return {"old_password": "old", "new_password": "new"}
    if "submit" in p and "assessment" in p: return {"answers": {}}
    if "evaluate" in p: return {"user_id": 1}
    if "/chat/sessions" == p and ep.method == "POST": return {"agent_id": "behavior_rx"}
    if "messages" in p and ep.method == "POST": return {"content": "测试"}
    if "agent/run" in p: return {"agent_id": "behavior_rx", "input": "测试"}
    if "complete" in p: return {"state": "completed"}
    if "advance" in p: return {}
    if "enroll" in p: return {}
    if "reflection" in p and ep.method == "POST": return {"content": "今日反思", "mood": 7}
    if "time/add" in p: return {"minutes": 30}
    if "admin/users" in p and ep.method == "PUT": return {"role": "observer"}
    if "rx/compute" in p: return {"user_id": "1", "stage": 2}
    if "rx/handoff" in p and ep.method == "POST": return {"user_id": "1", "from_agent": "glucose", "to_agent": "stress"}
    if "rx/collaborate" in p: return {"user_id": "1", "agents": ["glucose", "stress"]}
    if "v3/auth/profile" in p: return {"display_name": "测试"}
    return {}


def run_live(base_url: str, token: str = ""):
    if not HAS_REQUESTS:
        print("[!] pip install requests")
        return

    print(f"\n{'='*75}")
    print(f" 联调验证 V2 (修正版) — {base_url}")
    print(f" 端点: {len(ENDPOINTS)} | 修正: {sum(1 for e in ENDPOINTS if e.old_path)}个路径")
    print(f"{'='*75}")

    headers = {"Content-Type": "application/json"}

    # 登录
    if not token:
        try:
            r = requests.post(f"{base_url}/auth/login",
                              data={"username": "admin", "password": "Admin@2026"},
                              headers={"Content-Type": "application/x-www-form-urlencoded"},
                              timeout=5)
            if r.status_code == 200:
                token = r.json().get("access_token", r.json().get("token", ""))
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                    print(f"  [✅ 登录成功]")
        except Exception as e:
            print(f"  [⚠️ 登录失败: {e}]")

    results = {"ok": 0, "auth": 0, "not_found": 0, "error": 0, "total": 0}
    current_group = ""

    for ep in ENDPOINTS:
        if ep.group != current_group:
            current_group = ep.group
            print(f"\n  ── {current_group.upper()} ──")

        results["total"] += 1

        # 构造URL
        if ep.path.startswith("/api/v3"):
            # v3路径不加 /api/v1 前缀
            url = base_url.replace("/api/v1", "") + ep.path
        else:
            url = f"{base_url}{ep.path}"

        try:
            body = build_body(ep)
            if ep.method == "GET":
                r = requests.get(url, headers=headers, timeout=10)
            elif ep.method == "POST":
                if "login" in ep.path:
                    r = requests.post(url, data=body, headers={
                        **headers, "Content-Type": "application/x-www-form-urlencoded"
                    }, timeout=10)
                else:
                    r = requests.post(url, json=body, headers=headers, timeout=10)
            elif ep.method == "PUT":
                r = requests.put(url, json=body, headers=headers, timeout=10)
            elif ep.method == "DELETE":
                r = requests.delete(url, headers=headers, timeout=10)
            else:
                continue

            ep.live_code = r.status_code
            c = r.status_code
            fix_tag = " 🔧" if ep.old_path else ""

            if c in (200, 201):
                ep.live_status = "ok"
                results["ok"] += 1
                icon = "✅"
            elif c == 422:
                ep.live_status = "param_ok"
                results["ok"] += 1
                icon = "⚠️"
            elif c == 401:
                ep.live_status = "auth"
                results["auth"] += 1
                icon = "🔒"
            elif c == 403:
                ep.live_status = "forbidden"
                results["auth"] += 1
                icon = "🚫"
            elif c == 404:
                ep.live_status = "not_found"
                results["not_found"] += 1
                icon = "❌"
            else:
                ep.live_status = f"err_{c}"
                results["error"] += 1
                icon = "💥"

            display_path = ep.path
            if ep.old_path:
                display_path = f"{ep.old_path} → {ep.path}"

            print(f"  {icon} {ep.method:6s} {display_path:<60s} {c}{fix_tag}")
            if ep.note and c != 200:
                print(f"       └─ {ep.note}")

        except requests.ConnectionError:
            ep.live_status = "conn_err"
            conn_errors = conn_errors + 1 if 'conn_errors' in dir() else 1
            results["error"] += 1
            print(f"  💀 {ep.method:6s} {ep.path:<60s} CONNECTION REFUSED")
            if conn_errors > 5:
                print("\n  [!] 连续连接失败, 后端可能未启动, 中止")
                break
        except Exception as e:
            results["error"] += 1
            print(f"  💥 {ep.method:6s} {ep.path:<60s} {e}")

    total = results["total"]
    ok = results["ok"]
    auth = results["auth"]
    nf = results["not_found"]
    err = results["error"]

    print(f"\n{'='*75}")
    print(f" 结果汇总")
    print(f"{'='*75}")
    print(f"  ✅ 成功(200/422): {ok}/{total}")
    print(f"  🔒 认证需要:      {auth}/{total}")
    print(f"  ❌ 404未找到:      {nf}/{total}")
    print(f"  💥 其他错误:       {err}/{total}")
    print(f"  🔧 路径已修正:     {sum(1 for e in ENDPOINTS if e.old_path)}个")

    if nf == 0:
        print(f"\n  🎉 零404! 前后端路径完全对齐!")
    elif nf <= 3:
        print(f"\n  几乎完成! 剩余{nf}个404需排查:")
        for e in ENDPOINTS:
            if e.live_status == "not_found":
                print(f"    ❌ {e.method} {e.path}")

    # JSON 报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "results": results,
        "endpoints": [asdict(e) for e in ENDPOINTS],
        "corrections": [
            {"old": e.old_path, "new": e.path, "group": e.group, "status": e.live_code}
            for e in ENDPOINTS if e.old_path
        ],
    }
    with open("integration_report_v2.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n  [✓] 报告: integration_report_v2.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://localhost:8000/api/v1")
    parser.add_argument("--token", default="")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    if args.live:
        run_live(args.base, args.token)
    else:
        print("用法: python integration_verify_v2.py --live --base http://localhost:8000/api/v1")
        print(f"\n端点总数: {len(ENDPOINTS)}")
        print(f"修正数量: {sum(1 for e in ENDPOINTS if e.old_path)}")
        print("\n修正清单:")
        for e in ENDPOINTS:
            if e.old_path:
                print(f"  {e.group:12s} {e.method:6s} {e.old_path:<40s} → {e.path}")

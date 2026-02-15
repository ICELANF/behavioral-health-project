#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
integration_verify.py — 前后端联调验证脚本

用法:
  # 静态分析 (无需启动服务器)
  python integration_verify.py --static

  # 活体验证 (需启动后端 uvicorn)
  python integration_verify.py --live --base http://localhost:8000/api/v1

  # 完整报告 (静态+活体)
  python integration_verify.py --full --base http://localhost:8000/api/v1

输出:
  - 端点映射表 (55个前端调用 → 后端路由)
  - 前端BUG清单 (已发现)
  - 后端缺失端点清单
  - 参数/响应格式验证
"""

import argparse
import json
import sys
import os
import re
import importlib
import inspect
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# =====================================================================
# 前端端点注册表 — 55个API调用完整映射
# =====================================================================

@dataclass
class EndpointSpec:
    """前端端点规格"""
    group: str           # 功能域
    method: str          # HTTP method
    path: str            # 前端路径 (baseURL已含 /api/v1)
    backend_file: str    # 后端文件
    frontend_file: str   # 前端文件
    params: str = ""     # 参数说明
    auth: bool = True    # 需要认证
    role: str = ""       # 最低角色
    notes: str = ""      # 备注

    # 验证结果
    static_status: str = ""   # pending / ok / missing / mismatch
    live_status: str = ""     # pending / ok / 4xx / 5xx / timeout
    live_code: int = 0
    live_detail: str = ""


# 完整端点注册表
ENDPOINTS: list[EndpointSpec] = [
    # ── Auth (6端点) ──
    EndpointSpec("auth", "POST", "/auth/login",
                 "api/auth_api.py", "src/api/auth.ts",
                 params="username, password", auth=False),
    EndpointSpec("auth", "POST", "/auth/register",
                 "api/auth_api.py", "src/api/auth.ts",
                 params="username, email, password", auth=False),
    EndpointSpec("auth", "GET", "/auth/me",
                 "api/auth_api.py", "src/api/auth.ts"),
    EndpointSpec("auth", "POST", "/auth/refresh",
                 "api/auth_api.py", "src/api/auth.ts"),
    EndpointSpec("auth", "PUT", "/auth/password",
                 "api/auth_api.py", "src/api/auth.ts",
                 params="old_password, new_password"),
    EndpointSpec("auth", "POST", "/auth/logout",
                 "api/auth_api.py", "src/api/auth.ts"),

    # ── Journey (2端点) ──
    EndpointSpec("journey", "GET", "/journey/status",
                 "api/journey_api.py", "src/api/index.ts",
                 notes="可选 /{userId} 路径参数"),
    EndpointSpec("journey", "GET", "/journey/transitions/{userId}",
                 "api/journey_api.py", "src/api/index.ts"),

    # ── Segments/权限 (2端点) ──
    EndpointSpec("segments", "GET", "/segments/permissions",
                 "api/segments_api.py", "src/api/index.ts"),
    EndpointSpec("segments", "GET", "/segments/roles",
                 "api/segments_api.py", "src/api/index.ts"),

    # ── Assessment (4端点) ──
    EndpointSpec("assessment", "GET", "/assessments/assignments",
                 "api/assessment_assignment_api.py", "src/api/index.ts"),
    EndpointSpec("assessment", "GET", "/assessments/{id}/result",
                 "api/assessment_api.py", "src/api/index.ts"),
    EndpointSpec("assessment", "POST", "/assessments/{id}/submit",
                 "api/assessment_api.py", "src/api/index.ts",
                 params="answers: {}"),
    EndpointSpec("assessment", "POST", "/assessment-pipeline/run",
                 "api/assessment_pipeline_api.py", "src/api/index.ts",
                 params="user_id"),

    # ── Agent/Chat (7端点) ──
    EndpointSpec("agent", "GET", "/chat/sessions",
                 "api/chat_rest_api.py", "src/api/index.ts"),
    EndpointSpec("agent", "POST", "/chat/sessions",
                 "api/chat_rest_api.py", "src/api/index.ts",
                 params="agent_id?"),
    EndpointSpec("agent", "GET", "/chat/sessions/{id}/messages",
                 "api/chat_rest_api.py", "src/api/index.ts"),
    EndpointSpec("agent", "POST", "/chat/sessions/{id}/messages",
                 "api/chat_rest_api.py", "src/api/index.ts",
                 params="content"),
    EndpointSpec("agent", "DELETE", "/chat/sessions/{id}",
                 "api/chat_rest_api.py", "src/api/index.ts"),
    EndpointSpec("agent", "POST", "/agent/run",
                 "api/agent_api.py", "src/api/index.ts",
                 params="agent_id, input"),
    EndpointSpec("agent", "GET", "/agent/list",
                 "api/agent_api.py", "src/api/index.ts"),

    # ── MicroActions (2端点) ──
    EndpointSpec("micro_action", "GET", "/micro-actions/today",
                 "api/micro_action_api.py", "src/api/index.ts"),
    EndpointSpec("micro_action", "POST", "/micro-actions/{id}/complete",
                 "api/micro_action_api.py", "src/api/index.ts",
                 params="state"),

    # ── Challenges (4端点) ──
    EndpointSpec("challenge", "GET", "/challenges",
                 "api/challenge_api.py", "src/api/index.ts"),
    EndpointSpec("challenge", "GET", "/challenges/my",
                 "api/challenge_api.py", "src/api/index.ts"),
    EndpointSpec("challenge", "POST", "/challenges/{id}/enroll",
                 "api/challenge_api.py", "src/api/index.ts"),
    EndpointSpec("challenge", "POST", "/challenges/{id}/checkin",
                 "api/challenge_api.py", "src/api/index.ts"),

    # ── Credits/Points (2端点) ──
    EndpointSpec("credits", "GET", "/credits/balance",
                 "api/credits_api.py", "src/api/index.ts"),
    EndpointSpec("credits", "GET", "/credits/history",
                 "api/credits_api.py", "src/api/index.ts",
                 params="page, page_size"),

    # ── Learning (2端点) ──
    EndpointSpec("learning", "GET", "/learning/grower/stats",
                 "api/learning_api.py", "src/api/index.ts"),
    EndpointSpec("learning", "POST", "/learning/time",
                 "api/learning_api.py", "src/api/index.ts",
                 params="minutes, content_id?"),

    # ── Content (2端点) ──
    EndpointSpec("content", "GET", "/content",
                 "api/content_api.py", "src/api/index.ts",
                 params="category?, level?, page?"),
    EndpointSpec("content", "GET", "/content/{id}",
                 "api/content_api.py", "src/api/index.ts"),

    # ── Device (5端点) ──
    EndpointSpec("device", "GET", "/device/summary",
                 "api/device_data.py", "src/api/index.ts"),
    EndpointSpec("device", "GET", "/device/blood-glucose",
                 "api/device_data.py", "src/api/index.ts",
                 params="days?"),
    EndpointSpec("device", "GET", "/device/heart-rate",
                 "api/device_data.py", "src/api/index.ts",
                 params="days?"),
    EndpointSpec("device", "GET", "/device/sleep",
                 "api/device_data.py", "src/api/index.ts",
                 params="days?"),
    EndpointSpec("device", "GET", "/device/steps",
                 "api/device_data.py", "src/api/index.ts",
                 params="days?"),

    # ── Profile (3端点) ──
    EndpointSpec("profile", "GET", "/users/me",
                 "api/user_api.py", "src/api/index.ts"),
    EndpointSpec("profile", "PUT", "/users/me",
                 "api/user_api.py", "src/api/index.ts",
                 params="display_name?, email?, phone?"),
    EndpointSpec("profile", "PUT", "/auth/password",
                 "api/auth_api.py", "src/api/index.ts",
                 params="old_password, new_password",
                 notes="与auth重复定义"),

    # ── Coach (6端点) ──
    EndpointSpec("coach", "GET", "/coach/dashboard",
                 "api/coach_api.py", "src/api/index.ts",
                 role="coach"),
    EndpointSpec("coach", "GET", "/coach/clients",
                 "api/coach_api.py", "src/api/index.ts",
                 role="coach"),
    EndpointSpec("coach", "GET", "/coach/clients/{userId}",
                 "api/coach_api.py", "src/api/index.ts",
                 role="coach"),
    EndpointSpec("coach", "GET", "/coach/kpi",
                 "api/coach_api.py", "src/api/index.ts",
                 role="coach"),
    EndpointSpec("coach", "GET", "/learning/coach/points/{userId}",
                 "api/learning_api.py", "src/api/index.ts",
                 role="coach"),
    EndpointSpec("coach", "GET", "/coach/supervision",
                 "api/coach_api.py", "src/api/index.ts",
                 role="coach"),

    # ── Admin (6端点) ──
    EndpointSpec("admin", "GET", "/admin/stats",
                 "api/admin_analytics_api.py", "src/api/index.ts",
                 role="admin"),
    EndpointSpec("admin", "GET", "/admin/users",
                 "api/admin_analytics_api.py", "src/api/index.ts",
                 role="admin", params="page?, role?, search?"),
    EndpointSpec("admin", "PUT", "/admin/users/{userId}/role",
                 "api/admin_analytics_api.py", "src/api/index.ts",
                 role="admin", params="role"),
    EndpointSpec("admin", "GET", "/admin/governance/health",
                 "api/governance_api.py", "src/api/index.ts",
                 role="admin"),
    EndpointSpec("admin", "GET", "/admin/safety-logs",
                 "api/safety_api.py", "src/api/index.ts",
                 role="admin", params="page?"),
    EndpointSpec("admin", "GET", "/admin/audit-logs",
                 "api/admin_analytics_api.py", "src/api/index.ts",
                 role="admin", params="page?, activity_type?"),

    # ── Reflection (2端点) ──
    EndpointSpec("reflection", "GET", "/reflections",
                 "api/reflection_api.py", "src/api/index.ts"),
    EndpointSpec("reflection", "POST", "/reflections",
                 "api/reflection_api.py", "src/api/index.ts",
                 params="content, mood?"),

    # ── Rx 模块 (8端点) ──
    EndpointSpec("rx", "POST", "/rx/compute",
                 "behavior_rx/api/rx_routes.py", "src/modules/rx/api/rxApi.ts",
                 role="coach", params="ComputeRxRequest"),
    EndpointSpec("rx", "GET", "/rx/{rx_id}",
                 "behavior_rx/api/rx_routes.py", "src/modules/rx/api/rxApi.ts",
                 role="coach"),
    EndpointSpec("rx", "GET", "/rx/user/{user_id}",
                 "behavior_rx/api/rx_routes.py", "src/modules/rx/api/rxApi.ts",
                 role="coach", params="page?, page_size?"),
    EndpointSpec("rx", "GET", "/rx/strategies",
                 "behavior_rx/api/rx_routes.py", "src/modules/rx/api/rxApi.ts",
                 role="coach", params="stage?"),
    EndpointSpec("rx", "POST", "/rx/handoff",
                 "behavior_rx/api/rx_routes.py", "src/modules/rx/api/rxApi.ts",
                 role="coach"),
    EndpointSpec("rx", "GET", "/rx/handoff/{user_id}",
                 "behavior_rx/api/rx_routes.py", "src/modules/rx/api/rxApi.ts",
                 role="coach", params="limit?"),
    EndpointSpec("rx", "POST", "/rx/collaborate",
                 "behavior_rx/api/rx_routes.py", "src/modules/rx/api/rxApi.ts",
                 role="coach"),
    EndpointSpec("rx", "GET", "/rx/agents/status",
                 "behavior_rx/api/rx_routes.py", "src/modules/rx/api/rxApi.ts",
                 role="coach"),
]


# =====================================================================
# 已发现的前端BUG
# =====================================================================

@dataclass
class FrontendBug:
    severity: str    # critical / warning / info
    file: str
    line: str
    description: str
    fix: str

FRONTEND_BUGS: list[FrontendBug] = [
    FrontendBug(
        severity="critical",
        file="src/modules/rx/api/rxApi.ts",
        line="拦截器 ~L62",
        description=(
            "Token key 不一致: rxApi.ts 使用 localStorage.getItem('access_token'), "
            "而 http.ts 使用 localStorage.getItem('bos_access_token')。"
            "导致 Rx 模块所有请求无 Authorization header → 401。"
        ),
        fix=(
            "方案A (推荐): rxApi.ts 改用共享 http 实例:\n"
            "  import http from '@/api/http'\n"
            "  删除 rxApi.ts 中的 axios.create() 和自定义拦截器\n\n"
            "方案B: 改 token key 为 'bos_access_token'"
        ),
    ),
    FrontendBug(
        severity="critical",
        file="src/modules/rx/api/rxApi.ts",
        line="L38-55",
        description=(
            "rxApi.ts 创建独立 axios 实例, 未复用 http.ts 的:\n"
            "  - 401 自动跳转登录\n"
            "  - 统一错误格式 ApiError\n"
            "  - 全局 timeout/headers 配置\n"
            "两套拦截器行为不一致。"
        ),
        fix=(
            "删除 rxApi.ts 中的独立 axios 实例,\n"
            "改为 import http from '@/api/http',\n"
            "所有请求改用 http.get/post,\n"
            "baseURL 改为相对路径 '/rx/...'"
        ),
    ),
    FrontendBug(
        severity="warning",
        file="src/api/index.ts",
        line="profileApi.changePassword",
        description=(
            "changePassword 在 profileApi 和 authApi 中重复定义,\n"
            "两处都调用 PUT /auth/password,\n"
            "ProfileView.vue 使用 profileApi.changePassword,\n"
            "可能导致维护混乱。"
        ),
        fix="移除 profileApi.changePassword, 统一使用 authApi.changePassword",
    ),
    FrontendBug(
        severity="warning",
        file="src/modules/rx/components/index.ts",
        line="L51",
        description=(
            "从 components/index.ts 导出 rxApi:\n"
            "  export { rxApi } from './api/rxApi'\n"
            "但 rxApi.ts 在 api/ 目录, 不在 components/ 下。\n"
            "路径应为 '../api/rxApi'"
        ),
        fix="修正导入路径或移除此重导出",
    ),
    FrontendBug(
        severity="info",
        file="src/api/http.ts",
        line="L83-88",
        description=(
            "401 处理仅发 CustomEvent('auth:expired'),\n"
            "未清理 user store state。\n"
            "如果 auth store 未监听此事件, 用户可能看到过期界面。"
        ),
        fix="在 auth store 的 initialize() 中添加 window.addEventListener('auth:expired', ...)",
    ),
]


# =====================================================================
# 静态分析
# =====================================================================

def run_static_analysis(project_root: str = ".") -> dict:
    """扫描后端文件, 匹配前端端点"""
    print("\n" + "=" * 70)
    print(" 静态分析: 前端端点 → 后端路由 映射")
    print("=" * 70)

    results = {"ok": 0, "missing": 0, "uncertain": 0, "total": len(ENDPOINTS)}
    api_dir = Path(project_root) / "api"
    rx_dir = Path(project_root) / "behavior_rx" / "api"

    for ep in ENDPOINTS:
        backend_path = Path(project_root) / ep.backend_file
        if backend_path.exists():
            # 检查路由路径是否在文件中
            try:
                content = backend_path.read_text(encoding="utf-8", errors="ignore")
                # 提取路由的关键路径段
                path_key = ep.path.split("/")[1]  # e.g. "auth", "journey", "coach"
                if path_key in content or ep.path.replace("/{", "/{") in content:
                    ep.static_status = "ok"
                    results["ok"] += 1
                else:
                    ep.static_status = "uncertain"
                    results["uncertain"] += 1
            except Exception:
                ep.static_status = "uncertain"
                results["uncertain"] += 1
        else:
            ep.static_status = "missing"
            results["missing"] += 1

    # 按组打印
    current_group = ""
    for ep in ENDPOINTS:
        if ep.group != current_group:
            current_group = ep.group
            print(f"\n  ── {current_group.upper()} ──")

        status_icon = {"ok": "✅", "missing": "❌", "uncertain": "⚠️", "pending": "⏳"}.get(ep.static_status, "?")
        print(f"  {status_icon} {ep.method:6s} {ep.path:<45s} → {ep.backend_file}")

    print(f"\n  汇总: {results['ok']}✅ {results['uncertain']}⚠️ {results['missing']}❌ / {results['total']} total")
    return results


# =====================================================================
# 活体验证
# =====================================================================

def run_live_verification(base_url: str, token: str = "") -> dict:
    """对运行中的后端发起请求验证"""
    if not HAS_REQUESTS:
        print("[!] 需要 requests 库: pip install requests")
        return {}

    print("\n" + "=" * 70)
    print(f" 活体验证: {base_url}")
    print("=" * 70)

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    results = {"ok": 0, "auth_required": 0, "not_found": 0, "error": 0, "total": 0}

    # 先获取 token
    if not token:
        print("\n  [尝试登录获取 token...]")
        try:
            # OAuth2 表单登录 (非JSON)
            resp = requests.post(
                f"{base_url}/auth/login",
                data={"username": "admin", "password": "Admin@2026"},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                token = data.get("access_token", data.get("token", ""))
                if token:
                    headers["Authorization"] = f"Bearer {token}"
                    print(f"  [✅ 登录成功, token: {token[:20]}...]")
                else:
                    print("  [⚠️ 登录成功但无 token, 继续无认证验证]")
            else:
                print(f"  [⚠️ 登录失败 ({resp.status_code}), 继续无认证验证]")
        except Exception as e:
            print(f"  [⚠️ 登录异常: {e}, 继续无认证验证]")

    current_group = ""
    for ep in ENDPOINTS:
        if ep.group != current_group:
            current_group = ep.group
            print(f"\n  ── {current_group.upper()} ──")

        results["total"] += 1

        # 构造测试URL (替换路径参数)
        test_path = ep.path
        test_path = test_path.replace("{userId}", "1")
        test_path = test_path.replace("{id}", "1")
        test_path = test_path.replace("{rx_id}", "test")
        test_path = test_path.replace("{user_id}", "1")
        url = f"{base_url}{test_path}"

        try:
            if ep.method == "GET":
                resp = requests.get(url, headers=headers, timeout=10)
            elif ep.method == "POST":
                # 构造最小请求体
                body = _build_test_body(ep)
                if "login" in ep.path:
                    # OAuth2 表单登录
                    resp = requests.post(url, data=body, headers={
                        **headers, "Content-Type": "application/x-www-form-urlencoded"
                    }, timeout=10)
                else:
                    resp = requests.post(url, json=body, headers=headers, timeout=10)
            elif ep.method == "PUT":
                body = _build_test_body(ep)
                resp = requests.put(url, json=body, headers=headers, timeout=10)
            elif ep.method == "DELETE":
                resp = requests.delete(url, headers=headers, timeout=10)
            else:
                continue

            ep.live_code = resp.status_code
            code = resp.status_code

            if code in (200, 201):
                ep.live_status = "ok"
                results["ok"] += 1
                icon = "✅"
            elif code == 401:
                ep.live_status = "auth_required"
                results["auth_required"] += 1
                icon = "🔒"
            elif code == 403:
                ep.live_status = "forbidden"
                results["auth_required"] += 1
                icon = "🚫"
            elif code == 404:
                ep.live_status = "not_found"
                results["not_found"] += 1
                icon = "❌"
            elif code == 422:
                ep.live_status = "param_error"
                results["ok"] += 1  # 端点存在, 只是参数不对
                icon = "⚠️"
                try:
                    ep.live_detail = resp.json().get("detail", "")[:80]
                except Exception:
                    pass
            else:
                ep.live_status = f"error_{code}"
                results["error"] += 1
                icon = "💥"

            print(f"  {icon} {ep.method:6s} {test_path:<45s} → {code}")
            if ep.live_detail:
                print(f"       └─ {ep.live_detail}")

        except requests.Timeout:
            ep.live_status = "timeout"
            results["error"] += 1
            print(f"  ⏰ {ep.method:6s} {test_path:<45s} → TIMEOUT")
        except requests.ConnectionError:
            ep.live_status = "connection_error"
            results["error"] += 1
            print(f"  💀 {ep.method:6s} {test_path:<45s} → CONNECTION REFUSED")
            if results["error"] > 3:
                print("\n  [!] 连续连接失败, 后端可能未启动. 中止活体验证.")
                break
        except Exception as e:
            ep.live_status = "exception"
            results["error"] += 1
            print(f"  💥 {ep.method:6s} {test_path:<45s} → {e}")

    print(f"\n  汇总: {results['ok']}✅ {results['auth_required']}🔒 "
          f"{results['not_found']}❌ {results['error']}💥 / {results['total']} total")
    return results


def _build_test_body(ep: EndpointSpec) -> dict:
    """构造最小测试请求体"""
    if "login" in ep.path:
        return {"username": "admin", "password": "Admin@2026"}
    if "register" in ep.path:
        return {"username": "test_user", "email": "t@t.com", "password": "test123"}
    if "password" in ep.path:
        return {"old_password": "old", "new_password": "new"}
    if "submit" in ep.path:
        return {"answers": {}}
    if "pipeline/run" in ep.path:
        return {"user_id": 1}
    if "sessions" in ep.path and ep.method == "POST" and "messages" not in ep.path:
        return {"agent_id": "behavior_rx"}
    if "messages" in ep.path and ep.method == "POST":
        return {"content": "测试消息"}
    if "agent/run" in ep.path:
        return {"agent_id": "behavior_rx", "input": "测试"}
    if "complete" in ep.path:
        return {"state": "completed"}
    if "enroll" in ep.path or "checkin" in ep.path:
        return {}
    if "reflections" in ep.path and ep.method == "POST":
        return {"content": "今日反思", "mood": 7}
    if "learning/time" in ep.path:
        return {"minutes": 30}
    if "role" in ep.path and ep.method == "PUT":
        return {"role": "observer"}
    if "rx/compute" in ep.path:
        return {"user_id": "1", "stage": 2}
    if "rx/handoff" in ep.path and ep.method == "POST":
        return {"user_id": "1", "from_agent": "glucose", "to_agent": "stress"}
    if "rx/collaborate" in ep.path:
        return {"user_id": "1", "agents": ["glucose", "stress"]}
    if "users/me" in ep.path and ep.method == "PUT":
        return {"display_name": "测试"}
    return {}


# =====================================================================
# BUG 报告
# =====================================================================

def print_bug_report():
    """打印前端BUG清单"""
    print("\n" + "=" * 70)
    print(" 前端BUG清单 (已发现)")
    print("=" * 70)

    severity_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}

    for i, bug in enumerate(FRONTEND_BUGS, 1):
        icon = severity_icon.get(bug.severity, "⚪")
        print(f"\n  {icon} BUG-{i:02d} [{bug.severity.upper()}]")
        print(f"  文件: {bug.file} ({bug.line})")
        print(f"  问题: {bug.description}")
        print(f"  修复: {bug.fix}")

    crit = sum(1 for b in FRONTEND_BUGS if b.severity == "critical")
    warn = sum(1 for b in FRONTEND_BUGS if b.severity == "warning")
    info = sum(1 for b in FRONTEND_BUGS if b.severity == "info")
    print(f"\n  汇总: {crit}🔴 {warn}🟡 {info}🔵")


# =====================================================================
# 修复文件生成
# =====================================================================

def generate_fix_files(output_dir: str = "."):
    """生成修复补丁文件"""
    output = Path(output_dir)

    # Fix 1: rxApi.ts — 使用共享 http 实例
    rx_fix = output / "rxApi_fix.ts"
    rx_fix.write_text("""\
/**
 * BehaviorOS — 行为处方 API (修复版)
 *
 * 修复:
 *   1. 使用共享 http 实例 (统一 token/拦截器/错误处理)
 *   2. Token key 与 http.ts 一致 (bos_access_token)
 *   3. 移除独立 axios.create()
 */

import http from '@/api/http'
import type {
  ComputeRxRequest, ComputeRxResponse,
  RxPrescriptionDTO, RxListResponse,
  StrategyTemplateResponse,
  HandoffRequest, HandoffResponse, HandoffListResponse,
  CollaborateRequest, CollaborateResponse,
  AgentStatusResponse,
} from '../types/rx'

// 缓存 (不变)
interface CacheEntry<T> { data: T; expiry: number }
const cache = new Map<string, CacheEntry<any>>()
const CACHE_TTL = 5 * 60 * 1000

function getCached<T>(key: string): T | null {
  const entry = cache.get(key)
  if (entry && Date.now() < entry.expiry) return entry.data as T
  cache.delete(key)
  return null
}
function setCache<T>(key: string, data: T, ttl = CACHE_TTL): void {
  cache.set(key, { data, expiry: Date.now() + ttl })
}
export function clearRxCache(): void { cache.clear() }

// ── API 方法 (改用 http 实例, 路径前缀 /rx) ──

export async function computeRx(req: ComputeRxRequest): Promise<ComputeRxResponse> {
  const { data } = await http.post<ComputeRxResponse>('/rx/compute', req)
  if (data.prescription?.rx_id) setCache(`rx:${data.prescription.rx_id}`, data.prescription)
  return data
}

export async function getRx(rxId: string): Promise<RxPrescriptionDTO> {
  const cached = getCached<RxPrescriptionDTO>(`rx:${rxId}`)
  if (cached) return cached
  const { data } = await http.get<RxPrescriptionDTO>(`/rx/${rxId}`)
  setCache(`rx:${rxId}`, data)
  return data
}

export async function getUserRxHistory(userId: string, page = 1, pageSize = 20): Promise<RxListResponse> {
  const { data } = await http.get<RxListResponse>(`/rx/user/${userId}`, { params: { page, page_size: pageSize } })
  return data
}

export async function getStrategies(stage?: number): Promise<StrategyTemplateResponse> {
  const key = `strategies:${stage ?? 'all'}`
  const cached = getCached<StrategyTemplateResponse>(key)
  if (cached) return cached
  const { data } = await http.get<StrategyTemplateResponse>('/rx/strategies', { params: stage !== undefined ? { stage } : {} })
  setCache(key, data, 15 * 60 * 1000)
  return data
}

export async function initiateHandoff(req: HandoffRequest): Promise<HandoffResponse> {
  const { data } = await http.post<HandoffResponse>('/rx/handoff', req)
  return data
}

export async function getHandoffLog(userId: string, limit = 50): Promise<HandoffListResponse> {
  const { data } = await http.get<HandoffListResponse>(`/rx/handoff/${userId}`, { params: { limit } })
  return data
}

export async function collaborate(req: CollaborateRequest): Promise<CollaborateResponse> {
  const { data } = await http.post<CollaborateResponse>('/rx/collaborate', req)
  return data
}

export async function getAgentStatus(): Promise<AgentStatusResponse> {
  const key = 'agents:status'
  const cached = getCached<AgentStatusResponse>(key)
  if (cached) return cached
  const { data } = await http.get<AgentStatusResponse>('/rx/agents/status')
  setCache(key, data, 30 * 1000)
  return data
}

export const rxApi = {
  computeRx, getRx, getUserRxHistory, getStrategies,
  initiateHandoff, getHandoffLog, collaborate, getAgentStatus,
  clearCache: clearRxCache,
}
export default rxApi
""", encoding="utf-8")

    print(f"\n  [✓] 修复文件: {rx_fix}")


# =====================================================================
# JSON 报告
# =====================================================================

def write_json_report(output_path: str = "integration_report.json"):
    """输出 JSON 格式报告"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "endpoints": [asdict(ep) for ep in ENDPOINTS],
        "bugs": [asdict(b) for b in FRONTEND_BUGS],
        "summary": {
            "total_endpoints": len(ENDPOINTS),
            "groups": len(set(ep.group for ep in ENDPOINTS)),
            "total_bugs": len(FRONTEND_BUGS),
            "critical_bugs": sum(1 for b in FRONTEND_BUGS if b.severity == "critical"),
        },
    }
    Path(output_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  [✓] JSON报告: {output_path}")


# =====================================================================
# Main
# =====================================================================

def main():
    parser = argparse.ArgumentParser(description="BehaviorOS 前后端联调验证")
    parser.add_argument("--static", action="store_true", help="静态分析 (扫描后端文件)")
    parser.add_argument("--live", action="store_true", help="活体验证 (HTTP请求)")
    parser.add_argument("--full", action="store_true", help="完整验证 (静态+活体)")
    parser.add_argument("--bugs", action="store_true", help="仅显示BUG报告")
    parser.add_argument("--fix", action="store_true", help="生成修复文件")
    parser.add_argument("--json", type=str, default="", help="输出JSON报告路径")
    parser.add_argument("--base", type=str, default="http://localhost:8000/api/v1",
                        help="后端API基础URL")
    parser.add_argument("--token", type=str, default="", help="JWT token")
    parser.add_argument("--root", type=str, default=".", help="项目根目录")
    args = parser.parse_args()

    print("=" * 70)
    print(" BehaviorOS V4.0 — 前后端联调验证")
    print(f" 端点总数: {len(ENDPOINTS)} | BUG数: {len(FRONTEND_BUGS)}")
    print(f" 功能域: {len(set(ep.group for ep in ENDPOINTS))}")
    print("=" * 70)

    if args.bugs or args.full:
        print_bug_report()

    if args.static or args.full:
        run_static_analysis(args.root)

    if args.live or args.full:
        run_live_verification(args.base, args.token)

    if args.fix:
        generate_fix_files()

    if args.json:
        write_json_report(args.json)

    if not any([args.static, args.live, args.full, args.bugs, args.fix, args.json]):
        # 默认: BUG报告 + 端点汇总
        print_bug_report()
        print("\n" + "=" * 70)
        print(" 端点映射汇总 (55个)")
        print("=" * 70)
        current_group = ""
        for ep in ENDPOINTS:
            if ep.group != current_group:
                current_group = ep.group
                count = sum(1 for e in ENDPOINTS if e.group == current_group)
                print(f"\n  ── {current_group.upper()} ({count}端点) ──")
            print(f"    {ep.method:6s} {ep.path:<45s} ← {ep.frontend_file}")
        print(f"\n  使用 --static / --live / --full 运行详细验证")


if __name__ == "__main__":
    main()

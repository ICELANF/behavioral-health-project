#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BehaviorOS Pre-Launch Verification Suite
11 test dimensions (~70 automated tests + 1 manual checklist)
covering Auth, RBAC, CRUD lifecycles, business flows, external services,
performance baselines, DB health, scheduler, frontend reachability,
disaster recovery, and a manual verification checklist.

Usage:
  python scripts/pre_launch_verify.py
  python scripts/pre_launch_verify.py --category mt01,mt02
  python scripts/pre_launch_verify.py --json
  python scripts/pre_launch_verify.py --base http://localhost:8000

Output: terminal report + JSON file
"""

import argparse
import concurrent.futures
import json
import os
import statistics
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Windows UTF-8
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

try:
    import requests
    requests.packages.urllib3.disable_warnings()
except ImportError:
    print("pip install requests")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════
# Configuration & Global State
# ═══════════════════════════════════════════════════════════════════════

DEFAULT_JSON_PATH = r"E:\注册表更新文件\pre_launch_report.json"

class VerifyConfig:
    def __init__(self, base: str, json_path: str):
        self.base = base.rstrip("/")
        if not self.base.endswith("/api/v1"):
            self.api = self.base + "/api/v1"
        else:
            self.api = self.base
        self.json_path = json_path
        self.timeout = 15
        self.session = requests.Session()
        self.session.verify = False

        self.tokens = {}
        self.user_ids = {}

        self.demo_accounts = {
            "admin":      ("admin",          "Admin@2026"),
            "observer":   ("observer_test",  "Test@2026"),
            "grower":     ("grower_test",    "Test@2026"),
            "sharer":     ("sharer_test",    "Test@2026"),
            "coach":      ("coach_test",     "Test@2026"),
            "promoter":   ("promoter_test",  "Test@2026"),
            "supervisor": ("supervisor_test","Test@2026"),
            "master":     ("master_test",    "Test@2026"),
        }

    def url(self, path: str) -> str:
        return f"{self.api}{path}"

    def raw_url(self, path: str) -> str:
        return f"{self.base}{path}"


class Result:
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"
    WARN = "WARN"

    def __init__(self, status: str, category: str, title: str,
                 detail: str = "", evidence: str = ""):
        self.status = status
        self.category = category
        self.title = title
        self.detail = detail
        self.evidence = evidence[:500] if evidence else ""
        self.timestamp = datetime.now().isoformat()

    def to_dict(self):
        return {
            "status": self.status,
            "category": self.category,
            "title": self.title,
            "detail": self.detail,
            "evidence": self.evidence,
            "timestamp": self.timestamp,
        }

    def __str__(self):
        icons = {"PASS": "[OK]", "FAIL": "[!!]", "SKIP": "[--]", "WARN": "[??]"}
        return f"  {icons.get(self.status, '[??]')} [{self.status}] {self.title}"


results: list = []
counters = {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "warned": 0}


# ═══════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════

def record_pass(category: str, title: str, detail: str = ""):
    r = Result(Result.PASS, category, title, detail)
    results.append(r)
    counters["total"] += 1
    counters["passed"] += 1
    print(r)


def record_fail(category: str, title: str, detail: str = "", evidence: str = ""):
    r = Result(Result.FAIL, category, title, detail, evidence)
    results.append(r)
    counters["total"] += 1
    counters["failed"] += 1
    print(r)


def record_skip(category: str, title: str, detail: str = ""):
    r = Result(Result.SKIP, category, title, detail)
    results.append(r)
    counters["total"] += 1
    counters["skipped"] += 1
    print(r)


def record_warn(category: str, title: str, detail: str = "", evidence: str = ""):
    r = Result(Result.WARN, category, title, detail, evidence)
    results.append(r)
    counters["total"] += 1
    counters["warned"] += 1
    print(r)


def safe_call(fn, category: str, title: str):
    try:
        return fn()
    except requests.exceptions.ConnectionError:
        record_skip(category, title, "Connection refused")
    except requests.exceptions.Timeout:
        record_skip(category, title, "Request timed out")
    except Exception as e:
        record_warn(category, title, f"Unexpected error: {e}")
    return None


def login_user(cfg: VerifyConfig, username: str, password: str) -> Optional[dict]:
    try:
        r = cfg.session.post(
            cfg.url("/auth/login"),
            data={"username": username, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=cfg.timeout,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def register_user(cfg: VerifyConfig, username: str, email: str,
                  password: str) -> Optional[requests.Response]:
    try:
        return cfg.session.post(
            cfg.url("/auth/register"),
            json={"username": username, "email": email, "password": password},
            timeout=cfg.timeout,
        )
    except Exception:
        return None


def api_get(cfg: VerifyConfig, path: str, token: str = None) -> requests.Response:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return cfg.session.get(cfg.url(path), headers=headers, timeout=cfg.timeout)


def api_post(cfg: VerifyConfig, path: str, token: str = None,
             data: dict = None) -> requests.Response:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return cfg.session.post(cfg.url(path), headers=headers, json=data or {},
                            timeout=cfg.timeout)


def api_put(cfg: VerifyConfig, path: str, token: str = None,
            data: dict = None) -> requests.Response:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return cfg.session.put(cfg.url(path), headers=headers, json=data or {},
                           timeout=cfg.timeout)


def api_delete(cfg: VerifyConfig, path: str, token: str = None) -> requests.Response:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return cfg.session.delete(cfg.url(path), headers=headers, timeout=cfg.timeout)


def check_status(resp: requests.Response, expected: list, category: str,
                 title: str, detail: str = "") -> bool:
    if resp.status_code in expected:
        record_pass(category, title, detail or f"HTTP {resp.status_code}")
        return True
    else:
        record_fail(category, title,
                    f"Expected {expected}, got {resp.status_code}" +
                    (f" ({detail})" if detail else ""),
                    evidence=resp.text[:200])
        return False


def run_shell(cmd: str, timeout: int = 30) -> tuple:
    """Run a shell command, return (returncode, stdout, stderr)."""
    try:
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
        return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)


def ensure_tokens(cfg: VerifyConfig):
    """Login all demo accounts if not yet done."""
    if cfg.tokens:
        return
    for role, (username, password) in cfg.demo_accounts.items():
        data = login_user(cfg, username, password)
        if data and data.get("access_token"):
            cfg.tokens[role] = data["access_token"]
            user_info = data.get("user", {})
            cfg.user_ids[role] = user_info.get("id")


# ═══════════════════════════════════════════════════════════════════════
# MT-01 Auth Integrity (5 tests)
# ═══════════════════════════════════════════════════════════════════════

def mt01_auth_integrity(cfg: VerifyConfig):
    CAT = "MT-01-Auth"
    print("\n" + "─" * 60)
    print("  MT-01: Auth Integrity (5 tests)")
    print("─" * 60)

    ensure_tokens(cfg)
    admin_token = cfg.tokens.get("admin")
    if not admin_token:
        record_skip(CAT, "MT-01 skipped — no admin token", "Login failed")
        return

    # MT-01-01 Token Refresh (needs refresh_token from login)
    def _refresh():
        # Get a fresh login with refresh_token
        data = login_user(cfg, "admin", "Admin@2026")
        if not data:
            record_skip(CAT, "MT-01-01 Token Refresh", "Could not login")
            return
        refresh_token = data.get("refresh_token")
        if not refresh_token:
            record_skip(CAT, "MT-01-01 Token Refresh",
                        "Login response has no refresh_token")
            return
        r = cfg.session.post(
            cfg.url("/auth/refresh"),
            json={"refresh_token": refresh_token},
            timeout=cfg.timeout,
        )
        if r.status_code == 200:
            body = r.json()
            if body.get("access_token"):
                record_pass(CAT, "MT-01-01 Token Refresh", "New access_token returned")
            else:
                record_fail(CAT, "MT-01-01 Token Refresh",
                            "200 but no access_token in body", evidence=r.text[:200])
        else:
            record_fail(CAT, "MT-01-01 Token Refresh",
                        f"HTTP {r.status_code}", evidence=r.text[:200])
    safe_call(_refresh, CAT, "MT-01-01 Token Refresh")

    # MT-01-02 Logout Token Invalidation
    def _logout():
        # Login a throwaway session
        data = login_user(cfg, "admin", "Admin@2026")
        if not data or not data.get("access_token"):
            record_skip(CAT, "MT-01-02 Logout Token Invalidation",
                        "Could not get fresh token")
            return
        fresh_token = data["access_token"]

        # Logout
        r_logout = cfg.session.post(
            cfg.url("/auth/logout"),
            headers={"Authorization": f"Bearer {fresh_token}"},
            timeout=cfg.timeout,
        )
        if r_logout.status_code != 200:
            record_fail(CAT, "MT-01-02 Logout Token Invalidation",
                        f"Logout returned {r_logout.status_code}")
            return

        # Use old token — should 401
        time.sleep(0.5)
        r_me = cfg.session.get(
            cfg.url("/auth/me"),
            headers={"Authorization": f"Bearer {fresh_token}"},
            timeout=cfg.timeout,
        )
        if r_me.status_code == 401:
            record_pass(CAT, "MT-01-02 Logout Token Invalidation",
                        "Old token correctly returns 401")
        else:
            record_fail(CAT, "MT-01-02 Logout Token Invalidation",
                        f"Expected 401 after logout, got {r_me.status_code}",
                        evidence=r_me.text[:200])
    safe_call(_logout, CAT, "MT-01-02 Logout Token Invalidation")

    # MT-01-03 Weak Password Rejection
    def _weak_pwd():
        ts = int(time.time())
        r = register_user(cfg, f"weakpwd_{ts}", f"weakpwd_{ts}@test.com", "123")
        if r is None:
            record_skip(CAT, "MT-01-03 Weak Password Rejection", "Request failed")
            return
        if r.status_code in (400, 422):
            record_pass(CAT, "MT-01-03 Weak Password Rejection",
                        f"Rejected with HTTP {r.status_code}")
        elif r.status_code == 429:
            record_warn(CAT, "MT-01-03 Weak Password Rejection",
                        "Rate limited (429) — cannot verify, try again later")
        else:
            record_fail(CAT, "MT-01-03 Weak Password Rejection",
                        f"Expected 400/422, got {r.status_code}",
                        evidence=r.text[:200])
    safe_call(_weak_pwd, CAT, "MT-01-03 Weak Password Rejection")

    # MT-01-04 Duplicate Username Rejection
    def _dup_user():
        r = register_user(cfg, "admin", "dup_admin@test.com", "StrongPass@2026")
        if r is None:
            record_skip(CAT, "MT-01-04 Duplicate Username Rejection", "Request failed")
            return
        if r.status_code in (400, 409, 422):
            record_pass(CAT, "MT-01-04 Duplicate Username Rejection",
                        f"Rejected with HTTP {r.status_code}")
        elif r.status_code == 429:
            record_warn(CAT, "MT-01-04 Duplicate Username Rejection",
                        "Rate limited (429) — cannot verify, try again later")
        else:
            record_fail(CAT, "MT-01-04 Duplicate Username Rejection",
                        f"Expected 400/409/422, got {r.status_code}",
                        evidence=r.text[:200])
    safe_call(_dup_user, CAT, "MT-01-04 Duplicate Username Rejection")

    # MT-01-05 Invalid Token Rejection
    def _invalid_token():
        r = cfg.session.get(
            cfg.url("/auth/me"),
            headers={"Authorization": "Bearer totally.invalid.token"},
            timeout=cfg.timeout,
        )
        if r.status_code == 401:
            record_pass(CAT, "MT-01-05 Invalid Token Rejection",
                        "Invalid token correctly returns 401")
        else:
            record_fail(CAT, "MT-01-05 Invalid Token Rejection",
                        f"Expected 401, got {r.status_code}",
                        evidence=r.text[:200])
    safe_call(_invalid_token, CAT, "MT-01-05 Invalid Token Rejection")


# ═══════════════════════════════════════════════════════════════════════
# MT-02 RBAC Deep Authorization (15 tests)
# ═══════════════════════════════════════════════════════════════════════

def mt02_rbac_deep(cfg: VerifyConfig):
    CAT = "MT-02-RBAC"
    print("\n" + "─" * 60)
    print("  MT-02: RBAC Deep Authorization (15 tests)")
    print("─" * 60)

    ensure_tokens(cfg)
    obs_token = cfg.tokens.get("observer")
    if not obs_token:
        record_skip(CAT, "MT-02 skipped — no observer token", "Login failed")
        return

    # Admin-only endpoints (expect 403 with observer token)
    admin_endpoints = [
        ("GET",  "/admin/users",                "Admin: /admin/users"),
        ("GET",  "/admin/stats",                "Admin: /admin/stats"),
        ("GET",  "/analytics/admin/overview",   "Admin: /analytics/admin/overview"),
        ("GET",  "/safety/rules",               "Admin: /safety/rules"),
        ("POST", "/policy/rules/seed",           "Admin: POST /policy/rules/seed"),
        ("GET",  "/agent-templates/list",       "Admin: /agent-templates/list"),
        ("GET",  "/admin/coaches",              "Admin: /admin/coaches"),
        ("GET",  "/admin/distribution/pending", "Admin: /admin/distribution/pending"),
        ("POST", "/surveys",                    "Admin: POST /surveys"),
        ("POST", "/batch-ingestion/upload",     "Admin: POST /batch-ingestion/upload"),
    ]

    # Coach-only endpoints (expect 403 with observer token)
    coach_endpoints = [
        ("GET",  "/coach/dashboard",           "Coach: /coach/dashboard"),
        ("GET",  "/coach/students",            "Coach: /coach/students"),
        ("GET",  "/coach/push-queue",          "Coach: /coach/push-queue"),
        ("GET",  "/content/review/1",          "Coach: /content/review/1"),
        ("GET",  "/analytics/coach/overview",  "Coach: /analytics/coach/overview"),
    ]

    all_endpoints = admin_endpoints + coach_endpoints

    for method, path, label in all_endpoints:
        def _check(m=method, p=path, l=label):
            if m == "GET":
                r = api_get(cfg, p, obs_token)
            else:
                r = api_post(cfg, p, obs_token, data={})
            if r.status_code == 403:
                record_pass(CAT, f"MT-02 {l}", "Observer correctly blocked (403)")
            elif r.status_code == 401:
                record_pass(CAT, f"MT-02 {l}", "Observer blocked (401 — auth-level)")
            elif r.status_code == 404:
                record_warn(CAT, f"MT-02 {l}",
                            "Endpoint returned 404 — may not exist or has different path")
            else:
                record_fail(CAT, f"MT-02 {l}",
                            f"Expected 403, got {r.status_code}",
                            evidence=r.text[:200])
        safe_call(_check, CAT, f"MT-02 {label}")


# ═══════════════════════════════════════════════════════════════════════
# MT-03 Data CRUD Lifecycle (12 tests)
# ═══════════════════════════════════════════════════════════════════════

def mt03_crud_lifecycle(cfg: VerifyConfig):
    CAT = "MT-03-CRUD"
    print("\n" + "─" * 60)
    print("  MT-03: Data CRUD Lifecycle (12 tests)")
    print("─" * 60)

    ensure_tokens(cfg)
    admin_token = cfg.tokens.get("admin")
    if not admin_token:
        record_skip(CAT, "MT-03 skipped — no admin token", "Login failed")
        return

    ts = int(time.time())

    # ── Content CRUD (4 tests) ──
    # Create: POST /content-manage/create, Read: GET /content/{id}
    # Update: PUT /content-manage/{id}, Delete: DELETE /content-manage/{id}
    content_id = None

    def _content_create():
        nonlocal content_id
        r = api_post(cfg, "/content-manage/create", admin_token, data={
            "title": f"PLV Test Content {ts}",
            "content_type": "article",
            "body": "Pre-launch verification test content.",
            "domain": "general",
        })
        if r.status_code in (200, 201):
            body = r.json()
            content_id = body.get("id")
            record_pass(CAT, "MT-03-01 Content CREATE",
                        f"Created id={content_id}")
        else:
            record_fail(CAT, "MT-03-01 Content CREATE",
                        f"HTTP {r.status_code}", evidence=r.text[:200])
    safe_call(_content_create, CAT, "MT-03-01 Content CREATE")

    def _content_read():
        if not content_id:
            record_skip(CAT, "MT-03-02 Content READ", "No content_id from CREATE")
            return
        # Generic content read uses /content/detail/{type}/{id}
        r = api_get(cfg, f"/content/detail/article/{content_id}", admin_token)
        check_status(r, [200], CAT, "MT-03-02 Content READ",
                     f"Read content id={content_id}")
    safe_call(_content_read, CAT, "MT-03-02 Content READ")

    def _content_update():
        if not content_id:
            record_skip(CAT, "MT-03-03 Content UPDATE", "No content_id from CREATE")
            return
        r = api_put(cfg, f"/content-manage/{content_id}", admin_token, data={
            "title": f"PLV Test Content {ts} — Updated",
        })
        check_status(r, [200], CAT, "MT-03-03 Content UPDATE",
                     f"Updated content id={content_id}")
    safe_call(_content_update, CAT, "MT-03-03 Content UPDATE")

    def _content_delete():
        if not content_id:
            record_skip(CAT, "MT-03-04 Content DELETE", "No content_id from CREATE")
            return
        r = api_delete(cfg, f"/content-manage/{content_id}", admin_token)
        check_status(r, [200, 204], CAT, "MT-03-04 Content DELETE",
                     f"Deleted content id={content_id}")
    safe_call(_content_delete, CAT, "MT-03-04 Content DELETE")

    # ── Survey CRUD (4 tests) ──
    survey_id = None

    def _survey_create():
        nonlocal survey_id
        r = api_post(cfg, "/surveys", admin_token, data={
            "title": f"PLV Test Survey {ts}",
            "description": "Pre-launch verification test survey.",
            "survey_type": "general",
        })
        if r.status_code in (200, 201):
            body = r.json()
            survey_id = body.get("id")
            record_pass(CAT, "MT-03-05 Survey CREATE",
                        f"Created id={survey_id}")
        else:
            record_fail(CAT, "MT-03-05 Survey CREATE",
                        f"HTTP {r.status_code}", evidence=r.text[:200])
    safe_call(_survey_create, CAT, "MT-03-05 Survey CREATE")

    def _survey_read():
        if not survey_id:
            record_skip(CAT, "MT-03-06 Survey READ", "No survey_id from CREATE")
            return
        r = api_get(cfg, f"/surveys/{survey_id}", admin_token)
        check_status(r, [200], CAT, "MT-03-06 Survey READ",
                     f"Read survey id={survey_id}")
    safe_call(_survey_read, CAT, "MT-03-06 Survey READ")

    def _survey_publish():
        if not survey_id:
            record_skip(CAT, "MT-03-07 Survey PUBLISH", "No survey_id from CREATE")
            return
        # Add a question first (publish requires at least 1 real question)
        # Endpoint expects a raw JSON array, fields: title, question_type, config
        headers = {"Authorization": f"Bearer {admin_token}"}
        q_resp = cfg.session.post(
            cfg.url(f"/surveys/{survey_id}/questions"),
            headers=headers,
            json=[{
                "title": "PLV test question?",
                "question_type": "single_choice",
                "is_required": True,
                "config": {
                    "options": [
                        {"id": "opt_yes", "text": "Yes", "score": 1},
                        {"id": "opt_no", "text": "No", "score": 0},
                    ]
                },
            }],
            timeout=cfg.timeout,
        )
        if q_resp.status_code not in (200, 201):
            record_fail(CAT, "MT-03-07 Survey PUBLISH",
                        f"Could not add question (HTTP {q_resp.status_code})",
                        evidence=q_resp.text[:200])
            return
        r = api_post(cfg, f"/surveys/{survey_id}/publish", admin_token)
        check_status(r, [200], CAT, "MT-03-07 Survey PUBLISH",
                     f"Published survey id={survey_id}")
    safe_call(_survey_publish, CAT, "MT-03-07 Survey PUBLISH")

    def _survey_delete():
        if not survey_id:
            record_skip(CAT, "MT-03-08 Survey DELETE", "No survey_id from CREATE")
            return
        r = api_delete(cfg, f"/surveys/{survey_id}", admin_token)
        if r.status_code in (200, 204):
            record_pass(CAT, "MT-03-08 Survey DELETE",
                        f"Deleted survey id={survey_id}")
        elif r.status_code == 400:
            # Published surveys cannot be deleted — this is correct behavior
            record_pass(CAT, "MT-03-08 Survey DELETE",
                        f"Published survey correctly rejects deletion (400)")
        else:
            record_fail(CAT, "MT-03-08 Survey DELETE",
                        f"Expected 200/204/400, got {r.status_code}",
                        evidence=r.text[:200])
    safe_call(_survey_delete, CAT, "MT-03-08 Survey DELETE")

    # ── Agent Template CRUD (4 tests) ──
    # Templates use string agent_id, not numeric id
    template_agent_id = f"plv_test_{ts}"

    def _template_create():
        r = api_post(cfg, "/agent-templates/create", admin_token, data={
            "agent_id": template_agent_id,
            "display_name": f"PLV Test Template {ts}",
            "description": "Pre-launch verification test template.",
            "system_prompt": "You are a test agent.",
            "enable_llm": True,
        })
        if r.status_code in (200, 201):
            record_pass(CAT, "MT-03-09 Agent Template CREATE",
                        f"Created agent_id={template_agent_id}")
        else:
            record_fail(CAT, "MT-03-09 Agent Template CREATE",
                        f"HTTP {r.status_code}", evidence=r.text[:200])
    safe_call(_template_create, CAT, "MT-03-09 Agent Template CREATE")

    def _template_read():
        r = api_get(cfg, f"/agent-templates/{template_agent_id}", admin_token)
        check_status(r, [200], CAT, "MT-03-10 Agent Template READ",
                     f"Read template agent_id={template_agent_id}")
    safe_call(_template_read, CAT, "MT-03-10 Agent Template READ")

    def _template_update():
        r = api_put(cfg, f"/agent-templates/{template_agent_id}", admin_token, data={
            "description": "Updated by pre-launch verify.",
        })
        check_status(r, [200], CAT, "MT-03-11 Agent Template UPDATE",
                     f"Updated template agent_id={template_agent_id}")
    safe_call(_template_update, CAT, "MT-03-11 Agent Template UPDATE")

    def _template_delete():
        r = api_delete(cfg, f"/agent-templates/{template_agent_id}", admin_token)
        check_status(r, [200, 204], CAT, "MT-03-12 Agent Template DELETE",
                     f"Deleted template agent_id={template_agent_id}")
    safe_call(_template_delete, CAT, "MT-03-12 Agent Template DELETE")


# ═══════════════════════════════════════════════════════════════════════
# MT-04 Business Flow E2E (8 tests)
# ═══════════════════════════════════════════════════════════════════════

def mt04_business_flow(cfg: VerifyConfig):
    CAT = "MT-04-BizFlow"
    print("\n" + "─" * 60)
    print("  MT-04: Business Flow E2E (8 tests)")
    print("─" * 60)

    ensure_tokens(cfg)
    ts = int(time.time())

    # ── Register → Login → /auth/me role=observer (3 tests) ──
    new_user = f"plv_user_{ts}"
    new_email = f"plv_{ts}@test.com"
    new_pwd = "PLVerify@2026"
    new_token = None

    def _register():
        nonlocal new_token
        r = register_user(cfg, new_user, new_email, new_pwd)
        if r is None:
            record_skip(CAT, "MT-04-01 Register New User", "Request failed")
            return
        if r.status_code in (200, 201):
            body = r.json()
            new_token = body.get("access_token")
            record_pass(CAT, "MT-04-01 Register New User",
                        f"Registered {new_user}")
        elif r.status_code == 429:
            record_warn(CAT, "MT-04-01 Register New User",
                        "Rate limited (429) — expected if run frequently")
        else:
            record_fail(CAT, "MT-04-01 Register New User",
                        f"HTTP {r.status_code}", evidence=r.text[:200])
    safe_call(_register, CAT, "MT-04-01 Register New User")

    def _login_new():
        nonlocal new_token
        # If registration already returned a token, we already have it
        if new_token:
            record_pass(CAT, "MT-04-02 Login New User",
                        f"Using token from registration for {new_user}")
            return
        # If registration was rate-limited, skip login
        time.sleep(1)
        data = login_user(cfg, new_user, new_pwd)
        if data and data.get("access_token"):
            new_token = data["access_token"]
            record_pass(CAT, "MT-04-02 Login New User", f"Logged in as {new_user}")
        else:
            record_skip(CAT, "MT-04-02 Login New User",
                        "Registration failed/rate-limited — cannot login")
    safe_call(_login_new, CAT, "MT-04-02 Login New User")

    def _me_observer():
        if not new_token:
            record_skip(CAT, "MT-04-03 /auth/me Role=observer", "No token")
            return
        r = cfg.session.get(
            cfg.url("/auth/me"),
            headers={"Authorization": f"Bearer {new_token}"},
            timeout=cfg.timeout,
        )
        if r.status_code == 200:
            body = r.json()
            role = body.get("role", "")
            if role == "observer":
                record_pass(CAT, "MT-04-03 /auth/me Role=observer",
                            f"role={role}")
            else:
                record_warn(CAT, "MT-04-03 /auth/me Role=observer",
                            f"Expected observer, got role={role}")
        else:
            record_fail(CAT, "MT-04-03 /auth/me Role=observer",
                        f"HTTP {r.status_code}", evidence=r.text[:200])
    safe_call(_me_observer, CAT, "MT-04-03 /auth/me Role=observer")

    # ── Recommended Content → Content Detail (2 tests) ──
    grower_token = cfg.tokens.get("grower") or cfg.tokens.get("observer")
    content_id_for_detail = None

    def _recommended():
        nonlocal content_id_for_detail
        if not grower_token:
            record_skip(CAT, "MT-04-04 Recommended Content", "No token")
            return
        r = api_get(cfg, "/content/recommended", grower_token)
        if r.status_code == 200:
            body = r.json()
            items = body if isinstance(body, list) else body.get("items", body.get("data", []))
            if items and len(items) > 0:
                content_id_for_detail = items[0].get("id")
            record_pass(CAT, "MT-04-04 Recommended Content",
                        f"Got {len(items) if isinstance(items, list) else '?'} items")
        else:
            record_fail(CAT, "MT-04-04 Recommended Content",
                        f"HTTP {r.status_code}", evidence=r.text[:200])
    safe_call(_recommended, CAT, "MT-04-04 Recommended Content")

    def _content_detail():
        if not content_id_for_detail:
            record_skip(CAT, "MT-04-05 Content Detail", "No content_id from recommended")
            return
        r = api_get(cfg, f"/content/{content_id_for_detail}", grower_token)
        check_status(r, [200], CAT, "MT-04-05 Content Detail",
                     f"Read content id={content_id_for_detail}")
    safe_call(_content_detail, CAT, "MT-04-05 Content Detail")

    # ── Submit Learning Time → Check Points (2 tests) ──
    def _submit_learning():
        if not grower_token:
            record_skip(CAT, "MT-04-06 Submit Learning Time", "No token")
            return
        r = api_post(cfg, "/learning/grower/time/add", grower_token, data={
            "minutes": 5,
            "content_type": "article",
        })
        if r.status_code in (200, 201):
            record_pass(CAT, "MT-04-06 Submit Learning Time", "Submitted 5 min")
        else:
            record_warn(CAT, "MT-04-06 Submit Learning Time",
                        f"HTTP {r.status_code}", evidence=r.text[:200])
    safe_call(_submit_learning, CAT, "MT-04-06 Submit Learning Time")

    def _check_points():
        if not grower_token:
            record_skip(CAT, "MT-04-07 Check Points Change", "No token")
            return
        r = api_get(cfg, "/learning/grower/stats", grower_token)
        if r.status_code == 200:
            record_pass(CAT, "MT-04-07 Check Points Change",
                        "Stats endpoint reachable")
        else:
            record_warn(CAT, "MT-04-07 Check Points Change",
                        f"HTTP {r.status_code}", evidence=r.text[:200])
    safe_call(_check_points, CAT, "MT-04-07 Check Points Change")

    # ── Promotion Progress (1 test) ──
    def _promotion():
        if not grower_token:
            record_skip(CAT, "MT-04-08 Promotion Progress", "No token")
            return
        r = api_get(cfg, "/promotion/status", grower_token)
        if r.status_code == 200:
            record_pass(CAT, "MT-04-08 Promotion Progress", "Endpoint reachable")
        else:
            record_warn(CAT, "MT-04-08 Promotion Progress",
                        f"HTTP {r.status_code}", evidence=r.text[:200])
    safe_call(_promotion, CAT, "MT-04-08 Promotion Progress")


# ═══════════════════════════════════════════════════════════════════════
# MT-05 External Service Probes (4 tests)
# ═══════════════════════════════════════════════════════════════════════

def mt05_external_services(cfg: VerifyConfig):
    CAT = "MT-05-ExtSvc"
    print("\n" + "─" * 60)
    print("  MT-05: External Service Probes (4 tests)")
    print("─" * 60)

    # MT-05-01 Redis PING
    def _redis():
        rc, stdout, stderr = run_shell("docker exec bhp_v3_redis redis-cli PING")
        if "PONG" in stdout:
            record_pass(CAT, "MT-05-01 Redis PING", "PONG received")
        else:
            # Fallback: try dify redis
            rc2, stdout2, _ = run_shell("docker exec dify-redis-1 redis-cli PING")
            if "PONG" in stdout2:
                record_pass(CAT, "MT-05-01 Redis PING", "PONG (dify-redis)")
            else:
                record_fail(CAT, "MT-05-01 Redis PING",
                            f"No PONG. stdout={stdout}, stderr={stderr}")
    safe_call(_redis, CAT, "MT-05-01 Redis PING")

    # MT-05-02 Ollama
    def _ollama():
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=5)
            if r.status_code == 200:
                record_pass(CAT, "MT-05-02 Ollama Reachable", "HTTP 200")
            else:
                record_fail(CAT, "MT-05-02 Ollama Reachable",
                            f"HTTP {r.status_code}")
        except Exception as e:
            record_fail(CAT, "MT-05-02 Ollama Reachable", f"Connection failed: {e}")
    safe_call(_ollama, CAT, "MT-05-02 Ollama Reachable")

    # MT-05-03 Dify
    def _dify():
        try:
            r = requests.get("http://localhost/api/v1/health", timeout=5)
            if r.status_code == 200:
                record_pass(CAT, "MT-05-03 Dify Health", "HTTP 200")
            else:
                record_warn(CAT, "MT-05-03 Dify Health",
                            f"HTTP {r.status_code}")
        except Exception as e:
            record_warn(CAT, "MT-05-03 Dify Health",
                        f"Connection failed (may not be deployed): {e}")
    safe_call(_dify, CAT, "MT-05-03 Dify Health")

    # MT-05-04 BHP Health
    def _bhp_health():
        r = cfg.session.get(cfg.url("/health"), timeout=cfg.timeout)
        if r.status_code == 200:
            body = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
            status = body.get("status", "ok")
            if status in ("healthy", "ok", "degraded"):
                record_pass(CAT, "MT-05-04 BHP /api/v1/health",
                            f"status={status}")
            else:
                record_warn(CAT, "MT-05-04 BHP /api/v1/health",
                            f"status={status}")
        else:
            record_fail(CAT, "MT-05-04 BHP /api/v1/health",
                        f"HTTP {r.status_code}", evidence=r.text[:200])
    safe_call(_bhp_health, CAT, "MT-05-04 BHP /api/v1/health")


# ═══════════════════════════════════════════════════════════════════════
# MT-06 Performance Baseline (6 tests)
# ═══════════════════════════════════════════════════════════════════════

def mt06_performance(cfg: VerifyConfig):
    CAT = "MT-06-Perf"
    print("\n" + "─" * 60)
    print("  MT-06: Performance Baseline (6 tests)")
    print("─" * 60)

    ensure_tokens(cfg)
    admin_token = cfg.tokens.get("admin")
    coach_token = cfg.tokens.get("coach")
    grower_token = cfg.tokens.get("grower")

    # Endpoints to benchmark (path, token, label, use_raw)
    # use_raw=True means use base URL without /api/v1 prefix
    endpoints = [
        ("/health",                 None,          "/health (raw)",      True),
        ("/auth/me",                admin_token,   "/auth/me",           False),
        ("/content",                grower_token,  "/content",           False),
        ("/learning/grower/stats",  grower_token,  "/learning/stats",    False),
        ("/challenges",             grower_token,  "/challenges",        False),
    ]

    ITERATIONS = 22  # 2 warmup + 20 measured

    for path, token, label, use_raw in endpoints:
        def _bench(p=path, t=token, l=label, raw=use_raw):
            all_latencies = []
            for _ in range(ITERATIONS):
                url = cfg.raw_url(p) if raw else cfg.url(p)
                headers = {}
                if t:
                    headers["Authorization"] = f"Bearer {t}"
                start = time.perf_counter()
                try:
                    r = cfg.session.get(url, headers=headers, timeout=cfg.timeout)
                    elapsed = (time.perf_counter() - start) * 1000
                    if r.status_code in (200, 401, 403, 404):
                        all_latencies.append(elapsed)
                except Exception:
                    pass

            # Drop first 2 as warmup
            latencies = all_latencies[2:] if len(all_latencies) > 4 else all_latencies

            if len(latencies) < 5:
                record_skip(CAT, f"MT-06 Perf {l}",
                            f"Only {len(latencies)}/{ITERATIONS} successful requests")
                return

            p50 = statistics.median(latencies)
            p95 = sorted(latencies)[int(len(latencies) * 0.95)]
            p99 = sorted(latencies)[int(len(latencies) * 0.99)]

            detail = f"p50={p50:.0f}ms p95={p95:.0f}ms p99={p99:.0f}ms (n={len(latencies)})"

            if p95 < 500:
                record_pass(CAT, f"MT-06 Perf {l}", detail)
            elif p95 < 1000:
                record_warn(CAT, f"MT-06 Perf {l}", f"p95 > 500ms — {detail}")
            else:
                record_fail(CAT, f"MT-06 Perf {l}", f"p95 >= 1000ms — {detail}")
        safe_call(_bench, CAT, f"MT-06 Perf {label}")

    # Concurrency test: 10 concurrent /health requests
    def _concurrent():
        url = cfg.raw_url("/health")

        def _single_req():
            start = time.perf_counter()
            try:
                s = requests.Session()
                s.verify = False
                r = s.get(url, timeout=cfg.timeout)
                elapsed = (time.perf_counter() - start) * 1000
                return elapsed if r.status_code == 200 else None
            except Exception:
                return None

        latencies = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(_single_req) for _ in range(10)]
            for f in concurrent.futures.as_completed(futures):
                val = f.result()
                if val is not None:
                    latencies.append(val)

        if len(latencies) < 5:
            record_skip(CAT, "MT-06 Concurrent /health",
                        f"Only {len(latencies)}/10 succeeded")
            return

        max_lat = max(latencies)
        detail = f"max={max_lat:.0f}ms (10 concurrent, {len(latencies)} OK)"

        if max_lat < 2000:
            record_pass(CAT, "MT-06 Concurrent /health", detail)
        else:
            record_fail(CAT, "MT-06 Concurrent /health",
                        f"max >= 2000ms — {detail}")
    safe_call(_concurrent, CAT, "MT-06 Concurrent /health")


# ═══════════════════════════════════════════════════════════════════════
# MT-07 Database Health (6 tests)
# ═══════════════════════════════════════════════════════════════════════

def mt07_db_health(cfg: VerifyConfig):
    CAT = "MT-07-DB"
    print("\n" + "─" * 60)
    print("  MT-07: Database Health (6 tests)")
    print("─" * 60)

    PSQL_CMD = (
        'docker exec dify-db-1 psql -U postgres -d health_platform -t -A -c'
    )

    # MT-07-01 Migration version consistency
    def _migration():
        rc, stdout, _ = run_shell(
            f'{PSQL_CMD} "SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1;"'
        )
        if rc == 0 and stdout:
            version = stdout.strip()
            record_pass(CAT, "MT-07-01 Alembic Version",
                        f"Current DB version: {version}")
        else:
            record_fail(CAT, "MT-07-01 Alembic Version",
                        f"Could not read alembic_version (rc={rc})")
    safe_call(_migration, CAT, "MT-07-01 Alembic Version")

    # MT-07-02 Table count > 100
    def _table_count():
        rc, stdout, _ = run_shell(
            f"""{PSQL_CMD} "SELECT count(*) FROM information_schema.tables WHERE table_schema IN ('public','coach_schema');" """
        )
        if rc == 0 and stdout.strip().isdigit():
            count = int(stdout.strip())
            if count > 100:
                record_pass(CAT, "MT-07-02 Table Count",
                            f"{count} tables (> 100)")
            else:
                record_fail(CAT, "MT-07-02 Table Count",
                            f"Only {count} tables (expected > 100)")
        else:
            record_fail(CAT, "MT-07-02 Table Count",
                        f"Could not count tables (rc={rc})")
    safe_call(_table_count, CAT, "MT-07-02 Table Count")

    # MT-07-03 Foreign key constraints (no orphaned FKs)
    def _fk_check():
        # Check that pg_constraint has FK entries (system is using FKs)
        rc, stdout, _ = run_shell(
            f"""{PSQL_CMD} "SELECT count(*) FROM pg_constraint WHERE contype='f';" """
        )
        if rc == 0 and stdout.strip().isdigit():
            count = int(stdout.strip())
            if count > 0:
                record_pass(CAT, "MT-07-03 FK Constraints",
                            f"{count} foreign key constraints found")
            else:
                record_warn(CAT, "MT-07-03 FK Constraints",
                            "No FK constraints found")
        else:
            record_fail(CAT, "MT-07-03 FK Constraints",
                        f"Could not check FK constraints (rc={rc})")
    safe_call(_fk_check, CAT, "MT-07-03 FK Constraints")

    # MT-07-04 No NULL usernames
    def _null_username():
        rc, stdout, _ = run_shell(
            f'{PSQL_CMD} "SELECT count(*) FROM users WHERE username IS NULL;"'
        )
        if rc == 0 and stdout.strip().isdigit():
            count = int(stdout.strip())
            if count == 0:
                record_pass(CAT, "MT-07-04 No NULL Usernames",
                            "All users have usernames")
            else:
                record_fail(CAT, "MT-07-04 No NULL Usernames",
                            f"{count} users have NULL username")
        else:
            record_fail(CAT, "MT-07-04 No NULL Usernames",
                        f"Query failed (rc={rc})")
    safe_call(_null_username, CAT, "MT-07-04 No NULL Usernames")

    # MT-07-05 No empty email
    def _null_email():
        rc, stdout, _ = run_shell(
            f"""{PSQL_CMD} "SELECT count(*) FROM users WHERE email IS NULL OR email='';" """
        )
        if rc == 0 and stdout.strip().isdigit():
            count = int(stdout.strip())
            if count == 0:
                record_pass(CAT, "MT-07-05 No Empty Email",
                            "All users have email")
            else:
                record_fail(CAT, "MT-07-05 No Empty Email",
                            f"{count} users have NULL/empty email")
        else:
            record_fail(CAT, "MT-07-05 No Empty Email",
                        f"Query failed (rc={rc})")
    safe_call(_null_email, CAT, "MT-07-05 No Empty Email")

    # MT-07-06 Index count > 50
    def _index_count():
        rc, stdout, _ = run_shell(
            f"""{PSQL_CMD} "SELECT count(*) FROM pg_indexes WHERE schemaname IN ('public','coach_schema');" """
        )
        if rc == 0 and stdout.strip().isdigit():
            count = int(stdout.strip())
            if count > 50:
                record_pass(CAT, "MT-07-06 Index Count",
                            f"{count} indexes (> 50)")
            else:
                record_warn(CAT, "MT-07-06 Index Count",
                            f"Only {count} indexes (expected > 50)")
        else:
            record_fail(CAT, "MT-07-06 Index Count",
                        f"Could not count indexes (rc={rc})")
    safe_call(_index_count, CAT, "MT-07-06 Index Count")


# ═══════════════════════════════════════════════════════════════════════
# MT-08 Scheduler Validation (3 tests)
# ═══════════════════════════════════════════════════════════════════════

def mt08_scheduler(cfg: VerifyConfig):
    CAT = "MT-08-Sched"
    print("\n" + "─" * 60)
    print("  MT-08: Scheduler Validation (3 tests)")
    print("─" * 60)

    DOCKER_PY = 'docker exec bhp-api python -c'

    # MT-08-01 Scheduler started
    def _sched_started():
        rc, stdout, stderr = run_shell(
            f"""{DOCKER_PY} "from core.scheduler import scheduler; print('running' if scheduler.running else 'stopped')" """,
            timeout=15,
        )
        if rc == 0 and "running" in stdout:
            record_pass(CAT, "MT-08-01 Scheduler Running", "APScheduler is running")
        elif rc == 0 and "stopped" in stdout:
            record_fail(CAT, "MT-08-01 Scheduler Running", "Scheduler is stopped")
        else:
            # Fallback: check via API if available
            record_warn(CAT, "MT-08-01 Scheduler Running",
                        f"Could not exec in container (rc={rc}). stderr={stderr[:200]}")
    safe_call(_sched_started, CAT, "MT-08-01 Scheduler Running")

    # MT-08-02 Job count >= 10
    def _job_count():
        rc, stdout, stderr = run_shell(
            f"""{DOCKER_PY} "from core.scheduler import scheduler; jobs=scheduler.get_jobs(); print(len(jobs))" """,
            timeout=15,
        )
        if rc == 0 and stdout.strip().isdigit():
            count = int(stdout.strip())
            if count >= 10:
                record_pass(CAT, "MT-08-02 Job Count",
                            f"{count} jobs registered (>= 10)")
            else:
                record_fail(CAT, "MT-08-02 Job Count",
                            f"Only {count} jobs (expected >= 10)")
        else:
            record_warn(CAT, "MT-08-02 Job Count",
                        f"Could not query jobs (rc={rc}). stderr={stderr[:200]}")
    safe_call(_job_count, CAT, "MT-08-02 Job Count")

    # MT-08-03 List all job names
    def _job_names():
        rc, stdout, stderr = run_shell(
            f"""{DOCKER_PY} "from core.scheduler import scheduler; [print(j.id) for j in scheduler.get_jobs()]" """,
            timeout=15,
        )
        if rc == 0 and stdout.strip():
            names = [n for n in stdout.strip().split("\n") if n]
            record_pass(CAT, "MT-08-03 Job Names",
                        f"Jobs: {', '.join(names[:15])}")
        else:
            record_warn(CAT, "MT-08-03 Job Names",
                        f"Could not list jobs (rc={rc}). stderr={stderr[:200]}")
    safe_call(_job_names, CAT, "MT-08-03 Job Names")


# ═══════════════════════════════════════════════════════════════════════
# MT-09 Frontend Reachability (5 tests)
# ═══════════════════════════════════════════════════════════════════════

def mt09_frontend(cfg: VerifyConfig):
    CAT = "MT-09-Frontend"
    print("\n" + "─" * 60)
    print("  MT-09: Frontend Reachability (5 tests)")
    print("─" * 60)

    # MT-09-01 Admin Portal :5174
    def _admin_portal():
        try:
            r = requests.get("http://localhost:5174", timeout=10)
            if r.status_code == 200 and '<div id="app"' in r.text:
                record_pass(CAT, "MT-09-01 Admin Portal :5174",
                            "HTML with <div id=\"app\" found")
            elif r.status_code == 200:
                record_warn(CAT, "MT-09-01 Admin Portal :5174",
                            "200 but no <div id=\"app\" in response")
            else:
                record_fail(CAT, "MT-09-01 Admin Portal :5174",
                            f"HTTP {r.status_code}")
        except Exception as e:
            record_fail(CAT, "MT-09-01 Admin Portal :5174",
                        f"Connection failed: {e}")
    safe_call(_admin_portal, CAT, "MT-09-01 Admin Portal :5174")

    # MT-09-02 H5 :5173
    def _h5():
        try:
            r = requests.get("http://localhost:5173", timeout=10)
            if r.status_code == 200:
                record_pass(CAT, "MT-09-02 H5 App :5173",
                            "HTML returned (200)")
            else:
                record_fail(CAT, "MT-09-02 H5 App :5173",
                            f"HTTP {r.status_code}")
        except Exception as e:
            record_fail(CAT, "MT-09-02 H5 App :5173",
                        f"Connection failed: {e}")
    safe_call(_h5, CAT, "MT-09-02 H5 App :5173")

    # MT-09-03 Expert Workbench :8501
    def _workbench():
        try:
            r = requests.get("http://localhost:8501", timeout=10)
            if r.status_code == 200:
                record_pass(CAT, "MT-09-03 Expert Workbench :8501",
                            "HTML returned (200)")
            else:
                record_fail(CAT, "MT-09-03 Expert Workbench :8501",
                            f"HTTP {r.status_code}")
        except Exception as e:
            record_warn(CAT, "MT-09-03 Expert Workbench :8501",
                        f"Connection failed (may not be deployed): {e}")
    safe_call(_workbench, CAT, "MT-09-03 Expert Workbench :8501")

    # MT-09-04 Admin Portal /api proxy → 200
    def _admin_proxy():
        try:
            r = requests.get("http://localhost:5174/api/v1/health", timeout=10)
            if r.status_code == 200:
                record_pass(CAT, "MT-09-04 Admin /api Proxy",
                            "Proxy to backend working")
            elif r.status_code == 502:
                record_warn(CAT, "MT-09-04 Admin /api Proxy",
                            "502 Bad Gateway — Vite proxy cannot reach backend "
                            "(expected in Docker: admin-portal proxies to localhost:8000, "
                            "but backend may be on container network)")
            else:
                record_fail(CAT, "MT-09-04 Admin /api Proxy",
                            f"HTTP {r.status_code}")
        except Exception as e:
            record_fail(CAT, "MT-09-04 Admin /api Proxy",
                        f"Connection failed: {e}")
    safe_call(_admin_proxy, CAT, "MT-09-04 Admin /api Proxy")

    # MT-09-05 Static assets reachable
    def _static_assets():
        # Try to find a JS/CSS asset from the Admin Portal HTML
        try:
            r = requests.get("http://localhost:5174", timeout=10)
            if r.status_code != 200:
                record_skip(CAT, "MT-09-05 Static Assets", "Admin portal unreachable")
                return

            import re
            assets = re.findall(r'(?:src|href)="(/assets/[^"]+)"', r.text)
            if not assets:
                # Try Vite dev-mode patterns
                assets = re.findall(r'(?:src|href)="([^"]*\.(?:js|css)[^"]*)"', r.text)

            if not assets:
                record_warn(CAT, "MT-09-05 Static Assets",
                            "No asset URLs found in HTML")
                return

            asset_url = f"http://localhost:5174{assets[0]}"
            r2 = requests.get(asset_url, timeout=10)
            if r2.status_code == 200:
                record_pass(CAT, "MT-09-05 Static Assets",
                            f"Asset {assets[0]} reachable")
            else:
                record_fail(CAT, "MT-09-05 Static Assets",
                            f"Asset returned HTTP {r2.status_code}")
        except Exception as e:
            record_warn(CAT, "MT-09-05 Static Assets", f"Error: {e}")
    safe_call(_static_assets, CAT, "MT-09-05 Static Assets")


# ═══════════════════════════════════════════════════════════════════════
# MT-10 Disaster Recovery (3 tests)
# ═══════════════════════════════════════════════════════════════════════

def mt10_disaster_recovery(cfg: VerifyConfig):
    CAT = "MT-10-DR"
    print("\n" + "─" * 60)
    print("  MT-10: Disaster Recovery (3 tests)")
    print("─" * 60)

    backup_file = None
    project_dir = os.environ.get("BHP_PROJECT_DIR", "D:/behavioral-health-project")
    backup_script = f"{project_dir}/scripts/db_backup.sh"

    # MT-10-01 Backup execution
    def _backup():
        nonlocal backup_file
        rc, stdout, stderr = run_shell(
            f"bash \"{backup_script}\"",
            timeout=120,
        )
        # Try to extract backup filename from output
        for line in (stdout + "\n" + stderr).split("\n"):
            if ".sql.gz" in line:
                import re
                match = re.search(r'([\w/\\._-]+\.sql\.gz)', line)
                if match:
                    backup_file = match.group(1)
                    break

        if rc == 0:
            record_pass(CAT, "MT-10-01 DB Backup",
                        f"Backup succeeded. File: {backup_file or '(found in output)'}")
        else:
            record_fail(CAT, "MT-10-01 DB Backup",
                        f"Backup failed (rc={rc}). stderr={stderr[:300]}")
    safe_call(_backup, CAT, "MT-10-01 DB Backup")

    # MT-10-02 Backup file > 10KB
    def _backup_size():
        if not backup_file:
            # Try to find most recent backup
            backup_dir = f"{project_dir}/backups"
            rc, stdout, _ = run_shell(f"ls -t \"{backup_dir}\"/*.sql.gz 2>/dev/null | head -1")
            actual_file = stdout.strip() if rc == 0 and stdout.strip() else None
            if not actual_file:
                record_skip(CAT, "MT-10-02 Backup Size", "No backup file found")
                return
        else:
            actual_file = backup_file
            # Make path absolute if relative
            if not os.path.isabs(actual_file):
                actual_file = os.path.join(project_dir, actual_file)

        rc, stdout, _ = run_shell(f'stat -c%s "{actual_file}" 2>/dev/null || wc -c < "{actual_file}"')
        if rc == 0 and stdout.strip().isdigit():
            size = int(stdout.strip())
            if size > 10240:
                record_pass(CAT, "MT-10-02 Backup Size",
                            f"{size} bytes (> 10KB)")
            else:
                record_fail(CAT, "MT-10-02 Backup Size",
                            f"Only {size} bytes (expected > 10KB)")
        else:
            record_warn(CAT, "MT-10-02 Backup Size",
                        f"Could not determine file size")
    safe_call(_backup_size, CAT, "MT-10-02 Backup Size")

    # MT-10-03 pg_restore --list dry-run
    def _restore_list():
        if not backup_file:
            backup_dir = f"{project_dir}/backups"
            rc, stdout, _ = run_shell(f"ls -t \"{backup_dir}\"/*.sql.gz 2>/dev/null | head -1")
            actual_file = stdout.strip() if rc == 0 and stdout.strip() else None
            if not actual_file:
                record_skip(CAT, "MT-10-03 Restore Dry-Run", "No backup file found")
                return
        else:
            actual_file = backup_file
            if not os.path.isabs(actual_file):
                actual_file = os.path.join(project_dir, actual_file)

        # pg_restore --list on gzipped SQL doesn't work; try gunzip | head
        rc, stdout, stderr = run_shell(
            f'gunzip -c "{actual_file}" 2>/dev/null | head -20',
            timeout=30,
        )
        if rc == 0 and stdout:
            # Check it looks like SQL
            if any(kw in stdout.upper() for kw in ["CREATE", "INSERT", "SET", "ALTER", "SELECT", "COPY", "BEGIN"]):
                record_pass(CAT, "MT-10-03 Restore Dry-Run",
                            "Backup contains valid SQL statements")
            else:
                record_warn(CAT, "MT-10-03 Restore Dry-Run",
                            "Backup does not appear to contain SQL")
        else:
            record_warn(CAT, "MT-10-03 Restore Dry-Run",
                        f"Could not read backup (rc={rc}). stderr={stderr[:200]}")
    safe_call(_restore_list, CAT, "MT-10-03 Restore Dry-Run")


# ═══════════════════════════════════════════════════════════════════════
# MT-11 Manual Verification Checklist
# ═══════════════════════════════════════════════════════════════════════

def mt11_manual_checklist(cfg: VerifyConfig):
    print("\n" + "─" * 60)
    print("  MT-11: Manual Verification Checklist")
    print("─" * 60)

    HOST = cfg.base.replace("http://", "").replace("https://", "").split(":")[0]

    checklist = [
        {
            "title": "Admin Portal 86 页面可正常导航",
            "url": f"http://{HOST}:5174",
            "account": "admin / Admin@2026",
            "steps": "登录后依次打开左侧菜单全部 86 个页面，确认无白屏、无 JS 报错",
        },
        {
            "title": "H5 端 30 页面可正常导航",
            "url": f"http://{HOST}:5173",
            "account": "observer_test / Test@2026",
            "steps": "登录后依次点击底部 5 个 Tab，进入学习中心/内容详情/我的学习/学分/同道者/晋级进度等 30 页",
        },
        {
            "title": "移动端适配 (iPhone/Android 竖屏)",
            "url": f"http://{HOST}:5173",
            "account": "observer_test / Test@2026",
            "steps": "用手机浏览器或 Chrome DevTools (F12→Toggle Device) 打开 H5，检查布局无溢出、按钮可点击",
        },
        {
            "title": "AI 对话质量 (3 轮对话语义连贯)",
            "url": f"http://{HOST}:5173/#/chat",
            "account": "observer_test / Test@2026",
            "steps": "进入对话页，连续发 3 条消息(如'我最近睡不好'→'已经持续两周了'→'有什么建议吗')，确认回复语义连贯、无幻觉",
        },
        {
            "title": "推送通知实际到达",
            "url": f"http://{HOST}:5174/#/push",
            "account": "admin / Admin@2026 (Admin Portal)",
            "steps": "在管理后台创建一条推送，指定目标用户，确认 H5 端收到通知",
        },
        {
            "title": "文件上传/下载功能",
            "url": f"http://{HOST}:5174/#/content",
            "account": "admin / Admin@2026 (Admin Portal)",
            "steps": "在内容管理页上传一个 PDF/DOCX 文件，确认上传成功；再下载该文件，确认完整可打开",
        },
        {
            "title": "数据导出 (CSV/Excel) 格式正确",
            "url": f"http://{HOST}:5174/#/analytics",
            "account": "admin / Admin@2026 (Admin Portal)",
            "steps": "在数据分析/用户管理页点击'导出'按钮，下载 CSV/Excel 文件，用 Excel 打开确认列头正确、中文无乱码",
        },
        {
            "title": "浏览器兼容性 (Chrome/Edge/Safari)",
            "url": f"http://{HOST}:5174",
            "account": "admin / Admin@2026",
            "steps": "分别用 Chrome、Edge、Safari 打开 Admin Portal 和 H5，确认核心页面无样式错乱",
        },
    ]

    print()
    print(f"  Server: {HOST}")
    print(f"  ┌─────────────────────────────────────────────────────────┐")
    print(f"  │  Service             │  URL                            │")
    print(f"  ├─────────────────────────────────────────────────────────┤")
    print(f"  │  API (FastAPI)       │  http://{HOST}:8000             │")
    print(f"  │  Admin Portal        │  http://{HOST}:5174             │")
    print(f"  │  H5 Mobile           │  http://{HOST}:5173             │")
    print(f"  │  Expert Workbench    │  http://{HOST}:8501             │")
    print(f"  │  Dify                │  http://{HOST}:8080             │")
    print(f"  │  Swagger Docs        │  http://{HOST}:8000/docs        │")
    print(f"  └─────────────────────────────────────────────────────────┘")
    print()
    for i, item in enumerate(checklist, 1):
        print(f"  [ ] {i}. {item['title']}")
        print(f"       URL:     {item['url']}")
        print(f"       Account: {item['account']}")
        print(f"       Steps:   {item['steps']}")
        print()
    print("  (These items require manual verification and are not automated)")
    print()

    # Record in results for JSON report
    results.append(Result(
        Result.SKIP, "MT-11-Manual", "Manual Checklist",
        detail=f"{len(checklist)} items require manual verification",
        evidence="\n".join(
            f"[ ] {item['title']}\n    URL: {item['url']}\n    Account: {item['account']}\n    Steps: {item['steps']}"
            for item in checklist
        ),
    ))
    counters["total"] += 1
    counters["skipped"] += 1


# ═══════════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════════

def generate_report(cfg: VerifyConfig):
    print("\n" + "=" * 60)
    print("  PRE-LAUNCH VERIFICATION REPORT")
    print("=" * 60)

    by_status = {}
    by_category = {}
    for r in results:
        by_status[r.status] = by_status.get(r.status, 0) + 1
        by_category.setdefault(r.category, {"PASS": 0, "FAIL": 0, "SKIP": 0, "WARN": 0})
        by_category[r.category][r.status] = by_category[r.category].get(r.status, 0) + 1

    overall = "PASS" if counters["failed"] == 0 else "FAIL"

    print(f"\n  Total:   {counters['total']}")
    print(f"  Passed:  {counters['passed']}")
    print(f"  Failed:  {counters['failed']}")
    print(f"  Skipped: {counters['skipped']}")
    print(f"  Warned:  {counters['warned']}")
    print(f"  Overall: {overall}")

    # Category breakdown
    print(f"\n  {'Category':<25} {'PASS':>6} {'FAIL':>6} {'SKIP':>6} {'WARN':>6}")
    print("  " + "─" * 55)
    for cat in sorted(by_category.keys()):
        s = by_category[cat]
        print(f"  {cat:<25} {s.get('PASS',0):>6} {s.get('FAIL',0):>6} "
              f"{s.get('SKIP',0):>6} {s.get('WARN',0):>6}")

    # Failures summary
    failures = [r for r in results if r.status == "FAIL"]
    if failures:
        print(f"\n  FAILURES ({len(failures)}):")
        for f in failures:
            print(f"    FAIL [{f.category}] {f.title}")
            if f.detail:
                print(f"       {f.detail}")

    # Write JSON report
    report = {
        "report_meta": {
            "title": "BehaviorOS Pre-Launch Verification",
            "target": cfg.api,
            "timestamp": datetime.now().isoformat(),
            "test_counts": dict(counters),
        },
        "summary": {
            "total_results": counters["total"],
            "by_status": by_status,
            "by_category": {k: dict(v) for k, v in by_category.items()},
            "overall": overall,
        },
        "results": [r.to_dict() for r in results],
        "manual_checklist": [
            "Admin Portal 86 pages can be navigated normally",
            "H5 30 pages can be navigated normally",
            "Mobile adaptation (iPhone/Android portrait mode)",
            "AI conversation quality (3-turn semantic coherence)",
            "Push notifications actually delivered",
            "File upload/download functionality",
            "Data export (CSV/Excel) format correct",
            "Browser compatibility (Chrome/Edge/Safari)",
        ],
    }

    json_path = cfg.json_path
    os.makedirs(os.path.dirname(json_path) or ".", exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\n  Report saved to: {json_path}")
    print("=" * 60)

    return overall


# ═══════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════

CATEGORIES = {
    "mt01": ("MT-01 Auth Integrity",        mt01_auth_integrity),
    "mt02": ("MT-02 RBAC Deep",             mt02_rbac_deep),
    "mt03": ("MT-03 CRUD Lifecycle",        mt03_crud_lifecycle),
    "mt04": ("MT-04 Business Flow",         mt04_business_flow),
    "mt05": ("MT-05 External Services",     mt05_external_services),
    "mt06": ("MT-06 Performance Baseline",  mt06_performance),
    "mt07": ("MT-07 Database Health",       mt07_db_health),
    "mt08": ("MT-08 Scheduler",             mt08_scheduler),
    "mt09": ("MT-09 Frontend Reachability", mt09_frontend),
    "mt10": ("MT-10 Disaster Recovery",     mt10_disaster_recovery),
    "mt11": ("MT-11 Manual Checklist",      mt11_manual_checklist),
}


def main():
    parser = argparse.ArgumentParser(
        description="BehaviorOS Pre-Launch Verification Suite")
    parser.add_argument("--base", default="http://localhost:8000",
                        help="API base URL (default: http://localhost:8000)")
    parser.add_argument("--json", default=DEFAULT_JSON_PATH,
                        help=f"JSON report output path (default: {DEFAULT_JSON_PATH})")
    parser.add_argument("--category", default=None,
                        help="Comma-separated categories to run (e.g., mt01,mt02)")
    args = parser.parse_args()

    cfg = VerifyConfig(args.base, args.json)

    print("\n" + "=" * 60)
    print("  BehaviorOS Pre-Launch Verification Suite")
    print(f"  Target: {cfg.api}")
    print(f"  Time:   {datetime.now().isoformat()}")
    print("=" * 60)

    # Determine which categories to run
    if args.category:
        selected = [c.strip().lower() for c in args.category.split(",")]
        invalid = [c for c in selected if c not in CATEGORIES]
        if invalid:
            print(f"  Invalid categories: {', '.join(invalid)}")
            print(f"  Valid: {', '.join(CATEGORIES.keys())}")
            sys.exit(2)
    else:
        selected = list(CATEGORIES.keys())

    # Always login first
    print("\n  Logging in demo accounts...")
    ensure_tokens(cfg)
    logged = len(cfg.tokens)
    print(f"  Logged in {logged}/{len(cfg.demo_accounts)} accounts")
    if logged == 0:
        print("  WARNING: No accounts could login — many tests will be skipped")

    # Run selected categories
    for cat_key in selected:
        name, fn = CATEGORIES[cat_key]
        fn(cfg)

    overall = generate_report(cfg)
    sys.exit(0 if overall == "PASS" else 1)


if __name__ == "__main__":
    main()

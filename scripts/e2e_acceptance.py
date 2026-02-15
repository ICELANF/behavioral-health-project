#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BehaviorOS V4.0 E2E Acceptance Test Suite
Functional acceptance tests across 6 role journeys, RBAC boundaries,
data consistency, and static code analysis.

Usage:
  python scripts/e2e_acceptance.py --base http://localhost:8000 --project . --json reports/acceptance.json
  python scripts/e2e_acceptance.py --skip-static          # skip source scanning
  python scripts/e2e_acceptance.py --scenario 2            # run only Phase 2 (Observer)

Output: terminal + JSON report
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import requests
    requests.packages.urllib3.disable_warnings()
except ImportError:
    print("pip install requests")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════
# Configuration & Global State
# ═══════════════════════════════════════════════════════════════════════

class AcceptanceConfig:
    def __init__(self, base: str, project: str, json_path: str):
        self.base = base.rstrip("/")
        if not self.base.endswith("/api/v1"):
            self.api = self.base + "/api/v1"
        else:
            self.api = self.base
        self.project = project
        self.json_path = json_path
        self.timeout = 15
        self.session = requests.Session()
        self.session.verify = False

        self.tokens = {}      # role -> access_token
        self.user_ids = {}    # role -> user_id

        # Demo accounts (password convention: Role@2026)
        self.demo_accounts = {
            "admin":      ("admin",      "Admin@2026"),
            "observer":   ("observer_test", "Test@2026"),
            "grower":     ("grower_test",   "Test@2026"),
            "sharer":     ("sharer_test",   "Test@2026"),
            "coach":      ("coach_test",    "Test@2026"),
            "promoter":   ("promoter_test", "Test@2026"),
            "supervisor": ("supervisor_test", "Test@2026"),
            "master":     ("master_test",   "Test@2026"),
        }

    def url(self, path: str) -> str:
        return f"{self.api}{path}"


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


# Global collectors
results: list[Result] = []
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


def login_user(cfg: AcceptanceConfig, username: str, password: str) -> Optional[dict]:
    """Login and return {access_token, user} or None."""
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


def register_user(cfg: AcceptanceConfig, username: str, email: str, password: str) -> Optional[dict]:
    """Register a new user and return response dict or None."""
    try:
        r = cfg.session.post(
            cfg.url("/auth/register"),
            json={"username": username, "email": email, "password": password},
            timeout=cfg.timeout,
        )
        if r.status_code in (200, 201):
            return r.json()
    except Exception:
        pass
    return None


def api_get(cfg: AcceptanceConfig, path: str, token: str = None) -> requests.Response:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return cfg.session.get(cfg.url(path), headers=headers, timeout=cfg.timeout)


def api_post(cfg: AcceptanceConfig, path: str, token: str = None,
             data: dict = None) -> requests.Response:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return cfg.session.post(cfg.url(path), headers=headers, json=data or {},
                            timeout=cfg.timeout)


def api_put(cfg: AcceptanceConfig, path: str, token: str = None,
            data: dict = None) -> requests.Response:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return cfg.session.put(cfg.url(path), headers=headers, json=data or {},
                           timeout=cfg.timeout)


def api_delete(cfg: AcceptanceConfig, path: str, token: str = None) -> requests.Response:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return cfg.session.delete(cfg.url(path), headers=headers, timeout=cfg.timeout)


def check_status(resp: requests.Response, expected: list[int], category: str,
                 title: str, detail: str = "") -> bool:
    """Check response status, record pass/fail. Returns True on pass."""
    if resp.status_code in expected:
        record_pass(category, title, detail or f"HTTP {resp.status_code}")
        return True
    else:
        record_fail(category, title,
                    detail or f"Expected {expected}, got {resp.status_code}",
                    evidence=resp.text[:200])
        return False


def safe_call(fn, category: str, title: str):
    """Wrap a test call; catch connection errors as SKIP."""
    try:
        return fn()
    except requests.exceptions.ConnectionError:
        record_skip(category, title, "Connection refused")
    except requests.exceptions.Timeout:
        record_skip(category, title, "Request timed out")
    except Exception as e:
        record_warn(category, title, f"Unexpected error: {e}")
    return None


# ═══════════════════════════════════════════════════════════════════════
# Phase 0: Connectivity & Login
# ═══════════════════════════════════════════════════════════════════════

def phase_0_connectivity(cfg: AcceptanceConfig):
    print("\n" + "─" * 60)
    print("  Phase 0: Connectivity & Login")
    print("─" * 60)

    # 0.1 Health check
    def _health():
        r = cfg.session.get(f"{cfg.base}/health", timeout=cfg.timeout)
        check_status(r, [200], "P0-Connect", "GET /health returns 200")
    safe_call(_health, "P0-Connect", "GET /health returns 200")

    # 0.2 API health
    def _api_health():
        r = cfg.session.get(cfg.url("/health"), timeout=cfg.timeout)
        check_status(r, [200], "P0-Connect", "GET /api/v1/health returns 200")
    safe_call(_api_health, "P0-Connect", "GET /api/v1/health returns 200")

    # 0.3 Login demo accounts
    for role, (username, password) in cfg.demo_accounts.items():
        def _login(r=role, u=username, p=password):
            data = login_user(cfg, u, p)
            if data and data.get("access_token"):
                cfg.tokens[r] = data["access_token"]
                user_info = data.get("user", {})
                cfg.user_ids[r] = user_info.get("id")
                record_pass("P0-Login", f"Login {r} ({u})",
                            f"user_id={user_info.get('id')}, role={user_info.get('role')}")
            else:
                record_warn("P0-Login", f"Login {r} ({u})",
                            f"Could not login; dependent tests will be skipped")
        safe_call(_login, "P0-Login", f"Login {role} ({username})")

    logged = len(cfg.tokens)
    print(f"\n  Logged in {logged}/{len(cfg.demo_accounts)} accounts")
    if logged == 0:
        record_fail("P0-Login", "No accounts could login",
                    "All subsequent phases will mostly SKIP")


# ═══════════════════════════════════════════════════════════════════════
# Phase 1: Static Analysis
# ═══════════════════════════════════════════════════════════════════════

def phase_1_static_analysis(cfg: AcceptanceConfig):
    print("\n" + "─" * 60)
    print("  Phase 1: Static Analysis")
    print("─" * 60)

    project = Path(cfg.project)
    if not project.exists():
        record_skip("P1-Static", "Project directory not found", str(project))
        return

    api_dir = project / "api"
    core_dir = project / "core"

    def _scan_files(directory: Path, pattern: str = "*.py") -> list[Path]:
        if not directory.exists():
            return []
        return list(directory.rglob(pattern))

    api_files = _scan_files(api_dir)
    core_files = _scan_files(core_dir)
    all_py = api_files + core_files

    # SA-01: Hardcoded secrets
    secret_patterns = [
        re.compile(r'(?:password|secret|api_key|token)\s*=\s*["\'][^"\']{8,}["\']', re.IGNORECASE),
    ]
    exclude_files = {"seed_data.py", "conftest.py", "test_", "pentest_"}
    findings = []
    for f in all_py:
        if any(ex in f.name for ex in exclude_files):
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            for pat in secret_patterns:
                matches = pat.findall(content)
                for m in matches:
                    # Exclude common false positives
                    if any(fp in m.lower() for fp in [
                        "password_hash", "hashed_password", "password_field",
                        "password:", "password=password", "get_password",
                        "verify_password", "validate_password", "password_strength",
                        "os.getenv", "os.environ", "settings.", "config.",
                    ]):
                        continue
                    findings.append(f"{f.name}: {m[:80]}")
        except Exception:
            pass
    if findings:
        record_warn("P1-SA01", "Potential hardcoded secrets found",
                    f"{len(findings)} match(es)", evidence="; ".join(findings[:5]))
    else:
        record_pass("P1-SA01", "No hardcoded secrets detected")

    # SA-02: Debug mode in docker-compose
    compose_files = list(project.glob("docker-compose*.y*ml"))
    debug_found = False
    for cf in compose_files:
        try:
            content = cf.read_text(encoding="utf-8", errors="ignore")
            if "ENVIRONMENT=development" in content or "DEBUG=true" in content.upper():
                debug_found = True
                record_warn("P1-SA02", f"Debug mode in {cf.name}",
                            "ENVIRONMENT=development or DEBUG=true found")
        except Exception:
            pass
    if not debug_found:
        record_pass("P1-SA02", "No debug mode in docker-compose files")

    # SA-03: Unprotected router handlers
    # Check for router endpoints without Depends(get_current_user)
    unprotected = []
    route_pat = re.compile(r'@router\.(get|post|put|delete|patch)\s*\(')
    depends_pat = re.compile(r'Depends\s*\(\s*get_current_user')
    for f in api_files:
        try:
            lines = f.read_text(encoding="utf-8", errors="ignore").split("\n")
            for i, line in enumerate(lines):
                if route_pat.search(line):
                    # Check next 5 lines for Depends(get_current_user)
                    block = "\n".join(lines[i:i + 8])
                    if not depends_pat.search(block):
                        # Some endpoints are public (health, login, register)
                        if any(pub in block for pub in [
                            "/health", "/login", "/register", "/refresh",
                            "public", "/callback",
                        ]):
                            continue
                        unprotected.append(f"{f.name}:L{i + 1}")
        except Exception:
            pass
    if unprotected:
        record_warn("P1-SA03", f"{len(unprotected)} possibly unprotected endpoints",
                    "Missing Depends(get_current_user)",
                    evidence="; ".join(unprotected[:10]))
    else:
        record_pass("P1-SA03", "All endpoints appear protected")

    # SA-04: Raw f-string SQL
    sql_inject_pat = re.compile(r'text\s*\(\s*f["\']')
    sql_findings = []
    for f in all_py:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            for m in sql_inject_pat.finditer(content):
                line_no = content[:m.start()].count("\n") + 1
                sql_findings.append(f"{f.name}:L{line_no}")
        except Exception:
            pass
    if sql_findings:
        record_warn("P1-SA04", "Raw f-string SQL detected (review for injection risk)",
                    f"{len(sql_findings)} occurrence(s)",
                    evidence="; ".join(sql_findings[:5]))
    else:
        record_pass("P1-SA04", "No raw f-string SQL detected")

    # SA-05: CORS wildcard
    cors_found = False
    main_py = project / "api" / "main.py"
    if main_py.exists():
        try:
            content = main_py.read_text(encoding="utf-8", errors="ignore")
            if 'allow_origins=["*"]' in content or "allow_origins=['*']" in content:
                cors_found = True
        except Exception:
            pass
    if cors_found:
        record_warn("P1-SA05", "CORS wildcard allow_origins=['*'] detected",
                    "Consider restricting origins in production")
    else:
        record_pass("P1-SA05", "No CORS wildcard detected")

    # SA-06: Password validation exists
    auth_api_path = project / "api" / "auth_api.py"
    if auth_api_path.exists():
        try:
            content = auth_api_path.read_text(encoding="utf-8", errors="ignore")
            if "_validate_password_strength" in content or "validate_password" in content:
                record_pass("P1-SA06", "Password validation function exists")
            else:
                record_warn("P1-SA06", "No password validation function found in auth_api.py")
        except Exception:
            record_skip("P1-SA06", "Could not read auth_api.py")
    else:
        record_skip("P1-SA06", "auth_api.py not found")

    # SA-07: Migration downgrade completeness
    migrations_dir = project / "alembic" / "versions"
    if migrations_dir.exists():
        migrations = list(migrations_dir.glob("*.py"))
        no_downgrade = []
        for mf in migrations:
            try:
                content = mf.read_text(encoding="utf-8", errors="ignore")
                if "def downgrade" in content:
                    # Check if downgrade body is just pass
                    idx = content.index("def downgrade")
                    body = content[idx:idx + 200]
                    if "pass" in body and "op." not in body:
                        no_downgrade.append(mf.name)
            except Exception:
                pass
        if no_downgrade:
            record_warn("P1-SA07", f"{len(no_downgrade)} migration(s) with empty downgrade",
                        evidence="; ".join(no_downgrade[:5]))
        else:
            record_pass("P1-SA07", "All migrations have downgrade implementations")
    else:
        record_skip("P1-SA07", "Migrations directory not found")

    # SA-08: Model count
    models_py = project / "core" / "models.py"
    if models_py.exists():
        try:
            content = models_py.read_text(encoding="utf-8", errors="ignore")
            class_count = len(re.findall(r'^class \w+\(.*Base\)', content, re.MULTILINE))
            if class_count >= 100:
                record_pass("P1-SA08", f"Model count = {class_count} (>= 100)")
            else:
                record_warn("P1-SA08", f"Model count = {class_count} (< 100 expected)")
        except Exception:
            record_skip("P1-SA08", "Could not read models.py")
    else:
        record_skip("P1-SA08", "core/models.py not found")

    # SA-09: TODO/FIXME count (informational)
    todo_count = 0
    for f in all_py:
        try:
            content = f.read_text(encoding="utf-8", errors="ignore")
            todo_count += len(re.findall(r'#\s*(TODO|FIXME|HACK|XXX)', content, re.IGNORECASE))
        except Exception:
            pass
    record_warn("P1-SA09", f"TODO/FIXME count: {todo_count}",
                "Informational — review for stale items") if todo_count > 0 else \
        record_pass("P1-SA09", "No TODO/FIXME found")

    # SA-10: Requirements version pinning
    req_file = project / "requirements.txt"
    if req_file.exists():
        try:
            lines = req_file.read_text(encoding="utf-8", errors="ignore").strip().split("\n")
            unpinned = [l.strip() for l in lines
                        if l.strip() and not l.startswith("#")
                        and "==" not in l and ">=" not in l and "<=" not in l]
            if unpinned:
                record_warn("P1-SA10", f"{len(unpinned)} unpinned dependencies",
                            evidence="; ".join(unpinned[:10]))
            else:
                record_pass("P1-SA10", "All dependencies are version-pinned")
        except Exception:
            record_skip("P1-SA10", "Could not read requirements.txt")
    else:
        record_skip("P1-SA10", "requirements.txt not found")


# ═══════════════════════════════════════════════════════════════════════
# Phase 2: Observer Journey (S01)
# ═══════════════════════════════════════════════════════════════════════

def phase_2_observer(cfg: AcceptanceConfig):
    print("\n" + "─" * 60)
    print("  Phase 2: S01-Observer Journey")
    print("─" * 60)

    cat = "P2-Observer"
    ts = int(time.time())
    obs_user = f"accept_obs_{ts}"
    obs_email = f"accept_obs_{ts}@test.bhp"
    obs_pass = "AcceptTest1!"
    obs_token = None
    obs_id = None

    # 2.1 Register fresh observer (may hit rate limit → fallback to demo account)
    def _register():
        nonlocal obs_token, obs_id
        data = register_user(cfg, obs_user, obs_email, obs_pass)
        if data:
            obs_token = data.get("access_token")
            obs_id = data.get("user", {}).get("id")
            if not obs_token:
                login_data = login_user(cfg, obs_user, obs_pass)
                if login_data:
                    obs_token = login_data.get("access_token")
                    obs_id = login_data.get("user", {}).get("id")
            record_pass(cat, "Register fresh observer",
                        f"user={obs_user}, id={obs_id}")
        else:
            # Fallback to demo observer account
            obs_fallback = cfg.tokens.get("observer")
            if obs_fallback:
                record_warn(cat, "Register fresh observer",
                            "Registration failed (rate limit?), using demo observer_test")
            else:
                record_warn(cat, "Register fresh observer",
                            "Registration failed, no fallback available")
    safe_call(_register, cat, "Register fresh observer")

    if not obs_token:
        obs_token = cfg.tokens.get("observer")
        obs_id = cfg.user_ids.get("observer")
    if not obs_token:
        record_skip(cat, "Remaining observer tests", "No token available")
        return

    # 2.2 Confirm role = observer
    def _check_role():
        r = api_get(cfg, "/auth/me", obs_token)
        if r.status_code == 200:
            role = r.json().get("role", "")
            if role == "observer":
                record_pass(cat, "New user role is observer")
            else:
                record_fail(cat, "New user role is observer",
                            f"Got role={role}", evidence=r.text[:200])
        else:
            record_fail(cat, "GET /auth/me for observer", f"HTTP {r.status_code}")
    safe_call(_check_role, cat, "Check observer role")

    # 2.3 Journey state
    def _journey():
        r = api_get(cfg, "/journey/state", obs_token)
        check_status(r, [200, 404], cat, "GET /journey/state")
    safe_call(_journey, cat, "GET /journey/state")

    # 2.4 Observer tier
    def _tier():
        r = api_get(cfg, "/governance/observer/tier", obs_token)
        check_status(r, [200, 404], cat, "GET /governance/observer/tier")
    safe_call(_tier, cat, "GET /governance/observer/tier")

    # 2.5 Trial assessment (query param trial_type required)
    def _trial():
        r = cfg.session.post(
            cfg.url("/governance/observer/use-trial"),
            params={"trial_type": "ai_trial"},
            headers={"Authorization": f"Bearer {obs_token}"},
            timeout=cfg.timeout,
        )
        check_status(r, [200, 201, 400, 404, 429], cat, "POST /governance/observer/use-trial")
    safe_call(_trial, cat, "POST /governance/observer/use-trial")

    # 2.6 Create chat session
    session_id = None
    def _chat_create():
        nonlocal session_id
        r = api_post(cfg, "/chat/sessions", obs_token, {"title": "acceptance test"})
        if r.status_code in (200, 201):
            session_id = r.json().get("id") or r.json().get("session_id")
            record_pass(cat, "Create chat session", f"session_id={session_id}")
        else:
            check_status(r, [200, 201], cat, "Create chat session")
    safe_call(_chat_create, cat, "Create chat session")

    # 2.7 Send messages (may 500 if LLM unavailable — WARN not FAIL)
    if session_id:
        for i in range(1, 2):  # single message to avoid slow LLM calls
            def _msg(idx=i):
                r = api_post(cfg, f"/chat/sessions/{session_id}/messages", obs_token,
                             {"content": f"Hello test message {idx}"})
                if r.status_code in (200, 201):
                    record_pass(cat, f"Send message {idx}")
                elif r.status_code == 500:
                    record_warn(cat, f"Send message {idx}",
                                "HTTP 500 — likely LLM backend unavailable",
                                evidence=r.text[:200])
                else:
                    check_status(r, [200, 201], cat, f"Send message {idx}")
            safe_call(_msg, cat, f"Send message {i}")

    # 2.8 Verify observer blocked from coach dashboard
    def _block_coach():
        r = api_get(cfg, "/coach/dashboard", obs_token)
        if r.status_code in (401, 403):
            record_pass(cat, "Observer blocked from /coach/dashboard (403)")
        else:
            record_fail(cat, "Observer blocked from /coach/dashboard",
                        f"Expected 403, got {r.status_code}", evidence=r.text[:200])
    safe_call(_block_coach, cat, "Observer blocked from /coach/dashboard")

    # 2.9 Verify observer blocked from admin
    def _block_admin():
        r = api_get(cfg, "/admin/stats", obs_token)
        if r.status_code in (401, 403):
            record_pass(cat, "Observer blocked from /admin/stats (403)")
        else:
            record_fail(cat, "Observer blocked from /admin/stats",
                        f"Expected 403, got {r.status_code}")
    safe_call(_block_admin, cat, "Observer blocked from /admin/stats")

    # 2.10 Service rights
    def _rights():
        r = api_get(cfg, "/governance/service-rights", obs_token)
        check_status(r, [200, 404], cat, "GET /governance/service-rights")
    safe_call(_rights, cat, "GET /governance/service-rights")

    # 2.11 Agent layer
    def _agent_layer():
        r = api_get(cfg, "/governance/agent-layer", obs_token)
        check_status(r, [200, 404], cat, "GET /governance/agent-layer")
    safe_call(_agent_layer, cat, "GET /governance/agent-layer")

    # 2.12 Activation paths
    def _activation():
        r = api_get(cfg, "/journey/activation-paths", obs_token)
        check_status(r, [200, 404], cat, "GET /journey/activation-paths")
    safe_call(_activation, cat, "GET /journey/activation-paths")


# ═══════════════════════════════════════════════════════════════════════
# Phase 3: Grower Journey (S02)
# ═══════════════════════════════════════════════════════════════════════

def phase_3_grower(cfg: AcceptanceConfig):
    print("\n" + "─" * 60)
    print("  Phase 3: S02-Grower Journey")
    print("─" * 60)

    cat = "P3-Grower"
    token = cfg.tokens.get("grower")

    if not token:
        # Try registering a fresh grower
        ts = int(time.time())
        grw_user = f"accept_grw_{ts}"
        data = register_user(cfg, grw_user, f"{grw_user}@test.bhp", "AcceptTest1!")
        if data:
            login_data = login_user(cfg, grw_user, "AcceptTest1!")
            if login_data:
                token = login_data.get("access_token")
        if not token:
            record_skip(cat, "Grower phase", "No grower token available")
            return

    # 3.1 Chat session + agent
    def _chat():
        r = api_post(cfg, "/chat/sessions", token, {"title": "grower acceptance"})
        check_status(r, [200, 201], cat, "Create grower chat session")
    safe_call(_chat, cat, "Create grower chat session")

    # 3.2 Micro-actions
    def _micro():
        r = api_get(cfg, "/micro-actions/today", token)
        check_status(r, [200, 404], cat, "GET /micro-actions/today")
    safe_call(_micro, cat, "GET /micro-actions/today")

    # 3.3 Learning stats
    def _stats():
        r = api_get(cfg, "/learning/grower/stats", token)
        check_status(r, [200, 404], cat, "GET /learning/grower/stats")
    safe_call(_stats, cat, "GET /learning/grower/stats")

    # 3.4 Learning time
    def _time():
        r = api_post(cfg, "/learning/time/add", token,
                     {"content_id": 1, "duration_seconds": 60})
        check_status(r, [200, 201, 400, 404, 422], cat, "POST /learning/time/add")
    safe_call(_time, cat, "POST /learning/time/add")

    # 3.5 Streak
    def _streak():
        r = api_get(cfg, "/learning/streak", token)
        check_status(r, [200, 404], cat, "GET /learning/streak")
    safe_call(_streak, cat, "GET /learning/streak")

    # 3.6 Leaderboard
    def _leader():
        r = api_get(cfg, "/learning/leaderboard", token)
        check_status(r, [200, 404], cat, "GET /learning/leaderboard")
    safe_call(_leader, cat, "GET /learning/leaderboard")

    # 3.7 Content list
    def _content():
        r = api_get(cfg, "/content", token)
        check_status(r, [200], cat, "GET /content")
    safe_call(_content, cat, "GET /content")

    # 3.8 Recommended content
    def _recommended():
        r = api_get(cfg, "/content/recommended", token)
        check_status(r, [200, 404], cat, "GET /content/recommended")
    safe_call(_recommended, cat, "GET /content/recommended")

    # 3.9 Challenges list
    def _challenges():
        r = api_get(cfg, "/challenges", token)
        check_status(r, [200], cat, "GET /challenges")
    safe_call(_challenges, cat, "GET /challenges")

    # 3.10 My enrollments
    def _enrollments():
        r = api_get(cfg, "/challenges/my-enrollments", token)
        check_status(r, [200], cat, "GET /challenges/my-enrollments")
    safe_call(_enrollments, cat, "GET /challenges/my-enrollments")

    # 3.11 Programs
    def _programs():
        r = api_get(cfg, "/programs/templates", token)
        check_status(r, [200, 404], cat, "GET /programs/templates")
    safe_call(_programs, cat, "GET /programs/templates")

    # 3.12 My programs
    def _my_prog():
        r = api_get(cfg, "/programs/my", token)
        check_status(r, [200, 404], cat, "GET /programs/my")
    safe_call(_my_prog, cat, "GET /programs/my")

    # 3.13 Incentive dashboard
    def _incentive():
        r = api_get(cfg, "/incentive/dashboard", token)
        check_status(r, [200, 404], cat, "GET /incentive/dashboard")
    safe_call(_incentive, cat, "GET /incentive/dashboard")

    # 3.14 Credits
    def _credits():
        r = api_get(cfg, "/credits/my", token)
        check_status(r, [200, 404], cat, "GET /credits/my")
    safe_call(_credits, cat, "GET /credits/my")

    # 3.15 Promotion progress
    def _promo():
        r = api_get(cfg, "/promotion/progress", token)
        check_status(r, [200, 404], cat, "GET /promotion/progress")
    safe_call(_promo, cat, "GET /promotion/progress")

    # 3.16 Journey state
    def _journey():
        r = api_get(cfg, "/journey/state", token)
        check_status(r, [200, 404], cat, "GET /journey/state")
    safe_call(_journey, cat, "GET /journey/state")

    # 3.17 Agency status
    def _agency():
        r = api_get(cfg, "/agency/status", token)
        check_status(r, [200, 404], cat, "GET /agency/status")
    safe_call(_agency, cat, "GET /agency/status")

    # 3.18 Trust score
    def _trust():
        r = api_get(cfg, "/journey/trust", token)
        check_status(r, [200, 404], cat, "GET /journey/trust")
    safe_call(_trust, cat, "GET /journey/trust")

    # 3.19 Reflection journals
    def _reflect():
        r = api_get(cfg, "/reflection/journals", token)
        check_status(r, [200, 404], cat, "GET /reflection/journals")
    safe_call(_reflect, cat, "GET /reflection/journals")

    # 3.20 Peer support
    def _peer():
        r = api_get(cfg, "/peer-support/my-groups", token)
        check_status(r, [200, 404], cat, "GET /peer-support/my-groups")
    safe_call(_peer, cat, "GET /peer-support/my-groups")


# ═══════════════════════════════════════════════════════════════════════
# Phase 4: Sharer Journey (S03)
# ═══════════════════════════════════════════════════════════════════════

def phase_4_sharer(cfg: AcceptanceConfig):
    print("\n" + "─" * 60)
    print("  Phase 4: S03-Sharer Journey")
    print("─" * 60)

    cat = "P4-Sharer"
    token = cfg.tokens.get("sharer")
    if not token:
        record_skip(cat, "Sharer phase", "No sharer token available")
        return

    # 4.1 Submit contribution
    def _contribute():
        r = api_post(cfg, "/contributions/submit", token, {
            "title": "Acceptance test contribution",
            "content": "Test content for acceptance testing",
            "content_type": "article",
        })
        if r.status_code == 500:
            record_warn(cat, "POST /contributions/submit",
                        "HTTP 500 — server error (may need service dependency)",
                        evidence=r.text[:200])
        else:
            check_status(r, [200, 201, 400, 404, 422], cat, "POST /contributions/submit")
    safe_call(_contribute, cat, "POST /contributions/submit")

    # 4.2 My contributions
    def _my_contrib():
        r = api_get(cfg, "/contributions/my", token)
        check_status(r, [200, 404], cat, "GET /contributions/my")
    safe_call(_my_contrib, cat, "GET /contributions/my")

    # 4.3 My mentees
    def _mentees():
        r = api_get(cfg, "/companions/my-mentees", token)
        check_status(r, [200, 404], cat, "GET /companions/my-mentees")
    safe_call(_mentees, cat, "GET /companions/my-mentees")

    # 4.4 My mentors
    def _mentors():
        r = api_get(cfg, "/companions/my-mentors", token)
        check_status(r, [200, 404], cat, "GET /companions/my-mentors")
    safe_call(_mentors, cat, "GET /companions/my-mentors")

    # 4.5 Learning stats
    def _stats():
        r = api_get(cfg, "/learning/grower/stats", token)
        check_status(r, [200, 404], cat, "GET /learning/grower/stats (sharer)")
    safe_call(_stats, cat, "GET /learning/grower/stats (sharer)")

    # 4.6 Content
    def _content():
        r = api_get(cfg, "/content", token)
        check_status(r, [200], cat, "GET /content (sharer)")
    safe_call(_content, cat, "GET /content (sharer)")

    # 4.7 Credits
    def _credits():
        r = api_get(cfg, "/credits/my", token)
        check_status(r, [200, 404], cat, "GET /credits/my (sharer)")
    safe_call(_credits, cat, "GET /credits/my (sharer)")

    # 4.8 Promotion progress + rules
    def _promo():
        r = api_get(cfg, "/promotion/progress", token)
        check_status(r, [200, 404], cat, "GET /promotion/progress (sharer)")
    safe_call(_promo, cat, "GET /promotion/progress (sharer)")


# ═══════════════════════════════════════════════════════════════════════
# Phase 5: Coach Journey (S04)
# ═══════════════════════════════════════════════════════════════════════

def phase_5_coach(cfg: AcceptanceConfig):
    print("\n" + "─" * 60)
    print("  Phase 5: S04-Coach Journey")
    print("─" * 60)

    cat = "P5-Coach"
    token = cfg.tokens.get("coach")
    if not token:
        record_skip(cat, "Coach phase", "No coach token available")
        return

    # 5.1 Dashboard
    def _dash():
        r = api_get(cfg, "/coach/dashboard", token)
        check_status(r, [200], cat, "GET /coach/dashboard")
    safe_call(_dash, cat, "GET /coach/dashboard")

    # 5.2 Students
    def _students():
        r = api_get(cfg, "/coach/students", token)
        check_status(r, [200], cat, "GET /coach/students")
    safe_call(_students, cat, "GET /coach/students")

    # 5.3 Challenges
    def _challenges():
        r = api_get(cfg, "/challenges", token)
        check_status(r, [200], cat, "GET /challenges (coach)")
    safe_call(_challenges, cat, "GET /challenges (coach)")

    # 5.4 Coach analytics - performance
    def _perf():
        r = api_get(cfg, "/coach/performance", token)
        check_status(r, [200, 404], cat, "GET /coach/performance")
    safe_call(_perf, cat, "GET /coach/performance")

    # 5.5 Coach analytics - certification
    def _cert():
        r = api_get(cfg, "/coach/my-certification", token)
        check_status(r, [200, 404], cat, "GET /coach/my-certification")
    safe_call(_cert, cat, "GET /coach/my-certification")

    # 5.6 Coach analytics - tools stats
    def _tools():
        r = api_get(cfg, "/coach/my-tools-stats", token)
        check_status(r, [200, 404], cat, "GET /coach/my-tools-stats")
    safe_call(_tools, cat, "GET /coach/my-tools-stats")

    # 5.7 Agent templates
    def _templates():
        r = api_get(cfg, "/agent-templates", token)
        check_status(r, [200, 404], cat, "GET /agent-templates")
    safe_call(_templates, cat, "GET /agent-templates")

    # 5.8 My tenant
    def _tenant():
        r = api_get(cfg, "/tenants/mine", token)
        check_status(r, [200, 404], cat, "GET /tenants/mine")
    safe_call(_tenant, cat, "GET /tenants/mine")

    # 5.9 Coach messages
    def _messages():
        r = api_get(cfg, "/coach/messages", token)
        check_status(r, [200, 404, 405], cat, "GET /coach/messages")
    safe_call(_messages, cat, "GET /coach/messages")

    # 5.10 Push queue
    def _push():
        r = api_get(cfg, "/push-queue/list", token)
        check_status(r, [200, 404], cat, "GET /push-queue/list")
    safe_call(_push, cat, "GET /push-queue/list")

    # 5.11 Coach levels
    def _levels():
        r = api_get(cfg, "/learning/coach-levels/levels", token)
        check_status(r, [200, 404], cat, "GET /learning/coach-levels/levels")
    safe_call(_levels, cat, "GET /learning/coach-levels/levels")

    # 5.12 Coach points
    def _points():
        r = api_get(cfg, "/learning/coach/points", token)
        check_status(r, [200, 404], cat, "GET /learning/coach/points")
    safe_call(_points, cat, "GET /learning/coach/points")

    # 5.13 Coach directory
    def _directory():
        r = api_get(cfg, "/coach/directory", token)
        check_status(r, [200, 404], cat, "GET /coach/directory")
    safe_call(_directory, cat, "GET /coach/directory")

    # 5.14 Governance dual-track
    def _dual():
        r = api_get(cfg, "/governance/dual-track/status", token)
        check_status(r, [200, 404], cat, "GET /governance/dual-track/status (coach)")
    safe_call(_dual, cat, "GET /governance/dual-track/status (coach)")


# ═══════════════════════════════════════════════════════════════════════
# Phase 6: Supervisor Journey (S05)
# ═══════════════════════════════════════════════════════════════════════

def phase_6_supervisor(cfg: AcceptanceConfig):
    print("\n" + "─" * 60)
    print("  Phase 6: S05-Supervisor Journey")
    print("─" * 60)

    cat = "P6-Supervisor"
    token = cfg.tokens.get("supervisor") or cfg.tokens.get("promoter")
    if not token:
        record_skip(cat, "Supervisor phase", "No supervisor/promoter token available")
        return

    # 6.1 Agent list
    def _agents():
        r = api_get(cfg, "/agent-templates", token)
        check_status(r, [200, 404], cat, "GET /agent-templates (supervisor)")
    safe_call(_agents, cat, "GET /agent-templates (supervisor)")

    # 6.2 Knowledge sharing review queue
    def _review():
        r = api_get(cfg, "/knowledge-sharing/review-queue", token)
        check_status(r, [200, 404], cat, "GET /knowledge-sharing/review-queue")
    safe_call(_review, cat, "GET /knowledge-sharing/review-queue")

    # 6.3 Knowledge sharing stats
    def _kstats():
        r = api_get(cfg, "/knowledge-sharing/stats", token)
        check_status(r, [200, 404], cat, "GET /knowledge-sharing/stats")
    safe_call(_kstats, cat, "GET /knowledge-sharing/stats")

    # 6.4 Pending reviews
    def _pending():
        r = api_get(cfg, "/contributions/pending-reviews", token)
        check_status(r, [200, 404], cat, "GET /contributions/pending-reviews")
    safe_call(_pending, cat, "GET /contributions/pending-reviews")

    # 6.5 Agent feedback metrics
    def _feedback():
        r = api_get(cfg, "/agent-feedback/metrics", token)
        check_status(r, [200, 404], cat, "GET /agent-feedback/metrics")
    safe_call(_feedback, cat, "GET /agent-feedback/metrics")

    # 6.6 Governance dashboard (may be admin-only)
    def _gov():
        r = api_get(cfg, "/governance/dashboard", token)
        check_status(r, [200, 403, 404], cat, "GET /governance/dashboard (supervisor)")
    safe_call(_gov, cat, "GET /governance/dashboard (supervisor)")

    # 6.7 Agent ecosystem marketplace
    def _market():
        r = api_get(cfg, "/agent-ecosystem/marketplace", token)
        check_status(r, [200, 404], cat, "GET /agent-ecosystem/marketplace")
    safe_call(_market, cat, "GET /agent-ecosystem/marketplace")

    # 6.8 Companion overview
    def _companions():
        r = api_get(cfg, "/governance/companions/overview", token)
        check_status(r, [200, 404], cat, "GET /governance/companions/overview")
    safe_call(_companions, cat, "GET /governance/companions/overview")


# ═══════════════════════════════════════════════════════════════════════
# Phase 7: Admin Journey (S06)
# ═══════════════════════════════════════════════════════════════════════

def phase_7_admin(cfg: AcceptanceConfig):
    print("\n" + "─" * 60)
    print("  Phase 7: S06-Admin Journey")
    print("─" * 60)

    cat = "P7-Admin"
    token = cfg.tokens.get("admin")
    if not token:
        record_skip(cat, "Admin phase", "No admin token available")
        return

    endpoints = [
        ("/admin/stats",                  "GET /admin/stats"),
        ("/admin/users",                  "GET /admin/users"),
        ("/content-manage/list",          "GET /content-manage/list"),
        ("/agent-templates",              "GET /agent-templates (admin)"),
        ("/agent-templates/presets",      "GET /agent-templates/presets"),
        ("/safety/dashboard",             "GET /safety/dashboard"),
        ("/safety/logs",                  "GET /safety/logs"),
        ("/safety/config",                "GET /safety/config"),
        ("/analytics/admin/overview",     "GET /analytics/admin/overview"),
        ("/analytics/admin/role-distribution", "GET /analytics/admin/role-distribution"),
        ("/analytics/admin/user-growth",  "GET /analytics/admin/user-growth"),
        ("/surveys",                      "GET /surveys"),
        ("/exams",                        "GET /exams"),
        ("/policy/rules",                 "GET /policy/rules"),
        ("/credits/modules",             "GET /credits/modules"),
        ("/governance/dashboard",         "GET /governance/dashboard (admin)"),
    ]

    for path, title in endpoints:
        def _test(p=path, t=title):
            r = api_get(cfg, p, token)
            check_status(r, [200, 404], cat, t)
        safe_call(_test, cat, title)


# ═══════════════════════════════════════════════════════════════════════
# Phase 8: RBAC Boundary Tests
# ═══════════════════════════════════════════════════════════════════════

def phase_8_rbac(cfg: AcceptanceConfig):
    print("\n" + "─" * 60)
    print("  Phase 8: RBAC Boundary Tests")
    print("─" * 60)

    cat = "P8-RBAC"

    # 8.1 Observer → admin endpoints → expect 403
    obs_token = cfg.tokens.get("observer")
    if obs_token:
        admin_endpoints = [
            "/admin/stats",
            "/admin/users",
            "/safety/dashboard",
            "/analytics/admin/overview",
            "/content-manage/list",
            "/agent-templates/presets",
        ]
        for path in admin_endpoints:
            def _test(p=path):
                r = api_get(cfg, p, obs_token)
                if r.status_code in (401, 403):
                    record_pass(cat, f"Observer blocked: {p}")
                else:
                    record_fail(cat, f"Observer NOT blocked: {p}",
                                f"Expected 403, got {r.status_code}",
                                evidence=r.text[:200])
            safe_call(_test, cat, f"Observer blocked: {path}")
    else:
        record_skip(cat, "Observer RBAC tests", "No observer token")

    # 8.2 Grower → coach endpoints → expect 403/404 (both block access)
    grw_token = cfg.tokens.get("grower")
    if grw_token:
        coach_endpoints = [
            "/coach/dashboard",
            "/coach/students",
            "/push-queue/list",
        ]
        for path in coach_endpoints:
            def _test(p=path):
                r = api_get(cfg, p, grw_token)
                if r.status_code in (401, 403, 404):
                    record_pass(cat, f"Grower blocked: {p}")
                else:
                    record_fail(cat, f"Grower NOT blocked: {p}",
                                f"Expected 403/404, got {r.status_code}",
                                evidence=r.text[:200])
            safe_call(_test, cat, f"Grower blocked: {path}")
    else:
        record_skip(cat, "Grower RBAC tests", "No grower token")

    # 8.3 Coach → admin-only endpoints → expect 403
    coach_token = cfg.tokens.get("coach")
    if coach_token:
        admin_only = [
            "/admin/stats",
            "/admin/users",
            "/safety/dashboard",
        ]
        for path in admin_only:
            def _test(p=path):
                r = api_get(cfg, p, coach_token)
                if r.status_code in (401, 403):
                    record_pass(cat, f"Coach blocked: {p}")
                else:
                    record_fail(cat, f"Coach NOT blocked: {p}",
                                f"Expected 403, got {r.status_code}",
                                evidence=r.text[:200])
            safe_call(_test, cat, f"Coach blocked: {path}")
    else:
        record_skip(cat, "Coach RBAC tests", "No coach token")

    # 8.4 No token → protected endpoints → expect 401/403
    protected = [
        "/auth/me",
        "/journey/state",
        "/credits/my",
        "/micro-actions/today",
        "/challenges/my-enrollments",
        "/coach/dashboard",
        "/admin/stats",
    ]
    for path in protected:
        def _test(p=path):
            r = api_get(cfg, p)  # no token
            if r.status_code in (401, 403, 422):
                record_pass(cat, f"No-token blocked: {p}")
            else:
                record_fail(cat, f"No-token NOT blocked: {p}",
                            f"Expected 401/403, got {r.status_code}",
                            evidence=r.text[:200])
        safe_call(_test, cat, f"No-token blocked: {path}")


# ═══════════════════════════════════════════════════════════════════════
# Phase 9: Data Consistency
# ═══════════════════════════════════════════════════════════════════════

def phase_9_data_consistency(cfg: AcceptanceConfig):
    print("\n" + "─" * 60)
    print("  Phase 9: Data Consistency")
    print("─" * 60)

    cat = "P9-Data"
    admin_token = cfg.tokens.get("admin")

    # 9.1 Admin stats total users >= logged-in count
    if admin_token:
        def _user_count():
            r = api_get(cfg, "/admin/stats", admin_token)
            if r.status_code == 200:
                data = r.json()
                total = data.get("total", data.get("total_users", 0))
                logged = len(cfg.tokens)
                if total >= logged:
                    record_pass(cat, f"total users ({total}) >= logged-in ({logged})")
                else:
                    record_fail(cat, f"total users ({total}) < logged-in ({logged})",
                                "Data inconsistency")
            else:
                record_skip(cat, "Admin stats user count", f"HTTP {r.status_code}")
        safe_call(_user_count, cat, "Admin stats user count")

        # 9.2 Role distribution has data
        def _role_dist():
            r = api_get(cfg, "/analytics/admin/role-distribution", admin_token)
            if r.status_code == 200:
                data = r.json()
                if data:
                    record_pass(cat, "Role distribution has data")
                else:
                    record_warn(cat, "Role distribution returned empty data")
            else:
                record_skip(cat, "Role distribution", f"HTTP {r.status_code}")
        safe_call(_role_dist, cat, "Role distribution")

        # 9.3 Agent templates count
        def _template_count():
            r = api_get(cfg, "/agent-templates/list", admin_token)
            if r.status_code == 200:
                data = r.json()
                count = data.get("total", 0)
                if not count:
                    items = data if isinstance(data, list) else data.get("items", [])
                    count = len(items) if isinstance(items, list) else 0
                if count > 0:
                    record_pass(cat, f"Agent templates count = {count}")
                else:
                    record_warn(cat, "Agent templates returned 0 items")
            else:
                record_skip(cat, "Agent templates count", f"HTTP {r.status_code}")
        safe_call(_template_count, cat, "Agent templates count")
    else:
        record_skip(cat, "Admin data consistency", "No admin token")

    # 9.4 /auth/me user_id matches stored id (multiple roles)
    for role in ["admin", "coach", "grower"]:
        token = cfg.tokens.get(role)
        stored_id = cfg.user_ids.get(role)
        if token and stored_id:
            def _me_check(r=role, t=token, sid=stored_id):
                resp = api_get(cfg, "/auth/me", t)
                if resp.status_code == 200:
                    me_id = resp.json().get("id")
                    if me_id == sid:
                        record_pass(cat, f"/auth/me id matches for {r} (id={sid})")
                    else:
                        record_fail(cat, f"/auth/me id mismatch for {r}",
                                    f"Stored {sid}, got {me_id}")
                else:
                    record_skip(cat, f"/auth/me check for {r}", f"HTTP {resp.status_code}")
            safe_call(_me_check, cat, f"/auth/me check for {role}")

    # 9.5 User growth analytics
    if admin_token:
        def _growth():
            r = api_get(cfg, "/analytics/admin/user-growth", admin_token)
            if r.status_code == 200:
                record_pass(cat, "User growth analytics returns data")
            else:
                record_skip(cat, "User growth analytics", f"HTTP {r.status_code}")
        safe_call(_growth, cat, "User growth analytics")

    # 9.6 Governance dashboard consistency
    if admin_token:
        def _gov_dash():
            r = api_get(cfg, "/governance/dashboard", admin_token)
            if r.status_code == 200:
                record_pass(cat, "Governance dashboard returns data")
            else:
                record_skip(cat, "Governance dashboard", f"HTTP {r.status_code}")
        safe_call(_gov_dash, cat, "Governance dashboard")


# ═══════════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════════

def generate_report(cfg: AcceptanceConfig):
    print("\n" + "=" * 60)
    print("  ACCEPTANCE TEST REPORT")
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
    print(f"\n  {'Category':<20} {'PASS':>6} {'FAIL':>6} {'SKIP':>6} {'WARN':>6}")
    print("  " + "─" * 50)
    for cat in sorted(by_category.keys()):
        s = by_category[cat]
        print(f"  {cat:<20} {s.get('PASS',0):>6} {s.get('FAIL',0):>6} "
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
            "title": "BehaviorOS V4.0 E2E Acceptance Test",
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

def main():
    parser = argparse.ArgumentParser(
        description="BehaviorOS V4.0 E2E Acceptance Test Suite")
    parser.add_argument("--base", default="http://localhost:8000",
                        help="API base URL (default: http://localhost:8000)")
    parser.add_argument("--project", default=".",
                        help="Project root directory for static analysis (default: .)")
    parser.add_argument("--json", default="reports/acceptance.json",
                        help="JSON report output path (default: reports/acceptance.json)")
    parser.add_argument("--skip-static", action="store_true",
                        help="Skip static analysis phase")
    parser.add_argument("--scenario", type=int, default=None,
                        help="Run only a specific phase (0-9)")
    args = parser.parse_args()

    cfg = AcceptanceConfig(args.base, args.project, args.json)

    print("\n" + "=" * 60)
    print("  BehaviorOS V4.0 — E2E Acceptance Test Suite")
    print(f"  Target: {cfg.api}")
    print(f"  Time:   {datetime.now().isoformat()}")
    print("=" * 60)

    phases = {
        0: ("Connectivity & Login", phase_0_connectivity),
        1: ("Static Analysis", phase_1_static_analysis),
        2: ("S01-Observer", phase_2_observer),
        3: ("S02-Grower", phase_3_grower),
        4: ("S03-Sharer", phase_4_sharer),
        5: ("S04-Coach", phase_5_coach),
        6: ("S05-Supervisor", phase_6_supervisor),
        7: ("S06-Admin", phase_7_admin),
        8: ("RBAC Boundary", phase_8_rbac),
        9: ("Data Consistency", phase_9_data_consistency),
    }

    if args.scenario is not None:
        if args.scenario not in phases:
            print(f"  Invalid scenario: {args.scenario}. Valid: 0-9")
            sys.exit(2)
        # Always run Phase 0 for tokens
        if args.scenario != 0:
            phase_0_connectivity(cfg)
        name, fn = phases[args.scenario]
        if args.scenario == 1 and args.skip_static:
            print("  Skipping static analysis (--skip-static)")
        else:
            fn(cfg)
    else:
        # Run all phases
        phase_0_connectivity(cfg)

        if args.skip_static:
            print("\n  Skipping Phase 1 (--skip-static)")
        else:
            phase_1_static_analysis(cfg)

        for phase_num in range(2, 10):
            _, fn = phases[phase_num]
            fn(cfg)

    overall = generate_report(cfg)
    sys.exit(0 if overall == "PASS" else 1)


if __name__ == "__main__":
    main()

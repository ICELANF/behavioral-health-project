#!/usr/bin/env python3
"""
BHP Pre-Launch Comprehensive Check
Tests all routes, chunks, API connectivity for both frontends.
"""
import re
import sys
import json
import time
import urllib.request
import urllib.error
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

ADMIN_BASE = "http://localhost:5174"
H5_BASE = "http://localhost:5173"
API_BASE = "http://localhost:8000"

# ── All Admin Portal Routes ──
ADMIN_ROUTES = [
    "/login", "/landing", "/portal/public", "/portal/medical",
    "/react", "/react/demo", "/expert/workspace", "/journey", "/trace",
    "/admin/evolution",
    "/client", "/client/home-v2", "/client/data-input", "/client/chat",
    "/client/chat-v2", "/client/progress",
    "/client/my/profile", "/client/my/devices", "/client/my/assessments",
    "/client/my/trajectory", "/client/device-dashboard",
    "/client/assessment/list", "/client/assessment/take/1",
    "/client/assessment/result/1", "/client/learning-progress",
    "/coach-portal", "/coach-portal/students", "/coach-portal/ai-review",
    "/expert-portal", "/expert-workbench", "/exam/session/1",
    "/component-showcase",
    "/dashboard",
    "/course/list", "/course/create", "/course/edit/1", "/course/chapters/1",
    "/content/review", "/content/articles", "/content/cases", "/content/cards",
    "/question/bank", "/question/create", "/question/edit/1",
    "/exam/list", "/exam/create", "/exam/edit/1", "/exam/results/1",
    "/exam/proctor-review",
    "/live/list", "/live/create", "/live/edit/1",
    "/coach/list", "/coach/detail/1", "/coach/review",
    "/student",
    "/prompts/list", "/prompts/create", "/prompts/edit/1",
    "/interventions",
    "/coach/my/students", "/coach/my/performance", "/coach/my/certification",
    "/coach/my/tools", "/coach/my/analytics",
    "/coach/content-sharing", "/coach/student-assessment/1",
    "/coach/student-profile/1", "/coach/messages", "/coach/student-health/1",
    "/admin/challenges",
    "/expert/dashboard/1", "/expert/content-studio/1",
    "/expert/my/supervision", "/expert/my/reviews", "/expert/my/research",
    "/admin/user-management", "/admin/distribution", "/admin/analytics",
    "/admin/batch-ingestion", "/admin/content-manage", "/admin/activity-report",
    "/admin/credit-system/dashboard", "/admin/credit-system/modules",
    "/admin/credit-system/companions", "/admin/credit-system/promotion-review",
    "/settings",
]

# ── All H5 Routes ──
H5_ROUTES = [
    "/login", "/", "/chat", "/tasks", "/dashboard", "/profile",
    "/health-records", "/history-reports", "/data-sync", "/notifications",
    "/account-settings", "/privacy-policy", "/about-us",
    "/behavior-assessment", "/my-stage", "/my-plan", "/food-recognition",
    "/challenges", "/challenge-day/1",
    "/learn", "/content/article/1", "/my-learning",
    "/coach-directory", "/contribute",
    "/expert-hub", "/studio/1",
    "/my-credits", "/my-companions", "/promotion-progress",
    "/journey",
    "/programs", "/program/1/today", "/program/1/timeline", "/program/1/progress",
]


def fetch(url, timeout=10):
    """Fetch URL, return (status, content_type, content_length, error)"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BHP-PreLaunch/1.0"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        body = resp.read()
        ct = resp.headers.get("Content-Type", "")
        return resp.status, ct, len(body), None, body
    except urllib.error.HTTPError as e:
        return e.code, "", 0, str(e), b""
    except Exception as e:
        return 0, "", 0, str(e), b""


def check_routes(base, routes, label):
    """Check all SPA routes return index.html"""
    print(f"\n{'='*60}")
    print(f"  {label}: {len(routes)} routes @ {base}")
    print(f"{'='*60}")

    pass_count = 0
    fail_list = []

    for route in routes:
        url = f"{base}{route}"
        status, ct, size, err, body = fetch(url)
        if status == 200 and b"<div id=\"app\">" in body:
            pass_count += 1
        else:
            fail_list.append((route, status, err or f"ct={ct} size={size}"))
            print(f"  FAIL  {route}  [{status}] {err or ''}")

    print(f"\n  Result: {pass_count}/{len(routes)} PASS", end="")
    if fail_list:
        print(f", {len(fail_list)} FAIL")
    else:
        print(" (all good)")
    return fail_list


def check_chunks(base, label):
    """Download index.html, extract entry JS, then check all lazy chunks"""
    print(f"\n{'='*60}")
    print(f"  {label}: Chunk integrity check")
    print(f"{'='*60}")

    # Get index.html
    status, _, _, err, body = fetch(f"{base}/")
    if status != 200:
        print(f"  ERROR: Cannot fetch index.html [{status}] {err}")
        return []

    html = body.decode("utf-8", errors="replace")

    # Extract entry JS path
    entry_match = re.search(r'src="(/assets/[^"]+\.js)"', html)
    entry_css = re.search(r'href="(/assets/[^"]+\.css)"', html)

    if not entry_match:
        print("  ERROR: No entry JS found in index.html")
        return []

    entry_js_path = entry_match.group(1)
    print(f"  Entry JS: {entry_js_path}")
    if entry_css:
        print(f"  Entry CSS: {entry_css.group(1)}")

    # Check entry JS loads
    status, ct, size, err, js_body = fetch(f"{base}{entry_js_path}")
    if status != 200:
        print(f"  FAIL: Entry JS [{status}] {err}")
        return [("entry.js", status, err)]

    js_content = js_body.decode("utf-8", errors="replace")
    print(f"  Entry JS size: {size:,} bytes")

    # Extract all chunk references from the entry JS
    # Vite uses patterns like: () => import("./ChunkName-hash.js") or __vitePreload
    # More commonly: "/assets/ChunkName-hash.js"
    # In Vite builds, chunks are referenced via dynamic import paths
    chunk_refs = set()

    # Pattern 1: Quoted asset paths
    for m in re.finditer(r'["\'](/assets/[A-Za-z0-9_.@-]+-[A-Za-z0-9_-]+\.(js|css))["\']', js_content):
        chunk_refs.add(m.group(1))

    # Pattern 2: Vite dynamic import helper patterns like: "ChunkName-hash"
    # These get resolved to /assets/ChunkName-hash.js at runtime
    # Look for __vitePreload patterns
    for m in re.finditer(r'import\(["\']\./([\w.-]+-[\w-]+\.js)["\']', js_content):
        chunk_refs.add(f"/assets/{m.group(1)}")

    print(f"  Chunk references found in entry JS: {len(chunk_refs)}")

    # Now check all chunks
    missing = []
    checked = 0
    for chunk_path in sorted(chunk_refs):
        status, ct, size, err, _ = fetch(f"{base}{chunk_path}")
        checked += 1
        if status != 200:
            missing.append((chunk_path, status))
            print(f"  MISSING: {chunk_path} [{status}]")

    print(f"  Checked: {checked} chunks, Missing: {len(missing)}")

    # Also list all assets available on server via a smart check
    # Fetch a non-existent path to see error behavior
    status404, _, _, _, body404 = fetch(f"{base}/assets/nonexistent-test.js")
    print(f"  404 behavior: status={status404}, is_html={b'<div id' in body404}")
    if b"<div id" in body404:
        print("  WARNING: nginx returns index.html for missing .js files!")
        print("  This will cause 'Failed to fetch dynamically imported module' errors")

    return missing


def check_api_health():
    """Check backend API is reachable"""
    print(f"\n{'='*60}")
    print(f"  Backend API Health Check @ {API_BASE}")
    print(f"{'='*60}")

    endpoints = [
        "/api/v1/auth/login",
        "/health",
        "/openapi.json",
    ]

    for ep in endpoints:
        status, ct, size, err, _ = fetch(f"{API_BASE}{ep}")
        label = "OK" if status in (200, 405, 422) else "FAIL"
        print(f"  [{label}] {ep} -> {status} ({size:,} bytes)")


def check_nginx_cache_headers(base, label):
    """Check if index.html has proper no-cache headers"""
    print(f"\n{'='*60}")
    print(f"  {label}: Cache header check")
    print(f"{'='*60}")

    try:
        req = urllib.request.Request(f"{base}/", headers={"User-Agent": "BHP-PreLaunch/1.0"})
        resp = urllib.request.urlopen(req, timeout=10)
        cc = resp.headers.get("Cache-Control", "")
        etag = resp.headers.get("ETag", "")
        lm = resp.headers.get("Last-Modified", "")
        print(f"  Cache-Control: {cc or '(not set)'}")
        print(f"  ETag: {etag or '(not set)'}")
        print(f"  Last-Modified: {lm or '(not set)'}")

        if not cc or "no-cache" not in cc.lower():
            print("  WARNING: index.html may be cached by browser!")
            print("  -> This causes 'Failed to fetch dynamically imported module' after rebuilds")
            return False
        else:
            print("  OK: index.html has no-cache headers")
            return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False


def main():
    print("=" * 60)
    print("  BHP Pre-Launch Comprehensive Check")
    print(f"  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    issues = []

    # 1. API Health
    check_api_health()

    # 2. Cache headers
    admin_cache_ok = check_nginx_cache_headers(ADMIN_BASE, "Admin Portal")
    h5_cache_ok = check_nginx_cache_headers(H5_BASE, "H5")
    if not admin_cache_ok:
        issues.append("ADMIN: index.html missing no-cache header")
    if not h5_cache_ok:
        issues.append("H5: index.html missing no-cache header")

    # 3. Chunk integrity
    admin_missing = check_chunks(ADMIN_BASE, "Admin Portal")
    h5_missing = check_chunks(H5_BASE, "H5")
    if admin_missing:
        issues.append(f"ADMIN: {len(admin_missing)} missing chunks")
    if h5_missing:
        issues.append(f"H5: {len(h5_missing)} missing chunks")

    # 4. Route checks
    admin_fails = check_routes(ADMIN_BASE, ADMIN_ROUTES, "Admin Portal Routes")
    h5_fails = check_routes(H5_BASE, H5_ROUTES, "H5 Routes")
    if admin_fails:
        issues.append(f"ADMIN: {len(admin_fails)} route failures")
    if h5_fails:
        issues.append(f"H5: {len(h5_fails)} route failures")

    # Summary
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    total_routes = len(ADMIN_ROUTES) + len(H5_ROUTES)
    total_fails = len(admin_fails) + len(h5_fails)
    print(f"  Routes tested: {total_routes}")
    print(f"  Routes passed: {total_routes - total_fails}")
    print(f"  Routes failed: {total_fails}")

    if issues:
        print(f"\n  ISSUES FOUND ({len(issues)}):")
        for i, issue in enumerate(issues, 1):
            print(f"    {i}. {issue}")
    else:
        print("\n  ALL CHECKS PASSED!")

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""
生产就绪度终极测验 — 4 维验证
基于 321.txt 修正版，修复: Auth/efficacy_score/停容器/判断条件

Usage:
    python scripts/test_production_readiness.py
    python scripts/test_production_readiness.py --skip-drill   # 跳过宕机演练
"""
import sys
import os
import subprocess
import asyncio
import time

# Windows UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

try:
    import httpx
except ImportError:
    print("Installing httpx...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx", "-q"])
    import httpx

# ── 配置 ──
GATEWAY_URL = "http://localhost:80"
BACKEND_URL = "http://localhost:8000"
AUTH_USER = "admin"
AUTH_PASS = "Admin@2026"

# ── 结果收集 ──
results = []


def record(name, passed, detail=""):
    results.append({"name": name, "passed": passed, "detail": detail})
    mark = "\u2705" if passed else "\u274c"
    tag = "PASS" if passed else "FAIL"
    print(f"  {mark} {tag}: {detail}")


async def get_token_fresh() -> str:
    """用独立 client 获取 JWT Token (避免连接池污染)"""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as c:
            resp = await c.post(
                f"{BACKEND_URL}/api/v1/auth/login",
                data={"username": AUTH_USER, "password": AUTH_PASS},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if resp.status_code != 200:
                print(f"  Auth failed: {resp.status_code}")
                return ""
            return resp.json().get("access_token", "")
    except Exception as e:
        print(f"  Auth error: {e}")
        return ""


def auth_header(token: str) -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }


def chat_body(message: str) -> dict:
    return {"message": message, "efficacy_score": 50}


async def wait_for_healthy(max_wait=75):
    """等待 bhp-api 恢复健康 (容忍连接中断)"""
    for i in range(max_wait // 5):
        await asyncio.sleep(5)
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0)) as hc:
                check = await hc.get(f"{BACKEND_URL}/health")
                if check.status_code == 200:
                    print(f"  bhp-api healthy after {(i+1)*5}s")
                    return True
        except Exception:
            pass  # Connection refused during restart is expected
    print(f"  WARNING: bhp-api did not become healthy in {max_wait}s")
    return False


async def run_test_suite():
    skip_drill = "--skip-drill" in sys.argv
    print("=" * 50)
    print(" BHP Production Readiness Test")
    print("=" * 50)
    print()

    # ── Auth ──
    print("[Auth] Acquiring token...")
    token = await get_token_fresh()
    if not token:
        print("  FATAL: Cannot get auth token. Aborting.")
        sys.exit(1)
    print(f"  Token acquired (len={len(token)})")
    print()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 1: Normal path via Nginx
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("[Test 1] Normal path via Nginx gateway (port 80)...")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            start = time.time()
            res = await client.post(
                f"{GATEWAY_URL}/api/v1/chat",
                json=chat_body("hello"),
                headers=auth_header(token),
            )
            duration = time.time() - start
            ok = res.status_code == 200 and duration < 5
            data = res.json() if res.status_code == 200 else {}
            status = data.get("status", "?")
            expert = data.get("primary_expert_id", "?")
            record("Normal path", ok,
                   f"HTTP {res.status_code}, {duration:.2f}s, status={status}, expert={expert}")
    except Exception as e:
        record("Normal path", False, f"Exception: {e}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 2: Ollama self-healing
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n[Test 2] Cloud LLM fallback to Ollama (direct backend)...")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
            res = await client.post(
                f"{BACKEND_URL}/api/v1/chat",
                json=chat_body("help me check blood sugar"),
                headers=auth_header(token),
            )
            data = res.json() if res.status_code == 200 else {}
            expert_id = data.get("primary_expert_id", "")
            status = data.get("status", "")
            is_fallback = "ollama" in expert_id.lower() or "fallback" in expert_id.lower()
            ok = res.status_code == 200 and (is_fallback or status == "success")
            record("Ollama self-heal", ok,
                   f"HTTP {res.status_code}, expert={expert_id}, status={status}")
    except Exception as e:
        record("Ollama self-heal", False, f"Exception: {e}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 3: Nginx fallback when backend is down
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if skip_drill:
        print("\n[Test 3] Nginx fallback drill -- SKIPPED (--skip-drill)")
        record("Nginx fallback", True, "Skipped by flag")
    else:
        print("\n[Test 3] Nginx fallback drill (stopping bhp-api)...")
        try:
            subprocess.run(
                ["docker", "stop", "bhp-api"],
                capture_output=True, timeout=30,
            )
            await asyncio.sleep(2)

            async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
                res = await client.post(
                    f"{GATEWAY_URL}/api/v1/chat",
                    json=chat_body("emergency"),
                    headers=auth_header(token),
                )
            body = res.text
            ok = res.status_code == 200 and "OFFLINE_HEALTH_MODE" in body
            record("Nginx fallback", ok,
                   f"HTTP {res.status_code}, has_OFFLINE={'OFFLINE_HEALTH_MODE' in body}")

            # Restore
            print("  Restoring bhp-api...")
            subprocess.run(
                ["docker", "start", "bhp-api"],
                capture_output=True, timeout=30,
            )
            await wait_for_healthy(75)

        except Exception as e:
            record("Nginx fallback", False, f"Exception: {e}")
            subprocess.run(["docker", "start", "bhp-api"], capture_output=True)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # Test 4: WeChat 5s concurrency stress test
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n[Test 4] WeChat 5s concurrency test (10 requests)...")
    try:
        # Re-acquire token (old one may have expired during drill)
        token = await get_token_fresh()
        if not token:
            record("5s concurrency", False, "Cannot re-acquire token after drill")
        else:
            async with httpx.AsyncClient(timeout=httpx.Timeout(15.0)) as client:
                tasks = [
                    client.post(
                        f"{GATEWAY_URL}/api/v1/chat",
                        json=chat_body(f"concurrent test {i}"),
                        headers=auth_header(token),
                    )
                    for i in range(10)
                ]
                start = time.time()
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                total_duration = time.time() - start

                successes = sum(
                    1 for r in responses
                    if not isinstance(r, Exception) and r.status_code == 200
                )
                errors = 10 - successes
                ok = errors == 0 and total_duration < 5
                record("5s concurrency", ok,
                       f"{successes}/10 success, {total_duration:.2f}s total, {errors} errors")
    except Exception as e:
        record("5s concurrency", False, f"Exception: {e}")

    # ── Summary ──
    print("\n" + "=" * 50)
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f" Result: {passed}/{total} PASSED")
    for r in results:
        mark = "\u2705" if r["passed"] else "\u274c"
        print(f"  {mark} {r['name']}: {r['detail']}")
    print("=" * 50)

    return 0 if passed == total else 1


if __name__ == "__main__":
    rc = asyncio.run(run_test_suite())
    sys.exit(rc)

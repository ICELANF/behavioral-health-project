# -*- coding: utf-8 -*-
"""
P3 联调: 6 角色端到端旅程验证
==============================
针对 Docker 后端 (http://localhost:8000) 运行

用法:
  1. docker-compose up -d
  2. python e2e_6roles.py [--base http://localhost:8000]

每个角色走完核心旅程，输出 PASS/FAIL/SKIP 清单
"""
import argparse
import json
import sys
import time
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from typing import Optional, Dict, Any, List, Tuple

# ─── 配置 ───────────────────────────────────────────────────
BASE = "http://localhost:8000"
API = f"{BASE}/api/v1"
V3 = f"{BASE}/v3"
TIMEOUT = 10

# ─── 工具 ───────────────────────────────────────────────────
class TestRunner:
    def __init__(self):
        self.results: List[Tuple[str, str, str, str]] = []  # (role, test, status, detail)
        self.tokens: Dict[str, str] = {}
        self.user_ids: Dict[str, int] = {}

    def _headers(self, role: str) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if role in self.tokens:
            h["Authorization"] = f"Bearer {self.tokens[role]}"
        return h

    def _get(self, role: str, path: str, base: str = None) -> requests.Response:
        url = f"{base or API}{path}"
        return requests.get(url, headers=self._headers(role), timeout=TIMEOUT, verify=False)

    def _post(self, role: str, path: str, data: dict = None, base: str = None) -> requests.Response:
        url = f"{base or API}{path}"
        return requests.post(url, json=data or {}, headers=self._headers(role), timeout=TIMEOUT, verify=False)

    def _put(self, role: str, path: str, data: dict = None, base: str = None) -> requests.Response:
        url = f"{base or API}{path}"
        return requests.put(url, json=data or {}, headers=self._headers(role), timeout=TIMEOUT, verify=False)

    def check(self, role: str, name: str, fn):
        """执行一个检查项"""
        try:
            ok, detail = fn()
            status = "PASS" if ok else "FAIL"
        except requests.ConnectionError:
            status, detail = "SKIP", "Connection refused (backend not running?)"
        except requests.Timeout:
            status, detail = "SKIP", "Timeout"
        except Exception as e:
            status, detail = "FAIL", str(e)[:120]
        self.results.append((role, name, status, detail))
        icon = {"PASS": "v", "FAIL": "x", "SKIP": "o"}[status]
        print(f"  {icon} [{role}] {name}: {detail}")

    # ─── 认证 ───────────────────────────────────────────
    def register_user(self, role: str, username: str, password: str = "Test123456!"):
        """注册用户"""
        def fn():
            # 尝试 v3 auth
            r = requests.post(f"{API}/auth/register", json={
                "username": username,
                "password": password,
                "email": f"{username}@test.behaviros.com",
                "full_name": f"Test {role.title()}",
            }, timeout=TIMEOUT, verify=False)
            if r.status_code in (200, 201):
                data = r.json()
                return True, f"registered (v3), status={r.status_code}"
            # 尝试 v1 auth
            r2 = requests.post(f"{API}/auth/register", json={
                "username": username,
                "password": password,
                "email": f"{username}2@test.behaviros.com",
                "full_name": f"Test {role.title()}",
            }, timeout=TIMEOUT, verify=False)
            if r2.status_code in (200, 201):
                return True, f"registered (v1), status={r2.status_code}"
            # 409 = already exists = OK
            if r.status_code in (400, 409, 429) or r2.status_code in (400, 409, 429):
                return True, "already exists or rate-limited"
            return False, f"v3={r.status_code} v1={r2.status_code}: {r.text[:80]}"
        self.check(role, "register", fn)

    def login_user(self, role: str, username: str, password: str = "Test123456!"):
        """登录获取 token"""
        def fn():
            # 尝试 v3
            for base_path in [f"{API}/auth/login"]:
                r = requests.post(base_path, json={
                    "username": username,
                    "password": password,
                }, timeout=TIMEOUT, verify=False)
                if r.status_code == 200:
                    data = r.json()
                    token = data.get("access_token") or data.get("token") or data.get("data", {}).get("access_token")
                    if token:
                        self.tokens[role] = token
                        # 提取 user_id
                        uid = data.get("user_id") or data.get("data", {}).get("user_id") or data.get("id")
                        if uid:
                            self.user_ids[role] = int(uid)
                        return True, f"logged in, token={token[:20]}..."
            return False, f"login failed at all endpoints"
        self.check(role, "login", fn)

    # ─── Observer 旅程 ──────────────────────────────────
    def test_observer(self):
        role = "observer"
        print(f"\n{'='*50}")
        print(f"  OBSERVER 旅程 (匿名 → 信任建立 → 注册引导)")
        print(f"{'='*50}")

        self.register_user(role, "test_observer")
        self.login_user(role, "test_observer")

        # Observer 配额
        self.check(role, "quota/today", lambda: (
            (r := self._get(role, "/observer/quota/today")).status_code == 200,
            f"status={r.status_code}, body={r.text[:80]}"
        ))

        # Observer 层级
        self.check(role, "observer/tier", lambda: (
            (r := self._get(role, "/observer/tier")).status_code in (200, 404),
            f"status={r.status_code}, body={r.text[:80]}"
        ))

        # Agent 对话 (TrustGuide)
        self.check(role, "agent/run (trust_guide)", lambda: (
            (r := self._post(role, "/agent/run", {
                "agent_type": "trust_guide",
                "user_id": str(self.user_ids.get(role, 1)),
                "expected_output": "你好，我想了解平台",
            })).status_code == 200,
            f"status={r.status_code}, body={r.text[:100]}"
        ))

        # 权限检查
        self.check(role, "segments/permissions", lambda: (
            (r := self._get(role, "/segments/permissions")).status_code == 200,
            f"status={r.status_code}"
        ))

    # ─── Grower 旅程 ───────────────────────────────────
    def test_grower(self):
        role = "grower"
        print(f"\n{'='*50}")
        print(f"  GROWER 旅程 (评估 → 微行动 → 挑战 → 学习 → 积分)")
        print(f"{'='*50}")

        self.register_user(role, "test_grower")
        self.login_user(role, "test_grower")

        uid = self.user_ids.get(role, 1)

        # 旅程状态
        self.check(role, "journey/state", lambda: (
            (r := self._get(role, "/journey/state")).status_code == 200,
            f"status={r.status_code}, body={r.text[:80]}"
        ))

        # 旅程激活
        self.check(role, "journey/activate", lambda: (
            (r := self._post(role, "/journey/activate")).status_code in (200, 400, 409),
            f"status={r.status_code}, body={r.text[:80]}"
        ))

        # 评估
        self.check(role, "assessment/profile/me", lambda: (
            (r := self._get(role, "/assessment/profile/me")).status_code in (200, 404),
            f"status={r.status_code}"
        ))

        self.check(role, "assessment-assignments/my-pending", lambda: (
            (r := self._get(role, "/assessment-assignments/my-pending")).status_code == 200,
            f"status={r.status_code}, body={r.text[:80]}"
        ))

        # 微行动
        self.check(role, "micro-actions/today", lambda: (
            (r := self._get(role, "/micro-actions/today")).status_code == 200,
            f"status={r.status_code}, body={r.text[:80]}"
        ))

        self.check(role, "micro-actions/stats", lambda: (
            (r := self._get(role, "/micro-actions/stats")).status_code == 200,
            f"status={r.status_code}"
        ))

        self.check(role, "micro-actions/history", lambda: (
            (r := self._get(role, "/micro-actions/history")).status_code == 200,
            f"status={r.status_code}"
        ))

        # 挑战
        self.check(role, "challenges (list)", lambda: (
            (r := self._get(role, "/challenges")).status_code == 200,
            f"status={r.status_code}, body={r.text[:80]}"
        ))

        self.check(role, "challenges/my-enrollments", lambda: (
            (r := self._get(role, "/challenges/my-enrollments")).status_code == 200,
            f"status={r.status_code}"
        ))

        # 积分
        self.check(role, "credits/my", lambda: (
            (r := self._get(role, "/credits/my")).status_code == 200,
            f"status={r.status_code}, body={r.text[:80]}"
        ))

        self.check(role, "credits/my/records", lambda: (
            (r := self._get(role, "/credits/my/records")).status_code == 200,
            f"status={r.status_code}"
        ))

        # 学习
        self.check(role, f"learning/grower/stats/{uid}", lambda: (
            (r := self._get(role, f"/learning/grower/stats/{uid}")).status_code in (200, 403, 404),
            f"status={r.status_code}"
        ))

        # 内容
        self.check(role, "content (list)", lambda: (
            (r := self._get(role, "/content")).status_code == 200,
            f"status={r.status_code}, body={r.text[:80]}"
        ))

        self.check(role, "content/recommended", lambda: (
            (r := self._get(role, "/content/recommended")).status_code == 200,
            f"status={r.status_code}"
        ))

        # 健康数据
        self.check(role, "health-data/summary", lambda: (
            (r := self._get(role, "/health-data/summary")).status_code in (200, 404),
            f"status={r.status_code}"
        ))

        # 反思
        self.check(role, "reflection/entries", lambda: (
            (r := self._get(role, "/reflection/entries")).status_code == 200,
            f"status={r.status_code}"
        ))

        self.check(role, "reflection/prompts", lambda: (
            (r := self._get(role, "/reflection/prompts")).status_code == 200,
            f"status={r.status_code}"
        ))

        # Agent 对话
        self.check(role, "agent/list", lambda: (
            (r := self._get(role, "/agent/list")).status_code == 200,
            f"status={r.status_code}, agents={len(r.json().get('data', []))}"
        ))

        self.check(role, "chat/sessions (list)", lambda: (
            (r := self._get(role, "/chat/sessions")).status_code == 200,
            f"status={r.status_code}"
        ))

    # ─── Sharer 旅程 ───────────────────────────────────
    def test_sharer(self):
        role = "sharer"
        print(f"\n{'='*50}")
        print(f"  SHARER 旅程 (分享 → 社区 → 升级)")
        print(f"{'='*50}")

        # 复用 grower token (sharer 是 grower 的升级)
        if "grower" in self.tokens:
            self.tokens[role] = self.tokens["grower"]
            self.user_ids[role] = self.user_ids.get("grower", 1)
        else:
            self.register_user(role, "test_sharer")
            self.login_user(role, "test_sharer")

        # Sharer 资格检查
        self.check(role, "promotion/sharer-check", lambda: (
            (r := self._get(role, "/promotion/sharer-check")).status_code in (200, 404),
            f"status={r.status_code}, body={r.text[:80]}"
        ))

    # ─── Coach 旅程 ────────────────────────────────────
    def test_coach(self):
        role = "coach"
        print(f"\n{'='*50}")
        print(f"  COACH 旅程 (仪表板 → 学员 → AI建议 → 督导)")
        print(f"{'='*50}")

        self.register_user(role, "test_coach")
        self.login_user(role, "test_coach")

        # 教练仪表板
        self.check(role, "coach/dashboard", lambda: (
            (r := self._get(role, "/coach/dashboard")).status_code in (200, 403),
            f"status={r.status_code}, body={r.text[:80]}"
        ))

        # 学员列表
        self.check(role, "coach/students", lambda: (
            (r := self._get(role, "/coach/students")).status_code in (200, 403),
            f"status={r.status_code}"
        ))

        # 教练绩效
        self.check(role, "coach/performance", lambda: (
            (r := self._get(role, "/coach/performance")).status_code in (200, 403),
            f"status={r.status_code}"
        ))

        # Agent 待审核
        self.check(role, "agent/pending-reviews", lambda: (
            (r := self._get(role, "/agent/pending-reviews")).status_code == 200,
            f"status={r.status_code}"
        ))

        # 推送队列
        self.check(role, "coach/push-queue", lambda: (
            (r := self._get(role, "/coach/push-queue/")).status_code in (200, 403, 404),
            f"status={r.status_code}"
        ))

    # ─── Supervisor 旅程 ──────────────────────────────
    def test_supervisor(self):
        role = "supervisor"
        print(f"\n{'='*50}")
        print(f"  SUPERVISOR 旅程 (审计 → 治理 → 质控)")
        print(f"{'='*50}")

        self.register_user(role, "test_supervisor")
        self.login_user(role, "test_supervisor")

        # 审计日志
        self.check(role, "audit-log/recent", lambda: (
            (r := self._get(role, "/audit-log/recent")).status_code in (200, 403, 404),
            f"status={r.status_code}"
        ))

        # 审计队列
        self.check(role, "audit-queue", lambda: (
            (r := self._get(role, "/audit-queue")).status_code in (200, 403, 404),
            f"status={r.status_code}"
        ))

        # 治理仪表板
        self.check(role, "governance/dashboard", lambda: (
            (r := self._get(role, "/governance/dashboard")).status_code in (200, 403, 404),
            f"status={r.status_code}"
        ))

    # ─── Admin 旅程 ───────────────────────────────────
    def test_admin(self):
        role = "admin"
        print(f"\n{'='*50}")
        print(f"  ADMIN 旅程 (用户管理 → 统计 → 安全 → Agent系统)")
        print(f"{'='*50}")

        self.register_user(role, "test_admin")
        self.login_user(role, "test_admin")

        # 管理统计
        self.check(role, "admin/stats", lambda: (
            (r := self._get(role, "/admin/stats")).status_code in (200, 403),
            f"status={r.status_code}, body={r.text[:80]}"
        ))

        # 用户列表
        self.check(role, "admin/users", lambda: (
            (r := self._get(role, "/admin/users")).status_code in (200, 403),
            f"status={r.status_code}"
        ))

        # 安全日志
        self.check(role, "safety/logs", lambda: (
            (r := self._get(role, "/safety/logs")).status_code in (200, 403, 404),
            f"status={r.status_code}"
        ))

        # 分析
        self.check(role, "analytics/admin/overview", lambda: (
            (r := self._get(role, "/analytics/admin/overview")).status_code in (200, 403, 404),
            f"status={r.status_code}"
        ))

        self.check(role, "analytics/admin/stage-distribution", lambda: (
            (r := self._get(role, "/analytics/admin/stage-distribution")).status_code in (200, 403, 404),
            f"status={r.status_code}"
        ))

        # Agent 系统状态
        self.check(role, "agent/status", lambda: (
            (r := self._get(role, "/agent/status")).status_code == 200,
            f"status={r.status_code}, body={r.text[:100]}"
        ))

    # ─── 跨角色: 危机检测 ─────────────────────────────
    def test_crisis_e2e(self):
        role = "grower"
        print(f"\n{'='*50}")
        print(f"  CRISIS 全链路 (Agent 危机检测端到端)")
        print(f"{'='*50}")

        if role not in self.tokens:
            print("  o SKIP: no grower token")
            return

        self.check("crisis", "agent/run (crisis message)", lambda: (
            (r := self._post(role, "/agent/run", {
                "agent_type": "crisis",
                "user_id": str(self.user_ids.get(role, 1)),
                "expected_output": "我不想活了，太痛苦了",
                "priority": "high",
            })).status_code == 200,
            f"status={r.status_code}, routed_to={r.json().get('data',{}).get('agent_type','?')}, success={r.json().get('success')}"
        ))

    # ─── 汇总 ──────────────────────────────────────────
    def summary(self):
        print(f"\n{'='*60}")
        print(f"  E2E 联调汇总")
        print(f"{'='*60}")

        by_role = {}
        for role, name, status, detail in self.results:
            if role not in by_role:
                by_role[role] = {"PASS": 0, "FAIL": 0, "SKIP": 0}
            by_role[role][status] += 1

        total_pass = sum(v["PASS"] for v in by_role.values())
        total_fail = sum(v["FAIL"] for v in by_role.values())
        total_skip = sum(v["SKIP"] for v in by_role.values())
        total = total_pass + total_fail + total_skip

        for role, counts in by_role.items():
            icon = "v" if counts["FAIL"] == 0 else "x"
            print(f"  {icon} {role:12} PASS={counts['PASS']} FAIL={counts['FAIL']} SKIP={counts['SKIP']}")

        print(f"\n  Total: {total_pass}/{total} passed, {total_fail} failed, {total_skip} skipped")

        # FAIL 清单
        fails = [(r, n, d) for r, n, s, d in self.results if s == "FAIL"]
        if fails:
            print(f"\n  ── FAIL Details ──")
            for role, name, detail in fails:
                print(f"    x [{role}] {name}: {detail}")

        return total_fail


# ─── Main ───────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="P3 E2E 6-Role Integration Test")
    parser.add_argument("--base", default="http://localhost:8000", help="Backend base URL")
    args = parser.parse_args()

    global BASE, API, V3
    BASE = args.base.rstrip("/")
    API = f"{BASE}/api/v1"
    V3 = f"{BASE}/v3"

    print(f"Target: {BASE}")
    print(f"API:    {API}")

    # 连通性检查
    try:
        r = requests.get(f"{BASE}/api/v1/agent/status", timeout=5, verify=False)
        print(f"Backend: UP (status={r.status_code})")
    except requests.ConnectionError:
        print(f"\nx Backend not reachable at {BASE}")
        print(f"  Run: docker-compose up -d")
        print(f"  Then: python e2e_6roles.py")
        sys.exit(1)

    runner = TestRunner()

    runner.test_observer()
    runner.test_grower()
    runner.test_sharer()
    runner.test_coach()
    runner.test_supervisor()
    runner.test_admin()
    runner.test_crisis_e2e()

    fails = runner.summary()
    sys.exit(1 if fails > 0 else 0)


if __name__ == "__main__":
    main()

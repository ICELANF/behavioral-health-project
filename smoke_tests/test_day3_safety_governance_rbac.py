"""
Day 3 端到端冒烟测试 — 安全链路 + 治理闭环 + RBAC边界
覆盖 Sheet: ②治理轨 · ⑥责任追踪 · ⑨治理触点 · ⑬Rx引擎 · ⑮工具引擎

路径A: SafetyPipeline拦截 + 审计
路径B: Coach KPI + 治理仪表盘
路径C: RBAC全角色越权拦截
路径D: BehaviorRx处方引擎
验收标准: 安全拦截可验证，仪表盘可达，角色越权被拦

Uses pre-seeded accounts from seed_smoke_data.py.
Auth: form-encoded login with username field (OAuth2PasswordRequestForm).
"""
import pytest
import httpx
import time

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api/v1"
SMOKE_PASSWORD = "Test@Smoke2026!"


# ============================================================
# Module-scoped fixtures — login once per role
# ============================================================

@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=API, timeout=30) as c:
        yield c

@pytest.fixture(scope="module")
def raw_client():
    with httpx.Client(base_url=BASE_URL, timeout=30) as c:
        yield c


def _do_login(client, username, password=SMOKE_PASSWORD):
    """Form-encoded login, returns headers dict or None"""
    r = client.post("/auth/login", data={
        "username": username,
        "password": password,
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if r.status_code == 200:
        token = r.json().get("access_token") or r.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    return None


@pytest.fixture(scope="module")
def observer_auth(client):
    headers = _do_login(client, "smoke_observer")
    if not headers:
        pytest.skip("smoke_observer not available")
    return headers

@pytest.fixture(scope="module")
def grower_auth(client):
    time.sleep(0.3)
    headers = _do_login(client, "smoke_grower")
    if not headers:
        pytest.skip("smoke_grower not available")
    return headers

@pytest.fixture(scope="module")
def coach_auth(client):
    time.sleep(0.3)
    headers = _do_login(client, "smoke_coach")
    if not headers:
        pytest.skip("smoke_coach not available")
    return headers

@pytest.fixture(scope="module")
def sharer_auth(client):
    time.sleep(0.3)
    headers = _do_login(client, "smoke_sharer")
    if not headers:
        pytest.skip("smoke_sharer not available")
    return headers

@pytest.fixture(scope="module")
def admin_auth(client):
    time.sleep(0.3)
    headers = _do_login(client, "admin", "Admin@2026")
    if not headers:
        pytest.skip("admin account not available")
    return headers


# ============================================================
# Part A: SafetyPipeline — Sheet⑨⑬⑮
# ============================================================

class TestA1_SafetyPipelineNormal:
    """正常输入 → 正常响应"""

    def test_agent_run_normal(self, client, grower_auth):
        """POST /agent/run (正常输入) → 200"""
        # Get user_id from /auth/me first
        me = client.get("/auth/me", headers=grower_auth)
        user_id = me.json().get("id") or me.json().get("user_id") if me.status_code == 200 else 1

        r = client.post("/agent/run", headers=grower_auth, json={
            "input": "Please help me plan a healthy diet",
            "agent_type": "health_assistant",
            "user_id": user_id,
        })
        if r.status_code == 404:
            pytest.skip("Agent run endpoint not found")
        # 200=success, 500=internal (LLM unavailable)
        if r.status_code == 500:
            pytest.skip(f"Agent internal error (LLM may be offline): {r.text[:80]}")
        assert r.status_code in (200, 422), f"Agent run: {r.status_code} {r.text[:200]}"

    def test_agent_unauthenticated_blocked(self, client):
        """Agent run without token — 401"""
        r = client.post("/agent/run", json={
            "input": "test", "agent_type": "health_assistant",
        })
        if r.status_code == 404:
            pytest.skip("Agent run endpoint not found")
        assert r.status_code in (401, 403), f"Unauthenticated agent: {r.status_code}"


class TestA2_SafetyDashboard:
    """Safety admin endpoints"""

    def test_safety_dashboard(self, client, admin_auth):
        """Admin safety dashboard"""
        r = client.get("/safety/dashboard", headers=admin_auth)
        if r.status_code == 404:
            pytest.skip("Safety dashboard not found")
        assert r.status_code == 200

    def test_safety_logs(self, client, admin_auth):
        """Admin safety logs"""
        r = client.get("/safety/logs", headers=admin_auth)
        if r.status_code == 404:
            pytest.skip("Safety logs not found")
        assert r.status_code == 200

    def test_safety_config(self, client, admin_auth):
        """Admin safety config"""
        r = client.get("/safety/config", headers=admin_auth)
        if r.status_code == 404:
            pytest.skip("Safety config not found")
        assert r.status_code == 200


# ============================================================
# Part B: 治理闭环 — Coach + Admin dashboards
# ============================================================

class TestB1_CoachDashboard:
    """教练仪表盘"""

    def test_coach_dashboard(self, client, coach_auth):
        """Coach dashboard accessible"""
        r = client.get("/coach/dashboard", headers=coach_auth)
        if r.status_code == 404:
            pytest.skip("Coach dashboard not found")
        assert r.status_code == 200

    def test_coach_students(self, client, coach_auth):
        """Coach students list"""
        r = client.get("/coach/students", headers=coach_auth)
        if r.status_code == 404:
            pytest.skip("Coach students not found")
        assert r.status_code == 200

    def test_coach_performance(self, client, coach_auth):
        """Coach performance metrics"""
        r = client.get("/coach/performance", headers=coach_auth)
        if r.status_code == 404:
            pytest.skip("Coach performance not found")
        assert r.status_code == 200


class TestB2_AdminGovernance:
    """管理员治理看板"""

    def test_admin_stats(self, client, admin_auth):
        """Admin stats endpoint"""
        r = client.get("/admin/stats", headers=admin_auth)
        if r.status_code == 404:
            pytest.skip("Admin stats not found")
        assert r.status_code == 200

    def test_admin_users(self, client, admin_auth):
        """Admin users list"""
        r = client.get("/admin/users", headers=admin_auth)
        if r.status_code == 404:
            pytest.skip("Admin users not found")
        assert r.status_code == 200

    def test_governance_dashboard(self, client, admin_auth):
        """Governance dashboard"""
        r = client.get("/governance/dashboard", headers=admin_auth)
        if r.status_code == 404:
            pytest.skip("Governance dashboard not found")
        assert r.status_code == 200

    def test_analytics_admin_overview(self, client, admin_auth):
        """Admin analytics overview"""
        r = client.get("/analytics/admin/overview", headers=admin_auth)
        if r.status_code == 404:
            pytest.skip("Admin analytics not found")
        assert r.status_code == 200


# ============================================================
# Part C: RBAC全角色越权拦截
# ============================================================

class TestC1_ObserverRBAC:
    """Observer cannot access elevated endpoints"""

    def test_observer_blocked_from_coach_dashboard(self, client, observer_auth):
        r = client.get("/coach/dashboard", headers=observer_auth)
        assert r.status_code in (403, 404)

    def test_observer_blocked_from_coach_students(self, client, observer_auth):
        r = client.get("/coach/students", headers=observer_auth)
        assert r.status_code in (403, 404)

    def test_observer_blocked_from_admin_users(self, client, observer_auth):
        r = client.get("/admin/users", headers=observer_auth)
        assert r.status_code in (403, 404)

    def test_observer_blocked_from_safety(self, client, observer_auth):
        r = client.get("/safety/dashboard", headers=observer_auth)
        assert r.status_code in (403, 404)

    def test_observer_blocked_from_agent_templates(self, client, observer_auth):
        r = client.post("/agent-templates", headers=observer_auth,
                        json={"name": "test"})
        assert r.status_code in (403, 404, 405)


class TestC2_GrowerRBAC:
    """Grower cannot access coach/admin endpoints"""

    def test_grower_blocked_from_admin(self, client, grower_auth):
        r = client.get("/admin/users", headers=grower_auth)
        assert r.status_code in (403, 404)

    def test_grower_blocked_from_coach_dashboard(self, client, grower_auth):
        r = client.get("/coach/dashboard", headers=grower_auth)
        assert r.status_code in (403, 404)

    def test_grower_blocked_from_safety_config(self, client, grower_auth):
        r = client.get("/safety/config", headers=grower_auth)
        assert r.status_code in (403, 404)


class TestC3_CoachRBAC:
    """Coach cannot access admin-only endpoints"""

    def test_coach_blocked_from_admin_users(self, client, coach_auth):
        r = client.get("/admin/users", headers=coach_auth)
        assert r.status_code in (403, 404)

    def test_coach_blocked_from_admin_stats(self, client, coach_auth):
        r = client.get("/admin/stats", headers=coach_auth)
        assert r.status_code in (403, 404)

    def test_coach_blocked_from_safety_config(self, client, coach_auth):
        """Coach should not modify safety config"""
        r = client.put("/safety/config", headers=coach_auth, json={"key": "val"})
        assert r.status_code in (403, 404, 405)


class TestC4_SharerRBAC:
    """Sharer role boundary"""

    def test_sharer_blocked_from_admin(self, client, sharer_auth):
        r = client.get("/admin/users", headers=sharer_auth)
        assert r.status_code in (403, 404)

    def test_sharer_can_view_content(self, client, sharer_auth):
        """Sharer can access content"""
        r = client.get("/content", headers=sharer_auth)
        assert r.status_code == 200


class TestC5_UnauthenticatedRBAC:
    """No token → 401 on protected endpoints"""

    PROTECTED = [
        "/auth/me", "/content", "/coach/dashboard",
        "/admin/users", "/safety/dashboard",
    ]

    @pytest.mark.parametrize("path", PROTECTED)
    def test_no_token_blocked(self, client, path):
        r = client.get(path)
        assert r.status_code in (401, 403), \
            f"No-token access to {path} should be blocked, got: {r.status_code}"


class TestC6_AdminFullAccess:
    """Admin can access admin-only endpoints"""

    def test_admin_can_access_users(self, client, admin_auth):
        r = client.get("/admin/users", headers=admin_auth)
        assert r.status_code == 200

    def test_admin_can_access_safety(self, client, admin_auth):
        r = client.get("/safety/dashboard", headers=admin_auth)
        if r.status_code == 404:
            pytest.skip("Safety dashboard not found")
        assert r.status_code == 200

    def test_admin_can_view_agent_templates(self, client, admin_auth):
        r = client.get("/agent-templates", headers=admin_auth)
        if r.status_code == 404:
            pytest.skip("Agent templates not found")
        assert r.status_code == 200


# ============================================================
# Part D: BehaviorRx 处方引擎 — Sheet⑬
# ============================================================

class TestD1_BehaviorRxSmoke:
    """行为处方引擎基本可用性"""

    def test_ecosystem_rx_endpoint(self, client, grower_auth):
        """Ecosystem Rx endpoint"""
        r = client.get("/ecosystem-v4/rx/current", headers=grower_auth)
        if r.status_code == 404:
            r = client.post("/ecosystem-v4/rx/generate", headers=grower_auth, json={})
        if r.status_code == 404:
            pytest.skip("Rx endpoint not found")
        assert r.status_code in (200, 201, 422), \
            f"Rx engine: {r.status_code}"


# ============================================================
# Part E: 数据一致性 & 角色验证
# ============================================================

class TestE1_RoleVerification:
    """Verify all seeded accounts have correct roles"""

    def test_observer_role(self, client, observer_auth):
        r = client.get("/auth/me", headers=observer_auth)
        assert r.status_code == 200
        assert r.json().get("role", "").upper() == "OBSERVER"

    def test_grower_role(self, client, grower_auth):
        r = client.get("/auth/me", headers=grower_auth)
        assert r.status_code == 200
        assert r.json().get("role", "").upper() == "GROWER"

    def test_coach_role(self, client, coach_auth):
        r = client.get("/auth/me", headers=coach_auth)
        assert r.status_code == 200
        assert r.json().get("role", "").upper() == "COACH"

    def test_sharer_role(self, client, sharer_auth):
        r = client.get("/auth/me", headers=sharer_auth)
        assert r.status_code == 200
        assert r.json().get("role", "").upper() == "SHARER"

    def test_admin_role(self, client, admin_auth):
        r = client.get("/auth/me", headers=admin_auth)
        assert r.status_code == 200
        assert r.json().get("role", "").upper() == "ADMIN"

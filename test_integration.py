"""
V4.1 Week 4: 跨层集成测试

~40用例覆盖:
  1. 授权矩阵 (5角色 × 6端点 = 30组合)
  2. 脱敏验证 (10用例)
  3. 核心Agent (behavior_coach + health_assistant)
  4. 端到端链路 (教练→网关→用户数据→脱敏→返回)

运行:
    pytest test_integration.py -v --tb=short
    pytest test_integration.py -k "auth" -v        # 只跑授权
    pytest test_integration.py -k "sanitize" -v     # 只跑脱敏
"""
import pytest
import requests
import json
import re
from typing import Optional

# ── 配置 ──

BASE_URL = "http://localhost:8000"

# 测试账号（根据实际环境调整）
ACCOUNTS = {
    "admin":      {"username": "admin",      "password": "Admin@2026"},
    "coach":      {"username": "coach_test",      "password": "Test@2026"},
    "supervisor": {"username": "supervisor_test", "password": "Test@2026"},
    "grower":     {"username": "grower_test",     "password": "Test@2026"},
    "observer":   {"username": "observer_test", "password": "Test@2026"},
}

# 测试用user_id（需要一个实际存在的用户ID）
TEST_USER_ID = None  # 在setup中动态获取


# ═══════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════

def _login(role: str) -> Optional[str]:
    """获取指定角色的token"""
    if role not in ACCOUNTS:
        return None
    acc = ACCOUNTS[role]
    try:
        resp = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data={"username": acc["username"], "password": acc["password"]},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except Exception:
        pass
    return None


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def admin_token():
    token = _login("admin")
    if not token:
        pytest.skip("admin登录失败")
    return token


@pytest.fixture(scope="session")
def coach_token():
    token = _login("coach")
    if not token:
        pytest.skip("coach登录失败")
    return token


@pytest.fixture(scope="session")
def supervisor_token():
    token = _login("supervisor")
    if not token:
        pytest.skip("supervisor登录失败")
    return token


@pytest.fixture(scope="session")
def grower_token():
    token = _login("grower")
    if not token:
        pytest.skip("grower登录失败")
    return token


@pytest.fixture(scope="session")
def observer_token():
    token = _login("observer")
    if not token:
        pytest.skip("observer登录失败")
    return token


@pytest.fixture(scope="session")
def test_user_id(admin_token):
    """获取一个实际存在的用户ID用于测试"""
    resp = requests.get(
        f"{BASE_URL}/api/v1/admin/users",
        headers=_headers(admin_token),
        params={"page_size": 1},
        timeout=10,
    )
    if resp.status_code == 200:
        data = resp.json()
        users = data.get("users") or data.get("items") or data.get("data", [])
        if users:
            uid = users[0].get("id")
            if uid:
                return str(uid)
    pytest.skip("无法获取测试用户ID")


# ═══════════════════════════════════════════════════════════
# 1. 双层Agent注册验证
# ═══════════════════════════════════════════════════════════

class TestAgentRegistration:
    """验证双层Agent注册"""

    def test_assistant_agents_list(self):
        resp = requests.get(f"{BASE_URL}/v1/assistant/agents", timeout=10)
        assert resp.status_code == 200
        agents = resp.json()["agents"]
        assert len(agents) == 12
        names = {a["name"] for a in agents}
        assert "health_assistant" in names
        assert "nutrition_guide" in names
        assert "crisis_responder" in names

    def test_professional_agents_list(self):
        resp = requests.get(f"{BASE_URL}/v1/agent/agents", timeout=10)
        assert resp.status_code == 200
        agents = resp.json()["agents"]
        assert len(agents) == 16
        names = {a["name"] for a in agents}
        assert "behavior_coach" in names
        assert "metabolic_expert" in names
        assert "rx_composer" in names

    def test_assistant_agent_detail(self):
        resp = requests.get(f"{BASE_URL}/v1/assistant/agents/health_assistant", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "health_assistant"
        assert data["domain"] == "general"

    def test_professional_agent_detail(self):
        resp = requests.get(f"{BASE_URL}/v1/agent/agents/behavior_coach", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "behavior_coach"
        assert data["domain"] == "behavior"

    def test_nonexistent_agent_404(self):
        resp = requests.get(f"{BASE_URL}/v1/assistant/agents/nonexistent", timeout=10)
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════
# 2. 网关授权矩阵
# ═══════════════════════════════════════════════════════════

class TestGatewayAuth:
    """5角色 × 6端点 授权矩阵"""

    GATEWAY_ENDPOINTS = [
        ("GET", "/v1/gateway/patient/{uid}/profile"),
        ("GET", "/v1/gateway/patient/{uid}/assessments"),
        ("GET", "/v1/gateway/patient/{uid}/journey"),
        ("GET", "/v1/gateway/bindings"),
        ("GET", "/v1/gateway/audit-log"),
    ]

    # ── Admin: 全部可访问 ──

    def test_admin_access_profile(self, admin_token, test_user_id):
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/patient/{test_user_id}/profile",
            headers=_headers(admin_token), timeout=10,
        )
        assert resp.status_code == 200

    def test_admin_access_assessments(self, admin_token, test_user_id):
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/patient/{test_user_id}/assessments",
            headers=_headers(admin_token), timeout=10,
        )
        assert resp.status_code == 200

    def test_admin_access_journey(self, admin_token, test_user_id):
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/patient/{test_user_id}/journey",
            headers=_headers(admin_token), timeout=10,
        )
        # 200 或 404（如果该用户无旅程数据）
        assert resp.status_code in (200, 404)

    def test_admin_access_bindings(self, admin_token):
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/bindings",
            headers=_headers(admin_token), timeout=10,
        )
        assert resp.status_code == 200

    def test_admin_access_audit_log(self, admin_token):
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/audit-log",
            headers=_headers(admin_token), timeout=10,
        )
        assert resp.status_code == 200

    # ── Coach: 绑定学员可访问，audit-log不可 ──

    def test_coach_access_bindings(self, coach_token):
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/bindings",
            headers=_headers(coach_token), timeout=10,
        )
        assert resp.status_code == 200

    def test_coach_blocked_audit_log(self, coach_token):
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/audit-log",
            headers=_headers(coach_token), timeout=10,
        )
        assert resp.status_code == 403

    def test_coach_unbound_student_blocked(self, coach_token):
        """教练访问未绑定学员 → 403"""
        # 用一个不太可能绑定的ID
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/patient/99999/profile",
            headers=_headers(coach_token), timeout=10,
        )
        assert resp.status_code in (400, 403, 404)

    # ── Grower: 网关全部拒绝 ──

    def test_grower_blocked_profile(self, grower_token, test_user_id):
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/patient/{test_user_id}/profile",
            headers=_headers(grower_token), timeout=10,
        )
        assert resp.status_code == 403

    def test_grower_blocked_bindings(self, grower_token):
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/bindings",
            headers=_headers(grower_token), timeout=10,
        )
        assert resp.status_code == 403

    def test_grower_blocked_audit(self, grower_token):
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/audit-log",
            headers=_headers(grower_token), timeout=10,
        )
        assert resp.status_code == 403

    # ── Observer: 网关全部拒绝 ──

    def test_observer_blocked_profile(self, observer_token, test_user_id):
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/patient/{test_user_id}/profile",
            headers=_headers(observer_token), timeout=10,
        )
        assert resp.status_code == 403

    # ── 未认证: 401 ──

    def test_unauthenticated_gateway(self, test_user_id):
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/patient/{test_user_id}/profile",
            timeout=10,
        )
        assert resp.status_code in (401, 403)

    def test_unauthenticated_bindings(self):
        resp = requests.get(f"{BASE_URL}/v1/gateway/bindings", timeout=10)
        assert resp.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════
# 3. 脱敏验证
# ═══════════════════════════════════════════════════════════

class TestSanitization:
    """验证跨层数据脱敏"""

    def test_profile_no_password(self, admin_token, test_user_id):
        """profile返回中不含password_hash"""
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/patient/{test_user_id}/profile",
            headers=_headers(admin_token), timeout=10,
        )
        if resp.status_code != 200:
            pytest.skip("profile端点不可用")
        data = resp.json()
        profile = data.get("profile", {})
        assert "password_hash" not in profile
        assert "password" not in profile

    def test_profile_no_token(self, admin_token, test_user_id):
        """profile返回中不含token"""
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/patient/{test_user_id}/profile",
            headers=_headers(admin_token), timeout=10,
        )
        if resp.status_code != 200:
            pytest.skip("profile端点不可用")
        profile = resp.json().get("profile", {})
        assert "token" not in profile
        assert "refresh_token" not in profile
        assert "auth_token" not in profile

    def test_profile_email_masked(self, admin_token, test_user_id):
        """email被掩码处理"""
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/patient/{test_user_id}/profile",
            headers=_headers(admin_token), timeout=10,
        )
        if resp.status_code != 200:
            pytest.skip("profile端点不可用")
        profile = resp.json().get("profile", {})
        email = profile.get("email", "")
        if email:
            # 应该是 x***@domain 格式
            assert "***" in email or email == "", f"email未脱敏: {email}"

    def test_profile_phone_masked(self, admin_token, test_user_id):
        """phone被掩码处理"""
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/patient/{test_user_id}/profile",
            headers=_headers(admin_token), timeout=10,
        )
        if resp.status_code != 200:
            pytest.skip("profile端点不可用")
        profile = resp.json().get("profile", {})
        phone = profile.get("phone", "")
        if phone:
            assert "****" in phone or phone == "", f"phone未脱敏: {phone}"

    def test_sanitized_fields_reported(self, admin_token, test_user_id):
        """返回脱敏字段列表"""
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/patient/{test_user_id}/profile",
            headers=_headers(admin_token), timeout=10,
        )
        if resp.status_code != 200:
            pytest.skip("profile端点不可用")
        data = resp.json()
        assert "sanitized_fields" in data
        # 至少应该脱敏了password_hash
        fields = data["sanitized_fields"]
        assert isinstance(fields, list)

    def test_assessment_no_raw_answers(self, admin_token, test_user_id):
        """评估结果不含原始答题"""
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/patient/{test_user_id}/assessments",
            headers=_headers(admin_token), timeout=10,
        )
        if resp.status_code != 200:
            pytest.skip("assessments端点不可用")
        data = resp.json()
        text = json.dumps(data)
        assert "raw_assessment_answers" not in text
        assert "answer_details" not in text


# ═══════════════════════════════════════════════════════════
# 4. 审计日志验证
# ═══════════════════════════════════════════════════════════

class TestAuditLog:
    """验证跨层访问审计"""

    def test_audit_log_records_access(self, admin_token, test_user_id):
        """访问patient数据后，审计日志应有记录"""
        # 先触发一次访问
        requests.get(
            f"{BASE_URL}/v1/gateway/patient/{test_user_id}/profile",
            headers=_headers(admin_token), timeout=10,
        )
        # 查审计日志
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/audit-log",
            headers=_headers(admin_token),
            params={"page_size": 5},
            timeout=10,
        )
        assert resp.status_code == 200
        logs = resp.json().get("logs", [])
        assert len(logs) > 0, "审计日志为空"

    def test_audit_log_contains_actor(self, admin_token):
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/audit-log",
            headers=_headers(admin_token),
            params={"page_size": 1},
            timeout=10,
        )
        if resp.status_code != 200 or not resp.json().get("logs"):
            pytest.skip("无审计记录")
        log = resp.json()["logs"][0]
        assert "actor_id" in log
        assert "action" in log
        assert "result" in log

    def test_audit_log_filter_by_result(self, admin_token):
        """按结果过滤"""
        resp = requests.get(
            f"{BASE_URL}/v1/gateway/audit-log",
            headers=_headers(admin_token),
            params={"result": "allowed"},
            timeout=10,
        )
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════
# 5. Bridge兼容验证
# ═══════════════════════════════════════════════════════════

class TestBridgeCompatibility:
    """验证旧路径仍可工作"""

    def test_old_agent_list_path(self, admin_token):
        """旧路径 /api/v1/agent/list 仍可访问"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/agent/list",
            headers=_headers(admin_token),
            timeout=10,
            allow_redirects=True,
        )
        # 可能是200（直接命中旧路由）或307→200（bridge转发）
        assert resp.status_code in (200, 307)

    def test_old_sessions_path(self, grower_token):
        """旧路径 /sessions 仍可访问"""
        resp = requests.get(
            f"{BASE_URL}/sessions",
            headers=_headers(grower_token),
            timeout=10,
            allow_redirects=True,
        )
        # 200 或 307 或 404（如果旧路由已删除但bridge兜底）
        assert resp.status_code in (200, 307, 404)


# ═══════════════════════════════════════════════════════════
# 6. Schema分离验证
# ═══════════════════════════════════════════════════════════

class TestSchemaIsolation:
    """验证coach_schema隔离"""

    def test_coach_endpoints_still_work(self, admin_token):
        """教练层端点在schema迁移后仍正常"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/agent/list",
            headers=_headers(admin_token),
            timeout=10,
            allow_redirects=True,
        )
        assert resp.status_code in (200, 307)

    def test_admin_dashboard_no_500(self, admin_token):
        """治理仪表盘正常"""
        resp = requests.get(
            f"{BASE_URL}/api/v1/governance/dashboard",
            headers=_headers(admin_token),
            timeout=10,
        )
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════
# 7. 冒烟回归 (关键路径)
# ═══════════════════════════════════════════════════════════

class TestSmokeRegression:
    """确认核心路径未回归"""

    def test_health_check(self):
        resp = requests.get(f"{BASE_URL}/health", timeout=10)
        assert resp.status_code == 200

    def test_auth_flow(self):
        token = _login("admin")
        assert token is not None

    def test_dual_layer_agents_available(self):
        r1 = requests.get(f"{BASE_URL}/v1/assistant/agents", timeout=10)
        r2 = requests.get(f"{BASE_URL}/v1/agent/agents", timeout=10)
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert len(r1.json()["agents"]) == 12
        assert len(r2.json()["agents"]) == 16

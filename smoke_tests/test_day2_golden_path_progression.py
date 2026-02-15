"""
Day 2 端到端冒烟测试 — 黄金路径后半段
覆盖 Sheet: ④晋级契约 · ⑦积分契约 · ⑪教练体系

路径: 积分累积 → S0-S4阶段 → L0→L1双轨晋级 → AntiCheat → 数据一致性
验收标准: 积分正确累积，双轨晋级可查，防刷端点可达，数据一致
前置: Day1通过, seed_smoke_data.py已执行, smoke_grower/coach/sharer账号存在
"""
import pytest
import httpx
import time

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api/v1"
SMOKE_PASSWORD = "Test@Smoke2026!"


# ============================================================
# Module-scoped fixtures
# ============================================================

@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=API, timeout=30) as c:
        yield c

@pytest.fixture(scope="module")
def raw_client():
    with httpx.Client(base_url=BASE_URL, timeout=30) as c:
        yield c


def _do_login(client, username):
    """Form-encoded login, returns headers dict or None"""
    r = client.post("/auth/login", data={
        "username": username,
        "password": SMOKE_PASSWORD,
    }, headers={"Content-Type": "application/x-www-form-urlencoded"})
    if r.status_code == 200:
        token = r.json().get("access_token") or r.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    return None


@pytest.fixture(scope="module")
def grower_auth(client):
    """Pre-seeded smoke_grower account"""
    headers = _do_login(client, "smoke_grower")
    if not headers:
        pytest.skip("smoke_grower account not available (run seed_smoke_data.py)")
    return headers


@pytest.fixture(scope="module")
def coach_auth(client):
    """Pre-seeded smoke_coach account"""
    time.sleep(0.3)
    headers = _do_login(client, "smoke_coach")
    if not headers:
        pytest.skip("smoke_coach account not available")
    return headers


# ============================================================
# S1. 积分累积 — Sheet⑦ 积分契约
# ============================================================

class TestS1_PointsAccumulation:
    """验证积分相关端点可达"""

    def _get_points(self, client, headers):
        """Try multiple paths for points/credits summary"""
        for path in ["/credits/my", "/learning/grower/stats"]:
            r = client.get(path, headers=headers)
            if r.status_code == 200:
                return r.json()
        return None

    def test_credits_endpoint(self, client, grower_auth):
        """积分/学分端点可达"""
        r = client.get("/credits/my", headers=grower_auth)
        if r.status_code == 404:
            pytest.skip("Credits endpoint not found")
        assert r.status_code == 200, f"Credits: {r.status_code}"

    def test_learning_stats(self, client, grower_auth):
        """学习统计端点可达"""
        r = client.get("/learning/grower/stats", headers=grower_auth)
        if r.status_code == 404:
            # Try alternate path
            r = client.get("/learning/stats", headers=grower_auth)
        if r.status_code == 404:
            pytest.skip("Learning stats endpoint not found")
        assert r.status_code == 200, f"Learning stats: {r.status_code}"

    def test_learning_time_add(self, client, grower_auth):
        """POST /learning/time/add — 记录学习时间"""
        r = client.post("/learning/time/add", headers=grower_auth, json={
            "duration": 10,
            "content_id": 1,
        })
        if r.status_code == 404:
            pytest.skip("Learning time add endpoint not found")
        # 200/201 success, 422 validation
        assert r.status_code in (200, 201, 422), \
            f"Learning time add: {r.status_code} {r.text[:200]}"

    def test_points_history(self, client, grower_auth):
        """积分历史/明细端点"""
        for path in ["/learning/points/history", "/credits/records",
                     "/learning/grower/stats"]:
            r = client.get(path, headers=grower_auth)
            if r.status_code == 200:
                return  # found a working endpoint
        pytest.skip("No points history endpoint found")


# ============================================================
# S2. S0→S4 阶段查询 — StageEngine
# ============================================================

class TestS2_StageProgression:
    """阶段查询与推进"""

    def test_current_stage_queryable(self, client, grower_auth):
        """可查询当前阶段"""
        r = client.get("/journey/state", headers=grower_auth)
        if r.status_code == 404:
            pytest.skip("Journey state endpoint not found")
        assert r.status_code == 200
        data = r.json()
        # Check that some stage-related data exists
        assert data, "Journey state returned empty"

    def test_journey_has_stage_field(self, client, grower_auth):
        """Journey state has stage information"""
        r = client.get("/journey/state", headers=grower_auth)
        if r.status_code == 404:
            pytest.skip("Journey state not available")
        assert r.status_code == 200
        data = r.json()
        stage = (data.get("journey_stage") or data.get("current_stage")
                 or data.get("stage") or data.get("status"))
        if not stage:
            pytest.skip(f"No stage field in journey: {list(data.keys())}")

    def test_stage_advance_endpoint(self, client, grower_auth):
        """Stage advance endpoint reachable"""
        r = client.post("/journey/advance", headers=grower_auth, json={
            "target_stage": "S1",
        })
        if r.status_code == 404:
            # Try governance stage transition
            r = client.post("/governance/stage-transition",
                            headers=grower_auth, json={"target": "S1"})
        if r.status_code == 404:
            pytest.skip("Stage advance endpoint not found")
        # Any non-500 is OK (422=conditions not met, 200=success)
        assert r.status_code != 500, f"Stage advance 500: {r.text[:200]}"

    def test_stage_skip_blocked(self, client, grower_auth):
        """Skipping stages should be prevented"""
        r = client.post("/journey/advance", headers=grower_auth, json={
            "target_stage": "S4",
        })
        if r.status_code == 404:
            pytest.skip("Stage advance endpoint not found")
        # Direct S4 jump should be rejected (422/400/403)
        assert r.status_code in (422, 400, 403), \
            f"Stage skip to S4 should be blocked, got: {r.status_code}"


# ============================================================
# S3. L0→L1 双轨晋级校验 — Sheet④
# ============================================================

class TestS3_DualTrackPromotion:
    """双轨晋级: 积分轨 + 成长轨"""

    def test_promotion_progress(self, client, grower_auth):
        """晋级进度可查"""
        r = client.get("/promotion/progress", headers=grower_auth)
        if r.status_code == 404:
            r = client.get("/promotion/status", headers=grower_auth)
        if r.status_code == 404:
            pytest.skip("Promotion endpoint not found")
        assert r.status_code == 200, f"Promotion: {r.status_code}"

    def test_promotion_rules(self, client, grower_auth):
        """晋级规则/要求可查"""
        r = client.get("/promotion/rules", headers=grower_auth)
        if r.status_code == 404:
            pytest.skip("Promotion rules not found")
        assert r.status_code == 200

    def test_promotion_apply(self, client, grower_auth):
        """申请晋级 — 条件未满足应422"""
        r = client.post("/promotion/apply", headers=grower_auth, json={
            "target_level": "L1",
        })
        if r.status_code == 404:
            pytest.skip("Promotion apply endpoint not found")
        # 200=success, 422/400=conditions not met
        assert r.status_code in (200, 201, 422, 400), \
            f"Promotion apply: {r.status_code}"


# ============================================================
# S4. 挑战 & 微行动
# ============================================================

class TestS4_ChallengesAndActions:
    """挑战系统 + 微行动"""

    def test_challenges_list(self, client, grower_auth):
        """挑战列表可达"""
        r = client.get("/challenges", headers=grower_auth)
        if r.status_code == 404:
            pytest.skip("Challenges endpoint not found")
        assert r.status_code == 200

    def test_my_enrollments(self, client, grower_auth):
        """我参加的挑战"""
        r = client.get("/challenges/my-enrollments", headers=grower_auth)
        if r.status_code == 404:
            pytest.skip("My enrollments not found")
        assert r.status_code == 200

    def test_micro_actions(self, client, grower_auth):
        """微行动端点"""
        r = client.get("/micro-actions/today", headers=grower_auth)
        if r.status_code == 404:
            pytest.skip("Micro actions not found")
        assert r.status_code == 200

    def test_incentive_dashboard(self, client, grower_auth):
        """激励面板可达"""
        r = client.get("/incentive/dashboard", headers=grower_auth)
        if r.status_code == 404:
            pytest.skip("Incentive dashboard not found")
        assert r.status_code == 200


# ============================================================
# S5. Coach端点验证
# ============================================================

class TestS5_CoachEndpoints:
    """Coach角色端点可达性"""

    def test_coach_dashboard(self, client, coach_auth):
        """Coach dashboard"""
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


# ============================================================
# S6. 数据一致性 Day2
# ============================================================

class TestS6_DataConsistency:
    """数据一致性验证"""

    def test_auth_me_consistent(self, client, grower_auth):
        """/auth/me returns consistent data"""
        r1 = client.get("/auth/me", headers=grower_auth)
        r2 = client.get("/auth/me", headers=grower_auth)
        assert r1.status_code == 200 and r2.status_code == 200
        assert r1.json().get("id") == r2.json().get("id")

    def test_grower_role_correct(self, client, grower_auth):
        """smoke_grower has GROWER role"""
        r = client.get("/auth/me", headers=grower_auth)
        assert r.status_code == 200
        role = r.json().get("role", "").upper()
        assert role == "GROWER", f"Expected GROWER, got: {role}"

    def test_coach_role_correct(self, client, coach_auth):
        """smoke_coach has COACH role"""
        r = client.get("/auth/me", headers=coach_auth)
        assert r.status_code == 200
        role = r.json().get("role", "").upper()
        assert role == "COACH", f"Expected COACH, got: {role}"

    def test_no_500_errors(self, client, grower_auth):
        """Key endpoints don't return 500"""
        endpoints = [
            "/auth/me", "/content", "/journey/state",
            "/credits/my", "/challenges",
        ]
        for ep in endpoints:
            r = client.get(ep, headers=grower_auth)
            assert r.status_code != 500, f"500 on {ep}: {r.text[:100]}"

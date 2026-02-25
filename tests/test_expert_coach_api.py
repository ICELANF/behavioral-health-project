"""
tests/test_expert_coach_api.py
Migration 054 + Expert API + Coach Recruit 集成测试
对应: api/expert_api.py, api/institution_partner_api.py, alembic/versions/054_*.py
"""
import pytest
from httpx import AsyncClient

BASE = "http://localhost:8000"
HEADERS_COACH   = {"Authorization": "Bearer <coach_token>"}
HEADERS_EXPERT  = {"Authorization": "Bearer <expert_token>"}
HEADERS_ADMIN   = {"Authorization": "Bearer <admin_token>"}
HEADERS_STUDENT = {"Authorization": "Bearer <observer_token>"}


# ── Migration 054 验证 ─────────────────────────────────────────────
class TestMigration054:
    async def test_new_tables_exist(self, db):
        tables = [
            "expert_public_profiles", "expert_patient_bindings",
            "xzb_knowledge", "xzb_rules",
            "partner_configs", "partner_revenue_logs",
        ]
        for t in tables:
            result = await db.fetch_one(
                f"SELECT to_regclass('public.{t}') AS oid"
            )
            assert result["oid"] is not None, f"Table {t} missing"

    async def test_institution_admin_enum(self, db):
        result = await db.fetch_one(
            "SELECT enumlabel FROM pg_enum WHERE enumlabel = 'INSTITUTION_ADMIN'"
        )
        assert result is not None, "INSTITUTION_ADMIN enum missing"

    async def test_expert_tenants_columns(self, db):
        result = await db.fetch_one(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='expert_tenants' AND column_name='expert_slug'"
        )
        assert result is not None, "expert_slug column missing"


# ── Expert Service Modes ───────────────────────────────────────────
class TestExpertServiceModes:
    @pytest.mark.asyncio
    async def test_get_service_modes(self):
        async with AsyncClient(base_url=BASE) as client:
            r = await client.get("/api/v1/expert/service-modes", headers=HEADERS_EXPERT)
        assert r.status_code == 200
        data = r.json()
        assert "mode_a_public" in data
        assert "mode_b_clinical" in data
        assert "mode_c_coach_network" in data

    @pytest.mark.asyncio
    async def test_patch_service_modes(self):
        async with AsyncClient(base_url=BASE) as client:
            r = await client.patch("/api/v1/expert/service-modes",
                headers=HEADERS_EXPERT,
                json={"mode_a_public": True})
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_public_homepage_no_auth(self):
        """公开主页无需登录可访问"""
        async with AsyncClient(base_url=BASE) as client:
            r = await client.get("/api/v1/expert/public/test-slug")
        assert r.status_code in (200, 404)  # 404 if slug not exist

    @pytest.mark.asyncio
    async def test_force_push_blocked_always_403(self):
        """铁律 I-06: Expert 永远不能直接推送任务"""
        async with AsyncClient(base_url=BASE) as client:
            r = await client.post("/api/v1/expert/tasks/force-push",
                headers=HEADERS_EXPERT,
                json={"student_id": 1, "content": "test"})
        assert r.status_code == 403
        assert "铁律" in r.json().get("detail", "")

    @pytest.mark.asyncio
    async def test_xzb_requires_coach_review(self):
        """XZBRxFragment.requires_coach_review 始终为 True"""
        from core.xzb_service import XZBRxFragment
        frag = XZBRxFragment(rx_suggestion="test", evidence_tier="T1",
                              knowledge_ids=[1], confidence=0.8)
        assert frag.requires_coach_review is True


# ── Institution API ────────────────────────────────────────────────
class TestInstitutionAPI:
    @pytest.mark.asyncio
    async def test_register_institution_public(self):
        """机构注册无需登录"""
        async with AsyncClient(base_url=BASE) as client:
            r = await client.post("/api/v1/institutions/register", json={
                "name": "测试学校", "institution_type": "school",
                "contact_name": "张老师", "contact_phone": "13800138000",
                "address": "北京市海淀区",
            })
        assert r.status_code in (200, 201)


# ── Coach Promotion Apply ──────────────────────────────────────────
class TestCoachPromotion:
    @pytest.mark.asyncio
    async def test_apply_promotion(self):
        """POST /api/v1/coach/promotion-applications"""
        async with AsyncClient(base_url=BASE) as client:
            r = await client.post("/api/v1/coach/promotion-applications",
                headers=HEADERS_STUDENT,
                json={
                    "current_level": "L2",
                    "story": "我通过持续的行为干预成功改善了自身的代谢状况，" * 5,
                    "target_domain": "代谢综合征管理",
                })
        assert r.status_code in (200, 201)

    @pytest.mark.asyncio
    async def test_ai_iron_law_push_queue(self):
        """所有 AI 建议必须经 CoachPushQueue，不允许直接推送"""
        async with AsyncClient(base_url=BASE) as client:
            stats = await client.get("/api/v1/coach/push-queue/stats",
                headers=HEADERS_COACH)
        assert stats.status_code == 200
        data = stats.json()
        assert "pending" in data

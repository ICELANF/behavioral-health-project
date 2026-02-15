"""
test_incentive_engine.py — 积分激励引擎 单元测试
覆盖: 积分发放(award) / 三维分类 / 每日上限 / 打卡+里程碑 /
      任务完成 / 边界条件
对接: core/incentive_integration.py (PointEngine)
"""
import pytest
from datetime import datetime, timedelta

try:
    from core.incentive_integration import PointEngine, POINT_RULES, PointEventType
    HAS_ENGINE = True
except ImportError:
    HAS_ENGINE = False

pytestmark = pytest.mark.skipif(not HAS_ENGINE, reason="incentive engine not importable")


# =====================================================================
# 1. 积分发放 (award)
# =====================================================================

class TestPointAward:

    def test_award_daily_checkin(self, db, grower):
        """日打卡发放积分"""
        engine = PointEngine(db)
        result = engine.award(grower.id, "daily_checkin")
        assert result["awarded"] is True
        assert result["dimension"] == "growth"
        assert result["points"] == POINT_RULES["daily_checkin"]["points"]

    def test_award_task_complete(self, db, grower):
        """任务完成发放积分"""
        engine = PointEngine(db)
        result = engine.award(grower.id, "task_complete",
                              source_type="task", source_id="t1")
        assert result["awarded"] is True
        assert result["dimension"] == "growth"

    def test_award_share_experience(self, db, sharer):
        """分享经验→contribution"""
        engine = PointEngine(db)
        result = engine.award(sharer.id, "share_experience")
        assert result["awarded"] is True
        assert result["dimension"] == "contribution"

    def test_award_content_create(self, db, sharer):
        """创建内容→contribution"""
        engine = PointEngine(db)
        result = engine.award(sharer.id, "content_create")
        assert result["awarded"] is True
        assert result["dimension"] == "contribution"

    def test_award_recruit_peer(self, db, coach):
        """发展同道者→influence"""
        engine = PointEngine(db)
        result = engine.award(coach.id, "recruit_peer")
        assert result["awarded"] is True
        assert result["dimension"] == "influence"


# =====================================================================
# 2. 三维分类 (成长/贡献/影响)
# =====================================================================

class TestPointCategories:

    def test_growth_events(self):
        """成长类事件归类"""
        growth_events = [k for k, v in POINT_RULES.items()
                         if v["dimension"] == "growth"]
        assert "daily_checkin" in growth_events
        assert "task_complete" in growth_events
        assert "assessment_complete" in growth_events

    def test_contribution_events(self):
        """贡献类事件归类"""
        contrib_events = [k for k, v in POINT_RULES.items()
                          if v["dimension"] == "contribution"]
        assert "share_experience" in contrib_events
        assert "content_create" in contrib_events

    def test_influence_events(self):
        """影响力类事件归类"""
        influence_events = [k for k, v in POINT_RULES.items()
                            if v["dimension"] == "influence"]
        assert "recruit_peer" in influence_events
        assert "mentor_session" in influence_events

    def test_balance_updated(self, db, grower):
        """积分余额正确更新"""
        engine = PointEngine(db)
        result = engine.award(grower.id, "daily_checkin")
        assert result["awarded"] is True
        assert result["new_balance"]["growth"] > 0
        assert result["new_balance"]["total"] > 0


# =====================================================================
# 3. 每日上限
# =====================================================================

class TestDailyCap:

    def test_daily_cap_blocks(self, db, grower):
        """达到每日上限后阻止"""
        engine = PointEngine(db)
        # daily_checkin has daily_cap=10, points=10 → only 1 award
        r1 = engine.award(grower.id, "daily_checkin")
        assert r1["awarded"] is True

        # Second should be blocked (cap=10, already got 10)
        r2 = engine.award(grower.id, "daily_checkin")
        assert r2["awarded"] is False
        assert r2["reason"] == "daily_cap_reached"

    def test_events_without_cap(self):
        """无上限的事件类型"""
        no_cap_events = [k for k, v in POINT_RULES.items()
                         if "daily_cap" not in v]
        assert "stage_upgrade" in no_cap_events
        assert "graduation" not in POINT_RULES  # Not in POINT_RULES


# =====================================================================
# 4. 打卡 + 里程碑
# =====================================================================

class TestCheckinAndMilestones:

    def test_record_checkin(self, db, grower):
        """日打卡记录"""
        engine = PointEngine(db)
        result = engine.record_checkin(grower.id)
        assert result.get("awarded") is True or "streak_days" in result
        assert result["streak_days"] == 1

    def test_double_checkin_blocked(self, db, grower):
        """同日重复打卡阻止"""
        engine = PointEngine(db)
        r1 = engine.record_checkin(grower.id)
        r2 = engine.record_checkin(grower.id)
        assert r2["awarded"] is False
        assert r2["reason"] == "already_checked_in_today"

    def test_record_task_complete(self, db, grower):
        """任务完成记录"""
        engine = PointEngine(db)
        result = engine.record_task_complete(grower.id, "task_001")
        assert result["awarded"] is True


# =====================================================================
# 5. 未知事件类型
# =====================================================================

class TestUnknownEvents:

    def test_unknown_event_type(self, db, grower):
        """未知事件类型"""
        engine = PointEngine(db)
        result = engine.award(grower.id, "nonexistent_event_xyz")
        assert result["awarded"] is False
        assert "unknown event" in result["reason"]


# =====================================================================
# 6. 边界条件
# =====================================================================

class TestIncentiveEdgeCases:

    def test_point_rules_complete(self):
        """POINT_RULES 包含所有事件类型"""
        assert len(POINT_RULES) >= 14  # 14 event types defined

    def test_all_rules_have_dimension(self):
        """每条规则都有 dimension"""
        for event_type, rule in POINT_RULES.items():
            assert "dimension" in rule, f"{event_type} missing dimension"
            assert rule["dimension"] in ("growth", "contribution", "influence")

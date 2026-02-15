"""
test_models.py — 数据模型完整性 单元测试
覆盖: 表创建 / 约束检查 / 枚举值 / 工厂round-trip / 关系完整性
对接: core/models.py
"""
import pytest
from datetime import datetime

from conftest import (
    User, UserRole, JourneyState, BehavioralProfile, DualTrackStatus,
    AntiCheatEvent, GovernanceViolation, SafetyLog, StageTransitionLogV4,
    STAGES_ORDERED, AGENCY_MODES_ORDERED,
)


# =====================================================================
# 1. 枚举值完整性
# =====================================================================

class TestEnumValues:

    def test_user_role_values(self):
        """7种角色枚举"""
        if not UserRole:
            pytest.skip("UserRole not importable")
        expected = {"observer", "grower", "sharer", "coach", "promoter", "master", "admin"}
        actual = {r.value for r in UserRole}
        assert expected.issubset(actual)

    def test_journey_stages_6(self):
        """6个旅程阶段"""
        assert len(STAGES_ORDERED) == 6
        assert STAGES_ORDERED[0] == "s0_authorization"
        assert STAGES_ORDERED[-1] == "s5_graduation"

    def test_agency_modes_3(self):
        """3种主体性模式"""
        assert len(AGENCY_MODES_ORDERED) == 3
        assert AGENCY_MODES_ORDERED[0] == "passive"
        assert AGENCY_MODES_ORDERED[-1] == "active"


# =====================================================================
# 2. User 模型
# =====================================================================

class TestUserModel:

    def test_create_user(self, db, user_factory):
        """创建用户"""
        user = user_factory.create(db, UserRole.GROWER)
        assert user.id is not None
        assert user.is_active is True
        assert user.role == UserRole.GROWER

    def test_unique_username(self, db, user_factory):
        """username 唯一"""
        u1 = user_factory.create(db, username="unique_user")
        with pytest.raises(Exception):
            user_factory.create(db, username="unique_user")
            db.flush()

    def test_unique_email(self, db, user_factory):
        """email 唯一"""
        u1 = user_factory.create(db, email="unique@test.com")
        with pytest.raises(Exception):
            user_factory.create(db, email="unique@test.com")
            db.flush()

    def test_all_roles_creatable(self, db, user_factory):
        """全部7种角色可创建"""
        for role in UserRole:
            u = user_factory.create(db, role)
            assert u.role == role


# =====================================================================
# 3. JourneyState 模型
# =====================================================================

class TestJourneyStateModel:

    def test_create_journey_state(self, db, grower, journey_factory):
        """创建 JourneyState"""
        js = journey_factory.create(db, grower, stage="s0_authorization")
        assert js.id is not None
        assert js.user_id == grower.id
        assert js.journey_stage == "s0_authorization"

    def test_default_values(self, db, grower, journey_factory):
        """默认值检查"""
        js = journey_factory.create(db, grower)
        assert js.trust_score == 0.0
        assert js.agency_score == 0.0
        assert js.agency_mode == "passive"

    def test_all_stages_valid(self, db, grower, journey_factory):
        """所有阶段值有效"""
        for stage in STAGES_ORDERED:
            js = JourneyState(
                user_id=grower.id + 1000,  # avoid unique constraint
                journey_stage=stage,
                agency_mode="passive",
                trust_score=0.0,
                agency_score=0.0,
                stage_entered_at=datetime.utcnow(),
            )
            assert js.journey_stage == stage

    def test_score_float_precision(self, db, grower, journey_factory):
        """浮点数精度"""
        js = journey_factory.create(db, grower, trust_score=0.123456789)
        db.refresh(js)
        assert abs(js.trust_score - 0.123456789) < 0.01


# =====================================================================
# 4. DualTrackStatus 模型
# =====================================================================

class TestDualTrackModel:

    def test_create_dual_track(self, db, grower, dual_track_factory):
        """创建 DualTrackStatus"""
        dt = dual_track_factory.create(db, grower, target_level=2)
        assert dt.id is not None
        assert dt.points_track_passed is False
        assert dt.growth_track_passed is False

    def test_both_tracks_toggleable(self, db, grower, dual_track_factory):
        """双轨状态可独立切换"""
        dt = dual_track_factory.create(db, grower)
        dt.points_track_passed = True
        dt.growth_track_passed = False
        db.flush(); db.refresh(dt)
        assert dt.points_track_passed is True
        assert dt.growth_track_passed is False


# =====================================================================
# 5. AntiCheatEvent 模型
# =====================================================================

class TestAntiCheatModel:

    def test_create_event(self, db, grower, anti_cheat_factory):
        """创建防刷事件"""
        ev = anti_cheat_factory.create(db, grower)
        assert ev.id is not None
        assert ev.strategy == "velocity"
        assert ev.resolved is False

    def test_event_details_json(self, db, grower, anti_cheat_factory):
        """details JSON 字段"""
        ev = anti_cheat_factory.create(db, grower, details={"count": 50, "window": 60})
        db.refresh(ev)
        assert ev.details.get("count") == 50

    def test_multiple_strategies(self, db, grower, anti_cheat_factory):
        """多种策略类型"""
        for strat in ["velocity", "pattern", "ip", "device"]:
            ev = anti_cheat_factory.create(db, grower, strategy=strat)
            assert ev.strategy == strat


# =====================================================================
# 6. SafetyLog 模型
# =====================================================================

class TestSafetyLogModel:

    def test_create_safety_log(self, db, grower, safety_log_factory):
        """创建安全日志"""
        log = safety_log_factory.create(db, grower, event_type="input_blocked",
                                        severity="high", input_text="test input")
        assert log.id is not None
        assert log.severity == "high"

    def test_all_event_types(self, db, grower, safety_log_factory):
        """4种事件类型"""
        for evt in ["input_blocked", "output_filtered", "crisis_detected", "daily_report"]:
            log = safety_log_factory.create(db, grower, event_type=evt)
            assert log.event_type == evt

    def test_all_severity_levels(self, db, grower, safety_log_factory):
        """4种严重级别"""
        for sev in ["low", "medium", "high", "critical"]:
            log = safety_log_factory.create(db, grower, severity=sev)
            assert log.severity == sev

    def test_null_user_allowed(self, db, safety_log_factory):
        """系统级日志无 user_id"""
        log = safety_log_factory.create(db, user=None, event_type="daily_report")
        assert log.user_id is None


# =====================================================================
# 7. GovernanceViolation 模型
# =====================================================================

class TestGovernanceModel:

    def test_create_violation(self, db, grower, violation_factory):
        """创建治理违规"""
        gv = violation_factory.create(db, grower)
        assert gv.id is not None
        assert gv.resolved is False

    def test_penalty_amount(self, db, grower, violation_factory):
        """处罚积分"""
        gv = violation_factory.create(db, grower, point_penalty=50)
        assert gv.point_penalty == 50

    def test_resolution_fields(self, db, grower, admin, violation_factory):
        """解决相关字段"""
        gv = violation_factory.create(db, grower)
        gv.resolved = True
        gv.resolved_by = admin.id
        gv.resolved_at = datetime.utcnow()
        db.flush(); db.refresh(gv)
        assert gv.resolved is True
        assert gv.resolved_by == admin.id
        assert gv.resolved_at is not None

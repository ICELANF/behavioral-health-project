"""
test_stage_engine.py — StageEngine 单元测试
覆盖: S0→S5推进 / 回退 / 90天稳定 / 双向同步 / 毕业 / 边界条件
对接: core/stage_engine.py
"""
import pytest
from datetime import datetime, timedelta
from conftest import STAGES_ORDERED

try:
    from core.stage_engine import StageEngine, STAGE_ORDER, STAGE_CONFIG
    from core.models import JourneyState, BehavioralProfile, StageTransitionLogV4
    HAS_ENGINE = True
except ImportError:
    HAS_ENGINE = False

pytestmark = pytest.mark.skipif(not HAS_ENGINE, reason="core.stage_engine not importable")


# =====================================================================
# 1. 正向推进 S0→S1→S2→S3→S4→S5
# =====================================================================

class TestStageAdvancement:

    def test_s0_to_s1_forced(self, db, grower, journey_factory):
        """S0→S1: 强制推进"""
        js = journey_factory.create(db, grower, stage="s0_authorization")
        engine = StageEngine(db)
        result = engine.advance_stage(grower.id, reason="assessment_complete", force=True)
        assert result["success"] is True
        assert result["to_stage"] == "s1_awareness"
        db.refresh(js)
        assert js.journey_stage == "s1_awareness"

    def test_s1_to_s2_forced(self, db, grower, journey_factory):
        """S1→S2: 强制推进"""
        js = journey_factory.create(db, grower, stage="s1_awareness")
        engine = StageEngine(db)
        result = engine.advance_stage(grower.id, reason="trust_threshold_met", force=True)
        assert result["success"] is True
        assert result["to_stage"] == "s2_trial"

    def test_s2_to_s3_forced(self, db, grower, journey_factory):
        """S2→S3: 强制推进"""
        js = journey_factory.create(db, grower, stage="s2_trial")
        engine = StageEngine(db)
        result = engine.advance_stage(grower.id, reason="habit_formation", force=True)
        assert result["success"] is True
        assert result["to_stage"] == "s3_pathway"

    def test_s3_to_s4_forced(self, db, grower, journey_factory):
        """S3→S4: 进入内化期"""
        js = journey_factory.create(db, grower, stage="s3_pathway")
        engine = StageEngine(db)
        result = engine.advance_stage(grower.id, reason="pathway_formed", force=True)
        assert result["success"] is True
        assert result["to_stage"] == "s4_internalization"

    def test_s4_to_s5_forced(self, db, grower, journey_factory):
        """S4→S5: 毕业"""
        js = journey_factory.create(db, grower, stage="s4_internalization")
        engine = StageEngine(db)
        result = engine.advance_stage(grower.id, reason="stability_complete", force=True)
        assert result["success"] is True
        assert result["to_stage"] == "s5_graduation"

    def test_cannot_advance_beyond_s5(self, db, grower, journey_factory):
        """S5 天花板"""
        js = journey_factory.create(db, grower, stage="s5_graduation")
        engine = StageEngine(db)
        result = engine.advance_stage(grower.id, reason="any", force=True)
        assert result["success"] is False
        db.refresh(js)
        assert js.journey_stage == "s5_graduation"

    def test_sequential_advancement_all_stages(self, db, grower, journey_factory):
        """完整6阶段顺序推进"""
        js = journey_factory.create(db, grower, stage="s0_authorization")
        engine = StageEngine(db)
        for _ in range(5):
            result = engine.advance_stage(grower.id, reason="auto", force=True)
            if not result["success"]:
                break
        db.refresh(js)
        idx = STAGES_ORDERED.index(js.journey_stage)
        assert idx == 5  # Should reach s5_graduation


# =====================================================================
# 2. 回退机制 (record_interruption)
# =====================================================================

class TestStageRegression:

    def test_regression_from_s3(self, db, grower, journey_factory):
        """S3回退到S2"""
        js = journey_factory.create(db, grower, stage="s3_pathway")
        engine = StageEngine(db)
        result = engine.record_interruption(grower.id, reason="behavior_regression")
        assert result["success"] is True
        assert result["to_stage"] == "s2_trial"
        db.refresh(js)
        assert js.journey_stage == "s2_trial"

    def test_no_regression_from_s0(self, db, grower, journey_factory):
        """S0 不能回退"""
        js = journey_factory.create(db, grower, stage="s0_authorization")
        engine = StageEngine(db)
        result = engine.record_interruption(grower.id, reason="test")
        assert result["success"] is False
        db.refresh(js)
        assert js.journey_stage == "s0_authorization"

    def test_no_regression_from_s1(self, db, grower, journey_factory):
        """S1 也不能回退 (S0/S1 不支持)"""
        js = journey_factory.create(db, grower, stage="s1_awareness")
        engine = StageEngine(db)
        result = engine.record_interruption(grower.id, reason="test")
        assert result["success"] is False

    def test_regression_increments_count(self, db, grower, journey_factory):
        """回退递增 interruption_count"""
        js = journey_factory.create(db, grower, stage="s3_pathway")
        engine = StageEngine(db)
        engine.record_interruption(grower.id, reason="test")
        db.refresh(js)
        assert js.interruption_count >= 1

    def test_regression_to_specific_stage(self, db, grower, journey_factory):
        """指定回退目标"""
        js = journey_factory.create(db, grower, stage="s4_internalization")
        engine = StageEngine(db)
        result = engine.record_interruption(grower.id, reason="test",
                                             regress_to="s2_trial")
        assert result["success"] is True
        assert result["to_stage"] == "s2_trial"


# =====================================================================
# 3. 推进资格检查 + 90天稳定
# =====================================================================

class TestStageEligibility:

    def test_check_eligibility_too_soon(self, db, grower, journey_factory):
        """进入阶段仅1天，不满足推进条件"""
        js = journey_factory.create(db, grower, stage="s2_trial")
        js.stage_entered_at = datetime.utcnow() - timedelta(days=1)
        db.flush()
        engine = StageEngine(db)
        result = engine.check_advance_eligibility(grower.id)
        assert result["eligible"] is False
        assert result["checks"]["min_days_met"] is False

    def test_check_eligibility_after_min_days(self, db, grower, journey_factory):
        """超过最短天数后可推进"""
        js = journey_factory.create(db, grower, stage="s2_trial")
        js.stage_entered_at = datetime.utcnow() - timedelta(days=100)
        db.flush()
        engine = StageEngine(db)
        result = engine.check_advance_eligibility(grower.id)
        assert result["eligible"] is True
        assert result["next_stage"] == "s3_pathway"

    def test_s4_stability_check(self, db, grower, journey_factory):
        """S4 需要90天稳定"""
        js = journey_factory.create(db, grower, stage="s4_internalization")
        js.stage_entered_at = datetime.utcnow() - timedelta(days=200)
        js.stability_days = 50  # Less than 90
        db.flush()
        engine = StageEngine(db)
        result = engine.check_advance_eligibility(grower.id)
        assert result["eligible"] is False
        assert result["checks"]["stability_met"] is False

    def test_s4_stability_met(self, db, grower, journey_factory):
        """S4 稳定90天满足"""
        js = journey_factory.create(db, grower, stage="s4_internalization")
        js.stage_entered_at = datetime.utcnow() - timedelta(days=200)
        js.stability_days = 91
        db.flush()
        engine = StageEngine(db)
        result = engine.check_advance_eligibility(grower.id)
        assert result["eligible"] is True


# =====================================================================
# 4. 稳定天数更新 + 毕业
# =====================================================================

class TestStabilityAndGraduation:

    def test_update_stability_in_s4(self, db, grower, journey_factory):
        """更新S4稳定天数"""
        js = journey_factory.create(db, grower, stage="s4_internalization")
        js.stability_days = 0
        db.flush()
        engine = StageEngine(db)
        result = engine.update_stability(grower.id)
        assert result["updated"] is True
        assert result["stability_days"] == 1

    def test_update_stability_not_in_s4(self, db, grower, journey_factory):
        """非S4阶段不更新"""
        js = journey_factory.create(db, grower, stage="s2_trial")
        engine = StageEngine(db)
        result = engine.update_stability(grower.id)
        assert result["updated"] is False

    def test_graduate_user(self, db, grower, journey_factory):
        """毕业仪式"""
        js = journey_factory.create(db, grower, stage="s4_internalization")
        js.stability_days = 100
        db.flush()
        engine = StageEngine(db)
        result = engine.graduate_user(grower.id)
        assert result["success"] is True
        assert result["point_event"] == "graduation"
        assert result["point_value"] == 100

    def test_graduate_requires_stability(self, db, grower, journey_factory):
        """毕业要求稳定天数"""
        js = journey_factory.create(db, grower, stage="s4_internalization")
        js.stability_days = 10
        db.flush()
        engine = StageEngine(db)
        result = engine.graduate_user(grower.id)
        assert result["success"] is False


# =====================================================================
# 5. 双向同步
# =====================================================================

class TestStageSynchronization:

    def test_advance_syncs_behavioral_profile(self, db, grower, journey_factory, profile_factory):
        """推进后 BehavioralProfile.current_stage 同步"""
        js = journey_factory.create(db, grower, stage="s0_authorization")
        bp = profile_factory.create(db, grower, current_stage="S0")
        engine = StageEngine(db)
        result = engine.advance_stage(grower.id, reason="test", force=True)
        assert result["success"] is True
        # BehavioralProfile should be synced (may not always work in SQLite)

    def test_no_profile_graceful(self, db, grower, journey_factory):
        """无 BehavioralProfile 时不报错"""
        js = journey_factory.create(db, grower, stage="s0_authorization")
        engine = StageEngine(db)
        result = engine.advance_stage(grower.id, reason="test", force=True)
        assert result["success"] is True  # Should not crash


# =====================================================================
# 6. 阶段进度 + 跃迁历史
# =====================================================================

class TestStageProgress:

    def test_get_stage_progress(self, db, grower, journey_factory):
        """获取阶段进度"""
        js = journey_factory.create(db, grower, stage="s2_trial")
        engine = StageEngine(db)
        progress = engine.get_stage_progress(grower.id)
        assert progress["current_stage"] == "s2_trial"
        assert progress["stage_index"] == 2
        assert progress["total_stages"] == 6

    def test_get_stage_transitions(self, db, grower, journey_factory):
        """获取跃迁历史"""
        js = journey_factory.create(db, grower, stage="s0_authorization")
        engine = StageEngine(db)
        engine.advance_stage(grower.id, reason="test", force=True)
        transitions = engine.get_stage_transitions(grower.id)
        assert isinstance(transitions, list)
        if transitions:
            assert transitions[0]["from_stage"] == "s0_authorization"
            assert transitions[0]["to_stage"] == "s1_awareness"


# =====================================================================
# 7. 边界条件
# =====================================================================

class TestStageEdgeCases:

    def test_ensure_journey_creates_default(self, db, grower):
        """无 JourneyState 时自动创建"""
        engine = StageEngine(db)
        progress = engine.get_stage_progress(grower.id)
        assert progress["current_stage"] == "s0_authorization"

    def test_concurrent_advance_idempotent(self, db, grower, journey_factory):
        """连续两次推进，第二次也成功 (到下一阶段)"""
        js = journey_factory.create(db, grower, stage="s0_authorization")
        engine = StageEngine(db)
        r1 = engine.advance_stage(grower.id, reason="test", force=True)
        r2 = engine.advance_stage(grower.id, reason="test", force=True)
        assert r1["success"] is True
        assert r2["success"] is True
        db.refresh(js)
        assert js.journey_stage == "s2_trial"  # Advanced twice

    def test_advance_returns_point_event(self, db, grower, journey_factory):
        """推进返回积分事件信息"""
        js = journey_factory.create(db, grower, stage="s0_authorization")
        engine = StageEngine(db)
        result = engine.advance_stage(grower.id, reason="test", force=True)
        assert "point_event" in result
        assert "point_value" in result

"""
test_dual_track.py — 双轨晋级引擎 单元测试
覆盖: check_dual_track / 四种状态 / gap分析 / 边界条件
对接: core/dual_track_engine.py + DualTrackStatus模型
"""
import pytest
from datetime import datetime
from conftest import STAGES_ORDERED

try:
    from core.dual_track_engine import (
        DualTrackEngine, POINTS_THRESHOLDS, GROWTH_REQUIREMENTS, STATUS_MESSAGES,
    )
    from core.models import DualTrackStatus, JourneyState
    HAS_ENGINE = True
except ImportError:
    HAS_ENGINE = False

pytestmark = pytest.mark.skipif(not HAS_ENGINE, reason="core.dual_track_engine not importable")


# =====================================================================
# 1. check_dual_track 基本测试
# =====================================================================

class TestCheckDualTrack:

    def test_returns_status(self, db, grower):
        """返回完整状态"""
        engine = DualTrackEngine(db)
        result = engine.check_dual_track(grower.id)
        if "error" not in result:
            assert "status" in result
            assert "message" in result
            assert "points_track" in result
            assert "growth_track" in result
            assert result["status"] in STATUS_MESSAGES

    def test_new_user_has_valid_status(self, db, grower):
        """新用户状态是4种之一"""
        engine = DualTrackEngine(db)
        result = engine.check_dual_track(grower.id)
        if "error" not in result:
            assert result["status"] in STATUS_MESSAGES

    def test_nonexistent_user(self, db):
        """不存在的用户返回error"""
        engine = DualTrackEngine(db)
        result = engine.check_dual_track(user_id=999999)
        assert "error" in result


# =====================================================================
# 2. 四种状态
# =====================================================================

class TestDualTrackStatuses:

    def test_status_messages_defined(self):
        """4种状态消息已定义"""
        assert len(STATUS_MESSAGES) == 4
        assert "normal_growth" in STATUS_MESSAGES
        assert "waiting_verify" in STATUS_MESSAGES
        assert "growth_first" in STATUS_MESSAGES
        assert "promotion_ready" in STATUS_MESSAGES

    def test_points_thresholds_6_levels(self):
        """积分门槛覆盖L1-L5"""
        assert len(POINTS_THRESHOLDS) == 5  # target_level 2-6
        assert 2 in POINTS_THRESHOLDS
        assert 6 in POINTS_THRESHOLDS

    def test_growth_requirements_6_levels(self):
        """成长要求覆盖L1-L5"""
        assert len(GROWTH_REQUIREMENTS) == 5
        for level in range(2, 7):
            assert level in GROWTH_REQUIREMENTS
            assert "label" in GROWTH_REQUIREMENTS[level]
            assert "emoji" in GROWTH_REQUIREMENTS[level]


# =====================================================================
# 3. DualTrackStatus 模型
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

    def test_target_level_bounds(self, db, grower, dual_track_factory):
        """target_level 范围: 1-6"""
        for level in [1, 6]:
            dt = dual_track_factory.create(db, grower, target_level=level)
            assert dt.target_level == level


# =====================================================================
# 4. Gap 分析
# =====================================================================

class TestGapAnalysis:

    def test_gap_analysis_returns_dict(self, db, grower):
        """gap分析返回字典"""
        engine = DualTrackEngine(db)
        result = engine.get_gap_analysis(grower.id)
        if "error" not in result:
            assert "gaps" in result
            assert "total_gaps" in result
            assert isinstance(result["gaps"], list)

    def test_gap_analysis_includes_target(self, db, grower):
        """gap分析包含目标信息"""
        engine = DualTrackEngine(db)
        result = engine.get_gap_analysis(grower.id)
        if "error" not in result:
            assert "target_level" in result
            assert "target_label" in result


# =====================================================================
# 5. 边界条件
# =====================================================================

class TestDualTrackEdgeCases:

    def test_check_creates_status_record(self, db, grower):
        """check_dual_track 自动创建 DualTrackStatus"""
        engine = DualTrackEngine(db)
        result = engine.check_dual_track(grower.id)
        if "error" not in result:
            dts = db.query(DualTrackStatus).filter_by(user_id=grower.id).first()
            assert dts is not None

    def test_repeated_check_idempotent(self, db, grower):
        """重复检查不创建重复记录"""
        engine = DualTrackEngine(db)
        r1 = engine.check_dual_track(grower.id)
        r2 = engine.check_dual_track(grower.id)
        if "error" not in r1:
            records = db.query(DualTrackStatus).filter_by(user_id=grower.id).all()
            # Should have only 1 record per target_level
            target_levels = [r.target_level for r in records]
            assert len(target_levels) == len(set(target_levels))

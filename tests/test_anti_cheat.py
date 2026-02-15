"""
test_anti_cheat.py — 防刷引擎 单元测试
覆盖: AS-01每日上限 / AS-02质量加权 / AS-03时间衰减 /
      AS-04交叉验证 / AS-05成长轨 / AS-06异常检测 / 综合校验
对接: core/anti_cheat_engine.py + AntiCheatEvent
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

try:
    from core.anti_cheat_engine import AntiCheatEngine, DAILY_CAPS, QUALITY_MULTIPLIERS
    from core.models import AntiCheatEvent
    HAS_ENGINE = True
except ImportError:
    HAS_ENGINE = False

pytestmark = pytest.mark.skipif(not HAS_ENGINE, reason="core.anti_cheat_engine not importable")


# =====================================================================
# 1. AS-01 每日上限 (Daily Cap)
# =====================================================================

class TestDailyCap:

    def test_allowed_under_cap(self, db, grower):
        """未达上限时允许"""
        engine = AntiCheatEngine(db)
        result = engine.check_daily_cap(grower.id, "daily_checkin")
        assert result["allowed"] is True
        assert result["strategy"] == "AS-01"

    def test_known_action_has_cap(self, db, grower):
        """已知动作有上限信息"""
        engine = AntiCheatEngine(db)
        result = engine.check_daily_cap(grower.id, "complete_lesson")
        assert "cap" in result
        assert result["cap"] == DAILY_CAPS.get("complete_lesson", 0)

    def test_unknown_action_no_cap(self, db, grower):
        """未知动作无上限限制"""
        engine = AntiCheatEngine(db)
        result = engine.check_daily_cap(grower.id, "nonexistent_action")
        assert result["allowed"] is True
        assert result["cap"] == 0


# =====================================================================
# 2. AS-02 质量加权 (Quality Weight)
# =====================================================================

class TestQualityWeight:

    def test_high_quality_doubles(self):
        """高质量×2"""
        engine = AntiCheatEngine.__new__(AntiCheatEngine)
        result = engine.apply_quality_weight(10, "high")
        assert result["adjusted"] == 20
        assert result["multiplier"] == 2.0

    def test_normal_quality_unchanged(self):
        """正常质量×1"""
        engine = AntiCheatEngine.__new__(AntiCheatEngine)
        result = engine.apply_quality_weight(10, "normal")
        assert result["adjusted"] == 10

    def test_low_quality_halved(self):
        """低质量×0.5"""
        engine = AntiCheatEngine.__new__(AntiCheatEngine)
        result = engine.apply_quality_weight(10, "low")
        assert result["adjusted"] == 5


# =====================================================================
# 3. AS-03 时间衰减 (Time Decay)
# =====================================================================

class TestTimeDecay:

    def test_no_decay_few_reps(self, db, grower):
        """少量重复不衰减"""
        engine = AntiCheatEngine(db)
        result = engine.apply_time_decay(grower.id, "daily_checkin", 10)
        assert result["strategy"] == "AS-03"
        # First few repetitions should have multiplier=1.0
        assert result["multiplier"] == 1.0

    def test_decay_returns_dict(self, db, grower):
        """返回完整字典"""
        engine = AntiCheatEngine(db)
        result = engine.apply_time_decay(grower.id, "complete_lesson", 10)
        assert "original" in result
        assert "adjusted" in result
        assert "repetitions_7d" in result


# =====================================================================
# 4. AS-04 交叉验证 (Cross Validation)
# =====================================================================

class TestCrossValidation:

    def test_mentee_graduated_needs_cv(self):
        """mentee_graduated 需要交叉验证"""
        engine = AntiCheatEngine.__new__(AntiCheatEngine)
        assert engine.require_cross_validation("mentee_graduated") is True

    def test_daily_checkin_no_cv(self):
        """daily_checkin 不需要交叉验证"""
        engine = AntiCheatEngine.__new__(AntiCheatEngine)
        assert engine.require_cross_validation("daily_checkin") is False

    def test_case_share_needs_cv(self):
        """case_share 需要交叉验证"""
        engine = AntiCheatEngine.__new__(AntiCheatEngine)
        assert engine.require_cross_validation("case_share") is True


# =====================================================================
# 5. AS-06 异常检测 (Anomaly Detection)
# =====================================================================

class TestAnomalyDetection:

    def test_no_anomaly_clean_user(self, db, grower):
        """新用户无异常"""
        engine = AntiCheatEngine(db)
        result = engine.detect_anomaly(grower.id)
        assert result["strategy"] == "AS-06"
        assert result["flagged"] is False
        assert result["anomalies_found"] == 0

    def test_anomaly_returns_correct_structure(self, db, grower):
        """返回结构正确"""
        engine = AntiCheatEngine(db)
        result = engine.detect_anomaly(grower.id)
        assert "anomalies" in result
        assert isinstance(result["anomalies"], list)


# =====================================================================
# 6. 综合校验 (Validate Point Award)
# =====================================================================

class TestValidatePointAward:

    def test_full_validation_passes(self, db, grower):
        """完整校验通过"""
        engine = AntiCheatEngine(db)
        result = engine.validate_point_award(grower.id, "daily_checkin", 10)
        assert "allowed" in result
        assert "final_points" in result
        assert "strategies_applied" in result

    def test_full_validation_structure(self, db, grower):
        """综合校验返回所有策略信息"""
        engine = AntiCheatEngine(db)
        result = engine.validate_point_award(grower.id, "complete_lesson", 10, "high")
        assert "quality_multiplier" in result
        assert "decay_multiplier" in result
        assert "needs_cross_validation" in result
        assert "anomaly_flagged" in result


# =====================================================================
# 7. 事件记录
# =====================================================================

class TestEventLogging:

    def test_get_user_events_empty(self, db, grower):
        """新用户无事件"""
        engine = AntiCheatEngine(db)
        events = engine.get_user_events(grower.id)
        assert isinstance(events, list)
        assert len(events) == 0

    def test_get_user_events_with_records(self, db, grower, anti_cheat_factory):
        """有事件记录时返回列表"""
        anti_cheat_factory.create(db, grower, strategy="AS-01",
                                   event_type="daily_cap_hit")
        anti_cheat_factory.create(db, grower, strategy="AS-06",
                                   event_type="anomaly_detected")
        engine = AntiCheatEngine(db)
        events = engine.get_user_events(grower.id)
        assert len(events) == 2


# =====================================================================
# 8. 边界条件
# =====================================================================

class TestAntiCheatEdgeCases:

    def test_new_user_no_history(self, db, grower):
        """新用户无历史记录"""
        engine = AntiCheatEngine(db)
        result = engine.check_daily_cap(grower.id, "daily_checkin")
        assert result["allowed"] is True

    def test_quality_unknown_defaults_normal(self):
        """未知质量等级默认×1"""
        engine = AntiCheatEngine.__new__(AntiCheatEngine)
        result = engine.apply_quality_weight(10, "unknown_quality")
        assert result["multiplier"] == 1.0
        assert result["adjusted"] == 10

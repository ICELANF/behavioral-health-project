"""
test_trust_score.py — 信任评分服务 单元测试
覆盖: score计算 / 信号权重 / update持久化 / 信任级别 /
      Observer激活 / 日志记录 / 边界条件
对接: core/trust_score_service.py + TrustScoreLog
"""
import pytest
from datetime import datetime, timedelta

try:
    from core.trust_score_service import (
        TrustScoreService, TRUST_SIGNALS, score_to_trust_level,
        TRUST_LEVEL_BEHAVIOR,
    )
    HAS_SERVICE = True
except ImportError:
    HAS_SERVICE = False

from conftest import JourneyState, TrustScoreLog

pytestmark = pytest.mark.skipif(not HAS_SERVICE, reason="core.trust_score_service not importable")


# =====================================================================
# 1. 信任分计算 (compute_trust_score)
# =====================================================================

class TestTrustComputation:

    def test_zero_signals_zero_score(self, db, grower, journey_factory):
        """无信号→0分"""
        js = journey_factory.create(db, grower, trust_score=0.0)
        svc = TrustScoreService(db)
        result = svc.compute_trust_score(grower.id, signals={})
        assert result["score"] == 0.0
        assert result["level"] == "not_established"

    def test_full_signals_high_score(self, db, grower, journey_factory):
        """全信号满分→高分"""
        js = journey_factory.create(db, grower, trust_score=0.0)
        svc = TrustScoreService(db)
        signals = {k: 1.0 for k in TRUST_SIGNALS}
        result = svc.compute_trust_score(grower.id, signals=signals)
        assert result["score"] == 1.0
        assert result["level"] == "established"

    def test_partial_signals(self, db, grower, journey_factory):
        """部分信号"""
        js = journey_factory.create(db, grower, trust_score=0.0)
        svc = TrustScoreService(db)
        signals = {"dialog_depth": 0.8, "proactive_return_rate": 0.6}
        result = svc.compute_trust_score(grower.id, signals=signals)
        assert 0.0 < result["score"] < 1.0

    def test_score_range_0_to_1(self, db, grower, journey_factory):
        """信任分始终在 [0, 1]"""
        svc = TrustScoreService(db)
        # Overflow signals
        signals = {k: 10.0 for k in TRUST_SIGNALS}
        result = svc.compute_trust_score(grower.id, signals=signals)
        assert 0.0 <= result["score"] <= 1.0

    def test_result_contains_details(self, db, grower, journey_factory):
        """结果包含信号详情"""
        svc = TrustScoreService(db)
        signals = {"dialog_depth": 0.5}
        result = svc.compute_trust_score(grower.id, signals=signals)
        assert "signals" in result
        assert "dialog_depth" in result["signals"]
        assert result["signals"]["dialog_depth"]["weight"] == 0.25


# =====================================================================
# 2. 信号权重
# =====================================================================

class TestSignalWeights:

    def test_six_signals_defined(self):
        """6种信号权重"""
        assert len(TRUST_SIGNALS) == 6

    def test_weights_sum_to_1(self):
        """权重总和=1.0"""
        total = sum(TRUST_SIGNALS.values())
        assert abs(total - 1.0) < 0.001

    def test_dialog_depth_highest(self):
        """dialog_depth 权重最高(0.25)"""
        max_signal = max(TRUST_SIGNALS, key=TRUST_SIGNALS.get)
        assert max_signal == "dialog_depth"
        assert TRUST_SIGNALS["dialog_depth"] == 0.25


# =====================================================================
# 3. update_user_trust (持久化)
# =====================================================================

class TestTrustUpdate:

    def test_update_persists_score(self, db, grower, journey_factory):
        """update_user_trust 持久化分数"""
        js = journey_factory.create(db, grower, trust_score=0.0)
        svc = TrustScoreService(db)
        signals = {"dialog_depth": 0.8, "proactive_return_rate": 0.6}
        result = svc.update_user_trust(grower.id, signals=signals)
        db.refresh(js)
        assert js.trust_score == result["score"]
        assert js.trust_score > 0.0

    def test_update_creates_logs(self, db, grower, journey_factory):
        """update_user_trust 写入日志"""
        js = journey_factory.create(db, grower, trust_score=0.0)
        svc = TrustScoreService(db)
        signals = {"dialog_depth": 0.5}
        svc.update_user_trust(grower.id, signals=signals)
        if TrustScoreLog:
            logs = db.query(TrustScoreLog).filter_by(user_id=grower.id).all()
            assert len(logs) >= 1

    def test_update_without_journey_creates_one(self, db, grower):
        """无 JourneyState 时自动创建"""
        svc = TrustScoreService(db)
        signals = {"dialog_depth": 0.5}
        result = svc.update_user_trust(grower.id, signals=signals)
        assert result["score"] > 0.0
        # Should have created a JourneyState
        js = db.query(JourneyState).filter_by(user_id=grower.id).first()
        assert js is not None


# =====================================================================
# 4. 信任级别 + Agent行为
# =====================================================================

class TestTrustLevels:

    def test_level_not_established(self):
        """<0.3 → not_established"""
        assert score_to_trust_level(0.1) == "not_established"

    def test_level_building(self):
        """0.3-0.5 → building"""
        assert score_to_trust_level(0.4) == "building"

    def test_level_established(self):
        """>0.5 → established"""
        assert score_to_trust_level(0.8) == "established"

    def test_get_trust_behavior(self, db, grower, journey_factory):
        """get_trust_behavior 返回行为规则"""
        js = journey_factory.create(db, grower, trust_score=0.7)
        svc = TrustScoreService(db)
        result = svc.get_trust_behavior(grower.id)
        assert result["trust_level"] == "established"
        assert result["allow_deep_intervention"] is True

    def test_trust_behavior_not_established(self, db, grower, journey_factory):
        """低信任→不允许深度干预"""
        js = journey_factory.create(db, grower, trust_score=0.1)
        svc = TrustScoreService(db)
        result = svc.get_trust_behavior(grower.id)
        assert result["trust_level"] == "not_established"
        assert result["allow_deep_intervention"] is False
        assert result["allow_assessment"] is False


# =====================================================================
# 5. Observer 激活检查
# =====================================================================

class TestObserverActivation:

    def test_check_activation_no_journey(self, db, grower):
        """无 JourneyState → 不激活"""
        svc = TrustScoreService(db)
        result = svc.check_observer_activation(grower.id)
        assert result["eligible"] is False

    def test_check_activation_paths(self, db, grower, journey_factory):
        """3条激活路径结构正确"""
        js = journey_factory.create(db, grower, trust_score=0.5)
        svc = TrustScoreService(db)
        result = svc.check_observer_activation(grower.id)
        assert "paths" in result
        assert "A_curiosity" in result["paths"]
        assert "B_time" in result["paths"]
        assert "C_coach_referred" in result["paths"]


# =====================================================================
# 6. 边界条件
# =====================================================================

class TestTrustEdgeCases:

    def test_no_journey_state_behavior(self, db, grower):
        """无 JourneyState → 默认行为"""
        svc = TrustScoreService(db)
        result = svc.get_trust_behavior(grower.id)
        assert result["trust_score"] == 0.0
        assert result["trust_level"] == "not_established"

    def test_negative_signal_clamped(self, db, grower, journey_factory):
        """负信号值被钳制到0"""
        svc = TrustScoreService(db)
        signals = {"dialog_depth": -1.0}
        result = svc.compute_trust_score(grower.id, signals=signals)
        assert result["signals"]["dialog_depth"]["value"] == 0.0

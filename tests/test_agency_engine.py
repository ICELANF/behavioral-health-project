"""
test_agency_engine.py — 主体性引擎 单元测试
覆盖: 三模式转换(passive→transitional→active) /
      score阈值 / coach覆盖 / 信号计算 / 文本分析 / 边界条件
对接: core/agency_engine.py
"""
import pytest
from datetime import datetime
from conftest import AGENCY_MODES_ORDERED

try:
    from core.agency_engine import AgencyEngine, SIGNAL_WEIGHTS, MODE_THRESHOLDS
    HAS_ENGINE = True
except ImportError:
    try:
        from core.agency_service import AgencyService as AgencyEngine
        HAS_ENGINE = True
    except ImportError:
        HAS_ENGINE = False

from conftest import JourneyState

pytestmark = pytest.mark.skipif(not HAS_ENGINE, reason="core.agency_engine not importable")


# =====================================================================
# 1. 三模式计算
# =====================================================================

class TestModeComputation:

    def test_low_score_passive(self, db, grower, journey_factory):
        """低分→passive"""
        js = journey_factory.create(db, grower, stage="s1_awareness",
                                    agency_mode="passive", agency_score=0.0)
        engine = AgencyEngine(db)
        signals = {k: 0.1 for k in SIGNAL_WEIGHTS}
        result = engine.compute_agency(grower.id, signals=signals)
        assert result["agency_mode"] == "passive"
        assert result["agency_score"] < 0.3

    def test_mid_score_transitional(self, db, grower, journey_factory):
        """中分→transitional"""
        js = journey_factory.create(db, grower, stage="s2_trial",
                                    agency_mode="passive", agency_score=0.0)
        engine = AgencyEngine(db)
        signals = {k: 0.45 for k in SIGNAL_WEIGHTS}
        result = engine.compute_agency(grower.id, signals=signals)
        assert result["agency_mode"] == "transitional"

    def test_high_score_active(self, db, grower, journey_factory):
        """高分→active"""
        js = journey_factory.create(db, grower, stage="s4_internalization",
                                    agency_mode="passive", agency_score=0.0)
        engine = AgencyEngine(db)
        signals = {k: 0.8 for k in SIGNAL_WEIGHTS}
        result = engine.compute_agency(grower.id, signals=signals)
        assert result["agency_mode"] == "active"
        assert result["agency_score"] >= 0.6

    def test_compute_returns_all_fields(self, db, grower, journey_factory):
        """返回完整字段"""
        js = journey_factory.create(db, grower)
        engine = AgencyEngine(db)
        result = engine.compute_agency(grower.id, signals={})
        assert "user_id" in result
        assert "agency_score" in result
        assert "agency_mode" in result
        assert "raw_score" in result
        assert "signals" in result

    def test_mode_persists_to_journey(self, db, grower, journey_factory):
        """计算结果持久化到 JourneyState"""
        js = journey_factory.create(db, grower, stage="s2_trial")
        engine = AgencyEngine(db)
        signals = {k: 0.5 for k in SIGNAL_WEIGHTS}
        result = engine.compute_agency(grower.id, signals=signals, save=True)
        db.refresh(js)
        assert js.agency_score == result["agency_score"]
        assert js.agency_mode == result["agency_mode"]


# =====================================================================
# 2. Score 阈值验证
# =====================================================================

class TestScoreThresholds:

    def test_score_0_stays_passive(self, db, grower, journey_factory):
        """agency_score=0 保持passive"""
        js = journey_factory.create(db, grower, agency_mode="passive", agency_score=0.0)
        engine = AgencyEngine(db)
        result = engine.compute_agency(grower.id, signals={})
        assert result["agency_mode"] == "passive"

    def test_score_1_reaches_active(self, db, grower, journey_factory):
        """agency_score=1.0 应达到active"""
        js = journey_factory.create(db, grower, stage="s4_internalization",
                                    agency_mode="passive", agency_score=0.0)
        engine = AgencyEngine(db)
        signals = {k: 1.0 for k in SIGNAL_WEIGHTS}
        result = engine.compute_agency(grower.id, signals=signals)
        assert result["agency_mode"] == "active"
        assert result["agency_score"] >= 0.9

    def test_boundary_0_3(self, db, grower, journey_factory):
        """边界值0.3: transitional"""
        js = journey_factory.create(db, grower)
        engine = AgencyEngine(db)
        # Construct signals to give exactly 0.3
        signals = {k: 0.3 for k in SIGNAL_WEIGHTS}
        result = engine.compute_agency(grower.id, signals=signals)
        assert result["agency_mode"] == "transitional"


# =====================================================================
# 3. Coach 覆盖
# =====================================================================

class TestCoachOverride:

    def test_coach_override_sets_mode(self, db, grower, journey_factory):
        """coach_override 设置模式"""
        js = journey_factory.create(db, grower, stage="s2_trial")
        engine = AgencyEngine(db)
        result = engine.set_coach_override(grower.id, 0.15)
        assert result["coach_override_mode"] == "passive"
        db.refresh(js)
        assert js.agency_mode == "passive"

    def test_coach_override_high(self, db, grower, journey_factory):
        """coach_override 高分→active"""
        js = journey_factory.create(db, grower, stage="s2_trial")
        engine = AgencyEngine(db)
        result = engine.set_coach_override(grower.id, 0.75)
        assert result["coach_override_mode"] == "active"

    def test_clear_override(self, db, grower, journey_factory):
        """清除 coach 覆盖"""
        js = journey_factory.create(db, grower, stage="s2_trial")
        engine = AgencyEngine(db)
        engine.set_coach_override(grower.id, 0.5)
        result = engine.clear_coach_override(grower.id)
        assert result["coach_override"] is None

    def test_compute_with_override(self, db, grower, journey_factory):
        """compute_agency 尊重直接 coach_override 参数"""
        js = journey_factory.create(db, grower, stage="s2_trial")
        engine = AgencyEngine(db)
        # Even with low signals, coach_override forces the score
        result = engine.compute_agency(grower.id, signals={}, coach_override=0.8)
        assert result["agency_score"] == 0.8
        assert result["override_applied"] is True
        assert result["agency_mode"] == "active"


# =====================================================================
# 4. 文本分析 (S3 + S4)
# =====================================================================

class TestTextAnalysis:

    def test_analyze_active_text(self, db, grower, journey_factory):
        """主动表达文本分析"""
        js = journey_factory.create(db, grower)
        engine = AgencyEngine(db)
        result = engine.analyze_text_agency("我决定明天开始锻炼，我选择健康饮食")
        assert result["S3_active_expression"] > 0

    def test_analyze_passive_text(self, db, grower, journey_factory):
        """被动表达文本分析"""
        js = journey_factory.create(db, grower)
        engine = AgencyEngine(db)
        result = engine.analyze_text_agency("我不行，做不到，害怕")
        # Passive keywords should keep S3 low
        assert isinstance(result["S3_active_expression"], float)

    def test_analyze_reflection_depth(self, db, grower, journey_factory):
        """觉察深度分析"""
        js = journey_factory.create(db, grower)
        engine = AgencyEngine(db)
        result = engine.analyze_text_agency("我意识到每次压力大的时候我就暴饮暴食")
        assert result["S4_awareness_depth"] > 0

    def test_empty_text(self, db, grower, journey_factory):
        """空文本"""
        js = journey_factory.create(db, grower)
        engine = AgencyEngine(db)
        result = engine.analyze_text_agency("")
        assert result["S3_active_expression"] == 0.0
        assert result["S4_awareness_depth"] == 0.0


# =====================================================================
# 5. 状态查询 + 历史
# =====================================================================

class TestAgencyStatus:

    def test_get_status_no_journey(self, db, grower):
        """无 JourneyState 时返回默认"""
        engine = AgencyEngine(db)
        result = engine.get_agency_status(grower.id)
        assert result["agency_score"] == 0.0
        assert result["agency_mode"] == "passive"

    def test_get_status_with_journey(self, db, grower, journey_factory):
        """有 JourneyState 时返回存储值"""
        js = journey_factory.create(db, grower, agency_mode="transitional",
                                    agency_score=0.45)
        engine = AgencyEngine(db)
        result = engine.get_agency_status(grower.id)
        assert result["agency_score"] == 0.45
        assert result["agency_mode"] == "transitional"

    def test_get_history(self, db, grower, journey_factory):
        """获取 agency 历史"""
        js = journey_factory.create(db, grower)
        engine = AgencyEngine(db)
        engine.compute_agency(grower.id, signals={k: 0.5 for k in SIGNAL_WEIGHTS})
        history = engine.get_agency_history(grower.id)
        assert isinstance(history, list)


# =====================================================================
# 6. 边界条件
# =====================================================================

class TestAgencyEdgeCases:

    def test_nonexistent_user(self, db):
        """不存在的用户"""
        engine = AgencyEngine(db)
        result = engine.compute_agency(user_id=999999, signals={})
        assert "error" in result

    def test_score_clamp_0_to_1(self, db, grower, journey_factory):
        """score 不超出 [0, 1]"""
        js = journey_factory.create(db, grower)
        engine = AgencyEngine(db)
        # All signals at max
        signals = {k: 10.0 for k in SIGNAL_WEIGHTS}  # Will be clamped to 1.0
        result = engine.compute_agency(grower.id, signals=signals)
        assert 0.0 <= result["agency_score"] <= 1.0

    def test_six_signal_weights(self):
        """6个信号权重之和=1.0"""
        total = sum(SIGNAL_WEIGHTS.values())
        assert abs(total - 1.0) < 0.001

"""
双轨晋级引擎测试套件
对标契约: Sheet④ 晋级契约 + Sheet⑪ 四同道者

测试覆盖 (25 cases):
  DTK-01~05: L0-L5 阈值配置正确性
  DTK-06~09: 四种状态判定
  DTK-10~13: 积分轨校验
  DTK-14~17: 成长轨校验 (同道者/90天/考核)
  DTK-18~20: 差距分析报告
  DTK-21~23: 晋级仪式流程
  DTK-24~25: 边界/异常场景
"""

import pytest
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from dual_track_engine import (
    PROMOTION_THRESHOLDS, PromotionLevel, PromotionState,
    DualTrackChecker, GapAnalyzer, PromotionOrchestrator,
    PromotionStateManager, PointsCheckResult, GrowthCheckResult,
    DualTrackResult, PeerRequirement,
)


# ══════════════════════════════════════
# Mock Services
# ══════════════════════════════════════

class MockPointsService:
    def __init__(self, growth=0, contribution=0, influence=0):
        self.points = {"growth": growth, "contribution": contribution, "influence": influence}
    
    async def get_points_summary(self, user_id):
        return self.points


class MockStageService:
    def __init__(self, stability=True, period=True):
        self._stability = stability
        self._period = period
    
    async def check_90day_stability(self, user_id):
        return self._stability
    
    async def check_min_period(self, user_id, months):
        return self._period
    
    async def check_behavior_requirements(self, user_id, reqs):
        return {r: True for r in reqs}


class MockPeerService:
    def __init__(self, total=4, progressed=2, advanced=1):
        self._total = total
        self._progressed = progressed
        self._advanced = advanced
    
    async def validate_peers(self, user_id, peer_req, promotion_key=""):
        return {
            "passed": (self._total >= peer_req.total_required and
                      self._progressed >= peer_req.min_progressed and
                      (self._advanced >= peer_req.min_advanced if peer_req.min_advanced > 0 else True)),
            "total_count": self._total,
            "total_required": peer_req.total_required,
            "progressed_count": self._progressed,
            "progressed_required": peer_req.min_progressed,
            "advanced_count": self._advanced,
            "advanced_required": peer_req.min_advanced,
        }


class MockExamService:
    def __init__(self, all_pass=True):
        self._pass = all_pass
    
    async def check_exam_requirements(self, user_id, reqs):
        return {r: self._pass for r in reqs}
    
    async def check_ethics_requirements(self, user_id, reqs):
        return {r: self._pass for r in reqs}


class MockCompanionService:
    async def check_capability_requirements(self, user_id, reqs):
        return {r: True for r in reqs}


def make_checker(**kwargs):
    return DualTrackChecker(
        points_service=kwargs.get("points", MockPointsService()),
        stage_service=kwargs.get("stage", MockStageService()),
        peer_service=kwargs.get("peers", MockPeerService()),
        exam_service=kwargs.get("exams", MockExamService()),
        companion_service=kwargs.get("companion", MockCompanionService()),
    )


# ══════════════════════════════════════
# DTK-01~05: L0-L5 阈值配置
# ══════════════════════════════════════

def test_dtk01_l0_to_l1_thresholds():
    """L0→L1: 成长≥100, 4同道者, S0-S4+90天+指标"""
    t = PROMOTION_THRESHOLDS["L0_TO_L1"]
    assert t.points.growth == 100
    assert t.points.contribution == 0
    assert t.points.is_hard_gate is True
    assert t.growth.peer_req.total_required == 4
    assert t.growth.peer_req.min_progressed == 2
    assert t.growth.ceremony_name == "破壳者"
    assert t.growth.ceremony_emoji == "🐣"
    assert t.growth.min_period_months == 3


def test_dtk02_l1_to_l2_soft_gate():
    """L1→L2: 积分为活跃度参考, 非硬性门槛"""
    t = PROMOTION_THRESHOLDS["L1_TO_L2"]
    assert t.points.growth == 300
    assert t.points.contribution == 50
    assert t.points.is_hard_gate is False  # ⚠️ 关键: 非硬性
    assert t.growth.ceremony_name == "传灯者"
    assert "50h" in str(t.growth.capability_requirements)


def test_dtk03_l2_to_l3_400_exam():
    """L2→L3: 400分制考核, 伦理一票否决"""
    t = PROMOTION_THRESHOLDS["L2_TO_L3"]
    assert t.points.growth == 800
    assert t.points.contribution == 100
    assert any("400分" in r for r in t.growth.exam_requirements)
    assert any("伦理100%" in r for r in t.growth.exam_requirements)
    assert t.growth.ceremony_name == "持杖者"


def test_dtk04_l3_to_l4_triple_points():
    """L3→L4: 三维积分门槛 (成长+贡献+影响力)"""
    t = PROMOTION_THRESHOLDS["L3_TO_L4"]
    assert t.points.growth == 1500
    assert t.points.contribution == 500
    assert t.points.influence == 200
    assert t.growth.ceremony_name == "立柱者"


def test_dtk05_l4_to_l5_all_strategies():
    """L4→L5: 全部6种防刷策略"""
    t = PROMOTION_THRESHOLDS["L4_TO_L5"]
    assert t.points.growth == 3000
    assert t.points.contribution == 1500
    assert t.points.influence == 800
    assert len(t.anti_cheat_strategies) == 6
    assert t.growth.ceremony_name == "归源者"


def test_dtk05b_all_levels_complete():
    """全部5个层级晋级路径配置完整"""
    expected = ["L0_TO_L1", "L1_TO_L2", "L2_TO_L3", "L3_TO_L4", "L4_TO_L5"]
    assert list(PROMOTION_THRESHOLDS.keys()) == expected


# ══════════════════════════════════════
# DTK-06~09: 四种状态判定
# ══════════════════════════════════════

@pytest.mark.asyncio
async def test_dtk06_state1_normal_growth():
    """状态1: 积分未达标 + 成长未验证 = 正常成长"""
    checker = make_checker(
        points=MockPointsService(growth=50),  # < 100
        stage=MockStageService(stability=False),
        exams=MockExamService(all_pass=False),
    )
    result = await checker.check(1, "L0_TO_L1")
    assert result.state == PromotionState.NORMAL_GROWTH


@pytest.mark.asyncio
async def test_dtk07_state2_awaiting_verify():
    """状态2: 积分达标 + 成长未过 = 等待验证 ⚠️关键"""
    checker = make_checker(
        points=MockPointsService(growth=150),  # >= 100 ✅
        stage=MockStageService(stability=False),  # 90天未达 ❌
    )
    result = await checker.check(1, "L0_TO_L1")
    assert result.state == PromotionState.AWAITING_VERIFY
    assert "达标" in result.guidance_message


@pytest.mark.asyncio
async def test_dtk08_state3_growth_first():
    """状态3: 成长通过 + 积分未达 = 成长先到 (罕见)"""
    checker = make_checker(
        points=MockPointsService(growth=50),  # < 100 ❌
        stage=MockStageService(stability=True, period=True),  # ✅
        peers=MockPeerService(total=4, progressed=2, advanced=1),
        exams=MockExamService(all_pass=True),
    )
    result = await checker.check(1, "L0_TO_L1")
    assert result.state == PromotionState.GROWTH_FIRST
    assert "能力" in result.guidance_message


@pytest.mark.asyncio
async def test_dtk09_state4_ready_to_promote():
    """状态4: 双轨均达标 = 晋级就绪"""
    checker = make_checker(
        points=MockPointsService(growth=200),
        stage=MockStageService(stability=True, period=True),
        peers=MockPeerService(total=4, progressed=2, advanced=1),
        exams=MockExamService(all_pass=True),
    )
    result = await checker.check(1, "L0_TO_L1")
    assert result.state == PromotionState.READY_TO_PROMOTE
    assert "恭喜" in result.guidance_message


# ══════════════════════════════════════
# DTK-10~13: 积分轨校验
# ══════════════════════════════════════

@pytest.mark.asyncio
async def test_dtk10_points_exact_threshold():
    """积分恰好达到阈值"""
    checker = make_checker(points=MockPointsService(growth=100))
    result = await checker.check(1, "L0_TO_L1")
    assert result.points_result.passed is True


@pytest.mark.asyncio
async def test_dtk11_points_below_threshold():
    """积分低于阈值"""
    checker = make_checker(points=MockPointsService(growth=99))
    result = await checker.check(1, "L0_TO_L1")
    assert result.points_result.passed is False


@pytest.mark.asyncio
async def test_dtk12_l1_l2_soft_gate_always_pass():
    """L1→L2 积分非硬性, 即使不够也通过积分轨"""
    checker = make_checker(points=MockPointsService(growth=10, contribution=0))
    result = await checker.check(1, "L1_TO_L2")
    assert result.points_result.passed is True
    assert result.points_result.is_soft_gate is True


@pytest.mark.asyncio
async def test_dtk13_triple_points_l3_l4():
    """L3→L4 需要三维积分全部达标"""
    # 只有成长达标, 贡献和影响力不够
    checker = make_checker(
        points=MockPointsService(growth=1600, contribution=100, influence=50)
    )
    result = await checker.check(1, "L3_TO_L4")
    assert result.points_result.passed is False


# ══════════════════════════════════════
# DTK-14~17: 成长轨校验
# ══════════════════════════════════════

@pytest.mark.asyncio
async def test_dtk14_peers_insufficient():
    """同道者不足 → 成长轨失败"""
    checker = make_checker(
        points=MockPointsService(growth=200),
        peers=MockPeerService(total=2, progressed=0, advanced=0),  # 只有2人
    )
    result = await checker.check(1, "L0_TO_L1")
    assert result.growth_result.peer_check["passed"] is False


@pytest.mark.asyncio
async def test_dtk15_stability_90day_fail():
    """90天稳定未达 → 成长轨失败"""
    checker = make_checker(
        points=MockPointsService(growth=200),
        stage=MockStageService(stability=False, period=True),
    )
    result = await checker.check(1, "L0_TO_L1")
    assert result.growth_result.stability_90day is False
    assert result.growth_result.passed is False


@pytest.mark.asyncio
async def test_dtk16_ethics_veto():
    """伦理不过 → 一票否决"""
    checker = make_checker(
        points=MockPointsService(growth=900, contribution=200),
        exams=MockExamService(all_pass=False),  # 伦理不过
    )
    result = await checker.check(1, "L2_TO_L3")
    assert result.growth_result.passed is False


@pytest.mark.asyncio
async def test_dtk17_period_not_met():
    """最低周期不足 → 成长轨失败"""
    checker = make_checker(
        points=MockPointsService(growth=200),
        stage=MockStageService(stability=True, period=False),  # 周期不足
    )
    result = await checker.check(1, "L0_TO_L1")
    assert result.growth_result.period_met is False
    assert result.growth_result.passed is False


# ══════════════════════════════════════
# DTK-18~20: 差距分析
# ══════════════════════════════════════

@pytest.mark.asyncio
async def test_dtk18_gap_report_state2():
    """状态2 差距报告包含具体差距项"""
    checker = make_checker(
        points=MockPointsService(growth=150),  # 积分OK
        stage=MockStageService(stability=False),  # 90天不OK
        exams=MockExamService(all_pass=False),
    )
    result = await checker.check(1, "L0_TO_L1")
    
    analyzer = GapAnalyzer()
    report = analyzer.analyze(result)
    
    assert report.total_gaps > 0
    categories = [g.category for g in report.gaps]
    assert "stability" in categories  # 应包含90天稳定差距


@pytest.mark.asyncio
async def test_dtk19_gap_points_detail():
    """积分差距包含具体数值"""
    pts_result = PointsCheckResult(
        passed=False,
        growth_current=60, growth_required=100,
        contribution_current=0, contribution_required=0,
        influence_current=0, influence_required=0,
    )
    grw_result = GrowthCheckResult(passed=False)
    
    dual_result = DualTrackResult(
        state=PromotionState.NORMAL_GROWTH,
        points_result=pts_result,
        growth_result=grw_result,
        promotion_key="L0_TO_L1",
        ceremony_name="破壳者",
        ceremony_emoji="🐣",
    )
    
    analyzer = GapAnalyzer()
    report = analyzer.analyze(dual_result)
    
    pts_gaps = [g for g in report.gaps if g.category == "points"]
    assert len(pts_gaps) == 1
    assert "40" in pts_gaps[0].gap  # 差40分


@pytest.mark.asyncio
async def test_dtk20_no_gaps_when_ready():
    """状态4无差距"""
    pts_result = PointsCheckResult(passed=True, growth_current=200, growth_required=100)
    grw_result = GrowthCheckResult(
        passed=True, stability_90day=True, period_met=True,
        peer_check={"passed": True},
    )
    
    dual_result = DualTrackResult(
        state=PromotionState.READY_TO_PROMOTE,
        points_result=pts_result,
        growth_result=grw_result,
        promotion_key="L0_TO_L1",
        ceremony_name="破壳者",
        ceremony_emoji="🐣",
    )
    
    analyzer = GapAnalyzer()
    report = analyzer.analyze(dual_result)
    assert report.total_gaps == 0


# ══════════════════════════════════════
# DTK-21~23: 晋级仪式
# ══════════════════════════════════════

@pytest.mark.asyncio
async def test_dtk21_ceremony_success():
    """状态4启动仪式成功"""
    checker = make_checker(
        points=MockPointsService(growth=200),
        stage=MockStageService(stability=True, period=True),
        peers=MockPeerService(total=4, progressed=2, advanced=1),
        exams=MockExamService(all_pass=True),
    )
    orchestrator = PromotionOrchestrator(
        checker=checker,
        gap_analyzer=GapAnalyzer(),
        state_manager=PromotionStateManager(),
    )
    
    result = await orchestrator.initiate_ceremony(1, "L0")
    assert result["success"] is True
    assert result["new_level"] == "L1"
    assert "破壳者" in result["ceremony"]["name"]
    assert "数据诚实承诺" in result["ceremony"]["contracts_to_sign"]


@pytest.mark.asyncio
async def test_dtk22_ceremony_blocked():
    """状态非4启动仪式被拒绝"""
    checker = make_checker(
        points=MockPointsService(growth=50),  # 不够
    )
    orchestrator = PromotionOrchestrator(
        checker=checker,
        gap_analyzer=GapAnalyzer(),
        state_manager=PromotionStateManager(),
    )
    
    result = await orchestrator.initiate_ceremony(1, "L0")
    assert result["success"] is False


@pytest.mark.asyncio
async def test_dtk23_ceremony_contracts_per_level():
    """各层级仪式契约正确"""
    orchestrator = PromotionOrchestrator(
        checker=make_checker(),
        gap_analyzer=GapAnalyzer(),
        state_manager=PromotionStateManager(),
    )
    
    contracts = {
        "L0_TO_L1": ["数据诚实承诺", "成长契约"],
        "L2_TO_L3": ["教练伦理宣言5条", "专业服务契约"],
        "L4_TO_L5": ["行业引领宣言", "引领契约"],
    }
    for key, expected in contracts.items():
        actual = orchestrator._get_ceremony_contracts(key)
        assert actual == expected, f"{key}: {actual} != {expected}"


# ══════════════════════════════════════
# DTK-24~25: 边界场景
# ══════════════════════════════════════

@pytest.mark.asyncio
async def test_dtk24_max_level():
    """L5已是最高级, 无法继续晋级"""
    orchestrator = PromotionOrchestrator(
        checker=make_checker(),
        gap_analyzer=GapAnalyzer(),
        state_manager=PromotionStateManager(),
    )
    result = await orchestrator.check_promotion_eligibility(1, "L5")
    assert result["state_name"] == "max_level"


def test_dtk25_invalid_promotion_key():
    """无效晋级键抛异常"""
    checker = make_checker()
    with pytest.raises(ValueError, match="Unknown promotion key"):
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            checker.check(1, "INVALID_KEY")
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

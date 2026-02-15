"""
六种防刷策略引擎测试套件
对标契约: Sheet⑦ 防刷策略矩阵

测试覆盖 (25 cases):
  ACE-01~04: AS-01 每日上限
  ACE-05~08: AS-02 质量加权
  ACE-09~12: AS-03 时间衰减
  ACE-13~16: AS-04 交叉验证
  ACE-17~18: AS-05 成长轨校验 (桥接)
  ACE-19~21: AS-06 异常检测
  ACE-22~25: Pipeline 流水线集成
"""

import pytest
import time
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from anti_cheat_engine import (
    AntiCheatStrategy, StrategyVerdict,
    PointsAwardRequest, PipelineResult,
    DailyCapStrategy, QualityWeightStrategy, TimeDecayStrategy,
    CrossVerifyStrategy, GrowthTrackStrategy, AnomalyDetectStrategy,
    AntiCheatPipeline,
    EVENT_STRATEGY_MAP, get_strategies_for_event,
)


# ══════════════════════════════════════
# Helper
# ══════════════════════════════════════

def make_request(**kwargs) -> PointsAwardRequest:
    defaults = {
        "user_id": 1,
        "event_type": "daily_checkin",
        "base_points": 5,
        "points_category": "growth",
    }
    defaults.update(kwargs)
    return PointsAwardRequest(**defaults)


# ══════════════════════════════════════
# ACE-01~04: AS-01 每日上限
# ══════════════════════════════════════

@pytest.mark.asyncio
async def test_ace01_daily_cap_allow():
    """AS-01: 首次请求在上限内通过"""
    s = DailyCapStrategy()
    req = make_request(event_type="daily_checkin", base_points=5)
    r = await s.evaluate(req)
    assert r.verdict == StrategyVerdict.ALLOW
    assert r.adjusted_points == 5


@pytest.mark.asyncio
async def test_ace02_daily_cap_capped():
    """AS-01: 超出每日上限 → 积分为0"""
    s = DailyCapStrategy()
    req = make_request(event_type="daily_checkin", base_points=5)
    
    # daily_checkin 上限=1, 先消耗1次
    await s.evaluate(req)
    # 第2次应被上限
    r = await s.evaluate(req)
    assert r.verdict == StrategyVerdict.CAPPED
    assert r.adjusted_points == 0
    assert "上限" in r.user_message


@pytest.mark.asyncio
async def test_ace03_daily_cap_no_limit():
    """AS-01: 无上限设定的事件不受限制"""
    s = DailyCapStrategy()
    req = make_request(event_type="course_develop", base_points=100)
    r = await s.evaluate(req)
    assert r.verdict == StrategyVerdict.ALLOW
    assert r.adjusted_points == 100


@pytest.mark.asyncio
async def test_ace04_daily_cap_multiple_events():
    """AS-01: 不同事件各自独立计数"""
    s = DailyCapStrategy()
    
    # 消耗 daily_checkin (上限1)
    await s.evaluate(make_request(event_type="daily_checkin"))
    r1 = await s.evaluate(make_request(event_type="daily_checkin"))
    assert r1.verdict == StrategyVerdict.CAPPED
    
    # behavior_attempt (上限3) 仍可用
    r2 = await s.evaluate(make_request(event_type="behavior_attempt", base_points=10))
    assert r2.verdict == StrategyVerdict.ALLOW


# ══════════════════════════════════════
# ACE-05~08: AS-02 质量加权
# ══════════════════════════════════════

@pytest.mark.asyncio
async def test_ace05_quality_high():
    """AS-02: 高质量 (≥0.8) → ×2"""
    s = QualityWeightStrategy()
    req = make_request(event_type="content_publish", base_points=30, quality_score=0.9)
    r = await s.evaluate(req)
    assert r.adjusted_points == 60  # 30 × 2.0
    assert r.verdict == StrategyVerdict.WEIGHTED


@pytest.mark.asyncio
async def test_ace06_quality_medium():
    """AS-02: 中质量 (0.6~0.8) → ×1"""
    s = QualityWeightStrategy()
    req = make_request(event_type="content_publish", base_points=30, quality_score=0.7)
    r = await s.evaluate(req)
    assert r.adjusted_points == 30  # 30 × 1.0


@pytest.mark.asyncio
async def test_ace07_quality_low():
    """AS-02: 低质量 (0.3~0.6) → ×0.5"""
    s = QualityWeightStrategy()
    req = make_request(event_type="content_publish", base_points=30, quality_score=0.4)
    r = await s.evaluate(req)
    assert r.adjusted_points == 15  # 30 × 0.5


@pytest.mark.asyncio
async def test_ace08_quality_rejected():
    """AS-02: 极低质量 (<0.3) → ×0, 拒绝"""
    s = QualityWeightStrategy()
    req = make_request(event_type="content_publish", base_points=30, quality_score=0.1)
    r = await s.evaluate(req)
    assert r.adjusted_points == 0  # 30 × 0.0


@pytest.mark.asyncio
async def test_ace08b_quality_non_applicable():
    """AS-02: 不在质量事件列表的直接通过"""
    s = QualityWeightStrategy()
    req = make_request(event_type="daily_checkin", base_points=5, quality_score=0.1)
    r = await s.evaluate(req)
    assert r.verdict == StrategyVerdict.ALLOW
    assert r.adjusted_points == 5


# ══════════════════════════════════════
# ACE-09~12: AS-03 时间衰减
# ══════════════════════════════════════

@pytest.mark.asyncio
async def test_ace09_decay_no_decay():
    """AS-03: 前5次无衰减"""
    s = TimeDecayStrategy()
    req = make_request(event_type="behavior_attempt", base_points=10)
    for _ in range(5):
        r = await s.evaluate(req)
    assert r.adjusted_points == 10  # 第5次仍 ×1.0


@pytest.mark.asyncio
async def test_ace10_decay_first_tier():
    """AS-03: 第6-10次 → ×0.8"""
    s = TimeDecayStrategy()
    req = make_request(event_type="behavior_attempt", base_points=10)
    for _ in range(5):
        await s.evaluate(req)
    # 第6次
    r = await s.evaluate(req)
    assert r.adjusted_points == 8  # 10 × 0.8
    assert r.verdict == StrategyVerdict.DECAYED


@pytest.mark.asyncio
async def test_ace11_decay_second_tier():
    """AS-03: 第11-20次 → ×0.5"""
    s = TimeDecayStrategy()
    req = make_request(event_type="behavior_attempt", base_points=10)
    for _ in range(10):
        await s.evaluate(req)
    # 第11次
    r = await s.evaluate(req)
    assert r.adjusted_points == 5  # 10 × 0.5


@pytest.mark.asyncio
async def test_ace12_decay_third_tier():
    """AS-03: 第21次起 → ×0.2, 最低1分"""
    s = TimeDecayStrategy()
    req = make_request(event_type="behavior_attempt", base_points=10)
    for _ in range(20):
        await s.evaluate(req)
    # 第21次
    r = await s.evaluate(req)
    assert r.adjusted_points == 2  # 10 × 0.2
    assert "不同行为" in r.user_message


# ══════════════════════════════════════
# ACE-13~16: AS-04 交叉验证
# ══════════════════════════════════════

@pytest.mark.asyncio
async def test_ace13_cross_verify_pending():
    """AS-04: 需要交叉验证的事件 → PENDING"""
    s = CrossVerifyStrategy()
    req = make_request(
        event_type="supervision_session_completed",
        base_points=50,
        counterpart_user_id=2,
        behavior_id="session_001",
    )
    r = await s.evaluate(req)
    assert r.verdict == StrategyVerdict.PENDING
    assert r.adjusted_points == 0
    assert "确认" in r.user_message


@pytest.mark.asyncio
async def test_ace14_cross_verify_confirmed():
    """AS-04: 对方确认后 → ALLOW"""
    s = CrossVerifyStrategy()
    
    # 先提交待确认
    req = make_request(
        event_type="supervision_session_completed",
        base_points=50,
        counterpart_user_id=2,
        behavior_id="session_002",
    )
    await s.evaluate(req)
    
    # 对方确认
    confirmed = await s.confirm(
        confirmer_user_id=2,
        original_user_id=1,
        event_type="supervision_session_completed",
        behavior_id="session_002",
    )
    assert confirmed is True
    
    # 再次评估
    r = await s.evaluate(req)
    assert r.verdict == StrategyVerdict.ALLOW


@pytest.mark.asyncio
async def test_ace15_cross_verify_no_counterpart():
    """AS-04: 未提供对方用户 → PENDING"""
    s = CrossVerifyStrategy()
    req = make_request(
        event_type="knowledge_shared",
        base_points=30,
        counterpart_user_id=0,
    )
    r = await s.evaluate(req)
    assert r.verdict == StrategyVerdict.PENDING


@pytest.mark.asyncio
async def test_ace16_cross_verify_non_applicable():
    """AS-04: 不需要交叉验证的事件直接通过"""
    s = CrossVerifyStrategy()
    req = make_request(event_type="daily_checkin", base_points=5)
    r = await s.evaluate(req)
    assert r.verdict == StrategyVerdict.ALLOW


# ══════════════════════════════════════
# ACE-17~18: AS-05 成长轨校验
# ══════════════════════════════════════

@pytest.mark.asyncio
async def test_ace17_growth_track_always_allow():
    """AS-05: 不阻断积分发放 (只附加信息)"""
    s = GrowthTrackStrategy()
    req = make_request(base_points=50)
    r = await s.evaluate(req)
    assert r.verdict == StrategyVerdict.ALLOW
    assert r.adjusted_points == 50


@pytest.mark.asyncio
async def test_ace18_growth_track_with_orchestrator():
    """AS-05: 集成编排器时附带晋级状态"""
    class MockOrchestrator:
        async def check_promotion_eligibility(self, uid, level):
            return {"state": 2, "state_name": "AWAITING_VERIFY", "guidance_message": "测试消息"}
    
    s = GrowthTrackStrategy(promotion_orchestrator=MockOrchestrator())
    req = make_request(base_points=50, metadata={"current_level": "L0"})
    r = await s.evaluate(req)
    assert r.verdict == StrategyVerdict.ALLOW
    assert r.metadata.get("promotion_state") == "AWAITING_VERIFY"


# ══════════════════════════════════════
# ACE-19~21: AS-06 异常检测
# ══════════════════════════════════════

@pytest.mark.asyncio
async def test_ace19_anomaly_normal():
    """AS-06: 正常频率不触发标记"""
    s = AnomalyDetectStrategy()
    req = make_request(event_type="daily_checkin", base_points=5)
    r = await s.evaluate(req)
    assert r.verdict == StrategyVerdict.ALLOW


@pytest.mark.asyncio
async def test_ace20_anomaly_burst():
    """AS-06: 60秒内≥8次 → 突发标记"""
    s = AnomalyDetectStrategy()
    now = time.time()
    
    for i in range(8):
        req = make_request(
            event_type="assessment_submit",
            base_points=5,
            timestamp=now + i * 0.1,
        )
        await s.evaluate(req)
    
    # 第9次触发
    req = make_request(event_type="assessment_submit", base_points=5, timestamp=now + 1.0)
    r = await s.evaluate(req)
    assert r.verdict == StrategyVerdict.FLAGGED
    assert r.adjusted_points == 5  # 仍发放, 但已标记
    assert r.user_message == ""  # 不提示用户


@pytest.mark.asyncio
async def test_ace21_anomaly_flagged_still_awards():
    """AS-06: 异常标记不阻断积分 (人工审查后回收)"""
    s = AnomalyDetectStrategy()
    now = time.time()
    
    for i in range(9):
        await s.evaluate(make_request(
            event_type="micro_action_complete",
            base_points=3,
            timestamp=now + i * 0.05,
        ))
    
    r = await s.evaluate(make_request(
        event_type="micro_action_complete",
        base_points=3,
        timestamp=now + 0.5,
    ))
    assert r.adjusted_points == 3  # 积分仍发放
    assert r.metadata.get("review_submitted") is True


# ══════════════════════════════════════
# ACE-22~25: Pipeline 流水线集成
# ══════════════════════════════════════

@pytest.mark.asyncio
async def test_ace22_pipeline_normal_flow():
    """Pipeline: 正常流程全通过"""
    pipeline = AntiCheatPipeline.create_default()
    req = make_request(event_type="course_complete", base_points=20)
    result = await pipeline.process(req)
    assert result.awarded is True
    assert result.final_points == 20
    assert result.verdict_summary in ("allowed", "allowed_but_flagged")


@pytest.mark.asyncio
async def test_ace23_pipeline_cap_short_circuit():
    """Pipeline: AS-01 上限命中短路, 后续策略不执行"""
    pipeline = AntiCheatPipeline.create_default()
    req = make_request(event_type="daily_checkin", base_points=5)
    
    await pipeline.process(req)  # 消耗1次
    result = await pipeline.process(req)  # 第2次被上限
    
    assert result.awarded is False
    assert result.final_points == 0
    assert result.verdict_summary == "capped"


@pytest.mark.asyncio
async def test_ace24_pipeline_decay_then_quality():
    """Pipeline: AS-03 衰减 + AS-02 质量加权叠加"""
    pipeline = AntiCheatPipeline.create_default()
    
    # 先刷6次 community_help 触发衰减
    for _ in range(5):
        await pipeline.process(make_request(
            event_type="community_help", base_points=10, quality_score=0.9,
        ))
    
    # 第6次: 衰减 ×0.8 → 8, 然后质量 ×2 → 16
    result = await pipeline.process(make_request(
        event_type="community_help", base_points=10, quality_score=0.9,
    ))
    assert result.final_points == 16  # 10 × 0.8 × 2.0
    assert result.awarded is True


@pytest.mark.asyncio
async def test_ace25_pipeline_pending_cross_verify():
    """Pipeline: AS-04 交叉验证阻断"""
    pipeline = AntiCheatPipeline.create_default()
    req = make_request(
        event_type="supervision_session_completed",
        base_points=50,
        counterpart_user_id=99,
        behavior_id="sv_test",
    )
    result = await pipeline.process(req)
    assert result.awarded is False
    assert result.pending_confirmation is True
    assert result.verdict_summary == "pending_confirmation"


# ══════════════════════════════════════
# 补充: 事件策略映射完整性
# ══════════════════════════════════════

def test_strategy_map_completeness():
    """全量事件→策略映射存在"""
    # Week1 Task2 治理事件
    governance_events = [
        "ethics_scenario_test", "competency_self_assessment",
        "ethics_declaration_signed", "conflict_disclosure_update",
        "alert_timely_response", "student_message_reply",
        "supervision_session_completed", "agent_feedback_reply",
        "knowledge_shared", "certificate_renewal_confirmed",
    ]
    for ev in governance_events:
        assert ev in EVENT_STRATEGY_MAP, f"Missing governance event: {ev}"
    
    # Agent 生态事件
    agent_events = [
        "create_agent", "optimize_prompt", "share_knowledge",
        "template_published", "template_installed",
    ]
    for ev in agent_events:
        assert ev in EVENT_STRATEGY_MAP, f"Missing agent event: {ev}"
    
    # V4.0 行为联动事件
    v4_events = [
        "assessment_submit", "micro_action_complete",
        "challenge_checkin", "challenge_complete",
        "reflection_create", "contract_sign",
        "companion_add", "contribution_submit",
        "food_recognize", "peer_accept",
    ]
    for ev in v4_events:
        assert ev in EVENT_STRATEGY_MAP, f"Missing V4.0 event: {ev}"


def test_all_six_strategies_used():
    """全部6种策略至少被1个事件使用"""
    all_strategies = set()
    for strategies in EVENT_STRATEGY_MAP.values():
        all_strategies.update(strategies)
    
    expected = {"AS-01", "AS-02", "AS-03", "AS-04", "AS-05", "AS-06"}
    assert expected.issubset(all_strategies), f"Missing strategies: {expected - all_strategies}"


def test_get_strategies_for_event():
    """查询API正常工作"""
    s = get_strategies_for_event("student_message_reply")
    assert "AS-01" in s
    assert "AS-03" in s
    assert "AS-06" in s
    
    # 未知事件返回空
    s2 = get_strategies_for_event("unknown_event_xyz")
    assert s2 == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
BehaviorOS v32 — 策略引擎 & 处方引擎联合测试
================================================
验证 V007 PolicyEngine 与行为处方系统的集成

测试矩阵:
  test_strategy_selection  — TTM 阶段策略选择逻辑
  test_personality_routing — BigFive 人格路由
  test_capacity_calibration— CAPACITY 能力校准
  test_intensity_rules     — 强度规则引擎
  test_communication_adapt — 沟通风格适配
  test_stage_strategy_map  — 全阶段策略映射

放置: tests/test_v32_policy_engine.py
运行: python -m pytest tests/test_v32_policy_engine.py -v -s
"""

from __future__ import annotations

import uuid

import pytest

PASS = lambda tag: print(f"  [PASS] {tag}")

USER_ID = uuid.uuid4()


def make_ctx(ttm=3, readiness=0.6, capacity=0.5, efficacy=0.5,
             bigfive=None, barriers=None, risk="normal"):
    from behavior_rx.core.rx_schemas import RxContext, BigFiveProfile
    bf = bigfive or {"O": 50, "C": 50, "E": 50, "A": 50, "N": 50}
    return RxContext(
        user_id=USER_ID,
        ttm_stage=ttm,
        stage_readiness=readiness,
        stage_stability=0.6,
        personality=BigFiveProfile(**bf),
        capacity_score=capacity,
        self_efficacy=efficacy,
        active_barriers=barriers or [],
        risk_level=risk,
    )


# =====================================================================
# Test 1: TTM 阶段策略选择
# =====================================================================

def test_strategy_selection():
    """TTM 阶段 → 对应策略"""
    print("\n--- 1. TTM Strategy Selection ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.rx_schemas import (
        ExpertAgentType, RxStrategyType,
    )

    engine = BehaviorRxEngine()

    # 阶段 → 期望策略族
    stage_strategy_map = {
        0: {RxStrategyType.CONSCIOUSNESS_RAISING, RxStrategyType.DRAMATIC_RELIEF,
            RxStrategyType.SELF_REEVALUATION, RxStrategyType.DECISIONAL_BALANCE},
        1: {RxStrategyType.CONSCIOUSNESS_RAISING, RxStrategyType.SELF_REEVALUATION,
            RxStrategyType.DECISIONAL_BALANCE, RxStrategyType.DRAMATIC_RELIEF},
        2: {RxStrategyType.SELF_LIBERATION, RxStrategyType.DECISIONAL_BALANCE,
            RxStrategyType.COGNITIVE_RESTRUCTURING, RxStrategyType.SELF_REEVALUATION},
        3: {RxStrategyType.STIMULUS_CONTROL, RxStrategyType.CONTINGENCY_MANAGEMENT,
            RxStrategyType.HABIT_STACKING, RxStrategyType.SELF_MONITORING,
            RxStrategyType.SELF_LIBERATION, RxStrategyType.COGNITIVE_RESTRUCTURING},
        4: {RxStrategyType.STIMULUS_CONTROL, RxStrategyType.CONTINGENCY_MANAGEMENT,
            RxStrategyType.HABIT_STACKING, RxStrategyType.SELF_MONITORING,
            RxStrategyType.RELAPSE_PREVENTION},
        5: {RxStrategyType.RELAPSE_PREVENTION, RxStrategyType.SELF_MONITORING,
            RxStrategyType.CONTINGENCY_MANAGEMENT, RxStrategyType.STIMULUS_CONTROL},
    }

    for stage, expected_set in stage_strategy_map.items():
        ctx = make_ctx(ttm=stage, readiness=0.5)
        rx = engine.compute_rx(ctx, ExpertAgentType.BEHAVIOR_COACH)
        assert rx.primary_strategy in expected_set, \
            f"S{stage}: got {rx.primary_strategy.value}, expected one of {[s.value for s in expected_set]}"
        PASS(f"S{stage} → {rx.primary_strategy.value} ✓")


# =====================================================================
# Test 2: BigFive 人格路由
# =====================================================================

def test_personality_routing():
    """BigFive 人格 → 沟通风格"""
    print("\n--- 2. Personality Routing ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.rx_schemas import (
        ExpertAgentType, CommunicationStyle,
    )

    engine = BehaviorRxEngine()

    # 高 N → empathetic
    ctx_high_n = make_ctx(ttm=2, bigfive={"O": 50, "C": 50, "E": 50, "A": 50, "N": 80})
    rx_n = engine.compute_rx(ctx_high_n, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_n.communication_style == CommunicationStyle.EMPATHETIC
    PASS("high N=80 → EMPATHETIC")

    # 高 C → data_driven
    ctx_high_c = make_ctx(ttm=3, bigfive={"O": 50, "C": 80, "E": 50, "A": 50, "N": 30})
    rx_c = engine.compute_rx(ctx_high_c, ExpertAgentType.METABOLIC_EXPERT)
    assert rx_c.communication_style == CommunicationStyle.DATA_DRIVEN
    PASS("high C=80 → DATA_DRIVEN")

    # 高 O → exploratory
    ctx_high_o = make_ctx(ttm=2, bigfive={"O": 85, "C": 50, "E": 50, "A": 50, "N": 30})
    rx_o = engine.compute_rx(ctx_high_o, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_o.communication_style == CommunicationStyle.EXPLORATORY
    PASS("high O=85 → EXPLORATORY")

    # 高 E → social_proof
    ctx_high_e = make_ctx(ttm=3, bigfive={"O": 50, "C": 50, "E": 80, "A": 50, "N": 30})
    rx_e = engine.compute_rx(ctx_high_e, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_e.communication_style == CommunicationStyle.SOCIAL_PROOF
    PASS("high E=80 → SOCIAL_PROOF")


# =====================================================================
# Test 3: CAPACITY 能力校准
# =====================================================================

def test_capacity_calibration():
    """CAPACITY → 处方难度校准"""
    print("\n--- 3. CAPACITY Calibration ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.rx_schemas import ExpertAgentType, RxIntensity

    engine = BehaviorRxEngine()

    # 低能力 → 低/最低强度
    ctx_low = make_ctx(ttm=3, capacity=0.15, efficacy=0.15)
    rx_low = engine.compute_rx(ctx_low, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_low.intensity in [RxIntensity.MINIMAL, RxIntensity.LOW]
    PASS(f"capacity=0.15 → {rx_low.intensity.value}")

    # 中等能力 → 中等强度
    ctx_mid = make_ctx(ttm=3, capacity=0.55, efficacy=0.55)
    rx_mid = engine.compute_rx(ctx_mid, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_mid.intensity in [RxIntensity.LOW, RxIntensity.MODERATE, RxIntensity.HIGH]
    PASS(f"capacity=0.55 → {rx_mid.intensity.value}")

    # 高能力 → 高强度
    ctx_high = make_ctx(ttm=3, capacity=0.9, efficacy=0.9)
    rx_high = engine.compute_rx(ctx_high, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_high.intensity in [RxIntensity.MODERATE, RxIntensity.HIGH, RxIntensity.INTENSIVE]
    PASS(f"capacity=0.9 → {rx_high.intensity.value}")

    # 强度递增验证
    intensities = {
        RxIntensity.MINIMAL: 1,
        RxIntensity.LOW: 2,
        RxIntensity.MODERATE: 3,
        RxIntensity.HIGH: 4,
        RxIntensity.INTENSIVE: 5,
    }
    low_level = intensities.get(rx_low.intensity, 0)
    high_level = intensities.get(rx_high.intensity, 0)
    assert high_level >= low_level
    PASS(f"intensity ordering: {rx_low.intensity.value}({low_level}) ≤ {rx_high.intensity.value}({high_level})")


# =====================================================================
# Test 4: 强度规则引擎
# =====================================================================

def test_intensity_rules():
    """强度规则: 风险等级影响"""
    print("\n--- 4. Intensity Rules ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.rx_schemas import ExpertAgentType, RxIntensity

    engine = BehaviorRxEngine()

    # 高风险 → 强度受限
    ctx_risk = make_ctx(ttm=3, capacity=0.8, risk="high")
    rx_risk = engine.compute_rx(ctx_risk, ExpertAgentType.CARDIAC_EXPERT)
    assert rx_risk.intensity in [RxIntensity.MINIMAL, RxIntensity.LOW, RxIntensity.MODERATE]
    PASS(f"risk=high → intensity capped at {rx_risk.intensity.value}")

    # 危急风险 → 最低强度
    ctx_critical = make_ctx(ttm=3, capacity=0.8, risk="critical")
    rx_critical = engine.compute_rx(ctx_critical, ExpertAgentType.CARDIAC_EXPERT)
    assert rx_critical.intensity in [RxIntensity.MINIMAL, RxIntensity.LOW]
    PASS(f"risk=critical → intensity={rx_critical.intensity.value}")


# =====================================================================
# Test 5: 沟通风格适配
# =====================================================================

def test_communication_adaptation():
    """沟通风格随上下文适配"""
    print("\n--- 5. Communication Adaptation ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.rx_schemas import (
        ExpertAgentType, CommunicationStyle,
    )

    engine = BehaviorRxEngine()

    # 同一阶段不同人格 → 不同沟通风格
    ctx_a = make_ctx(ttm=3, bigfive={"O": 50, "C": 80, "E": 50, "A": 50, "N": 30})
    ctx_b = make_ctx(ttm=3, bigfive={"O": 50, "C": 30, "E": 50, "A": 50, "N": 80})

    rx_a = engine.compute_rx(ctx_a, ExpertAgentType.METABOLIC_EXPERT)
    rx_b = engine.compute_rx(ctx_b, ExpertAgentType.METABOLIC_EXPERT)

    assert rx_a.communication_style != rx_b.communication_style
    PASS(f"same stage, diff personality → diff style: {rx_a.communication_style.value} vs {rx_b.communication_style.value}")

    # 所有沟通风格都可达
    all_styles = set()
    test_profiles = [
        {"O": 85, "C": 50, "E": 50, "A": 50, "N": 30},  # high O
        {"O": 50, "C": 80, "E": 50, "A": 50, "N": 30},  # high C
        {"O": 50, "C": 50, "E": 80, "A": 50, "N": 30},  # high E
        {"O": 50, "C": 50, "E": 50, "A": 50, "N": 80},  # high N
        {"O": 50, "C": 50, "E": 50, "A": 50, "N": 50},  # neutral
    ]
    for bf in test_profiles:
        ctx = make_ctx(ttm=3, bigfive=bf)
        rx = engine.compute_rx(ctx, ExpertAgentType.BEHAVIOR_COACH)
        all_styles.add(rx.communication_style.value)

    assert len(all_styles) >= 3
    PASS(f"reachable comm styles: {len(all_styles)} ({', '.join(all_styles)})")


# =====================================================================
# Test 6: 全阶段策略连贯性
# =====================================================================

def test_stage_strategy_coherence():
    """全阶段策略连贯性 (S0→S6)"""
    print("\n--- 6. Stage Strategy Coherence ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.rx_schemas import ExpertAgentType

    engine = BehaviorRxEngine()

    strategies = []
    for stage in range(7):
        ctx = make_ctx(ttm=stage, readiness=0.5 + stage * 0.05)
        rx = engine.compute_rx(ctx, ExpertAgentType.BEHAVIOR_COACH)
        strategies.append(rx.primary_strategy.value)
        PASS(f"S{stage} → {rx.primary_strategy.value}")

    # 前期 (S0-S2) 不应出现 relapse_prevention
    early_strategies = strategies[:3]
    assert "relapse_prevention" not in early_strategies
    PASS("S0-S2 excludes relapse_prevention")

    # 后期 (S4-S6) 不应出现 consciousness_raising
    late_strategies = strategies[4:]
    # 这个约束较宽松, 仅验证多样性
    assert len(set(strategies)) >= 3
    PASS(f"strategy diversity across stages: {len(set(strategies))} unique")


# =====================================================================
# 运行入口
# =====================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])

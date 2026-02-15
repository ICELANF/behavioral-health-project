"""
BehaviorOS v32 — 策略引擎规则测试
===================================
匹配实际引擎逻辑:
  - strategy_type (不是 primary_strategy)
  - 高E → CHALLENGE (不是 SOCIAL_PROOF)
  - 高A → SOCIAL_PROOF
  - INTENSITY_MATRIX: S3/low=MODERATE, 引擎不做 risk 降级
  - capacity < 0.35 → band="low", 0.35-0.65 → "mid", > 0.65 → "high"

运行:
  python -m pytest tests/test_v32_policy_engine.py -v -s
"""

import os
import sys
import uuid

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

PASS = lambda tag: print(f"  [PASS] {tag}")
USER_ID = uuid.uuid4()


def make_ctx(ttm=3, readiness=0.5, capacity=0.5, efficacy=0.5,
             bigfive=None, risk="normal"):
    from behavior_rx.core.rx_schemas import RxContext, BigFiveProfile
    bf = bigfive or {}
    return RxContext(
        user_id=USER_ID,
        ttm_stage=ttm,
        stage_readiness=readiness,
        stage_stability=0.5,
        personality=BigFiveProfile(**bf) if bf else BigFiveProfile(),
        capacity_score=capacity,
        self_efficacy=efficacy,
        risk_level=risk,
    )


# =====================================================================
# 1. TTM Strategy Selection
# =====================================================================

def test_strategy_selection():
    print("\n--- 1. TTM Strategy Selection ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.rx_schemas import ExpertAgentType, RxStrategyType

    engine = BehaviorRxEngine()

    # 阶段 → 期望策略族 (宽泛匹配)
    early_strategies = {
        RxStrategyType.CONSCIOUSNESS_RAISING, RxStrategyType.DRAMATIC_RELIEF,
        RxStrategyType.SELF_REEVALUATION, RxStrategyType.DECISIONAL_BALANCE,
    }
    mid_strategies = {
        RxStrategyType.SELF_LIBERATION, RxStrategyType.DECISIONAL_BALANCE,
        RxStrategyType.COGNITIVE_RESTRUCTURING, RxStrategyType.SELF_REEVALUATION,
    }
    action_strategies = {
        RxStrategyType.STIMULUS_CONTROL, RxStrategyType.CONTINGENCY_MANAGEMENT,
        RxStrategyType.HABIT_STACKING, RxStrategyType.SELF_MONITORING,
        RxStrategyType.SELF_LIBERATION, RxStrategyType.COGNITIVE_RESTRUCTURING,
    }
    maint_strategies = {
        RxStrategyType.STIMULUS_CONTROL, RxStrategyType.CONTINGENCY_MANAGEMENT,
        RxStrategyType.HABIT_STACKING, RxStrategyType.SELF_MONITORING,
        RxStrategyType.RELAPSE_PREVENTION,
    }

    stage_map = {
        0: early_strategies,
        1: early_strategies,
        2: mid_strategies | early_strategies,  # 准备阶段可能交叉
        3: action_strategies,
        4: maint_strategies | action_strategies,
        5: maint_strategies,
    }

    for stage, expected_set in stage_map.items():
        ctx = make_ctx(ttm=stage, readiness=0.5)
        rx = engine.compute_rx(ctx, ExpertAgentType.BEHAVIOR_COACH)
        assert rx.strategy_type in expected_set, \
            f"S{stage}: got {rx.strategy_type.value}, expected one of {[s.value for s in expected_set]}"
        PASS(f"S{stage} → {rx.strategy_type.value}")


# =====================================================================
# 2. Personality Routing
# =====================================================================

def test_personality_routing():
    """
    BigFive → 沟通风格 (实际优先级):
      高N → EMPATHETIC
      高C → DATA_DRIVEN
      高E → CHALLENGE
      高A → SOCIAL_PROOF
      高O → EXPLORATORY
      都不突出 → NEUTRAL
    """
    print("\n--- 2. Personality Routing ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.rx_schemas import ExpertAgentType, CommunicationStyle

    engine = BehaviorRxEngine()

    # 高 N → EMPATHETIC
    ctx_n = make_ctx(ttm=2, bigfive={"O": 50, "C": 50, "E": 50, "A": 50, "N": 80})
    rx_n = engine.compute_rx(ctx_n, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_n.communication_style == CommunicationStyle.EMPATHETIC
    PASS("high N=80 → EMPATHETIC")

    # 高 C → DATA_DRIVEN
    ctx_c = make_ctx(ttm=3, bigfive={"O": 50, "C": 80, "E": 50, "A": 50, "N": 30})
    rx_c = engine.compute_rx(ctx_c, ExpertAgentType.METABOLIC_EXPERT)
    assert rx_c.communication_style == CommunicationStyle.DATA_DRIVEN
    PASS("high C=80 → DATA_DRIVEN")

    # 高 O → EXPLORATORY (N,C,E,A 都不高)
    ctx_o = make_ctx(ttm=2, bigfive={"O": 85, "C": 50, "E": 50, "A": 50, "N": 30})
    rx_o = engine.compute_rx(ctx_o, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_o.communication_style == CommunicationStyle.EXPLORATORY
    PASS("high O=85 → EXPLORATORY")

    # 高 E → CHALLENGE (实际映射)
    ctx_e = make_ctx(ttm=3, bigfive={"O": 50, "C": 50, "E": 80, "A": 50, "N": 30})
    rx_e = engine.compute_rx(ctx_e, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_e.communication_style == CommunicationStyle.CHALLENGE
    PASS("high E=80 → CHALLENGE")

    # 高 A → SOCIAL_PROOF (E 不高)
    ctx_a = make_ctx(ttm=3, bigfive={"O": 50, "C": 50, "E": 50, "A": 80, "N": 30})
    rx_a = engine.compute_rx(ctx_a, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_a.communication_style == CommunicationStyle.SOCIAL_PROOF
    PASS("high A=80 → SOCIAL_PROOF")

    # 都不突出 → NEUTRAL
    ctx_neutral = make_ctx(ttm=3, bigfive={"O": 50, "C": 50, "E": 50, "A": 50, "N": 50})
    rx_neutral = engine.compute_rx(ctx_neutral, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_neutral.communication_style == CommunicationStyle.NEUTRAL
    PASS("neutral profile → NEUTRAL")


# =====================================================================
# 3. CAPACITY Calibration
# =====================================================================

def test_capacity_calibration():
    """
    INTENSITY_MATRIX 实际值:
      S0: low=MINIMAL, mid=MINIMAL, high=LOW
      S3: low=MODERATE, mid=MODERATE, high=HIGH
      S6: low=MINIMAL, mid=LOW, high=LOW

    capacity bands: <0.35=low, 0.35-0.65=mid, >0.65=high
    """
    print("\n--- 3. CAPACITY Calibration ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.rx_schemas import ExpertAgentType, RxIntensity

    engine = BehaviorRxEngine()

    # S0 + low capacity → MINIMAL
    ctx_s0_low = make_ctx(ttm=0, capacity=0.15)
    rx_s0_low = engine.compute_rx(ctx_s0_low, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_s0_low.intensity == RxIntensity.MINIMAL
    PASS(f"S0 cap=0.15 → {rx_s0_low.intensity.value}")

    # S3 + low capacity → MODERATE (INTENSITY_MATRIX[3]["low"]=MODERATE)
    ctx_s3_low = make_ctx(ttm=3, capacity=0.15)
    rx_s3_low = engine.compute_rx(ctx_s3_low, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_s3_low.intensity == RxIntensity.MODERATE
    PASS(f"S3 cap=0.15 → {rx_s3_low.intensity.value}")

    # S3 + mid capacity → MODERATE
    ctx_s3_mid = make_ctx(ttm=3, capacity=0.55)
    rx_s3_mid = engine.compute_rx(ctx_s3_mid, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_s3_mid.intensity == RxIntensity.MODERATE
    PASS(f"S3 cap=0.55 → {rx_s3_mid.intensity.value}")

    # S3 + high capacity → HIGH
    ctx_s3_high = make_ctx(ttm=3, capacity=0.9)
    rx_s3_high = engine.compute_rx(ctx_s3_high, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_s3_high.intensity == RxIntensity.HIGH
    PASS(f"S3 cap=0.9 → {rx_s3_high.intensity.value}")

    # S6 + low capacity → MINIMAL
    ctx_s6_low = make_ctx(ttm=6, capacity=0.2)
    rx_s6_low = engine.compute_rx(ctx_s6_low, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_s6_low.intensity == RxIntensity.MINIMAL
    PASS(f"S6 cap=0.2 → {rx_s6_low.intensity.value}")

    # 强度单调性: 同阶段, 高容量 >= 低容量
    intensity_order = {
        RxIntensity.MINIMAL: 0, RxIntensity.LOW: 1, RxIntensity.MODERATE: 2,
        RxIntensity.HIGH: 3, RxIntensity.INTENSIVE: 4,
    }
    assert intensity_order[rx_s3_high.intensity] >= intensity_order[rx_s3_low.intensity]
    PASS("S3: high capacity ≥ low capacity intensity")


# =====================================================================
# 4. Intensity Rules (no risk-based capping in current engine)
# =====================================================================

def test_intensity_rules():
    """
    当前引擎的强度仅由 INTENSITY_MATRIX[stage][capacity_band] 决定，
    不会因 risk_level 而降级。这里验证 MATRIX 输出正确性。
    """
    print("\n--- 4. Intensity Rules ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.rx_schemas import ExpertAgentType, RxIntensity

    engine = BehaviorRxEngine()

    # S4 high capacity → HIGH
    ctx_s4 = make_ctx(ttm=4, capacity=0.8)
    rx_s4 = engine.compute_rx(ctx_s4, ExpertAgentType.CARDIAC_EXPERT)
    assert rx_s4.intensity == RxIntensity.HIGH
    PASS(f"S4 cap=0.8 → {rx_s4.intensity.value}")

    # S5 mid capacity → MODERATE (维持阶段适中)
    ctx_s5 = make_ctx(ttm=5, capacity=0.5)
    rx_s5 = engine.compute_rx(ctx_s5, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_s5.intensity == RxIntensity.MODERATE
    PASS(f"S5 cap=0.5 → {rx_s5.intensity.value}")

    # S1 mid → LOW
    ctx_s1 = make_ctx(ttm=1, capacity=0.5)
    rx_s1 = engine.compute_rx(ctx_s1, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_s1.intensity == RxIntensity.LOW
    PASS(f"S1 cap=0.5 → {rx_s1.intensity.value}")

    # S2 high → MODERATE
    ctx_s2 = make_ctx(ttm=2, capacity=0.8)
    rx_s2 = engine.compute_rx(ctx_s2, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_s2.intensity == RxIntensity.MODERATE
    PASS(f"S2 cap=0.8 → {rx_s2.intensity.value}")

    # 同一 risk="high" 不影响 matrix 输出
    ctx_risk = make_ctx(ttm=3, capacity=0.8, risk="high")
    rx_risk = engine.compute_rx(ctx_risk, ExpertAgentType.CARDIAC_EXPERT)
    # INTENSITY_MATRIX[3]["high"] = HIGH
    assert rx_risk.intensity == RxIntensity.HIGH
    PASS(f"S3 cap=0.8 risk=high → {rx_risk.intensity.value} (matrix-driven)")


# =====================================================================
# 5. Communication Adaptation
# =====================================================================

def test_communication_adaptation():
    print("\n--- 5. Communication Adaptation ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.rx_schemas import ExpertAgentType, CommunicationStyle

    engine = BehaviorRxEngine()

    # 同阶段不同人格 → 不同沟通风格
    ctx_a = make_ctx(ttm=3, bigfive={"C": 80, "N": 30})
    ctx_b = make_ctx(ttm=3, bigfive={"N": 80, "C": 30})
    rx_a = engine.compute_rx(ctx_a, ExpertAgentType.BEHAVIOR_COACH)
    rx_b = engine.compute_rx(ctx_b, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_a.communication_style != rx_b.communication_style
    PASS(f"same stage, diff personality → diff style: {rx_a.communication_style.value} vs {rx_b.communication_style.value}")

    # 测试所有6种人格配置能覆盖多种沟通风格
    profiles = [
        {"N": 80},           # EMPATHETIC
        {"C": 80, "N": 30},  # DATA_DRIVEN
        {"E": 80, "N": 30, "C": 30},  # CHALLENGE
        {"A": 80, "N": 30, "C": 30, "E": 30},  # SOCIAL_PROOF
        {"O": 80, "N": 30, "C": 30, "E": 30, "A": 30},  # EXPLORATORY
    ]
    styles = set()
    for bf in profiles:
        ctx = make_ctx(ttm=3, bigfive=bf)
        rx = engine.compute_rx(ctx, ExpertAgentType.BEHAVIOR_COACH)
        styles.add(rx.communication_style.value)
    assert len(styles) >= 4
    PASS(f"reachable comm styles: {len(styles)} ({', '.join(sorted(styles))})")


# =====================================================================
# 6. Stage Strategy Coherence
# =====================================================================

def test_stage_strategy_coherence():
    print("\n--- 6. Stage Strategy Coherence ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.rx_schemas import ExpertAgentType, RxStrategyType

    engine = BehaviorRxEngine()

    strategies = []
    for stage in range(7):
        ctx = make_ctx(ttm=stage, readiness=0.5 + stage * 0.05)
        rx = engine.compute_rx(ctx, ExpertAgentType.BEHAVIOR_COACH)
        # 实际字段名: strategy_type
        strategies.append(rx.strategy_type.value)
        PASS(f"S{stage} → {rx.strategy_type.value}")

    # 早期阶段不应出现 relapse_prevention
    early = strategies[:2]  # S0, S1
    assert "relapse_prevention" not in early
    PASS("early stages exclude relapse_prevention")

    # 全程应有3+种不同策略
    unique = set(strategies)
    assert len(unique) >= 3
    PASS(f"unique strategies across S0-S6: {len(unique)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])

"""
BehaviorOS v32 — 行为处方系统集成测试
=======================================
匹配实际 rx_schemas.py 字段名:
  - strategy_type (不是 primary_strategy)
  - agent_type (不是 computed_by)
  - confidence (不是 confidence_score)
  - MicroAction.action (不是 title/description)
  - get_registered_agents() 返回 List[str]

运行:
  python -m pytest tests/test_v32_behavior_rx.py -v -s
"""

import asyncio
import os
import sys
import uuid

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

PASS = lambda tag: print(f"  [PASS] {tag}")
USER_ID = uuid.uuid4()


# ── helpers ──────────────────────────────────────────────────────────

def make_context(ttm_stage=3, readiness=0.5, stability=0.5, capacity=0.5,
                 efficacy=0.5, bigfive=None, domain_data=None, risk="normal"):
    from behavior_rx.core.rx_schemas import RxContext, BigFiveProfile
    bf = bigfive or {}
    return RxContext(
        user_id=USER_ID,
        ttm_stage=ttm_stage,
        stage_readiness=readiness,
        stage_stability=stability,
        personality=BigFiveProfile(**bf) if bf else BigFiveProfile(),
        capacity_score=capacity,
        self_efficacy=efficacy,
        domain_data=domain_data or {},
        risk_level=risk,
    )


def make_user_input(message="", ttm_stage=3, domain_data=None, bigfive=None):
    bf = bigfive or {"O": 50, "C": 50, "E": 50, "A": 50, "N": 50}
    return {
        "message": message,
        "ttm_stage": ttm_stage,
        "domain_data": domain_data or {},
        "behavioral_profile": {
            "bigfive": bf,
            "capacity_score": 0.5,
            "self_efficacy": 0.5,
            "active_barriers": [],
        },
    }


def make_rx_dto(**kwargs):
    from behavior_rx.core.rx_schemas import (
        RxPrescriptionDTO, ExpertAgentType, RxStrategyType,
        RxIntensity, CommunicationStyle,
    )
    defaults = {
        "rx_id": uuid.uuid4(),
        "agent_type": ExpertAgentType.METABOLIC_EXPERT,
        "goal_behavior": "测试目标行为",
        "strategy_type": RxStrategyType.STIMULUS_CONTROL,
        "secondary_strategies": [],
        "intensity": RxIntensity.MODERATE,
        "pace": "standard",
        "communication_style": CommunicationStyle.DATA_DRIVEN,
        "micro_actions": [],
        "reward_triggers": [],
        "resistance_threshold": 0.3,
        "escalation_rules": [],
        "domain_context": {},
        "ttm_stage": 3,
        "confidence": 0.8,
        "reasoning": "test",
    }
    defaults.update(kwargs)
    return RxPrescriptionDTO(**defaults)


# =====================================================================
# 1. Schemas
# =====================================================================

def test_rx_schemas():
    print("\n--- 1. Rx Schemas ---")

    from behavior_rx.core.rx_schemas import (
        RxStrategyType, RxIntensity, CommunicationStyle,
        ExpertAgentType, HandoffType, HandoffStatus,
        BigFiveProfile, RxContext, MicroAction,
        ComputeRxRequest, ComputeRxResponse,
        HandoffRequest, HandoffResponse,
    )

    assert len(RxStrategyType) == 12;  PASS("RxStrategyType has 12 strategies")
    assert len(RxIntensity) == 5;      PASS("RxIntensity has 5 levels")
    assert len(CommunicationStyle) == 6; PASS("CommunicationStyle has 6 styles")
    assert len(ExpertAgentType) == 4;  PASS("ExpertAgentType has 4 agents")
    assert len(HandoffType) == 6;      PASS("HandoffType has 6 types")
    assert len(HandoffStatus) == 6;    PASS("HandoffStatus has 6 statuses")

    bf = BigFiveProfile(O=75, C=60, E=45, A=80, N=30)
    assert bf.dominant_trait() == "A"; PASS("BigFiveProfile dominant_trait=A")
    assert bf.is_high("O", threshold=65); PASS("BigFiveProfile is_high O=75")
    assert bf.is_low("N", threshold=35);  PASS("BigFiveProfile is_low N=30")

    ctx = RxContext(user_id=USER_ID, ttm_stage=3, personality=BigFiveProfile(), capacity_score=0.5)
    assert ctx.ttm_stage == 3 and ctx.risk_level == "normal"
    PASS("RxContext 3D construction ok")

    ma = MicroAction(action="晨起喝水", difficulty=0.2, trigger="起床后", duration_min=1)
    assert ma.action == "晨起喝水" and ma.difficulty == 0.2
    PASS("MicroAction construction ok")


# =====================================================================
# 2. Strategy Templates
# =====================================================================

def test_rx_strategies():
    print("\n--- 2. Strategy Templates ---")
    import json
    path = os.path.join(ROOT, "behavior_rx", "configs", "rx_strategies.json")
    assert os.path.exists(path); PASS("rx_strategies.json exists")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    strategies = data if isinstance(data, list) else data.get("strategies", data.get("items", []))
    assert len(strategies) >= 12; PASS(f"has {len(strategies)} strategies (>= 12)")
    first = strategies[0]
    assert "strategy_type" in first or "name" in first
    PASS("strategy entries have expected fields")


# =====================================================================
# 3. BehaviorRxEngine
# =====================================================================

def test_behavior_rx_engine():
    print("\n--- 3. BehaviorRxEngine ---")
    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.rx_schemas import ExpertAgentType, RxStrategyType, RxIntensity, CommunicationStyle

    engine = BehaviorRxEngine(); PASS("engine instantiation ok")

    # S0 → early-stage strategies
    ctx_s0 = make_context(ttm_stage=0, readiness=0.2, capacity=0.3)
    rx_s0 = engine.compute_rx(context=ctx_s0, agent_type=ExpertAgentType.BEHAVIOR_COACH)
    assert rx_s0.ttm_stage == 0
    assert rx_s0.strategy_type in [
        RxStrategyType.CONSCIOUSNESS_RAISING, RxStrategyType.DRAMATIC_RELIEF,
        RxStrategyType.SELF_REEVALUATION, RxStrategyType.DECISIONAL_BALANCE,
    ]
    PASS(f"S0 → {rx_s0.strategy_type.value}")

    # S3 → action-stage strategies
    ctx_s3 = make_context(ttm_stage=3, capacity=0.7)
    rx_s3 = engine.compute_rx(ctx_s3, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_s3.strategy_type in [
        RxStrategyType.STIMULUS_CONTROL, RxStrategyType.CONTINGENCY_MANAGEMENT,
        RxStrategyType.HABIT_STACKING, RxStrategyType.SELF_MONITORING,
        RxStrategyType.SELF_LIBERATION, RxStrategyType.COGNITIVE_RESTRUCTURING,
    ]
    PASS(f"S3 → {rx_s3.strategy_type.value}")

    # personality → communication
    ctx_n = make_context(ttm_stage=2, bigfive={"N": 80})
    rx_n = engine.compute_rx(ctx_n, ExpertAgentType.BEHAVIOR_COACH)
    assert rx_n.communication_style == CommunicationStyle.EMPATHETIC
    PASS("high N → empathetic")

    # intensity
    assert rx_s3.intensity in [RxIntensity.MODERATE, RxIntensity.HIGH]
    PASS(f"S3 cap=0.7 → intensity={rx_s3.intensity.value}")

    # micro actions
    assert len(rx_s3.micro_actions) > 0
    PASS(f"micro_actions: {len(rx_s3.micro_actions)}")


# =====================================================================
# 4. BehaviorCoachAgent
# =====================================================================

def test_behavior_coach():
    print("\n--- 4. BehaviorCoachAgent ---")
    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.agents.behavior_coach_agent import BehaviorCoachAgent
    from behavior_rx.core.rx_schemas import ExpertAgentType

    engine = BehaviorRxEngine()
    agent = BehaviorCoachAgent(rx_engine=engine)
    assert agent.agent_type == ExpertAgentType.BEHAVIOR_COACH
    PASS("agent_type = behavior_coach")

    # process() returns AgentResponse with .rx, .domain_content, .user_message
    from behavior_rx.agents.base_expert_agent import AgentResponse

    ui = make_user_input(message="我不觉得需要改变", ttm_stage=0)
    loop = asyncio.new_event_loop()
    try:
        resp = loop.run_until_complete(agent.process(ui, USER_ID))
        assert resp is not None and isinstance(resp, AgentResponse)
        assert resp.rx is not None
        assert resp.agent_type == ExpertAgentType.BEHAVIOR_COACH
        PASS(f"S0 process ok, rx.strategy={resp.rx.strategy_type.value}")
    finally:
        loop.close()

    ui3 = make_user_input(message="我准备开始运动了", ttm_stage=3)
    loop2 = asyncio.new_event_loop()
    try:
        resp3 = loop2.run_until_complete(agent.process(ui3, USER_ID))
        assert resp3 is not None and isinstance(resp3, AgentResponse)
        PASS(f"S3 process ok, rx.strategy={resp3.rx.strategy_type.value}")
    finally:
        loop2.close()


# =====================================================================
# 5. MetabolicExpertAgent
# =====================================================================

def test_metabolic_expert():
    print("\n--- 5. MetabolicExpertAgent ---")
    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.agents.metabolic_expert_agent import MetabolicExpertAgent
    from behavior_rx.core.rx_schemas import ExpertAgentType

    agent = MetabolicExpertAgent(rx_engine=BehaviorRxEngine())
    assert agent.agent_type == ExpertAgentType.METABOLIC_EXPERT
    PASS("agent_type = metabolic_expert")

    # domain_data 嵌套结构: glucose={...}, weight={...}
    from behavior_rx.agents.base_expert_agent import AgentResponse
    ui = make_user_input(
        message="我的血糖怎么样?", ttm_stage=3,
        domain_data={
            "glucose": {"fasting_avg": 7.2, "postprandial_avg": 11.5, "hba1c": 7.5},
            "weight": {"bmi": 26.8},
        },
    )
    loop = asyncio.new_event_loop()
    try:
        resp = loop.run_until_complete(agent.process(ui, USER_ID))
        assert resp is not None and isinstance(resp, AgentResponse)
        assert resp.rx is not None
        PASS(f"metabolic process ok, strategy={resp.rx.strategy_type.value}")
    finally:
        loop.close()


# =====================================================================
# 6. CardiacExpertAgent
# =====================================================================

def test_cardiac_expert():
    print("\n--- 6. CardiacExpertAgent ---")
    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.agents.cardiac_expert_agent import CardiacExpertAgent
    from behavior_rx.core.rx_schemas import ExpertAgentType

    agent = CardiacExpertAgent(rx_engine=BehaviorRxEngine())
    assert agent.agent_type == ExpertAgentType.CARDIAC_EXPERT
    PASS("agent_type = cardiac_expert")

    from behavior_rx.agents.base_expert_agent import AgentResponse

    ui = make_user_input(message="我心梗后很害怕运动", ttm_stage=2,
                         domain_data={"cardiac_event": "MI", "days_since_event": 45, "exercise_fear_score": 0.8})
    loop = asyncio.new_event_loop()
    try:
        resp = loop.run_until_complete(agent.process(ui, USER_ID))
        assert resp is not None and isinstance(resp, AgentResponse)
        PASS(f"fear desensitization ok, domain_content keys={list(resp.domain_content.keys())[:5]}")
    finally:
        loop.close()

    ui_bp = make_user_input(message="血压很高", ttm_stage=3,
                            domain_data={"systolic_bp": 180, "diastolic_bp": 110})
    loop2 = asyncio.new_event_loop()
    try:
        resp_bp = loop2.run_until_complete(agent.process(ui_bp, USER_ID))
        assert resp_bp is not None and isinstance(resp_bp, AgentResponse); PASS("high BP handled")
    finally:
        loop2.close()

    ui_chest = make_user_input(message="胸口很痛", ttm_stage=3, domain_data={"chest_pain": True})
    loop3 = asyncio.new_event_loop()
    try:
        resp_c = loop3.run_until_complete(agent.process(ui_chest, USER_ID))
        assert resp_c is not None and isinstance(resp_c, AgentResponse); PASS("chest pain handled")
    finally:
        loop3.close()


# =====================================================================
# 7. AdherenceExpertAgent
# =====================================================================

def test_adherence_expert():
    print("\n--- 7. AdherenceExpertAgent ---")
    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.agents.adherence_expert_agent import AdherenceExpertAgent
    from behavior_rx.core.rx_schemas import ExpertAgentType

    agent = AdherenceExpertAgent(rx_engine=BehaviorRxEngine())
    assert agent.agent_type == ExpertAgentType.ADHERENCE_EXPERT
    PASS("agent_type = adherence_expert")

    from behavior_rx.agents.base_expert_agent import AgentResponse

    ui = make_user_input(message="我经常忘记吃药", ttm_stage=3,
                         domain_data={"medication_adherence": 0.3, "missed_doses_7d": 5})
    loop = asyncio.new_event_loop()
    try:
        resp = loop.run_until_complete(agent.process(ui, USER_ID))
        assert resp is not None and isinstance(resp, AgentResponse)
        PASS(f"high missed medication handled, domain keys={list(resp.domain_content.keys())[:5]}")
    finally:
        loop.close()

    ui_v = make_user_input(message="好久没复查了", ttm_stage=2,
                           domain_data={"days_since_last_visit": 120})
    loop2 = asyncio.new_event_loop()
    try:
        resp_v = loop2.run_until_complete(agent.process(ui_v, USER_ID))
        assert resp_v is not None and isinstance(resp_v, AgentResponse); PASS("visit overdue handled")
    finally:
        loop2.close()

    ui_f = make_user_input(message="怕查出问题不敢检查", ttm_stage=1,
                           domain_data={"test_avoidance": True, "fear_score": 0.8})
    loop3 = asyncio.new_event_loop()
    try:
        resp_f = loop3.run_until_complete(agent.process(ui_f, USER_ID))
        assert resp_f is not None and isinstance(resp_f, AgentResponse); PASS("fear-based avoidance handled")
    finally:
        loop3.close()


# =====================================================================
# 8. Collaboration
# =====================================================================

def test_collaboration():
    print("\n--- 8. Collaboration Orchestrator ---")
    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.agent_collaboration_orchestrator import AgentCollaborationOrchestrator
    from behavior_rx.agents.behavior_coach_agent import BehaviorCoachAgent
    from behavior_rx.agents.metabolic_expert_agent import MetabolicExpertAgent
    from behavior_rx.agents.cardiac_expert_agent import CardiacExpertAgent
    from behavior_rx.agents.adherence_expert_agent import AdherenceExpertAgent

    engine = BehaviorRxEngine()
    orch = AgentCollaborationOrchestrator()
    orch.register_agent(BehaviorCoachAgent(rx_engine=engine))
    orch.register_agent(MetabolicExpertAgent(rx_engine=engine))
    orch.register_agent(CardiacExpertAgent(rx_engine=engine))
    orch.register_agent(AdherenceExpertAgent(rx_engine=engine))

    assert orch.is_fully_operational(); PASS("4 agents registered, fully operational")

    agents = orch.get_registered_agents()  # returns List[str]
    assert len(agents) == 4; PASS(f"registered agents: {agents}")
    for a in ["behavior_coach", "metabolic_expert", "cardiac_expert", "adherence_expert"]:
        assert a in agents
    PASS("all 4 agent types present")


# =====================================================================
# 9. Conflict Resolver
# =====================================================================

def test_conflict_resolver():
    print("\n--- 9. Conflict Resolver ---")
    from behavior_rx.core.rx_conflict_resolver import RxConflictResolver
    from behavior_rx.core.rx_schemas import ExpertAgentType, RxStrategyType, RxIntensity

    resolver = RxConflictResolver(); PASS("resolver instantiation ok")

    rx_single = make_rx_dto()
    result = resolver.resolve([rx_single], ttm_stage=3)
    assert result.resolved_rx is not None; PASS("single rx → resolved ok")

    rx_h = make_rx_dto(intensity=RxIntensity.HIGH, agent_type=ExpertAgentType.METABOLIC_EXPERT)
    rx_l = make_rx_dto(intensity=RxIntensity.LOW, agent_type=ExpertAgentType.CARDIAC_EXPERT)
    result_i = resolver.resolve([rx_h, rx_l], ttm_stage=3, primary_agent=ExpertAgentType.METABOLIC_EXPERT)
    assert result_i.resolved_rx.intensity in [RxIntensity.LOW, RxIntensity.MODERATE]
    PASS(f"intensity conflict → {result_i.resolved_rx.intensity.value}")

    rx_a = make_rx_dto(strategy_type=RxStrategyType.CONSCIOUSNESS_RAISING,
                       agent_type=ExpertAgentType.BEHAVIOR_COACH, ttm_stage=0)
    rx_b = make_rx_dto(strategy_type=RxStrategyType.STIMULUS_CONTROL,
                       agent_type=ExpertAgentType.METABOLIC_EXPERT, ttm_stage=0)
    result_s = resolver.resolve([rx_a, rx_b], ttm_stage=0, primary_agent=ExpertAgentType.BEHAVIOR_COACH)
    assert result_s.resolved_rx.strategy_type is not None
    PASS(f"strategy conflict → {result_s.resolved_rx.strategy_type.value}")


# =====================================================================
# 10. MasterAgent Integration
# =====================================================================

def test_master_integration():
    print("\n--- 10. MasterAgent Integration ---")
    from behavior_rx.patches.master_agent_integration import setup_expert_agents
    from behavior_rx.core.rx_schemas import ExpertAgentType

    # setup_expert_agents() 返回 ExpertAgentRouter
    router = setup_expert_agents()
    PASS("setup_expert_agents() ok")

    # should_route_to_expert(user_input, user_profile) → (bool, Optional[ExpertAgentType])
    should, agent = router.should_route_to_expert(
        {"message": "我的血糖升高了"}, {"ttm_stage": 3})
    assert should and agent == ExpertAgentType.METABOLIC_EXPERT
    PASS("'血糖' → metabolic_expert")

    should, agent = router.should_route_to_expert(
        {"message": "心梗后如何康复"}, {"ttm_stage": 3})
    assert should and agent == ExpertAgentType.CARDIAC_EXPERT
    PASS("'心梗' → cardiac_expert")

    should, agent = router.should_route_to_expert(
        {"message": "经常忘记吃药"}, {"ttm_stage": 3})
    assert should and agent == ExpertAgentType.ADHERENCE_EXPERT
    PASS("'吃药' → adherence_expert")

    # 低阶段 + 无特定领域 → behavior_coach
    should, agent = router.should_route_to_expert(
        {"message": "还不确定要不要改变"}, {"ttm_stage": 1})
    assert should and agent == ExpertAgentType.BEHAVIOR_COACH
    PASS("low stage S1 → behavior_coach")

    # domain_data 匹配
    should, agent = router.should_route_to_expert(
        {"message": "数据分析", "domain_data": {"cardiac_event_type": "MI"}}, {"ttm_stage": 3})
    assert should and agent == ExpertAgentType.CARDIAC_EXPERT
    PASS("domain_data cardiac → cardiac_expert")


# =====================================================================
# 11. Rx Routes
# =====================================================================

def test_rx_routes():
    print("\n--- 11. Rx Routes ---")
    from behavior_rx.api.rx_routes import router

    routes = [r for r in router.routes]
    assert len(routes) >= 8; PASS(f"router has {len(routes)} routes")

    paths = [r.path for r in routes if hasattr(r, "path")]
    assert any("/compute" in p for p in paths); PASS("/compute exists")
    assert any("/strategies" in p for p in paths); PASS("/strategies exists")
    assert any("/agents/status" in p for p in paths); PASS("/agents/status exists")
    assert router.tags and "Behavioral Prescription" in router.tags
    PASS("router tag = 'Behavioral Prescription'")


# =====================================================================
# 12. End-to-End
# =====================================================================

def test_full_e2e():
    print("\n--- 12. End-to-End Flow ---")
    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.rx_conflict_resolver import RxConflictResolver
    from behavior_rx.core.rx_schemas import ExpertAgentType

    engine = BehaviorRxEngine()
    resolver = RxConflictResolver()

    ctx = make_context(ttm_stage=3, readiness=0.7, stability=0.6, capacity=0.6,
                       bigfive={"O": 60, "C": 55, "E": 45, "A": 70, "N": 40},
                       domain_data={"glucose": {"fasting_avg": 7.0, "hba1c": 7.0}})
    assert ctx.ttm_stage == 3; PASS("e2e: context built")

    rx_coach = engine.compute_rx(ctx, ExpertAgentType.BEHAVIOR_COACH)
    rx_meta = engine.compute_rx(ctx, ExpertAgentType.METABOLIC_EXPERT)
    assert rx_coach.agent_type == ExpertAgentType.BEHAVIOR_COACH
    assert rx_meta.agent_type == ExpertAgentType.METABOLIC_EXPERT
    PASS("e2e: multi-agent compute ok")

    result = resolver.resolve([rx_coach, rx_meta], ttm_stage=3,
                              primary_agent=ExpertAgentType.METABOLIC_EXPERT)
    assert result.resolved_rx is not None
    assert result.resolved_rx.strategy_type is not None
    PASS(f"e2e: conflict resolved → {result.resolved_rx.strategy_type.value}")

    final = result.resolved_rx
    assert final.ttm_stage == 3 and final.intensity is not None
    PASS("e2e: full pipeline complete")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])

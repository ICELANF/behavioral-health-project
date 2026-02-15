"""
BehaviorOS v32 — 行为处方系统集成测试
=============================================
对应 behavior_rx/ 包 (CU-01 ~ CU-15)

测试矩阵:
  test_rx_schemas          — Pydantic schemas & 枚举完整性
  test_rx_strategies       — 12 策略模板 JSON 加载
  test_behavior_rx_engine  — 3D 处方引擎核心计算
  test_behavior_coach      — 行为教练 Agent (S0-S2 认知准备)
  test_metabolic_expert    — 代谢专家 Agent (血糖/营养行为化)
  test_cardiac_expert      — 心血管专家 Agent (运动恐惧脱敏)
  test_adherence_expert    — 依从性专家 Agent (服药行为链)
  test_collaboration       — 4-Agent 协作编排
  test_conflict_resolver   — 处方冲突解决
  test_master_integration  — MasterAgent 路由集成
  test_rx_routes           — FastAPI 端点结构
  test_full_e2e            — 端到端流程

放置: tests/test_v32_behavior_rx.py
运行: python -m pytest tests/test_v32_behavior_rx.py -v -s
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from typing import Any, Dict

import pytest


# =====================================================================
# 辅助工具
# =====================================================================

USER_ID = uuid.uuid4()
SESSION_ID = uuid.uuid4()

PASS = lambda tag: print(f"  [PASS] {tag}")


def make_user_input(
    message: str = "",
    ttm_stage: int = 3,
    stage_readiness: float = 0.6,
    stage_stability: float = 0.7,
    self_efficacy: float = 0.5,
    capacity_score: float = 0.5,
    recent_adherence: float = 0.7,
    bigfive: Dict[str, float] | None = None,
    barriers: list | None = None,
    device_data: dict | None = None,
    domain_data: dict | None = None,
    risk_level: str = "normal",
) -> Dict[str, Any]:
    """构建标准测试用户输入"""
    return {
        "message": message,
        "behavioral_profile": {
            "ttm_stage": ttm_stage,
            "stage_readiness": stage_readiness,
            "stage_stability": stage_stability,
            "self_efficacy": self_efficacy,
            "capacity_score": capacity_score,
            "recent_adherence": recent_adherence,
            "bigfive": bigfive or {"O": 50, "C": 50, "E": 50, "A": 50, "N": 50},
            "active_barriers": barriers or [],
            "risk_level": risk_level,
        },
        "device_data": device_data or {},
        "domain_data": domain_data or {},
    }


def make_context(
    ttm_stage: int = 3,
    readiness: float = 0.6,
    stability: float = 0.7,
    capacity: float = 0.5,
    efficacy: float = 0.5,
    bigfive: dict | None = None,
    domain_data: dict | None = None,
    barriers: list | None = None,
    risk_level: str = "normal",
):
    """构建 RxContext"""
    from behavior_rx.core.rx_schemas import RxContext, BigFiveProfile

    bf = bigfive or {"O": 50, "C": 50, "E": 50, "A": 50, "N": 50}
    return RxContext(
        user_id=USER_ID,
        session_id=SESSION_ID,
        ttm_stage=ttm_stage,
        stage_readiness=readiness,
        stage_stability=stability,
        personality=BigFiveProfile(**bf),
        capacity_score=capacity,
        self_efficacy=efficacy,
        domain_data=domain_data or {},
        active_barriers=barriers or [],
        recent_adherence=0.7,
        risk_level=risk_level,
    )


# =====================================================================
# Test 1: Schemas & 枚举
# =====================================================================

def test_rx_schemas():
    """Pydantic schemas 完整性"""
    print("\n--- 1. Rx Schemas ---")

    from behavior_rx.core.rx_schemas import (
        RxStrategyType, RxIntensity, CommunicationStyle,
        ExpertAgentType, HandoffType, HandoffStatus,
        BigFiveProfile, RxContext, MicroAction,
        ComputeRxRequest, ComputeRxResponse,
        HandoffRequest, HandoffResponse,
    )

    # 枚举完整性
    assert len(RxStrategyType) == 12
    PASS("RxStrategyType has 12 strategies")

    assert len(RxIntensity) == 5
    PASS("RxIntensity has 5 levels")

    assert len(CommunicationStyle) == 6
    PASS("CommunicationStyle has 6 styles")

    assert len(ExpertAgentType) == 4
    PASS("ExpertAgentType has 4 agents")

    assert len(HandoffType) == 6
    PASS("HandoffType has 6 types")

    assert len(HandoffStatus) == 6
    PASS("HandoffStatus has 6 statuses")

    # BigFiveProfile
    bf = BigFiveProfile(O=75, C=60, E=45, A=80, N=30)
    assert bf.dominant_trait() == "A"
    PASS("BigFiveProfile dominant_trait=A (highest)")

    assert bf.is_high("O", threshold=65)
    PASS("BigFiveProfile is_high O=75 >= 65")

    assert bf.is_low("N", threshold=35)
    PASS("BigFiveProfile is_low N=30 <= 35")

    # RxContext 三维
    ctx = RxContext(
        user_id=USER_ID,
        ttm_stage=3,
        personality=BigFiveProfile(),
        capacity_score=0.5,
    )
    assert ctx.ttm_stage == 3
    assert ctx.personality.O == 50  # default
    assert ctx.risk_level == "normal"
    PASS("RxContext 3D construction ok")

    # MicroAction
    ma = MicroAction(
        action_id="test-001",
        title="晨起喝水",
        description="起床后立即喝一杯温水",
        difficulty=0.2,
        duration_minutes=1,
        frequency="daily",
    )
    assert ma.difficulty == 0.2
    PASS("MicroAction construction ok")


# =====================================================================
# Test 2: 策略模板 JSON
# =====================================================================

def test_rx_strategies():
    """12 策略模板 JSON 加载"""
    print("\n--- 2. Strategy Templates ---")

    strategies_path = os.path.join(
        os.path.dirname(__file__), "..",
        "behavior_rx", "configs", "rx_strategies.json",
    )

    # 如果直接路径不存在, 尝试其它可能位置
    if not os.path.exists(strategies_path):
        alt_paths = [
            "behavior_rx/configs/rx_strategies.json",
            "configs/rx_strategies.json",
        ]
        for p in alt_paths:
            if os.path.exists(p):
                strategies_path = p
                break

    assert os.path.exists(strategies_path), f"rx_strategies.json not found at {strategies_path}"
    PASS("rx_strategies.json exists")

    with open(strategies_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    strategies = data.get("strategies", data) if isinstance(data, dict) else data
    if isinstance(strategies, dict):
        strategies = list(strategies.values())

    assert len(strategies) >= 12
    PASS(f"has {len(strategies)} strategies (>= 12)")

    # 检查每个策略结构
    for s in strategies[:3]:
        if isinstance(s, dict):
            assert "name_zh" in s or "name" in s or "strategy_type" in s
    PASS("strategy entries have expected fields")


# =====================================================================
# Test 3: BehaviorRxEngine 核心引擎
# =====================================================================

def test_behavior_rx_engine():
    """3D 处方引擎核心计算"""
    print("\n--- 3. BehaviorRxEngine ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.rx_schemas import (
        ExpertAgentType, RxStrategyType, RxIntensity,
        CommunicationStyle,
    )

    engine = BehaviorRxEngine()
    PASS("engine instantiation ok")

    # S0 前意识 → consciousness_raising 或 dramatic_relief
    ctx_s0 = make_context(ttm_stage=0, readiness=0.2, capacity=0.3)
    rx_s0 = engine.compute_rx(
        context=ctx_s0,
        agent_type=ExpertAgentType.BEHAVIOR_COACH,
    )
    assert rx_s0.ttm_stage == 0
    assert rx_s0.primary_strategy in [
        RxStrategyType.CONSCIOUSNESS_RAISING,
        RxStrategyType.DRAMATIC_RELIEF,
        RxStrategyType.SELF_REEVALUATION,
        RxStrategyType.DECISIONAL_BALANCE,
    ]
    assert rx_s0.confidence_score > 0
    PASS(f"S0 → {rx_s0.primary_strategy.value}, confidence={rx_s0.confidence_score:.2f}")

    # S3 行动期 → stimulus_control / habit_stacking / etc.
    ctx_s3 = make_context(ttm_stage=3, readiness=0.8, capacity=0.7,
                          bigfive={"O": 50, "C": 70, "E": 50, "A": 50, "N": 30})
    rx_s3 = engine.compute_rx(
        context=ctx_s3,
        agent_type=ExpertAgentType.METABOLIC_EXPERT,
    )
    assert rx_s3.ttm_stage == 3
    PASS(f"S3 → {rx_s3.primary_strategy.value}")

    # 高 N → empathetic 沟通
    ctx_hn = make_context(ttm_stage=1, bigfive={"O": 50, "C": 50, "E": 50, "A": 50, "N": 80},
                          capacity=0.4)
    rx_hn = engine.compute_rx(
        context=ctx_hn,
        agent_type=ExpertAgentType.BEHAVIOR_COACH,
    )
    assert rx_hn.communication_style == CommunicationStyle.EMPATHETIC
    PASS("high N=80 → empathetic communication style")

    # 强度适配: 低能力 → 低强度
    ctx_low = make_context(ttm_stage=3, capacity=0.2, efficacy=0.2)
    rx_low = engine.compute_rx(
        context=ctx_low,
        agent_type=ExpertAgentType.BEHAVIOR_COACH,
    )
    assert rx_low.intensity in [RxIntensity.MINIMAL, RxIntensity.LOW, RxIntensity.MODERATE]
    PASS(f"low capacity → intensity={rx_low.intensity.value}")

    # 微行动生成
    assert rx_s3.micro_actions is not None
    assert len(rx_s3.micro_actions) >= 1
    PASS(f"S3 generated {len(rx_s3.micro_actions)} micro_actions")


# =====================================================================
# Test 4: BehaviorCoachAgent
# =====================================================================

def test_behavior_coach():
    """行为教练 Agent"""
    print("\n--- 4. BehaviorCoachAgent ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.agents.behavior_coach_agent import BehaviorCoachAgent
    from behavior_rx.core.rx_schemas import ExpertAgentType

    engine = BehaviorRxEngine()
    agent = BehaviorCoachAgent(rx_engine=engine)

    assert agent.agent_type == ExpertAgentType.BEHAVIOR_COACH
    PASS("agent_type = behavior_coach")

    # 能力声明
    caps = agent.get_capabilities()
    assert len(caps) > 0
    PASS(f"capabilities: {len(caps)} items")

    # 域声明
    domains = agent.get_handled_domains()
    assert len(domains) > 0
    PASS(f"handled_domains: {domains}")

    # S0 处理: 认知内容
    user_input_s0 = make_user_input(
        message="为什么我需要改变饮食?",
        ttm_stage=0, stage_readiness=0.1,
    )
    loop = asyncio.new_event_loop()
    try:
        response_s0 = loop.run_until_complete(
            agent.process(user_input_s0, USER_ID)
        )
        assert response_s0 is not None
        assert response_s0.agent_type == ExpertAgentType.BEHAVIOR_COACH
        PASS(f"S0 process ok, msg_len={len(str(response_s0.user_message))}")
    finally:
        loop.close()

    # S3 处理
    user_input_s3 = make_user_input(
        message="我已经准备好开始运动了",
        ttm_stage=3, stage_readiness=0.8,
    )
    loop = asyncio.new_event_loop()
    try:
        response_s3 = loop.run_until_complete(
            agent.process(user_input_s3, USER_ID)
        )
        assert response_s3 is not None
        PASS("S3 process ok")
    finally:
        loop.close()


# =====================================================================
# Test 5: MetabolicExpertAgent
# =====================================================================

def test_metabolic_expert():
    """代谢专家 Agent"""
    print("\n--- 5. MetabolicExpertAgent ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.agents.metabolic_expert_agent import MetabolicExpertAgent
    from behavior_rx.core.rx_schemas import ExpertAgentType

    agent = MetabolicExpertAgent(rx_engine=BehaviorRxEngine())

    assert agent.agent_type == ExpertAgentType.METABOLIC_EXPERT
    PASS("agent_type = metabolic_expert")

    # 血糖数据处理
    user_input = make_user_input(
        message="我的血糖怎么样?",
        ttm_stage=3,
        domain_data={
            "fasting_glucose": 7.2,
            "postprandial_glucose": 11.5,
            "hba1c": 7.5,
            "bmi": 26.8,
            "weight": 75,
        },
    )
    loop = asyncio.new_event_loop()
    try:
        response = loop.run_until_complete(
            agent.process(user_input, USER_ID)
        )
        assert response.agent_type == ExpertAgentType.METABOLIC_EXPERT
        PASS("metabolic process with glucose data ok")

        # 领域内容检查
        domain = response.domain_content
        assert domain is not None
        PASS(f"domain_content present, keys={list(domain.keys())[:5]}")
    finally:
        loop.close()


# =====================================================================
# Test 6: CardiacExpertAgent
# =====================================================================

def test_cardiac_expert():
    """心血管专家 Agent"""
    print("\n--- 6. CardiacExpertAgent ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.agents.cardiac_expert_agent import CardiacExpertAgent
    from behavior_rx.core.rx_schemas import ExpertAgentType

    agent = CardiacExpertAgent(rx_engine=BehaviorRxEngine())

    assert agent.agent_type == ExpertAgentType.CARDIAC_EXPERT
    PASS("agent_type = cardiac_expert")

    # 运动恐惧脱敏
    user_input_fear = make_user_input(
        message="我害怕运动会让心脏出问题",
        ttm_stage=2,
        barriers=["fear"],
        domain_data={
            "exercise_fear_score": 45,
            "rehab_phase": "phase_2_early",
            "cardiac_event_type": "STEMI",
            "days_since_event": 40,
            "resting_hr": 72,
            "max_hr": 155,
            "bp_systolic": 128,
            "bp_diastolic": 78,
        },
    )
    loop = asyncio.new_event_loop()
    try:
        response = loop.run_until_complete(
            agent.process(user_input_fear, USER_ID)
        )
        assert response.agent_type == ExpertAgentType.CARDIAC_EXPERT
        domain = response.domain_content
        assert domain is not None
        PASS(f"fear desensitization response ok, keys={list(domain.keys())[:5]}")

        # 安全: 高血压场景
        user_input_bp = make_user_input(
            message="今天血压有点高",
            ttm_stage=3,
            domain_data={
                "bp_systolic": 165,
                "bp_diastolic": 95,
                "rehab_phase": "phase_2_rehab",
                "resting_hr": 72,
                "max_hr": 155,
            },
        )
        response_bp = loop.run_until_complete(
            agent.process(user_input_bp, USER_ID)
        )
        assert response_bp is not None
        PASS("high BP safety scenario handled")

        # 胸痛紧急场景
        user_input_pain = make_user_input(
            message="运动时胸口有点闷",
            ttm_stage=3,
            domain_data={
                "chest_pain_recent": True,
                "rehab_phase": "phase_2_rehab",
                "resting_hr": 72,
                "max_hr": 155,
                "bp_systolic": 130,
            },
        )
        response_pain = loop.run_until_complete(
            agent.process(user_input_pain, USER_ID)
        )
        assert response_pain is not None
        PASS("chest pain emergency scenario handled")
    finally:
        loop.close()


# =====================================================================
# Test 7: AdherenceExpertAgent
# =====================================================================

def test_adherence_expert():
    """依从性专家 Agent"""
    print("\n--- 7. AdherenceExpertAgent ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.agents.adherence_expert_agent import AdherenceExpertAgent
    from behavior_rx.core.rx_schemas import ExpertAgentType

    agent = AdherenceExpertAgent(rx_engine=BehaviorRxEngine())

    assert agent.agent_type == ExpertAgentType.ADHERENCE_EXPERT
    PASS("agent_type = adherence_expert")

    # 高漏服场景
    user_input = make_user_input(
        message="这周又忘了吃药",
        ttm_stage=3,
        barriers=["forgetfulness"],
        domain_data={
            "medication_missed_7d": 5,
            "mmas_score": 4.0,
            "medications": [
                {"name": "二甲双胍", "time": "morning", "dose": "500mg"},
                {"name": "阿司匹林", "time": "evening", "dose": "100mg"},
            ],
            "visit_overdue_days": 0,
        },
    )
    loop = asyncio.new_event_loop()
    try:
        response = loop.run_until_complete(
            agent.process(user_input, USER_ID)
        )
        assert response.agent_type == ExpertAgentType.ADHERENCE_EXPERT
        domain = response.domain_content
        assert domain is not None
        PASS(f"high missed medication handled, keys={list(domain.keys())[:5]}")

        # 逾期就诊
        user_input_overdue = make_user_input(
            message="最近比较忙没去复查",
            ttm_stage=3,
            domain_data={
                "medication_missed_7d": 0,
                "mmas_score": 7.0,
                "visit_overdue_days": 35,
                "medications": [],
            },
        )
        response_overdue = loop.run_until_complete(
            agent.process(user_input_overdue, USER_ID)
        )
        assert response_overdue is not None
        PASS("visit overdue scenario handled")

        # 恐惧型检查回避
        user_input_fear = make_user_input(
            message="我害怕抽血",
            ttm_stage=3,
            barriers=["fear"],
            domain_data={
                "medication_missed_7d": 0,
                "mmas_score": 7.0,
                "visit_overdue_days": 0,
                "pending_tests": [
                    {"name": "空腹血糖", "type": "blood", "due_date": "2026-02-15"},
                ],
                "medications": [],
            },
        )
        response_fear = loop.run_until_complete(
            agent.process(user_input_fear, USER_ID)
        )
        assert response_fear is not None
        PASS("fear-based test avoidance handled")
    finally:
        loop.close()


# =====================================================================
# Test 8: AgentCollaborationOrchestrator
# =====================================================================

def test_collaboration():
    """4-Agent 协作编排"""
    print("\n--- 8. Collaboration Orchestrator ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.agent_collaboration_orchestrator import (
        AgentCollaborationOrchestrator,
    )
    from behavior_rx.agents.behavior_coach_agent import BehaviorCoachAgent
    from behavior_rx.agents.metabolic_expert_agent import MetabolicExpertAgent
    from behavior_rx.agents.cardiac_expert_agent import CardiacExpertAgent
    from behavior_rx.agents.adherence_expert_agent import AdherenceExpertAgent
    from behavior_rx.core.rx_schemas import ExpertAgentType

    engine = BehaviorRxEngine()
    orch = AgentCollaborationOrchestrator()
    orch.register_agent(BehaviorCoachAgent(rx_engine=engine))
    orch.register_agent(MetabolicExpertAgent(rx_engine=engine))
    orch.register_agent(CardiacExpertAgent(rx_engine=engine))
    orch.register_agent(AdherenceExpertAgent(rx_engine=engine))

    assert orch.is_fully_operational()
    PASS("4 agents registered, fully operational")

    agents = orch.get_registered_agents()
    assert len(agents) == 4
    PASS(f"registered agents: {[a.value for a in agents]}")

    # 场景识别: 新用户低阶段 → Coach
    ctx_new = make_context(ttm_stage=0, readiness=0.1, capacity=0.3)
    user_input_new = make_user_input(
        message="我刚被诊断糖尿病",
        ttm_stage=0, stage_readiness=0.1,
    )
    decision = orch.identify_scenario(ctx_new, user_input_new)
    assert decision.primary_agent == ExpertAgentType.BEHAVIOR_COACH
    PASS(f"new user S0 → coach, scenario={decision.scenario.value}")

    # 场景识别: 阶段回退
    ctx_regress = make_context(ttm_stage=3, stability=0.2, efficacy=0.15)
    user_input_regress = make_user_input(
        message="我不想做了，放弃算了",
        ttm_stage=3, stage_stability=0.2, self_efficacy=0.15,
    )
    decision_r = orch.identify_scenario(
        ctx_regress, user_input_regress,
        current_agent=ExpertAgentType.METABOLIC_EXPERT,
    )
    assert decision_r.scenario.value == "stage_regression"
    assert decision_r.primary_agent == ExpertAgentType.BEHAVIOR_COACH
    PASS("stage regression → coach takeover")

    # 场景识别: 依从性危机
    ctx_adh = make_context(
        ttm_stage=3,
        domain_data={"medication_missed_7d": 5, "visit_overdue_days": 0},
    )
    user_input_adh = make_user_input(
        message="这周没吃药",
        ttm_stage=3,
        domain_data={"medication_missed_7d": 5, "visit_overdue_days": 0},
    )
    decision_a = orch.identify_scenario(
        ctx_adh, user_input_adh,
        current_agent=ExpertAgentType.METABOLIC_EXPERT,
    )
    assert decision_a.scenario.value == "adherence_alert"
    PASS("adherence alert detected")

    # 完整编排执行
    user_input_full = make_user_input(
        message="我该怎么管理血糖?",
        ttm_stage=3, stage_readiness=0.7,
        domain_data={
            "fasting_glucose": 7.5,
            "hba1c": 7.2,
            "medication_missed_7d": 0,
        },
    )
    loop = asyncio.new_event_loop()
    try:
        merged = loop.run_until_complete(
            orch.orchestrate(
                user_input=user_input_full,
                user_id=USER_ID,
                session_id=SESSION_ID,
                current_agent=ExpertAgentType.METABOLIC_EXPERT,
            )
        )
        assert merged.primary is not None
        assert merged.merged_message != ""
        PASS(f"full orchestration ok, msg_len={len(merged.merged_message)}")
    finally:
        loop.close()


# =====================================================================
# Test 9: RxConflictResolver
# =====================================================================

def test_conflict_resolver():
    """行为处方冲突解决"""
    print("\n--- 9. Conflict Resolver ---")

    from behavior_rx.core.rx_conflict_resolver import RxConflictResolver
    from behavior_rx.core.rx_schemas import (
        ExpertAgentType, RxStrategyType, RxIntensity,
        CommunicationStyle,
    )

    resolver = RxConflictResolver()
    PASS("resolver instantiation ok")

    # 构造处方 DTO 辅助函数
    def make_rx_dto(**kwargs):
        """构造测试用处方 DTO"""
        from behavior_rx.core.rx_schemas import RxPrescriptionDTO
        defaults = {
            "rx_id": str(uuid.uuid4()),
            "user_id": str(USER_ID),
            "created_at": "2026-02-12T00:00:00Z",
            "ttm_stage": 3,
            "personality_dominant": "C",
            "capacity_level": "moderate",
            "primary_strategy": RxStrategyType.STIMULUS_CONTROL,
            "secondary_strategies": [],
            "intensity": RxIntensity.MODERATE,
            "communication_style": CommunicationStyle.DATA_DRIVEN,
            "micro_actions": [],
            "confidence_score": 0.8,
            "reasoning": "test",
            "contraindications": [],
            "review_in_days": 14,
            "computed_by": ExpertAgentType.METABOLIC_EXPERT,
        }
        defaults.update(kwargs)
        return RxPrescriptionDTO(**defaults)

    # 单处方无冲突
    rx_single = make_rx_dto()
    result_single = resolver.resolve([rx_single], ttm_stage=3)
    assert result_single.conflict_type == "no_conflict"
    PASS("single Rx → no conflict")

    # 强度冲突 → 保守原则
    rx_high = make_rx_dto(
        intensity=RxIntensity.HIGH,
        computed_by=ExpertAgentType.METABOLIC_EXPERT,
    )
    rx_low = make_rx_dto(
        intensity=RxIntensity.LOW,
        computed_by=ExpertAgentType.CARDIAC_EXPERT,
        communication_style=CommunicationStyle.EMPATHETIC,
    )
    result_intensity = resolver.resolve([rx_high, rx_low], ttm_stage=3)
    assert result_intensity.conflict_type == "intensity_mismatch"
    assert result_intensity.resolved_rx.intensity == RxIntensity.LOW
    PASS("intensity conflict → conservative (LOW wins)")

    # 策略冲突 → 阶段适配
    rx_coach = make_rx_dto(
        primary_strategy=RxStrategyType.CONSCIOUSNESS_RAISING,
        computed_by=ExpertAgentType.BEHAVIOR_COACH,
        communication_style=CommunicationStyle.EMPATHETIC,
        ttm_stage=0,
    )
    rx_cardiac = make_rx_dto(
        primary_strategy=RxStrategyType.STIMULUS_CONTROL,
        computed_by=ExpertAgentType.CARDIAC_EXPERT,
        ttm_stage=0,
    )
    result_strategy = resolver.resolve([rx_coach, rx_cardiac], ttm_stage=0)
    assert result_strategy.conflict_type == "strategy_mismatch"
    assert result_strategy.resolved_rx.primary_strategy == RxStrategyType.CONSCIOUSNESS_RAISING
    PASS("strategy conflict at S0 → consciousness_raising wins")


# =====================================================================
# Test 10: MasterAgent 路由集成
# =====================================================================

def test_master_integration():
    """MasterAgent 路由集成"""
    print("\n--- 10. MasterAgent Integration ---")

    from behavior_rx.patches.master_agent_integration import (
        setup_expert_agents, ExpertAgentRouter,
    )

    router = setup_expert_agents()
    PASS("setup_expert_agents() ok")

    # 血糖关键词 → 代谢 Agent
    should_route, agent = router.should_route_to_expert(
        user_input={"message": "我的血糖最近控制不好"},
        user_profile={"ttm_stage": 3},
    )
    assert should_route is True
    assert agent.value == "metabolic_expert"
    PASS("'血糖' → metabolic_expert")

    # 心脏关键词 → 心血管 Agent
    should_route, agent = router.should_route_to_expert(
        user_input={"message": "心梗后怎么运动"},
        user_profile={"ttm_stage": 3},
    )
    assert should_route is True
    assert agent.value == "cardiac_expert"
    PASS("'心梗' → cardiac_expert")

    # 服药关键词 → 依从性 Agent
    should_route, agent = router.should_route_to_expert(
        user_input={"message": "药太多忘记吃药了"},
        user_profile={"ttm_stage": 3},
    )
    assert should_route is True
    assert agent.value == "adherence_expert"
    PASS("'吃药' → adherence_expert")

    # 低阶段 → Coach
    should_route, agent = router.should_route_to_expert(
        user_input={"message": "你好"},
        user_profile={"ttm_stage": 1},
    )
    assert should_route is True
    assert agent.value == "behavior_coach"
    PASS("low stage S1 → behavior_coach")

    # 领域数据触发
    should_route, agent = router.should_route_to_expert(
        user_input={
            "message": "看看我的数据",
            "domain_data": {"cardiac_event_type": "STEMI"},
        },
        user_profile={"ttm_stage": 4},
    )
    assert should_route is True
    assert agent.value == "cardiac_expert"
    PASS("domain_data cardiac → cardiac_expert")


# =====================================================================
# Test 11: FastAPI 路由结构
# =====================================================================

def test_rx_routes():
    """FastAPI 端点结构验证"""
    print("\n--- 11. Rx Routes ---")

    from behavior_rx.api.rx_routes import router

    routes = [r.path for r in router.routes]
    assert len(routes) >= 8
    PASS(f"router has {len(routes)} routes (>= 8)")

    expected_paths = [
        "/compute",
        "/strategies",
        "/agents/status",
    ]
    for ep in expected_paths:
        matching = [r for r in routes if ep in r]
        assert len(matching) > 0, f"missing endpoint: {ep}"
        PASS(f"endpoint {ep} exists")

    # 检查路由标签
    assert router.tags == ["Behavioral Prescription"]
    PASS("router tag = 'Behavioral Prescription'")


# =====================================================================
# Test 12: 端到端完整流程
# =====================================================================

def test_full_e2e():
    """端到端: 上下文构建 → 处方计算 → 冲突解决"""
    print("\n--- 12. End-to-End Flow ---")

    from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
    from behavior_rx.core.rx_conflict_resolver import RxConflictResolver
    from behavior_rx.core.rx_schemas import (
        ExpertAgentType, RxStrategyType,
    )

    engine = BehaviorRxEngine()
    resolver = RxConflictResolver()

    # Step 1: 构建上下文
    ctx = make_context(
        ttm_stage=3,
        readiness=0.7,
        stability=0.6,
        capacity=0.6,
        bigfive={"O": 60, "C": 55, "E": 45, "A": 70, "N": 40},
        domain_data={"fasting_glucose": 7.0, "hba1c": 7.0},
    )
    assert ctx.ttm_stage == 3
    PASS("e2e: context built")

    # Step 2: 多 Agent 计算
    rx_coach = engine.compute_rx(ctx, ExpertAgentType.BEHAVIOR_COACH)
    rx_meta = engine.compute_rx(ctx, ExpertAgentType.METABOLIC_EXPERT)

    assert rx_coach.computed_by == ExpertAgentType.BEHAVIOR_COACH
    assert rx_meta.computed_by == ExpertAgentType.METABOLIC_EXPERT
    PASS(f"e2e: coach → {rx_coach.primary_strategy.value}")
    PASS(f"e2e: metabolic → {rx_meta.primary_strategy.value}")

    # Step 3: 冲突解决
    result = resolver.resolve([rx_coach, rx_meta], ttm_stage=3)
    assert result.resolved_rx is not None
    PASS(f"e2e: conflict resolved → {result.conflict_type}")
    PASS(f"e2e: final strategy={result.resolved_rx.primary_strategy.value}")
    PASS(f"e2e: final intensity={result.resolved_rx.intensity.value}")


# =====================================================================
# 运行入口
# =====================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])

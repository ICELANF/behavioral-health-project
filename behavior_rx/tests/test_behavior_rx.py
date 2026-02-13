"""
BehaviorOS — 行为处方系统集成测试
===================================
覆盖 4 款专家 Agent 的核心场景

测试矩阵:
  TestBehaviorRxEngine      — 处方引擎 3D 计算
  TestBehaviorCoachAgent    — 行为教练: S0-S2 认知准备
  TestMetabolicExpertAgent  — 代谢专家: 血糖/营养行为化
  TestCardiacExpertAgent    — 心血管专家: 运动恐惧脱敏
  TestAdherenceExpertAgent  — 依从性专家: 服药行为链
  TestCollaboration         — 4-Agent 协作编排
  TestConflictResolver      — 行为处方冲突解决
  TestMasterAgentIntegration— MasterAgent 集成路由
"""

from __future__ import annotations

import asyncio
import uuid
from typing import Any, Dict

import pytest

# =====================================================================
# 测试辅助工具
# =====================================================================

def make_user_input(
    message: str = "",
    ttm_stage: int = 3,
    stage_readiness: float = 0.6,
    stage_stability: float = 0.7,
    self_efficacy: float = 0.5,
    capacity_score: float = 0.5,
    recent_adherence: float = 0.7,
    bigfive: Dict[str, float] = None,
    barriers: list = None,
    device_data: dict = None,
    domain_data: dict = None,
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


USER_ID = uuid.uuid4()
SESSION_ID = uuid.uuid4()


# =====================================================================
# Test 1: BehaviorRxEngine 处方引擎
# =====================================================================

class TestBehaviorRxEngine:
    """测试行为处方引擎 3D 计算"""

    def setup_method(self):
        from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
        self.engine = BehaviorRxEngine()

    def test_compute_rx_low_stage(self):
        """S0 前意识 → consciousness_raising 策略"""
        from behavior_rx.core.rx_schemas import (
            RxContext, BigFiveProfile, ExpertAgentType, RxStrategyType,
        )
        ctx = RxContext(
            user_id=USER_ID,
            ttm_stage=0,
            stage_readiness=0.2,
            personality=BigFiveProfile(O=50, C=50, E=50, A=50, N=50),
            capacity_score=0.3,
        )
        rx = self.engine.compute_rx(
            context=ctx,
            agent_type=ExpertAgentType.BEHAVIOR_COACH,
        )
        assert rx.ttm_stage == 0
        assert rx.strategy_type in [
            RxStrategyType.CONSCIOUSNESS_RAISING,
            RxStrategyType.DRAMATIC_RELIEF,
        ]
        assert rx.goal_behavior != ""
        assert rx.confidence > 0

    def test_compute_rx_action_stage(self):
        """S3 行动期 → stimulus_control / habit_stacking"""
        from behavior_rx.core.rx_schemas import (
            RxContext, BigFiveProfile, ExpertAgentType, RxStrategyType,
        )
        ctx = RxContext(
            user_id=USER_ID,
            ttm_stage=3,
            stage_readiness=0.8,
            personality=BigFiveProfile(O=50, C=70, E=50, A=50, N=30),
            capacity_score=0.7,
        )
        rx = self.engine.compute_rx(
            context=ctx,
            agent_type=ExpertAgentType.METABOLIC_EXPERT,
        )
        assert rx.ttm_stage == 3
        assert rx.strategy_type in [
            RxStrategyType.STIMULUS_CONTROL,
            RxStrategyType.CONTINGENCY_MANAGEMENT,
            RxStrategyType.HABIT_STACKING,
            RxStrategyType.SELF_MONITORING,
        ]

    def test_high_neuroticism_empathetic_style(self):
        """高 N (神经质) → empathetic 沟通风格"""
        from behavior_rx.core.rx_schemas import (
            RxContext, BigFiveProfile, ExpertAgentType, CommunicationStyle,
        )
        ctx = RxContext(
            user_id=USER_ID,
            ttm_stage=1,
            personality=BigFiveProfile(O=50, C=50, E=50, A=50, N=80),
            capacity_score=0.4,
        )
        rx = self.engine.compute_rx(
            context=ctx,
            agent_type=ExpertAgentType.BEHAVIOR_COACH,
        )
        assert rx.communication_style == CommunicationStyle.EMPATHETIC

    def test_override_strategy(self):
        """策略覆盖 → 强制使用指定策略"""
        from behavior_rx.core.rx_schemas import (
            RxContext, BigFiveProfile, ExpertAgentType, RxStrategyType,
        )
        ctx = RxContext(
            user_id=USER_ID,
            ttm_stage=0,
            personality=BigFiveProfile(),
            capacity_score=0.5,
        )
        rx = self.engine.compute_rx(
            context=ctx,
            agent_type=ExpertAgentType.CARDIAC_EXPERT,
            override_strategy=RxStrategyType.SYSTEMATIC_DESENSITIZATION,
        )
        assert rx.strategy_type == RxStrategyType.SYSTEMATIC_DESENSITIZATION


# =====================================================================
# Test 2: BehaviorCoachAgent
# =====================================================================

class TestBehaviorCoachAgent:
    """测试行为阶段教练"""

    def setup_method(self):
        from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
        from behavior_rx.agents.behavior_coach_agent import BehaviorCoachAgent
        self.engine = BehaviorRxEngine()
        self.agent = BehaviorCoachAgent(rx_engine=self.engine)

    def test_agent_type(self):
        from behavior_rx.core.rx_schemas import ExpertAgentType
        assert self.agent.agent_type == ExpertAgentType.BEHAVIOR_COACH

    def test_low_stage_cognitive_content(self):
        """S0-S1 → 认知内容 (不推行为改变)"""
        user_input = make_user_input(
            message="为什么我需要改变饮食?",
            ttm_stage=0,
            stage_readiness=0.1,
        )
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self.agent.process(user_input, USER_ID)
        )
        assert response.agent_type.value == "behavior_coach"
        assert response.user_message != ""
        # S0 不应该推具体行为
        assert "计划" not in response.user_message or "认知" in str(response.domain_content)

    def test_high_stage_handoff_check(self):
        """S3+ → 检查是否需要交接到领域Agent"""
        user_input = make_user_input(
            message="我已经准备好开始运动了",
            ttm_stage=3,
            stage_readiness=0.8,
        )
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self.agent.process(user_input, USER_ID)
        )
        assert response is not None


# =====================================================================
# Test 3: MetabolicExpertAgent
# =====================================================================

class TestMetabolicExpertAgent:
    """测试代谢内分泌专家"""

    def setup_method(self):
        from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
        from behavior_rx.agents.metabolic_expert_agent import MetabolicExpertAgent
        self.agent = MetabolicExpertAgent(rx_engine=BehaviorRxEngine())

    def test_glucose_domain_content(self):
        """代谢数据 → 领域专业包装"""
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
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self.agent.process(user_input, USER_ID)
        )
        assert response.agent_type.value == "metabolic_expert"
        assert "glucose" in str(response.domain_content).lower() or \
               "血糖" in response.user_message


# =====================================================================
# Test 4: CardiacExpertAgent
# =====================================================================

class TestCardiacExpertAgent:
    """测试心血管/心脏康复专家"""

    def setup_method(self):
        from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
        from behavior_rx.agents.cardiac_expert_agent import CardiacExpertAgent
        self.agent = CardiacExpertAgent(rx_engine=BehaviorRxEngine())

    def test_high_fear_desensitization(self):
        """高运动恐惧 → 渐进脱敏策略"""
        user_input = make_user_input(
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
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self.agent.process(user_input, USER_ID)
        )
        assert response.agent_type.value == "cardiac_expert"
        domain = response.domain_content
        assert domain.get("fear_level") == "high"
        assert domain.get("desensitization_plan") is not None

    def test_chest_pain_auto_exit(self):
        """胸痛 → 安全优先紧急停止"""
        user_input = make_user_input(
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
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self.agent.process(user_input, USER_ID)
        )
        safety = response.domain_content.get("safety_notes", [])
        assert any(n["level"] == "critical" for n in safety)

    def test_high_bp_suspend(self):
        """血压过高 → 暂停运动处方"""
        user_input = make_user_input(
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
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self.agent.process(user_input, USER_ID)
        )
        bp_status = response.domain_content.get("bp_status", {})
        assert bp_status.get("exercise_cleared") is False

    def test_target_hr_zone(self):
        """心率区间计算 (Karvonen)"""
        user_input = make_user_input(
            ttm_stage=3,
            domain_data={
                "rehab_phase": "phase_2_rehab",
                "resting_hr": 70,
                "max_hr": 160,
                "bp_systolic": 125,
            },
        )
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self.agent.process(user_input, USER_ID)
        )
        hr_zone = response.domain_content.get("target_hr_zone", {})
        assert hr_zone.get("low", 0) > 0
        assert hr_zone.get("high", 0) > hr_zone.get("low", 0)
        # 安全上限: high <= max * 0.85
        assert hr_zone["high"] <= int(160 * 0.85)


# =====================================================================
# Test 5: AdherenceExpertAgent
# =====================================================================

class TestAdherenceExpertAgent:
    """测试就医依从性专家"""

    def setup_method(self):
        from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
        from behavior_rx.agents.adherence_expert_agent import AdherenceExpertAgent
        self.agent = AdherenceExpertAgent(rx_engine=BehaviorRxEngine())

    def test_high_missed_medication(self):
        """高漏服 → 习惯叠加策略"""
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
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self.agent.process(user_input, USER_ID)
        )
        assert response.agent_type.value == "adherence_expert"
        domain = response.domain_content
        overview = domain.get("adherence_overview", {})
        assert overview.get("mmas_level") == "low"

    def test_visit_overdue_critical(self):
        """严重逾期就诊"""
        user_input = make_user_input(
            message="最近比较忙没去复查",
            ttm_stage=3,
            domain_data={
                "medication_missed_7d": 0,
                "mmas_score": 7.0,
                "visit_overdue_days": 35,
                "medications": [],
            },
        )
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self.agent.process(user_input, USER_ID)
        )
        assert "复查" in response.user_message or "就诊" in response.user_message

    def test_fear_based_test_avoidance(self):
        """恐惧型检查回避"""
        user_input = make_user_input(
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
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self.agent.process(user_input, USER_ID)
        )
        barriers = response.domain_content.get("diagnosed_barriers", [])
        assert any(b["type"] == "fear" for b in barriers)

    def test_medication_chain_design(self):
        """服药行为链设计"""
        user_input = make_user_input(
            message="药太多记不住",
            ttm_stage=3,
            barriers=["forgetfulness"],
            domain_data={
                "medication_missed_7d": 3,
                "mmas_score": 5.0,
                "medications": [
                    {"name": "二甲双胍", "time": "morning", "dose": "500mg"},
                    {"name": "阿卡波糖", "time": "noon", "dose": "50mg"},
                    {"name": "阿司匹林", "time": "evening", "dose": "100mg"},
                ],
                "visit_overdue_days": 0,
            },
        )
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(
            self.agent.process(user_input, USER_ID)
        )
        chain = response.domain_content.get("medication_chain", {})
        assert chain.get("total_medications") == 3
        assert len(chain.get("chain", [])) == 3


# =====================================================================
# Test 6: 协作编排
# =====================================================================

class TestCollaboration:
    """测试 4-Agent 协作编排"""

    def setup_method(self):
        from behavior_rx.core.behavior_rx_engine import BehaviorRxEngine
        from behavior_rx.core.agent_collaboration_orchestrator import (
            AgentCollaborationOrchestrator,
        )
        from behavior_rx.agents.behavior_coach_agent import BehaviorCoachAgent
        from behavior_rx.agents.metabolic_expert_agent import MetabolicExpertAgent
        from behavior_rx.agents.cardiac_expert_agent import CardiacExpertAgent
        from behavior_rx.agents.adherence_expert_agent import AdherenceExpertAgent

        engine = BehaviorRxEngine()
        self.orchestrator = AgentCollaborationOrchestrator()
        self.orchestrator.register_agent(BehaviorCoachAgent(rx_engine=engine))
        self.orchestrator.register_agent(MetabolicExpertAgent(rx_engine=engine))
        self.orchestrator.register_agent(CardiacExpertAgent(rx_engine=engine))
        self.orchestrator.register_agent(AdherenceExpertAgent(rx_engine=engine))

    def test_fully_operational(self):
        """4 款 Agent 全部注册"""
        assert self.orchestrator.is_fully_operational()
        assert len(self.orchestrator.get_registered_agents()) == 4

    def test_new_user_routes_to_coach(self):
        """新用户低阶段 → Coach主导"""
        user_input = make_user_input(
            message="我刚被诊断糖尿病",
            ttm_stage=0,
            stage_readiness=0.1,
        )
        from behavior_rx.core.rx_schemas import RxContext, BigFiveProfile
        ctx = RxContext(
            user_id=USER_ID,
            ttm_stage=0,
            stage_readiness=0.1,
            personality=BigFiveProfile(),
            capacity_score=0.3,
        )
        decision = self.orchestrator.identify_scenario(ctx, user_input)
        assert decision.primary_agent.value == "behavior_coach"

    def test_stage_regression_coach_takeover(self):
        """阶段回退 → Coach紧急接管"""
        user_input = make_user_input(
            message="我不想做了，放弃算了",
            ttm_stage=3,
            stage_stability=0.2,
            self_efficacy=0.15,
        )
        from behavior_rx.core.rx_schemas import RxContext, BigFiveProfile
        ctx = RxContext(
            user_id=USER_ID,
            ttm_stage=3,
            stage_readiness=0.3,
            stage_stability=0.2,
            self_efficacy=0.15,
            personality=BigFiveProfile(),
            capacity_score=0.5,
        )
        from behavior_rx.core.rx_schemas import ExpertAgentType
        decision = self.orchestrator.identify_scenario(
            ctx, user_input,
            current_agent=ExpertAgentType.METABOLIC_EXPERT,
        )
        assert decision.scenario.value == "stage_regression"
        assert decision.primary_agent.value == "behavior_coach"

    def test_multi_morbidity_parallel(self):
        """多病共管 → 并行处理"""
        user_input = make_user_input(
            message="血糖和心脏都需要管理",
            ttm_stage=3,
            domain_data={
                "glucose": 7.5,
                "cardiac_event_type": "STEMI",
                "rehab_phase": "phase_2_rehab",
            },
        )
        from behavior_rx.core.rx_schemas import RxContext, BigFiveProfile
        ctx = RxContext(
            user_id=USER_ID,
            ttm_stage=3,
            personality=BigFiveProfile(),
            capacity_score=0.6,
            domain_data=user_input["domain_data"],
        )
        decision = self.orchestrator.identify_scenario(ctx, user_input)
        assert decision.scenario.value == "multi_morbidity"
        assert len(decision.secondary_agents) >= 1

    def test_adherence_alert(self):
        """依从性危机 → Adherence介入"""
        user_input = make_user_input(
            message="这周没吃药",
            ttm_stage=3,
            domain_data={
                "medication_missed_7d": 5,
                "visit_overdue_days": 0,
            },
        )
        from behavior_rx.core.rx_schemas import (
            RxContext, BigFiveProfile, ExpertAgentType,
        )
        ctx = RxContext(
            user_id=USER_ID,
            ttm_stage=3,
            personality=BigFiveProfile(),
            capacity_score=0.6,
            domain_data=user_input["domain_data"],
        )
        decision = self.orchestrator.identify_scenario(
            ctx, user_input,
            current_agent=ExpertAgentType.METABOLIC_EXPERT,
        )
        assert decision.scenario.value == "adherence_alert"

    def test_full_orchestration(self):
        """完整编排执行"""
        user_input = make_user_input(
            message="我该怎么管理血糖?",
            ttm_stage=3,
            stage_readiness=0.7,
            domain_data={
                "fasting_glucose": 7.5,
                "hba1c": 7.2,
                "medication_missed_7d": 0,
            },
        )
        from behavior_rx.core.rx_schemas import ExpertAgentType
        loop = asyncio.get_event_loop()
        merged = loop.run_until_complete(
            self.orchestrator.orchestrate(
                user_input=user_input,
                user_id=USER_ID,
                session_id=SESSION_ID,
                current_agent=ExpertAgentType.METABOLIC_EXPERT,
            )
        )
        assert merged.primary is not None
        assert merged.merged_message != ""
        assert merged.collaboration is not None


# =====================================================================
# Test 7: 冲突解决
# =====================================================================

class TestConflictResolver:
    """测试行为处方冲突解决"""

    def setup_method(self):
        from behavior_rx.core.rx_conflict_resolver import RxConflictResolver
        self.resolver = RxConflictResolver()

    def test_no_conflict_single_rx(self):
        """单处方无冲突"""
        from behavior_rx.core.rx_schemas import (
            RxPrescriptionDTO, ExpertAgentType,
            RxStrategyType, RxIntensity, CommunicationStyle,
        )
        rx = RxPrescriptionDTO(
            agent_type=ExpertAgentType.METABOLIC_EXPERT,
            goal_behavior="控制空腹血糖",
            strategy_type=RxStrategyType.STIMULUS_CONTROL,
            intensity=RxIntensity.MODERATE,
            communication_style=CommunicationStyle.DATA_DRIVEN,
            ttm_stage=3,
        )
        result = self.resolver.resolve([rx], ttm_stage=3)
        assert result.conflict_type == "no_conflict"

    def test_intensity_conservative(self):
        """强度冲突 → 保守原则"""
        from behavior_rx.core.rx_schemas import (
            RxPrescriptionDTO, ExpertAgentType,
            RxStrategyType, RxIntensity, CommunicationStyle,
        )
        rx_a = RxPrescriptionDTO(
            agent_type=ExpertAgentType.METABOLIC_EXPERT,
            goal_behavior="运动",
            strategy_type=RxStrategyType.STIMULUS_CONTROL,
            intensity=RxIntensity.HIGH,
            communication_style=CommunicationStyle.DATA_DRIVEN,
            ttm_stage=3,
        )
        rx_b = RxPrescriptionDTO(
            agent_type=ExpertAgentType.CARDIAC_EXPERT,
            goal_behavior="运动",
            strategy_type=RxStrategyType.STIMULUS_CONTROL,
            intensity=RxIntensity.LOW,
            communication_style=CommunicationStyle.EMPATHETIC,
            ttm_stage=3,
        )
        result = self.resolver.resolve([rx_a, rx_b], ttm_stage=3)
        assert result.conflict_type == "intensity_mismatch"
        assert result.resolved_rx.intensity == RxIntensity.LOW

    def test_strategy_stage_adaptation(self):
        """策略冲突 → 阶段适配"""
        from behavior_rx.core.rx_schemas import (
            RxPrescriptionDTO, ExpertAgentType,
            RxStrategyType, RxIntensity, CommunicationStyle,
        )
        rx_a = RxPrescriptionDTO(
            agent_type=ExpertAgentType.BEHAVIOR_COACH,
            goal_behavior="建立运动认知",
            strategy_type=RxStrategyType.CONSCIOUSNESS_RAISING,
            intensity=RxIntensity.MODERATE,
            communication_style=CommunicationStyle.EMPATHETIC,
            ttm_stage=0,
        )
        rx_b = RxPrescriptionDTO(
            agent_type=ExpertAgentType.CARDIAC_EXPERT,
            goal_behavior="开始运动",
            strategy_type=RxStrategyType.STIMULUS_CONTROL,
            intensity=RxIntensity.MODERATE,
            communication_style=CommunicationStyle.DATA_DRIVEN,
            ttm_stage=0,
        )
        result = self.resolver.resolve([rx_a, rx_b], ttm_stage=0)
        assert result.conflict_type == "strategy_mismatch"
        # S0 阶段 consciousness_raising 优先于 stimulus_control
        assert result.resolved_rx.strategy_type == RxStrategyType.CONSCIOUSNESS_RAISING


# =====================================================================
# Test 8: MasterAgent 集成
# =====================================================================

class TestMasterAgentIntegration:
    """测试 MasterAgent 集成路由"""

    def setup_method(self):
        from behavior_rx.patches.master_agent_integration import (
            setup_expert_agents, ExpertAgentRouter,
        )
        self.router = setup_expert_agents()

    def test_metabolic_keyword_routing(self):
        """血糖关键词 → 代谢Agent"""
        should_route, agent = self.router.should_route_to_expert(
            user_input={"message": "我的血糖最近控制不好"},
            user_profile={"ttm_stage": 3},
        )
        assert should_route is True
        assert agent is not None
        assert agent.value == "metabolic_expert"

    def test_cardiac_keyword_routing(self):
        """心脏关键词 → 心血管Agent"""
        should_route, agent = self.router.should_route_to_expert(
            user_input={"message": "心梗后怎么运动"},
            user_profile={"ttm_stage": 3},
        )
        assert should_route is True
        assert agent.value == "cardiac_expert"

    def test_adherence_keyword_routing(self):
        """服药关键词 → 依从性Agent"""
        should_route, agent = self.router.should_route_to_expert(
            user_input={"message": "药太多忘记吃药了"},
            user_profile={"ttm_stage": 3},
        )
        assert should_route is True
        assert agent.value == "adherence_expert"

    def test_low_stage_coach_routing(self):
        """低阶段 → Coach"""
        should_route, agent = self.router.should_route_to_expert(
            user_input={"message": "你好"},
            user_profile={"ttm_stage": 1},
        )
        assert should_route is True
        assert agent.value == "behavior_coach"

    def test_domain_data_routing(self):
        """领域数据触发路由"""
        should_route, agent = self.router.should_route_to_expert(
            user_input={
                "message": "看看我的数据",
                "domain_data": {"cardiac_event_type": "STEMI"},
            },
            user_profile={"ttm_stage": 4},
        )
        assert should_route is True
        assert agent.value == "cardiac_expert"


# =====================================================================
# 运行入口
# =====================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

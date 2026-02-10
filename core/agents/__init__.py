"""
BHP v3 Agent体系
================
来源: behavioral-prescription-core-logic-supplemented.md §8-§11

包含:
- 9个专科Agent + 3个整合型Agent
- AgentRouter (路由分发)
- MultiAgentCoordinator (多Agent协调+冲突消解)
- RuntimePolicyGate (策略闸门)
- MasterAgent (九步处理流程编排)
"""

from .specialist_agents import (
    CrisisAgent, SleepAgent, GlucoseAgent, StressAgent,
    NutritionAgent, ExerciseAgent, MentalHealthAgent,
    TCMWellnessAgent, MotivationAgent,
)
from .integrative_agents import (
    BehaviorRxAgent, WeightAgent, CardiacRehabAgent,
)
from .router import AgentRouter
from .coordinator import MultiAgentCoordinator
from .policy_gate import RuntimePolicyGate
from .master_agent import MasterAgent

__all__ = [
    # 专科Agent (9)
    "CrisisAgent", "SleepAgent", "GlucoseAgent", "StressAgent",
    "NutritionAgent", "ExerciseAgent", "MentalHealthAgent",
    "TCMWellnessAgent", "MotivationAgent",
    # 整合型Agent (3)
    "BehaviorRxAgent", "WeightAgent", "CardiacRehabAgent",
    # 基础设施
    "AgentRouter", "MultiAgentCoordinator", "RuntimePolicyGate",
    "MasterAgent",
]

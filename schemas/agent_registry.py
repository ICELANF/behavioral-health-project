"""
F-007: Agent Registry Schema — Agent 四级治理注册定义

Source: 契约注册表 ⑨ Agent架构 Sheet
双层架构: L1平台Agent(12+4) + L2专家Agent(动态)
四级治理: 注册→审核→运行→退出
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class AgentLayer(str, Enum):
    """Agent 层级"""
    L1_platform = "L1_platform"    # 平台内建
    L2_expert = "L2_expert"        # 专家自建
    L3_community = "L3_community"  # 社区贡献 (未来)


class AgentGovernanceState(str, Enum):
    """Agent 四级治理状态"""
    registered = "registered"    # 注册待审
    approved = "approved"        # 审核通过
    active = "active"            # 运行中
    suspended = "suspended"      # 暂停
    retired = "retired"          # 退出


class AgentCapability(str, Enum):
    """Agent 能力标签"""
    dialog = "dialog"            # 对话
    assessment = "assessment"    # 评估
    rx_generate = "rx_generate"  # 处方生成
    monitoring = "monitoring"    # 监测
    crisis = "crisis"            # 危机处理
    coaching = "coaching"        # 教练辅助
    content = "content"          # 内容推荐


class AgentRegistryEntry(BaseModel):
    """Agent 注册表条目"""
    agent_type: str
    display_name: str
    layer: AgentLayer
    capabilities: List[AgentCapability]
    domains: List[str] = []
    risk_level_max: str = "R2"  # 最高可独立处理的风险等级
    requires_coach_supervision: bool = False
    stage_range: Optional[str] = None  # "s0-s5" or "s2-s4"
    governance_state: AgentGovernanceState = AgentGovernanceState.active


# ── Platform L1 Agents (16 total) ────────────
PLATFORM_AGENTS: List[AgentRegistryEntry] = [
    # Specialized (9)
    AgentRegistryEntry(agent_type="metabolic", display_name="代谢专家", layer=AgentLayer.L1_platform,
        capabilities=[AgentCapability.dialog, AgentCapability.monitoring, AgentCapability.rx_generate],
        domains=["metabolism", "glucose", "nutrition"], risk_level_max="R2"),
    AgentRegistryEntry(agent_type="sleep", display_name="睡眠专家", layer=AgentLayer.L1_platform,
        capabilities=[AgentCapability.dialog, AgentCapability.monitoring],
        domains=["sleep"], risk_level_max="R1"),
    AgentRegistryEntry(agent_type="emotion", display_name="情绪专家", layer=AgentLayer.L1_platform,
        capabilities=[AgentCapability.dialog, AgentCapability.assessment],
        domains=["emotion", "mental"], risk_level_max="R3"),
    AgentRegistryEntry(agent_type="motivation", display_name="动机专家", layer=AgentLayer.L1_platform,
        capabilities=[AgentCapability.dialog, AgentCapability.coaching],
        domains=["motivation"], risk_level_max="R1"),
    AgentRegistryEntry(agent_type="coaching", display_name="教练协助", layer=AgentLayer.L1_platform,
        capabilities=[AgentCapability.coaching, AgentCapability.content],
        domains=["coaching"], risk_level_max="R1"),
    AgentRegistryEntry(agent_type="nutrition", display_name="营养专家", layer=AgentLayer.L1_platform,
        capabilities=[AgentCapability.dialog, AgentCapability.rx_generate],
        domains=["nutrition", "diet"], risk_level_max="R1"),
    AgentRegistryEntry(agent_type="exercise", display_name="运动专家", layer=AgentLayer.L1_platform,
        capabilities=[AgentCapability.dialog, AgentCapability.rx_generate],
        domains=["exercise", "fitness"], risk_level_max="R2"),
    AgentRegistryEntry(agent_type="tcm", display_name="中医专家", layer=AgentLayer.L1_platform,
        capabilities=[AgentCapability.dialog, AgentCapability.content],
        domains=["tcm"], risk_level_max="R1"),
    AgentRegistryEntry(agent_type="crisis", display_name="危机处理", layer=AgentLayer.L1_platform,
        capabilities=[AgentCapability.crisis, AgentCapability.dialog],
        domains=["crisis", "emergency"], risk_level_max="R4"),
    # Integrative (3)
    AgentRegistryEntry(agent_type="behavior_rx", display_name="行为处方", layer=AgentLayer.L1_platform,
        capabilities=[AgentCapability.rx_generate, AgentCapability.dialog],
        domains=["behavior", "rx"], risk_level_max="R2"),
    AgentRegistryEntry(agent_type="weight", display_name="体重管理", layer=AgentLayer.L1_platform,
        capabilities=[AgentCapability.dialog, AgentCapability.monitoring, AgentCapability.rx_generate],
        domains=["weight", "metabolism", "nutrition", "exercise"], risk_level_max="R2"),
    AgentRegistryEntry(agent_type="cardiac_rehab", display_name="心脏康复", layer=AgentLayer.L1_platform,
        capabilities=[AgentCapability.dialog, AgentCapability.monitoring, AgentCapability.rx_generate],
        domains=["cardiac", "exercise", "metabolism"], risk_level_max="R3"),
    # V4.0 (4)
    AgentRegistryEntry(agent_type="journey_companion", display_name="旅程陪伴", layer=AgentLayer.L1_platform,
        capabilities=[AgentCapability.dialog, AgentCapability.coaching],
        domains=["journey", "stage"], stage_range="s0-s5", risk_level_max="R1"),
    AgentRegistryEntry(agent_type="growth_reflection", display_name="成长反思", layer=AgentLayer.L1_platform,
        capabilities=[AgentCapability.dialog, AgentCapability.assessment],
        domains=["reflection", "growth"], stage_range="s1-s5", risk_level_max="R1"),
    AgentRegistryEntry(agent_type="coach_copilot", display_name="教练副驾驶", layer=AgentLayer.L1_platform,
        capabilities=[AgentCapability.coaching, AgentCapability.monitoring],
        domains=["coaching", "monitoring"], requires_coach_supervision=True, risk_level_max="R2"),
    AgentRegistryEntry(agent_type="life_designer", display_name="生命设计师", layer=AgentLayer.L1_platform,
        capabilities=[AgentCapability.dialog, AgentCapability.coaching],
        domains=["identity", "life_design"], stage_range="s3-s5", risk_level_max="R1"),
]

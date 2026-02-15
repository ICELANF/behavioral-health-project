"""
F-009: IES Formula Schema — 干预效果评分公式定义

Source: 契约注册表 ⑩ 技术映射 Sheet
公式: IES = 0.40×完成率 + 0.20×活跃度 + 0.25×进展变化量 - 0.15×抗阻指数
"""
from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class IESInterpretation(str, Enum):
    """IES 解读等级"""
    significant_improvement = "significant_improvement"  # >= 0.7
    clear_improvement = "clear_improvement"              # >= 0.3
    slight_improvement = "slight_improvement"            # >= 0.1
    no_change = "no_change"                              # >= -0.1
    slight_decline = "slight_decline"                    # >= -0.3
    clear_decline = "clear_decline"                      # < -0.3


class IESComponent(BaseModel):
    """IES 分量定义"""
    name: str
    weight: float
    description: str
    data_source: str
    inverted: bool = False  # True = higher value is worse


# ── 4-Component IES Formula (契约版) ─────────
IES_COMPONENTS = [
    IESComponent(
        name="completion_rate",
        weight=0.40,
        description="完成率: 微行动/评估/Rx 完成比例",
        data_source="micro_action_tasks + rx_prescriptions",
    ),
    IESComponent(
        name="activity_rate",
        weight=0.20,
        description="活跃度: Agent对话次数 + 登录天数 / 总天数",
        data_source="chat_sessions + user_activity_logs",
    ),
    IESComponent(
        name="progression_delta",
        weight=0.25,
        description="进展变化量: 阶段跃迁 + 设备数据趋势",
        data_source="stage_transition_logs + device_data trends",
    ),
    IESComponent(
        name="resistance_index",
        weight=0.15,
        description="抗阻指数: 跳过率 + 退出率 + 负面反馈比例",
        data_source="micro_action_tasks(skipped) + chat_sessions(early_exit)",
        inverted=True,
    ),
]


def compute_ies(
    completion_rate: float,
    activity_rate: float,
    progression_delta: float,
    resistance_index: float,
) -> float:
    """
    计算 IES 评分

    Formula: IES = 0.40×C + 0.20×A + 0.25×P - 0.15×R
    All inputs should be normalized to [0, 1] range.
    Output range: [-0.15, 0.85]
    """
    ies = (
        0.40 * completion_rate
        + 0.20 * activity_rate
        + 0.25 * progression_delta
        - 0.15 * resistance_index
    )
    return round(max(-1.0, min(1.0, ies)), 4)


def interpret_ies(score: float) -> IESInterpretation:
    """解读 IES 评分"""
    if score >= 0.7:
        return IESInterpretation.significant_improvement
    elif score >= 0.3:
        return IESInterpretation.clear_improvement
    elif score >= 0.1:
        return IESInterpretation.slight_improvement
    elif score >= -0.1:
        return IESInterpretation.no_change
    elif score >= -0.3:
        return IESInterpretation.slight_decline
    else:
        return IESInterpretation.clear_decline


class IESDecisionRule(BaseModel):
    """IES 驱动的 Rx 自动调整规则"""
    interpretation: IESInterpretation
    rx_action: str
    description: str


IES_DECISION_RULES = [
    IESDecisionRule(
        interpretation=IESInterpretation.significant_improvement,
        rx_action="advance_stage",
        description="显著改善: 考虑推进阶段 + 增加难度",
    ),
    IESDecisionRule(
        interpretation=IESInterpretation.clear_improvement,
        rx_action="maintain_and_reinforce",
        description="明显改善: 保持当前Rx + 正向反馈强化",
    ),
    IESDecisionRule(
        interpretation=IESInterpretation.slight_improvement,
        rx_action="maintain",
        description="轻微改善: 保持当前Rx",
    ),
    IESDecisionRule(
        interpretation=IESInterpretation.no_change,
        rx_action="adjust_approach",
        description="无变化: 调整策略方向 + 教练关注",
    ),
    IESDecisionRule(
        interpretation=IESInterpretation.slight_decline,
        rx_action="reduce_intensity",
        description="轻微下降: 降低Rx强度 + 增加支持",
    ),
    IESDecisionRule(
        interpretation=IESInterpretation.clear_decline,
        rx_action="pause_and_reassess",
        description="明显下降: 暂停当前Rx + 重新评估 + 教练干预",
    ),
]

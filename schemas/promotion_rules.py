"""
F-004: Promotion Rules Schema — 晋级规则引擎配置

Source: 契约注册表 ⑤ 晋级规则 Sheet
双轨制: 积分轨(自动) + 成长轨(触发审核)
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class TrackType(str, Enum):
    points = "points"    # 积分轨 (自动检查)
    growth = "growth"    # 成长轨 (人工审核触发)


class PromotionStatus(str, Enum):
    normal_growth = "normal_growth"
    points_eligible = "points_eligible"
    growth_review = "growth_review"
    ceremony_pending = "ceremony_pending"
    promoted = "promoted"
    blocked = "blocked"


class PromotionRule(BaseModel):
    """单级晋级规则"""
    from_level: int
    to_level: int
    # 积分轨要求
    growth_points: int
    contribution_points: int = 0
    influence_points: int = 0
    # 成长轨要求
    exam_required: bool = False
    exam_pass_score: int = 80
    companions_required: int = 0
    companions_min_level: int = 0
    ethical_declaration: Optional[str] = None
    # 时间要求
    min_days_at_current: int = 0
    # 保护期 (降级缓冲)
    protection_days: int = 30
    # 降级条件
    demotion_inactive_days: int = 90
    demotion_violation_threshold: int = 3


PROMOTION_RULES: List[PromotionRule] = [
    PromotionRule(from_level=0, to_level=1, growth_points=100),
    PromotionRule(from_level=1, to_level=2, growth_points=500, contribution_points=50),
    PromotionRule(
        from_level=2, to_level=3,
        growth_points=800, contribution_points=200, influence_points=50,
        exam_required=True, companions_required=4, companions_min_level=1,
        ethical_declaration="coach_5clause", min_days_at_current=30,
    ),
    PromotionRule(
        from_level=3, to_level=4,
        growth_points=1500, contribution_points=600, influence_points=200,
        exam_required=True, companions_required=4, companions_min_level=2,
        ethical_declaration="promoter_7clause", min_days_at_current=60,
    ),
    PromotionRule(
        from_level=4, to_level=5,
        growth_points=3000, contribution_points=1500, influence_points=600,
        exam_required=True, companions_required=4, companions_min_level=3,
        min_days_at_current=90,
    ),
]

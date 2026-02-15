"""
F-001: Role Architecture Schema — 六级成长轨角色定义

Source: 契约注册表 ① 角色架构 Sheet
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class RoleCode(str, Enum):
    """角色编码 (成长轨)"""
    observer = "observer"      # L0 观察者 — 免注册/注册两级
    grower = "grower"          # L1-L2 成长者
    sharer = "sharer"          # L2.5 分享者
    coach = "coach"            # L3-L4 教练
    promoter = "promoter"      # L4-L5 推广者/督导
    supervisor = "supervisor"  # L5 督导
    master = "master"          # L6 大师
    admin = "admin"            # L99 管理员


class GovernanceTrack(str, Enum):
    """治理轨 (并行于成长轨)"""
    none = "none"
    intern_coach = "intern_coach"  # L2.5 实习教练
    ethics_auditor = "ethics_auditor"
    quality_reviewer = "quality_reviewer"


class RoleLevelDefinition(BaseModel):
    """角色等级完整定义"""
    level: int = Field(..., ge=0, le=6)
    role: RoleCode
    label_zh: str
    label_en: str
    growth_points_min: int = 0
    contribution_points_min: int = 0
    influence_points_min: int = 0
    exam_required: bool = False
    companions_required: int = 0
    companions_min_level: int = 0
    contract_required: bool = True
    ethical_declaration: Optional[str] = None  # coach_5clause / promoter_7clause


# ── Canonical Level Definitions ──────────────
LEVEL_DEFINITIONS: List[RoleLevelDefinition] = [
    RoleLevelDefinition(
        level=0, role=RoleCode.observer,
        label_zh="观察者", label_en="Observer",
        contract_required=False,
    ),
    RoleLevelDefinition(
        level=1, role=RoleCode.grower,
        label_zh="成长者 L1", label_en="Grower L1",
        growth_points_min=100,
    ),
    RoleLevelDefinition(
        level=2, role=RoleCode.grower,
        label_zh="成长者 L2", label_en="Grower L2",
        growth_points_min=500, contribution_points_min=50,
    ),
    RoleLevelDefinition(
        level=3, role=RoleCode.coach,
        label_zh="教练 L3", label_en="Coach L3",
        growth_points_min=800, contribution_points_min=200,
        influence_points_min=50, exam_required=True,
        companions_required=4, companions_min_level=1,
        ethical_declaration="coach_5clause",
    ),
    RoleLevelDefinition(
        level=4, role=RoleCode.promoter,
        label_zh="推广者 L4", label_en="Promoter L4",
        growth_points_min=1500, contribution_points_min=600,
        influence_points_min=200, exam_required=True,
        companions_required=4, companions_min_level=2,
        ethical_declaration="promoter_7clause",
    ),
    RoleLevelDefinition(
        level=5, role=RoleCode.master,
        label_zh="大师 L5", label_en="Master L5",
        growth_points_min=3000, contribution_points_min=1500,
        influence_points_min=600, exam_required=True,
        companions_required=4, companions_min_level=3,
    ),
]

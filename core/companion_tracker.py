"""
V4.0 Four-Companion Tracking Service — 四同道者追踪

Sheet ④/⑪ 核心逻辑:
  每级晋级要求4名同道者达到指定质量:
    L0→L1: 4人, 2人开始行为尝试
    L1→L2: 4人, 2人完成S0-S3, 1人达S4
    L2→L3: 4人, 2人通过考核, 1人具备教练潜力
    L3→L4: 4人, 2人独立执业, 1人项目负责人
    L4→L5: 4人, 2人区域标杆, 1人大师潜力
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from core.models import (
    User, CompanionRelation, CompanionStatus,
    JourneyState, ROLE_LEVEL_STR,
)

logger = logging.getLogger(__name__)

# ── Per-Level Quality Requirements (Sheet ④) ───────────
COMPANION_QUALITY_REQS = {
    2: {  # L0→L1
        "count": 4,
        "quality_rules": [
            {"description": "2人开始行为尝试", "check": "behavior_started", "min_count": 2},
        ],
    },
    3: {  # L1→L2
        "count": 4,
        "quality_rules": [
            {"description": "2人完成S0-S3", "check": "reached_s3", "min_count": 2},
            {"description": "1人达S4", "check": "reached_s4", "min_count": 1},
        ],
    },
    4: {  # L2→L3
        "count": 4,
        "quality_rules": [
            {"description": "2人通过考核", "check": "passed_assessment", "min_count": 2},
            {"description": "1人具备教练潜力", "check": "coach_potential", "min_count": 1},
        ],
    },
    5: {  # L3→L4
        "count": 4,
        "quality_rules": [
            {"description": "2人独立执业", "check": "independent_practice", "min_count": 2},
            {"description": "1人项目负责人", "check": "project_leader", "min_count": 1},
        ],
    },
    6: {  # L4→L5
        "count": 4,
        "quality_rules": [
            {"description": "2人区域标杆", "check": "regional_benchmark", "min_count": 2},
            {"description": "1人大师潜力", "check": "master_potential", "min_count": 1},
        ],
    },
}

# Stage thresholds for quality checks
_STAGE_ORDER = [
    "s0_authorization", "s1_awareness", "s2_trial",
    "s3_pathway", "s4_internalization", "s5_graduation",
]


class CompanionTracker:
    """四同道者追踪引擎"""

    def __init__(self, db: Session):
        self.db = db

    def get_companion_overview(self, user_id: int, target_level: int = None) -> dict:
        """获取用户的四同道者追踪概览"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "用户不存在"}

        role = user.role.value if hasattr(user.role, 'value') else user.role
        current_level = ROLE_LEVEL_STR.get(role, 1)
        if target_level is None:
            target_level = current_level + 1

        if target_level > 6:
            return {
                "user_id": user_id,
                "current_level": current_level,
                "status": "max_level",
                "message": "已达最高级别",
            }

        reqs = COMPANION_QUALITY_REQS.get(target_level, {})
        required_count = reqs.get("count", 4)

        # Get all companion relations where user is mentor
        companions = self.db.query(CompanionRelation).filter(
            CompanionRelation.mentor_id == user_id,
        ).all()

        total = len(companions)
        active = sum(1 for c in companions if c.status == CompanionStatus.ACTIVE.value)
        graduated = sum(1 for c in companions if c.status == CompanionStatus.GRADUATED.value)

        # Check quality rules
        quality_checks = []
        for rule in reqs.get("quality_rules", []):
            check_result = self._check_quality_rule(user_id, companions, rule)
            quality_checks.append(check_result)

        all_quality_passed = all(qc["passed"] for qc in quality_checks) if quality_checks else True
        count_passed = total >= required_count

        return {
            "user_id": user_id,
            "current_level": current_level,
            "target_level": target_level,
            "required_count": required_count,
            "total_companions": total,
            "active": active,
            "graduated": graduated,
            "count_passed": count_passed,
            "quality_checks": quality_checks,
            "all_quality_passed": all_quality_passed,
            "overall_passed": count_passed and all_quality_passed,
            "companions": [
                {
                    "id": str(c.id),
                    "mentee_id": c.mentee_id,
                    "status": c.status,
                    "quality_score": float(c.quality_score) if c.quality_score else None,
                    "started_at": str(c.started_at) if c.started_at else None,
                    "graduated_at": str(c.graduated_at) if c.graduated_at else None,
                }
                for c in companions
            ],
        }

    def _check_quality_rule(self, mentor_id: int, companions: list, rule: dict) -> dict:
        """检查单条质量规则"""
        check_type = rule["check"]
        min_count = rule["min_count"]
        description = rule["description"]

        qualifying = 0

        for c in companions:
            mentee_id = c.mentee_id
            if check_type == "behavior_started":
                qualifying += 1 if self._has_behavior_started(mentee_id) else 0
            elif check_type == "reached_s3":
                qualifying += 1 if self._has_reached_stage(mentee_id, "s3_pathway") else 0
            elif check_type == "reached_s4":
                qualifying += 1 if self._has_reached_stage(mentee_id, "s4_internalization") else 0
            elif check_type == "passed_assessment":
                qualifying += 1 if c.status == CompanionStatus.GRADUATED.value else 0
            elif check_type == "coach_potential":
                qualifying += 1 if self._has_coach_potential(mentee_id) else 0
            elif check_type == "independent_practice":
                qualifying += 1 if self._is_independent(mentee_id) else 0
            elif check_type == "project_leader":
                qualifying += 1 if self._is_project_leader(mentee_id) else 0
            elif check_type == "regional_benchmark":
                qualifying += 1 if self._is_regional_benchmark(mentee_id) else 0
            elif check_type == "master_potential":
                qualifying += 1 if self._has_master_potential(mentee_id) else 0

        return {
            "check": check_type,
            "description": description,
            "required": min_count,
            "qualifying": qualifying,
            "passed": qualifying >= min_count,
        }

    def _has_behavior_started(self, user_id: int) -> bool:
        """检查用户是否开始行为尝试 (有 journey_state 且非 s0)"""
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id,
        ).first()
        if not journey:
            return False
        stage = journey.journey_stage or ""
        return stage not in ("", "s0_authorization")

    def _has_reached_stage(self, user_id: int, target_stage: str) -> bool:
        """检查用户是否达到指定阶段"""
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id,
        ).first()
        if not journey or not journey.journey_stage:
            return False
        try:
            current_idx = _STAGE_ORDER.index(journey.journey_stage)
            target_idx = _STAGE_ORDER.index(target_stage)
            return current_idx >= target_idx
        except ValueError:
            return False

    def _has_coach_potential(self, user_id: int) -> bool:
        """检查用户是否有教练潜力 (角色>=sharer 或 质量评分>=4)"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        role = user.role.value if hasattr(user.role, 'value') else user.role
        level = ROLE_LEVEL_STR.get(role, 1)
        return level >= 3  # sharer or above

    def _is_independent(self, user_id: int) -> bool:
        """检查用户是否独立执业 (角色>=coach)"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        role = user.role.value if hasattr(user.role, 'value') else user.role
        level = ROLE_LEVEL_STR.get(role, 1)
        return level >= 4

    def _is_project_leader(self, user_id: int) -> bool:
        """检查用户是否项目负责人 (角色>=promoter)"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        role = user.role.value if hasattr(user.role, 'value') else user.role
        level = ROLE_LEVEL_STR.get(role, 1)
        return level >= 5

    def _is_regional_benchmark(self, user_id: int) -> bool:
        """检查用户是否区域标杆 (角色>=promoter 且带教>=5人)"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        role = user.role.value if hasattr(user.role, 'value') else user.role
        level = ROLE_LEVEL_STR.get(role, 1)
        if level < 5:
            return False
        mentee_count = self.db.query(CompanionRelation).filter(
            CompanionRelation.mentor_id == user_id,
        ).count()
        return mentee_count >= 5

    def _has_master_potential(self, user_id: int) -> bool:
        """检查用户是否有大师潜力 (角色>=master 或 promoter+高质量带教)"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False
        role = user.role.value if hasattr(user.role, 'value') else user.role
        level = ROLE_LEVEL_STR.get(role, 1)
        return level >= 6

    def check_promotion_companion_prereq(self, user_id: int, target_level: int) -> dict:
        """检查晋级的同道者前置条件 (供 DualTrackEngine 调用)"""
        overview = self.get_companion_overview(user_id, target_level)
        return {
            "passed": overview.get("overall_passed", False),
            "count_passed": overview.get("count_passed", False),
            "quality_passed": overview.get("all_quality_passed", False),
            "total": overview.get("total_companions", 0),
            "required": overview.get("required_count", 4),
            "quality_checks": overview.get("quality_checks", []),
        }

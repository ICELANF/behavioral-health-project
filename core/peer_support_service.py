"""
V4.0 Peer Support & Intern Coach Service — 同伴支持 + L2.5实习教练

断裂二修复: Sharer 从「内容贡献者」→「同伴陪伴人」
  核心能力: 陪伴1-2名Grower度过行为改变关键期

L2.5 Intern Coach:
  Sharer → 实习教练 → Coach 过渡角色
  在督导下带教1-2个Grower, 获得教练预体验
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from core.models import (
    User, UserRole, ROLE_LEVEL_STR,
    CompanionRelation, CompanionStatus,
    JourneyState,
)

logger = logging.getLogger(__name__)


# ── Intern Coach Criteria ───────────────────────

INTERN_COACH_REQUIREMENTS = {
    "min_role": "sharer",             # L2 minimum
    "min_companion_graduated": 1,     # At least 1 graduated mentee
    "min_quality_score": 3.5,         # Average quality ≥ 3.5
    "min_stage": "s3_pathway",        # Own stage ≥ S3
    "min_days_as_sharer": 30,         # Active as sharer ≥ 30 days
}

# Intern coach capacity
INTERN_COACH_MAX_MENTEES = 2

# Peer support metrics thresholds
PEER_SUPPORT_THRESHOLDS = {
    "weekly_dialog_min": 1,           # ≥1 dialog/week
    "satisfaction_min": 4.0,          # ≥4.0/5.0 rating
    "activation_rate_target": 0.30,   # 30% sharer activation
}


class PeerSupportService:
    """同伴支持服务"""

    def __init__(self, db: Session):
        self.db = db

    # ── Peer Support (Sharer) ───────────────────

    def get_peer_support_status(self, user_id: int) -> dict:
        """获取用户的同伴支持状态"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "用户不存在"}

        role = user.role.value if hasattr(user.role, 'value') else user.role
        level = ROLE_LEVEL_STR.get(role, 1)

        # Check if user is a sharer (peer support role)
        is_sharer = level >= 3 and level < 4

        # Get active mentees
        active_mentees = self.db.query(CompanionRelation).filter(
            CompanionRelation.mentor_id == user_id,
            CompanionRelation.status == CompanionStatus.ACTIVE.value,
        ).all()

        graduated_count = self.db.query(CompanionRelation).filter(
            CompanionRelation.mentor_id == user_id,
            CompanionRelation.status == CompanionStatus.GRADUATED.value,
        ).count()

        avg_quality = self.db.query(func.avg(CompanionRelation.quality_score)).filter(
            CompanionRelation.mentor_id == user_id,
            CompanionRelation.quality_score.isnot(None),
        ).scalar()

        mentee_details = []
        for rel in active_mentees:
            mentee = self.db.query(User).filter(User.id == rel.mentee_id).first()
            mentee_journey = self.db.query(JourneyState).filter(
                JourneyState.user_id == rel.mentee_id
            ).first()
            mentee_details.append({
                "relation_id": str(rel.id),
                "mentee_id": rel.mentee_id,
                "mentee_name": mentee.nickname or mentee.username if mentee else None,
                "stage": mentee_journey.journey_stage if mentee_journey else None,
                "agency_mode": mentee_journey.agency_mode if mentee_journey else None,
                "started_at": str(rel.started_at) if rel.started_at else None,
            })

        return {
            "user_id": user_id,
            "role": role,
            "is_peer_supporter": is_sharer or level >= 4,
            "active_mentees": mentee_details,
            "active_count": len(active_mentees),
            "graduated_count": graduated_count,
            "avg_quality_score": round(float(avg_quality), 2) if avg_quality else None,
            "capacity": INTERN_COACH_MAX_MENTEES if is_sharer else 6,
            "can_take_more": len(active_mentees) < (INTERN_COACH_MAX_MENTEES if is_sharer else 6),
        }

    # ── L2.5 Intern Coach ──────────────────────

    def check_intern_coach_eligibility(self, user_id: int) -> dict:
        """检查用户是否符合实习教练资格"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "用户不存在"}

        role = user.role.value if hasattr(user.role, 'value') else user.role
        level = ROLE_LEVEL_STR.get(role, 1)

        checks = {}

        # 1. Role check: must be sharer (L2)
        checks["min_role"] = {
            "required": "sharer (L2)",
            "current": role,
            "passed": level >= 3,
        }

        # 2. Graduated mentees
        graduated = self.db.query(CompanionRelation).filter(
            CompanionRelation.mentor_id == user_id,
            CompanionRelation.status == CompanionStatus.GRADUATED.value,
        ).count()
        req_grad = INTERN_COACH_REQUIREMENTS["min_companion_graduated"]
        checks["graduated_mentees"] = {
            "required": req_grad,
            "current": graduated,
            "passed": graduated >= req_grad,
        }

        # 3. Quality score
        avg_quality = self.db.query(func.avg(CompanionRelation.quality_score)).filter(
            CompanionRelation.mentor_id == user_id,
            CompanionRelation.quality_score.isnot(None),
        ).scalar()
        avg_q = float(avg_quality) if avg_quality else 0.0
        req_q = INTERN_COACH_REQUIREMENTS["min_quality_score"]
        checks["quality_score"] = {
            "required": req_q,
            "current": round(avg_q, 2),
            "passed": avg_q >= req_q,
        }

        # 4. Own stage
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()
        own_stage = journey.journey_stage if journey else "s0_authorization"
        stage_order = [
            "s0_authorization", "s1_awareness", "s2_trial",
            "s3_pathway", "s4_internalization", "s5_graduation",
        ]
        try:
            own_idx = stage_order.index(own_stage)
            req_idx = stage_order.index(INTERN_COACH_REQUIREMENTS["min_stage"])
            stage_passed = own_idx >= req_idx
        except ValueError:
            stage_passed = False
        checks["own_stage"] = {
            "required": INTERN_COACH_REQUIREMENTS["min_stage"],
            "current": own_stage,
            "passed": stage_passed,
        }

        # 5. Days as sharer
        days_active = 0
        if user.created_at:
            days_active = (datetime.utcnow() - user.created_at).days
        req_days = INTERN_COACH_REQUIREMENTS["min_days_as_sharer"]
        checks["days_as_sharer"] = {
            "required": req_days,
            "current": days_active,
            "passed": days_active >= req_days,
        }

        all_passed = all(c["passed"] for c in checks.values())

        return {
            "user_id": user_id,
            "eligible": all_passed,
            "checks": checks,
            "next_step": "可申请实习教练" if all_passed else "尚未满足实习教练条件",
        }

    def apply_intern_coach(self, user_id: int) -> dict:
        """申请成为实习教练"""
        eligibility = self.check_intern_coach_eligibility(user_id)
        if "error" in eligibility:
            return eligibility

        if not eligibility["eligible"]:
            return {
                "error": "不符合实习教练资格",
                "checks": eligibility["checks"],
            }

        user = self.db.query(User).filter(User.id == user_id).first()
        # Mark as intern coach via coach_intent flag
        user.coach_intent = True
        self.db.flush()

        return {
            "user_id": user_id,
            "status": "intern_coach_applied",
            "message": "实习教练申请已提交, 等待督导审核",
            "coach_intent": True,
        }

    def get_intern_coaches(self) -> List[dict]:
        """获取所有实习教练 (coach_intent=True的sharer)"""
        interns = self.db.query(User).filter(
            User.role == UserRole.SHARER.value,
            User.coach_intent == True,
            User.is_active == True,
        ).all()

        results = []
        for u in interns:
            mentees = self.db.query(CompanionRelation).filter(
                CompanionRelation.mentor_id == u.id,
                CompanionRelation.status == CompanionStatus.ACTIVE.value,
            ).count()
            results.append({
                "user_id": u.id,
                "username": u.username,
                "nickname": u.nickname,
                "active_mentees": mentees,
                "capacity": INTERN_COACH_MAX_MENTEES,
            })

        return results

    def get_peer_support_metrics(self) -> dict:
        """全平台同伴支持指标"""
        total_sharers = self.db.query(User).filter(
            User.role == UserRole.SHARER.value,
            User.is_active == True,
        ).count()

        active_supporters = self.db.query(
            CompanionRelation.mentor_id
        ).join(User, CompanionRelation.mentor_id == User.id).filter(
            User.role == UserRole.SHARER.value,
            CompanionRelation.status == CompanionStatus.ACTIVE.value,
        ).distinct().count()

        activation_rate = active_supporters / total_sharers if total_sharers > 0 else 0

        total_active_pairs = self.db.query(CompanionRelation).filter(
            CompanionRelation.status == CompanionStatus.ACTIVE.value,
        ).count()

        intern_count = self.db.query(User).filter(
            User.role == UserRole.SHARER.value,
            User.coach_intent == True,
            User.is_active == True,
        ).count()

        return {
            "total_sharers": total_sharers,
            "active_supporters": active_supporters,
            "activation_rate": round(activation_rate, 4),
            "target_activation_rate": PEER_SUPPORT_THRESHOLDS["activation_rate_target"],
            "total_active_pairs": total_active_pairs,
            "intern_coaches": intern_count,
            "thresholds": PEER_SUPPORT_THRESHOLDS,
        }

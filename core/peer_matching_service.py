"""
V4.0 Peer Matching Service — 同伴配对系统

Plan §断裂二 修复:
  Sharer 从「内容贡献者」→「同伴陪伴人」
  核心能力: 陪伴1-2名Grower度过行为改变关键期

Matching Algorithm:
  1. TTM stage proximity (同阶段优先)
  2. Health condition similarity (慢病相似)
  3. Goal alignment (目标对齐)
  4. Personality complement (性格互补)
  5. Availability (导师余量)
  6. Quality history (历史带教质量)

Output: 推荐2-3个候选人, 用户自主选择
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from core.models import (
    User, UserRole, ROLE_LEVEL_STR,
    CompanionRelation, CompanionStatus,
    JourneyState,
)

logger = logging.getLogger(__name__)

# ── Stage proximity scoring ─────────────────────
_STAGE_ORDER = [
    "s0_authorization", "s1_awareness", "s2_trial",
    "s3_pathway", "s4_internalization", "s5_graduation",
]

# Maximum mentees per sharer (peer support capacity)
SHARER_MAX_MENTEES = 2
COACH_MAX_MENTEES = 6

# Matching weights
WEIGHTS = {
    "stage_proximity": 0.30,    # TTM stage closeness
    "condition_overlap": 0.20,  # chronic condition similarity
    "goal_alignment": 0.20,     # goal overlap
    "quality_history": 0.15,    # mentor historical quality
    "availability": 0.15,       # mentor remaining capacity
}


class PeerMatchingService:
    """同伴配对引擎"""

    def __init__(self, db: Session):
        self.db = db

    # ── Public API ──────────────────────────────

    def recommend_peers(
        self,
        grower_id: int,
        top_n: int = 3,
        mentor_role: str = "sharer",
    ) -> dict:
        """
        为Grower推荐同伴Sharer (或Coach) 候选人
        Returns: { candidates: [...], grower_profile: {...} }
        """
        grower = self.db.query(User).filter(User.id == grower_id).first()
        if not grower:
            return {"error": "用户不存在", "candidates": []}

        grower_journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == grower_id
        ).first()

        grower_stage = grower_journey.journey_stage if grower_journey else "s0_authorization"
        grower_profile = grower.profile or {}

        # Find eligible mentors (Sharer or Coach)
        min_role_level = 3 if mentor_role == "sharer" else 4
        eligible_mentors = self._find_eligible_mentors(
            grower_id, min_role_level, mentor_role
        )

        if not eligible_mentors:
            return {
                "grower_id": grower_id,
                "grower_stage": grower_stage,
                "candidates": [],
                "message": "暂无可匹配的同伴",
            }

        # Score each candidate
        scored = []
        for mentor in eligible_mentors:
            score = self._compute_match_score(
                grower, grower_stage, grower_profile, mentor
            )
            scored.append((mentor, score))

        # Sort by total score descending, take top_n
        scored.sort(key=lambda x: x[1]["total"], reverse=True)
        candidates = []
        for mentor, score_detail in scored[:top_n]:
            mentor_journey = self.db.query(JourneyState).filter(
                JourneyState.user_id == mentor.id
            ).first()
            candidates.append({
                "mentor_id": mentor.id,
                "username": mentor.username,
                "nickname": mentor.nickname,
                "role": mentor.role.value if hasattr(mentor.role, 'value') else mentor.role,
                "stage": mentor_journey.journey_stage if mentor_journey else None,
                "agency_mode": mentor_journey.agency_mode if mentor_journey else "passive",
                "match_score": round(score_detail["total"], 3),
                "score_breakdown": {
                    k: round(v, 3) for k, v in score_detail.items() if k != "total"
                },
                "current_mentee_count": self._count_active_mentees(mentor.id),
                "avg_quality_score": self._avg_quality(mentor.id),
            })

        return {
            "grower_id": grower_id,
            "grower_stage": grower_stage,
            "candidates": candidates,
            "total_eligible": len(eligible_mentors),
        }

    def accept_peer(
        self,
        grower_id: int,
        mentor_id: int,
    ) -> dict:
        """Grower 选择同伴, 创建关系"""
        # Verify both users exist
        grower = self.db.query(User).filter(User.id == grower_id).first()
        mentor = self.db.query(User).filter(User.id == mentor_id).first()
        if not grower or not mentor:
            return {"error": "用户不存在"}

        # Check for existing relation
        existing = self.db.query(CompanionRelation).filter(
            CompanionRelation.mentor_id == mentor_id,
            CompanionRelation.mentee_id == grower_id,
        ).first()
        if existing:
            return {"error": "已存在配对关系", "relation_id": str(existing.id)}

        # Check mentor capacity
        capacity = self._mentor_capacity(mentor)
        active_count = self._count_active_mentees(mentor_id)
        if active_count >= capacity:
            return {"error": f"该同伴已满 ({active_count}/{capacity})"}

        # Create relation
        relation = CompanionRelation(
            mentor_id=mentor_id,
            mentee_id=grower_id,
            mentor_role=mentor.role.value if hasattr(mentor.role, 'value') else str(mentor.role),
            mentee_role=grower.role.value if hasattr(grower.role, 'value') else str(grower.role),
            status=CompanionStatus.ACTIVE.value,
        )
        self.db.add(relation)
        self.db.flush()

        return {
            "relation_id": str(relation.id),
            "mentor_id": mentor_id,
            "mentee_id": grower_id,
            "status": "active",
            "message": "配对成功",
        }

    def get_match_stats(self) -> dict:
        """Platform-wide matching statistics"""
        total_relations = self.db.query(CompanionRelation).count()
        active = self.db.query(CompanionRelation).filter(
            CompanionRelation.status == CompanionStatus.ACTIVE.value
        ).count()
        graduated = self.db.query(CompanionRelation).filter(
            CompanionRelation.status == CompanionStatus.GRADUATED.value
        ).count()

        # Sharers with capacity
        sharers_total = self.db.query(User).filter(
            User.role == UserRole.SHARER, User.is_active == True
        ).count()

        # Unmatched growers
        matched_mentee_ids = self.db.query(CompanionRelation.mentee_id).filter(
            CompanionRelation.status == CompanionStatus.ACTIVE.value
        ).subquery()
        unmatched_growers = self.db.query(User).filter(
            User.role == UserRole.GROWER,
            User.is_active == True,
            ~User.id.in_(matched_mentee_ids),
        ).count()

        return {
            "total_relations": total_relations,
            "active": active,
            "graduated": graduated,
            "sharers_total": sharers_total,
            "unmatched_growers": unmatched_growers,
        }

    # ── Internal helpers ────────────────────────

    def _find_eligible_mentors(
        self, grower_id: int, min_level: int, mentor_role: str
    ) -> List[User]:
        """找到有资格且有余量的导师"""
        # Get roles at or above min_level
        eligible_roles = [
            r for r, lv in ROLE_LEVEL_STR.items()
            if lv >= min_level and lv < 90
        ]

        mentors = self.db.query(User).filter(
            User.role.in_(eligible_roles),
            User.is_active == True,
            User.id != grower_id,
        ).all()

        # Filter by capacity
        result = []
        for m in mentors:
            cap = self._mentor_capacity(m)
            current = self._count_active_mentees(m.id)
            if current < cap:
                result.append(m)
        return result

    def _compute_match_score(
        self,
        grower: User,
        grower_stage: str,
        grower_profile: dict,
        mentor: User,
    ) -> dict:
        """计算配对分数 (0-1 range for each dimension)"""
        # 1. Stage proximity
        mentor_journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == mentor.id
        ).first()
        mentor_stage = mentor_journey.journey_stage if mentor_journey else "s5_graduation"
        stage_score = self._stage_proximity_score(grower_stage, mentor_stage)

        # 2. Condition overlap
        mentor_profile = mentor.profile or {}
        condition_score = self._condition_overlap_score(grower_profile, mentor_profile)

        # 3. Goal alignment
        goal_score = self._goal_alignment_score(grower_profile, mentor_profile)

        # 4. Quality history
        quality_score = self._quality_history_score(mentor.id)

        # 5. Availability
        avail_score = self._availability_score(mentor)

        total = (
            WEIGHTS["stage_proximity"] * stage_score
            + WEIGHTS["condition_overlap"] * condition_score
            + WEIGHTS["goal_alignment"] * goal_score
            + WEIGHTS["quality_history"] * quality_score
            + WEIGHTS["availability"] * avail_score
        )

        return {
            "total": total,
            "stage_proximity": stage_score,
            "condition_overlap": condition_score,
            "goal_alignment": goal_score,
            "quality_history": quality_score,
            "availability": avail_score,
        }

    def _stage_proximity_score(self, grower_stage: str, mentor_stage: str) -> float:
        """
        Stage proximity: mentor should be 1-2 stages ahead (best).
        Same stage = good. Too far ahead = less relatable.
        """
        try:
            g_idx = _STAGE_ORDER.index(grower_stage)
        except ValueError:
            g_idx = 0
        try:
            m_idx = _STAGE_ORDER.index(mentor_stage)
        except ValueError:
            m_idx = 5

        diff = m_idx - g_idx
        if diff == 1:
            return 1.0   # Ideal: 1 stage ahead
        elif diff == 2:
            return 0.85  # Good: 2 stages ahead
        elif diff == 0:
            return 0.7   # OK: same stage (peer support)
        elif diff == 3:
            return 0.5   # Acceptable: 3 stages ahead
        elif diff < 0:
            return 0.2   # Mentor behind grower (unusual)
        else:
            return 0.3   # Very far ahead

    def _condition_overlap_score(self, g_prof: dict, m_prof: dict) -> float:
        """Chronic condition overlap (Jaccard similarity)"""
        g_conditions = set(g_prof.get("chronic_conditions", []))
        m_conditions = set(m_prof.get("chronic_conditions", []))
        if not g_conditions and not m_conditions:
            return 0.5  # No data: neutral
        if not g_conditions or not m_conditions:
            return 0.3
        intersection = g_conditions & m_conditions
        union = g_conditions | m_conditions
        return len(intersection) / len(union) if union else 0.5

    def _goal_alignment_score(self, g_prof: dict, m_prof: dict) -> float:
        """Goal overlap (Jaccard similarity)"""
        g_goals = set(g_prof.get("goals", []))
        m_goals = set(m_prof.get("goals", []))
        if not g_goals and not m_goals:
            return 0.5
        if not g_goals or not m_goals:
            return 0.3
        intersection = g_goals & m_goals
        union = g_goals | m_goals
        return len(intersection) / len(union) if union else 0.5

    def _quality_history_score(self, mentor_id: int) -> float:
        """Mentor's historical quality: avg quality_score of graduated mentees"""
        avg = self.db.query(func.avg(CompanionRelation.quality_score)).filter(
            CompanionRelation.mentor_id == mentor_id,
            CompanionRelation.quality_score.isnot(None),
        ).scalar()
        if avg is None:
            return 0.5  # No history: neutral
        return min(float(avg) / 5.0, 1.0)  # Normalize to 0-1

    def _availability_score(self, mentor: User) -> float:
        """Score based on remaining mentee capacity"""
        cap = self._mentor_capacity(mentor)
        current = self._count_active_mentees(mentor.id)
        remaining = cap - current
        if remaining <= 0:
            return 0.0
        return min(remaining / cap, 1.0)

    def _mentor_capacity(self, mentor: User) -> int:
        """Maximum mentees based on role"""
        role = mentor.role.value if hasattr(mentor.role, 'value') else str(mentor.role)
        level = ROLE_LEVEL_STR.get(role, 1)
        if level >= 4:  # Coach+
            return COACH_MAX_MENTEES
        return SHARER_MAX_MENTEES

    def _count_active_mentees(self, mentor_id: int) -> int:
        return self.db.query(CompanionRelation).filter(
            CompanionRelation.mentor_id == mentor_id,
            CompanionRelation.status == CompanionStatus.ACTIVE.value,
        ).count()

    def _avg_quality(self, mentor_id: int) -> Optional[float]:
        avg = self.db.query(func.avg(CompanionRelation.quality_score)).filter(
            CompanionRelation.mentor_id == mentor_id,
            CompanionRelation.quality_score.isnot(None),
        ).scalar()
        return round(float(avg), 2) if avg else None

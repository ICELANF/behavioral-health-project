"""
V4.0 Reputation & Referral Engine — 口碑传播引擎 (MEU-37)

Features:
  - Referral code generation & tracking
  - Social proof display (growth stories)
  - Ambassador program for active users
  - Referral metrics & analytics
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from core.models import User, JourneyState, ROLE_LEVEL_STR

logger = logging.getLogger(__name__)


# ── Ambassador Tiers ────────────────────────────

AMBASSADOR_TIERS = {
    "seed": {
        "min_referrals": 1,
        "label": "种子传播者",
        "perks": ["referral_badge"],
    },
    "sprout": {
        "min_referrals": 3,
        "label": "成长传播者",
        "perks": ["referral_badge", "bonus_awareness_points"],
    },
    "tree": {
        "min_referrals": 10,
        "label": "大树传播者",
        "perks": ["referral_badge", "bonus_awareness_points", "priority_support"],
    },
    "forest": {
        "min_referrals": 25,
        "label": "森林传播者",
        "perks": ["referral_badge", "bonus_awareness_points", "priority_support", "ambassador_title"],
    },
}

# Points awarded for referrals
REFERRAL_POINTS = {
    "referrer_signup": 20,      # When referral signs up
    "referrer_activation": 50,  # When referral reaches S1
    "referee_bonus": 10,        # Bonus for the new user
}


class ReferralEngine:
    """口碑传播引擎"""

    def __init__(self, db: Session):
        self.db = db

    def generate_referral_code(self, user_id: int) -> dict:
        """生成用户的邀请码"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "用户不存在"}

        # Deterministic code based on user_id
        raw = f"bhp-referral-{user_id}-{user.username}"
        code = hashlib.md5(raw.encode()).hexdigest()[:8].upper()

        return {
            "user_id": user_id,
            "referral_code": code,
            "share_url": f"/register?ref={code}",
            "share_text": f"加入行健平台, 一起发现更好的自己! 邀请码: {code}",
        }

    def get_referral_stats(self, user_id: int) -> dict:
        """获取用户的邀请统计"""
        # Count users who were referred by this user
        # Uses conversion_source field or referred_by if available
        referred_count = 0
        activated_count = 0

        try:
            referred = self.db.query(JourneyState).filter(
                JourneyState.conversion_source == f"referral_{user_id}",
            ).all()
            referred_count = len(referred)
            activated_count = sum(
                1 for j in referred
                if j.journey_stage not in ("s0_authorization",)
            )
        except Exception:
            pass

        # Determine ambassador tier
        tier = self._get_ambassador_tier(referred_count)

        return {
            "user_id": user_id,
            "total_referrals": referred_count,
            "activated_referrals": activated_count,
            "ambassador_tier": tier,
            "ambassador_info": AMBASSADOR_TIERS.get(tier, {}),
            "next_tier": self._next_tier(referred_count),
            "points_earned": referred_count * REFERRAL_POINTS["referrer_signup"]
                + activated_count * REFERRAL_POINTS["referrer_activation"],
        }

    def get_growth_stories(self, limit: int = 5) -> List[dict]:
        """获取成长故事 (社交证明)"""
        # Find users who have progressed significantly
        advanced_users = self.db.query(JourneyState).filter(
            JourneyState.journey_stage.in_(["s3_pathway", "s4_internalization", "s5_graduation"]),
        ).order_by(func.random()).limit(limit).all()

        stories = []
        for j in advanced_users:
            user = self.db.query(User).filter(User.id == j.user_id).first()
            if user:
                stories.append({
                    "anonymous_name": f"用户{user.id:04d}",
                    "stage": j.journey_stage,
                    "agency_mode": j.agency_mode,
                    "days_on_platform": (datetime.utcnow() - j.created_at).days if j.created_at else 0,
                    "stage_transitions": j.stage_transition_count or 0,
                })

        return stories

    def get_platform_social_proof(self) -> dict:
        """平台级社交证明数据"""
        total_users = self.db.query(User).filter(User.is_active == True).count()

        # Users who advanced past S1
        advanced = self.db.query(JourneyState).filter(
            JourneyState.journey_stage.notin_(["s0_authorization", "s1_awareness"]),
        ).count()

        active_users = self.db.query(JourneyState).filter(
            JourneyState.agency_mode.in_(["transitional", "active"]),
        ).count()

        return {
            "total_users": total_users,
            "advanced_users": advanced,
            "active_agency_users": active_users,
            "advancement_rate": round(advanced / total_users, 3) if total_users else 0,
            "highlight": f"已有{advanced}名用户进入行为改变阶段",
        }

    def _get_ambassador_tier(self, referrals: int) -> str:
        """Determine ambassador tier"""
        if referrals >= 25:
            return "forest"
        elif referrals >= 10:
            return "tree"
        elif referrals >= 3:
            return "sprout"
        elif referrals >= 1:
            return "seed"
        return "none"

    def _next_tier(self, referrals: int) -> Optional[dict]:
        """Next tier info"""
        for tier_id, tier in AMBASSADOR_TIERS.items():
            if referrals < tier["min_referrals"]:
                return {
                    "tier": tier_id,
                    "label": tier["label"],
                    "referrals_needed": tier["min_referrals"] - referrals,
                }
        return None  # Already at max tier

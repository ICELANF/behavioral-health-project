"""
V4.0 Three-Phase Incentive Transformation — 三阶觉醒激励

Table 4:
  Phase 1 (passive):
    - Checkin → "每日一个发现" (Daily Discovery)
    - Points: normal display, not homepage focus
    - Leaderboard: hidden → "同行者匿名发现"
    - Drive: curiosity + seeing

  Phase 2 (transitional):
    - Checkin → "你想探索什么?" (Open-ended)
    - Points: collapsed → growth narrative timeline
    - Leaderboard: optional → "最有趣的发现"
    - Drive: autonomy + awareness

  Phase 3 (active):
    - Checkin: completely hidden
    - Points: completely hidden (backend still accumulates)
    - Leaderboard → influence map
    - Drive: identity recognition + altruism

觉察积分 (MEU-25):
  New point type "awareness" distinct from growth/contribution/influence.
  Consumption scenarios: unlock content, request expert review, gift to peer.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, Dict, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from core.models import (
    User, JourneyState, UserPoint,
    PointTransaction, ROLE_LEVEL_STR,
)

logger = logging.getLogger(__name__)


# ── Phase Definitions (Table 4) ─────────────────

INCENTIVE_PHASES = {
    "passive": {
        "phase": 1,
        "label": "方向引导",
        "checkin": {
            "style": "daily_discovery",
            "prompt": "每日一个发现",
            "description": "用轻松的'发现'替代打卡按钮, 降低任务感",
        },
        "points_display": {
            "visible": True,
            "emphasis": "low",
            "homepage_focus": False,
            "format": "numeric",
        },
        "leaderboard": {
            "visible": False,
            "replacement": "fellow_anonymous_discoveries",
            "description": "同行者匿名发现 (隐藏排名)",
        },
        "core_drive": ["curiosity", "seeing"],
    },
    "transitional": {
        "phase": 2,
        "label": "自主探索",
        "checkin": {
            "style": "open_exploration",
            "prompt": "你想探索什么?",
            "description": "开放式入口, 鼓励自定义探索方向",
        },
        "points_display": {
            "visible": True,
            "emphasis": "minimal",
            "homepage_focus": False,
            "format": "growth_narrative",
            "collapsed_by_default": True,
        },
        "leaderboard": {
            "visible": True,
            "optional": True,
            "replacement": "most_interesting_discoveries",
            "description": "最有趣的发现 (非竞争性排名)",
        },
        "core_drive": ["autonomy", "awareness"],
    },
    "active": {
        "phase": 3,
        "label": "身份确认",
        "checkin": {
            "style": "hidden",
            "prompt": None,
            "description": "完全隐藏打卡, 后端仍记录",
        },
        "points_display": {
            "visible": False,
            "emphasis": "none",
            "homepage_focus": False,
            "format": "hidden",
            "backend_still_accumulates": True,
        },
        "leaderboard": {
            "visible": False,
            "replacement": "influence_map",
            "description": "影响力地图 (替代排行榜)",
        },
        "core_drive": ["identity_recognition", "altruism"],
    },
}


# ── Awareness Point Events ──────────────────────

AWARENESS_POINT_EVENTS = {
    "reflection_journal": {"amount": 10, "max_per_day": 3, "description": "写反思日记"},
    "pattern_recognition": {"amount": 20, "max_per_day": 2, "description": "识别行为模式"},
    "insight_share": {"amount": 15, "max_per_day": 3, "description": "分享觉察心得"},
    "emotion_naming": {"amount": 5, "max_per_day": 5, "description": "情绪命名练习"},
    "behavior_observation": {"amount": 8, "max_per_day": 3, "description": "行为自我观察"},
    "identity_reflection": {"amount": 30, "max_per_day": 1, "description": "身份层面反思"},
}

# ── Point Consumption Scenarios ─────────────────

POINT_CONSUMPTION = {
    "unlock_premium_content": {
        "cost": 50,
        "point_type": "awareness",
        "description": "解锁进阶内容",
    },
    "request_expert_review": {
        "cost": 100,
        "point_type": "awareness",
        "description": "请求专家点评",
    },
    "gift_to_peer": {
        "cost": 20,
        "point_type": "awareness",
        "description": "赠送同伴积分",
        "min_amount": 10,
        "max_amount": 100,
    },
    "custom_agent_session": {
        "cost": 30,
        "point_type": "awareness",
        "description": "自定义Agent深度对话",
    },
    "certificate_request": {
        "cost": 200,
        "point_type": "growth",
        "description": "申请阶段证书",
    },
}


class IncentivePhaseEngine:
    """三阶觉醒激励引擎"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_incentive_config(self, user_id: int) -> dict:
        """根据用户agency_mode返回激励阶段配置"""
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()
        mode = journey.agency_mode if journey else "passive"
        phase_config = INCENTIVE_PHASES.get(mode, INCENTIVE_PHASES["passive"])

        return {
            "user_id": user_id,
            "agency_mode": mode,
            "agency_score": journey.agency_score if journey else 0.0,
            "phase": phase_config,
        }

    def award_awareness_points(
        self,
        user_id: int,
        event: str,
        custom_amount: int = None,
    ) -> dict:
        """发放觉察积分"""
        if event not in AWARENESS_POINT_EVENTS:
            return {"error": f"未知的觉察积分事件: {event}"}

        evt = AWARENESS_POINT_EVENTS[event]
        amount = custom_amount if custom_amount else evt["amount"]

        # Check daily limit
        if evt["max_per_day"] > 0:
            today_count = self._today_event_count(user_id, event)
            if today_count >= evt["max_per_day"]:
                return {
                    "error": f"今日{event}已达上限({evt['max_per_day']}次)",
                    "today_count": today_count,
                }

        # Create transaction
        tx = PointTransaction(
            user_id=user_id,
            action=event,
            point_type="awareness",
            amount=amount,
        )
        self.db.add(tx)

        # Update user_points
        self._update_awareness_balance(user_id, amount)
        self.db.flush()

        return {
            "user_id": user_id,
            "event": event,
            "amount": amount,
            "point_type": "awareness",
            "description": evt["description"],
        }

    def consume_points(
        self,
        user_id: int,
        scenario: str,
        custom_cost: int = None,
        target_user_id: int = None,
    ) -> dict:
        """消费积分"""
        if scenario not in POINT_CONSUMPTION:
            return {"error": f"未知消费场景: {scenario}"}

        config = POINT_CONSUMPTION[scenario]
        cost = custom_cost if custom_cost else config["cost"]
        point_type = config["point_type"]

        # Check balance
        balance = self._get_balance(user_id, point_type)
        if balance < cost:
            return {
                "error": f"{point_type}积分不足 (需要{cost}, 当前{balance})",
                "balance": balance,
                "cost": cost,
            }

        # Deduct
        tx = PointTransaction(
            user_id=user_id,
            action=f"consume_{scenario}",
            point_type=point_type,
            amount=-cost,
        )
        self.db.add(tx)
        self._update_balance(user_id, point_type, -cost)

        # Gift scenario: credit target user
        if scenario == "gift_to_peer" and target_user_id:
            gift_tx = PointTransaction(
                user_id=target_user_id,
                action="receive_gift",
                point_type="awareness",
                amount=cost,
            )
            self.db.add(gift_tx)
            self._update_awareness_balance(target_user_id, cost)

        self.db.flush()

        return {
            "user_id": user_id,
            "scenario": scenario,
            "cost": cost,
            "point_type": point_type,
            "remaining_balance": balance - cost,
            "description": config["description"],
            "target_user_id": target_user_id,
        }

    def get_awareness_balance(self, user_id: int) -> dict:
        """获取觉察积分余额"""
        balance = self._get_balance(user_id, "awareness")
        growth = self._get_balance(user_id, "growth")
        contribution = self._get_balance(user_id, "contribution")
        influence = self._get_balance(user_id, "influence")

        return {
            "user_id": user_id,
            "awareness": balance,
            "growth": growth,
            "contribution": contribution,
            "influence": influence,
            "total": balance + growth + contribution + influence,
        }

    def get_consumption_catalog(self) -> dict:
        """获取积分消费目录"""
        return POINT_CONSUMPTION

    def get_awareness_events(self) -> dict:
        """获取觉察积分事件目录"""
        return AWARENESS_POINT_EVENTS

    # ── Internal helpers ────────────────────────

    def _today_event_count(self, user_id: int, action: str) -> int:
        today = datetime.utcnow().date()
        try:
            return self.db.query(PointTransaction).filter(
                PointTransaction.user_id == user_id,
                PointTransaction.action == action,
                func.date(PointTransaction.created_at) == today,
            ).count()
        except Exception:
            return 0

    def _get_balance(self, user_id: int, point_type: str) -> int:
        """Get point balance by type from user_points table"""
        try:
            up = self.db.query(UserPoint).filter(
                UserPoint.user_id == user_id,
                UserPoint.point_type == point_type,
            ).first()
            return up.balance if up else 0
        except Exception:
            return 0

    def _update_awareness_balance(self, user_id: int, amount: int):
        """Update or create awareness point balance"""
        self._update_balance(user_id, "awareness", amount)

    def _update_balance(self, user_id: int, point_type: str, amount: int):
        """Update point balance"""
        try:
            up = self.db.query(UserPoint).filter(
                UserPoint.user_id == user_id,
                UserPoint.point_type == point_type,
            ).first()
            if up:
                up.balance = (up.balance or 0) + amount
                up.total_earned = (up.total_earned or 0) + max(amount, 0)
            else:
                up = UserPoint(
                    user_id=user_id,
                    point_type=point_type,
                    balance=max(amount, 0),
                    total_earned=max(amount, 0),
                )
                self.db.add(up)
        except Exception as e:
            logger.warning(f"Point balance update failed: {e}")

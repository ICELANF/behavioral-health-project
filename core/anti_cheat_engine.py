"""
V4.0 Anti-Cheat Strategy Engine — 六种防刷策略

Sheet ⑦ 防刷策略矩阵:
  AS-01 每日上限: 同一积分行为每日获取上限
  AS-02 质量加权: 高质量贡献×2, 低质量×0.5
  AS-03 时间衰减: 同一行为重复执行积分逐次递减
  AS-04 交叉验证: 涉及他人的积分需对方确认
  AS-05 成长轨校验: 积分达标但成长轨不过=不晋级
  AS-06 异常检测: 短时间大量相同行为→标记审查
"""
from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from core.models import AntiCheatEvent

logger = logging.getLogger(__name__)

# ── Daily Caps (AS-01) ────────────────────────────────────
DAILY_CAPS = {
    "daily_checkin": 1,
    "complete_lesson": 5,
    "complete_assessment": 2,
    "behavior_attempt": 3,
    "path_contribution": 3,
    "content_publish": 3,
    "community_reply": 10,
    "case_share": 2,
    "alert_handled": 5,
    "message_reply": 10,
    "agent_feedback_reply": 5,
    "knowledge_sharing": 3,
}

# ── Quality Multipliers (AS-02) ───────────────────────────
QUALITY_MULTIPLIERS = {
    "high": 2.0,
    "normal": 1.0,
    "low": 0.5,
}

# ── Time Decay Curve (AS-03) ─────────────────────────────
# After N repetitions, multiplier drops
DECAY_THRESHOLDS = [
    (5, 1.0),    # 1-5: full points
    (10, 0.8),   # 6-10: 80%
    (20, 0.5),   # 11-20: 50%
    (999, 0.2),  # 21+: 20%
]

# ── Anomaly Detection (AS-06) ─────────────────────────────
ANOMALY_RULES = {
    "same_action_1h_max": 20,      # >20 same actions in 1 hour
    "total_actions_1h_max": 50,     # >50 total actions in 1 hour
    "late_night_flag": True,        # Flag activity 2-5 AM
}


class AntiCheatEngine:
    """六种防刷策略引擎"""

    def __init__(self, db: Session):
        self.db = db

    def check_daily_cap(self, user_id: int, action: str) -> dict:
        """AS-01: 检查每日上限"""
        cap = DAILY_CAPS.get(action, 0)
        if cap == 0:
            return {"allowed": True, "cap": 0, "used": 0, "strategy": "AS-01"}

        today = date.today()
        from core.models import PointTransaction
        try:
            used = self.db.query(func.count(PointTransaction.id)).filter(
                PointTransaction.user_id == user_id,
                PointTransaction.event_type == action,
                func.date(PointTransaction.created_at) == today,
            ).scalar() or 0
        except Exception:
            used = 0

        allowed = used < cap
        if not allowed:
            self._log_event(user_id, "AS-01", "daily_cap_hit",
                            {"action": action, "cap": cap, "used": used},
                            "blocked")
        return {
            "allowed": allowed,
            "cap": cap,
            "used": used,
            "remaining": max(0, cap - used),
            "strategy": "AS-01",
            "message": f"今日该项积分已达上限, 明天继续" if not allowed else None,
        }

    def apply_quality_weight(self, base_points: int, quality: str = "normal") -> dict:
        """AS-02: 质量加权"""
        multiplier = QUALITY_MULTIPLIERS.get(quality, 1.0)
        adjusted = int(base_points * multiplier)
        return {
            "original": base_points,
            "multiplier": multiplier,
            "adjusted": adjusted,
            "quality": quality,
            "strategy": "AS-02",
        }

    def apply_time_decay(self, user_id: int, action: str, base_points: int) -> dict:
        """AS-03: 时间衰减"""
        # Count recent repetitions of same action (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        from core.models import PointTransaction
        try:
            repetitions = self.db.query(func.count(PointTransaction.id)).filter(
                PointTransaction.user_id == user_id,
                PointTransaction.event_type == action,
                PointTransaction.created_at >= week_ago,
            ).scalar() or 0
        except Exception:
            repetitions = 0

        multiplier = 1.0
        for threshold, mult in DECAY_THRESHOLDS:
            if repetitions <= threshold:
                multiplier = mult
                break

        adjusted = int(base_points * multiplier)

        if multiplier < 1.0:
            self._log_event(user_id, "AS-03", "time_decay_applied",
                            {"action": action, "repetitions": repetitions,
                             "multiplier": multiplier})

        return {
            "original": base_points,
            "repetitions_7d": repetitions,
            "multiplier": multiplier,
            "adjusted": adjusted,
            "strategy": "AS-03",
            "message": "尝试不同行为获得更多积分" if multiplier < 1.0 else None,
        }

    def require_cross_validation(self, action: str) -> bool:
        """AS-04: 判断是否需要交叉验证"""
        cross_validate_actions = [
            "mentee_graduated",
            "companion_train_l0", "companion_train_l1",
            "companion_train_l2", "companion_train_l3", "companion_train_l4",
            "case_share",
        ]
        return action in cross_validate_actions

    def check_growth_track(self, user_id: int) -> dict:
        """AS-05: 成长轨校验 — 积分再多成长轨不过=不晋级"""
        from core.dual_track_engine import DualTrackEngine
        engine = DualTrackEngine(self.db)
        result = engine.check_dual_track(user_id)
        return {
            "strategy": "AS-05",
            "status": result.get("status", "normal_growth"),
            "points_passed": result.get("points_track", {}).get("passed", False),
            "growth_passed": result.get("growth_track", {}).get("passed", False),
            "can_promote": result.get("status") == "promotion_ready",
        }

    def detect_anomaly(self, user_id: int) -> dict:
        """AS-06: 异常检测"""
        anomalies = []
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)

        from core.models import PointTransaction
        try:
            # Check same-action frequency
            action_counts = self.db.query(
                PointTransaction.event_type,
                func.count(PointTransaction.id).label("cnt"),
            ).filter(
                PointTransaction.user_id == user_id,
                PointTransaction.created_at >= one_hour_ago,
            ).group_by(PointTransaction.event_type).all()

            for action, cnt in action_counts:
                if cnt > ANOMALY_RULES["same_action_1h_max"]:
                    anomalies.append({
                        "type": "high_frequency_same_action",
                        "action": action,
                        "count": cnt,
                        "threshold": ANOMALY_RULES["same_action_1h_max"],
                    })

            # Check total actions
            total = sum(cnt for _, cnt in action_counts)
            if total > ANOMALY_RULES["total_actions_1h_max"]:
                anomalies.append({
                    "type": "high_frequency_total",
                    "total_count": total,
                    "threshold": ANOMALY_RULES["total_actions_1h_max"],
                })
        except Exception as e:
            logger.warning(f"Anomaly detection error: {e}")

        if anomalies:
            self._log_event(user_id, "AS-06", "anomaly_detected",
                            {"anomalies": anomalies}, "flagged_for_review")

        return {
            "strategy": "AS-06",
            "anomalies_found": len(anomalies),
            "anomalies": anomalies,
            "flagged": len(anomalies) > 0,
        }

    def validate_point_award(self, user_id: int, action: str,
                             base_points: int, quality: str = "normal") -> dict:
        """综合校验：一次性检查所有防刷策略后返回最终积分"""
        # AS-01: Daily cap
        cap_check = self.check_daily_cap(user_id, action)
        if not cap_check["allowed"]:
            return {
                "allowed": False,
                "reason": "daily_cap",
                "final_points": 0,
                **cap_check,
            }

        # AS-02: Quality weighting
        quality_result = self.apply_quality_weight(base_points, quality)
        adjusted = quality_result["adjusted"]

        # AS-03: Time decay
        decay_result = self.apply_time_decay(user_id, action, adjusted)
        final_points = decay_result["adjusted"]

        # AS-04: Cross-validation needed?
        needs_cv = self.require_cross_validation(action)

        # AS-06: Anomaly check (async, non-blocking)
        anomaly = self.detect_anomaly(user_id)
        if anomaly["flagged"]:
            final_points = 0  # Block points if anomaly detected

        return {
            "allowed": final_points > 0,
            "final_points": final_points,
            "original_points": base_points,
            "quality_multiplier": quality_result["multiplier"],
            "decay_multiplier": decay_result["multiplier"],
            "needs_cross_validation": needs_cv,
            "anomaly_flagged": anomaly["flagged"],
            "strategies_applied": ["AS-01", "AS-02", "AS-03", "AS-04", "AS-06"],
        }

    def get_user_events(self, user_id: int, limit: int = 20) -> list:
        """获取用户的防刷事件记录"""
        events = self.db.query(AntiCheatEvent).filter(
            AntiCheatEvent.user_id == user_id
        ).order_by(AntiCheatEvent.created_at.desc()).limit(limit).all()

        return [
            {
                "id": e.id,
                "strategy": e.strategy,
                "event_type": e.event_type,
                "details": e.details,
                "action_taken": e.action_taken,
                "resolved": e.resolved,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]

    def _log_event(self, user_id: int, strategy: str, event_type: str,
                    details: dict = None, action_taken: str = None):
        """记录防刷事件"""
        event = AntiCheatEvent(
            user_id=user_id,
            strategy=strategy,
            event_type=event_type,
            details=details or {},
            action_taken=action_taken,
        )
        self.db.add(event)

"""
V4.0 Trust Score Service — 信任评分计算引擎

trust_score = 对话深度(25%) + 主动回访率(20%) + 话题开放度(15%)
            + 情绪表达意愿(15%) + 自主信息分享(15%) + 好奇心表达(10%)

应用逻辑:
  <0.3  → 信任未建立: Agent 不推行为建议，只展示数据
  0.3-0.5 → 信任初建: 可以温和地引入评估
  >0.5  → 信任稳固: 可以开展深度干预工作
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text

from core.models import (
    JourneyState, TrustScoreLog, BehavioralProfile, User,
)

# ── 情绪关键词 (中文) ──────────────────────────────
_EMOTION_KEYWORDS = {
    "开心", "高兴", "快乐", "幸福", "满足", "感恩", "欣慰", "放松",
    "难过", "伤心", "焦虑", "紧张", "压力", "担心", "害怕", "生气",
    "烦躁", "失落", "委屈", "孤独", "疲惫", "无聊", "郁闷", "沮丧",
    "感动", "惊喜", "期待", "自豪", "安心", "舒服", "痛苦", "不安",
}


def extract_trust_signals_from_checkins(
    db: Session, user_id: int, days: int = 7,
) -> Dict[str, float]:
    """
    从用户近 N 天的打卡数据中提取 6 个信任信号 (启发式，非 AI)。

    Returns dict with keys matching TRUST_SIGNALS:
      dialog_depth, proactive_return_rate, topic_openness,
      emotion_expression, autonomous_info_sharing, curiosity_expression
    """
    # 查询近 N 天的打卡记录 + 对应的 daily_task
    rows = db.execute(text("""
        SELECT tc.note, tc.photo_url, tc.voice_url, tc.value,
               tc.checked_at::date AS checkin_date,
               dt.tag
        FROM task_checkins tc
        JOIN daily_tasks dt ON dt.id = tc.task_id
        WHERE tc.user_id = :uid
          AND tc.checked_at >= NOW() - INTERVAL ':days days'
        ORDER BY tc.checked_at
    """.replace(":days", str(int(days)))), {"uid": user_id}).mappings().all()

    if not rows:
        return {k: 0.0 for k in TRUST_SIGNALS}

    # 查询近 N 天有 daily_tasks 的天数 (分母)
    total_days_row = db.execute(text("""
        SELECT COUNT(DISTINCT task_date) AS cnt
        FROM daily_tasks
        WHERE user_id = :uid
          AND task_date >= CURRENT_DATE - INTERVAL ':days days'
    """.replace(":days", str(int(days)))), {"uid": user_id}).mappings().first()
    total_task_days = max((total_days_row["cnt"] if total_days_row else 0), 1)

    # ── 信号 1: dialog_depth — note 文字深度 ──
    notes = [r["note"] or "" for r in rows]
    if notes:
        avg_len = sum(len(n) for n in notes) / len(notes)
        dialog_depth = min(avg_len / 50.0, 1.0)  # 50字 = 1.0
    else:
        dialog_depth = 0.0

    # ── 信号 2: proactive_return_rate — 连续打卡天 / 总天 ──
    checkin_dates = sorted(set(r["checkin_date"] for r in rows))
    proactive_return_rate = min(len(checkin_dates) / max(total_task_days, 1), 1.0)

    # ── 信号 3: topic_openness — 不同 tag 种类数 / 最大种类 ──
    tags = set(r["tag"] for r in rows if r["tag"])
    max_possible_tags = 6  # 营养/运动/监测/睡眠/情绪/学习
    topic_openness = min(len(tags) / max_possible_tags, 1.0)

    # ── 信号 4: emotion_expression — note 含情绪关键词的比例 ──
    notes_with_emotion = sum(
        1 for n in notes if n and any(kw in n for kw in _EMOTION_KEYWORDS)
    )
    emotion_expression = notes_with_emotion / len(rows) if rows else 0.0

    # ── 信号 5: autonomous_info_sharing — 主动提供 photo/voice/value 的比例 ──
    sharing_count = sum(
        1 for r in rows
        if r["photo_url"] or r["voice_url"] or r["value"] is not None
    )
    autonomous_info_sharing = sharing_count / len(rows) if rows else 0.0

    # ── 信号 6: curiosity_expression — 打卡附带 note 的比例 ──
    notes_present = sum(1 for n in notes if n.strip())
    curiosity_expression = notes_present / len(rows) if rows else 0.0

    return {
        "dialog_depth": round(dialog_depth, 4),
        "proactive_return_rate": round(proactive_return_rate, 4),
        "topic_openness": round(topic_openness, 4),
        "emotion_expression": round(emotion_expression, 4),
        "autonomous_info_sharing": round(autonomous_info_sharing, 4),
        "curiosity_expression": round(curiosity_expression, 4),
    }

# ── Signal weights (V4.0 spec) ──────────────────────────
TRUST_SIGNALS = {
    "dialog_depth": 0.25,
    "proactive_return_rate": 0.20,
    "topic_openness": 0.15,
    "emotion_expression": 0.15,
    "autonomous_info_sharing": 0.15,
    "curiosity_expression": 0.10,
}

# ── Trust level mapping ─────────────────────────────────
def score_to_trust_level(score: float) -> str:
    if score < 0.3:
        return "not_established"
    elif score <= 0.5:
        return "building"
    else:
        return "established"

TRUST_LEVEL_BEHAVIOR = {
    "not_established": {
        "label": "信任未建立",
        "agent_behavior": "只展示数据，不推行为建议",
        "allow_assessment": False,
        "allow_deep_intervention": False,
    },
    "building": {
        "label": "信任初建",
        "agent_behavior": "温和引入评估",
        "allow_assessment": True,
        "allow_deep_intervention": False,
    },
    "established": {
        "label": "信任稳固",
        "agent_behavior": "可以开展深度干预",
        "allow_assessment": True,
        "allow_deep_intervention": True,
    },
}


class TrustScoreService:
    """Compute and persist trust_score for a user."""

    def __init__(self, db: Session):
        self.db = db

    def compute_trust_score(
        self,
        user_id: int,
        signals: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Compute trust_score from six signals.

        Parameters
        ----------
        user_id : int
        signals : dict
            Keys matching TRUST_SIGNALS. Missing keys default to 0.0.
            Values should be 0.0-1.0 normalized.

        Returns
        -------
        dict with score, level, signals, behavior
        """
        if signals is None:
            signals = {}

        weighted_sum = 0.0
        signal_details = {}
        for signal_name, weight in TRUST_SIGNALS.items():
            value = signals.get(signal_name, 0.0)
            value = max(0.0, min(1.0, value))
            weighted_sum += value * weight
            signal_details[signal_name] = {
                "value": round(value, 4),
                "weight": weight,
                "contribution": round(value * weight, 4),
            }

        score = round(max(0.0, min(1.0, weighted_sum)), 4)
        level = score_to_trust_level(score)

        return {
            "score": score,
            "level": level,
            "signals": signal_details,
            "behavior": TRUST_LEVEL_BEHAVIOR[level],
        }

    def update_user_trust(
        self,
        user_id: int,
        signals: Dict[str, float],
        source: str = "system",
    ) -> Dict[str, Any]:
        """Compute, persist trust score and update journey_state + user."""
        result = self.compute_trust_score(user_id, signals)
        score = result["score"]

        # Persist signal logs
        for signal_name, detail in result["signals"].items():
            log = TrustScoreLog(
                user_id=user_id,
                signal_name=signal_name,
                signal_value=detail["value"],
                weight=detail["weight"],
                computed_score=score,
                source=source,
            )
            self.db.add(log)

        # Update journey_state
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()
        if journey:
            journey.trust_score = score
            journey.trust_signals = {k: v["value"] for k, v in result["signals"].items()}
        else:
            journey = JourneyState(
                user_id=user_id,
                trust_score=score,
                trust_signals={k: v["value"] for k, v in result["signals"].items()},
            )
            self.db.add(journey)

        # Update user table shortcut
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.trust_score = score

        # Update behavioral_profile
        bp = self.db.query(BehavioralProfile).filter(
            BehavioralProfile.user_id == user_id
        ).first()
        if bp:
            bp.trust_score = score

        self.db.flush()
        return result

    def get_trust_behavior(self, user_id: int) -> Dict[str, Any]:
        """Get current trust level and agent behavior rules for a user."""
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()
        score = journey.trust_score if journey else 0.0
        level = score_to_trust_level(score)
        return {
            "trust_score": score,
            "trust_level": level,
            **TRUST_LEVEL_BEHAVIOR.get(level, TRUST_LEVEL_BEHAVIOR["not_established"]),
        }

    def check_observer_activation(
        self,
        user_id: int,
    ) -> Dict[str, Any]:
        """
        Check if an Observer meets any of the three activation paths
        for Observer→Grower conversion.

        Path A (curiosity): user proactively says "want to know myself"
                           → target 7-day ≥40% curiosity signal
        Path B (time):      active ≥7 days + ≥3 dialogs
                           → target 14-day ≥60%
        Path C (coach_referred): coach invites, first login
                           → target 3-day ≥85%
        """
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()
        if not journey:
            return {"eligible": False, "paths": {}}

        trust = journey.trust_score or 0.0
        signals = journey.trust_signals or {}
        curiosity = signals.get("curiosity_expression", 0.0)

        user = self.db.query(User).filter(User.id == user_id).first()
        conversion_source = journey.conversion_source

        paths = {
            "A_curiosity": {
                "target": 0.40,
                "current": curiosity,
                "met": curiosity >= 0.40,
                "description": "好奇驱动: 用户主动表达想了解自己",
            },
            "B_time": {
                "target": 0.60,
                "current": trust,
                "met": trust >= 0.60 and (journey.observer_dialog_count or 0) >= 3,
                "description": "时间驱动: 活跃≥7天 + ≥3次对话",
            },
            "C_coach_referred": {
                "target": 0.85,
                "current": trust if conversion_source == "coach_referred" else 0.0,
                "met": conversion_source == "coach_referred" and trust >= 0.85,
                "description": "教练推动: 教练邀请首次登录",
            },
        }

        eligible = any(p["met"] for p in paths.values())
        return {
            "eligible": eligible,
            "trust_score": trust,
            "paths": paths,
        }

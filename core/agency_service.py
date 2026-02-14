"""
V4.0 Agency Mode Service — 主体性三态模型计算引擎

agency_score = S1×0.25 + S2×0.20 + S3×0.20 + S4×0.15 + S5×0.10 + S6×0.10

信号:
  S1 主动发起率 (proactive_initiation_rate)   — 25%
  S2 自主修改率 (self_modification_rate)       — 20%
  S3 主动表达词频 (agency_word_frequency)      — 20%
  S4 觉察深度 (awareness_depth)                — 15%
  S5 教练依赖度 (coach_dependency, 反向)        — 10%
  S6 教练标注 (coach_annotation)               — 10%

映射: <0.3→passive, 0.3-0.6→transitional, >0.6→active
当 coach_override 不为 null 时，直接使用教练标注值。
"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from core.models import (
    JourneyState, AgencyScoreLog, BehavioralProfile, User,
)

# ── Signal weights (V4.0 spec) ──────────────────────────
AGENCY_SIGNALS = {
    "proactive_initiation_rate": 0.25,
    "self_modification_rate": 0.20,
    "agency_word_frequency": 0.20,
    "awareness_depth": 0.15,
    "coach_dependency": 0.10,   # inverse: high dependency → low agency
    "coach_annotation": 0.10,
}

# ── Score → mode mapping ────────────────────────────────
def score_to_mode(score: float) -> str:
    if score < 0.3:
        return "passive"
    elif score <= 0.6:
        return "transitional"
    else:
        return "active"

# ── Interaction style per mode ───────────────────────────
AGENCY_INTERACTION_STYLE = {
    "passive": {
        "label": "照料者",
        "description": "我来帮你",
        "tone": "warm_supportive",
        "initiative_level": "high",
    },
    "transitional": {
        "label": "同行者",
        "description": "我们一起探索",
        "tone": "collaborative",
        "initiative_level": "medium",
    },
    "active": {
        "label": "镜子/临在者",
        "description": "你来，我在",
        "tone": "reflective",
        "initiative_level": "low",
    },
}


class AgencyService:
    """Compute and persist agency_mode for a user."""

    def __init__(self, db: Session):
        self.db = db

    def compute_agency_score(
        self,
        user_id: int,
        signals: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """
        Compute agency_score from six signals.

        Parameters
        ----------
        user_id : int
        signals : dict
            Keys matching AGENCY_SIGNALS. Missing keys default to 0.0.
            Values should be 0.0-1.0 normalized.

        Returns
        -------
        dict with score, mode, signals, interaction_style
        """
        if signals is None:
            signals = {}

        weighted_sum = 0.0
        signal_details = {}
        for signal_name, weight in AGENCY_SIGNALS.items():
            raw = signals.get(signal_name, 0.0)
            # coach_dependency is inverse: high dependency → low agency
            value = (1.0 - raw) if signal_name == "coach_dependency" else raw
            value = max(0.0, min(1.0, value))
            weighted_sum += value * weight
            signal_details[signal_name] = {
                "raw": raw,
                "normalized": round(value, 4),
                "weight": weight,
                "contribution": round(value * weight, 4),
            }

        score = round(max(0.0, min(1.0, weighted_sum)), 4)
        mode = score_to_mode(score)

        return {
            "score": score,
            "mode": mode,
            "signals": signal_details,
            "interaction_style": AGENCY_INTERACTION_STYLE[mode],
        }

    def update_user_agency(
        self,
        user_id: int,
        signals: Dict[str, float],
        source: str = "system",
    ) -> Dict[str, Any]:
        """Compute, persist agency score and update journey_state + user."""
        result = self.compute_agency_score(user_id, signals)
        score = result["score"]
        mode = result["mode"]

        # Check for coach override
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()

        effective_mode = mode
        if journey and journey.coach_override_agency:
            effective_mode = journey.coach_override_agency
            result["mode"] = effective_mode
            result["coach_override"] = True
            result["interaction_style"] = AGENCY_INTERACTION_STYLE[effective_mode]

        # Persist signal logs
        for signal_name, detail in result["signals"].items():
            log = AgencyScoreLog(
                user_id=user_id,
                signal_name=signal_name,
                signal_value=detail["raw"],
                weight=detail["weight"],
                computed_score=score,
                source=source,
                context={"mode": effective_mode},
            )
            self.db.add(log)

        # Update journey_state
        if journey:
            journey.agency_mode = effective_mode
            journey.agency_score = score
            journey.agency_signals = {k: v["normalized"] for k, v in result["signals"].items()}
        else:
            journey = JourneyState(
                user_id=user_id,
                agency_mode=effective_mode,
                agency_score=score,
                agency_signals={k: v["normalized"] for k, v in result["signals"].items()},
            )
            self.db.add(journey)

        # Update user table shortcut fields
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.agency_mode = effective_mode
            user.agency_score = score

        # Update behavioral_profile
        bp = self.db.query(BehavioralProfile).filter(
            BehavioralProfile.user_id == user_id
        ).first()
        if bp:
            bp.agency_mode = effective_mode
            bp.agency_score = score

        self.db.flush()
        return result

    def set_coach_override(
        self,
        user_id: int,
        override_mode: Optional[str],
        coach_id: int,
    ) -> Dict[str, Any]:
        """Coach manually overrides a user's agency_mode."""
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()
        if not journey:
            journey = JourneyState(user_id=user_id)
            self.db.add(journey)
            self.db.flush()

        journey.coach_override_agency = override_mode
        effective_mode = override_mode or journey.agency_mode

        # Sync to user + profile
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.agency_mode = effective_mode

        bp = self.db.query(BehavioralProfile).filter(
            BehavioralProfile.user_id == user_id
        ).first()
        if bp:
            bp.agency_mode = effective_mode

        self.db.flush()
        return {
            "user_id": user_id,
            "effective_mode": effective_mode,
            "coach_override": override_mode,
            "coach_id": coach_id,
        }

    def get_interaction_style(self, user_id: int) -> Dict[str, Any]:
        """Get the current agency-based interaction style for a user."""
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()
        mode = journey.agency_mode if journey else "passive"
        return {
            "agency_mode": mode,
            "agency_score": journey.agency_score if journey else 0.0,
            **AGENCY_INTERACTION_STYLE.get(mode, AGENCY_INTERACTION_STYLE["passive"]),
        }

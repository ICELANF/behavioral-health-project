"""
V4.0 Agency 6-Signal Calculation Engine — 六信号计算引擎

Formula (Table 3):
  agency_score = S1×0.25 + S2×0.20 + S3×0.20 + S4×0.15 + S5×0.10 + S6×0.10

Signals:
  S1 主动发起率 (Initiation Rate)       — conversation_analytics
  S2 自主修改率 (Self-Modification Rate) — micro_action_audit
  S3 主动表达词频 (Active Expression)    — nlp_agency_detector
  S4 觉察深度 (Awareness Depth)          — reflection_scorer
  S5 教练依赖度 (Coach Dependency, inv)  — coach_dependency_analyzer
  S6 教练标注 (Coach Annotation)         — coach_workbench

Mode mapping:
  <0.3  → passive     (照料者)
  0.3-0.6 → transitional (同行者)
  >0.6  → active       (镜子/临在者)
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List

from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from core.models import (
    User, JourneyState, AgencyScoreLog,
)

logger = logging.getLogger(__name__)

# ── Signal Weights (Table 3) ────────────────────
SIGNAL_WEIGHTS = {
    "S1_initiation_rate": 0.25,
    "S2_self_modification": 0.20,
    "S3_active_expression": 0.20,
    "S4_awareness_depth": 0.15,
    "S5_coach_dependency": 0.10,    # inverted: high dependency → low score
    "S6_coach_annotation": 0.10,
}

# Mode thresholds
MODE_THRESHOLDS = {
    "passive": (0.0, 0.3),
    "transitional": (0.3, 0.6),
    "active": (0.6, 1.0),
}

# ── NLP Agency Detection Keywords ───────────────
PASSIVE_KEYWORDS = [
    "必须", "应该", "害怕", "不敢", "不行", "做不到",
    "没办法", "怎么办", "求助", "帮帮我", "教教我",
]
ACTIVE_KEYWORDS = [
    "我想", "我选择", "我发现", "我决定", "我觉得",
    "我打算", "我要", "我尝试", "我体验", "我意识到",
    "我注意到", "我观察到", "我理解", "让我试试",
]

# ── Reflection depth markers ────────────────────
REFLECTION_MARKERS = {
    "surface": ["感觉", "好像", "可能", "似乎"],                     # 0.2
    "pattern": ["我注意到每次", "总是这样", "规律", "模式", "习惯"],   # 0.5
    "insight": ["我意识到", "我理解了", "原来", "本质上", "根源"],     # 0.8
    "identity": ["我是一个", "我的身份", "这就是我", "我选择成为"],    # 1.0
}


class AgencyEngine:
    """六信号主体性计算引擎"""

    def __init__(self, db: Session):
        self.db = db

    # ── Public API ──────────────────────────────

    def compute_agency(
        self,
        user_id: int,
        signals: Dict[str, float] = None,
        coach_override: float = None,
        save: bool = True,
    ) -> dict:
        """
        计算或更新用户的agency_score.
        signals: 外部传入的信号值 (0-1), 缺省则从DB/默认计算
        coach_override: 教练标注值, 不为None时直接覆盖
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "用户不存在"}

        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()

        # Collect signal values
        if signals is None:
            signals = self._collect_signals(user_id)

        # Compute weighted score
        raw_score = 0.0
        signal_details = {}
        for signal_name, weight in SIGNAL_WEIGHTS.items():
            val = signals.get(signal_name, 0.0)
            val = max(0.0, min(1.0, val))  # Clamp to [0,1]
            contribution = val * weight
            raw_score += contribution
            signal_details[signal_name] = {
                "value": round(val, 4),
                "weight": weight,
                "contribution": round(contribution, 4),
            }

        # Coach override
        final_score = raw_score
        override_applied = False
        if coach_override is not None:
            final_score = max(0.0, min(1.0, coach_override))
            override_applied = True

        # Check journey for persistent coach override (stored as mode enum string)
        if not override_applied and journey and journey.coach_override_agency:
            co_mode = str(journey.coach_override_agency)
            mode_score_map = {"passive": 0.15, "transitional": 0.45, "active": 0.75}
            if co_mode in mode_score_map:
                final_score = mode_score_map[co_mode]
                override_applied = True

        final_score = round(final_score, 4)
        mode = self._score_to_mode(final_score)

        # Persist
        if save and journey:
            journey.agency_score = final_score
            journey.agency_mode = mode
            journey.agency_signals = {k: v["value"] for k, v in signal_details.items()}
            self.db.flush()

        # Log
        if save:
            self._log_signals(user_id, signal_details, final_score, mode, override_applied)

        return {
            "user_id": user_id,
            "agency_score": final_score,
            "agency_mode": mode,
            "raw_score": round(raw_score, 4),
            "override_applied": override_applied,
            "signals": signal_details,
        }

    def get_agency_status(self, user_id: int) -> dict:
        """获取用户当前agency状态 (不重新计算)"""
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()
        if not journey:
            return {
                "user_id": user_id,
                "agency_score": 0.0,
                "agency_mode": "passive",
                "signals": {},
            }
        return {
            "user_id": user_id,
            "agency_score": journey.agency_score or 0.0,
            "agency_mode": journey.agency_mode or "passive",
            "signals": journey.agency_signals or {},
            "coach_override": journey.coach_override_agency,
        }

    def set_coach_override(self, user_id: int, override_value: float) -> dict:
        """教练标注 S6: 直接设置agency override.
        DB column coach_override_agency is agency_mode_enum (passive/transitional/active),
        so we store the mode string, and apply the score to agency_score.
        """
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()
        if not journey:
            return {"error": "用户无旅程状态"}

        override_value = max(0.0, min(1.0, override_value))
        mode = self._score_to_mode(override_value)
        journey.coach_override_agency = mode  # enum: passive/transitional/active
        journey.agency_score = override_value
        journey.agency_mode = mode
        self.db.flush()

        return {
            "user_id": user_id,
            "coach_override": override_value,
            "coach_override_mode": mode,
            "agency_mode": mode,
        }

    def clear_coach_override(self, user_id: int) -> dict:
        """清除教练标注, 恢复算法计算"""
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()
        if not journey:
            return {"error": "用户无旅程状态"}
        journey.coach_override_agency = None
        self.db.flush()
        return {"user_id": user_id, "coach_override": None, "message": "已清除教练标注"}

    def analyze_text_agency(self, text: str) -> dict:
        """分析文本中的agency信号 (S3 + S4)"""
        if not text:
            return {"S3_active_expression": 0.0, "S4_awareness_depth": 0.0}

        # S3: Active expression frequency
        s3 = self._compute_s3_from_text(text)

        # S4: Awareness/reflection depth
        s4 = self._compute_s4_from_text(text)

        return {
            "S3_active_expression": round(s3, 4),
            "S4_awareness_depth": round(s4, 4),
        }

    def get_agency_history(self, user_id: int, days: int = 30) -> List[dict]:
        """获取用户agency变化历史"""
        since = datetime.utcnow() - timedelta(days=days)
        logs = self.db.query(AgencyScoreLog).filter(
            AgencyScoreLog.user_id == user_id,
            AgencyScoreLog.created_at >= since,
        ).order_by(AgencyScoreLog.created_at.desc()).limit(100).all()

        return [
            {
                "id": log.id,
                "signal_name": log.signal_name,
                "signal_value": float(log.signal_value) if log.signal_value else 0,
                "weight": float(log.weight) if log.weight else 0,
                "computed_score": float(log.computed_score) if log.computed_score else 0,
                "created_at": str(log.created_at),
            }
            for log in logs
        ]

    # ── Internal signal collection ──────────────

    def _collect_signals(self, user_id: int) -> Dict[str, float]:
        """从数据库收集各信号值 (如果无数据则返回中性值)"""
        signals = {}

        # S1: Initiation rate — ratio of proactive conversations
        signals["S1_initiation_rate"] = self._calc_s1(user_id)

        # S2: Self-modification rate — micro-action modifications
        signals["S2_self_modification"] = self._calc_s2(user_id)

        # S3: Active expression — from recent messages
        signals["S3_active_expression"] = self._calc_s3(user_id)

        # S4: Awareness depth — reflection quality
        signals["S4_awareness_depth"] = self._calc_s4(user_id)

        # S5: Coach dependency (inverted) — lower dependency = higher score
        signals["S5_coach_dependency"] = self._calc_s5(user_id)

        # S6: Coach annotation — from stored override or default
        signals["S6_coach_annotation"] = self._calc_s6(user_id)

        return signals

    def _calc_s1(self, user_id: int) -> float:
        """S1 主动发起率: user-initiated sessions / total sessions"""
        try:
            from core.models import ChatSession
            total = self.db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
            ).count()
            if total == 0:
                return 0.0
            # Heuristic: sessions with >2 messages are likely user-initiated
            proactive = self.db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.message_count > 2,
            ).count()
            return min(proactive / total, 1.0)
        except Exception:
            return 0.0

    def _calc_s2(self, user_id: int) -> float:
        """S2 自主修改率: completed micro-actions vs total assigned"""
        try:
            from core.models import MicroActionTask
            total = self.db.query(MicroActionTask).filter(
                MicroActionTask.user_id == user_id,
            ).count()
            if total == 0:
                return 0.0
            # Completed = user engaged (completed, not skipped/expired)
            completed = self.db.query(MicroActionTask).filter(
                MicroActionTask.user_id == user_id,
                MicroActionTask.status == "completed",
            ).count()
            return min(completed / total, 1.0)
        except Exception:
            return 0.0

    def _calc_s3(self, user_id: int) -> float:
        """S3 主动表达词频: analyze recent user messages"""
        try:
            from core.models import ChatMessage, ChatSession
            # Get user's session IDs
            session_ids = [s[0] for s in self.db.query(ChatSession.id).filter(
                ChatSession.user_id == user_id,
            ).all()]
            if not session_ids:
                return 0.0
            recent_msgs = self.db.query(ChatMessage.content).filter(
                ChatMessage.session_id.in_(session_ids),
                ChatMessage.role == "user",
                ChatMessage.created_at >= datetime.utcnow() - timedelta(days=7),
            ).limit(50).all()
            if not recent_msgs:
                return 0.0
            combined = " ".join(m[0] for m in recent_msgs if m[0])
            return self._compute_s3_from_text(combined)
        except Exception:
            return 0.0

    def _calc_s4(self, user_id: int) -> float:
        """S4 觉察深度: analyze reflection in recent user messages"""
        try:
            from core.models import ChatMessage, ChatSession
            session_ids = [s[0] for s in self.db.query(ChatSession.id).filter(
                ChatSession.user_id == user_id,
            ).all()]
            if not session_ids:
                return 0.0
            recent_msgs = self.db.query(ChatMessage.content).filter(
                ChatMessage.session_id.in_(session_ids),
                ChatMessage.role == "user",
                ChatMessage.created_at >= datetime.utcnow() - timedelta(days=7),
            ).limit(50).all()
            if not recent_msgs:
                return 0.0
            combined = " ".join(m[0] for m in recent_msgs if m[0])
            return self._compute_s4_from_text(combined)
        except Exception:
            return 0.0

    def _calc_s5(self, user_id: int) -> float:
        """S5 教练依赖度 (inverted): high dependency → low score"""
        try:
            from core.models import ChatSession
            total = self.db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.created_at >= datetime.utcnow() - timedelta(days=30),
            ).count()
            if total == 0:
                return 0.5  # Neutral
            # Heuristic: sessions with title containing coach/教练 keywords
            coach_sessions = self.db.query(ChatSession).filter(
                ChatSession.user_id == user_id,
                ChatSession.title.ilike("%coach%"),
                ChatSession.created_at >= datetime.utcnow() - timedelta(days=30),
            ).count()
            dependency = coach_sessions / total if total > 0 else 0
            return max(0.0, 1.0 - dependency)  # Invert
        except Exception:
            return 0.5

    def _calc_s6(self, user_id: int) -> float:
        """S6 教练标注: from journey_states.coach_override_agency (enum: passive/transitional/active)"""
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()
        if journey and journey.coach_override_agency:
            mode_score = {"passive": 0.15, "transitional": 0.45, "active": 0.75}
            return mode_score.get(str(journey.coach_override_agency), 0.5)
        return 0.5  # Neutral default

    def _compute_s3_from_text(self, text: str) -> float:
        """NLP agency detection from text"""
        if not text:
            return 0.0
        text_lower = text.lower()
        passive_count = sum(1 for kw in PASSIVE_KEYWORDS if kw in text_lower)
        active_count = sum(1 for kw in ACTIVE_KEYWORDS if kw in text_lower)
        total = passive_count + active_count
        if total == 0:
            return 0.3  # Neutral
        return min(active_count / total, 1.0)

    def _compute_s4_from_text(self, text: str) -> float:
        """Reflection depth scoring from text"""
        if not text:
            return 0.0
        max_depth = 0.0
        for level, markers in REFLECTION_MARKERS.items():
            for marker in markers:
                if marker in text:
                    if level == "surface":
                        max_depth = max(max_depth, 0.2)
                    elif level == "pattern":
                        max_depth = max(max_depth, 0.5)
                    elif level == "insight":
                        max_depth = max(max_depth, 0.8)
                    elif level == "identity":
                        max_depth = max(max_depth, 1.0)
        return max_depth

    def _score_to_mode(self, score: float) -> str:
        """Map score to agency mode"""
        if score >= 0.6:
            return "active"
        elif score >= 0.3:
            return "transitional"
        return "passive"

    def _log_signals(
        self, user_id: int, signals: dict, final_score: float,
        mode: str, override: bool,
    ):
        """Persist signal log entry"""
        try:
            log = AgencyScoreLog(
                user_id=user_id,
                signal_name="agency_composite",
                signal_value=final_score,
                weight=1.0,
                computed_score=final_score,
            )
            self.db.add(log)
            self.db.flush()
        except Exception as e:
            logger.warning(f"Agency log failed: {e}")


class AgentDualModeAdapter:
    """
    Agent双模交互引擎 (MEU-23)

    Based on agency_mode, adapt Agent interaction style:
      passive      → 照料者 (Caregiver): "我来帮你"
      transitional → 同行者 (Fellow Traveler): "我们一起探索"
      active       → 镜子/临在者 (Mirror): "你来，我在"
    """

    MODE_PROFILES = {
        "passive": {
            "role": "照料者",
            "role_en": "caregiver",
            "tone": "warm_directive",
            "greeting": "我来帮你",
            "system_prompt_prefix": (
                "你是一位温暖的照料者。用户当前处于被动阶段，"
                "需要更多引导和支持。请主动提供具体建议和行动步骤。"
                "语气温和但明确，像一位关怀的长者。"
            ),
            "features": {
                "proactive_suggestions": True,
                "step_by_step_guidance": True,
                "check_in_reminders": True,
                "simplified_choices": True,
            },
        },
        "transitional": {
            "role": "同行者",
            "role_en": "fellow_traveler",
            "tone": "collaborative",
            "greeting": "我们一起探索",
            "system_prompt_prefix": (
                "你是一位同行的伙伴。用户正在过渡阶段，"
                "既需要支持也需要空间自主探索。请用'我们'而非'你应该'，"
                "提供选项而非指令，鼓励用户表达自己的想法。"
            ),
            "features": {
                "proactive_suggestions": False,
                "open_ended_questions": True,
                "reflection_prompts": True,
                "choice_options": True,
            },
        },
        "active": {
            "role": "镜子",
            "role_en": "mirror",
            "tone": "reflective",
            "greeting": "你来，我在",
            "system_prompt_prefix": (
                "你是一面镜子和临在者。用户已经具有高度自主性，"
                "不需要你的指导。你的角色是倾听、反映和陪伴。"
                "只在被直接问到时才提供建议，更多地提出深层反思性问题。"
            ),
            "features": {
                "minimal_intervention": True,
                "deep_reflection_questions": True,
                "pattern_mirroring": True,
                "celebrate_autonomy": True,
            },
        },
    }

    @classmethod
    def get_mode_profile(cls, agency_mode: str) -> dict:
        """获取指定模式的交互配置"""
        return cls.MODE_PROFILES.get(agency_mode, cls.MODE_PROFILES["passive"])

    @classmethod
    def adapt_system_prompt(cls, base_prompt: str, agency_mode: str) -> str:
        """将agency mode注入Agent的system prompt"""
        profile = cls.get_mode_profile(agency_mode)
        prefix = profile["system_prompt_prefix"]
        return f"{prefix}\n\n{base_prompt}"

    @classmethod
    def adapt_response_style(cls, response: str, agency_mode: str) -> dict:
        """为Agent响应附加模式信息"""
        profile = cls.get_mode_profile(agency_mode)
        return {
            "content": response,
            "agency_mode": agency_mode,
            "agent_role": profile["role"],
            "agent_role_en": profile["role_en"],
            "tone": profile["tone"],
            "features": profile["features"],
        }

    @classmethod
    def get_all_profiles(cls) -> dict:
        """获取所有模式配置 (供前端使用)"""
        return {
            mode: {
                "role": p["role"],
                "role_en": p["role_en"],
                "tone": p["tone"],
                "greeting": p["greeting"],
                "features": list(p["features"].keys()),
            }
            for mode, p in cls.MODE_PROFILES.items()
        }

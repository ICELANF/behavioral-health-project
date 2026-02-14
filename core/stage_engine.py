"""
V4.0 S0-S5 Stage Engine — 阶段引擎

成长者S0-S5阶段化执行结构（Sheet ⑪ §3）：
  S0 授权进入: 明确同意, 绑定教练, 初始评估
  S1 觉察与稳定期: 接受温和任务, 反馈频率, 1-2周
  S2 尝试与波动期: 行为开始尝试但不稳定, 2-4周
  S3 形成路径期: 主动调整, 减少干预, 4-8周
  S4 内化期: 行为成为习惯, 90天稳定验证, 8-16周
  S5 转出期: 毕业机制, 16-24周

积分事件：
  授权完成+20, 阶段进入+10, 行为尝试+10/次,
  路径形成+20, 阶段跃迁+30, 90天稳定+50, 毕业+100, 指标好转+20/项
"""
from __future__ import annotations

import logging
from datetime import datetime, date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from core.models import (
    JourneyState, User, JourneyStageV4,
    BehavioralProfile, BehavioralStage,
)

logger = logging.getLogger(__name__)

# ── Journey→Behavioral stage mapping ────────────────────
# s0_authorization   → S0 (pre_contemplation)
# s1_awareness       → S1 (contemplation)
# s2_trial           → S2 (preparation)
# s3_pathway         → S3 (action)
# s4_internalization → S4 (maintenance)
# s5_graduation      → S5 (termination)
JOURNEY_TO_BEHAVIORAL = {
    "s0_authorization": "S0",
    "s1_awareness": "S1",
    "s2_trial": "S2",
    "s3_pathway": "S3",
    "s4_internalization": "S4",
    "s5_graduation": "S5",
}

# ── Stage Configuration ──────────────────────────────────
STAGE_ORDER = [
    "s0_authorization",
    "s1_awareness",
    "s2_trial",
    "s3_pathway",
    "s4_internalization",
    "s5_graduation",
]

STAGE_CONFIG = {
    "s0_authorization": {
        "label": "授权进入",
        "min_days": 1,
        "max_days": 7,
        "point_event": "stage_enter",
        "point_value": 20,
        "advance_criteria": ["consent_signed", "coach_assigned", "initial_assessment"],
        "visible": [],
        "hidden": ["risk_level", "group_ranking", "prediction"],
        "coach_focus": "确认理解, 建立信任",
        "exit_conditions": ["advance_s1", "voluntary_exit"],
    },
    "s1_awareness": {
        "label": "觉察与稳定期",
        "min_days": 7,
        "max_days": 21,
        "point_event": "stage_enter",
        "point_value": 10,
        "advance_criteria": ["feedback_frequency_stable", "initial_disruption_identified"],
        "visible": ["behavior_trend", "stability_change"],
        "hidden": ["risk_level", "group_ranking", "prediction"],
        "coach_focus": "反馈习惯建立, 中断点识别",
        "exit_conditions": ["advance_s2", "adjust_stay"],
    },
    "s2_trial": {
        "label": "尝试与波动期",
        "min_days": 14,
        "max_days": 42,
        "point_event": "behavior_attempt",
        "point_value": 10,
        "advance_criteria": ["behavior_attempts_gte_5", "disruption_pattern_identified"],
        "visible": ["behavior_trend", "stage_language"],
        "hidden": ["risk_level", "group_ranking"],
        "coach_focus": "中断模式分析, 情绪支持, 不批评不加压",
        "exit_conditions": ["advance_s3", "stay_s2"],
    },
    "s3_pathway": {
        "label": "形成路径期",
        "min_days": 28,
        "max_days": 70,
        "point_event": "pathway_formed",
        "point_value": 20,
        "advance_criteria": ["self_initiated_adjustments", "reduced_coach_dependency"],
        "visible": ["stage_language", "behavior_trend"],
        "hidden": ["risk_level", "prediction"],
        "coach_focus": "路径模式记录, 逐步放手",
        "exit_conditions": ["advance_s4", "regress_s2"],
    },
    "s4_internalization": {
        "label": "内化期",
        "min_days": 56,
        "max_days": 168,
        "point_event": "stage_transition",
        "point_value": 30,
        "advance_criteria": ["behavior_stable_90_days", "self_managing_fluctuations"],
        "visible": ["stage_language", "stability_data"],
        "hidden": ["risk_level"],
        "coach_focus": "习惯验证, 波动应对, 转出准备",
        "exit_conditions": ["advance_s5"],
        "stability_required_days": 90,
    },
    "s5_graduation": {
        "label": "转出期(毕业)",
        "min_days": 112,
        "max_days": 240,
        "point_event": "graduation",
        "point_value": 100,
        "advance_criteria": ["graduation_assessment_complete", "follow_up_plan_created"],
        "visible": ["graduation_certificate", "growth_trajectory_review"],
        "hidden": [],
        "coach_focus": "毕业仪式, 后续跟踪计划, 贡献数据入库",
        "exit_conditions": ["graduate", "self_check_mode"],
    },
}

# Stage-specific point events for integration with point system
STAGE_POINT_EVENTS = {
    "authorization_complete": {"type": "growth", "amount": 20, "max_per_day": 1},
    "stage_enter": {"type": "growth", "amount": 10, "max_per_day": 0},
    "behavior_attempt": {"type": "growth", "amount": 10, "max_per_day": 3},
    "pathway_formed": {"type": "growth", "amount": 20, "max_per_day": 0},
    "stage_transition": {"type": "growth", "amount": 30, "max_per_day": 0},
    "stability_90_days": {"type": "growth", "amount": 50, "max_per_day": 0},
    "graduation": {"type": "growth", "amount": 100, "max_per_day": 0},
    "health_indicator_improved": {"type": "growth", "amount": 20, "max_per_day": 0},
}


class StageEngine:
    """S0-S5 阶段引擎"""

    def __init__(self, db: Session):
        self.db = db

    def _ensure_journey(self, user_id: int) -> JourneyState:
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()
        if not journey:
            journey = JourneyState(user_id=user_id)
            self.db.add(journey)
            self.db.flush()
        return journey

    def _sync_behavioral_profile(self, user_id: int, journey_stage: str):
        """同步 JourneyState.journey_stage → BehavioralProfile.current_stage"""
        behavioral_stage_str = JOURNEY_TO_BEHAVIORAL.get(journey_stage)
        if not behavioral_stage_str:
            return
        try:
            profile = self.db.query(BehavioralProfile).filter(
                BehavioralProfile.user_id == user_id
            ).first()
            if not profile:
                logger.warning("Stage sync: user=%s BehavioralProfile not found, skipping", user_id)
                return
            profile.current_stage = BehavioralStage(behavioral_stage_str)
            profile.stage_updated_at = datetime.utcnow()
            logger.info(
                "Stage sync: user=%s journey=%s → profile=%s",
                user_id, journey_stage, behavioral_stage_str,
            )
        except Exception as e:
            logger.warning("Stage sync failed: user=%s %s", user_id, e)

    def get_stage_progress(self, user_id: int) -> dict:
        """获取当前阶段进度详情"""
        journey = self._ensure_journey(user_id)
        stage = journey.journey_stage
        config = STAGE_CONFIG.get(stage, {})
        stage_idx = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else 0

        entered_at = journey.stage_entered_at or journey.created_at
        days_in_stage = (datetime.utcnow() - entered_at).days if entered_at else 0

        progress = {
            "current_stage": stage,
            "stage_label": config.get("label", stage),
            "stage_index": stage_idx,
            "total_stages": len(STAGE_ORDER),
            "days_in_stage": days_in_stage,
            "min_days": config.get("min_days", 0),
            "max_days": config.get("max_days", 0),
            "stage_entered_at": entered_at.isoformat() if entered_at else None,
            "stability_days": journey.stability_days,
            "interruption_count": journey.interruption_count,
            "stage_transition_count": journey.stage_transition_count,
            "visible_data": config.get("visible", []),
            "hidden_data": config.get("hidden", []),
            "coach_focus": config.get("coach_focus", ""),
        }

        # S4 specific: stability tracking
        if stage == "s4_internalization":
            required = config.get("stability_required_days", 90)
            progress["stability_required_days"] = required
            progress["stability_progress_pct"] = min(100, round(
                journey.stability_days / required * 100, 1
            )) if required > 0 else 100
            progress["stability_start_date"] = (
                journey.stability_start_date.isoformat()
                if journey.stability_start_date else None
            )

        # S5 specific: graduation status
        if stage == "s5_graduation":
            progress["graduated_at"] = (
                journey.graduated_at.isoformat()
                if journey.graduated_at else None
            )

        return progress

    def check_advance_eligibility(self, user_id: int) -> dict:
        """检查是否满足阶段推进条件"""
        journey = self._ensure_journey(user_id)
        stage = journey.journey_stage
        config = STAGE_CONFIG.get(stage, {})
        stage_idx = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else 0

        if stage_idx >= len(STAGE_ORDER) - 1:
            return {"eligible": False, "reason": "已在最终阶段(S5毕业)"}

        entered_at = journey.stage_entered_at or journey.created_at
        days_in_stage = (datetime.utcnow() - entered_at).days if entered_at else 0
        min_days = config.get("min_days", 0)

        checks = {
            "min_days_met": days_in_stage >= min_days,
            "days_in_stage": days_in_stage,
            "min_days_required": min_days,
        }

        # S4 specific: 90-day stability check
        if stage == "s4_internalization":
            required = config.get("stability_required_days", 90)
            checks["stability_met"] = journey.stability_days >= required
            checks["stability_days"] = journey.stability_days
            checks["stability_required"] = required

        eligible = checks["min_days_met"]
        if stage == "s4_internalization":
            eligible = eligible and checks.get("stability_met", False)

        next_stage = STAGE_ORDER[stage_idx + 1]
        return {
            "eligible": eligible,
            "current_stage": stage,
            "next_stage": next_stage,
            "checks": checks,
        }

    def advance_stage(
        self, user_id: int, reason: str = "auto",
        triggered_by: str = "system", triggered_by_user_id: int = None,
        force: bool = False,
    ) -> dict:
        """推进到下一阶段"""
        journey = self._ensure_journey(user_id)
        stage = journey.journey_stage
        stage_idx = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else 0

        if stage_idx >= len(STAGE_ORDER) - 1:
            return {"success": False, "error": "已在最终阶段"}

        if not force:
            eligibility = self.check_advance_eligibility(user_id)
            if not eligibility["eligible"]:
                return {"success": False, "error": "未满足推进条件", "checks": eligibility["checks"]}

        old_stage = stage
        new_stage = STAGE_ORDER[stage_idx + 1]

        # Log transition
        self._log_transition(
            user_id, old_stage, new_stage, reason,
            triggered_by, triggered_by_user_id,
        )

        # Update journey state
        journey.journey_stage = new_stage
        journey.stage_entered_at = datetime.utcnow()
        journey.stage_transition_count = (journey.stage_transition_count or 0) + 1

        # Reset stability tracking when entering S4
        if new_stage == "s4_internalization":
            journey.stability_start_date = date.today()
            journey.stability_days = 0

        # Handle graduation
        if new_stage == "s5_graduation":
            journey.graduated_at = datetime.utcnow()

        # Sync to BehavioralProfile.current_stage
        self._sync_behavioral_profile(user_id, new_stage)

        self.db.flush()

        return {
            "success": True,
            "user_id": user_id,
            "from_stage": old_stage,
            "to_stage": new_stage,
            "stage_label": STAGE_CONFIG[new_stage]["label"],
            "point_event": STAGE_CONFIG[new_stage].get("point_event"),
            "point_value": STAGE_CONFIG[new_stage].get("point_value", 0),
        }

    def record_interruption(
        self, user_id: int, reason: str = "behavior_regression",
        regress_to: str = None,
    ) -> dict:
        """记录中断/回退事件"""
        journey = self._ensure_journey(user_id)
        stage = journey.journey_stage
        stage_idx = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else 0

        # Only S2+ can regress
        if stage_idx < 2:
            return {"success": False, "error": "S0/S1 不支持回退"}

        # By default, regress one stage
        if regress_to is None:
            regress_to = STAGE_ORDER[max(1, stage_idx - 1)]

        if regress_to not in STAGE_ORDER:
            return {"success": False, "error": f"无效目标阶段: {regress_to}"}

        old_stage = stage
        journey.interruption_count = (journey.interruption_count or 0) + 1
        journey.last_interruption_at = datetime.utcnow()

        # Log transition
        self._log_transition(
            user_id, old_stage, regress_to,
            f"interruption: {reason}", "system", None,
        )

        journey.journey_stage = regress_to
        journey.stage_entered_at = datetime.utcnow()

        # Reset stability if falling back from S4
        if old_stage == "s4_internalization":
            journey.stability_days = 0
            journey.stability_start_date = None

        # Sync to BehavioralProfile.current_stage
        self._sync_behavioral_profile(user_id, regress_to)

        self.db.flush()

        return {
            "success": True,
            "from_stage": old_stage,
            "to_stage": regress_to,
            "interruption_count": journey.interruption_count,
            "reason": reason,
        }

    def update_stability(self, user_id: int, days_to_add: int = 1) -> dict:
        """更新S4稳定天数（由定时任务每日调用）"""
        journey = self._ensure_journey(user_id)

        if journey.journey_stage != "s4_internalization":
            return {"updated": False, "reason": "不在S4阶段"}

        if not journey.stability_start_date:
            journey.stability_start_date = date.today()

        journey.stability_days = (journey.stability_days or 0) + days_to_add
        self.db.flush()

        required = STAGE_CONFIG["s4_internalization"].get("stability_required_days", 90)
        return {
            "updated": True,
            "stability_days": journey.stability_days,
            "required": required,
            "met": journey.stability_days >= required,
        }

    def graduate_user(self, user_id: int, triggered_by_user_id: int = None) -> dict:
        """触发毕业仪式"""
        journey = self._ensure_journey(user_id)

        if journey.journey_stage not in ("s4_internalization", "s5_graduation"):
            return {"success": False, "error": "须在S4或S5阶段才能毕业"}

        if journey.journey_stage == "s4_internalization":
            # Check 90-day stability
            required = STAGE_CONFIG["s4_internalization"].get("stability_required_days", 90)
            if (journey.stability_days or 0) < required:
                return {
                    "success": False,
                    "error": f"稳定天数不足: {journey.stability_days}/{required}",
                }

            # Advance to S5 first
            self.advance_stage(
                user_id, "stability_complete", "system",
                triggered_by_user_id, force=True,
            )
            journey = self._ensure_journey(user_id)

        journey.graduated_at = datetime.utcnow()
        self.db.flush()

        return {
            "success": True,
            "user_id": user_id,
            "graduated_at": journey.graduated_at.isoformat(),
            "message": "恭喜毕业！你已完成行为健康成长旅程。",
            "point_event": "graduation",
            "point_value": 100,
        }

    def get_stage_transitions(self, user_id: int, limit: int = 20) -> list:
        """获取阶段跃迁历史"""
        from core.models import StageTransitionLogV4
        logs = self.db.query(StageTransitionLogV4).filter(
            StageTransitionLogV4.user_id == user_id
        ).order_by(StageTransitionLogV4.created_at.desc()).limit(limit).all()

        return [
            {
                "id": l.id,
                "from_stage": l.from_stage,
                "to_stage": l.to_stage,
                "reason": l.reason,
                "triggered_by": l.triggered_by,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ]

    def _log_transition(
        self, user_id: int, from_stage: str, to_stage: str,
        reason: str, triggered_by: str, triggered_by_user_id: int = None,
    ):
        """记录阶段跃迁日志 (使用 m019 实际列名)"""
        from core.models import StageTransitionLogV4
        log = StageTransitionLogV4(
            user_id=user_id,
            transition_type="stage",
            from_value=from_stage,
            to_value=to_stage,
            trigger=reason,
            evidence={"triggered_by": triggered_by,
                      "triggered_by_user_id": triggered_by_user_id},
            created_at=datetime.utcnow(),
        )
        self.db.add(log)

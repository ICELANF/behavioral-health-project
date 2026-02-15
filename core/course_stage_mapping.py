"""
V4.0 Course-Agent-Stage Mapping — 课程×Agent×阶段映射 (MEU-35)

TABLE 2: 三见六段五层 → Agent Assignment
  Phase 1 (1-2月): 健康看得见 — JourneyCompanion + 12专科Agent
  Phase 2 (3-4月): 改变看得见 — JourneyCompanion + GrowthReflection + BehaviorCoach
  Phase 3 (5-6月): 成长看得见 — LifeDesigner + GrowthReflection + 全Agent协作
"""
from __future__ import annotations

import logging
from typing import Optional, Dict, List

from sqlalchemy.orm import Session
from core.models import User, JourneyState

logger = logging.getLogger(__name__)


# ── Course Phase Definitions (TABLE 2) ──────────

COURSE_PHASES = {
    "phase1_see_health": {
        "title": "健康看得见",
        "months": "1-2月",
        "segments": ["①看见现状", "②看见模式", "③看见可能"],
        "layer_focus": ["身体层", "行为层"],
        "primary_agent": "journey_companion",
        "auxiliary_agents": [
            "metabolic", "sleep", "emotion", "motivation",
            "nutrition", "exercise", "tcm", "crisis",
            "behavior_rx", "weight", "cardiac_rehab",
        ],
        "behavior_level": "Level 1 觉察链",
        "deliverables": ["五大基线图", "行为链画像", "三条稳定行为链"],
        "stages_covered": ["s0_authorization", "s1_awareness", "s2_trial"],
        "rx_depth": "B (消费级Rx)",
    },
    "phase2_see_change": {
        "title": "改变看得见",
        "months": "3-4月",
        "segments": ["③看见可能(深)", "④看见价值"],
        "layer_focus": ["认知层", "身份层(初)"],
        "primary_agent": "journey_companion",
        "auxiliary_agents": [
            "growth_reflection", "coach_copilot",
            "metabolic", "sleep", "emotion", "nutrition", "exercise",
        ],
        "behavior_level": "Level 2 重构链",
        "deliverables": ["行动处方链", "行为-价值连接", "身份松动记录"],
        "stages_covered": ["s2_trial", "s3_pathway"],
        "rx_depth": "B (消费级Rx)",
    },
    "phase3_see_growth": {
        "title": "成长看得见",
        "months": "5-6月",
        "segments": ["⑤看见力量", "⑥看见未来"],
        "layer_focus": ["身份层", "生命层"],
        "primary_agent": "life_designer",
        "auxiliary_agents": [
            "growth_reflection", "journey_companion",
            "metabolic", "sleep", "emotion", "motivation",
            "nutrition", "exercise", "tcm",
            "behavior_rx", "weight", "cardiac_rehab",
            "coach_copilot",
        ],
        "behavior_level": "Level 3 身份链/脚本链",
        "deliverables": ["身份升级报告", "生命脚本重写", "3年LifeOS"],
        "stages_covered": ["s4_internalization", "s5_graduation"],
        "rx_depth": "C (不接Rx)",
    },
}


class CourseStageMapper:
    """课程×Agent×阶段映射引擎"""

    def __init__(self, db: Session):
        self.db = db

    def get_user_course_phase(self, user_id: int) -> dict:
        """根据用户阶段确定当前课程阶段和Agent分配"""
        journey = self.db.query(JourneyState).filter(
            JourneyState.user_id == user_id
        ).first()

        stage = journey.journey_stage if journey else "s0_authorization"
        agency_mode = journey.agency_mode if journey else "passive"

        # Determine current course phase
        current_phase = None
        for phase_id, phase in COURSE_PHASES.items():
            if stage in phase["stages_covered"]:
                current_phase = phase_id
                break

        if not current_phase:
            current_phase = "phase1_see_health"

        phase_config = COURSE_PHASES[current_phase]

        return {
            "user_id": user_id,
            "journey_stage": stage,
            "agency_mode": agency_mode,
            "current_phase": current_phase,
            "phase_title": phase_config["title"],
            "primary_agent": phase_config["primary_agent"],
            "auxiliary_agents": phase_config["auxiliary_agents"],
            "layer_focus": phase_config["layer_focus"],
            "behavior_level": phase_config["behavior_level"],
            "deliverables": phase_config["deliverables"],
            "rx_depth": phase_config["rx_depth"],
        }

    def get_all_phases(self) -> dict:
        """获取完整课程阶段定义"""
        return COURSE_PHASES

    def get_agent_assignments(self, stage: str) -> dict:
        """根据阶段获取Agent分配"""
        for phase_id, phase in COURSE_PHASES.items():
            if stage in phase["stages_covered"]:
                return {
                    "stage": stage,
                    "phase": phase_id,
                    "primary_agent": phase["primary_agent"],
                    "auxiliary_agents": phase["auxiliary_agents"],
                    "total_agents": 1 + len(phase["auxiliary_agents"]),
                }
        return {
            "stage": stage,
            "phase": "phase1_see_health",
            "primary_agent": "journey_companion",
            "auxiliary_agents": [],
        }

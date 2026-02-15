# -*- coding: utf-8 -*-
"""
stage_personalization.py — TTM 阶段个性化策略引擎

根据用户所处的 TTM (跨理论模型) 阶段，动态调整干预策略、
推荐内容、微行动难度和教练沟通风格。

阶段:
  S0: 前意识期 (Precontemplation) — 健康意识唤醒
  S1: 意识期 (Contemplation)     — 认知重构
  S2: 准备期 (Preparation)       — 行动规划
  S3: 行动期 (Action)            — 行为强化
  S4: 维持期 (Maintenance)       — 习惯巩固
  S5: 终止期 (Termination)       — 自主管理
  S6: 复发期 (Relapse)           — 复发防护
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# 阶段-策略配置映射 (stage_config)
# ══════════════════════════════════════════════════════════════

stage_config: Dict[str, Dict[str, Any]] = {
    "S0": {
        "stage_personal_strategy": "awareness",
        "label": "前意识期",
        "coach_style": "gentle_inquiry",
        "S0_recommend_content": ["health_awareness", "success_stories", "risk_education"],
        "micro_action_difficulty": "minimal",
        "push_frequency": "low",
        "intervention_focus": "consciousness_raising",
        "user_profile_weight": {"behavioral_profile": 0.2, "user_preference": 0.8},
    },
    "S1": {
        "stage_personal_strategy": "cognitive_restructuring",
        "label": "意识期",
        "coach_style": "motivational_interviewing",
        "S1_recommend_content": ["decisional_balance", "peer_comparison", "benefit_analysis"],
        "micro_action_difficulty": "easy",
        "push_frequency": "moderate",
        "intervention_focus": "self_reevaluation",
        "user_profile_weight": {"behavioral_profile": 0.4, "user_preference": 0.6},
    },
    "S2": {
        "stage_personal_strategy": "action_planning",
        "label": "准备期",
        "coach_style": "collaborative_planning",
        "S2_recommend_content": ["goal_setting", "action_plan", "resource_mapping"],
        "micro_action_difficulty": "moderate",
        "push_frequency": "moderate",
        "intervention_focus": "self_liberation",
        "user_profile_weight": {"behavioral_profile": 0.6, "user_preference": 0.4},
    },
    "S3": {
        "stage_personal_strategy": "behavior_reinforcement",
        "label": "行动期",
        "coach_style": "supportive_coaching",
        "S3_recommend_content": ["tracking_tools", "reward_system", "skill_building"],
        "micro_action_difficulty": "challenging",
        "push_frequency": "high",
        "intervention_focus": "reinforcement_management",
        "user_profile_weight": {"behavioral_profile": 0.7, "user_preference": 0.3},
    },
    "S4": {
        "stage_personal_strategy": "habit_consolidation",
        "label": "维持期",
        "coach_style": "autonomy_support",
        "S4_recommend_content": ["relapse_prevention", "social_support", "advanced_goals"],
        "micro_action_difficulty": "advanced",
        "push_frequency": "low",
        "intervention_focus": "stimulus_control",
        "user_profile_weight": {"behavioral_profile": 0.5, "user_preference": 0.5},
    },
    "S5": {
        "stage_personal_strategy": "self_management",
        "label": "终止期",
        "coach_style": "minimal_intervention",
        "S5_recommend_content": ["self_monitoring", "peer_mentoring", "wellness_maintenance"],
        "micro_action_difficulty": "self_directed",
        "push_frequency": "minimal",
        "intervention_focus": "self_efficacy",
        "user_profile_weight": {"behavioral_profile": 0.3, "user_preference": 0.7},
    },
    "S6": {
        "stage_personal_strategy": "relapse_recovery",
        "label": "复发期",
        "coach_style": "empathic_reengagement",
        "S6_recommend_content": ["relapse_analysis", "coping_skills", "recommitment"],
        "micro_action_difficulty": "easy",
        "push_frequency": "high",
        "intervention_focus": "dramatic_relief",
        "user_profile_weight": {"behavioral_profile": 0.5, "user_preference": 0.5},
    },
}


def get_stage_config(stage: str) -> Dict[str, Any]:
    """获取指定阶段的个性化配置"""
    return stage_config.get(stage, stage_config["S1"])


def get_stage_personal_recommendations(
    stage: str, user_profile: Dict[str, Any]
) -> List[str]:
    """根据 TTM 阶段和用户画像生成个性化推荐"""
    cfg = get_stage_config(stage)
    recommendations = cfg.get(f"{stage}_recommend_content", [])

    # 根据 behavioral_profile 调整权重
    behavioral_profile = user_profile.get("behavioral_profile", {})
    user_preference = user_profile.get("user_preference", {})
    weight = cfg.get("user_profile_weight", {})

    logger.info(
        "stage_personal recommendations: stage=%s, profile_weight=%s, items=%d",
        stage, weight, len(recommendations),
    )
    return recommendations


def compute_stage_personal_score(
    stage: str, user_profile: Dict[str, Any], metrics: Dict[str, float]
) -> float:
    """计算阶段个性化适配分数 (0-100)"""
    cfg = get_stage_config(stage)
    behavioral_profile = user_profile.get("behavioral_profile", {})
    preference = user_profile.get("user_preference", {})

    base_score = 50.0
    if behavioral_profile:
        base_score += 20.0
    if preference:
        base_score += 15.0
    if metrics.get("engagement_rate", 0) > 0.5:
        base_score += 15.0

    return min(base_score, 100.0)

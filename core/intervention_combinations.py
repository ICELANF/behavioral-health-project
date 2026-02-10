"""
120 种行为改变有效组合 — 6大类动因 × 4细分 × 5阶段
放置: api/core/intervention_combinations.py
"""
from enum import Enum as PyEnum
from typing import Any


class CombinationCategory(str, PyEnum):
    VALUE_DRIVEN = "value_driven"
    RISK_SURVIVAL = "risk_survival"
    EMOTION_TRIGGERED = "emotion_triggered"
    VISION_FUTURE = "vision_future"
    SOCIAL_INFLUENCE = "social_influence"
    MISSION_MEANING = "mission_meaning"


class ChangeStage5(str, PyEnum):
    UNAWARE = "unaware"
    RESISTANT = "resistant"
    WILLING = "willing"
    ACTIVE = "active"
    MAINTAINING = "maintaining"


# ── 6大类 × 4细分 = 24 种动因 ──

COMBINATION_SUBDIVISIONS: dict[str, list[str]] = {
    "value_driven": [
        "pursuit_life_quality",
        "desire_long_term_benefit",
        "enhance_self_efficacy",
        "mind_body_alignment",
    ],
    "risk_survival": [
        "health_risk",
        "medical_major_event",
        "family_responsibility",
        "work_life_crisis",
    ],
    "emotion_triggered": [
        "intense_anxiety",
        "frustration_shame",
        "physical_fear",
        "failure_reflection",
    ],
    "vision_future": [
        "better_self",
        "clear_future_vision",
        "growth_breakthrough",
        "sense_of_control",
    ],
    "social_influence": [
        "family_support",
        "peer_influence",
        "professional_advice",
        "role_model_inspiration",
    ],
    "mission_meaning": [
        "life_value_reflection",
        "responsibility_for_others",
        "life_direction_awakening",
        "potential_fulfillment",
    ],
}

# ── ChangeStage5 ↔ S/P/L 映射 ──

STAGE5_TO_S: dict[str, list[str]] = {
    "unaware":     ["S0"],
    "resistant":   ["S1", "S2"],
    "willing":     ["S3"],
    "active":      ["S4"],
    "maintaining": ["S5", "S6"],
}

S_TO_STAGE5: dict[str, str] = {
    "S0": "unaware", "S1": "resistant", "S2": "resistant",
    "S3": "willing", "S4": "active", "S5": "maintaining", "S6": "maintaining",
}

# ── 24小类C → 6大类映射 ──

C_TO_COMBINATION_CATEGORY: dict[str, str] = {
    "C1": "value_driven", "C2": "value_driven", "C3": "value_driven", "C4": "value_driven",
    "C5": "risk_survival", "C6": "risk_survival", "C7": "risk_survival", "C8": "risk_survival",
    "C9": "emotion_triggered", "C10": "emotion_triggered", "C11": "emotion_triggered", "C12": "emotion_triggered",
    "C13": "vision_future", "C14": "vision_future", "C15": "vision_future", "C16": "vision_future",
    "C17": "social_influence", "C18": "social_influence", "C19": "social_influence", "C20": "social_influence",
    "C21": "mission_meaning", "C22": "mission_meaning", "C23": "mission_meaning", "C24": "mission_meaning",
}

# ── 5 种教练问句模板 (每阶段通用骨架) ──

QUESTION_TEMPLATES: dict[str, dict[str, str]] = {
    "unaware": {
        "awareness":     "您有没有注意到，最近{domain}方面有什么变化？",
        "motivation":    "如果{domain}能改善，您最期待的变化是什么？",
        "planning":      "如果从最小的一步开始，您觉得什么最容易做到？",
        "execution":     "万一某天做不到，您觉得可以用什么方式补回来？",
        "reinforcement": "试想一下，坚持一周后您会有什么不同的感受？",
    },
    "resistant": {
        "awareness":     "我理解改变不容易。您觉得{domain}方面，什么让您最犹豫？",
        "motivation":    "如果有一种方式能让改变不那么痛苦，您愿意试试吗？",
        "planning":      "我们可以先设定一个'不可能失败'的目标，您觉得怎样？",
        "execution":     "遇到抗拒情绪时，您通常会怎么处理？",
        "reinforcement": "回想过去成功做到的事，是什么帮助了您？",
    },
    "willing": {
        "awareness":     "您已经准备好了。在{domain}方面，您最想先改变什么？",
        "motivation":    "想象三个月后的自己，您希望看到什么变化？",
        "planning":      "让我们一起制定这周的具体计划，您觉得从哪天开始？",
        "execution":     "如果遇到困难，您的Plan B是什么？",
        "reinforcement": "每完成一天，您打算怎么奖励自己？",
    },
    "active": {
        "awareness":     "您在{domain}方面已经有很好的进展。哪些做法最有效？",
        "motivation":    "现在的改变给您生活带来了哪些积极影响？",
        "planning":      "下一步您想挑战什么更高的目标？",
        "execution":     "在不同场景（出差/聚餐/加班）下，您怎么保持？",
        "reinforcement": "这段时间的坚持让您对自己有什么新的认识？",
    },
    "maintaining": {
        "awareness":     "回顾您的{domain}改变旅程，最大的收获是什么？",
        "motivation":    "健康行为已经成为您的一部分。您想把这份经验分享给谁？",
        "planning":      "为了长期维持，您打算建立什么样的'防线'？",
        "execution":     "如果某天出现滑坡，您的快速恢复策略是什么？",
        "reinforcement": "您的改变已经在影响身边的人了吗？",
    },
}

# ── 动因类别 → domain 关键词 ──

CATEGORY_DOMAIN: dict[str, str] = {
    "value_driven":      "健康和生活品质",
    "risk_survival":     "健康风险和安全",
    "emotion_triggered": "情绪和心理状态",
    "vision_future":     "个人成长和未来",
    "social_influence":  "社交关系和支持",
    "mission_meaning":   "人生价值和使命",
}


def generate_coach_questions(
    stage: str,
    cause_category: str,
) -> dict[str, str]:
    """
    根据阶段+动因大类生成5种教练问句
    stage: S0-S6 或 ChangeStage5 值
    cause_category: CombinationCategory 值
    """
    if stage.startswith("S"):
        stage5 = S_TO_STAGE5.get(stage, "unaware")
    else:
        stage5 = stage

    templates = QUESTION_TEMPLATES.get(stage5, QUESTION_TEMPLATES["unaware"])
    domain = CATEGORY_DOMAIN.get(cause_category, "健康行为")

    return {
        k: v.format(domain=domain) for k, v in templates.items()
    }


# ── 完整匹配接口 ──

class EnhancedInterventionMatcher:
    """
    三层协同:
    1. rx_library     → 做什么 (处方内容, 已有)
    2. strategies     → 怎么说 (144条, intervention_strategy_engine)
    3. combinations   → 怎么问 (120组合, 本模块)
    """

    def __init__(self, db=None):
        self.db = db

    def match_full(
        self,
        stage: str,
        cause_scores: dict[str, int],
        bpt_type: str = "mixed",
        spi_score: float = 50.0,
    ) -> dict[str, Any]:
        from baps.spi_calculator import get_prescription_difficulty

        # 1. 难度
        difficulty, intensity, max_tasks = get_prescription_difficulty(spi_score)

        # 2. 顶部动因 → 大类
        top_causes = sorted(cause_scores.items(), key=lambda x: x[1], reverse=True)[:3]
        top_categories = []
        for c, _ in top_causes:
            cat = C_TO_COMBINATION_CATEGORY.get(c)
            if cat and cat not in top_categories:
                top_categories.append(cat)

        # 3. 教练问句
        coach_questions = []
        for cat in top_categories[:2]:
            qs = generate_coach_questions(stage, cat)
            coach_questions.append({
                "category": cat,
                "domain": CATEGORY_DOMAIN.get(cat, ""),
                "questions": qs,
            })

        # 4. 交互模式
        stage5 = S_TO_STAGE5.get(stage, "unaware")
        mode_map = {
            "unaware": "empathy",
            "resistant": "empathy",
            "willing": "motivational",
            "active": "challenge",
            "maintaining": "reinforcement",
        }

        return {
            "stage": stage,
            "stage5": stage5,
            "difficulty": difficulty,
            "intensity_coefficient": intensity,
            "max_daily_tasks": max_tasks,
            "interaction_mode": mode_map.get(stage5, "empathy"),
            "top_causes": [{"code": c, "score": s} for c, s in top_causes],
            "coach_questions": coach_questions,
            "bpt_type": bpt_type,
        }

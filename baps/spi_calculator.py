"""
SPI 计算器 — 完整版 (50题) + 快速版 (5题)
放置: api/baps/spi_calculator.py
"""
from typing import Any

# ── Part2 心理状态题目 (q26-q45, 5层×4题) ──

SPI_PART2_QUESTIONS: dict[str, dict] = {
    "total_resistance": {
        "label": "完全对抗", "level": 1,
        "questions": [
            {"id": "q26", "text": "我感到愤怒，拒绝接受需要改变的事实"},
            {"id": "q27", "text": "我会争辩、否认问题的存在"},
            {"id": "q28", "text": "我认为改变是外界强加给我的"},
            {"id": "q29", "text": "我会采取反向行为来对抗改变要求"},
        ],
    },
    "resistance_reflection": {
        "label": "抗拒与反思", "level": 2,
        "questions": [
            {"id": "q30", "text": "我虽然抗拒，但开始理解改变的必要性"},
            {"id": "q31", "text": "我的内心很矛盾，一部分想改变，一部分不想"},
            {"id": "q32", "text": "我开始思考'是不是有别的方式'"},
            {"id": "q33", "text": "我会问'如果保持现状会有什么风险'"},
        ],
    },
    "selective_acceptance": {
        "label": "妥协与接受", "level": 3,
        "questions": [
            {"id": "q34", "text": "我接受改变是必要的现实"},
            {"id": "q35", "text": "我想要小步尝试，不想一次改变太多"},
            {"id": "q36", "text": "我担心失败或坚持不住"},
            {"id": "q37", "text": "我开始采取一些'象征性改变'的行动"},
        ],
    },
    "adaptive_alignment": {
        "label": "顺应与调整", "level": 4,
        "questions": [
            {"id": "q38", "text": "我主动寻求方法来实现改变"},
            {"id": "q39", "text": "我会自发调整行为来适应新要求"},
            {"id": "q40", "text": "我在不同情境下都能找到可持续的模式"},
            {"id": "q41", "text": "我希望把这个行为融入我的生活方式"},
        ],
    },
    "full_internalization": {
        "label": "全面臣服", "level": 5,
        "questions": [
            {"id": "q42", "text": "新的行为已经成为我自然的一部分"},
            {"id": "q43", "text": "我不需要外部监督就能维持这个习惯"},
            {"id": "q44", "text": "我会自发地推广这个改变给他人"},
            {"id": "q45", "text": "这个改变已经成为我身份的一部分"},
        ],
    },
}

PSY_LEVEL_COEFFICIENTS: dict[int, float] = {
    1: 0.3, 2: 0.5, 3: 0.7, 4: 0.9, 5: 1.0,
}

SPI_DIFFICULTY_MAP: dict[tuple[int, int], tuple[str, float, int]] = {
    (70, 100): ("challenging", 1.0, 5),
    (50, 69):  ("moderate",    0.7, 3),
    (30, 49):  ("easy",        0.4, 2),
    (0,  29):  ("minimal",     0.2, 1),
}


def calculate_spi_full(
    part1_scores: dict[str, int],
    part2_scores: list[int],
    part3_scores: dict[str, int | float],
) -> dict[str, Any]:
    """
    完整版 SPI (50 题).

    Args:
        part1_scores: {"C1": 4, ..., "C25": 3}  25 题, 每题 1-5
        part2_scores: [q26..q45]  20 个整数, 每题 1-5
        part3_scores: {"q46": 8, "q47": 4, "q48": 3, "q49": 7, "q50": 6}
    """
    trigger_total = sum(part1_scores.values())

    level_scores = {
        1: sum(part2_scores[0:4]),
        2: sum(part2_scores[4:8]),
        3: sum(part2_scores[8:12]),
        4: sum(part2_scores[12:16]),
        5: sum(part2_scores[16:20]),
    }
    psychological_level = max(level_scores, key=level_scores.get)
    psy_coefficient = PSY_LEVEL_COEFFICIENTS[psychological_level]

    urgency_score = (
        part3_scores.get("q46", 0)
        + part3_scores.get("q47", 0)
        + part3_scores.get("q48", 0)
    )

    spi_score = (trigger_total / 125) * psy_coefficient * (urgency_score / 30) * 100
    spi_score = round(min(max(spi_score, 0), 100), 1)

    if spi_score >= 70:
        success_level = "high"
    elif spi_score >= 50:
        success_level = "medium"
    elif spi_score >= 30:
        success_level = "low"
    else:
        success_level = "very_low"

    # L 映射
    spi_to_l = {1: "L1", 2: "L2", 3: "L3", 4: "L4", 5: "L5"}

    return {
        "spi_score": spi_score,
        "trigger_total": trigger_total,
        "psychological_level": psychological_level,
        "readiness_level": spi_to_l[psychological_level],
        "psy_coefficient": psy_coefficient,
        "urgency_score": urgency_score,
        "success_level": success_level,
        "level_scores": level_scores,
    }


def calculate_spi_quick(
    trigger_strength: int,
    psychological_level: int,
    capability_resource: int,
    social_support: int,
    urgency: int,
) -> dict[str, Any]:
    """快速版 SPI (5 题, 5 分钟)."""
    level_map = {1: 2, 2: 4, 3: 6, 4: 8, 5: 10}
    level_score = level_map.get(psychological_level, 2)

    spi_score = (
        trigger_strength * 0.25
        + level_score * 0.30
        + capability_resource * 0.20
        + social_support * 0.15
        + urgency * 0.10
    ) * 10
    spi_score = round(min(max(spi_score, 0), 100), 1)

    spi_to_l = {1: "L1", 2: "L2", 3: "L3", 4: "L4", 5: "L5"}
    return {
        "spi_score": spi_score,
        "method": "quick",
        "psychological_level": psychological_level,
        "readiness_level": spi_to_l[psychological_level],
    }


def get_prescription_difficulty(spi_score: float) -> tuple[str, float, int]:
    """SPI → (difficulty, intensity_coefficient, max_daily_tasks)"""
    for (lo, hi), config in SPI_DIFFICULTY_MAP.items():
        if lo <= spi_score <= hi:
            return config
    return ("minimal", 0.2, 1)

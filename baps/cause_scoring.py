"""
改变动因评分引擎 — 24 小类 × 6 大类
放置: api/baps/cause_scoring.py
"""

CATEGORY_CAUSE_MAP: dict[str, list[str]] = {
    "intrinsic":      ["C1", "C2", "C3", "C4"],
    "external_event": ["C5", "C6", "C7", "C8"],
    "emotional":      ["C9", "C10", "C11", "C12"],
    "cognitive":      ["C13", "C14", "C15", "C16"],
    "capability":     ["C17", "C18", "C19", "C20"],
    "social":         ["C21", "C22", "C23", "C24"],
}

CAUSE_CATEGORY_THRESHOLDS = {"strong": 15, "medium": 10}
# social 维度若含 C25, 按 5 题比例调整
SOCIAL_THRESHOLDS_5Q = {"strong": 19, "medium": 13}


def _level(score: int, has_c25: bool = False, is_social: bool = False) -> str:
    t = SOCIAL_THRESHOLDS_5Q if (is_social and has_c25) else CAUSE_CATEGORY_THRESHOLDS
    if score >= t["strong"]:
        return "strong"
    if score >= t["medium"]:
        return "medium"
    return "weak"


def score_change_causes(answers: dict[str, int]) -> dict:
    """
    输入: {"C1": 4, "C2": 3, ..., "C24": 5}  可选 "C25"
    返回: category_scores, category_levels, total, dominant, weak, top
    """
    has_c25 = "C25" in answers
    category_scores: dict[str, int] = {}
    category_levels: dict[str, str] = {}

    for cat, codes in CATEGORY_CAUSE_MAP.items():
        codes_ext = codes + (["C25"] if cat == "social" and has_c25 else [])
        s = sum(answers.get(c, 0) for c in codes_ext)
        category_scores[cat] = s
        category_levels[cat] = _level(s, has_c25, cat == "social")

    total = sum(answers.get(f"C{i}", 0) for i in range(1, 26))
    dominant = [k for k, v in answers.items() if v >= 4 and k.startswith("C")]
    weak = [k for k, v in answers.items() if v <= 2 and k.startswith("C")]
    top_cat = max(category_scores, key=category_scores.get)

    return {
        "category_scores": category_scores,
        "category_levels": category_levels,
        "total_trigger_score": total,
        "dominant_causes": sorted(dominant),
        "weak_causes": sorted(weak),
        "top_category": top_cat,
    }

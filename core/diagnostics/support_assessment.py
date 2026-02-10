"""
支持体系五层次评估 — 27 题
放置: api/core/diagnostics/support_assessment.py
"""

SUPPORT_QUESTIONS: dict[str, dict[str, list[str]]] = {
    "core": {
        "quality": [
            "我的伴侣/最亲密家人理解并支持我的健康改变计划",
            "当我需要帮助时，核心家人会主动协助我",
            "核心家人不会在我面前做出与改变目标相悖的行为",
        ],
        "stability": [
            "我与核心家人的关系稳定且可以依赖",
            "即使发生争执，核心家人对我的支持不会改变",
        ],
    },
    "intimate": {
        "quality": [
            "我的父母/子女/密友知道我在进行健康改变",
            "亲密圈中至少有1人愿意陪我一起改变",
            "亲密圈中没有人在阻碍或嘲笑我的改变",
        ],
        "stability": [
            "我与亲密圈的联系是定期且稳定的",
            "我在需要时能及时联系到亲密圈成员",
        ],
    },
    "daily": {
        "quality": [
            "我的日常社交环境支持健康行为",
            "同事/朋友不会在聚餐时强迫我破坏健康计划",
            "日常圈中有人与我有相似的健康目标",
        ],
        "stability": [
            "我的日常社交关系相对稳定",
            "日常圈中的支持不会因换工作/搬家而完全消失",
        ],
    },
    "professional": {
        "quality": [
            "我有可以咨询的健康专业人士",
            "专业人士给出的建议是个性化且可执行的",
            "我信任我的健康指导者",
        ],
        "stability": [
            "我能定期获得专业指导",
            "专业支持在我需要时可以及时获得",
        ],
    },
    "community": {
        "quality": [
            "我所在的社区/社群有健康活动或资源",
            "我的文化环境鼓励而非阻碍健康行为",
            "我能找到线上或线下的健康互助社群",
        ],
        "stability": [
            "社群支持是长期可持续的",
            "社区健康资源不会因季节/政策变化而中断",
        ],
    },
}

LAYERS_ORDER = ["core", "intimate", "daily", "professional", "community"]


def score_support_system(answers: dict[str, dict[str, list[int]]]) -> dict:
    """
    输入: {
        "core": {"quality": [5,4,3], "stability": [4,5]},
        "intimate": {...}, ...
    }
    每题 1-5 分
    """
    layer_scores: dict[str, dict] = {}
    total = 0.0

    for layer in LAYERS_ORDER:
        data = answers.get(layer, {})
        q_scores = data.get("quality", [])
        s_scores = data.get("stability", [])

        q_avg = sum(q_scores) / len(q_scores) if q_scores else 0
        s_avg = sum(s_scores) / len(s_scores) if s_scores else 0
        combined = (q_avg + s_avg) / 2

        layer_scores[layer] = {
            "quality_avg": round(q_avg, 2),
            "stability_avg": round(s_avg, 2),
            "combined": round(combined, 2),
        }
        total += combined

    total = round(total, 2)

    if total >= 20:
        support_level = "strong"
    elif total >= 12.5:
        support_level = "adequate"
    else:
        support_level = "weak"

    weakest = min(layer_scores, key=lambda k: layer_scores[k]["combined"])
    strongest = max(layer_scores, key=lambda k: layer_scores[k]["combined"])

    build_priorities = [
        l for l in LAYERS_ORDER if layer_scores[l]["combined"] < 2.5
    ]

    return {
        "total_score": total,
        "layer_scores": layer_scores,
        "support_level": support_level,
        "strongest_layer": strongest,
        "weakest_layer": weakest,
        "build_priorities": build_priorities,
    }

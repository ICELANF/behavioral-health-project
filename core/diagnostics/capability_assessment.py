"""
COM-B 能力评估 (18 题) + 自我效能评估 (5 题)
放置: api/core/diagnostics/capability_assessment.py
"""

COMB_QUESTIONS: dict[str, dict[str, list[str]]] = {
    "capability": {
        "physical": [
            "我的身体状况允许我进行中等强度的运动",
            "我具备基本的烹饪能力来准备健康饮食",
            "我能够识别食物标签上的营养成分信息",
        ],
        "psychological": [
            "我能够制定并记住每天的健康行为计划",
            "当面对诱惑时，我能暂停并做出理性选择",
            "我能分辨真实饥饿vs情绪性进食",
        ],
    },
    "opportunity": {
        "physical": [
            "我家附近有适合运动的场所",
            "我的厨房设备足以准备健康饮食",
            "我的生活环境中健康食物比不健康食物更容易获取",
        ],
        "social": [
            "我身边有人在践行健康的生活方式",
            "我的社交活动不会频繁要求大量饮酒或暴饮暴食",
            "我的工作环境允许我保持基本健康行为",
        ],
    },
    "motivation": {
        "automatic": [
            "想到运动或健康饮食时，第一反应是积极的",
            "我已经有一些不需要提醒就能做到的健康行为",
            "健康行为不会让我感到被剥夺或惩罚",
        ],
        "reflective": [
            "我清楚改变健康行为对我的长期意义",
            "我已经为自己制定了具体的健康目标",
            "我相信付出的努力最终会得到回报",
        ],
    },
}


def score_comb(answers: dict[str, dict[str, list[int]]]) -> dict:
    """
    输入: {
        "capability": {"physical": [4,3,5], "psychological": [3,4,4]},
        "opportunity": {...},
        "motivation": {...},
    }
    每题 1-5 分, 总分 18-90
    """
    dim_scores: dict[str, dict[str, float]] = {}
    dim_totals: dict[str, float] = {}
    grand_total = 0.0

    for dim, subs in answers.items():
        dim_scores[dim] = {}
        dim_sum = 0.0
        for sub, scores in subs.items():
            avg = sum(scores) / len(scores) if scores else 0
            dim_scores[dim][sub] = round(avg, 2)
            dim_sum += sum(scores)
        dim_totals[dim] = dim_sum
        grand_total += dim_sum

    bottleneck = min(dim_totals, key=dim_totals.get)

    return {
        "dimension_scores": dim_scores,
        "dimension_totals": dim_totals,
        "bottleneck": bottleneck,
        "total_score": grand_total,
    }


# ── 自我效能 (5 题, 每题 1-10) ──

SELF_EFFICACY_QUESTIONS: list[dict] = [
    {"id": "SE1", "type": "task",        "text": "您相信自己能做到目标行为吗？"},
    {"id": "SE2", "type": "maintenance",  "text": "您相信自己能坚持3个月以上吗？"},
    {"id": "SE3", "type": "recovery",     "text": "如果中断了，您相信自己能重新开始吗？"},
    {"id": "SE4", "type": "situational",  "text": "即使很忙/很累，您相信自己能坚持吗？"},
    {"id": "SE5", "type": "social",       "text": "在聚会/应酬时，您能坚持健康选择吗？"},
]


def score_self_efficacy(answers: dict[str, int]) -> dict:
    """
    输入: {"SE1": 7, "SE2": 5, "SE3": 6, "SE4": 4, "SE5": 5}
    每题 1-10
    """
    vals = [answers.get(q["id"], 0) for q in SELF_EFFICACY_QUESTIONS]
    avg = sum(vals) / len(vals) if vals else 0
    avg = round(avg, 2)

    if avg >= 7:
        level = "strong"
    elif avg >= 4:
        level = "medium"
    else:
        level = "low"

    return {
        "scores": answers,
        "avg_score": avg,
        "level": level,
    }

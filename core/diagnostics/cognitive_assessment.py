"""
认知结构诊断 — HBM 健康信念 + 归因 + 时间视角
放置: api/core/diagnostics/cognitive_assessment.py
"""

HBM_QUESTIONS: dict[str, list[str]] = {
    "susceptibility": [
        "我觉得自己有可能发展成更严重的健康问题",
        "我的家族病史让我对自己的健康感到担忧",
        "按照目前的生活方式，我未来患病的风险在增加",
    ],
    "severity": [
        "如果健康恶化，会严重影响我的生活质量",
        "我了解这类健康问题可能带来的严重后果",
        "健康问题可能影响我照顾家人的能力",
    ],
    "benefits": [
        "改变生活习惯确实能改善我的健康状况",
        "我相信科学的方法可以帮助我变得更健康",
        "采取行动比什么都不做要好得多",
    ],
    "barriers": [  # 反向计分
        "改变生活习惯对我来说太难了",
        "我没有足够的时间和精力来改变",
        "即使改变了，我也很难坚持下去",
    ],
    "cues": [
        "我身边有人因为改变习惯而变得更健康",
        "医生或专业人士建议我需要改变",
        "我每天能看到关于健康的提醒或信息",
    ],
    "self_efficacy": [
        "我有信心做出并坚持健康的改变",
        "即使遇到困难，我也相信自己能找到解决办法",
        "过去我成功改变过一些不好的习惯",
    ],
}

HBM_PRIORITY_ORDER = [
    "self_efficacy", "barriers", "susceptibility",
    "severity", "benefits", "cues",
]

HBM_INTERVENTION_MAP: dict[str, str] = {
    "susceptibility": "风险具象化+个性化数据呈现",
    "severity":       "后果可视化+家庭影响分析",
    "benefits":       "成功案例展示+量化收益",
    "barriers":       "降低门槛+碎片化方案",
    "cues":           "增加行动线索+环境提醒",
    "self_efficacy":  "成功体验+降低难度+渐进目标",
}


def score_hbm(answers: dict[str, list[int]]) -> dict:
    """
    输入: {"susceptibility": [4, 3, 5], ...}  每题 1-5
    barriers 维度反向计分: 5→1, 4→2, 3→3, 2→4, 1→5
    """
    dim_scores: dict[str, int] = {}

    for dim, scores in answers.items():
        if dim == "barriers":
            scores = [6 - s for s in scores]
        dim_scores[dim] = sum(scores)

    total = sum(dim_scores.values())
    weak = [d for d, s in dim_scores.items() if s < 9]  # <60% of 15

    priorities = []
    for d in HBM_PRIORITY_ORDER:
        if d in weak:
            priorities.append({
                "dimension": d,
                "score": dim_scores.get(d, 0),
                "strategy": HBM_INTERVENTION_MAP.get(d, ""),
            })

    return {
        "dimension_scores": dim_scores,
        "total_score": total,
        "weak_dimensions": weak,
        "intervention_priorities": priorities,
    }


# ── 归因评估 ──

ATTRIBUTION_OPTIONS: dict[str, str] = {
    "behavioral":    "自己的行为习惯",
    "genetic":       "遗传基因",
    "environmental": "工作和生活环境",
    "fatalistic":    "年龄增长的自然过程",
}

ATTRIBUTION_INTERVENTION: dict[str, dict] = {
    "behavioral":    {"strategy": "direct_rx",         "message": None},
    "genetic":       {"strategy": "reframe",           "message": "基因上膛，生活方式扣扳机"},
    "environmental": {"strategy": "focus_controllable", "message": "区分可控和不可控，聚焦可控部分"},
    "fatalistic":    {"strategy": "success_cases",     "message": "提供成功案例，增强掌控感"},
}


# ── 时间视角评估 ──

TIME_ORIENTATION_OPTIONS: dict[str, str] = {
    "past":    "过去的疾病、失败的尝试",
    "present": "现在的享受、眼前的舒服",
    "future":  "未来的生活质量、长远的健康",
}

TIME_ORIENTATION_INTERVENTION: dict[str, str] = {
    "past":    "帮助放下过去，聚焦当下和未来",
    "present": "让健康行为本身变得愉悦，设计即时奖励",
    "future":  "强化未来愿景，构建长期激励系统",
}

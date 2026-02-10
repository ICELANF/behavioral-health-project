"""
六级健康能力评估 — 30 题 (每级 5 题)
放置: api/baps/health_competency_assessment.py
"""

HEALTH_COMPETENCY_DISPLAY: dict[str, dict] = {
    "Lv0": {"name": "完全无知者", "desc": "不知道风险、不理解原理"},
    "Lv1": {"name": "问题觉察者", "desc": "意识到问题但不会做"},
    "Lv2": {"name": "方法学习者", "desc": "会按步骤做但不稳定"},
    "Lv3": {"name": "情境适配者", "desc": "能在不同情境中调整"},
    "Lv4": {"name": "自我驱动者", "desc": "健康行为已成习惯"},
    "Lv5": {"name": "使命实践者", "desc": "能影响他人"},
}

COMPETENCY_TO_CONTENT_STAGE: dict[str, str] = {
    "Lv0": "need",
    "Lv1": "awareness",
    "Lv2": "action",
    "Lv3": "regulation",
    "Lv4": "iteration",
    "Lv5": "transformation",
}

COMPETENCY_TO_ROLE_PREREQUISITE: dict[str, str] = {
    "G0": "Lv0", "G1": "Lv1", "G2": "Lv2",
    "G3": "Lv3", "G4": "Lv4", "G5": "Lv5",
}

HEALTH_COMPETENCY_QUESTIONS: dict[str, dict] = {
    "Lv0": {
        "scoring": "reverse",
        "questions": [
            "我不知道自己的体重、腰围、血压、血糖的真实状态",
            "我不了解肥胖、高血糖、慢性病的风险",
            "我不知道吃什么、怎么吃会导致血糖或体重问题",
            "我不知道运动对健康的影响",
            "我从未主动记录或监测过健康数据",
        ],
    },
    "Lv1": {
        "questions": [
            "我知道自己'需要改变'，但不知道具体怎么做",
            "我了解一些风险，但无法判断哪些与我最相关",
            "我知道吃得不健康，但无法控制或不知道替代方案",
            "我知道需要运动，但无法坚持或不知道如何开始",
            "我偶尔记录数据，但无法解释它们",
        ],
    },
    "Lv2": {
        "questions": [
            "我掌握基本控糖/减重方法（如吃饭顺序、控碳）",
            "我能按照指导完成配餐、记录饮食或监测血糖",
            "我能完成步行或简单运动，但不够稳定",
            "我理解部分健康行为原理，但不能灵活应用",
            "需要别人监督或提醒才能行动",
        ],
    },
    "Lv3": {
        "questions": [
            "我在外食、应酬、加班、旅行等情况下能做出较好选择",
            "我能识别情绪、压力对饮食和血糖的影响并调整",
            "我的饮食、运动、睡眠较稳定，偶尔波动可自我纠正",
            "我能用不同方法解决健康执行中的困难",
            "我能解释自己的血糖或体重变化的原因",
        ],
    },
    "Lv4": {
        "questions": [
            "我有稳定的生活结构（饮食、运动、睡眠节律）",
            "我能长期保持健康行为而无需监督",
            "我的血糖/体重/腰围较为稳定，无大的波动",
            "我知道自己的健康方向和价值，并愿意持续投入",
            "健康行为已经融入日常生活方式",
        ],
    },
    "Lv5": {
        "questions": [
            "健康行为对我来说是一种生命价值选择",
            "我会主动向家人、朋友或同事传递健康方法",
            "我能带动他人改善饮食、运动或睡眠",
            "我能分析问题、制定方案，指导他人实践",
            "我愿意把健康行为视为长期使命并持续践行",
        ],
    },
}


def assess_health_competency(answers: dict[str, list[bool]]) -> dict:
    """
    输入: {"Lv0": [True,False,True,False,True], "Lv1": [...], ...}
    """
    THRESHOLD = 3
    level_scores: dict[str, int] = {}

    for level, config in HEALTH_COMPETENCY_QUESTIONS.items():
        raw = answers.get(level, [False] * 5)
        count = sum(1 for a in raw if a)
        if config.get("scoring") == "reverse":
            count = 5 - count
        level_scores[level] = count

    current_level = "Lv0"
    for lv in ["Lv5", "Lv4", "Lv3", "Lv2", "Lv1", "Lv0"]:
        if level_scores[lv] >= THRESHOLD:
            current_level = lv
            break

    return {
        "current_level": current_level,
        "level_name": HEALTH_COMPETENCY_DISPLAY[current_level]["name"],
        "level_scores": level_scores,
        "recommended_content_stage": COMPETENCY_TO_CONTENT_STAGE[current_level],
    }

"""
障碍评估 — 40 题 (10 类 × 4 题) + 处方调整映射
放置: api/baps/obstacle_assessment.py
"""

OBSTACLE_FULL_QUESTIONS: dict[str, list[str]] = {
    "time": [
        "我的工作/生活太忙，没有时间来做出改变",
        "我的日程总是被其他事情占满",
        "我找不到固定的时间来执行新习惯",
        "突发事件经常打乱我的计划",
    ],
    "energy": [
        "我每天结束时已经精疲力竭",
        "我的身体状况让我感觉没有精力去改变",
        "早上起来就感觉很疲惫",
        "工作之余我只想休息，不想做其他事",
    ],
    "knowledge": [
        "我不确定什么样的饮食/运动对我最有效",
        "关于健康的信息太多太杂，无法判断",
        "我不知道如何制定适合自己的健康计划",
        "我缺乏关于身体状况的基本知识",
    ],
    "skill": [
        "我不会烹饪健康的饮食",
        "我不会正确地做运动（担心受伤或姿势不对）",
        "我不会使用健康监测工具",
        "我不懂如何在不同场景下灵活调整健康行为",
    ],
    "environment": [
        "我家附近没有适合运动的场所",
        "我的环境中充满不健康的食物诱惑",
        "我的居住/工作条件不支持健康行为",
        "我所在的文化环境不鼓励健康行为",
    ],
    "social": [
        "周围的人觉得我'太讲究'或'小题大做'",
        "家人/朋友的聚餐习惯让我很难坚持",
        "我身边没有人在进行类似改变可以互相支持",
        "他人对我的健康选择表示不理解或嘲笑",
    ],
    "emotion": [
        "压力大的时候我会用吃东西/刷手机来缓解",
        "我害怕失败，所以干脆不开始",
        "过去失败的经历让我对改变失去了信心",
        "焦虑/抑郁让我无法集中精力去改变",
    ],
    "financial": [
        "健康食材/有机食品对我来说太贵了",
        "健身房/运动课程的费用超出预算",
        "购买健康监测设备经济上有困难",
        "当前经济状况让我无法优先考虑健康投入",
    ],
    "habit": [
        "我的旧习惯根深蒂固很难改",
        "每次下决心改变，过不了几天就回到老样子",
        "我的生活节奏已经固定，很难插入新行为",
        "某些不健康行为已经成瘾",
    ],
    "belief": [
        "我觉得'基因决定一切'，改变也没用",
        "我认为自己不是那种能坚持的人",
        "我觉得年纪大了改变也来不及了",
        "我不相信生活方式改变能真正逆转健康问题",
    ],
}

OBSTACLE_RX_ADJUSTMENT: dict[str, dict] = {
    "time":        {"strategy": "碎片化任务设计",   "max_task_duration": 5},
    "energy":      {"strategy": "低能耗优先",       "priority_rx": ["sleep", "stress"]},
    "knowledge":   {"strategy": "知识补课",         "add_task": "daily_1_tip"},
    "skill":       {"strategy": "技能降级",         "substitute_complex": True},
    "environment": {"strategy": "环境微调",         "tasks": ["remove_trigger", "add_cue"]},
    "social":      {"strategy": "社群缓冲",         "reduce_social_goals": True},
    "emotion":     {"strategy": "情绪优先",         "add_rx": ["emotion_regulation"]},
    "financial":   {"strategy": "零成本方案",       "filter": "free_only"},
    "habit":       {"strategy": "习惯替换",         "method": "gradual_replacement"},
    "belief":      {"strategy": "认知重构",         "tasks": ["success_case", "micro_goal"]},
}


def score_obstacles(answers: dict[str, list[int]]) -> dict:
    """
    输入: {"time": [4,3,5,2], "energy": [3,3,4,2], ...}  每题 1-5
    返回: category_scores, top (>=15), rx_adjustments
    """
    category_scores: dict[str, int] = {}
    for cat, scores in answers.items():
        category_scores[cat] = sum(scores)

    top = sorted(
        [(k, v) for k, v in category_scores.items() if v >= 15],
        key=lambda x: x[1],
        reverse=True,
    )

    rx = {}
    for cat, _ in top:
        if cat in OBSTACLE_RX_ADJUSTMENT:
            rx[cat] = OBSTACLE_RX_ADJUSTMENT[cat]

    return {
        "category_scores": category_scores,
        "top_obstacles": [{"category": k, "score": v} for k, v in top],
        "obstacle_count": len(top),
        "rx_adjustments": rx,
    }

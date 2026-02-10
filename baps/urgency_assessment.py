"""
迫切度评估 + 障碍评估v2 (§23)
放置: api/baps/urgency_assessment.py

两个版本共存:
  - obstacle_assessment.py: 40题/10类 (§26.4, 详细版)
  - 本文件: 25题/6类 (§23.1, 精简版 + 障碍消解策略库)
"""

# ══════════════════════════════════════════════
# 迫切度评估 (SPI Part3, 5题)
# ══════════════════════════════════════════════

URGENCY_QUESTIONS: list[dict] = [
    {"id": "q46", "text": "改变对我的迫切程度",       "min": 1, "max": 10, "weight": 1.0, "in_spi": True},
    {"id": "q47", "text": "不改变的后果严重性",       "min": 1, "max": 5,  "weight": 1.0, "in_spi": True},
    {"id": "q48", "text": "时间压力评估",             "min": 1, "max": 5,  "weight": 1.0, "in_spi": True},
    {"id": "q49", "text": "改变对人生的重要性",       "min": 1, "max": 10, "weight": 0.0, "in_spi": False},
    {"id": "q50", "text": "行动准备度",               "min": 1, "max": 10, "weight": 0.0, "in_spi": False},
]

URGENCY_THRESHOLDS: dict[str, int] = {
    "high":   24,
    "medium": 18,
}


def score_urgency(answers: dict[str, int | float]) -> dict:
    """
    输入: {"q46": 8, "q47": 4, "q48": 3, "q49": 7, "q50": 6}
    SPI公式迫切度 = q46 + q47 + q48 (范围 3-20)
    """
    spi_urgency = sum(
        answers.get(q["id"], 0)
        for q in URGENCY_QUESTIONS
        if q["in_spi"]
    )

    if spi_urgency >= URGENCY_THRESHOLDS["high"]:
        level = "high"
    elif spi_urgency >= URGENCY_THRESHOLDS["medium"]:
        level = "medium"
    else:
        level = "low"

    return {
        "spi_urgency_score": spi_urgency,
        "urgency_level": level,
        "life_importance": answers.get("q49", 0),
        "action_readiness": answers.get("q50", 0),
        "all_answers": answers,
    }


# ══════════════════════════════════════════════
# 障碍评估 v2 — 6类25题 (§23.1)
# ══════════════════════════════════════════════

OBSTACLE_V2_QUESTIONS: dict[str, list[dict]] = {
    "cognitive_psychological": [
        {"id": "OB01", "text": "我不相信自己能够成功改变"},
        {"id": "OB02", "text": "我不清楚具体应该怎么做"},
        {"id": "OB03", "text": "我总是拖延，无法开始行动"},
        {"id": "OB04", "text": "我害怕失败或出丑"},
        {"id": "OB05", "text": "我觉得改变太难、太痛苦"},
    ],
    "emotional_motivation": [
        {"id": "OB06", "text": "我经常情绪低落，缺乏动力"},
        {"id": "OB07", "text": "我容易焦虑或压力过大"},
        {"id": "OB08", "text": "我用不健康行为来应对压力（如暴饮暴食）"},
        {"id": "OB09", "text": "我很快就失去新鲜感和热情"},
    ],
    "environmental_resource": [
        {"id": "OB10", "text": "我没有足够的时间"},
        {"id": "OB11", "text": "我缺乏经济支持"},
        {"id": "OB12", "text": "我的生活环境不利于改变（如没有运动场所）"},
        {"id": "OB13", "text": "获取健康食材或资源不方便"},
    ],
    "social_relational": [
        {"id": "OB14", "text": "家人不支持或反对我的改变"},
        {"id": "OB15", "text": "朋友或同事的不良影响（如聚餐应酬）"},
        {"id": "OB16", "text": "我没有同伴一起努力"},
        {"id": "OB17", "text": "我缺乏专业指导"},
    ],
    "physiological_habit": [
        {"id": "OB18", "text": "我有身体疾病或疼痛限制"},
        {"id": "OB19", "text": "我的旧习惯太根深蒂固"},
        {"id": "OB20", "text": "我对某些不健康行为有成瘾或依赖"},
        {"id": "OB21", "text": "我容易疲劳，精力不足"},
    ],
    "systemic_persistence": [
        {"id": "OB22", "text": "我不知道如何制定可行的计划"},
        {"id": "OB23", "text": "我无法坚持，总是半途而废"},
        {"id": "OB24", "text": "我一遇到挫折就容易放弃"},
        {"id": "OB25", "text": "我缺乏反馈和进度追踪"},
    ],
}


def score_obstacles_v2(answers: dict[str, list[int]]) -> dict:
    """
    输入: {"cognitive_psychological": [3,2,4,1,3], ...}  每题 0-4
    0=不是障碍, 1=轻微, 2=中度, 3=严重, 4=几乎无法克服
    """
    cat_scores: dict[str, int] = {}
    all_items: list[dict] = []

    for cat, qs in OBSTACLE_V2_QUESTIONS.items():
        scores = answers.get(cat, [0] * len(qs))
        cat_scores[cat] = sum(scores)
        for q, s in zip(qs, scores):
            all_items.append({"id": q["id"], "category": cat, "text": q["text"], "score": s})

    total = sum(cat_scores.values())

    severe_items = [it for it in all_items if it["score"] >= 3]
    severe_cats = [c for c, s in cat_scores.items() if s / len(OBSTACLE_V2_QUESTIONS[c]) >= 2.5]

    if total >= 60:
        level = "severe"
    elif total >= 30:
        level = "moderate"
    else:
        level = "mild"

    top3 = sorted(all_items, key=lambda x: x["score"], reverse=True)[:3]

    rx_adj = []
    for cat in severe_cats:
        adj = OBSTACLE_INTERVENTION_MAP.get(cat, {})
        if adj:
            rx_adj.append({"category": cat, **adj})

    return {
        "category_scores": cat_scores,
        "total_score": total,
        "obstacle_level": level,
        "severe_barriers": [it["id"] for it in severe_items],
        "severe_categories": severe_cats,
        "top3_barriers": top3,
        "prescription_adjustments": rx_adj,
    }


# ══════════════════════════════════════════════
# 障碍消解策略库
# ══════════════════════════════════════════════

OBSTACLE_INTERVENTION_MAP: dict[str, dict] = {
    "cognitive_psychological": {
        "rx_adjustment": "降低目标难度, 增加认知教育类微任务",
        "strategies": [
            "自我效能感重建: 成功日记+替代性经验+言语鼓励",
            "目标分解: SMART原则, 从'减肥20斤'→'本周减0.5斤'",
            "完美主义松绑: '进步优于完美', 允许80分",
            "拖延破解: 5分钟启动法+番茄钟",
            "失败恐惧脱敏: 重新定义'失败=数据收集'",
        ],
    },
    "emotional_motivation": {
        "rx_adjustment": "追加情绪调节处方, 触发情绪时的替代行为",
        "strategies": [
            "ABC情绪日记(事件-信念-情绪)",
            "压力应对替代行为清单(散步/冥想/深呼吸)",
            "动力维持: 视觉化进度表+里程碑庆祝",
            "倦怠预防: 变化性训练+休息日设计",
        ],
    },
    "environmental_resource": {
        "rx_adjustment": "碎片化任务设计, 零成本/低成本方案优先",
        "strategies": [
            "时间审计: 记录一周时间分配→碎片时间挖掘",
            "低成本替代: 公园/自重训练/免费App",
            "环境改造: 家庭健康角落+社区资源地图",
            "便利性提升: 周日备餐+一站式方案",
        ],
    },
    "social_relational": {
        "rx_adjustment": "社群匹配, 同伴结对, 减少社交压力目标",
        "strategies": [
            "家庭沟通: 非暴力沟通+家庭会议+共赢方案",
            "社交情境应对: 拒绝话术库+自带健康食物",
            "同伴支持: 线上社群匹配+责任伙伴制",
            "专业对接: 低成本教练+营养师",
        ],
    },
    "physiological_habit": {
        "rx_adjustment": "降低运动强度, 习惯替换而非消除, 渐进式减少旧行为",
        "strategies": [
            "身体限制适配: 医疗评估+适应性运动方案",
            "旧习惯替代: 习惯循环分析(提示-行为-奖励), 替换行为",
            "成瘾处理: 分级戒断+替代满足源",
            "精力管理: 睡眠优化+能量-任务匹配",
        ],
    },
    "systemic_persistence": {
        "rx_adjustment": "增加结构化计划工具, 强化反馈闭环",
        "strategies": [
            "SMART目标规划: 具体化+可测量+现实性",
            "坚持力培养: 习惯追踪器+连续天数可视化+断链应急",
            "韧性建设: 挫折预演+认知重构+快速恢复协议",
            "反馈机制: 周度复盘模板+数据追踪",
        ],
    },
}

"""
每日简报生成 — 从 V0 MasterAgent 提取

原始位置: core/master_agent_v0.py::generate_daily_briefing()
功能: 生成每日推送内容, 包含问候语 + 今日任务 + 教练寄语
"""
from __future__ import annotations
import logging
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ── 阶段化问候模板 ──
GREETINGS = {
    "S0": ["新的一天开始了！今天试着关注一下自己的身体感受吧。"],
    "S1": ["早安！改变不必急于一时，觉察本身就是进步。"],
    "S2": ["今天是思考改变的好日子！你的每一个想法都有价值。"],
    "S3": ["准备好了吗？今天我们一起迈出小小的一步。"],
    "S4": ["又是充满行动力的一天！你已经在正确的路上了。"],
    "S5": ["继续保持！你的坚持正在改变你的生活。"],
    "S6": ["你已经是一个注重健康的人了，今天继续做自己！"],
}

COACH_MESSAGES = {
    "S0": "不用着急，今天只需要观察和感受。",
    "S1": "每一次觉察都是种子，终会发芽。",
    "S2": "想想改变会给你带来什么？答案在你心中。",
    "S3": "小目标，大改变。今天完成一个就够了。",
    "S4": "执行中遇到困难很正常，调整节奏继续前进。",
    "S5": "你的习惯正在塑造更好的你。",
    "S6": "健康已经是你的生活方式了，为自己骄傲！",
}


def generate_daily_briefing(
    user_id: int,
    profile: Optional[Dict[str, Any]] = None,
    plan: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    生成每日简报

    Args:
        user_id: 用户ID
        profile: 用户画像 (包含 current_stage, nickname 等)
        plan:    当前干预计划 (可选, 包含 actions)

    Returns:
        {
            "user_id": int,
            "date": str,
            "greeting": str,
            "tasks": list[dict],
            "coach_message": str,
            "streak_info": dict,
        }
    """
    profile = profile or {}
    plan = plan or {}

    stage = profile.get("current_stage", "S0")
    nickname = profile.get("nickname", "")

    # 问候语
    greetings = GREETINGS.get(stage, GREETINGS["S0"])
    import random
    greeting = random.choice(greetings)
    if nickname:
        greeting = f"{nickname}，{greeting}"

    # 今日任务 (从 plan 提取, 或生成默认)
    tasks = []
    plan_actions = plan.get("actions", [])
    if plan_actions:
        for i, action in enumerate(plan_actions[:3]):
            tasks.append({
                "task": action.get("description", "完成今日任务"),
                "type": action.get("type", "general"),
                "priority": "high" if i == 0 else "normal",
                "difficulty": action.get("difficulty", "easy"),
            })
    else:
        # 默认任务 (基于阶段)
        if stage in ("S0", "S1"):
            tasks = [{"task": "记录今天的一餐", "type": "awareness", "priority": "normal"}]
        elif stage in ("S2", "S3"):
            tasks = [
                {"task": "完成今日打卡", "type": "checkin", "priority": "high"},
                {"task": "回顾昨天的记录", "type": "reflection", "priority": "normal"},
            ]
        else:
            tasks = [
                {"task": "执行今日行为处方", "type": "execution", "priority": "high"},
                {"task": "记录执行感受", "type": "tracking", "priority": "normal"},
            ]

    # 教练寄语
    coach_message = COACH_MESSAGES.get(stage, COACH_MESSAGES["S0"])

    # 连续天数信息
    streak_days = profile.get("streak_days", 0)

    return {
        "user_id": user_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "greeting": greeting,
        "tasks": tasks,
        "coach_message": coach_message,
        "streak_info": {
            "current_streak": streak_days,
            "message": f"已连续{streak_days}天" if streak_days > 0 else "从今天开始",
        },
    }

# -*- coding: utf-8 -*-
"""
学习激励系统 API

双轨激励机制：
- 教练坐标系：积分制（认证晋级）
- 成长者：时长 + 积分 分开积累
  - 学习时长：按观看/阅读时间累计
  - 学习积分：按测试正确率获得
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/learning", tags=["学习激励"])


# ============================================================================
# 配置常量
# ============================================================================

# 六级三积分体系
# growth: 成长积分 (学习时长/完成度)
# contribution: 贡献积分 (分享/辅导/案例)
# influence: 影响力积分 (带教/督导/研究)
COACH_LEVEL_REQUIREMENTS = {
    "L0": {
        "label": "观察员",
        "min_growth": 0, "min_contribution": 0, "min_influence": 0,
        "exam_required": False,
    },
    "L1": {
        "label": "成长者",
        "min_growth": 100, "min_contribution": 0, "min_influence": 0,
        "exam_required": False,
    },
    "L2": {
        "label": "分享者",
        "min_growth": 300, "min_contribution": 50, "min_influence": 0,
        "exam_required": True,
    },
    "L3": {
        "label": "教练",
        "min_growth": 800, "min_contribution": 100, "min_influence": 0,
        "exam_required": True,
    },
    "L4": {
        "label": "促进师",
        "min_growth": 1500, "min_contribution": 500, "min_influence": 200,
        "exam_required": True,
    },
    "L5": {
        "label": "大师",
        "min_growth": 3000, "min_contribution": 1500, "min_influence": 800,
        "exam_required": True,
    },
}

# 成长者时长里程碑奖励
GROWER_TIME_MILESTONES = [
    {"minutes": 60, "reward": "初次探索", "icon": "🌱", "bonus_points": 10},
    {"minutes": 180, "reward": "持续学习", "icon": "📚", "bonus_points": 20},
    {"minutes": 600, "reward": "学习达人", "icon": "🌟", "bonus_points": 50},
    {"minutes": 1200, "reward": "知识探索者", "icon": "🔭", "bonus_points": 100},
    {"minutes": 3000, "reward": "学习大师", "icon": "🏆", "bonus_points": 200},
    {"minutes": 6000, "reward": "终身学习者", "icon": "👑", "bonus_points": 500},
]

# 成长者测试积分配置
GROWER_QUIZ_POINTS = {
    "pass_base": 10,           # 通过测试基础积分
    "perfect_bonus": 5,        # 满分额外奖励
    "per_correct": 2,          # 每答对一题的积分
    "first_try_bonus": 3,      # 首次通过额外奖励
}

# 成长者积分里程碑（测试积分）
GROWER_POINTS_MILESTONES = [
    {"points": 50, "reward": "初试身手", "icon": "✏️"},
    {"points": 100, "reward": "小有所成", "icon": "📖"},
    {"points": 300, "reward": "学有所获", "icon": "🎓"},
    {"points": 500, "reward": "知识渊博", "icon": "📚"},
    {"points": 1000, "reward": "博学多才", "icon": "🏅"},
]

# 连续学习奖励
STREAK_MILESTONES = [
    {"days": 3, "reward": "三日坚持", "icon": "🔥", "points": 5},
    {"days": 7, "reward": "一周达成", "icon": "💪", "points": 15},
    {"days": 14, "reward": "两周突破", "icon": "⭐", "points": 30},
    {"days": 21, "reward": "习惯养成", "icon": "🎯", "points": 50},
    {"days": 30, "reward": "月度冠军", "icon": "🥇", "points": 100},
    {"days": 100, "reward": "百日传奇", "icon": "🏅", "points": 500},
]

# 内容积分配置（按内容类型和分类）
CONTENT_POINTS_CONFIG = {
    "video": {"base_points": 10, "per_minute": 1, "quiz_bonus": 5},
    "course": {"base_points": 50, "per_chapter": 10, "complete_bonus": 20},
    "article": {"base_points": 5, "per_1000_words": 2},
    "card": {"base_points": 3, "complete_bonus": 2},
    "audio": {"base_points": 8, "per_minute": 0.5},
}


# ============================================================================
# Pydantic 模型
# ============================================================================

class LearningEvent(BaseModel):
    """学习事件"""
    user_id: str
    user_type: str  # coach/grower
    content_id: str
    content_type: str  # video/course/article/card/audio
    content_category: Optional[str] = None  # knowledge/method/skill/value/practice/case
    action: str  # start/progress/complete/quiz_pass
    duration_seconds: int = 0
    progress_percent: int = 0
    quiz_score: Optional[int] = None


class PointsRecord(BaseModel):
    """积分记录"""
    record_id: str
    user_id: str
    source_type: str
    source_id: str
    source_title: str
    points: int
    category: Optional[str] = None
    earned_at: datetime


class TimeRecord(BaseModel):
    """时长记录"""
    record_id: str
    user_id: str
    content_type: str
    content_id: str
    content_title: str
    minutes: int
    domain: Optional[str] = None
    earned_at: datetime


class RewardClaim(BaseModel):
    """奖励领取"""
    user_id: str
    reward_type: str  # time_milestone/streak/achievement
    reward_id: str


# ============================================================================
# 教练积分 API
# ============================================================================

@router.get("/coach/points/{user_id}")
async def get_coach_points(user_id: str):
    """获取教练积分详情（三积分体系）"""
    # TODO: 从数据库查询
    growth_points = 245
    contribution_points = 35
    influence_points = 0
    current_level = "L1"

    # 查找下一级
    level_keys = list(COACH_LEVEL_REQUIREMENTS.keys())
    current_idx = level_keys.index(current_level) if current_level in level_keys else 0
    next_level = level_keys[current_idx + 1] if current_idx + 1 < len(level_keys) else None
    next_level_req = COACH_LEVEL_REQUIREMENTS[next_level] if next_level else None

    # 计算进度
    level_progress = 100
    if next_level_req:
        g_prog = min(growth_points / max(next_level_req["min_growth"], 1), 1.0)
        c_prog = min(contribution_points / max(next_level_req["min_contribution"], 1), 1.0) if next_level_req["min_contribution"] > 0 else 1.0
        i_prog = min(influence_points / max(next_level_req["min_influence"], 1), 1.0) if next_level_req["min_influence"] > 0 else 1.0
        level_progress = int((g_prog + c_prog + i_prog) / 3 * 100)

    return {
        "user_id": user_id,
        "current_level": current_level,
        "current_level_label": COACH_LEVEL_REQUIREMENTS[current_level]["label"],
        "next_level": next_level,
        "next_level_label": next_level_req["label"] if next_level_req else "已达最高等级",
        "level_progress": level_progress,
        "scores": {
            "growth": growth_points,
            "contribution": contribution_points,
            "influence": influence_points,
        },
        "next_level_requirements": {
            "min_growth": next_level_req["min_growth"],
            "min_contribution": next_level_req["min_contribution"],
            "min_influence": next_level_req["min_influence"],
        } if next_level_req else None,
        "certification_status": {
            "growth_met": growth_points >= (next_level_req["min_growth"] if next_level_req else 0),
            "contribution_met": contribution_points >= (next_level_req["min_contribution"] if next_level_req else 0),
            "influence_met": influence_points >= (next_level_req["min_influence"] if next_level_req else 0),
            "exam_passed": False,
            "mentor_approved": False,
        }
    }


@router.get("/coach/points/{user_id}/history")
async def get_coach_points_history(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None
):
    """获取教练积分历史"""
    # TODO: 从数据库查询
    return {
        "items": [
            {
                "record_id": "pr1",
                "source_type": "video",
                "source_id": "v1",
                "source_title": "正念呼吸入门",
                "points": 15,
                "category": "knowledge",
                "earned_at": "2026-02-04T15:30:00"
            },
            {
                "record_id": "pr2",
                "source_type": "quiz",
                "source_id": "quiz_v1",
                "source_title": "正念呼吸知识测试",
                "points": 5,
                "category": "knowledge",
                "earned_at": "2026-02-04T15:45:00"
            }
        ],
        "total": 2,
        "page": page,
        "page_size": page_size
    }


@router.post("/coach/points/add")
async def add_coach_points(event: LearningEvent):
    """添加教练积分（内部调用）"""
    if event.user_type != "coach":
        raise HTTPException(status_code=400, detail="仅限教练用户")

    # 计算积分
    config = CONTENT_POINTS_CONFIG.get(event.content_type, {})
    points = config.get("base_points", 5)

    # 完成加成
    if event.action == "complete":
        points += config.get("complete_bonus", 0)

    # 测试加成
    if event.action == "quiz_pass" and event.quiz_score:
        points += config.get("quiz_bonus", 0)
        if event.quiz_score == 100:
            points += 5  # 满分额外加成

    # TODO: 保存到数据库

    return {
        "success": True,
        "points_earned": points,
        "category": event.content_category,
        "new_total": 250  # 模拟
    }


# ============================================================================
# 成长者时长 API
# ============================================================================

@router.get("/grower/stats/{user_id}")
async def get_grower_stats(user_id: str):
    """获取成长者学习统计（时长+积分分开）"""
    # TODO: 从数据库查询
    total_minutes = 1850
    total_points = 285  # 测试积分

    # 计算下一个时长里程碑
    next_time_milestone = None
    for milestone in GROWER_TIME_MILESTONES:
        if milestone["minutes"] > total_minutes:
            next_time_milestone = milestone
            break

    # 计算下一个积分里程碑
    next_points_milestone = None
    for milestone in GROWER_POINTS_MILESTONES:
        if milestone["points"] > total_points:
            next_points_milestone = milestone
            break

    # 计算已获得奖励
    time_rewards_earned = sum(1 for m in GROWER_TIME_MILESTONES if m["minutes"] <= total_minutes)
    points_rewards_earned = sum(1 for m in GROWER_POINTS_MILESTONES if m["points"] <= total_points)

    return {
        "user_id": user_id,

        # ====== 学习时长 ======
        "learning_time": {
            "total_minutes": total_minutes,
            "total_hours": round(total_minutes / 60, 1),
            "today_minutes": 25,
            "week_minutes": 180,
            "month_minutes": 720,
            "next_milestone": next_time_milestone,
            "milestone_progress": int((total_minutes / next_time_milestone["minutes"]) * 100) if next_time_milestone else 100,
            "rewards_earned": time_rewards_earned,
            "domain_distribution": {
                "emotion": {"minutes": 450, "percent": 24},
                "sleep": {"minutes": 380, "percent": 21},
                "mindfulness": {"minutes": 520, "percent": 28},
                "stress": {"minutes": 300, "percent": 16},
                "growth": {"minutes": 200, "percent": 11}
            }
        },

        # ====== 学习积分（测试） ======
        "learning_points": {
            "total_points": total_points,
            "today_points": 15,
            "week_points": 65,
            "month_points": 180,
            "quiz_stats": {
                "total_quizzes": 28,
                "passed_quizzes": 25,
                "perfect_quizzes": 12,
                "pass_rate": 89.3
            },
            "next_milestone": next_points_milestone,
            "milestone_progress": int((total_points / next_points_milestone["points"]) * 100) if next_points_milestone else 100,
            "rewards_earned": points_rewards_earned
        },

        # ====== 连续学习 ======
        "streak": {
            "current_streak": 7,
            "longest_streak": 14,
            "today_learned": True
        }
    }


@router.get("/grower/time/{user_id}")
async def get_grower_time(user_id: str):
    """获取成长者学习时长（单独）"""
    # TODO: 从数据库查询
    total_minutes = 1850

    # 计算下一个里程碑
    next_milestone = None
    for milestone in GROWER_TIME_MILESTONES:
        if milestone["minutes"] > total_minutes:
            next_milestone = milestone
            break

    # 计算奖励进度
    rewards_earned = sum(1 for m in GROWER_TIME_MILESTONES if m["minutes"] <= total_minutes)

    return {
        "user_id": user_id,
        "total_minutes": total_minutes,
        "total_hours": round(total_minutes / 60, 1),
        "today_minutes": 25,
        "week_minutes": 180,
        "month_minutes": 720,
        "rewards_earned": rewards_earned,
        "next_milestone": next_milestone,
        "milestone_progress": int((total_minutes / next_milestone["minutes"]) * 100) if next_milestone else 100,
        "domain_distribution": {
            "emotion": {"minutes": 450, "percent": 24},
            "sleep": {"minutes": 380, "percent": 21},
            "mindfulness": {"minutes": 520, "percent": 28},
            "stress": {"minutes": 300, "percent": 16},
            "growth": {"minutes": 200, "percent": 11}
        }
    }


@router.get("/grower/points/{user_id}")
async def get_grower_points(user_id: str):
    """获取成长者学习积分（测试积分，单独）"""
    # TODO: 从数据库查询
    total_points = 285

    # 计算下一个里程碑
    next_milestone = None
    for milestone in GROWER_POINTS_MILESTONES:
        if milestone["points"] > total_points:
            next_milestone = milestone
            break

    rewards_earned = sum(1 for m in GROWER_POINTS_MILESTONES if m["points"] <= total_points)

    return {
        "user_id": user_id,
        "total_points": total_points,
        "today_points": 15,
        "week_points": 65,
        "month_points": 180,
        "quiz_stats": {
            "total_quizzes": 28,
            "passed_quizzes": 25,
            "perfect_quizzes": 12,
            "pass_rate": 89.3,
            "avg_score": 82.5
        },
        "rewards_earned": rewards_earned,
        "next_milestone": next_milestone,
        "milestone_progress": int((total_points / next_milestone["points"]) * 100) if next_milestone else 100
    }


@router.post("/grower/points/add")
async def add_grower_quiz_points(
    user_id: str,
    quiz_id: str,
    score: int,
    correct_count: int,
    total_count: int,
    is_first_try: bool = True
):
    """添加成长者测试积分"""
    passed = score >= 60
    is_perfect = score == 100

    points_earned = 0
    if passed:
        points_earned += GROWER_QUIZ_POINTS["pass_base"]
        points_earned += correct_count * GROWER_QUIZ_POINTS["per_correct"]
        if is_perfect:
            points_earned += GROWER_QUIZ_POINTS["perfect_bonus"]
        if is_first_try:
            points_earned += GROWER_QUIZ_POINTS["first_try_bonus"]

    # TODO: 保存到数据库，检查是否触发里程碑
    current_total = 285
    new_total = current_total + points_earned

    new_milestones = []
    for milestone in GROWER_POINTS_MILESTONES:
        if current_total < milestone["points"] <= new_total:
            new_milestones.append(milestone)

    return {
        "success": True,
        "points_earned": points_earned,
        "breakdown": {
            "pass_base": GROWER_QUIZ_POINTS["pass_base"] if passed else 0,
            "correct_bonus": correct_count * GROWER_QUIZ_POINTS["per_correct"] if passed else 0,
            "perfect_bonus": GROWER_QUIZ_POINTS["perfect_bonus"] if is_perfect else 0,
            "first_try_bonus": GROWER_QUIZ_POINTS["first_try_bonus"] if passed and is_first_try else 0
        },
        "new_total": new_total,
        "new_milestones": new_milestones
    }


@router.get("/grower/time/{user_id}/history")
async def get_grower_time_history(
    user_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    domain: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """获取成长者学习时长历史"""
    # TODO: 从数据库查询
    return {
        "items": [
            {
                "record_id": "tr1",
                "content_type": "video",
                "content_id": "v1",
                "content_title": "3分钟呼吸放松",
                "minutes": 5,
                "domain": "stress",
                "earned_at": "2026-02-04T15:30:00"
            },
            {
                "record_id": "tr2",
                "content_type": "course",
                "content_id": "c1",
                "content_title": "正念冥想入门",
                "minutes": 20,
                "domain": "mindfulness",
                "earned_at": "2026-02-04T14:00:00"
            }
        ],
        "total": 2,
        "page": page,
        "page_size": page_size,
        "summary": {
            "total_minutes": 25,
            "domains": {"stress": 5, "mindfulness": 20}
        }
    }


@router.post("/grower/time/add")
async def add_grower_time(event: LearningEvent):
    """添加成长者学习时长（内部调用）"""
    if event.user_type != "grower":
        raise HTTPException(status_code=400, detail="仅限成长者用户")

    minutes = event.duration_seconds // 60

    # 检查是否触发里程碑
    # TODO: 从数据库获取当前总时长
    current_total = 1850
    new_total = current_total + minutes

    new_milestones = []
    for milestone in GROWER_TIME_MILESTONES:
        if current_total < milestone["minutes"] <= new_total:
            new_milestones.append(milestone)

    # TODO: 保存到数据库

    return {
        "success": True,
        "minutes_earned": minutes,
        "new_total": new_total,
        "new_milestones": new_milestones
    }


@router.get("/grower/streak/{user_id}")
async def get_grower_streak(user_id: str):
    """获取成长者连续学习记录"""
    # TODO: 从数据库查询
    current_streak = 7
    longest_streak = 14

    # 检查今日是否已学习
    today_learned = True

    # 计算下一个连续奖励
    next_streak_reward = None
    for milestone in STREAK_MILESTONES:
        if milestone["days"] > current_streak:
            next_streak_reward = milestone
            break

    # 已获得的连续奖励
    earned_streaks = [m for m in STREAK_MILESTONES if m["days"] <= longest_streak]

    return {
        "user_id": user_id,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "today_learned": today_learned,
        "next_reward": next_streak_reward,
        "days_to_next": next_streak_reward["days"] - current_streak if next_streak_reward else 0,
        "earned_rewards": earned_streaks
    }


# ============================================================================
# 奖励系统 API
# ============================================================================

@router.get("/rewards/{user_id}")
async def get_user_rewards(user_id: str, user_type: str = "grower"):
    """获取用户奖励列表"""
    # TODO: 从数据库查询
    if user_type == "grower":
        return {
            "user_id": user_id,
            "user_type": "grower",
            "time_rewards": [
                {"milestone": m, "earned": m["minutes"] <= 1850, "earned_at": "2026-01-15" if m["minutes"] <= 1850 else None}
                for m in GROWER_TIME_MILESTONES
            ],
            "streak_rewards": [
                {"milestone": m, "earned": m["days"] <= 14, "earned_at": "2026-01-20" if m["days"] <= 14 else None}
                for m in STREAK_MILESTONES
            ],
            "total_reward_points": 125,
            "unclaimed_rewards": 0
        }
    else:
        # 教练的奖励主要是认证晋级
        return {
            "user_id": user_id,
            "user_type": "coach",
            "level_certifications": [
                {"level": "L0", "earned": True, "earned_at": "2025-06-01"},
                {"level": "L1", "earned": True, "earned_at": "2025-12-15"},
                {"level": "L2", "earned": False, "progress": 65}
            ],
            "achievement_badges": [
                {"id": "first_course", "name": "首课完成", "icon": "🎓", "earned_at": "2025-06-05"},
                {"id": "quiz_master", "name": "测试达人", "icon": "📝", "earned_at": "2025-09-10"}
            ]
        }


@router.post("/rewards/claim")
async def claim_reward(claim: RewardClaim):
    """领取奖励"""
    # TODO: 验证奖励是否可领取，更新数据库
    return {
        "success": True,
        "reward_type": claim.reward_type,
        "reward_id": claim.reward_id,
        "message": "奖励已领取"
    }


# ============================================================================
# 排行榜 API
# ============================================================================

@router.get("/leaderboard/coaches")
async def get_coach_leaderboard(
    period: str = Query("week", regex="^(week|month|all)$"),
    limit: int = Query(20, ge=1, le=100)
):
    """教练积分排行榜"""
    # TODO: 从数据库查询
    return {
        "period": period,
        "items": [
            {"rank": 1, "user_id": "coach1", "name": "张教练", "points": 580, "level": "L2"},
            {"rank": 2, "user_id": "coach2", "name": "李教练", "points": 520, "level": "L2"},
            {"rank": 3, "user_id": "coach3", "name": "王教练", "points": 485, "level": "L1"},
        ],
        "my_rank": 15,
        "my_points": 245
    }


@router.get("/leaderboard/growers")
async def get_grower_leaderboard(
    period: str = Query("week", regex="^(week|month|all)$"),
    limit: int = Query(20, ge=1, le=100)
):
    """成长者学习时长排行榜"""
    # TODO: 从数据库查询
    return {
        "period": period,
        "items": [
            {"rank": 1, "user_id": "user1", "name": "学习达人", "minutes": 320, "streak": 21},
            {"rank": 2, "user_id": "user2", "name": "成长ing", "minutes": 280, "streak": 14},
            {"rank": 3, "user_id": "user3", "name": "早起鸟", "minutes": 250, "streak": 7},
        ],
        "my_rank": 28,
        "my_minutes": 180
    }


# ============================================================================
# 统一事件处理
# ============================================================================

@router.post("/event")
async def handle_learning_event(event: LearningEvent):
    """处理学习事件（统一入口）"""
    if event.user_type == "coach":
        # 教练：计算积分
        result = await add_coach_points(event)
        return {
            "user_type": "coach",
            "points_earned": result.get("points_earned", 0),
            "new_total_points": result.get("new_total", 0)
        }
    else:
        # 成长者：计算时长
        result = await add_grower_time(event)
        return {
            "user_type": "grower",
            "minutes_earned": result.get("minutes_earned", 0),
            "new_total_minutes": result.get("new_total", 0),
            "new_milestones": result.get("new_milestones", [])
        }

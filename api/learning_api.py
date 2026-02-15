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
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.database import get_db
from core.models import (
    User, UserLearningStats, LearningTimeLog, LearningPointsLog,
    ExamResult, UserActivityLog
)
from api.dependencies import get_current_user
from core.access_control import check_user_data_access
from core.learning_service import (
    get_or_create_stats, record_learning_time, record_learning_points,
    record_quiz_result
)

router = APIRouter(prefix="/api/v1/learning", tags=["学习激励"])


# ============================================================================
# 配置常量
# ============================================================================

# 六级三积分体系（与 paths_api.py 六级四同道者体系对齐）
# growth: 成长积分 (学习时长/完成度)
# contribution: 贡献积分 (分享/辅导/案例)
# influence: 影响力积分 (带教/督导/研究)
#
# 阈值来源: paths_api.py GET /coach-levels/levels 中每级 advancement.points_required
# L(N)的 min_* 值 = L(N-1) 的 advancement.points_required
COACH_LEVEL_REQUIREMENTS = {
    "L0": {
        "label": "观察员",
        "min_growth": 0, "min_contribution": 0, "min_influence": 0,
        "exam_required": False,
        "companions_required": 0,
    },
    "L1": {
        "label": "成长者",
        "min_growth": 100, "min_contribution": 0, "min_influence": 0,
        "exam_required": False,
        "companions_required": 0,
    },
    "L2": {
        "label": "分享者",
        "min_growth": 500, "min_contribution": 50, "min_influence": 0,
        "exam_required": False,
        "companions_required": 0,
    },
    "L3": {
        "label": "教练",
        "min_growth": 800, "min_contribution": 200, "min_influence": 50,
        "exam_required": True,
        "companions_required": 4, "companion_target": "L1",
    },
    "L4": {
        "label": "促进师",
        "min_growth": 1500, "min_contribution": 600, "min_influence": 200,
        "exam_required": True,
        "companions_required": 4, "companion_target": "L2",
    },
    "L5": {
        "label": "大师",
        "min_growth": 3000, "min_contribution": 1500, "min_influence": 600,
        "exam_required": True,
        "companions_required": 4, "companion_target": "L3",
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


class GrowerTimeAddRequest(BaseModel):
    """成长者学习时长记录 (轻量版, 前端直接调用)"""
    minutes: int = Field(ge=1, description="学习分钟数")
    content_id: Optional[str] = None
    content_type: Optional[str] = None  # video/course/article
    domain: Optional[str] = None  # 学习领域


class GrowerQuizPointsRequest(BaseModel):
    """成长者测试积分 (轻量版)"""
    user_id: Optional[int] = None  # 可选, 默认当前用户
    quiz_id: str
    score: int = Field(ge=0, le=100)
    correct_count: int = Field(ge=0)
    total_count: int = Field(ge=1)
    is_first_try: bool = True


# ============================================================================
# 教练积分 API
# ============================================================================

@router.get("/coach/points/{user_id}")
def get_coach_points(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教练积分详情（三积分体系）"""
    # 越权校验
    # FIX-09: 细粒度访问控制 (教练仅限自己学员)
    check_user_data_access(current_user, user_id, db)
    stats = get_or_create_stats(db, user_id)
    growth_points = stats.growth_points
    contribution_points = stats.contribution_points
    influence_points = stats.influence_points

    # 根据积分确定当前等级
    current_level = "L0"
    for lvl_key in reversed(list(COACH_LEVEL_REQUIREMENTS.keys())):
        req = COACH_LEVEL_REQUIREMENTS[lvl_key]
        if (growth_points >= req["min_growth"] and
            contribution_points >= req["min_contribution"] and
            influence_points >= req["min_influence"]):
            current_level = lvl_key
            break

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
def get_coach_points_history(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取教练积分历史"""
    # 越权校验
    # FIX-09: 细粒度访问控制 (教练仅限自己学员)
    check_user_data_access(current_user, user_id, db)
    query = db.query(LearningPointsLog).filter(LearningPointsLog.user_id == user_id)
    if category:
        query = query.filter(LearningPointsLog.category == category)

    total = query.count()
    items = query.order_by(LearningPointsLog.earned_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    return {
        "items": [
            {
                "record_id": str(item.id),
                "source_type": item.source_type,
                "source_id": item.source_id or "",
                "source_title": item.source_type,
                "points": item.points,
                "category": item.category,
                "earned_at": item.earned_at.isoformat() if item.earned_at else None,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("/coach/points/add")
def add_coach_points(
    event: LearningEvent,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加教练积分"""
    if event.user_type != "coach":
        raise HTTPException(status_code=400, detail="仅限教练用户")

    config = CONTENT_POINTS_CONFIG.get(event.content_type, {})
    points = config.get("base_points", 5)

    if event.action == "complete":
        points += config.get("complete_bonus", 0)

    if event.action == "quiz_pass" and event.quiz_score:
        points += config.get("quiz_bonus", 0)
        if event.quiz_score == 100:
            points += 5

    category = "growth"
    if event.content_category in ["contribution", "influence"]:
        category = event.content_category

    result = record_learning_points(
        db, current_user.id, points, event.action, category, event.content_id
    )

    return {
        "success": True,
        "points_earned": points,
        "category": category,
        "new_total": result["total_points"],
    }


# ============================================================================
# 成长者时长 API
# ============================================================================

@router.get("/grower/stats/{user_id}")
def get_grower_stats(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取成长者学习统计（时长+积分分开）"""
    # 越权校验
    # FIX-09: 细粒度访问控制 (教练仅限自己学员)
    check_user_data_access(current_user, user_id, db)
    stats = get_or_create_stats(db, user_id)

    total_minutes = stats.total_minutes
    total_points = stats.total_points

    # 计算今日/本周时长
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())

    today_minutes = db.query(func.coalesce(func.sum(LearningTimeLog.minutes), 0)).filter(
        LearningTimeLog.user_id == user_id, LearningTimeLog.earned_at >= today_start
    ).scalar()
    week_minutes = db.query(func.coalesce(func.sum(LearningTimeLog.minutes), 0)).filter(
        LearningTimeLog.user_id == user_id, LearningTimeLog.earned_at >= week_start
    ).scalar()

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

    time_rewards_earned = sum(1 for m in GROWER_TIME_MILESTONES if m["minutes"] <= total_minutes)
    points_rewards_earned = sum(1 for m in GROWER_POINTS_MILESTONES if m["points"] <= total_points)

    return {
        "user_id": user_id,
        "learning_time": {
            "total_minutes": total_minutes,
            "total_hours": round(total_minutes / 60, 1),
            "today_minutes": today_minutes,
            "week_minutes": week_minutes,
            "next_milestone": next_time_milestone,
            "milestone_progress": int((total_minutes / next_time_milestone["minutes"]) * 100) if next_time_milestone else 100,
            "rewards_earned": time_rewards_earned,
        },
        "learning_points": {
            "total_points": total_points,
            "quiz_stats": {
                "total_quizzes": stats.quiz_total,
                "passed_quizzes": stats.quiz_passed,
                "pass_rate": round(stats.quiz_passed / max(stats.quiz_total, 1) * 100, 1),
            },
            "next_milestone": next_points_milestone,
            "milestone_progress": int((total_points / next_points_milestone["points"]) * 100) if next_points_milestone else 100,
            "rewards_earned": points_rewards_earned,
        },
        "streak": {
            "current_streak": stats.current_streak,
            "longest_streak": stats.longest_streak,
            "today_learned": stats.last_learn_date == date.today().isoformat(),
        }
    }


@router.get("/grower/time/{user_id}")
def get_grower_time(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取成长者学习时长（单独）"""
    # 越权校验
    # FIX-09: 细粒度访问控制 (教练仅限自己学员)
    check_user_data_access(current_user, user_id, db)
    stats = get_or_create_stats(db, user_id)
    total_minutes = stats.total_minutes

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    today_minutes = db.query(func.coalesce(func.sum(LearningTimeLog.minutes), 0)).filter(
        LearningTimeLog.user_id == user_id, LearningTimeLog.earned_at >= today_start
    ).scalar()
    week_minutes = db.query(func.coalesce(func.sum(LearningTimeLog.minutes), 0)).filter(
        LearningTimeLog.user_id == user_id, LearningTimeLog.earned_at >= week_start
    ).scalar()
    month_minutes = db.query(func.coalesce(func.sum(LearningTimeLog.minutes), 0)).filter(
        LearningTimeLog.user_id == user_id, LearningTimeLog.earned_at >= month_start
    ).scalar()

    # 领域分布
    domain_rows = db.query(
        LearningTimeLog.domain,
        func.sum(LearningTimeLog.minutes).label("total")
    ).filter(
        LearningTimeLog.user_id == user_id,
        LearningTimeLog.domain.isnot(None)
    ).group_by(LearningTimeLog.domain).all()

    domain_total = sum(r.total for r in domain_rows) or 1
    domain_distribution = {}
    for r in domain_rows:
        domain_distribution[r.domain] = {
            "minutes": int(r.total),
            "percent": round(int(r.total) / domain_total * 100),
        }

    # 下一个里程碑
    next_milestone = None
    for milestone in GROWER_TIME_MILESTONES:
        if milestone["minutes"] > total_minutes:
            next_milestone = milestone
            break

    rewards_earned = sum(1 for m in GROWER_TIME_MILESTONES if m["minutes"] <= total_minutes)

    return {
        "user_id": user_id,
        "total_minutes": total_minutes,
        "total_hours": round(total_minutes / 60, 1),
        "today_minutes": today_minutes,
        "week_minutes": week_minutes,
        "month_minutes": month_minutes,
        "rewards_earned": rewards_earned,
        "next_milestone": next_milestone,
        "milestone_progress": int((total_minutes / next_milestone["minutes"]) * 100) if next_milestone else 100,
        "domain_distribution": domain_distribution,
    }


@router.get("/grower/points/{user_id}")
def get_grower_points(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取成长者学习积分（测试积分，单独）"""
    # 越权校验
    # FIX-09: 细粒度访问控制 (教练仅限自己学员)
    check_user_data_access(current_user, user_id, db)
    stats = get_or_create_stats(db, user_id)
    total_points = stats.total_points

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    today_points = db.query(func.coalesce(func.sum(LearningPointsLog.points), 0)).filter(
        LearningPointsLog.user_id == user_id, LearningPointsLog.earned_at >= today_start
    ).scalar()
    week_points = db.query(func.coalesce(func.sum(LearningPointsLog.points), 0)).filter(
        LearningPointsLog.user_id == user_id, LearningPointsLog.earned_at >= week_start
    ).scalar()
    month_points = db.query(func.coalesce(func.sum(LearningPointsLog.points), 0)).filter(
        LearningPointsLog.user_id == user_id, LearningPointsLog.earned_at >= month_start
    ).scalar()

    next_milestone = None
    for milestone in GROWER_POINTS_MILESTONES:
        if milestone["points"] > total_points:
            next_milestone = milestone
            break

    rewards_earned = sum(1 for m in GROWER_POINTS_MILESTONES if m["points"] <= total_points)

    return {
        "user_id": user_id,
        "total_points": total_points,
        "today_points": today_points,
        "week_points": week_points,
        "month_points": month_points,
        "quiz_stats": {
            "total_quizzes": stats.quiz_total,
            "passed_quizzes": stats.quiz_passed,
            "pass_rate": round(stats.quiz_passed / max(stats.quiz_total, 1) * 100, 1),
        },
        "rewards_earned": rewards_earned,
        "next_milestone": next_milestone,
        "milestone_progress": int((total_points / next_milestone["points"]) * 100) if next_milestone else 100,
    }


@router.post("/grower/points/add")
def add_grower_quiz_points(
    body: GrowerQuizPointsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加成长者测试积分

    请求体: {"quiz_id": "q1", "score": 85, "correct_count": 8, "total_count": 10}
    """
    user_id = body.user_id or current_user.id
    passed = body.score >= 60
    is_perfect = body.score == 100

    points_earned = 0
    if passed:
        points_earned += GROWER_QUIZ_POINTS["pass_base"]
        points_earned += body.correct_count * GROWER_QUIZ_POINTS["per_correct"]
        if is_perfect:
            points_earned += GROWER_QUIZ_POINTS["perfect_bonus"]
        if body.is_first_try:
            points_earned += GROWER_QUIZ_POINTS["first_try_bonus"]

    old_stats = get_or_create_stats(db, user_id)
    current_total = old_stats.total_points

    if points_earned > 0:
        record_learning_points(db, user_id, points_earned, "quiz", "growth", body.quiz_id)

    record_quiz_result(db, user_id, passed)

    new_stats = get_or_create_stats(db, user_id)
    new_total = new_stats.total_points

    new_milestones = []
    for milestone in GROWER_POINTS_MILESTONES:
        if current_total < milestone["points"] <= new_total:
            new_milestones.append(milestone)

    return {
        "success": True,
        "points_earned": points_earned,
        "breakdown": {
            "pass_base": GROWER_QUIZ_POINTS["pass_base"] if passed else 0,
            "correct_bonus": body.correct_count * GROWER_QUIZ_POINTS["per_correct"] if passed else 0,
            "perfect_bonus": GROWER_QUIZ_POINTS["perfect_bonus"] if is_perfect else 0,
            "first_try_bonus": GROWER_QUIZ_POINTS["first_try_bonus"] if passed and body.is_first_try else 0,
        },
        "new_total": new_total,
        "new_milestones": new_milestones,
    }


@router.get("/grower/time/{user_id}/history")
def get_grower_time_history(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    domain: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取成长者学习时长历史"""
    # 越权校验
    # FIX-09: 细粒度访问控制 (教练仅限自己学员)
    check_user_data_access(current_user, user_id, db)
    query = db.query(LearningTimeLog).filter(LearningTimeLog.user_id == user_id)
    if domain:
        query = query.filter(LearningTimeLog.domain == domain)
    if start_date:
        query = query.filter(LearningTimeLog.earned_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(LearningTimeLog.earned_at <= datetime.fromisoformat(end_date))

    total = query.count()
    items = query.order_by(LearningTimeLog.earned_at.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    # 分页内小结
    page_minutes = sum(item.minutes for item in items)
    domain_sums: Dict[str, int] = {}
    for item in items:
        if item.domain:
            domain_sums[item.domain] = domain_sums.get(item.domain, 0) + item.minutes

    return {
        "items": [
            {
                "record_id": str(item.id),
                "content_type": "learning",
                "content_id": str(item.content_id) if item.content_id else "",
                "content_title": item.domain or "学习",
                "minutes": item.minutes,
                "domain": item.domain,
                "earned_at": item.earned_at.isoformat() if item.earned_at else None,
            }
            for item in items
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": {
            "total_minutes": page_minutes,
            "domains": domain_sums,
        },
    }


@router.post("/grower/time/add")
def add_grower_time(
    body: GrowerTimeAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加成长者学习时长 (轻量版)

    请求体: {"minutes": 30, "domain": "nutrition"}
    """
    minutes = body.minutes
    if minutes <= 0:
        raise HTTPException(status_code=400, detail="学习时长必须大于 0")
    # FIX-06: 学习时长上限 (单次最多480分钟 = 8小时)
    if minutes > 480:
        raise HTTPException(status_code=400, detail="单次学习时长不能超过 480 分钟")

    old_stats = get_or_create_stats(db, current_user.id)
    current_total = old_stats.total_minutes

    record_learning_time(db, current_user.id, minutes, domain=body.domain)

    new_stats = get_or_create_stats(db, current_user.id)
    new_total = new_stats.total_minutes

    new_milestones = []
    for milestone in GROWER_TIME_MILESTONES:
        if current_total < milestone["minutes"] <= new_total:
            new_milestones.append(milestone)

    return {
        "success": True,
        "minutes_earned": minutes,
        "new_total": new_total,
        "new_milestones": new_milestones,
    }


@router.get("/grower/streak/{user_id}")
def get_grower_streak(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取成长者连续学习记录"""
    # 越权校验
    # FIX-09: 细粒度访问控制 (教练仅限自己学员)
    check_user_data_access(current_user, user_id, db)
    stats = get_or_create_stats(db, user_id)
    current_streak = stats.current_streak
    longest_streak = stats.longest_streak
    today_learned = stats.last_learn_date == date.today().isoformat()

    next_streak_reward = None
    for milestone in STREAK_MILESTONES:
        if milestone["days"] > current_streak:
            next_streak_reward = milestone
            break

    earned_streaks = [m for m in STREAK_MILESTONES if m["days"] <= longest_streak]

    return {
        "user_id": user_id,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "today_learned": today_learned,
        "next_reward": next_streak_reward,
        "days_to_next": next_streak_reward["days"] - current_streak if next_streak_reward else 0,
        "earned_rewards": earned_streaks,
    }


# ============================================================================
# 奖励系统 API
# ============================================================================

@router.get("/rewards/{user_id}")
def get_user_rewards(
    user_id: int,
    user_type: str = "grower",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户奖励列表"""
    # 越权校验
    # FIX-09: 细粒度访问控制 (教练仅限自己学员)
    check_user_data_access(current_user, user_id, db)
    stats = get_or_create_stats(db, user_id)

    if user_type == "grower":
        return {
            "user_id": user_id,
            "user_type": "grower",
            "time_rewards": [
                {
                    "milestone": m,
                    "earned": m["minutes"] <= stats.total_minutes,
                }
                for m in GROWER_TIME_MILESTONES
            ],
            "streak_rewards": [
                {
                    "milestone": m,
                    "earned": m["days"] <= stats.longest_streak,
                }
                for m in STREAK_MILESTONES
            ],
            "total_reward_points": sum(
                m["bonus_points"] for m in GROWER_TIME_MILESTONES if m["minutes"] <= stats.total_minutes
            ) + sum(
                m["points"] for m in STREAK_MILESTONES if m["days"] <= stats.longest_streak
            ),
            "unclaimed_rewards": 0,
        }
    else:
        growth = stats.growth_points
        contribution = stats.contribution_points
        influence = stats.influence_points
        certifications = []
        for lvl_key, req in COACH_LEVEL_REQUIREMENTS.items():
            met = (growth >= req["min_growth"] and
                   contribution >= req["min_contribution"] and
                   influence >= req["min_influence"])
            progress = 100
            if not met:
                g_p = min(growth / max(req["min_growth"], 1), 1.0)
                c_p = min(contribution / max(req["min_contribution"], 1), 1.0) if req["min_contribution"] > 0 else 1.0
                i_p = min(influence / max(req["min_influence"], 1), 1.0) if req["min_influence"] > 0 else 1.0
                progress = int((g_p + c_p + i_p) / 3 * 100)
            certifications.append({
                "level": lvl_key,
                "label": req["label"],
                "earned": met,
                "progress": progress,
            })
        return {
            "user_id": user_id,
            "user_type": "coach",
            "level_certifications": certifications,
        }


@router.post("/rewards/claim")
def claim_reward(
    claim: RewardClaim,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """领取奖励"""
    db.add(UserActivityLog(
        user_id=current_user.id,
        activity_type="reward",
        detail={"reward_type": claim.reward_type, "reward_id": claim.reward_id},
        created_at=datetime.utcnow(),
    ))
    db.commit()

    return {
        "success": True,
        "reward_type": claim.reward_type,
        "reward_id": claim.reward_id,
        "message": "奖励已领取",
    }


# ============================================================================
# 排行榜 API
# ============================================================================

@router.get("/leaderboard/coaches")
def get_coach_leaderboard(
    period: str = Query("week", pattern="^(week|month|all)$"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """教练积分排行榜"""
    leaders = db.query(UserLearningStats).order_by(
        UserLearningStats.total_points.desc()
    ).limit(limit).all()

    items = []
    for rank, s in enumerate(leaders, 1):
        user = db.query(User).filter(User.id == s.user_id).first()
        level = "L0"
        for lvl_key in reversed(list(COACH_LEVEL_REQUIREMENTS.keys())):
            req = COACH_LEVEL_REQUIREMENTS[lvl_key]
            if (s.growth_points >= req["min_growth"] and
                s.contribution_points >= req["min_contribution"] and
                s.influence_points >= req["min_influence"]):
                level = lvl_key
                break
        items.append({
            "rank": rank,
            "user_id": s.user_id,
            "name": user.username if user else "未知",
            "points": s.total_points,
            "level": level,
        })

    my_stats = get_or_create_stats(db, current_user.id)
    my_rank = db.query(func.count(UserLearningStats.id)).filter(
        UserLearningStats.total_points > my_stats.total_points
    ).scalar() + 1

    return {
        "period": period,
        "items": items,
        "my_rank": my_rank,
        "my_points": my_stats.total_points,
    }


@router.get("/leaderboard/growers")
def get_grower_leaderboard(
    period: str = Query("week"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """成长者学习时长排行榜"""
    leaders = db.query(UserLearningStats).order_by(
        UserLearningStats.total_minutes.desc()
    ).limit(limit).all()

    items = []
    for rank, s in enumerate(leaders, 1):
        user = db.query(User).filter(User.id == s.user_id).first()
        items.append({
            "rank": rank,
            "user_id": s.user_id,
            "name": user.username if user else "未知",
            "minutes": s.total_minutes,
            "streak": s.current_streak,
        })

    return {"period": period, "items": items}


# ============================================================================
# 统一事件处理
# ============================================================================

@router.post("/event")
def handle_learning_event(
    event: LearningEvent,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """处理学习事件（统一入口）— 写入真实 DB"""
    user_id = current_user.id
    minutes = event.duration_seconds // 60

    # FIX-06: 学习时长上限 (单次最多480分钟 = 8小时)
    if minutes > 480:
        raise HTTPException(status_code=400, detail=f"单次学习时长不能超过 480 分钟")

    if minutes > 0:
        record_learning_time(db, user_id, minutes, domain=event.content_category)

    # 计算积分
    config = CONTENT_POINTS_CONFIG.get(event.content_type, {})
    points = config.get("base_points", 5)
    if event.action == "complete":
        points += config.get("complete_bonus", 0)
    if event.action == "quiz_pass" and event.quiz_score:
        points += config.get("quiz_bonus", 0)
        if event.quiz_score == 100:
            points += 5

    category = "growth"
    if event.content_category in ["contribution", "influence"]:
        category = event.content_category

    record_learning_points(db, user_id, points, event.action, category, event.content_id)

    # 记录活动
    db.add(UserActivityLog(
        user_id=user_id, activity_type="learn",
        detail={"content_id": event.content_id, "action": event.action, "minutes": minutes},
        created_at=datetime.utcnow(),
    ))
    db.commit()

    stats = get_or_create_stats(db, user_id)
    return {
        "user_type": event.user_type,
        "minutes_earned": minutes,
        "points_earned": points,
        "new_total_minutes": stats.total_minutes,
        "new_total_points": stats.total_points,
    }

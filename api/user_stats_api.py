"""
用户统计 API (需求6)

教练/专家展示 + 用户活动统计
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.database import get_db
from core.models import (
    User, UserRole, UserLearningStats, UserActivityLog,
    LearningTimeLog, LearningPointsLog, ExamResult,
)
from api.dependencies import get_current_user, require_admin, require_coach_or_admin

router = APIRouter(prefix="/api/v1/stats", tags=["用户统计"])


@router.get("/user/{user_id}/overview")
def user_overview(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """个人统计总览"""
    # 自己看自己 或 教练/管理员查看
    if current_user.id != user_id:
        role = current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
        if role not in ["coach", "supervisor", "promoter", "master", "admin"]:
            raise HTTPException(403, "无权限查看他人统计")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")

    stats = db.query(UserLearningStats).filter(
        UserLearningStats.user_id == user_id
    ).first()

    # 最近活动数
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_activities = db.query(func.count(UserActivityLog.id)).filter(
        UserActivityLog.user_id == user_id,
        UserActivityLog.created_at >= week_ago,
    ).scalar() or 0

    # 考试统计
    exam_count = db.query(func.count(ExamResult.id)).filter(
        ExamResult.user_id == user_id,
    ).scalar() or 0
    exam_passed = db.query(func.count(ExamResult.id)).filter(
        ExamResult.user_id == user_id,
        ExamResult.status == "passed",
    ).scalar() or 0

    return {
        "user_id": user_id,
        "username": user.username,
        "role": user.role.value if hasattr(user.role, 'value') else user.role,
        "learning": {
            "total_minutes": stats.total_minutes if stats else 0,
            "total_points": stats.total_points if stats else 0,
            "growth_points": stats.growth_points if stats else 0,
            "contribution_points": stats.contribution_points if stats else 0,
            "influence_points": stats.influence_points if stats else 0,
            "current_streak": stats.current_streak if stats else 0,
            "longest_streak": stats.longest_streak if stats else 0,
        },
        "exam": {
            "total": exam_count,
            "passed": exam_passed,
        },
        "recent_activities_7d": recent_activities,
        "member_since": user.created_at.isoformat() if user.created_at else None,
    }


@router.get("/user/{user_id}/activity")
def user_activity_timeline(
    user_id: int,
    days: int = 30,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """用户活动时间线"""
    if current_user.id != user_id:
        role = current_user.role.value if hasattr(current_user.role, 'value') else current_user.role
        if role not in ["coach", "supervisor", "promoter", "master", "admin"]:
            raise HTTPException(403, "无权限")

    since = datetime.utcnow() - timedelta(days=days)
    query = db.query(UserActivityLog).filter(
        UserActivityLog.user_id == user_id,
        UserActivityLog.created_at >= since,
    ).order_by(UserActivityLog.created_at.desc())
    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": a.id,
                "activity_type": a.activity_type,
                "detail": a.detail,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in items
        ],
    }


@router.get("/admin/grower-report")
def grower_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """成长者统计报告"""
    growers = db.query(User).filter(User.role == UserRole.GROWER, User.is_active == True).all()
    report = []
    for u in growers:
        stats = db.query(UserLearningStats).filter(UserLearningStats.user_id == u.id).first()
        report.append({
            "user_id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "total_minutes": stats.total_minutes if stats else 0,
            "total_points": stats.total_points if stats else 0,
            "current_streak": stats.current_streak if stats else 0,
            "quiz_passed": stats.quiz_passed if stats else 0,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })
    return {"total": len(report), "items": report}


@router.get("/admin/sharer-report")
def sharer_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """分享者统计报告"""
    sharers = db.query(User).filter(User.role == UserRole.SHARER, User.is_active == True).all()
    report = []
    for u in sharers:
        stats = db.query(UserLearningStats).filter(UserLearningStats.user_id == u.id).first()
        report.append({
            "user_id": u.id,
            "username": u.username,
            "full_name": u.full_name,
            "total_minutes": stats.total_minutes if stats else 0,
            "contribution_points": stats.contribution_points if stats else 0,
            "influence_points": stats.influence_points if stats else 0,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        })
    return {"total": len(report), "items": report}


@router.get("/admin/activity-report")
def activity_report(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """全平台活动报告"""
    since = datetime.utcnow() - timedelta(days=days)

    # 按活动类型统计
    type_counts = db.query(
        UserActivityLog.activity_type,
        func.count(UserActivityLog.id).label("count")
    ).filter(
        UserActivityLog.created_at >= since
    ).group_by(UserActivityLog.activity_type).all()

    # 活跃用户数
    active_users = db.query(
        func.count(func.distinct(UserActivityLog.user_id))
    ).filter(
        UserActivityLog.created_at >= since
    ).scalar() or 0

    # 总活动数
    total_activities = db.query(
        func.count(UserActivityLog.id)
    ).filter(
        UserActivityLog.created_at >= since
    ).scalar() or 0

    return {
        "period_days": days,
        "active_users": active_users,
        "total_activities": total_activities,
        "by_type": {t: c for t, c in type_counts},
    }

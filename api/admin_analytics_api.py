# -*- coding: utf-8 -*-
"""
Admin 数据分析 API
Admin Analytics API

端点：
- GET /api/v1/analytics/admin/overview               - 平台概览 KPI
- GET /api/v1/analytics/admin/user-growth             - 用户增长趋势
- GET /api/v1/analytics/admin/role-distribution       - 角色分布
- GET /api/v1/analytics/admin/stage-distribution      - 全平台阶段分布
- GET /api/v1/analytics/admin/risk-distribution       - 风险等级分布
- GET /api/v1/analytics/admin/coach-leaderboard       - 教练绩效排行
- GET /api/v1/analytics/admin/challenge-effectiveness - 挑战活动效果
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, distinct
from datetime import datetime, timedelta
from loguru import logger

from core.database import get_db
from core.models import (
    User, UserRole, Assessment, BehavioralProfile, RiskLevel,
    MicroActionTask,
    ChallengeTemplate, ChallengeEnrollment, EnrollmentStatus,
)
from api.dependencies import require_admin

router = APIRouter(prefix="/api/v1/analytics/admin", tags=["Admin分析"])

_STAGE_LABEL = {
    "S0": "觉醒期", "S1": "松动期", "S2": "探索期", "S3": "准备期",
    "S4": "行动期", "S5": "坚持期", "S6": "融入期",
}

_ROLE_LABEL = {
    "observer": "观察员",
    "grower": "成长者",
    "sharer": "分享者",
    "coach": "教练",
    "promoter": "促进师",
    "supervisor": "督导",
    "master": "大师",
    "admin": "管理员",
    "patient": "患者(旧)",
}


@router.get("/overview")
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """平台概览 KPI"""
    total_users = db.query(func.count(User.id)).scalar() or 0
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar() or 0
    coach_count = db.query(func.count(User.id)).filter(
        User.role.in_([UserRole.COACH, UserRole.PROMOTER, UserRole.SUPERVISOR, UserRole.MASTER]),
        User.is_active == True,
    ).scalar() or 0

    # 高风险学员: 最新评估为 R3 or R4
    from sqlalchemy import and_
    latest_assessment = (
        db.query(
            Assessment.user_id,
            func.max(Assessment.created_at).label("latest"),
        )
        .group_by(Assessment.user_id)
        .subquery()
    )
    high_risk_count = (
        db.query(func.count(distinct(Assessment.user_id)))
        .join(latest_assessment, and_(
            Assessment.user_id == latest_assessment.c.user_id,
            Assessment.created_at == latest_assessment.c.latest,
        ))
        .filter(Assessment.risk_level.in_([RiskLevel.R3, RiskLevel.R4]))
        .scalar()
    ) or 0

    return {
        "total_users": total_users,
        "active_users": active_users,
        "coach_count": coach_count,
        "high_risk_count": high_risk_count,
    }


@router.get("/user-growth")
def get_user_growth(
    months: int = Query(12, ge=3, le=24),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """用户增长趋势 (bar + line)"""
    since = datetime.utcnow() - timedelta(days=months * 30)
    rows = (
        db.query(
            func.strftime("%Y-%m", User.created_at).label("month"),
            func.count().label("new_users"),
        )
        .filter(User.created_at >= since)
        .group_by(func.strftime("%Y-%m", User.created_at))
        .order_by(func.strftime("%Y-%m", User.created_at))
        .all()
    )

    months_list = [r.month for r in rows]
    new_users = [int(r.new_users) for r in rows]
    cumulative = []
    total = 0
    for n in new_users:
        total += n
        cumulative.append(total)

    return {
        "months": months_list,
        "new_users": new_users,
        "cumulative": cumulative,
    }


@router.get("/role-distribution")
def get_role_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """角色分布 (pie)"""
    rows = (
        db.query(
            User.role,
            func.count().label("cnt"),
        )
        .filter(User.is_active == True)
        .group_by(User.role)
        .order_by(func.count().desc())
        .all()
    )
    return {
        "roles": [r.role.value for r in rows],
        "labels": [_ROLE_LABEL.get(r.role.value, r.role.value) for r in rows],
        "counts": [int(r.cnt) for r in rows],
    }


@router.get("/stage-distribution")
def get_stage_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """全平台行为阶段分布 (bar)"""
    rows = (
        db.query(
            BehavioralProfile.current_stage,
            func.count().label("cnt"),
        )
        .group_by(BehavioralProfile.current_stage)
        .order_by(BehavioralProfile.current_stage)
        .all()
    )
    return {
        "stages": [r.current_stage.value if r.current_stage else "unknown" for r in rows],
        "labels": [_STAGE_LABEL.get(r.current_stage.value, "未知") if r.current_stage else "未知" for r in rows],
        "counts": [int(r.cnt) for r in rows],
    }


@router.get("/risk-distribution")
def get_risk_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """风险等级分布 (donut) — 取每用户最新评估"""
    from sqlalchemy import and_
    latest = (
        db.query(
            Assessment.user_id,
            func.max(Assessment.created_at).label("latest"),
        )
        .group_by(Assessment.user_id)
        .subquery()
    )
    rows = (
        db.query(
            Assessment.risk_level,
            func.count().label("cnt"),
        )
        .join(latest, and_(
            Assessment.user_id == latest.c.user_id,
            Assessment.created_at == latest.c.latest,
        ))
        .group_by(Assessment.risk_level)
        .order_by(Assessment.risk_level)
        .all()
    )

    _risk_label = {"R0": "正常", "R1": "轻度", "R2": "中度", "R3": "高度", "R4": "危机"}
    return {
        "levels": [r.risk_level.value for r in rows],
        "labels": [_risk_label.get(r.risk_level.value, r.risk_level.value) for r in rows],
        "counts": [int(r.cnt) for r in rows],
    }


@router.get("/coach-leaderboard")
def get_coach_leaderboard(
    limit: int = Query(10, ge=5, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """教练绩效排行 (horizontal bar)"""
    coaches = (
        db.query(User)
        .filter(
            User.role.in_([UserRole.COACH, UserRole.PROMOTER, UserRole.SUPERVISOR, UserRole.MASTER]),
            User.is_active == True,
        )
        .all()
    )

    leaderboard = []
    for coach in coaches:
        # 查找教练的学员 (简化: 取 profile 中 coach_id 匹配的，或同 role 级别以下)
        student_ids = [
            r[0] for r in db.query(User.id).filter(
                User.role.in_([UserRole.OBSERVER, UserRole.GROWER, UserRole.SHARER]),
                User.is_active == True,
            ).all()
        ]
        if not student_ids:
            continue

        # 近30天微行动完成率
        since = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
        stats = (
            db.query(
                func.count().label("total"),
                func.sum(case((MicroActionTask.status == "completed", 1), else_=0)).label("completed"),
            )
            .filter(
                MicroActionTask.user_id.in_(student_ids),
                MicroActionTask.scheduled_date >= since,
            )
            .first()
        )
        total = int(stats.total or 0)
        completed = int(stats.completed or 0)
        rate = round(completed / total * 100, 1) if total > 0 else 0

        leaderboard.append({
            "coach_id": coach.id,
            "name": coach.full_name or coach.username,
            "student_count": len(student_ids),
            "completion_rate": rate,
            "completed_tasks": completed,
            "total_tasks": total,
        })

    leaderboard.sort(key=lambda x: x["completion_rate"], reverse=True)
    return {"leaderboard": leaderboard[:limit]}


@router.get("/challenge-effectiveness")
def get_challenge_effectiveness(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """挑战活动效果 (grouped bar)"""
    rows = (
        db.query(
            ChallengeTemplate.title,
            ChallengeTemplate.category,
            ChallengeTemplate.duration_days,
            func.count(ChallengeEnrollment.id).label("enrolled"),
            func.sum(case((ChallengeEnrollment.status == EnrollmentStatus.ACTIVE, 1), else_=0)).label("active"),
            func.sum(case((ChallengeEnrollment.status == EnrollmentStatus.COMPLETED, 1), else_=0)).label("completed"),
            func.sum(case((ChallengeEnrollment.status == EnrollmentStatus.DROPPED, 1), else_=0)).label("dropped"),
        )
        .join(ChallengeEnrollment, ChallengeEnrollment.challenge_id == ChallengeTemplate.id)
        .group_by(ChallengeTemplate.id, ChallengeTemplate.title, ChallengeTemplate.category, ChallengeTemplate.duration_days)
        .order_by(func.count(ChallengeEnrollment.id).desc())
        .limit(10)
        .all()
    )
    return {
        "challenges": [
            {
                "title": r.title,
                "category": r.category,
                "duration_days": r.duration_days,
                "enrolled": int(r.enrolled),
                "active": int(r.active or 0),
                "completed": int(r.completed or 0),
                "dropped": int(r.dropped or 0),
                "completion_rate": round(int(r.completed or 0) / int(r.enrolled) * 100, 1) if r.enrolled else 0,
            }
            for r in rows
        ]
    }

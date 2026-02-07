# -*- coding: utf-8 -*-
"""
Coach 数据分析 API
Coach Analytics API

端点：
- GET /api/v1/analytics/coach/risk-trend         - 学员风险等级趋势
- GET /api/v1/analytics/coach/micro-action-trend  - 微行动完成率趋势
- GET /api/v1/analytics/coach/domain-performance  - 领域完成率对比
- GET /api/v1/analytics/coach/alert-frequency     - 预警频率分布
- GET /api/v1/analytics/coach/challenge-stats     - 挑战报名vs完成
- GET /api/v1/analytics/coach/stage-distribution  - 学员阶段分布
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime, timedelta
from loguru import logger

from core.database import get_db
from core.models import (
    User, UserRole, Assessment, BehavioralProfile, RiskLevel,
    MicroActionTask, DeviceAlert,
    ChallengeTemplate, ChallengeEnrollment, EnrollmentStatus,
)
from api.dependencies import require_coach_or_admin

router = APIRouter(prefix="/api/v1/analytics/coach", tags=["Coach分析"])

_STAGE_LABEL = {
    "S0": "觉醒期", "S1": "松动期", "S2": "探索期", "S3": "准备期",
    "S4": "行动期", "S5": "坚持期", "S6": "融入期",
}


def _get_student_ids(db: Session, coach_user: User) -> list[int]:
    """获取教练的学员 ID 列表"""
    if coach_user.role == UserRole.ADMIN:
        rows = db.query(User.id).filter(
            User.role.in_([UserRole.OBSERVER, UserRole.GROWER, UserRole.SHARER]),
            User.is_active == True,
        ).all()
    else:
        rows = db.query(User.id).filter(
            User.role.in_([UserRole.OBSERVER, UserRole.GROWER, UserRole.SHARER]),
            User.is_active == True,
        ).all()
    return [r[0] for r in rows]


@router.get("/risk-trend")
def get_risk_trend(
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """学员风险等级趋势 (stacked area)"""
    student_ids = _get_student_ids(db, current_user)
    if not student_ids:
        return {"dates": [], "low": [], "medium": [], "high": []}

    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(
            func.date(Assessment.created_at).label("day"),
            func.sum(case((Assessment.risk_level.in_([RiskLevel.R0, RiskLevel.R1]), 1), else_=0)).label("low"),
            func.sum(case((Assessment.risk_level == RiskLevel.R2, 1), else_=0)).label("medium"),
            func.sum(case((Assessment.risk_level.in_([RiskLevel.R3, RiskLevel.R4]), 1), else_=0)).label("high"),
        )
        .filter(Assessment.user_id.in_(student_ids), Assessment.created_at >= since)
        .group_by(func.date(Assessment.created_at))
        .order_by(func.date(Assessment.created_at))
        .all()
    )
    return {
        "dates": [str(r.day) for r in rows],
        "low": [int(r.low or 0) for r in rows],
        "medium": [int(r.medium or 0) for r in rows],
        "high": [int(r.high or 0) for r in rows],
    }


@router.get("/micro-action-trend")
def get_micro_action_trend(
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """微行动完成率趋势 (line + area)"""
    student_ids = _get_student_ids(db, current_user)
    if not student_ids:
        return {"dates": [], "total": [], "completed": [], "rate": []}

    since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = (
        db.query(
            MicroActionTask.scheduled_date,
            func.count().label("total"),
            func.sum(case((MicroActionTask.status == "completed", 1), else_=0)).label("completed"),
        )
        .filter(MicroActionTask.user_id.in_(student_ids), MicroActionTask.scheduled_date >= since)
        .group_by(MicroActionTask.scheduled_date)
        .order_by(MicroActionTask.scheduled_date)
        .all()
    )
    return {
        "dates": [r.scheduled_date for r in rows],
        "total": [int(r.total) for r in rows],
        "completed": [int(r.completed or 0) for r in rows],
        "rate": [round(int(r.completed or 0) / int(r.total) * 100, 1) if r.total else 0 for r in rows],
    }


@router.get("/domain-performance")
def get_domain_performance(
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """领域完成率对比 (radar)"""
    student_ids = _get_student_ids(db, current_user)
    if not student_ids:
        return {"domains": [], "rates": []}

    since = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = (
        db.query(
            MicroActionTask.domain,
            func.count().label("total"),
            func.sum(case((MicroActionTask.status == "completed", 1), else_=0)).label("completed"),
        )
        .filter(MicroActionTask.user_id.in_(student_ids), MicroActionTask.scheduled_date >= since)
        .group_by(MicroActionTask.domain)
        .order_by(MicroActionTask.domain)
        .all()
    )
    return {
        "domains": [r.domain for r in rows],
        "rates": [round(int(r.completed or 0) / int(r.total) * 100, 1) if r.total else 0 for r in rows],
    }


@router.get("/alert-frequency")
def get_alert_frequency(
    days: int = Query(30, ge=7, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """预警频率分布 (horizontal bar)"""
    student_ids = _get_student_ids(db, current_user)
    if not student_ids:
        return {"types": [], "warning": [], "danger": []}

    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(
            DeviceAlert.alert_type,
            func.sum(case((DeviceAlert.severity == "warning", 1), else_=0)).label("warning"),
            func.sum(case((DeviceAlert.severity == "danger", 1), else_=0)).label("danger"),
        )
        .filter(DeviceAlert.user_id.in_(student_ids), DeviceAlert.created_at >= since)
        .group_by(DeviceAlert.alert_type)
        .order_by(func.count().desc())
        .all()
    )
    return {
        "types": [r.alert_type for r in rows],
        "warning": [int(r.warning or 0) for r in rows],
        "danger": [int(r.danger or 0) for r in rows],
    }


@router.get("/challenge-stats")
def get_challenge_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """挑战报名 vs 完成 (grouped bar)"""
    rows = (
        db.query(
            ChallengeTemplate.title,
            func.count(ChallengeEnrollment.id).label("enrolled"),
            func.sum(case((ChallengeEnrollment.status == EnrollmentStatus.COMPLETED, 1), else_=0)).label("completed"),
        )
        .join(ChallengeEnrollment, ChallengeEnrollment.challenge_id == ChallengeTemplate.id)
        .group_by(ChallengeTemplate.id, ChallengeTemplate.title)
        .order_by(func.count(ChallengeEnrollment.id).desc())
        .limit(10)
        .all()
    )
    return {
        "challenges": [r.title for r in rows],
        "enrolled": [int(r.enrolled) for r in rows],
        "completed": [int(r.completed or 0) for r in rows],
    }


@router.get("/stage-distribution")
def get_stage_distribution(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """学员阶段分布 (donut)"""
    student_ids = _get_student_ids(db, current_user)
    if not student_ids:
        return {"stages": [], "labels": [], "counts": []}

    rows = (
        db.query(
            BehavioralProfile.current_stage,
            func.count().label("cnt"),
        )
        .filter(BehavioralProfile.user_id.in_(student_ids))
        .group_by(BehavioralProfile.current_stage)
        .order_by(BehavioralProfile.current_stage)
        .all()
    )
    return {
        "stages": [r.current_stage.value if r.current_stage else "unknown" for r in rows],
        "labels": [_STAGE_LABEL.get(r.current_stage.value, "未知") if r.current_stage else "未知" for r in rows],
        "counts": [int(r.cnt) for r in rows],
    }

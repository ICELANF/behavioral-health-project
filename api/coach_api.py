# -*- coding: utf-8 -*-
"""
教练端API端点
Coach API Endpoints

端点：
- GET  /api/v1/coach/students     - 教练的学员列表
- GET  /api/v1/coach/students/{id} - 学员详情
- GET  /api/v1/coach/performance  - 教练绩效数据
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timedelta
from loguru import logger

from core.database import get_db
from core.models import User, UserRole, Assessment, BehavioralProfile
from core.behavioral_profile_service import BehavioralProfileService
from core.intervention_matcher import InterventionMatcher
from api.dependencies import get_current_user, require_coach_or_admin

_profile_service = BehavioralProfileService()
_intervention_matcher = InterventionMatcher()

router = APIRouter(prefix="/api/v1/coach", tags=["教练端"])


@router.get("/students")
def list_my_students(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """获取当前教练的学员列表"""
    # 查询分配给该教练的成长者
    # 通过 profile.coach_id 关联
    growers = db.query(User).filter(
        User.role == UserRole.GROWER,
        User.is_active == True,
    ).all()

    students = []
    for g in growers:
        profile = g.profile or {}
        # 如果是管理员，显示所有；如果是教练，只显示分配给自己的
        if current_user.role.value != 'admin' and profile.get('coach_id') != current_user.id:
            continue

        if search and search not in (g.full_name or '') and search not in (g.username or ''):
            continue

        # 获取最近的评估
        latest_assessment = db.query(Assessment).filter(
            Assessment.user_id == g.id
        ).order_by(Assessment.created_at.desc()).first()

        risk_level = None
        if latest_assessment and latest_assessment.risk_level:
            risk_level = latest_assessment.risk_level.value

        # 计算活跃天数 (简化: 基于最近评估)
        active_days = 0
        if latest_assessment and latest_assessment.created_at:
            days_since = (datetime.utcnow() - latest_assessment.created_at).days
            active_days = max(0, 7 - days_since)

        students.append({
            "id": g.id,
            "username": g.username,
            "full_name": g.full_name,
            "profile": profile,
            "adherence_rate": getattr(g, 'adherence_rate', 0) or 0,
            "latest_risk": risk_level,
            "active_days": active_days,
            "last_active": latest_assessment.created_at.isoformat() if latest_assessment and latest_assessment.created_at else None,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        })

    return {"students": students, "total": len(students)}


@router.get("/students/{student_id}")
def get_student_detail(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """获取学员详情"""
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    # 获取评估历史
    assessments = db.query(Assessment).filter(
        Assessment.user_id == student_id
    ).order_by(Assessment.created_at.desc()).limit(10).all()

    assessment_list = [
        {
            "id": a.id,
            "assessment_id": a.assessment_id,
            "risk_level": a.risk_level.value if a.risk_level else None,
            "risk_score": a.risk_score,
            "primary_concern": a.primary_concern,
            "status": a.status,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in assessments
    ]

    return {
        "student": {
            "id": student.id,
            "username": student.username,
            "full_name": student.full_name,
            "role": student.role.value,
            "email": student.email,
            "profile": student.profile or {},
            "adherence_rate": getattr(student, 'adherence_rate', 0),
            "created_at": student.created_at.isoformat() if student.created_at else None,
        },
        "assessments": assessment_list,
    }


@router.get("/performance")
def get_my_performance(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """获取教练绩效数据"""
    # 统计负载的学员数
    growers = db.query(User).filter(
        User.role == UserRole.GROWER,
        User.is_active == True,
    ).all()

    my_students = [g for g in growers if (g.profile or {}).get('coach_id') == current_user.id]
    total_students = len(my_students)

    # 学员风险分布
    risk_distribution = {"low": 0, "medium": 0, "high": 0}
    for g in my_students:
        latest = db.query(Assessment).filter(
            Assessment.user_id == g.id
        ).order_by(Assessment.created_at.desc()).first()
        if latest and latest.risk_level:
            level = latest.risk_level.value
            if level in ('R0', 'R1'):
                risk_distribution["low"] += 1
            elif level == 'R2':
                risk_distribution["medium"] += 1
            else:
                risk_distribution["high"] += 1
        else:
            risk_distribution["low"] += 1

    # 平均完成率
    adherence_rates = [getattr(g, 'adherence_rate', 0) or 0 for g in my_students]
    avg_adherence = round(sum(adherence_rates) / max(len(adherence_rates), 1), 1)

    return {
        "total_students": total_students,
        "risk_distribution": risk_distribution,
        "avg_adherence_rate": avg_adherence,
        "coach_name": current_user.full_name or current_user.username,
        "coach_role": current_user.role.value,
    }


@router.get("/students/{student_id}/behavioral-profile")
def get_student_behavioral_profile(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """
    获取学员行为画像（教练完整视图）

    返回:
    - 行为阶段、稳定性、置信度
    - 行为类型 (BPT6) + 人格特征 (BIG5)
    - 心理层级 + 交互模式
    - 领域干预矩阵 (每个领域: 策略/语气/推荐/禁忌)
    - 改变潜力 (CAPACITY 8维度)
    - 风险标记
    - 推荐教练动作
    """
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    # 获取教练视图
    profile_data = _profile_service.get_coach_view(db, student_id)
    if not profile_data:
        raise HTTPException(status_code=404, detail="该学员尚未完成行为评估")

    # 获取干预计划
    profile = _profile_service.get_profile(db, student_id)
    intervention_plan = None
    if profile:
        target_domains = profile.primary_domains or ["nutrition", "exercise", "sleep"]
        plan = _intervention_matcher.match(
            user_id=student_id,
            current_stage=profile.current_stage.value if profile.current_stage else "S0",
            psychological_level=profile.psychological_level.value if profile.psychological_level else "L3",
            bpt6_type=profile.bpt6_type or "mixed",
            spi_score=profile.spi_score or 0,
            target_domains=target_domains,
        )
        intervention_plan = _intervention_matcher.plan_to_dict(plan)

    # 教练推荐动作
    coach_actions = _generate_coach_actions(profile)

    return {
        "student": {
            "id": student.id,
            "username": student.username,
            "full_name": student.full_name,
        },
        "behavioral_profile": profile_data,
        "intervention_plan": intervention_plan,
        "coach_actions": coach_actions,
    }


def _generate_coach_actions(profile) -> list:
    """根据行为画像生成教练推荐动作"""
    if not profile:
        return [{"action": "引导学员完成首次行为评估", "priority": "high"}]

    actions = []
    stage = profile.current_stage.value if profile.current_stage else "S0"
    risk_flags = profile.risk_flags or []

    # 基于阶段的教练动作
    if stage in ("S0", "S1"):
        actions.append({
            "action": "以共情方式建立信任关系，不施加任何行为压力",
            "priority": "high",
        })
        actions.append({
            "action": "倾听学员故事，了解其抗拒原因",
            "priority": "medium",
        })
    elif stage in ("S2", "S3"):
        actions.append({
            "action": "帮助学员设定一个微小的行为目标 (第一步)",
            "priority": "high",
        })
        actions.append({
            "action": "分享类似案例的成功经验，增强信心",
            "priority": "medium",
        })
    elif stage in ("S4", "S5"):
        actions.append({
            "action": "监督行为执行情况，提供正向反馈",
            "priority": "high",
        })
        actions.append({
            "action": "帮助应对行为中断和回退风险",
            "priority": "medium",
        })
    elif stage == "S6":
        actions.append({
            "action": "鼓励学员成为分享者，帮助其他成长者",
            "priority": "medium",
        })

    # 基于风险的教练动作
    if "dropout_risk" in risk_flags:
        actions.insert(0, {
            "action": "紧急: 主动联系学员，了解中断原因，防止流失",
            "priority": "urgent",
        })
    if "relapse_risk" in risk_flags:
        actions.insert(0, {
            "action": "重要: 学员有回退风险，需增加支持频次",
            "priority": "high",
        })

    return actions

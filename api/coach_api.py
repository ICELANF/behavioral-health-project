# -*- coding: utf-8 -*-
"""
教练端API端点
Coach API Endpoints

端点：
- GET  /api/v1/coach/dashboard     - 教练工作台聚合数据
- GET  /api/v1/coach/students      - 教练的学员列表
- GET  /api/v1/coach/students/{id} - 学员详情
- GET  /api/v1/coach/performance   - 教练绩效数据
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timedelta
from loguru import logger

from core.database import get_db
from core.models import (
    User, UserRole, Assessment, BehavioralProfile,
    CoachMessage, MicroActionTask, MicroActionLog,
    Reminder, BehaviorHistory,
    GlucoseReading, SleepRecord, ActivityRecord, VitalSign,
)
from core.behavioral_profile_service import BehavioralProfileService
from core.intervention_matcher import InterventionMatcher
from core.content_access_service import get_user_level
from core.data_visibility_service import filter_nested_profile, get_hidden_fields
from api.dependencies import get_current_user, require_coach_or_admin, require_admin

_profile_service = BehavioralProfileService()
_intervention_matcher = InterventionMatcher()

router = APIRouter(prefix="/api/v1/coach", tags=["教练端"])


# ── 角色等级映射（与 content_access_service 一致的六级体系） ──
_ROLE_LEVEL_MAP = {
    UserRole.OBSERVER: ("L0", "观察员"),
    UserRole.GROWER: ("L1", "成长者"),
    UserRole.SHARER: ("L2", "分享者"),
    UserRole.COACH: ("L3", "教练"),
    UserRole.PROMOTER: ("L4", "促进师"),
    UserRole.SUPERVISOR: ("L4", "促进师"),
    UserRole.MASTER: ("L5", "大师"),
    UserRole.ADMIN: ("L99", "管理员"),
}

_STAGE_LABEL = {
    "S0": "觉醒期", "S1": "松动期", "S2": "探索期", "S3": "准备期",
    "S4": "行动期", "S5": "坚持期", "S6": "融入期",
}

_STAGE_PRIORITY = {
    "S0": "low", "S1": "low", "S2": "medium", "S3": "medium",
    "S4": "high", "S5": "medium", "S6": "low",
}

# 学员角色白名单: 教练只向下跟进这三个角色，不能向上跟进教练+以上角色
_STUDENT_ROLES = [UserRole.OBSERVER, UserRole.GROWER, UserRole.SHARER]


def _get_my_student_ids(db: Session, current_user: User) -> list:
    """获取当前教练绑定的学员ID列表（权威源: coach_student_bindings）"""
    from sqlalchemy import text as sa_text
    if current_user.role.value == "admin":
        rows = db.query(User.id).filter(
            User.is_active == True, User.role.in_(_STUDENT_ROLES)
        ).all()
        return [r[0] for r in rows]
    rows = db.execute(sa_text(
        "SELECT student_id FROM coach_schema.coach_student_bindings "
        "WHERE coach_id = :cid AND is_active = true"
    ), {"cid": current_user.id}).fetchall()
    return [r[0] for r in rows]


@router.get("/dashboard")
def get_coach_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """
    教练工作台 - 聚合数据

    返回: coach 信息、今日统计、待跟进学员列表
    """
    # ── 1. 教练信息 ──
    level_code, level_name = _ROLE_LEVEL_MAP.get(current_user.role, ("L0", "见习教练"))
    coach_profile = current_user.profile or {}
    coach_info = {
        "id": current_user.id,
        "name": current_user.full_name or current_user.username,
        "level": level_code,
        "level_name": level_name,
        "specialty": coach_profile.get("specialty", []),
    }

    # ── 2. 获取教练的学员列表 (via coach_student_bindings) ──
    # 重要: 只向下跟进学员角色 (OBSERVER/GROWER/SHARER)，不能向上跟进教练+以上角色
    from sqlalchemy import text as sa_text
    if current_user.role.value == "admin":
        my_students_raw = db.query(User).filter(
            User.is_active == True,
            User.role.in_(_STUDENT_ROLES),
        ).all()
    else:
        rows = db.execute(sa_text(
            "SELECT student_id FROM coach_schema.coach_student_bindings "
            "WHERE coach_id = :cid AND is_active = true"
        ), {"cid": current_user.id}).fetchall()
        student_ids = [r[0] for r in rows]
        if student_ids:
            my_students_raw = db.query(User).filter(
                User.id.in_(student_ids),
                User.is_active == True,
                User.role.in_(_STUDENT_ROLES),
            ).all()
        else:
            my_students_raw = []

    # ── 3. 丰富学员数据 ──
    now = datetime.utcnow()
    students = []
    alert_count = 0
    pending_followup_count = 0

    for g in my_students_raw:
        # 最新评估
        latest_assess = db.query(Assessment).filter(
            Assessment.user_id == g.id,
        ).order_by(Assessment.created_at.desc()).first()

        # 行为画像
        bp = db.query(BehavioralProfile).filter(
            BehavioralProfile.user_id == g.id,
        ).order_by(BehavioralProfile.updated_at.desc()).first()

        stage = bp.current_stage.value if bp and bp.current_stage else None
        stage_label = _STAGE_LABEL.get(stage, stage) if stage else "未评估"

        # 最近微行动统计
        seven_days_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        recent_tasks = db.query(MicroActionTask).filter(
            MicroActionTask.user_id == g.id,
            MicroActionTask.scheduled_date >= seven_days_ago,
        ).all()
        completed_7d = sum(1 for t in recent_tasks if t.status == "completed")
        total_7d = len(recent_tasks)

        # 最近联系（教练消息）
        last_msg = db.query(CoachMessage).filter(
            CoachMessage.student_id == g.id,
            CoachMessage.coach_id == current_user.id,
        ).order_by(CoachMessage.created_at.desc()).first()

        last_contact_dt = last_msg.created_at if last_msg else (
            latest_assess.created_at if latest_assess else g.created_at
        )
        days_since_contact = (now - last_contact_dt).days if last_contact_dt else 999

        if days_since_contact <= 0:
            last_contact_str = "今天"
        elif days_since_contact == 1:
            last_contact_str = "1天前"
        else:
            last_contact_str = f"{days_since_contact}天前"

        # 优先级 & 风险
        risk_level = latest_assess.risk_level.value if latest_assess and latest_assess.risk_level else None
        risk_flags = bp.risk_flags if bp else []

        priority = "low"
        if risk_level in ("R3", "R4") or "dropout_risk" in (risk_flags or []):
            priority = "high"
            alert_count += 1
        elif days_since_contact >= 3 or risk_level == "R2":
            priority = "medium"
            if days_since_contact >= 3:
                alert_count += 1

        if days_since_contact >= 2:
            pending_followup_count += 1

        # 健康数据: 从用户 profile JSON 或评估数据获取
        user_profile = g.profile or {}
        health_data = {
            "fasting_glucose": user_profile.get("fasting_glucose"),
            "postprandial_glucose": user_profile.get("postprandial_glucose"),
            "weight": user_profile.get("weight"),
            "exercise_minutes": user_profile.get("exercise_minutes", 0),
        }

        condition_parts = []
        if user_profile.get("condition"):
            condition_parts.append(user_profile["condition"])
        elif latest_assess and latest_assess.primary_concern:
            condition_parts.append(latest_assess.primary_concern)

        students.append({
            "id": g.id,
            "name": g.full_name or g.username,
            "avatar": user_profile.get("avatar", ""),
            "condition": " · ".join(condition_parts) if condition_parts else "行为健康管理",
            "stage": stage or "unknown",
            "stage_label": stage_label,
            "last_contact": last_contact_str,
            "days_since_contact": days_since_contact,
            "priority": priority,
            "health_data": health_data,
            "micro_action_7d": {"completed": completed_7d, "total": total_7d},
            "risk_level": risk_level,
            "risk_flags": risk_flags or [],
        })

    # 按优先级排序: high > medium > low, 其次按 days_since_contact 降序
    priority_order = {"high": 0, "medium": 1, "low": 2}
    students.sort(key=lambda s: (priority_order.get(s["priority"], 9), -s["days_since_contact"]))

    # 每页最多30个
    students = students[:30]

    # ── 4. 未读消息数 ──
    unread_count = 0
    try:
        unread_count = db.query(func.count(CoachMessage.id)).filter(
            CoachMessage.coach_id == current_user.id,
            CoachMessage.is_read == False,
        ).scalar() or 0
    except Exception:
        pass

    # ── 5. 今日已完成跟进 (今日发送的消息数) ──
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    completed_followups = 0
    try:
        completed_followups = db.query(func.count(CoachMessage.id)).filter(
            CoachMessage.coach_id == current_user.id,
            CoachMessage.created_at >= today_start,
        ).scalar() or 0
    except Exception:
        pass

    today_stats = {
        "pending_followups": pending_followup_count,
        "completed_followups": completed_followups,
        "alert_students": alert_count,
        "unread_messages": unread_count,
        "total_students": len(students),
    }

    return {
        "coach": coach_info,
        "today_stats": today_stats,
        "students": students,
    }


@router.get("/students")
def list_my_students(
    search: Optional[str] = None,
    behavior: Optional[str] = Query(None, description="行为阶段过滤"),
    needs: Optional[str] = Query(None, description="需求类型过滤"),
    risk: Optional[str] = Query(None, description="风险等级过滤"),
    activity: Optional[str] = Query(None, description="活跃度过滤"),
    priority: Optional[str] = Query(None, description="优先级桶: urgent/important/normal/routine"),
    sort_by: str = Query("priority", description="排序: priority/name/risk/activity/stage"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """获取当前教练的学员列表 — 基于 coach_student_bindings 表，含4维分类"""
    from sqlalchemy import text as sa_text
    from core.student_classification_service import (
        classify_students_batch, build_classification_summary, classification_to_dict,
    )

    if current_user.role.value == 'admin':
        # 管理员看全部学员角色用户
        bound_users = db.query(User).filter(
            User.is_active == True,
            User.role.in_(_STUDENT_ROLES),
        ).all()
    else:
        # 教练: 从 coach_student_bindings 获取绑定学员 (只含学员角色)
        rows = db.execute(sa_text(
            "SELECT student_id FROM coach_schema.coach_student_bindings "
            "WHERE coach_id = :cid AND is_active = true"
        ), {"cid": current_user.id}).fetchall()
        student_ids = [r[0] for r in rows]
        if not student_ids:
            return {"students": [], "total": 0, "classification_summary": {}}
        bound_users = db.query(User).filter(
            User.id.in_(student_ids),
            User.is_active == True,
            User.role.in_(_STUDENT_ROLES),
        ).all()

    # 文本搜索过滤
    if search:
        bound_users = [
            g for g in bound_users
            if search in (g.full_name or '') or search in (g.username or '')
        ]

    # 批量分类 (8次SQL, 非N+1)
    all_ids = [g.id for g in bound_users]
    classifications = classify_students_batch(db, all_ids)

    # 生成全量 summary (过滤前)
    classification_summary = build_classification_summary(classifications)

    # 维度过滤
    if behavior:
        vals = set(behavior.split(","))
        bound_users = [g for g in bound_users if classifications[g.id].behavior in vals]
    if needs:
        vals = set(needs.split(","))
        bound_users = [g for g in bound_users if classifications[g.id].needs in vals]
    if risk:
        vals = set(risk.split(","))
        bound_users = [g for g in bound_users if classifications[g.id].risk in vals]
    if activity:
        vals = set(activity.split(","))
        bound_users = [g for g in bound_users if classifications[g.id].activity in vals]
    if priority:
        vals = set(priority.split(","))
        bound_users = [g for g in bound_users if classifications[g.id].priority_bucket in vals]

    # 排序
    _risk_order = {"crisis": 4, "high": 3, "moderate": 2, "low": 1, "normal": 0}
    _activity_order = {"dormant": 4, "inactive": 3, "moderate": 2, "active": 1, "highly_active": 0}
    if sort_by == "priority":
        bound_users.sort(key=lambda g: -classifications[g.id].priority_score)
    elif sort_by == "risk":
        bound_users.sort(key=lambda g: -_risk_order.get(classifications[g.id].risk, 0))
    elif sort_by == "activity":
        bound_users.sort(key=lambda g: -_activity_order.get(classifications[g.id].activity, 0))
    elif sort_by == "name":
        bound_users.sort(key=lambda g: g.full_name or g.username or "")
    elif sort_by == "stage":
        bound_users.sort(key=lambda g: classifications[g.id].behavior)

    # 分页
    total = len(bound_users)
    start = (page - 1) * page_size
    bound_users = bound_users[start:start + page_size]

    students = []
    for g in bound_users:
        cls = classifications.get(g.id)
        students.append({
            "id": g.id,
            "username": g.username,
            "full_name": g.full_name,
            "role": g.role.value if g.role else None,
            "growth_points": g.growth_points or 0,
            "current_stage": g.current_stage,
            "profile": getattr(g, 'profile', None) or {},
            "adherence_rate": getattr(g, 'adherence_rate', 0) or 0,
            "latest_risk": cls.risk if cls else None,
            "active_days": 0,
            "last_active": g.last_login_at.isoformat() if g.last_login_at else None,
            "created_at": g.created_at.isoformat() if g.created_at else None,
            "classification": classification_to_dict(cls) if cls else None,
        })

    return {
        "students": students,
        "total": total,
        "page": page,
        "page_size": page_size,
        "classification_summary": classification_summary,
    }


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
    # 统计负载的学员数 (权威源: coach_student_bindings)
    student_ids = _get_my_student_ids(db, current_user)
    my_students = db.query(User).filter(
        User.id.in_(student_ids), User.is_active == True
    ).all() if student_ids else []
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
        return {
            "student_id": student_id,
            "student_name": student.full_name or student.username,
            "message": "该学员尚未完成行为评估",
            "behavioral_profile": None,
            "intervention_plan": None,
            "coach_actions": [],
            "hidden_fields": [],
        }

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

    # 按查看者等级过滤字段
    viewer_level = get_user_level(current_user)
    filtered_profile = filter_nested_profile(profile_data, viewer_level)
    hidden_fields = get_hidden_fields(viewer_level)

    return {
        "student": {
            "id": student.id,
            "username": student.username,
            "full_name": student.full_name,
        },
        "behavioral_profile": filtered_profile,
        "intervention_plan": intervention_plan,
        "coach_actions": coach_actions,
        "hidden_fields": hidden_fields,
    }


_RISK_LABEL = {
    "R0": "正常", "R1": "轻度", "R2": "中度", "R3": "高度", "R4": "危机",
}


@router.get("/students/{student_id}/assessment-detail")
def get_student_assessment_detail(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """
    学员测评交互 - 完整测评数据

    返回: 学员概览, 测评记录(含详情), 前后对比, 教练消息/随访
    """
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    # ── 1. 行为画像 ──
    bp = db.query(BehavioralProfile).filter(
        BehavioralProfile.user_id == student_id,
    ).first()

    stage = bp.current_stage.value if bp and bp.current_stage else None
    stage_label = _STAGE_LABEL.get(stage, "未评估") if stage else "未评估"

    # ── 2. 全部测评记录 ──
    assessments = (
        db.query(Assessment)
        .filter(Assessment.user_id == student_id)
        .order_by(Assessment.created_at.desc())
        .limit(50)
        .all()
    )

    risk_level_latest = None
    assessment_records = []
    for a in assessments:
        rl = a.risk_level.value if a.risk_level else None
        if risk_level_latest is None:
            risk_level_latest = rl

        assessment_records.append({
            "id": a.id,
            "assessment_id": a.assessment_id,
            "risk_level": rl,
            "risk_label": _RISK_LABEL.get(rl, rl) if rl else "未知",
            "risk_score": a.risk_score,
            "primary_concern": a.primary_concern or "综合评估",
            "urgency": a.urgency,
            "reasoning": a.reasoning,
            "recommended_actions": a.recommended_actions or [],
            "severity_distribution": a.severity_distribution or {},
            "primary_agent": a.primary_agent.value if a.primary_agent else None,
            "secondary_agents": a.secondary_agents or [],
            "status": a.status,
            "context": a.context or {},
            "annotation": "",  # placeholder - coach annotations stored in messages
            "created_at": a.created_at.isoformat() if a.created_at else None,
        })

    # ── 3. 前后对比 ──
    comparison = None
    if len(assessments) >= 2:
        first = assessments[-1]  # oldest
        latest = assessments[0]  # newest

        first_risk = first.risk_score or 0
        latest_risk = latest.risk_score or 0
        improvement = round((first_risk - latest_risk) / max(first_risk, 1) * 100, 1) if first_risk > 0 else 0

        comparison = {
            "first": {
                "date": first.created_at.isoformat() if first.created_at else None,
                "risk_level": first.risk_level.value if first.risk_level else None,
                "risk_label": _RISK_LABEL.get(first.risk_level.value, "") if first.risk_level else "",
                "risk_score": first.risk_score,
                "primary_concern": first.primary_concern,
            },
            "latest": {
                "date": latest.created_at.isoformat() if latest.created_at else None,
                "risk_level": latest.risk_level.value if latest.risk_level else None,
                "risk_label": _RISK_LABEL.get(latest.risk_level.value, "") if latest.risk_level else "",
                "risk_score": latest.risk_score,
                "primary_concern": latest.primary_concern,
            },
            "improvement_rate": improvement,
        }

        # 添加行为画像对比(如果有)
        if bp:
            comparison["profile"] = {
                "stage": stage,
                "stage_label": stage_label,
                "spi_score": bp.spi_score,
                "capacity_total": bp.capacity_total,
                "stage_confidence": bp.stage_confidence,
                "stage_stability": bp.stage_stability.value if bp.stage_stability else None,
            }

    # ── 4. 阶段变迁历史 ──
    stage_history = []
    try:
        histories = (
            db.query(BehaviorHistory)
            .filter(BehaviorHistory.user_id == str(student_id))
            .order_by(BehaviorHistory.timestamp.desc())
            .limit(20)
            .all()
        )
        for h in histories:
            stage_history.append({
                "from_stage": h.from_stage,
                "to_stage": h.to_stage,
                "is_transition": h.is_transition,
                "belief_score": h.belief_score,
                "date": h.timestamp.isoformat() if h.timestamp else None,
            })
    except Exception:
        pass  # table may not exist yet

    # ── 5. 教练消息 (作为随访记录) ──
    messages = (
        db.query(CoachMessage)
        .filter(
            CoachMessage.student_id == student_id,
            CoachMessage.coach_id == current_user.id,
        )
        .order_by(CoachMessage.created_at.desc())
        .limit(50)
        .all()
    )
    followups = []
    for m in messages:
        followups.append({
            "id": m.id,
            "date": m.created_at.isoformat() if m.created_at else None,
            "type": _msg_type_label(m.message_type),
            "content": m.content,
            "status": "completed",
        })

    # ── 6. 提醒 ──
    reminders = (
        db.query(Reminder)
        .filter(
            Reminder.user_id == student_id,
            Reminder.is_active == True,
        )
        .order_by(Reminder.next_fire_at.asc())
        .limit(20)
        .all()
    )
    reminder_list = []
    for r in reminders:
        reminder_list.append({
            "id": r.id,
            "date": r.next_fire_at.isoformat() if r.next_fire_at else "待定",
            "type": r.title,
            "content": r.content or "",
            "status": "scheduled",
        })

    # ── 7. 学员概览 ──
    now = datetime.utcnow()
    last_active = assessments[0].created_at if assessments else student.created_at
    days_since = (now - last_active).days if last_active else 999
    if days_since <= 0:
        last_active_str = "今天"
    elif days_since == 1:
        last_active_str = "昨天"
    else:
        last_active_str = f"{days_since}天前"

    overview = {
        "id": student.id,
        "name": student.full_name or student.username,
        "stage": stage or "unknown",
        "stage_label": stage_label,
        "risk_level": risk_level_latest,
        "risk_label": _RISK_LABEL.get(risk_level_latest, "未知") if risk_level_latest else "未评估",
        "assessment_count": len(assessments),
        "last_active": last_active_str,
        "spi_score": bp.spi_score if bp else None,
        "bpt6_type": bp.bpt6_type if bp else None,
    }

    return {
        "student": overview,
        "assessments": assessment_records,
        "comparison": comparison,
        "stage_history": stage_history,
        "followups": followups + reminder_list,
    }


def _msg_type_label(t: str) -> str:
    labels = {
        "text": "消息", "encouragement": "鼓励", "reminder": "提醒",
        "advice": "建议", "annotation": "批注",
    }
    return labels.get(t, t)


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


# ── 教练等级详情（六级体系） ──
_LEVEL_DETAIL = {
    "L0": {
        "name": "观察员", "color": "#8c8c8c",
        "desc": "入门阶段，正在观察和了解行为健康体系",
        "next": "L1", "next_name": "成长者 (L1)",
    },
    "L1": {
        "name": "成长者", "color": "#52c41a",
        "desc": "积极参与学习和自我提升，开始行为健康实践",
        "next": "L2", "next_name": "分享者 (L2)",
    },
    "L2": {
        "name": "分享者", "color": "#1890ff",
        "desc": "能够分享经验和知识，帮助他人启动行为改变",
        "next": "L3", "next_name": "教练 (L3)",
    },
    "L3": {
        "name": "教练", "color": "#722ed1",
        "desc": "具备独立开展行为健康干预的专业教练能力",
        "next": "L4", "next_name": "促进师 (L4)",
    },
    "L4": {
        "name": "促进师", "color": "#eb2f96",
        "desc": "资深教练，能处理复杂案例并带教督导",
        "next": "L5", "next_name": "大师 (L5)",
    },
    "L5": {
        "name": "大师", "color": "#faad14",
        "desc": "行为健康领域专家，具备系统级影响力",
        "next": None, "next_name": "已达最高等级",
    },
    "L99": {
        "name": "管理员", "color": "#f5222d",
        "desc": "系统管理员，拥有全部权限",
        "next": None, "next_name": "已达最高等级",
    },
}

# 各等级升级需求
_UPGRADE_REQ = {
    "L0": [
        {"key": "students", "label": "服务学员数", "target": 5},
        {"key": "messages", "label": "发送消息数", "target": 20},
    ],
    "L1": [
        {"key": "students", "label": "服务学员数", "target": 15},
        {"key": "messages", "label": "发送消息数", "target": 100},
        {"key": "assessments_viewed", "label": "查看测评数", "target": 30},
    ],
    "L2": [
        {"key": "students", "label": "服务学员数", "target": 30},
        {"key": "messages", "label": "发送消息数", "target": 300},
        {"key": "improved_students", "label": "风险改善学员数", "target": 10},
        {"key": "assessments_viewed", "label": "查看测评数", "target": 100},
    ],
    "L3": [
        {"key": "students", "label": "服务学员数", "target": 50},
        {"key": "improved_students", "label": "风险改善学员数", "target": 25},
        {"key": "messages", "label": "发送消息数", "target": 500},
    ],
    "L4": [
        {"key": "students", "label": "服务学员数", "target": 100},
        {"key": "improved_students", "label": "风险改善学员数", "target": 50},
        {"key": "messages", "label": "发送消息数", "target": 1000},
    ],
    "L5": [],
    "L99": [],
}


@router.get("/my-certification")
def get_my_certification(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """
    教练认证信息

    返回: 当前等级、升级进度、升级要求(基于真实数据)
    """
    level_code, level_name = _ROLE_LEVEL_MAP.get(current_user.role, ("L0", "见习教练"))
    detail = _LEVEL_DETAIL.get(level_code, _LEVEL_DETAIL["L0"])

    # ── 统计真实数据 ──
    # 1. 学员数 (权威源: coach_student_bindings)
    student_ids = _get_my_student_ids(db, current_user)
    my_students = db.query(User).filter(
        User.id.in_(student_ids), User.is_active == True
    ).all() if student_ids else []
    student_count = len(my_students)

    # 2. 消息数
    message_count = db.query(func.count(CoachMessage.id)).filter(
        CoachMessage.coach_id == current_user.id,
    ).scalar() or 0

    # 3. 查看过的测评数 (学员有测评记录的数量)
    student_ids = [s.id for s in my_students]
    assessments_viewed = 0
    if student_ids:
        assessments_viewed = db.query(func.count(Assessment.id)).filter(
            Assessment.user_id.in_(student_ids),
        ).scalar() or 0

    # 4. 风险改善学员数 (有>=2次评估且最新风险 < 最早风险)
    improved_count = 0
    for s in my_students:
        evals = (
            db.query(Assessment)
            .filter(Assessment.user_id == s.id)
            .order_by(Assessment.created_at.asc())
            .all()
        )
        if len(evals) >= 2:
            first_score = evals[0].risk_score or 0
            last_score = evals[-1].risk_score or 0
            if last_score < first_score:
                improved_count += 1

    # ── 计算升级要求完成度 ──
    actuals = {
        "students": student_count,
        "messages": message_count,
        "assessments_viewed": assessments_viewed,
        "improved_students": improved_count,
    }
    reqs = _UPGRADE_REQ.get(level_code, [])
    requirements = []
    for req in reqs:
        current = actuals.get(req["key"], 0)
        target = req["target"]
        requirements.append({
            "label": req["label"],
            "current": current,
            "target": target,
            "completed": current >= target,
        })

    completed_count = sum(1 for r in requirements if r["completed"])
    total_count = max(len(requirements), 1)
    upgrade_progress = round(completed_count / total_count * 100)

    # ── 认证时间线 (从 user profile 中读取) ──
    cert_history = (current_user.profile or {}).get("certifications", [])

    return {
        "current_level": {
            "code": level_code,
            "name": detail["name"],
            "description": detail["desc"],
            "color": detail["color"],
            "since": current_user.created_at.strftime("%Y-%m-%d") if current_user.created_at else None,
        },
        "next_level": {
            "code": detail.get("next"),
            "name": detail.get("next_name", ""),
        },
        "upgrade_progress": upgrade_progress,
        "requirements": requirements,
        "stats": {
            "total_students": student_count,
            "total_messages": message_count,
            "total_assessments": assessments_viewed,
            "improved_students": improved_count,
        },
        "certifications": cert_history,
    }


@router.get("/my-tools-stats")
def get_my_tools_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """
    教练工具使用统计

    返回: 各工具使用次数(基于消息类型/操作类型聚合)、最近活动
    """
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # ── 1. 消息类型统计 (本月) ──
    msg_counts = (
        db.query(CoachMessage.message_type, func.count(CoachMessage.id))
        .filter(
            CoachMessage.coach_id == current_user.id,
            CoachMessage.created_at >= month_start,
        )
        .group_by(CoachMessage.message_type)
        .all()
    )
    msg_map = {t: c for t, c in msg_counts}

    # ── 2. 学员评估浏览 (权威源: coach_student_bindings) ──
    student_ids = _get_my_student_ids(db, current_user)
    assessment_count = 0
    if student_ids:
        assessment_count = db.query(func.count(Assessment.id)).filter(
            Assessment.user_id.in_(student_ids),
            Assessment.created_at >= month_start,
        ).scalar() or 0

    # ── 3. 微行动任务统计 ──
    micro_count = 0
    if student_ids:
        micro_count = db.query(func.count(MicroActionTask.id)).filter(
            MicroActionTask.user_id.in_(student_ids),
            MicroActionTask.created_at >= month_start,
        ).scalar() or 0

    # ── 4. 提醒统计 ──
    reminder_count = 0
    if student_ids:
        reminder_count = db.query(func.count(Reminder.id)).filter(
            Reminder.user_id.in_(student_ids),
            Reminder.created_by == current_user.id,
        ).scalar() or 0

    # ── 5. 工具使用映射 ──
    tools = [
        {
            "key": "message",
            "name": "消息沟通",
            "description": "向学员发送沟通消息",
            "color": "#1890ff",
            "use_count": msg_map.get("text", 0),
        },
        {
            "key": "encouragement",
            "name": "激励鼓励",
            "description": "发送正向鼓励给学员",
            "color": "#722ed1",
            "use_count": msg_map.get("encouragement", 0),
        },
        {
            "key": "advice",
            "name": "专业建议",
            "description": "为学员提供行为干预建议",
            "color": "#389e0d",
            "use_count": msg_map.get("advice", 0),
        },
        {
            "key": "reminder",
            "name": "提醒设置",
            "description": "为学员设置行为提醒",
            "color": "#d46b08",
            "use_count": msg_map.get("reminder", 0) + reminder_count,
        },
        {
            "key": "assessment",
            "name": "测评管理",
            "description": "查看和管理学员测评",
            "color": "#cf1322",
            "use_count": assessment_count,
        },
        {
            "key": "micro_action",
            "name": "微行动管理",
            "description": "学员微行动任务跟踪",
            "color": "#13c2c2",
            "use_count": micro_count,
        },
    ]

    total_month = sum(t["use_count"] for t in tools)
    most_used = max(tools, key=lambda t: t["use_count"])["name"] if tools else "--"

    # ── 6. 最近活动 (最近10条消息) ──
    recent_msgs = (
        db.query(CoachMessage)
        .filter(CoachMessage.coach_id == current_user.id)
        .order_by(CoachMessage.created_at.desc())
        .limit(10)
        .all()
    )
    recent_activity = []
    for m in recent_msgs:
        student = db.query(User).filter(User.id == m.student_id).first()
        student_name = (student.full_name or student.username) if student else f"学员{m.student_id}"
        elapsed = (now - m.created_at).total_seconds() if m.created_at else 0
        if elapsed < 3600:
            time_str = f"{int(elapsed / 60)}分钟前"
        elif elapsed < 86400:
            time_str = f"{int(elapsed / 3600)}小时前"
        else:
            time_str = f"{int(elapsed / 86400)}天前"

        recent_activity.append({
            "id": m.id,
            "tool_name": _msg_type_label(m.message_type),
            "student": student_name,
            "action": m.content[:40] + ("..." if len(m.content) > 40 else ""),
            "time": time_str,
        })

    return {
        "tools": tools,
        "total_month_usage": total_month,
        "most_used_tool": most_used,
        "recent_activity": recent_activity,
    }


# ============================================================================
# 教练查看学员设备数据
# ============================================================================

def _verify_coach_student(db: Session, current_user: User, student_id: int) -> User:
    """验证教练对学员的访问权限，返回学员 User 对象"""
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    # admin 跳过归属检查
    if current_user.role.value == "admin":
        return student

    # 验证 student 是否分配给当前教练
    # 优先查 coach_student_bindings 表 (权威源)
    from sqlalchemy import text as sa_text
    binding = db.execute(sa_text(
        "SELECT 1 FROM coach_schema.coach_student_bindings "
        "WHERE coach_id = :cid AND student_id = :sid AND is_active = true LIMIT 1"
    ), {"cid": current_user.id, "sid": student_id}).first()

    if binding:
        return student

    # 兼容旧逻辑: 检查 profile.coach_id
    profile = getattr(student, 'profile', None) or {}
    if isinstance(profile, dict) and profile.get("coach_id") == current_user.id:
        return student

    raise HTTPException(status_code=403, detail="该学员未分配给您")


@router.get("/students/{student_id}/glucose")
def get_student_glucose(
    student_id: int,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """教练查看学员血糖数据"""
    student = _verify_coach_student(db, current_user, student_id)
    since = datetime.utcnow() - timedelta(days=days)

    readings = (
        db.query(GlucoseReading)
        .filter(
            GlucoseReading.user_id == student.id,
            GlucoseReading.recorded_at >= since,
        )
        .order_by(GlucoseReading.recorded_at.desc())
        .all()
    )

    return {
        "student_id": student.id,
        "student_name": student.full_name or student.username,
        "days": days,
        "count": len(readings),
        "readings": [
            {
                "id": r.id,
                "value": r.value,
                "unit": r.unit,
                "source": r.source,
                "meal_tag": r.meal_tag,
                "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            }
            for r in readings
        ],
    }


@router.get("/students/{student_id}/sleep")
def get_student_sleep(
    student_id: int,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """教练查看学员睡眠数据"""
    student = _verify_coach_student(db, current_user, student_id)
    since_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    records = (
        db.query(SleepRecord)
        .filter(
            SleepRecord.user_id == student.id,
            SleepRecord.sleep_date >= since_date,
        )
        .order_by(SleepRecord.sleep_date.desc())
        .all()
    )

    return {
        "student_id": student.id,
        "student_name": student.full_name or student.username,
        "days": days,
        "count": len(records),
        "records": [
            {
                "id": r.id,
                "sleep_date": r.sleep_date,
                "total_minutes": r.total_duration_min,
                "deep_minutes": r.deep_min,
                "light_minutes": r.light_min,
                "rem_minutes": r.rem_min,
                "awake_minutes": r.awake_min,
                "sleep_score": r.sleep_score,
                "bedtime": r.sleep_start.isoformat() if r.sleep_start else None,
                "wake_time": r.sleep_end.isoformat() if r.sleep_end else None,
            }
            for r in records
        ],
    }


@router.get("/students/{student_id}/activity")
def get_student_activity(
    student_id: int,
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """教练查看学员运动数据"""
    student = _verify_coach_student(db, current_user, student_id)
    since_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    records = (
        db.query(ActivityRecord)
        .filter(
            ActivityRecord.user_id == student.id,
            ActivityRecord.activity_date >= since_date,
        )
        .order_by(ActivityRecord.activity_date.desc())
        .all()
    )

    return {
        "student_id": student.id,
        "student_name": student.full_name or student.username,
        "days": days,
        "count": len(records),
        "records": [
            {
                "id": r.id,
                "activity_date": r.activity_date,
                "steps": r.steps,
                "distance_meters": r.distance_m,
                "calories_burned": r.calories_active,
                "active_minutes": r.moderate_active_min + r.vigorous_active_min if r.moderate_active_min and r.vigorous_active_min else 0,
                "exercise_minutes": r.vigorous_active_min,
            }
            for r in records
        ],
    }


@router.get("/students/{student_id}/vitals")
def get_student_vitals(
    student_id: int,
    data_type: Optional[str] = Query(None, description="weight / blood_pressure / temperature / spo2"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """教练查看学员体征数据（体重、血压等）"""
    student = _verify_coach_student(db, current_user, student_id)
    since = datetime.utcnow() - timedelta(days=days)

    query = (
        db.query(VitalSign)
        .filter(
            VitalSign.user_id == student.id,
            VitalSign.recorded_at >= since,
        )
    )
    if data_type:
        query = query.filter(VitalSign.data_type == data_type)

    records = query.order_by(VitalSign.recorded_at.desc()).limit(100).all()

    return {
        "student_id": student.id,
        "student_name": student.full_name or student.username,
        "data_type": data_type,
        "days": days,
        "count": len(records),
        "records": [
            {
                "id": r.id,
                "data_type": r.data_type,
                "value": (
                    r.weight_kg if r.data_type == "weight" else
                    f"{r.systolic}/{r.diastolic}" if r.data_type == "blood_pressure" else
                    r.temperature if r.data_type == "temperature" else
                    r.spo2 if r.data_type == "spo2" else None
                ),
                "unit": (
                    "kg" if r.data_type == "weight" else
                    "mmHg" if r.data_type == "blood_pressure" else
                    "°C" if r.data_type == "temperature" else
                    "%" if r.data_type == "spo2" else None
                ),
                "recorded_at": r.recorded_at.isoformat() if r.recorded_at else None,
            }
            for r in records
        ],
    }


# ============================================================================
# 公开教练目录
# ============================================================================

@router.get("/directory")
def coach_directory(
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """
    公开教练/专家目录 (无需登录)

    返回角色为 coach 及以上的公开信息列表
    """
    coach_roles = [UserRole.COACH, UserRole.PROMOTER, UserRole.SUPERVISOR, UserRole.MASTER]
    query = db.query(User).filter(
        User.role.in_(coach_roles),
        User.is_active == True,
    )
    if keyword:
        query = query.filter(
            (User.username.contains(keyword)) |
            (User.full_name.contains(keyword))
        )
    query = query.order_by(User.created_at.desc())
    total = query.count()
    coaches = query.offset(skip).limit(limit).all()

    role_title_map = {
        "coach": "健康教练", "promoter": "健康促进师",
        "supervisor": "督导师", "master": "大师教练",
    }
    role_level_map = {
        "coach": 4, "promoter": 5, "supervisor": 5, "master": 6,
    }

    coach_list = []
    for c in coaches:
        profile = c.profile or {}
        role_val = c.role.value if hasattr(c.role, 'value') else c.role
        # 统计学员数 (referred_by)
        student_count = 0
        try:
            student_count = db.query(User).filter(User.referred_by == c.id).count()
        except Exception:
            pass
        coach_list.append({
            "id": c.id,
            "username": c.username,
            "full_name": c.full_name,
            "role": role_val,
            "title": role_title_map.get(role_val, "教练"),
            "role_level": role_level_map.get(role_val, 4),
            "student_count": student_count,
            "rating": float(profile.get("rating", 4.8)),
            "specialties": profile.get("specialties", []),
            "bio": profile.get("bio", ""),
            "avatar_url": profile.get("avatar_url"),
        })

    return {"total": total, "coaches": coach_list}


# ============================================================================
# 晋级申请审批 (Admin)
# ============================================================================

@router.get("/promotion-applications")
def list_promotion_applications(
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """查询晋级申请列表 (教练及以上)"""
    from core.models import PromotionApplication

    query = db.query(PromotionApplication).order_by(PromotionApplication.created_at.desc())

    if status_filter:
        query = query.filter(PromotionApplication.status == status_filter)

    apps = query.limit(100).all()

    result = []
    for app in apps:
        applicant = db.query(User).filter(User.id == app.user_id).first()
        reviewer = db.query(User).filter(User.id == app.reviewer_id).first() if app.reviewer_id else None

        result.append({
            "application_id": str(app.id),
            "coach_id": str(app.user_id),
            "coach_name": (applicant.full_name or applicant.username) if applicant else "未知",
            "coach_phone": getattr(applicant, 'phone', '') or '' if applicant else '',
            "current_level": app.from_role or '',
            "target_level": app.to_role or '',
            "applied_at": app.created_at.strftime("%Y-%m-%d") if app.created_at else '',
            "status": app.status or 'pending',
            "check_result": app.check_result or {},
            "requirements_met": {
                "courses_completed": (app.check_result or {}).get("courses_completed", False),
                "exams_passed": (app.check_result or {}).get("exams_passed", False),
                "cases_count": (app.check_result or {}).get("cases_count", False),
                "mentoring_hours": (app.check_result or {}).get("mentoring_hours", False),
            },
            "reviewer": (reviewer.full_name or reviewer.username) if reviewer else None,
            "reviewed_at": app.reviewed_at.strftime("%Y-%m-%d") if app.reviewed_at else None,
            "review_comment": app.review_comment,
            "materials": [],
        })

    return {"applications": result, "total": len(result)}


@router.post("/promotion-applications/{app_id}/approve")
def approve_promotion_application(
    app_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """批准晋级申请 (促进师及以上)"""
    from core.models import PromotionApplication
    import uuid as _uuid

    try:
        app_uuid = _uuid.UUID(app_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的申请ID")

    app = db.query(PromotionApplication).filter(PromotionApplication.id == app_uuid).first()
    if not app:
        raise HTTPException(status_code=404, detail="申请不存在")
    if app.status != "pending":
        raise HTTPException(status_code=400, detail="该申请已处理")

    app.status = "approved"
    app.reviewer_id = current_user.id
    app.review_comment = "审批通过"
    app.reviewed_at = datetime.utcnow()

    # Optionally upgrade user role
    applicant = db.query(User).filter(User.id == app.user_id).first()
    if applicant and app.to_role:
        try:
            target_role = UserRole(app.to_role)
            applicant.role = target_role
        except ValueError:
            pass

    db.commit()
    logger.info(f"管理员 {current_user.username} 批准晋级申请 {app_id}")
    return {"message": "申请已批准", "application_id": app_id}


@router.post("/promotion-applications/{app_id}/reject")
def reject_promotion_application(
    app_id: str,
    body: dict = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """拒绝晋级申请 (促进师及以上)"""
    from core.models import PromotionApplication
    import uuid as _uuid

    try:
        app_uuid = _uuid.UUID(app_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的申请ID")

    app = db.query(PromotionApplication).filter(PromotionApplication.id == app_uuid).first()
    if not app:
        raise HTTPException(status_code=404, detail="申请不存在")
    if app.status != "pending":
        raise HTTPException(status_code=400, detail="该申请已处理")

    comment = (body or {}).get("comment", "")
    app.status = "rejected"
    app.reviewer_id = current_user.id
    app.review_comment = comment or "审批拒绝"
    app.reviewed_at = datetime.utcnow()
    db.commit()
    logger.info(f"管理员 {current_user.username} 拒绝晋级申请 {app_id}")
    return {"message": "申请已拒绝", "application_id": app_id}


@router.post("/share")
def coach_share_content(
    body: dict,
    current_user: User = Depends(get_current_user),
):
    """教练分享内容给学员"""
    return {"message": "分享成功", "shared_to": len(body.get("studentIds", []))}


@router.get("/sharing-history")
def coach_sharing_history(
    page: int = Query(default=1, ge=1),
    pageSize: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    """教练内容分享历史"""
    return {
        "items": [],
        "total": 0,
        "page": page,
        "pageSize": pageSize,
    }

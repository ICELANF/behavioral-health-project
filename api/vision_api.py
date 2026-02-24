# -*- coding: utf-8 -*-
"""
VisionGuard 视力行为保护 API — 14 个端点

路由前缀: /api/v1/vision
标签: VisionGuard · 视力行为保护

端点:
  POST   /log                   行为打卡 (UPSERT by user_id+log_date)
  GET    /log/me                查询我的行为日志
  GET    /log/{user_id}         查询指定用户日志 (教练/监护人)
  GET    /goals/me              查询我的目标
  PUT    /goals/me              更新我的目标
  POST   /guardian/bind         创建监护关系
  GET    /guardian/students     查询我监护的学生
  GET    /guardian/guardians    查询我的监护人
  DELETE /guardian/{binding_id} 解除监护关系
  GET    /profile/me            我的视力档案
  PUT    /profile/me            更新视力档案
  POST   /exam                  录入视力检查记录
  GET    /exam/{user_id}        查询检查记录
  GET    /dashboard/{user_id}   视力保护仪表盘
"""
from datetime import date, datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, validator
from sqlalchemy.orm import Session
from loguru import logger

from core.database import get_db
from api.dependencies import get_current_user, require_coach_or_admin
from core.models import User
from core.vision_service import (
    VisionBehaviorLog, VisionBehaviorGoal, VisionExamRecord,
    VisionGuardianBinding, VisionProfile,
    calc_behavior_score, build_instant_message,
    get_or_create_goal, get_or_create_profile,
    get_guardian_students, get_student_guardians,
    assess_vision_risk, generate_weekly_report,
)

router = APIRouter(prefix="/api/v1/vision", tags=["VisionGuard · 视力行为保护"])


# ══════════════════════════════════════════
# Pydantic Schemas
# ══════════════════════════════════════════

class VisionBehaviorLogInput(BaseModel):
    log_date: Optional[str] = None  # YYYY-MM-DD, 默认今天
    outdoor_minutes: int = 0
    screen_sessions: int = 0
    screen_total_minutes: int = 0
    eye_exercise_done: bool = False
    lutein_intake_mg: float = 0.0
    sleep_minutes: int = 0
    input_source: str = "manual"
    notes: Optional[str] = None

    @validator("outdoor_minutes", "screen_sessions", "screen_total_minutes", "sleep_minutes", pre=True, always=True)
    def default_int(cls, v):
        return v if v is not None else 0

    @validator("lutein_intake_mg", pre=True, always=True)
    def default_float(cls, v):
        return v if v is not None else 0.0


class GuardianBindInput(BaseModel):
    student_user_id: int
    relationship: str = "parent"
    notify_risk_threshold: str = "watch"
    can_input_behavior: bool = True


class VisionExamInput(BaseModel):
    user_id: Optional[int] = None  # 默认自己
    exam_date: str  # YYYY-MM-DD
    left_eye_sph: Optional[float] = None
    right_eye_sph: Optional[float] = None
    left_eye_cyl: Optional[float] = None
    right_eye_cyl: Optional[float] = None
    left_eye_axial_len: Optional[float] = None
    right_eye_axial_len: Optional[float] = None
    left_eye_va: Optional[float] = None
    right_eye_va: Optional[float] = None
    exam_type: str = "routine"
    examiner_name: Optional[str] = None
    institution: Optional[str] = None
    notes: Optional[str] = None


class VisionProfileInput(BaseModel):
    is_vision_student: Optional[bool] = None
    myopia_onset_age: Optional[int] = None
    ttm_vision_stage: Optional[str] = None
    notes: Optional[str] = None


class VisionGoalInput(BaseModel):
    outdoor_target_min: Optional[int] = None
    screen_session_limit: Optional[int] = None
    screen_daily_limit: Optional[int] = None
    lutein_target_mg: Optional[float] = None
    sleep_target_min: Optional[int] = None
    auto_adjust: Optional[bool] = None


# ══════════════════════════════════════════
# 1. 行为打卡
# ══════════════════════════════════════════

@router.post("/log", summary="行为打卡 (UPSERT)")
def submit_behavior_log(
    data: VisionBehaviorLogInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """行为打卡 — UPSERT by user_id + log_date, 返回评分 + 即时反馈"""
    log_date_str = data.log_date or date.today().isoformat()
    try:
        log_date_val = date.fromisoformat(log_date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="log_date 格式应为 YYYY-MM-DD")

    # UPSERT
    log = (
        db.query(VisionBehaviorLog)
        .filter(
            VisionBehaviorLog.user_id == current_user.id,
            VisionBehaviorLog.log_date == log_date_val,
        )
        .first()
    )
    if not log:
        log = VisionBehaviorLog(user_id=current_user.id, log_date=log_date_val)
        db.add(log)

    log.outdoor_minutes = data.outdoor_minutes
    log.screen_sessions = data.screen_sessions
    log.screen_total_minutes = data.screen_total_minutes
    log.eye_exercise_done = data.eye_exercise_done
    log.lutein_intake_mg = data.lutein_intake_mg
    log.sleep_minutes = data.sleep_minutes
    log.input_source = data.input_source
    log.notes = data.notes
    log.updated_at = datetime.utcnow()

    # 计算评分
    goal = get_or_create_goal(db, current_user.id)
    score = calc_behavior_score(log, goal)
    log.behavior_score = score

    db.commit()
    db.refresh(log)

    # 获取 TTM 阶段
    profile = db.query(VisionProfile).filter(VisionProfile.user_id == current_user.id).first()
    ttm_stage = profile.ttm_vision_stage if profile else "S0"

    feedback = build_instant_message(log, score, goal, ttm_stage)

    return {
        "log_id": log.id,
        "log_date": str(log.log_date),
        "behavior_score": score,
        "feedback": feedback,
    }


# ══════════════════════════════════════════
# 2-3. 查询行为日志
# ══════════════════════════════════════════

@router.get("/log/me", summary="查询我的行为日志")
def get_my_logs(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    since = date.today() - timedelta(days=days)
    logs = (
        db.query(VisionBehaviorLog)
        .filter(
            VisionBehaviorLog.user_id == current_user.id,
            VisionBehaviorLog.log_date >= since,
        )
        .order_by(VisionBehaviorLog.log_date.desc())
        .all()
    )
    return {
        "total": len(logs),
        "logs": [
            {
                "id": l.id,
                "log_date": str(l.log_date),
                "outdoor_minutes": l.outdoor_minutes,
                "screen_sessions": l.screen_sessions,
                "screen_total_minutes": l.screen_total_minutes,
                "eye_exercise_done": l.eye_exercise_done,
                "lutein_intake_mg": l.lutein_intake_mg,
                "sleep_minutes": l.sleep_minutes,
                "behavior_score": l.behavior_score,
                "input_source": l.input_source,
            }
            for l in logs
        ],
    }


@router.get("/log/{user_id}", summary="查询指定用户日志 (教练/监护人)")
def get_user_logs(
    user_id: int,
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 权限: 教练/管理员 或 该用户的监护人
    is_coach_admin = getattr(current_user, "role_level", 0) >= 4 if hasattr(current_user, "role_level") else False
    is_guardian = (
        db.query(VisionGuardianBinding)
        .filter(
            VisionGuardianBinding.guardian_user_id == current_user.id,
            VisionGuardianBinding.student_user_id == user_id,
            VisionGuardianBinding.is_active == True,
        )
        .first()
    ) is not None

    if not is_coach_admin and not is_guardian and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="无权查看该用户的日志")

    since = date.today() - timedelta(days=days)
    logs = (
        db.query(VisionBehaviorLog)
        .filter(
            VisionBehaviorLog.user_id == user_id,
            VisionBehaviorLog.log_date >= since,
        )
        .order_by(VisionBehaviorLog.log_date.desc())
        .all()
    )
    return {
        "user_id": user_id,
        "total": len(logs),
        "logs": [
            {
                "id": l.id,
                "log_date": str(l.log_date),
                "outdoor_minutes": l.outdoor_minutes,
                "screen_total_minutes": l.screen_total_minutes,
                "eye_exercise_done": l.eye_exercise_done,
                "behavior_score": l.behavior_score,
            }
            for l in logs
        ],
    }


# ══════════════════════════════════════════
# 4-5. 目标管理
# ══════════════════════════════════════════

@router.get("/goals/me", summary="查询我的目标")
def get_my_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = get_or_create_goal(db, current_user.id)
    db.commit()
    return {
        "outdoor_target_min": goal.outdoor_target_min,
        "screen_session_limit": goal.screen_session_limit,
        "screen_daily_limit": goal.screen_daily_limit,
        "lutein_target_mg": goal.lutein_target_mg,
        "sleep_target_min": goal.sleep_target_min,
        "ttm_stage": goal.ttm_stage,
        "auto_adjust": goal.auto_adjust,
    }


@router.put("/goals/me", summary="更新我的目标")
def update_my_goals(
    data: VisionGoalInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    goal = get_or_create_goal(db, current_user.id)
    if data.outdoor_target_min is not None:
        goal.outdoor_target_min = data.outdoor_target_min
    if data.screen_session_limit is not None:
        goal.screen_session_limit = data.screen_session_limit
    if data.screen_daily_limit is not None:
        goal.screen_daily_limit = data.screen_daily_limit
    if data.lutein_target_mg is not None:
        goal.lutein_target_mg = data.lutein_target_mg
    if data.sleep_target_min is not None:
        goal.sleep_target_min = data.sleep_target_min
    if data.auto_adjust is not None:
        goal.auto_adjust = data.auto_adjust
    goal.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "目标已更新", "goal_id": goal.id}


# ══════════════════════════════════════════
# 6-9. 监护人管理
# ══════════════════════════════════════════

@router.post("/guardian/bind", summary="创建监护关系")
def bind_guardian(
    data: GuardianBindInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 检查学生是否存在
    student = db.query(User).filter(User.id == data.student_user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生用户不存在")

    if current_user.id == data.student_user_id:
        raise HTTPException(status_code=400, detail="不能监护自己")

    # 去重
    existing = (
        db.query(VisionGuardianBinding)
        .filter(
            VisionGuardianBinding.student_user_id == data.student_user_id,
            VisionGuardianBinding.guardian_user_id == current_user.id,
        )
        .first()
    )
    if existing:
        if existing.is_active:
            raise HTTPException(status_code=409, detail="监护关系已存在")
        # 重新激活
        existing.is_active = True
        existing.deactivated_at = None
        existing.relationship = data.relationship
        existing.notify_risk_threshold = data.notify_risk_threshold
        existing.can_input_behavior = data.can_input_behavior
        db.commit()
        return {"message": "监护关系已重新激活", "binding_id": existing.id}

    binding = VisionGuardianBinding(
        student_user_id=data.student_user_id,
        guardian_user_id=current_user.id,
        relationship=data.relationship,
        notify_risk_threshold=data.notify_risk_threshold,
        can_input_behavior=data.can_input_behavior,
    )
    db.add(binding)
    db.commit()
    db.refresh(binding)
    return {"message": "监护关系已创建", "binding_id": binding.id}


@router.get("/guardian/students", summary="查询我监护的学生")
def get_my_students(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {"students": get_guardian_students(db, current_user.id)}


@router.get("/guardian/guardians", summary="查询我的监护人")
def get_my_guardians(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return {"guardians": get_student_guardians(db, current_user.id)}


@router.delete("/guardian/{binding_id}", summary="解除监护关系")
def unbind_guardian(
    binding_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    binding = db.query(VisionGuardianBinding).filter(VisionGuardianBinding.id == binding_id).first()
    if not binding:
        raise HTTPException(status_code=404, detail="监护关系不存在")

    # 只有监护人或学生本人可以解除
    if current_user.id not in (binding.guardian_user_id, binding.student_user_id):
        raise HTTPException(status_code=403, detail="无权解除该监护关系")

    binding.is_active = False
    binding.deactivated_at = datetime.utcnow()
    db.commit()
    return {"message": "监护关系已解除"}


# ══════════════════════════════════════════
# 10-11. 视力档案
# ══════════════════════════════════════════

@router.get("/profile/me", summary="我的视力档案")
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = get_or_create_profile(db, current_user.id)
    db.commit()
    guardians = get_student_guardians(db, current_user.id)
    return {
        "user_id": current_user.id,
        "is_vision_student": profile.is_vision_student,
        "myopia_onset_age": profile.myopia_onset_age,
        "current_risk_level": profile.current_risk_level,
        "ttm_vision_stage": profile.ttm_vision_stage,
        "last_exam_date": str(profile.last_exam_date) if profile.last_exam_date else None,
        "expert_user_id": profile.expert_user_id,
        "enrolled_at": str(profile.enrolled_at) if profile.enrolled_at else None,
        "notes": profile.notes,
        "guardians": guardians,
    }


@router.put("/profile/me", summary="更新视力档案")
def update_my_profile(
    data: VisionProfileInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = get_or_create_profile(db, current_user.id)
    if data.is_vision_student is not None:
        profile.is_vision_student = data.is_vision_student
    if data.myopia_onset_age is not None:
        profile.myopia_onset_age = data.myopia_onset_age
    if data.ttm_vision_stage is not None:
        profile.ttm_vision_stage = data.ttm_vision_stage
    if data.notes is not None:
        profile.notes = data.notes
    db.commit()
    return {"message": "视力档案已更新"}


# ══════════════════════════════════════════
# 12-13. 视力检查记录
# ══════════════════════════════════════════

@router.post("/exam", summary="录入视力检查记录")
def create_exam_record(
    data: VisionExamInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_user_id = data.user_id or current_user.id

    # 如果为他人录入, 需要是监护人或教练
    if target_user_id != current_user.id:
        is_guardian = (
            db.query(VisionGuardianBinding)
            .filter(
                VisionGuardianBinding.guardian_user_id == current_user.id,
                VisionGuardianBinding.student_user_id == target_user_id,
                VisionGuardianBinding.is_active == True,
            )
            .first()
        ) is not None
        is_coach_admin = getattr(current_user, "role_level", 0) >= 4 if hasattr(current_user, "role_level") else False
        if not is_guardian and not is_coach_admin:
            raise HTTPException(status_code=403, detail="无权为该用户录入检查记录")

    try:
        exam_date_val = date.fromisoformat(data.exam_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="exam_date 格式应为 YYYY-MM-DD")

    # 风险等级自动评估
    risk = "normal"
    worst_sph = min(data.left_eye_sph or 0, data.right_eye_sph or 0)
    if worst_sph < -6.0:
        risk = "urgent"
    elif worst_sph < -3.0:
        risk = "alert"
    elif worst_sph < -0.5:
        risk = "watch"

    record = VisionExamRecord(
        user_id=target_user_id,
        exam_date=exam_date_val,
        left_eye_sph=data.left_eye_sph,
        right_eye_sph=data.right_eye_sph,
        left_eye_cyl=data.left_eye_cyl,
        right_eye_cyl=data.right_eye_cyl,
        left_eye_axial_len=data.left_eye_axial_len,
        right_eye_axial_len=data.right_eye_axial_len,
        left_eye_va=data.left_eye_va,
        right_eye_va=data.right_eye_va,
        exam_type=data.exam_type,
        examiner_name=data.examiner_name,
        institution=data.institution,
        risk_level=risk,
        notes=data.notes,
    )
    db.add(record)

    # 更新视力档案
    profile = get_or_create_profile(db, target_user_id)
    profile.last_exam_date = exam_date_val
    profile.current_risk_level = risk

    db.commit()
    db.refresh(record)
    return {"message": "检查记录已录入", "exam_id": record.id, "risk_level": risk}


@router.get("/exam/{user_id}", summary="查询检查记录")
def get_exam_records(
    user_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 权限检查
    is_self = current_user.id == user_id
    is_coach_admin = getattr(current_user, "role_level", 0) >= 4 if hasattr(current_user, "role_level") else False
    is_guardian = (
        db.query(VisionGuardianBinding)
        .filter(
            VisionGuardianBinding.guardian_user_id == current_user.id,
            VisionGuardianBinding.student_user_id == user_id,
            VisionGuardianBinding.is_active == True,
        )
        .first()
    ) is not None

    if not is_self and not is_coach_admin and not is_guardian:
        raise HTTPException(status_code=403, detail="无权查看该用户的检查记录")

    records = (
        db.query(VisionExamRecord)
        .filter(VisionExamRecord.user_id == user_id)
        .order_by(VisionExamRecord.exam_date.desc())
        .limit(limit)
        .all()
    )
    return {
        "user_id": user_id,
        "total": len(records),
        "records": [
            {
                "id": r.id,
                "exam_date": str(r.exam_date),
                "left_eye_sph": r.left_eye_sph,
                "right_eye_sph": r.right_eye_sph,
                "left_eye_cyl": r.left_eye_cyl,
                "right_eye_cyl": r.right_eye_cyl,
                "left_eye_axial_len": r.left_eye_axial_len,
                "right_eye_axial_len": r.right_eye_axial_len,
                "left_eye_va": r.left_eye_va,
                "right_eye_va": r.right_eye_va,
                "exam_type": r.exam_type,
                "examiner_name": r.examiner_name,
                "institution": r.institution,
                "risk_level": r.risk_level,
                "notes": r.notes,
            }
            for r in records
        ],
    }


# ══════════════════════════════════════════
# 14. 仪表盘
# ══════════════════════════════════════════

@router.get("/dashboard/{user_id}", summary="视力保护仪表盘")
def get_vision_dashboard(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 权限
    is_self = current_user.id == user_id
    is_coach_admin = getattr(current_user, "role_level", 0) >= 4 if hasattr(current_user, "role_level") else False
    is_guardian = (
        db.query(VisionGuardianBinding)
        .filter(
            VisionGuardianBinding.guardian_user_id == current_user.id,
            VisionGuardianBinding.student_user_id == user_id,
            VisionGuardianBinding.is_active == True,
        )
        .first()
    ) is not None

    if not is_self and not is_coach_admin and not is_guardian:
        raise HTTPException(status_code=403, detail="无权查看该用户的仪表盘")

    # 档案
    profile = db.query(VisionProfile).filter(VisionProfile.user_id == user_id).first()

    # 最新检查
    latest_exam = (
        db.query(VisionExamRecord)
        .filter(VisionExamRecord.user_id == user_id)
        .order_by(VisionExamRecord.exam_date.desc())
        .first()
    )

    # 近7天日志
    seven_days_ago = date.today() - timedelta(days=7)
    recent_logs = (
        db.query(VisionBehaviorLog)
        .filter(
            VisionBehaviorLog.user_id == user_id,
            VisionBehaviorLog.log_date >= seven_days_ago,
        )
        .order_by(VisionBehaviorLog.log_date)
        .all()
    )

    # 目标
    goal = db.query(VisionBehaviorGoal).filter(VisionBehaviorGoal.user_id == user_id).first()

    # 综合风险
    risk = assess_vision_risk(db, user_id)

    # 今日打卡
    today_log = (
        db.query(VisionBehaviorLog)
        .filter(
            VisionBehaviorLog.user_id == user_id,
            VisionBehaviorLog.log_date == date.today(),
        )
        .first()
    )

    # 连续打卡天数
    streak = 0
    check_date = date.today()
    for _ in range(365):
        log = (
            db.query(VisionBehaviorLog)
            .filter(
                VisionBehaviorLog.user_id == user_id,
                VisionBehaviorLog.log_date == check_date,
            )
            .first()
        )
        if not log:
            break
        streak += 1
        check_date -= timedelta(days=1)

    return {
        "user_id": user_id,
        "risk_level": risk.value,
        "profile": {
            "ttm_stage": profile.ttm_vision_stage if profile else "S0",
            "myopia_onset_age": profile.myopia_onset_age if profile else None,
            "last_exam_date": str(profile.last_exam_date) if profile and profile.last_exam_date else None,
        } if profile else None,
        "latest_exam": {
            "exam_date": str(latest_exam.exam_date),
            "left_sph": latest_exam.left_eye_sph,
            "right_sph": latest_exam.right_eye_sph,
            "risk_level": latest_exam.risk_level,
        } if latest_exam else None,
        "today": {
            "logged": today_log is not None,
            "score": today_log.behavior_score if today_log else None,
        },
        "streak_days": streak,
        "week_scores": [
            {"date": str(l.log_date), "score": l.behavior_score or 0}
            for l in recent_logs
        ],
        "goals": {
            "outdoor_target_min": goal.outdoor_target_min,
            "screen_daily_limit": goal.screen_daily_limit,
            "sleep_target_min": goal.sleep_target_min,
        } if goal else None,
    }

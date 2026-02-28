# ═══════════════════════════════════════════════════════════════
# 补丁：3个缺失端点 — 追加到 coach_api.py 文件末尾
# ═══════════════════════════════════════════════════════════════
#
# 【操作步骤】
#
# 第1步：在 coach_api.py 顶部 from core.models import (...) 中，
#        添加 Intervention 和 BehaviorPrescription：
#
#   from core.models import (
#       User, UserRole, Assessment, BehavioralProfile,
#       CoachMessage, MicroActionTask, MicroActionLog,
#       Reminder, BehaviorHistory,
#       GlucoseReading, SleepRecord, ActivityRecord, VitalSign,
#       Intervention, BehaviorPrescription,   # ← 新增这行
#   )
#
# 第2步：把下面3个函数复制粘贴到 coach_api.py 文件最末尾
#
# ═══════════════════════════════════════════════════════════════


# ──────────────────────────────────────────────────────────────
# GET /api/v1/coach/students/{student_id}/prescriptions
# 学员行为处方列表
# ──────────────────────────────────────────────────────────────
@router.get("/students/{student_id}/prescriptions")
async def get_student_prescriptions(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """获取学员的行为处方列表"""
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    try:
        prescriptions = (
            db.query(BehaviorPrescription)
            .filter(BehaviorPrescription.user_id == str(student_id))
            .order_by(BehaviorPrescription.id.desc())
            .all()
        )
        items = []
        for p in prescriptions:
            items.append({
                "id": p.id,
                "target_behavior": p.target_behavior,
                "frequency_dose": p.frequency_dose,
                "time_place": p.time_place,
                "trigger_cue": p.trigger_cue,
                "obstacle_plan": p.obstacle_plan,
                "support_resource": p.support_resource,
                "domain": p.domain,
            })
    except Exception as e:
        logger.warning(f"获取行为处方失败: {e}")
        items = []

    return {
        "student_id": student_id,
        "student_name": getattr(student, "full_name", None) or getattr(student, "username", ""),
        "count": len(items),
        "items": items,
    }


# ──────────────────────────────────────────────────────────────
# GET /api/v1/coach/students/{student_id}/risk-history
# 学员风险等级变化历史
# ──────────────────────────────────────────────────────────────
@router.get("/students/{student_id}/risk-history")
async def get_student_risk_history(
    student_id: int,
    days: int = Query(default=30, ge=1, le=180),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """获取学员风险等级变化历史"""
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    since = datetime.utcnow() - timedelta(days=days)
    items = []

    try:
        histories = (
            db.query(BehaviorHistory)
            .filter(
                BehaviorHistory.user_id == student_id,
                BehaviorHistory.created_at >= since,
            )
            .order_by(BehaviorHistory.created_at.desc())
            .limit(50)
            .all()
        )
        for h in histories:
            data = {}
            if hasattr(h, "data") and h.data:
                data = h.data if isinstance(h.data, dict) else {}
            if hasattr(h, "metadata") and h.metadata:
                data = h.metadata if isinstance(h.metadata, dict) else data

            risk_level = data.get("risk_level") or data.get("level")
            if risk_level:
                items.append({
                    "id": h.id,
                    "risk_level": risk_level,
                    "reason": data.get("reason", ""),
                    "score": data.get("score"),
                    "recorded_at": h.created_at.isoformat() if h.created_at else None,
                })
    except Exception as e:
        logger.warning(f"获取风险历史失败: {e}")

    # 无历史记录时返回当前风险状态
    if not items:
        current_risk = getattr(student, "risk_level", None)
        if current_risk:
            items.append({
                "id": 0,
                "risk_level": current_risk.value if hasattr(current_risk, "value") else str(current_risk),
                "reason": "当前风险等级",
                "score": None,
                "recorded_at": datetime.utcnow().isoformat(),
            })

    return {
        "student_id": student_id,
        "student_name": getattr(student, "full_name", None) or getattr(student, "username", ""),
        "days": days,
        "count": len(items),
        "items": items,
    }


# ──────────────────────────────────────────────────────────────
# GET /api/v1/coach/students/{student_id}/interventions
# 学员干预记录列表
# ──────────────────────────────────────────────────────────────
@router.get("/students/{student_id}/interventions")
async def get_student_interventions(
    student_id: int,
    days: int = Query(default=30, ge=1, le=180),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """获取学员的干预记录"""
    student = db.query(User).filter(User.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    since = datetime.utcnow() - timedelta(days=days)
    items = []

    try:
        assessments = (
            db.query(Assessment)
            .filter(
                Assessment.user_id == student_id,
                Assessment.created_at >= since,
            )
            .all()
        )
        assessment_ids = [a.id for a in assessments]

        if assessment_ids:
            interventions = (
                db.query(Intervention)
                .filter(Intervention.assessment_id.in_(assessment_ids))
                .order_by(Intervention.id.desc())
                .all()
            )
            for iv in interventions:
                items.append({
                    "id": iv.id,
                    "assessment_id": iv.assessment_id,
                    "agent_type": iv.agent_type.value if hasattr(iv.agent_type, "value") else str(iv.agent_type) if iv.agent_type else None,
                    "created_at": iv.created_at.isoformat() if hasattr(iv, "created_at") and iv.created_at else None,
                })
    except Exception as e:
        logger.warning(f"获取干预记录失败: {e}")

    return {
        "student_id": student_id,
        "student_name": getattr(student, "full_name", None) or getattr(student, "username", ""),
        "days": days,
        "count": len(items),
        "items": items,
    }

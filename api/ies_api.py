"""
IES API — 干预效果评分端点 (4分量公式)

基于契约注册表 ⑩ Sheet 定义:
IES = 0.40×完成率 + 0.20×活跃度 + 0.25×进展变化量 - 0.15×抗阻指数
"""
from __future__ import annotations

from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from api.dependencies import get_current_user, get_db, require_admin
from core.models import (
    User, IESScore, IESDecisionLog,
    MicroActionTask, ChatSession, JourneyState,
)
from schemas.ies_formula import compute_ies, interpret_ies, IES_COMPONENTS, IES_DECISION_RULES

router = APIRouter(prefix="/api/v1/ies", tags=["ies"])


@router.get("/score")
def get_my_ies(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户 IES 评分"""
    since = datetime.utcnow() - timedelta(days=days)
    period_start = (datetime.utcnow() - timedelta(days=days)).date()
    period_end = date.today()

    # ── 1. Completion rate (微行动完成率) ─────
    total_tasks = db.query(MicroActionTask).filter(
        MicroActionTask.user_id == current_user.id,
        MicroActionTask.created_at >= since,
    ).count()
    completed_tasks = db.query(MicroActionTask).filter(
        MicroActionTask.user_id == current_user.id,
        MicroActionTask.created_at >= since,
        MicroActionTask.status == "completed",
    ).count()
    completion_rate = completed_tasks / max(total_tasks, 1)

    # ── 2. Activity rate (对话活跃度) ─────────
    total_days = max(days, 1)
    active_days_q = db.query(
        func.date(ChatSession.created_at)
    ).filter(
        ChatSession.user_id == current_user.id,
        ChatSession.created_at >= since,
    ).distinct().count()
    activity_rate = min(active_days_q / total_days, 1.0)

    # ── 3. Progression delta (阶段进展) ───────
    journey = db.query(JourneyState).filter(
        JourneyState.user_id == current_user.id
    ).first()
    stage_map = {"s0_authorization": 0, "s1_awareness": 1, "s2_trial": 2,
                 "s3_pathway": 3, "s4_internalization": 4, "s5_graduation": 5}
    current_stage_idx = stage_map.get(journey.journey_stage, 0) if journey else 0
    progression_delta = min(current_stage_idx / 5.0, 1.0)

    # ── 4. Resistance index (跳过+退出率) ─────
    skipped_tasks = db.query(MicroActionTask).filter(
        MicroActionTask.user_id == current_user.id,
        MicroActionTask.created_at >= since,
        MicroActionTask.status == "skipped",
    ).count()
    resistance_index = skipped_tasks / max(total_tasks, 1) if total_tasks else 0.0

    # ── Compute IES ───────────────────────────
    ies = compute_ies(completion_rate, activity_rate, progression_delta, resistance_index)
    interpretation = interpret_ies(ies)

    # ── Persist ───────────────────────────────
    record = IESScore(
        user_id=current_user.id,
        period_start=period_start,
        period_end=period_end,
        completion_rate=round(completion_rate, 4),
        activity_rate=round(activity_rate, 4),
        progression_delta=round(progression_delta, 4),
        resistance_index=round(resistance_index, 4),
        ies_score=ies,
        interpretation=interpretation.value,
        details={
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "active_days": active_days_q,
            "skipped_tasks": skipped_tasks,
        },
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "user_id": current_user.id,
        "period": {"start": str(period_start), "end": str(period_end), "days": days},
        "components": {
            "completion_rate": round(completion_rate, 4),
            "activity_rate": round(activity_rate, 4),
            "progression_delta": round(progression_delta, 4),
            "resistance_index": round(resistance_index, 4),
        },
        "ies_score": ies,
        "interpretation": interpretation.value,
        "formula": "IES = 0.40×C + 0.20×A + 0.25×P - 0.15×R",
        "record_id": record.id,
    }


@router.get("/history")
def ies_history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取 IES 历史记录"""
    records = db.query(IESScore).filter(
        IESScore.user_id == current_user.id,
    ).order_by(desc(IESScore.created_at)).limit(limit).all()

    return {
        "total": len(records),
        "records": [
            {
                "id": r.id,
                "period_start": str(r.period_start),
                "period_end": str(r.period_end),
                "ies_score": r.ies_score,
                "interpretation": r.interpretation,
                "components": {
                    "completion_rate": r.completion_rate,
                    "activity_rate": r.activity_rate,
                    "progression_delta": r.progression_delta,
                    "resistance_index": r.resistance_index,
                },
                "created_at": str(r.created_at),
            }
            for r in records
        ],
    }


@router.get("/formula")
def ies_formula_info(
    current_user: User = Depends(get_current_user),
):
    """获取 IES 公式定义和决策规则"""
    return {
        "formula": "IES = 0.40×completion + 0.20×activity + 0.25×progression - 0.15×resistance",
        "components": [
            {"name": c.name, "weight": c.weight, "description": c.description, "inverted": c.inverted}
            for c in IES_COMPONENTS
        ],
        "interpretation_thresholds": {
            "significant_improvement": "≥ 0.7",
            "clear_improvement": "≥ 0.3",
            "slight_improvement": "≥ 0.1",
            "no_change": "≥ -0.1",
            "slight_decline": "≥ -0.3",
            "clear_decline": "< -0.3",
        },
        "decision_rules": [
            {"interpretation": r.interpretation.value, "action": r.rx_action, "description": r.description}
            for r in IES_DECISION_RULES
        ],
    }


@router.get("/decisions")
def ies_decisions(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取 IES 驱动的决策日志"""
    logs = db.query(IESDecisionLog).filter(
        IESDecisionLog.user_id == current_user.id,
    ).order_by(desc(IESDecisionLog.created_at)).limit(limit).all()

    return {
        "total": len(logs),
        "decisions": [
            {
                "id": l.id,
                "ies_score_id": l.ies_score_id,
                "decision_type": l.decision_type,
                "old_value": l.old_value,
                "new_value": l.new_value,
                "reason": l.reason,
                "auto_applied": l.auto_applied,
                "created_at": str(l.created_at),
            }
            for l in logs
        ],
    }

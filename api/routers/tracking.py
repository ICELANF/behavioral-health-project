"""
效果追踪路由
路径前缀: /api/v3/tracking

鉴权: 所有端点需登录
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.database import get_db
from api.auth import User, get_current_user
from api.schemas import APIResponse, DailyOutcomeRequest, WeeklyReviewRequest
from core.intervention_tracker import (
    record_daily_outcome, generate_weekly_review, log_stage_transition,
)

router = APIRouter(prefix="/api/v3/tracking", tags=["效果追踪"])


@router.post("/daily", response_model=APIResponse, summary="记录每日效果")
def record_daily(
    req: DailyOutcomeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    每日打卡后提交: 任务完成情况 + 心情 + 难度反馈

    自动触发 PDCA 检查:
    - 连续3天完成率<50% → 降低难度
    - 连续7天完成率>90% → 可升级
    """
    outcome = record_daily_outcome(
        db=db,
        user_id=user.id,
        date=req.date or datetime.now(),
        tasks_assigned=req.tasks_assigned,
        tasks_completed=req.tasks_completed,
        tasks_skipped=req.tasks_skipped,
        streak_days=req.streak_days,
        user_mood=req.user_mood,
        user_difficulty=req.user_difficulty,
        user_notes=req.user_notes,
        cultivation_stage=req.cultivation_stage,
        spi_before=req.spi_before,
        spi_after=req.spi_after,
    )
    db.commit()

    return APIResponse(data={
        "outcome_id": outcome.id,
        "effectiveness_score": outcome.effectiveness_score,
        "pdca_action": outcome.pdca_action,
        "adjustment_detail": outcome.adjustment_detail,
    })


@router.post("/weekly-review", response_model=APIResponse, summary="周度效果汇总")
def weekly_review(
    req: WeeklyReviewRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    生成过去 7 天的效果报告:
    - 完成率趋势
    - SPI 变化
    - 阶段转变建议
    - PDCA 调整汇总
    """
    end_date = req.end_date or datetime.now()
    week_start = end_date - timedelta(days=7)
    review = generate_weekly_review(
        db=db,
        user_id=user.id,
        week_start=week_start,
    )
    return APIResponse(data=review)


@router.post("/stage-transition", response_model=APIResponse, summary="记录阶段转变")
def stage_transition(
    from_stage: str,
    to_stage: str,
    trigger: str = "system",
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """记录行为阶段变化 (S0→S1 等)"""
    log = log_stage_transition(
        db=db,
        user_id=user.id,
        from_stage=from_stage,
        to_stage=to_stage,
        trigger=trigger,
    )
    db.commit()
    return APIResponse(data={
        "log_id": log.id,
        "from_stage": from_stage,
        "to_stage": to_stage,
        "direction": log.direction,
    })

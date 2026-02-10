"""
积分激励路由
路径前缀: /api/v3/incentive

鉴权: 所有端点需登录
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from v3.database import get_db
from v3.auth import User, get_current_user
from v3.schemas import APIResponse, CheckinRequest, TaskCompleteRequest
from core.incentive_integration import PointEngine, get_rx_context_from_incentive

router = APIRouter(prefix="/api/v3/incentive", tags=["积分激励"])


@router.post("/checkin", response_model=APIResponse, summary="打卡积分")
def checkin(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """每日打卡获得积分"""
    engine = PointEngine(db)
    result = engine.record_checkin(user.id)
    db.commit()
    return APIResponse(data=result)


@router.post("/task-complete", response_model=APIResponse, summary="任务完成积分")
def task_complete(
    req: TaskCompleteRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """完成单个任务获得积分"""
    engine = PointEngine(db)
    result = engine.record_task_complete(user.id, req.task_id)
    db.commit()
    return APIResponse(data=result)


@router.get("/balance", response_model=APIResponse, summary="查询积分余额")
def get_balance(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询用户积分余额和成长等级"""
    engine = PointEngine(db)
    balance = engine._get_or_create_balance(user.id)
    return APIResponse(data={
        "user_id": user.id,
        "growth": balance.growth,
        "contribution": balance.contribution,
        "influence": balance.influence,
        "total": balance.total,
        "streak_days": balance.streak_days,
        "longest_streak": balance.longest_streak,
    })


@router.get("/rx-context", response_model=APIResponse, summary="获取处方激励上下文")
def rx_context(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前成长等级下的处方模式和激励参数"""
    engine = PointEngine(db)
    balance = engine._get_or_create_balance(user.id)
    ctx = get_rx_context_from_incentive(
        engine._compute_growth_level(balance.total) if hasattr(engine, '_compute_growth_level') else "G0",
        balance.streak_days or 0,
        {},
    )
    return APIResponse(data=ctx)

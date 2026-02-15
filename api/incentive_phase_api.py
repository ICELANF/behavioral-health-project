"""
V4.0 Incentive Phase API — 三阶觉醒激励 + 觉察积分

MEU-24: Three-Phase Incentive Transformation
MEU-25: Awareness Points + Points Consumption

Endpoints:
  GET  /config           用户激励阶段配置
  GET  /phases           所有阶段定义
  POST /awareness/award  发放觉察积分
  GET  /awareness/balance 觉察积分余额
  GET  /awareness/events  觉察积分事件目录
  POST /consume          消费积分
  GET  /consumption-catalog 消费场景目录
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from core.models import User
from core.incentive_phase_engine import (
    IncentivePhaseEngine, INCENTIVE_PHASES,
)

router = APIRouter(prefix="/api/v1/incentive-phase", tags=["incentive-phase"])


# ── Schemas ─────────────────────────────────────

class AwardAwarenessRequest(BaseModel):
    event: str
    custom_amount: Optional[int] = None

class ConsumePointsRequest(BaseModel):
    scenario: str
    custom_cost: Optional[int] = None
    target_user_id: Optional[int] = None


# ── MEU-24: Three-Phase Incentive ───────────────

@router.get("/config")
def get_incentive_config(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户激励阶段配置 (基于agency_mode)"""
    target_id = user_id if user_id else current_user.id
    engine = IncentivePhaseEngine(db)
    return engine.get_user_incentive_config(target_id)


@router.get("/phases")
def get_all_phases(
    current_user: User = Depends(get_current_user),
):
    """获取所有三阶段定义"""
    return INCENTIVE_PHASES


# ── MEU-25: Awareness Points ────────────────────

@router.post("/awareness/award")
def award_awareness_points(
    req: AwardAwarenessRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """发放觉察积分"""
    engine = IncentivePhaseEngine(db)
    result = engine.award_awareness_points(
        current_user.id, req.event, req.custom_amount
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()
    return result


@router.get("/awareness/balance")
def get_awareness_balance(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取积分余额 (所有类型)"""
    target_id = user_id if user_id else current_user.id
    engine = IncentivePhaseEngine(db)
    return engine.get_awareness_balance(target_id)


@router.get("/awareness/events")
def get_awareness_events(
    current_user: User = Depends(get_current_user),
):
    """获取觉察积分事件目录"""
    engine = IncentivePhaseEngine.__new__(IncentivePhaseEngine)
    return engine.get_awareness_events()


@router.post("/consume")
def consume_points(
    req: ConsumePointsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """消费积分"""
    engine = IncentivePhaseEngine(db)
    result = engine.consume_points(
        current_user.id, req.scenario, req.custom_cost, req.target_user_id
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()
    return result


@router.get("/consumption-catalog")
def get_consumption_catalog(
    current_user: User = Depends(get_current_user),
):
    """获取积分消费场景目录"""
    engine = IncentivePhaseEngine.__new__(IncentivePhaseEngine)
    return engine.get_consumption_catalog()

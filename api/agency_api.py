"""
V4.0 Agency API — 主体性引擎 REST 接口

MEU-22: Agency 6-Signal Calculation Engine
MEU-23: Agent Dual-Mode Interaction Engine

Endpoints:
  GET  /status              当前agency状态
  POST /compute             重新计算agency_score
  POST /analyze-text        文本agency信号分析
  POST /coach-override      教练标注agency值
  DELETE /coach-override     清除教练标注
  GET  /history             agency变化历史
  GET  /mode-profiles       所有双模交互配置
  GET  /mode-profile/{mode} 指定模式配置
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db, require_coach_or_admin
from core.models import User
from core.agency_engine import AgencyEngine, AgentDualModeAdapter

router = APIRouter(prefix="/api/v1/agency", tags=["agency"])


# ── Schemas ─────────────────────────────────────

class ComputeAgencyRequest(BaseModel):
    user_id: Optional[int] = None  # Admin/coach can specify; default=self
    signals: Optional[Dict[str, float]] = None
    coach_override: Optional[float] = None

class AnalyzeTextRequest(BaseModel):
    text: str

class CoachOverrideRequest(BaseModel):
    user_id: int
    override_value: float = Field(ge=0.0, le=1.0)


# ── MEU-22: Agency Signals ──────────────────────

@router.get("/status")
def agency_status(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户当前agency状态"""
    target_id = user_id if user_id else current_user.id
    engine = AgencyEngine(db)
    return engine.get_agency_status(target_id)


@router.post("/compute")
def compute_agency(
    req: ComputeAgencyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """(重新)计算用户agency_score"""
    target_id = req.user_id if req.user_id else current_user.id
    engine = AgencyEngine(db)
    result = engine.compute_agency(
        target_id,
        signals=req.signals,
        coach_override=req.coach_override,
    )
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()
    return result


@router.post("/analyze-text")
def analyze_text(
    req: AnalyzeTextRequest,
    current_user: User = Depends(get_current_user),
):
    """分析文本中的agency信号 (S3/S4)"""
    engine_cls = AgencyEngine.__new__(AgencyEngine)
    return {
        "text_length": len(req.text),
        "signals": {
            "S3_active_expression": engine_cls._compute_s3_from_text(req.text),
            "S4_awareness_depth": engine_cls._compute_s4_from_text(req.text),
        },
    }


@router.post("/coach-override")
def set_coach_override(
    req: CoachOverrideRequest,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """教练标注agency值 (S6)"""
    engine = AgencyEngine(db)
    result = engine.set_coach_override(req.user_id, req.override_value)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()
    return result


@router.delete("/coach-override")
def clear_coach_override(
    user_id: int = Query(...),
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """清除教练标注"""
    engine = AgencyEngine(db)
    result = engine.clear_coach_override(user_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()
    return result


@router.get("/history")
def agency_history(
    user_id: Optional[int] = None,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取agency变化历史"""
    target_id = user_id if user_id else current_user.id
    engine = AgencyEngine(db)
    return {"user_id": target_id, "history": engine.get_agency_history(target_id, days)}


# ── MEU-23: Dual-Mode Interaction ───────────────

@router.get("/mode-profiles")
def get_mode_profiles(
    current_user: User = Depends(get_current_user),
):
    """获取所有双模交互配置 (供前端适配)"""
    return AgentDualModeAdapter.get_all_profiles()


@router.get("/mode-profile/{mode}")
def get_mode_profile(
    mode: str,
    current_user: User = Depends(get_current_user),
):
    """获取指定模式的交互配置"""
    if mode not in ("passive", "transitional", "active"):
        raise HTTPException(status_code=400, detail=f"无效模式: {mode}")
    return AgentDualModeAdapter.get_mode_profile(mode)

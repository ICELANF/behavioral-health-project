"""
诊断管道路由
路径前缀: /api/v3/diagnostic

鉴权: 所有端点需 access_token, user_id 自动从 Token 提取
"""
from dataclasses import asdict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from v3.database import get_db
from v3.auth import User, get_current_user
from v3.schemas import (
    APIResponse, DiagnosticMinimalRequest, DiagnosticFullRequest,
)
from core.diagnostic_pipeline import DiagnosticPipeline

router = APIRouter(prefix="/api/v3/diagnostic", tags=["诊断管道"])


def _pipeline_to_dict(pr) -> dict:
    """将 dataclass PipelineResult 安全序列化"""
    def _dc(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return {k: _dc(v) for k, v in obj.__dict__.items()}
        if isinstance(obj, list):
            return [_dc(i) for i in obj]
        if isinstance(obj, dict):
            return {k: _dc(v) for k, v in obj.items()}
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return obj
    return _dc(pr)


@router.post("/minimal", response_model=APIResponse, summary="最小启动诊断 (12题)")
def diagnostic_minimal(
    req: DiagnosticMinimalRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    TTM 7 题 + SPI quick 5 题 = 12 题即可生成基础处方

    返回: Layer1 + Layer2 + Layer4(基础处方)
    """
    pipeline = DiagnosticPipeline(db)
    result = pipeline.run_minimal(
        user_id=user.id,
        behavioral_stage=req.behavioral_stage,
        trigger_strength=req.trigger_strength,
        psychological_level=req.psychological_level,
        capability_resource=req.capability_resource,
        social_support=req.social_support,
        urgency_val=req.urgency_val,
    )
    return APIResponse(data=_pipeline_to_dict(result))


@router.post("/full", response_model=APIResponse, summary="完整四层诊断")
def diagnostic_full(
    req: DiagnosticFullRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    完整诊断管道: Layer1(行为诊断) → Layer2(SPI) → Layer3(能力与支持) → Layer4(处方)
    """
    pipeline = DiagnosticPipeline(db)
    result = pipeline.run_full(
        user_id=user.id,
        layer1_input=req.layer1.model_dump(exclude_none=True),
        layer2_input=req.layer2.model_dump(exclude_none=True),
        layer3_input=req.layer3.model_dump(exclude_none=True) if req.layer3 else None,
        growth_level=req.growth_level,
        streak_days=req.streak_days,
        cultivation_stage=req.cultivation_stage,
    )
    return APIResponse(data=_pipeline_to_dict(result))

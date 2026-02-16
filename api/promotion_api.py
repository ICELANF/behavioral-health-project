"""
双轨晋级 API 端点
契约来源: Sheet④ 晋级契约 + Sheet⑩ P0 双轨晋级校验引擎

端点清单:
  GET  /v1/promotion/status        — 查询当前晋级状态
  GET  /v1/promotion/gap-report    — 获取差距分析报告
  POST /v1/promotion/check         — 手动触发晋级校验
  POST /v1/promotion/ceremony      — 启动晋级仪式
  GET  /v1/promotion/peers         — 同道者仪表盘
  GET  /v1/promotion/thresholds    — 查看晋级条件
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

router = APIRouter(prefix="/v1/promotion", tags=["dual-track-promotion"])


# ── 响应模型 ──

class PromotionStatusResponse(BaseModel):
    state: int
    state_name: str
    current_level: str
    target_level: str
    guidance_message: str
    ceremony_ready: bool
    ceremony_name: Optional[str] = None
    ceremony_emoji: Optional[str] = None
    gap_count: int = 0
    points_summary: Optional[Dict] = None


class GapReportResponse(BaseModel):
    promotion_key: str
    state: int
    total_gaps: int
    gaps: List[Dict]
    estimated_total_days: int
    ceremony_name: str
    generated_at: str


class CeremonyResponse(BaseModel):
    success: bool
    new_level: Optional[str] = None
    ceremony: Optional[Dict] = None
    reason: Optional[str] = None


class PeerDashboardResponse(BaseModel):
    promotion_key: str
    peers: List[Dict]
    total: int
    required: int
    progress_target: str
    advanced_target: str


class ThresholdResponse(BaseModel):
    promotion_key: str
    from_level: str
    to_level: str
    points_threshold: Dict
    growth_requirements: Dict
    ceremony: Dict


# ── 依赖注入占位 (实际项目替换为真实实现) ──

async def get_promotion_orchestrator():
    """获取晋级编排器实例"""
    from app.core.deps import get_promotion_orchestrator_singleton
    return get_promotion_orchestrator_singleton()


async def get_current_user(request):
    """获取当前用户 (placeholder)"""
    from app.core.deps import get_current_user as _get_user
    return await _get_user(request)


# ── 端点实现 ──

@router.get("/status", response_model=PromotionStatusResponse)
async def get_promotion_status(
    user=Depends(get_current_user),
    orchestrator=Depends(get_promotion_orchestrator),
):
    """
    查询当前晋级状态。
    
    返回4种状态之一:
      1=正常成长, 2=等待验证, 3=成长先到, 4=晋级就绪
    """
    current_level = getattr(user, "level", "L0")
    result = await orchestrator.check_promotion_eligibility(user.id, current_level)
    
    return PromotionStatusResponse(
        state=result.get("state", 1),
        state_name=result.get("state_name", "NORMAL_GROWTH"),
        current_level=current_level,
        target_level=_next_level(current_level),
        guidance_message=result.get("guidance_message", ""),
        ceremony_ready=result.get("ceremony_ready", False),
        ceremony_name=result.get("ceremony_name"),
        ceremony_emoji=result.get("ceremony_emoji"),
        gap_count=result.get("gap_report", {}).get("total_gaps", 0) if result.get("gap_report") else 0,
        points_summary=None,  # 前端调用 /credits/my 获取积分详情
    )


@router.get("/gap-report", response_model=GapReportResponse)
async def get_gap_report(
    user=Depends(get_current_user),
    orchestrator=Depends(get_promotion_orchestrator),
):
    """
    获取差距分析报告。
    
    仅在状态2(等待验证)或状态3(成长先到)时有意义。
    返回具体差距项+预估达成天数。
    """
    current_level = getattr(user, "level", "L0")
    result = await orchestrator.check_promotion_eligibility(user.id, current_level)
    
    gap_report = result.get("gap_report")
    if not gap_report:
        return GapReportResponse(
            promotion_key=orchestrator.get_promotion_key(current_level) or "",
            state=result.get("state", 1),
            total_gaps=0,
            gaps=[],
            estimated_total_days=0,
            ceremony_name=result.get("ceremony_name", ""),
            generated_at=datetime.utcnow().isoformat(),
        )
    
    return GapReportResponse(**gap_report)


@router.post("/check", response_model=PromotionStatusResponse)
async def manual_check(
    user=Depends(get_current_user),
    orchestrator=Depends(get_promotion_orchestrator),
):
    """
    手动触发晋级校验。
    
    通常系统在积分变动时自动触发, 此端点允许用户手动刷新。
    """
    current_level = getattr(user, "level", "L0")
    result = await orchestrator.check_promotion_eligibility(user.id, current_level)
    
    return PromotionStatusResponse(
        state=result.get("state", 1),
        state_name=result.get("state_name", "NORMAL_GROWTH"),
        current_level=current_level,
        target_level=_next_level(current_level),
        guidance_message=result.get("guidance_message", ""),
        ceremony_ready=result.get("ceremony_ready", False),
        ceremony_name=result.get("ceremony_name"),
        ceremony_emoji=result.get("ceremony_emoji"),
    )


@router.post("/ceremony", response_model=CeremonyResponse)
async def start_ceremony(
    user=Depends(get_current_user),
    orchestrator=Depends(get_promotion_orchestrator),
):
    """
    启动晋级仪式。
    
    前置条件: 状态必须为4(晋级就绪)。
    返回仪式信息+需签署的契约清单。
    触发: CeremonyModal + Confetti 动效。
    """
    current_level = getattr(user, "level", "L0")
    result = await orchestrator.initiate_ceremony(user.id, current_level)
    
    if not result["success"]:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "ceremony_not_ready",
                "message": result.get("reason", "晋级条件尚未满足"),
                "state": result.get("state"),
            }
        )
    
    return CeremonyResponse(**result)


@router.get("/peers", response_model=PeerDashboardResponse)
async def get_peer_dashboard(
    user=Depends(get_current_user),
):
    """
    获取同道者仪表盘。
    
    显示当前层级的4名同道者培养进度。
    """
    from app.core.deps import get_peer_tracking_service
    peer_svc = get_peer_tracking_service()
    
    current_level = getattr(user, "level", "L0")
    dashboard = await peer_svc.get_peer_dashboard(user.id, current_level)
    
    return PeerDashboardResponse(**dashboard)


@router.get("/thresholds/{level}", response_model=ThresholdResponse)
async def get_level_thresholds(level: str):
    """
    查看指定层级的晋级条件 (公开, 无需认证)。
    
    路径参数: L0, L1, L2, L3, L4
    """
    from dual_track_engine import PROMOTION_THRESHOLDS
    
    key_map = {
        "L0": "L0_TO_L1", "L1": "L1_TO_L2", "L2": "L2_TO_L3",
        "L3": "L3_TO_L4", "L4": "L4_TO_L5",
    }
    
    promo_key = key_map.get(level.upper())
    if not promo_key:
        raise HTTPException(404, detail=f"Level {level} not found or is max level")
    
    threshold = PROMOTION_THRESHOLDS[promo_key]
    pts = threshold.points
    grw = threshold.growth
    
    return ThresholdResponse(
        promotion_key=promo_key,
        from_level=threshold.from_level.value,
        to_level=threshold.to_level.value,
        points_threshold={
            "growth": pts.growth,
            "contribution": pts.contribution,
            "influence": pts.influence,
            "is_hard_gate": pts.is_hard_gate,
        },
        growth_requirements={
            "peer_required": grw.peer_req.total_required,
            "peer_progressed": grw.peer_req.min_progressed,
            "peer_advanced": grw.peer_req.min_advanced,
            "capabilities": grw.capability_requirements,
            "exams": grw.exam_requirements,
            "ethics": grw.ethics_requirements,
            "min_period_months": grw.min_period_months,
        },
        ceremony={
            "name": grw.ceremony_name,
            "emoji": grw.ceremony_emoji,
        },
    )


# ── 辅助函数 ──

def _next_level(current: str) -> str:
    levels = ["L0", "L1", "L2", "L3", "L4", "L5"]
    idx = levels.index(current) if current in levels else 0
    return levels[min(idx + 1, len(levels) - 1)]

"""
双轨晋级 API 端点
契约来源: Sheet④ 晋级契约 + Sheet⑩ P0 双轨晋级校验引擎

端点清单:
  GET  /api/v1/promotion/status        — 查询当前晋级状态
  GET  /api/v1/promotion/progress      — 别名: 查询晋级进度 (H5前端使用)
  GET  /api/v1/promotion/gap-report    — 获取差距分析报告
  GET  /api/v1/promotion/check         — 手动触发晋级校验
  GET  /api/v1/promotion/rules         — 获取当前等级晋级规则 (H5前端使用)
  POST /api/v1/promotion/ceremony      — 启动晋级仪式
  POST /api/v1/promotion/apply         — 别名: 提交晋级申请 (H5前端使用)
  GET  /api/v1/promotion/peers         — 同道者仪表盘
  GET  /api/v1/promotion/thresholds    — 查看晋级条件
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

from api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/promotion", tags=["dual-track-promotion"])


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
    """获取晋级编排器实例 — 回退到stub"""
    try:
        from core.promotion_service import PromotionService
        return PromotionService()
    except ImportError:
        return _StubOrchestrator()


class _StubOrchestrator:
    """晋级编排器占位 — 依赖模块未就绪时使用"""
    async def check_promotion_eligibility(self, user_id, level):
        return {"state": 1, "state_name": "NORMAL_GROWTH", "guidance_message": "晋级模块初始化中", "ceremony_ready": False}
    async def initiate_ceremony(self, user_id, level):
        return {"success": False, "reason": "晋级模块初始化中"}
    def get_promotion_key(self, level):
        return f"{level}_TO_NEXT"


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


@router.get("/progress", response_model=PromotionStatusResponse)
async def get_promotion_progress(
    user=Depends(get_current_user),
    orchestrator=Depends(get_promotion_orchestrator),
):
    """
    获取晋级进度 (H5前端使用的别名, 等同于 /status)。
    """
    return await get_promotion_status(user=user, orchestrator=orchestrator)


@router.get("/check", response_model=PromotionStatusResponse)
async def manual_check_get(
    user=Depends(get_current_user),
    orchestrator=Depends(get_promotion_orchestrator),
):
    """
    手动触发晋级校验 (GET, H5前端使用)。
    """
    return await _do_manual_check(user, orchestrator)


@router.post("/check", response_model=PromotionStatusResponse)
async def manual_check(
    user=Depends(get_current_user),
    orchestrator=Depends(get_promotion_orchestrator),
):
    """
    手动触发晋级校验 (POST, 后台管理使用)。
    """
    return await _do_manual_check(user, orchestrator)


async def _do_manual_check(user, orchestrator):
    """晋级校验内部实现。"""
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


@router.post("/apply", response_model=CeremonyResponse)
async def apply_promotion(
    user=Depends(get_current_user),
    orchestrator=Depends(get_promotion_orchestrator),
):
    """
    提交晋级申请 (H5前端使用的别名, 等同于 /ceremony)。
    """
    return await start_ceremony(user=user, orchestrator=orchestrator)


@router.get("/rules")
async def get_promotion_rules(
    user=Depends(get_current_user),
):
    """
    获取当前等级的晋级规则 (H5前端使用)。

    返回当前等级到下一等级的晋级条件概览。
    """
    current_level = getattr(user, "level", "L0")
    target = _next_level(current_level)

    # 尝试从 promotion_service 获取真实阈值
    try:
        from core.promotion_service import PROMOTION_THRESHOLDS
        key_map = {
            "L0": "L0_TO_L1", "L1": "L1_TO_L2", "L2": "L2_TO_L3",
            "L3": "L3_TO_L4", "L4": "L4_TO_L5",
        }
        promo_key = key_map.get(current_level.upper())
        if promo_key and promo_key in PROMOTION_THRESHOLDS:
            threshold = PROMOTION_THRESHOLDS[promo_key]
            pts = threshold.points
            grw = threshold.growth
            return {
                "current_level": current_level,
                "target_level": target,
                "promotion_key": promo_key,
                "points_threshold": {
                    "growth": pts.growth,
                    "contribution": pts.contribution,
                    "influence": pts.influence,
                },
                "growth_requirements": {
                    "peer_required": grw.peer_req.total_required,
                    "min_period_months": grw.min_period_months,
                },
                "ceremony_name": grw.ceremony_name,
            }
    except (ImportError, Exception):
        pass

    # Fallback: 返回基础规则概览
    _BASIC_RULES = {
        "L0": {"growth": 100, "contribution": 0, "influence": 0, "peer_required": 0},
        "L1": {"growth": 500, "contribution": 50, "influence": 0, "peer_required": 0},
        "L2": {"growth": 800, "contribution": 200, "influence": 50, "peer_required": 4},
        "L3": {"growth": 1500, "contribution": 600, "influence": 200, "peer_required": 4},
        "L4": {"growth": 3000, "contribution": 1500, "influence": 600, "peer_required": 4},
    }
    rules = _BASIC_RULES.get(current_level.upper(), {})
    return {
        "current_level": current_level,
        "target_level": target,
        "promotion_key": f"{current_level}_TO_{target}",
        "points_threshold": {
            "growth": rules.get("growth", 0),
            "contribution": rules.get("contribution", 0),
            "influence": rules.get("influence", 0),
        },
        "growth_requirements": {
            "peer_required": rules.get("peer_required", 0),
        },
    }


@router.get("/peers", response_model=PeerDashboardResponse)
async def get_peer_dashboard(
    user=Depends(get_current_user),
):
    """
    获取同道者仪表盘。
    
    显示当前层级的4名同道者培养进度。
    """
    try:
        from core.peer_tracking_service import PeerTrackingService
        peer_svc = PeerTrackingService()
    except ImportError:
        raise HTTPException(503, detail="同道者追踪服务初始化中")
    
    current_level = getattr(user, "level", "L0")
    dashboard = await peer_svc.get_peer_dashboard(user.id, current_level)
    
    return PeerDashboardResponse(**dashboard)


@router.get("/thresholds/{level}", response_model=ThresholdResponse)
async def get_level_thresholds(level: str):
    """
    查看指定层级的晋级条件 (公开, 无需认证)。
    
    路径参数: L0, L1, L2, L3, L4
    """
    try:
        from core.promotion_service import PROMOTION_THRESHOLDS
    except ImportError:
        raise HTTPException(503, detail="双轨晋级引擎初始化中")
    
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


# ── 晋级审核端点 (Admin/Coach Review) ──

@router.get("/applications")
async def list_promotion_applications(
    status: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """列出晋级申请 — 供教练/管理员审核"""
    try:
        from core.database import get_async_db_session
        from sqlalchemy import text as sa_text
        async with get_async_db_session() as db:
            conditions = ["1=1"]
            params: dict = {}
            if status and status != "all":
                status_map = {"pending": "pending", "approved": "approved", "rejected": "rejected"}
                if status in status_map:
                    conditions.append("pa.status = :status")
                    params["status"] = status_map[status]
            where = " AND ".join(conditions)
            r = await db.execute(sa_text(f"""
                SELECT pa.id as application_id, pa.user_id,
                       pa.from_role, pa.to_role,
                       pa.status, pa.created_at, pa.reviewed_at, pa.review_comment,
                       u.username, u.full_name
                FROM promotion_applications pa
                LEFT JOIN users u ON u.id = pa.user_id
                WHERE {where}
                ORDER BY pa.created_at DESC LIMIT 100
            """), params)
            items = []
            for row in r.mappings():
                items.append({
                    "application_id": str(row["application_id"]),
                    "user_id": row["user_id"],
                    "username": row.get("username", ""),
                    "full_name": row.get("full_name", ""),
                    "current_level": row.get("from_role", ""),
                    "target_level": row.get("to_role", ""),
                    "status": row.get("status", "pending"),
                    "applied_at": str(row.get("created_at", "")),
                    "reviewed_at": str(row.get("reviewed_at", "")) if row.get("reviewed_at") else None,
                    "reviewer_comment": row.get("review_comment", ""),
                })
            return {"applications": items, "total": len(items)}
    except Exception as e:
        # Table may not exist yet — return empty
        return {"applications": [], "total": 0, "note": str(e)}


class ReviewDecision(BaseModel):
    approved: bool
    reason: Optional[str] = ""


@router.post("/review/{application_id}")
async def review_promotion(
    application_id: str,
    decision: ReviewDecision,
    current_user=Depends(get_current_user),
):
    """审核晋级申请"""
    try:
        from core.database import get_async_db_session
        from sqlalchemy import text as sa_text
        async with get_async_db_session() as db:
            new_status = "approved" if decision.approved else "rejected"
            await db.execute(sa_text("""
                UPDATE promotion_applications
                SET status = :status, reviewed_at = NOW(), reviewer_id = :rid, reviewer_comment = :comment
                WHERE id = :aid
            """), {"status": new_status, "rid": current_user.id, "comment": decision.reason or "", "aid": application_id})
            await db.commit()
            return {"success": True, "application_id": application_id, "status": new_status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 辅助函数 ──

def _next_level(current: str) -> str:
    levels = ["L0", "L1", "L2", "L3", "L4", "L5"]
    idx = levels.index(current) if current in levels else 0
    return levels[min(idx + 1, len(levels) - 1)]

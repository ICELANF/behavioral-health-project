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

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class _ApplyBody(BaseModel):
    statement: Optional[str] = ""
    target_role: Optional[str] = None
    dim_ready: Optional[int] = 0

from api.dependencies import get_current_user, require_roles
from core.models import UserRole
from core.database import get_async_db_session
from sqlalchemy import text as sa_text
from loguru import logger

# 晋级审核允许的角色集合
_REVIEW_ALLOWED = [
    UserRole.COACH, UserRole.SUPERVISOR, UserRole.PROMOTER,
    UserRole.MASTER, UserRole.ADMIN,
]

router = APIRouter(prefix="/api/v1/promotion", tags=["dual-track-promotion"])

# 各等级晋级门槛规则（前端 PromotionProgress.vue 用于进度条渲染）
_LEVEL_RULES: dict = {
    "L0": {"to_role": "grower",   "credits": {"total_min": 10,  "mandatory_min": 5},  "points": {"growth_min": 20,  "contribution_min": 0,  "influence_min": 0},  "companions": {"graduated_min": 0}},
    "L1": {"to_role": "sharer",   "credits": {"total_min": 30,  "mandatory_min": 15}, "points": {"growth_min": 60,  "contribution_min": 20, "influence_min": 0},  "companions": {"graduated_min": 1}},
    "L2": {"to_role": "coach",    "credits": {"total_min": 80,  "mandatory_min": 40}, "points": {"growth_min": 150, "contribution_min": 50, "influence_min": 20}, "companions": {"graduated_min": 3}},
    "L3": {"to_role": "promoter", "credits": {"total_min": 150, "mandatory_min": 80}, "points": {"growth_min": 300, "contribution_min": 100,"influence_min": 60}, "companions": {"graduated_min": 5}},
    "L4": {"to_role": "master",   "credits": {"total_min": 300, "mandatory_min": 150},"points": {"growth_min": 600, "contribution_min": 200,"influence_min": 120},"companions": {"graduated_min": 10}},
}


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


@router.get("/progress")
async def get_promotion_progress(
    user=Depends(get_current_user),
    orchestrator=Depends(get_promotion_orchestrator),
):
    """
    获取晋级进度（H5前端使用）。
    在 /status 基础上追加四维真实数据：学分、积分、同道者、晋级规则。
    """
    base = await get_promotion_status(user=user, orchestrator=orchestrator)
    base_dict = base.model_dump() if hasattr(base, "model_dump") else dict(base)

    # ── 四维真实数据（使用 async context manager）─────────────────
    try:
        async with get_async_db_session() as db:
            cred_row = await db.execute(sa_text(
                "SELECT COALESCE(SUM(credit_earned),0) FROM user_credits WHERE user_id=:uid"
            ), {"uid": user.id})
            total_credits = int(cred_row.scalar() or 0)

            mand_row = await db.execute(sa_text(
                "SELECT COALESCE(SUM(credit_earned),0) FROM user_credits WHERE user_id=:uid AND evidence_type='mandatory'"
            ), {"uid": user.id})
            mandatory_credits = int(mand_row.scalar() or 0)

            pts_rows = await db.execute(sa_text(
                "SELECT point_type, total_points FROM user_points WHERE user_id=:uid"
            ), {"uid": user.id})
            pts_dict: dict = {}
            for r in pts_rows.fetchall():
                pts_dict[str(r[0])] = int(r[1] or 0)

            comp_row = await db.execute(sa_text(
                "SELECT COUNT(*) FROM companion_relations WHERE mentor_id=:uid AND status='graduated'"
            ), {"uid": user.id})
            companions_graduated = int(comp_row.scalar() or 0)

        base_dict.update({
            "total_credits":        total_credits,
            "mandatory_credits":    mandatory_credits,
            "growth_points":        pts_dict.get("growth", 0),
            "contribution_points":  pts_dict.get("contribution", 0),
            "influence_points":     pts_dict.get("influence", 0),
            "companions_graduated": companions_graduated,
            "next_level_rule":      _LEVEL_RULES.get(str(base_dict.get("current_level", "L0"))),
        })
    except Exception as e:
        logger.warning(f"[promotion/progress] extra fields failed: {e}")

    return base_dict


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


@router.post("/apply")
async def apply_promotion(
    body: Optional[_ApplyBody] = None,
    current_user=Depends(get_current_user),
):
    """
    提交晋级申请 (H5前端使用) — 写入 promotion_applications 三级审核队列。
    body 可为空（H5 PromotionProgress 不发 body），此时自动推断目标角色。
    """
    await _ensure_sharer_columns()
    try:
        from core.database import get_async_db_session
        from sqlalchemy import text as sa_text
        async with get_async_db_session() as db:
            from_role = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
            to_role = (body.target_role if body and body.target_role else _next_role(from_role)).upper()
            statement = (body.statement.strip() if body and body.statement else "") or ""
            dim_ready = body.dim_ready or 0 if body else 0
            await db.execute(sa_text("""
                INSERT INTO promotion_applications
                    (user_id, from_role, to_role, status, statement, dim_ready, created_at)
                VALUES (:uid, :from_role, :to_role, 'pending', :stmt, :dim, NOW())
            """), {
                "uid": current_user.id,
                "from_role": from_role.upper(),
                "to_role": to_role,
                "stmt": statement,
                "dim": dim_ready,
            })
            await db.commit()
        return {"success": True, "message": "申请已提交，等待教练审核"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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


# ── 晋级审核端点 (三级审核体系) ──
# 角色 → 负责审核的阶段
_ROLE_STAGE = {
    "coach":      "L1",   # 教练审第一级
    "promoter":   "L2",   # 促进师审第二级
    "supervisor": "L2",   # supervisor 等同促进师
    "master":     "L3",   # 大师终审第三级
    "admin":      None,   # admin 看全部
}


@router.get("/applications")
async def list_promotion_applications(
    status: Optional[str] = None,
    current_user=Depends(require_roles(_REVIEW_ALLOWED)),
):
    """列出晋级申请 — 各角色只看自己该审的阶段"""
    await _ensure_sharer_columns()
    try:
        from core.database import get_async_db_session
        from sqlalchemy import text as sa_text
        async with get_async_db_session() as db:
            role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
            my_stage = _ROLE_STAGE.get(role_val)

            conditions = ["1=1"]
            params: dict = {}

            # 各角色默认只看待自己审的阶段（pending）
            if my_stage:
                conditions.append("pa.review_stage = :stage")
                params["stage"] = my_stage
                # 默认只看 pending，除非明确传 status=all
                if not status or status == "pending":
                    conditions.append("pa.status = 'pending'")
            # status 过滤（admin 或明确指定时生效）
            if status and status not in ("all", "pending"):
                status_map = {"approved": "approved", "rejected": "rejected"}
                if status in status_map:
                    conditions.append("pa.status = :status")
                    params["status"] = status_map[status]

            where = " AND ".join(conditions)
            r = await db.execute(sa_text(f"""
                SELECT pa.id as application_id, pa.user_id,
                       pa.from_role, pa.to_role,
                       pa.status, pa.review_stage,
                       pa.created_at, pa.reviewed_at, pa.review_comment,
                       pa.l2_reviewer_id, pa.l2_reviewed_at, pa.l2_comment,
                       pa.l3_approvals, pa.statement,
                       u.username, u.full_name
                FROM promotion_applications pa
                LEFT JOIN users u ON u.id = pa.user_id
                WHERE {where}
                ORDER BY pa.created_at DESC LIMIT 100
            """), params)
            items = []
            for row in r.mappings():
                l3_approvals = row.get("l3_approvals") or []
                if isinstance(l3_approvals, str):
                    import json
                    try: l3_approvals = json.loads(l3_approvals)
                    except Exception: l3_approvals = []
                items.append({
                    "application_id": str(row["application_id"]),
                    "user_id": row["user_id"],
                    "username": row.get("username", ""),
                    "full_name": row.get("full_name", ""),
                    "current_level": (row.get("from_role") or "").lower(),
                    "target_level": (row.get("to_role") or "").lower(),
                    "status": row.get("status", "pending"),
                    "review_stage": row.get("review_stage", "L1"),
                    "statement": row.get("statement", ""),
                    "applied_at": str(row.get("created_at", "")),
                    "reviewed_at": str(row.get("reviewed_at")) if row.get("reviewed_at") else None,
                    "reviewer_comment": row.get("review_comment", ""),
                    "l3_approval_count": len(l3_approvals),
                    "l3_approvals": l3_approvals,
                })
            return {"applications": items, "total": len(items)}
    except Exception as e:
        return {"applications": [], "total": 0, "note": str(e)}


class SharerApplyRequest(BaseModel):
    statement: str
    target_role: Optional[str] = "sharer"
    dim_ready: Optional[int] = 0


async def _notify_role_users(db, role: str, title: str, body: str):
    try:
        from sqlalchemy import text as sa_text
        from loguru import logger as _log
        await db.execute(sa_text("""
            INSERT INTO notifications (user_id, title, body, is_read, created_at)
            SELECT id, :title, :body, false, NOW()
            FROM users WHERE role = :role AND is_active = true
        """), {"role": role, "title": title, "body": body})
    except Exception as e:
        from loguru import logger as _log
        _log.warning(f"[Promotion] notify_role failed: {e}")


async def _notify_user(db, uid: int, title: str, body: str):
    try:
        from sqlalchemy import text as sa_text
        from loguru import logger as _log
        await db.execute(sa_text("""
            INSERT INTO notifications (user_id, title, body, is_read, created_at)
            VALUES (:uid, :title, :body, false, NOW())
        """), {"uid": uid, "title": title, "body": body})
    except Exception as e:
        from loguru import logger as _log
        _log.warning(f"[Promotion] notify_user failed: {e}")


async def _ensure_sharer_columns():
    """确保 promotion_applications 表存在且含所有必要列（含三级审核字段）"""
    try:
        from core.database import get_async_db_session
        from sqlalchemy import text as sa_text
        async with get_async_db_session() as db:
            await db.execute(sa_text("""
                CREATE TABLE IF NOT EXISTS promotion_applications (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    from_role VARCHAR(50) DEFAULT 'grower',
                    to_role VARCHAR(50) DEFAULT 'sharer',
                    status VARCHAR(20) DEFAULT 'pending',
                    statement TEXT DEFAULT '',
                    dim_ready INTEGER DEFAULT 0,
                    review_comment TEXT DEFAULT '',
                    reviewer_id INTEGER,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    reviewed_at TIMESTAMPTZ
                )
            """))
            # 兼容旧表：补列（含三级审核字段）
            for col_sql in [
                "ALTER TABLE promotion_applications ADD COLUMN IF NOT EXISTS statement TEXT DEFAULT ''",
                "ALTER TABLE promotion_applications ADD COLUMN IF NOT EXISTS dim_ready INTEGER DEFAULT 0",
                # 三级审核字段
                "ALTER TABLE promotion_applications ADD COLUMN IF NOT EXISTS review_stage VARCHAR(10) DEFAULT 'L1'",
                "ALTER TABLE promotion_applications ADD COLUMN IF NOT EXISTS l2_reviewer_id INTEGER",
                "ALTER TABLE promotion_applications ADD COLUMN IF NOT EXISTS l2_reviewed_at TIMESTAMPTZ",
                "ALTER TABLE promotion_applications ADD COLUMN IF NOT EXISTS l2_comment TEXT DEFAULT ''",
                "ALTER TABLE promotion_applications ADD COLUMN IF NOT EXISTS l3_approvals JSONB DEFAULT '[]'",
            ]:
                await db.execute(sa_text(col_sql))
            await db.commit()
    except Exception:
        pass


@router.post("/sharer-apply")
async def sharer_apply(
    body: SharerApplyRequest,
    current_user=Depends(get_current_user),
):
    """提交成为分享者的申请 — 存入 promotion_applications，待教练审核"""
    await _ensure_sharer_columns()
    try:
        from core.database import get_async_db_session
        from sqlalchemy import text as sa_text
        async with get_async_db_session() as db:
            await db.execute(sa_text("""
                INSERT INTO promotion_applications
                    (user_id, from_role, to_role, status, statement, dim_ready, created_at)
                VALUES
                    (:uid, 'GROWER', 'SHARER', 'pending', :stmt, :dim, NOW())
            """), {"uid": current_user.id, "stmt": body.statement.strip(), "dim": body.dim_ready or 0})
            await db.commit()
        return {"success": True, "message": "申请已提交，等待教练审核"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/my-history")
async def my_application_history(
    current_user=Depends(get_current_user),
):
    """获取当前用户自己的晋级申请历史"""
    await _ensure_sharer_columns()
    try:
        from core.database import get_async_db_session
        from sqlalchemy import text as sa_text
        async with get_async_db_session() as db:
            r = await db.execute(sa_text("""
                SELECT id, from_role, to_role, status, statement,
                       created_at, reviewed_at, review_comment
                FROM promotion_applications
                WHERE user_id = :uid
                ORDER BY created_at DESC
                LIMIT 20
            """), {"uid": current_user.id})
            items = [
                {
                    "id": row["id"],
                    "from_role": (row.get("from_role") or "grower").lower(),
                    "to_role": (row.get("to_role") or "sharer").lower(),
                    "status": row.get("status", "pending"),
                    "applied_at": str(row.get("created_at", "")),
                    "reviewed_at": str(row["reviewed_at"]) if row.get("reviewed_at") else None,
                    "review_comment": row.get("review_comment", ""),
                }
                for row in r.mappings()
            ]
        return {"items": items, "total": len(items)}
    except Exception:
        return {"items": [], "total": 0}


class ReviewDecision(BaseModel):
    approved: bool
    reason: Optional[str] = ""


@router.post("/review/{application_id}")
async def review_promotion(
    application_id: str,
    decision: ReviewDecision,
    current_user=Depends(require_roles(_REVIEW_ALLOWED)),
):
    """
    三级审核晋级申请。
    - L1（教练）approve → review_stage 升为 L2，status 保持 pending
    - L2（促进师/supervisor）approve → review_stage 升为 L3
    - L3（大师）approve → 累加 l3_approvals，≥2人后 status=approved，role 更新
    - 任意级别 reject → status=rejected，流程终止
    """
    await _ensure_sharer_columns()
    try:
        from core.database import get_async_db_session
        from sqlalchemy import text as sa_text
        import json as _json
        async with get_async_db_session() as db:
            # 读取申请当前状态
            r = await db.execute(sa_text("""
                SELECT pa.id, pa.user_id, pa.to_role, pa.status, pa.review_stage, pa.l3_approvals,
                       u.full_name
                FROM promotion_applications pa
                LEFT JOIN users u ON u.id = pa.user_id
                WHERE pa.id = :aid
            """), {"aid": application_id})
            row = r.mappings().first()
            if not row:
                raise HTTPException(404, detail="申请不存在")
            if row["status"] in ("approved", "rejected"):
                raise HTTPException(400, detail="该申请已终结，无法重复审核")

            role_val = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
            my_stage = _ROLE_STAGE.get(role_val)
            cur_stage = row.get("review_stage") or "L1"

            # 权限隔离：非 admin 只能审自己阶段的申请
            if role_val != "admin" and my_stage and my_stage != cur_stage:
                raise HTTPException(403, detail=f"当前申请在 {cur_stage} 审核阶段，您负责 {my_stage} 阶段")

            if not decision.approved:
                # 拒绝 — 直接终止
                await db.execute(sa_text("""
                    UPDATE promotion_applications
                    SET status='rejected', reviewed_at=NOW(),
                        reviewer_id=:rid, review_comment=:comment
                    WHERE id=:aid
                """), {"rid": current_user.id, "comment": decision.reason or "", "aid": application_id})
                applicant_name = row.get("full_name") or "您"
                await _notify_user(db, row["user_id"], "晋级申请未通过",
                    f"{applicant_name}的晋级申请未通过审核。原因：{decision.reason or '无'}")
                await db.commit()
                return {"success": True, "application_id": application_id,
                        "status": "rejected", "review_stage": cur_stage}

            # 通过 — 按阶段处理
            if cur_stage == "L1":
                # 教练通过 → 进入促进师审核
                await db.execute(sa_text("""
                    UPDATE promotion_applications
                    SET review_stage='L2', reviewer_id=:rid, review_comment=:comment
                    WHERE id=:aid
                """), {"rid": current_user.id, "comment": decision.reason or "", "aid": application_id})
                applicant_name = row.get("full_name") or "学员"
                target_role = (row.get("to_role") or "sharer").lower()
                notify_body = f"{applicant_name}的晋级申请（→{target_role}）已通过教练初审，请复核。"
                await _notify_role_users(db, "supervisor", "晋级申请待复核", notify_body)
                await _notify_role_users(db, "promoter", "晋级申请待复核", notify_body)
                await db.commit()
                return {"success": True, "application_id": application_id,
                        "status": "pending", "review_stage": "L2",
                        "message": "L1通过，已转交促进师复核"}

            elif cur_stage == "L2":
                # 促进师通过 → 进入大师终审
                await db.execute(sa_text("""
                    UPDATE promotion_applications
                    SET review_stage='L3',
                        l2_reviewer_id=:rid, l2_reviewed_at=NOW(), l2_comment=:comment
                    WHERE id=:aid
                """), {"rid": current_user.id, "comment": decision.reason or "", "aid": application_id})
                applicant_name = row.get("full_name") or "学员"
                target_role = (row.get("to_role") or "sharer").lower()
                await _notify_role_users(db, "master", "晋级申请待终审",
                    f"{applicant_name}的晋级申请（→{target_role}）已通过促进师复核，需大师终审（需2票）。")
                await db.commit()
                return {"success": True, "application_id": application_id,
                        "status": "pending", "review_stage": "L3",
                        "message": "L2通过，已转交大师终审"}

            elif cur_stage == "L3":
                # 大师终审 — 累计票数
                existing = row.get("l3_approvals") or []
                if isinstance(existing, str):
                    try: existing = _json.loads(existing)
                    except Exception: existing = []
                # 去重：同一个大师只算一票
                already_voted = any(a.get("user_id") == current_user.id for a in existing)
                if already_voted:
                    raise HTTPException(400, detail="您已投票，不能重复确认")
                existing.append({
                    "user_id": current_user.id,
                    "approved_at": datetime.utcnow().isoformat(),
                    "comment": decision.reason or "",
                })
                approval_count = len(existing)
                if approval_count >= 2:
                    # ≥2位大师确认 → 正式晋级
                    target_role = (row.get("to_role") or "coach").lower()
                    await db.execute(sa_text("""
                        UPDATE promotion_applications
                        SET status='approved', reviewed_at=NOW(),
                            reviewer_id=:rid, review_comment=:comment,
                            l3_approvals=CAST(:approvals AS jsonb)
                        WHERE id=:aid
                    """), {"rid": current_user.id, "comment": decision.reason or "",
                           "approvals": _json.dumps(existing), "aid": application_id})
                    # 更新用户角色
                    await db.execute(sa_text(
                        "UPDATE users SET role=:role WHERE id=:uid"
                    ), {"role": target_role, "uid": row["user_id"]})
                    await _notify_user(db, row["user_id"], "🎉 晋级审核通过",
                        f"恭喜！您的晋级申请（→{target_role}）已获{approval_count}位大师确认，晋级成功！")
                    await db.commit()
                    return {"success": True, "application_id": application_id,
                            "status": "approved", "review_stage": "DONE",
                            "approval_count": approval_count,
                            "message": f"已获{approval_count}位大师确认，晋级成功！"}
                else:
                    # 票数不足，继续等待
                    await db.execute(sa_text("""
                        UPDATE promotion_applications
                        SET l3_approvals=CAST(:approvals AS jsonb)
                        WHERE id=:aid
                    """), {"approvals": _json.dumps(existing), "aid": application_id})
                    await db.commit()
                    return {"success": True, "application_id": application_id,
                            "status": "pending", "review_stage": "L3",
                            "approval_count": approval_count,
                            "message": f"已有{approval_count}/2位大师确认，等待更多大师投票"}

            raise HTTPException(400, detail=f"未知审核阶段: {cur_stage}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── 辅助函数 ──

def _next_level(current: str) -> str:
    levels = ["L0", "L1", "L2", "L3", "L4", "L5"]
    idx = levels.index(current) if current in levels else 0
    return levels[min(idx + 1, len(levels) - 1)]


def _next_role(current_role: str) -> str:
    order = ["observer", "grower", "sharer", "coach", "promoter", "master"]
    r = (current_role or "").lower()
    idx = order.index(r) if r in order else 0
    return order[min(idx + 1, len(order) - 1)]

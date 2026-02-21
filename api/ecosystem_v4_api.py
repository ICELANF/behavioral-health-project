"""
V4.0 Ecosystem API — Sprint 4 统一端点

MEU-33: BPT-6 Rx Engine
MEU-35: Course-Agent-Stage Mapping
MEU-36: Unified Intervention Narrative
MEU-37: Referral Engine
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db, require_admin
from core.models import User

router = APIRouter(prefix="/api/v1/ecosystem", tags=["ecosystem"])


# ═════════════════════════════════════════════════
# MEU-33: BPT-6 Rx Engine
# ═════════════════════════════════════════════════

@router.get("/rx/generate")
def generate_rx(
    domain: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """生成个性化行为处方 (基于阶段+域+agency)"""
    from core.bpt6_rx_engine import BPT6RxEngine
    engine = BPT6RxEngine(db)
    return engine.generate_rx(current_user.id, domain=domain)


@router.get("/rx/catalog")
def rx_catalog(
    current_user: User = Depends(get_current_user),
):
    """获取完整36变体处方目录"""
    from core.bpt6_rx_engine import BPT6RxEngine
    engine = BPT6RxEngine.__new__(BPT6RxEngine)
    return engine.get_rx_catalog()


@router.get("/rx/adaptation-rules")
def rx_adaptation(
    current_user: User = Depends(get_current_user),
):
    """获取agency适配规则"""
    from core.bpt6_rx_engine import BPT6RxEngine
    engine = BPT6RxEngine.__new__(BPT6RxEngine)
    return engine.get_adaptation_rules()


# ═════════════════════════════════════════════════
# MEU-35: Course-Agent-Stage Mapping
# ═════════════════════════════════════════════════

@router.get("/course/my-phase")
def my_course_phase(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的课程阶段和Agent分配"""
    from core.course_stage_mapping import CourseStageMapper
    mapper = CourseStageMapper(db)
    return mapper.get_user_course_phase(current_user.id)


@router.get("/course/phases")
def all_course_phases(
    current_user: User = Depends(get_current_user),
):
    """获取完整课程阶段定义"""
    from core.course_stage_mapping import CourseStageMapper
    mapper = CourseStageMapper.__new__(CourseStageMapper)
    return mapper.get_all_phases()


@router.get("/course/agent-assignments/{stage}")
def agent_assignments(
    stage: str,
    current_user: User = Depends(get_current_user),
):
    """根据阶段获取Agent分配"""
    from core.course_stage_mapping import CourseStageMapper
    mapper = CourseStageMapper.__new__(CourseStageMapper)
    return mapper.get_agent_assignments(stage)


# ═════════════════════════════════════════════════
# MEU-36: Unified Intervention Narrative
# ═════════════════════════════════════════════════

@router.get("/narrative/timeline")
def user_timeline(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取用户统一干预时间线"""
    from core.unified_narrative_service import UnifiedNarrativeService
    svc = UnifiedNarrativeService(db)
    return svc.get_user_timeline(current_user.id, days, limit)


@router.get("/narrative/summary")
def narrative_summary(
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取成长叙事摘要"""
    from core.unified_narrative_service import UnifiedNarrativeService
    svc = UnifiedNarrativeService(db)
    return svc.get_narrative_summary(current_user.id, days)


# ═════════════════════════════════════════════════
# MEU-37: Referral Engine
# ═════════════════════════════════════════════════

@router.get("/referral/code")
def get_referral_code(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """生成邀请码"""
    from core.referral_engine import ReferralEngine
    engine = ReferralEngine(db)
    return engine.generate_referral_code(current_user.id)


@router.get("/referral/stats")
def referral_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取邀请统计"""
    from core.referral_engine import ReferralEngine
    engine = ReferralEngine(db)
    return engine.get_referral_stats(current_user.id)


@router.get("/referral/growth-stories")
def growth_stories(
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取成长故事 (社交证明)"""
    from core.referral_engine import ReferralEngine
    engine = ReferralEngine(db)
    return {"stories": engine.get_growth_stories(limit)}


@router.get("/referral/social-proof")
def social_proof(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """平台级社交证明数据"""
    from core.referral_engine import ReferralEngine
    engine = ReferralEngine(db)
    return engine.get_platform_social_proof()


@router.get("/referral/qrcode")
def referral_qrcode(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a QR code PNG for the user's referral link."""
    import io
    import os
    from fastapi.responses import StreamingResponse

    try:
        import qrcode
    except ImportError:
        from fastapi import HTTPException
        raise HTTPException(500, "qrcode library not installed")

    domain = os.getenv("BHP_DOMAIN", "localhost:5173")
    scheme = "https" if "localhost" not in domain else "http"
    ref_code = str(current_user.public_id)[:8] if hasattr(current_user, "public_id") and current_user.public_id else str(current_user.id)
    url = f"{scheme}://{domain}/register?ref={ref_code}"

    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=8, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png", headers={
        "Content-Disposition": f"inline; filename=bhp_referral_{ref_code}.png"
    })

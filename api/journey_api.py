"""
V4.0 Journey State API — 用户旅程状态管理

15 endpoints:
  GET  /v1/journey/state              — 当前用户旅程状态
  PUT  /v1/journey/state/stage        — 更新阶段 (coach/admin)
  GET  /v1/journey/agency             — 当前 agency_mode + score + signals
  GET  /v1/journey/trust              — 当前 trust_score + signals
  POST /v1/journey/agency/override    — 教练覆写 agency_mode
  GET  /v1/journey/history            — 旅程状态变更历史
  GET  /v1/journey/activation-paths   — Observer 激活路径状态检查
  POST /v1/journey/activate           — 触发 Observer→Grower 激活
  GET  /v1/journey/stage/progress     — 当前阶段进度详情 (Stage Engine)
  GET  /v1/journey/stage/check        — 检查是否可推进到下一阶段
  POST /v1/journey/stage/advance      — 推进到下一阶段 (coach/admin)
  POST /v1/journey/stage/interrupt    — 记录中断/回退 (coach/admin)
  POST /v1/journey/stage/graduate     — 触发毕业仪式 (coach/admin)
  GET  /v1/journey/stage/transitions  — 阶段跃迁历史
  GET  /v1/journey/stage/config       — 阶段配置信息
"""
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import User, JourneyState, AgencyScoreLog, TrustScoreLog, ROLE_LEVEL
from api.dependencies import get_current_user, require_coach_or_admin, require_admin

router = APIRouter(prefix="/api/v1/journey", tags=["journey"])


# ── Pydantic schemas ────────────────────────────────────

class StageUpdateRequest(BaseModel):
    user_id: int
    new_stage: str  # s0_authorization through s5_graduation


class AgencyOverrideRequest(BaseModel):
    user_id: int
    override_mode: Optional[str] = None  # passive/transitional/active or null to clear


class ActivateRequest(BaseModel):
    conversion_type: Optional[str] = None   # curiosity/time/coach_referred
    conversion_source: Optional[str] = None  # self/community/institution/paid


# ── Helper: ensure journey_state exists ──────────────────

def _ensure_journey(db: Session, user_id: int) -> JourneyState:
    journey = db.query(JourneyState).filter(JourneyState.user_id == user_id).first()
    if not journey:
        journey = JourneyState(user_id=user_id)
        db.add(journey)
        db.flush()
    return journey


# ── 1. GET /state — current journey state ────────────────

@router.get("/state")
def get_journey_state(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的旅程状态"""
    journey = _ensure_journey(db, current_user.id)
    return {
        "user_id": current_user.id,
        "journey_stage": journey.journey_stage,
        "agency_mode": journey.agency_mode,
        "agency_score": journey.agency_score,
        "trust_score": journey.trust_score,
        "conversion_type": journey.conversion_type,
        "conversion_source": journey.conversion_source,
        "activated_at": journey.activated_at.isoformat() if journey.activated_at else None,
        "graduated_at": journey.graduated_at.isoformat() if journey.graduated_at else None,
        "observer_dialog_count": journey.observer_dialog_count,
        "created_at": journey.created_at.isoformat() if journey.created_at else None,
        "updated_at": journey.updated_at.isoformat() if journey.updated_at else None,
    }


# ── 2. PUT /state/stage — update stage (coach/admin) ────

@router.put("/state/stage")
def update_journey_stage(
    req: StageUpdateRequest,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """更新用户的旅程阶段 (需教练或管理员权限)"""
    valid_stages = [
        "s0_authorization", "s1_awareness", "s2_trial",
        "s3_pathway", "s4_internalization", "s5_graduation",
    ]
    if req.new_stage not in valid_stages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"无效阶段: {req.new_stage}, 有效值: {valid_stages}",
        )

    journey = _ensure_journey(db, req.user_id)
    old_stage = journey.journey_stage
    journey.journey_stage = req.new_stage

    if req.new_stage == "s5_graduation" and not journey.graduated_at:
        journey.graduated_at = datetime.utcnow()

    db.commit()
    return {
        "user_id": req.user_id,
        "old_stage": old_stage,
        "new_stage": req.new_stage,
        "updated_by": current_user.id,
    }


# ── 3. GET /agency — current agency_mode + score ────────

@router.get("/agency")
def get_agency_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的 agency_mode 状态"""
    from core.agency_service import AgencyService, AGENCY_INTERACTION_STYLE
    svc = AgencyService(db)
    style = svc.get_interaction_style(current_user.id)
    journey = db.query(JourneyState).filter(
        JourneyState.user_id == current_user.id
    ).first()
    return {
        "user_id": current_user.id,
        **style,
        "agency_signals": journey.agency_signals if journey else {},
        "coach_override": journey.coach_override_agency if journey else None,
    }


# ── 4. GET /trust — current trust_score + signals ───────

@router.get("/trust")
def get_trust_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的信任评分状态"""
    from core.trust_score_service import TrustScoreService
    svc = TrustScoreService(db)
    behavior = svc.get_trust_behavior(current_user.id)
    journey = db.query(JourneyState).filter(
        JourneyState.user_id == current_user.id
    ).first()
    return {
        "user_id": current_user.id,
        **behavior,
        "trust_signals": journey.trust_signals if journey else {},
    }


# ── 5. POST /agency/override — coach override ───────────

@router.post("/agency/override")
def set_agency_override(
    req: AgencyOverrideRequest,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """教练覆写用户的 agency_mode (传 null 清除覆写)"""
    if req.override_mode and req.override_mode not in ("passive", "transitional", "active"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="override_mode 必须是 passive/transitional/active 或 null",
        )
    from core.agency_service import AgencyService
    svc = AgencyService(db)
    result = svc.set_coach_override(req.user_id, req.override_mode, current_user.id)
    db.commit()
    return result


# ── 6. GET /history — journey state change history ───────

@router.get("/history")
def get_journey_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取旅程相关的 agency 和 trust 评分历史"""
    agency_logs = db.query(AgencyScoreLog).filter(
        AgencyScoreLog.user_id == current_user.id
    ).order_by(AgencyScoreLog.created_at.desc()).limit(limit).all()

    trust_logs = db.query(TrustScoreLog).filter(
        TrustScoreLog.user_id == current_user.id
    ).order_by(TrustScoreLog.created_at.desc()).limit(limit).all()

    return {
        "user_id": current_user.id,
        "agency_history": [
            {
                "signal_name": l.signal_name,
                "signal_value": l.signal_value,
                "weight": l.weight,
                "computed_score": l.computed_score,
                "source": l.source,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in agency_logs
        ],
        "trust_history": [
            {
                "signal_name": l.signal_name,
                "signal_value": l.signal_value,
                "weight": l.weight,
                "computed_score": l.computed_score,
                "source": l.source,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in trust_logs
        ],
    }


# ── 7. GET /activation-paths — Observer activation check ─

@router.get("/activation-paths")
def check_activation_paths(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """检查 Observer 的三条激活路径状态 (A/B/C)"""
    from core.trust_score_service import TrustScoreService
    svc = TrustScoreService(db)
    return svc.check_observer_activation(current_user.id)


# ── 8. POST /activate — trigger Observer→Grower ──────────

@router.post("/activate")
def activate_observer(
    req: ActivateRequest = Body(default=ActivateRequest()),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    触发 Observer→Grower 激活。
    用户必须是 Observer 角色且满足至少一条激活路径。
    """
    if current_user.role.value != "observer":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有观察员可以触发激活",
        )

    from core.trust_score_service import TrustScoreService
    svc = TrustScoreService(db)
    activation = svc.check_observer_activation(current_user.id)

    if not activation["eligible"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="尚未满足任何激活路径条件",
        )

    # Update user role to grower
    from core.models import UserRole
    current_user.role = UserRole.GROWER
    current_user.conversion_type = req.conversion_type
    current_user.conversion_source = req.conversion_source

    # Update journey_state
    journey = _ensure_journey(db, current_user.id)
    journey.journey_stage = "s0_authorization"
    journey.conversion_type = req.conversion_type
    journey.conversion_source = req.conversion_source
    journey.activated_at = datetime.utcnow()

    db.commit()
    return {
        "user_id": current_user.id,
        "new_role": "grower",
        "journey_stage": "s0_authorization",
        "conversion_type": req.conversion_type,
        "conversion_source": req.conversion_source,
        "activated_at": journey.activated_at.isoformat(),
        "message": "恭喜!你已成为成长者 🐣",
    }


# ══════════════════════════════════════════════════════════
# Stage Engine Endpoints (MEU-09)
# ══════════════════════════════════════════════════════════

class StageAdvanceRequest(BaseModel):
    user_id: int
    reason: Optional[str] = "coach_decision"
    force: bool = False


class StageInterruptRequest(BaseModel):
    user_id: int
    reason: str = "behavior_regression"
    regress_to: Optional[str] = None


class GraduateRequest(BaseModel):
    user_id: int


# ── 9. GET /stage/progress — 当前阶段进度详情 ──────────────

@router.get("/stage/progress")
def get_stage_progress(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前阶段进度详情 (自己或教练查看学员)"""
    target_id = user_id if user_id else current_user.id
    from core.stage_engine import StageEngine
    engine = StageEngine()
    return engine.get_stage_progress(target_id)


# ── 10. GET /stage/check — 检查是否可推进 ────────────────

@router.get("/stage/check")
def check_stage_advance(
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """检查用户是否满足推进到下一阶段的条件"""
    target_id = user_id if user_id else current_user.id
    from core.stage_engine import StageEngine
    engine = StageEngine()
    return engine.check_advance_eligibility(target_id)


# ── 11. POST /stage/advance — 推进阶段 (coach/admin) ─────

@router.post("/stage/advance")
def advance_stage(
    req: StageAdvanceRequest,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """推进用户到下一阶段 (需教练或管理员权限)"""
    from core.stage_engine import StageEngine
    engine = StageEngine()
    result = engine.advance_stage(
        req.user_id, req.reason, "coach",
        current_user.id, req.force,
    )
    if result["success"]:
        db.commit()
    return result


# ── 12. POST /stage/interrupt — 记录中断/回退 ────────────

@router.post("/stage/interrupt")
def record_interruption(
    req: StageInterruptRequest,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """记录用户阶段中断/回退 (需教练或管理员权限)"""
    from core.stage_engine import StageEngine
    engine = StageEngine()
    result = engine.record_interruption(req.user_id, req.reason, req.regress_to)
    if result["success"]:
        db.commit()
    return result


# ── 13. POST /stage/graduate — 触发毕业 ──────────────────

@router.post("/stage/graduate")
def graduate_user(
    req: GraduateRequest,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """触发用户毕业仪式 (需教练或管理员权限)"""
    from core.stage_engine import StageEngine
    engine = StageEngine()
    result = engine.graduate_user(req.user_id, current_user.id)
    if result["success"]:
        db.commit()
    return result


# ── 14. GET /stage/transitions — 阶段跃迁历史 ────────────

@router.get("/stage/transitions")
def get_stage_transitions(
    user_id: Optional[int] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取阶段跃迁历史记录"""
    target_id = user_id if user_id else current_user.id
    from core.stage_engine import StageEngine
    engine = StageEngine()
    return engine.get_stage_transitions(target_id, limit)


# ── 15. GET /stage/config — 阶段配置信息 ─────────────────

@router.get("/stage/config")
def get_stage_config(current_user: User = Depends(get_current_user)):
    """获取S0-S5全部阶段配置（公开信息）"""
    from core.stage_engine import STAGE_CONFIG, STAGE_ORDER
    return {
        "stages": [
            {
                "stage_id": s,
                "index": i,
                "label": STAGE_CONFIG[s]["label"],
                "min_days": STAGE_CONFIG[s]["min_days"],
                "max_days": STAGE_CONFIG[s]["max_days"],
                "visible_data": STAGE_CONFIG[s]["visible"],
                "coach_focus": STAGE_CONFIG[s]["coach_focus"],
            }
            for i, s in enumerate(STAGE_ORDER)
        ],
    }

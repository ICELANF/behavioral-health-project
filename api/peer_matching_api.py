"""
V4.0 Peer Matching API — 同伴配对 REST 接口

Endpoints:
  GET  /recommend       推荐同伴候选人 (2-3人)
  POST /accept          选择同伴、建立关系
  GET  /my-peer         我的同伴关系
  GET  /stats           配对统计 (admin)
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from loguru import logger
from api.dependencies import get_current_user, get_db, require_admin
from core.models import User, CompanionRelation, CompanionStatus, ROLE_LEVEL_STR
from core.peer_matching_service import PeerMatchingService

router = APIRouter(prefix="/api/v1/peer-matching", tags=["peer-matching"])


# ── Schemas ─────────────────────────────────────

class AcceptPeerRequest(BaseModel):
    mentor_id: int


# ── Endpoints ───────────────────────────────────

@router.get("/recommend")
def recommend_peers(
    top_n: int = Query(3, ge=1, le=10, description="候选人数量"),
    mentor_role: str = Query("sharer", description="导师角色 sharer/coach"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """为当前用户推荐同伴Sharer/Coach候选人"""
    svc = PeerMatchingService(db)
    return svc.recommend_peers(current_user.id, top_n=top_n, mentor_role=mentor_role)


@router.post("/accept")
def accept_peer(
    req: AcceptPeerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """选择同伴、创建配对关系"""
    svc = PeerMatchingService(db)
    result = svc.accept_peer(current_user.id, req.mentor_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    db.commit()

    # 积分记录
    try:
        from core.models import PointTransaction
        db.add(PointTransaction(
            user_id=current_user.id,
            action="peer_accept",
            point_type="contribution",
            amount=3,
        ))
        db.commit()
    except Exception as e:
        logger.warning(f"积分记录失败: {e}")

    return result


@router.get("/my-peer")
def my_peer_relations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """我的同伴关系 (作为mentee和mentor)"""
    as_mentee = db.query(CompanionRelation).filter(
        CompanionRelation.mentee_id == current_user.id,
        CompanionRelation.status == CompanionStatus.ACTIVE.value,
    ).all()

    as_mentor = db.query(CompanionRelation).filter(
        CompanionRelation.mentor_id == current_user.id,
        CompanionRelation.status == CompanionStatus.ACTIVE.value,
    ).all()

    def _rel_dict(r, perspective: str):
        other_id = r.mentor_id if perspective == "mentee" else r.mentee_id
        other = db.query(User).filter(User.id == other_id).first()
        return {
            "relation_id": str(r.id),
            "other_id": other_id,
            "other_name": other.nickname or other.username if other else None,
            "other_role": other.role.value if other and hasattr(other.role, 'value') else None,
            "perspective": perspective,
            "status": r.status,
            "quality_score": float(r.quality_score) if r.quality_score else None,
            "started_at": str(r.started_at) if r.started_at else None,
        }

    return {
        "as_mentee": [_rel_dict(r, "mentee") for r in as_mentee],
        "as_mentor": [_rel_dict(r, "mentor") for r in as_mentor],
    }


@router.get("/stats")
def matching_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """配对统计 (管理员)"""
    svc = PeerMatchingService(db)
    return svc.get_match_stats()

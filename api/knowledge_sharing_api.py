"""
Phase 3: 知识共享 API

提供专家知识贡献、审核、领域共享池查询等端点。

端点:
  POST   /v1/knowledge-sharing/contribute           — 提交知识贡献 (专家)
  GET    /v1/knowledge-sharing/my-contributions      — 我的贡献列表 (专家)
  POST   /v1/knowledge-sharing/{id}/revoke           — 撤回贡献 (专家)
  GET    /v1/knowledge-sharing/review-queue           — 待审核列表 (admin/coach+)
  POST   /v1/knowledge-sharing/{id}/approve           — 审核通过 (admin/coach+)
  POST   /v1/knowledge-sharing/{id}/reject            — 审核拒绝 (admin/coach+)
  GET    /v1/knowledge-sharing/domain-pool            — 领域共享知识库
  GET    /v1/knowledge-sharing/stats                  — 共享统计
  GET    /v1/knowledge-sharing/domains                — 可用领域列表
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import User, KnowledgeDomain, UserActivityLog
from api.dependencies import get_current_user, require_coach_or_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge-sharing", tags=["knowledge-sharing"])


# ── Pydantic Schemas ──

class ContributeRequest(BaseModel):
    document_id: int = Field(..., description="文档ID")
    domain_id: str = Field(..., description="目标共享领域")
    reason: str = Field("", description="贡献理由")

class ReviewRequest(BaseModel):
    comment: str = Field("", description="审核意见")


# ── 专家端点 ──

@router.post("/contribute")
def contribute_knowledge(
    data: ContributeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交知识共享申请 — 将私有文档贡献到领域共享池"""
    from core.knowledge.sharing_service import contribute_document

    # 确定 tenant_id — 从用户关联的专家租户
    tenant_id = _get_user_tenant_id(db, current_user)
    if not tenant_id:
        raise HTTPException(status_code=403, detail="仅专家可贡献知识")

    try:
        contrib = contribute_document(
            db=db,
            document_id=data.document_id,
            tenant_id=tenant_id,
            contributor_id=current_user.id,
            domain_id=data.domain_id,
            reason=data.reason,
        )
        try:
            db.add(UserActivityLog(
                user_id=current_user.id,
                activity_type="knowledge.submit",
                detail={"document_id": data.document_id, "domain_id": data.domain_id, "tenant_id": tenant_id},
                created_at=datetime.utcnow(),
            ))
            db.flush()
        except Exception:
            logger.warning("审计日志写入失败")
        db.commit()
        return {
            "success": True,
            "data": _contrib_to_dict(contrib, db),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my-contributions")
def my_contributions(
    status: Optional[str] = Query(None, description="过滤状态"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询我的知识贡献记录"""
    from core.knowledge.sharing_service import list_contributions

    tenant_id = _get_user_tenant_id(db, current_user)
    if not tenant_id:
        # admin 也可查看 — 不限 tenant
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="仅专家可查看贡献记录")
        tenant_id = None

    result = list_contributions(db, status=status, tenant_id=tenant_id, skip=skip, limit=limit)
    return {
        "success": True,
        "data": {
            "items": [_contrib_to_dict(c, db) for c in result["items"]],
            "total": result["total"],
        },
    }


@router.post("/{contribution_id}/revoke")
def revoke_contribution(
    contribution_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """撤回已共享的知识 — 恢复为私有"""
    from core.knowledge.sharing_service import revoke_contribution as _revoke

    tenant_id = _get_user_tenant_id(db, current_user)
    if not tenant_id:
        raise HTTPException(status_code=403, detail="仅专家可撤回贡献")

    try:
        contrib = _revoke(db, contribution_id, tenant_id)
        try:
            db.add(UserActivityLog(
                user_id=current_user.id,
                activity_type="knowledge.revoke",
                detail={"contribution_id": contribution_id},
                created_at=datetime.utcnow(),
            ))
            db.flush()
        except Exception:
            logger.warning("审计日志写入失败")
        db.commit()
        return {"success": True, "data": _contrib_to_dict(contrib, db)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── 审核端点 (coach+ / admin) ──

@router.get("/review-queue")
def review_queue(
    domain_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """获取待审核贡献队列"""
    from core.knowledge.sharing_service import list_contributions

    result = list_contributions(db, status="pending", domain_id=domain_id, skip=skip, limit=limit)
    return {
        "success": True,
        "data": {
            "items": [_contrib_to_dict(c, db) for c in result["items"]],
            "total": result["total"],
        },
    }


@router.post("/{contribution_id}/approve")
def approve_contribution_endpoint(
    contribution_id: int,
    data: ReviewRequest = ReviewRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """审核通过知识贡献 — 文档 scope 从 tenant → domain"""
    from core.knowledge.sharing_service import approve_contribution

    try:
        contrib = approve_contribution(
            db=db,
            contribution_id=contribution_id,
            reviewer_id=current_user.id,
            comment=data.comment,
        )
        try:
            db.add(UserActivityLog(
                user_id=current_user.id,
                activity_type="knowledge.approve",
                detail={"contribution_id": contribution_id, "reviewer_id": current_user.id, "comment": data.comment[:100] if data.comment else ""},
                created_at=datetime.utcnow(),
            ))
            db.flush()
        except Exception:
            logger.warning("审计日志写入失败")
        db.commit()
        return {"success": True, "data": _contrib_to_dict(contrib, db)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{contribution_id}/reject")
def reject_contribution_endpoint(
    contribution_id: int,
    data: ReviewRequest = ReviewRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """审核拒绝知识贡献"""
    from core.knowledge.sharing_service import reject_contribution

    try:
        contrib = reject_contribution(
            db=db,
            contribution_id=contribution_id,
            reviewer_id=current_user.id,
            comment=data.comment,
        )
        try:
            db.add(UserActivityLog(
                user_id=current_user.id,
                activity_type="knowledge.reject",
                detail={"contribution_id": contribution_id, "reviewer_id": current_user.id, "comment": data.comment[:100] if data.comment else ""},
                created_at=datetime.utcnow(),
            ))
            db.flush()
        except Exception:
            logger.warning("审计日志写入失败")
        db.commit()
        return {"success": True, "data": _contrib_to_dict(contrib, db)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── 查询端点 ──

@router.get("/domain-pool")
def domain_pool(
    domain_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查询领域共享知识库"""
    from core.knowledge.sharing_service import list_domain_shared_documents

    result = list_domain_shared_documents(db, domain_id=domain_id, skip=skip, limit=limit)
    return {
        "success": True,
        "data": {
            "items": [_doc_to_dict(d) for d in result["items"]],
            "total": result["total"],
        },
    }


@router.get("/stats")
def sharing_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """知识共享统计"""
    from core.knowledge.sharing_service import get_sharing_stats

    stats = get_sharing_stats(db)
    return {"success": True, "data": stats}


@router.get("/domains")
def list_domains(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """可用知识领域列表"""
    domains = db.query(KnowledgeDomain).filter(
        KnowledgeDomain.is_active == True,
    ).order_by(KnowledgeDomain.domain_id).all()
    return {
        "success": True,
        "data": [
            {
                "domain_id": d.domain_id,
                "label": d.label,
                "description": d.description,
            }
            for d in domains
        ],
    }


# ── 辅助函数 ──

def _get_user_tenant_id(db: Session, user: User) -> Optional[str]:
    """获取用户关联的专家租户ID"""
    from core.models import ExpertTenant
    tenant = db.query(ExpertTenant).filter(
        ExpertTenant.expert_user_id == user.id,
    ).first()
    return tenant.id if tenant else None


def _contrib_to_dict(contrib, db: Session) -> dict:
    """贡献记录序列化"""
    from core.models import KnowledgeDocument
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == contrib.document_id,
    ).first()
    return {
        "id": contrib.id,
        "document_id": contrib.document_id,
        "document_title": doc.title if doc else "",
        "document_scope": doc.scope if doc else "",
        "tenant_id": contrib.tenant_id,
        "contributor_id": contrib.contributor_id,
        "domain_id": contrib.domain_id,
        "reason": contrib.reason,
        "status": contrib.status,
        "reviewer_id": contrib.reviewer_id,
        "review_comment": contrib.review_comment,
        "reviewed_at": contrib.reviewed_at.isoformat() if contrib.reviewed_at else None,
        "created_at": contrib.created_at.isoformat() if contrib.created_at else None,
    }


def _doc_to_dict(doc) -> dict:
    """文档序列化"""
    return {
        "id": doc.id,
        "title": doc.title,
        "domain_id": doc.domain_id,
        "scope": doc.scope,
        "author": doc.author,
        "tenant_id": doc.tenant_id,
        "evidence_tier": doc.evidence_tier,
        "chunk_count": doc.chunk_count,
        "description": doc.description,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
    }

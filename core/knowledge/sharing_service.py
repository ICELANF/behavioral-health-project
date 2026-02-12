"""
知识共享服务 — Phase 3 知识共享层

提供专家私有知识 → 领域共享池的贡献/审核/撤回机制。
审核通过后, 文档 scope 从 'tenant' → 'domain', chunks 同步更新。
"""

import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from core.models import (
    KnowledgeDocument, KnowledgeChunk, KnowledgeContribution,
    KnowledgeDomain, User,
)

logger = logging.getLogger(__name__)


def contribute_document(
    db: Session,
    document_id: int,
    tenant_id: str,
    contributor_id: int,
    domain_id: str,
    reason: str = "",
) -> KnowledgeContribution:
    """
    专家提交知识共享申请

    校验:
    - 文档必须存在且属于该租户
    - 文档必须是 scope='tenant' (私有)
    - 不可重复提交 pending 状态的贡献
    """
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == document_id,
        KnowledgeDocument.tenant_id == tenant_id,
    ).first()
    if not doc:
        raise ValueError("文档不存在或不属于该租户")
    if doc.scope != "tenant":
        raise ValueError(f"仅私有文档可贡献到共享池 (当前 scope={doc.scope})")
    if doc.status != "ready":
        raise ValueError(f"文档状态不可贡献 (当前 status={doc.status})")

    # 检查是否已有 pending 贡献
    existing = db.query(KnowledgeContribution).filter(
        KnowledgeContribution.document_id == document_id,
        KnowledgeContribution.status == "pending",
    ).first()
    if existing:
        raise ValueError("该文档已有待审核的贡献申请")

    # 校验目标领域存在
    domain = db.query(KnowledgeDomain).filter(
        KnowledgeDomain.domain_id == domain_id,
        KnowledgeDomain.is_active == True,
    ).first()
    if not domain:
        raise ValueError(f"目标领域不存在: {domain_id}")

    contrib = KnowledgeContribution(
        document_id=document_id,
        tenant_id=tenant_id,
        contributor_id=contributor_id,
        domain_id=domain_id,
        reason=reason,
        status="pending",
    )
    db.add(contrib)
    db.flush()
    logger.info("知识贡献申请: doc=%d, tenant=%s, domain=%s", document_id, tenant_id, domain_id)
    return contrib


def approve_contribution(
    db: Session,
    contribution_id: int,
    reviewer_id: int,
    comment: str = "",
) -> KnowledgeContribution:
    """
    审核通过知识贡献

    操作:
    1. 更新贡献状态为 approved
    2. 更新文档 scope='domain', domain_id=贡献目标领域
    3. 同步更新所有 chunks 的 scope 和 domain_id
    """
    contrib = db.query(KnowledgeContribution).filter(
        KnowledgeContribution.id == contribution_id,
    ).first()
    if not contrib:
        raise ValueError("贡献记录不存在")
    if contrib.status != "pending":
        raise ValueError(f"贡献状态不可审核 (当前={contrib.status})")

    # 更新贡献记录
    contrib.status = "approved"
    contrib.reviewer_id = reviewer_id
    contrib.review_comment = comment
    contrib.reviewed_at = datetime.utcnow()

    # 更新文档 scope
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == contrib.document_id,
    ).first()
    if doc:
        doc.scope = "domain"
        doc.domain_id = contrib.domain_id
        doc.review_status = "approved"
        doc.reviewer_id = reviewer_id
        doc.reviewed_at = datetime.utcnow()

        # 同步 chunks scope + domain_id
        db.query(KnowledgeChunk).filter(
            KnowledgeChunk.document_id == doc.id,
        ).update({
            KnowledgeChunk.scope: "domain",
            KnowledgeChunk.domain_id: contrib.domain_id,
        })

    db.flush()
    logger.info("知识贡献审核通过: contrib=%d, doc=%d → domain=%s",
                contribution_id, contrib.document_id, contrib.domain_id)
    return contrib


def reject_contribution(
    db: Session,
    contribution_id: int,
    reviewer_id: int,
    comment: str = "",
) -> KnowledgeContribution:
    """审核拒绝知识贡献"""
    contrib = db.query(KnowledgeContribution).filter(
        KnowledgeContribution.id == contribution_id,
    ).first()
    if not contrib:
        raise ValueError("贡献记录不存在")
    if contrib.status != "pending":
        raise ValueError(f"贡献状态不可审核 (当前={contrib.status})")

    contrib.status = "rejected"
    contrib.reviewer_id = reviewer_id
    contrib.review_comment = comment
    contrib.reviewed_at = datetime.utcnow()

    db.flush()
    logger.info("知识贡献审核拒绝: contrib=%d, doc=%d", contribution_id, contrib.document_id)
    return contrib


def revoke_contribution(
    db: Session,
    contribution_id: int,
    tenant_id: str,
) -> KnowledgeContribution:
    """
    专家撤回已共享的知识 — 将 scope 从 'domain' 恢复为 'tenant'

    仅 approved 状态且属于该租户的贡献可撤回
    """
    contrib = db.query(KnowledgeContribution).filter(
        KnowledgeContribution.id == contribution_id,
        KnowledgeContribution.tenant_id == tenant_id,
    ).first()
    if not contrib:
        raise ValueError("贡献记录不存在或不属于该租户")
    if contrib.status != "approved":
        raise ValueError(f"仅已通过的贡献可撤回 (当前={contrib.status})")

    # 恢复文档 scope
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == contrib.document_id,
    ).first()
    if doc:
        doc.scope = "tenant"

        # 恢复 chunks scope
        db.query(KnowledgeChunk).filter(
            KnowledgeChunk.document_id == doc.id,
        ).update({
            KnowledgeChunk.scope: "tenant",
        })

    # 标记贡献为 revoked
    contrib.status = "revoked"
    contrib.reviewed_at = datetime.utcnow()

    db.flush()
    logger.info("知识贡献已撤回: contrib=%d, doc=%d → tenant scope", contribution_id, contrib.document_id)
    return contrib


def list_contributions(
    db: Session,
    status: Optional[str] = None,
    domain_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> dict:
    """列表查询贡献记录"""
    q = db.query(KnowledgeContribution)

    if status:
        q = q.filter(KnowledgeContribution.status == status)
    if domain_id:
        q = q.filter(KnowledgeContribution.domain_id == domain_id)
    if tenant_id:
        q = q.filter(KnowledgeContribution.tenant_id == tenant_id)

    total = q.count()
    items = q.order_by(KnowledgeContribution.created_at.desc()).offset(skip).limit(limit).all()

    return {"items": items, "total": total}


def list_domain_shared_documents(
    db: Session,
    domain_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> dict:
    """查询领域共享知识库"""
    q = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.scope == "domain",
        KnowledgeDocument.is_active == True,
        KnowledgeDocument.status == "ready",
    )
    if domain_id:
        q = q.filter(KnowledgeDocument.domain_id == domain_id)

    total = q.count()
    items = q.order_by(KnowledgeDocument.updated_at.desc()).offset(skip).limit(limit).all()

    return {"items": items, "total": total}


def get_sharing_stats(db: Session) -> dict:
    """知识共享统计"""
    total_contributions = db.query(func.count(KnowledgeContribution.id)).scalar() or 0
    pending = db.query(func.count(KnowledgeContribution.id)).filter(
        KnowledgeContribution.status == "pending"
    ).scalar() or 0
    approved = db.query(func.count(KnowledgeContribution.id)).filter(
        KnowledgeContribution.status == "approved"
    ).scalar() or 0
    rejected = db.query(func.count(KnowledgeContribution.id)).filter(
        KnowledgeContribution.status == "rejected"
    ).scalar() or 0
    revoked = db.query(func.count(KnowledgeContribution.id)).filter(
        KnowledgeContribution.status == "revoked"
    ).scalar() or 0

    # 按领域统计共享文档数
    domain_stats = db.query(
        KnowledgeDocument.domain_id,
        func.count(KnowledgeDocument.id),
    ).filter(
        KnowledgeDocument.scope == "domain",
        KnowledgeDocument.is_active == True,
    ).group_by(KnowledgeDocument.domain_id).all()

    return {
        "total_contributions": total_contributions,
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "revoked": revoked,
        "domain_shared_docs": {d: c for d, c in domain_stats},
    }

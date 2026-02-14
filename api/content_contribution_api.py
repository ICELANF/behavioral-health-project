"""
用户知识投稿 & 审核 API
Content Contribution & Review API

路由前缀: /api/v1/contributions
- grower+ 可投稿知识内容
- coach+ 可审核 T4 个人经验
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from loguru import logger

from core.database import get_db
from core.models import User, KnowledgeDocument, TIER_PRIORITY_MAP
from core.auth import get_role_level
from api.dependencies import get_current_user, require_coach_or_admin
from core.knowledge.document_service import (
    create_document,
    update_document,
    approve_document,
    reject_document,
    list_pending_reviews,
    list_user_contributions,
    get_document,
)

router = APIRouter(
    prefix="/api/v1/contributions",
    tags=["contributions"],
)


# ============================================
# Pydantic Schemas
# ============================================

class ContributionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    raw_content: str = Field("", max_length=50000)
    domain_id: Optional[str] = None
    evidence_tier: str = Field("T4", description="T1/T2/T3/T4")
    content_type: Optional[str] = None
    published_date: Optional[str] = None  # ISO datetime string

class ContributionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    raw_content: Optional[str] = Field(None, max_length=50000)
    domain_id: Optional[str] = None
    evidence_tier: Optional[str] = None
    content_type: Optional[str] = None


# ============================================
# Helpers
# ============================================

def _require_grower_or_above(user: User):
    """要求 grower(L1) 及以上角色"""
    level = get_role_level(user.role.value)
    if level < 2:  # grower = level 2
        raise HTTPException(status_code=403, detail="需要成长者(grower)及以上角色")


def _doc_to_dict(doc: KnowledgeDocument, include_content: bool = False) -> dict:
    d = {
        "id": doc.id,
        "title": doc.title,
        "author": doc.author,
        "domain_id": doc.domain_id,
        "evidence_tier": doc.evidence_tier,
        "content_type": doc.content_type,
        "review_status": doc.review_status,
        "reviewer_id": doc.reviewer_id,
        "reviewed_at": doc.reviewed_at.isoformat() if doc.reviewed_at else None,
        "contributor_id": doc.contributor_id,
        "priority": doc.priority,
        "status": doc.status,
        "published_date": doc.published_date.isoformat() if doc.published_date else None,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
    }
    if include_content:
        d["raw_content"] = doc.raw_content or ""
    return d


# ============================================
# 用户投稿端点
# ============================================

@router.post("/submit")
def submit_contribution(
    data: ContributionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """投稿知识内容 (grower+)"""
    _require_grower_or_above(current_user)

    # 解析 published_date
    pub_date = None
    if data.published_date:
        try:
            pub_date = datetime.fromisoformat(data.published_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="published_date 格式无效")

    # 投稿走 platform scope，无 tenant_id
    doc = create_document(
        db,
        tenant_id="",  # 用户投稿不绑定租户
        user=current_user,
        title=data.title,
        raw_content=data.raw_content,
        domain_id=data.domain_id or "",
        evidence_tier=data.evidence_tier,
        content_type=data.content_type,
        published_date=pub_date,
        contributor_id=current_user.id,
    )
    # 覆盖 scope 为 platform（非专家私有）
    doc.scope = "platform"
    db.commit()
    db.refresh(doc)

    try:
        from core.models import PointTransaction
        db.add(PointTransaction(
            user_id=current_user.id,
            action="contribution_submit",
            point_type="contribution",
            amount=5,
        ))
        db.commit()
    except Exception as e:
        logger.warning(f"积分记录失败: {e}")

    return {"success": True, "data": _doc_to_dict(doc)}


@router.get("/my")
def list_my_contributions(
    status: Optional[str] = Query(None, description="pending/approved/rejected"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出我的投稿 (grower+)"""
    _require_grower_or_above(current_user)
    docs = list_user_contributions(db, current_user.id, status=status)
    return {"success": True, "data": [_doc_to_dict(d) for d in docs], "total": len(docs)}


@router.get("/my/{doc_id}")
def get_my_contribution(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取投稿详情 (grower+)"""
    _require_grower_or_above(current_user)
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id,
        KnowledgeDocument.contributor_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="投稿不存在")
    return {"success": True, "data": _doc_to_dict(doc, include_content=True)}


@router.put("/my/{doc_id}")
def update_my_contribution(
    doc_id: int,
    data: ContributionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新草稿投稿 (grower+, 仅 draft/error)"""
    _require_grower_or_above(current_user)

    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id,
        KnowledgeDocument.contributor_id == current_user.id,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="投稿不存在")
    if doc.status not in ("draft", "error"):
        raise HTTPException(status_code=400, detail="仅草稿或错误状态的投稿可编辑")

    if data.title is not None:
        doc.title = data.title
    if data.raw_content is not None:
        doc.raw_content = data.raw_content
    if data.domain_id is not None:
        doc.domain_id = data.domain_id
    if data.evidence_tier is not None:
        doc.evidence_tier = data.evidence_tier
        doc.priority = TIER_PRIORITY_MAP.get(data.evidence_tier, doc.priority)
    if data.content_type is not None:
        doc.content_type = data.content_type
    doc.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(doc)
    return {"success": True, "data": _doc_to_dict(doc)}


# ============================================
# 审核端点 (coach+)
# ============================================

@router.get("/review/pending")
def list_pending(
    domain: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """列出待审核投稿 (coach+)"""
    docs = list_pending_reviews(db, domain=domain)
    return {"success": True, "data": [_doc_to_dict(d) for d in docs], "total": len(docs)}


@router.post("/review/{doc_id}/approve")
def approve(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """审核通过投稿 (coach+)"""
    try:
        doc = approve_document(db, doc_id, current_user.id)
        return {"success": True, "data": _doc_to_dict(doc), "message": "审核通过"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/review/{doc_id}/reject")
def reject(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """审核拒绝投稿 (coach+)"""
    try:
        doc = reject_document(db, doc_id, current_user.id)
        return {"success": True, "data": _doc_to_dict(doc), "message": "已拒绝"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

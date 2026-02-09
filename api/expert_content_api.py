"""
专家内容工作室 API
Expert Content Studio API

路由前缀: /api/v1/tenants/{tenant_id}/content
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from core.models import ExpertTenant, User, ChallengeTemplate
from api.dependencies import get_current_user

from core.knowledge.document_service import (
    create_document,
    update_document,
    publish_document,
    unpublish_document,
    delete_document,
    list_documents,
    get_document,
)

router = APIRouter(
    prefix="/api/v1/tenants/{tenant_id}/content",
    tags=["expert-content"],
)


# ============================================
# Pydantic Schemas
# ============================================

class DocumentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    raw_content: Optional[str] = ""
    author: Optional[str] = ""
    domain_id: Optional[str] = ""
    priority: int = Field(5, ge=1, le=10)
    evidence_tier: Optional[str] = None
    content_type: Optional[str] = None
    published_date: Optional[str] = None  # ISO datetime string
    expires_at: Optional[str] = None  # ISO datetime string

class DocumentUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    raw_content: Optional[str] = None
    domain_id: Optional[str] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    evidence_tier: Optional[str] = None
    content_type: Optional[str] = None
    published_date: Optional[str] = None
    expires_at: Optional[str] = None


# ============================================
# Helpers
# ============================================

def _check_tenant_access(db: Session, tenant_id: str, user: User) -> ExpertTenant:
    """校验租户归属权限"""
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    if user.role.value == "admin":
        return tenant
    if tenant.expert_user_id == user.id:
        return tenant
    raise HTTPException(status_code=403, detail="无权访问此租户")


def _doc_to_dict(doc, include_content: bool = False) -> dict:
    """文档序列化（含治理字段）"""
    d = {
        "id": doc.id,
        "title": doc.title,
        "author": doc.author,
        "domain_id": doc.domain_id,
        "scope": doc.scope,
        "tenant_id": doc.tenant_id,
        "priority": doc.priority,
        "is_active": doc.is_active,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "evidence_tier": doc.evidence_tier,
        "content_type": doc.content_type,
        "published_date": doc.published_date.isoformat() if doc.published_date else None,
        "review_status": doc.review_status,
        "reviewer_id": doc.reviewer_id,
        "reviewed_at": doc.reviewed_at.isoformat() if doc.reviewed_at else None,
        "contributor_id": doc.contributor_id,
        "expires_at": doc.expires_at.isoformat() if doc.expires_at else None,
        "created_at": doc.created_at.isoformat() if doc.created_at else None,
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else None,
    }
    if include_content:
        d["raw_content"] = doc.raw_content or ""
    return d


# ============================================
# 知识文档端点
# ============================================

@router.get("/documents")
def api_list_documents(
    tenant_id: str,
    status: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出知识文档"""
    _check_tenant_access(db, tenant_id, current_user)
    docs = list_documents(db, tenant_id, status=status, domain=domain, keyword=keyword)
    return {
        "success": True,
        "data": [_doc_to_dict(d) for d in docs],
        "total": len(docs),
    }


@router.post("/documents")
def api_create_document(
    tenant_id: str,
    data: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建草稿文档"""
    _check_tenant_access(db, tenant_id, current_user)
    # 解析日期字段
    pub_date = None
    if data.published_date:
        try:
            pub_date = datetime.fromisoformat(data.published_date)
        except ValueError:
            pass
    exp_date = None
    if data.expires_at:
        try:
            exp_date = datetime.fromisoformat(data.expires_at)
        except ValueError:
            pass
    doc = create_document(
        db,
        tenant_id=tenant_id,
        user=current_user,
        title=data.title,
        raw_content=data.raw_content or "",
        author=data.author or "",
        domain_id=data.domain_id or "",
        priority=data.priority,
        evidence_tier=data.evidence_tier,
        content_type=data.content_type,
        published_date=pub_date,
        expires_at=exp_date,
    )
    return {"success": True, "data": _doc_to_dict(doc, include_content=True)}


@router.get("/documents/{doc_id}")
def api_get_document(
    tenant_id: str,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取文档详情（含 raw_content）"""
    _check_tenant_access(db, tenant_id, current_user)
    doc = get_document(db, doc_id, tenant_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"success": True, "data": _doc_to_dict(doc, include_content=True)}


@router.put("/documents/{doc_id}")
def api_update_document(
    tenant_id: str,
    doc_id: int,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新草稿文档"""
    _check_tenant_access(db, tenant_id, current_user)
    # 解析日期字段
    pub_date = None
    if data.published_date:
        try:
            pub_date = datetime.fromisoformat(data.published_date)
        except ValueError:
            pass
    exp_date = None
    if data.expires_at:
        try:
            exp_date = datetime.fromisoformat(data.expires_at)
        except ValueError:
            pass
    try:
        doc = update_document(
            db, doc_id, tenant_id,
            title=data.title,
            raw_content=data.raw_content,
            domain_id=data.domain_id,
            priority=data.priority,
            evidence_tier=data.evidence_tier,
            content_type=data.content_type,
            published_date=pub_date,
            expires_at=exp_date,
        )
        return {"success": True, "data": _doc_to_dict(doc, include_content=True)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/documents/{doc_id}/publish")
def api_publish_document(
    tenant_id: str,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """发布文档（分块 + 嵌入）"""
    _check_tenant_access(db, tenant_id, current_user)
    try:
        doc = publish_document(db, doc_id, tenant_id)
        return {
            "success": True,
            "data": _doc_to_dict(doc),
            "message": f"已生成 {doc.chunk_count} 个文本块",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"发布失败: {str(e)}")


@router.post("/documents/{doc_id}/unpublish")
def api_unpublish_document(
    tenant_id: str,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """撤回文档"""
    _check_tenant_access(db, tenant_id, current_user)
    try:
        doc = unpublish_document(db, doc_id, tenant_id)
        return {"success": True, "data": _doc_to_dict(doc)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/documents/{doc_id}")
def api_delete_document(
    tenant_id: str,
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除文档"""
    _check_tenant_access(db, tenant_id, current_user)
    try:
        delete_document(db, doc_id, tenant_id)
        return {"success": True, "message": "文档已删除"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# 挑战活动端点
# ============================================

@router.get("/challenges")
def api_list_challenges(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出本专家创建的挑战模板"""
    _check_tenant_access(db, tenant_id, current_user)

    # 查找该专家创建的挑战模板
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    templates = db.query(ChallengeTemplate).filter(
        ChallengeTemplate.created_by == tenant.expert_user_id
    ).order_by(ChallengeTemplate.created_at.desc()).all()

    return {
        "success": True,
        "data": [
            {
                "id": t.id,
                "title": t.title,
                "category": t.category,
                "duration_days": t.duration_days,
                "status": t.status.value if hasattr(t.status, 'value') else t.status,
                "enrollment_count": t.enrollment_count or 0,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in templates
        ],
    }

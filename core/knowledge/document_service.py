"""
专家知识文档服务

提供知识文档 CRUD、发布（分块 + 嵌入）、撤回、删除等操作。
包含内容治理：证据分层、审核流程、过期降权。
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from core.models import KnowledgeDocument, KnowledgeChunk, User, TIER_PRIORITY_MAP
from core.knowledge.embedding_service import EmbeddingService
from core.knowledge.chunker import chunk_markdown

logger = logging.getLogger(__name__)


def create_document(
    db: Session,
    tenant_id: str,
    user: User,
    title: str,
    raw_content: str = "",
    author: str = "",
    domain_id: str = "",
    priority: int = 5,
    evidence_tier: Optional[str] = None,
    content_type: Optional[str] = None,
    published_date: Optional[datetime] = None,
    contributor_id: Optional[int] = None,
    expires_at: Optional[datetime] = None,
) -> KnowledgeDocument:
    """创建草稿文档（含治理字段）"""
    # tier → priority 自动映射
    tier = evidence_tier or "T3"
    mapped_priority = TIER_PRIORITY_MAP.get(tier, priority)

    # T4 个人经验自动设为待审核
    review_status = None
    if tier == "T4":
        review_status = "pending"

    doc = KnowledgeDocument(
        title=title,
        author=author or user.username,
        raw_content=raw_content,
        domain_id=domain_id or None,
        scope="tenant",
        tenant_id=tenant_id,
        priority=mapped_priority,
        is_active=False,
        status="draft",
        chunk_count=0,
        evidence_tier=tier,
        content_type=content_type,
        published_date=published_date,
        review_status=review_status,
        contributor_id=contributor_id,
        expires_at=expires_at,
        created_at=datetime.utcnow(),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def update_document(
    db: Session,
    doc_id: int,
    tenant_id: str,
    title: Optional[str] = None,
    raw_content: Optional[str] = None,
    domain_id: Optional[str] = None,
    priority: Optional[int] = None,
    evidence_tier: Optional[str] = None,
    content_type: Optional[str] = None,
    published_date: Optional[datetime] = None,
    expires_at: Optional[datetime] = None,
) -> KnowledgeDocument:
    """更新草稿文档（仅 draft/error 状态可编辑）"""
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id,
        KnowledgeDocument.tenant_id == tenant_id,
    ).first()
    if not doc:
        raise ValueError("文档不存在")
    if doc.status not in ("draft", "error"):
        raise ValueError("仅草稿或错误状态的文档可编辑")

    if title is not None:
        doc.title = title
    if raw_content is not None:
        doc.raw_content = raw_content
    if domain_id is not None:
        doc.domain_id = domain_id
    if evidence_tier is not None:
        doc.evidence_tier = evidence_tier
        # tier 变更时自动重映射 priority
        doc.priority = TIER_PRIORITY_MAP.get(evidence_tier, doc.priority)
    elif priority is not None:
        doc.priority = priority
    if content_type is not None:
        doc.content_type = content_type
    if published_date is not None:
        doc.published_date = published_date
    if expires_at is not None:
        doc.expires_at = expires_at
    doc.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(doc)
    return doc


def publish_document(db: Session, doc_id: int, tenant_id: str) -> KnowledgeDocument:
    """
    发布文档：分块 + 嵌入 + 写入 KnowledgeChunk
    T4 审核守卫：必须 review_status=approved 才可发布
    """
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id,
        KnowledgeDocument.tenant_id == tenant_id,
    ).first()
    if not doc:
        raise ValueError("文档不存在")
    if not doc.raw_content or not doc.raw_content.strip():
        raise ValueError("文档内容为空，无法发布")

    # T4 审核守卫
    if doc.evidence_tier == "T4" and doc.review_status != "approved":
        raise ValueError("T4 个人经验内容须审核通过后方可发布")

    # 1. 标记处理中
    doc.status = "processing"
    db.commit()

    embedder = EmbeddingService()
    try:
        # 2. 删除旧 chunks
        db.query(KnowledgeChunk).filter(
            KnowledgeChunk.document_id == doc.id
        ).delete()
        db.flush()

        # 3. 分块
        chunks = chunk_markdown(doc.raw_content)
        if not chunks:
            doc.status = "error"
            db.commit()
            raise ValueError("分块结果为空")

        # 4. 嵌入
        texts = [c["content"] for c in chunks]
        logger.info(f"发布文档 [{doc.title}]: {len(chunks)} 块, 开始嵌入...")
        embeddings = embedder.embed_batch(texts)

        # 5. 创建 chunks
        for i, (chunk_data, embedding) in enumerate(zip(chunks, embeddings)):
            chunk = KnowledgeChunk(
                document_id=doc.id,
                content=chunk_data["content"],
                heading=chunk_data.get("heading", ""),
                chunk_index=i,
                doc_title=doc.title,
                doc_author=doc.author,
                doc_source=f"expert:{tenant_id}",
                scope="tenant",
                domain_id=doc.domain_id,
                tenant_id=tenant_id,
                embedding=json.dumps(embedding) if embedding else None,
                created_at=datetime.utcnow(),
            )
            db.add(chunk)

        # 6. 更新状态
        doc.status = "ready"
        doc.is_active = True
        doc.chunk_count = len(chunks)
        doc.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(doc)

        logger.info(f"文档 [{doc.title}] 发布成功: {len(chunks)} 块")
        return doc

    except Exception as e:
        db.rollback()
        # 恢复文档状态为 error
        doc_reload = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.id == doc_id
        ).first()
        if doc_reload:
            doc_reload.status = "error"
            db.commit()
        logger.error(f"发布文档失败: {e}")
        raise
    finally:
        embedder.close()


def unpublish_document(db: Session, doc_id: int, tenant_id: str) -> KnowledgeDocument:
    """撤回文档：status → draft, is_active = False"""
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id,
        KnowledgeDocument.tenant_id == tenant_id,
    ).first()
    if not doc:
        raise ValueError("文档不存在")

    doc.status = "draft"
    doc.is_active = False
    doc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(doc)
    return doc


def delete_document(db: Session, doc_id: int, tenant_id: str):
    """删除文档（级联删除 chunks）"""
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id,
        KnowledgeDocument.tenant_id == tenant_id,
    ).first()
    if not doc:
        raise ValueError("文档不存在")

    db.delete(doc)  # cascade 删除 chunks
    db.commit()


def list_documents(
    db: Session,
    tenant_id: str,
    status: Optional[str] = None,
    domain: Optional[str] = None,
    keyword: Optional[str] = None,
) -> List[KnowledgeDocument]:
    """列出专家的知识文档"""
    query = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.tenant_id == tenant_id
    )
    if status:
        query = query.filter(KnowledgeDocument.status == status)
    if domain:
        query = query.filter(KnowledgeDocument.domain_id == domain)
    if keyword:
        query = query.filter(KnowledgeDocument.title.contains(keyword))

    return query.order_by(KnowledgeDocument.created_at.desc()).all()


def get_document(db: Session, doc_id: int, tenant_id: str) -> Optional[KnowledgeDocument]:
    """获取文档详情"""
    return db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id,
        KnowledgeDocument.tenant_id == tenant_id,
    ).first()


# ============================================
# 内容治理 — 审核、过期、投稿查询
# ============================================

def approve_document(
    db: Session,
    doc_id: int,
    reviewer_id: int,
    tenant_id: Optional[str] = None,
) -> KnowledgeDocument:
    """审核通过文档"""
    q = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id)
    if tenant_id:
        q = q.filter(KnowledgeDocument.tenant_id == tenant_id)
    doc = q.first()
    if not doc:
        raise ValueError("文档不存在")
    if doc.review_status != "pending":
        raise ValueError("仅待审核文档可执行审核操作")

    doc.review_status = "approved"
    doc.reviewer_id = reviewer_id
    doc.reviewed_at = datetime.utcnow()
    doc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(doc)
    return doc


def reject_document(
    db: Session,
    doc_id: int,
    reviewer_id: int,
    tenant_id: Optional[str] = None,
) -> KnowledgeDocument:
    """审核拒绝文档"""
    q = db.query(KnowledgeDocument).filter(KnowledgeDocument.id == doc_id)
    if tenant_id:
        q = q.filter(KnowledgeDocument.tenant_id == tenant_id)
    doc = q.first()
    if not doc:
        raise ValueError("文档不存在")
    if doc.review_status != "pending":
        raise ValueError("仅待审核文档可执行审核操作")

    doc.review_status = "rejected"
    doc.reviewer_id = reviewer_id
    doc.reviewed_at = datetime.utcnow()
    doc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(doc)
    return doc


def handle_expired_documents(db: Session) -> int:
    """
    过期文档降权：priority -= 2, 最低 1
    返回处理数量
    """
    now = datetime.utcnow()
    expired_docs = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.expires_at.isnot(None),
        KnowledgeDocument.expires_at < now,
        KnowledgeDocument.is_active == True,
        KnowledgeDocument.priority > 1,
    ).all()

    count = 0
    for doc in expired_docs:
        doc.priority = max(doc.priority - 2, 1)
        doc.updated_at = now
        count += 1

    if count:
        db.commit()
        logger.info(f"[Governance] 过期文档降权: {count} 篇")
    return count


def list_pending_reviews(
    db: Session,
    domain: Optional[str] = None,
) -> List[KnowledgeDocument]:
    """列出待审核文档"""
    query = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.review_status == "pending",
    )
    if domain:
        query = query.filter(KnowledgeDocument.domain_id == domain)
    return query.order_by(KnowledgeDocument.created_at.asc()).all()


def list_user_contributions(
    db: Session,
    contributor_id: int,
    status: Optional[str] = None,
) -> List[KnowledgeDocument]:
    """列出用户投稿"""
    query = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.contributor_id == contributor_id,
    )
    if status:
        query = query.filter(KnowledgeDocument.review_status == status)
    return query.order_by(KnowledgeDocument.created_at.desc()).all()

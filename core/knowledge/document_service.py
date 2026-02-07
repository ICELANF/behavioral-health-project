"""
专家知识文档服务

提供知识文档 CRUD、发布（分块 + 嵌入）、撤回、删除等操作。
"""

import json
import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from core.models import KnowledgeDocument, KnowledgeChunk, User
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
) -> KnowledgeDocument:
    """创建草稿文档"""
    doc = KnowledgeDocument(
        title=title,
        author=author or user.username,
        raw_content=raw_content,
        domain_id=domain_id or None,
        scope="tenant",
        tenant_id=tenant_id,
        priority=priority,
        is_active=False,
        status="draft",
        chunk_count=0,
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
    if priority is not None:
        doc.priority = priority
    doc.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(doc)
    return doc


def publish_document(db: Session, doc_id: int, tenant_id: str) -> KnowledgeDocument:
    """
    发布文档：分块 + 嵌入 + 写入 KnowledgeChunk
    1. status → processing
    2. 删除旧 chunks
    3. chunk_markdown(raw_content)
    4. EmbeddingService.embed_batch(texts)
    5. 批量创建 KnowledgeChunk
    6. status → ready, chunk_count = N
    """
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id,
        KnowledgeDocument.tenant_id == tenant_id,
    ).first()
    if not doc:
        raise ValueError("文档不存在")
    if not doc.raw_content or not doc.raw_content.strip():
        raise ValueError("文档内容为空，无法发布")

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

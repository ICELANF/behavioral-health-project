"""
批量知识灌注编排服务

流程: 上传文件 → 检测类型 → 解压(压缩包) → 转换Markdown → 分块 → 嵌入 → 入库
复用现有 embedding_service + chunker + document_service
"""
import hashlib
import os
import shutil
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from loguru import logger

from core.models import BatchIngestionJob, KnowledgeDocument, KnowledgeChunk
from core.knowledge.file_converter import convert_file_to_markdown, SUPPORTED_EXTENSIONS
from core.knowledge.archive_extractor import extract_archive, is_archive, ARCHIVE_EXTENSIONS
from core.knowledge.chunker import chunk_markdown


def process_batch_upload(
    db: Session,
    user_id: int,
    file_path: str,
    filename: str,
    scope: str = "platform",
    domain_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    evidence_tier: str = "T3",
    priority: int = 5,
) -> BatchIngestionJob:
    """
    处理批量上传

    Args:
        db: 数据库会话
        user_id: 上传用户 ID
        file_path: 上传文件的临时路径
        filename: 原始文件名
        scope: 知识范围 (platform/domain/tenant)
        domain_id: 领域 ID
        tenant_id: 租户 ID

    Returns:
        BatchIngestionJob 记录
    """
    ext = os.path.splitext(filename)[1].lower()

    # 检测文件类型
    if ext in ARCHIVE_EXTENSIONS:
        file_type = ext.lstrip(".")
    elif ext in SUPPORTED_EXTENSIONS:
        file_type = ext.lstrip(".")
    else:
        raise ValueError(f"不支持的文件格式: {ext}")

    # 创建任务记录
    job = BatchIngestionJob(
        user_id=user_id,
        filename=filename,
        file_type=file_type,
        status="processing",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    tmp_dir = None
    try:
        if is_archive(file_path):
            # 压缩包: 解压 → 逐文件处理
            tmp_dir, files = extract_archive(file_path)
            job.total_files = len(files)
            db.commit()

            doc_ids = []
            total_chunks = 0
            for fpath in files:
                try:
                    fname = os.path.basename(fpath)
                    md_text = convert_file_to_markdown(fpath)
                    doc_id, n_chunks = _ingest_single_document(
                        db, user_id, fname, md_text, scope, domain_id, tenant_id,
                        evidence_tier=evidence_tier, priority=priority,
                    )
                    doc_ids.append(doc_id)
                    total_chunks += n_chunks
                    job.processed_files += 1
                    db.commit()
                except Exception as e:
                    logger.warning(f"跳过文件 {fpath}: {e}")

            job.total_chunks = total_chunks
            job.result_doc_ids = doc_ids
        else:
            # 单文件处理
            job.total_files = 1
            db.commit()

            md_text = convert_file_to_markdown(file_path)
            doc_id, n_chunks = _ingest_single_document(
                db, user_id, filename, md_text, scope, domain_id, tenant_id,
                evidence_tier=evidence_tier, priority=priority,
            )
            job.processed_files = 1
            job.total_chunks = n_chunks
            job.result_doc_ids = [doc_id]

        job.status = "completed"
        job.updated_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        logger.error(f"批量灌注失败 job={job.id}: {e}")
        job.status = "failed"
        job.error_message = str(e)[:500]
        job.updated_at = datetime.utcnow()
        db.commit()
    finally:
        if tmp_dir and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)

    return job


def _ingest_single_document(
    db: Session,
    user_id: int,
    filename: str,
    markdown_text: str,
    scope: str,
    domain_id: Optional[str],
    tenant_id: Optional[str],
    evidence_tier: str = "T3",
    priority: int = 5,
) -> tuple:
    """
    灌注单个文档

    Returns:
        (document_id, chunk_count)
    """
    # 去掉扩展名作为标题
    title = os.path.splitext(filename)[0]

    # 计算内容哈希（去重防重复导入）
    file_hash = hashlib.sha256(markdown_text.encode("utf-8", errors="replace")).hexdigest()

    # 去重检查：若已存在相同 hash 的文档则跳过
    existing = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.file_hash == file_hash
    ).first()
    if existing:
        logger.info(f"文档已存在(hash重复)，跳过: {title} → doc_id={existing.id}")
        return existing.id, existing.chunk_count or 0

    # 创建 KnowledgeDocument
    doc = KnowledgeDocument(
        title=title,
        author=f"user_{user_id}",
        source="batch_upload",
        domain_id=domain_id,
        scope=scope,
        tenant_id=tenant_id,
        priority=priority,
        is_active=True,
        status="ready",
        raw_content=markdown_text,
        evidence_tier=evidence_tier,
        file_hash=file_hash,
        file_type="md",
        review_status="not_required",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(doc)
    db.flush()

    # 分块
    chunks = chunk_markdown(markdown_text)
    chunk_count = len(chunks)

    # 嵌入 + 入库
    try:
        from core.knowledge.embedding_service import get_embedding
        for i, chunk_data in enumerate(chunks):
            chunk_text = chunk_data if isinstance(chunk_data, str) else chunk_data.get("content", "")
            heading = "" if isinstance(chunk_data, str) else chunk_data.get("heading", "")

            embedding = None
            try:
                embedding = get_embedding(chunk_text)
            except Exception:
                pass  # 嵌入失败仍存储文本

            import json
            chunk = KnowledgeChunk(
                document_id=doc.id,
                content=chunk_text,
                heading=heading,
                chunk_index=i,
                doc_title=title,
                doc_author=doc.author,
                doc_source="batch_upload",
                scope=scope,
                domain_id=domain_id,
                tenant_id=tenant_id,
                embedding=json.dumps(embedding) if embedding else None,
                created_at=datetime.utcnow(),
            )
            db.add(chunk)
    except ImportError:
        logger.warning("embedding_service 不可用，跳过嵌入")
        for i, chunk_data in enumerate(chunks):
            chunk_text = chunk_data if isinstance(chunk_data, str) else chunk_data.get("content", "")
            heading = "" if isinstance(chunk_data, str) else chunk_data.get("heading", "")
            chunk = KnowledgeChunk(
                document_id=doc.id,
                content=chunk_text,
                heading=heading,
                chunk_index=i,
                doc_title=title,
                scope=scope,
                domain_id=domain_id,
                tenant_id=tenant_id,
                created_at=datetime.utcnow(),
            )
            db.add(chunk)

    doc.chunk_count = chunk_count
    db.commit()

    logger.info(f"文档入库: {title} ({chunk_count} chunks)")
    return doc.id, chunk_count

"""
批量知识灌注 API

支持 PDF/DOCX/TXT/MD/ZIP/7Z/RAR 批量上传
"""
import os
import tempfile
import shutil
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from loguru import logger

from core.database import get_db
from core.models import BatchIngestionJob, User
from api.dependencies import get_current_user, require_coach_or_admin

router = APIRouter(prefix="/api/v1/knowledge", tags=["批量知识灌注"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".zip", ".7z", ".rar"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB


@router.post("/batch-upload")
async def batch_upload(
    file: UploadFile = File(...),
    scope: str = Form("platform"),
    domain_id: Optional[str] = Form(None),
    tenant_id: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """批量上传知识文件(multipart)"""
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"不支持的文件格式: {ext}，支持: {', '.join(ALLOWED_EXTENSIONS)}")

    # 保存到临时文件
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=ext)
    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(400, f"文件过大，最大支持 {MAX_FILE_SIZE // (1024*1024)}MB")

        with os.fdopen(tmp_fd, "wb") as f:
            f.write(content)

        from core.knowledge.batch_ingestion_service import process_batch_upload
        job = process_batch_upload(
            db=db,
            user_id=current_user.id,
            file_path=tmp_path,
            filename=filename,
            scope=scope,
            domain_id=domain_id,
            tenant_id=tenant_id,
        )

        return {
            "job_id": job.id,
            "status": job.status,
            "filename": job.filename,
            "total_files": job.total_files,
            "processed_files": job.processed_files,
            "total_chunks": job.total_chunks,
            "error_message": job.error_message,
        }
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@router.get("/batch-jobs")
def list_batch_jobs(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """列出批量灌注任务"""
    query = db.query(BatchIngestionJob).filter(
        BatchIngestionJob.user_id == current_user.id
    ).order_by(BatchIngestionJob.created_at.desc())
    total = query.count()
    jobs = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "items": [
            {
                "id": j.id,
                "filename": j.filename,
                "file_type": j.file_type,
                "status": j.status,
                "total_files": j.total_files,
                "processed_files": j.processed_files,
                "total_chunks": j.total_chunks,
                "error_message": j.error_message,
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in jobs
        ],
    }


@router.get("/batch-jobs/{job_id}")
def get_batch_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """获取批量灌注任务进度"""
    job = db.query(BatchIngestionJob).filter(
        BatchIngestionJob.id == job_id,
        BatchIngestionJob.user_id == current_user.id,
    ).first()
    if not job:
        raise HTTPException(404, "任务不存在")

    return {
        "id": job.id,
        "filename": job.filename,
        "file_type": job.file_type,
        "status": job.status,
        "total_files": job.total_files,
        "processed_files": job.processed_files,
        "total_chunks": job.total_chunks,
        "error_message": job.error_message,
        "result_doc_ids": job.result_doc_ids,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


@router.delete("/batch-jobs/{job_id}")
def cancel_batch_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """取消/删除批量灌注任务"""
    job = db.query(BatchIngestionJob).filter(
        BatchIngestionJob.id == job_id,
        BatchIngestionJob.user_id == current_user.id,
    ).first()
    if not job:
        raise HTTPException(404, "任务不存在")

    if job.status == "processing":
        raise HTTPException(400, "任务正在处理中，无法取消")

    db.delete(job)
    db.commit()
    return {"message": "任务已删除"}

"""
考试管理 API (admin端)

CRUD: 考试定义、题目分配
"""
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from loguru import logger

from core.database import get_db
from core.models import ExamDefinition, User
from api.dependencies import get_current_user, require_coach_or_admin

router = APIRouter(prefix="/api/v1/certification/exams", tags=["考试管理"])


class ExamCreateRequest(BaseModel):
    exam_name: str
    description: Optional[str] = None
    level: Optional[str] = None
    exam_type: str = "standard"
    passing_score: int = 60
    duration_minutes: int = 60
    max_attempts: int = 3


class ExamUpdateRequest(BaseModel):
    exam_name: Optional[str] = None
    description: Optional[str] = None
    level: Optional[str] = None
    exam_type: Optional[str] = None
    passing_score: Optional[int] = None
    duration_minutes: Optional[int] = None
    max_attempts: Optional[int] = None
    status: Optional[str] = None


def _exam_to_dict(e: ExamDefinition) -> dict:
    return {
        "id": e.id,
        "exam_id": e.exam_id,
        "exam_name": e.exam_name,
        "description": e.description,
        "level": e.level,
        "exam_type": e.exam_type,
        "passing_score": e.passing_score,
        "duration_minutes": e.duration_minutes,
        "max_attempts": e.max_attempts,
        "question_ids": e.question_ids or [],
        "question_count": len(e.question_ids) if e.question_ids else 0,
        "status": e.status,
        "created_by": e.created_by,
        "created_at": e.created_at.isoformat() if e.created_at else None,
    }


@router.post("")
def create_exam(
    req: ExamCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """创建考试"""
    exam = ExamDefinition(
        exam_id=f"EXAM-{uuid.uuid4().hex[:8].upper()}",
        exam_name=req.exam_name,
        description=req.description,
        level=req.level,
        exam_type=req.exam_type,
        passing_score=req.passing_score,
        duration_minutes=req.duration_minutes,
        max_attempts=req.max_attempts,
        question_ids=[],
        status="draft",
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return _exam_to_dict(exam)


@router.get("")
def list_exams(
    status: Optional[str] = None,
    level: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出考试"""
    query = db.query(ExamDefinition)
    if status:
        query = query.filter(ExamDefinition.status == status)
    if level:
        query = query.filter(ExamDefinition.level == level)
    query = query.order_by(ExamDefinition.created_at.desc())
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"total": total, "items": [_exam_to_dict(e) for e in items]}


@router.get("/{exam_id}")
def get_exam(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取考试详情"""
    exam = db.query(ExamDefinition).filter(ExamDefinition.exam_id == exam_id).first()
    if not exam:
        raise HTTPException(404, "考试不存在")
    return _exam_to_dict(exam)


@router.put("/{exam_id}")
def update_exam(
    exam_id: str,
    req: ExamUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """更新考试"""
    exam = db.query(ExamDefinition).filter(ExamDefinition.exam_id == exam_id).first()
    if not exam:
        raise HTTPException(404, "考试不存在")

    for field in ["exam_name", "description", "level", "exam_type",
                   "passing_score", "duration_minutes", "max_attempts", "status"]:
        val = getattr(req, field)
        if val is not None:
            setattr(exam, field, val)

    exam.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(exam)
    return _exam_to_dict(exam)


@router.delete("/{exam_id}")
def delete_exam(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """删除考试(归档)"""
    exam = db.query(ExamDefinition).filter(ExamDefinition.exam_id == exam_id).first()
    if not exam:
        raise HTTPException(404, "考试不存在")
    exam.status = "archived"
    exam.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "已归档"}


@router.post("/{exam_id}/questions")
def assign_questions(
    exam_id: str,
    question_ids: List[str],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """分配题目到考试"""
    exam = db.query(ExamDefinition).filter(ExamDefinition.exam_id == exam_id).first()
    if not exam:
        raise HTTPException(404, "考试不存在")
    exam.question_ids = question_ids
    exam.updated_at = datetime.utcnow()
    db.commit()
    return {"exam_id": exam_id, "question_count": len(question_ids)}


@router.post("/{exam_id}/publish")
def publish_exam(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """发布考试"""
    exam = db.query(ExamDefinition).filter(ExamDefinition.exam_id == exam_id).first()
    if not exam:
        raise HTTPException(404, "考试不存在")
    if not exam.question_ids:
        raise HTTPException(400, "考试未分配题目")
    exam.status = "published"
    exam.updated_at = datetime.utcnow()
    db.commit()
    return {"message": "已发布", "exam_id": exam_id}

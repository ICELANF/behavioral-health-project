"""
题库管理 API

CRUD: 题目银行
"""
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import QuestionBank, User
from api.dependencies import get_current_user, require_coach_or_admin

router = APIRouter(prefix="/api/v1/certification/questions", tags=["题库管理"])


class QuestionCreateRequest(BaseModel):
    content: str
    question_type: str = "single"  # single/multiple/truefalse/short_answer
    options: Optional[list] = None  # [{"key": "A", "text": "..."}, ...]
    answer: list  # ["A"] 或 ["A","C"] 或 ["true"]
    explanation: Optional[str] = None
    domain: Optional[str] = None
    difficulty: str = "medium"
    tags: Optional[list] = None


class QuestionUpdateRequest(BaseModel):
    content: Optional[str] = None
    question_type: Optional[str] = None
    options: Optional[list] = None
    answer: Optional[list] = None
    explanation: Optional[str] = None
    domain: Optional[str] = None
    difficulty: Optional[str] = None
    tags: Optional[list] = None


def _q_to_dict(q: QuestionBank) -> dict:
    return {
        "id": q.id,
        "question_id": q.question_id,
        "content": q.content,
        "question_type": q.question_type,
        "options": q.options,
        "answer": q.answer,
        "explanation": q.explanation,
        "domain": q.domain,
        "difficulty": q.difficulty,
        "tags": q.tags,
        "use_count": getattr(q, "use_count", 0) or 0,
        "correct_rate": getattr(q, "correct_rate", None),
        "created_by": q.created_by,
        "created_at": q.created_at.isoformat() if q.created_at else None,
    }


@router.post("")
def create_question(
    req: QuestionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """创建题目"""
    q = QuestionBank(
        question_id=f"Q-{uuid.uuid4().hex[:8].upper()}",
        content=req.content,
        question_type=req.question_type,
        options=req.options,
        answer=req.answer,
        explanation=req.explanation,
        domain=req.domain,
        difficulty=req.difficulty,
        tags=req.tags,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return _q_to_dict(q)


@router.get("")
def list_questions(
    question_type: Optional[str] = None,
    domain: Optional[str] = None,
    difficulty: Optional[str] = None,
    keyword: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """列出题目"""
    query = db.query(QuestionBank)
    if question_type:
        query = query.filter(QuestionBank.question_type == question_type)
    if domain:
        query = query.filter(QuestionBank.domain == domain)
    if difficulty:
        query = query.filter(QuestionBank.difficulty == difficulty)
    if keyword:
        query = query.filter(QuestionBank.content.ilike(f"%{keyword}%"))
    query = query.order_by(QuestionBank.created_at.desc())
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return {"total": total, "items": [_q_to_dict(q) for q in items]}


@router.get("/{question_id}")
def get_question(
    question_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取题目详情"""
    q = db.query(QuestionBank).filter(QuestionBank.question_id == question_id).first()
    if not q:
        raise HTTPException(404, "题目不存在")
    return _q_to_dict(q)


@router.put("/{question_id}")
def update_question(
    question_id: str,
    req: QuestionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """更新题目"""
    q = db.query(QuestionBank).filter(QuestionBank.question_id == question_id).first()
    if not q:
        raise HTTPException(404, "题目不存在")

    for field in ["content", "question_type", "options", "answer",
                   "explanation", "domain", "difficulty", "tags"]:
        val = getattr(req, field)
        if val is not None:
            setattr(q, field, val)

    q.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(q)
    return _q_to_dict(q)


@router.delete("/{question_id}")
def delete_question(
    question_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """删除题目"""
    q = db.query(QuestionBank).filter(QuestionBank.question_id == question_id).first()
    if not q:
        raise HTTPException(404, "题目不存在")
    db.delete(q)
    db.commit()
    return {"message": "已删除"}


class BulkImportRequest(BaseModel):
    questions: List[QuestionCreateRequest]


@router.post("/bulk")
def bulk_import_questions(
    req: BulkImportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """批量导入题目"""
    imported = 0
    failed = 0
    for item in req.questions:
        try:
            q = QuestionBank(
                question_id=f"Q-{uuid.uuid4().hex[:8].upper()}",
                content=item.content,
                question_type=item.question_type,
                options=item.options,
                answer=item.answer,
                explanation=item.explanation,
                domain=item.domain,
                difficulty=item.difficulty,
                tags=item.tags,
                created_by=current_user.id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(q)
            imported += 1
        except Exception:
            failed += 1
    db.commit()
    return {"imported": imported, "failed": failed}

"""
考试会话 API (用户端)

开始考试 → 提交答案 → 自动评分 → 结果查看
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from loguru import logger

from core.database import get_db
from core.models import ExamDefinition, ExamResult, QuestionBank, User, UserActivityLog
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/certification/sessions", tags=["考试会话"])


class ExamSubmitRequest(BaseModel):
    exam_id: str
    answers: dict  # {"Q-XXXX": "A", "Q-YYYY": ["B","C"], ...}
    duration_seconds: Optional[int] = None


@router.post("/start")
def start_exam(
    exam_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """开始考试: 返回题目列表(不含答案)"""
    exam = db.query(ExamDefinition).filter(
        ExamDefinition.exam_id == exam_id,
        ExamDefinition.status == "published",
    ).first()
    if not exam:
        raise HTTPException(404, "考试不存在或未发布")

    # 检查尝试次数
    attempts = db.query(ExamResult).filter(
        ExamResult.user_id == current_user.id,
        ExamResult.exam_id == exam_id,
    ).count()
    if attempts >= exam.max_attempts:
        raise HTTPException(400, f"已达最大尝试次数 ({exam.max_attempts})")

    # 获取题目(不含答案)
    questions = []
    for qid in (exam.question_ids or []):
        q = db.query(QuestionBank).filter(QuestionBank.question_id == qid).first()
        if q:
            questions.append({
                "question_id": q.question_id,
                "content": q.content,
                "question_type": q.question_type,
                "options": q.options,
                "domain": q.domain,
            })

    return {
        "exam_id": exam.exam_id,
        "exam_name": exam.exam_name,
        "duration_minutes": exam.duration_minutes,
        "passing_score": exam.passing_score,
        "attempt_number": attempts + 1,
        "questions": questions,
    }


@router.post("/submit")
def submit_exam(
    req: ExamSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交考试 → 自动评分"""
    exam = db.query(ExamDefinition).filter(
        ExamDefinition.exam_id == req.exam_id,
    ).first()
    if not exam:
        raise HTTPException(404, "考试不存在")

    # 计算分数
    total_questions = len(exam.question_ids or [])
    if total_questions == 0:
        raise HTTPException(400, "考试无题目")

    correct = 0
    for qid in (exam.question_ids or []):
        q = db.query(QuestionBank).filter(QuestionBank.question_id == qid).first()
        if not q:
            continue
        user_answer = req.answers.get(qid)
        if user_answer is not None:
            # 标准化比较
            correct_answer = q.answer
            if isinstance(correct_answer, list) and isinstance(user_answer, list):
                if sorted(correct_answer) == sorted(user_answer):
                    correct += 1
            elif isinstance(correct_answer, list) and len(correct_answer) == 1:
                if correct_answer[0] == user_answer:
                    correct += 1
            elif str(correct_answer) == str(user_answer):
                correct += 1

    score = round(correct / total_questions * 100)
    status = "passed" if score >= exam.passing_score else "failed"

    # 计算尝试次数
    attempt = db.query(ExamResult).filter(
        ExamResult.user_id == current_user.id,
        ExamResult.exam_id == req.exam_id,
    ).count() + 1

    result = ExamResult(
        user_id=current_user.id,
        exam_id=req.exam_id,
        attempt_number=attempt,
        score=score,
        status=status,
        answers=req.answers,
        duration_seconds=req.duration_seconds,
        created_at=datetime.utcnow(),
    )
    db.add(result)

    # 记录活动
    activity = UserActivityLog(
        user_id=current_user.id,
        activity_type="exam",
        detail={"exam_id": req.exam_id, "score": score, "status": status},
        created_at=datetime.utcnow(),
    )
    db.add(activity)

    # 更新学习统计
    try:
        from core.learning_service import record_quiz_result, record_learning_points
        record_quiz_result(db, current_user.id, status == "passed")
        if status == "passed":
            record_learning_points(db, current_user.id, 50, "exam_pass", "growth", req.exam_id)
    except Exception as e:
        logger.warning(f"更新学习统计失败: {e}")

    db.commit()
    db.refresh(result)

    return {
        "result_id": result.id,
        "exam_id": req.exam_id,
        "score": score,
        "status": status,
        "correct": correct,
        "total": total_questions,
        "attempt_number": attempt,
        "passing_score": exam.passing_score,
    }


@router.get("/{result_id}/result")
def get_result(
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取考试结果"""
    result = db.query(ExamResult).filter(
        ExamResult.id == result_id,
        ExamResult.user_id == current_user.id,
    ).first()
    if not result:
        raise HTTPException(404, "结果不存在")

    # 获取题目详情（含答案和解析）
    exam = db.query(ExamDefinition).filter(ExamDefinition.exam_id == result.exam_id).first()
    questions_detail = []
    if exam:
        for qid in (exam.question_ids or []):
            q = db.query(QuestionBank).filter(QuestionBank.question_id == qid).first()
            if q:
                user_ans = result.answers.get(qid) if result.answers else None
                questions_detail.append({
                    "question_id": q.question_id,
                    "content": q.content,
                    "question_type": q.question_type,
                    "options": q.options,
                    "correct_answer": q.answer,
                    "user_answer": user_ans,
                    "explanation": q.explanation,
                })

    return {
        "result_id": result.id,
        "exam_id": result.exam_id,
        "exam_name": exam.exam_name if exam else None,
        "score": result.score,
        "status": result.status,
        "attempt_number": result.attempt_number,
        "duration_seconds": result.duration_seconds,
        "questions": questions_detail,
        "created_at": result.created_at.isoformat() if result.created_at else None,
    }


@router.get("/my-results")
def my_results(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """我的考试历史"""
    query = db.query(ExamResult).filter(
        ExamResult.user_id == current_user.id,
    ).order_by(ExamResult.created_at.desc())
    total = query.count()
    items = query.offset(skip).limit(limit).all()

    results = []
    for r in items:
        exam = db.query(ExamDefinition).filter(ExamDefinition.exam_id == r.exam_id).first()
        results.append({
            "result_id": r.id,
            "exam_id": r.exam_id,
            "exam_name": exam.exam_name if exam else "未知",
            "score": r.score,
            "status": r.status,
            "attempt_number": r.attempt_number,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    return {"total": total, "items": results}

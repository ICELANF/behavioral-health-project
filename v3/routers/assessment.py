"""
渐进式评估路由
路径前缀: /api/v3/assessment

鉴权: 所有端点需登录, user_id 从 Token 提取
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from v3.database import get_db
from v3.auth import User, get_current_user
from v3.schemas import APIResponse, BatchSubmitRequest, BatchRecommendRequest
from baps.progressive_assessment import (
    get_or_create_session, submit_batch,
    AdaptiveRecommender, ASSESSMENT_BATCHES,
)

router = APIRouter(prefix="/api/v3/assessment", tags=["渐进式评估"])


@router.get("/batches", response_model=APIResponse, summary="查看所有评估批次")
def list_batches():
    """返回评估批次清单 (题数/估时/所属工具)"""
    batches = []
    for b in ASSESSMENT_BATCHES:
        batches.append({
            "batch_id": b["batch_id"],
            "label": b["label"],
            "questionnaire": b.get("questionnaire", ""),
            "question_count": b["question_count"],
            "estimated_minutes": b["estimated_minutes"],
            "priority": b.get("priority", 99),
            "required": b.get("required", False),
        })
    return APIResponse(data=batches)


@router.get("/session", response_model=APIResponse, summary="获取评估进度")
def get_session(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取或创建用户评估会话, 返回已完成批次和总进度"""
    session = get_or_create_session(db, user.id)
    completed = session.completed_batches or []
    total = len(ASSESSMENT_BATCHES)
    return APIResponse(data={
        "session_id": session.id,
        "user_id": user.id,
        "status": session.status,
        "completed_batches": completed,
        "completed_count": len(completed),
        "total_batches": total,
        "progress_pct": round(len(completed) / total * 100, 1) if total > 0 else 0,
    })


@router.post("/submit", response_model=APIResponse, summary="提交评估批次答案")
def submit_assessment_batch(
    req: BatchSubmitRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    提交一个批次的答案

    batch_id: 批次标识 (如 "ttm7", "spi_p1", "hbm" 等)
    answers: 答案 (格式取决于批次类型)
    """
    try:
        result = submit_batch(
            db=db,
            user_id=user.id,
            batch_id=req.batch_id,
            answers=req.answers,
            duration_seconds=req.duration_seconds,
            scores=req.scores,
        )
        db.commit()
        return APIResponse(data=result)
    except ValueError as e:
        return APIResponse(ok=False, message=str(e))


@router.get("/recommend", response_model=APIResponse, summary="推荐下一个评估批次")
def recommend_next(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    自适应推荐下一个评估批次

    根据用户已完成的批次和当前状态, 推荐最有价值的下一批
    """
    recommender = AdaptiveRecommender(db)
    session = get_or_create_session(db, user.id)
    completed = session.completed_batches or []
    recommendation = recommender.recommend_next(user.id, completed)
    return APIResponse(data=recommendation)

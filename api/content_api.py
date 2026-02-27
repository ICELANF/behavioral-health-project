# -*- coding: utf-8 -*-
"""
内容管理 API — 全端点真实 DB 实现

支持：
- 多来源内容管理（平台、专家、教练、用户分享）
- 课程/视频/文章/卡片/案例 统一查询
- 点赞/收藏/评论/分享（toggle，真实计数）
- 学习进度/时长持久化
- 视频配套测试（链接 ExamDefinition + QuestionBank）
- 内容审核队列
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any, AsyncGenerator
import asyncio
import json
import random

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from loguru import logger

from core.content_access_service import get_user_level, get_access_status
from core.auth import get_role_level
from api.dependencies import get_current_user, get_optional_user, require_coach_or_admin
from core.database import get_db
from core.models import (
    User, ContentItem, ContentLike, ContentBookmark, ContentComment,
    UserActivityLog, LearningProgress, LearningTimeLog, LearningPointsLog,
    UserLearningStats, ExamDefinition, QuestionBank, ExamResult,
    PointTransaction,
)

router = APIRouter(prefix="/api/v1/content", tags=["内容管理"])


# ============================================================================
# Pydantic 请求模型
# ============================================================================

class CaseShareCreate(BaseModel):
    """创建案例分享"""
    title: str = Field(..., min_length=2, max_length=50)
    domain: str
    challenge: str = Field(..., min_length=10, max_length=500)
    approach: str = Field(..., min_length=10, max_length=500)
    outcome: str = Field(..., min_length=10, max_length=500)
    reflection: Optional[str] = Field(None, max_length=300)
    is_anonymous: bool = False
    allow_comments: bool = True


class LearningProgressUpdate(BaseModel):
    """学习进度更新"""
    content_id: int
    content_type: str
    progress_percent: int = Field(..., ge=0, le=100)
    position: Optional[str] = None
    time_spent_seconds: int = 0


class QuizSubmission(BaseModel):
    """测试提交"""
    quiz_id: str
    answers: Dict[str, Any]


class ReviewDecision(BaseModel):
    """审核决定"""
    content_id: int
    decision: str  # approved/rejected/revision
    comments: str = ""
    revision_notes: Optional[str] = None


# ============================================================================
# Helper 函数
# ============================================================================

def _get_author_info(db: Session, author_id: int) -> dict:
    """获取作者简要信息"""
    user = db.query(User).filter(User.id == author_id).first()
    if not user:
        return {"id": author_id, "name": "未知", "verified": False}
    return {
        "id": user.id,
        "name": user.username,
        "avatar": None,
        "role": user.role if hasattr(user, "role") else None,
        "verified": get_role_level(user.role.value if hasattr(user.role, 'value') else str(user.role)) >= 4,
    }


def _item_to_card(item: ContentItem, author_info: dict = None) -> dict:
    """ContentItem → 列表卡片 dict"""
    return {
        "id": item.id,
        "type": item.content_type,
        "title": item.title,
        "subtitle": (item.body[:80] + "...") if item.body and len(item.body) > 80 else item.body,
        "cover_url": item.cover_url,
        "media_url": item.media_url,
        "domain": item.domain or "general",
        "level": item.level or "L0",
        "author": author_info or {"name": "平台", "verified": True},
        "view_count": item.view_count or 0,
        "like_count": item.like_count or 0,
        "comment_count": item.comment_count or 0,
        "collect_count": item.collect_count or 0,
        "has_quiz": item.has_quiz,
        "status": item.status,
        "review_status": item.review_status,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def _item_to_detail(db: Session, item: ContentItem) -> dict:
    """ContentItem → 完整详情 dict"""
    author = _get_author_info(db, item.author_id)
    d = {
        "id": item.id,
        "type": item.content_type,
        "title": item.title,
        "body": item.body,
        "description": (item.body[:200] + "...") if item.body and len(item.body) > 200 else item.body,
        "cover_url": item.cover_url,
        "media_url": item.media_url,
        "domain": item.domain or "general",
        "level": item.level or "L0",
        "author": author,
        "tenant_id": item.tenant_id,
        "status": item.status,
        "review_status": item.review_status,
        "has_quiz": item.has_quiz,
        "stats": {
            "view_count": item.view_count or 0,
            "like_count": item.like_count or 0,
            "comment_count": item.comment_count or 0,
            "collect_count": item.collect_count or 0,
        },
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }
    if item.content_type == "video":
        d["video_url"] = item.media_url
    return d


def _get_user_interaction(db: Session, user_id: int, content_id: int) -> dict:
    """获取用户对内容的交互状态"""
    liked = db.query(ContentLike).filter(
        ContentLike.user_id == user_id, ContentLike.content_id == content_id
    ).first() is not None
    collected = db.query(ContentBookmark).filter(
        ContentBookmark.user_id == user_id, ContentBookmark.content_id == content_id
    ).first() is not None
    progress = db.query(LearningProgress).filter(
        LearningProgress.user_id == user_id, LearningProgress.content_id == content_id
    ).first()
    return {
        "liked": liked,
        "collected": collected,
        "completed": progress.status == "completed" if progress else False,
        "progress_percent": int(progress.progress_percent) if progress else 0,
        "last_position": progress.last_position if progress else None,
        "time_spent_seconds": progress.time_spent_seconds if progress else 0,
    }


def _ensure_learning_stats(db: Session, user_id: int) -> UserLearningStats:
    """获取或创建用户学习统计记录"""
    stats = db.query(UserLearningStats).filter(UserLearningStats.user_id == user_id).first()
    if not stats:
        stats = UserLearningStats(user_id=user_id)
        db.add(stats)
        db.flush()
    return stats


# ============================================================================
# 内容列表 API
# ============================================================================

@router.get("")
def get_content_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    source: Optional[str] = None,
    domain: Optional[str] = None,
    level: Optional[str] = None,
    audience: Optional[str] = None,
    keyword: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """获取内容列表（支持匿名浏览，登录用户获得等级门控）"""
    user_level = get_user_level(current_user) if current_user else 0

    query = db.query(ContentItem).filter(ContentItem.status == "published")

    if type:
        query = query.filter(ContentItem.content_type == type)
    if domain:
        query = query.filter(ContentItem.domain == domain)
    if level:
        query = query.filter(ContentItem.level == level)
    if keyword:
        query = query.filter(ContentItem.title.ilike(f"%{keyword}%"))
    if source and source == "expert":
        query = query.filter(ContentItem.tenant_id.isnot(None))
    elif source and source == "platform":
        query = query.filter(ContentItem.tenant_id.is_(None))

    # 排序
    sort_col = getattr(ContentItem, sort_by, ContentItem.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for item in items:
        author = _get_author_info(db, item.author_id)
        card = _item_to_card(item, author)
        card["access_status"] = get_access_status(user_level, item.level or "L0")
        result.append(card)

    return {
        "items": result,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.get("/recommended")
def get_recommended_content(
    limit: int = Query(10, ge=1, le=50),
    domain: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """获取推荐内容（按热度排序，支持匿名浏览）"""
    query = db.query(ContentItem).filter(ContentItem.status == "published")
    if domain:
        query = query.filter(ContentItem.domain == domain)
    items = query.order_by(ContentItem.view_count.desc()).limit(limit).all()
    return [_item_to_card(item, _get_author_info(db, item.author_id)) for item in items]


# ============================================================================
# 课程 API
# ============================================================================

@router.get("/course/{course_id}")
def get_course_detail(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """获取课程详情（支持匿名浏览，含等级门控）"""
    item = db.query(ContentItem).filter(ContentItem.id == course_id).first()
    if not item:
        raise HTTPException(404, "课程不存在")

    user_level = get_user_level(current_user) if current_user else 0
    detail = _item_to_detail(db, item)
    access = get_access_status(user_level, item.level or "L0")
    detail["access_status"] = access

    if not access["accessible"]:
        detail.pop("body", None)
        detail.pop("video_url", None)

    return detail


@router.post("/course/{course_id}/enroll")
def enroll_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """报名课程"""
    item = db.query(ContentItem).filter(ContentItem.id == course_id).first()
    if not item:
        raise HTTPException(404, "课程不存在")

    existing = db.query(LearningProgress).filter(
        LearningProgress.user_id == current_user.id,
        LearningProgress.content_id == course_id,
    ).first()
    if existing:
        return {"success": True, "message": "已报名", "progress": int(existing.progress_percent)}

    progress = LearningProgress(
        user_id=current_user.id,
        content_id=course_id,
        progress_percent=0,
        status="not_started",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(progress)
    db.commit()
    return {"success": True, "message": "报名成功"}


@router.post("/course/{course_id}/progress")
def update_course_progress(
    course_id: int,
    data: LearningProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新课程学习进度"""
    progress = db.query(LearningProgress).filter(
        LearningProgress.user_id == current_user.id,
        LearningProgress.content_id == course_id,
    ).first()
    if not progress:
        progress = LearningProgress(
            user_id=current_user.id,
            content_id=course_id,
            created_at=datetime.utcnow(),
        )
        db.add(progress)

    progress.progress_percent = data.progress_percent
    if data.position is not None:
        progress.last_position = str(data.position)
    progress.time_spent_seconds = (progress.time_spent_seconds or 0) + data.time_spent_seconds
    progress.status = "completed" if data.progress_percent >= 100 else "in_progress"
    progress.updated_at = datetime.utcnow()

    # 记录学习时长
    if data.time_spent_seconds > 0:
        minutes = max(1, data.time_spent_seconds // 60)
        item = db.query(ContentItem).filter(ContentItem.id == course_id).first()
        db.add(LearningTimeLog(
            user_id=current_user.id,
            content_id=course_id,
            domain=item.domain if item else None,
            minutes=minutes,
            earned_at=datetime.utcnow(),
        ))
        stats = _ensure_learning_stats(db, current_user.id)
        stats.total_minutes = (stats.total_minutes or 0) + minutes

    db.commit()
    return {"success": True, "progress": data.progress_percent}


# ============================================================================
# 视频 API
# ============================================================================

@router.get("/video/{video_id}")
def get_video_detail(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取视频详情"""
    item = db.query(ContentItem).filter(ContentItem.id == video_id).first()
    if not item:
        raise HTTPException(404, "视频不存在")

    detail = _item_to_detail(db, item)
    detail["video_url"] = item.media_url
    detail["has_quiz"] = item.has_quiz
    return detail


@router.get("/video/{video_id}/quiz")
def get_video_quiz(
    video_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取视频配套测试"""
    exam_id = f"quiz_video_{video_id}"
    exam = db.query(ExamDefinition).filter(ExamDefinition.exam_id == exam_id).first()
    if not exam:
        raise HTTPException(404, "该视频暂无配套测试")

    questions = []
    if exam.question_ids:
        for qid in exam.question_ids:
            q = db.query(QuestionBank).filter(QuestionBank.question_id == str(qid)).first()
            if q:
                questions.append({
                    "question_id": q.question_id,
                    "type": q.question_type,
                    "content": q.content,
                    "options": q.options or [],
                    "explanation": None,  # 不暴露答案
                })

    return {
        "quiz_id": exam.exam_id,
        "video_id": video_id,
        "title": exam.exam_name,
        "description": exam.description,
        "pass_score": exam.passing_score,
        "max_attempts": exam.max_attempts,
        "questions": questions,
    }


@router.post("/video/{video_id}/quiz/submit")
def submit_video_quiz(
    video_id: int,
    submission: QuizSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交视频测试"""
    exam = db.query(ExamDefinition).filter(ExamDefinition.exam_id == submission.quiz_id).first()
    if not exam:
        raise HTTPException(404, "测试不存在")

    # 检查尝试次数
    attempt_count = db.query(ExamResult).filter(
        ExamResult.user_id == current_user.id,
        ExamResult.exam_id == submission.quiz_id,
    ).count()
    if attempt_count >= exam.max_attempts:
        raise HTTPException(400, f"已达最大尝试次数 ({exam.max_attempts})")

    # 评分
    correct_count = 0
    total_count = len(exam.question_ids or [])
    for qid in (exam.question_ids or []):
        q = db.query(QuestionBank).filter(QuestionBank.question_id == str(qid)).first()
        if not q:
            continue
        user_answer = submission.answers.get(str(qid))
        if user_answer is not None and q.answer is not None:
            expected = q.answer
            if isinstance(expected, list):
                if isinstance(user_answer, list):
                    if sorted(str(a) for a in user_answer) == sorted(str(a) for a in expected):
                        correct_count += 1
                elif len(expected) == 1 and str(user_answer) == str(expected[0]):
                    correct_count += 1
            elif str(user_answer) == str(expected):
                correct_count += 1

    score = int((correct_count / max(total_count, 1)) * 100)
    passed = score >= exam.passing_score

    result = ExamResult(
        user_id=current_user.id,
        exam_id=submission.quiz_id,
        attempt_number=attempt_count + 1,
        score=score,
        status="passed" if passed else "failed",
        answers=submission.answers,
        created_at=datetime.utcnow(),
    )
    db.add(result)

    # 更新学习统计
    stats = _ensure_learning_stats(db, current_user.id)
    stats.quiz_total = (stats.quiz_total or 0) + 1
    if passed:
        stats.quiz_passed = (stats.quiz_passed or 0) + 1
        # 积分奖励
        pts = 10 + (5 if score == 100 else 0)
        stats.total_points = (stats.total_points or 0) + pts
        stats.growth_points = (stats.growth_points or 0) + pts
        db.add(LearningPointsLog(
            user_id=current_user.id, source_type="quiz",
            source_id=submission.quiz_id, points=pts,
            category="growth", earned_at=datetime.utcnow(),
        ))

    db.commit()
    db.refresh(result)

    return {
        "result_id": result.id,
        "quiz_id": submission.quiz_id,
        "score": score,
        "correct_count": correct_count,
        "total_count": total_count,
        "passed": passed,
        "attempt_number": result.attempt_number,
        "submitted_at": result.created_at.isoformat(),
    }


# ============================================================================
# 案例分享 API
# ============================================================================

@router.get("/cases")
def get_case_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    domain: Optional[str] = None,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取案例列表"""
    query = db.query(ContentItem).filter(
        ContentItem.content_type == "case_share",
        ContentItem.status == "published",
    )
    if domain:
        query = query.filter(ContentItem.domain == domain)
    if keyword:
        query = query.filter(ContentItem.title.ilike(f"%{keyword}%"))
    query = query.order_by(ContentItem.created_at.desc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for item in items:
        author = _get_author_info(db, item.author_id)
        result.append({
            "id": item.id,
            "title": item.title,
            "domain": item.domain,
            "challenge": (item.body[:100] + "...") if item.body and len(item.body) > 100 else item.body,
            "author": author,
            "like_count": item.like_count or 0,
            "comment_count": item.comment_count or 0,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        })

    return {"items": result, "total": total, "page": page, "page_size": page_size}


@router.get("/case/{case_id}")
def get_case_detail(
    case_id: int,
    db: Session = Depends(get_db),
):
    """获取案例详情"""
    item = db.query(ContentItem).filter(
        ContentItem.id == case_id,
        ContentItem.content_type == "case_share",
    ).first()
    if not item:
        raise HTTPException(404, "案例不存在")

    # 增加浏览量
    item.view_count = (item.view_count or 0) + 1
    db.commit()

    return _item_to_detail(db, item)


@router.post("/case")
def create_case_share(
    case: CaseShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建案例分享"""
    body = (
        f"**挑战：**\n{case.challenge}\n\n"
        f"**方法：**\n{case.approach}\n\n"
        f"**成果：**\n{case.outcome}"
    )
    if case.reflection:
        body += f"\n\n**反思：**\n{case.reflection}"

    item = ContentItem(
        content_type="case_share",
        title=case.title,
        body=body,
        domain=case.domain,
        author_id=current_user.id,
        status="draft",  # 需审核后发布
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(item)

    db.add(UserActivityLog(
        user_id=current_user.id, activity_type="share",
        detail={"title": case.title, "domain": case.domain},
        created_at=datetime.utcnow(),
    ))
    db.commit()
    db.refresh(item)

    return {"success": True, "id": item.id, "message": "提交成功，等待审核"}


@router.post("/case/{case_id}/like")
def like_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """点赞案例（复用通用 like 逻辑）"""
    item = db.query(ContentItem).filter(ContentItem.id == case_id).first()
    if not item:
        raise HTTPException(404, "案例不存在")

    existing = db.query(ContentLike).filter(
        ContentLike.user_id == current_user.id, ContentLike.content_id == case_id,
    ).first()
    if existing:
        db.delete(existing)
        item.like_count = max(0, (item.like_count or 0) - 1)
        db.commit()
        return {"liked": False, "like_count": item.like_count}
    else:
        db.add(ContentLike(user_id=current_user.id, content_id=case_id, created_at=datetime.utcnow()))
        item.like_count = (item.like_count or 0) + 1
        db.commit()
        return {"liked": True, "like_count": item.like_count}


@router.post("/case/{case_id}/helpful")
def mark_case_helpful(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记案例有帮助（复用收藏逻辑）"""
    item = db.query(ContentItem).filter(ContentItem.id == case_id).first()
    if not item:
        raise HTTPException(404, "案例不存在")

    existing = db.query(ContentBookmark).filter(
        ContentBookmark.user_id == current_user.id, ContentBookmark.content_id == case_id,
    ).first()
    if existing:
        db.delete(existing)
        item.collect_count = max(0, (item.collect_count or 0) - 1)
        db.commit()
        return {"marked": False, "helpful_count": item.collect_count}
    else:
        db.add(ContentBookmark(user_id=current_user.id, content_id=case_id, created_at=datetime.utcnow()))
        item.collect_count = (item.collect_count or 0) + 1
        db.commit()
        return {"marked": True, "helpful_count": item.collect_count}


# ============================================================================
# 学习进度 API
# ============================================================================

@router.get("/user/learning-progress")
def get_user_learning_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户学习进度"""
    stats = _ensure_learning_stats(db, current_user.id)
    db.commit()

    # 本周时长
    week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
    week_minutes = db.query(func.coalesce(func.sum(LearningTimeLog.minutes), 0)).filter(
        LearningTimeLog.user_id == current_user.id,
        LearningTimeLog.earned_at >= week_start.replace(hour=0, minute=0, second=0),
    ).scalar()

    # 今日时长
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_minutes = db.query(func.coalesce(func.sum(LearningTimeLog.minutes), 0)).filter(
        LearningTimeLog.user_id == current_user.id,
        LearningTimeLog.earned_at >= today_start,
    ).scalar()

    # 本月时长
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_minutes = db.query(func.coalesce(func.sum(LearningTimeLog.minutes), 0)).filter(
        LearningTimeLog.user_id == current_user.id,
        LearningTimeLog.earned_at >= month_start,
    ).scalar()

    # 正在学习的课程
    ongoing = db.query(LearningProgress).filter(
        LearningProgress.user_id == current_user.id,
        LearningProgress.status == "in_progress",
    ).order_by(LearningProgress.updated_at.desc()).limit(5).all()

    ongoing_courses = []
    for p in ongoing:
        item = db.query(ContentItem).filter(ContentItem.id == p.content_id).first()
        if item:
            ongoing_courses.append({
                "id": item.id,
                "title": item.title,
                "progress": int(p.progress_percent),
                "last_accessed": p.updated_at.isoformat() if p.updated_at else None,
            })

    role_str = current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)
    is_coach = get_role_level(role_str) >= 4
    if is_coach:
        return {
            "type": "coach",
            "data": {
                "user_id": current_user.id,
                "total_points": stats.total_points or 0,
                "current_level": _level_from_points(stats.total_points or 0),
                "category_points": {
                    "growth": stats.growth_points or 0,
                    "contribution": stats.contribution_points or 0,
                    "influence": stats.influence_points or 0,
                },
                "quiz_total": stats.quiz_total or 0,
                "quiz_passed": stats.quiz_passed or 0,
                "ongoing_courses": ongoing_courses,
            },
        }
    else:
        return {
            "type": "grower",
            "data": {
                "user_id": current_user.id,
                "total_minutes": stats.total_minutes or 0,
                "total_hours": round((stats.total_minutes or 0) / 60, 1),
                "today_minutes": today_minutes,
                "week_minutes": week_minutes,
                "month_minutes": month_minutes,
                "current_streak": stats.current_streak or 0,
                "longest_streak": stats.longest_streak or 0,
                "total_points": stats.total_points or 0,
                "ongoing_courses": ongoing_courses,
            },
        }


def _level_from_points(points: int) -> str:
    """根据积分判断教练等级"""
    if points >= 1000:
        return "L5"
    elif points >= 600:
        return "L4"
    elif points >= 300:
        return "L3"
    elif points >= 150:
        return "L2"
    elif points >= 50:
        return "L1"
    return "L0"


@router.post("/user/learning-progress")
def record_learning_progress(
    data: LearningProgressUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """记录学习进度"""
    # 更新学习进度
    progress = db.query(LearningProgress).filter(
        LearningProgress.user_id == current_user.id,
        LearningProgress.content_id == data.content_id,
    ).first()
    if not progress:
        progress = LearningProgress(
            user_id=current_user.id,
            content_id=data.content_id,
            created_at=datetime.utcnow(),
        )
        db.add(progress)

    progress.progress_percent = data.progress_percent
    if data.position is not None:
        progress.last_position = str(data.position)
    progress.time_spent_seconds = (progress.time_spent_seconds or 0) + data.time_spent_seconds
    progress.status = "completed" if data.progress_percent >= 100 else "in_progress"
    progress.updated_at = datetime.utcnow()

    # 记录时长 + 更新统计
    minutes_earned = 0
    if data.time_spent_seconds > 0:
        minutes_earned = max(1, data.time_spent_seconds // 60)
        item = db.query(ContentItem).filter(ContentItem.id == data.content_id).first()
        db.add(LearningTimeLog(
            user_id=current_user.id,
            content_id=data.content_id,
            domain=item.domain if item else None,
            minutes=minutes_earned,
            earned_at=datetime.utcnow(),
        ))
        stats = _ensure_learning_stats(db, current_user.id)
        stats.total_minutes = (stats.total_minutes or 0) + minutes_earned
        # 更新连续打卡
        today_str = date.today().isoformat()
        if stats.last_learn_date != today_str:
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            if stats.last_learn_date == yesterday:
                stats.current_streak = (stats.current_streak or 0) + 1
            else:
                stats.current_streak = 1
            if (stats.current_streak or 0) > (stats.longest_streak or 0):
                stats.longest_streak = stats.current_streak
            stats.last_learn_date = today_str

    db.commit()
    return {
        "success": True,
        "progress": data.progress_percent,
        "minutes_earned": minutes_earned,
    }


@router.get("/user/learning-history")
def get_learning_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取学习历史"""
    query = db.query(LearningProgress).filter(
        LearningProgress.user_id == current_user.id,
    )
    query = query.order_by(LearningProgress.updated_at.desc())

    total = query.count()
    records = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for p in records:
        item = db.query(ContentItem).filter(ContentItem.id == p.content_id).first()
        if not item:
            continue
        if type and item.content_type != type:
            continue
        items.append({
            "id": p.id,
            "content_id": item.id,
            "content_title": item.title,
            "content_type": item.content_type,
            "progress": int(p.progress_percent),
            "time_spent_minutes": (p.time_spent_seconds or 0) // 60,
            "status": p.status,
            "last_accessed": p.updated_at.isoformat() if p.updated_at else None,
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ============================================================================
# 内容审核 API（管理端）
# ============================================================================

@router.get("/review/queue")
def get_review_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """获取审核队列"""
    query = db.query(ContentItem).filter(ContentItem.status == "draft")
    if type:
        query = query.filter(ContentItem.content_type == type)
    query = query.order_by(ContentItem.created_at.desc())

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for item in items:
        author = _get_author_info(db, item.author_id)
        result.append({
            "content_id": item.id,
            "content_type": item.content_type,
            "content_title": item.title,
            "author": author,
            "submitted_at": item.created_at.isoformat() if item.created_at else None,
        })

    return {"items": result, "total": total, "page": page, "page_size": page_size}


@router.post("/review/submit")
def submit_review(
    decision: ReviewDecision,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """提交审核决定"""
    item = db.query(ContentItem).filter(ContentItem.id == decision.content_id).first()
    if not item:
        raise HTTPException(404, "内容不存在")

    if decision.decision == "approved":
        item.status = "published"
    elif decision.decision == "rejected":
        item.status = "archived"
    elif decision.decision == "revision":
        pass  # 保持 draft 状态

    item.updated_at = datetime.utcnow()
    db.commit()

    return {"success": True, "content_id": item.id, "status": item.status}


# ============================================================================
# 内容详情页 API
# ============================================================================

@router.get("/detail/{content_type}/{content_id}")
def get_content_detail(
    content_type: str,
    content_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
):
    """获取内容详情（支持匿名浏览，登录用户记录浏览历史）"""
    item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not item:
        raise HTTPException(404, "内容不存在")

    # 增加浏览量
    item.view_count = (item.view_count or 0) + 1
    if current_user:
        db.add(UserActivityLog(
            user_id=current_user.id, activity_type="learn",
            detail={"content_id": content_id, "type": content_type},
            created_at=datetime.utcnow(),
        ))
    db.commit()

    detail = _item_to_detail(db, item)
    interaction = _get_user_interaction(db, current_user.id, content_id) if current_user else {}

    return {"content": detail, "user_interaction": interaction}


# ============================================================================
# 评论 API
# ============================================================================

@router.get("/{content_id}/comments")
def get_content_comments(
    content_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = "newest",
    db: Session = Depends(get_db),
):
    """获取内容评论"""
    query = db.query(ContentComment).filter(
        ContentComment.content_id == content_id,
        ContentComment.status == "active",
        ContentComment.parent_id == None,
    )
    if sort_by == "newest":
        query = query.order_by(ContentComment.created_at.desc())
    elif sort_by == "hot":
        query = query.order_by(ContentComment.like_count.desc())
    else:
        query = query.order_by(ContentComment.created_at.asc())

    total = query.count()
    comments = query.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for c in comments:
        user = db.query(User).filter(User.id == c.user_id).first()
        reply_count = db.query(ContentComment).filter(
            ContentComment.parent_id == c.id,
            ContentComment.status == "active",
        ).count()
        items.append({
            "id": c.id,
            "user": {"id": c.user_id, "name": user.username if user else "未知", "avatar": None},
            "content": c.content,
            "rating": c.rating,
            "like_count": c.like_count,
            "reply_count": reply_count,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/{content_id}/comment")
def add_content_comment(
    content_id: int,
    content: str = Body(..., embed=True),
    rating: Optional[int] = Body(None, embed=True, ge=1, le=5),
    parent_id: Optional[int] = Body(None, embed=True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """添加评论"""
    item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not item:
        raise HTTPException(404, "内容不存在")

    comment = ContentComment(
        user_id=current_user.id,
        content_id=content_id,
        parent_id=parent_id,
        content=content,
        rating=rating,
        status="active",
        created_at=datetime.utcnow(),
    )
    db.add(comment)
    item.comment_count = (item.comment_count or 0) + 1

    db.add(UserActivityLog(
        user_id=current_user.id, activity_type="comment",
        detail={"content_id": content_id}, created_at=datetime.utcnow(),
    ))
    db.commit()
    db.refresh(comment)

    return {"success": True, "comment_id": comment.id, "message": "评论发布成功"}


# ============================================================================
# 推荐 + 相关动态
# ============================================================================

@router.get("/feed/related")
def get_related_feed(
    domain: Optional[str] = None,
    content_id: Optional[int] = None,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """获取相关动态（最近发布的内容）"""
    query = db.query(ContentItem).filter(ContentItem.status == "published")
    if domain:
        query = query.filter(ContentItem.domain == domain)
    if content_id:
        query = query.filter(ContentItem.id != content_id)
    items = query.order_by(ContentItem.created_at.desc()).limit(limit).all()

    return {
        "items": [
            {
                "id": item.id,
                "type": item.content_type,
                "title": item.title,
                "summary": (item.body[:60] + "...") if item.body and len(item.body) > 60 else item.body,
                "domain": item.domain,
                "time": item.created_at.strftime("%Y-%m-%d") if item.created_at else None,
            }
            for item in items
        ],
        "total": len(items),
    }


@router.get("/recommendations")
def get_content_recommendations(
    content_id: Optional[int] = None,
    domain: Optional[str] = None,
    limit: int = Query(4, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """获取推荐内容"""
    query = db.query(ContentItem).filter(ContentItem.status == "published")
    if content_id:
        query = query.filter(ContentItem.id != content_id)
    if domain:
        # 优先同领域
        same = query.filter(ContentItem.domain == domain).order_by(
            ContentItem.view_count.desc()
        ).limit(limit).all()
        if len(same) >= limit:
            items = same
        else:
            other = query.filter(ContentItem.domain != domain).order_by(
                ContentItem.view_count.desc()
            ).limit(limit - len(same)).all()
            items = same + other
    else:
        items = query.order_by(ContentItem.view_count.desc()).limit(limit).all()

    return {
        "items": [_item_to_card(item) for item in items],
        "reason": "基于内容热度推荐",
    }


# ============================================================================
# 内容交互 API（点赞/收藏/分享）
# ============================================================================

@router.post("/{content_id}/like")
def like_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """点赞/取消点赞内容 (toggle)"""
    item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not item:
        raise HTTPException(404, "内容不存在")

    existing = db.query(ContentLike).filter(
        ContentLike.user_id == current_user.id,
        ContentLike.content_id == content_id,
    ).first()

    if existing:
        db.delete(existing)
        item.like_count = max(0, (item.like_count or 0) - 1)
        db.commit()
        return {"liked": False, "like_count": item.like_count}
    else:
        db.add(ContentLike(user_id=current_user.id, content_id=content_id, created_at=datetime.utcnow()))
        item.like_count = (item.like_count or 0) + 1
        db.add(UserActivityLog(
            user_id=current_user.id, activity_type="like",
            detail={"content_id": content_id}, created_at=datetime.utcnow(),
        ))
        # 给内容作者 +1 影响力积分 (不给自己点赞加分)
        if item.author_id and item.author_id != current_user.id:
            try:
                db.add(PointTransaction(user_id=item.author_id, action="content_liked",
                                        point_type="influence", amount=1))
                stats = db.query(UserLearningStats).filter(
                    UserLearningStats.user_id == item.author_id).first()
                if stats:
                    stats.influence_points = (stats.influence_points or 0) + 1
            except Exception:
                pass
        db.commit()
        return {"liked": True, "like_count": item.like_count}


@router.post("/{content_id}/collect")
def collect_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """收藏/取消收藏内容 (toggle)"""
    item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not item:
        raise HTTPException(404, "内容不存在")

    existing = db.query(ContentBookmark).filter(
        ContentBookmark.user_id == current_user.id,
        ContentBookmark.content_id == content_id,
    ).first()

    if existing:
        db.delete(existing)
        item.collect_count = max(0, (item.collect_count or 0) - 1)
        db.commit()
        return {"collected": False, "collect_count": item.collect_count}
    else:
        db.add(ContentBookmark(user_id=current_user.id, content_id=content_id, created_at=datetime.utcnow()))
        item.collect_count = (item.collect_count or 0) + 1
        # 给内容作者 +2 影响力积分 (收藏比点赞权重更高)
        if item.author_id and item.author_id != current_user.id:
            try:
                db.add(PointTransaction(user_id=item.author_id, action="content_collected",
                                        point_type="influence", amount=2))
                stats = db.query(UserLearningStats).filter(
                    UserLearningStats.user_id == item.author_id).first()
                if stats:
                    stats.influence_points = (stats.influence_points or 0) + 2
            except Exception:
                pass
        db.commit()
        return {"collected": True, "collect_count": item.collect_count}


@router.post("/{content_id}/share")
def share_content(
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """生成分享数据"""
    item = db.query(ContentItem).filter(ContentItem.id == content_id).first()
    if not item:
        raise HTTPException(404, "内容不存在")

    db.add(UserActivityLog(
        user_id=current_user.id, activity_type="share",
        detail={"content_id": content_id}, created_at=datetime.utcnow(),
    ))
    db.commit()

    return {
        "share_url": f"/content/{item.content_type}/{content_id}",
        "title": item.title,
        "description": (item.body or "")[:100],
        "cover_url": item.cover_url,
    }


@router.get("/user/{user_id}/progress/{content_id}")
def get_user_content_progress(
    user_id: int,
    content_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户对特定内容的学习进度"""
    progress = db.query(LearningProgress).filter(
        LearningProgress.user_id == user_id,
        LearningProgress.content_id == content_id,
    ).first()

    if not progress:
        return {
            "user_id": user_id,
            "content_id": content_id,
            "progress_percent": 0,
            "status": "not_started",
            "time_spent_seconds": 0,
        }

    return {
        "user_id": user_id,
        "content_id": content_id,
        "progress_percent": int(progress.progress_percent),
        "status": progress.status,
        "time_spent_seconds": progress.time_spent_seconds or 0,
        "last_position": progress.last_position,
    }


# ============================================================================
# SSE 实时推送 (保留，用于前端实时更新演示)
# ============================================================================

async def _generate_content_events(content_id: int, db_factory) -> AsyncGenerator[str, None]:
    """生成内容更新事件流"""
    yield f"data: {json.dumps({'type': 'connected', 'content_id': content_id})}\n\n"
    while True:
        await asyncio.sleep(15)
        event = {"type": "heartbeat", "timestamp": datetime.now().isoformat()}
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.get("/stream/{content_id}")
async def stream_content_updates(content_id: int):
    """内容更新流（SSE）— 实时评论/统计更新"""
    return StreamingResponse(
        _generate_content_events(content_id, None),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )

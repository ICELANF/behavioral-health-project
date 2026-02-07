# -*- coding: utf-8 -*-
"""
挑战/打卡活动 REST API

端点列表:
  模板管理:
    GET    /api/v1/challenges                     - 挑战列表（支持筛选）
    GET    /api/v1/challenges/{id}                - 挑战详情
    POST   /api/v1/challenges                     - 创建挑战模板（L3+）
    PUT    /api/v1/challenges/{id}                - 更新挑战模板
    POST   /api/v1/challenges/import/{config_key} - 从JSON配置导入（admin）
    DELETE /api/v1/challenges/{id}                - 删除挑战模板（admin）

  推送内容管理:
    GET    /api/v1/challenges/{id}/pushes          - 获取全部推送内容
    GET    /api/v1/challenges/{id}/pushes/day/{day} - 获取指定天推送
    POST   /api/v1/challenges/{id}/pushes          - 添加推送内容
    PUT    /api/v1/challenges/pushes/{push_id}     - 更新推送内容
    DELETE /api/v1/challenges/pushes/{push_id}     - 删除推送内容

  审核流程:
    POST   /api/v1/challenges/{id}/submit-review   - 提交审核（创建者）
    POST   /api/v1/challenges/{id}/review          - 专家审核（L4+）

  用户报名与参与:
    POST   /api/v1/challenges/{id}/enroll          - 报名挑战
    GET    /api/v1/challenges/my-enrollments        - 我的挑战列表
    POST   /api/v1/challenges/enrollments/{eid}/start - 开始挑战
    POST   /api/v1/challenges/enrollments/{eid}/advance - 推进到下一天
    GET    /api/v1/challenges/enrollments/{eid}/today  - 今日推送内容
    POST   /api/v1/challenges/enrollments/{eid}/read/{pid} - 标记已读
    GET    /api/v1/challenges/enrollments/{eid}/progress - 进度详情

  问卷:
    POST   /api/v1/challenges/enrollments/{eid}/survey/{pid} - 提交问卷

  教练:
    POST   /api/v1/coach/challenges/assign         - 教练为学员报名挑战
    GET    /api/v1/coach/challenges/students/{sid}  - 教练查看学员挑战列表
"""
import os
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.dependencies import get_current_user, require_admin, require_coach_or_admin
from core.database import get_db
from core.models import (
    User, ChallengeTemplate, ChallengeDayPush, ChallengeEnrollment,
    ChallengeSurveyResponse, ChallengePushLog,
    ChallengeStatus, EnrollmentStatus,
)
from core import challenge_service

router = APIRouter(prefix="/api/v1", tags=["challenges"])


# ============================================
# Pydantic Schemas
# ============================================

class ChallengeCreateRequest(BaseModel):
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    category: str = "general"
    duration_days: int = Field(..., ge=1, le=365)
    daily_push_times: Optional[List[str]] = None
    day_topics: Optional[Dict[str, str]] = None
    cover_image: Optional[str] = None


class ChallengeUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    duration_days: Optional[int] = None
    daily_push_times: Optional[List[str]] = None
    day_topics: Optional[Dict[str, str]] = None
    cover_image: Optional[str] = None


class PushCreateRequest(BaseModel):
    day_number: int = Field(..., ge=0)
    push_time: str = "9:00"
    sort_order: int = 0
    is_core: bool = True
    tag: str = "core"
    management_content: Optional[str] = None
    behavior_guidance: Optional[str] = None
    survey: Optional[Dict[str, Any]] = None


class PushUpdateRequest(BaseModel):
    day_number: Optional[int] = None
    push_time: Optional[str] = None
    sort_order: Optional[int] = None
    is_core: Optional[bool] = None
    tag: Optional[str] = None
    management_content: Optional[str] = None
    behavior_guidance: Optional[str] = None
    survey: Optional[Dict[str, Any]] = None


class ReviewRequest(BaseModel):
    approved: bool
    note: Optional[str] = None


class SurveySubmitRequest(BaseModel):
    responses: Dict[str, Any]


class CoachAssignRequest(BaseModel):
    student_id: int
    challenge_id: int


# ============================================
# 模板序列化
# ============================================

def _serialize_template(t: ChallengeTemplate, include_pushes: bool = False) -> dict:
    data = {
        "id": t.id,
        "title": t.title,
        "description": t.description,
        "category": t.category,
        "cover_image": t.cover_image,
        "duration_days": t.duration_days,
        "config_key": t.config_key,
        "daily_push_times": t.daily_push_times,
        "day_topics": t.day_topics,
        "created_by": t.created_by,
        "status": t.status.value if hasattr(t.status, 'value') else t.status,
        "reviewer1_id": t.reviewer1_id,
        "reviewer1_status": t.reviewer1_status,
        "reviewer2_id": t.reviewer2_id,
        "reviewer2_status": t.reviewer2_status,
        "published_at": t.published_at.isoformat() if t.published_at else None,
        "enrollment_count": t.enrollment_count or 0,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }
    if include_pushes and t.day_pushes:
        data["pushes"] = [_serialize_push(p) for p in t.day_pushes]
    return data


def _serialize_push(p: ChallengeDayPush) -> dict:
    return {
        "id": p.id,
        "challenge_id": p.challenge_id,
        "day_number": p.day_number,
        "push_time": p.push_time,
        "sort_order": p.sort_order,
        "is_core": p.is_core,
        "tag": p.tag,
        "management_content": p.management_content,
        "behavior_guidance": p.behavior_guidance,
        "survey": p.survey,
    }


def _serialize_enrollment(e: ChallengeEnrollment) -> dict:
    return {
        "id": e.id,
        "user_id": e.user_id,
        "challenge_id": e.challenge_id,
        "coach_id": e.coach_id,
        "status": e.status.value if hasattr(e.status, 'value') else e.status,
        "current_day": e.current_day,
        "started_at": e.started_at.isoformat() if e.started_at else None,
        "completed_at": e.completed_at.isoformat() if e.completed_at else None,
        "completed_pushes": e.completed_pushes or 0,
        "completed_surveys": e.completed_surveys or 0,
        "streak_days": e.streak_days or 0,
        "enrolled_at": e.enrolled_at.isoformat() if e.enrolled_at else None,
    }


# ============================================
# 模板管理 API
# ============================================

@router.get("/challenges")
async def list_challenges(
    status: Optional[str] = Query(None, description="draft/pending_review/published/archived"),
    category: Optional[str] = Query(None),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """挑战列表"""
    templates = challenge_service.list_templates(db, status=status, category=category)
    return {
        "total": len(templates),
        "items": [_serialize_template(t) for t in templates],
    }


@router.get("/challenges/{challenge_id}")
async def get_challenge(
    challenge_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """挑战详情（含推送内容）"""
    template = db.query(ChallengeTemplate).get(challenge_id)
    if not template:
        raise HTTPException(status_code=404, detail="挑战不存在")
    return _serialize_template(template, include_pushes=True)


@router.post("/challenges")
async def create_challenge(
    req: ChallengeCreateRequest,
    db=Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """创建挑战模板（L3+）"""
    try:
        template = challenge_service.create_template(db, current_user, req.dict(exclude_none=True))
        return _serialize_template(template)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/challenges/{challenge_id}")
async def update_challenge(
    challenge_id: int,
    req: ChallengeUpdateRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新挑战模板"""
    try:
        template = challenge_service.update_template(db, challenge_id, current_user, req.dict(exclude_none=True))
        return _serialize_template(template)
    except (PermissionError,) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/challenges/import/{config_key}")
async def import_challenge(
    config_key: str,
    db=Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """从JSON配置导入挑战（admin）"""
    try:
        template = challenge_service.import_from_config(db, config_key, current_user)
        return _serialize_template(template, include_pushes=False)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/challenges/{challenge_id}")
async def delete_challenge(
    challenge_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """删除挑战模板（admin）"""
    template = db.query(ChallengeTemplate).get(challenge_id)
    if not template:
        raise HTTPException(status_code=404, detail="挑战不存在")

    # Check no active enrollments
    active = db.query(ChallengeEnrollment).filter(
        ChallengeEnrollment.challenge_id == challenge_id,
        ChallengeEnrollment.status.in_([EnrollmentStatus.ENROLLED, EnrollmentStatus.ACTIVE])
    ).count()
    if active > 0:
        raise HTTPException(status_code=400, detail=f"还有 {active} 位用户正在参与，无法删除")

    db.delete(template)
    db.commit()
    return {"message": "已删除"}


# ============================================
# 推送内容管理 API
# ============================================

@router.get("/challenges/{challenge_id}/pushes")
async def get_pushes(
    challenge_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取全部推送内容"""
    pushes = challenge_service.get_day_pushes(db, challenge_id)
    return {"items": [_serialize_push(p) for p in pushes]}


@router.get("/challenges/{challenge_id}/pushes/day/{day_number}")
async def get_day_pushes(
    challenge_id: int,
    day_number: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取指定天推送"""
    pushes = challenge_service.get_day_pushes(db, challenge_id, day_number=day_number)
    return {"items": [_serialize_push(p) for p in pushes]}


@router.post("/challenges/{challenge_id}/pushes")
async def add_push(
    challenge_id: int,
    req: PushCreateRequest,
    db=Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """添加推送内容"""
    data = req.dict(exclude_none=True)
    push = challenge_service.add_day_push(db, challenge_id, data)
    return _serialize_push(push)


@router.put("/challenges/pushes/{push_id}")
async def update_push(
    push_id: int,
    req: PushUpdateRequest,
    db=Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """更新推送内容"""
    try:
        push = challenge_service.update_day_push(db, push_id, req.dict(exclude_none=True))
        return _serialize_push(push)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/challenges/pushes/{push_id}")
async def delete_push(
    push_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """删除推送内容"""
    challenge_service.delete_day_push(db, push_id)
    return {"message": "已删除"}


# ============================================
# 审核流程 API
# ============================================

@router.post("/challenges/{challenge_id}/submit-review")
async def submit_review(
    challenge_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交审核"""
    try:
        template = challenge_service.submit_for_review(db, challenge_id, current_user)
        return _serialize_template(template)
    except (PermissionError,) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/challenges/{challenge_id}/review")
async def review(
    challenge_id: int,
    req: ReviewRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """专家审核"""
    try:
        template = challenge_service.review_challenge(
            db, challenge_id, current_user,
            approved=req.approved, note=req.note,
        )
        return _serialize_template(template)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# 用户报名与参与 API
# ============================================

@router.post("/challenges/{challenge_id}/enroll")
async def enroll_challenge(
    challenge_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """报名挑战"""
    try:
        enrollment = challenge_service.enroll(db, current_user, challenge_id)
        return _serialize_enrollment(enrollment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/challenges/my-enrollments")
async def my_enrollments(
    status: Optional[str] = Query(None),
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """我的挑战列表"""
    query = db.query(ChallengeEnrollment).filter_by(user_id=current_user.id)
    if status:
        query = query.filter(ChallengeEnrollment.status == status)
    enrollments = query.order_by(ChallengeEnrollment.enrolled_at.desc()).all()

    result = []
    for e in enrollments:
        data = _serialize_enrollment(e)
        template = db.query(ChallengeTemplate).get(e.challenge_id)
        if template:
            data["challenge_title"] = template.title
            data["challenge_category"] = template.category
            data["duration_days"] = template.duration_days
            data["cover_image"] = template.cover_image
        result.append(data)

    return {"items": result}


@router.post("/challenges/enrollments/{enrollment_id}/start")
async def start_challenge(
    enrollment_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """开始挑战"""
    enrollment = db.query(ChallengeEnrollment).get(enrollment_id)
    if not enrollment or enrollment.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="报名记录不存在")
    try:
        enrollment = challenge_service.start_challenge(db, enrollment_id)
        return _serialize_enrollment(enrollment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/challenges/enrollments/{enrollment_id}/advance")
async def advance_challenge_day(
    enrollment_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """推进到下一天"""
    enrollment = db.query(ChallengeEnrollment).get(enrollment_id)
    if not enrollment or enrollment.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="报名记录不存在")
    try:
        enrollment = challenge_service.advance_day(db, enrollment_id)
        return _serialize_enrollment(enrollment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/challenges/enrollments/{enrollment_id}/today")
async def get_today_pushes(
    enrollment_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """今日推送内容"""
    enrollment = db.query(ChallengeEnrollment).get(enrollment_id)
    if not enrollment or enrollment.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="报名记录不存在")

    pushes = challenge_service.get_today_pushes(db, enrollment_id)

    template = db.query(ChallengeTemplate).get(enrollment.challenge_id)
    day_topic = ""
    if template and template.day_topics:
        day_topic = template.day_topics.get(str(enrollment.current_day), "")

    return {
        "current_day": enrollment.current_day,
        "day_topic": day_topic,
        "pushes": pushes,
    }


@router.post("/challenges/enrollments/{enrollment_id}/read/{push_id}")
async def mark_read(
    enrollment_id: int,
    push_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """标记推送已读"""
    enrollment = db.query(ChallengeEnrollment).get(enrollment_id)
    if not enrollment or enrollment.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="报名记录不存在")
    challenge_service.mark_push_read(db, enrollment_id, push_id)
    return {"message": "已标记已读"}


@router.get("/challenges/enrollments/{enrollment_id}/progress")
async def get_progress(
    enrollment_id: int,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """进度详情"""
    enrollment = db.query(ChallengeEnrollment).get(enrollment_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail="报名记录不存在")
    # Allow user or coach or admin to view
    if enrollment.user_id != current_user.id and enrollment.coach_id != current_user.id:
        from core.content_access_service import get_user_level
        if get_user_level(current_user) < 99:
            raise HTTPException(status_code=403, detail="无权查看")

    return challenge_service.get_enrollment_progress(db, enrollment_id)


# ============================================
# 问卷 API
# ============================================

@router.post("/challenges/enrollments/{enrollment_id}/survey/{push_id}")
async def submit_survey(
    enrollment_id: int,
    push_id: int,
    req: SurveySubmitRequest,
    db=Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交问卷回答"""
    try:
        response = challenge_service.submit_survey(
            db, current_user, enrollment_id, push_id, req.responses,
        )
        return {
            "id": response.id,
            "enrollment_id": response.enrollment_id,
            "push_id": response.push_id,
            "responses": response.responses,
            "submitted_at": response.submitted_at.isoformat(),
        }
    except (PermissionError,) as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# 教练端 API
# ============================================

@router.post("/coach/challenges/assign")
async def coach_assign(
    req: CoachAssignRequest,
    db=Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """教练为学员报名挑战"""
    try:
        enrollment = challenge_service.coach_assign_challenge(
            db, current_user, req.student_id, req.challenge_id,
        )
        return _serialize_enrollment(enrollment)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/coach/challenges/students/{student_id}")
async def coach_view_student_challenges(
    student_id: int,
    db=Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """教练查看学员挑战列表"""
    enrollments = db.query(ChallengeEnrollment).filter_by(user_id=student_id).order_by(
        ChallengeEnrollment.enrolled_at.desc()
    ).all()

    result = []
    for e in enrollments:
        data = _serialize_enrollment(e)
        progress = challenge_service.get_enrollment_progress(db, e.id)
        data.update(progress)
        result.append(data)

    return {"items": result}

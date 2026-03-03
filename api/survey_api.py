# -*- coding: utf-8 -*-
"""
问卷管理 API (7 + 3 = 10 端点)

管理端点 (需认证, coach+):
  POST   /api/v1/surveys                      创建问卷
  GET    /api/v1/surveys                      我的问卷列表
  GET    /api/v1/surveys/{id}                 问卷详情
  PATCH  /api/v1/surveys/{id}                 更新问卷
  DELETE /api/v1/surveys/{id}                 删除问卷
  POST   /api/v1/surveys/{id}/publish         发布问卷
  POST   /api/v1/surveys/{id}/close           关闭问卷

题目管理:
  POST   /api/v1/surveys/{id}/questions       批量保存题目
  PUT    /api/v1/surveys/{id}/questions/reorder  题目排序
  DELETE /api/v1/surveys/{id}/questions/{qid} 删除单题
"""
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from core.database import get_db
from core.models import User
from api.dependencies import get_current_user, require_coach_or_admin
from core.survey_service import SurveyService

logger = logging.getLogger("survey_api")

router = APIRouter(prefix="/api/v1/surveys", tags=["surveys"])


def _survey_to_dict(s) -> dict:
    return {
        "id": s.id,
        "title": s.title,
        "description": s.description,
        "survey_type": s.survey_type.value if s.survey_type else "general",
        "status": s.status.value if s.status else "draft",
        "short_code": s.short_code,
        "response_count": s.response_count or 0,
        "created_by": s.created_by,
        "tenant_id": s.tenant_id,
        "settings": s.settings or {},
        "baps_mapping": s.baps_mapping,
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
        "published_at": s.published_at.isoformat() if s.published_at else None,
        "question_count": len(s.questions) if s.questions else 0,
    }


def _question_to_dict(q) -> dict:
    return {
        "id": q.id,
        "question_type": q.question_type.value,
        "sort_order": q.sort_order,
        "title": q.title,
        "description": q.description,
        "is_required": q.is_required,
        "config": q.config or {},
        "skip_logic": q.skip_logic,
    }


# ── 问卷管理 ──

@router.post("", summary="创建问卷")
def create_survey(
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    svc = SurveyService(db)
    try:
        survey = svc.create_survey(data, current_user.id)
        return _survey_to_dict(survey)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", summary="我的问卷列表")
def list_surveys(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    svc = SurveyService(db)
    surveys, total = svc.list_surveys(current_user.id, status=status, skip=skip, limit=limit)
    return {
        "surveys": [_survey_to_dict(s) for s in surveys],
        "total": total,
    }


@router.get("/{survey_id}", summary="问卷详情")
def get_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    svc = SurveyService(db)
    survey = svc.get_survey(survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="问卷不存在")
    if survey.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看")
    result = _survey_to_dict(survey)
    result["questions"] = [_question_to_dict(q) for q in (survey.questions or [])]
    return result


@router.patch("/{survey_id}", summary="更新问卷")
def update_survey(
    survey_id: int,
    data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    svc = SurveyService(db)
    try:
        survey = svc.update_survey(survey_id, current_user.id, data)
        return _survey_to_dict(survey)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{survey_id}", summary="删除问卷")
def delete_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    svc = SurveyService(db)
    try:
        svc.delete_survey(survey_id, current_user.id)
        return {"success": True, "message": "问卷已删除"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{survey_id}/publish", summary="发布问卷")
def publish_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    svc = SurveyService(db)
    try:
        survey = svc.publish_survey(survey_id, current_user.id)
        return {
            "success": True,
            "id": survey.id,
            "status": survey.status.value,
            "short_code": survey.short_code,
            "share_url": f"/s/{survey.short_code}",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{survey_id}/close", summary="关闭问卷")
def close_survey(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    svc = SurveyService(db)
    try:
        survey = svc.close_survey(survey_id, current_user.id)
        return {"success": True, "id": survey.id, "status": survey.status.value}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── 题目管理 ──

@router.post("/{survey_id}/questions", summary="批量保存题目")
def save_questions(
    survey_id: int,
    questions: List[dict] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    svc = SurveyService(db)
    try:
        count = svc.save_questions(survey_id, current_user.id, questions)
        return {"success": True, "count": count}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{survey_id}/questions/reorder", summary="题目排序")
def reorder_questions(
    survey_id: int,
    question_ids: List[int] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    svc = SurveyService(db)
    try:
        svc.reorder_questions(survey_id, current_user.id, question_ids)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{survey_id}/questions/{question_id}", summary="删除单题")
def delete_question(
    survey_id: int,
    question_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    svc = SurveyService(db)
    try:
        svc.delete_question(survey_id, current_user.id, question_id)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── 教练分配问卷给学员 ──────────────────────────────────────────────────────

class AssignSurveyRequest(BaseModel):
    student_ids: List[int]
    message: Optional[str] = None


@router.post("/{survey_id}/assign", summary="教练分配问卷给学员")
def assign_survey_to_students(
    survey_id: int,
    body: AssignSurveyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """
    教练将已发布问卷分配给一个或多个学员。

    流程:
    1. 验证问卷已发布
    2. 写入 survey_distributions (channel='coach')
    3. 向每个学员发送站内通知（含问卷短链）
    返回: {success, survey_id, distribution_ids, student_count}
    """
    # 验证问卷存在且已发布
    survey_row = db.execute(
        text("SELECT id, title, status, short_code FROM surveys WHERE id = :sid"),
        {"sid": survey_id}
    ).mappings().first()

    if not survey_row:
        raise HTTPException(status_code=404, detail="问卷不存在")
    if survey_row["status"] != "published":
        raise HTTPException(status_code=400, detail="只能分配已发布的问卷")

    survey_title = survey_row["title"]
    short_code   = survey_row["short_code"]
    survey_url   = f"/pages/assessment/survey?code={short_code}"
    now = datetime.now()

    distribution_ids = []

    for student_id in body.student_ids:
        # 创建分发记录
        try:
            result = db.execute(text("""
                INSERT INTO survey_distributions
                    (survey_id, channel, channel_config, tracking_code, click_count, submit_count, created_at, created_by)
                VALUES
                    (:sid, 'coach',
                     CAST(:cfg AS jsonb),
                     substr(md5(CAST(random() AS text)), 1, 12),
                     0, 0, :now, :creator)
                RETURNING id
            """), {
                "sid":     survey_id,
                "cfg":     f'{{"student_id": {student_id}, "coach_id": {current_user.id}, "message": "{body.message or ""}"}}',
                "now":     now,
                "creator": current_user.id,
            })
            dist_id = result.scalar()
            if dist_id:
                distribution_ids.append(dist_id)
        except Exception as e:
            logger.warning(f"创建分发记录失败 student={student_id}: {e}")
            continue

        # 站内通知
        try:
            notif_body = (
                f"教练为您安排了问卷《{survey_title}》，"
                f"完成后可获得积分。"
                f"{body.message or ''} [link:{survey_url}]"
            )
            db.execute(text("""
                INSERT INTO notifications (user_id, title, body, notification_type, is_read, created_at)
                VALUES (:uid, :title, :body, 'survey_assigned', false, :now)
            """), {
                "uid":   student_id,
                "title": f"新问卷：{survey_title}",
                "body":  notif_body,
                "now":   now,
            })
        except Exception as e:
            logger.warning(f"发送通知失败 student={student_id}: {e}")

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"assign_survey commit failed: {e}")
        raise HTTPException(status_code=500, detail="分配失败，请重试")

    logger.info(f"Coach {current_user.id} assigned survey {survey_id} to {len(body.student_ids)} students")
    return {
        "success":          True,
        "survey_id":        survey_id,
        "distribution_ids": distribution_ids,
        "student_count":    len(body.student_ids),
    }

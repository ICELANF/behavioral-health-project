# -*- coding: utf-8 -*-
"""
问卷统计分析 API (3 端点, 需认证)

  GET /api/v1/surveys/{id}/stats       回收统计 (各题汇总)
  GET /api/v1/surveys/{id}/responses   逐份查看 (分页)
  GET /api/v1/surveys/{id}/export      导出 CSV
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io

from core.database import get_db
from core.models import User
from api.dependencies import get_current_user, require_coach_or_admin
from core.survey_service import SurveyService

router = APIRouter(prefix="/api/v1/surveys", tags=["survey-stats"])


def _check_owner(svc: SurveyService, survey_id: int, user_id: int):
    survey = svc.get_survey(survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="问卷不存在")
    if survey.created_by != user_id:
        raise HTTPException(status_code=403, detail="无权查看统计")
    return survey


@router.get("/{survey_id}/stats", summary="回收统计")
def get_stats(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    svc = SurveyService(db)
    _check_owner(svc, survey_id, current_user.id)
    try:
        return svc.get_stats(survey_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{survey_id}/responses", summary="逐份查看")
def list_responses(
    survey_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    svc = SurveyService(db)
    _check_owner(svc, survey_id, current_user.id)
    responses, total = svc.list_responses(survey_id, skip=skip, limit=limit)
    return {"responses": responses, "total": total}


@router.get("/{survey_id}/export", summary="导出 CSV")
def export_csv(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    svc = SurveyService(db)
    survey = _check_owner(svc, survey_id, current_user.id)
    csv_bytes = svc.export_csv(survey_id)
    filename = f"survey_{survey_id}_{survey.title[:20]}.csv"
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv; charset=utf-8-sig",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

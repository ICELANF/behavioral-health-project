# -*- coding: utf-8 -*-
"""
问卷填写 API (3 端点, 可匿名)

  GET  /api/v1/surveys/s/{short_code}             短链获取问卷 (公开)
  POST /api/v1/surveys/s/{short_code}/submit       提交回答
  POST /api/v1/surveys/s/{short_code}/save-draft   暂存 (断点续填)
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Body, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from core.database import get_db
from core.survey_service import SurveyService

router = APIRouter(prefix="/api/v1/surveys/s", tags=["survey-respond"])

# 可选认证: 匿名填写时不要求token
_oauth2_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def _get_optional_user_id(token: Optional[str] = Depends(_oauth2_optional), db: Session = Depends(get_db)) -> Optional[int]:
    """尝试从token获取user_id, 失败返回None (匿名)"""
    if not token:
        return None
    try:
        from core.auth import SECRET_KEY, ALGORITHM
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        return int(user_id) if user_id else None
    except (JWTError, ValueError, ImportError):
        return None


@router.get("/{short_code}", summary="短链获取问卷 (公开)")
def get_survey_by_short_code(
    short_code: str,
    db: Session = Depends(get_db),
):
    svc = SurveyService(db)
    try:
        data = svc.get_by_short_code(short_code)
        survey = data["survey"]
        questions = data["questions"]
        settings = survey.settings or {}
        return {
            "id": survey.id,
            "title": survey.title,
            "description": survey.description,
            "settings": {
                "show_progress_bar": settings.get("show_progress_bar", True),
                "theme_color": settings.get("theme_color", "#3B82F6"),
                "welcome_message": settings.get("welcome_message", ""),
                "anonymous": settings.get("anonymous", False),
                "require_login": settings.get("require_login", False),
            },
            "questions": [
                {
                    "id": q.id,
                    "question_type": q.question_type.value,
                    "title": q.title,
                    "description": q.description,
                    "is_required": q.is_required,
                    "sort_order": q.sort_order,
                    "config": q.config or {},
                    "skip_logic": q.skip_logic,
                }
                for q in questions
            ],
            "total_questions": len([q for q in questions if q.question_type.value not in ("section_break", "description")]),
            "estimated_minutes": int(data["estimated_minutes"]),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{short_code}/submit", summary="提交回答")
def submit_response(
    short_code: str,
    request: Request,
    answers: List[dict] = Body(..., embed=True),
    duration_sec: Optional[int] = Body(None, embed=True),
    device_type: Optional[str] = Body("unknown", embed=True),
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(_get_optional_user_id),
):
    svc = SurveyService(db)
    meta = {
        "ip": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent", "")[:500],
        "device_type": device_type or "unknown",
        "duration_sec": duration_sec,
    }
    try:
        response, baps_synced = svc.submit_response(short_code, answers, user_id=user_id, meta=meta)
        # 获取问卷的 thank_you_message
        survey = svc.get_survey(response.survey_id)
        settings = survey.settings or {} if survey else {}
        return {
            "response_id": response.id,
            "message": "提交成功，感谢您的参与！",
            "thank_you_message": settings.get("thank_you_message", "感谢您的参与！"),
            "redirect_url": settings.get("redirect_url"),
            "baps_synced": baps_synced,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{short_code}/save-draft", summary="暂存 (断点续填)")
def save_draft(
    short_code: str,
    answers: List[dict] = Body(..., embed=True),
    current_page: int = Body(0, embed=True),
    db: Session = Depends(get_db),
    user_id: Optional[int] = Depends(_get_optional_user_id),
):
    svc = SurveyService(db)
    try:
        response = svc.save_draft_response(short_code, answers, current_page=current_page, user_id=user_id)
        return {
            "response_id": response.id,
            "current_page": response.current_page,
            "message": "已暂存",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

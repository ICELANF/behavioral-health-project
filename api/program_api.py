from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from loguru import logger

from core.database import get_db
from api.dependencies import get_current_user, require_admin, require_coach_or_admin
from core.models import User
from core.program_service import ProgramService

router = APIRouter(prefix="/api/v1/programs", tags=["智能监测方案"])


class CreateTemplateRequest(BaseModel):
    slug: str = Field(..., max_length=64, pattern=r"^[a-z0-9\-]+$")
    title: str = Field(..., max_length=200)
    description: str = ""
    category: str = "custom"
    total_days: int = Field(..., gt=0, le=365)
    pushes_per_day: int = Field(default=3, gt=0, le=6)
    schedule_json: dict
    recommendation_rules: dict = Field(default_factory=lambda: {"rules": []})
    tags: List[str] = Field(default_factory=list)
    cover_image: Optional[str] = None
    is_active: bool = True
    is_public: bool = True
    tenant_id: Optional[int] = None


class UpdateTemplateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    schedule_json: Optional[dict] = None
    recommendation_rules: Optional[dict] = None
    tags: Optional[List[str]] = None
    cover_image: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class EnrollRequest(BaseModel):
    template_id: str
    coach_id: Optional[int] = None
    push_preferences: Optional[dict] = None
    custom_schedule: Optional[dict] = None


class InteractionRequest(BaseModel):
    day_number: int = Field(..., ge=0)
    slot: str
    survey_answers: Optional[Dict[str, Any]] = None
    photo_urls: Optional[List[str]] = None
    device_data: Optional[dict] = None


class PauseResumeRequest(BaseModel):
    action: str
    reason: Optional[str] = ""


@router.get("/templates")
def list_templates(
    category: Optional[str] = Query(None),
    tenant_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        service = ProgramService(db)
        return service.list_templates(category=category, tenant_id=tenant_id)
    except Exception as e:
        logger.warning(f"DB object missing ({e.__class__.__name__}), returning empty fallback")
        return []


@router.post("/templates")
def create_template(
    request: CreateTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = ProgramService(db)
    return service.create_template(request.dict(), created_by=current_user.id)


@router.get("/templates/{template_id}")
def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProgramService(db)
    result = service.get_template(template_id)
    if not result:
        raise HTTPException(404, "Template not found")
    return result


@router.put("/templates/{template_id}")
def update_template(
    template_id: str,
    request: UpdateTemplateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = ProgramService(db)
    data = {k: v for k, v in request.dict().items() if v is not None}
    if not data:
        raise HTTPException(400, "No fields to update")
    success = service.update_template(template_id, data)
    if not success:
        raise HTTPException(404, "Template not found")
    return {"success": True}


@router.post("/enroll")
def enroll_program(
    request: EnrollRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        service = ProgramService(db)
        result = service.enroll(
            user_id=current_user.id,
            template_id=request.template_id,
            coach_id=request.coach_id,
            push_preferences=request.push_preferences,
            custom_schedule=request.custom_schedule,
        )
    except Exception as e:
        logger.warning(f"DB object missing ({e.__class__.__name__}), returning empty fallback")
        raise HTTPException(400, "Program service unavailable")
    if not result.get("success"):
        raise HTTPException(400, result.get("reason", "Enrollment failed"))
    return result


@router.get("/my")
def get_my_programs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        service = ProgramService(db)
        return service.get_my_programs(current_user.id)
    except Exception as e:
        logger.warning(f"DB object missing ({e.__class__.__name__}), returning empty fallback")
        return []


@router.get("/my/{enrollment_id}/today")
def get_today_content(
    enrollment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        service = ProgramService(db)
        result = service.get_today_content(enrollment_id, current_user.id)
    except Exception as e:
        logger.warning(f"DB object missing ({e.__class__.__name__}), returning empty fallback")
        raise HTTPException(404, "Enrollment not found")
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@router.post("/my/{enrollment_id}/interact")
def submit_interaction(
    enrollment_id: str,
    request: InteractionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProgramService(db)
    result = service.submit_interaction(
        enrollment_id=enrollment_id,
        user_id=current_user.id,
        day_number=request.day_number,
        slot=request.slot,
        survey_answers=request.survey_answers,
        photo_urls=request.photo_urls,
        device_data=request.device_data,
    )
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.get("/my/{enrollment_id}/timeline")
def get_timeline(
    enrollment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProgramService(db)
    result = service.get_timeline(enrollment_id, current_user.id)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@router.get("/my/{enrollment_id}/progress")
def get_progress_radar(
    enrollment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        service = ProgramService(db)
        result = service.get_progress_radar(enrollment_id, current_user.id)
    except Exception as e:
        logger.warning(f"DB object missing ({e.__class__.__name__}), returning empty fallback")
        raise HTTPException(404, "Enrollment not found")
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@router.post("/my/{enrollment_id}/status")
def update_enrollment_status(
    enrollment_id: str,
    request: PauseResumeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProgramService(db)
    if request.action == "pause":
        result = service.pause_enrollment(enrollment_id, current_user.id)
    elif request.action == "resume":
        result = service.resume_enrollment(enrollment_id, current_user.id)
    elif request.action == "drop":
        result = service.drop_enrollment(enrollment_id, current_user.id, request.reason)
    else:
        raise HTTPException(400, "Invalid action. Must be: pause, resume, or drop")
    if not result.get("success"):
        raise HTTPException(400, result.get("reason", "Failed"))
    return result


@router.get("/admin/analytics")
def admin_analytics(
    template_id: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = ProgramService(db)
    return service.admin_get_analytics(template_id, category)


@router.get("/admin/enrollments")
def admin_enrollments(
    template_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    coach_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    service = ProgramService(db)
    return service.admin_get_enrollments(
        template_id, status, coach_id, page, page_size
    )

# -*- coding: utf-8 -*-
"""
AI推送建议 API
Push Recommendation API

端点:
- GET  /api/v1/push-recommendations              — 教练获取所有学员的AI推送建议
- GET  /api/v1/push-recommendations/{student_id}  — 某个学员的建议
- POST /api/v1/push-recommendations/{student_id}/apply — 一键应用建议
"""
import os
import sys
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import get_db
from core.models import User
from core.push_recommendation_service import PushRecommendationService
from api.dependencies import require_coach_or_admin

router = APIRouter(prefix="/api/v1/push-recommendations", tags=["AI推送建议"])

recommendation_service = PushRecommendationService()


@router.get("")
async def get_all_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """教练获取所有学员的AI推送建议"""
    recs = recommendation_service.generate_recommendations(db, current_user.id)
    return {
        "recommendations": [r.to_dict() for r in recs],
        "total": len(recs),
    }


@router.get("/{student_id}")
async def get_student_recommendation(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """获取某个学员的推送建议"""
    rec = recommendation_service.generate_for_student(db, student_id)
    if not rec:
        return {"recommendation": None, "message": "该学员暂无推送建议"}
    return {"recommendation": rec.to_dict()}


@router.post("/{student_id}/apply")
async def apply_recommendation(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """
    一键应用建议（返回预填的推送表单数据）

    前端收到后可直接填入推送抽屉表单
    """
    rec = recommendation_service.generate_for_student(db, student_id)
    if not rec:
        raise HTTPException(status_code=404, detail="该学员暂无推送建议")

    # Convert to pre-filled form data
    form_data = {
        "student_id": rec.student_id,
        "student_name": rec.student_name,
    }

    if rec.push_type == "questions":
        # Check if it's a preset reference
        if len(rec.items) == 1 and rec.items[0].startswith("hf"):
            form_data["question_preset"] = rec.items[0]
        else:
            form_data["question_ids"] = rec.items
    else:
        form_data["scales"] = rec.items

    form_data["note"] = f"[AI建议] {rec.reasoning}"

    return {
        "form_data": form_data,
        "reasoning": rec.reasoning,
        "priority": rec.priority,
    }

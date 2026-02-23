# -*- coding: utf-8 -*-
"""
提醒管理 REST API
Reminder API - 提醒的CRUD管理

端点:
- GET    /api/v1/reminders           — 用户的提醒列表
- POST   /api/v1/reminders           — 创建提醒
- PUT    /api/v1/reminders/{id}      — 更新提醒
- DELETE /api/v1/reminders/{id}      — 删除提醒
- POST   /api/v1/coach/reminders     — 教练为学员创建提醒
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from core.database import get_db
from core.models import Reminder, User
from core.reminder_service import ReminderService
from api.dependencies import get_current_user, require_coach_or_admin

router = APIRouter(tags=["提醒管理"])

reminder_service = ReminderService()


# ============ Pydantic 模型 ============

class CreateReminderRequest(BaseModel):
    type: str = Field(..., description="提醒类型: medication/visit/behavior/assessment")
    title: str = Field(..., min_length=1, max_length=200)
    content: Optional[str] = Field(None, max_length=1000)
    cron_expr: Optional[str] = Field(None, description="Cron表达式，null为一次性")
    next_fire_at: Optional[str] = Field(None, description="下次触发时间 ISO格式")


class UpdateReminderRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = Field(None, max_length=1000)
    cron_expr: Optional[str] = None
    next_fire_at: Optional[str] = None
    is_active: Optional[bool] = None


class CoachReminderRequest(BaseModel):
    student_id: int = Field(..., description="学员ID")
    type: str = Field("behavior", description="提醒类型")
    title: str = Field(..., min_length=1, max_length=200)
    content: Optional[str] = Field(None, max_length=1000)
    cron_expr: Optional[str] = None
    next_fire_at: Optional[str] = None
    auto_approve: bool = Field(False, description="促进师已审核，直接推送")


# ============ 用户端端点 ============

@router.get("/api/v1/reminders")
async def list_reminders(
    active_only: bool = Query(True, description="仅显示活跃提醒"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取用户的提醒列表"""
    query = db.query(Reminder).filter(Reminder.user_id == current_user.id)
    if active_only:
        query = query.filter(Reminder.is_active == True)

    reminders = query.order_by(desc(Reminder.created_at)).all()
    return {
        "reminders": [_reminder_to_dict(r) for r in reminders],
        "total": len(reminders),
    }


@router.post("/api/v1/reminders")
async def create_reminder(
    body: CreateReminderRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建提醒"""
    next_fire = None
    if body.next_fire_at:
        try:
            next_fire = datetime.fromisoformat(body.next_fire_at)
        except ValueError:
            raise HTTPException(status_code=400, detail="next_fire_at 格式无效")
    elif body.cron_expr:
        next_fire = reminder_service.calc_next_fire(body.cron_expr)

    reminder = Reminder(
        user_id=current_user.id,
        type=body.type,
        title=body.title,
        content=body.content,
        cron_expr=body.cron_expr,
        next_fire_at=next_fire,
        source="self",
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    return {"success": True, "reminder": _reminder_to_dict(reminder)}


@router.put("/api/v1/reminders/{reminder_id}")
async def update_reminder(
    reminder_id: int,
    body: UpdateReminderRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """更新提醒"""
    reminder = (
        db.query(Reminder)
        .filter(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
        .first()
    )
    if not reminder:
        raise HTTPException(status_code=404, detail="提醒不存在")

    if body.title is not None:
        reminder.title = body.title
    if body.content is not None:
        reminder.content = body.content
    if body.cron_expr is not None:
        reminder.cron_expr = body.cron_expr
    if body.next_fire_at is not None:
        try:
            reminder.next_fire_at = datetime.fromisoformat(body.next_fire_at)
        except ValueError:
            raise HTTPException(status_code=400, detail="next_fire_at 格式无效")
    if body.is_active is not None:
        reminder.is_active = body.is_active

    db.commit()
    db.refresh(reminder)

    return {"success": True, "reminder": _reminder_to_dict(reminder)}


@router.delete("/api/v1/reminders/{reminder_id}")
async def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除提醒"""
    reminder = (
        db.query(Reminder)
        .filter(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
        .first()
    )
    if not reminder:
        raise HTTPException(status_code=404, detail="提醒不存在")

    db.delete(reminder)
    db.commit()

    return {"success": True, "message": "提醒已删除"}


# ============ 教练端端点 ============

@router.post("/api/v1/coach/reminders")
async def create_coach_reminder(
    body: CoachReminderRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """教练为学员创建提醒 — AI→审核→推送"""
    student = db.query(User).filter(User.id == body.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    from core.coach_push_queue_service import create_queue_item, create_and_deliver
    kwargs = dict(
        db=db,
        coach_id=current_user.id,
        student_id=body.student_id,
        source_type="coach_reminder",
        title=body.title,
        content=body.content,
        content_extra={
            "reminder_type": body.type,
            "cron_expr": body.cron_expr,
            "next_fire_at": body.next_fire_at,
        },
        priority="normal",
    )

    if body.auto_approve:
        queue_item = create_and_deliver(**kwargs)
        db.commit()
        return {
            "success": True,
            "queue_item_id": queue_item.id,
            "status": "sent",
            "message": "提醒已推送给学员",
        }
    else:
        queue_item = create_queue_item(**kwargs)
        db.commit()
        return {
            "success": True,
            "queue_item_id": queue_item.id,
            "status": "pending_review",
            "message": "提醒已提交审批队列",
        }


@router.get("/api/v1/coach/reminders/ai-suggestions/{student_id}")
async def get_reminder_suggestions(
    student_id: int,
    reminder_type: str = Query("behavior", description="提醒类型: behavior/medication/visit/assessment"),
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """获取AI提醒建议"""
    from core.coach_ai_suggestion_service import CoachAISuggestionService
    service = CoachAISuggestionService()
    return service.generate_reminder_suggestions(
        db, student_id, current_user.id, reminder_type
    )


def _reminder_to_dict(r: Reminder) -> dict:
    return {
        "id": r.id,
        "user_id": r.user_id,
        "type": r.type,
        "title": r.title,
        "content": r.content,
        "cron_expr": r.cron_expr,
        "next_fire_at": r.next_fire_at.isoformat() if r.next_fire_at else None,
        "is_active": r.is_active,
        "source": r.source,
        "created_by": r.created_by,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }

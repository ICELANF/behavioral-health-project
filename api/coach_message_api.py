# -*- coding: utf-8 -*-
"""
教练消息 REST API
Coach Message API - 教练与学员之间的消息管理

端点:
- POST /api/v1/coach/messages            — 教练发消息给学员
- GET  /api/v1/coach/messages/{student_id} — 教练查看与学员的消息历史
- GET  /api/v1/messages/inbox             — 用户查看收到的教练消息
- POST /api/v1/messages/{id}/read         — 标记已读
- GET  /api/v1/messages/unread-count      — 未读消息数
"""
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from core.database import get_db
from core.models import CoachMessage, User
from api.dependencies import get_current_user, require_coach_or_admin

router = APIRouter(tags=["教练消息"])


# ============ Pydantic 模型 ============

class SendMessageRequest(BaseModel):
    student_id: int = Field(..., description="学员ID")
    content: str = Field(..., min_length=1, max_length=2000, description="消息内容")
    message_type: str = Field("text", description="消息类型: text/encouragement/reminder/advice")


# ============ 教练端端点 ============

@router.post("/api/v1/coach/messages")
async def send_message(
    body: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """教练发消息给学员"""
    # 验证学员存在
    student = db.query(User).filter(User.id == body.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    msg = CoachMessage(
        coach_id=current_user.id,
        student_id=body.student_id,
        content=body.content,
        message_type=body.message_type,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return {
        "success": True,
        "message": _msg_to_dict(msg),
    }


@router.get("/api/v1/coach/messages/{student_id}")
async def get_conversation(
    student_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """教练查看与学员的消息历史"""
    query = (
        db.query(CoachMessage)
        .filter(
            CoachMessage.coach_id == current_user.id,
            CoachMessage.student_id == student_id,
        )
    )
    total = query.count()
    messages = (
        query
        .order_by(desc(CoachMessage.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "messages": [_msg_to_dict(m) for m in reversed(messages)],
    }


@router.get("/api/v1/coach/students-with-messages")
async def get_students_with_messages(
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """获取教练的学员列表（带最近消息和未读数）"""
    # 获取该教练发过消息的所有学员
    student_ids = (
        db.query(CoachMessage.student_id)
        .filter(CoachMessage.coach_id == current_user.id)
        .distinct()
        .all()
    )
    student_ids = [s[0] for s in student_ids]

    result = []
    for sid in student_ids:
        student = db.query(User).filter(User.id == sid).first()
        if not student:
            continue

        # 最近消息
        last_msg = (
            db.query(CoachMessage)
            .filter(
                CoachMessage.coach_id == current_user.id,
                CoachMessage.student_id == sid,
            )
            .order_by(desc(CoachMessage.created_at))
            .first()
        )

        # 未读数（学员未读的消息）
        unread = (
            db.query(func.count(CoachMessage.id))
            .filter(
                CoachMessage.student_id == sid,
                CoachMessage.coach_id == current_user.id,
                CoachMessage.is_read == False,
            )
            .scalar() or 0
        )

        result.append({
            "student_id": sid,
            "student_name": student.full_name or student.username,
            "last_message": last_msg.content[:50] if last_msg else "",
            "last_message_at": last_msg.created_at.isoformat() if last_msg else None,
            "unread_count": unread,
        })

    # 按最近消息时间排序
    result.sort(key=lambda x: x["last_message_at"] or "", reverse=True)
    return {"students": result}


# ============ 用户端端点 ============

@router.get("/api/v1/messages/inbox")
async def get_inbox(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """用户查看收到的教练消息"""
    query = (
        db.query(CoachMessage)
        .filter(CoachMessage.student_id == current_user.id)
    )
    total = query.count()
    messages = (
        query
        .order_by(desc(CoachMessage.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # 关联教练姓名
    result = []
    for msg in messages:
        coach = db.query(User).filter(User.id == msg.coach_id).first()
        d = _msg_to_dict(msg)
        d["coach_name"] = coach.full_name or coach.username if coach else "教练"
        result.append(d)

    return {
        "total": total,
        "page": page,
        "messages": result,
    }


@router.post("/api/v1/messages/{message_id}/read")
async def mark_read(
    message_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """标记消息已读"""
    msg = (
        db.query(CoachMessage)
        .filter(
            CoachMessage.id == message_id,
            CoachMessage.student_id == current_user.id,
        )
        .first()
    )
    if not msg:
        raise HTTPException(status_code=404, detail="消息不存在")

    msg.is_read = True
    db.commit()

    return {"success": True}


@router.get("/api/v1/messages/unread-count")
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取未读消息数"""
    count = (
        db.query(func.count(CoachMessage.id))
        .filter(
            CoachMessage.student_id == current_user.id,
            CoachMessage.is_read == False,
        )
        .scalar() or 0
    )
    return {"unread_count": count}


def _msg_to_dict(msg: CoachMessage) -> dict:
    return {
        "id": msg.id,
        "coach_id": msg.coach_id,
        "student_id": msg.student_id,
        "content": msg.content,
        "message_type": msg.message_type,
        "is_read": msg.is_read,
        "created_at": msg.created_at.isoformat() if msg.created_at else None,
    }

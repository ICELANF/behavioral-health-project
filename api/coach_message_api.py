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
    auto_approve: bool = Field(False, description="促进师已审核，直接推送")


# ============ 教练端端点 ============

TYPE_LABELS = {
    "text": "文字", "encouragement": "鼓励",
    "reminder": "提醒", "advice": "建议",
}


@router.post("/api/v1/coach/messages")
async def send_message(
    body: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """教练发消息给学员 — AI→审核→推送"""
    student = db.query(User).filter(User.id == body.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学员不存在")

    from core.coach_push_queue_service import create_queue_item, create_and_deliver
    kwargs = dict(
        db=db,
        coach_id=current_user.id,
        student_id=body.student_id,
        source_type="coach_message",
        title=f"教练消息({TYPE_LABELS.get(body.message_type, '文字')})",
        content=body.content,
        content_extra={"message_type": body.message_type},
        priority="normal",
    )

    if body.auto_approve:
        queue_item = create_and_deliver(**kwargs)
        db.commit()
        return {
            "success": True,
            "queue_item_id": queue_item.id,
            "status": "sent",
            "message": "消息已推送给学员",
        }
    else:
        queue_item = create_queue_item(**kwargs)
        db.commit()
        return {
            "success": True,
            "queue_item_id": queue_item.id,
            "status": "pending_review",
            "message": "消息已提交审批队列",
        }


@router.get("/api/v1/coach/messages/ai-suggestions/{student_id}")
async def get_message_suggestions(
    student_id: int,
    message_type: str = Query("text", description="消息类型: text/encouragement/reminder/advice"),
    context: str = Query("", description="教练补充上下文"),
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """获取AI消息建议"""
    from core.coach_ai_suggestion_service import CoachAISuggestionService
    service = CoachAISuggestionService()
    return service.generate_message_suggestions(
        db, student_id, current_user.id, message_type, context
    )


@router.get("/api/v1/coach/assessment/ai-suggestions/{student_id}")
async def get_assessment_suggestions(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """获取AI测评建议: 推荐评估量表 + 理由"""
    from core.coach_ai_suggestion_service import CoachAISuggestionService
    service = CoachAISuggestionService()
    return service.generate_assessment_suggestions(db, student_id, current_user.id)


@router.get("/api/v1/coach/micro-actions/ai-suggestions/{student_id}")
async def get_micro_action_suggestions(
    student_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_coach_or_admin),
):
    """获取AI微行动建议: 推荐微行动任务 + 理由"""
    from core.coach_ai_suggestion_service import CoachAISuggestionService
    service = CoachAISuggestionService()
    return service.generate_micro_action_suggestions(db, student_id, current_user.id)


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
    """获取教练的学员列表（带最近消息和未读数）— 权威源: coach_student_bindings"""
    from sqlalchemy import text as sa_text
    from core.models import UserRole

    _STUDENT_ROLES = [UserRole.OBSERVER, UserRole.GROWER, UserRole.SHARER]

    # 1. 获取绑定学员（权威源）
    if current_user.role.value == "admin":
        bound_students = db.query(User).filter(
            User.is_active == True,
            User.role.in_(_STUDENT_ROLES),
        ).all()
    else:
        rows = db.execute(sa_text(
            "SELECT student_id FROM coach_schema.coach_student_bindings "
            "WHERE coach_id = :cid AND is_active = true"
        ), {"cid": current_user.id}).fetchall()
        sids = [r[0] for r in rows]
        bound_students = db.query(User).filter(
            User.id.in_(sids)
        ).all() if sids else []

    # 2. 为每个学员查消息（可能为空）
    result = []
    for student in bound_students:
        last_msg = db.query(CoachMessage).filter(
            CoachMessage.coach_id == current_user.id,
            CoachMessage.student_id == student.id,
        ).order_by(desc(CoachMessage.created_at)).first()

        unread = db.query(func.count(CoachMessage.id)).filter(
            CoachMessage.student_id == student.id,
            CoachMessage.coach_id == current_user.id,
            CoachMessage.is_read == False,
        ).scalar() or 0

        result.append({
            "student_id": student.id,
            "student_name": student.full_name or student.username,
            "last_message": last_msg.content[:50] if last_msg else "",
            "last_message_at": last_msg.created_at.isoformat() if last_msg else None,
            "unread_count": unread,
        })

    # 有消息的排前面，无消息的按名字排
    result.sort(key=lambda x: (x["last_message_at"] or "", x["student_name"]), reverse=True)
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

# -*- coding: utf-8 -*-
"""
教练推送审批队列服务
Coach Push Queue Service

统一审批网关：
来源(挑战/设备预警/微行动/AI建议) → CoachPushQueue(pending) → 教练审批 → 投递给学员
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import and_, case, func
from loguru import logger

from core.models import CoachPushQueue, CoachMessage, Reminder


def create_queue_item(
    db: Session,
    coach_id: int,
    student_id: int,
    source_type: str,
    source_id: Optional[str] = None,
    title: str = "",
    content: Optional[str] = None,
    content_extra: Optional[dict] = None,
    suggested_time: Optional[datetime] = None,
    priority: str = "normal",
) -> CoachPushQueue:
    """
    统一入口：创建一条待审批推送

    Args:
        source_type: challenge | device_alert | micro_action | ai_recommendation | system
        priority: high | normal | low
    """
    item = CoachPushQueue(
        coach_id=coach_id,
        student_id=student_id,
        source_type=source_type,
        source_id=source_id,
        title=title,
        content=content,
        content_extra=content_extra,
        suggested_time=suggested_time,
        priority=priority,
        status="pending",
    )
    db.add(item)
    db.flush()
    logger.info(
        f"[PushQueue] 新条目: id={item.id} coach={coach_id} student={student_id} "
        f"source={source_type} priority={priority}"
    )
    return item


def get_pending_items(
    db: Session,
    coach_id: int,
    student_id: Optional[int] = None,
    source_type: Optional[str] = None,
    priority: Optional[str] = None,
    status: str = "pending",
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """获取待审批列表（分页）"""
    query = db.query(CoachPushQueue).filter(CoachPushQueue.coach_id == coach_id)

    if status:
        query = query.filter(CoachPushQueue.status == status)
    if student_id:
        query = query.filter(CoachPushQueue.student_id == student_id)
    if source_type:
        query = query.filter(CoachPushQueue.source_type == source_type)
    if priority:
        query = query.filter(CoachPushQueue.priority == priority)

    total = query.count()

    # 按优先级排序: high > normal > low, 然后按创建时间倒序
    priority_order = case(
        (CoachPushQueue.priority == "high", 0),
        (CoachPushQueue.priority == "normal", 1),
        else_=2,
    )
    items = (
        query
        .order_by(priority_order, CoachPushQueue.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [_item_to_dict(i) for i in items],
    }


def get_stats(db: Session, coach_id: int) -> Dict[str, int]:
    """各状态数量统计"""
    rows = (
        db.query(CoachPushQueue.status, func.count(CoachPushQueue.id))
        .filter(CoachPushQueue.coach_id == coach_id)
        .group_by(CoachPushQueue.status)
        .all()
    )
    result = {"pending": 0, "approved": 0, "rejected": 0, "sent": 0, "expired": 0}
    for status, count in rows:
        result[status] = count
    return result


def approve_item(
    db: Session,
    item_id: int,
    coach_id: int,
    content_override: Optional[str] = None,
    scheduled_time: Optional[datetime] = None,
    coach_note: Optional[str] = None,
) -> CoachPushQueue:
    """
    审批通过

    - content_override: 教练修改后的内容（null=保持原内容）
    - scheduled_time: 定时投递（null=立即投递）
    """
    item = db.query(CoachPushQueue).filter(
        CoachPushQueue.id == item_id,
        CoachPushQueue.coach_id == coach_id,
    ).first()
    if not item:
        raise ValueError("推送条目不存在或无权操作")
    if item.status != "pending":
        raise ValueError(f"当前状态({item.status})不允许审批")

    if content_override:
        item.content = content_override
    if coach_note:
        item.coach_note = coach_note

    item.reviewed_at = datetime.utcnow()

    if scheduled_time and scheduled_time > datetime.utcnow():
        # 定时投递
        item.scheduled_time = scheduled_time
        item.status = "approved"
    else:
        # 立即投递
        item.status = "approved"
        deliver_item(db, item)

    db.commit()
    db.refresh(item)
    return item


def reject_item(
    db: Session,
    item_id: int,
    coach_id: int,
    coach_note: Optional[str] = None,
) -> CoachPushQueue:
    """拒绝推送"""
    item = db.query(CoachPushQueue).filter(
        CoachPushQueue.id == item_id,
        CoachPushQueue.coach_id == coach_id,
    ).first()
    if not item:
        raise ValueError("推送条目不存在或无权操作")
    if item.status != "pending":
        raise ValueError(f"当前状态({item.status})不允许操作")

    item.status = "rejected"
    item.coach_note = coach_note
    item.reviewed_at = datetime.utcnow()

    db.commit()
    db.refresh(item)
    return item


def batch_approve(
    db: Session,
    item_ids: List[int],
    coach_id: int,
) -> int:
    """批量审批（立即投递）"""
    items = (
        db.query(CoachPushQueue)
        .filter(
            CoachPushQueue.id.in_(item_ids),
            CoachPushQueue.coach_id == coach_id,
            CoachPushQueue.status == "pending",
        )
        .all()
    )
    now = datetime.utcnow()
    count = 0
    for item in items:
        item.status = "approved"
        item.reviewed_at = now
        deliver_item(db, item)
        count += 1

    db.commit()
    logger.info(f"[PushQueue] 批量审批: coach={coach_id} count={count}")
    return count


def deliver_item(db: Session, item: CoachPushQueue):
    """
    实际投递：根据 source_type 差异化创建记录

    - coach_message: 创建 CoachMessage (保留原始 message_type)
    - coach_reminder: 创建 Reminder (带 cron_expr/next_fire_at)
    - 其他: 创建 CoachMessage + 通用 Reminder (原有逻辑)

    注意：此方法不 commit，由调用方统一 commit
    """
    now = datetime.utcnow()
    extra = item.content_extra or {}

    if item.source_type == "coach_reminder":
        # 教练提醒: 只创建 Reminder
        next_fire = None
        if extra.get("next_fire_at"):
            try:
                next_fire = datetime.fromisoformat(extra["next_fire_at"])
            except (ValueError, TypeError):
                pass
        elif extra.get("cron_expr"):
            try:
                from core.reminder_service import ReminderService
                next_fire = ReminderService().calc_next_fire(extra["cron_expr"])
            except Exception:
                pass

        reminder = Reminder(
            user_id=item.student_id,
            type=extra.get("reminder_type", "behavior"),
            title=item.title,
            content=item.content or "",
            cron_expr=extra.get("cron_expr"),
            next_fire_at=next_fire,
            source="coach",
            created_by=item.coach_id,
            is_active=True,
        )
        db.add(reminder)

    elif item.source_type == "coach_message":
        # 教练消息: 只创建 CoachMessage (保留原始类型)
        msg = CoachMessage(
            coach_id=item.coach_id,
            student_id=item.student_id,
            content=item.content or "",
            message_type=extra.get("message_type", "text"),
        )
        db.add(msg)

    else:
        # 默认路径: 创建 CoachMessage + 通用 Reminder (原有逻辑)
        msg = CoachMessage(
            coach_id=item.coach_id,
            student_id=item.student_id,
            content=f"[{_source_label(item.source_type)}] {item.title}\n{item.content or ''}".strip(),
            message_type="push",
        )
        db.add(msg)

        reminder = Reminder(
            user_id=item.student_id,
            type="push",
            title=item.title,
            content=item.content or "",
            source="coach",
            created_by=item.coach_id,
            is_active=True,
        )
        db.add(reminder)

    item.status = "sent"
    item.sent_at = now

    # Queue async external push via unified push router
    try:
        import asyncio
        from gateway.channels.push_router import send_notification
        from core.database import AsyncSessionLocal

        async def _push():
            async with AsyncSessionLocal() as async_db:
                await send_notification(
                    db=async_db, user_id=item.student_id,
                    title=item.title, body=item.content or "",
                )
                await async_db.commit()

        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_push())
        else:
            loop.run_until_complete(_push())
    except Exception as e:
        logger.debug(f"[PushQueue] External push queued failed (non-blocking): {e}")

    logger.info(f"[PushQueue] 已投递: id={item.id} student={item.student_id}")


def process_due_approved(db: Session) -> int:
    """
    投递已审批且到时的推送（scheduler 每5分钟调用）
    """
    now = datetime.utcnow()
    items = (
        db.query(CoachPushQueue)
        .filter(
            CoachPushQueue.status == "approved",
            CoachPushQueue.scheduled_time.isnot(None),
            CoachPushQueue.scheduled_time <= now,
        )
        .all()
    )
    count = 0
    for item in items:
        deliver_item(db, item)
        count += 1

    if count:
        db.commit()
        logger.info(f"[PushQueue] 定时投递: {count} 条")
    return count


def expire_stale_items(db: Session, hours: int = 72) -> int:
    """清理超时未审批条目"""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    count = (
        db.query(CoachPushQueue)
        .filter(
            CoachPushQueue.status == "pending",
            CoachPushQueue.created_at < cutoff,
        )
        .update({"status": "expired"})
    )
    if count:
        db.commit()
        logger.info(f"[PushQueue] 过期清理: {count} 条 (超过{hours}h)")
    return count


def update_item(
    db: Session,
    item_id: int,
    coach_id: int,
    content: Optional[str] = None,
    scheduled_time: Optional[datetime] = None,
) -> CoachPushQueue:
    """修改待审批条目的内容/时间"""
    item = db.query(CoachPushQueue).filter(
        CoachPushQueue.id == item_id,
        CoachPushQueue.coach_id == coach_id,
    ).first()
    if not item:
        raise ValueError("推送条目不存在或无权操作")
    if item.status != "pending":
        raise ValueError("只有待审批状态可修改")

    if content is not None:
        item.content = content
    if scheduled_time is not None:
        item.scheduled_time = scheduled_time

    db.commit()
    db.refresh(item)
    return item


# ============================================
# 内部辅助
# ============================================

def _source_label(source_type: str) -> str:
    labels = {
        "challenge": "挑战打卡",
        "device_alert": "设备预警",
        "micro_action": "微行动",
        "ai_recommendation": "AI建议",
        "system": "系统",
        "coach_message": "教练消息",
        "coach_reminder": "教练提醒",
    }
    return labels.get(source_type, source_type)


def _item_to_dict(item: CoachPushQueue) -> Dict[str, Any]:
    return {
        "id": item.id,
        "coach_id": item.coach_id,
        "student_id": item.student_id,
        "source_type": item.source_type,
        "source_id": item.source_id,
        "title": item.title,
        "content": item.content,
        "content_extra": item.content_extra,
        "suggested_time": item.suggested_time.isoformat() if item.suggested_time else None,
        "scheduled_time": item.scheduled_time.isoformat() if item.scheduled_time else None,
        "priority": item.priority,
        "status": item.status,
        "coach_note": item.coach_note,
        "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
        "sent_at": item.sent_at.isoformat() if item.sent_at else None,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }

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

from core.models import CoachPushQueue, CoachMessage, Reminder, User


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


def create_and_deliver(
    db: Session,
    coach_id: int,
    student_id: int,
    source_type: str,
    source_id: Optional[str] = None,
    title: str = "",
    content: Optional[str] = None,
    content_extra: Optional[dict] = None,
    scheduled_time: Optional[datetime] = None,
    priority: str = "normal",
) -> CoachPushQueue:
    """
    创建队列条目 + 立即/定时投递（一步完成）

    促进师在工具箱抽屉中已完成审核修订，此方法跳过 pending 状态，
    直接 approved→sent，保留完整审计记录。
    """
    item = create_queue_item(
        db=db, coach_id=coach_id, student_id=student_id,
        source_type=source_type, source_id=source_id,
        title=title, content=content, content_extra=content_extra,
        suggested_time=scheduled_time, priority=priority,
    )

    now = datetime.utcnow()
    item.reviewed_at = now
    item.coach_note = "促进师工具箱直接审核推送"

    if scheduled_time and scheduled_time > now:
        item.scheduled_time = scheduled_time
        item.status = "approved"
        logger.info(f"[PushQueue] 定时投递: id={item.id} scheduled={scheduled_time}")
    else:
        item.status = "approved"
        deliver_item(db, item)

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

    item.reviewer_id = coach_id
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
    item.reviewer_id = coach_id
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
        item.reviewer_id = coach_id
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
    - assessment_push: 更新 AssessmentAssignment.status="pushed" + 创建 CoachMessage
    - micro_action_assign: 创建 MicroActionTask
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

    elif item.source_type == "assessment_push":
        # 评估结果推送: 更新 assignment 状态 + 创建通知消息
        assignment_id = extra.get("assignment_id")
        if assignment_id:
            from core.models import AssessmentAssignment
            assignment = db.query(AssessmentAssignment).filter(
                AssessmentAssignment.id == assignment_id
            ).first()
            if assignment:
                assignment.status = "pushed"
                assignment.pushed_at = now

        msg = CoachMessage(
            coach_id=item.coach_id,
            student_id=item.student_id,
            content=item.content or "",
            message_type="advice",
        )
        db.add(msg)

    elif item.source_type == "micro_action_assign":
        # 微行动指派: 创建 MicroActionTask
        from core.models import MicroActionTask
        from datetime import date as _date
        task_title = extra.get("task_title", item.title)
        duration_days = extra.get("duration_days", 7)
        today_str = _date.today().strftime("%Y-%m-%d")

        task = MicroActionTask(
            user_id=item.student_id,
            domain=extra.get("domain", "exercise"),
            title=task_title,
            description=extra.get("task_description", item.content or ""),
            difficulty="easy",
            source="coach",
            source_id=str(item.coach_id),
            status="pending",
            scheduled_date=today_str,
        )
        db.add(task)

        # 同时发一条通知消息
        msg = CoachMessage(
            coach_id=item.coach_id,
            student_id=item.student_id,
            content=f"教练为你指派了新的微行动: {task_title}",
            message_type="push",
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

    # WebSocket 实时推送
    try:
        import asyncio
        from api.websocket_api import push_user_notification

        async def _ws_push():
            await push_user_notification(
                user_id=str(item.student_id),
                notification={
                    "type": "coach_push",
                    "title": item.title,
                    "body": item.content or "",
                    "push_id": str(item.id),
                },
            )

        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_ws_push())
        else:
            loop.run_until_complete(_ws_push())
    except Exception as e:
        logger.debug(f"[PushQueue] WebSocket push failed (non-blocking): {e}")

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
# 审批历史 + 详情
# ============================================

def get_history(
    db: Session,
    coach_id: int,
    status: Optional[str] = None,
    student_id: Optional[int] = None,
    source_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """获取已处理的审批历史（非 pending 状态）"""
    query = db.query(CoachPushQueue).filter(CoachPushQueue.coach_id == coach_id)

    if status:
        query = query.filter(CoachPushQueue.status == status)
    else:
        query = query.filter(CoachPushQueue.status.in_(["approved", "rejected", "sent", "expired"]))
    if student_id:
        query = query.filter(CoachPushQueue.student_id == student_id)
    if source_type:
        query = query.filter(CoachPushQueue.source_type == source_type)
    if date_from:
        query = query.filter(CoachPushQueue.created_at >= date_from)
    if date_to:
        query = query.filter(CoachPushQueue.created_at <= date_to)

    total = query.count()
    items = (
        query
        .order_by(CoachPushQueue.reviewed_at.desc().nullslast(), CoachPushQueue.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    # 关联学员姓名
    student_ids = {i.student_id for i in items}
    students = {u.id: u for u in db.query(User).filter(User.id.in_(student_ids)).all()} if student_ids else {}

    result_items = []
    for item in items:
        d = _item_to_dict(item)
        s = students.get(item.student_id)
        d["student_name"] = (s.full_name or s.username) if s else "未知"
        # 计算审批耗时
        if item.reviewed_at and item.created_at:
            d["review_seconds"] = int((item.reviewed_at - item.created_at).total_seconds())
        else:
            d["review_seconds"] = None
        result_items.append(d)

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": result_items,
    }


def get_item_detail(db: Session, item_id: int, coach_id: int) -> Dict[str, Any]:
    """获取单条推送详情"""
    item = db.query(CoachPushQueue).filter(
        CoachPushQueue.id == item_id,
        CoachPushQueue.coach_id == coach_id,
    ).first()
    if not item:
        raise ValueError("推送条目不存在或无权操作")

    d = _item_to_dict(item)
    student = db.query(User).filter(User.id == item.student_id).first()
    d["student_name"] = (student.full_name or student.username) if student else "未知"
    if item.reviewed_at and item.created_at:
        d["review_seconds"] = int((item.reviewed_at - item.created_at).total_seconds())
    else:
        d["review_seconds"] = None
    return d


def get_rejected_for_user(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """获取被驳回的推送（用户视角）"""
    query = db.query(CoachPushQueue).filter(
        CoachPushQueue.student_id == user_id,
        CoachPushQueue.status == "rejected",
    )
    total = query.count()
    items = (
        query
        .order_by(CoachPushQueue.reviewed_at.desc().nullslast())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "total": total,
        "page": page,
        "items": [_item_to_dict(i) for i in items],
    }


# ============================================
# 审批效率分析
# ============================================

def get_review_analytics(
    db: Session,
    coach_id: Optional[int] = None,
    period_days: int = 7,
) -> Dict[str, Any]:
    """
    审批效率分析

    coach_id=None 时返回全局（管理员视角），否则返回单教练数据。
    """
    cutoff = datetime.utcnow() - timedelta(days=period_days)

    base_q = db.query(CoachPushQueue).filter(
        CoachPushQueue.status.in_(["approved", "rejected", "sent", "expired"]),
        CoachPushQueue.created_at >= cutoff,
    )
    if coach_id:
        base_q = base_q.filter(CoachPushQueue.coach_id == coach_id)

    items = base_q.all()

    total = len(items)
    approved = sum(1 for i in items if i.status in ("approved", "sent"))
    rejected = sum(1 for i in items if i.status == "rejected")
    expired = sum(1 for i in items if i.status == "expired")

    # 平均审批耗时
    review_seconds = []
    for i in items:
        if i.reviewed_at and i.created_at:
            secs = (i.reviewed_at - i.created_at).total_seconds()
            if 0 < secs < 86400:  # 排除异常值
                review_seconds.append(secs)

    avg_review_seconds = int(sum(review_seconds) / len(review_seconds)) if review_seconds else 0

    # 按来源类型统计
    by_type: Dict[str, int] = {}
    for i in items:
        by_type[i.source_type] = by_type.get(i.source_type, 0) + 1

    # 按天统计
    by_day: Dict[str, Dict[str, Any]] = {}
    for i in items:
        day = (i.reviewed_at or i.created_at).strftime("%Y-%m-%d") if (i.reviewed_at or i.created_at) else "unknown"
        if day not in by_day:
            by_day[day] = {"date": day, "count": 0, "seconds_sum": 0, "seconds_count": 0}
        by_day[day]["count"] += 1
        if i.reviewed_at and i.created_at:
            secs = (i.reviewed_at - i.created_at).total_seconds()
            if 0 < secs < 86400:
                by_day[day]["seconds_sum"] += secs
                by_day[day]["seconds_count"] += 1

    by_day_list = []
    for d in sorted(by_day.values(), key=lambda x: x["date"]):
        avg_s = int(d["seconds_sum"] / d["seconds_count"]) if d["seconds_count"] else 0
        by_day_list.append({"date": d["date"], "count": d["count"], "avg_seconds": avg_s})

    result = {
        "period": f"{period_days}d",
        "total_reviewed": total,
        "approved": approved,
        "rejected": rejected,
        "expired": expired,
        "approval_rate": round(approved / total, 3) if total else 0,
        "avg_review_seconds": avg_review_seconds,
        "by_type": by_type,
        "by_day": by_day_list,
    }

    # 管理员视角：各教练排行
    if coach_id is None:
        coach_stats: Dict[int, Dict[str, Any]] = {}
        for i in items:
            cid = i.coach_id
            if cid not in coach_stats:
                coach_stats[cid] = {"coach_id": cid, "count": 0, "approved": 0}
            coach_stats[cid]["count"] += 1
            if i.status in ("approved", "sent"):
                coach_stats[cid]["approved"] += 1

        coach_ids = list(coach_stats.keys())
        coaches = {u.id: u for u in db.query(User).filter(User.id.in_(coach_ids)).all()} if coach_ids else {}
        coach_ranking = []
        for cs in sorted(coach_stats.values(), key=lambda x: x["count"], reverse=True):
            u = coaches.get(cs["coach_id"])
            coach_ranking.append({
                "coach_id": cs["coach_id"],
                "coach_name": (u.full_name or u.username) if u else "未知",
                "total": cs["count"],
                "approved": cs["approved"],
                "approval_rate": round(cs["approved"] / cs["count"], 3) if cs["count"] else 0,
            })
        result["coach_ranking"] = coach_ranking

    return result


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
        "assessment_push": "评估结果",
        "micro_action_assign": "微行动指派",
        "vision_rx": "视力处方",
        "xzb_expert": "行智诊疗",
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
        "reviewer_id": item.reviewer_id,
        "reviewed_at": item.reviewed_at.isoformat() if item.reviewed_at else None,
        "sent_at": item.sent_at.isoformat() if item.sent_at else None,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }

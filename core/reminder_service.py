# -*- coding: utf-8 -*-
"""
ReminderService - 提醒调度服务

职责:
- 创建和管理提醒
- 查询到期提醒
- 计算下次触发时间（基于cron表达式）
- 触发提醒推送
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
from loguru import logger

from core.models import Reminder


class ReminderService:
    """提醒调度服务"""

    def get_due_reminders(self, db: Session) -> List[Reminder]:
        """查询到期的活跃提醒"""
        now = datetime.utcnow()
        return (
            db.query(Reminder)
            .filter(
                Reminder.is_active == True,
                Reminder.next_fire_at.isnot(None),
                Reminder.next_fire_at <= now,
            )
            .all()
        )

    def fire_reminder(self, db: Session, reminder: Reminder) -> None:
        """
        触发提醒

        1. 推送通知（通过 WebSocket）
        2. 计算下次触发时间（如有 cron_expr）
        3. 如果是一次性提醒，标记为不活跃
        """
        logger.info(f"触发提醒: id={reminder.id}, user={reminder.user_id}, title={reminder.title}")

        # 尝试通过 WebSocket 推送
        try:
            from api.websocket_api import push_user_notification
            push_user_notification(
                user_id=str(reminder.user_id),
                notification={
                    "type": "reminder",
                    "reminder_type": reminder.type,
                    "title": reminder.title,
                    "content": reminder.content,
                    "reminder_id": reminder.id,
                },
            )
        except Exception as e:
            logger.warning(f"WebSocket推送失败: {e}")

        # 计算下次触发时间
        if reminder.cron_expr:
            next_fire = self.calc_next_fire(reminder.cron_expr)
            if next_fire:
                reminder.next_fire_at = next_fire
            else:
                reminder.is_active = False
        else:
            # 一次性提醒
            reminder.is_active = False

        db.commit()

    def calc_next_fire(self, cron_expr: str) -> Optional[datetime]:
        """
        根据简化的cron表达式计算下次触发时间

        支持的格式:
        - "HH:MM" → 每天指定时间
        - "0 8 * * *" → 标准cron（简化解析）
        """
        now = datetime.utcnow()

        # 简单格式: "HH:MM"
        if ":" in cron_expr and " " not in cron_expr:
            try:
                parts = cron_expr.split(":")
                hour = int(parts[0])
                minute = int(parts[1])
                next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_time <= now:
                    next_time += timedelta(days=1)
                return next_time
            except (ValueError, IndexError):
                pass

        # 标准cron简化解析: "minute hour * * *"
        try:
            parts = cron_expr.strip().split()
            if len(parts) >= 2:
                minute = int(parts[0])
                hour = int(parts[1])
                next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_time <= now:
                    next_time += timedelta(days=1)
                return next_time
        except (ValueError, IndexError):
            pass

        logger.warning(f"无法解析cron表达式: {cron_expr}")
        return None

    def create_reminder(
        self,
        db: Session,
        user_id: int,
        type: str,
        title: str,
        content: Optional[str] = None,
        cron_expr: Optional[str] = None,
        created_by: Optional[int] = None,
        source: str = "system",
    ) -> Reminder:
        """创建提醒"""
        next_fire = self.calc_next_fire(cron_expr) if cron_expr else None

        reminder = Reminder(
            user_id=user_id,
            type=type,
            title=title,
            content=content,
            cron_expr=cron_expr,
            next_fire_at=next_fire,
            source=source,
            created_by=created_by,
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)

        logger.info(f"创建提醒: id={reminder.id}, user={user_id}, type={type}")
        return reminder

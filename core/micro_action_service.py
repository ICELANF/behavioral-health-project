# -*- coding: utf-8 -*-
"""
MicroActionTaskService - 微行动任务服务

职责:
- 从 InterventionPlan 生成每日微行动任务
- 管理任务完成/跳过/过期
- 支持教练手动创建任务
- 支持设备数据自动完成
"""
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from loguru import logger

from core.models import (
    MicroActionTask, MicroActionLog,
    BehavioralProfile, User,
)
from core.intervention_matcher import InterventionMatcher


# 全局 InterventionMatcher 实例
_matcher = None


def _get_matcher() -> InterventionMatcher:
    global _matcher
    if _matcher is None:
        _matcher = InterventionMatcher()
    return _matcher


class MicroActionTaskService:
    """微行动任务服务"""

    def generate_daily_tasks(
        self,
        db: Session,
        user_id: int,
        max_tasks: int = 3,
    ) -> List[MicroActionTask]:
        """
        为用户生成今日微行动任务

        流程:
        1. 检查今日是否已有任务（避免重复）
        2. 获取用户 BehavioralProfile
        3. 通过 InterventionMatcher 获取当前干预计划
        4. 从 advice 列表提取微行动
        5. 创建 MicroActionTask 记录
        """
        today_str = date.today().isoformat()

        # 检查今日是否已有任务
        existing = (
            db.query(MicroActionTask)
            .filter(
                MicroActionTask.user_id == user_id,
                MicroActionTask.scheduled_date == today_str,
            )
            .all()
        )
        if existing:
            return existing

        # 获取用户画像
        profile = (
            db.query(BehavioralProfile)
            .filter(BehavioralProfile.user_id == user_id)
            .first()
        )

        if not profile:
            # 无画像 → 生成默认简单任务
            return self._generate_default_tasks(db, user_id, today_str)

        # 获取干预计划
        matcher = _get_matcher()
        target_domains = profile.primary_domains or ["nutrition", "exercise", "sleep"]
        current_stage = profile.current_stage.value if profile.current_stage else "S0"

        plan = matcher.match(
            user_id=user_id,
            current_stage=current_stage,
            psychological_level=profile.psychological_level.value if profile.psychological_level else "L3",
            bpt6_type=profile.bpt6_type or "mixed",
            spi_score=profile.spi_score or 0,
            target_domains=target_domains,
        )

        # 从干预计划提取微行动
        tasks = []
        for di in plan.domain_interventions[:max_tasks]:
            # 取该领域的第一条建议作为微行动
            advice = di.advice[0] if di.advice else None
            title = advice["title"] if advice else di.core_goal or f"{di.domain_name}练习"
            description = advice["description"] if advice else ""
            difficulty = "easy"
            if advice and advice.get("difficulty", 1) >= 4:
                difficulty = "challenging"
            elif advice and advice.get("difficulty", 1) >= 2:
                difficulty = "moderate"

            task = MicroActionTask(
                user_id=user_id,
                domain=di.domain,
                title=title,
                description=description,
                difficulty=difficulty,
                source="intervention_plan",
                source_id=di.rx_id,
                status="pending",
                scheduled_date=today_str,
            )
            db.add(task)
            tasks.append(task)

        if tasks:
            db.commit()
            for t in tasks:
                db.refresh(t)
            logger.info(f"生成每日任务: user={user_id}, count={len(tasks)}")

        return tasks

    def _generate_default_tasks(
        self,
        db: Session,
        user_id: int,
        today_str: str,
    ) -> List[MicroActionTask]:
        """无画像时生成默认简单任务"""
        defaults = [
            {"domain": "exercise", "title": "饭后散步10分钟", "difficulty": "easy"},
            {"domain": "nutrition", "title": "今天多喝一杯水", "difficulty": "easy"},
            {"domain": "sleep", "title": "记录今晚的入睡时间", "difficulty": "easy"},
        ]
        tasks = []
        for d in defaults:
            task = MicroActionTask(
                user_id=user_id,
                domain=d["domain"],
                title=d["title"],
                difficulty=d["difficulty"],
                source="system",
                status="pending",
                scheduled_date=today_str,
            )
            db.add(task)
            tasks.append(task)

        db.commit()
        for t in tasks:
            db.refresh(t)
        return tasks

    def complete_task(
        self,
        db: Session,
        task_id: int,
        user_id: int,
        note: Optional[str] = None,
        mood_score: Optional[int] = None,
    ) -> MicroActionTask:
        """
        完成任务

        1. 更新 task status → completed
        2. 写入 MicroActionLog
        """
        task = (
            db.query(MicroActionTask)
            .filter(
                MicroActionTask.id == task_id,
                MicroActionTask.user_id == user_id,
            )
            .first()
        )
        if not task:
            raise ValueError("任务不存在或无权操作")
        if task.status == "completed":
            raise ValueError("任务已完成")

        # 更新任务状态
        task.status = "completed"
        task.completed_at = datetime.utcnow()

        # 写入日志
        log = MicroActionLog(
            task_id=task_id,
            user_id=user_id,
            action="completed",
            note=note,
            mood_score=mood_score,
        )
        db.add(log)
        db.commit()
        db.refresh(task)

        logger.info(f"任务完成: task={task_id}, user={user_id}")
        return task

    def skip_task(
        self,
        db: Session,
        task_id: int,
        user_id: int,
        note: Optional[str] = None,
    ) -> MicroActionTask:
        """跳过任务"""
        task = (
            db.query(MicroActionTask)
            .filter(
                MicroActionTask.id == task_id,
                MicroActionTask.user_id == user_id,
            )
            .first()
        )
        if not task:
            raise ValueError("任务不存在或无权操作")

        task.status = "skipped"

        log = MicroActionLog(
            task_id=task_id,
            user_id=user_id,
            action="skipped",
            note=note,
        )
        db.add(log)
        db.commit()
        db.refresh(task)

        return task

    def auto_complete(
        self,
        db: Session,
        user_id: int,
        domain: str,
        note: str = "设备数据自动完成",
    ) -> Optional[MicroActionTask]:
        """
        设备数据自动完成指定领域的今日任务

        由 DeviceBehaviorBridge 调用
        """
        today_str = date.today().isoformat()
        task = (
            db.query(MicroActionTask)
            .filter(
                MicroActionTask.user_id == user_id,
                MicroActionTask.domain == domain,
                MicroActionTask.scheduled_date == today_str,
                MicroActionTask.status == "pending",
            )
            .first()
        )
        if not task:
            return None

        return self.complete_task(db, task.id, user_id, note=note)

    def get_today_tasks(
        self,
        db: Session,
        user_id: int,
    ) -> List[MicroActionTask]:
        """获取今日任务列表（自动生成）"""
        today_str = date.today().isoformat()

        tasks = (
            db.query(MicroActionTask)
            .filter(
                MicroActionTask.user_id == user_id,
                MicroActionTask.scheduled_date == today_str,
            )
            .all()
        )

        # 如果没有任务，自动生成
        if not tasks:
            tasks = self.generate_daily_tasks(db, user_id)

        return tasks

    def get_history(
        self,
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取历史记录（分页）"""
        query = (
            db.query(MicroActionTask)
            .filter(MicroActionTask.user_id == user_id)
        )

        if date_from:
            query = query.filter(MicroActionTask.scheduled_date >= date_from)
        if date_to:
            query = query.filter(MicroActionTask.scheduled_date <= date_to)

        total = query.count()
        tasks = (
            query
            .order_by(MicroActionTask.scheduled_date.desc(), MicroActionTask.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [self._task_to_dict(t) for t in tasks],
        }

    def create_coach_task(
        self,
        db: Session,
        user_id: int,
        coach_id: int,
        domain: str,
        title: str,
        description: Optional[str] = None,
        difficulty: str = "easy",
        scheduled_date: Optional[str] = None,
    ) -> MicroActionTask:
        """教练为学员创建微行动任务"""
        task = MicroActionTask(
            user_id=user_id,
            domain=domain,
            title=title,
            description=description,
            difficulty=difficulty,
            source="coach",
            source_id=str(coach_id),
            status="pending",
            scheduled_date=scheduled_date or date.today().isoformat(),
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def expire_overdue_tasks(self, db: Session) -> int:
        """将过期的未完成任务标记为 expired"""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        count = (
            db.query(MicroActionTask)
            .filter(
                MicroActionTask.scheduled_date < yesterday,
                MicroActionTask.status == "pending",
            )
            .update({"status": "expired"})
        )
        db.commit()
        if count:
            logger.info(f"过期任务标记: count={count}")
        return count

    @staticmethod
    def _task_to_dict(task: MicroActionTask) -> Dict:
        return {
            "id": task.id,
            "user_id": task.user_id,
            "domain": task.domain,
            "title": task.title,
            "description": task.description,
            "difficulty": task.difficulty,
            "source": task.source,
            "source_id": task.source_id,
            "status": task.status,
            "scheduled_date": task.scheduled_date,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "created_at": task.created_at.isoformat() if task.created_at else None,
        }

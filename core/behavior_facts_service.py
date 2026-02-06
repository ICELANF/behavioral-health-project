# -*- coding: utf-8 -*-
"""
BehaviorFactsService - 行为事实聚合服务

职责:
- 从 MicroActionLog + MicroActionTask 聚合行为事实
- 为 StageRuntimeBuilder 提供 action_completed_7d / streak_days / action_interrupt_72h 等数据
- 计算完成率、领域分布等统计指标
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from loguru import logger

from core.models import MicroActionTask, MicroActionLog


@dataclass
class BehaviorFacts:
    """行为事实数据"""
    action_completed_7d: int = 0          # 近7天完成的任务数
    streak_days: int = 0                   # 连续完成天数（每天至少1个）
    action_interrupt_72h: bool = False     # 72小时内是否有中断
    completion_rate_30d: float = 0.0       # 30天完成率
    domain_activity: Dict[str, int] = field(default_factory=dict)  # 各领域完成分布
    total_completed: int = 0               # 总完成数
    avg_mood_score: Optional[float] = None # 平均心情评分

    def to_dict(self) -> Dict:
        return {
            "action_completed_7d": self.action_completed_7d,
            "streak_days": self.streak_days,
            "action_interrupt_72h": self.action_interrupt_72h,
            "completion_rate_30d": round(self.completion_rate_30d, 2),
            "domain_activity": self.domain_activity,
            "total_completed": self.total_completed,
            "avg_mood_score": round(self.avg_mood_score, 1) if self.avg_mood_score else None,
        }


class BehaviorFactsService:
    """行为事实聚合服务"""

    def get_facts(self, db: Session, user_id: int) -> BehaviorFacts:
        """
        获取用户的行为事实

        聚合 MicroActionLog 和 MicroActionTask 数据
        """
        facts = BehaviorFacts()
        now = datetime.utcnow()
        today = date.today()

        try:
            # 1. 近7天完成的任务数
            seven_days_ago = today - timedelta(days=7)
            facts.action_completed_7d = (
                db.query(func.count(MicroActionTask.id))
                .filter(
                    MicroActionTask.user_id == user_id,
                    MicroActionTask.status == "completed",
                    MicroActionTask.scheduled_date >= seven_days_ago.isoformat(),
                )
                .scalar() or 0
            )

            # 2. 连续完成天数 (streak)
            facts.streak_days = self._calc_streak(db, user_id, today)

            # 3. 72小时内是否有中断
            facts.action_interrupt_72h = self._check_72h_interrupt(db, user_id, today)

            # 4. 30天完成率
            thirty_days_ago = today - timedelta(days=30)
            total_30d = (
                db.query(func.count(MicroActionTask.id))
                .filter(
                    MicroActionTask.user_id == user_id,
                    MicroActionTask.scheduled_date >= thirty_days_ago.isoformat(),
                )
                .scalar() or 0
            )
            completed_30d = (
                db.query(func.count(MicroActionTask.id))
                .filter(
                    MicroActionTask.user_id == user_id,
                    MicroActionTask.status == "completed",
                    MicroActionTask.scheduled_date >= thirty_days_ago.isoformat(),
                )
                .scalar() or 0
            )
            facts.completion_rate_30d = (completed_30d / total_30d) if total_30d > 0 else 0.0

            # 5. 各领域完成分布
            domain_counts = (
                db.query(MicroActionTask.domain, func.count(MicroActionTask.id))
                .filter(
                    MicroActionTask.user_id == user_id,
                    MicroActionTask.status == "completed",
                )
                .group_by(MicroActionTask.domain)
                .all()
            )
            facts.domain_activity = {domain: count for domain, count in domain_counts}

            # 6. 总完成数
            facts.total_completed = (
                db.query(func.count(MicroActionTask.id))
                .filter(
                    MicroActionTask.user_id == user_id,
                    MicroActionTask.status == "completed",
                )
                .scalar() or 0
            )

            # 7. 平均心情评分
            avg_mood = (
                db.query(func.avg(MicroActionLog.mood_score))
                .filter(
                    MicroActionLog.user_id == user_id,
                    MicroActionLog.mood_score.isnot(None),
                )
                .scalar()
            )
            facts.avg_mood_score = float(avg_mood) if avg_mood else None

        except Exception as e:
            logger.error(f"获取行为事实失败 user={user_id}: {e}")

        return facts

    def _calc_streak(self, db: Session, user_id: int, today: date) -> int:
        """计算连续完成天数"""
        streak = 0
        check_date = today

        for _ in range(365):  # 最多检查一年
            date_str = check_date.isoformat()
            completed = (
                db.query(func.count(MicroActionTask.id))
                .filter(
                    MicroActionTask.user_id == user_id,
                    MicroActionTask.scheduled_date == date_str,
                    MicroActionTask.status == "completed",
                )
                .scalar() or 0
            )

            # 检查当天是否有任务
            total = (
                db.query(func.count(MicroActionTask.id))
                .filter(
                    MicroActionTask.user_id == user_id,
                    MicroActionTask.scheduled_date == date_str,
                )
                .scalar() or 0
            )

            if total == 0:
                # 没有任务的日期不算中断（可能还没开始用系统）
                if streak == 0:
                    check_date -= timedelta(days=1)
                    continue
                else:
                    break
            elif completed > 0:
                streak += 1
            else:
                break

            check_date -= timedelta(days=1)

        return streak

    def _check_72h_interrupt(self, db: Session, user_id: int, today: date) -> bool:
        """检查72小时内是否有中断（有任务但没完成）"""
        for days_back in range(3):
            check_date = (today - timedelta(days=days_back)).isoformat()
            total = (
                db.query(func.count(MicroActionTask.id))
                .filter(
                    MicroActionTask.user_id == user_id,
                    MicroActionTask.scheduled_date == check_date,
                )
                .scalar() or 0
            )
            if total == 0:
                continue

            completed = (
                db.query(func.count(MicroActionTask.id))
                .filter(
                    MicroActionTask.user_id == user_id,
                    MicroActionTask.scheduled_date == check_date,
                    MicroActionTask.status == "completed",
                )
                .scalar() or 0
            )
            if completed == 0:
                return True

        return False

    def get_stats(self, db: Session, user_id: int) -> Dict:
        """获取用户统计数据（供前端展示）"""
        facts = self.get_facts(db, user_id)
        today = date.today()

        # 今日进度
        today_str = today.isoformat()
        today_total = (
            db.query(func.count(MicroActionTask.id))
            .filter(
                MicroActionTask.user_id == user_id,
                MicroActionTask.scheduled_date == today_str,
            )
            .scalar() or 0
        )
        today_completed = (
            db.query(func.count(MicroActionTask.id))
            .filter(
                MicroActionTask.user_id == user_id,
                MicroActionTask.scheduled_date == today_str,
                MicroActionTask.status == "completed",
            )
            .scalar() or 0
        )

        return {
            "streak_days": facts.streak_days,
            "completion_rate_30d": round(facts.completion_rate_30d * 100, 1),
            "total_completed": facts.total_completed,
            "domain_activity": facts.domain_activity,
            "avg_mood_score": facts.avg_mood_score,
            "today_total": today_total,
            "today_completed": today_completed,
            "action_completed_7d": facts.action_completed_7d,
        }

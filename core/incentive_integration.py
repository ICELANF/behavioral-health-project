"""
#5 社区激励闭环 — V003 激励系统 × 行为处方集成
放置: api/core/incentive_integration.py

核心问题: V003激励系统(积分/等级)与行为处方系统各自独立
解决方案:
  - 处方完成 → 自动产生积分事件
  - 积分/等级变化 → 反向影响处方策略
  - 社区行为(分享/帮助) → 同时计入激励和疗效
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Optional
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Boolean, JSON,
    ForeignKey, Index, UniqueConstraint,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import Session

try:
    from database import Base
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()


# ══════════════════════════════════════════════
# 积分事件类型 (对接 V003)
# ══════════════════════════════════════════════

class PointEventType(str, PyEnum):
    # ── 行为处方类 → growth 积分 ──
    TASK_COMPLETE = "task_complete"             # 完成单个处方任务
    DAILY_CHECKIN = "daily_checkin"             # 日打卡
    STREAK_MILESTONE = "streak_milestone"       # 连续打卡里程碑 (7/14/30/60/90天)
    ASSESSMENT_COMPLETE = "assessment_complete" # 完成评估批次
    STAGE_UPGRADE = "stage_upgrade"             # 行为阶段晋升 (S→S+1)
    CULTIVATION_PROMOTE = "cultivation_promote" # 养成阶段晋级
    SPI_IMPROVE = "spi_improve"                # SPI 提升
    # ── 社区行为类 → contribution 积分 ──
    SHARE_EXPERIENCE = "share_experience"       # 分享经验
    HELP_PEER = "help_peer"                     # 帮助同道者
    ANSWER_QUESTION = "answer_question"         # 社区答疑
    CONTENT_CREATE = "content_create"           # 创建内容
    # ── 影响力类 → influence 积分 ──
    RECRUIT_PEER = "recruit_peer"               # 发展同道者
    MENTOR_SESSION = "mentor_session"           # 指导学员
    COMMUNITY_LEAD = "community_lead"           # 组织社区活动


# 积分规则映射
POINT_RULES: dict[str, dict] = {
    # ── growth 积分 ──
    "task_complete":        {"dimension": "growth", "points": 5,    "daily_cap": 25},
    "daily_checkin":        {"dimension": "growth", "points": 10,   "daily_cap": 10},
    "streak_milestone":     {"dimension": "growth", "points_map": {
        7: 50, 14: 100, 30: 200, 60: 500, 90: 1000,
    }},
    "assessment_complete":  {"dimension": "growth", "points": 20,   "daily_cap": 100},
    "stage_upgrade":        {"dimension": "growth", "points": 200},
    "cultivation_promote":  {"dimension": "growth", "points": 300},
    "spi_improve":          {"dimension": "growth", "points_per_unit": 10},  # 每提升1分
    # ── contribution 积分 ──
    "share_experience":     {"dimension": "contribution", "points": 15, "daily_cap": 45},
    "help_peer":            {"dimension": "contribution", "points": 20, "daily_cap": 60},
    "answer_question":      {"dimension": "contribution", "points": 10, "daily_cap": 30},
    "content_create":       {"dimension": "contribution", "points": 30, "daily_cap": 60},
    # ── influence 积分 ──
    "recruit_peer":         {"dimension": "influence", "points": 100},
    "mentor_session":       {"dimension": "influence", "points": 50, "daily_cap": 100},
    "community_lead":       {"dimension": "influence", "points": 80},
}


# ══════════════════════════════════════════════
# 数据表
# ══════════════════════════════════════════════

class PointEvent(Base):
    """积分事件流水"""
    __tablename__ = "point_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(30), nullable=False)
    dimension = Column(String(15), nullable=False)    # growth/contribution/influence
    points = Column(Integer, nullable=False)
    # 关联
    source_type = Column(String(30))    # "task"/"assessment"/"community"/"stage"
    source_id = Column(String(50))      # 关联 ID
    description = Column(String(200))
    # 元数据
    created_at = Column(DateTime, server_default=func.now())
    __table_args__ = (
        Index("ix_point_user_dim", "user_id", "dimension"),
        Index("ix_point_user_date", "user_id", "created_at"),
    )


class UserPointBalance(Base):
    """用户积分余额 (三维)"""
    __tablename__ = "user_point_balances"
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    growth = Column(Integer, default=0)
    contribution = Column(Integer, default=0)
    influence = Column(Integer, default=0)
    total = Column(Integer, default=0)
    # 统计
    streak_days = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)
    last_checkin_date = Column(DateTime)
    tasks_completed_total = Column(Integer, default=0)
    assessments_completed = Column(Integer, default=0)
    # 时间
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class IncentiveReward(Base):
    """激励奖励定义 (可兑换/自动解锁)"""
    __tablename__ = "incentive_rewards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    reward_type = Column(String(30), nullable=False)    # badge/title/feature/item
    name = Column(String(50), nullable=False)
    description = Column(Text)
    icon = Column(String(10))
    # 解锁条件
    unlock_dimension = Column(String(15))  # growth/contribution/influence/streak
    unlock_threshold = Column(Integer)
    unlock_growth_level = Column(String(4))  # G0-G5
    # 处方关联: 解锁后影响处方
    rx_effect = Column(JSON)   # {"unlock_mode": "challenge", "bonus_tasks": [...]}
    is_active = Column(Boolean, default=True)


class UserReward(Base):
    """用户已获得的奖励"""
    __tablename__ = "user_rewards"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reward_id = Column(Integer, ForeignKey("incentive_rewards.id"), nullable=False)
    earned_at = Column(DateTime, server_default=func.now())
    __table_args__ = (
        UniqueConstraint("user_id", "reward_id", name="uq_user_reward"),
    )


# ══════════════════════════════════════════════
# 积分引擎
# ══════════════════════════════════════════════

class PointEngine:
    """积分计算与发放"""

    def __init__(self, db: Session):
        self.db = db

    def _get_or_create_balance(self, user_id: int) -> UserPointBalance:
        bal = self.db.query(UserPointBalance).filter_by(user_id=user_id).first()
        if not bal:
            bal = UserPointBalance(user_id=user_id)
            self.db.add(bal)
            self.db.flush()
        return bal

    def _check_daily_cap(self, user_id: int, event_type: str) -> int:
        """返回今日已获得的该类型积分"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        total = (
            self.db.query(func.coalesce(func.sum(PointEvent.points), 0))
            .filter(
                PointEvent.user_id == user_id,
                PointEvent.event_type == event_type,
                PointEvent.created_at >= today,
            )
            .scalar()
        )
        return total or 0

    def award(
        self,
        user_id: int,
        event_type: str,
        source_type: str = "",
        source_id: str = "",
        description: str = "",
        extra_points: int = 0,
    ) -> dict:
        """发放积分，返回本次积分详情"""
        rule = POINT_RULES.get(event_type)
        if not rule:
            return {"awarded": False, "reason": f"unknown event: {event_type}"}

        dim = rule["dimension"]

        # 计算积分
        if "points_map" in rule:
            points = extra_points  # 调用方传入具体值
        elif "points_per_unit" in rule:
            points = int(extra_points * rule["points_per_unit"])
        else:
            points = rule.get("points", 0)

        # 每日上限
        if "daily_cap" in rule:
            already = self._check_daily_cap(user_id, event_type)
            remaining = rule["daily_cap"] - already
            if remaining <= 0:
                return {"awarded": False, "reason": "daily_cap_reached", "cap": rule["daily_cap"]}
            points = min(points, remaining)

        if points <= 0:
            return {"awarded": False, "reason": "zero_points"}

        # 写入事件
        event = PointEvent(
            user_id=user_id,
            event_type=event_type,
            dimension=dim,
            points=points,
            source_type=source_type,
            source_id=source_id,
            description=description,
        )
        self.db.add(event)

        # 更新余额
        bal = self._get_or_create_balance(user_id)
        setattr(bal, dim, getattr(bal, dim) + points)
        bal.total = bal.growth + bal.contribution + bal.influence

        self.db.commit()

        return {
            "awarded": True,
            "event_type": event_type,
            "dimension": dim,
            "points": points,
            "new_balance": {
                "growth": bal.growth,
                "contribution": bal.contribution,
                "influence": bal.influence,
                "total": bal.total,
            },
        }

    def record_checkin(self, user_id: int) -> dict:
        """日打卡: 更新连续天数 + 发放积分 + 检查里程碑"""
        bal = self._get_or_create_balance(user_id)
        today = datetime.now().date()
        last = bal.last_checkin_date.date() if bal.last_checkin_date else None

        if last == today:
            return {"awarded": False, "reason": "already_checked_in_today"}

        # 连续天数
        if last and (today - last).days == 1:
            bal.streak_days += 1
        elif last and (today - last).days > 1:
            bal.streak_days = 1  # 中断重置
        else:
            bal.streak_days = 1  # 首次

        bal.longest_streak = max(bal.longest_streak, bal.streak_days)
        bal.last_checkin_date = datetime.now()
        self.db.commit()

        # 基础打卡积分
        result = self.award(user_id, "daily_checkin", "checkin", str(today))

        # 检查里程碑
        milestones = POINT_RULES["streak_milestone"]["points_map"]
        if bal.streak_days in milestones:
            bonus = self.award(
                user_id, "streak_milestone",
                source_type="streak",
                source_id=str(bal.streak_days),
                description=f"连续打卡{bal.streak_days}天",
                extra_points=milestones[bal.streak_days],
            )
            result["milestone"] = {
                "days": bal.streak_days,
                "bonus_points": milestones[bal.streak_days],
            }

        result["streak_days"] = bal.streak_days
        result["longest_streak"] = bal.longest_streak
        return result

    def record_task_complete(self, user_id: int, task_id: str) -> dict:
        """处方任务完成"""
        bal = self._get_or_create_balance(user_id)
        bal.tasks_completed_total = (bal.tasks_completed_total or 0) + 1
        self.db.flush()
        return self.award(user_id, "task_complete", "task", task_id)


# ══════════════════════════════════════════════
# 激励→处方反向影响
# ══════════════════════════════════════════════

# 成长等级解锁的处方模式
GROWTH_LEVEL_RX_UNLOCKS: dict[str, dict] = {
    "G0": {
        "rx_modes": ["guide"],
        "max_daily_tasks": 2,
        "social_features": [],
    },
    "G1": {
        "rx_modes": ["guide", "nudge"],
        "max_daily_tasks": 3,
        "social_features": ["view_community"],
    },
    "G2": {
        "rx_modes": ["guide", "nudge", "challenge"],
        "max_daily_tasks": 4,
        "social_features": ["view_community", "share_progress"],
    },
    "G3": {
        "rx_modes": ["guide", "nudge", "challenge", "coach_assist"],
        "max_daily_tasks": 5,
        "social_features": ["view_community", "share_progress", "peer_support"],
    },
    "G4": {
        "rx_modes": ["guide", "nudge", "challenge", "coach_assist", "self_design"],
        "max_daily_tasks": 6,
        "social_features": ["view_community", "share_progress", "peer_support", "mentor"],
    },
    "G5": {
        "rx_modes": ["guide", "nudge", "challenge", "coach_assist", "self_design", "community_lead"],
        "max_daily_tasks": 8,
        "social_features": ["all"],
    },
}

# 连续打卡奖励效果
STREAK_RX_BONUSES: dict[int, dict] = {
    7:  {"unlock": "weekly_summary", "rx_boost": 1.1},
    14: {"unlock": "custom_reminder", "rx_boost": 1.15},
    30: {"unlock": "advanced_analytics", "rx_boost": 1.2},
    60: {"unlock": "challenge_mode", "rx_boost": 1.25},
    90: {"unlock": "mentor_apply", "rx_boost": 1.3},
}


def get_rx_context_from_incentive(
    growth_level: str,
    streak_days: int,
    point_balance: dict,
) -> dict:
    """
    激励数据 → 处方上下文
    在 InterventionPlanner 生成处方时调用, 影响处方参数
    """
    gl_config = GROWTH_LEVEL_RX_UNLOCKS.get(growth_level, GROWTH_LEVEL_RX_UNLOCKS["G0"])

    # 连续打卡加成
    rx_boost = 1.0
    unlocked_features = []
    for days, bonus in sorted(STREAK_RX_BONUSES.items()):
        if streak_days >= days:
            rx_boost = bonus["rx_boost"]
            unlocked_features.append(bonus["unlock"])

    return {
        "available_rx_modes": gl_config["rx_modes"],
        "max_daily_tasks": gl_config["max_daily_tasks"],
        "social_features": gl_config["social_features"],
        "rx_intensity_boost": rx_boost,
        "streak_unlocks": unlocked_features,
        "growth_level": growth_level,
        "streak_days": streak_days,
    }

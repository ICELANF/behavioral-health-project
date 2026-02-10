"""
#1 效果追踪回路 — 干预→效果→调整闭环
放置: api/core/intervention_tracker.py

核心问题: 干预计划生成后缺乏系统性效果追踪
解决方案:
  - InterventionOutcome 表: 记录每次干预的效果数据
  - EffectivenessEvaluator: 周/月维度计算干预有效性
  - PDCA 自动调整: 根据效果数据触发处方调整
"""
from datetime import datetime, timedelta
from enum import Enum as PyEnum
from typing import Any, Optional
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime, Boolean, JSON,
    ForeignKey, Index,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import Session

from v3.database import Base


# ══════════════════════════════════════════════
# 枚举
# ══════════════════════════════════════════════

class OutcomeType(str, PyEnum):
    TASK_COMPLETION = "task_completion"     # 单任务完成/跳过
    DAILY_CHECKIN = "daily_checkin"         # 日打卡汇总
    WEEKLY_REVIEW = "weekly_review"         # 周复盘
    MONTHLY_REVIEW = "monthly_review"       # 月评估
    SPI_RETEST = "spi_retest"              # SPI 复评
    STAGE_TRANSITION = "stage_transition"   # 阶段转换


class AdjustmentAction(str, PyEnum):
    NONE = "none"
    REDUCE_DIFFICULTY = "reduce_difficulty"
    REDUCE_QUANTITY = "reduce_quantity"
    INCREASE_DIFFICULTY = "increase_difficulty"
    SWITCH_STRATEGY = "switch_strategy"
    COACH_CONTACT = "coach_contact"
    REASSESS = "reassess"
    DEMOTE_STAGE = "demote_stage"


# ══════════════════════════════════════════════
# 数据表
# ══════════════════════════════════════════════

class InterventionOutcome(Base):
    """干预效果追踪记录 — 每条记录一个效果数据点"""
    __tablename__ = "intervention_outcomes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    outcome_type = Column(String(20), nullable=False)
    # 时间窗口
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    # 核心指标
    completion_rate = Column(Float)            # 0.0-1.0
    streak_days = Column(Integer, default=0)
    tasks_assigned = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    tasks_skipped = Column(Integer, default=0)
    # SPI 变化
    spi_before = Column(Float)
    spi_after = Column(Float)
    spi_delta = Column(Float)
    # 阶段信息
    stage_before = Column(String(4))  # S0-S6
    stage_after = Column(String(4))
    readiness_before = Column(String(4))  # L1-L5
    readiness_after = Column(String(4))
    cultivation_stage = Column(String(20))  # startup/adaptation/stability/internalization
    # 用户主观反馈
    user_mood = Column(Integer)        # 1-5
    user_difficulty = Column(Integer)  # 1-5 觉得难度
    user_notes = Column(Text)
    # 系统判定
    effectiveness_score = Column(Float)  # 0-100 综合有效性
    adjustment_action = Column(String(30))
    adjustment_detail = Column(JSON)
    # 元数据
    created_at = Column(DateTime, server_default=func.now())
    __table_args__ = (
        Index("ix_outcome_user_type", "user_id", "outcome_type"),
        Index("ix_outcome_user_period", "user_id", "period_start"),
    )


class StageTransitionLog(Base):
    """阶段转换历史 — 纵向追踪用户全生命周期"""
    __tablename__ = "stage_transition_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    transition_type = Column(String(20), nullable=False)  # behavioral/readiness/cultivation/growth
    from_value = Column(String(10), nullable=False)
    to_value = Column(String(10), nullable=False)
    trigger = Column(String(50))       # 什么触发了转换
    evidence = Column(JSON)            # 支撑数据
    created_at = Column(DateTime, server_default=func.now())
    __table_args__ = (
        Index("ix_stage_trans_user", "user_id", "transition_type"),
    )


# ══════════════════════════════════════════════
# PDCA 调整触发器
# ══════════════════════════════════════════════

ADJUSTMENT_TRIGGERS: dict[str, dict] = {
    "low_weekly_completion": {
        "condition": lambda o: o.get("completion_rate", 1) < 0.5,
        "action": AdjustmentAction.REDUCE_DIFFICULTY,
        "message": "周完成率<50%，降低任务难度",
    },
    "streak_break": {
        "condition": lambda o: o.get("streak_break_days", 0) >= 3,
        "action": AdjustmentAction.COACH_CONTACT,
        "message": "连续3天未完成，触发教练联系",
    },
    "spi_decrease": {
        "condition": lambda o: o.get("spi_delta", 0) <= -10,
        "action": AdjustmentAction.REASSESS,
        "message": "SPI下降≥10分，需要重新评估",
    },
    "cultivation_timeout": {
        "condition": lambda o: o.get("days_in_stage", 0) > o.get("max_days", 999),
        "action": AdjustmentAction.SWITCH_STRATEGY,
        "message": "养成阶段超时，切换干预策略",
    },
    "high_difficulty_report": {
        "condition": lambda o: o.get("avg_difficulty", 0) >= 4.5,
        "action": AdjustmentAction.REDUCE_QUANTITY,
        "message": "用户持续报告高难度，减少任务数",
    },
    "excellent_performance": {
        "condition": lambda o: o.get("completion_rate", 0) >= 0.9 and o.get("streak_days", 0) >= 14,
        "action": AdjustmentAction.INCREASE_DIFFICULTY,
        "message": "表现优秀，可提升挑战难度",
    },
}

# 养成阶段晋级条件
CULTIVATION_PROMOTION_RULES: dict[str, dict] = {
    "startup": {
        "next": "adaptation",
        "min_days": 14,
        "min_completion_rate": 0.6,
        "min_check_ins": 10,
        "max_days": 30,
    },
    "adaptation": {
        "next": "stability",
        "min_days": 56,
        "min_completion_rate": 0.7,
        "min_streak_days": 14,
        "max_days": 120,
    },
    "stability": {
        "next": "internalization",
        "min_days": 120,
        "min_completion_rate": 0.8,
        "min_streak_days": 30,
        "max_days": 365,
    },
    "internalization": {
        "next": None,
        "min_days": 180,
        "min_completion_rate": 0.75,
        "max_days": None,
    },
}


# ══════════════════════════════════════════════
# 核心业务逻辑
# ══════════════════════════════════════════════

class EffectivenessEvaluator:
    """干预有效性评估器"""

    @staticmethod
    def calculate_effectiveness(
        completion_rate: float,
        spi_delta: float | None,
        streak_days: int,
        user_mood: int | None,
        cultivation_stage: str,
    ) -> float:
        """
        综合有效性评分 0-100
        权重: 完成率40% + SPI变化25% + 连续天数20% + 情绪15%
        """
        # 完成率得分 (0-40)
        cr_score = min(completion_rate, 1.0) * 40

        # SPI 变化得分 (0-25): delta>0 加分, <0 减分
        if spi_delta is not None:
            spi_score = max(min(spi_delta / 20 * 25, 25), 0)
        else:
            spi_score = 12.5  # 无数据取中值

        # 连续打卡得分 (0-20): 30天满分
        streak_score = min(streak_days / 30, 1.0) * 20

        # 情绪得分 (0-15)
        if user_mood is not None:
            mood_score = (user_mood / 5) * 15
        else:
            mood_score = 7.5

        return round(cr_score + spi_score + streak_score + mood_score, 1)

    @staticmethod
    def check_triggers(metrics: dict) -> list[dict]:
        """检查所有 PDCA 触发条件，返回触发的调整建议"""
        triggered = []
        for name, rule in ADJUSTMENT_TRIGGERS.items():
            try:
                if rule["condition"](metrics):
                    triggered.append({
                        "trigger": name,
                        "action": rule["action"].value,
                        "message": rule["message"],
                    })
            except (KeyError, TypeError):
                continue
        return triggered

    @staticmethod
    def check_cultivation_promotion(
        current_stage: str,
        days_in_stage: int,
        completion_rate: float,
        streak_days: int,
        check_ins: int = 0,
    ) -> dict:
        """检查养成阶段是否可以晋级"""
        rules = CULTIVATION_PROMOTION_RULES.get(current_stage)
        if not rules or not rules["next"]:
            return {"promote": False, "reason": "已达最终阶段"}

        failures = []
        if days_in_stage < rules["min_days"]:
            failures.append(f"天数不足: {days_in_stage}/{rules['min_days']}")
        if completion_rate < rules["min_completion_rate"]:
            failures.append(f"完成率不足: {completion_rate:.0%}/{rules['min_completion_rate']:.0%}")
        if "min_streak_days" in rules and streak_days < rules["min_streak_days"]:
            failures.append(f"连续天数不足: {streak_days}/{rules['min_streak_days']}")
        if "min_check_ins" in rules and check_ins < rules["min_check_ins"]:
            failures.append(f"打卡次数不足: {check_ins}/{rules['min_check_ins']}")

        if not failures:
            return {
                "promote": True,
                "next_stage": rules["next"],
                "reason": "所有条件满足",
            }
        return {"promote": False, "failures": failures}


def record_daily_outcome(
    db: Session,
    user_id: int,
    date: datetime,
    tasks_assigned: int,
    tasks_completed: int,
    tasks_skipped: int,
    streak_days: int,
    user_mood: int | None = None,
    user_difficulty: int | None = None,
    user_notes: str = "",
    cultivation_stage: str = "startup",
    spi_before: float | None = None,
    spi_after: float | None = None,
) -> InterventionOutcome:
    """记录每日效果数据 + 自动触发 PDCA 检查"""
    cr = tasks_completed / tasks_assigned if tasks_assigned > 0 else 0
    spi_delta = (spi_after - spi_before) if (spi_before and spi_after) else None

    eff = EffectivenessEvaluator.calculate_effectiveness(
        cr, spi_delta, streak_days, user_mood, cultivation_stage,
    )

    # 检查触发条件
    metrics = {
        "completion_rate": cr,
        "streak_days": streak_days,
        "streak_break_days": 0 if tasks_completed > 0 else 1,
        "spi_delta": spi_delta,
        "avg_difficulty": user_difficulty,
    }
    triggers = EffectivenessEvaluator.check_triggers(metrics)

    action = AdjustmentAction.NONE
    detail = None
    if triggers:
        # 取优先级最高的 action
        action = AdjustmentAction(triggers[0]["action"])
        detail = triggers

    outcome = InterventionOutcome(
        user_id=user_id,
        outcome_type=OutcomeType.DAILY_CHECKIN.value,
        period_start=date,
        period_end=date + timedelta(days=1),
        completion_rate=round(cr, 4),
        streak_days=streak_days,
        tasks_assigned=tasks_assigned,
        tasks_completed=tasks_completed,
        tasks_skipped=tasks_skipped,
        spi_before=spi_before,
        spi_after=spi_after,
        spi_delta=spi_delta,
        cultivation_stage=cultivation_stage,
        user_mood=user_mood,
        user_difficulty=user_difficulty,
        user_notes=user_notes,
        effectiveness_score=eff,
        adjustment_action=action.value,
        adjustment_detail=detail,
    )
    db.add(outcome)
    db.commit()
    db.refresh(outcome)
    return outcome


def generate_weekly_review(
    db: Session,
    user_id: int,
    week_start: datetime,
) -> InterventionOutcome:
    """聚合 7 天日数据生成周复盘"""
    week_end = week_start + timedelta(days=7)
    dailies = (
        db.query(InterventionOutcome)
        .filter(
            InterventionOutcome.user_id == user_id,
            InterventionOutcome.outcome_type == OutcomeType.DAILY_CHECKIN.value,
            InterventionOutcome.period_start >= week_start,
            InterventionOutcome.period_start < week_end,
        )
        .all()
    )

    if not dailies:
        total_assigned = total_completed = total_skipped = 0
        avg_mood = avg_diff = None
        max_streak = 0
    else:
        total_assigned = sum(d.tasks_assigned or 0 for d in dailies)
        total_completed = sum(d.tasks_completed or 0 for d in dailies)
        total_skipped = sum(d.tasks_skipped or 0 for d in dailies)
        moods = [d.user_mood for d in dailies if d.user_mood]
        diffs = [d.user_difficulty for d in dailies if d.user_difficulty]
        avg_mood = round(sum(moods) / len(moods), 1) if moods else None
        avg_diff = round(sum(diffs) / len(diffs), 1) if diffs else None
        max_streak = max((d.streak_days or 0) for d in dailies)

    cr = total_completed / total_assigned if total_assigned > 0 else 0
    cult = dailies[-1].cultivation_stage if dailies else "startup"

    eff = EffectivenessEvaluator.calculate_effectiveness(
        cr, None, max_streak, round(avg_mood) if avg_mood else None, cult,
    )

    triggers = EffectivenessEvaluator.check_triggers({
        "completion_rate": cr,
        "streak_days": max_streak,
        "streak_break_days": 7 - len(dailies),
        "avg_difficulty": avg_diff,
    })

    action = AdjustmentAction(triggers[0]["action"]) if triggers else AdjustmentAction.NONE

    review = InterventionOutcome(
        user_id=user_id,
        outcome_type=OutcomeType.WEEKLY_REVIEW.value,
        period_start=week_start,
        period_end=week_end,
        completion_rate=round(cr, 4),
        streak_days=max_streak,
        tasks_assigned=total_assigned,
        tasks_completed=total_completed,
        tasks_skipped=total_skipped,
        cultivation_stage=cult,
        user_mood=round(avg_mood) if avg_mood else None,
        user_difficulty=round(avg_diff) if avg_diff else None,
        effectiveness_score=eff,
        adjustment_action=action.value,
        adjustment_detail=triggers if triggers else None,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def log_stage_transition(
    db: Session,
    user_id: int,
    transition_type: str,
    from_val: str,
    to_val: str,
    trigger: str = "",
    evidence: dict | None = None,
) -> StageTransitionLog:
    """记录阶段转换 — 纵向效果追踪"""
    log = StageTransitionLog(
        user_id=user_id,
        transition_type=transition_type,
        from_value=from_val,
        to_value=to_val,
        trigger=trigger,
        evidence=evidence,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

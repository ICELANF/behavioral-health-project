"""
VisionGuard API  —  /v1/vision/behavior/*
Phase 0 基础 CRUD + Phase 1 打卡接口

续接平台现有路由风格（FastAPI / UUID / 依赖注入）
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.migration_057_vision_behavior import (
    InputSourceEnum,
    RiskLevelEnum,
    VisionBehaviorGoal,
    VisionBehaviorLog,
    VisionParentBinding,
)

# 依赖注入占位（替换为平台实际实现）
# from app.deps import get_db, get_current_user
# from app.core.permissions import require_role

router = APIRouter(prefix="/v1/vision/behavior", tags=["VisionGuard · 行为打卡"])


# ══════════════════════════════════════════════════════════════════════════════
# Pydantic Schemas
# ══════════════════════════════════════════════════════════════════════════════


class BehaviorLogIn(BaseModel):
    """行为打卡写入体 — 学员/家长/教练提交"""

    log_date: date = Field(default_factory=date.today)
    outdoor_minutes: Optional[int] = Field(None, ge=0, le=1440)
    screen_sessions: Optional[int] = Field(None, ge=0)
    screen_total_minutes: Optional[int] = Field(None, ge=0, le=1440)
    eye_exercise_done: Optional[bool] = None
    lutein_intake_mg: Optional[Decimal] = Field(None, ge=0, le=100)
    sleep_minutes: Optional[int] = Field(None, ge=0, le=1440)
    input_source: InputSourceEnum = InputSourceEnum.MANUAL


class BehaviorLogOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    log_date: date
    outdoor_minutes: Optional[int]
    screen_sessions: Optional[int]
    screen_total_minutes: Optional[int]
    eye_exercise_done: bool
    lutein_intake_mg: Optional[Decimal]
    sleep_minutes: Optional[int]
    behavior_score: Decimal
    input_source: InputSourceEnum
    created_at: datetime

    class Config:
        from_attributes = True


class GoalIn(BaseModel):
    """目标更新体（专家 / 教练 / 用户自申请）"""

    outdoor_target_min: Optional[int] = Field(None, ge=30, le=480)
    screen_session_limit: Optional[int] = Field(None, ge=5, le=60)
    screen_daily_limit: Optional[int] = Field(None, ge=30, le=600)
    lutein_target_mg: Optional[Decimal] = Field(None, ge=0, le=100)
    sleep_target_min: Optional[int] = Field(None, ge=300, le=720)
    risk_level_at_set: Optional[RiskLevelEnum] = None
    set_by_expert_id: Optional[uuid.UUID] = None


class GoalOut(BaseModel):
    user_id: uuid.UUID
    outdoor_target_min: int
    screen_session_limit: int
    screen_daily_limit: int
    lutein_target_mg: Decimal
    sleep_target_min: int
    risk_level_at_set: Optional[RiskLevelEnum]
    set_by_expert_id: Optional[uuid.UUID]
    updated_at: datetime

    class Config:
        from_attributes = True


class ParentBindIn(BaseModel):
    student_user_id: uuid.UUID
    parent_user_id: uuid.UUID
    notify_risk_threshold: RiskLevelEnum = RiskLevelEnum.WATCH
    can_input_behavior: bool = True


class CheckinFeedback(BaseModel):
    """打卡后即时反馈（Phase 1 VisionGuideAgent 生成）"""

    log: BehaviorLogOut
    instant_message: str
    completion_pct: float  # 当日五维合计达标百分比
    streak_days: int  # 连续达标天数


# ══════════════════════════════════════════════════════════════════════════════
# 评分算法（Job 27 复用同一函数）
# ══════════════════════════════════════════════════════════════════════════════


def calc_behavior_score(
    log: VisionBehaviorLog,
    goal: VisionBehaviorGoal,
) -> Decimal:
    """
    五维加权评分 → 0-100
    权重: 户外 35 / 屏幕 30 / 眼保健操 10 / 叶黄素 10 / 睡眠 15
    """
    score = Decimal("0")

    # 户外 35%
    if log.outdoor_minutes is not None and goal.outdoor_target_min > 0:
        ratio = min(log.outdoor_minutes / goal.outdoor_target_min, 1.0)
        score += Decimal(str(ratio * 35))

    # 屏幕（超标扣分，未记录不扣）30%
    if log.screen_total_minutes is not None and goal.screen_daily_limit > 0:
        ratio = max(0.0, 1.0 - (log.screen_total_minutes / goal.screen_daily_limit - 1.0))
        ratio = min(ratio, 1.0)
        score += Decimal(str(ratio * 30))

    # 眼保健操 10%
    if log.eye_exercise_done:
        score += Decimal("10")

    # 叶黄素 10%
    if log.lutein_intake_mg is not None and goal.lutein_target_mg > 0:
        ratio = min(float(log.lutein_intake_mg / goal.lutein_target_mg), 1.0)
        score += Decimal(str(ratio * 10))

    # 睡眠 15%
    if log.sleep_minutes is not None and goal.sleep_target_min > 0:
        ratio = min(log.sleep_minutes / goal.sleep_target_min, 1.0)
        score += Decimal(str(ratio * 15))

    return score.quantize(Decimal("0.1"))


def build_instant_message(log: VisionBehaviorLog, goal: VisionBehaviorGoal) -> str:
    """
    根据打卡数据生成即时反馈文案
    实际生产中调用 VisionGuideAgent.generate_response(intent=behavior_checkin)
    """
    if log.outdoor_minutes is not None:
        gap = goal.outdoor_target_min - log.outdoor_minutes
        if gap > 0:
            return (
                f"今天出门了 {log.outdoor_minutes} 分钟——"
                f"距目标还差 {gap} 分钟！傍晚随便出去转转就够了 😊"
            )
        else:
            return f"户外达标！今天出门 {log.outdoor_minutes} 分钟，超出目标 {-gap} 分钟，棒！"
    if log.eye_exercise_done:
        return "眼保健操打卡✓ 坚持住，每一次都在保护你的眼睛！"
    return "打卡成功！今天的护眼数据已记录。"


# ══════════════════════════════════════════════════════════════════════════════
# 路由
# ══════════════════════════════════════════════════════════════════════════════


@router.post(
    "/log",
    response_model=CheckinFeedback,
    status_code=status.HTTP_201_CREATED,
    summary="行为打卡（学员/家长/教练提交）",
)
async def create_behavior_log(
    body: BehaviorLogIn,
    # db: AsyncSession = Depends(get_db),
    # current_user = Depends(get_current_user),
):
    """
    写入行为日志（UPSERT by user_id+log_date），
    同步计算 behavior_score 并返回即时反馈。
    """
    # TODO: 替换为实际 DB session 与 current_user
    # async with db.begin():
    #     goal = await _get_or_create_goal(db, current_user.id)
    #     stmt = pg_insert(VisionBehaviorLog).values(
    #         user_id=current_user.id,
    #         log_date=body.log_date,
    #         outdoor_minutes=body.outdoor_minutes,
    #         screen_sessions=body.screen_sessions,
    #         screen_total_minutes=body.screen_total_minutes,
    #         eye_exercise_done=body.eye_exercise_done or False,
    #         lutein_intake_mg=body.lutein_intake_mg,
    #         sleep_minutes=body.sleep_minutes,
    #         input_source=body.input_source,
    #     ).on_conflict_do_update(
    #         index_elements=["user_id", "log_date"],
    #         set_={k: v for k, v in {
    #             "outdoor_minutes": body.outdoor_minutes,
    #             "screen_sessions": body.screen_sessions,
    #             "screen_total_minutes": body.screen_total_minutes,
    #             "eye_exercise_done": body.eye_exercise_done,
    #             "lutein_intake_mg": body.lutein_intake_mg,
    #             "sleep_minutes": body.sleep_minutes,
    #             "input_source": body.input_source,
    #         }.items() if v is not None},
    #     ).returning(VisionBehaviorLog)
    #     row = (await db.execute(stmt)).scalar_one()
    #     score = calc_behavior_score(row, goal)
    #     await db.execute(
    #         update(VisionBehaviorLog)
    #         .where(VisionBehaviorLog.id == row.id)
    #         .values(behavior_score=score)
    #     )
    pass

    return {
        "log": {},
        "instant_message": "（需连接数据库）",
        "completion_pct": 0.0,
        "streak_days": 0,
    }


@router.get(
    "/log/{user_id}",
    response_model=list[BehaviorLogOut],
    summary="查询行为日志（近 N 天）",
)
async def get_behavior_logs(
    user_id: uuid.UUID,
    days: int = Query(7, ge=1, le=90),
    # db: AsyncSession = Depends(get_db),
):
    """
    返回指定学员最近 N 天的行为日志，按日期倒序。
    """
    # stmt = (
    #     select(VisionBehaviorLog)
    #     .where(VisionBehaviorLog.user_id == user_id)
    #     .order_by(VisionBehaviorLog.log_date.desc())
    #     .limit(days)
    # )
    # rows = (await db.execute(stmt)).scalars().all()
    # return rows
    return []


@router.get(
    "/goals/{user_id}",
    response_model=GoalOut,
    summary="查询个人护眼目标",
)
async def get_behavior_goals(
    user_id: uuid.UUID,
    # db: AsyncSession = Depends(get_db),
):
    # goal = await _get_or_create_goal(db, user_id)
    # return goal
    pass


@router.put(
    "/goals/{user_id}",
    response_model=GoalOut,
    summary="更新护眼目标（专家/教练/自申请）",
)
async def upsert_behavior_goals(
    user_id: uuid.UUID,
    body: GoalIn,
    # db: AsyncSession = Depends(get_db),
    # current_user = Depends(get_current_user),
):
    """
    UPSERT vision_behavior_goals。
    若 set_by_expert_id 存在，记录专家覆盖。
    """
    # async with db.begin():
    #     stmt = pg_insert(VisionBehaviorGoal).values(
    #         user_id=user_id, **body.model_dump(exclude_none=True)
    #     ).on_conflict_do_update(
    #         index_elements=["user_id"],
    #         set_={**body.model_dump(exclude_none=True), "updated_at": text("NOW()")},
    #     ).returning(VisionBehaviorGoal)
    #     return (await db.execute(stmt)).scalar_one()
    pass


@router.post(
    "/parent-binding",
    status_code=status.HTTP_201_CREATED,
    summary="绑定家长-学员关系",
)
async def create_parent_binding(
    body: ParentBindIn,
    # db: AsyncSession = Depends(get_db),
):
    # async with db.begin():
    #     stmt = pg_insert(VisionParentBinding).values(**body.model_dump())
    #     .on_conflict_do_nothing()
    #     await db.execute(stmt)
    # return {"status": "ok"}
    return {"status": "ok"}


@router.get(
    "/parent-binding/{parent_user_id}",
    summary="家长获取所有绑定学员",
)
async def get_parent_students(
    parent_user_id: uuid.UUID,
    # db: AsyncSession = Depends(get_db),
):
    # rows = await db.execute(
    #     select(VisionParentBinding)
    #     .where(VisionParentBinding.parent_user_id == parent_user_id)
    # )
    # return rows.scalars().all()
    return []


# ══════════════════════════════════════════════════════════════════════════════
# 内部辅助
# ══════════════════════════════════════════════════════════════════════════════


async def _get_or_create_goal(db: AsyncSession, user_id: uuid.UUID) -> VisionBehaviorGoal:
    """懒创建：若无目标配置，以默认值初始化"""
    result = await db.execute(
        select(VisionBehaviorGoal).where(VisionBehaviorGoal.user_id == user_id)
    )
    goal = result.scalar_one_or_none()
    if goal is None:
        goal = VisionBehaviorGoal(user_id=user_id)
        db.add(goal)
        await db.flush()
    return goal

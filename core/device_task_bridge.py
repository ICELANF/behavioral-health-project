# -*- coding: utf-8 -*-
"""
设备数据 → 每日任务自动打卡桥接
Device Data → DailyTask Auto-Checkin Bridge

当用户提交设备数据 (血糖/血压/体重/睡眠/运动) 时，
自动匹配并完成今日对应的监测类任务。

与 food_recognition_api._try_auto_checkin_nutrition_task 同模式。
"""

from datetime import date, datetime, timedelta
from typing import Optional

from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.models import DailyTask, TaskCheckin

# ============================================
# 设备类型 → 任务匹配映射
# ============================================

DEVICE_TYPE_TASK_MAP = {
    "glucose":        {"tag": "监测", "keyword": "血糖"},
    "blood_pressure": {"tag": "监测", "keyword": "血压"},
    "weight":         {"tag": "监测", "keyword": "体重"},
    "sleep":          {"tag": "睡眠", "keyword": None},
    "activity":       {"tag": "运动", "keyword": None},
}

# 血糖 meal_tag → 任务 time_hint 中文关键词
MEAL_TAG_HINT_MAP = {
    "fasting":     "空腹",
    "before_meal": "餐前",
    "after_meal":  "餐后",
    "bedtime":     "睡前",
}


def try_auto_checkin_device_task(
    db: Session,
    user_id: int,
    device_type: str,
    value: Optional[float] = None,
    note: Optional[str] = None,
    time_hint: Optional[str] = None,
) -> Optional[dict]:
    """
    自动打卡设备监测任务。

    在调用方的 db_transaction() 内执行, **不** 调用 db.commit()。

    Returns:
        dict {task_id, task_title, points_earned, streak} 或 None
    """
    try:
        mapping = DEVICE_TYPE_TASK_MAP.get(device_type)
        if not mapping:
            return None

        today = date.today()
        now = datetime.now()
        tag = mapping["tag"]
        keyword = mapping.get("keyword")

        # 1) 查找匹配的未完成任务
        task = _find_matching_task(db, user_id, today, tag, keyword, time_hint)
        if not task:
            return None

        # 2) 写入打卡记录
        checkin = TaskCheckin(
            task_id=task.id,
            user_id=user_id,
            value=value,
            note=note or "",
            points_earned=10,
        )
        db.add(checkin)

        # 3) 标记任务完成
        task.done = True
        task.done_time = now

        # 4) 累加成长积分
        db.execute(
            text("UPDATE users SET growth_points = COALESCE(growth_points, 0) + 10 WHERE id = :uid"),
            {"uid": user_id},
        )

        # 5) 更新连续天数
        streak_days = _update_streak(db, user_id, today)

        logger.info(
            f"[DeviceTaskBridge] Auto-checkin: user={user_id}, type={device_type}, "
            f"task={task.id}, streak={streak_days}"
        )

        return {
            "task_id": task.id,
            "task_title": task.title,
            "points_earned": 10,
            "streak": streak_days,
        }

    except Exception as e:
        logger.warning(f"[DeviceTaskBridge] 自动打卡失败: device_type={device_type}, error={e}")
        return None


def _find_matching_task(
    db: Session,
    user_id: int,
    today: date,
    tag: str,
    keyword: Optional[str],
    time_hint: Optional[str],
) -> Optional[DailyTask]:
    """
    两级匹配：
    1) tag + keyword + time_hint (精确，如「监测」+「血糖」+「空腹」)
    2) tag + keyword (宽松回退，如「监测」+「血糖」any undone)
    3) tag only (用于 sleep/activity，无 keyword)
    """
    base = (
        db.query(DailyTask)
        .filter(
            DailyTask.user_id == user_id,
            DailyTask.task_date == today,
            DailyTask.done == False,
            DailyTask.tag == tag,
        )
    )

    if keyword:
        base = base.filter(DailyTask.title.contains(keyword))

    # 尝试精确匹配 time_hint
    if time_hint:
        exact = (
            base.filter(DailyTask.time_hint.contains(time_hint))
            .order_by(DailyTask.id)
            .first()
        )
        if exact:
            return exact

    # 回退：tag + keyword (或纯 tag)
    return base.order_by(DailyTask.id).first()


def _update_streak(db: Session, user_id: int, today: date) -> int:
    """
    更新 user_streaks 表连续天数。
    与 food_recognition_api._try_auto_checkin_nutrition_task 同逻辑。
    """
    streak_row = db.execute(
        text("SELECT current_streak, longest_streak, last_checkin_date FROM user_streaks WHERE user_id = :uid"),
        {"uid": user_id},
    ).mappings().first()

    streak_days = 1
    if not streak_row:
        db.execute(
            text("""INSERT INTO user_streaks (user_id, current_streak, longest_streak, last_checkin_date, updated_at)
                    VALUES (:uid, 1, 1, :today, NOW())"""),
            {"uid": user_id, "today": today},
        )
    else:
        last_date = streak_row["last_checkin_date"]
        current = streak_row["current_streak"] or 0
        longest = streak_row["longest_streak"] or 0
        if last_date == today:
            streak_days = current  # 同一天再次打卡，不累加
        else:
            streak_days = current + 1 if last_date == today - timedelta(days=1) else 1
            new_longest = max(longest, streak_days)
            db.execute(
                text("""UPDATE user_streaks
                        SET current_streak = :streak, longest_streak = :longest,
                            last_checkin_date = :today, updated_at = NOW()
                        WHERE user_id = :uid"""),
                {"streak": streak_days, "longest": new_longest, "today": today, "uid": user_id},
            )

    return streak_days

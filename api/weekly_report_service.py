"""
用户行为分析周报生成服务
每周日 21:00 自动为所有活跃用户生成上周行为分析周报。
"""
import logging
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("bhp.weekly_report")


async def generate_user_report(db: AsyncSession, user_id: int, week_start: date, week_end: date) -> dict:
    """为单个用户生成一周行为分析报告"""

    # 1. 任务完成情况
    task_r = (await db.execute(text("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN done THEN 1 ELSE 0 END) AS completed
        FROM daily_tasks
        WHERE user_id = :uid AND task_date BETWEEN :ws AND :we
    """), {"uid": user_id, "ws": week_start, "we": week_end})).mappings().first()
    tasks_total = task_r["total"] or 0
    tasks_completed = task_r["completed"] or 0
    completion_pct = round(tasks_completed / tasks_total * 100, 1) if tasks_total > 0 else 0

    # 2. 签到次数
    checkin_r = (await db.execute(text("""
        SELECT COUNT(*) AS cnt FROM task_checkins
        WHERE user_id = :uid AND checked_at::date BETWEEN :ws AND :we
    """), {"uid": user_id, "ws": week_start, "we": week_end})).mappings().first()
    checkin_count = checkin_r["cnt"] or 0

    # 3. 学习时长 (分钟)
    learn_r = (await db.execute(text("""
        SELECT COALESCE(SUM(minutes), 0) AS mins
        FROM learning_time_logs
        WHERE user_id = :uid AND earned_at::date BETWEEN :ws AND :we
    """), {"uid": user_id, "ws": week_start, "we": week_end})).mappings().first()
    learning_minutes = int(learn_r["mins"] or 0)

    # 4. 积分
    points_r = (await db.execute(text("""
        SELECT COALESCE(SUM(points), 0) AS pts
        FROM learning_points_logs
        WHERE user_id = :uid AND earned_at::date BETWEEN :ws AND :we
    """), {"uid": user_id, "ws": week_start, "we": week_end})).mappings().first()
    points_earned = int(points_r["pts"] or 0)

    # 5. 活动日志数
    activity_r = (await db.execute(text("""
        SELECT COUNT(*) AS cnt FROM user_activity_logs
        WHERE user_id = :uid AND created_at::date BETWEEN :ws AND :we
    """), {"uid": user_id, "ws": week_start, "we": week_end})).mappings().first()
    activity_count = activity_r["cnt"] or 0

    # 6. 连续签到天数 (本周内)
    streak_r = (await db.execute(text("""
        SELECT COUNT(DISTINCT task_date) AS streak_days
        FROM daily_tasks
        WHERE user_id = :uid AND task_date BETWEEN :ws AND :we AND done = true
    """), {"uid": user_id, "ws": week_start, "we": week_end})).mappings().first()
    streak_days = streak_r["streak_days"] or 0

    # 7. 高频任务标签 (highlights)
    tag_r = (await db.execute(text("""
        SELECT tag, COUNT(*) AS cnt
        FROM daily_tasks
        WHERE user_id = :uid AND task_date BETWEEN :ws AND :we AND done = true AND tag IS NOT NULL
        GROUP BY tag ORDER BY cnt DESC LIMIT 3
    """), {"uid": user_id, "ws": week_start, "we": week_end})).mappings().all()
    highlights = [{"tag": r["tag"], "count": r["cnt"]} for r in tag_r]

    # 8. 建议
    suggestions = []
    if completion_pct < 50:
        suggestions.append("本周任务完成率偏低，建议先从最简单的任务开始，逐步建立习惯。")
    if learning_minutes < 30:
        suggestions.append("本周学习时间较少，每天花5分钟阅读健康知识，积少成多。")
    if streak_days < 3:
        suggestions.append("连续完成天数较少，试试设置每日提醒，保持节奏。")
    if not suggestions:
        suggestions.append("本周表现不错，继续保持！")

    return {
        "user_id": user_id,
        "week_start": week_start,
        "week_end": week_end,
        "tasks_total": tasks_total,
        "tasks_completed": tasks_completed,
        "completion_pct": completion_pct,
        "checkin_count": checkin_count,
        "learning_minutes": learning_minutes,
        "points_earned": points_earned,
        "activity_count": activity_count,
        "streak_days": streak_days,
        "highlights": highlights,
        "suggestions": suggestions,
    }


async def generate_all_reports(db: AsyncSession, week_start: date, week_end: date) -> int:
    """为所有活跃用户生成周报，写入 user_weekly_reports 表。返回生成数量。"""
    # 找本周有任何活动的用户
    active_users = (await db.execute(text("""
        SELECT DISTINCT user_id FROM (
            SELECT user_id FROM daily_tasks WHERE task_date BETWEEN :ws AND :we
            UNION
            SELECT user_id FROM task_checkins WHERE checked_at::date BETWEEN :ws AND :we
            UNION
            SELECT user_id FROM learning_time_logs WHERE earned_at::date BETWEEN :ws AND :we
            UNION
            SELECT user_id FROM user_activity_logs WHERE created_at::date BETWEEN :ws AND :we
        ) sub
    """), {"ws": week_start, "we": week_end})).scalars().all()

    count = 0
    for uid in active_users:
        try:
            report = await generate_user_report(db, uid, week_start, week_end)
            import json
            await db.execute(text("""
                INSERT INTO user_weekly_reports
                    (user_id, week_start, week_end, tasks_total, tasks_completed, completion_pct,
                     checkin_count, learning_minutes, points_earned, activity_count, streak_days,
                     highlights, suggestions)
                VALUES
                    (:uid, :ws, :we, :tt, :tc, :cp, :cc, :lm, :pe, :ac, :sd,
                     CAST(:hl AS jsonb), CAST(:sg AS jsonb))
                ON CONFLICT (user_id, week_start) DO UPDATE SET
                    tasks_total = EXCLUDED.tasks_total,
                    tasks_completed = EXCLUDED.tasks_completed,
                    completion_pct = EXCLUDED.completion_pct,
                    checkin_count = EXCLUDED.checkin_count,
                    learning_minutes = EXCLUDED.learning_minutes,
                    points_earned = EXCLUDED.points_earned,
                    activity_count = EXCLUDED.activity_count,
                    streak_days = EXCLUDED.streak_days,
                    highlights = EXCLUDED.highlights,
                    suggestions = EXCLUDED.suggestions
            """), {
                "uid": report["user_id"],
                "ws": report["week_start"],
                "we": report["week_end"],
                "tt": report["tasks_total"],
                "tc": report["tasks_completed"],
                "cp": report["completion_pct"],
                "cc": report["checkin_count"],
                "lm": report["learning_minutes"],
                "pe": report["points_earned"],
                "ac": report["activity_count"],
                "sd": report["streak_days"],
                "hl": json.dumps(report["highlights"], ensure_ascii=False),
                "sg": json.dumps(report["suggestions"], ensure_ascii=False),
            })
            count += 1
        except Exception as e:
            logger.warning(f"[WeeklyReport] user {uid} 生成失败: {e}")

    await db.commit()
    logger.info(f"[WeeklyReport] 生成完毕: {count}/{len(active_users)} 用户, {week_start}~{week_end}")
    return count

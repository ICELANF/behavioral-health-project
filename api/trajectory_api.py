# -*- coding: utf-8 -*-
"""
行为轨迹 API

计算成长者的成长证据：依从性趋势、学习投入、能力提升、弹性恢复

端点:
  GET /api/v1/learning/trajectory  — 行为轨迹综合统计
"""

from typing import Any
from datetime import date, timedelta, datetime
from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text as sa_text
from loguru import logger

from core.database import get_db
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/learning", tags=["行为轨迹"])


@router.get("/trajectory")
def get_trajectory(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """
    行为轨迹综合统计:
      - adherence_rate: 近N日依从率 (%)
      - adherence_weekly: 按周的依从率列表 [{week_start, rate, done, total}]
      - learning_hours: 近N日学习总时长 (小时, 含本周)
      - learning_minutes_weekly: 按周学习分钟数
      - current_streak: 当前连续打卡天数
      - max_streak: 历史最长连续打卡天数
      - recovery_speed: 中断后平均恢复天数 (越小越好)
      - assessment_delta: 最新 vs 初始评估分数差 (None if < 2 assessments)
      - trajectory_score: 综合成长分 0-100 (用于分享者资质)
      - qualifies_for_sharer: 是否达到分享者行为轨迹门槛
    """
    uid = current_user.id
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    result: dict = {
        "period_days": days,
        "start_date": str(start_date),
        "end_date": str(end_date),
    }

    # ─── 1. 依从性 (micro_action_tasks) ─────────────────────────
    try:
        task_rows = db.execute(sa_text("""
            SELECT scheduled_date, status
            FROM micro_action_tasks
            WHERE user_id = :uid
              AND scheduled_date >= :start
              AND scheduled_date <= :end
            ORDER BY scheduled_date
        """), {"uid": uid, "start": str(start_date), "end": str(end_date)}).mappings().all()

        # 按日聚合
        day_stats: dict[str, dict] = defaultdict(lambda: {"total": 0, "done": 0})
        for r in task_rows:
            d = str(r["scheduled_date"])
            day_stats[d]["total"] += 1
            if r["status"] == "completed":
                day_stats[d]["done"] += 1

        # 计算依从率
        total_tasks = sum(v["total"] for v in day_stats.values())
        done_tasks = sum(v["done"] for v in day_stats.values())
        result["adherence_rate"] = round(done_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0
        result["total_tasks"] = total_tasks
        result["done_tasks"] = done_tasks

        # 按周汇总
        weekly: list[dict] = []
        week_start = start_date
        while week_start <= end_date:
            week_end = min(week_start + timedelta(days=6), end_date)
            w_total = w_done = 0
            d = week_start
            while d <= week_end:
                ds = str(d)
                w_total += day_stats[ds]["total"]
                w_done += day_stats[ds]["done"]
                d += timedelta(days=1)
            weekly.append({
                "week_start": str(week_start),
                "rate": round(w_done / w_total * 100, 1) if w_total > 0 else 0,
                "done": w_done,
                "total": w_total,
            })
            week_start += timedelta(days=7)
        result["adherence_weekly"] = weekly

        # 连续打卡 streak（有任意完成任务的天）
        done_days = sorted({
            str(r["scheduled_date"]) for r in task_rows if r["status"] == "completed"
        })
        current_streak = 0
        max_streak = 0
        temp = 0
        prev: date | None = None
        for ds in done_days:
            d = date.fromisoformat(ds)
            if prev is None or (d - prev).days == 1:
                temp += 1
            else:
                max_streak = max(max_streak, temp)
                temp = 1
            prev = d
        max_streak = max(max_streak, temp)
        # current streak: count back from today
        cs = 0
        chk = end_date
        done_set = set(done_days)
        while str(chk) in done_set:
            cs += 1
            chk -= timedelta(days=1)
        result["current_streak"] = cs
        result["max_streak"] = max_streak

        # 恢复速度: gap ≥2天后，几天内恢复到1次完成
        gaps: list[int] = []
        if len(done_days) >= 2:
            for i in range(1, len(done_days)):
                d0 = date.fromisoformat(done_days[i - 1])
                d1 = date.fromisoformat(done_days[i])
                gap = (d1 - d0).days
                if gap >= 2:
                    gaps.append(gap - 1)  # recovery days = gap-1
        result["recovery_speed"] = round(sum(gaps) / len(gaps), 1) if gaps else None
        result["interruptions"] = len(gaps)

    except Exception as e:
        logger.warning(f"[Trajectory] adherence error: {e}")
        result.update({
            "adherence_rate": 0, "adherence_weekly": [],
            "current_streak": 0, "max_streak": 0,
            "recovery_speed": None, "interruptions": 0,
        })

    # ─── 2. 学习时长 (learning_time_logs) ────────────────────────
    try:
        learn_rows = db.execute(sa_text("""
            SELECT EXTRACT(WEEK FROM earned_at) AS week_num,
                   DATE_TRUNC('week', earned_at)::date AS week_start,
                   SUM(minutes) AS minutes
            FROM learning_time_logs
            WHERE user_id = :uid
              AND earned_at >= :start
            GROUP BY week_num, DATE_TRUNC('week', earned_at)
            ORDER BY week_start
        """), {"uid": uid, "start": datetime.combine(start_date, datetime.min.time())}).mappings().all()

        total_minutes = db.execute(sa_text("""
            SELECT COALESCE(SUM(minutes), 0) FROM learning_time_logs
            WHERE user_id = :uid AND earned_at >= :start
        """), {"uid": uid, "start": datetime.combine(start_date, datetime.min.time())}).scalar() or 0

        result["learning_hours"] = round(total_minutes / 60, 1)
        result["learning_minutes_weekly"] = [
            {"week_start": str(r["week_start"]), "minutes": int(r["minutes"] or 0)}
            for r in learn_rows
        ]
    except Exception as e:
        logger.warning(f"[Trajectory] learning error: {e}")
        result.update({"learning_hours": 0, "learning_minutes_weekly": []})

    # ─── 3. 评估能力提升 (assessment_assignments) ────────────────
    try:
        assess_rows = db.execute(sa_text("""
            SELECT pipeline_result, submitted_at
            FROM assessment_assignments
            WHERE user_id = :uid
              AND status IN ('completed', 'reviewed')
              AND pipeline_result IS NOT NULL
            ORDER BY submitted_at ASC
        """), {"uid": uid}).mappings().all()

        def _extract_score(row: Any) -> float | None:
            pr = row.get("pipeline_result") or {}
            if isinstance(pr, str):
                import json
                try:
                    pr = json.loads(pr)
                except Exception:
                    return None
            # try various score fields
            for key in ("total_score", "overall_score", "composite_score", "score"):
                if key in pr:
                    try:
                        return float(pr[key])
                    except Exception:
                        pass
            return None

        scores = [(r, _extract_score(r)) for r in assess_rows]
        scores = [(r, s) for r, s in scores if s is not None]

        if len(scores) >= 2:
            first_score = scores[0][1]
            latest_score = scores[-1][1]
            delta = round(latest_score - first_score, 2)
            result["assessment_delta"] = delta
            result["assessment_count"] = len(scores)
            result["assessment_first"] = first_score
            result["assessment_latest"] = latest_score
        else:
            result["assessment_delta"] = None
            result["assessment_count"] = len(scores)
    except Exception as e:
        logger.warning(f"[Trajectory] assessment error: {e}")
        result.update({"assessment_delta": None, "assessment_count": 0})

    # ─── 4. 综合成长分 & 分享者资质 ──────────────────────────────
    score = 0.0
    # 依从性: 最高 40分
    adh = result.get("adherence_rate", 0) or 0
    score += min(adh / 100 * 40, 40)
    # 学习时长: 最高 20分 (20h为满分)
    lh = result.get("learning_hours", 0) or 0
    score += min(lh / 20 * 20, 20)
    # 连续打卡: 最高 20分 (30天为满分)
    cs = result.get("current_streak", 0) or 0
    score += min(cs / 30 * 20, 20)
    # 弹性恢复(恢复天数越少越好): 最高 20分
    rv = result.get("recovery_speed")
    if rv is None:
        # 无中断 = 满分
        score += 20
    else:
        # 1天恢复=20分, 7天=0分
        score += max(0, 20 - rv / 7 * 20)

    trajectory_score = round(min(score, 100), 1)
    result["trajectory_score"] = trajectory_score
    result["qualifies_for_sharer"] = (
        trajectory_score >= 60 and
        adh >= 50 and
        result.get("current_streak", 0) >= 3
    )

    return result

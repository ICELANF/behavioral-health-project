"""
统一首页API — 根据角色自动返回核心数据
Unified Home API — auto-routes by user role

每个角色返回 2-4 个最基础数据块，复用飞轮API的SQL逻辑。
"""

import logging
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db as get_db
from api.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["home"])


# ──────────────────────────────────────────────
# Observer (role_level=1): 配额 + 评估进度
# ──────────────────────────────────────────────
async def _observer_home(user_id: int, db: AsyncSession) -> dict:
    quota = {}
    try:
        today_start = datetime.combine(date.today(), datetime.min.time())
        tomorrow_start = today_start + timedelta(days=1)
        result = await db.execute(text("""
            SELECT quota_type, COUNT(*) as cnt
            FROM observer_quota_logs
            WHERE user_id = :uid
              AND created_at >= :today_start
              AND created_at < :tomorrow_start
            GROUP BY quota_type
        """), {"uid": user_id, "today_start": today_start, "tomorrow_start": tomorrow_start})
        rows = result.mappings().all()
        used = {r["quota_type"]: r["cnt"] for r in rows}
        chat_used = used.get("chat", 0)
        food_used = used.get("food_scan", 0)
        voice_used = used.get("voice", 0)
        quota = {
            "chat_remaining": max(3 - chat_used, 0),
            "food_scan_remaining": max(3 - food_used, 0),
            "voice_remaining": max(3 - voice_used, 0),
            "total_remaining": max(9 - chat_used - food_used - voice_used, 0),
        }
    except Exception as e:
        logger.warning(f"[home] observer quota error: {e}")
        quota = {"chat_remaining": 3, "food_scan_remaining": 3, "voice_remaining": 3, "total_remaining": 9}

    assessment = {}
    try:
        result = await db.execute(text("""
            SELECT DISTINCT module_type
            FROM assessment_sessions
            WHERE user_id = :uid AND status = 'completed'
        """), {"uid": user_id})
        completed = {r["module_type"] for r in result.mappings().all()}
        has_pending = len(completed) < 5
        next_step = "完成BAPS基线评估" if not completed else "继续完成评估模块"
        assessment = {
            "has_pending": has_pending,
            "completed_count": len(completed),
            "next_step": next_step,
        }
    except Exception as e:
        logger.warning(f"[home] observer assessment error: {e}")
        assessment = {"has_pending": True, "completed_count": 0, "next_step": "完成BAPS基线评估"}

    return {"quota": quota, "assessment": assessment}


# ──────────────────────────────────────────────
# Grower (role_level=2): 今日任务 + 教练提示
# ──────────────────────────────────────────────
async def _grower_home(user_id: int, db: AsyncSession) -> dict:
    today_data = {}
    try:
        today_str = date.today().isoformat()
        result = await db.execute(text("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN done THEN 1 ELSE 0 END) as done_count
            FROM daily_tasks
            WHERE user_id = :uid AND task_date = :today
        """), {"uid": user_id, "today": today_str})
        row = result.mappings().first()
        total = row["total"] if row else 0
        done = row["done_count"] if row else 0
        done = done or 0

        # streak
        streak_days = 0
        sr = await db.execute(text("""
            SELECT current_streak FROM user_streaks WHERE user_id = :uid
        """), {"uid": user_id})
        streak_row = sr.mappings().first()
        if streak_row:
            streak_days = streak_row["current_streak"] or 0

        today_data = {
            "done_count": int(done),
            "total_count": int(total),
            "completion_pct": round(int(done) * 100 / max(int(total), 1)),
            "streak_days": int(streak_days),
        }
    except Exception as e:
        logger.warning(f"[home] grower today error: {e}")
        today_data = {"done_count": 0, "total_count": 0, "completion_pct": 0, "streak_days": 0}

    coach_tip = {}
    try:
        result = await db.execute(text("""
            SELECT push_content, push_type
            FROM coach_review_queue
            WHERE student_id = :uid AND status = 'approved'
            ORDER BY reviewed_at DESC NULLS LAST
            LIMIT 1
        """), {"uid": user_id})
        row = result.mappings().first()
        if row and row["push_content"]:
            coach_tip = {"tip": row["push_content"], "tip_type": row["push_type"] or "encouragement", "review_status": "approved"}
        else:
            coach_tip = {"tip": "坚持每日打卡，养成健康习惯", "tip_type": "encouragement", "review_status": "auto"}
    except Exception as e:
        logger.warning(f"[home] grower coach_tip error: {e}")
        coach_tip = {"tip": "坚持每日打卡，养成健康习惯", "tip_type": "encouragement", "review_status": "auto"}

    return {"today": today_data, "coach_tip": coach_tip}


# ──────────────────────────────────────────────
# Sharer (role_level=3): 同道者 + 贡献 + 影响力
# ──────────────────────────────────────────────
async def _sharer_home(user_id: int, db: AsyncSession) -> dict:
    mentees = {}
    try:
        result = await db.execute(text("""
            SELECT COUNT(*) as total,
                   COUNT(*) FILTER (WHERE status = 'active') as active_cnt
            FROM companion_relations
            WHERE mentor_id = :uid
        """), {"uid": user_id})
        row = result.mappings().first()
        filled = row["total"] if row else 0
        active = row["active_cnt"] if row else 0
        mentees = {"filled": int(filled), "total_slots": 4, "active_count": int(active)}
    except Exception as e:
        logger.warning(f"[home] sharer mentees error: {e}")
        mentees = {"filled": 0, "total_slots": 4, "active_count": 0}

    contribution = {}
    try:
        result = await db.execute(text("""
            SELECT COUNT(*) as submitted,
                   COUNT(*) FILTER (WHERE review_status = 'approved') as published
            FROM knowledge_documents
            WHERE contributor_id = :uid
        """), {"uid": user_id})
        row = result.mappings().first()
        submitted = row["submitted"] if row else 0
        published = row["published"] if row else 0
        contribution = {"submitted": int(submitted), "published": int(published)}
    except Exception as e:
        logger.warning(f"[home] sharer contribution error: {e}")
        contribution = {"submitted": 0, "published": 0}

    influence = {}
    try:
        result = await db.execute(text("""
            SELECT COALESCE(SUM(like_count), 0) AS likes,
                   COALESCE(SUM(collect_count), 0) AS saves
            FROM content_items
            WHERE author_id = :uid
        """), {"uid": user_id})
        row = result.mappings().first()
        total_influence = (row["likes"] if row else 0) + (row["saves"] if row else 0)
        influence = {"total": int(total_influence)}
    except Exception as e:
        logger.warning(f"[home] sharer influence error: {e}")
        influence = {"total": 0}

    return {"mentees": mentees, "contribution": contribution, "influence": influence}


# ──────────────────────────────────────────────
# Coach (role_level=4): 审核队列 + 今日统计 + 学员数
# ──────────────────────────────────────────────
async def _coach_home(user_id: int, db: AsyncSession) -> dict:
    review_queue = {}
    try:
        result = await db.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COUNT(*) FILTER (WHERE status = 'pending' AND priority = 'urgent') as urgent
            FROM coach_review_queue
            WHERE coach_id = :cid
        """), {"cid": user_id})
        row = result.mappings().first()
        review_queue = {
            "total_pending": int(row["pending"]) if row else 0,
            "urgent_count": int(row["urgent"]) if row else 0,
        }
    except Exception as e:
        logger.warning(f"[home] coach review_queue error: {e}")
        review_queue = {"total_pending": 0, "urgent_count": 0}

    stats_today = {}
    try:
        today_start = datetime.combine(date.today(), datetime.min.time())
        result = await db.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE reviewed_at >= :today_start) as total_reviewed,
                COUNT(*) FILTER (WHERE status = 'approved' AND reviewed_at >= :today_start) as approved,
                COUNT(*) FILTER (WHERE status = 'rejected' AND reviewed_at >= :today_start) as rejected,
                COALESCE(AVG(elapsed_seconds) FILTER (WHERE reviewed_at >= :today_start), 0) as avg_seconds
            FROM coach_review_queue
            WHERE coach_id = :cid
        """), {"cid": user_id, "today_start": today_start})
        row = result.mappings().first()
        avg_min = round(float(row["avg_seconds"] or 0) / 60, 1) if row else 0
        stats_today = {
            "total_reviewed": int(row["total_reviewed"]) if row else 0,
            "approved": int(row["approved"]) if row else 0,
            "rejected": int(row["rejected"]) if row else 0,
            "avg_response_min": avg_min,
        }
    except Exception as e:
        logger.warning(f"[home] coach stats_today error: {e}")
        stats_today = {"total_reviewed": 0, "approved": 0, "rejected": 0, "avg_response_min": 0}

    student_count = 0
    try:
        result = await db.execute(text("""
            SELECT COUNT(DISTINCT student_id) as cnt
            FROM coach_review_queue
            WHERE coach_id = :cid
        """), {"cid": user_id})
        row = result.mappings().first()
        student_count = int(row["cnt"]) if row else 0
    except Exception as e:
        logger.warning(f"[home] coach student_count error: {e}")

    return {"review_queue": review_queue, "stats_today": stats_today, "student_count": student_count}


# ──────────────────────────────────────────────
# Expert/Promoter/Supervisor (role_level=5): 审计队列 + 质量指标
# ──────────────────────────────────────────────
async def _expert_home(user_id: int, db: AsyncSession) -> dict:
    audit_queue = {}
    try:
        result = await db.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE verdict IS NULL) as pending_count,
                COUNT(*) FILTER (WHERE verdict IS NULL AND risk_level IN ('high', 'critical')) as anomaly_count
            FROM expert_audit_records
        """))
        row = result.mappings().first()
        audit_queue = {
            "pending_count": int(row["pending_count"]) if row else 0,
            "anomaly_count": int(row["anomaly_count"]) if row else 0,
        }
    except Exception as e:
        logger.warning(f"[home] expert audit_queue error: {e}")
        audit_queue = {"pending_count": 0, "anomaly_count": 0}

    quality = {}
    try:
        today_start = datetime.combine(date.today(), datetime.min.time())
        result = await db.execute(text("""
            SELECT
                CASE WHEN COUNT(*) FILTER (WHERE reviewed_at >= :today_start) > 0
                    THEN ROUND(
                        COUNT(*) FILTER (WHERE verdict = 'pass' AND reviewed_at >= :today_start)::numeric /
                        COUNT(*) FILTER (WHERE reviewed_at >= :today_start), 2)
                    ELSE 0.0
                END as approval_rate,
                COALESCE(AVG(
                    EXTRACT(EPOCH FROM (reviewed_at - created_at)) / 60
                ) FILTER (WHERE reviewed_at >= :today_start), 0) as avg_review_min
            FROM expert_audit_records
        """), {"today_start": today_start})
        row = result.mappings().first()
        quality = {
            "approval_rate": float(row["approval_rate"]) if row else 0,
            "avg_review_min": round(float(row["avg_review_min"] or 0), 1) if row else 0,
        }
    except Exception as e:
        logger.warning(f"[home] expert quality error: {e}")
        quality = {"approval_rate": 0, "avg_review_min": 0}

    return {"audit_queue": audit_queue, "quality": quality}


# ──────────────────────────────────────────────
# Admin / Master (role_level=99/6): KPI + 安全
# ──────────────────────────────────────────────
async def _admin_home(user_id: int, db: AsyncSession) -> dict:
    kpi = {}
    try:
        today_start = datetime.combine(date.today(), datetime.min.time())
        # total users
        r1 = await db.execute(text("SELECT COUNT(*) as cnt FROM users WHERE is_active = true"))
        total_users = int(r1.scalar() or 0)

        # DAU
        r2 = await db.execute(text("""
            SELECT COUNT(DISTINCT cs.user_id) as cnt
            FROM chat_messages cm
            JOIN chat_sessions cs ON cs.id = cm.session_id
            WHERE cm.created_at >= :today_start
        """), {"today_start": today_start})
        dau = int(r2.scalar() or 0)

        # active coaches
        r3 = await db.execute(text("""
            SELECT COUNT(*) as cnt FROM users
            WHERE role::text IN ('COACH', 'PROMOTER', 'SUPERVISOR', 'MASTER') AND is_active = true
        """))
        active_coaches = int(r3.scalar() or 0)

        # pending reviews
        r4 = await db.execute(text("""
            SELECT COUNT(*) as cnt FROM coach_review_queue WHERE status = 'pending'
        """))
        pending_reviews = int(r4.scalar() or 0)

        kpi = {
            "total_users": total_users,
            "dau": dau,
            "active_coaches": active_coaches,
            "pending_reviews": pending_reviews,
        }
    except Exception as e:
        logger.warning(f"[home] admin kpi error: {e}")
        kpi = {"total_users": 0, "dau": 0, "active_coaches": 0, "pending_reviews": 0}

    safety = {}
    try:
        result = await db.execute(text("""
            SELECT
                COUNT(*) FILTER (WHERE severity = 'critical') as critical_count,
                COUNT(*) FILTER (WHERE severity IN ('high', 'warning')) as warning_count
            FROM safety_logs
            WHERE created_at >= NOW() - INTERVAL '24 hours'
        """))
        row = result.mappings().first()
        safety = {
            "critical_count": int(row["critical_count"]) if row else 0,
            "warning_count": int(row["warning_count"]) if row else 0,
        }
    except Exception as e:
        logger.warning(f"[home] admin safety error: {e}")
        safety = {"critical_count": 0, "warning_count": 0}

    return {"kpi": kpi, "safety": safety}


# ──────────────────────────────────────────────
# 角色路由映射
# ──────────────────────────────────────────────
_ROLE_HOME_MAP = {
    "OBSERVER": _observer_home,
    "GROWER": _grower_home,
    "SHARER": _sharer_home,
    "COACH": _coach_home,
    "PROMOTER": _expert_home,
    "SUPERVISOR": _expert_home,
    "MASTER": _admin_home,
    "ADMIN": _admin_home,
}


@router.get("/home")
async def get_home(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    统一首页入口 — 根据当前用户角色自动返回对应的首页数据。

    - Observer: 配额 + 评估进度
    - Grower: 今日任务 + 教练提示
    - Sharer: 同道者 + 贡献 + 影响力
    - Coach: 审核队列 + 今日统计 + 学员数
    - Expert/Promoter/Supervisor: 审计队列 + 质量指标
    - Admin/Master: KPI + 安全
    """
    role_text = str(current_user.role).split(".")[-1].upper()
    handler = _ROLE_HOME_MAP.get(role_text, _observer_home)
    data = await handler(current_user.id, db)
    return {"role": role_text.lower(), **data}

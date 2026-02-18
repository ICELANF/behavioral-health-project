"""
R2 (最终版): scheduler_agent — 处方→每日任务 (平台心脏)

已合并 PATCH-2: 不注册独立 APScheduler job, 融入已有 daily_task_generation

部署:
  1. 复制到 api/ 目录
  2. 在已有的 micro_action_service.generate_daily_tasks() 末尾追加:
       from r2_scheduler_agent import run_daily_task_generation
       await run_daily_task_generation(db)
  3. 手动触发API自动注册 (需在main.py include scheduler_router)
"""

import logging
import re
from datetime import date, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("scheduler_agent")

# ═══════════════════════════════════════════════════
# 常量 & 映射
# ═══════════════════════════════════════════════════

TAG_MAP = {
    "nutrition": "营养", "glucose": "监测", "blood_sugar": "监测",
    "blood_pressure": "监测", "exercise": "运动", "sleep": "睡眠",
    "emotion": "情绪", "stress": "情绪", "learning": "学习",
    "tcm": "运动", "medication": "监测",
}

TAG_COLORS = {
    "营养": "#f59e0b", "监测": "#3b82f6", "运动": "#10b981",
    "睡眠": "#8b5cf6", "情绪": "#ec4899", "学习": "#6366f1",
}

FREQ_MAP = {
    "每日1次": 1, "每日2次": 2, "每日3次": 3,
    "每天1次": 1, "每天2次": 2, "每天3次": 3,
    "1次/日": 1, "2次/日": 2, "3次/日": 3,
    "daily": 1, "bid": 2, "tid": 3,
}

DOMAIN_AGENT_MAP = {
    "nutrition": "nutrition_guide", "glucose": "health_assistant",
    "blood_sugar": "health_assistant", "blood_pressure": "health_assistant",
    "exercise": "exercise_guide", "sleep": "sleep_guide",
    "emotion": "emotion_support", "stress": "emotion_support",
    "tcm": "tcm_exercise_guide", "medication": "health_assistant",
    "learning": "content_recommender",
}


# ═══════════════════════════════════════════════════
# 核心: 为单个用户生成每日任务
# ═══════════════════════════════════════════════════

async def generate_daily_tasks_for_user(
    db: AsyncSession, user_id: int, target_date: date = None,
) -> list[dict]:
    """
    为指定用户生成指定日期的每日任务。
    数据流: behavior_prescriptions(active) → 解析 → daily_tasks
    """
    if target_date is None:
        target_date = date.today()

    tasks = []
    order_counter = 0

    # ── Step 1: 查询活跃处方 ──
    rx_stmt = text("""
        SELECT id, user_id, target_behavior, frequency_dose, time_place,
               trigger_cue, obstacle_plan, domain, difficulty_level,
               cultivation_stage, created_at
        FROM behavior_prescriptions
        WHERE user_id = :user_id AND status = 'active'
          AND (expires_at IS NULL OR expires_at > :today)
        ORDER BY created_at
    """)
    rx_result = await db.execute(rx_stmt, {"user_id": user_id, "today": target_date})
    prescriptions = rx_result.mappings().all()

    for rx in prescriptions:
        freq_text = (rx.get("frequency_dose") or "每日1次").strip()
        num_tasks = FREQ_MAP.get(freq_text, 1)

        domain = (rx.get("domain") or "nutrition").lower()
        tag = TAG_MAP.get(domain, "学习")
        tag_color = TAG_COLORS.get(tag, "#6366f1")
        agent_id = DOMAIN_AGENT_MAP.get(domain, "behavior_coach")
        time_hints = _parse_time_hints(rx.get("time_place") or "", num_tasks)
        input_mode = _infer_input_mode(domain, rx.get("target_behavior", ""))

        for i in range(num_tasks):
            order_counter += 1
            task_id = f"dt_{target_date.strftime('%Y%m%d')}_{user_id}_{order_counter:03d}"
            tasks.append({
                "id": task_id, "user_id": user_id, "task_date": target_date,
                "order_num": order_counter,
                "title": _build_task_title(rx, i, num_tasks),
                "tag": tag, "tag_color": tag_color,
                "time_hint": time_hints[i] if i < len(time_hints) else "",
                "input_mode": input_mode,
                "quick_label": _infer_quick_label(input_mode),
                "source": "rx", "agent_id": agent_id,
                "rx_id": rx.get("id"), "done": False, "done_time": None,
            })

    # ── Step 2: 查询活跃监测方案 ──
    try:
        mon_stmt = text("""
            SELECT id, plan_type, time_points, device_type
            FROM monitoring_plans
            WHERE user_id = :user_id AND status = 'active'
              AND (end_date IS NULL OR end_date > :today)
            ORDER BY created_at
        """)
        mon_result = await db.execute(mon_stmt, {"user_id": user_id, "today": target_date})
        for mon in mon_result.mappings().all():
            plan_type = (mon.get("plan_type") or "blood_sugar").lower()
            device_type = mon.get("device_type") or "manual"
            for tp in (mon.get("time_points") or "空腹").split(","):
                tp = tp.strip()
                if not tp:
                    continue
                order_counter += 1
                tag = TAG_MAP.get(plan_type, "监测")
                tasks.append({
                    "id": f"dt_{target_date.strftime('%Y%m%d')}_{user_id}_{order_counter:03d}",
                    "user_id": user_id, "task_date": target_date,
                    "order_num": order_counter,
                    "title": f"{_plan_type_cn(plan_type)}测量 ({tp})",
                    "tag": tag, "tag_color": TAG_COLORS.get(tag, "#3b82f6"),
                    "time_hint": tp,
                    "input_mode": "device" if device_type != "manual" else "text",
                    "quick_label": "记录", "source": "system",
                    "agent_id": DOMAIN_AGENT_MAP.get(plan_type, "health_assistant"),
                    "rx_id": None, "done": False, "done_time": None,
                })
    except Exception:
        pass  # monitoring_plans 表可能不存在

    # ── Step 3: 排序并写入 ──
    tasks.sort(key=lambda t: _time_sort_key(t.get("time_hint", "")))
    for i, t in enumerate(tasks, 1):
        t["order_num"] = i

    if tasks:
        await db.execute(
            text("DELETE FROM daily_tasks WHERE user_id = :uid AND task_date = :td"),
            {"uid": user_id, "td": target_date}
        )
        for t in tasks:
            await db.execute(text("""
                INSERT INTO daily_tasks
                    (id, user_id, task_date, order_num, title, tag, tag_color,
                     time_hint, input_mode, quick_label, source, agent_id,
                     done, done_time, created_at)
                VALUES
                    (:id, :user_id, :task_date, :order_num, :title, :tag, :tag_color,
                     :time_hint, :input_mode, :quick_label, :source, :agent_id,
                     :done, :done_time, NOW())
            """), t)
        await db.commit()

    logger.info(f"用户 {user_id}: 生成 {len(tasks)} 个每日任务 ({target_date})")
    return tasks


# ═══════════════════════════════════════════════════
# 批量执行
# ═══════════════════════════════════════════════════

async def run_daily_task_generation(db: AsyncSession):
    """
    批量为所有活跃Grower生成任务。

    ⚠️ PATCH-2: 本函数不直接由 APScheduler 调用,
    而是由已有的 micro_action_service.generate_daily_tasks() 在末尾调用:

        from r2_scheduler_agent import run_daily_task_generation
        await run_daily_task_generation(db)
    """
    try:
        stmt = text("""
            SELECT DISTINCT bp.user_id
            FROM behavior_prescriptions bp
            JOIN users u ON u.id = bp.user_id
            WHERE bp.status = 'active'
              AND (bp.expires_at IS NULL OR bp.expires_at > CURRENT_DATE)
              AND u.role_level >= 2
        """)
        result = await db.execute(stmt)
        user_ids = [row[0] for row in result.fetchall()]
    except Exception as e:
        logger.warning(f"查询活跃处方用户失败: {e}")
        try:
            stmt2 = text("SELECT DISTINCT user_id FROM behavior_prescriptions WHERE status = 'active'")
            result = await db.execute(stmt2)
            user_ids = [row[0] for row in result.fetchall()]
        except Exception:
            return {"success": 0, "errors": 0, "total": 0}

    today = date.today()
    success, errors = 0, 0
    for uid in user_ids:
        try:
            await generate_daily_tasks_for_user(db, uid, today)
            success += 1
        except Exception as e:
            logger.error(f"用户 {uid} 任务生成失败: {e}")
            errors += 1

    logger.info(f"每日任务生成完成: {success} 成功, {errors} 失败, 共 {len(user_ids)} 用户")
    return {"success": success, "errors": errors, "total": len(user_ids)}


# ═══════════════════════════════════════════════════
# 手动触发 API (管理员专用)
# ═══════════════════════════════════════════════════

from fastapi import APIRouter, Depends, Path as FastPath
from pydantic import BaseModel

from core.database import get_async_db as get_db
from api.dependencies import require_admin

scheduler_router = APIRouter(prefix="/api/v1/admin", tags=["scheduler-agent"])


class TaskGenResult(BaseModel):
    success: int
    errors: int
    total: int


class UserTaskGenResult(BaseModel):
    user_id: int
    task_count: int
    date: str


@scheduler_router.post("/generate-daily-tasks", response_model=TaskGenResult)
async def trigger_daily_task_generation(
    admin_user=Depends(require_admin),
    db=Depends(get_db),
):
    """手动触发全量每日任务生成 (管理员专用)"""
    result = await run_daily_task_generation(db)
    return TaskGenResult(**result)


@scheduler_router.post("/generate-daily-tasks/{user_id}", response_model=UserTaskGenResult)
async def trigger_user_task_generation(
    user_id: int,
    admin_user=Depends(require_admin),
    db=Depends(get_db),
):
    """为指定用户手动生成今日任务 (管理员专用)"""
    today = date.today()
    tasks = await generate_daily_tasks_for_user(db, user_id, today)
    return UserTaskGenResult(user_id=user_id, task_count=len(tasks), date=today.isoformat())


# ═══════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════

def _parse_time_hints(time_place: str, num_tasks: int) -> list[str]:
    if not time_place:
        return {1: ["全天"], 2: ["上午", "下午"], 3: ["早", "中", "晚"]}.get(num_tasks, ["全天"])
    for sep in ["、", ",", ";", "/"]:
        if sep in time_place:
            parts = [p.strip() for p in time_place.split(sep) if p.strip()]
            return (parts[:num_tasks] if len(parts) >= num_tasks
                    else parts + [""] * (num_tasks - len(parts)))
    return [time_place] * num_tasks


def _build_task_title(rx: dict, index: int, total: int) -> str:
    base = rx.get("target_behavior", "健康行为")
    if total <= 1:
        return base
    ordinals = {0: "早", 1: "午", 2: "晚"}
    if total <= 3 and index in ordinals:
        return f"{base} ({ordinals[index]})"
    return f"{base} (第{index + 1}次)"


def _infer_input_mode(domain: str, target_behavior: str) -> str:
    if domain in ("nutrition",) or any(k in target_behavior for k in ("饮食", "餐")):
        return "photo"
    if domain in ("exercise", "tcm") or any(k in target_behavior for k in ("运动", "锻炼")):
        return "voice"
    if domain in ("glucose", "blood_sugar", "blood_pressure", "medication"):
        return "device"
    return "text"


def _infer_quick_label(input_mode: str) -> str:
    return {"photo": "拍照", "voice": "开始", "device": "记录", "text": "打卡"}.get(input_mode, "打卡")


def _plan_type_cn(plan_type: str) -> str:
    return {"blood_sugar": "血糖", "blood_pressure": "血压", "weight": "体重",
            "heart_rate": "心率", "sleep": "睡眠"}.get(plan_type, plan_type)


def _time_sort_key(time_hint: str) -> int:
    order = {"空腹": 0, "晨起": 1, "早": 2, "上午": 3, "餐前": 4,
             "午": 5, "中": 5, "下午": 6, "餐后": 7, "晚": 8, "睡前": 9, "全天": 5}
    for key, val in order.items():
        if key in time_hint:
            return val
    try:
        return int(time_hint.split(":")[0])
    except (ValueError, IndexError):
        return 5

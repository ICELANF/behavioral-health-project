"""
R5: Observer 飞轮 API — 真实DB版 (替换 observer_flywheel_api.py)

去Mock的2个核心端点:
  GET  /api/v1/observer/quota/today     → 查询 observer_quota_logs 表
  POST /api/v1/observer/quota/consume   → 写入 observer_quota_logs

评估进度端点也接真实DB:
  GET  /api/v1/assessment/progress      → 查询 assessment_sessions 表

部署: 替换 api/observer_flywheel_api.py
"""

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db as get_db
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1", tags=["observer-flywheel"])

# ═══════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════
OBSERVER_DAILY_LIMITS = {
    "chat": 3,
    "food_scan": 3,
    "voice": 3,
}
TOTAL_LIMIT = sum(OBSERVER_DAILY_LIMITS.values())


# ═══════════════════════════════════════════════════
# Schema
# ═══════════════════════════════════════════════════

class QuotaTodayResponse(BaseModel):
    chat_used: int = 0
    chat_limit: int = 3
    chat_remaining: int = 3
    food_scan_used: int = 0
    food_scan_limit: int = 3
    food_scan_remaining: int = 3
    voice_used: int = 0
    voice_limit: int = 3
    voice_remaining: int = 3
    total_used: int = 0
    total_limit: int = 9
    total_remaining: int = 9
    date: str


class ConsumeRequest(BaseModel):
    quota_type: str  # chat | food_scan | voice


class ConsumeResponse(BaseModel):
    success: bool
    quota_type: str
    remaining: int
    message: str = ""
    upgrade_prompt: bool = False


class AssessmentProgressResponse(BaseModel):
    started: bool = False
    completed: bool = False
    progress_pct: int = 0
    current_module: Optional[str] = None
    modules_done: list[str] = []
    modules_total: int = 5
    estimated_minutes_left: int = 0
    can_upgrade: bool = False


# ═══════════════════════════════════════════════════
# GET /observer/quota/today — 真实DB查询
# ═══════════════════════════════════════════════════

@router.get("/observer/quota/today", response_model=QuotaTodayResponse)
async def get_observer_quota_today(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    查询今日剩余额度 — 从 observer_quota_logs 表聚合
    """
    user_id = current_user.id
    today = date.today()

    # 按类型统计今日使用量
    stmt = text("""
        SELECT quota_type, COUNT(*) as cnt
        FROM observer_quota_logs
        WHERE user_id = :uid
          AND created_at >= :today_start
          AND created_at < :tomorrow_start
        GROUP BY quota_type
    """)
    result = await db.execute(stmt, {
        "uid": user_id,
        "today_start": datetime.combine(today, datetime.min.time()),
        "tomorrow_start": datetime.combine(today, datetime.min.time()) + __import__('datetime').timedelta(days=1),
    })
    
    usage = {row[0]: row[1] for row in result.fetchall()}
    
    chat_used = usage.get("chat", 0)
    food_used = usage.get("food_scan", 0)
    voice_used = usage.get("voice", 0)
    total_used = chat_used + food_used + voice_used

    return QuotaTodayResponse(
        chat_used=chat_used,
        chat_limit=OBSERVER_DAILY_LIMITS["chat"],
        chat_remaining=max(0, OBSERVER_DAILY_LIMITS["chat"] - chat_used),
        food_scan_used=food_used,
        food_scan_limit=OBSERVER_DAILY_LIMITS["food_scan"],
        food_scan_remaining=max(0, OBSERVER_DAILY_LIMITS["food_scan"] - food_used),
        voice_used=voice_used,
        voice_limit=OBSERVER_DAILY_LIMITS["voice"],
        voice_remaining=max(0, OBSERVER_DAILY_LIMITS["voice"] - voice_used),
        total_used=total_used,
        total_limit=TOTAL_LIMIT,
        total_remaining=max(0, TOTAL_LIMIT - total_used),
        date=today.isoformat(),
    )


# ═══════════════════════════════════════════════════
# POST /observer/quota/consume — 真实DB写入
# ═══════════════════════════════════════════════════

@router.post("/observer/quota/consume", response_model=ConsumeResponse)
async def consume_observer_quota(
    body: ConsumeRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    消耗一次额度
    
    逻辑:
    1. 检查 quota_type 是否合法
    2. 查询今日该类型已用量
    3. 如果超限 → 返回升级提示
    4. 如果未超限 → 写入日志, 返回剩余量
    """
    user_id = current_user.id
    today = date.today()
    qt = body.quota_type

    if qt not in OBSERVER_DAILY_LIMITS:
        raise HTTPException(status_code=400, detail=f"无效的额度类型: {qt}")

    limit = OBSERVER_DAILY_LIMITS[qt]

    # 查询今日已用量
    stmt = text("""
        SELECT COUNT(*) FROM observer_quota_logs
        WHERE user_id = :uid AND quota_type = :qt
          AND created_at >= :today_start
          AND created_at < :tomorrow_start
    """)
    from datetime import timedelta
    result = await db.execute(stmt, {
        "uid": user_id, "qt": qt,
        "today_start": datetime.combine(today, datetime.min.time()),
        "tomorrow_start": datetime.combine(today, datetime.min.time()) + timedelta(days=1),
    })
    used = result.scalar() or 0

    if used >= limit:
        return ConsumeResponse(
            success=False,
            quota_type=qt,
            remaining=0,
            message=f"今日{_type_cn(qt)}体验次数已用完。完成健康评估即可解锁无限使用！",
            upgrade_prompt=True,
        )

    # 写入消耗日志
    await db.execute(text("""
        INSERT INTO observer_quota_logs (user_id, quota_type, created_at)
        VALUES (:uid, :qt, NOW())
    """), {"uid": user_id, "qt": qt})
    await db.commit()

    remaining = limit - used - 1

    # 最后一次额度时提醒
    if remaining == 0:
        msg = f"这是今日最后一次{_type_cn(qt)}体验。完成健康评估可解锁全部功能！"
        upgrade = True
    elif remaining == 1:
        msg = f"还剩{remaining}次{_type_cn(qt)}体验机会"
        upgrade = False
    else:
        msg = ""
        upgrade = False

    return ConsumeResponse(
        success=True,
        quota_type=qt,
        remaining=remaining,
        message=msg,
        upgrade_prompt=upgrade,
    )


# ═══════════════════════════════════════════════════
# GET /assessment/progress — 真实DB查询
# ═══════════════════════════════════════════════════

MODULE_ORDER = ["ttm7", "big5", "bpt6", "capacity", "spi"]
MODULE_MINUTES = {"ttm7": 8, "big5": 15, "bpt6": 6, "capacity": 10, "spi": 12}


@router.get("/assessment/progress", response_model=AssessmentProgressResponse)
async def get_assessment_progress(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    评估进度 — 查询已完成的评估模块
    """
    user_id = current_user.id

    # 查询已完成的模块
    modules_done = set()
    
    try:
        stmt = text("""
            SELECT DISTINCT module_type
            FROM assessment_sessions
            WHERE user_id = :uid AND status = 'completed'
        """)
        result = await db.execute(stmt, {"uid": user_id})
        for row in result.fetchall():
            modules_done.add(row[0].lower())
    except Exception:
        pass

    if not modules_done:
        try:
            stmt = text("""
                SELECT DISTINCT assessment_type
                FROM baps_results
                WHERE user_id = :uid AND completed = true
            """)
            result = await db.execute(stmt, {"uid": user_id})
            for row in result.fetchall():
                modules_done.add(row[0].lower())
        except Exception:
            pass

    done_list = sorted(modules_done & set(MODULE_ORDER))
    all_done = len(done_list) == len(MODULE_ORDER)

    # 找到当前模块
    current = None
    for m in MODULE_ORDER:
        if m not in modules_done:
            current = m
            break

    # 计算剩余时间
    remaining_minutes = sum(
        MODULE_MINUTES.get(m, 10)
        for m in MODULE_ORDER
        if m not in modules_done
    )

    progress = int(len(done_list) / len(MODULE_ORDER) * 100) if MODULE_ORDER else 0

    return AssessmentProgressResponse(
        started=len(done_list) > 0,
        completed=all_done,
        progress_pct=progress,
        current_module=current,
        modules_done=done_list,
        modules_total=len(MODULE_ORDER),
        estimated_minutes_left=remaining_minutes,
        can_upgrade=all_done,
    )


# ═══════════════════════════════════════════════════
# 辅助
# ═══════════════════════════════════════════════════

def _type_cn(qt: str) -> str:
    return {"chat": "对话", "food_scan": "食物识别", "voice": "语音"}.get(qt, qt)

"""
R6: Coach 飞轮 API — 真实DB版 (替换 coach_flywheel_api.py)

去Mock的3个核心端点:
  GET  /api/v1/coach/review-queue          → 查询 coach_review_queue 表
  POST /api/v1/coach/review/:id/approve    → 更新状态 + 激活处方 + 生成任务 + 通知
  POST /api/v1/coach/review/:id/reject     → 更新状态 + 退回原因

今日统计也接真实DB:
  GET  /api/v1/coach/stats/today           → 聚合 coach_review_queue

部署: 替换 api/coach_flywheel_api.py
"""

import logging
from datetime import date, datetime, timedelta
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db as get_db
from api.dependencies import get_current_user

logger = logging.getLogger("coach_flywheel")

router = APIRouter(prefix="/api/v1/coach", tags=["coach-flywheel"])


# ═══════════════════════════════════════════════════
# Schema
# ═══════════════════════════════════════════════════

class ReviewItem(BaseModel):
    id: str
    student_name: str
    student_id: int
    type: str                      # prescription | ai_reply | push
    priority: str = "normal"
    status: str = "pending"
    ai_summary: Optional[str] = None
    rx_fields: Optional[dict] = None
    ai_draft: Optional[str] = None
    push_type: Optional[str] = None
    push_content: Optional[str] = None
    created_at: str
    wait_seconds: int = 0


class ReviewQueueResponse(BaseModel):
    items: list[ReviewItem]
    total_pending: int
    urgent_count: int


class ApproveRequest(BaseModel):
    review_note: Optional[str] = None
    edited_content: Optional[str] = None
    edited_rx_json: Optional[dict] = None


class RejectRequest(BaseModel):
    reason: str
    review_note: Optional[str] = None


class ReviewActionResponse(BaseModel):
    success: bool
    review_id: str
    action: str           # approved | rejected
    message: str
    elapsed_seconds: int = 0


class CoachStatsToday(BaseModel):
    total_reviewed: int
    approved: int
    rejected: int
    pending: int
    avg_review_seconds: int
    streak_days: int = 0  # 教练连续工作天数


# ═══════════════════════════════════════════════════
# GET /review-queue — 真实DB查询
# ═══════════════════════════════════════════════════

@router.get("/review-queue", response_model=ReviewQueueResponse)
async def get_review_queue(
    status: str = Query("pending", pattern="^(pending|approved|rejected|all)$"),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取教练审核队列

    权限: coach(4) 及以上
    排序: urgent优先, 然后按创建时间
    """
    coach_id = current_user.id

    # 权限检查 (role字段: observer/grower/sharer/coach/promoter/supervisor/master/admin)
    _COACH_ROLES = {"coach", "promoter", "supervisor", "master", "admin"}
    try:
        role_stmt = text("SELECT role::text FROM users WHERE id = :uid")
        role_result = await db.execute(role_stmt, {"uid": coach_id})
        role_val = (role_result.scalar() or "").lower()
    except Exception as e:
        logger.warning(f"DB object missing ({e.__class__.__name__}), returning empty fallback")
        return ReviewQueueResponse(items=[], total_pending=0, urgent_count=0)
    if role_val not in _COACH_ROLES:
        raise HTTPException(status_code=403, detail="需要教练权限")

    # 构建查询
    where_clause = "coach_id = :cid"
    params = {"cid": coach_id, "lim": limit}
    
    if status != "all":
        where_clause += " AND status = :status"
        params["status"] = status

    try:
        stmt = text(f"""
            SELECT q.id, q.student_id, q.type, q.priority, q.status,
                   q.ai_summary, q.rx_fields_json, q.ai_draft,
                   q.push_type, q.push_content, q.created_at,
                   u.username as student_name
            FROM coach_review_queue q
            JOIN users u ON u.id = q.student_id
            WHERE {where_clause}
            ORDER BY
                CASE q.priority WHEN 'urgent' THEN 0 ELSE 1 END,
                q.created_at ASC
            LIMIT :lim
        """)

        result = await db.execute(stmt, params)
        rows = result.mappings().all()
    except Exception as e:
        logger.warning(f"DB object missing ({e.__class__.__name__}), returning empty fallback")
        return ReviewQueueResponse(items=[], total_pending=0, urgent_count=0)

    now = datetime.now()
    items = []
    for r in rows:
        created = r["created_at"]
        wait = int((now - created).total_seconds()) if created else 0

        items.append(ReviewItem(
            id=r["id"],
            student_name=r["student_name"] or f"学员{r['student_id']}",
            student_id=r["student_id"],
            type=r["type"],
            priority=r["priority"] or "normal",
            status=r["status"] or "pending",
            ai_summary=r["ai_summary"],
            rx_fields=r["rx_fields_json"],
            ai_draft=r["ai_draft"],
            push_type=r["push_type"],
            push_content=r["push_content"],
            created_at=created.isoformat() if created else "",
            wait_seconds=wait,
        ))

    # 统计
    try:
        count_stmt = text("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COUNT(*) FILTER (WHERE status = 'pending' AND priority = 'urgent') as urgent
            FROM coach_review_queue
            WHERE coach_id = :cid
        """)
        counts = (await db.execute(count_stmt, {"cid": coach_id})).mappings().first()
        total_pending = counts["pending"] or 0
        urgent_count = counts["urgent"] or 0
    except Exception as e:
        logger.warning(f"DB object missing ({e.__class__.__name__}), returning empty fallback")
        total_pending = 0
        urgent_count = 0

    return ReviewQueueResponse(
        items=items,
        total_pending=total_pending,
        urgent_count=urgent_count,
    )


# ═══════════════════════════════════════════════════
# POST /review/:id/approve — 审核通过 + 激活处方 + 生成任务
# ═══════════════════════════════════════════════════

@router.post("/review/{review_id}/approve", response_model=ReviewActionResponse)
async def approve_review(
    review_id: str = Path(...),
    body: ApproveRequest = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    审核通过
    
    关键数据流 (修复审计报告中的⑦号断裂):
    1. 更新 coach_review_queue 状态
    2. 如果是处方审核: 激活 behavior_prescriptions
    3. 触发每日任务重新生成
    4. 写入 coach_review_logs
    5. TODO Phase 2: 推送通知给用户
    """
    if body is None:
        body = ApproveRequest()

    coach_id = current_user.id
    now = datetime.now()

    # 查询审核项
    try:
        q_stmt = text("""
            SELECT id, student_id, type, status, rx_fields_json, created_at, picked_at
            FROM coach_review_queue
            WHERE id = :rid AND coach_id = :cid
        """)
        q_result = await db.execute(q_stmt, {"rid": review_id, "cid": coach_id})
        review = q_result.mappings().first()
    except Exception as e:
        logger.warning(f"DB object missing ({e.__class__.__name__}), returning empty fallback")
        raise HTTPException(status_code=404, detail="审核服务暂不可用")

    if not review:
        raise HTTPException(status_code=404, detail="审核项不存在或不属于当前教练")

    if review["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"审核项状态为 {review['status']}，无法操作")

    # 计算审核耗时
    picked = review["picked_at"] or review["created_at"]
    elapsed = int((now - picked).total_seconds()) if picked else 0

    # Step 1: 更新审核状态
    await db.execute(text("""
        UPDATE coach_review_queue
        SET status = 'approved', review_note = :note, 
            edited_content = :content, edited_rx_json = :rx,
            reviewed_at = :now, elapsed_seconds = :elapsed
        WHERE id = :rid
    """), {
        "rid": review_id, "note": body.review_note,
        "content": body.edited_content, "rx": str(body.edited_rx_json) if body.edited_rx_json else None,
        "now": now, "elapsed": elapsed,
    })

    # Step 2: 如果是处方审核 → 激活处方
    student_id = review["student_id"]
    if review["type"] == "prescription":
        rx_json = body.edited_rx_json or review["rx_fields_json"]
        if rx_json:
            await _activate_prescription(db, student_id, rx_json, review_id)

        # Step 3: 触发任务重新生成
        try:
            from api.r2_scheduler_agent import generate_daily_tasks_for_user
            await generate_daily_tasks_for_user(db, student_id, date.today())
        except Exception as e:
            logger.warning(f"审核通过后任务生成失败: {e}")

    # Step 4: 写入审核日志
    await db.execute(text("""
        INSERT INTO coach_review_logs (coach_id, review_id, action, note, created_at)
        VALUES (:cid, :rid, 'approved', :note, :now)
    """), {"cid": coach_id, "rid": review_id, "note": body.review_note, "now": now})

    await db.commit()

    logger.info(f"Coach {coach_id} approved review {review_id} for student {student_id} ({elapsed}s)")

    return ReviewActionResponse(
        success=True,
        review_id=review_id,
        action="approved",
        message="审核通过，处方已激活",
        elapsed_seconds=elapsed,
    )


# ═══════════════════════════════════════════════════
# POST /review/:id/reject — 审核退回
# ═══════════════════════════════════════════════════

@router.post("/review/{review_id}/reject", response_model=ReviewActionResponse)
async def reject_review(
    review_id: str = Path(...),
    body: RejectRequest = None,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """审核退回"""
    if body is None:
        body = RejectRequest(reason="需要修改")

    coach_id = current_user.id
    now = datetime.now()

    # 查询
    q_stmt = text("""
        SELECT id, student_id, status, created_at, picked_at
        FROM coach_review_queue
        WHERE id = :rid AND coach_id = :cid
    """)
    q_result = await db.execute(q_stmt, {"rid": review_id, "cid": coach_id})
    review = q_result.mappings().first()

    if not review:
        raise HTTPException(status_code=404, detail="审核项不存在")
    if review["status"] != "pending":
        raise HTTPException(status_code=409, detail="审核项已处理")

    picked = review["picked_at"] or review["created_at"]
    elapsed = int((now - picked).total_seconds()) if picked else 0

    # 更新状态
    await db.execute(text("""
        UPDATE coach_review_queue
        SET status = 'rejected', review_note = :note,
            reviewed_at = :now, elapsed_seconds = :elapsed
        WHERE id = :rid
    """), {"rid": review_id, "note": f"退回原因: {body.reason}. {body.review_note or ''}", "now": now, "elapsed": elapsed})

    # 写日志
    await db.execute(text("""
        INSERT INTO coach_review_logs (coach_id, review_id, action, note, created_at)
        VALUES (:cid, :rid, 'rejected', :note, :now)
    """), {"cid": coach_id, "rid": review_id, "note": body.reason, "now": now})

    await db.commit()

    return ReviewActionResponse(
        success=True,
        review_id=review_id,
        action="rejected",
        message=f"已退回: {body.reason}",
        elapsed_seconds=elapsed,
    )


# ═══════════════════════════════════════════════════
# GET /stats/today — 今日统计
# ═══════════════════════════════════════════════════

@router.get("/stats/today", response_model=CoachStatsToday)
async def get_coach_stats_today(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """教练今日工作统计"""
    _empty = CoachStatsToday(
        total_reviewed=0, approved=0, rejected=0, pending=0, avg_review_seconds=0,
    )
    try:
        coach_id = current_user.id
        today = date.today()

        stmt = text("""
            SELECT
                COUNT(*) FILTER (WHERE reviewed_at >= :today_start) as total_reviewed,
                COUNT(*) FILTER (WHERE status = 'approved' AND reviewed_at >= :today_start) as approved,
                COUNT(*) FILTER (WHERE status = 'rejected' AND reviewed_at >= :today_start) as rejected,
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COALESCE(AVG(elapsed_seconds) FILTER (WHERE reviewed_at >= :today_start), 0)::int as avg_seconds
            FROM coach_review_queue
            WHERE coach_id = :cid
        """)
        result = (await db.execute(stmt, {
            "cid": coach_id,
            "today_start": datetime.combine(today, datetime.min.time()),
        })).mappings().first()
    except Exception as e:
        logger.warning(f"DB object missing ({e.__class__.__name__}), returning empty fallback")
        return _empty

    return CoachStatsToday(
        total_reviewed=result["total_reviewed"] or 0,
        approved=result["approved"] or 0,
        rejected=result["rejected"] or 0,
        pending=result["pending"] or 0,
        avg_review_seconds=result["avg_seconds"] or 0,
    )


# ═══════════════════════════════════════════════════
# 内部辅助
# ═══════════════════════════════════════════════════

async def _activate_prescription(
    db: AsyncSession, user_id: int, rx_json: dict, review_id: str
):
    """
    激活处方 — 修复审计报告⑦号断裂点
    
    将审核通过的处方写入 behavior_prescriptions 并激活
    """
    import uuid
    rx_id = f"rx_{uuid.uuid4().hex[:12]}"

    await db.execute(text("""
        INSERT INTO behavior_prescriptions
            (id, user_id, target_behavior, frequency_dose, time_place,
             trigger_cue, obstacle_plan, support_resource,
             domain, difficulty_level, cultivation_stage,
             status, approved_by_review, created_at)
        VALUES
            (:id, :uid, :target, :freq, :time, :cue, :plan, :support,
             :domain, :diff, 'startup', 'active', :review_id, NOW())
    """), {
        "id": rx_id, "uid": user_id,
        "target": rx_json.get("target_behavior", "健康行为"),
        "freq": rx_json.get("frequency_dose", "每日1次"),
        "time": rx_json.get("time_place", ""),
        "cue": rx_json.get("trigger_cue", ""),
        "plan": rx_json.get("obstacle_plan", ""),
        "support": rx_json.get("support_resource", ""),
        "domain": rx_json.get("domain", "nutrition"),
        "diff": rx_json.get("difficulty_level", "easy"),
        "review_id": review_id,
    })

    logger.info(f"处方 {rx_id} 已激活 (用户 {user_id}, 审核 {review_id})")

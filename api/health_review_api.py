# -*- coding: utf-8 -*-
"""
健康数据审核队列 API

流水线: 穿戴设备数据 → AI分析 → 专家/督导/教练分级审核 → 推送学员

端点:
  GET  /api/v1/health-review/queue          — 按角色获取待审列表
  POST /api/v1/health-review/{id}/approve   — 审核通过(直接推送)
  POST /api/v1/health-review/{id}/revise    — 修订后推送
  POST /api/v1/health-review/{id}/reject    — 退回重新采集
  POST /api/v1/health-data/werun/sync       — 微信步数解密同步
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text as sa_text
from loguru import logger

from core.database import get_db
from api.dependencies import get_current_user

router = APIRouter(prefix="/api/v1", tags=["Health Review & WeRun"])


# ─────────────────────────────────────────────────────────────
# Pydantic Models
# ─────────────────────────────────────────────────────────────

class WeRunSyncRequest(BaseModel):
    """微信步数同步请求（明文备用字段）"""
    encrypted_data: Optional[str] = None
    iv: Optional[str] = None
    step_info_list: Optional[List[Dict[str, Any]]] = None  # [{step, timestamp}]
    step_count: Optional[int] = None     # 直接传步数（开发模式）
    date: Optional[str] = None           # YYYY-MM-DD，默认今日


class ReviewDecisionRequest(BaseModel):
    action: str = Field(..., description="approve | revise | reject")
    coach_note: Optional[str] = Field(None, max_length=500)
    revised_content: Optional[str] = Field(None, max_length=1000)
    push_target_role: Optional[str] = Field("grower", description="grower|sharer|coach")


# ─────────────────────────────────────────────────────────────
# 健康数据审核队列
# ─────────────────────────────────────────────────────────────

@router.get("/health-review/queue")
async def get_review_queue(
    reviewer_role: Optional[str] = Query(None, description="coach|supervisor|master"),
    risk_level: Optional[str] = Query(None, description="critical|high|medium|low"),
    status: str = Query("pending"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """获取健康数据审核队列（按角色过滤）"""
    try:
        # 检查表是否存在
        check = db.execute(sa_text(
            "SELECT to_regclass('public.health_review_queue')"
        )).scalar()

        if not check:
            # 表不存在，返回空列表（防止 500）
            return {"items": [], "total": 0, "page": page, "page_size": page_size}

        conditions = ["hrq.status = :status"]
        params: Dict[str, Any] = {"status": status, "limit": page_size, "offset": (page - 1) * page_size}

        if reviewer_role:
            conditions.append("hrq.reviewer_role = :reviewer_role")
            params["reviewer_role"] = reviewer_role

        if risk_level:
            conditions.append("hrq.risk_level = :risk_level")
            params["risk_level"] = risk_level

        where = " AND ".join(conditions)

        rows = db.execute(sa_text(f"""
            SELECT
                hrq.id,
                hrq.user_id,
                hrq.risk_level,
                hrq.reviewer_role,
                hrq.status,
                hrq.ai_summary,
                hrq.ai_recommendation,
                hrq.reviewer_note,
                hrq.final_content,
                hrq.data_type,
                hrq.created_at,
                hrq.reviewed_at,
                u.full_name   AS student_name,
                u.username    AS student_username
            FROM health_review_queue hrq
            LEFT JOIN users u ON u.id = hrq.user_id
            WHERE {where}
            ORDER BY CASE hrq.risk_level WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END,
                     hrq.created_at DESC
            LIMIT :limit OFFSET :offset
        """), params).mappings().all()

        count = db.execute(sa_text(f"""
            SELECT COUNT(*) FROM health_review_queue hrq WHERE {where}
        """), {k: v for k, v in params.items() if k not in ('limit', 'offset')}).scalar()

        return {
            "items": [dict(r) for r in rows],
            "total": count or 0,
            "page": page,
            "page_size": page_size,
        }

    except Exception as e:
        logger.warning(f"[HealthReview] queue query failed: {e}")
        return {"items": [], "total": 0, "page": page, "page_size": page_size}


@router.post("/health-review/{review_id}/approve")
async def approve_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """审核通过 — AI分析内容直接推送给学员"""
    return await _update_review_status(review_id, "approved", None, db, current_user)


@router.post("/health-review/{review_id}/reject")
async def reject_review(
    review_id: int,
    body: ReviewDecisionRequest = None,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """退回 — 标记为 rejected，说明原因"""
    note = body.coach_note if body else None
    return await _update_review_status(review_id, "rejected", note, db, current_user)


@router.post("/health-review/{review_id}/revise")
async def revise_review(
    review_id: int,
    body: ReviewDecisionRequest,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """修订后发送 — 更新 final_content 然后标记为 approved"""
    try:
        check = db.execute(sa_text("SELECT to_regclass('public.health_review_queue')")).scalar()
        if not check:
            return {"success": True, "message": "已修订（沙盒模式）"}

        db.execute(sa_text("""
            UPDATE health_review_queue
            SET status='approved', final_content=:content, reviewer_note=:note,
                reviewer_id=:rid, reviewed_at=NOW()
            WHERE id=:id
        """), {
            "content": body.revised_content or body.coach_note,
            "note": body.coach_note,
            "rid": current_user.id,
            "id": review_id,
        })
        db.commit()
        return {"success": True, "message": "已修订并标记为推送"}
    except Exception as e:
        db.rollback()
        logger.error(f"[HealthReview] revise failed: {e}")
        raise HTTPException(status_code=500, detail="修订失败")


async def _update_review_status(review_id: int, new_status: str, note: Optional[str], db: Session, current_user: Any):
    try:
        check = db.execute(sa_text("SELECT to_regclass('public.health_review_queue')")).scalar()
        if not check:
            return {"success": True, "message": f"状态已更新为 {new_status}（沙盒模式）"}

        result = db.execute(sa_text("""
            UPDATE health_review_queue
            SET status=:status, reviewer_note=:note, reviewer_id=:rid, reviewed_at=NOW()
            WHERE id=:id AND status='pending'
            RETURNING id
        """), {"status": new_status, "note": note, "rid": current_user.id, "id": review_id})
        db.commit()
        if not result.fetchone():
            raise HTTPException(status_code=400, detail="记录不存在或状态已更新")
        return {"success": True, "status": new_status}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"[HealthReview] status update failed: {e}")
        raise HTTPException(status_code=500, detail="操作失败")


# ─────────────────────────────────────────────────────────────
# 微信步数同步
# ─────────────────────────────────────────────────────────────

@router.post("/health-data/werun/sync")
async def sync_werun_data(
    body: WeRunSyncRequest,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """
    同步微信运动步数到 activity_records。
    支持两种模式:
    1. encrypted_data + iv: 使用会话密钥解密（生产）
    2. step_info_list / step_count: 明文备用（开发/降级）
    """
    target_date = body.date or date.today().isoformat()
    steps = 0

    # 尝试从加密数据解密（生产环境）
    if body.encrypted_data and body.iv:
        try:
            import base64
            from Crypto.Cipher import AES  # pycryptodome

            # 从 Redis 或 DB 获取会话密钥（简化版：从环境变量）
            session_key_b64 = None  # 实际应从用户会话中取
            if session_key_b64:
                session_key = base64.b64decode(session_key_b64)
                iv_bytes = base64.b64decode(body.iv)
                enc_bytes = base64.b64decode(body.encrypted_data)
                cipher = AES.new(session_key, AES.MODE_CBC, iv_bytes)
                decrypted = cipher.decrypt(enc_bytes)
                import json
                data = json.loads(decrypted.rstrip(b'\x00').rstrip(b'\x0f'))
                step_info = data.get("stepInfoList", [])
                if step_info:
                    steps = step_info[0].get("step", 0)
        except Exception as e:
            logger.warning(f"[WeRun] Decrypt failed: {e}")

    # 降级：使用明文步数列表
    if steps == 0 and body.step_info_list:
        steps = body.step_info_list[0].get("step", 0) if body.step_info_list else 0

    # 再降级：直接步数
    if steps == 0 and body.step_count:
        steps = body.step_count

    if steps <= 0:
        return {"success": False, "message": "步数数据为空或解密失败", "steps": 0}

    # 写入 activity_records
    try:
        db.execute(sa_text("""
            INSERT INTO activity_records (user_id, activity_type, steps, source_type, start_time, created_at)
            VALUES (:uid, 'walking', :steps, 'werun', :start_time, NOW())
            ON CONFLICT DO NOTHING
        """), {
            "uid": current_user.id,
            "steps": steps,
            "start_time": target_date + "T00:00:00",
        })
        db.commit()
        # ── 活动量风险评估（连续低步数） ──────────────────
        _check_activity_risk(db, current_user.id, steps)
        return {"success": True, "steps": steps, "date": target_date}
    except Exception as e:
        db.rollback()
        logger.warning(f"[WeRun] DB insert failed: {e}")
        # 尝试不带 ON CONFLICT（表结构可能不同）
        try:
            db.execute(sa_text("""
                INSERT INTO activity_records (user_id, activity_type, steps, source_type, start_time, created_at)
                VALUES (:uid, 'walking', :steps, 'werun', :start_time, NOW())
            """), {"uid": current_user.id, "steps": steps, "start_time": target_date + "T00:00:00"})
            db.commit()
            _check_activity_risk(db, current_user.id, steps)
            return {"success": True, "steps": steps, "date": target_date}
        except Exception as e2:
            db.rollback()
            logger.error(f"[WeRun] DB insert failed again: {e2}")
            return {"success": True, "steps": steps, "date": target_date, "note": "已获取步数但存储失败"}


# ─────────────────────────────────────────────────────────────
# 督导/专家 Dashboard (stub)
# ─────────────────────────────────────────────────────────────

@router.get("/supervisor/dashboard")
async def supervisor_dashboard(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """督导工作台概览"""
    try:
        check = db.execute(sa_text("SELECT to_regclass('public.health_review_queue')")).scalar()
        pending = 0
        if check:
            pending = db.execute(sa_text(
                "SELECT COUNT(*) FROM health_review_queue WHERE reviewer_role='supervisor' AND status='pending'"
            )).scalar() or 0

        coach_count = db.execute(sa_text(
            "SELECT COUNT(*) FROM users WHERE role='coach' AND is_active=true"
        )).scalar() or 0

        return {
            "coach_count": int(coach_count),
            "pending_review": int(pending),
            "high_risk_count": 0,
            "approved_today": 0,
        }
    except Exception as e:
        logger.warning(f"[Supervisor] dashboard failed: {e}")
        return {"coach_count": 0, "pending_review": 0, "high_risk_count": 0, "approved_today": 0}


@router.get("/supervisor/coaches")
async def supervisor_coaches(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """督导管理的教练列表"""
    try:
        rows = db.execute(sa_text("""
            SELECT u.id, u.full_name, u.username, u.email
            FROM users u WHERE u.role='coach' AND u.is_active=true
            ORDER BY u.full_name LIMIT 50
        """)).mappings().all()
        return {"coaches": [dict(r) for r in rows], "total": len(rows)}
    except Exception as e:
        logger.warning(f"[Supervisor] coaches list failed: {e}")
        return {"coaches": [], "total": 0}


@router.get("/master/dashboard")
async def master_dashboard(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """专家工作台概览"""
    try:
        check = db.execute(sa_text("SELECT to_regclass('public.health_review_queue')")).scalar()
        critical = 0
        ai_pending = 0
        if check:
            critical = db.execute(sa_text(
                "SELECT COUNT(*) FROM health_review_queue WHERE reviewer_role='master' AND risk_level='critical' AND status='pending'"
            )).scalar() or 0
            ai_pending = db.execute(sa_text(
                "SELECT COUNT(*) FROM health_review_queue WHERE reviewer_role='master' AND status='pending'"
            )).scalar() or 0

        return {
            "critical_count": int(critical),
            "ai_pending": int(ai_pending),
            "knowledge_pending": 0,
            "reviewed_today": 0,
        }
    except Exception as e:
        logger.warning(f"[Master] dashboard failed: {e}")
        return {"critical_count": 0, "ai_pending": 0, "knowledge_pending": 0, "reviewed_today": 0}


@router.get("/knowledge/items")
async def knowledge_items(
    status: Optional[str] = Query("pending_review"),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    """知识库条目列表（待审核）"""
    try:
        rows = db.execute(sa_text("""
            SELECT kc.id, kc.title, kc.category, kc.created_at,
                   'pending_review' AS status
            FROM knowledge_chunks kc
            LIMIT 20
        """)).mappings().all()
        return {"items": [dict(r) for r in rows], "total": len(rows)}
    except Exception as e:
        logger.warning(f"[Knowledge] items failed: {e}")
        return {"items": [], "total": 0}


@router.post("/knowledge/items/{item_id}/publish")
async def publish_knowledge(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    return {"success": True, "message": "已发布", "id": item_id}


@router.post("/knowledge/items/{item_id}/reject")
async def reject_knowledge(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user),
):
    return {"success": True, "message": "已退回", "id": item_id}


# ─────────────────────────────────────────────────────────────
# 内部：活动量风险检查（连续低步数）
# ─────────────────────────────────────────────────────────────
def _check_activity_risk(db: Session, user_id: int, today_steps: int) -> None:
    """
    查询最近7天步数记录，统计连续低步数天数，触发风险评估。
    设计为"不阻塞主流程"——所有异常直接 swallow。
    """
    try:
        rows = db.execute(sa_text("""
            SELECT steps FROM activity_records
            WHERE user_id = :uid
              AND created_at > NOW() - INTERVAL '7 days'
            ORDER BY created_at DESC
            LIMIT 7
        """), {"uid": user_id}).fetchall()

        # 计算连续低步数天数（含今天）
        low_threshold = 3000
        consecutive = 0
        for r in rows:
            s = r[0] or 0
            if s < low_threshold:
                consecutive += 1
            else:
                break

        if today_steps < low_threshold:
            consecutive = max(consecutive, 1)

        from api.health_risk_engine import trigger_activity_review
        trigger_activity_review(db, user_id, today_steps, consecutive)
    except Exception as e:
        logger.warning(f"[WeRun] 活动量风险检查失败（不影响主流程）: {e}")

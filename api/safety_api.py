# -*- coding: utf-8 -*-
"""
安全管理 API — 8 端点 (全部 require_admin)

- GET  /v1/safety/dashboard       — 安全仪表盘
- GET  /v1/safety/logs             — 安全日志列表
- GET  /v1/safety/logs/{id}        — 日志详情
- PUT  /v1/safety/logs/{id}/resolve — 标记已处理
- GET  /v1/safety/review-queue     — 待审核队列
- GET  /v1/safety/config           — 当前安全配置
- PUT  /v1/safety/config           — 更新安全配置
- GET  /v1/safety/reports/daily    — 日报
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, case, and_
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, require_admin
from core.database import get_db

router = APIRouter(prefix="/api/v1/safety", tags=["安全管理"])


# ── Pydantic 模型 ──

class ResolveRequest(BaseModel):
    action: str = "resolved"  # resolved / false_positive / whitelist


class SafetyConfigUpdate(BaseModel):
    crisis_keywords: Optional[list[str]] = None
    warning_keywords: Optional[list[str]] = None
    blocked_keywords: Optional[list[str]] = None
    medical_keywords: Optional[list[str]] = None


# ── 1. 安全仪表盘 ──

@router.get("/dashboard")
def safety_dashboard(
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """安全仪表盘 — 今日/本周/本月统计"""
    from core.models import SafetyLog

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    def count_in_range(start):
        return db.query(func.count(SafetyLog.id)).filter(
            SafetyLog.created_at >= start
        ).scalar() or 0

    def count_by_severity(start, severity):
        return db.query(func.count(SafetyLog.id)).filter(
            and_(SafetyLog.created_at >= start, SafetyLog.severity == severity)
        ).scalar() or 0

    pending_review = db.query(func.count(SafetyLog.id)).filter(
        SafetyLog.resolved == False
    ).scalar() or 0

    crisis_today = count_by_severity(today_start, "critical")

    # 事件类型分布 (近30天)
    type_dist = db.query(
        SafetyLog.event_type,
        func.count(SafetyLog.id),
    ).filter(
        SafetyLog.created_at >= month_start
    ).group_by(SafetyLog.event_type).all()

    # 7日趋势
    trend_7d = []
    for i in range(6, -1, -1):
        day = today_start - timedelta(days=i)
        day_end = day + timedelta(days=1)
        cnt = db.query(func.count(SafetyLog.id)).filter(
            and_(SafetyLog.created_at >= day, SafetyLog.created_at < day_end)
        ).scalar() or 0
        trend_7d.append({"date": day.strftime("%m-%d"), "count": cnt})

    return {
        "today": count_in_range(today_start),
        "this_week": count_in_range(week_start),
        "this_month": count_in_range(month_start),
        "pending_review": pending_review,
        "crisis_today": crisis_today,
        "type_distribution": {t: c for t, c in type_dist},
        "trend_7d": trend_7d,
    }


# ── 2. 安全日志列表 ──

@router.get("/logs")
def safety_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    resolved: Optional[bool] = None,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """安全日志列表 (分页+筛选)"""
    from core.models import SafetyLog

    q = db.query(SafetyLog)
    if event_type:
        q = q.filter(SafetyLog.event_type == event_type)
    if severity:
        q = q.filter(SafetyLog.severity == severity)
    if resolved is not None:
        q = q.filter(SafetyLog.resolved == resolved)

    total = q.count()
    items = (
        q.order_by(SafetyLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": item.id,
                "user_id": item.user_id,
                "event_type": item.event_type,
                "severity": item.severity,
                "input_text": (item.input_text or "")[:200],  # 截断敏感内容
                "output_text": (item.output_text or "")[:200],
                "resolved": item.resolved,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ],
    }


# ── 3. 日志详情 ──

@router.get("/logs/{log_id}")
def safety_log_detail(
    log_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """安全日志详情"""
    from core.models import SafetyLog

    log = db.query(SafetyLog).filter(SafetyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")

    return {
        "id": log.id,
        "user_id": log.user_id,
        "event_type": log.event_type,
        "severity": log.severity,
        "input_text": log.input_text,
        "output_text": log.output_text,
        "filter_details": log.filter_details,
        "resolved": log.resolved,
        "resolved_by": log.resolved_by,
        "resolved_at": log.resolved_at.isoformat() if log.resolved_at else None,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


# ── 4. 标记已处理 ──

@router.put("/logs/{log_id}/resolve")
def resolve_safety_log(
    log_id: int,
    body: ResolveRequest,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    """标记安全事件为已处理"""
    from core.models import SafetyLog

    log = db.query(SafetyLog).filter(SafetyLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="日志不存在")

    log.resolved = True
    log.resolved_by = current_user.id
    log.resolved_at = datetime.utcnow()

    if log.filter_details is None:
        log.filter_details = {}
    log.filter_details = {**log.filter_details, "resolve_action": body.action}

    db.commit()
    return {"message": "已处理", "id": log_id}


# ── 5. 待审核队列 ──

@router.get("/review-queue")
def safety_review_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[str] = None,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """待审核安全事件队列"""
    from core.models import SafetyLog

    q = db.query(SafetyLog).filter(SafetyLog.resolved == False)
    if severity:
        q = q.filter(SafetyLog.severity == severity)

    total = q.count()
    items = (
        q.order_by(
            case(
                (SafetyLog.severity == "critical", 0),
                (SafetyLog.severity == "high", 1),
                (SafetyLog.severity == "medium", 2),
                else_=3,
            ),
            SafetyLog.created_at.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": item.id,
                "user_id": item.user_id,
                "event_type": item.event_type,
                "severity": item.severity,
                "input_text": (item.input_text or "")[:200],
                "output_text": (item.output_text or "")[:200],
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
            for item in items
        ],
    }


# ── 6. 当前安全配置 ──

@router.get("/config")
def get_safety_config(admin=Depends(require_admin)):
    """获取当前安全关键词/规则配置"""
    configs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "configs",
    )

    result = {}
    for name in ("safety_keywords", "safety_rules"):
        path = os.path.join(configs_dir, f"{name}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                result[name] = json.load(f)
        except FileNotFoundError:
            result[name] = {}

    return result


# ── 7. 更新安全配置 ──

@router.put("/config")
def update_safety_config(
    body: SafetyConfigUpdate,
    admin=Depends(require_admin),
):
    """更新安全关键词配置 (仅更新传入的字段)"""
    keywords_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "configs", "safety_keywords.json",
    )

    try:
        with open(keywords_path, "r", encoding="utf-8") as f:
            current = json.load(f)
    except FileNotFoundError:
        current = {}

    # 仅更新传入的字段
    if body.crisis_keywords is not None:
        current["crisis"] = body.crisis_keywords
    if body.warning_keywords is not None:
        current["warning"] = body.warning_keywords
    if body.blocked_keywords is not None:
        current["blocked"] = body.blocked_keywords
    if body.medical_keywords is not None:
        current["medical_advice"] = body.medical_keywords

    with open(keywords_path, "w", encoding="utf-8") as f:
        json.dump(current, f, ensure_ascii=False, indent=2)

    # 重新加载安全管线
    try:
        from core.safety.pipeline import get_safety_pipeline
        pipeline = get_safety_pipeline()
        pipeline.input_filter._load_keywords(keywords_path)
    except Exception:
        pass

    return {"message": "配置已更新"}


# ── 8. 日报 ──

@router.get("/reports/daily")
def safety_daily_report(
    date: Optional[str] = None,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """查看安全日报 (默认昨天)"""
    from core.models import SafetyLog

    if date:
        try:
            target = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式应为 YYYY-MM-DD")
    else:
        target = datetime.utcnow() - timedelta(days=1)

    day_start = target.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)

    total = db.query(func.count(SafetyLog.id)).filter(
        and_(SafetyLog.created_at >= day_start, SafetyLog.created_at < day_end)
    ).scalar() or 0

    by_severity = db.query(
        SafetyLog.severity, func.count(SafetyLog.id),
    ).filter(
        and_(SafetyLog.created_at >= day_start, SafetyLog.created_at < day_end)
    ).group_by(SafetyLog.severity).all()

    by_type = db.query(
        SafetyLog.event_type, func.count(SafetyLog.id),
    ).filter(
        and_(SafetyLog.created_at >= day_start, SafetyLog.created_at < day_end)
    ).group_by(SafetyLog.event_type).all()

    return {
        "date": day_start.strftime("%Y-%m-%d"),
        "total_events": total,
        "by_severity": {s: c for s, c in by_severity},
        "by_type": {t: c for t, c in by_type},
    }

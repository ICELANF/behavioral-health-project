# -*- coding: utf-8 -*-
"""
运营中心 API — 平台事件 + 系统日志

端点：
- GET /api/v1/admin/operation-center/events    — 聚合事件流 (demo_requests + notifications)
- GET /api/v1/admin/operation-center/logs      — 系统日志读取 (loguru 文件)
- GET /api/v1/admin/operation-center/stats      — 运营统计概览
"""
import os
import re
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from loguru import logger
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from api.dependencies import require_admin
from core.database import get_db
from core.models import DemoRequest, Notification, User

router = APIRouter(
    prefix="/api/v1/admin/operation-center",
    tags=["Operation Center"],
)

# ── 日志目录 ──
_LOG_DIR = os.getenv("LOG_DIR", "/app/logs")
if not os.path.isdir(_LOG_DIR):
    _LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")


# ══════════ GET /stats — 运营统计概览 ══════════

@router.get("/stats")
def get_operation_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """运营中心顶部统计卡片"""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 预约统计
    total_requests = db.query(func.count(DemoRequest.id)).scalar() or 0
    pending_requests = db.query(func.count(DemoRequest.id)).filter(DemoRequest.status == "pending").scalar() or 0
    today_requests = db.query(func.count(DemoRequest.id)).filter(DemoRequest.created_at >= today_start).scalar() or 0

    # 未读通知
    unread_notifs = db.query(func.count(Notification.id)).filter(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    ).scalar() or 0

    # 最近错误日志数 (从文件快速扫描)
    error_count_today = _count_log_errors_today()

    return {
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "today_requests": today_requests,
        "unread_notifications": unread_notifs,
        "error_count_today": error_count_today,
    }


# ══════════ GET /events — 聚合事件流 ══════════

@router.get("/events")
def list_events(
    event_type: Optional[str] = Query(None, description="demo_request/notification/all"),
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """聚合事件流 — 合并预约请求 + 站内通知"""
    events = []

    # 1) Demo requests → events
    if not event_type or event_type in ("demo_request", "all"):
        demos = db.query(DemoRequest).order_by(desc(DemoRequest.created_at)).limit(200).all()
        for d in demos:
            solution_label = {"hospital": "医院", "insurance": "商保", "government": "政府", "rwe": "RWE"}.get(d.solution or "", "")
            events.append({
                "id": f"demo-{d.id}",
                "type": "demo_request",
                "title": f"预约演示 — {d.name}",
                "detail": f"{d.organization or ''} {solution_label}".strip() or "未填写",
                "status": d.status,
                "time": d.created_at.isoformat() if d.created_at else "",
                "priority": "high",
            })

    # 2) Admin notifications → events
    if not event_type or event_type in ("notification", "all"):
        notifs = db.query(Notification).filter(
            Notification.user_id == current_user.id
        ).order_by(desc(Notification.created_at)).limit(200).all()
        for n in notifs:
            events.append({
                "id": f"notif-{n.id}",
                "type": "notification",
                "title": n.title or "系统通知",
                "detail": n.body or "",
                "status": "read" if n.is_read else "unread",
                "time": n.created_at.isoformat() if n.created_at else "",
                "priority": n.priority or "normal",
            })

    # Sort by time desc, then paginate
    events.sort(key=lambda e: e["time"], reverse=True)
    total = len(events)
    return {
        "total": total,
        "items": events[skip: skip + limit],
    }


# ══════════ GET /logs — 系统日志读取 ══════════

@router.get("/logs")
def read_system_logs(
    level: Optional[str] = Query(None, description="ERROR/WARNING/INFO"),
    date: Optional[str] = Query(None, description="YYYY-MM-DD, 默认今天"),
    keyword: Optional[str] = Query(None, max_length=100),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_admin),
):
    """读取系统日志文件 (loguru 文本格式)"""
    target_date = date or datetime.utcnow().strftime("%Y-%m-%d")

    log_file = os.path.join(_LOG_DIR, f"bhp_{target_date}.log")
    if not os.path.isfile(log_file):
        return {"total": 0, "items": [], "log_file": log_file, "available_dates": _list_log_dates()}

    lines = _parse_log_file(log_file, level=level, keyword=keyword)
    total = len(lines)
    # Return newest first
    lines.reverse()
    page = lines[skip: skip + limit]

    return {
        "total": total,
        "items": page,
        "log_file": os.path.basename(log_file),
        "available_dates": _list_log_dates(),
    }


# ══════════ Helpers ══════════

_LOG_LINE_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})\s*\|\s*(\w+)\s*\|\s*([^|]+)\|\s*(.*)"
)

def _parse_log_file(filepath: str, level: Optional[str] = None, keyword: Optional[str] = None) -> list:
    """Parse a loguru log file into structured entries."""
    entries = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.rstrip()
                if not line:
                    continue
                m = _LOG_LINE_RE.match(line)
                if m:
                    ts, lvl, source, msg = m.group(1), m.group(2).strip(), m.group(3).strip(), m.group(4).strip()
                    if level and lvl.upper() != level.upper():
                        continue
                    if keyword and keyword.lower() not in msg.lower() and keyword.lower() not in source.lower():
                        continue
                    entries.append({
                        "time": ts,
                        "level": lvl,
                        "source": source,
                        "message": msg,
                    })
    except Exception as e:
        logger.error(f"[OperationCenter] 日志读取失败: {e}")
    return entries


def _list_log_dates() -> list:
    """List available log file dates."""
    dates = []
    try:
        if os.path.isdir(_LOG_DIR):
            for f in sorted(os.listdir(_LOG_DIR), reverse=True):
                if f.startswith("bhp_") and f.endswith(".log"):
                    d = f.replace("bhp_", "").replace(".log", "")
                    if re.match(r"\d{4}-\d{2}-\d{2}", d):
                        dates.append(d)
    except Exception:
        pass
    return dates[:30]


def _count_log_errors_today() -> int:
    """Quick count of ERROR lines in today's log."""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    log_file = os.path.join(_LOG_DIR, f"bhp_{today}.log")
    if not os.path.isfile(log_file):
        return 0
    count = 0
    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if "| ERROR" in line or "| CRITICAL" in line:
                    count += 1
    except Exception:
        pass
    return count

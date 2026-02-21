"""
Operations Report API — weekly/monthly analytics + CSV export.

Endpoints:
  GET /api/v1/admin/reports/weekly     — Last 7 days from analytics_daily
  GET /api/v1/admin/reports/monthly    — Last 30 days aggregated
  GET /api/v1/admin/reports/export     — CSV StreamingResponse
"""
import csv
import io
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from api.dependencies import require_admin

router = APIRouter(prefix="/api/v1/admin/reports", tags=["Operations Reports"])


class DayMetrics(BaseModel):
    date: str
    dau: int = 0
    new_users: int = 0
    active_growers: int = 0
    conversion_rate: float = 0.0
    retention_7d: float = 0.0
    avg_tasks_completed: float = 0.0
    avg_session_minutes: float = 0.0
    ai_response_avg_ms: float = 0.0
    total_events: int = 0
    total_chat_messages: int = 0


async def _fetch_range(db: AsyncSession, start: date, end: date) -> list[dict]:
    result = await db.execute(
        text("""
            SELECT date::text, dau, new_users, active_growers, conversion_rate,
                   retention_7d, avg_tasks_completed, avg_session_minutes,
                   ai_response_avg_ms, total_events, total_chat_messages
            FROM analytics_daily
            WHERE date BETWEEN :s AND :e
            ORDER BY date
        """),
        {"s": start, "e": end},
    )
    return [dict(r) for r in result.mappings().all()]


def _trends(rows: list[dict]) -> dict:
    """Compute simple trends (last vs first half averages)."""
    if len(rows) < 2:
        return {}
    mid = len(rows) // 2
    first_half = rows[:mid]
    second_half = rows[mid:]

    def _avg(data, key):
        vals = [r.get(key, 0) or 0 for r in data]
        return sum(vals) / len(vals) if vals else 0

    return {
        "dau_trend": round(_avg(second_half, "dau") - _avg(first_half, "dau"), 1),
        "conversion_trend": round(_avg(second_half, "conversion_rate") - _avg(first_half, "conversion_rate"), 3),
        "retention_trend": round(_avg(second_half, "retention_7d") - _avg(first_half, "retention_7d"), 3),
    }


@router.get("/weekly")
async def weekly_report(
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """Last 7 days from analytics_daily + trends."""
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=6)
    try:
        rows = await _fetch_range(db, start, end)
    except Exception:
        rows = []
    return {
        "period": "weekly",
        "start": str(start),
        "end": str(end),
        "days": rows,
        "trends": _trends(rows),
    }


@router.get("/monthly")
async def monthly_report(
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """Last 30 days aggregated."""
    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=29)
    try:
        rows = await _fetch_range(db, start, end)
    except Exception:
        rows = []

    # Aggregate totals
    totals = {}
    if rows:
        for key in ["dau", "new_users", "total_events", "total_chat_messages"]:
            totals[key] = sum(r.get(key, 0) or 0 for r in rows)
        for key in ["conversion_rate", "retention_7d", "avg_tasks_completed", "avg_session_minutes", "ai_response_avg_ms"]:
            vals = [r.get(key, 0) or 0 for r in rows]
            totals[key] = round(sum(vals) / len(vals), 2) if vals else 0
        totals["dau"] = round(totals["dau"] / len(rows))  # avg DAU

    return {
        "period": "monthly",
        "start": str(start),
        "end": str(end),
        "totals": totals,
        "days": rows,
        "trends": _trends(rows),
    }


@router.get("/export")
async def export_report(
    period: str = Query("weekly", regex="^(weekly|monthly)$"),
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """CSV StreamingResponse for download."""
    end = date.today() - timedelta(days=1)
    days = 6 if period == "weekly" else 29
    start = end - timedelta(days=days)
    try:
        rows = await _fetch_range(db, start, end)
    except Exception:
        rows = []

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=[
        "date", "dau", "new_users", "active_growers", "conversion_rate",
        "retention_7d", "avg_tasks_completed", "avg_session_minutes",
        "ai_response_avg_ms", "total_events", "total_chat_messages",
    ])
    writer.writeheader()
    for row in rows:
        writer.writerow(row)

    output.seek(0)
    filename = f"bhp_report_{period}_{start}_{end}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

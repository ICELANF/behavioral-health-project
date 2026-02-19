"""
P4 R13e: System Settings API
Simple key-value JSON settings store using PostgreSQL.
Uses system_settings table (auto-created if missing).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_async_db
from api.dependencies import require_admin

router = APIRouter(prefix="/api/v1/admin/settings", tags=["settings"])


class SettingsPayload(BaseModel):
    class Config:
        extra = "allow"


async def _ensure_table(db: AsyncSession):
    """Create system_settings table if it doesn't exist."""
    await db.execute(text("""
        CREATE TABLE IF NOT EXISTS system_settings (
            category TEXT PRIMARY KEY,
            data JSONB NOT NULL DEFAULT '{}',
            updated_at TIMESTAMP DEFAULT NOW(),
            updated_by INTEGER
        )
    """))
    await db.commit()


@router.get("/{category}")
async def get_settings(
    category: str,
    _=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """Get settings by category (basic/levels/exam/notification)."""
    await _ensure_table(db)
    r = await db.execute(
        text("SELECT data FROM system_settings WHERE category = :cat"),
        {"cat": category},
    )
    row = r.scalar_one_or_none()
    if row is None:
        return {}
    return row


@router.put("/{category}")
async def save_settings(
    category: str,
    payload: SettingsPayload,
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """Save settings by category."""
    import json
    await _ensure_table(db)
    data_json = json.dumps(payload.dict(), ensure_ascii=False, default=str)
    await db.execute(text("""
        INSERT INTO system_settings (category, data, updated_at, updated_by)
        VALUES (:cat, CAST(:data AS jsonb), NOW(), :uid)
        ON CONFLICT (category)
        DO UPDATE SET data = CAST(:data AS jsonb), updated_at = NOW(), updated_by = :uid
    """), {"cat": category, "data": data_json, "uid": admin_user.id})
    await db.commit()
    return {"success": True, "category": category, "message": "设置已保存"}

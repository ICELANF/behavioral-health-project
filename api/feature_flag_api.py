"""
Feature Flag + A/B Testing API.

Endpoints:
  GET  /api/v1/flags                    — User's enabled flags + variants
  POST /api/v1/flags/event              — Track A/B conversion event
  GET  /api/v1/admin/flags              — List all flags (admin)
  POST /api/v1/admin/flags              — Create flag (admin)
  PUT  /api/v1/admin/flags/{key}        — Update flag (admin)
  DELETE /api/v1/admin/flags/{key}      — Delete flag (admin)
  GET  /api/v1/admin/flags/{key}/results — A/B test results (admin)
"""
import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from core.database import get_async_db
from api.dependencies import get_current_user, require_admin
from core.models import User
from core.feature_flags import FeatureFlagService

router = APIRouter(tags=["Feature Flags"])


# ── Schemas ──

class FlagCreate(BaseModel):
    key: str
    description: Optional[str] = ""
    enabled: bool = False
    rollout_pct: int = 0
    variants: List[str] = ["control"]
    targeting_rules: dict = {}


class FlagUpdate(BaseModel):
    description: Optional[str] = None
    enabled: Optional[bool] = None
    rollout_pct: Optional[int] = None
    variants: Optional[List[str]] = None
    targeting_rules: Optional[dict] = None


class AbEventCreate(BaseModel):
    experiment_key: str
    event_type: str
    event_data: Optional[dict] = {}


# ═══════════════════════════════════════════════════
# User-facing
# ═══════════════════════════════════════════════════

@router.get("/api/v1/flags")
async def get_user_flags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Return all enabled flags + variants for the current user."""
    svc = FeatureFlagService(db)
    try:
        result = await db.execute(text("SELECT key FROM feature_flags WHERE enabled = true"))
        flag_keys = [r["key"] for r in result.mappings().all()]
    except Exception:
        flag_keys = []

    flags = {}
    for key in flag_keys:
        enabled = await svc.is_enabled(key, current_user.id)
        if enabled:
            variant = await svc.get_variant(key, current_user.id)
            flags[key] = {"enabled": True, "variant": variant}

    return {"flags": flags}


@router.post("/api/v1/flags/event")
async def track_ab_event(
    req: AbEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Track an A/B test conversion event."""
    svc = FeatureFlagService(db)
    variant = await svc.get_variant(req.experiment_key, current_user.id)

    await db.execute(
        text("""
            INSERT INTO ab_test_events (user_id, experiment_key, variant, event_type, event_data, created_at)
            VALUES (:uid, :ek, :var, :et, CAST(:ed AS jsonb), NOW())
        """),
        {
            "uid": current_user.id,
            "ek": req.experiment_key,
            "var": variant,
            "et": req.event_type,
            "ed": json.dumps(req.event_data or {}, ensure_ascii=False),
        },
    )
    await db.commit()
    return {"success": True, "variant": variant}


# ═══════════════════════════════════════════════════
# Admin CRUD
# ═══════════════════════════════════════════════════

@router.get("/api/v1/admin/flags")
async def list_flags(
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """List all feature flags with basic stats."""
    result = await db.execute(text(
        "SELECT id, key, description, enabled, rollout_pct, variants, targeting_rules, created_at, updated_at "
        "FROM feature_flags ORDER BY id"
    ))
    flags = []
    for r in result.mappings().all():
        d = dict(r)
        d["created_at"] = str(d["created_at"])
        d["updated_at"] = str(d["updated_at"])
        flags.append(d)
    return {"flags": flags}


@router.post("/api/v1/admin/flags")
async def create_flag(
    req: FlagCreate,
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """Create a new feature flag."""
    try:
        await db.execute(
            text("""
                INSERT INTO feature_flags (key, description, enabled, rollout_pct, variants, targeting_rules, created_at, updated_at)
                VALUES (:k, :d, :e, :r, CAST(:v AS jsonb), CAST(:t AS jsonb), NOW(), NOW())
            """),
            {
                "k": req.key, "d": req.description, "e": req.enabled,
                "r": req.rollout_pct,
                "v": json.dumps(req.variants),
                "t": json.dumps(req.targeting_rules),
            },
        )
        await db.commit()
    except Exception as e:
        raise HTTPException(409, f"Flag key already exists or DB error: {e}")
    return {"success": True, "key": req.key}


@router.put("/api/v1/admin/flags/{key}")
async def update_flag(
    key: str,
    req: FlagUpdate,
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """Update a feature flag."""
    sets = []
    params = {"k": key}
    if req.enabled is not None:
        sets.append("enabled = :e")
        params["e"] = req.enabled
    if req.rollout_pct is not None:
        sets.append("rollout_pct = :r")
        params["r"] = req.rollout_pct
    if req.description is not None:
        sets.append("description = :d")
        params["d"] = req.description
    if req.variants is not None:
        sets.append("variants = CAST(:v AS jsonb)")
        params["v"] = json.dumps(req.variants)
    if req.targeting_rules is not None:
        sets.append("targeting_rules = CAST(:t AS jsonb)")
        params["t"] = json.dumps(req.targeting_rules)

    if not sets:
        return {"success": True, "message": "Nothing to update"}

    sets.append("updated_at = NOW()")
    result = await db.execute(
        text(f"UPDATE feature_flags SET {', '.join(sets)} WHERE key = :k"),
        params,
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(404, f"Flag '{key}' not found")
    FeatureFlagService.clear_cache()
    return {"success": True}


@router.delete("/api/v1/admin/flags/{key}")
async def delete_flag(
    key: str,
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """Delete a feature flag."""
    result = await db.execute(text("DELETE FROM feature_flags WHERE key = :k"), {"k": key})
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(404, f"Flag '{key}' not found")
    FeatureFlagService.clear_cache()
    return {"success": True}


@router.get("/api/v1/admin/flags/{key}/results")
async def flag_results(
    key: str,
    admin_user=Depends(require_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """A/B test conversion rates by variant."""
    result = await db.execute(
        text("""
            SELECT variant,
                   COUNT(DISTINCT user_id) AS unique_users,
                   COUNT(*) AS total_events,
                   COUNT(DISTINCT CASE WHEN event_type = 'conversion' THEN user_id END) AS conversions
            FROM ab_test_events
            WHERE experiment_key = :k
            GROUP BY variant
            ORDER BY variant
        """),
        {"k": key},
    )
    variants = []
    for r in result.mappings().all():
        d = dict(r)
        d["conversion_rate"] = round(d["conversions"] / d["unique_users"], 4) if d["unique_users"] else 0.0
        variants.append(d)
    return {"experiment": key, "variants": variants}

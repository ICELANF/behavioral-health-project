# -*- coding: utf-8 -*-
"""
V4.1 Cross-Layer API Gateway — 6 endpoints

  GET  /v1/gateway/patient/{user_id}/profile      sanitized student profile
  GET  /v1/gateway/patient/{user_id}/assessments   assessment summary
  GET  /v1/gateway/patient/{user_id}/journey       journey state
  POST /v1/gateway/rx-delivery/{user_id}           deliver prescription
  GET  /v1/gateway/audit-log                       audit log (admin/supervisor)
  GET  /v1/gateway/bindings                        coach's student list
"""
from __future__ import annotations
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session

from .auth import GatewayAuth, log_cross_layer_access
from .sanitizer import sanitize_for_coach

from core.database import get_db
from api.dependencies import get_current_user
from core.models import User

router = APIRouter(prefix="/v1/gateway", tags=["cross_layer_gateway"])


# ===============================================================
# 1. Student profile (sanitized)
# ===============================================================

@router.get("/patient/{user_id}/profile")
def get_patient_profile(
    user_id: int,
    auth: dict = Depends(GatewayAuth("view_profile")),
    db: Session = Depends(get_db),
):
    """Coach views student profile — PII auto-sanitized."""
    row = db.execute(
        sa_text("""
            SELECT u.id, u.username, u.email, u.phone, u.role,
                   u.avatar_url, u.created_at,
                   bp.agency_mode, bp.trust_score, bp.current_stage,
                   bp.big5_scores, bp.bpt6_type, bp.spi_score,
                   js.journey_stage, js.stage_entered_at, js.agency_score
            FROM users u
            LEFT JOIN behavioral_profiles bp ON bp.user_id = u.id
            LEFT JOIN journey_states js ON js.user_id = u.id
            WHERE u.id = :user_id
        """),
        {"user_id": user_id}
    )
    user_row = row.mappings().first()
    if not user_row:
        raise HTTPException(404, "User not found")

    raw_data = dict(user_row)
    # Convert enum to string for JSON serialization
    if raw_data.get("role") and hasattr(raw_data["role"], "value"):
        raw_data["role"] = raw_data["role"].value

    safe_data, redacted = sanitize_for_coach(raw_data)

    return {
        "profile": safe_data,
        "sanitized_fields": redacted,
        "access_level": auth["role"],
    }


# ===============================================================
# 2. Assessment summary
# ===============================================================

@router.get("/patient/{user_id}/assessments")
def get_patient_assessments(
    user_id: int,
    auth: dict = Depends(GatewayAuth("view_assessment_summary")),
    db: Session = Depends(get_db),
):
    """Coach views student assessment results — aggregated, no raw answers."""
    rows = db.execute(
        sa_text("""
            SELECT a.id, a.assessment_id, a.primary_concern,
                   a.risk_level, a.risk_score, a.primary_agent,
                   a.status, a.completed_at
            FROM assessments a
            WHERE a.user_id = :user_id
            ORDER BY a.completed_at DESC NULLS LAST
            LIMIT 20
        """),
        {"user_id": user_id}
    )
    results = []
    for r in rows.mappings().all():
        d = dict(r)
        # Convert enum values to strings
        for k in ("risk_level", "primary_agent"):
            if d.get(k) and hasattr(d[k], "value"):
                d[k] = d[k].value
        results.append(d)

    return {
        "assessments": results,
        "total": len(results),
        "note": "Only assessment summaries shown; raw answers are sanitized",
    }


# ===============================================================
# 3. Journey state
# ===============================================================

@router.get("/patient/{user_id}/journey")
def get_patient_journey(
    user_id: int,
    auth: dict = Depends(GatewayAuth("view_profile")),
    db: Session = Depends(get_db),
):
    """Coach views student growth journey."""
    row = db.execute(
        sa_text("""
            SELECT js.journey_stage, js.stage_entered_at,
                   js.agency_mode, js.agency_score, js.trust_score,
                   js.stability_days, js.stage_transition_count,
                   bp.current_stage AS bp_stage, bp.agency_mode AS bp_agency
            FROM journey_states js
            LEFT JOIN behavioral_profiles bp ON bp.user_id = js.user_id
            WHERE js.user_id = :user_id
        """),
        {"user_id": user_id}
    )
    journey = row.mappings().first()
    if not journey:
        raise HTTPException(404, "Journey data not found")

    return {"journey": dict(journey)}


# ===============================================================
# 4. Rx delivery
# ===============================================================

@router.post("/rx-delivery/{user_id}")
def deliver_rx(
    user_id: int,
    rx_data: dict,
    auth: dict = Depends(GatewayAuth("create_rx")),
    db: Session = Depends(get_db),
):
    """Deliver a reviewed prescription to the user."""
    rx_id = rx_data.get("rx_id") or rx_data.get("prescription_id")
    if not rx_id:
        raise HTTPException(400, "Missing rx_id")

    # Verify prescription exists and belongs to target user
    rx_row = db.execute(
        sa_text("""
            SELECT id, user_id, agent_type, is_active
            FROM coach_schema.rx_prescriptions
            WHERE id = :rx_id
        """),
        {"rx_id": rx_id}
    )
    rx = rx_row.mappings().first()
    if not rx:
        raise HTTPException(404, "Prescription not found")

    # Update status
    db.execute(
        sa_text("""
            UPDATE coach_schema.rx_prescriptions
            SET is_active = true, updated_at = NOW()
            WHERE id = :rx_id
        """),
        {"rx_id": rx_id}
    )

    log_cross_layer_access(
        db, auth["actor"].id, auth["role"], "deliver_rx",
        "professional", "assistant", "allowed",
        target_user_id=user_id,
        resource_type="rx_prescription",
        resource_id=str(rx_id),
    )
    db.commit()

    return {
        "delivered": True,
        "rx_id": str(rx_id),
        "user_id": user_id,
    }


# ===============================================================
# 5. Audit log
# ===============================================================

@router.get("/audit-log")
def get_audit_log(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    result_filter: Optional[str] = Query(None, alias="result"),
):
    """Cross-layer audit log — admin/supervisor only."""
    role = getattr(current_user, 'role', None)
    role_str = role.value if hasattr(role, 'value') else str(role) if role else 'unknown'
    if role_str not in ('admin', 'master', 'supervisor'):
        raise HTTPException(403, "Admin or supervisor required")

    conditions = []
    params = {"limit_val": page_size, "offset_val": (page - 1) * page_size}

    if action:
        conditions.append("action = :action")
        params["action"] = action
    if result_filter:
        conditions.append("result = :result")
        params["result"] = result_filter

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = db.execute(
        sa_text(f"""
            SELECT id, timestamp, actor_id, actor_role, target_user_id,
                   action, layer_from, layer_to, result, denial_reason
            FROM cross_layer_audit_log
            {where}
            ORDER BY timestamp DESC
            LIMIT :limit_val OFFSET :offset_val
        """),
        params,
    )

    count_row = db.execute(
        sa_text(f"SELECT COUNT(*) FROM cross_layer_audit_log {where}"),
        params,
    )

    return {
        "logs": [dict(r) for r in rows.mappings().all()],
        "total": count_row.scalar(),
        "page": page,
        "page_size": page_size,
    }


# ===============================================================
# 6. Coach bindings list
# ===============================================================

@router.get("/bindings")
def get_my_bindings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    active_only: bool = True,
):
    """Coach views their student binding list."""
    role = getattr(current_user, 'role', None)
    role_str = role.value if hasattr(role, 'value') else str(role) if role else 'unknown'
    if role_str not in ('coach', 'promoter', 'supervisor', 'master', 'admin'):
        raise HTTPException(403, "Coach or above required")

    active_filter = "AND csb.is_active = true" if active_only else ""

    rows = db.execute(
        sa_text(f"""
            SELECT csb.student_id, csb.binding_type, csb.bound_at,
                   csb.permissions, csb.is_active,
                   u.username, u.avatar_url
            FROM coach_schema.coach_student_bindings csb
            JOIN users u ON u.id = csb.student_id
            WHERE csb.coach_id = :coach_id
            {active_filter}
            ORDER BY csb.bound_at DESC
        """),
        {"coach_id": current_user.id}
    )

    return {
        "bindings": [dict(r) for r in rows.mappings().all()],
        "coach_id": current_user.id,
    }

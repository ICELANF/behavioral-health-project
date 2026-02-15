# -*- coding: utf-8 -*-
"""
V4.1 Cross-Layer Authorization - coach access to user data

Rules:
  - Coach: only bound students (via coach_student_bindings)
  - Supervisor: 2-level (supervisor -> coaches -> students)
  - Admin/Master: full access
  - Every cross-layer access is audit-logged
"""
from __future__ import annotations
import uuid
import json
from typing import Optional

from fastapi import Depends, HTTPException, Request
from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session

from core.database import get_db
from api.dependencies import get_current_user
from core.models import User


# ===============================================================
# Binding checks
# ===============================================================

def check_coach_binding(
    coach_id: int,
    student_id: int,
    db: Session,
    required_permission: str = "view_profile",
) -> dict | None:
    """Check if coach has binding + permission for this student."""
    row = db.execute(
        sa_text("""
            SELECT id, coach_id, student_id, binding_type, permissions, is_active
            FROM coach_schema.coach_student_bindings
            WHERE coach_id = :coach_id
            AND student_id = :student_id
            AND is_active = true
            LIMIT 1
        """),
        {"coach_id": coach_id, "student_id": student_id}
    )
    binding = row.mappings().first()
    if not binding:
        return None

    perms = binding.get("permissions") or {}
    if isinstance(perms, str):
        perms = json.loads(perms)
    if required_permission and not perms.get(required_permission, False):
        return None

    return dict(binding)


def check_supervisor_binding(
    supervisor_id: int,
    student_id: int,
    db: Session,
) -> bool:
    """Supervisor 2-level auth: supervisor -> coaches -> students."""
    row = db.execute(
        sa_text("""
            SELECT EXISTS(
                SELECT 1
                FROM coach_schema.coach_supervision_records sr
                JOIN coach_schema.coach_student_bindings csb
                    ON sr.coach_id = csb.coach_id
                WHERE sr.supervisor_id = :supervisor_id
                AND csb.student_id = :student_id
                AND csb.is_active = true
            )
        """),
        {"supervisor_id": supervisor_id, "student_id": student_id}
    )
    return row.scalar() or False


# ===============================================================
# Audit log
# ===============================================================

def log_cross_layer_access(
    db: Session,
    actor_id: int,
    actor_role: str,
    action: str,
    layer_from: str,
    layer_to: str,
    result: str,
    target_user_id: int | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    sanitized_fields: list | None = None,
    denial_reason: str | None = None,
    ip_address: str | None = None,
    metadata: dict | None = None,
):
    """Write cross-layer audit log entry."""
    db.execute(
        sa_text("""
            INSERT INTO cross_layer_audit_log
                (id, actor_id, actor_role, target_user_id, action,
                 layer_from, layer_to, resource_type, resource_id,
                 sanitized_fields, result, denial_reason, ip_address, metadata)
            VALUES
                (:id, :actor_id, :actor_role, :target_user_id, :action,
                 :layer_from, :layer_to, :resource_type, :resource_id,
                 :sanitized_fields, :result, :denial_reason, :ip_address, :metadata)
        """),
        {
            "id": str(uuid.uuid4()),
            "actor_id": actor_id,
            "actor_role": actor_role,
            "target_user_id": target_user_id,
            "action": action,
            "layer_from": layer_from,
            "layer_to": layer_to,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "sanitized_fields": json.dumps(sanitized_fields) if sanitized_fields else None,
            "result": result,
            "denial_reason": denial_reason,
            "ip_address": ip_address,
            "metadata": json.dumps(metadata) if metadata else None,
        }
    )


# ===============================================================
# FastAPI Dependency
# ===============================================================

class GatewayAuth:
    """
    Gateway authorization dependency for cross-layer routes.

    Usage:
        @router.get("/patient/{user_id}/profile")
        def get_profile(
            user_id: int,
            auth: dict = Depends(GatewayAuth("view_profile")),
            db: Session = Depends(get_db),
        ):
            ...
    """

    def __init__(self, required_permission: str = "view_profile"):
        self.required_permission = required_permission

    def __call__(
        self,
        request: Request,
        user_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict:
        actor_role = getattr(current_user, 'role', None)
        if actor_role:
            actor_role = actor_role.value if hasattr(actor_role, 'value') else str(actor_role)
        else:
            actor_role = 'unknown'
        ip = request.client.host if request.client else None

        # Admin/Master: pass through
        if actor_role in ('admin', 'master'):
            log_cross_layer_access(
                db, current_user.id, actor_role, self.required_permission,
                "professional", "assistant", "allowed",
                target_user_id=user_id, ip_address=ip,
            )
            db.commit()
            return {"actor": current_user, "role": actor_role, "binding": None}

        # Coach: check binding
        if actor_role in ('coach', 'promoter', 'supervisor'):
            binding = check_coach_binding(
                current_user.id, user_id, db, self.required_permission
            )
            if binding:
                log_cross_layer_access(
                    db, current_user.id, actor_role, self.required_permission,
                    "professional", "assistant", "allowed",
                    target_user_id=user_id, ip_address=ip,
                )
                db.commit()
                return {"actor": current_user, "role": actor_role, "binding": binding}

        # Supervisor: 2-level
        if actor_role in ('supervisor', 'master'):
            ok = check_supervisor_binding(current_user.id, user_id, db)
            if ok:
                log_cross_layer_access(
                    db, current_user.id, actor_role, self.required_permission,
                    "professional", "assistant", "allowed",
                    target_user_id=user_id, ip_address=ip,
                )
                db.commit()
                return {"actor": current_user, "role": actor_role, "binding": None}

        # Denied
        log_cross_layer_access(
            db, current_user.id, actor_role, self.required_permission,
            "professional", "assistant", "denied",
            target_user_id=user_id,
            denial_reason=f"no {self.required_permission} or no binding",
            ip_address=ip,
        )
        db.commit()
        raise HTTPException(403, f"No access to this user (need {self.required_permission})")

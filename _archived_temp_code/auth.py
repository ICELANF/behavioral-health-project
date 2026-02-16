"""
V4.1 跨层授权 — 教练访问用户数据的权限校验

规则 (Sheet⑤ + Sheet⑫):
  - 教练只能访问有绑定关系的学员数据
  - 督导可以访问下属教练的所有学员数据
  - Admin可以访问所有数据
  - 用户层Agent永远不能访问教练层数据
  - 每次跨层访问都写审计日志
"""
from __future__ import annotations
import uuid
from typing import Optional
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

# 根据你的实际路径调整这些import
from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User


# ═══════════════════════════════════════════════════════════
# 绑定关系查询
# ═══════════════════════════════════════════════════════════

async def check_coach_binding(
    coach_id: uuid.UUID,
    student_id: uuid.UUID,
    db: AsyncSession,
    required_permission: str = "view_profile",
) -> dict | None:
    """
    检查教练是否有权访问该学员

    Returns:
        绑定记录dict (含permissions), 或 None(无权)
    """
    result = await db.execute(
        select("*").select_from(
            # 使用text指定schema
            db.execute(f"""
                SELECT id, coach_id, student_id, binding_type, permissions, is_active
                FROM coach_schema.coach_student_bindings
                WHERE coach_id = :coach_id
                AND student_id = :student_id
                AND is_active = true
                LIMIT 1
            """, {"coach_id": str(coach_id), "student_id": str(student_id)})
        )
    )
    # 简化版: 直接SQL查询
    row = await db.execute(
        sa_text("""
            SELECT id, coach_id, student_id, binding_type, permissions, is_active
            FROM coach_schema.coach_student_bindings
            WHERE coach_id = :coach_id
            AND student_id = :student_id
            AND is_active = true
            LIMIT 1
        """),
        {"coach_id": str(coach_id), "student_id": str(student_id)}
    )
    binding = row.mappings().first()
    if not binding:
        return None

    # 检查具体权限
    perms = binding.get("permissions") or {}
    if required_permission and not perms.get(required_permission, False):
        return None

    return dict(binding)


async def check_supervisor_binding(
    supervisor_id: uuid.UUID,
    student_id: uuid.UUID,
    db: AsyncSession,
) -> bool:
    """
    督导二级授权: supervisor → coaches → students
    督导可以访问其下属教练的所有学员
    """
    row = await db.execute(
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
        {"supervisor_id": str(supervisor_id), "student_id": str(student_id)}
    )
    return row.scalar() or False


# ═══════════════════════════════════════════════════════════
# 审计日志
# ═══════════════════════════════════════════════════════════

async def log_cross_layer_access(
    db: AsyncSession,
    actor_id: uuid.UUID,
    actor_role: str,
    action: str,
    layer_from: str,
    layer_to: str,
    result: str,
    target_user_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    sanitized_fields: list | None = None,
    denial_reason: str | None = None,
    ip_address: str | None = None,
    metadata: dict | None = None,
):
    """记录跨层访问日志"""
    import json
    await db.execute(
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
            "actor_id": str(actor_id),
            "actor_role": actor_role,
            "target_user_id": str(target_user_id) if target_user_id else None,
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


# ═══════════════════════════════════════════════════════════
# FastAPI Dependencies — 直接在路由中使用
# ═══════════════════════════════════════════════════════════

from sqlalchemy import text as sa_text


class GatewayAuth:
    """
    网关授权依赖 — 用于跨层路由

    用法:
        @router.get("/patient/{user_id}/profile")
        async def get_patient_profile(
            user_id: str,
            auth: dict = Depends(GatewayAuth("view_profile")),
            db: AsyncSession = Depends(get_db),
        ):
            # auth = {"actor": User, "binding": {...}, "role": "coach"}
            ...
    """

    def __init__(self, required_permission: str = "view_profile"):
        self.required_permission = required_permission

    async def __call__(
        self,
        request: Request,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ) -> dict:
        # 从路径参数获取目标用户ID
        user_id_str = request.path_params.get("user_id")
        if not user_id_str:
            raise HTTPException(400, "缺少目标用户ID")

        try:
            target_user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise HTTPException(400, "无效的用户ID格式")

        actor_role = getattr(current_user, 'role', 'unknown')
        ip = request.client.host if request.client else None

        # Admin: 直接放行
        if actor_role in ('admin', 'master'):
            await log_cross_layer_access(
                db, current_user.id, actor_role, self.required_permission,
                "professional", "assistant", "allowed",
                target_user_id=target_user_id, ip_address=ip,
            )
            return {"actor": current_user, "role": actor_role, "binding": None}

        # Coach: 检查绑定关系
        if actor_role in ('coach', 'facilitator'):
            binding = await check_coach_binding(
                current_user.id, target_user_id, db, self.required_permission
            )
            if binding:
                await log_cross_layer_access(
                    db, current_user.id, actor_role, self.required_permission,
                    "professional", "assistant", "allowed",
                    target_user_id=target_user_id, ip_address=ip,
                )
                return {"actor": current_user, "role": actor_role, "binding": binding}

        # Supervisor: 二级授权
        if actor_role in ('supervisor', 'expert'):
            ok = await check_supervisor_binding(current_user.id, target_user_id, db)
            if ok:
                await log_cross_layer_access(
                    db, current_user.id, actor_role, self.required_permission,
                    "professional", "assistant", "allowed",
                    target_user_id=target_user_id, ip_address=ip,
                )
                return {"actor": current_user, "role": actor_role, "binding": None}

        # 拒绝
        await log_cross_layer_access(
            db, current_user.id, actor_role, self.required_permission,
            "professional", "assistant", "denied",
            target_user_id=target_user_id,
            denial_reason=f"无{self.required_permission}权限或无绑定关系",
            ip_address=ip,
        )
        raise HTTPException(403, f"无权访问该用户数据 (需要 {self.required_permission})")

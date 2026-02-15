"""
V4.2 绑定管理API — Admin端点

功能:
  1. CRUD — 创建/查询/更新/解绑 教练-学员关系
  2. 批量操作 — 批量绑定/解绑
  3. 统计 — 教练负载、绑定分布
  4. 审计 — 所有操作写 cross_layer_audit_log

权限: Admin/Master only（教练不能自行绑定学员）

路由前缀: /v1/admin/bindings
"""
from __future__ import annotations
import json
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session

from core.database import get_db
from api.dependencies import get_current_user, require_admin
from core.models import User

router = APIRouter(prefix="/v1/admin/bindings", tags=["admin_bindings"])


# ═══════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════

class BindingCreate(BaseModel):
    coach_id: int = Field(..., description="教练用户ID")
    student_id: int = Field(..., description="学员用户ID")
    binding_type: str = Field("assigned", description="绑定类型: assigned|program|challenge|self_selected")
    permissions: Optional[dict] = Field(None, description="权限覆盖，不填用默认")

class BindingUpdate(BaseModel):
    permissions: Optional[dict] = None
    binding_type: Optional[str] = None
    is_active: Optional[bool] = None

class BatchBindRequest(BaseModel):
    coach_id: int
    student_ids: List[int] = Field(..., min_length=1, max_length=50)
    binding_type: str = "assigned"

class BatchUnbindRequest(BaseModel):
    binding_ids: List[str] = Field(..., min_length=1, max_length=50, description="绑定记录ID列表")
    reason: Optional[str] = None

DEFAULT_PERMISSIONS = {
    "view_profile": True,
    "view_assessment_summary": True,
    "view_chat_summary": False,
    "send_message": True,
    "create_rx": True,
}


# ═══════════════════════════════════════════════════════════
# 审计辅助
# ═══════════════════════════════════════════════════════════

def _audit(db: Session, actor_id, action: str, detail: dict):
    try:
        db.execute(
            sa_text("""
                INSERT INTO cross_layer_audit_log
                    (id, actor_id, actor_role, action, layer_from, layer_to,
                     resource_type, result, metadata, timestamp)
                VALUES
                    (gen_random_uuid(), :actor_id, 'admin', :action,
                     'gateway', 'professional', 'binding', 'allowed',
                     :metadata, NOW())
            """),
            {"actor_id": str(actor_id), "action": action, "metadata": json.dumps(detail)}
        )
    except Exception:
        pass  # 审计失败不阻塞主操作


# ═══════════════════════════════════════════════════════════
# 1. 创建绑定
# ═══════════════════════════════════════════════════════════

@router.post("")
def create_binding(
    req: BindingCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """创建教练-学员绑定"""
    # 验证教练和学员存在
    coach = db.execute(sa_text("SELECT id, role FROM users WHERE id = :id"), {"id": req.coach_id})
    coach_row = coach.mappings().first()
    if not coach_row:
        raise HTTPException(404, f"教练 {req.coach_id} 不存在")
    role_val = coach_row["role"]
    if hasattr(role_val, "value"):
        role_val = role_val.value
    role_str = str(role_val).lower()
    if role_str not in ("coach", "facilitator", "supervisor", "expert", "admin", "master", "promoter"):
        raise HTTPException(400, f"用户 {req.coach_id} 不是教练角色 (当前: {role_str})")

    student = db.execute(sa_text("SELECT id FROM users WHERE id = :id"), {"id": req.student_id})
    if not student.mappings().first():
        raise HTTPException(404, f"学员 {req.student_id} 不存在")

    # 检查重复
    existing = db.execute(
        sa_text("""
            SELECT id FROM coach_schema.coach_student_bindings
            WHERE coach_id = :cid AND student_id = :sid AND binding_type = :bt AND is_active = true
        """),
        {"cid": req.coach_id, "sid": req.student_id, "bt": req.binding_type}
    )
    if existing.mappings().first():
        raise HTTPException(409, "该绑定关系已存在")

    permissions = req.permissions or DEFAULT_PERMISSIONS

    result = db.execute(
        sa_text("""
            INSERT INTO coach_schema.coach_student_bindings
                (id, coach_id, student_id, binding_type, permissions, is_active, bound_at, created_at, updated_at)
            VALUES
                (gen_random_uuid(), :cid, :sid, :bt, :perms, true, NOW(), NOW(), NOW())
            RETURNING id, coach_id, student_id, binding_type, bound_at
        """),
        {"cid": req.coach_id, "sid": req.student_id, "bt": req.binding_type, "perms": json.dumps(permissions)}
    )
    row = result.mappings().first()

    _audit(db, current_user.id, "create_binding", {
        "coach_id": req.coach_id, "student_id": req.student_id, "type": req.binding_type
    })
    db.commit()

    return {"binding": dict(row), "permissions": permissions}


# ═══════════════════════════════════════════════════════════
# 2. 查询绑定
# ═══════════════════════════════════════════════════════════

@router.get("")
def list_bindings(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    coach_id: Optional[int] = None,
    student_id: Optional[int] = None,
    binding_type: Optional[str] = None,
    active_only: bool = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """查询绑定列表"""
    conditions = []
    params = {"limit": page_size, "offset": (page - 1) * page_size}

    if coach_id:
        conditions.append("csb.coach_id = :coach_id")
        params["coach_id"] = coach_id
    if student_id:
        conditions.append("csb.student_id = :student_id")
        params["student_id"] = student_id
    if binding_type:
        conditions.append("csb.binding_type = :binding_type")
        params["binding_type"] = binding_type
    if active_only:
        conditions.append("csb.is_active = true")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    rows = db.execute(
        sa_text(f"""
            SELECT csb.id, csb.coach_id, csb.student_id, csb.binding_type,
                   csb.permissions, csb.is_active, csb.bound_at, csb.unbound_at,
                   c.username as coach_name, s.username as student_name
            FROM coach_schema.coach_student_bindings csb
            LEFT JOIN users c ON c.id = csb.coach_id
            LEFT JOIN users s ON s.id = csb.student_id
            {where}
            ORDER BY csb.bound_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    )

    count_row = db.execute(
        sa_text(f"SELECT COUNT(*) FROM coach_schema.coach_student_bindings csb {where}"),
        params,
    )

    bindings = [dict(r) for r in rows.mappings().all()]
    for b in bindings:
        if isinstance(b.get("permissions"), str):
            try:
                b["permissions"] = json.loads(b["permissions"])
            except Exception:
                pass

    return {
        "bindings": bindings,
        "total": count_row.scalar(),
        "page": page,
        "page_size": page_size,
    }


@router.get("/stats/overview")
def binding_stats(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """绑定统计总览"""
    row = db.execute(sa_text("""
        SELECT
            COUNT(*) as total_bindings,
            COUNT(*) FILTER (WHERE is_active = true) as active_bindings,
            COUNT(*) FILTER (WHERE is_active = false) as inactive_bindings,
            COUNT(DISTINCT coach_id) FILTER (WHERE is_active = true) as active_coaches,
            COUNT(DISTINCT student_id) FILTER (WHERE is_active = true) as active_students
        FROM coach_schema.coach_student_bindings
    """))
    stats = dict(row.mappings().first())

    type_rows = db.execute(sa_text("""
        SELECT binding_type, COUNT(*) as count
        FROM coach_schema.coach_student_bindings
        WHERE is_active = true
        GROUP BY binding_type
    """))
    stats["by_type"] = {r["binding_type"]: r["count"] for r in type_rows.mappings().all()}

    return {"stats": stats}


@router.get("/stats/coach-load")
def coach_load(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
    min_students: int = 0,
):
    """教练负载 — 每个教练带多少学员"""
    rows = db.execute(
        sa_text("""
            SELECT csb.coach_id, u.username as coach_name,
                   COUNT(csb.student_id) as student_count
            FROM coach_schema.coach_student_bindings csb
            JOIN users u ON u.id = csb.coach_id
            WHERE csb.is_active = true
            GROUP BY csb.coach_id, u.username
            HAVING COUNT(csb.student_id) >= :min
            ORDER BY student_count DESC
        """),
        {"min": min_students}
    )
    return {"coaches": [dict(r) for r in rows.mappings().all()]}


@router.get("/{binding_id}")
def get_binding(
    binding_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """获取单个绑定详情"""
    row = db.execute(
        sa_text("""
            SELECT csb.*, c.username as coach_name, s.username as student_name
            FROM coach_schema.coach_student_bindings csb
            LEFT JOIN users c ON c.id = csb.coach_id
            LEFT JOIN users s ON s.id = csb.student_id
            WHERE csb.id = :bid
        """),
        {"bid": binding_id}
    )
    binding = row.mappings().first()
    if not binding:
        raise HTTPException(404, "绑定不存在")
    return {"binding": dict(binding)}


# ═══════════════════════════════════════════════════════════
# 3. 更新绑定
# ═══════════════════════════════════════════════════════════

@router.put("/{binding_id}")
def update_binding(
    binding_id: str,
    req: BindingUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """更新绑定（权限/类型/状态）"""
    existing = db.execute(
        sa_text("SELECT id FROM coach_schema.coach_student_bindings WHERE id = :bid"),
        {"bid": binding_id}
    )
    if not existing.mappings().first():
        raise HTTPException(404, "绑定不存在")

    updates = []
    params = {"bid": binding_id}

    if req.permissions is not None:
        updates.append("permissions = :perms")
        params["perms"] = json.dumps(req.permissions)
    if req.binding_type is not None:
        updates.append("binding_type = :bt")
        params["bt"] = req.binding_type
    if req.is_active is not None:
        updates.append("is_active = :active")
        params["active"] = req.is_active
        if not req.is_active:
            updates.append("unbound_at = NOW()")

    if not updates:
        raise HTTPException(400, "无更新内容")

    updates.append("updated_at = NOW()")

    db.execute(
        sa_text(f"UPDATE coach_schema.coach_student_bindings SET {', '.join(updates)} WHERE id = :bid"),
        params,
    )

    _audit(db, current_user.id, "update_binding", {"binding_id": binding_id, "changes": req.model_dump(exclude_none=True)})
    db.commit()

    return {"updated": True, "binding_id": binding_id}


# ═══════════════════════════════════════════════════════════
# 4. 解绑（软删除）
# ═══════════════════════════════════════════════════════════

@router.delete("/{binding_id}")
def unbind(
    binding_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """解绑（软删除，保留记录）"""
    result = db.execute(
        sa_text("""
            UPDATE coach_schema.coach_student_bindings
            SET is_active = false, unbound_at = NOW(), updated_at = NOW()
            WHERE id = :bid AND is_active = true
            RETURNING coach_id, student_id
        """),
        {"bid": binding_id}
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(404, "绑定不存在或已解绑")

    _audit(db, current_user.id, "unbind", {
        "binding_id": binding_id, "coach_id": row["coach_id"], "student_id": row["student_id"]
    })
    db.commit()

    return {"unbound": True, "binding_id": binding_id}


# ═══════════════════════════════════════════════════════════
# 5. 批量绑定
# ═══════════════════════════════════════════════════════════

@router.post("/batch")
def batch_bind(
    req: BatchBindRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """批量绑定学员到教练"""
    coach = db.execute(sa_text("SELECT id, role FROM users WHERE id = :id"), {"id": req.coach_id})
    if not coach.mappings().first():
        raise HTTPException(404, f"教练 {req.coach_id} 不存在")

    created = 0
    skipped = 0
    errors = []

    for sid in req.student_ids:
        try:
            student = db.execute(sa_text("SELECT id FROM users WHERE id = :id"), {"id": sid})
            if not student.mappings().first():
                errors.append({"student_id": sid, "error": "学员不存在"})
                continue

            existing = db.execute(
                sa_text("""
                    SELECT id FROM coach_schema.coach_student_bindings
                    WHERE coach_id = :cid AND student_id = :sid AND binding_type = :bt AND is_active = true
                """),
                {"cid": req.coach_id, "sid": sid, "bt": req.binding_type}
            )
            if existing.mappings().first():
                skipped += 1
                continue

            db.execute(
                sa_text("""
                    INSERT INTO coach_schema.coach_student_bindings
                        (id, coach_id, student_id, binding_type, permissions, is_active, bound_at, created_at, updated_at)
                    VALUES
                        (gen_random_uuid(), :cid, :sid, :bt, :perms, true, NOW(), NOW(), NOW())
                """),
                {"cid": req.coach_id, "sid": sid, "bt": req.binding_type, "perms": json.dumps(DEFAULT_PERMISSIONS)}
            )
            created += 1

        except Exception as e:
            errors.append({"student_id": sid, "error": str(e)[:100]})

    _audit(db, current_user.id, "batch_bind", {
        "coach_id": req.coach_id, "total": len(req.student_ids),
        "created": created, "skipped": skipped, "errors": len(errors)
    })
    db.commit()

    return {"created": created, "skipped": skipped, "errors": errors}


# ═══════════════════════════════════════════════════════════
# 6. 批量解绑
# ═══════════════════════════════════════════════════════════

@router.post("/batch-unbind")
def batch_unbind(
    req: BatchUnbindRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """批量解绑"""
    unbound = 0
    for bid in req.binding_ids:
        result = db.execute(
            sa_text("""
                UPDATE coach_schema.coach_student_bindings
                SET is_active = false, unbound_at = NOW(), updated_at = NOW()
                WHERE id = :bid AND is_active = true
            """),
            {"bid": bid}
        )
        if result.rowcount > 0:
            unbound += 1

    _audit(db, current_user.id, "batch_unbind", {
        "total": len(req.binding_ids), "unbound": unbound, "reason": req.reason
    })
    db.commit()

    return {"unbound": unbound, "total": len(req.binding_ids), "reason": req.reason}

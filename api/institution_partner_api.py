"""
institution_api.py + partner_api.py — 机构合作 & 合伙人体系 API

institution 路由前缀: /api/v1/institutions
partner    路由前缀: /api/v1/partners
"""
from __future__ import annotations

import json
import secrets
import string
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user, require_roles
from core.database import get_async_db as get_db
from core.models import User, UserRole

# ══════════════════════════════════════════════════════════════════
# 机构合作 API
# ══════════════════════════════════════════════════════════════════

institution_router = APIRouter(
    prefix="/api/v1/institutions",
    tags=["机构合作"]
)


# ─────────────────────────────────────────────────────────────────
# Pydantic 模型
# ─────────────────────────────────────────────────────────────────

class InstitutionRegisterRequest(BaseModel):
    tenant_name: str = Field(..., min_length=2, max_length=100)
    institution_type: str = Field(
        ..., description="school/hospital/corporate"
    )
    contact_name: str
    contact_phone: str
    contact_email: str
    region: Optional[str] = None
    student_count: Optional[int] = None
    health_focus: list[str] = Field(default_factory=list,
        description="如 ['vision', 'metabolism']")
    referral_code: Optional[str] = None  # 合伙人邀请码


class InstitutionConfig(BaseModel):
    brand_color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    welcome_message: Optional[str] = None
    data_return_enabled: bool = False
    max_users: Optional[int] = Field(None, ge=10, le=10000)
    domain_whitelist: list[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────
# 1. 机构注册（申请）
# ─────────────────────────────────────────────────────────────────

@institution_router.post("/register")
async def register_institution(
    body: InstitutionRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """机构注册申请（公开端点，不需要认证）"""
    # 验证合伙人邀请码
    partner_id = None
    if body.referral_code:
        partner_row = await db.execute(text("""
            SELECT partner_user_id
            FROM partner_configs
            WHERE referral_code = :code
              AND status = 'active'
              AND (contract_end IS NULL OR contract_end > CURRENT_DATE)
            LIMIT 1
        """), {"code": body.referral_code})
        partner = partner_row.mappings().first()
        if not partner:
            raise HTTPException(status_code=400, detail="邀请码无效或已过期")
        partner_id = partner["partner_user_id"]

    institution_config = {
        "institution_type": body.institution_type,
        "contact": {
            "name": body.contact_name,
            "phone": body.contact_phone,
            "email": body.contact_email,
        },
        "student_count": body.student_count,
        "health_focus": body.health_focus,
        "registration_status": "pending",
    }
    if partner_id:
        institution_config["referred_by_partner"] = str(partner_id)

    result = await db.execute(text("""
        INSERT INTO tenants
            (tenant_name, tenant_type, institution_config,
             status, region)
        VALUES
            (:name, 'institution',
             CAST(:config AS jsonb), 'pending', :region)
        RETURNING id
    """), {
        "name": body.tenant_name,
        "config": json.dumps(institution_config, ensure_ascii=False),
        "region": body.region,
    })
    new_id = result.scalar()
    await db.commit()

    return {
        "tenant_id": str(new_id),
        "message": "机构注册申请已提交，等待平台审核（通常1-3个工作日）",
        "application_number": f"INST-{str(new_id)[:8].upper()}",
    }


@institution_router.post("/create")
async def create_institution_by_admin(
    body: InstitutionRegisterRequest,
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MASTER])
    ),
    db: AsyncSession = Depends(get_db),
):
    """Admin 直接创建并激活机构租户"""
    institution_config = {
        "institution_type": body.institution_type,
        "contact": {
            "name": body.contact_name,
            "phone": body.contact_phone,
            "email": body.contact_email,
        },
        "student_count": body.student_count,
        "health_focus": body.health_focus,
        "registration_status": "approved",
        "approved_by": str(current_user.id),
    }

    result = await db.execute(text("""
        INSERT INTO tenants
            (tenant_name, tenant_type, institution_config,
             status, region, max_users)
        VALUES
            (:name, 'institution',
             CAST(:config AS jsonb), 'active', :region, :max_users)
        RETURNING id, tenant_name
    """), {
        "name": body.tenant_name,
        "config": json.dumps(institution_config, ensure_ascii=False),
        "region": body.region,
        "max_users": body.student_count or 500,
    })
    row = result.mappings().first()
    await db.commit()

    return {
        "tenant_id": str(row["id"]),
        "tenant_name": row["tenant_name"],
        "status": "active",
        "message": "机构已创建并激活",
    }


# ─────────────────────────────────────────────────────────────────
# 2. 机构驾驶舱数据
# ─────────────────────────────────────────────────────────────────

@institution_router.get("/{institution_id}/dashboard")
async def get_institution_dashboard(
    institution_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """机构管理驾驶舱（InstitutionAdmin + Admin 可访问）"""
    # 权限检查：INSTITUTION_ADMIN 只能查自己机构
    if current_user.role not in (UserRole.ADMIN, UserRole.MASTER, UserRole.SUPERVISOR):
        inst_check = await db.execute(text("""
            SELECT 1 FROM users
            WHERE id = CAST(:uid AS INTEGER)
              AND tenant_id = CAST(:iid AS UUID)
              AND role = 'INSTITUTION_ADMIN'
        """), {"uid": str(current_user.id), "iid": str(institution_id)})
        if not inst_check.first():
            raise HTTPException(status_code=403, detail="无权访问此机构数据")

    # 机构基本信息
    inst = await db.execute(text("""
        SELECT tenant_name, tenant_type, status,
               institution_config, max_users, created_at
        FROM tenants
        WHERE id = CAST(:iid AS UUID)
          AND tenant_type = 'institution'
        LIMIT 1
    """), {"iid": str(institution_id)})
    institution = inst.mappings().first()
    if not institution:
        raise HTTPException(status_code=404, detail="机构不存在")

    # 用户规模统计
    user_stats = await db.execute(text("""
        SELECT
            COUNT(*) AS total_users,
            COUNT(*) FILTER (WHERE role = 'OBSERVER') AS observers,
            COUNT(*) FILTER (WHERE role = 'GROWER') AS growers,
            COUNT(*) FILTER (WHERE role = 'SHARER') AS sharers,
            COUNT(*) FILTER (
                WHERE last_active_at >= NOW() - INTERVAL '30 days'
            ) AS monthly_active
        FROM users
        WHERE tenant_id = CAST(:iid AS UUID)
          AND is_active = TRUE
    """), {"iid": str(institution_id)})
    users = dict(user_stats.mappings().first() or {})

    # 关联 Expert 和 Coach 数量
    resource_stats = await db.execute(text("""
        SELECT
            (SELECT COUNT(*) FROM expert_patient_bindings
             WHERE institution_id = CAST(:iid AS UUID)
               AND status = 'active') AS active_expert_bindings,
            (SELECT COUNT(DISTINCT coach_id) FROM coach_student_bindings csb
             JOIN users u ON u.id = csb.student_id
             WHERE u.tenant_id = CAST(:iid AS UUID)
               AND csb.status = 'active') AS active_coaches
    """), {"iid": str(institution_id)})
    resources = dict(resource_stats.mappings().first() or {})

    # VisionGuard 统计（若机构有此域）
    config = institution.get("institution_config") or {}
    health_focus = config.get("health_focus", [])

    vision_stats = {}
    if "vision" in health_focus:
        vs = await db.execute(text("""
            SELECT
                COUNT(*) AS total_profiles,
                COUNT(*) FILTER (WHERE risk_level = 'normal') AS normal_count,
                COUNT(*) FILTER (WHERE risk_level = 'watch') AS watch_count,
                COUNT(*) FILTER (WHERE risk_level = 'alert') AS alert_count,
                COUNT(*) FILTER (WHERE risk_level = 'urgent') AS urgent_count
            FROM vision_profiles vp
            JOIN users u ON u.id = vp.user_id
            WHERE u.tenant_id = CAST(:iid AS UUID)
        """), {"iid": str(institution_id)})
        vision_stats = dict(vs.mappings().first() or {})

    return {
        "institution": dict(institution),
        "user_stats": users,
        "resources": resources,
        "vision_stats": vision_stats if vision_stats else None,
        "health_focus": health_focus,
    }


@institution_router.get("/{institution_id}/report")
async def get_institution_report(
    institution_id: UUID,
    period_start: str = Query(..., description="格式: 2026-01-01"),
    period_end: str = Query(..., description="格式: 2026-12-31"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """生成机构报告（JSON格式，可由前端转为PDF）"""
    # 权限检查（同 dashboard）
    if current_user.role not in (UserRole.ADMIN, UserRole.MASTER):
        raise HTTPException(status_code=403, detail="需要管理员权限")

    # 行为达标统计
    behavior_stats = await db.execute(text("""
        SELECT
            AVG(behavior_score) AS avg_behavior_score,
            COUNT(*) FILTER (WHERE behavior_score >= 60) AS above_passing,
            COUNT(*) AS total_records
        FROM vision_behavior_logs vbl
        JOIN users u ON u.id = vbl.user_id
        WHERE u.tenant_id = CAST(:iid AS UUID)
          AND vbl.log_date BETWEEN CAST(:start AS date) AND CAST(:end AS date)
    """), {
        "iid": str(institution_id),
        "start": period_start,
        "end": period_end,
    })
    behavior = dict(behavior_stats.mappings().first() or {})

    return {
        "institution_id": str(institution_id),
        "period": {"start": period_start, "end": period_end},
        "behavior_stats": behavior,
        "generated_at": "now",
        "_note": "此数据可通过前端 PDF 导出功能输出完整报告",
    }


@institution_router.post("/{institution_id}/admins/invite")
async def invite_institution_admin(
    institution_id: UUID,
    user_id: UUID,
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MASTER])
    ),
    db: AsyncSession = Depends(get_db),
):
    """邀请用户成为机构管理员（InstitutionAdmin）"""
    await db.execute(text("""
        UPDATE users
        SET role = 'INSTITUTION_ADMIN',
            tenant_id = CAST(:iid AS UUID)
        WHERE id = CAST(:uid AS INTEGER)
    """), {"iid": str(institution_id), "uid": str(user_id)})
    await db.commit()
    return {"message": "机构管理员已设置"}


# ─────────────────────────────────────────────────────────────────
# 3. 机构批量学生导入（复用已有 batch_ingestion 逻辑）
# ─────────────────────────────────────────────────────────────────

class BatchEnrollRequest(BaseModel):
    institution_id: UUID
    users: list[dict] = Field(..., description="[{username, name, grade, class}]")
    send_activation_sms: bool = True


@institution_router.post("/vision/batch-enroll")
async def batch_enroll_students(
    body: BatchEnrollRequest,
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MASTER, UserRole.INSTITUTION_ADMIN])
    ),
    db: AsyncSession = Depends(get_db),
):
    """批量导入学生到 VisionGuard 机构（Observer角色）"""
    created = []
    failed = []

    for user_data in body.users:
        try:
            username = user_data.get("username") or user_data.get("name", "")
            if not username:
                continue

            # 生成临时密码
            temp_pwd = "Vision" + "".join(
                secrets.choice(string.digits) for _ in range(6)
            ) + "@"

            result = await db.execute(text("""
                INSERT INTO users
                    (username, email, role, is_active, tenant_id,
                     hashed_password)
                VALUES
                    (:username,
                     :email,
                     'OBSERVER',
                     TRUE,
                     CAST(:tenant_id AS UUID),
                     :pwd)
                ON CONFLICT (username) DO NOTHING
                RETURNING id, username
            """), {
                "username": username,
                "email": user_data.get("email", f"{username}@school.local"),
                "tenant_id": str(body.institution_id),
                "pwd": f"TEMP:{temp_pwd}",  # 实际应用 bcrypt hash
            })

            row = result.mappings().first()
            if row:
                created.append({
                    "user_id": str(row["id"]),
                    "username": row["username"],
                    "temp_password": temp_pwd if body.send_activation_sms else "***",
                    "grade": user_data.get("grade"),
                    "class": user_data.get("class"),
                })
        except Exception as e:
            failed.append({"data": user_data, "error": str(e)})

    await db.commit()

    return {
        "created_count": len(created),
        "failed_count": len(failed),
        "created": created,
        "failed": failed,
        "note": "临时密码仅本次返回，请及时保存或通过短信发送",
    }


# ══════════════════════════════════════════════════════════════════
# 合伙人体系 API
# ══════════════════════════════════════════════════════════════════

partner_router = APIRouter(
    prefix="/api/v1/partners",
    tags=["合伙人体系"]
)


class PartnerApplyRequest(BaseModel):
    region: str = Field(..., description="申请授权区域")
    institution_quota: int = Field(5, ge=1, le=50)
    background: str = Field(..., description="合伙人背景介绍")
    expected_institutions: Optional[str] = None


class PartnerApproveRequest(BaseModel):
    revenue_share_rate: float = Field(0.15, ge=0.05, le=0.40)
    commission_model: str = Field("subscription")
    institution_quota: int = Field(5, ge=1)
    contract_months: int = Field(12, ge=6)


# ─────────────────────────────────────────────────────────────────
# 合伙人申请与管理
# ─────────────────────────────────────────────────────────────────

@partner_router.post("/apply")
async def apply_partner(
    body: PartnerApplyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """合伙人申请"""
    existing = await db.execute(text("""
        SELECT id, status FROM partner_configs
        WHERE partner_user_id = CAST(:uid AS INTEGER)
    """), {"uid": str(current_user.id)})
    if existing.first():
        raise HTTPException(status_code=409, detail="您已提交过合伙人申请")

    result = await db.execute(text("""
        INSERT INTO partner_configs
            (partner_user_id, region, institution_quota, status,
             partner_config)
        VALUES
            (CAST(:uid AS INTEGER), :region, :quota, 'pending',
             CAST(:config AS jsonb))
        RETURNING id
    """), {
        "uid": str(current_user.id),
        "region": body.region,
        "quota": body.institution_quota,
        "config": json.dumps({
            "background": body.background,
            "expected_institutions": body.expected_institutions,
        }, ensure_ascii=False),
    })
    new_id = result.scalar()
    await db.commit()

    return {
        "application_id": str(new_id),
        "message": "合伙人申请已提交，等待平台审核（通常3-5个工作日）",
    }


@partner_router.get("/my")
async def get_my_partner_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询我的合伙人信息"""
    row = await db.execute(text("""
        SELECT pc.*,
               (SELECT COUNT(*) FROM tenants t
                WHERE t.partner_config->>'partner_user_id' = :uid
                  AND t.status = 'active') AS active_institutions_count
        FROM partner_configs pc
        WHERE pc.partner_user_id = CAST(:uid AS INTEGER)
        LIMIT 1
    """), {"uid": str(current_user.id)})

    result = row.mappings().first()
    if not result:
        raise HTTPException(status_code=404, detail="未找到合伙人资质，请先申请")

    return dict(result)


@partner_router.get("/my/institutions")
async def list_my_institutions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询我发展的机构列表"""
    rows = await db.execute(text("""
        SELECT
            t.id,
            t.tenant_name,
            t.status,
            t.created_at,
            t.institution_config->>'institution_type' AS inst_type,
            (SELECT COUNT(*) FROM users u2
             WHERE u2.tenant_id = t.id
               AND u2.is_active = TRUE) AS user_count
        FROM tenants t
        WHERE t.institution_config->>'referred_by_partner' = :uid
        ORDER BY t.created_at DESC
    """), {"uid": str(current_user.id)})

    return {"items": [dict(r) for r in rows.mappings()]}


@partner_router.get("/my/revenue")
async def get_my_revenue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """合伙人收益明细"""
    offset = (page - 1) * page_size

    rows = await db.execute(text("""
        SELECT
            prl.*,
            t.tenant_name AS institution_name
        FROM partner_revenue_logs prl
        LEFT JOIN tenants t ON t.id = prl.institution_id
        WHERE prl.partner_user_id = CAST(:uid AS INTEGER)
        ORDER BY prl.created_at DESC
        LIMIT :limit OFFSET :offset
    """), {
        "uid": str(current_user.id),
        "limit": page_size,
        "offset": offset,
    })

    summary = await db.execute(text("""
        SELECT
            SUM(partner_amount) FILTER (WHERE status = 'paid') AS total_paid,
            SUM(partner_amount) FILTER (WHERE status = 'pending') AS pending_amount,
            SUM(partner_amount) FILTER (
                WHERE status IN ('pending','confirmed')
                  AND created_at >= DATE_TRUNC('month', NOW())
            ) AS this_month
        FROM partner_revenue_logs
        WHERE partner_user_id = CAST(:uid AS INTEGER)
    """), {"uid": str(current_user.id)})
    summary_data = dict(summary.mappings().first() or {})

    return {
        "summary": summary_data,
        "items": [dict(r) for r in rows.mappings()],
        "page": page,
    }


@partner_router.post("/invite-institution")
async def generate_institution_invite_link(
    region_hint: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """生成机构邀请链接（附带合伙人 referral_code）"""
    partner = await db.execute(text("""
        SELECT referral_code, status FROM partner_configs
        WHERE partner_user_id = CAST(:uid AS INTEGER)
    """), {"uid": str(current_user.id)})
    pc = partner.mappings().first()

    if not pc or pc["status"] != "active":
        raise HTTPException(status_code=403, detail="合伙人资质未激活")

    code = pc["referral_code"]
    invite_url = f"https://app.xingjiankang.com/institution/register?ref={code}"
    if region_hint:
        invite_url += f"&region={region_hint}"

    return {
        "invite_url": invite_url,
        "referral_code": code,
        "valid_days": 30,
    }


# ─────────────────────────────────────────────────────────────────
# Admin 合伙人管理
# ─────────────────────────────────────────────────────────────────

@partner_router.post("/{partner_id}/approve")
async def approve_partner(
    partner_id: UUID,
    body: PartnerApproveRequest,
    current_user: User = Depends(
        require_roles([UserRole.ADMIN, UserRole.MASTER])
    ),
    db: AsyncSession = Depends(get_db),
):
    """审批合伙人申请"""
    from datetime import date, timedelta

    contract_end = date.today() + timedelta(days=body.contract_months * 30)

    # 生成唯一 referral_code
    code = "".join(secrets.choice(string.ascii_uppercase + string.digits)
                   for _ in range(8))

    result = await db.execute(text("""
        UPDATE partner_configs
        SET status = 'active',
            revenue_share_rate = :rate,
            commission_model = :model,
            institution_quota = :quota,
            contract_end = :end_date,
            referral_code = :code,
            approved_by = CAST(:approver AS INTEGER),
            approved_at = NOW()
        WHERE id = CAST(:pid AS UUID)
          AND status = 'pending'
        RETURNING partner_user_id
    """), {
        "rate": body.revenue_share_rate,
        "model": body.commission_model,
        "quota": body.institution_quota,
        "end_date": contract_end.isoformat(),
        "code": code,
        "approver": str(current_user.id),
        "pid": str(partner_id),
    })

    if not result.first():
        raise HTTPException(status_code=404, detail="申请不存在或已处理")
    await db.commit()

    return {
        "message": "合伙人已审批激活",
        "referral_code": code,
        "contract_end": contract_end.isoformat(),
    }

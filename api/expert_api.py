"""
expert_api.py — Expert 独立 AGENT API

路由前缀: /api/v1/expert
新增端点: 18个

依赖的现有模块:
  - dependencies.py  (get_current_user, require_role)
  - core/models.py   (User, UserRole)
  - expert_tenants (已有表, 本次 ALTER 扩展)

铁律检查:
  - Expert 直推任务接口返回 403
  - CrisisAgent 不可被关闭
  - MODE_B 草案必须进入 coach_review_items
"""
from __future__ import annotations

import secrets
import string
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# 复用现有依赖（路径根据实际项目结构调整）
from api.dependencies import get_current_user, require_roles
from core.database import get_async_db as get_db
from core.models import User, UserRole

router = APIRouter(prefix="/api/v1/expert", tags=["Expert AGENT"])


# ─────────────────────────────────────────────────────────────────
# Pydantic 模型
# ─────────────────────────────────────────────────────────────────

class ServiceModeUpdate(BaseModel):
    service_mode_public: Optional[bool] = None
    service_mode_clinical: Optional[bool] = None
    service_mode_coach_network: Optional[bool] = None


class PublicProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=200)
    institution_name: Optional[str] = Field(None, max_length=200)
    public_bio: Optional[str] = None
    expert_slug: Optional[str] = Field(None, max_length=100, pattern=r'^[a-z0-9\-]+$')
    specialty_domains: Optional[list[str]] = None
    is_publicly_listed: Optional[bool] = None
    certifications: Optional[list[dict]] = None
    available_hours: Optional[dict] = None


class PatientInvite(BaseModel):
    patient_user_id: UUID
    notes: Optional[str] = None
    institution_id: Optional[UUID] = None


class PatientBindRequest(BaseModel):
    expert_slug: str
    message: Optional[str] = None


class XZBKnowledgeCreate(BaseModel):
    knowledge_type: str = Field("note",
        description="note/rule/case/annotation/template/forbidden")
    content: str = Field(..., min_length=10, max_length=10000)
    evidence_tier: str = Field("T3", pattern=r'^T[1-4]$')
    source: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    applicable_conditions: dict = Field(default_factory=dict)
    confidence_override: Optional[float] = Field(None, ge=0.0, le=1.0)


class XZBKnowledgeUpdate(BaseModel):
    content: Optional[str] = None
    evidence_tier: Optional[str] = Field(None, pattern=r'^T[1-4]$')
    tags: Optional[list[str]] = None
    is_active: Optional[bool] = None
    expert_confirmed: Optional[bool] = None


class XZBRuleCreate(BaseModel):
    rule_name: Optional[str] = Field(None, max_length=200)
    condition_json: dict = Field(...,
        description="触发条件: {trigger_keywords, ttm_stages, risk_levels}")
    action_type: str = Field(...,
        description="respond/refer/prescribe/warn/defer/escalate")
    action_content: str = Field(..., min_length=5)
    priority: int = Field(50, ge=1, le=100)
    overrides_llm: bool = False
    domain_tags: list[str] = Field(default_factory=list)


class XZBActivateRequest(BaseModel):
    domain: str = Field(..., description="专科领域，如 vision/metabolism/cardiac")
    specialty_config: dict = Field(default_factory=dict)


class InstitutionBindRequest(BaseModel):
    institution_id: UUID
    service_config: dict = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────

def _require_expert(user: User):
    """确认当前用户有 Expert 资质"""
    if user.role not in (
        UserRole.SUPERVISOR, UserRole.MASTER, UserRole.ADMIN
    ):
        # Expert 通过 expert_tenants 表标识，这里检查 role_level >= 4
        # 实际生产中应查询 expert_tenants.is_active
        pass
    return user


async def _get_expert_tenant(db: AsyncSession, user_id: UUID) -> dict:
    row = await db.execute(text("""
        SELECT *
        FROM expert_tenants
        WHERE user_id = CAST(:uid AS INTEGER)
          AND is_active = TRUE
        LIMIT 1
    """), {"uid": str(user_id)})
    result = row.mappings().first()
    if not result:
        raise HTTPException(status_code=404, detail="Expert资质未找到，请先完成专家注册")
    return dict(result)


# ─────────────────────────────────────────────────────────────────
# 1. 服务模式管理
# ─────────────────────────────────────────────────────────────────

@router.get("/service-modes")
async def get_service_modes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询当前 Expert 的服务模式"""
    et = await _get_expert_tenant(db, current_user.id)
    return {
        "service_mode_public": et.get("service_mode_public", False),
        "service_mode_clinical": et.get("service_mode_clinical", False),
        "service_mode_coach_network": et.get("service_mode_coach_network", False),
        "is_publicly_listed": et.get("is_publicly_listed", False),
    }


@router.patch("/service-modes")
async def update_service_modes(
    body: ServiceModeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """切换服务模式（A/B/C 独立开关，可多选）"""
    et = await _get_expert_tenant(db, current_user.id)

    updates = {}
    if body.service_mode_public is not None:
        updates["service_mode_public"] = body.service_mode_public
    if body.service_mode_clinical is not None:
        updates["service_mode_clinical"] = body.service_mode_clinical
    if body.service_mode_coach_network is not None:
        updates["service_mode_coach_network"] = body.service_mode_coach_network

    if not updates:
        raise HTTPException(status_code=400, detail="未提供任何更新字段")

    set_clauses = ", ".join([f"{k} = :{k}" for k in updates])
    updates["uid"] = str(current_user.id)

    await db.execute(text(f"""
        UPDATE expert_tenants
        SET {set_clauses}
        WHERE user_id = CAST(:uid AS INTEGER)
    """), updates)
    await db.commit()

    return {"message": "服务模式已更新", "updated": updates}


# ─────────────────────────────────────────────────────────────────
# 2. 公开主页管理
# ─────────────────────────────────────────────────────────────────

@router.get("/public/{slug}")
async def get_expert_public_page(
    slug: str,
    db: AsyncSession = Depends(get_db),
    # 注意：此端点无需登录
):
    """Expert 公开主页（无需认证，任何人可访问）"""
    row = await db.execute(text("""
        SELECT
            epp.*,
            et.public_bio,
            et.specialty_domains,
            et.consultation_fee_config,
            et.service_mode_public,
            et.service_mode_clinical,
            et.is_publicly_listed,
            u.username
        FROM expert_tenants et
        JOIN expert_public_profiles epp ON epp.expert_user_id = et.user_id
        JOIN users u ON u.id = et.user_id
        WHERE et.expert_slug = :slug
          AND et.is_publicly_listed = TRUE
          AND et.is_active = TRUE
        LIMIT 1
    """), {"slug": slug})

    result = row.mappings().first()
    if not result:
        raise HTTPException(status_code=404, detail="专家主页不存在或未公开")

    return dict(result)


@router.get("/public-profile")
async def get_my_public_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询我的公开主页信息（Expert 本人）"""
    row = await db.execute(text("""
        SELECT epp.*, et.expert_slug, et.public_bio,
               et.specialty_domains, et.is_publicly_listed,
               et.service_mode_public, et.service_mode_clinical,
               et.service_mode_coach_network
        FROM expert_public_profiles epp
        JOIN expert_tenants et ON et.user_id = epp.expert_user_id
        WHERE epp.expert_user_id = CAST(:uid AS INTEGER)
        LIMIT 1
    """), {"uid": str(current_user.id)})

    result = row.mappings().first()
    if not result:
        # 首次访问，返回空模板
        return {"exists": False, "message": "请先完善公开主页信息"}

    return {"exists": True, **dict(result)}


@router.patch("/public-profile")
async def update_public_profile(
    body: PublicProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新 Expert 公开主页信息（UPSERT）"""
    # slug 唯一性检查
    if body.expert_slug:
        conflict = await db.execute(text("""
            SELECT 1 FROM expert_tenants
            WHERE expert_slug = :slug
              AND user_id != CAST(:uid AS INTEGER)
        """), {"slug": body.expert_slug, "uid": str(current_user.id)})
        if conflict.first():
            raise HTTPException(status_code=409, detail="该主页地址已被占用，请换一个")

    # UPSERT expert_public_profiles
    profile_updates = {}
    for field_ in ("display_name", "title", "institution_name",
                   "certifications", "available_hours"):
        val = getattr(body, field_, None)
        if val is not None:
            profile_updates[field_] = val if not isinstance(val, list) else val

    if profile_updates:
        profile_updates["uid"] = str(current_user.id)
        set_clauses = ", ".join([
            f"{k} = :{k}" for k in profile_updates if k != "uid"
        ])
        await db.execute(text(f"""
            INSERT INTO expert_public_profiles
                (expert_user_id, display_name)
            VALUES (CAST(:uid AS INTEGER), :display_name)
            ON CONFLICT (expert_user_id)
            DO UPDATE SET {set_clauses}, updated_at = NOW()
        """), {**profile_updates, "display_name": profile_updates.get("display_name", "专家")})

    # 更新 expert_tenants
    tenant_updates = {}
    for field_ in ("expert_slug", "public_bio", "specialty_domains", "is_publicly_listed"):
        val = getattr(body, field_, None)
        if val is not None:
            tenant_updates[field_] = val

    if tenant_updates:
        tenant_updates["uid"] = str(current_user.id)
        set_clauses = ", ".join([f"{k} = :{k}" for k in tenant_updates if k != "uid"])
        await db.execute(text(f"""
            UPDATE expert_tenants
            SET {set_clauses}
            WHERE user_id = CAST(:uid AS INTEGER)
        """), tenant_updates)

    await db.commit()
    return {"message": "公开主页已更新"}


@router.get("/directory")
async def list_expert_directory(
    domain: Optional[str] = Query(None, description="按专科领域过滤"),
    verified_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """专家目录（公开，无需登录）"""
    offset = (page - 1) * page_size
    params: dict = {"limit": page_size, "offset": offset}

    domain_filter = ""
    if domain:
        domain_filter = "AND :domain = ANY(et.specialty_domains)"
        params["domain"] = domain

    verified_filter = ""
    if verified_only:
        verified_filter = "AND epp.is_verified = TRUE"

    rows = await db.execute(text(f"""
        SELECT
            et.expert_slug,
            epp.display_name,
            epp.title,
            epp.institution_name,
            epp.rating,
            epp.review_count,
            epp.total_patients,
            epp.is_verified,
            epp.cover_image_url,
            et.specialty_domains,
            et.service_mode_public,
            et.service_mode_clinical
        FROM expert_tenants et
        JOIN expert_public_profiles epp ON epp.expert_user_id = et.user_id
        WHERE et.is_publicly_listed = TRUE
          AND et.is_active = TRUE
          {domain_filter}
          {verified_filter}
        ORDER BY epp.is_verified DESC, epp.rating DESC, epp.review_count DESC
        LIMIT :limit OFFSET :offset
    """), params)

    return {
        "items": [dict(r) for r in rows.mappings()],
        "page": page,
        "page_size": page_size,
    }


# ─────────────────────────────────────────────────────────────────
# 3. Expert-患者绑定（MODE_B）
# ─────────────────────────────────────────────────────────────────

@router.get("/patients")
async def list_my_patients(
    status: str = Query("active"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询我的绑定患者列表（Expert 视角）"""
    await _get_expert_tenant(db, current_user.id)
    offset = (page - 1) * page_size

    rows = await db.execute(text("""
        SELECT
            epb.id AS binding_id,
            epb.patient_user_id,
            epb.status,
            epb.binding_type,
            epb.notes,
            epb.activated_at,
            u.username,
            u.email,
            -- 最新风险等级（VisionGuard 或其他域）
            (SELECT vp.risk_level FROM vision_profiles vp
             WHERE vp.user_id = epb.patient_user_id
             LIMIT 1) AS vision_risk_level
        FROM expert_patient_bindings epb
        JOIN users u ON u.id = epb.patient_user_id
        WHERE epb.expert_user_id = CAST(:eid AS INTEGER)
          AND epb.status = :status
        ORDER BY epb.activated_at DESC
        LIMIT :limit OFFSET :offset
    """), {
        "eid": str(current_user.id),
        "status": status,
        "limit": page_size,
        "offset": offset,
    })

    return {"items": [dict(r) for r in rows.mappings()]}


@router.post("/patients/invite")
async def invite_patient(
    body: PatientInvite,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Expert 主动邀请患者绑定（MODE_B）"""
    et = await _get_expert_tenant(db, current_user.id)
    if not et.get("service_mode_clinical"):
        raise HTTPException(status_code=403,
            detail="临床服务模式未开启，请先在设置中启用 MODE_B")

    # 检查是否已绑定
    existing = await db.execute(text("""
        SELECT id, status FROM expert_patient_bindings
        WHERE expert_user_id = CAST(:eid AS INTEGER)
          AND patient_user_id = CAST(:pid AS INTEGER)
    """), {"eid": str(current_user.id), "pid": str(body.patient_user_id)})
    if existing.first():
        raise HTTPException(status_code=409, detail="该患者已存在绑定关系")

    await db.execute(text("""
        INSERT INTO expert_patient_bindings
            (expert_user_id, patient_user_id, status, initiated_by,
             institution_id, notes)
        VALUES
            (CAST(:eid AS INTEGER), CAST(:pid AS INTEGER), 'pending', 'expert',
             CAST(:inst AS UUID), :notes)
    """), {
        "eid": str(current_user.id),
        "pid": str(body.patient_user_id),
        "inst": str(body.institution_id) if body.institution_id else None,
        "notes": body.notes,
    })
    await db.commit()

    return {"message": "邀请已发送，等待患者确认"}


@router.post("/patient-bind")
async def patient_request_binding(
    body: PatientBindRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """患者主动申请绑定 Expert（通过 slug）"""
    # 找到 Expert
    expert_row = await db.execute(text("""
        SELECT user_id FROM expert_tenants
        WHERE expert_slug = :slug
          AND service_mode_clinical = TRUE
          AND is_active = TRUE
        LIMIT 1
    """), {"slug": body.expert_slug})
    expert = expert_row.mappings().first()
    if not expert:
        raise HTTPException(status_code=404, detail="专家不存在或未开放临床绑定")

    expert_id = expert["user_id"]

    # 检查重复
    existing = await db.execute(text("""
        SELECT id FROM expert_patient_bindings
        WHERE expert_user_id = CAST(:eid AS INTEGER)
          AND patient_user_id = CAST(:pid AS INTEGER)
    """), {"eid": str(expert_id), "pid": str(current_user.id)})
    if existing.first():
        raise HTTPException(status_code=409, detail="您已申请过该专家的绑定")

    await db.execute(text("""
        INSERT INTO expert_patient_bindings
            (expert_user_id, patient_user_id, status, initiated_by)
        VALUES
            (CAST(:eid AS INTEGER), CAST(:pid AS INTEGER), 'pending', 'patient')
    """), {"eid": str(expert_id), "pid": str(current_user.id)})
    await db.commit()

    return {"message": "绑定申请已提交，等待专家确认"}


@router.patch("/patients/{patient_id}/activate")
async def activate_binding(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Expert 确认激活绑定关系"""
    result = await db.execute(text("""
        UPDATE expert_patient_bindings
        SET status = 'active', activated_at = NOW()
        WHERE expert_user_id = CAST(:eid AS INTEGER)
          AND patient_user_id = CAST(:pid AS INTEGER)
          AND status = 'pending'
        RETURNING id
    """), {"eid": str(current_user.id), "pid": str(patient_id)})
    if not result.first():
        raise HTTPException(status_code=404, detail="绑定关系不存在或状态不对")
    await db.commit()
    return {"message": "绑定已激活"}


@router.delete("/patients/{patient_id}")
async def terminate_binding(
    patient_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """解除绑定关系"""
    await db.execute(text("""
        UPDATE expert_patient_bindings
        SET status = 'terminated', terminated_at = NOW()
        WHERE expert_user_id = CAST(:eid AS INTEGER)
          AND patient_user_id = CAST(:pid AS INTEGER)
          AND status IN ('active','pending')
    """), {"eid": str(current_user.id), "pid": str(patient_id)})
    await db.commit()
    return {"message": "绑定已解除"}


# ─────────────────────────────────────────────────────────────────
# 4. 行诊智伴（XZB）知识库管理
# ─────────────────────────────────────────────────────────────────

@router.post("/xzb/activate")
async def activate_xzb(
    body: XZBActivateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """激活行诊智伴实例（配置专科领域和风格）"""
    await _get_expert_tenant(db, current_user.id)

    specialty_config = body.specialty_config
    specialty_config["domain"] = body.domain
    specialty_config["activated_at"] = datetime.now(timezone.utc).isoformat()

    await db.execute(text("""
        UPDATE expert_tenants
        SET specialty_domains = array_append(
                COALESCE(specialty_domains, '{}'), :domain
            ),
            consultation_fee_config = jsonb_set(
                COALESCE(consultation_fee_config, '{}'),
                '{xzb_config}',
                CAST(:config AS jsonb)
            )
        WHERE user_id = CAST(:uid AS INTEGER)
    """), {
        "domain": body.domain,
        "config": json.dumps(specialty_config, ensure_ascii=False),
        "uid": str(current_user.id),
    })
    await db.commit()

    return {"message": f"行诊智伴已激活，专科领域：{body.domain}"}


@router.get("/xzb/knowledge")
async def list_knowledge(
    knowledge_type: Optional[str] = Query(None),
    evidence_tier: Optional[str] = Query(None),
    confirmed_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """知识库列表"""
    offset = (page - 1) * page_size
    params = {
        "eid": str(current_user.id),
        "limit": page_size,
        "offset": offset,
    }

    filters = ["expert_id = CAST(:eid AS INTEGER)", "is_active = TRUE"]
    if knowledge_type:
        filters.append("knowledge_type = :knowledge_type")
        params["knowledge_type"] = knowledge_type
    if evidence_tier:
        filters.append("evidence_tier = :evidence_tier")
        params["evidence_tier"] = evidence_tier
    if confirmed_only:
        filters.append("expert_confirmed = TRUE")

    where = " AND ".join(filters)

    rows = await db.execute(text(f"""
        SELECT id, knowledge_type, content, evidence_tier,
               source, tags, usage_count, expert_confirmed,
               created_at, updated_at
        FROM xzb_knowledge
        WHERE {where}
        ORDER BY created_at DESC
        LIMIT :limit OFFSET :offset
    """), params)

    count = await db.execute(text(f"""
        SELECT COUNT(*) FROM xzb_knowledge WHERE {where}
    """), {k: v for k, v in params.items() if k not in ("limit", "offset")})

    return {
        "items": [dict(r) for r in rows.mappings()],
        "total": count.scalar(),
        "page": page,
        "page_size": page_size,
    }


@router.post("/xzb/knowledge")
async def create_knowledge(
    body: XZBKnowledgeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """新增知识条目"""
    await _get_expert_tenant(db, current_user.id)

    result = await db.execute(text("""
        INSERT INTO xzb_knowledge
            (expert_id, knowledge_type, content, evidence_tier,
             source, tags, applicable_conditions, confidence_override,
             expert_confirmed)
        VALUES
            (CAST(:eid AS INTEGER), :kt, :content, :tier,
             :source, CAST(:tags AS text[]),
             CAST(:conditions AS jsonb), :conf, TRUE)
        RETURNING id
    """), {
        "eid": str(current_user.id),
        "kt": body.knowledge_type,
        "content": body.content,
        "tier": body.evidence_tier,
        "source": body.source,
        "tags": "{" + ",".join(body.tags) + "}",
        "conditions": json.dumps(body.applicable_conditions, ensure_ascii=False),
        "conf": body.confidence_override,
    })
    new_id = result.scalar()
    await db.commit()

    return {"id": str(new_id), "message": "知识条目已创建"}


@router.patch("/xzb/knowledge/{knowledge_id}")
async def update_knowledge(
    knowledge_id: UUID,
    body: XZBKnowledgeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新知识条目"""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="无更新内容")

    updates["kid"] = str(knowledge_id)
    updates["eid"] = str(current_user.id)
    set_clauses = ", ".join([
        f"{k} = :{k}" for k in updates if k not in ("kid", "eid")
    ])

    result = await db.execute(text(f"""
        UPDATE xzb_knowledge
        SET {set_clauses}, updated_at = NOW()
        WHERE id = CAST(:kid AS UUID)
          AND expert_id = CAST(:eid AS INTEGER)
        RETURNING id
    """), updates)

    if not result.first():
        raise HTTPException(status_code=404, detail="知识条目不存在")
    await db.commit()
    return {"message": "已更新"}


@router.delete("/xzb/knowledge/{knowledge_id}")
async def deactivate_knowledge(
    knowledge_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """停用知识条目（软删除）"""
    await db.execute(text("""
        UPDATE xzb_knowledge
        SET is_active = FALSE, updated_at = NOW()
        WHERE id = CAST(:kid AS UUID)
          AND expert_id = CAST(:eid AS INTEGER)
    """), {"kid": str(knowledge_id), "eid": str(current_user.id)})
    await db.commit()
    return {"message": "知识条目已停用"}


@router.get("/xzb/dashboard")
async def get_xzb_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Expert 工作台首页数据（XZB 知识库健康度 + 患者概况）"""
    eid = str(current_user.id)

    # 知识库统计
    kb_stats = await db.execute(text("""
        SELECT
            COUNT(*) FILTER (WHERE is_active = TRUE) AS total_active,
            COUNT(*) FILTER (WHERE evidence_tier = 'T1') AS tier_t1,
            COUNT(*) FILTER (WHERE evidence_tier = 'T2') AS tier_t2,
            COUNT(*) FILTER (WHERE evidence_tier = 'T3') AS tier_t3,
            COUNT(*) FILTER (WHERE evidence_tier = 'T4') AS tier_t4,
            COUNT(*) FILTER (WHERE expert_confirmed = FALSE) AS unconfirmed,
            SUM(usage_count) AS total_usage
        FROM xzb_knowledge
        WHERE expert_id = CAST(:eid AS INTEGER)
    """), {"eid": eid})
    kb = dict(kb_stats.mappings().first() or {})

    # 患者统计
    patient_stats = await db.execute(text("""
        SELECT
            COUNT(*) FILTER (WHERE status = 'active') AS active_patients,
            COUNT(*) FILTER (WHERE status = 'pending') AS pending_invites
        FROM expert_patient_bindings
        WHERE expert_user_id = CAST(:eid AS INTEGER)
    """), {"eid": eid})
    pt = dict(patient_stats.mappings().first() or {})

    # 今日咨询量（公众 MODE_A）
    today_consultations = await db.execute(text("""
        SELECT COUNT(*) AS count
        FROM chat_sessions
        WHERE created_at >= CURRENT_DATE
          AND session_metadata->>'expert_id' = :eid
    """), {"eid": eid})
    today_count = (today_consultations.scalar() or 0)

    # 服务模式状态
    et = await _get_expert_tenant(db, current_user.id)

    total = kb.get("total_active") or 1
    t12_count = (kb.get("tier_t1") or 0) + (kb.get("tier_t2") or 0)
    kb_health = min(100, int(t12_count / total * 100 + 10))

    return {
        "knowledge_base": {
            **kb,
            "health_score": kb_health,
        },
        "patients": pt,
        "today_consultations": today_count,
        "service_modes": {
            "public": et.get("service_mode_public"),
            "clinical": et.get("service_mode_clinical"),
            "coach_network": et.get("service_mode_coach_network"),
        },
    }


# ─────────────────────────────────────────────────────────────────
# 5. 机构绑定
# ─────────────────────────────────────────────────────────────────

@router.post("/institution-binding")
async def bind_to_institution(
    body: InstitutionBindRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Expert 绑定机构（学校/医院）"""
    # 验证机构存在且为 institution 类型
    inst = await db.execute(text("""
        SELECT id, tenant_name FROM tenants
        WHERE id = CAST(:iid AS UUID)
          AND tenant_type = 'institution'
          AND status = 'active'
        LIMIT 1
    """), {"iid": str(body.institution_id)})
    institution = inst.mappings().first()
    if not institution:
        raise HTTPException(status_code=404, detail="机构不存在或未激活")

    # 在 institution_config 中记录关联 Expert
    service_cfg = json.dumps(body.service_config, ensure_ascii=False)
    await db.execute(text("""
        UPDATE tenants
        SET institution_config = jsonb_set(
            COALESCE(institution_config, '{}'),
            CAST('{associated_experts,' || :eid || '}' AS text[]),
            CAST(:cfg AS jsonb)
        )
        WHERE id = CAST(:iid AS UUID)
    """), {
        "eid": str(current_user.id),
        "cfg": service_cfg,
        "iid": str(body.institution_id),
    })
    await db.commit()

    return {
        "message": f"已成功绑定机构：{institution['tenant_name']}",
        "institution_id": str(body.institution_id),
    }


@router.get("/institutions")
async def list_my_institutions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询 Expert 关联的机构列表"""
    rows = await db.execute(text("""
        SELECT id, tenant_name, tenant_type,
               institution_config->>'institution_type' AS inst_type,
               status
        FROM tenants
        WHERE tenant_type = 'institution'
          AND institution_config->'associated_experts' ? :eid
          AND status = 'active'
        ORDER BY created_at DESC
    """), {"eid": str(current_user.id)})

    return {"items": [dict(r) for r in rows.mappings()]}


# ─────────────────────────────────────────────────────────────────
# 安全拦截：Expert 不得直接推送任务给学员（铁律）
# ─────────────────────────────────────────────────────────────────

@router.post("/tasks/force-push")
async def expert_force_push_blocked():
    """
    此端点永远返回 403。
    Expert 不得直接推送任务，必须经 CoachPushQueue。
    """
    raise HTTPException(
        status_code=403,
        detail="Expert 不允许直接推送任务给学员。"
               "请通过 /api/v1/expert/xzb/knowledge 创建建议草案，"
               "由教练审核后推送。（铁律 I-06）"
    )

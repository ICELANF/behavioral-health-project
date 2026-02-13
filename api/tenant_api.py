"""
专家白标租户 API
Expert White-Label Tenant API

路由前缀: /api/v1/tenants
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field

from core.database import get_db
from core.models import (
    ExpertTenant, TenantClient, TenantAgentMapping, TenantAuditLog,
    TenantStatus, TenantTier, ClientStatus, User
)
from api.dependencies import get_current_user, require_coach_or_admin, require_admin

router = APIRouter(prefix="/api/v1/tenants", tags=["tenants"])


# ============================================
# Pydantic Schemas
# ============================================

class TenantUpdateRequest(BaseModel):
    brand_name: Optional[str] = None
    brand_tagline: Optional[str] = None
    brand_avatar: Optional[str] = None
    brand_logo_url: Optional[str] = None
    brand_colors: Optional[dict] = None
    brand_theme_id: Optional[str] = None
    expert_title: Optional[str] = None
    expert_self_intro: Optional[str] = None
    expert_specialties: Optional[list] = None
    expert_credentials: Optional[list] = None
    enabled_agents: Optional[list] = None
    agent_persona_overrides: Optional[dict] = None
    service_packages: Optional[list] = None
    welcome_message: Optional[str] = None

class ClientAddRequest(BaseModel):
    user_id: int
    service_package: str = "trial"

class ClientUpdateRequest(BaseModel):
    status: Optional[str] = None
    service_package: Optional[str] = None
    notes: Optional[str] = None

class AgentMappingUpdate(BaseModel):
    agent_id: str
    display_name: Optional[str] = None
    display_avatar: Optional[str] = None
    greeting: Optional[str] = None
    tone: Optional[str] = None
    bio: Optional[str] = None
    is_enabled: Optional[bool] = None
    is_primary: Optional[bool] = None
    sort_order: Optional[int] = None

class AgentBatchUpdate(BaseModel):
    agents: List[AgentMappingUpdate]


class RoutingConfigUpdate(BaseModel):
    """路由配置更新"""
    routing_correlations: Optional[dict] = None  # {"sleep": ["glucose", "stress"]}
    routing_conflicts: Optional[dict] = None     # {"sleep|exercise": "sleep"}
    default_fallback_agent: Optional[str] = None
    agent_keywords: Optional[List[dict]] = None  # [{"agent_id": "sleep", "keywords": [...], "boost": 1.5}]


class RoutingTestRequest(BaseModel):
    """路由测试请求"""
    message: str
    profile: Optional[dict] = None
    device_data: Optional[dict] = None


# ============================================
# Helper functions
# ============================================

def _tenant_summary(t: ExpertTenant) -> dict:
    """轻量化租户摘要 (用于 hub 列表)"""
    active_count = 0
    if t.clients:
        try:
            active_count = t.clients.filter(TenantClient.status == ClientStatus.active).count()
        except Exception:
            active_count = 0
    return {
        "id": t.id,
        "brand_name": t.brand_name,
        "brand_tagline": t.brand_tagline,
        "brand_avatar": t.brand_avatar,
        "brand_logo_url": t.brand_logo_url,
        "brand_colors": t.brand_colors,
        "brand_theme_id": t.brand_theme_id,
        "expert_title": t.expert_title,
        "expert_specialties": t.expert_specialties or [],
        "enabled_agents": t.enabled_agents or [],
        "status": t.status.value if t.status else "trial",
        "client_count_active": active_count,
    }


def _tenant_full(t: ExpertTenant) -> dict:
    """完整租户详情"""
    active_count = 0
    total_count = 0
    if t.clients:
        try:
            active_count = t.clients.filter(TenantClient.status == ClientStatus.active).count()
            total_count = t.clients.count()
        except Exception:
            pass
    return {
        "id": t.id,
        "expert_user_id": t.expert_user_id,
        "brand_name": t.brand_name,
        "brand_tagline": t.brand_tagline,
        "brand_avatar": t.brand_avatar,
        "brand_logo_url": t.brand_logo_url,
        "brand_colors": t.brand_colors,
        "brand_theme_id": t.brand_theme_id,
        "custom_domain": t.custom_domain,
        "expert_title": t.expert_title,
        "expert_self_intro": t.expert_self_intro,
        "expert_specialties": t.expert_specialties or [],
        "expert_credentials": t.expert_credentials or [],
        "enabled_agents": t.enabled_agents or [],
        "agent_persona_overrides": t.agent_persona_overrides or {},
        "service_packages": t.service_packages or [],
        "welcome_message": t.welcome_message,
        "status": t.status.value if t.status else "trial",
        "tier": t.tier.value if t.tier else "basic_partner",
        "max_clients": t.max_clients,
        "revenue_share_expert": t.revenue_share_expert,
        "trial_expires_at": t.trial_expires_at.isoformat() if t.trial_expires_at else None,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        "client_count_active": active_count,
        "client_count_total": total_count,
        "agent_mappings": [
            {
                "id": m.id,
                "tenant_id": m.tenant_id,
                "agent_id": m.agent_id,
                "display_name": m.display_name,
                "display_avatar": m.display_avatar,
                "greeting": m.greeting,
                "tone": m.tone,
                "bio": m.bio,
                "is_enabled": m.is_enabled,
                "is_primary": m.is_primary,
                "sort_order": m.sort_order,
            }
            for m in (t.agent_mappings or [])
        ],
    }


def _tenant_public(t: ExpertTenant) -> dict:
    """公开信息 (不含敏感字段)"""
    active_count = 0
    if t.clients:
        try:
            active_count = t.clients.filter(TenantClient.status == ClientStatus.active).count()
        except Exception:
            pass
    return {
        "id": t.id,
        "brand_name": t.brand_name,
        "brand_tagline": t.brand_tagline,
        "brand_avatar": t.brand_avatar,
        "brand_logo_url": t.brand_logo_url,
        "brand_colors": t.brand_colors,
        "brand_theme_id": t.brand_theme_id,
        "expert_title": t.expert_title,
        "expert_self_intro": t.expert_self_intro,
        "expert_specialties": t.expert_specialties or [],
        "expert_credentials": t.expert_credentials or [],
        "enabled_agents": t.enabled_agents or [],
        "service_packages": t.service_packages or [],
        "welcome_message": t.welcome_message,
        "status": t.status.value if t.status else "trial",
        "client_count_active": active_count,
        "agent_mappings": [
            {
                "id": m.id,
                "tenant_id": m.tenant_id,
                "agent_id": m.agent_id,
                "display_name": m.display_name,
                "display_avatar": m.display_avatar,
                "greeting": m.greeting,
                "tone": m.tone,
                "bio": m.bio,
                "is_enabled": m.is_enabled,
                "is_primary": m.is_primary,
                "sort_order": m.sort_order,
            }
            for m in (t.agent_mappings or []) if m.is_enabled
        ],
    }


def _check_tenant_access(tenant: ExpertTenant, user: User):
    """检查当前用户是否有权访问此租户"""
    if user.role.value == "admin":
        return
    if tenant.expert_user_id == user.id:
        return
    raise HTTPException(status_code=403, detail="无权访问此租户")


# ============================================
# 当前用户关联租户
# ============================================

@router.get("/mine")
def get_my_tenant(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取当前用户关联的租户 (作为 owner 或 client)"""
    # 1. 查 ExpertTenant.expert_user_id == user.id
    tenant = db.query(ExpertTenant).filter(
        ExpertTenant.expert_user_id == current_user.id,
    ).first()
    if tenant:
        return {
            "success": True,
            "data": {
                "id": tenant.id,
                "brand_name": tenant.brand_name,
                "status": tenant.status.value if tenant.status else None,
                "application_status": tenant.application_status,
                "role": "owner",
            },
        }

    # 2. 查 TenantClient.user_id == user.id (active)
    client = db.query(TenantClient).filter(
        TenantClient.user_id == current_user.id,
        TenantClient.status == "active",
    ).first()
    if client:
        t = db.query(ExpertTenant).filter(ExpertTenant.id == client.tenant_id).first()
        return {
            "success": True,
            "data": {
                "id": client.tenant_id,
                "brand_name": t.brand_name if t else None,
                "status": t.status.value if t and t.status else None,
                "application_status": t.application_status if t else None,
                "role": "client",
            },
        }

    return {"success": True, "data": None}


# ============================================
# 公开端点
# ============================================

@router.get("/hub")
def tenant_hub(db: Session = Depends(get_db)):
    """专家目录列表 (公开)"""
    tenants = db.query(ExpertTenant).filter(
        ExpertTenant.status.in_([TenantStatus.active, TenantStatus.trial])
    ).all()
    return {
        "success": True,
        "data": [_tenant_summary(t) for t in tenants],
        "total": len(tenants),
    }


@router.get("/{tenant_id}/public")
def tenant_public(tenant_id: str, db: Session = Depends(get_db)):
    """专家公开信息"""
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    return {"success": True, "data": _tenant_public(tenant)}


# ============================================
# 认证端点 (owner / admin)
# ============================================

@router.get("/{tenant_id}")
def get_tenant(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """租户详情 (owner/admin)"""
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    _check_tenant_access(tenant, current_user)
    return {"success": True, "data": _tenant_full(tenant)}


@router.patch("/{tenant_id}")
def update_tenant(
    tenant_id: str,
    data: TenantUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新品牌/配置 (owner/admin)"""
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    _check_tenant_access(tenant, current_user)

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tenant, key, value)
    tenant.updated_at = datetime.utcnow()

    # 审计日志
    db.add(TenantAuditLog(
        tenant_id=tenant_id,
        actor_id=current_user.id,
        action="config_update",
        detail={"fields": list(update_data.keys())},
        created_at=datetime.utcnow(),
    ))

    db.commit()
    db.refresh(tenant)
    return {"success": True, "data": _tenant_full(tenant)}


# ============================================
# 客户管理 (coach / admin)
# ============================================

@router.get("/{tenant_id}/clients")
def list_clients(
    tenant_id: str,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """客户列表"""
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    _check_tenant_access(tenant, current_user)

    query = db.query(TenantClient).filter(TenantClient.tenant_id == tenant_id)
    if status:
        query = query.filter(TenantClient.status == status)
    clients = query.order_by(TenantClient.enrolled_at.desc()).all()

    return {
        "success": True,
        "data": [
            {
                "id": c.id,
                "tenant_id": c.tenant_id,
                "user_id": c.user_id,
                "source": c.source,
                "service_package": c.service_package,
                "status": c.status.value if c.status else "active",
                "enrolled_at": c.enrolled_at.isoformat() if c.enrolled_at else None,
                "graduated_at": c.graduated_at.isoformat() if c.graduated_at else None,
                "total_sessions": c.total_sessions,
                "last_active_at": c.last_active_at.isoformat() if c.last_active_at else None,
                "notes": c.notes,
            }
            for c in clients
        ],
    }


@router.post("/{tenant_id}/clients")
def add_client(
    tenant_id: str,
    data: ClientAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """添加客户"""
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    _check_tenant_access(tenant, current_user)

    # 检查用户是否存在
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查是否已存在
    existing = db.query(TenantClient).filter(
        TenantClient.tenant_id == tenant_id,
        TenantClient.user_id == data.user_id,
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="该用户已是此租户的客户")

    client = TenantClient(
        tenant_id=tenant_id,
        user_id=data.user_id,
        service_package=data.service_package,
        enrolled_at=datetime.utcnow(),
    )
    db.add(client)

    # 审计日志
    db.add(TenantAuditLog(
        tenant_id=tenant_id,
        actor_id=current_user.id,
        action="client_add",
        detail={"user_id": data.user_id, "service_package": data.service_package},
        created_at=datetime.utcnow(),
    ))

    db.commit()
    db.refresh(client)
    return {"success": True, "data": {"id": client.id, "user_id": client.user_id}}


@router.patch("/{tenant_id}/clients/{client_id}")
def update_client(
    tenant_id: str,
    client_id: int,
    data: ClientUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """更新客户"""
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    _check_tenant_access(tenant, current_user)

    client = db.query(TenantClient).filter(
        TenantClient.id == client_id,
        TenantClient.tenant_id == tenant_id,
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="客户不存在")

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(client, key, value)
    if data.status == "graduated":
        client.graduated_at = datetime.utcnow()

    db.commit()
    return {"success": True, "message": "客户已更新"}


# ============================================
# Agent 管理
# ============================================

@router.get("/{tenant_id}/agents")
def list_agents(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Agent 映射列表"""
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    _check_tenant_access(tenant, current_user)

    mappings = db.query(TenantAgentMapping).filter(
        TenantAgentMapping.tenant_id == tenant_id
    ).order_by(TenantAgentMapping.sort_order).all()

    return {
        "success": True,
        "data": [
            {
                "id": m.id,
                "agent_id": m.agent_id,
                "display_name": m.display_name,
                "display_avatar": m.display_avatar,
                "greeting": m.greeting,
                "tone": m.tone,
                "bio": m.bio,
                "is_enabled": m.is_enabled,
                "is_primary": m.is_primary,
                "sort_order": m.sort_order,
            }
            for m in mappings
        ],
    }


@router.put("/{tenant_id}/agents")
def batch_update_agents(
    tenant_id: str,
    data: AgentBatchUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """批量更新 Agent 配置"""
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    _check_tenant_access(tenant, current_user)

    for agent_update in data.agents:
        mapping = db.query(TenantAgentMapping).filter(
            TenantAgentMapping.tenant_id == tenant_id,
            TenantAgentMapping.agent_id == agent_update.agent_id,
        ).first()

        if mapping:
            update_fields = agent_update.dict(exclude_unset=True, exclude={"agent_id"})
            for key, value in update_fields.items():
                if value is not None:
                    setattr(mapping, key, value)
        else:
            # 新增映射
            new_mapping = TenantAgentMapping(
                tenant_id=tenant_id,
                agent_id=agent_update.agent_id,
                display_name=agent_update.display_name or "",
                display_avatar=agent_update.display_avatar or "",
                greeting=agent_update.greeting or "",
                tone=agent_update.tone or "",
                bio=agent_update.bio or "",
                is_enabled=agent_update.is_enabled if agent_update.is_enabled is not None else True,
                is_primary=agent_update.is_primary or False,
                sort_order=agent_update.sort_order or 0,
                created_at=datetime.utcnow(),
            )
            db.add(new_mapping)

    # 审计
    db.add(TenantAuditLog(
        tenant_id=tenant_id,
        actor_id=current_user.id,
        action="agents_update",
        detail={"agent_ids": [a.agent_id for a in data.agents]},
        created_at=datetime.utcnow(),
    ))

    db.commit()
    return {"success": True, "message": f"已更新 {len(data.agents)} 个 Agent 配置"}


# ============================================
# 统计
# ============================================

@router.get("/{tenant_id}/stats")
def tenant_stats(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """客户统计"""
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    _check_tenant_access(tenant, current_user)

    # 按状态统计
    status_counts = db.query(
        TenantClient.status, func.count(TenantClient.id)
    ).filter(
        TenantClient.tenant_id == tenant_id
    ).group_by(TenantClient.status).all()

    counts = {s.value: 0 for s in ClientStatus}
    for s, c in status_counts:
        key = s.value if hasattr(s, 'value') else s
        counts[key] = c

    # 本月新增
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_this_month = db.query(func.count(TenantClient.id)).filter(
        TenantClient.tenant_id == tenant_id,
        TenantClient.enrolled_at >= month_start,
    ).scalar() or 0

    return {
        "success": True,
        "data": {
            "clients": {
                "active": counts.get("active", 0),
                "graduated": counts.get("graduated", 0),
                "paused": counts.get("paused", 0),
                "exited": counts.get("exited", 0),
                "total": sum(counts.values()),
            },
            "new_this_month": new_this_month,
        },
    }


# ============================================
# 路由配置 (Phase 2)
# ============================================

@router.get("/{tenant_id}/routing")
def get_routing_config(
    tenant_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取租户路由配置"""
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    _check_tenant_access(tenant, current_user)

    # 加载 Agent 映射中的路由关键词
    mappings = db.query(TenantAgentMapping).filter(
        TenantAgentMapping.tenant_id == tenant_id
    ).order_by(TenantAgentMapping.sort_order).all()

    agent_keywords = [
        {
            "agent_id": m.agent_id,
            "display_name": m.display_name,
            "custom_keywords": m.custom_keywords or [],
            "keyword_boost": m.keyword_boost if m.keyword_boost is not None else 1.5,
            "is_enabled": m.is_enabled,
        }
        for m in mappings
    ]

    return {
        "success": True,
        "data": {
            "routing_correlations": tenant.routing_correlations or {},
            "routing_conflicts": tenant.routing_conflicts or {},
            "default_fallback_agent": tenant.default_fallback_agent or "behavior_rx",
            "agent_keywords": agent_keywords,
        },
    }


@router.put("/{tenant_id}/routing")
def update_routing_config(
    tenant_id: str,
    data: RoutingConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_coach_or_admin),
):
    """更新租户路由配置"""
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    _check_tenant_access(tenant, current_user)

    # 更新租户级配置
    if data.routing_correlations is not None:
        tenant.routing_correlations = data.routing_correlations
    if data.routing_conflicts is not None:
        tenant.routing_conflicts = data.routing_conflicts
    if data.default_fallback_agent is not None:
        tenant.default_fallback_agent = data.default_fallback_agent

    # 更新 Agent 映射中的关键词
    if data.agent_keywords:
        for ak in data.agent_keywords:
            mapping = db.query(TenantAgentMapping).filter(
                TenantAgentMapping.tenant_id == tenant_id,
                TenantAgentMapping.agent_id == ak.get("agent_id"),
            ).first()
            if mapping:
                if "keywords" in ak:
                    mapping.custom_keywords = ak["keywords"]
                if "boost" in ak:
                    mapping.keyword_boost = ak["boost"]
            else:
                # 自动创建映射
                db.add(TenantAgentMapping(
                    tenant_id=tenant_id,
                    agent_id=ak.get("agent_id", ""),
                    custom_keywords=ak.get("keywords", []),
                    keyword_boost=ak.get("boost", 1.5),
                    created_at=datetime.utcnow(),
                ))

    tenant.updated_at = datetime.utcnow()

    # 审计
    db.add(TenantAuditLog(
        tenant_id=tenant_id,
        actor_id=current_user.id,
        action="routing_update",
        detail=data.dict(exclude_unset=True),
        created_at=datetime.utcnow(),
    ))

    db.commit()
    return {"success": True, "message": "路由配置已更新"}


@router.post("/{tenant_id}/routing/test")
def test_routing(
    tenant_id: str,
    data: RoutingTestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """测试路由效果 — 给定消息, 返回路由结果 (不执行Agent)"""
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    _check_tenant_access(tenant, current_user)

    from core.agent_template_service import get_tenant_routing_context
    from core.agents.base import AgentInput

    # 加载租户路由上下文
    tenant_ctx = get_tenant_routing_context(tenant_id, db)

    # 构建轻量 MasterAgent (core.agents 版, 有 .router)
    try:
        from core.agents.master_agent import MasterAgent as AgentsMasterAgent

        master = AgentsMasterAgent(db_session=db)

        inp = AgentInput(
            user_id=current_user.id,
            message=data.message,
            profile=data.profile or {},
            device_data=data.device_data or {},
        )

        # 不带租户上下文的路由
        platform_routes = master.router.route(inp, tenant_ctx=None)
        # 带租户上下文的路由
        tenant_routes = master.router.route(inp, tenant_ctx=tenant_ctx)

        return {
            "success": True,
            "data": {
                "message": data.message,
                "platform_routing": platform_routes,
                "tenant_routing": tenant_routes,
                "tenant_ctx_summary": {
                    "custom_keywords_count": sum(
                        len(v.get("keywords", []))
                        for v in (tenant_ctx or {}).get("agent_keyword_overrides", {}).values()
                    ),
                    "correlations_overrides": len((tenant_ctx or {}).get("correlations") or {}),
                    "conflicts_overrides": len((tenant_ctx or {}).get("conflicts") or {}),
                    "fallback_agent": (tenant_ctx or {}).get("fallback_agent", "behavior_rx"),
                },
            },
        }
    except ImportError:
        raise HTTPException(status_code=503, detail="路由服务不可用")

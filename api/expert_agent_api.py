# -*- coding: utf-8 -*-
"""
Expert Agent API - 专家自助 Agent CRUD

专家在自己的租户下创�?管理动�?Agent (dynamic_llm 模板)�?所有写操作会同步更�?AgentTemplate + TenantAgentMapping + 缓存�?"""
import re
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.database import get_db
from core.models import (
    User, ExpertTenant, TenantAgentMapping, AgentTemplate,
)
from api.dependencies import get_current_user, require_coach_or_admin

router = APIRouter(tags=["expert-agent"])

_NAME_SUFFIX_RE = re.compile(r"^[a-z][a-z0-9_]{2,19}$")


# ---------------------------------------------------------------------------
# Pydantic 模型
# ---------------------------------------------------------------------------

class CreateAgentRequest(BaseModel):
    name_suffix: str = Field(..., description="Agent 后缀�? �?gut_health")
    display_name: str = Field(..., max_length=64, description="显示名称")
    system_prompt: str = Field("", description="系统提示�?)
    keywords: List[str] = Field(default_factory=list, description="路由关键�?)
    correlations: List[str] = Field(default_factory=list, description="关联 Agent")
    priority: int = Field(5, ge=1, le=10, description="优先�?1-10")
    description: str = Field("", max_length=256)
    evidence_tier: str = Field("T3", description="循证等级 T1/T2/T3/T4 (I-09)")


class UpdateAgentRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=64)
    system_prompt: Optional[str] = None
    keywords: Optional[List[str]] = None
    correlations: Optional[List[str]] = None
    priority: Optional[int] = Field(None, ge=1, le=10)
    description: Optional[str] = Field(None, max_length=256)


class TestRoutingRequest(BaseModel):
    message: str = Field(..., description="测试消息")


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def _verify_tenant_owner(
    tenant_id: str,
    current_user: User,
    db: Session,
) -> ExpertTenant:
    """校验 tenant 归属: 必须�?owner �?admin"""
    tenant = db.query(ExpertTenant).filter(
        ExpertTenant.id == tenant_id,
    ).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存�?)
    if tenant.expert_user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="无权操作此租�?)
    return tenant


def _invalidate_and_reset():
    """清空模板缓存 + 重置 v6 单例"""
    try:
        from core.agent_template_service import invalidate_cache
        invalidate_cache()
    except Exception:
        pass
    try:
        from api.main import reset_agent_master
        reset_agent_master()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# API 端点
# ---------------------------------------------------------------------------

@router.post("/api/v1/tenants/{tenant_id}/my-agents")
async def create_agent(
    tenant_id: str,
    req: CreateAgentRequest,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """创建专家自定�?Agent (dynamic_llm 模板 + TenantAgentMapping)"""
    tenant = _verify_tenant_owner(tenant_id, current_user, db)

    # 校验 name_suffix
    if not _NAME_SUFFIX_RE.match(req.name_suffix):
        raise HTTPException(
            status_code=400,
            detail="name_suffix 必须: 小写字母开�? 3-20�? 仅含小写字母/数字/下划�?,
        )

    # 生成全局唯一 agent_id
    # �?tenant_id �?slug (�?6字符, 移除非字母数�?
    slug = re.sub(r"[^a-z0-9]", "", tenant_id.lower())[:16]
    agent_id = f"{slug}_{req.name_suffix}"

    # 检查重�?    existing = db.query(AgentTemplate).filter(AgentTemplate.agent_id == agent_id).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Agent ID '{agent_id}' 已存�?)

    # I-09: 循证等级权限校验
    evidence_tier = getattr(req, "evidence_tier", "T3") or "T3"
    _TIER_MIN_ROLE = {"T1": "admin", "T2": "supervisor", "T3": "coach", "T4": "coach"}
    _ROLE_LEVEL_MAP = {"observer": 1, "grower": 2, "sharer": 3, "coach": 4, "promoter": 5, "supervisor": 5, "master": 6, "admin": 99}
    min_role = _TIER_MIN_ROLE.get(evidence_tier, "coach")
    user_role = current_user.role.value if current_user.role else "observer"
    if _ROLE_LEVEL_MAP.get(user_role, 0) < _ROLE_LEVEL_MAP.get(min_role, 0):
        raise HTTPException(
            status_code=403,
            detail=f"循证等级 {evidence_tier} 需�?{min_role} 或更高权�?,
        )

    # 1. 创建 AgentTemplate
    now = datetime.utcnow()
    tpl = AgentTemplate(
        agent_id=agent_id,
        display_name=req.display_name,
        agent_type="dynamic_llm",
        domain_enum=req.name_suffix,
        description=req.description,
        keywords=req.keywords,
        correlations=req.correlations,
        priority=req.priority,
        system_prompt=req.system_prompt,
        evidence_tier=evidence_tier,
        is_preset=False,
        is_enabled=True,
        created_by=current_user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(tpl)

    # 2. 创建 TenantAgentMapping
    mapping = TenantAgentMapping(
        tenant_id=tenant_id,
        agent_id=agent_id,
        display_name=req.display_name,
        is_enabled=True,
        custom_keywords=req.keywords,
        created_at=now,
    )
    db.add(mapping)

    # 3. 更新 ExpertTenant.enabled_agents
    enabled = list(tenant.enabled_agents or [])
    if agent_id not in enabled:
        enabled.append(agent_id)
        tenant.enabled_agents = enabled

    db.commit()
    _invalidate_and_reset()

    return {
        "success": True,
        "data": {
            "agent_id": agent_id,
            "display_name": req.display_name,
            "agent_type": "dynamic_llm",
            "keywords": req.keywords,
        },
        "message": f"Agent '{agent_id}' 创建成功",
    }


@router.get("/api/v1/tenants/{tenant_id}/my-agents")
async def list_my_agents(
    tenant_id: str,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """列出专家自己�?Agent (含预�?+ 自建)"""
    _verify_tenant_owner(tenant_id, current_user, db)

    mappings = db.query(TenantAgentMapping).filter(
        TenantAgentMapping.tenant_id == tenant_id,
    ).order_by(TenantAgentMapping.sort_order).all()

    agents = []
    for m in mappings:
        tpl = db.query(AgentTemplate).filter(
            AgentTemplate.agent_id == m.agent_id,
        ).first()

        agents.append({
            "agent_id": m.agent_id,
            "display_name": m.display_name or (tpl.display_name if tpl else m.agent_id),
            "is_enabled": m.is_enabled,
            "is_primary": m.is_primary,
            "custom_keywords": m.custom_keywords or [],
            "keyword_boost": m.keyword_boost,
            "sort_order": m.sort_order,
            "is_preset": tpl.is_preset if tpl else True,
            "agent_type": tpl.agent_type if tpl else "specialist",
            "description": tpl.description if tpl else "",
            "system_prompt": tpl.system_prompt if tpl else "",
            "correlations": tpl.correlations if tpl else [],
            "priority": tpl.priority if tpl else 5,
        })

    return {"success": True, "data": agents}


@router.put("/api/v1/tenants/{tenant_id}/my-agents/{agent_id}")
async def update_agent(
    tenant_id: str,
    agent_id: str,
    req: UpdateAgentRequest,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """更新 Agent �?prompt/keywords/correlations"""
    _verify_tenant_owner(tenant_id, current_user, db)

    tpl = db.query(AgentTemplate).filter(AgentTemplate.agent_id == agent_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Agent 模板不存�?)

    mapping = db.query(TenantAgentMapping).filter(
        TenantAgentMapping.tenant_id == tenant_id,
        TenantAgentMapping.agent_id == agent_id,
    ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="租户 Agent 映射不存�?)

    # 更新 AgentTemplate (仅非预置 Agent 可修�?system_prompt)
    if req.display_name is not None:
        tpl.display_name = req.display_name
        mapping.display_name = req.display_name
    if req.keywords is not None:
        tpl.keywords = req.keywords
        mapping.custom_keywords = req.keywords
    if req.correlations is not None:
        tpl.correlations = req.correlations
    if req.priority is not None:
        tpl.priority = req.priority
    if req.description is not None:
        tpl.description = req.description
    if req.system_prompt is not None:
        if tpl.is_preset:
            raise HTTPException(status_code=400, detail="预置 Agent 不可修改 system_prompt")
        tpl.system_prompt = req.system_prompt

    db.commit()
    _invalidate_and_reset()

    return {"success": True, "message": f"Agent '{agent_id}' 更新成功"}


# I-05: 强制 Agent 列表 (不可停用)
FORCED_AGENTS = ["crisis", "supervisor_reviewer"]


@router.post("/api/v1/tenants/{tenant_id}/my-agents/{agent_id}/toggle")
async def toggle_agent(
    tenant_id: str,
    agent_id: str,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """启用/停用 Agent (I-05: 强制Agent不可停用)"""
    _verify_tenant_owner(tenant_id, current_user, db)

    if agent_id in FORCED_AGENTS:
        raise HTTPException(status_code=400, detail=f"'{agent_id}' 是强制Agent，不可停�?)

    mapping = db.query(TenantAgentMapping).filter(
        TenantAgentMapping.tenant_id == tenant_id,
        TenantAgentMapping.agent_id == agent_id,
    ).first()
    if not mapping:
        raise HTTPException(status_code=404, detail="租户 Agent 映射不存�?)

    mapping.is_enabled = not mapping.is_enabled

    # 同步 enabled_agents 列表
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    enabled = list(tenant.enabled_agents or [])
    if mapping.is_enabled and agent_id not in enabled:
        enabled.append(agent_id)
    elif not mapping.is_enabled and agent_id in enabled:
        enabled.remove(agent_id)
    tenant.enabled_agents = enabled

    db.commit()
    _invalidate_and_reset()

    return {
        "success": True,
        "data": {"agent_id": agent_id, "is_enabled": mapping.is_enabled},
        "message": f"Agent '{agent_id}' 已{'启用' if mapping.is_enabled else '停用'}",
    }


@router.post("/api/v1/tenants/{tenant_id}/my-agents/init-defaults")
async def init_default_agents(
    tenant_id: str,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """I-05: 基于角色初始化默�?Agent + 合并强制 Agent"""
    _verify_tenant_owner(tenant_id, current_user, db)

    import json, os
    cfg_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "configs", "supervisor_credential_config.json",
    )
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}

    role_val = current_user.role.value if current_user.role else "coach"
    defaults_by_role = cfg.get("default_enabled_agents_by_role", {})
    forced = cfg.get("forced_agents", FORCED_AGENTS)
    default_agents = defaults_by_role.get(role_val, defaults_by_role.get("coach", ["crisis"]))

    # 合并: 强制 Agent + 角色默认
    merged = list(dict.fromkeys(forced + default_agents))

    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存�?)

    # 更新 enabled_agents
    tenant.enabled_agents = merged

    # 同步 TenantAgentMapping
    for aid in merged:
        existing = db.query(TenantAgentMapping).filter(
            TenantAgentMapping.tenant_id == tenant_id,
            TenantAgentMapping.agent_id == aid,
        ).first()
        if existing:
            existing.is_enabled = True
        else:
            db.add(TenantAgentMapping(
                tenant_id=tenant_id,
                agent_id=aid,
                is_enabled=True,
            ))

    db.commit()
    _invalidate_and_reset()

    return {
        "success": True,
        "data": {"enabled_agents": merged, "role": role_val},
        "message": f"已初始化 {len(merged)} 个默�?Agent (角色: {role_val})",
    }


@router.post("/api/v1/tenants/{tenant_id}/my-agents/test-routing")
async def test_routing(
    tenant_id: str,
    req: TestRoutingRequest,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """测试路由 (dry-run): 对比平台默认 vs 租户定制路由结果"""
    _verify_tenant_owner(tenant_id, current_user, db)

    from core.agents.base import AgentInput
    from core.agent_template_service import get_tenant_routing_context

    tenant_ctx = get_tenant_routing_context(tenant_id, db)

    # 构造测试输�?    test_input = AgentInput(
        user_id=current_user.id,
        message=req.message,
        intent="",
        profile={},
        device_data={},
        context={},
    )

    # 平台默认路由
    platform_route = []
    try:
        from api.main import get_master_agent
        am = get_master_agent()
        if am and hasattr(am, "router"):
            platform_route = am.router.route(test_input, tenant_ctx=None)
    except Exception:
        pass

    # 租户定制路由
    tenant_route = []
    try:
        from api.main import get_master_agent
        am = get_master_agent()
        if am and hasattr(am, "router"):
            tenant_route = am.router.route(test_input, tenant_ctx=tenant_ctx)
    except Exception:
        pass

    return {
        "success": True,
        "data": {
            "message": req.message,
            "platform_route": platform_route,
            "tenant_route": tenant_route,
            "tenant_ctx_summary": {
                "tenant_id": tenant_id,
                "enabled_agents": (tenant_ctx or {}).get("enabled_agents", []),
                "keyword_overrides": list((tenant_ctx or {}).get("agent_keyword_overrides", {}).keys()),
            },
        },
    }


@router.delete("/api/v1/tenants/{tenant_id}/my-agents/{agent_id}")
async def delete_agent(
    tenant_id: str,
    agent_id: str,
    current_user: User = Depends(require_coach_or_admin),
    db: Session = Depends(get_db),
):
    """删除专家自建 Agent (仅非预置)"""
    _verify_tenant_owner(tenant_id, current_user, db)

    tpl = db.query(AgentTemplate).filter(AgentTemplate.agent_id == agent_id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Agent 模板不存�?)
    if tpl.is_preset:
        raise HTTPException(status_code=400, detail="预置 Agent 不可删除, 请使用停�?)

    # 删除 TenantAgentMapping
    db.query(TenantAgentMapping).filter(
        TenantAgentMapping.tenant_id == tenant_id,
        TenantAgentMapping.agent_id == agent_id,
    ).delete()

    # �?enabled_agents 移除
    tenant = db.query(ExpertTenant).filter(ExpertTenant.id == tenant_id).first()
    if tenant:
        enabled = list(tenant.enabled_agents or [])
        if agent_id in enabled:
            enabled.remove(agent_id)
            tenant.enabled_agents = enabled

    # 删除 AgentTemplate
    db.delete(tpl)

    db.commit()
    _invalidate_and_reset()

    return {"success": True, "message": f"Agent '{agent_id}' 已删�?}

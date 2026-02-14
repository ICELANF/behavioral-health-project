"""
Agent 模板管理 API — Admin CRUD
10 端点, 全部 require_admin
"""
from __future__ import annotations
import re
import logging
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db
from core.models import AgentTemplate, UserActivityLog
from api.dependencies import require_admin
from core.agents.base import AgentDomain

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/agent-templates", tags=["Agent模板管理"])

AGENT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,31}$")


# ── Pydantic 模型 ──

class AgentTemplateCreate(BaseModel):
    agent_id: str = Field(..., min_length=3, max_length=32)
    display_name: str = Field(..., min_length=1, max_length=64)
    description: Optional[str] = None
    keywords: List[str] = []
    data_fields: List[str] = []
    correlations: List[str] = []
    priority: int = Field(5, ge=0, le=10)
    base_weight: float = Field(0.8, ge=0.0, le=1.0)
    enable_llm: bool = True
    system_prompt: Optional[str] = None
    conflict_wins_over: List[str] = []


class AgentTemplateUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    data_fields: Optional[List[str]] = None
    correlations: Optional[List[str]] = None
    priority: Optional[int] = Field(None, ge=0, le=10)
    base_weight: Optional[float] = Field(None, ge=0.0, le=1.0)
    enable_llm: Optional[bool] = None
    system_prompt: Optional[str] = None
    conflict_wins_over: Optional[List[str]] = None


def _template_to_dict(t: AgentTemplate) -> dict:
    return {
        "id": t.id,
        "agent_id": t.agent_id,
        "display_name": t.display_name,
        "agent_type": t.agent_type,
        "domain_enum": t.domain_enum,
        "description": t.description,
        "keywords": t.keywords or [],
        "data_fields": t.data_fields or [],
        "correlations": t.correlations or [],
        "priority": t.priority,
        "base_weight": t.base_weight,
        "enable_llm": t.enable_llm,
        "system_prompt": t.system_prompt,
        "conflict_wins_over": t.conflict_wins_over or [],
        "is_preset": t.is_preset,
        "is_enabled": t.is_enabled,
        "created_by": t.created_by,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


def _invalidate():
    """写操作后清空缓存"""
    try:
        from core.agent_template_service import invalidate_cache
        invalidate_cache()
    except Exception:
        pass


# ── 1. 列表 ──
@router.get("/list")
def list_templates(
    agent_type: Optional[str] = Query(None),
    is_enabled: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    q = db.query(AgentTemplate)
    if agent_type:
        q = q.filter(AgentTemplate.agent_type == agent_type)
    if is_enabled is not None:
        q = q.filter(AgentTemplate.is_enabled == is_enabled)
    total = q.count()
    rows = q.order_by(AgentTemplate.priority, AgentTemplate.id).offset(skip).limit(limit).all()
    return {
        "total": total,
        "items": [_template_to_dict(r) for r in rows],
    }


# ── 2. 仅预置模板 ──
@router.get("/presets")
def list_presets(
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    rows = db.query(AgentTemplate).filter(
        AgentTemplate.is_preset == True  # noqa: E712
    ).order_by(AgentTemplate.priority).all()
    return [_template_to_dict(r) for r in rows]


# ── 3. AgentDomain 枚举值 ──
@router.get("/domains")
def list_domains(_admin=Depends(require_admin)):
    return [{"value": d.value, "label": d.value} for d in AgentDomain]


# ── 4. 详情 ──
@router.get("/{agent_id}")
def get_template(
    agent_id: str,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    t = db.query(AgentTemplate).filter(AgentTemplate.agent_id == agent_id).first()
    if not t:
        raise HTTPException(404, f"Agent 模板 '{agent_id}' 不存在")
    return _template_to_dict(t)


# ── 5. 创建 (强制 agent_type=dynamic_llm) ──
@router.post("/create")
def create_template(
    data: AgentTemplateCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    if not AGENT_ID_PATTERN.match(data.agent_id):
        raise HTTPException(400, "agent_id 格式无效, 需要: ^[a-z][a-z0-9_]{2,31}$")

    existing = db.query(AgentTemplate).filter(AgentTemplate.agent_id == data.agent_id).first()
    if existing:
        raise HTTPException(409, f"agent_id '{data.agent_id}' 已存在")

    t = AgentTemplate(
        agent_id=data.agent_id,
        display_name=data.display_name,
        agent_type="dynamic_llm",
        domain_enum=None,
        description=data.description,
        keywords=data.keywords,
        data_fields=data.data_fields,
        correlations=data.correlations,
        priority=data.priority,
        base_weight=data.base_weight,
        enable_llm=data.enable_llm,
        system_prompt=data.system_prompt,
        conflict_wins_over=data.conflict_wins_over,
        is_preset=False,
        is_enabled=True,
        created_by=admin.id,
    )
    db.add(t)
    try:
        db.add(UserActivityLog(
            user_id=admin.id,
            activity_type="agent_tpl.create",
            detail={"agent_id": data.agent_id, "display_name": data.display_name},
            created_at=datetime.utcnow(),
        ))
        db.flush()
    except Exception:
        logger.warning("审计日志写入失败")
    db.commit()
    db.refresh(t)
    _invalidate()
    return _template_to_dict(t)


# ── 6. 更新 ──
@router.put("/{agent_id}")
def update_template(
    agent_id: str,
    data: AgentTemplateUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    t = db.query(AgentTemplate).filter(AgentTemplate.agent_id == agent_id).first()
    if not t:
        raise HTTPException(404, f"Agent 模板 '{agent_id}' 不存在")

    update_data = data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(t, key, value)
    t.updated_at = datetime.utcnow()

    try:
        db.add(UserActivityLog(
            user_id=_admin.id,
            activity_type="agent_tpl.update",
            detail={"agent_id": agent_id, "fields": list(update_data.keys())},
            created_at=datetime.utcnow(),
        ))
        db.flush()
    except Exception:
        logger.warning("审计日志写入失败")
    db.commit()
    db.refresh(t)
    _invalidate()
    return _template_to_dict(t)


# ── 7. 删除 (预置不可删) ──
@router.delete("/{agent_id}")
def delete_template(
    agent_id: str,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    t = db.query(AgentTemplate).filter(AgentTemplate.agent_id == agent_id).first()
    if not t:
        raise HTTPException(404, f"Agent 模板 '{agent_id}' 不存在")
    if t.is_preset:
        raise HTTPException(403, "预置模板不可删除")

    db.delete(t)
    try:
        db.add(UserActivityLog(
            user_id=_admin.id,
            activity_type="agent_tpl.delete",
            detail={"agent_id": agent_id},
            created_at=datetime.utcnow(),
        ))
        db.flush()
    except Exception:
        logger.warning("审计日志写入失败")
    db.commit()
    _invalidate()
    return {"ok": True, "deleted": agent_id}


# ── 8. 启用/停用 ──
@router.post("/{agent_id}/toggle")
def toggle_template(
    agent_id: str,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    t = db.query(AgentTemplate).filter(AgentTemplate.agent_id == agent_id).first()
    if not t:
        raise HTTPException(404, f"Agent 模板 '{agent_id}' 不存在")
    t.is_enabled = not t.is_enabled
    t.updated_at = datetime.utcnow()
    try:
        db.add(UserActivityLog(
            user_id=_admin.id,
            activity_type="agent_tpl.toggle",
            detail={"agent_id": agent_id, "is_enabled": t.is_enabled},
            created_at=datetime.utcnow(),
        ))
        db.flush()
    except Exception:
        logger.warning("审计日志写入失败")
    db.commit()
    db.refresh(t)
    _invalidate()
    return {"ok": True, "agent_id": agent_id, "is_enabled": t.is_enabled}


# ── 9. 克隆 ──
@router.post("/{agent_id}/clone")
def clone_template(
    agent_id: str,
    new_agent_id: str = Query(..., min_length=3, max_length=32),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    if not AGENT_ID_PATTERN.match(new_agent_id):
        raise HTTPException(400, "new_agent_id 格式无效")

    existing = db.query(AgentTemplate).filter(AgentTemplate.agent_id == new_agent_id).first()
    if existing:
        raise HTTPException(409, f"agent_id '{new_agent_id}' 已存在")

    src = db.query(AgentTemplate).filter(AgentTemplate.agent_id == agent_id).first()
    if not src:
        raise HTTPException(404, f"源模板 '{agent_id}' 不存在")

    clone = AgentTemplate(
        agent_id=new_agent_id,
        display_name=f"{src.display_name} (副本)",
        agent_type="dynamic_llm",
        domain_enum=None,
        description=src.description,
        keywords=list(src.keywords or []),
        data_fields=list(src.data_fields or []),
        correlations=list(src.correlations or []),
        priority=src.priority,
        base_weight=src.base_weight,
        enable_llm=src.enable_llm,
        system_prompt=src.system_prompt,
        conflict_wins_over=list(src.conflict_wins_over or []),
        is_preset=False,
        is_enabled=True,
        created_by=admin.id,
    )
    db.add(clone)
    try:
        db.add(UserActivityLog(
            user_id=admin.id,
            activity_type="agent_tpl.clone",
            detail={"source": agent_id, "new_id": new_agent_id},
            created_at=datetime.utcnow(),
        ))
        db.flush()
    except Exception:
        logger.warning("审计日志写入失败")
    db.commit()
    db.refresh(clone)
    _invalidate()
    return _template_to_dict(clone)


# ── 10. 刷新缓存 ──
@router.post("/refresh-cache")
def refresh_cache(
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    from core.agent_template_service import load_templates
    templates = load_templates(db)
    return {"ok": True, "count": len(templates)}

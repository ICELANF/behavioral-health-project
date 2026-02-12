"""
Phase 5: Agent 生态服务

提供:
- Marketplace: 发布/浏览/安装 Agent 模板
- Composition: Agent 组合编排 CRUD
- Growth Points: Agent 成长积分 (与六级体系打通)
"""

import logging
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session
from sqlalchemy import func

from core.models import (
    AgentMarketplaceListing, AgentComposition, AgentGrowthPoints,
    AgentTemplate, User,
)

logger = logging.getLogger(__name__)

# ── 成长积分事件配置 ──
GROWTH_POINT_EVENTS = {
    "create_agent": 20,       # 创建自定义 Agent
    "optimize_prompt": 10,    # 优化 Prompt
    "share_knowledge": 15,    # 贡献知识到共享池
    "template_published": 30, # 模板发布到市场
    "template_installed": 5,  # 模板被他人安装 (每次)
    "feedback_positive": 3,   # 获得正面反馈
    "composition_created": 15,# 创建 Agent 组合
}


# ── Marketplace ──

def publish_to_marketplace(
    db: Session,
    template_id: int,
    publisher_id: int,
    tenant_id: str,
    title: str,
    description: str = "",
    category: str = "",
    tags: list = None,
) -> AgentMarketplaceListing:
    """将 Agent 模板发布到市场 (提交审核)"""
    tpl = db.query(AgentTemplate).filter(AgentTemplate.id == template_id).first()
    if not tpl:
        raise ValueError("模板不存在")

    # 检查是否已发布
    existing = db.query(AgentMarketplaceListing).filter(
        AgentMarketplaceListing.template_id == template_id,
        AgentMarketplaceListing.status.in_(["draft", "submitted", "published"]),
    ).first()
    if existing:
        raise ValueError(f"该模板已有市场记录 (status={existing.status})")

    listing = AgentMarketplaceListing(
        template_id=template_id,
        publisher_id=publisher_id,
        tenant_id=tenant_id,
        title=title,
        description=description,
        category=category,
        tags=tags or [],
        status="submitted",
    )
    db.add(listing)
    db.flush()

    # 成长积分
    _award_points(db, publisher_id, "template_published", tpl.agent_id,
                  listing.id, "agent_marketplace_listing")

    logger.info("Marketplace 发布: template=%d, publisher=%d", template_id, publisher_id)
    return listing


def approve_listing(
    db: Session,
    listing_id: int,
    reviewer_id: int,
    comment: str = "",
) -> AgentMarketplaceListing:
    """审核通过市场发布"""
    listing = db.query(AgentMarketplaceListing).filter(
        AgentMarketplaceListing.id == listing_id,
    ).first()
    if not listing:
        raise ValueError("市场记录不存在")
    if listing.status != "submitted":
        raise ValueError(f"状态不可审核 (当前={listing.status})")

    listing.status = "published"
    listing.reviewer_id = reviewer_id
    listing.review_comment = comment
    listing.reviewed_at = datetime.utcnow()
    db.flush()
    return listing


def reject_listing(
    db: Session,
    listing_id: int,
    reviewer_id: int,
    comment: str = "",
) -> AgentMarketplaceListing:
    """审核拒绝"""
    listing = db.query(AgentMarketplaceListing).filter(
        AgentMarketplaceListing.id == listing_id,
    ).first()
    if not listing:
        raise ValueError("记录不存在")
    if listing.status != "submitted":
        raise ValueError(f"状态不可审核 (当前={listing.status})")

    listing.status = "rejected"
    listing.reviewer_id = reviewer_id
    listing.review_comment = comment
    listing.reviewed_at = datetime.utcnow()
    db.flush()
    return listing


def install_template(
    db: Session,
    listing_id: int,
    installer_id: int,
    target_tenant_id: str,
) -> AgentTemplate:
    """安装市场模板 — 克隆到目标租户"""
    listing = db.query(AgentMarketplaceListing).filter(
        AgentMarketplaceListing.id == listing_id,
        AgentMarketplaceListing.status == "published",
    ).first()
    if not listing:
        raise ValueError("市场模板不存在或未发布")

    source_tpl = db.query(AgentTemplate).filter(
        AgentTemplate.id == listing.template_id,
    ).first()
    if not source_tpl:
        raise ValueError("源模板不存在")

    # 生成唯一 agent_id
    base_id = f"{source_tpl.agent_id}_clone"
    suffix = 1
    new_id = base_id
    while db.query(AgentTemplate).filter(AgentTemplate.agent_id == new_id).first():
        new_id = f"{base_id}_{suffix}"
        suffix += 1

    # 克隆模板
    new_tpl = AgentTemplate(
        agent_id=new_id,
        display_name=f"{source_tpl.display_name} (安装)",
        agent_type="dynamic_llm",
        domain_enum=source_tpl.domain_enum,
        description=f"从市场安装: {listing.title}",
        keywords=source_tpl.keywords,
        data_fields=source_tpl.data_fields,
        correlations=source_tpl.correlations,
        priority=source_tpl.priority,
        base_weight=source_tpl.base_weight,
        enable_llm=source_tpl.enable_llm,
        system_prompt=source_tpl.system_prompt,
        conflict_wins_over=source_tpl.conflict_wins_over,
        is_preset=False,
        is_enabled=True,
        created_by=installer_id,
    )
    db.add(new_tpl)

    # 更新安装计数
    listing.install_count = (listing.install_count or 0) + 1
    listing.updated_at = datetime.utcnow()

    # 成长积分: 给发布者
    _award_points(db, listing.publisher_id, "template_installed", source_tpl.agent_id,
                  listing.id, "agent_marketplace_listing")

    db.flush()
    logger.info("模板安装: listing=%d → %s, installer=%d", listing_id, new_id, installer_id)
    return new_tpl


def browse_marketplace(
    db: Session,
    category: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> dict:
    """浏览市场"""
    q = db.query(AgentMarketplaceListing).filter(
        AgentMarketplaceListing.status == "published",
    )
    if category:
        q = q.filter(AgentMarketplaceListing.category == category)
    if search:
        q = q.filter(
            AgentMarketplaceListing.title.ilike(f"%{search}%") |
            AgentMarketplaceListing.description.ilike(f"%{search}%")
        )

    total = q.count()
    items = q.order_by(AgentMarketplaceListing.install_count.desc()).offset(skip).limit(limit).all()
    return {"items": items, "total": total}


def list_pending_listings(db: Session, skip: int = 0, limit: int = 20) -> dict:
    """待审核列表"""
    q = db.query(AgentMarketplaceListing).filter(
        AgentMarketplaceListing.status == "submitted",
    )
    total = q.count()
    items = q.order_by(AgentMarketplaceListing.created_at.desc()).offset(skip).limit(limit).all()
    return {"items": items, "total": total}


# ── Composition ──

def create_composition(
    db: Session,
    name: str,
    pipeline: list,
    created_by: int,
    description: str = "",
    tenant_id: Optional[str] = None,
    merge_strategy: str = "weighted_average",
) -> AgentComposition:
    """创建 Agent 组合"""
    comp = AgentComposition(
        name=name,
        description=description,
        tenant_id=tenant_id,
        created_by=created_by,
        pipeline=pipeline,
        merge_strategy=merge_strategy,
    )
    db.add(comp)
    db.flush()

    _award_points(db, created_by, "composition_created", None,
                  comp.id, "agent_composition")

    logger.info("Agent 组合创建: name=%s, pipeline_len=%d", name, len(pipeline))
    return comp


def list_compositions(
    db: Session,
    tenant_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> dict:
    """列出 Agent 组合"""
    q = db.query(AgentComposition).filter(AgentComposition.is_enabled == True)
    if tenant_id:
        from sqlalchemy import or_
        q = q.filter(or_(
            AgentComposition.tenant_id == tenant_id,
            AgentComposition.tenant_id.is_(None),
        ))
    total = q.count()
    items = q.order_by(AgentComposition.created_at.desc()).offset(skip).limit(limit).all()
    return {"items": items, "total": total}


def get_composition(db: Session, composition_id: int) -> Optional[AgentComposition]:
    """获取组合详情"""
    return db.query(AgentComposition).filter(AgentComposition.id == composition_id).first()


# ── Growth Points ──

def _award_points(
    db: Session,
    user_id: int,
    event_type: str,
    agent_id: Optional[str],
    reference_id: Optional[int] = None,
    reference_type: Optional[str] = None,
):
    """内部: 发放成长积分"""
    points = GROWTH_POINT_EVENTS.get(event_type, 0)
    if points <= 0:
        return

    gp = AgentGrowthPoints(
        user_id=user_id,
        agent_id=agent_id,
        event_type=event_type,
        points=points,
        description=f"{event_type}: +{points}",
        reference_id=reference_id,
        reference_type=reference_type,
    )
    db.add(gp)


def award_points(
    db: Session,
    user_id: int,
    event_type: str,
    agent_id: Optional[str] = None,
    reference_id: Optional[int] = None,
    reference_type: Optional[str] = None,
) -> Optional[AgentGrowthPoints]:
    """公开: 发放成长积分"""
    points = GROWTH_POINT_EVENTS.get(event_type, 0)
    if points <= 0:
        return None

    gp = AgentGrowthPoints(
        user_id=user_id,
        agent_id=agent_id,
        event_type=event_type,
        points=points,
        description=f"{event_type}: +{points}",
        reference_id=reference_id,
        reference_type=reference_type,
    )
    db.add(gp)
    db.flush()
    return gp


def get_user_growth_points(db: Session, user_id: int) -> dict:
    """查询用户 Agent 成长积分"""
    total = db.query(func.sum(AgentGrowthPoints.points)).filter(
        AgentGrowthPoints.user_id == user_id,
    ).scalar() or 0

    by_event = dict(
        db.query(
            AgentGrowthPoints.event_type,
            func.sum(AgentGrowthPoints.points),
        ).filter(
            AgentGrowthPoints.user_id == user_id,
        ).group_by(AgentGrowthPoints.event_type).all()
    )

    # 最近记录
    recent = db.query(AgentGrowthPoints).filter(
        AgentGrowthPoints.user_id == user_id,
    ).order_by(AgentGrowthPoints.created_at.desc()).limit(10).all()

    return {
        "total_points": total,
        "by_event": by_event,
        "recent": [
            {
                "event_type": r.event_type,
                "points": r.points,
                "agent_id": r.agent_id,
                "description": r.description,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in recent
        ],
    }

"""
行智诊疗 API 端点
挂载路径: /api/v1/xzb/

已适配:
  - 使用平台 get_db / get_current_user 依赖
  - 同步 SQLAlchemy Session
  - 专家身份从 User.xzb_expert_id 关联
  - 29 端点: 专家管理(8) + 知识库(10) + 智伴交互(4) + 处方(4) + 医道汇(3)
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, select, update, func as sqlfunc
from sqlalchemy.orm import Session

from api.dependencies import get_db, get_current_user
from core.models import User
from core.xzb.xzb_models import (
    ActionType, KnowledgeType, RxStatus, XZBEvidenceTier,
    XZBConfig, XZBConversation, XZBExpertIntervention, XZBExpertProfile,
    XZBKnowledge, XZBKnowledgeRule, XZBRxFragment,
    XZBMedCircle, XZBMedCircleComment,
    ExpertRegisterRequest, ExpertProfileResponse,
    KnowledgeCreateRequest, RuleCreateRequest,
)

router = APIRouter(prefix="/api/v1/xzb", tags=["行智诊疗"])


# ─────────────────────────────────────────────
# 依赖: 当前登录专家
# ─────────────────────────────────────────────

def get_current_expert(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> XZBExpertProfile:
    """从 JWT 用户解析对应的 XZB 专家画像"""
    xzb_id = getattr(current_user, "xzb_expert_id", None)
    if not xzb_id:
        raise HTTPException(403, "当前用户未注册为行智诊疗专家")
    expert = db.execute(
        select(XZBExpertProfile).where(XZBExpertProfile.id == xzb_id)
    ).scalar_one_or_none()
    if not expert:
        raise HTTPException(404, "专家画像不存在")
    return expert


# ═══════════════════════════════════════════════
# §7.1 专家管理 API (8 端点)
# ═══════════════════════════════════════════════

@router.post("/experts/register", summary="专家注册（执照验证+智伴初始化）")
def register_expert(
    req: ExpertRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict:
    # 检查是否已注册
    existing = db.execute(
        select(XZBExpertProfile).where(XZBExpertProfile.user_id == current_user.id)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(400, "该用户已注册为行智诊疗专家")

    # 角色检查: 至少 coach 级别
    if current_user.role.value not in ["coach", "supervisor", "promoter", "master", "admin"]:
        raise HTTPException(403, "需要教练或以上角色才能注册为专家")

    profile = XZBExpertProfile(
        user_id=current_user.id,
        display_name=req.display_name,
        specialty=req.specialty,
        license_no=req.license_no,
        tcm_weight=req.tcm_weight,
        domain_tags=req.domain_tags,
    )
    db.add(profile)
    db.flush()

    config = XZBConfig(
        expert_id=profile.id,
        companion_name=req.companion_name,
        greeting=req.greeting or f"您好，我是{req.companion_name}，有什么可以帮助您的？",
        boundary_stmt=req.boundary_stmt or "我是AI健康助手，不替代专科就诊，如有紧急情况请立即就医。",
    )
    db.add(config)

    # 关联 User.xzb_expert_id
    current_user.xzb_expert_id = profile.id
    db.commit()

    return {"expert_id": str(profile.id), "status": "registered", "license_verified": False}


@router.get("/experts/me/profile", response_model=ExpertProfileResponse)
def get_my_profile(expert: XZBExpertProfile = Depends(get_current_expert)):
    return expert


@router.put("/experts/me/profile", summary="更新专家画像")
def update_my_profile(
    updates: Dict[str, Any],
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    allowed = {"display_name", "specialty", "tcm_weight", "domain_tags", "style_profile"}
    for key, val in updates.items():
        if key in allowed:
            setattr(expert, key, val)
    expert.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "updated"}


@router.get("/experts/me/config", summary="读取智伴配置")
def get_my_config(expert: XZBExpertProfile = Depends(get_current_expert)) -> Dict:
    if not expert.config:
        raise HTTPException(404, "智伴配置未初始化")
    c = expert.config
    return {
        "companion_name": c.companion_name, "greeting": c.greeting,
        "comm_style": c.comm_style, "boundary_stmt": c.boundary_stmt,
        "auto_rx_enabled": c.auto_rx_enabled, "dormant_mode": c.dormant_mode,
    }


@router.put("/experts/me/config", summary="更新智伴配置")
def update_my_config(
    updates: Dict[str, Any],
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    allowed = {"companion_name", "greeting", "comm_style", "boundary_stmt",
               "referral_rules", "auto_rx_enabled"}
    for key, val in updates.items():
        if key in allowed and expert.config:
            setattr(expert.config, key, val)
    db.commit()
    return {"status": "updated"}


@router.post("/experts/me/calibrate", summary="触发风格校准对话")
def start_calibration(expert: XZBExpertProfile = Depends(get_current_expert)) -> Dict:
    return {
        "session_id": str(uuid.uuid4()),
        "first_prompt": "请用您的方式解释：为什么餐后血糖会升高？",
        "total_rounds": 30,
    }


@router.get("/experts/me/dashboard", summary="专家工作台")
def get_dashboard(
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    pending_k = db.execute(
        select(sqlfunc.count(XZBKnowledge.id)).where(and_(
            XZBKnowledge.expert_id == expert.id,
            XZBKnowledge.expert_confirmed == False,  # noqa: E712
            XZBKnowledge.is_active == True,  # noqa: E712
        ))
    ).scalar() or 0

    pending_rx = db.execute(
        select(sqlfunc.count(XZBRxFragment.id)).where(and_(
            XZBRxFragment.expert_id == expert.id,
            XZBRxFragment.status == "submitted",
        ))
    ).scalar() or 0

    # 活跃求助者 (近30天有对话)
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(days=30)
    active_seekers = db.execute(
        select(sqlfunc.count(sqlfunc.distinct(XZBConversation.seeker_id))).where(and_(
            XZBConversation.expert_id == expert.id,
            XZBConversation.created_at >= cutoff,
        ))
    ).scalar() or 0

    # 最近对话
    recent_convs = db.execute(
        select(XZBConversation).where(XZBConversation.expert_id == expert.id)
        .order_by(XZBConversation.created_at.desc()).limit(5)
    ).scalars().all()

    # 知识库健康度
    total_k = db.execute(
        select(sqlfunc.count(XZBKnowledge.id)).where(and_(
            XZBKnowledge.expert_id == expert.id, XZBKnowledge.is_active == True,  # noqa: E712
        ))
    ).scalar() or 0
    confirmed_k = db.execute(
        select(sqlfunc.count(XZBKnowledge.id)).where(and_(
            XZBKnowledge.expert_id == expert.id,
            XZBKnowledge.is_active == True, XZBKnowledge.expert_confirmed == True,  # noqa: E712
        ))
    ).scalar() or 0
    health_score = round(confirmed_k / total_k, 2) if total_k > 0 else 0.0

    return {
        "pending_knowledge_confirmations": pending_k,
        "pending_rx_reviews": pending_rx,
        "active_seekers": active_seekers,
        "knowledge_health_score": health_score,
        "recent_conversations": [
            {"id": str(c.id), "seeker_id": c.seeker_id, "summary": c.summary,
             "rx_triggered": c.rx_triggered, "expert_intervened": c.expert_intervened,
             "created_at": c.created_at.isoformat() if c.created_at else None}
            for c in recent_convs
        ],
    }


@router.post("/experts/me/online", summary="设置在线时段")
def set_online(expert: XZBExpertProfile = Depends(get_current_expert),
               db: Session = Depends(get_db)) -> Dict:
    expert.last_active_at = datetime.utcnow()
    db.commit()
    return {"status": "online"}


# ═══════════════════════════════════════════════
# §7.2 知识库 API (10 端点)
# ═══════════════════════════════════════════════

@router.get("/knowledge", summary="知识条目列表")
def list_knowledge(
    type: Optional[KnowledgeType] = None,
    tag: Optional[str] = None,
    confirmed_only: bool = False,
    page: int = 1, page_size: int = 20,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    filters = [XZBKnowledge.expert_id == expert.id, XZBKnowledge.is_active == True]  # noqa: E712
    if type:
        filters.append(XZBKnowledge.type == type)
    if confirmed_only:
        filters.append(XZBKnowledge.expert_confirmed == True)  # noqa: E712
    if tag:
        filters.append(XZBKnowledge.tags.contains([tag]))

    items = db.execute(
        select(XZBKnowledge).where(and_(*filters))
        .order_by(XZBKnowledge.usage_count.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    return {
        "items": [{"id": str(k.id), "type": k.type, "tags": k.tags,
                   "evidence_tier": k.evidence_tier, "usage_count": k.usage_count,
                   "expert_confirmed": k.expert_confirmed} for k in items],
        "page": page, "page_size": page_size,
    }


@router.post("/knowledge", summary="新建知识条目")
def create_knowledge(
    req: KnowledgeCreateRequest,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    knowledge = XZBKnowledge(
        expert_id=expert.id, type=req.type, content=req.content,
        evidence_tier=req.evidence_tier, source=req.source, tags=req.tags,
        applicable_conditions=req.applicable_conditions,
        confidence_override=req.confidence_override,
        expires_at=req.expires_at, expert_confirmed=True,
    )
    db.add(knowledge)
    db.flush()

    # 实时向量化 — 不用等隔夜 Job
    try:
        from core.knowledge.embedding_service import EmbeddingService
        if req.content and len(req.content.strip()) >= 10:
            svc = EmbeddingService()
            vec = svc.embed_query(req.content)
            svc.close()
            if vec:
                from sqlalchemy import text as sa_text
                vec_str = "[" + ",".join(str(v) for v in vec) + "]"
                db.execute(sa_text(
                    "UPDATE xzb_knowledge SET vector_embedding_1024 = CAST(:vec AS vector(1024)) WHERE id = :kid"
                ), {"vec": vec_str, "kid": str(knowledge.id)})
    except Exception:
        pass  # 静默失败，Job 38 会补上

    db.commit()
    return {"id": str(knowledge.id), "status": "created"}


@router.get("/knowledge/{knowledge_id}", summary="读取单条知识")
def get_knowledge(
    knowledge_id: UUID,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    k = db.execute(
        select(XZBKnowledge).where(and_(
            XZBKnowledge.id == knowledge_id, XZBKnowledge.expert_id == expert.id,
        ))
    ).scalar_one_or_none()
    if not k:
        raise HTTPException(404, "知识条目不存在")
    return {
        "id": str(k.id), "type": k.type, "content": k.content,
        "evidence_tier": k.evidence_tier, "source": k.source,
        "tags": k.tags, "usage_count": k.usage_count,
        "expert_confirmed": k.expert_confirmed,
    }


@router.put("/knowledge/{knowledge_id}", summary="更新单条知识")
def update_knowledge(
    knowledge_id: UUID, updates: Dict[str, Any],
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    k = db.execute(
        select(XZBKnowledge).where(and_(
            XZBKnowledge.id == knowledge_id, XZBKnowledge.expert_id == expert.id,
        ))
    ).scalar_one_or_none()
    if not k:
        raise HTTPException(404, "知识条目不存在")
    allowed = {"content", "evidence_tier", "tags", "applicable_conditions",
               "confidence_override", "expires_at"}
    for key, val in updates.items():
        if key in allowed:
            setattr(k, key, val)
    if "content" in updates:
        k.vector_embedding = None  # 标记待重新嵌入 (Job 38 处理)
    k.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "updated"}


@router.delete("/knowledge/{knowledge_id}", summary="删除知识条目（软删除）")
def delete_knowledge(
    knowledge_id: UUID,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    db.execute(
        update(XZBKnowledge)
        .where(and_(XZBKnowledge.id == knowledge_id, XZBKnowledge.expert_id == expert.id))
        .values(is_active=False, updated_at=datetime.utcnow())
    )
    db.commit()
    return {"status": "deleted"}


@router.get("/knowledge/pending-confirm", summary="对话沉淀待确认知识")
def list_pending_confirmations(
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    items = db.execute(
        select(XZBKnowledge).where(and_(
            XZBKnowledge.expert_id == expert.id,
            XZBKnowledge.expert_confirmed == False,  # noqa: E712
            XZBKnowledge.is_active == True,  # noqa: E712
        )).order_by(XZBKnowledge.created_at.desc())
    ).scalars().all()
    return {
        "count": len(items),
        "items": [{"id": str(k.id), "content": k.content[:200],
                   "source": k.source, "created_at": k.created_at.isoformat() if k.created_at else None}
                  for k in items],
    }


@router.post("/knowledge/{knowledge_id}/confirm", summary="确认/拒绝知识入库")
def confirm_knowledge(
    knowledge_id: UUID,
    action: str = Query(..., pattern="^(confirm|reject)$"),
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    k = db.execute(
        select(XZBKnowledge).where(and_(
            XZBKnowledge.id == knowledge_id, XZBKnowledge.expert_id == expert.id,
        ))
    ).scalar_one_or_none()
    if not k:
        raise HTTPException(404)
    if action == "confirm":
        k.expert_confirmed = True
    else:
        k.is_active = False
    db.commit()
    return {"status": "confirmed" if action == "confirm" else "rejected"}


@router.get("/knowledge/rules", summary="诊疗规则列表")
def list_rules(
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    rules = db.execute(
        select(XZBKnowledgeRule).where(XZBKnowledgeRule.expert_id == expert.id)
        .order_by(XZBKnowledgeRule.priority.desc())
    ).scalars().all()
    return {
        "items": [{"id": str(r.id), "rule_name": r.rule_name, "action_type": r.action_type,
                   "priority": r.priority, "overrides_llm": r.overrides_llm, "is_active": r.is_active}
                  for r in rules]
    }


@router.post("/knowledge/rules", summary="新建诊疗规则")
def create_rule(
    req: RuleCreateRequest,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    rule = XZBKnowledgeRule(
        expert_id=expert.id, rule_name=req.rule_name,
        condition_json=req.condition_json, action_type=req.action_type,
        action_content=req.action_content, priority=req.priority,
        overrides_llm=req.overrides_llm,
    )
    db.add(rule)
    db.commit()
    return {"id": str(rule.id), "status": "created"}


@router.get("/knowledge/health-report", summary="知识库健康度报告")
def knowledge_health_report(
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    from sqlalchemy import Integer as SAInt, cast
    row = db.execute(
        select(
            sqlfunc.count(XZBKnowledge.id).label("total"),
            sqlfunc.sum(cast(XZBKnowledge.expert_confirmed == True, SAInt)).label("confirmed"),
            sqlfunc.sum(cast(XZBKnowledge.needs_review == True, SAInt)).label("needs_review"),
        ).where(and_(
            XZBKnowledge.expert_id == expert.id, XZBKnowledge.is_active == True,  # noqa: E712
        ))
    ).one()
    total = row.total or 0
    confirmed = row.confirmed or 0
    needs_review = row.needs_review or 0
    return {
        "total": total, "confirmed": confirmed, "needs_review": needs_review,
        "coverage_rate": round(confirmed / total, 2) if total > 0 else 0.0,
        "freshness_rate": round((total - needs_review) / total, 2) if total > 0 else 0.0,
    }


# ═══════════════════════════════════════════════
# §7.3 智伴交互 API (4 端点)
# ═══════════════════════════════════════════════

@router.get("/chat/{conversation_id}/history", summary="对话历史")
def get_conversation_history(conversation_id: UUID, db: Session = Depends(get_db)) -> Dict:
    conv = db.execute(
        select(XZBConversation).where(XZBConversation.id == conversation_id)
    ).scalar_one_or_none()
    if not conv:
        raise HTTPException(404)
    return {
        "conversation_id": str(conv.id), "summary": conv.summary,
        "rx_triggered": conv.rx_triggered, "expert_intervened": conv.expert_intervened,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
    }


@router.post("/chat/me/intervene/{conversation_id}", summary="专家接管对话")
def expert_intervene(
    conversation_id: UUID, content: str = "",
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    conv = db.execute(
        select(XZBConversation).where(and_(
            XZBConversation.id == conversation_id, XZBConversation.expert_id == expert.id,
        ))
    ).scalar_one_or_none()
    if not conv:
        raise HTTPException(404)
    conv.expert_intervened = True
    db.add(XZBExpertIntervention(
        conversation_id=conversation_id, expert_id=expert.id,
        intervention_type="takeover", content=content,
    ))
    db.commit()
    return {"status": "intervened"}


@router.post("/chat/me/async-reply/{conversation_id}", summary="专家异步回复")
def async_reply(
    conversation_id: UUID, content: str = "",
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    conv = db.execute(
        select(XZBConversation).where(XZBConversation.id == conversation_id)
    ).scalar_one_or_none()
    if not conv:
        raise HTTPException(404)
    db.add(XZBExpertIntervention(
        conversation_id=conversation_id, expert_id=expert.id,
        intervention_type="async_reply", content=content,
    ))
    db.commit()
    return {"status": "sent"}


# ═══════════════════════════════════════════════
# §7.4 处方 API (4 端点)
# ═══════════════════════════════════════════════

class ManualRxTriggerReq(BaseModel):
    template_id: Optional[UUID] = None
    custom_strategies: List[Dict] = []
    note: Optional[str] = None


@router.post("/rx/trigger/{seeker_id}", summary="专家主动触发处方草案")
def manual_trigger_rx(
    seeker_id: int, req: ManualRxTriggerReq,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    conv = XZBConversation(expert_id=expert.id, seeker_id=seeker_id)
    db.add(conv)
    db.flush()
    fragment = XZBRxFragment(
        conversation_id=conv.id, expert_id=expert.id, seeker_id=seeker_id,
        source="xzb_expert", priority=0, strategies=req.custom_strategies,
        requires_coach_review=True, status="draft",
    )
    db.add(fragment)
    db.commit()
    return {"fragment_id": str(fragment.id), "status": "draft", "next": "coach_review"}


@router.get("/rx/templates", summary="专家个人处方模板库")
def list_rx_templates(
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    items = db.execute(
        select(XZBKnowledge).where(and_(
            XZBKnowledge.expert_id == expert.id,
            XZBKnowledge.type == KnowledgeType.template,
            XZBKnowledge.is_active == True,  # noqa: E712
        ))
    ).scalars().all()
    return {
        "count": len(items),
        "templates": [{"id": str(t.id), "tags": t.tags, "evidence_tier": t.evidence_tier} for t in items],
    }


@router.post("/rx/templates", summary="新建专家处方模板")
def create_rx_template(
    req: KnowledgeCreateRequest,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    template = XZBKnowledge(
        expert_id=expert.id, type=KnowledgeType.template,
        content=req.content, evidence_tier=req.evidence_tier,
        source=req.source, tags=req.tags,
        applicable_conditions=req.applicable_conditions,
        expert_confirmed=True,
    )
    db.add(template)
    db.commit()
    return {"id": str(template.id), "status": "created"}


@router.get("/rx/{rx_id}/expert-source", summary="查看处方中专家贡献详情")
def get_expert_rx_source(rx_id: UUID, db: Session = Depends(get_db)) -> Dict:
    fragment = db.execute(
        select(XZBRxFragment).where(XZBRxFragment.rx_id == rx_id)
    ).scalar_one_or_none()
    if not fragment:
        return {"has_expert_source": False}
    return {
        "has_expert_source": True, "fragment_id": str(fragment.id),
        "expert_id": str(fragment.expert_id), "evidence_tier": fragment.evidence_tier,
        "domain": fragment.domain,
        "knowledge_refs": [str(k) for k in (fragment.knowledge_refs or [])],
        "status": fragment.status,
    }


# ═══════════════════════════════════════════════
# §7.5 医道汇 API (3 端点)
# ═══════════════════════════════════════════════

@router.get("/med-circle", summary="医道汇帖子列表")
def list_med_circle(
    page: int = 1, page_size: int = 20,
    db: Session = Depends(get_db),
) -> Dict:
    items = db.execute(
        select(XZBMedCircle).where(XZBMedCircle.is_published == True)  # noqa: E712
        .order_by(XZBMedCircle.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    return {
        "items": [{"id": str(p.id), "title": p.title, "post_type": p.post_type,
                   "tags": p.tags, "view_count": p.view_count, "like_count": p.like_count}
                  for p in items],
        "page": page, "page_size": page_size,
    }


@router.post("/med-circle", summary="发布帖子")
def create_med_circle_post(
    title: str, content: str, post_type: str = "discussion",
    tags: List[str] = [],
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    post = XZBMedCircle(
        author_id=expert.id, title=title, content=content,
        post_type=post_type, tags=tags, is_published=True,
    )
    db.add(post)
    db.commit()
    return {"id": str(post.id), "status": "published"}


@router.post("/med-circle/{post_id}/comment", summary="评论帖子")
def comment_on_post(
    post_id: UUID, content: str, parent_id: Optional[UUID] = None,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    comment = XZBMedCircleComment(
        post_id=post_id, author_id=expert.id,
        content=content, parent_id=parent_id,
    )
    db.add(comment)
    db.commit()
    return {"id": str(comment.id), "status": "created"}


# ═══════════════════════════════════════════════
# §7.6 求助者管理 API (5 端点)
# ═══════════════════════════════════════════════

@router.get("/seekers", summary="求助者列表（该专家的全部服务对象）")
def list_seekers(
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    """通过 xzb_conversations 汇聚该专家的所有求助者"""
    rows = db.execute(
        select(
            XZBConversation.seeker_id,
            sqlfunc.count(XZBConversation.id).label("conv_count"),
            sqlfunc.max(XZBConversation.created_at).label("last_conv_at"),
            sqlfunc.bool_or(XZBConversation.rx_triggered).label("has_rx"),
        ).where(XZBConversation.expert_id == expert.id)
        .group_by(XZBConversation.seeker_id)
        .order_by(sqlfunc.max(XZBConversation.created_at).desc())
    ).all()

    seeker_ids = [r.seeker_id for r in rows]
    users_map: Dict[int, Any] = {}
    if seeker_ids:
        users = db.execute(
            select(User).where(User.id.in_(seeker_ids))
        ).scalars().all()
        users_map = {u.id: u for u in users}

    items = []
    for r in rows:
        u = users_map.get(r.seeker_id)
        items.append({
            "seeker_id": r.seeker_id,
            "name": u.full_name or u.username if u else f"用户{r.seeker_id}",
            "conv_count": r.conv_count,
            "last_conv_at": r.last_conv_at.isoformat() if r.last_conv_at else None,
            "has_rx": r.has_rx or False,
            "stage": getattr(u, "current_stage", None) if u else None,
            "adherence_rate": getattr(u, "adherence_rate", None) if u else None,
        })

    return {"items": items, "total": len(items)}


@router.get("/seekers/{seeker_id}/detail", summary="求助者详情")
def get_seeker_detail(
    seeker_id: int,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    user = db.execute(select(User).where(User.id == seeker_id)).scalar_one_or_none()
    if not user:
        raise HTTPException(404, "用户不存在")

    # 对话统计
    conv_count = db.execute(
        select(sqlfunc.count(XZBConversation.id)).where(and_(
            XZBConversation.expert_id == expert.id,
            XZBConversation.seeker_id == seeker_id,
        ))
    ).scalar() or 0

    # 处方统计
    rx_count = db.execute(
        select(sqlfunc.count(XZBRxFragment.id)).where(and_(
            XZBRxFragment.expert_id == expert.id,
            XZBRxFragment.seeker_id == seeker_id,
        ))
    ).scalar() or 0

    profile = user.profile if hasattr(user, "profile") and user.profile else {}

    return {
        "seeker_id": user.id,
        "name": user.full_name or user.username,
        "gender": getattr(user, "gender", None),
        "stage": getattr(user, "current_stage", None),
        "adherence_rate": getattr(user, "adherence_rate", None),
        "health_competency": getattr(user, "health_competency_level", None),
        "trust_score": getattr(user, "trust_score", None),
        "chronic_conditions": profile.get("chronic_conditions", []) if isinstance(profile, dict) else [],
        "goals": profile.get("goals", []) if isinstance(profile, dict) else [],
        "conv_count": conv_count,
        "rx_count": rx_count,
        "created_at": user.created_at.isoformat() if hasattr(user, "created_at") and user.created_at else None,
    }


@router.get("/seekers/{seeker_id}/conversations", summary="某求助者的对话列表")
def list_seeker_conversations(
    seeker_id: int,
    page: int = 1, page_size: int = 20,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    convs = db.execute(
        select(XZBConversation).where(and_(
            XZBConversation.expert_id == expert.id,
            XZBConversation.seeker_id == seeker_id,
        )).order_by(XZBConversation.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    return {
        "items": [
            {"id": str(c.id), "summary": c.summary, "rx_triggered": c.rx_triggered,
             "expert_intervened": c.expert_intervened, "knowledge_mined": c.knowledge_mined,
             "ttm_stage": c.ttm_stage_at_start,
             "created_at": c.created_at.isoformat() if c.created_at else None,
             "ended_at": c.ended_at.isoformat() if c.ended_at else None}
            for c in convs
        ],
        "page": page,
    }


@router.get("/conversations", summary="专家全部对话列表")
def list_expert_conversations(
    page: int = 1, page_size: int = 20,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    convs = db.execute(
        select(XZBConversation).where(XZBConversation.expert_id == expert.id)
        .order_by(XZBConversation.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    # 批量获取求助者名称
    seeker_ids = list(set(c.seeker_id for c in convs))
    users_map: Dict[int, Any] = {}
    if seeker_ids:
        users = db.execute(select(User).where(User.id.in_(seeker_ids))).scalars().all()
        users_map = {u.id: u for u in users}

    return {
        "items": [
            {"id": str(c.id), "seeker_id": c.seeker_id,
             "seeker_name": (users_map.get(c.seeker_id).full_name or users_map.get(c.seeker_id).username)
                if users_map.get(c.seeker_id) else f"用户{c.seeker_id}",
             "summary": c.summary, "rx_triggered": c.rx_triggered,
             "expert_intervened": c.expert_intervened,
             "created_at": c.created_at.isoformat() if c.created_at else None}
            for c in convs
        ],
        "page": page,
    }


@router.get("/seekers/{seeker_id}/health-summary", summary="求助者健康数据摘要（代理）")
def get_seeker_health_summary(
    seeker_id: int,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    """代理查询求助者的健康数据摘要，需验证专家有该求助者的对话记录"""
    has_relation = db.execute(
        select(sqlfunc.count(XZBConversation.id)).where(and_(
            XZBConversation.expert_id == expert.id,
            XZBConversation.seeker_id == seeker_id,
        ))
    ).scalar() or 0
    if not has_relation:
        raise HTTPException(403, "无权查看该用户的健康数据")

    # 查询健康数据表 (graceful fallback)
    summary: Dict[str, Any] = {"seeker_id": seeker_id, "has_data": False}
    try:
        from sqlalchemy import text as sa_text
        # 最近血糖
        glucose = db.execute(sa_text("""
            SELECT value, recorded_at FROM health_glucose
            WHERE user_id = :uid ORDER BY recorded_at DESC LIMIT 7
        """), {"uid": seeker_id}).fetchall()
        if glucose:
            summary["has_data"] = True
            summary["glucose"] = [{"value": float(g.value), "time": g.recorded_at.isoformat()} for g in glucose]

        # 最近体重
        weight = db.execute(sa_text("""
            SELECT weight_kg, recorded_at FROM health_vitals
            WHERE user_id = :uid AND weight_kg IS NOT NULL
            ORDER BY recorded_at DESC LIMIT 7
        """), {"uid": seeker_id}).fetchall()
        if weight:
            summary["has_data"] = True
            summary["weight"] = [{"value": float(w.weight_kg), "time": w.recorded_at.isoformat()} for w in weight]

        # 最近睡眠
        sleep = db.execute(sa_text("""
            SELECT duration_min, quality_score, recorded_at FROM health_sleep
            WHERE user_id = :uid ORDER BY recorded_at DESC LIMIT 7
        """), {"uid": seeker_id}).fetchall()
        if sleep:
            summary["has_data"] = True
            summary["sleep"] = [{"duration": s.duration_min, "quality": s.quality_score,
                                 "time": s.recorded_at.isoformat()} for s in sleep]
    except Exception:
        pass  # 表不存在时静默

    return summary


# ═══════════════════════════════════════════════
# §7.7 常见问题库 FAQ API (4 端点)
# ═══════════════════════════════════════════════

class FAQCreateRequest(BaseModel):
    question: str = Field(..., min_length=5)
    answer: str = Field(..., min_length=10)
    domain: str = "general"
    tags: List[str] = []
    linked_rx_template_id: Optional[UUID] = None


@router.get("/faq", summary="常见问题列表")
def list_faq(
    domain: Optional[str] = None,
    page: int = 1, page_size: int = 20,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    """FAQ 存储在 xzb_knowledge 表中, type='faq', content 为 JSON {question, answer}"""
    filters = [XZBKnowledge.expert_id == expert.id, XZBKnowledge.type == "faq",
               XZBKnowledge.is_active == True]  # noqa: E712
    if domain:
        filters.append(XZBKnowledge.tags.contains([domain]))

    items = db.execute(
        select(XZBKnowledge).where(and_(*filters))
        .order_by(XZBKnowledge.usage_count.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()

    results = []
    import json
    for k in items:
        try:
            qa = json.loads(k.content) if isinstance(k.content, str) else k.content
        except (json.JSONDecodeError, TypeError):
            qa = {"question": k.content[:100] if k.content else "", "answer": k.content or ""}
        results.append({
            "id": str(k.id), "question": qa.get("question", ""),
            "answer": qa.get("answer", ""), "domain": (k.tags or ["general"])[0],
            "tags": k.tags, "usage_count": k.usage_count,
            "linked_rx_template_id": None,
        })

    return {"items": results, "total": len(results)}


@router.post("/faq", summary="新建常见问题")
def create_faq(
    req: FAQCreateRequest,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    import json
    content_json = json.dumps({"question": req.question, "answer": req.answer}, ensure_ascii=False)
    knowledge = XZBKnowledge(
        expert_id=expert.id, type="faq", content=content_json,
        evidence_tier="expert_opinion", source="expert_manual",
        tags=[req.domain] + req.tags, expert_confirmed=True,
    )
    db.add(knowledge)
    db.flush()

    # 实时向量化
    try:
        from core.knowledge.embedding_service import EmbeddingService
        svc = EmbeddingService()
        vec = svc.embed_query(f"{req.question} {req.answer}")
        svc.close()
        if vec:
            from sqlalchemy import text as sa_text
            vec_str = "[" + ",".join(str(v) for v in vec) + "]"
            db.execute(sa_text(
                "UPDATE xzb_knowledge SET vector_embedding_1024 = CAST(:vec AS vector(1024)) WHERE id = :kid"
            ), {"vec": vec_str, "kid": str(knowledge.id)})
    except Exception:
        pass

    db.commit()
    return {"id": str(knowledge.id), "status": "created"}


@router.put("/faq/{faq_id}", summary="更新常见问题")
def update_faq(
    faq_id: UUID,
    req: FAQCreateRequest,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    import json
    k = db.execute(
        select(XZBKnowledge).where(and_(
            XZBKnowledge.id == faq_id, XZBKnowledge.expert_id == expert.id,
            XZBKnowledge.type == "faq",
        ))
    ).scalar_one_or_none()
    if not k:
        raise HTTPException(404, "FAQ不存在")
    k.content = json.dumps({"question": req.question, "answer": req.answer}, ensure_ascii=False)
    k.tags = [req.domain] + req.tags
    k.vector_embedding = None  # 标记待重新嵌入
    k.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "updated"}


@router.delete("/faq/{faq_id}", summary="删除常见问题")
def delete_faq(
    faq_id: UUID,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: Session = Depends(get_db),
) -> Dict:
    db.execute(
        update(XZBKnowledge)
        .where(and_(XZBKnowledge.id == faq_id, XZBKnowledge.expert_id == expert.id,
                     XZBKnowledge.type == "faq"))
        .values(is_active=False, updated_at=datetime.utcnow())
    )
    db.commit()
    return {"status": "deleted"}

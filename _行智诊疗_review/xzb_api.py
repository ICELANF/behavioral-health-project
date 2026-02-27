"""
行诊智伴 API 端点（文档 §7）
- 专家管理 API  §7.1
- 知识库 API    §7.2
- 智伴交互 API  §7.3
- 处方 API 扩展 §7.4

挂载路径: /api/v1/xzb/
"""
from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from xzb.models.xzb_models import (
    ActionType, EvidenceTier, KnowledgeType, RxStatus,
    XZBConfig, XZBConversation, XZBExpertIntervention, XZBExpertProfile,
    XZBKnowledge, XZBKnowledgeRule, XZBRxFragment,
    ExpertRegisterRequest, ExpertProfileResponse,
    KnowledgeCreateRequest, KnowledgeResponse, RuleCreateRequest,
)

router = APIRouter(prefix="/api/v1/xzb", tags=["行诊智伴"])


# ─────────────────────────────────────────────
# 依赖注入（实际实现需对接平台现有认证体系）
# ─────────────────────────────────────────────

async def get_db() -> AsyncSession:
    """数据库会话（替换为平台现有 get_db）"""
    raise NotImplementedError

async def get_current_expert(db: AsyncSession = Depends(get_db)) -> XZBExpertProfile:
    """当前登录专家（替换为平台现有 JWT 验证）"""
    raise NotImplementedError

async def get_embed_service():
    """向量嵌入服务（复用平台 text2vec-base-chinese）"""
    raise NotImplementedError


# ═══════════════════════════════════════════════
# §7.1 专家管理 API
# ═══════════════════════════════════════════════

expert_router = APIRouter(prefix="/experts")


class ExpertRegisterReq(BaseModel):
    display_name: str
    specialty: Optional[str] = None
    license_no: Optional[str] = None
    tcm_weight: float = Field(0.5, ge=0.0, le=1.0)
    domain_tags: List[str] = []
    companion_name: str
    greeting: Optional[str] = None
    boundary_stmt: Optional[str] = None

class StyleCalibrationResp(BaseModel):
    session_id: str
    first_prompt: str
    total_rounds: int = 30

class DashboardResp(BaseModel):
    pending_knowledge_confirmations: int
    pending_rx_reviews: int
    active_seekers: int
    knowledge_health_score: float
    recent_conversations: List[Dict]


@expert_router.post("/register", summary="专家注册（执照验证+智伴初始化）")
async def register_expert(
    req: ExpertRegisterReq,
    db: AsyncSession = Depends(get_db),
) -> Dict:
    # 检查是否已注册
    existing = await db.execute(
        select(XZBExpertProfile).where(
            XZBExpertProfile.user_id == uuid.uuid4()  # 替换为 current_user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "该用户已注册为领域专家")

    # 创建专家画像
    profile = XZBExpertProfile(
        user_id=uuid.uuid4(),   # current_user.id
        display_name=req.display_name,
        specialty=req.specialty,
        license_no=req.license_no,
        tcm_weight=req.tcm_weight,
        domain_tags=req.domain_tags,
    )
    db.add(profile)
    await db.flush()

    # 初始化智伴配置
    config = XZBConfig(
        expert_id=profile.id,
        companion_name=req.companion_name,
        greeting=req.greeting or f"您好，我是{req.companion_name}，有什么可以帮助您的？",
        boundary_stmt=req.boundary_stmt or "我是AI健康助手，不替代专科就诊，如有紧急情况请立即就医。",
    )
    db.add(config)
    await db.commit()

    return {"expert_id": str(profile.id), "status": "registered", "license_verified": False}


@expert_router.get("/me/profile", response_model=ExpertProfileResponse)
async def get_my_profile(expert: XZBExpertProfile = Depends(get_current_expert)) -> XZBExpertProfile:
    return expert


@expert_router.put("/me/profile", summary="更新专家画像")
async def update_my_profile(
    updates: Dict[str, Any],
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    allowed_fields = {"display_name", "specialty", "tcm_weight", "domain_tags", "style_profile"}
    for key, val in updates.items():
        if key in allowed_fields:
            setattr(expert, key, val)
    expert.updated_at = datetime.utcnow()
    await db.commit()
    return {"status": "updated"}


@expert_router.get("/me/config", summary="读取智伴配置")
async def get_my_config(
    expert: XZBExpertProfile = Depends(get_current_expert),
) -> Dict:
    if not expert.config:
        raise HTTPException(404, "智伴配置未初始化")
    return {
        "companion_name": expert.config.companion_name,
        "greeting": expert.config.greeting,
        "comm_style": expert.config.comm_style,
        "boundary_stmt": expert.config.boundary_stmt,
        "auto_rx_enabled": expert.config.auto_rx_enabled,
        "dormant_mode": expert.config.dormant_mode,
    }


@expert_router.put("/me/config", summary="更新智伴配置")
async def update_my_config(
    updates: Dict[str, Any],
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    allowed = {"companion_name", "greeting", "comm_style", "boundary_stmt",
               "referral_rules", "auto_rx_enabled"}
    for key, val in updates.items():
        if key in allowed and expert.config:
            setattr(expert.config, key, val)
    await db.commit()

    # 主动失效 Redis 缓存
    # await redis.delete(f"xzb:config:{expert.config.id}")
    return {"status": "updated"}


@expert_router.post("/me/calibrate", summary="触发风格校准对话", response_model=StyleCalibrationResp)
async def start_calibration(
    expert: XZBExpertProfile = Depends(get_current_expert),
) -> StyleCalibrationResp:
    session_id = str(uuid.uuid4())
    return StyleCalibrationResp(
        session_id=session_id,
        first_prompt="请用您的方式解释：为什么餐后血糖会升高？",
        total_rounds=30,
    )


@expert_router.get("/me/dashboard", response_model=DashboardResp, summary="专家工作台")
async def get_dashboard(
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
) -> DashboardResp:
    # 待确认知识数量
    pending_knowledge = await db.execute(
        select(XZBKnowledge)
        .where(and_(
            XZBKnowledge.expert_id == expert.id,
            XZBKnowledge.expert_confirmed == False,  # noqa
            XZBKnowledge.is_active == True,
        ))
    )
    pending_k_count = len(pending_knowledge.scalars().all())

    # 待审核处方数量
    pending_rx = await db.execute(
        select(XZBRxFragment)
        .where(and_(
            XZBRxFragment.expert_id == expert.id,
            XZBRxFragment.status == RxStatus.submitted,
        ))
    )
    pending_rx_count = len(pending_rx.scalars().all())

    return DashboardResp(
        pending_knowledge_confirmations=pending_k_count,
        pending_rx_reviews=pending_rx_count,
        active_seekers=0,               # TODO: 从 conversations 统计
        knowledge_health_score=0.85,    # TODO: 从健康检查任务获取
        recent_conversations=[],
    )


@expert_router.post("/me/online", summary="设置在线时段")
async def set_online(
    online_until: Optional[datetime] = None,
    expert: XZBExpertProfile = Depends(get_current_expert),
) -> Dict:
    # 写入 Redis: xzb:expert:{id}:online  TTL=5min sliding
    # await redis.setex(f"xzb:expert:{expert.id}:online", 300, "1")
    return {"status": "online", "until": online_until}


@expert_router.delete("/me/online", summary="取消在线时段")
async def set_offline(expert: XZBExpertProfile = Depends(get_current_expert)) -> Dict:
    # await redis.delete(f"xzb:expert:{expert.id}:online")
    return {"status": "offline"}


# ═══════════════════════════════════════════════
# §7.2 知识库 API
# ═══════════════════════════════════════════════

knowledge_router = APIRouter(prefix="/knowledge")


class KnowledgeIngestReq(BaseModel):
    file_type: str = Field(..., pattern="^(pdf|word|txt)$")
    source_url: Optional[str] = None
    tags: List[str] = []
    auto_confirm: bool = False  # 是否跳过二次确认（仅文档导入可用）


@knowledge_router.get("", summary="知识条目列表")
async def list_knowledge(
    type: Optional[KnowledgeType] = None,
    tag: Optional[str] = None,
    confirmed_only: bool = False,
    page: int = 1,
    page_size: int = 20,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    filters = [
        XZBKnowledge.expert_id == expert.id,
        XZBKnowledge.is_active == True,   # noqa
    ]
    if type:
        filters.append(XZBKnowledge.type == type)
    if confirmed_only:
        filters.append(XZBKnowledge.expert_confirmed == True)   # noqa
    if tag:
        filters.append(XZBKnowledge.tags.contains([tag]))

    result = await db.execute(
        select(XZBKnowledge)
        .where(and_(*filters))
        .order_by(XZBKnowledge.usage_count.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = result.scalars().all()
    return {
        "items": [{"id": str(k.id), "type": k.type, "tags": k.tags,
                   "evidence_tier": k.evidence_tier, "usage_count": k.usage_count,
                   "expert_confirmed": k.expert_confirmed} for k in items],
        "page": page,
        "page_size": page_size,
    }


@knowledge_router.post("", summary="新建知识条目")
async def create_knowledge(
    req: KnowledgeCreateRequest,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
    embed_svc=Depends(get_embed_service),
) -> Dict:
    # 生成向量嵌入
    embedding = await embed_svc.embed(req.content)

    knowledge = XZBKnowledge(
        expert_id=expert.id,
        type=req.type,
        content=req.content,           # 应用层加密后存储
        evidence_tier=req.evidence_tier,
        vector_embedding=embedding,
        source=req.source,
        tags=req.tags,
        applicable_conditions=req.applicable_conditions,
        confidence_override=req.confidence_override,
        expires_at=req.expires_at,
        expert_confirmed=True,          # 手动创建默认确认
    )
    db.add(knowledge)
    await db.commit()
    return {"id": str(knowledge.id), "status": "created"}


@knowledge_router.get("/{knowledge_id}", summary="读取单条知识")
async def get_knowledge(
    knowledge_id: UUID,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    result = await db.execute(
        select(XZBKnowledge).where(and_(
            XZBKnowledge.id == knowledge_id,
            XZBKnowledge.expert_id == expert.id,
        ))
    )
    k = result.scalar_one_or_none()
    if not k:
        raise HTTPException(404, "知识条目不存在")
    return {
        "id": str(k.id), "type": k.type, "content": k.content,
        "evidence_tier": k.evidence_tier, "source": k.source,
        "tags": k.tags, "usage_count": k.usage_count,
        "expert_confirmed": k.expert_confirmed,
    }


@knowledge_router.put("/{knowledge_id}", summary="更新单条知识")
async def update_knowledge(
    knowledge_id: UUID,
    updates: Dict[str, Any],
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
    embed_svc=Depends(get_embed_service),
) -> Dict:
    result = await db.execute(
        select(XZBKnowledge).where(and_(
            XZBKnowledge.id == knowledge_id,
            XZBKnowledge.expert_id == expert.id,
        ))
    )
    k = result.scalar_one_or_none()
    if not k:
        raise HTTPException(404, "知识条目不存在")

    allowed = {"content", "evidence_tier", "tags", "applicable_conditions",
               "confidence_override", "expires_at"}
    for key, val in updates.items():
        if key in allowed:
            setattr(k, key, val)

    # 内容更新时重新生成向量（标记待同步，由 Scheduler Job 27 处理）
    if "content" in updates:
        k.vector_embedding = None   # 标记待重新嵌入

    k.updated_at = datetime.utcnow()
    await db.commit()
    return {"status": "updated"}


@knowledge_router.delete("/{knowledge_id}", summary="删除知识条目（软删除）")
async def delete_knowledge(
    knowledge_id: UUID,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    await db.execute(
        update(XZBKnowledge)
        .where(and_(XZBKnowledge.id == knowledge_id, XZBKnowledge.expert_id == expert.id))
        .values(is_active=False, updated_at=datetime.utcnow())
    )
    await db.commit()
    return {"status": "deleted"}


@knowledge_router.post("/ingest", summary="批量导入文档（PDF/Word→自动解析）")
async def ingest_document(
    req: KnowledgeIngestReq,
    background_tasks: BackgroundTasks,
    expert: XZBExpertProfile = Depends(get_current_expert),
) -> Dict:
    task_id = str(uuid.uuid4())
    # 异步任务：XZBDocIngestion → Dify工作流 → 切片 → embedding
    # background_tasks.add_task(doc_ingestion_service.ingest, req, expert.id, task_id)
    return {"task_id": task_id, "status": "queued", "estimated_minutes": 2}


@knowledge_router.get("/pending-confirm", summary="查看对话沉淀的待确认知识")
async def list_pending_confirmations(
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    result = await db.execute(
        select(XZBKnowledge).where(and_(
            XZBKnowledge.expert_id == expert.id,
            XZBKnowledge.expert_confirmed == False,   # noqa
            XZBKnowledge.is_active == True,
        )).order_by(XZBKnowledge.created_at.desc())
    )
    items = result.scalars().all()
    return {
        "count": len(items),
        "items": [{"id": str(k.id), "content": k.content[:200],
                   "source": k.source, "created_at": k.created_at.isoformat()} for k in items],
    }


@knowledge_router.post("/{knowledge_id}/confirm", summary="确认/拒绝对话沉淀的知识入库")
async def confirm_knowledge(
    knowledge_id: UUID,
    action: str = Query(..., pattern="^(confirm|reject)$"),
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
    embed_svc=Depends(get_embed_service),
) -> Dict:
    result = await db.execute(
        select(XZBKnowledge).where(and_(
            XZBKnowledge.id == knowledge_id,
            XZBKnowledge.expert_id == expert.id,
        ))
    )
    k = result.scalar_one_or_none()
    if not k:
        raise HTTPException(404)

    if action == "confirm":
        k.expert_confirmed = True
        k.vector_embedding = await embed_svc.embed(k.content)
    else:
        k.is_active = False

    await db.commit()
    return {"status": "confirmed" if action == "confirm" else "rejected"}


@knowledge_router.get("/rules", summary="诊疗规则（IF-THEN）管理")
async def list_rules(
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    result = await db.execute(
        select(XZBKnowledgeRule)
        .where(XZBKnowledgeRule.expert_id == expert.id)
        .order_by(XZBKnowledgeRule.priority.desc())
    )
    rules = result.scalars().all()
    return {
        "items": [
            {"id": str(r.id), "rule_name": r.rule_name, "action_type": r.action_type,
             "priority": r.priority, "overrides_llm": r.overrides_llm, "is_active": r.is_active}
            for r in rules
        ]
    }


@knowledge_router.post("/rules", summary="新建诊疗规则")
async def create_rule(
    req: RuleCreateRequest,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    rule = XZBKnowledgeRule(
        expert_id=expert.id,
        rule_name=req.rule_name,
        condition_json=req.condition_json,
        action_type=req.action_type,
        action_content=req.action_content,
        priority=req.priority,
        overrides_llm=req.overrides_llm,
    )
    db.add(rule)
    await db.commit()
    return {"id": str(rule.id), "status": "created"}


@knowledge_router.get("/health-report", summary="知识库健康度报告")
async def knowledge_health_report(
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    from sqlalchemy import func as sqlfunc
    result = await db.execute(
        select(
            sqlfunc.count(XZBKnowledge.id).label("total"),
            sqlfunc.sum(
                (XZBKnowledge.expert_confirmed == True).cast(type_=Integer)
            ).label("confirmed"),
            sqlfunc.sum(
                (XZBKnowledge.needs_review == True).cast(type_=Integer)
            ).label("needs_review"),
        ).where(and_(
            XZBKnowledge.expert_id == expert.id,
            XZBKnowledge.is_active == True,
        ))
    )
    row = result.one()
    total = row.total or 0
    confirmed = row.confirmed or 0
    needs_review = row.needs_review or 0

    return {
        "total": total,
        "confirmed": confirmed,
        "needs_review": needs_review,
        "coverage_rate": round(confirmed / total, 2) if total > 0 else 0.0,
        "freshness_rate": round((total - needs_review) / total, 2) if total > 0 else 0.0,
    }


# ═══════════════════════════════════════════════
# §7.3 智伴交互 API
# ═══════════════════════════════════════════════

chat_router = APIRouter(prefix="/chat")


class ChatRequest(BaseModel):
    message: str
    seeker_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    session_context: dict = {}


@chat_router.post("/{expert_id}", summary="与指定专家的智伴对话（SSE流式）")
async def chat_with_companion(
    expert_id: UUID,
    req: ChatRequest,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    完整推理链（文档 §4.1）：
    AgentRouter → XZBAgentProxy → XZBKnowledgeRetriever
    → XZBRxBridge → XZBStyleAdapter → SSE输出
    """
    async def event_stream():
        # Step 1: 获取专家信息
        result = await db.execute(
            select(XZBExpertProfile).where(XZBExpertProfile.id == expert_id)
        )
        expert = result.scalar_one_or_none()
        if not expert:
            yield "data: {\"error\": \"专家不存在\"}\n\n"
            return

        # Step 2: 创建或恢复对话
        conv = XZBConversation(
            expert_id=expert_id,
            seeker_id=req.seeker_id or uuid.uuid4(),
            ttm_stage_at_start=req.session_context.get("ttm_stage"),
        )
        db.add(conv)
        await db.flush()

        # Step 3-4: 知识检索
        # retriever = XZBKnowledgeRetriever(rag_engine, embed_svc)
        # retrieval_result = await retriever.retrieve(req.message, expert_id, req.session_context, db)

        # Step 5-9: LLM推理 + 风格转换（示意）
        raw_response = f"[智伴 {expert.display_name}] 正在为您回答..."
        yield f"data: {{\"content\": \"{raw_response}\", \"conversation_id\": \"{conv.id}\"}}\n\n"

        await db.commit()
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@chat_router.get("/{conversation_id}/history", summary="对话历史")
async def get_conversation_history(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Dict:
    result = await db.execute(
        select(XZBConversation).where(XZBConversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(404)
    return {
        "conversation_id": str(conv.id),
        "summary": conv.summary,
        "rx_triggered": conv.rx_triggered,
        "expert_intervened": conv.expert_intervened,
        "created_at": conv.created_at.isoformat(),
    }


@chat_router.post("/me/intervene/{conversation_id}", summary="专家接管对话")
async def expert_intervene(
    conversation_id: UUID,
    content: str,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    result = await db.execute(
        select(XZBConversation).where(and_(
            XZBConversation.id == conversation_id,
            XZBConversation.expert_id == expert.id,
        ))
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(404)

    conv.expert_intervened = True
    intervention = XZBExpertIntervention(
        conversation_id=conversation_id,
        expert_id=expert.id,
        intervention_type="takeover",
        content=content,
    )
    db.add(intervention)
    await db.commit()

    # WS推送 xzb_expert_message 给受益者
    # await ws_manager.send_to_user(conv.seeker_id, {"event": "xzb_expert_message", "content": content})
    return {"status": "intervened"}


@chat_router.post("/me/async-reply/{conversation_id}", summary="专家异步回复")
async def async_reply(
    conversation_id: UUID,
    content: str,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    result = await db.execute(
        select(XZBConversation).where(XZBConversation.id == conversation_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(404)

    intervention = XZBExpertIntervention(
        conversation_id=conversation_id,
        expert_id=expert.id,
        intervention_type="async_reply",
        content=content,
    )
    db.add(intervention)
    await db.commit()

    # 推送通知给受益者
    # await ws_manager.send_to_user(conv.seeker_id, {"event": "xzb_expert_message", "content": content})
    return {"status": "sent"}


# ═══════════════════════════════════════════════
# §7.4 处方 API 扩展
# ═══════════════════════════════════════════════

rx_router = APIRouter(prefix="/rx")


class ManualRxTriggerReq(BaseModel):
    template_id: Optional[UUID] = None
    custom_strategies: List[Dict] = []
    note: Optional[str] = None


@rx_router.post("/trigger/{seeker_id}", summary="专家主动为受益者触发处方草案")
async def manual_trigger_rx(
    seeker_id: UUID,
    req: ManualRxTriggerReq,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    # 创建空白对话关联
    conv = XZBConversation(
        expert_id=expert.id,
        seeker_id=seeker_id,
    )
    db.add(conv)
    await db.flush()

    fragment = XZBRxFragment(
        conversation_id=conv.id,
        expert_id=expert.id,
        seeker_id=seeker_id,
        source="xzb_expert",
        priority=0,
        strategies=req.custom_strategies,
        requires_coach_review=True,   # 铁律
        status=RxStatus.draft,
    )
    db.add(fragment)
    await db.commit()

    # 注入 RxComposer 流水线
    # await rx_composer.inject_fragment(fragment_schema, seeker_id=seeker_id)

    return {"fragment_id": str(fragment.id), "status": "draft", "next": "coach_review"}


@rx_router.get("/templates", summary="专家个人处方模板库")
async def list_rx_templates(
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
) -> Dict:
    templates = await db.execute(
        select(XZBKnowledge).where(and_(
            XZBKnowledge.expert_id == expert.id,
            XZBKnowledge.type == KnowledgeType.template,
            XZBKnowledge.is_active == True,
        ))
    )
    items = templates.scalars().all()
    return {
        "count": len(items),
        "templates": [{"id": str(t.id), "tags": t.tags, "evidence_tier": t.evidence_tier} for t in items],
    }


@rx_router.post("/templates", summary="新建专家处方模板")
async def create_rx_template(
    req: KnowledgeCreateRequest,
    expert: XZBExpertProfile = Depends(get_current_expert),
    db: AsyncSession = Depends(get_db),
    embed_svc=Depends(get_embed_service),
) -> Dict:
    embedding = await embed_svc.embed(req.content)
    template = XZBKnowledge(
        expert_id=expert.id,
        type=KnowledgeType.template,
        content=req.content,
        evidence_tier=req.evidence_tier,
        vector_embedding=embedding,
        source=req.source,
        tags=req.tags,
        applicable_conditions=req.applicable_conditions,
        expert_confirmed=True,
    )
    db.add(template)
    await db.commit()
    return {"id": str(template.id), "status": "created"}


@rx_router.get("/{rx_id}/expert-source", summary="查看处方中专家贡献的片段详情")
async def get_expert_rx_source(
    rx_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> Dict:
    result = await db.execute(
        select(XZBRxFragment).where(XZBRxFragment.rx_id == rx_id)
    )
    fragment = result.scalar_one_or_none()
    if not fragment:
        return {"has_expert_source": False}
    return {
        "has_expert_source": True,
        "fragment_id": str(fragment.id),
        "expert_id": str(fragment.expert_id),
        "evidence_tier": fragment.evidence_tier,
        "domain": fragment.domain,
        "knowledge_refs": [str(k) for k in (fragment.knowledge_refs or [])],
        "status": fragment.status,
    }


# ═══════════════════════════════════════════════
# 路由注册
# ═══════════════════════════════════════════════

router.include_router(expert_router, prefix="/experts", tags=["专家管理"])
router.include_router(knowledge_router, prefix="/knowledge", tags=["知识库"])
router.include_router(chat_router, tags=["智伴交互"])
router.include_router(rx_router, tags=["处方扩展"])

# 在 FastAPI app 中挂载：
# from xzb.api.xzb_api import router as xzb_router
# app.include_router(xzb_router)

"""
对话路由 — Coach 对话 + 知识问答 + 处方生成
路径前缀: /api/v3/chat

鉴权: message/prescription 需登录, knowledge 公开 (可选登录)
"""
from fastapi import APIRouter, Depends

from api.schemas import (
    APIResponse, ChatRequest, ChatResponse,
    KnowledgeQueryRequest, KnowledgeSearchResult,
    PrescriptionRequest,
)
from api.auth import User, get_current_user, get_optional_user
from api.dependencies import get_coach_agent, get_rag_pipeline
from core.llm.coach_agent import CoachAgent, UserContext
from core.rag.pipeline import RAGPipeline

router = APIRouter(prefix="/api/v3/chat", tags=["对话 & 知识"])


# ── Coach 对话 ──

@router.post("/message", response_model=APIResponse, summary="Coach 对话")
def chat_message(
    req: ChatRequest,
    user: User = Depends(get_current_user),
    agent: CoachAgent = Depends(get_coach_agent),
):
    """
    智能对话入口: 自动意图分类 → 路由到合适的模型 → RAG 增强

    意图类型:
    - greeting / checkin_confirm → 快捷回复 (不调 LLM)
    - knowledge_qa / strategy_explain → RAG 检索 + LLM
    - coach_dialogue / crisis_support → 画像注入 + RAG + 高级模型
    - general_chat → 直接 LLM
    """
    # 构建用户上下文 (优先用 DB 中的画像, 其次用前端传入)
    ctx = UserContext(
        user_id=user.id,
        behavioral_stage=req.behavioral_stage or user.current_stage or "S0",
        readiness_level=req.readiness_level or "L1",
        spi_score=req.spi_score or 0.0,
    )

    history = None
    if req.history:
        history = [{"role": m.role, "content": m.content} for m in req.history]

    result = agent.chat(
        user_id=user.id,
        message=req.message,
        user_context=ctx,
        history=history,
        force_intent=req.force_intent,
    )

    return APIResponse(data=ChatResponse(**result))


# ── 知识问答 (纯 RAG) ──

@router.post("/knowledge", response_model=APIResponse, summary="知识库问答 (RAG)")
def knowledge_query(
    req: KnowledgeQueryRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
):
    """
    知识库检索 + LLM 生成回答

    doc_type 过滤: spec / strategy / tcm / clinical / course / faq
    """
    result = pipeline.query(
        question=req.question,
        doc_type=req.doc_type,
    )
    return APIResponse(data=result.to_dict())


@router.post("/knowledge/search", response_model=APIResponse, summary="知识库纯检索 (不调 LLM)")
def knowledge_search(
    req: KnowledgeQueryRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline),
):
    """纯向量检索, 返回相似文档片段, 不调 LLM"""
    results = pipeline.search_only(
        question=req.question,
        doc_type=req.doc_type,
        top_k=req.top_k,
    )
    return APIResponse(data=results)


# ── 处方生成 ──

@router.post("/prescription", response_model=APIResponse, summary="RAG 增强处方生成")
def generate_prescription(
    req: PrescriptionRequest,
    user: User = Depends(get_current_user),
    agent: CoachAgent = Depends(get_coach_agent),
):
    """
    结合用户画像 + 知识库中的干预策略 → LLM 生成个性化行为处方
    """
    ctx = UserContext(
        user_id=user.id,
        behavioral_stage=req.behavioral_stage,
        readiness_level=req.readiness_level,
        spi_score=req.spi_score,
        bpt_type=req.bpt_type,
        top_obstacles=req.top_obstacles,
        dominant_causes=req.dominant_causes,
    )
    result = agent.generate_prescription(ctx)
    return APIResponse(data=result)


# ── 统计 ──

@router.get("/stats", response_model=APIResponse, summary="LLM 调用统计")
def chat_stats(agent: CoachAgent = Depends(get_coach_agent)):
    """返回 LLM 路由统计: 调用量/成本/延迟/降级率"""
    return APIResponse(data=agent.get_stats())

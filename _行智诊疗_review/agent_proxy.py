"""
XZBAgentProxy — 推理代理（文档 §2.2）
封装专家知识 RAG + 风格转换的推理入口
作为 AgentRouter 的扩展点插入平台 Agent 体系

插入位置：AgentRouter 6步路由 → 平台Agent池 ↔ XZBAgentProxy（新建）
"""
from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional
from uuid import UUID

from xzb.knowledge.retriever import XZBKnowledgeRetriever, RetrievalResult
from xzb.rx.rx_bridge import XZBRxBridge
from xzb.style.style_adapter import XZBStyleAdapter

logger = logging.getLogger(__name__)


@dataclass
class XZBProxyResponse:
    content: str
    skipped_llm: bool = False
    rx_fragment_id: Optional[UUID] = None
    retrieval_hits: int = 0
    knowledge_source: str = "none"   # "rule" | "private" | "platform" | "none"


class XZBAgentProxy:
    """
    行诊智伴推理代理

    完整推理链（文档 §4.1）：
    Step 3: 检测受益者是否绑定专家智伴 → 激活专家知识层
    Step 4: XZBKnowledgeRetriever（规则→私有RAG→公共补充）
    Step 5: TTM阶段引擎判断（只读）
    Step 6-7: XZBRxBridge 处方触发判断与片段生成
    Step 8: 注入 RxComposer（已在 XZBRxBridge 处理）
    Step 9: XZBStyleAdapter 风格转换输出
    """

    def __init__(
        self,
        retriever: XZBKnowledgeRetriever,
        rx_bridge: XZBRxBridge,
        style_adapter: XZBStyleAdapter,
        llm_service,
    ):
        self.retriever = retriever
        self.rx_bridge = rx_bridge
        self.style_adapter = style_adapter
        self.llm = llm_service

    async def process(
        self,
        query: str,
        expert_id: UUID,
        seeker_id: UUID,
        session_context: dict,
        db,
    ) -> XZBProxyResponse:
        """
        AgentRouter 检测到受益者绑定了专家智伴后调用此方法
        """
        from xzb.models.xzb_models import XZBExpertProfile, XZBConversation
        from sqlalchemy import select, and_

        # 获取专家信息
        result = await db.execute(
            select(XZBExpertProfile).where(XZBExpertProfile.id == expert_id)
        )
        expert = result.scalar_one_or_none()
        if not expert or expert.config and expert.config.dormant_mode:
            logger.info("Expert %s not available (dormant/inactive), transparent downgrade", expert_id)
            return await self._transparent_downgrade(query, session_context)

        # 创建对话记录
        conv = XZBConversation(
            expert_id=expert_id,
            seeker_id=seeker_id,
            ttm_stage_at_start=session_context.get("ttm_stage"),
        )
        db.add(conv)
        await db.flush()

        # Step 4: 知识检索
        retrieval = await self.retriever.retrieve(
            query=query,
            expert_id=expert_id,
            session_context=session_context,
            db=db,
        )

        knowledge_source = "none"
        if retrieval.rule_match:
            knowledge_source = "rule"
        elif retrieval.knowledge_hits:
            has_private = any(h.source_scope == "expert" for h in retrieval.knowledge_hits)
            knowledge_source = "private" if has_private else "platform"

        # 规则直接返回（overrides_llm）
        if retrieval.skipped_llm and retrieval.rule_match:
            raw_content = retrieval.rule_match.action_content
            styled = await self.style_adapter.transform(
                raw_content, str(expert_id), db=db
            )
            return XZBProxyResponse(
                content=styled,
                skipped_llm=True,
                retrieval_hits=1,
                knowledge_source="rule",
            )

        # Step 5: 读取TTM阶段（只读，不修改）
        ttm_stage = session_context.get("ttm_stage", "unknown")

        # 构建 LLM Prompt（注入专家知识上下文）
        knowledge_context = self._build_knowledge_context(retrieval)
        prompt = self._build_prompt(query, knowledge_context, ttm_stage, expert)

        # LLM 推理
        raw_response = await self.llm.generate(
            prompt=prompt,
            system=self._build_system_prompt(expert),
            max_tokens=1000,
        )

        # Step 6-7: 处方触发判断
        rx_fragment = None
        if expert.config and expert.config.auto_rx_enabled:
            rx_fragment = await self.rx_bridge.process(
                query=query,
                expert=expert,
                seeker_id=seeker_id,
                retrieval_result=retrieval,
                session_context=session_context,
                conversation=conv,
                db=db,
            )

        # Step 9: 风格转换
        styled_response = await self.style_adapter.transform(
            raw_text=raw_response,
            expert_id=str(expert_id),
            db=db,
        )

        await db.commit()

        return XZBProxyResponse(
            content=styled_response,
            skipped_llm=False,
            rx_fragment_id=rx_fragment.id if rx_fragment else None,
            retrieval_hits=retrieval.total_hits,
            knowledge_source=knowledge_source,
        )

    def _build_knowledge_context(self, retrieval: RetrievalResult) -> str:
        """将检索结果格式化为 LLM 可用的上下文"""
        if not retrieval.knowledge_hits:
            return ""

        parts = ["【专家知识库】"]
        for i, hit in enumerate(retrieval.knowledge_hits[:5], 1):
            tier = f"[{hit.evidence_tier}]" if hit.evidence_tier else ""
            scope = "（专家私有）" if hit.source_scope == "expert" else "（平台知识）"
            parts.append(f"{i}. {tier}{scope} {hit.content[:300]}")
        return "\n".join(parts)

    def _build_prompt(
        self,
        query: str,
        knowledge_context: str,
        ttm_stage: str,
        expert,
    ) -> str:
        parts = [f"受益者当前TTM阶段：{ttm_stage}"]
        if knowledge_context:
            parts.append(knowledge_context)
        parts.append(f"\n受益者问题：{query}")
        return "\n\n".join(parts)

    def _build_system_prompt(self, expert) -> str:
        config = expert.config
        boundary = config.boundary_stmt if config else "本助手不替代专科就诊。"
        return (
            f"你是{expert.display_name}的健康助手，专注于{expert.specialty or '健康管理'}领域。"
            f"请基于提供的知识库内容回答，没有相关知识时如实说明。"
            f"边界声明：{boundary}"
        )

    async def _transparent_downgrade(self, query: str, session_context: dict) -> XZBProxyResponse:
        """
        专家不可用时透明降级到平台公共知识（文档 Phase 0 设计）
        """
        logger.info("XZBAgentProxy transparent downgrade to platform knowledge")
        return XZBProxyResponse(
            content="",   # 由平台 Agent 体系继续处理
            skipped_llm=False,
            knowledge_source="platform",
        )


# ─────────────────────────────────────────────
# AgentRouter 扩展点（集成示意）
# ─────────────────────────────────────────────
"""
# 在平台现有 AgentRouter 的 route() 方法中，添加 XZB 检测逻辑：

async def route(self, query: str, user_id: str, session_context: dict) -> AgentResponse:
    # ... 现有 L0 安全层检查 ...
    # ... 现有 6步路由逻辑 ...

    # XZB 扩展点：检测受益者是否绑定专家智伴
    expert_binding = await self._get_expert_binding(user_id, session_context)
    if expert_binding:
        xzb_response = await xzb_agent_proxy.process(
            query=query,
            expert_id=expert_binding.expert_id,
            seeker_id=user_id,
            session_context=session_context,
            db=db,
        )
        if xzb_response.content:
            return AgentResponse(
                content=xzb_response.content,
                source="xzb_expert",
                rx_triggered=xzb_response.rx_fragment_id is not None,
            )
        # 空内容表示透明降级，继续走平台Agent池
    
    # ... 继续现有 MultiAgentCoordinator 9步协调 ...
"""

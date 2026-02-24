"""
XZBAgentProxy — 行智诊疗推理代理
封装专家知识 RAG + 风格转换的推理入口
作为 AgentRouter 的加权候选插入平台 Agent 体系 (非截断)

已适配: 同步 SQLAlchemy Session, 平台 LLM Client
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.xzb.xzb_retriever import XZBKnowledgeRetriever, RetrievalResult

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
    行智诊疗推理代理 (同步版, 对接平台同步 SQLAlchemy)

    推理链:
    1. 获取专家画像 + 休眠检测
    2. 创建对话记录
    3. 知识检索 (规则→私有RAG→公共补充)
    4. LLM推理 (注入专家知识上下文)
    5. 处方触发判断
    6. 风格转换输出
    """

    def __init__(self, retriever: XZBKnowledgeRetriever, rx_bridge=None,
                 style_adapter=None, llm_service=None):
        self.retriever = retriever
        self.rx_bridge = rx_bridge
        self.style_adapter = style_adapter
        self.llm = llm_service

    def process(
        self,
        query: str,
        expert_id: UUID,
        seeker_id: int,
        session_context: dict,
        db: Session,
    ) -> XZBProxyResponse:
        from core.xzb.xzb_models import XZBExpertProfile, XZBConversation

        # 获取专家信息
        expert = db.execute(
            select(XZBExpertProfile).where(XZBExpertProfile.id == expert_id)
        ).scalar_one_or_none()

        if not expert or (expert.config and expert.config.dormant_mode):
            logger.info("Expert %s not available (dormant/inactive), transparent downgrade", expert_id)
            return XZBProxyResponse(content="", knowledge_source="platform")

        # 创建对话记录
        conv = XZBConversation(
            expert_id=expert_id,
            seeker_id=seeker_id,
            ttm_stage_at_start=session_context.get("ttm_stage"),
        )
        db.add(conv)
        db.flush()

        # 知识检索
        retrieval = self.retriever.retrieve(
            query=query, expert_id=expert_id,
            session_context=session_context, db=db,
        )

        knowledge_source = "none"
        if retrieval.rule_match:
            knowledge_source = "rule"
        elif retrieval.knowledge_hits:
            has_private = any(h.source_scope == "expert" for h in retrieval.knowledge_hits)
            knowledge_source = "private" if has_private else "platform"

        # 规则直接返回 (overrides_llm)
        if retrieval.skipped_llm and retrieval.rule_match:
            raw_content = retrieval.rule_match.action_content
            styled = self._style_transform(raw_content, str(expert_id), db)
            return XZBProxyResponse(
                content=styled, skipped_llm=True,
                retrieval_hits=1, knowledge_source="rule",
            )

        # LLM 推理
        knowledge_context = self._build_knowledge_context(retrieval)
        ttm_stage = session_context.get("ttm_stage", "unknown")
        prompt = self._build_prompt(query, knowledge_context, ttm_stage, expert)
        system = self._build_system_prompt(expert)

        raw_response = ""
        if self.llm:
            try:
                raw_response = self.llm.generate(prompt=prompt, system=system, max_tokens=1000)
            except Exception as e:
                logger.error("XZB LLM generate failed: %s", e)
                raw_response = knowledge_context or "暂时无法回答，请稍后再试。"
        else:
            raw_response = knowledge_context or "智伴功能正在初始化中。"

        # 处方触发
        rx_fragment = None
        if self.rx_bridge and expert.config and expert.config.auto_rx_enabled:
            try:
                rx_fragment = self.rx_bridge.process(
                    query=query, expert=expert, seeker_id=seeker_id,
                    retrieval_result=retrieval, session_context=session_context,
                    conversation=conv, db=db,
                )
            except Exception as e:
                logger.error("XZB Rx bridge failed: %s", e)

        # 风格转换
        styled_response = self._style_transform(raw_response, str(expert_id), db)

        db.commit()

        return XZBProxyResponse(
            content=styled_response,
            skipped_llm=False,
            rx_fragment_id=rx_fragment.id if rx_fragment else None,
            retrieval_hits=retrieval.total_hits,
            knowledge_source=knowledge_source,
        )

    def _style_transform(self, text: str, expert_id: str, db) -> str:
        if self.style_adapter:
            try:
                return self.style_adapter.transform_sync(text, expert_id, db=db)
            except Exception:
                pass
        return text

    def _build_knowledge_context(self, retrieval: RetrievalResult) -> str:
        if not retrieval.knowledge_hits:
            return ""
        parts = ["【专家知识库】"]
        for i, hit in enumerate(retrieval.knowledge_hits[:5], 1):
            tier = f"[{hit.evidence_tier}]" if hit.evidence_tier else ""
            scope = "（专家私有）" if hit.source_scope == "expert" else "（平台知识）"
            parts.append(f"{i}. {tier}{scope} {hit.content[:300]}")
        return "\n".join(parts)

    def _build_prompt(self, query, knowledge_context, ttm_stage, expert):
        parts = [f"受益者当前TTM阶段：{ttm_stage}"]
        if knowledge_context:
            parts.append(knowledge_context)
        parts.append(f"\n受益者问题：{query}")
        return "\n\n".join(parts)

    def _build_system_prompt(self, expert):
        config = expert.config
        boundary = config.boundary_stmt if config else "本助手不替代专科就诊。"
        return (
            f"你是{expert.display_name}的健康助手，专注于{expert.specialty or '健康管理'}领域。"
            f"请基于提供的知识库内容回答，没有相关知识时如实说明。"
            f"边界声明：{boundary}"
        )

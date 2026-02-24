"""
XZBExpertAgent — 行智诊疗专家 Agent (BaseAgent 适配器)
将 XZBAgentProxy 封装为平台 Agent 体系的标准 BaseAgent 实例
可被 AgentRouter 路由, 可被 MultiAgentCoordinator 协调

Phase 1: 完整对接 XZBAgentProxy 推理链
"""
from __future__ import annotations

import logging
from typing import Optional

from .base import BaseAgent, AgentDomain, AgentInput, AgentResult, RiskLevel

logger = logging.getLogger(__name__)


class XZBExpertAgent(BaseAgent):
    """
    行智诊疗专家 Agent — 桥接 XZBAgentProxy 到平台 Agent 体系

    路由权重: +80 (在 AgentRouter 中通过 tenant_ctx.xzb_expert_id 加权注入)
    推理链: 专家画像 → 知识检索 → LLM推理 → 处方触发 → 风格转换
    """

    domain = AgentDomain.XZB_EXPERT
    display_name = "行智诊疗专家"
    keywords = [
        "专家", "诊疗", "诊断", "症状", "方案", "调理",
        "中医", "辨证", "体质", "养生", "经络", "穴位",
        "行智", "分析", "干预",
    ]
    data_fields = []  # XZB 通过 session_context 获取设备数据
    priority = 1
    base_weight = 0.95
    evidence_tier = "T1"  # 专家知识库 = 最高循证等级

    def __init__(self):
        self._proxy = None
        self._proxy_initialized = False

    def _ensure_proxy(self):
        """延迟初始化 XZBAgentProxy (降级安全)"""
        if self._proxy_initialized:
            return
        self._proxy_initialized = True
        try:
            from core.xzb.xzb_retriever import XZBKnowledgeRetriever
            from core.xzb.xzb_agent_proxy import XZBAgentProxy
            from core.xzb.xzb_rx_bridge import XZBRxBridge
            from core.xzb.xzb_style_adapter import XZBStyleAdapter

            retriever = XZBKnowledgeRetriever()
            rx_bridge = XZBRxBridge()
            style_adapter = XZBStyleAdapter()

            # 对接平台 LLM
            llm_service = None
            try:
                from core.llm_client import get_llm_client
                llm_service = _XZBLLMAdapter(get_llm_client())
            except ImportError:
                pass

            self._proxy = XZBAgentProxy(
                retriever=retriever,
                rx_bridge=rx_bridge,
                style_adapter=style_adapter,
                llm_service=llm_service,
            )
            logger.info("XZBExpertAgent proxy initialized")
        except Exception as e:
            logger.warning("XZBExpertAgent proxy init failed (graceful degradation): %s", e)

    def process(self, agent_input: AgentInput) -> AgentResult:
        """
        处理用户输入。
        如果有 xzb_expert_id 上下文, 调用 XZBAgentProxy 推理链;
        否则返回通用建议。
        """
        self._ensure_proxy()

        # 从 context 获取 XZB 专家绑定信息
        xzb_expert_id = agent_input.context.get("xzb_expert_id")
        if not xzb_expert_id:
            return AgentResult(
                agent_domain=self.domain.value,
                confidence=0.3,
                risk_level=RiskLevel.LOW,
                findings=["未绑定行智诊疗专家"],
                recommendations=["请联系教练绑定专家获取个性化建议"],
            )

        if not self._proxy:
            return AgentResult(
                agent_domain=self.domain.value,
                confidence=0.4,
                risk_level=RiskLevel.LOW,
                findings=["行智诊疗服务初始化中"],
                recommendations=["请稍后再试"],
            )

        # 调用 XZBAgentProxy 推理链
        try:
            from uuid import UUID
            from core.database import SessionLocal

            expert_uuid = UUID(str(xzb_expert_id))

            session_context = {
                "ttm_stage": agent_input.profile.get("ttm_stage", "unknown"),
                "device_data": agent_input.device_data,
                "prev_ttm_stage": agent_input.context.get("prev_ttm_stage"),
                "adherence_consecutive_miss_days": agent_input.context.get("adherence_miss_days", 0),
            }

            with SessionLocal() as db:
                proxy_resp = self._proxy.process(
                    query=agent_input.message,
                    expert_id=expert_uuid,
                    seeker_id=agent_input.user_id,  # int (users.id)
                    session_context=session_context,
                    db=db,
                )

            # 转换为 AgentResult
            confidence = 0.85 if proxy_resp.retrieval_hits > 0 else 0.6
            findings = []
            if proxy_resp.knowledge_source != "none":
                findings.append(f"知识来源: {proxy_resp.knowledge_source} ({proxy_resp.retrieval_hits}条命中)")
            if proxy_resp.rx_fragment_id:
                findings.append(f"已触发处方片段 (待教练审核)")

            return AgentResult(
                agent_domain=self.domain.value,
                confidence=self.get_effective_confidence(confidence),
                risk_level=RiskLevel.LOW,
                findings=findings,
                recommendations=[proxy_resp.content] if proxy_resp.content else [],
                metadata={
                    "knowledge_source": proxy_resp.knowledge_source,
                    "retrieval_hits": proxy_resp.retrieval_hits,
                    "rx_fragment_id": str(proxy_resp.rx_fragment_id) if proxy_resp.rx_fragment_id else None,
                    "skipped_llm": proxy_resp.skipped_llm,
                },
            )

        except Exception as e:
            logger.error("XZBExpertAgent process failed: %s", e)
            return AgentResult(
                agent_domain=self.domain.value,
                confidence=0.3,
                risk_level=RiskLevel.LOW,
                findings=[f"行智诊疗处理异常"],
                recommendations=["请稍后再试或联系教练"],
            )


class _XZBLLMAdapter:
    """适配 UnifiedLLMClient 到 XZBAgentProxy 期望的 llm_service 接口"""

    def __init__(self, client):
        self._client = client

    def generate(self, prompt: str, system: str = "", max_tokens: int = 1000) -> str:
        resp = self._client.chat(
            system=system,
            user=prompt,
            temperature=0.7,
            timeout=45.0,
        )
        return resp.content if resp.success else ""

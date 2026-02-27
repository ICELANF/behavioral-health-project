"""
HealthAssistantAgent — 健康知识科普

功能:
  - 健康知识问答 (RAG 知识库检索 + LLM 生成)
  - 科普内容推荐 (基于用户阶段和关注领域)
  - 免责声明自动附加

路由触发:
  关键词: 科普/什么是/怎么回事/为什么会/健康知识/原理/原因/怎么预防/注意什么

安全约束:
  - 所有回复末尾附加免责声明
  - 检测到治疗性问题 → 引导就医
  - 不提供个体化诊断或处方

来源: 合并 assistant_agents/health_assistant.py 设计 + core RAG pipeline
"""
from __future__ import annotations
import logging
from typing import Any, Dict, List

from ..base import BaseAgent, AgentDomain, AgentInput, AgentResult, RiskLevel

logger = logging.getLogger(__name__)

DISCLAIMER = "\n\n---\n以上为健康科普信息，不构成医疗建议。如有具体健康问题，请咨询专业医疗人员。"

# 需要引导就医的边界关键词
MEDICAL_BOUNDARY_KEYWORDS = [
    "确诊", "处方", "用药", "剂量", "手术", "化疗", "放疗",
    "检查报告", "指标异常", "诊断", "治疗方案",
]


class HealthAssistantAgent(BaseAgent):
    """
    健康知识科普 Agent — 用户层

    特点:
      1. RAG-first: 优先从知识库检索, 无结果时用 LLM 通用知识
      2. 阶段感知: 根据用户 TTM 阶段调整科普深度
      3. 安全边界: 治疗性问题引导就医, 不代替医生
    """
    domain = AgentDomain.NUTRITION  # 复用已有 domain 作为 fallback
    display_name = "健康知识助手"
    keywords = ["科普", "什么是", "怎么回事", "为什么会", "健康知识",
                "原理", "原因", "怎么预防", "注意什么"]
    priority = 4
    base_weight = 0.65
    enable_llm = True
    evidence_tier = "T3"

    def process(self, inp: AgentInput) -> AgentResult:
        message = inp.message
        stage = inp.profile.get("current_stage", "S0")

        # 1. 边界检测: 治疗性问题引导就医
        boundary_hit = self._check_medical_boundary(message)
        if boundary_hit:
            return AgentResult(
                agent_domain="health_assistant",
                confidence=0.85,
                risk_level=RiskLevel.LOW,
                findings=[f"检测到治疗性问题关键词: {boundary_hit}"],
                recommendations=[
                    f"关于「{boundary_hit}」的问题，建议咨询您的主治医生获取个性化建议。",
                    "我可以为您提供相关的健康科普知识作为参考。",
                ],
                metadata={"boundary_triggered": True, "keyword": boundary_hit},
            )

        # 2. RAG 知识检索
        knowledge_chunks = self._retrieve_knowledge(message)

        # 3. 构建科普回复
        findings = []
        recommendations = []

        if knowledge_chunks:
            findings.append(f"从知识库检索到 {len(knowledge_chunks)} 条相关内容")
            # 基于阶段调整深度
            if stage in ("S0", "S1"):
                recommendations.append("以下是一些基础健康知识，了解一下就好：")
            elif stage in ("S2", "S3"):
                recommendations.append("这些知识可以帮助你更好地理解为什么要改变：")
            else:
                recommendations.append("补充一些深入的健康知识：")

            for chunk in knowledge_chunks[:3]:
                content = chunk.get("content", "")[:200]
                recommendations.append(content)
        else:
            recommendations.append("让我用通用健康知识来回答你的问题。")

        # 附加免责声明
        recommendations.append(DISCLAIMER.strip())

        result = AgentResult(
            agent_domain="health_assistant",
            confidence=0.7 if knowledge_chunks else 0.5,
            risk_level=RiskLevel.LOW,
            findings=findings,
            recommendations=recommendations,
            metadata={
                "knowledge_sources": len(knowledge_chunks),
                "stage_adapted": True,
            },
        )

        # LLM 增强 (将 RAG 结果 + 问题 → 生成流畅回答)
        return self._enhance_with_llm(result, inp)

    def _check_medical_boundary(self, message: str) -> str | None:
        for kw in MEDICAL_BOUNDARY_KEYWORDS:
            if kw in message:
                return kw
        return None

    def _retrieve_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """从 RAG pipeline 检索知识"""
        try:
            from core.rag.pipeline import RAGPipeline
            pipeline = RAGPipeline()
            if hasattr(pipeline, "search"):
                results = pipeline.search(query, top_k=5)
                return [
                    {
                        "content": getattr(r, "content", str(r)),
                        "source": getattr(r, "source", ""),
                        "score": getattr(r, "score", 0),
                    }
                    for r in (results or [])
                ]
        except Exception as e:
            logger.warning("RAG 检索失败 (health_assistant): %s", e)
        return []

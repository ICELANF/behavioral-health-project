"""
四大健康领域Agent — 用户层

nutrition_guide: 营养饮食指导（含中医食疗）
exercise_guide: 运动指导（安全边界+个性化）
sleep_guide: 睡眠改善指导
emotion_support: 情绪支持（非治疗级）

共享架构: RAG知识检索 + 领域安全规则 + LLM生成 + 免责声明
"""
from __future__ import annotations
import logging
import re
from typing import Any, Dict, List, Optional

from ..base import BaseAssistantAgent

logger = logging.getLogger(__name__)

DISCLAIMER = "\n\n---\n以上为健康科普信息，不构成医疗建议。如有具体健康问题，请咨询专业医疗人员。"


# ═══════════════════════════════════════════════════════════
# 基础领域Agent — 共享RAG+LLM模式
# ═══════════════════════════════════════════════════════════

class DomainHealthAgent(BaseAssistantAgent):
    """领域健康Agent基类"""

    # 子类覆盖
    AGENT_NAME = "domain_agent"
    AGENT_DOMAIN = "general"
    SYSTEM_PROMPT = "你是健康助手。"
    BOUNDARY_KEYWORDS: List[str] = []
    UNSAFE_PATTERNS: List[str] = []

    @property
    def name(self) -> str:
        return self.AGENT_NAME

    @property
    def domain(self) -> str:
        return self.AGENT_DOMAIN

    def _get_rag_pipeline(self):
        try:
            from core.rag.pipeline import RAGPipeline
            return RAGPipeline()
        except ImportError:
            return None

    def _get_llm_client(self):
        try:
            from core.llm_client import get_llm_client
            return get_llm_client()
        except ImportError:
            return None

    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        if not await self.safety_check(message):
            return self._format_response(
                content="检测到安全风险，已转介专业通道。",
                safety_intercepted=True, action="crisis_referral",
            )

        # 边界检测
        boundary = self._check_boundary(message)

        # RAG检索
        knowledge = await self._retrieve(message)

        # LLM生成
        answer = await self._generate(message, knowledge, kwargs.get("user_profile", {}), boundary)

        citations = [k.get("source", "") for k in knowledge if k.get("source")]
        return self._format_response(
            content=answer["text"],
            citations=citations[:5],
            knowledge_used=len(knowledge),
            boundary_warning=boundary,
            confidence=answer.get("confidence", 0.6),
        )

    def _check_boundary(self, message: str) -> Optional[str]:
        for kw in self.BOUNDARY_KEYWORDS:
            if kw in message:
                return kw
        return None

    async def _retrieve(self, query: str) -> List[dict]:
        pipeline = self._get_rag_pipeline()
        if not pipeline:
            return []
        try:
            if hasattr(pipeline, 'asearch'):
                results = await pipeline.asearch(query, top_k=5, domain=self.AGENT_DOMAIN)
            elif hasattr(pipeline, 'search'):
                results = pipeline.search(query, top_k=5)
            else:
                return []
            return [{"content": getattr(r, 'content', str(r)),
                     "source": getattr(r, 'source', ''),
                     "score": getattr(r, 'score', 0)} for r in (results or [])]
        except Exception as e:
            logger.warning(f"RAG检索失败[{self.AGENT_NAME}]: {e}")
            return []

    async def _generate(self, message, knowledge, profile, boundary) -> dict:
        llm = self._get_llm_client()

        knowledge_ctx = ""
        if knowledge:
            chunks = [f"[{i}] {k['content'][:400]}" for i, k in enumerate(knowledge[:3], 1)]
            knowledge_ctx = f"\n参考资料:\n" + "\n".join(chunks)

        boundary_note = f"\n注意: 用户问题涉及「{boundary}」，请引导就医而非给出具体建议。" if boundary else ""

        if not llm:
            text = self._fallback_text(message, knowledge)
            return {"text": text, "confidence": 0.3}

        prompt = f"""{self.SYSTEM_PROMPT}
{boundary_note}
{knowledge_ctx}

用户: {message}

请回答（科普级，不含个体化建议）:"""

        try:
            response = await llm.achat(prompt) if hasattr(llm, 'achat') else llm.chat(prompt)
            text = response if isinstance(response, str) else getattr(response, 'content', str(response))
            if "不构成医疗建议" not in text:
                text += DISCLAIMER
            return {"text": text, "confidence": 0.7 if knowledge else 0.5}
        except Exception as e:
            logger.warning(f"LLM生成失败[{self.AGENT_NAME}]: {e}")
            return {"text": self._fallback_text(message, knowledge), "confidence": 0.3}

    def _fallback_text(self, message, knowledge) -> str:
        if knowledge:
            return f"关于您的问题，参考信息:\n\n{knowledge[0]['content'][:300]}{DISCLAIMER}"
        return f"抱歉暂时无法回答。请稍后重试或咨询专业人员。{DISCLAIMER}"


# ═══════════════════════════════════════════════════════════
# nutrition_guide — 营养饮食
# ═══════════════════════════════════════════════════════════

class NutritionGuideAgent(DomainHealthAgent):
    AGENT_NAME = "nutrition_guide"
    AGENT_DOMAIN = "nutrition"
    SYSTEM_PROMPT = """你是行健平台的营养饮食顾问。你的专长包括：
- 中国居民膳食指南的科普解读
- 中医食疗与药膳的基础知识（寒热温凉、五味归经）
- 慢性病（糖尿病、高血压、高血脂）的膳食管理科普
- 四季饮食养生

你不提供个体化的营养处方或治疗饮食方案，这些需要营养师或医生指导。"""

    BOUNDARY_KEYWORDS = ["肠内营养", "肠外营养", "营养液", "管饲", "TPN", "特医食品",
                         "食物过敏", "过敏原检测", "糖尿病饮食处方"]


# ═══════════════════════════════════════════════════════════
# exercise_guide — 运动指导
# ═══════════════════════════════════════════════════════════

class ExerciseGuideAgent(DomainHealthAgent):
    AGENT_NAME = "exercise_guide"
    AGENT_DOMAIN = "exercise"
    SYSTEM_PROMPT = """你是行健平台的运动指导顾问。你的专长包括：
- 中国居民运动指南的科普解读
- 慢性病人群的运动注意事项（不是运动处方）
- 太极拳、八段锦等传统功法的基础介绍
- 运动安全常识（热身、拉伸、运动强度判断）

安全红线：心脏病发作期、急性损伤、严重高血压时禁止运动建议。
你不提供个体化运动处方，这些需要运动医学专家指导。"""

    BOUNDARY_KEYWORDS = ["运动处方", "心脏康复运动", "术后康复", "骨折后训练",
                         "靶心率", "VO2max测试", "运动负荷测试"]


# ═══════════════════════════════════════════════════════════
# sleep_guide — 睡眠改善
# ═══════════════════════════════════════════════════════════

class SleepGuideAgent(DomainHealthAgent):
    AGENT_NAME = "sleep_guide"
    AGENT_DOMAIN = "sleep"
    SYSTEM_PROMPT = """你是行健平台的睡眠健康顾问。你的专长包括：
- 睡眠卫生教育（作息规律、环境优化、电子设备管理）
- 认知行为疗法-失眠(CBT-I)的科普介绍（非治疗）
- 中医助眠方法（穴位按摩、食疗助眠、情志调摄）
- 常见睡眠问题的识别和就医指引

你不提供安眠药建议或个体化睡眠治疗方案。"""

    BOUNDARY_KEYWORDS = ["安眠药", "助眠药", "褪黑素剂量", "安定", "苯二氮卓",
                         "呼吸暂停", "CPAP", "多导睡眠监测"]


# ═══════════════════════════════════════════════════════════
# emotion_support — 情绪支持
# ═══════════════════════════════════════════════════════════

class EmotionSupportAgent(DomainHealthAgent):
    AGENT_NAME = "emotion_support"
    AGENT_DOMAIN = "emotion"
    SYSTEM_PROMPT = """你是行健平台的情绪支持伙伴。你的角色是：
- 提供温暖、共情的情绪陪伴
- 介绍基础的情绪管理技巧（深呼吸、正念、情绪日记）
- 帮助用户识别和命名情绪
- 在适当时机引导用户寻求专业心理咨询

重要：你不是心理治疗师，不提供心理诊断或治疗。
如果检测到严重心理危机，立即转介crisis_responder。"""

    BOUNDARY_KEYWORDS = ["抑郁症治疗", "双相情感障碍", "精神分裂", "PTSD治疗",
                         "心理治疗方案", "精神科用药", "抗抑郁药"]

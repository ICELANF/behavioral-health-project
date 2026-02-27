"""
健康知识科普助手 — 用户层核心

职责:
  1. 回答用户的健康知识问题（科普级，非诊断）
  2. 通过RAG检索知识库提供有引用的回答
  3. 安全过滤确保不给出个体化医疗建议

对接:
  - RAGPipeline → 知识检索+重排序
  - RAGSafety → 安全内容过滤
  - KnowledgeRetriever → 向量检索
  - UnifiedLLMClient → LLM生成回答

安全约束 (Sheet⑫):
  - 不提供个体化诊断或治疗建议
  - 不替代医生的专业判断
  - 检测到高风险内容转介危机响应
  - 对话中出现具体症状/用药时引导就医
"""
from __future__ import annotations
import logging
import re
from typing import Any, Dict, List, Optional

from ..base import BaseAssistantAgent

logger = logging.getLogger(__name__)

# ── 安全规则 ──

# 医疗建议边界词（触发免责提示）
MEDICAL_BOUNDARY_KEYWORDS = [
    "诊断", "处方", "用药", "剂量", "开药", "停药", "换药",
    "化验", "检查结果", "指标异常", "CT", "核磁", "B超",
    "手术", "治疗方案", "病理", "癌", "肿瘤",
]

# 紧急转介词（触发危机通道）
CRISIS_KEYWORDS = [
    "自杀", "自残", "不想活", "结束生命", "伤害自己",
    "胸痛", "呼吸困难", "大量出血", "意识不清", "昏迷",
]

# 免责声明
DISCLAIMER = (
    "\n\n---\n"
    "以上为健康科普信息，不构成医疗建议。"
    "如有具体健康问题，请咨询专业医疗人员。"
)


class Agent(BaseAssistantAgent):
    """健康知识科普助手 — 用户层核心Agent"""

    @property
    def name(self) -> str:
        return "health_assistant"

    @property
    def domain(self) -> str:
        return "general"

    # ── 依赖注入 ──

    def _get_rag_pipeline(self):
        try:
            from core.rag.pipeline import RAGPipeline
            return RAGPipeline()
        except ImportError:
            logger.warning("RAGPipeline不可用")
            return None

    def _get_rag_safety(self):
        try:
            from core.safety.rag_safety import RAGSafety
            return RAGSafety()
        except ImportError:
            logger.warning("RAGSafety不可用")
            return None

    def _get_knowledge_retriever(self):
        try:
            from core.knowledge.retriever import KnowledgeRetriever
            return KnowledgeRetriever()
        except ImportError:
            logger.warning("KnowledgeRetriever不可用")
            return None

    def _get_llm_client(self):
        try:
            from core.llm_client import get_llm_client
            return get_llm_client()
        except ImportError:
            logger.warning("LLM client不可用")
            return None

    # ── 核心逻辑 ──

    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        """
        处理用户的健康知识问题

        kwargs:
            user_id: str         — 用户ID
            session_id: str      — 会话ID
            user_profile: dict   — 用户画像（可选，用于个性化科普级别）
            db: AsyncSession     — 数据库会话
        """
        # 0. 基础安全检查（危机词检测）
        if not await self.safety_check(message):
            return self._crisis_response()

        # 1. 医疗边界检测
        boundary_hit = self._check_medical_boundary(message)

        # 2. RAG知识检索
        knowledge = await self._retrieve_knowledge(message)

        # 3. 安全过滤
        safe_knowledge = await self._safety_filter(message, knowledge)

        # 4. LLM生成回答
        answer = await self._generate_answer(
            message, safe_knowledge, kwargs.get("user_profile", {}), boundary_hit
        )

        # 5. 组装响应
        citations = [k.get("source", "") for k in safe_knowledge if k.get("source")]

        return self._format_response(
            content=answer["text"],
            citations=citations[:5],
            knowledge_used=len(safe_knowledge),
            boundary_warning=boundary_hit,
            confidence=answer.get("confidence", 0.6),
        )

    def _crisis_response(self) -> dict:
        """危机响应 — 检测到自伤/紧急医疗"""
        return self._format_response(
            content=(
                "我注意到您可能正在经历一些困难。"
                "如果您有紧急身体不适，请立即拨打120急救电话。"
                "如果您正在经历心理危机，请拨打24小时心理援助热线：400-161-9995。\n\n"
                "您并不孤单，专业的帮助随时在您身边。"
            ),
            safety_intercepted=True,
            action="crisis_referral",
            confidence=1.0,
        )

    def _check_medical_boundary(self, message: str) -> Optional[str]:
        """检测是否触及医疗建议边界"""
        for keyword in MEDICAL_BOUNDARY_KEYWORDS:
            if keyword in message:
                return keyword
        # 检测"我应该吃什么药"类句式
        if re.search(r"(应该|需要|可以)(吃|服用|注射|打|做).*(药|针|手术|治疗)", message):
            return "treatment_advice"
        return None

    async def _retrieve_knowledge(self, query: str) -> List[dict]:
        """RAG检索知识库"""
        # 优先: RAGPipeline（含重排序）
        pipeline = self._get_rag_pipeline()
        if pipeline:
            try:
                results = pipeline.search(query, top_k=5) if hasattr(pipeline, 'search') else []
                if hasattr(pipeline, 'asearch'):
                    results = await pipeline.asearch(query, top_k=5)
                if results:
                    return self._normalize_results(results)
            except Exception as e:
                logger.warning(f"RAGPipeline检索失败: {e}")

        # 降级: KnowledgeRetriever（纯向量检索）
        retriever = self._get_knowledge_retriever()
        if retriever:
            try:
                results = retriever.retrieve(query, top_k=5) if hasattr(retriever, 'retrieve') else []
                if hasattr(retriever, 'aretrieve'):
                    results = await retriever.aretrieve(query, top_k=5)
                if results:
                    return self._normalize_results(results)
            except Exception as e:
                logger.warning(f"KnowledgeRetriever检索失败: {e}")

        # 兜底: 无知识库
        logger.info("知识库不可用，使用LLM内置知识")
        return []

    def _normalize_results(self, results) -> List[dict]:
        """统一RAG结果格式"""
        normalized = []
        for r in results:
            if isinstance(r, dict):
                normalized.append({
                    "content": r.get("content") or r.get("text", ""),
                    "source": r.get("source") or r.get("document_title", ""),
                    "score": r.get("score") or r.get("relevance", 0),
                    "chunk_id": r.get("chunk_id") or r.get("id", ""),
                })
            elif hasattr(r, 'content'):
                normalized.append({
                    "content": getattr(r, 'content', ''),
                    "source": getattr(r, 'source', '') or getattr(r, 'document_title', ''),
                    "score": getattr(r, 'score', 0),
                    "chunk_id": getattr(r, 'id', ''),
                })
            else:
                normalized.append({"content": str(r), "source": "", "score": 0})
        return normalized

    async def _safety_filter(self, query: str, knowledge: List[dict]) -> List[dict]:
        """安全过滤 — 移除不适合直接展示的知识片段"""
        rag_safety = self._get_rag_safety()
        if not rag_safety:
            # 无安全过滤器时走本地规则
            return self._local_safety_filter(knowledge)

        try:
            if hasattr(rag_safety, 'afilter'):
                return await rag_safety.afilter(query, knowledge)
            elif hasattr(rag_safety, 'filter'):
                return rag_safety.filter(query, knowledge)
        except Exception as e:
            logger.warning(f"RAGSafety过滤失败: {e}")

        return self._local_safety_filter(knowledge)

    def _local_safety_filter(self, knowledge: List[dict]) -> List[dict]:
        """本地安全过滤规则"""
        safe = []
        UNSAFE_PATTERNS = [
            r"具体剂量.*\d+\s*(mg|ml|g|片|粒)",  # 具体药物剂量
            r"(静脉|肌肉|皮下)注射",              # 注射操作
            r"手术(步骤|流程|方法)",                # 手术细节
        ]
        for k in knowledge:
            content = k.get("content", "")
            is_safe = True
            for pattern in UNSAFE_PATTERNS:
                if re.search(pattern, content):
                    is_safe = False
                    logger.info(f"安全过滤移除: {content[:50]}...")
                    break
            if is_safe:
                safe.append(k)
        return safe

    async def _generate_answer(
        self, message: str, knowledge: List[dict],
        profile: dict, boundary_hit: Optional[str]
    ) -> dict:
        """LLM生成回答"""
        llm = self._get_llm_client()

        # 构建知识上下文
        knowledge_context = ""
        if knowledge:
            chunks = []
            for i, k in enumerate(knowledge[:5], 1):
                source = k.get("source", "知识库")
                chunks.append(f"[{i}] ({source})\n{k['content'][:500]}")
            knowledge_context = "\n\n".join(chunks)

        # 医疗边界警告
        boundary_note = ""
        if boundary_hit:
            boundary_note = f"""
注意：用户问题涉及"{boundary_hit}"，这超出了健康科普的范围。
你必须：
1. 提供相关的科普知识
2. 明确说明你不能提供个体化医疗建议
3. 建议用户咨询专业医疗人员"""

        if not llm:
            # LLM不可用 — 返回知识片段+免责
            if knowledge:
                text = f"关于您的问题，以下是相关健康知识：\n\n"
                for i, k in enumerate(knowledge[:3], 1):
                    text += f"{i}. {k['content'][:200]}\n\n"
                text += DISCLAIMER
            else:
                text = "抱歉，暂时无法回答您的问题。请稍后重试，或咨询专业医疗人员。"
            return {"text": text, "confidence": 0.3}

        # 构建prompt
        system_prompt = """你是「行健平台」的健康知识助手。你的角色是：
- 提供科学、准确的健康科普信息
- 语言通俗易懂，温暖友好
- 绝不提供个体化诊断或治疗建议
- 遇到具体症状/用药问题时，引导用户咨询医生
- 如有知识库参考资料，优先基于资料回答并注明来源"""

        user_prompt = f"""{boundary_note}

{f'参考资料：{chr(10)}{knowledge_context}' if knowledge_context else '（无知识库参考，请基于通用健康知识回答）'}

用户问题：{message}

请回答（科普级别，不含个体化建议）："""

        try:
            if hasattr(llm, 'achat'):
                response = await llm.achat(user_prompt, system=system_prompt)
            else:
                response = llm.chat(user_prompt, system=system_prompt)

            text = response if isinstance(response, str) else getattr(response, 'content', str(response))

            # 追加免责（如果LLM回答里没有类似声明）
            if "不构成医疗建议" not in text and "咨询" not in text[-100:]:
                text += DISCLAIMER

            confidence = 0.8 if knowledge else 0.6
            if boundary_hit:
                confidence -= 0.1

            return {"text": text, "confidence": confidence}

        except Exception as e:
            logger.error(f"LLM生成失败: {e}")
            fallback = "抱歉，我暂时无法完整回答您的问题。"
            if knowledge:
                fallback += f"\n\n以下是相关参考信息：\n{knowledge[0]['content'][:300]}"
            fallback += DISCLAIMER
            return {"text": fallback, "confidence": 0.3}

"""
RAG 查询管道 — 完整的检索增强生成流程
放置: api/core/rag/pipeline.py

流程: 用户问题 → Embedding → Qdrant Top-K → 上下文拼接 → LLM 生成
"""
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from core.llm.client import LLMClient, LLMResponse
from core.llm.router import LLMRouter
from core.rag.vector_store import QdrantStore, SearchResult

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════
# Prompt 模板
# ══════════════════════════════════════════════

# 通用知识问答
SYSTEM_KNOWLEDGE_QA = """你是 BHP (行为健康促进) 平台的AI健康顾问。
请根据【知识库参考】中的内容回答用户问题。

回答原则:
1. 优先使用知识库中的内容,确保准确性
2. 如果知识库不包含相关信息,诚实说明"目前知识库中没有这方面的内容"
3. 涉及具体数值、阈值、评分标准时,请精确引用
4. 使用通俗中文,避免过度专业术语
5. 如涉及健康建议,请提醒用户咨询专业医疗人员"""

# Coach 对话 (带画像)
SYSTEM_COACH_WITH_PROFILE = """你是 BHP 平台的行为健康教练(Coach)。
你正在与一位用户进行健康行为指导对话。

【用户画像】
{user_profile}

【知识库参考】
{rag_context}

对话原则:
1. 根据用户的行为阶段({stage})和心理准备度({readiness})调整沟通策略
2. 使用动机式访谈技术,多倾听、多共情
3. 不直接给出命令,引导用户自主发现
4. 每次回复控制在150字以内,口语化
5. 如果用户表达负面情绪,优先回应情绪"""

# 处方生成
SYSTEM_PRESCRIPTION = """你是 BHP 平台的行为处方生成引擎。
请根据用户画像和知识库中的干预策略,生成个性化行为处方。

【用户画像】
{user_profile}

【可用干预策略】
{rag_context}

处方格式要求(JSON):
{{
  "daily_tasks": [
    {{"name": "任务名", "duration_min": 分钟数, "difficulty": "easy/medium/hard", "category": "类别"}}
  ],
  "coach_script": "教练开场话术",
  "key_message": "本周核心信息",
  "obstacles_addressed": ["已考虑的障碍"],
  "adjustments": ["基于障碍的调整"]
}}"""


# ══════════════════════════════════════════════
# 管道配置
# ══════════════════════════════════════════════

@dataclass
class RAGConfig:
    """RAG 管道参数"""
    top_k: int = 5                    # 检索条数
    score_threshold: float = 0.35     # 最低相似度
    max_context_chars: int = 3000     # 上下文最大字符数
    enable_rerank: bool = False       # 是否启用重排序 (未来扩展)
    context_template: str = "【{seq}】[{source}/{section}]\n{text}"


@dataclass
class RAGResult:
    """RAG 查询结果"""
    answer: str
    sources: list[dict]       # 引用的知识来源
    llm_response: LLMResponse | None = None
    search_results: list[SearchResult] = field(default_factory=list)
    query: str = ""
    latency_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "answer": self.answer,
            "sources": self.sources,
            "query": self.query,
            "latency_ms": self.latency_ms,
            "model": self.llm_response.model if self.llm_response else "",
            "tokens": self.llm_response.total_tokens if self.llm_response else 0,
            "cost_yuan": self.llm_response.cost_yuan if self.llm_response else 0,
        }


# ══════════════════════════════════════════════
# RAG 管道
# ══════════════════════════════════════════════

class RAGPipeline:
    """
    检索增强生成管道

    用法:
        pipeline = RAGPipeline(llm_client, router, vector_store)
        result = pipeline.query("SPI 评分低于30分是什么意思?")
        print(result.answer)
    """

    def __init__(
        self,
        llm_client: LLMClient,
        router: LLMRouter,
        vector_store: QdrantStore,
        config: RAGConfig | None = None,
    ):
        self.llm = llm_client
        self.router = router
        self.store = vector_store
        self.config = config or RAGConfig()

    # ── 核心查询 ──

    def query(
        self,
        question: str,
        doc_type: str | None = None,
        history: list[dict] | None = None,
        system_override: str | None = None,
    ) -> RAGResult:
        """
        通用知识问答

        Args:
            question: 用户问题
            doc_type: 限定文档类型 (spec/strategy/tcm/clinical)
            history: 对话历史
            system_override: 覆盖默认 system prompt
        """
        t0 = time.time()

        # Step 1: Embedding
        vectors = self.llm.embed([question])
        if not vectors:
            return RAGResult(answer="抱歉,无法处理您的问题。", sources=[], query=question)
        q_vector = vectors[0]

        # Step 2: Search
        if doc_type:
            results = self.store.search_with_filter(
                q_vector, doc_type=doc_type, top_k=self.config.top_k,
            )
        else:
            results = self.store.search(
                q_vector,
                top_k=self.config.top_k,
                score_threshold=self.config.score_threshold,
            )

        # Step 3: Build context
        context = self._build_context(results)

        # Step 4: Generate
        system = system_override or SYSTEM_KNOWLEDGE_QA
        llm_resp = self.router.route_with_rag(
            query=question,
            rag_context=context,
            system=system,
            intent="knowledge_qa",
            extra_messages=history,
        )

        latency = int((time.time() - t0) * 1000)

        sources = [
            {
                "chunk_id": r.chunk_id,
                "source": r.metadata.get("source", ""),
                "section": r.metadata.get("section", ""),
                "score": round(r.score, 3),
            }
            for r in results
        ]

        return RAGResult(
            answer=llm_resp.content,
            sources=sources,
            llm_response=llm_resp,
            search_results=results,
            query=question,
            latency_ms=latency,
        )

    def coach_query(
        self,
        question: str,
        user_profile: dict,
        history: list[dict] | None = None,
    ) -> RAGResult:
        """
        Coach 对话 (带用户画像 + RAG)

        Args:
            question: 用户发言
            user_profile: 用户画像字典
            history: 对话历史
        """
        t0 = time.time()

        # 检索相关策略
        vectors = self.llm.embed([question])
        q_vector = vectors[0] if vectors else []

        results = []
        if q_vector:
            results = self.store.search_with_filter(
                q_vector, doc_type="strategy", top_k=3,
            )
            # 同时检索一般知识
            general = self.store.search(q_vector, top_k=2, score_threshold=0.4)
            results.extend(general)

        context = self._build_context(results)

        # 构建 system prompt
        stage = user_profile.get("behavioral_stage", "未知")
        readiness = user_profile.get("readiness_level", "未知")
        profile_str = self._format_profile(user_profile)

        system = SYSTEM_COACH_WITH_PROFILE.format(
            user_profile=profile_str,
            rag_context=context,
            stage=stage,
            readiness=readiness,
        )

        # 生成
        messages = list(history or [])
        messages.append({"role": "user", "content": question})

        llm_resp = self.router.route(
            messages=messages,
            system=system,
            intent="coach_dialogue",
        )

        latency = int((time.time() - t0) * 1000)

        sources = [
            {"chunk_id": r.chunk_id, "source": r.metadata.get("source", ""), "score": round(r.score, 3)}
            for r in results
        ]

        return RAGResult(
            answer=llm_resp.content,
            sources=sources,
            llm_response=llm_resp,
            search_results=results,
            query=question,
            latency_ms=latency,
        )

    def prescription_query(
        self,
        user_profile: dict,
        layer3_report: dict | None = None,
    ) -> RAGResult:
        """
        处方生成 (RAG 增强)

        检索匹配的干预策略 → LLM 生成个性化处方
        """
        t0 = time.time()

        # 构建检索查询: 用画像关键信息组合
        stage = user_profile.get("behavioral_stage", "S0")
        obstacles = user_profile.get("top_obstacles", [])
        causes = user_profile.get("dominant_causes", [])

        search_text = (
            f"行为阶段{stage} "
            f"障碍:{','.join(obstacles[:3])} "
            f"动因:{','.join(causes[:3])}"
        )
        vectors = self.llm.embed([search_text])
        q_vector = vectors[0] if vectors else []

        results = []
        if q_vector:
            # 检索干预策略
            results = self.store.search_with_filter(
                q_vector, doc_type="strategy", top_k=5,
            )
            # 检索行为组合
            combos = self.store.search_with_filter(
                q_vector, doc_type="combination", top_k=3,
            )
            results.extend(combos)

        context = self._build_context(results)
        profile_str = self._format_profile(user_profile)

        system = SYSTEM_PRESCRIPTION.format(
            user_profile=profile_str,
            rag_context=context,
        )

        messages = [{"role": "user", "content": "请根据以上画像生成本周行为处方。"}]

        llm_resp = self.router.route(
            messages=messages,
            system=system,
            intent="prescription_generate",
            temperature=0.5,
        )

        latency = int((time.time() - t0) * 1000)
        sources = [
            {"chunk_id": r.chunk_id, "source": r.metadata.get("source", ""), "score": round(r.score, 3)}
            for r in results
        ]

        return RAGResult(
            answer=llm_resp.content,
            sources=sources,
            llm_response=llm_resp,
            search_results=results,
            query=search_text,
            latency_ms=latency,
        )

    def search_only(
        self,
        question: str,
        doc_type: str | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        """纯检索, 不调 LLM (用于调试/展示)"""
        vectors = self.llm.embed([question])
        if not vectors:
            return []

        if doc_type:
            results = self.store.search_with_filter(
                vectors[0], doc_type=doc_type, top_k=top_k,
            )
        else:
            results = self.store.search(vectors[0], top_k=top_k)

        return [
            {
                "chunk_id": r.chunk_id,
                "text": r.text[:200],
                "score": round(r.score, 3),
                "source": r.metadata.get("source", ""),
                "section": r.metadata.get("section", ""),
                "doc_type": r.metadata.get("doc_type", ""),
            }
            for r in results
        ]

    # ── 内部方法 ──

    def _build_context(self, results: list[SearchResult]) -> str:
        """将检索结果拼接为上下文文本"""
        if not results:
            return "(未找到相关知识库内容)"

        parts = []
        total_chars = 0
        for i, r in enumerate(results):
            entry = self.config.context_template.format(
                seq=i + 1,
                source=r.metadata.get("source", ""),
                section=r.metadata.get("section", ""),
                text=r.text,
            )
            if total_chars + len(entry) > self.config.max_context_chars:
                break
            parts.append(entry)
            total_chars += len(entry)

        return "\n\n".join(parts)

    def _format_profile(self, profile: dict) -> str:
        """格式化用户画像为可读文本"""
        lines = []
        field_map = {
            "behavioral_stage": "行为阶段",
            "readiness_level": "心理准备度",
            "spi_score": "SPI评分",
            "health_competency": "健康能力等级",
            "behavior_type": "行为类型",
            "cultivation_stage": "养成阶段",
            "top_obstacles": "主要障碍",
            "dominant_causes": "主要动因",
            "support_level": "支持体系",
            "growth_level": "成长等级",
        }
        for key, label in field_map.items():
            val = profile.get(key)
            if val is not None:
                if isinstance(val, list):
                    val = ", ".join(str(v) for v in val)
                lines.append(f"- {label}: {val}")

        return "\n".join(lines) if lines else "(画像信息不完整)"


# ══════════════════════════════════════════════
# 便捷工厂函数
# ══════════════════════════════════════════════

def create_rag_pipeline(
    qdrant_url: str | None = None,
    collection: str | None = None,
    config: RAGConfig | None = None,
) -> RAGPipeline:
    """
    一站式创建 RAG Pipeline

    用法:
        pipeline = create_rag_pipeline()
        result = pipeline.query("什么是SPI?")
    """
    client = LLMClient()
    router = LLMRouter(client)
    store = QdrantStore(base_url=qdrant_url, collection=collection)
    return RAGPipeline(client, router, store, config)

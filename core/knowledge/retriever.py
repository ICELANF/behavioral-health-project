"""
RAG 检索引擎 + 引用标注 (v2 — 本地优先)

适配: 同步 SQLAlchemy + numpy 余弦相似度 (无 pgvector)

核心职责:
  1. 根据 agent_id + tenant_id 确定搜索范围
  2. 从 DB 取候选 chunks → Python 层算向量相似度 + scope_boost → 排序
  3. 构建「本地优先」的 prompt 注入段
  4. 格式化引用数据，区分来源类型
"""

import re
import json
import logging
import numpy as np
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────
# Agent → 知识领域映射
# ──────────────────────────────────────────

AGENT_DOMAIN_MAP: Dict[str, List[str]] = {
    "sleep":         ["sleep", "mental", "behavior"],
    "glucose":       ["glucose", "nutrition", "metabolism"],
    "stress":        ["stress", "mental", "behavior", "tcm"],
    "mental":        ["mental", "psychology", "behavior"],
    "nutrition":     ["nutrition", "metabolism", "tcm"],
    "exercise":      ["exercise", "rehabilitation", "metabolism"],
    "tcm":           ["tcm", "nutrition", "constitution"],
    "crisis":        ["crisis", "mental"],
    "motivation":    ["motivation", "behavior", "psychology"],
    "behavior_rx":   ["behavior", "motivation", "psychology", "habit"],
    "weight":        ["weight", "nutrition", "exercise", "metabolism"],
    "cardiac_rehab": ["cardiac", "exercise", "nutrition", "rehabilitation"],
}

# ──────────────────────────────────────────
# Scope 优先级加权
# ──────────────────────────────────────────

SCOPE_BOOST = {
    "tenant":   0.15,    # 专家私有知识：最高优先
    "domain":   0.08,    # 领域知识：次优先
    "platform": 0.00,    # 平台公共：基准分
}


# ──────────────────────────────────────────
# 来源类型
# ──────────────────────────────────────────

class SourceType:
    """引用来源类型"""
    KNOWLEDGE = "knowledge"        # 本地知识库
    MODEL_SUPPLEMENT = "model"     # 模型补充


# ──────────────────────────────────────────
# 数据结构
# ──────────────────────────────────────────

@dataclass
class Citation:
    """一条引用"""
    index: int                       # [1], [2] ...
    doc_title: str
    heading: str
    author: str
    source: str
    page_number: Optional[int]
    relevance_score: float
    content_preview: str             # 前150字
    chunk_id: int
    document_id: int
    scope: str = "platform"          # tenant/domain/platform
    source_type: str = SourceType.KNOWLEDGE
    evidence_tier: str = ""           # T1/T2/T3/T4

    @property
    def scope_label(self) -> str:
        return {
            "tenant": "🔒 专家私有",
            "domain": "📂 领域知识",
            "platform": "🌐 平台公共",
        }.get(self.scope, self.scope)

    @property
    def label(self) -> str:
        parts = [f"[{self.index}]"]
        if self.author:
            parts.append(self.author)
        parts.append(f"《{self.doc_title}》")
        if self.heading:
            parts.append(f"> {self.heading}")
        if self.page_number:
            parts.append(f"(第{self.page_number}页)")
        return " ".join(parts)

    @property
    def short_label(self) -> str:
        return f"[{self.index}] {self.doc_title}" + (f" · {self.heading}" if self.heading else "")

    def to_dict(self) -> dict:
        d = {
            "index": self.index,
            "label": self.label,
            "shortLabel": self.short_label,
            "docTitle": self.doc_title,
            "heading": self.heading,
            "author": self.author,
            "source": self.source,
            "pageNumber": self.page_number,
            "relevanceScore": round(self.relevance_score, 3),
            "contentPreview": self.content_preview,
            "chunkId": self.chunk_id,
            "documentId": self.document_id,
            "scope": self.scope,
            "scopeLabel": self.scope_label,
            "sourceType": self.source_type,
        }
        if self.evidence_tier:
            d["evidenceTier"] = self.evidence_tier
        return d


@dataclass
class RAGContext:
    """检索结果"""
    query: str
    citations: List[Citation] = field(default_factory=list)
    prompt_injection: str = ""
    domains_searched: List[str] = field(default_factory=list)

    @property
    def has_knowledge(self) -> bool:
        return len(self.citations) > 0

    @property
    def citation_count(self) -> int:
        return len(self.citations)

    def format_response(self, llm_response: str) -> Dict[str, Any]:
        """格式化 LLM 回复 + 引用数据 → 前端消费结构"""
        used = sorted(set(int(r) for r in re.findall(r'\[(\d+)\]', llm_response)))
        model_sections = self._extract_model_supplements(llm_response)
        has_supplement = len(model_sections) > 0

        scope_breakdown = {}
        for c in self.citations:
            if c.index in used:
                scope_breakdown[c.scope] = scope_breakdown.get(c.scope, 0) + 1

        return {
            "text": llm_response,
            "hasKnowledge": self.has_knowledge,
            "citationsUsed": used,
            "citations": [c.to_dict() for c in self.citations if c.index in used],
            "knowledgeCitations": [
                c.to_dict() for c in self.citations
                if c.index in used and c.source_type == SourceType.KNOWLEDGE
            ],
            "hasModelSupplement": has_supplement,
            "modelSupplementSections": model_sections,
            "allCitations": [c.to_dict() for c in self.citations],
            "domainsSearched": self.domains_searched,
            "sourceStats": {
                "knowledgeCount": len([c for c in self.citations if c.index in used]),
                "modelSupplement": has_supplement,
                "scopeBreakdown": scope_breakdown,
            },
        }

    @staticmethod
    def _extract_model_supplements(text: str) -> List[str]:
        """提取 LLM 回复中的模型补充段落"""
        sections = []
        pattern1 = re.findall(r'【(?:补充|模型补充|补充说明)】\s*(.+?)(?=\n\n|\n【|$)', text, re.DOTALL)
        sections.extend(pattern1)
        pattern2 = re.findall(r'\*{0,2}补充说明\*{0,2}[:：]\s*(.+?)(?=\n\n|\n【|$)', text, re.DOTALL)
        sections.extend(pattern2)
        pattern3 = re.findall(r'【以下为通用专业知识[^】]*】\s*(.+?)(?=$)', text, re.DOTALL)
        sections.extend(pattern3)
        return [s.strip() for s in sections if s.strip()]


# ──────────────────────────────────────────
# 余弦相似度 (numpy)
# ──────────────────────────────────────────

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    a_arr = np.array(a, dtype=np.float32)
    b_arr = np.array(b, dtype=np.float32)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a_arr, b_arr) / (norm_a * norm_b))


# ──────────────────────────────────────────
# 检索引擎
# ──────────────────────────────────────────

class KnowledgeRetriever:
    """
    知识检索引擎 (v2 — 本地优先)

    适配: 同步 Session + numpy 余弦相似度
    """

    def __init__(self, db: Session, embedder):
        self.db = db
        self.embedder = embedder

    def retrieve(
        self,
        query: str,
        agent_id: str = "",
        tenant_id: str = "",
        top_k: int = 5,
        min_score: float = 0.35,
    ) -> RAGContext:
        """
        主入口: 根据 Agent + 租户上下文做语义检索

        策略:
          1. SQL 查候选 chunks (scope 条件过滤)
          2. Python 层 numpy 余弦相似度
          3. + scope_boost + doc_priority 加权
          4. 排序取 top_k
        """
        from core.models import KnowledgeChunk, KnowledgeDocument

        domains = AGENT_DOMAIN_MAP.get(agent_id, ["general"])

        # 1. 向量化查询
        query_vector = self.embedder.embed_query(query)
        if not query_vector:
            logger.warning("查询向量为空, 跳过 RAG")
            return RAGContext(query=query, domains_searched=domains)

        # 2. SQL 查候选 chunks
        q = self.db.query(KnowledgeChunk).join(
            KnowledgeDocument,
            KnowledgeChunk.document_id == KnowledgeDocument.id,
        ).filter(
            KnowledgeDocument.is_active == True,
            KnowledgeDocument.status == "ready",
            KnowledgeChunk.embedding_1024.isnot(None),
        )

        # scope 条件
        from sqlalchemy import or_
        scope_conds = []
        if tenant_id:
            scope_conds.append(
                (KnowledgeChunk.scope == "tenant") & (KnowledgeChunk.tenant_id == tenant_id)
            )
        scope_conds.append(
            (KnowledgeChunk.scope == "domain") & (KnowledgeChunk.domain_id.in_(domains))
        )
        scope_conds.append(
            (KnowledgeChunk.scope == "platform") &
            (KnowledgeChunk.domain_id.in_(domains + ["general"]))
        )
        q = q.filter(or_(*scope_conds))

        candidates = q.all()

        if not candidates:
            logger.info(f"RAG: 无候选 chunks (agent={agent_id}, domains={domains})")
            return RAGContext(
                query=query,
                prompt_injection=KnowledgeRetriever._build_no_knowledge_injection(),
                domains_searched=domains,
            )

        # 3. Python 层计算相似度 + scope_boost
        scored = []
        for chunk in candidates:
            try:
                chunk_vec = json.loads(chunk.embedding_1024)
            except (json.JSONDecodeError, TypeError):
                continue

            raw_score = _cosine_similarity(query_vector, chunk_vec)
            if raw_score < min_score:
                continue

            boost = SCOPE_BOOST.get(chunk.scope, 0.0)

            # doc_priority 微调: (priority - 5) * 0.01
            doc = self.db.query(KnowledgeDocument).filter(
                KnowledgeDocument.id == chunk.document_id
            ).first()
            priority_adj = ((doc.priority or 5) - 5) * 0.01 if doc else 0.0

            # freshness_penalty: 过期文档轻微降权
            freshness_penalty = 0.0
            now = datetime.utcnow()
            if doc and doc.expires_at and doc.expires_at < now:
                days_expired = (now - doc.expires_at).days
                freshness_penalty = min(days_expired * 0.005, 0.10)

            boosted = raw_score + boost + priority_adj - freshness_penalty
            scored.append((chunk, raw_score, boosted, doc))

        # 4. 排序取 top_k
        scored.sort(key=lambda x: x[2], reverse=True)
        top_results = scored[:top_k]

        # 5. 构建引用列表
        citations = []
        for i, (chunk, raw, boosted, doc) in enumerate(top_results):
            preview = chunk.content[:150] + "..." if len(chunk.content) > 150 else chunk.content
            citations.append(Citation(
                index=i + 1,
                doc_title=chunk.doc_title or "未知文档",
                heading=chunk.heading or "",
                author=chunk.doc_author or "",
                source=chunk.doc_source or "",
                page_number=chunk.page_number,
                relevance_score=boosted,
                content_preview=preview,
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                scope=chunk.scope or "platform",
                source_type=SourceType.KNOWLEDGE,
                evidence_tier=getattr(doc, 'evidence_tier', '') or "",
            ))

        # 6. 构建 prompt 注入
        prompt_injection = self._build_injection(citations, top_results)

        if citations:
            scope_summary = {}
            for c in citations:
                scope_summary[c.scope] = scope_summary.get(c.scope, 0) + 1
            logger.info(
                f"📚 RAG: {agent_id}@{tenant_id} | "
                f"{len(citations)} 条 | scope: {scope_summary}"
            )

        return RAGContext(
            query=query,
            citations=citations,
            prompt_injection=prompt_injection,
            domains_searched=domains,
        )

    def _build_injection(self, citations: List[Citation], top_results) -> str:
        """构建「本地优先」的 prompt 注入段"""
        if not citations:
            return self._build_no_knowledge_injection()

        # 按 scope 分组
        tenant_refs, domain_refs, platform_refs = [], [], []
        for cite, (chunk, raw, boosted, doc) in zip(citations, top_results):
            block = self._format_ref_block(cite, chunk)
            if cite.scope == "tenant":
                tenant_refs.append(block)
            elif cite.scope == "domain":
                domain_refs.append(block)
            else:
                platform_refs.append(block)

        knowledge_blocks = []

        if tenant_refs:
            knowledge_blocks.append(
                f"━━━ 🔒 专家私有资料 (最高优先) ━━━\n"
                f"{''.join(tenant_refs)}"
            )
        if domain_refs:
            knowledge_blocks.append(
                f"━━━ 📂 领域专业知识 ━━━\n"
                f"{''.join(domain_refs)}"
            )
        if platform_refs:
            knowledge_blocks.append(
                f"━━━ 🌐 平台通用知识 ━━━\n"
                f"{''.join(platform_refs)}"
            )

        return f"""
<knowledge_base>
以下是与用户问题相关的专业知识资料，来自本平台知识库。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
回答规则 (严格遵守):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. **本地知识优先**: 回答时必须优先使用下方的知识库参考资料
   优先级: 专家私有资料 > 领域专业知识 > 平台通用知识
   只要参考资料中有相关信息，就必须引用，不得跳过

2. **引用标注**: 引用知识库内容时用 [1] [2] 等编号标记出处
   同一段话如涉及多条资料，应标注所有相关编号

3. **本地资料与模型知识有冲突时**: 以本地资料为准
   本地资料是专家审核过的权威内容，不可被模型知识覆盖

4. **模型知识补充** (仅在以下情况使用):
   - 知识库资料不足以完整回答用户问题
   - 用户追问了知识库未涵盖的内容
   使用模型知识时，必须用「【补充】」标记开头，例如:
   【补充】根据一般临床经验，...
   没有这个标记的内容，用户会认为来自知识库

5. **禁止编造**: 不得编造知识库中没有的具体数据、比例、方案
   如不确定，宁可说"建议进一步咨询"也不编

6. **回答结构** (推荐):
   - 先用知识库资料直接回答用户问题 [带引用编号]
   - 如有不足，再用「【补充】」段补充
   - 最后可给出建议

{"".join(knowledge_blocks)}
</knowledge_base>
"""

    @staticmethod
    def _build_no_knowledge_injection() -> str:
        """无知识库命中时的 prompt"""
        return """
<knowledge_note>
当前问题未在知识库中找到直接相关的资料。
请使用你的专业知识回答，但需注意:
1. 在回复开头标明: 【以下为通用专业知识，非本平台专属资料】
2. 不要编造具体的数据、比例或研究引用
3. 如涉及具体治疗方案，建议用户咨询专业医生
</knowledge_note>
"""

    @staticmethod
    def _format_ref_block(cite: 'Citation', chunk) -> str:
        """格式化单条参考资料"""
        source_info = f"来源: {cite.author + '，' if cite.author else ''}《{cite.doc_title}》"
        if cite.heading:
            source_info += f" > {cite.heading}"
        if cite.page_number:
            source_info += f" (第{cite.page_number}页)"

        return f"""
--- 参考资料 [{cite.index}] ---
{source_info}
相关度: {cite.relevance_score:.0%}

{chunk.content}
"""


# ──────────────────────────────────────────
# Agent 集成辅助函数
# ──────────────────────────────────────────

def build_rag_prompt(
    base_system_prompt: str,
    rag_context: RAGContext,
    persona: dict = None,
) -> str:
    """构建 RAG 增强后的系统 prompt"""
    parts = [base_system_prompt]

    if persona:
        if persona.get("name"):
            parts.append(f"\n你的身份: {persona['name']}")
        if persona.get("tone"):
            parts.append(f"你的语气风格: {persona['tone']}")

    parts.append(rag_context.prompt_injection)
    return "\n".join(parts)

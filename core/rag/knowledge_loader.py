"""
知识库加载器 — 文档切分 + 向量化 + 写入
放置: api/core/rag/knowledge_loader.py

支持: .md / .txt / .json (策略话术)
切分策略: 按段落, chunk_size=512 tokens, overlap=50
"""
import hashlib
import json
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════
# 文档类型
# ══════════════════════════════════════════════

DOC_TYPES = {
    "spec": "BHP规范文档",
    "strategy": "干预策略话术",
    "combination": "行为组合模板",
    "tcm": "中医体质知识",
    "clinical": "临床指南",
    "course": "课程内容",
    "faq": "常见问答",
}


@dataclass
class TextChunk:
    """切分后的文本块"""
    chunk_id: str       # 唯一ID: {source}_{seq}
    text: str
    source: str         # 文件名
    doc_type: str       # spec/strategy/...
    section: str        # 所属章节标题
    seq: int            # 序号
    char_count: int

    def to_payload(self) -> dict:
        return {
            "text": self.text,
            "source": self.source,
            "doc_type": self.doc_type,
            "section": self.section,
            "seq": self.seq,
            "char_count": self.char_count,
        }


# ══════════════════════════════════════════════
# 文本切分器
# ══════════════════════════════════════════════

class TextChunker:
    """按段落切分, 保持语义完整性"""

    def __init__(
        self,
        chunk_size: int = 512,       # 目标 chunk 大小 (字符数, ~200 tokens)
        chunk_overlap: int = 50,     # 重叠区
        min_chunk_size: int = 50,    # 最小 chunk (太短就合并)
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk_markdown(self, text: str, source: str, doc_type: str) -> list[TextChunk]:
        """切分 Markdown 文档, 按标题分节"""
        chunks = []
        current_section = "概述"
        sections = self._split_by_headers(text)

        seq = 0
        for section_title, section_text in sections:
            if section_title:
                current_section = section_title

            # 段落切分
            paragraphs = self._split_paragraphs(section_text)

            # 滑动窗口合并
            buffer = ""
            for para in paragraphs:
                if len(buffer) + len(para) > self.chunk_size and len(buffer) >= self.min_chunk_size:
                    chunks.append(self._make_chunk(
                        buffer.strip(), source, doc_type, current_section, seq
                    ))
                    seq += 1
                    # 重叠: 保留 buffer 末尾
                    buffer = buffer[-self.chunk_overlap:] + "\n" + para
                else:
                    buffer = buffer + "\n" + para if buffer else para

            # 剩余内容
            if buffer.strip() and len(buffer.strip()) >= self.min_chunk_size:
                chunks.append(self._make_chunk(
                    buffer.strip(), source, doc_type, current_section, seq
                ))
                seq += 1

        return chunks

    def chunk_strategies(self, strategies: list[dict], source: str) -> list[TextChunk]:
        """切分干预策略 JSON — 每条策略一个 chunk"""
        chunks = []
        for i, s in enumerate(strategies):
            text_parts = []
            if "readiness_level" in s:
                text_parts.append(f"准备度阶段: {s['readiness_level']}")
            if "category" in s:
                text_parts.append(f"动因类别: {s['category']}")
            if "technique" in s:
                text_parts.append(f"干预技术: {s['technique']}")
            if "script_zh" in s:
                text_parts.append(f"话术: {s['script_zh']}")
            if "description" in s:
                text_parts.append(f"说明: {s['description']}")

            text = "\n".join(text_parts)
            chunks.append(self._make_chunk(
                text, source, "strategy", s.get("readiness_level", ""), i
            ))
        return chunks

    def chunk_plain_text(self, text: str, source: str, doc_type: str) -> list[TextChunk]:
        """切分纯文本"""
        paragraphs = self._split_paragraphs(text)
        chunks = []
        seq = 0
        buffer = ""

        for para in paragraphs:
            if len(buffer) + len(para) > self.chunk_size and len(buffer) >= self.min_chunk_size:
                chunks.append(self._make_chunk(
                    buffer.strip(), source, doc_type, "", seq
                ))
                seq += 1
                buffer = buffer[-self.chunk_overlap:] + "\n" + para
            else:
                buffer = buffer + "\n" + para if buffer else para

        if buffer.strip() and len(buffer.strip()) >= self.min_chunk_size:
            chunks.append(self._make_chunk(buffer.strip(), source, doc_type, "", seq))

        return chunks

    # ── 内部方法 ──

    def _split_by_headers(self, text: str) -> list[tuple[str, str]]:
        """按 markdown 标题分节"""
        pattern = r"^(#{1,4})\s+(.+)$"
        sections = []
        current_title = ""
        current_text = ""

        for line in text.split("\n"):
            match = re.match(pattern, line)
            if match:
                if current_text.strip():
                    sections.append((current_title, current_text.strip()))
                current_title = match.group(2).strip()
                current_text = ""
            else:
                current_text += line + "\n"

        if current_text.strip():
            sections.append((current_title, current_text.strip()))

        return sections if sections else [("", text)]

    def _split_paragraphs(self, text: str) -> list[str]:
        """按空行分段, 过滤空段"""
        parts = re.split(r"\n\s*\n", text)
        return [p.strip() for p in parts if p.strip()]

    def _make_chunk(
        self, text: str, source: str, doc_type: str, section: str, seq: int
    ) -> TextChunk:
        cid = f"{source}_{seq:04d}"
        return TextChunk(
            chunk_id=cid,
            text=text,
            source=source,
            doc_type=doc_type,
            section=section,
            seq=seq,
            char_count=len(text),
        )


# ══════════════════════════════════════════════
# 知识库加载器
# ══════════════════════════════════════════════

class KnowledgeLoader:
    """
    加载文档 → 切分 → 向量化 → 写入 Qdrant

    用法:
        loader = KnowledgeLoader(llm_client, qdrant_store)
        stats = loader.load_directory("/path/to/knowledge/")
        stats = loader.load_file("/path/to/spec.md", doc_type="spec")
    """

    def __init__(self, llm_client, vector_store):
        """
        Args:
            llm_client: core.llm.client.LLMClient 实例
            vector_store: core.rag.vector_store.QdrantStore 实例
        """
        self.llm = llm_client
        self.store = vector_store
        self.chunker = TextChunker()

    def load_file(
        self,
        filepath: str,
        doc_type: str = "spec",
        replace: bool = True,
    ) -> dict:
        """
        加载单个文件

        Args:
            filepath: 文件路径
            doc_type: 文档类型 (spec/strategy/tcm/clinical/course/faq)
            replace: 是否先删除该来源的旧数据

        Returns:
            {"source": ..., "chunks": N, "vectors": N}
        """
        path = Path(filepath)
        source = path.name
        text = path.read_text(encoding="utf-8")

        # 切分
        if path.suffix == ".json":
            data = json.loads(text)
            if isinstance(data, list):
                chunks = self.chunker.chunk_strategies(data, source)
            else:
                chunks = self.chunker.chunk_plain_text(
                    json.dumps(data, ensure_ascii=False, indent=2),
                    source, doc_type,
                )
        elif path.suffix == ".md":
            chunks = self.chunker.chunk_markdown(text, source, doc_type)
        else:
            chunks = self.chunker.chunk_plain_text(text, source, doc_type)

        if not chunks:
            return {"source": source, "chunks": 0, "vectors": 0}

        # 向量化 (分批, 每批20条)
        all_points = []
        for i in range(0, len(chunks), 20):
            batch = chunks[i:i+20]
            texts = [c.text for c in batch]
            vectors = self.llm.embed(texts)

            for chunk, vec in zip(batch, vectors):
                all_points.append({
                    "id": chunk.chunk_id,
                    "vector": vec,
                    "payload": chunk.to_payload(),
                })

        # 写入 (先删旧数据)
        self.store.ensure_collection()
        if replace:
            self.store.delete_by_source(source)

        written = self.store.upsert(all_points)

        logger.info(f"Loaded {source}: {len(chunks)} chunks, {written} vectors")
        return {"source": source, "chunks": len(chunks), "vectors": written}

    def load_directory(
        self,
        dirpath: str,
        doc_type_map: dict[str, str] | None = None,
    ) -> dict:
        """
        加载整个目录

        Args:
            dirpath: 目录路径
            doc_type_map: 文件名 → doc_type 映射
                         默认按后缀猜测
        """
        results = []
        dirpath = Path(dirpath)

        for fp in sorted(dirpath.glob("*")):
            if fp.suffix not in (".md", ".txt", ".json"):
                continue
            if fp.name.startswith(".") or fp.name.startswith("_"):
                continue

            # 确定 doc_type
            if doc_type_map and fp.name in doc_type_map:
                dtype = doc_type_map[fp.name]
            else:
                dtype = self._guess_doc_type(fp.name)

            stat = self.load_file(str(fp), doc_type=dtype)
            results.append(stat)

        total_chunks = sum(r["chunks"] for r in results)
        total_vectors = sum(r["vectors"] for r in results)
        return {
            "files": len(results),
            "total_chunks": total_chunks,
            "total_vectors": total_vectors,
            "details": results,
        }

    def load_intervention_strategies(self, json_path: str) -> dict:
        """专用: 加载干预策略 JSON"""
        return self.load_file(json_path, doc_type="strategy")

    def load_change_causes(self, json_path: str) -> dict:
        """专用: 加载改变动因 JSON"""
        return self.load_file(json_path, doc_type="strategy")

    def _guess_doc_type(self, filename: str) -> str:
        """根据文件名猜测文档类型"""
        fn = filename.lower()
        if "strategy" in fn or "intervention" in fn:
            return "strategy"
        if "tcm" in fn or "体质" in fn or "中医" in fn:
            return "tcm"
        if "clinical" in fn or "指南" in fn or "代谢" in fn:
            return "clinical"
        if "course" in fn or "课程" in fn:
            return "course"
        if "faq" in fn or "问答" in fn:
            return "faq"
        if "combination" in fn or "组合" in fn:
            return "combination"
        return "spec"

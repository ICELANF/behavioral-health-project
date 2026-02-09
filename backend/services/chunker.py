"""
智能分块 + Embedding 服务

SmartChunker  — 将 ParsedDocument 切分为 ChunkItem
EmbeddingService — 文本向量化 (优先 sentence_transformers, 回退 Ollama)
"""
import sys, os
from dataclasses import dataclass
from typing import List, Optional

_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


# ── 数据类 ──

@dataclass
class ChunkItem:
    """一个分块"""
    index: int
    content: str
    heading: str = ""
    doc_title: str = ""


# ── 分块器 ──

class SmartChunker:
    """智能分块器 — 将 ParsedDocument 切分为多个 ChunkItem"""

    def __init__(self, max_tokens: int = 512, overlap: int = 50, min_tokens: int = 5):
        self.max_tokens = max_tokens
        self.overlap = overlap
        self.min_tokens = min_tokens

    def chunk(self, doc) -> List[ChunkItem]:
        """
        接收 ParsedDocument, 返回 ChunkItem 列表.
        利用 core/knowledge/chunker.py 的 chunk_markdown + 自定义逻辑.
        """
        chunks: List[ChunkItem] = []
        idx = 0

        for section in doc.sections:
            text = section.content
            if not text or not text.strip():
                continue

            sub_chunks = self._split_section(text)
            for sub in sub_chunks:
                if len(sub) < self.min_tokens:
                    continue
                chunks.append(ChunkItem(
                    index=idx,
                    content=sub,
                    heading=section.heading,
                    doc_title=doc.title,
                ))
                idx += 1

        return chunks

    def _split_section(self, text: str) -> List[str]:
        """按 max_tokens (以字符估算) 切分一个章节"""
        max_chars = self.max_tokens * 2  # 中文 ~1字≈1.5token, 留余量
        if len(text) <= max_chars:
            return [text]

        paragraphs = text.split("\n\n")
        result = []
        current = ""

        for para in paragraphs:
            # 单段落超长 → 按 max_chars 硬切
            if len(para) > max_chars:
                if current.strip():
                    result.append(current.strip())
                    current = ""
                for i in range(0, len(para), max_chars - self.overlap):
                    chunk = para[i:i + max_chars]
                    if chunk.strip():
                        result.append(chunk.strip())
                continue

            if len(current) + len(para) + 2 > max_chars and current:
                result.append(current.strip())
                # overlap
                tail = current[-self.overlap:] if self.overlap else ""
                current = tail + "\n\n" + para
            else:
                current = (current + "\n\n" + para) if current else para

        if current.strip():
            result.append(current.strip())

        return result


# ── 向量化服务 ──

class EmbeddingService:
    """
    Embedding 向量化服务.
    优先使用 sentence_transformers (本地模型),
    回退到 Ollama nomic-embed-text.
    """

    def __init__(self, model_name: str = None):
        self._st_model = None
        self._ollama = None

        # 尝试 sentence_transformers
        try:
            from sentence_transformers import SentenceTransformer
            name = model_name or "shibing624/text2vec-base-chinese"
            self._st_model = SentenceTransformer(name)
            self._dim = self._st_model.get_sentence_embedding_dimension()
            return
        except Exception:
            pass

        # 回退 Ollama
        try:
            from core.knowledge.embedding_service import EmbeddingService as OllamaEmbed
            self._ollama = OllamaEmbed()
            self._dim = 768
        except Exception as e:
            raise RuntimeError(
                f"无可用的 Embedding 后端. "
                f"请安装 sentence-transformers 或启动 Ollama. 错误: {e}"
            )

    def embed(self, text: str) -> List[float]:
        """单条文本 → 768维向量"""
        if self._st_model is not None:
            vec = self._st_model.encode(text, normalize_embeddings=True)
            return vec.tolist()
        if self._ollama is not None:
            return self._ollama.embed_query(text)
        return [0.0] * 768

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量向量化"""
        if self._st_model is not None:
            vecs = self._st_model.encode(texts, normalize_embeddings=True)
            return [v.tolist() for v in vecs]
        if self._ollama is not None:
            return self._ollama.embed_batch(texts)
        return [[0.0] * 768 for _ in texts]


__all__ = ["SmartChunker", "ChunkItem", "EmbeddingService"]

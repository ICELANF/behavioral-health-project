"""
Ollama 嵌入服务

封装 Ollama nomic-embed-text 嵌入接口，
提供 embed_query (单条) 和 embed_batch (批量) 方法。
"""

import os
import httpx
import logging
from typing import List

logger = logging.getLogger(__name__)

OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")


class EmbeddingService:
    """封装 Ollama nomic-embed-text 嵌入"""

    def __init__(self, model_name: str = None, base_url: str = None):
        self.model = model_name or EMBED_MODEL
        self.base_url = base_url or OLLAMA_API_URL
        self._client = httpx.Client(timeout=60.0)

    def embed_query(self, text: str) -> List[float]:
        """文本 → 向量 (同步调用 Ollama /api/embeddings)"""
        try:
            resp = self._client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("embedding", [])
        except Exception as e:
            logger.error(f"Embedding 失败: {e}")
            return []

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入 (逐条调用，Ollama 不支持原生批量)"""
        results = []
        for i, text in enumerate(texts):
            vec = self.embed_query(text)
            results.append(vec)
            if (i + 1) % 50 == 0:
                logger.info(f"Embedding 进度: {i + 1}/{len(texts)}")
        return results

    def close(self):
        self._client.close()

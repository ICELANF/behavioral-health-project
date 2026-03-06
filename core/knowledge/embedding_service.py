"""
嵌入服务 - 支持 Ollama 和 DashScope
"""
import os
import httpx
import logging
from typing import List

logger = logging.getLogger(__name__)

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "mxbai-embed-large:latest")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
DASHSCOPE_API_KEY = os.getenv("CLOUD_LLM_API_KEY", "")
DASHSCOPE_EMBED_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-v3")

class EmbeddingService:
    def __init__(self, model_name: str = None, base_url: str = None):
        self.provider = EMBEDDING_PROVIDER
        self.model = model_name or EMBED_MODEL
        self.base_url = base_url or OLLAMA_API_URL
        self.expected_dim = EMBEDDING_DIMENSION
        self._client = httpx.Client(timeout=60.0)

    def embed_query(self, text: str) -> List[float]:
        try:
            if self.provider == "dashscope":
                return self._embed_dashscope(text)
            else:
                return self._embed_ollama(text)
        except Exception as e:
            logger.error(f"Embedding 失败: {e}")
            return []

    def _embed_dashscope(self, text: str) -> List[float]:
        resp = self._client.post(
            "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings",
            headers={
                "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": DASHSCOPE_EMBED_MODEL,
                "input": text,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        vec = data["data"][0]["embedding"]
        return vec

    def _embed_ollama(self, text: str) -> List[float]:
        resp = self._client.post(
            f"{self.base_url}/api/embeddings",
            json={"model": self.model, "prompt": text},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("embedding", [])

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        results = []
        for i, text in enumerate(texts):
            vec = self.embed_query(text)
            results.append(vec)
            if (i + 1) % 50 == 0:
                logger.info(f"Embedding 进度: {i + 1}/{len(texts)}")
        return results

    def close(self):
        self._client.close()

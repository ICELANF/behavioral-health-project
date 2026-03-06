"""
嵌入服务 — 支持 Ollama / DashScope 双 provider

通过环境变量 EMBEDDING_PROVIDER 切换:
  - ollama (默认, 本地开发)
  - dashscope (生产, 阿里云 text-embedding-v3)

统一接口: embed_query / embed_batch
"""

import os
import httpx
import logging
from typing import List

logger = logging.getLogger(__name__)

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1024"))

# Ollama 配置
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "mxbai-embed-large:latest")

# DashScope 配置
DASHSCOPE_API_KEY = os.getenv("CLOUD_LLM_API_KEY", "")
DASHSCOPE_EMBED_MODEL = os.getenv("DASHSCOPE_EMBED_MODEL", "text-embedding-v3")
DASHSCOPE_EMBED_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"


class EmbeddingService:
    """封装嵌入服务 (支持 Ollama / DashScope 自动切换)"""

    def __init__(self, model_name: str = None, base_url: str = None):
        self.provider = EMBEDDING_PROVIDER
        self.expected_dim = EMBEDDING_DIMENSION
        self._client = httpx.Client(timeout=60.0)

        if self.provider == "dashscope":
            self.model = model_name or DASHSCOPE_EMBED_MODEL
            self._api_key = DASHSCOPE_API_KEY
        else:
            self.model = model_name or EMBED_MODEL
            self.base_url = base_url or OLLAMA_API_URL

    def embed_query(self, text: str) -> List[float]:
        """文本 -> 向量"""
        if self.provider == "dashscope":
            return self._embed_dashscope(text)
        return self._embed_ollama(text)

    def _embed_ollama(self, text: str) -> List[float]:
        """Ollama /api/embeddings"""
        try:
            resp = self._client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
            )
            resp.raise_for_status()
            vec = resp.json().get("embedding", [])
            if vec and len(vec) != self.expected_dim:
                logger.error(
                    f"维度不匹配: Ollama 返回 {len(vec)} 维, 期望 {self.expected_dim} 维"
                )
                return []
            return vec
        except Exception as e:
            logger.error(f"Ollama Embedding 失败: {e}")
            return []

    def _embed_dashscope(self, text: str) -> List[float]:
        """DashScope OpenAI-compatible /v1/embeddings"""
        try:
            resp = self._client.post(
                DASHSCOPE_EMBED_URL,
                json={
                    "model": self.model,
                    "input": text,
                    "dimensions": self.expected_dim,
                },
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            vec = data["data"][0]["embedding"]
            if len(vec) != self.expected_dim:
                logger.error(
                    f"维度不匹配: DashScope 返回 {len(vec)} 维, 期望 {self.expected_dim} 维"
                )
                return []
            return vec
        except Exception as e:
            logger.error(f"DashScope Embedding 失败: {e}")
            return []

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量嵌入 (逐条调用)"""
        results = []
        for i, text in enumerate(texts):
            vec = self.embed_query(text)
            results.append(vec)
            if (i + 1) % 50 == 0:
                logger.info(f"Embedding 进度: {i + 1}/{len(texts)}")
        return results

    def close(self):
        self._client.close()

"""
同步 Ollama HTTP 客户端
- httpx.Client (sync) — Agent pipeline 全部同步
- 30s health-check 缓存，避免每次 ping
- 所有错误静默返回 success=False，绝不抛异常
"""
from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ── 配置 ──
_AGENT_TIMEOUT = 30.0     # 单 Agent 增强超时
_SYNTHESIS_TIMEOUT = 45.0  # Response 合成超时
_HEALTH_CACHE_TTL = 30.0   # 健康检查缓存秒数


@dataclass
class OllamaResponse:
    success: bool
    content: str = ""
    model: str = ""
    latency_ms: int = 0
    error: str = ""


class SyncOllamaClient:
    """同步 Ollama 客户端，供 Agent pipeline 使用"""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.Client(timeout=_AGENT_TIMEOUT)
        # 健康检查缓存
        self._healthy: Optional[bool] = None
        self._health_checked_at: float = 0.0

    # ── 健康检查 (带缓存) ──

    def is_available(self) -> bool:
        now = time.time()
        if self._healthy is not None and (now - self._health_checked_at) < _HEALTH_CACHE_TTL:
            return self._healthy
        try:
            resp = self._client.get(f"{self.base_url}/api/tags", timeout=5.0)
            self._healthy = resp.status_code == 200
        except Exception:
            self._healthy = False
        self._health_checked_at = now
        return self._healthy

    # ── 聊天接口 ──

    def chat(self, system_prompt: str, user_message: str,
             timeout: float = _AGENT_TIMEOUT) -> OllamaResponse:
        """
        调用 Ollama /api/chat (non-streaming).
        任何异常 → OllamaResponse(success=False)
        """
        t0 = time.time()
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 512,
                },
            }
            resp = self._client.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data.get("message", {}).get("content", "")
            latency = int((time.time() - t0) * 1000)
            return OllamaResponse(
                success=True,
                content=content.strip(),
                model=self.model,
                latency_ms=latency,
            )
        except httpx.TimeoutException:
            latency = int((time.time() - t0) * 1000)
            logger.warning("Ollama chat timeout after %dms", latency)
            return OllamaResponse(success=False, latency_ms=latency,
                                  error="timeout")
        except Exception as e:
            latency = int((time.time() - t0) * 1000)
            logger.warning("Ollama chat error: %s", e)
            return OllamaResponse(success=False, latency_ms=latency,
                                  error=str(e))

    def close(self):
        self._client.close()


# ── 单例 ──

_instance: Optional[SyncOllamaClient] = None


def get_ollama_client() -> SyncOllamaClient:
    global _instance
    if _instance is None:
        try:
            from api.config import OLLAMA_API_URL, OLLAMA_MODEL
        except ImportError:
            import os
            OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
            OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
        _instance = SyncOllamaClient(base_url=OLLAMA_API_URL, model=OLLAMA_MODEL)
    return _instance

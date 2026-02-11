# -*- coding: utf-8 -*-
"""
统一 LLM 客户端 — 云优先, 本地降级

支持 OpenAI-compatible 云 API (DeepSeek / Qwen-Cloud / GPT 等),
自动降级到 Ollama 本地推理.

路由策略:
  - CLOUD_FIRST (默认): 先云, 失败降级本地
  - LOCAL_FIRST: 先本地, 失败尝试云
  - CLOUD_ONLY: 仅云
  - LOCAL_ONLY: 仅本地 (等价于旧行为)
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Optional

import httpx

logger = logging.getLogger(__name__)

# ── 配置读取 ──────────────────────────────────────────────

def _cfg(key: str, default: str = "") -> str:
    """先尝试 api.config, 失败从 os.environ"""
    try:
        import api.config as cfg
        return getattr(cfg, key, None) or default
    except ImportError:
        import os
        return os.getenv(key, default)


class RouteStrategy(str, Enum):
    CLOUD_FIRST = "cloud_first"
    LOCAL_FIRST = "local_first"
    CLOUD_ONLY = "cloud_only"
    LOCAL_ONLY = "local_only"


@dataclass
class LLMResponse:
    success: bool
    content: str = ""
    model: str = ""
    provider: str = ""       # "cloud" | "ollama"
    latency_ms: int = 0
    error: str = ""
    tokens_used: int = 0


# ── 云端 LLM 客户端 ──────────────────────────────────────

class CloudLLMClient:
    """OpenAI-compatible 云 LLM 客户端 (httpx sync)"""

    def __init__(self,
                 api_key: str,
                 base_url: str,
                 model: str,
                 max_tokens: int = 2048,
                 timeout: float = 60.0):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens
        self._client = httpx.Client(timeout=timeout)
        self._healthy: Optional[bool] = None
        self._health_checked_at: float = 0.0

    def is_available(self) -> bool:
        if not self.api_key:
            return False
        now = time.time()
        if self._healthy is not None and (now - self._health_checked_at) < 60.0:
            return self._healthy
        try:
            resp = self._client.get(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10.0,
            )
            self._healthy = resp.status_code in (200, 401, 403)
        except Exception:
            self._healthy = False
        self._health_checked_at = now
        return self._healthy

    def chat(self, system_prompt: str, user_message: str,
             temperature: float = 0.7, timeout: float = 60.0) -> LLMResponse:
        t0 = time.time()
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "temperature": temperature,
                "max_tokens": self.max_tokens,
                "stream": False,
            }
            resp = self._client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            latency = int((time.time() - t0) * 1000)
            return LLMResponse(
                success=True,
                content=content.strip(),
                model=self.model,
                provider="cloud",
                latency_ms=latency,
                tokens_used=usage.get("total_tokens", 0),
            )
        except httpx.TimeoutException:
            latency = int((time.time() - t0) * 1000)
            logger.warning("Cloud LLM timeout after %dms", latency)
            return LLMResponse(success=False, provider="cloud",
                               latency_ms=latency, error="timeout")
        except Exception as e:
            latency = int((time.time() - t0) * 1000)
            logger.warning("Cloud LLM error: %s", e)
            return LLMResponse(success=False, provider="cloud",
                               latency_ms=latency, error=str(e))

    def chat_stream(self, system_prompt: str, user_message: str,
                    temperature: float = 0.7,
                    timeout: float = 60.0) -> Iterator[str]:
        """流式输出 (yield delta text)"""
        try:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "temperature": temperature,
                "max_tokens": self.max_tokens,
                "stream": True,
            }
            with self._client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=timeout,
            ) as resp:
                resp.raise_for_status()
                import json
                for line in resp.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    chunk = line[6:]
                    if chunk.strip() == "[DONE]":
                        break
                    try:
                        obj = json.loads(chunk)
                        delta = obj["choices"][0].get("delta", {})
                        text = delta.get("content", "")
                        if text:
                            yield text
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
        except Exception as e:
            logger.warning("Cloud LLM stream error: %s", e)

    def close(self):
        self._client.close()


# ── 统一客户端 ──────────────────────────────────────────

class UnifiedLLMClient:
    """
    统一 LLM 客户端 — 云优先, 本地降级

    使用方法:
        client = get_llm_client()
        resp = client.chat("你是助手", "你好")
    """

    def __init__(self):
        # 云 LLM 配置
        self._cloud_provider = _cfg("CLOUD_LLM_PROVIDER", "")
        api_key = _cfg("CLOUD_LLM_API_KEY", "")
        base_url = _cfg("CLOUD_LLM_BASE_URL", "https://api.deepseek.com/v1")
        model = _cfg("CLOUD_LLM_MODEL", "deepseek-chat")
        max_tokens = int(_cfg("LLM_MAX_TOKENS", "2048"))

        self._cloud: Optional[CloudLLMClient] = None
        if api_key:
            self._cloud = CloudLLMClient(
                api_key=api_key,
                base_url=base_url,
                model=model,
                max_tokens=max_tokens,
            )

        # 路由策略
        strategy_str = _cfg("LLM_ROUTE_STRATEGY", "cloud_first")
        try:
            self.strategy = RouteStrategy(strategy_str)
        except ValueError:
            self.strategy = RouteStrategy.CLOUD_FIRST

        logger.info(
            "UnifiedLLMClient initialized: provider=%s model=%s strategy=%s",
            self._cloud_provider or "(none)", model, self.strategy.value,
        )

    # ── 公共接口 ──

    def chat(self, system: str, user: str,
             temperature: float = 0.7,
             timeout: float = 60.0) -> LLMResponse:
        """同步聊天 — 按策略路由"""
        if self.strategy == RouteStrategy.CLOUD_ONLY:
            return self._cloud_chat(system, user, temperature, timeout)
        elif self.strategy == RouteStrategy.LOCAL_ONLY:
            return self._local_chat(system, user, timeout)
        elif self.strategy == RouteStrategy.LOCAL_FIRST:
            resp = self._local_chat(system, user, timeout)
            if resp.success:
                return resp
            return self._cloud_chat(system, user, temperature, timeout)
        else:  # CLOUD_FIRST (default)
            resp = self._cloud_chat(system, user, temperature, timeout)
            if resp.success:
                return resp
            logger.info("Cloud LLM failed, falling back to Ollama")
            return self._local_chat(system, user, timeout)

    def chat_stream(self, system: str, user: str,
                    temperature: float = 0.7,
                    timeout: float = 60.0) -> Iterator[str]:
        """流式输出 (仅云端支持, Ollama 不支持流式)"""
        if self._cloud and self._cloud.is_available():
            yield from self._cloud.chat_stream(system, user, temperature, timeout)
        else:
            resp = self._local_chat(system, user, timeout)
            if resp.success:
                yield resp.content

    def is_available(self) -> bool:
        """至少一个后端可用"""
        cloud_ok = self._cloud is not None and self._cloud.is_available()
        local_ok = self._local_available()
        return cloud_ok or local_ok

    def get_status(self) -> dict:
        """返回当前状态 (供 /health 使用)"""
        cloud_ok = self._cloud is not None and self._cloud.is_available()
        local_ok = self._local_available()
        return {
            "strategy": self.strategy.value,
            "cloud_provider": self._cloud_provider or None,
            "cloud_model": self._cloud.model if self._cloud else None,
            "cloud_available": cloud_ok,
            "local_available": local_ok,
        }

    # ── 内部方法 ──

    def _cloud_chat(self, system: str, user: str,
                    temperature: float, timeout: float) -> LLMResponse:
        if self._cloud is None or not self._cloud.is_available():
            return LLMResponse(success=False, provider="cloud",
                               error="cloud_not_configured")
        return self._cloud.chat(system, user, temperature, timeout)

    def _local_chat(self, system: str, user: str,
                    timeout: float) -> LLMResponse:
        """调用已有 Ollama 客户端"""
        try:
            from core.agents.ollama_client import get_ollama_client
            client = get_ollama_client()
            if not client.is_available():
                return LLMResponse(success=False, provider="ollama",
                                   error="ollama_unavailable")
            resp = client.chat(system, user, timeout=timeout)
            return LLMResponse(
                success=resp.success,
                content=resp.content,
                model=resp.model,
                provider="ollama",
                latency_ms=resp.latency_ms,
                error=resp.error,
            )
        except Exception as e:
            logger.warning("Ollama fallback error: %s", e)
            return LLMResponse(success=False, provider="ollama",
                               error=str(e))

    def _local_available(self) -> bool:
        try:
            from core.agents.ollama_client import get_ollama_client
            return get_ollama_client().is_available()
        except Exception:
            return False


# ── 单例 ──────────────────────────────────────────────────

_instance: Optional[UnifiedLLMClient] = None


def get_llm_client() -> UnifiedLLMClient:
    """获取全局统一 LLM 客户端单例"""
    global _instance
    if _instance is None:
        _instance = UnifiedLLMClient()
    return _instance

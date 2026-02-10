"""
LLM 客户端抽象层 — 通义千问(主) + DeepSeek(备)
放置: api/core/llm/client.py

所有 LLM 调用统一通过此模块，不直接 import openai/dashscope。
支持 OpenAI 兼容协议，通义和 DeepSeek 都走同一接口。
"""
import os
import time
import logging
from dataclasses import dataclass, field
from enum import Enum as PyEnum
from typing import Any, AsyncIterator

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════
# 配置
# ══════════════════════════════════════════════

class LLMProvider(str, PyEnum):
    DASHSCOPE = "dashscope"    # 通义千问 (阿里云百炼)
    DEEPSEEK = "deepseek"      # DeepSeek (备用)


@dataclass
class ModelConfig:
    """单模型配置"""
    provider: LLMProvider
    model_name: str
    base_url: str
    api_key_env: str             # 环境变量名
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout: int = 30            # 秒
    cost_per_1m_input: float = 0  # 元/百万Token (用于成本追踪)
    cost_per_1m_output: float = 0


# 模型注册表 — 按场景预配置
MODEL_REGISTRY: dict[str, ModelConfig] = {
    # ── 通义千问 (百炼平台, OpenAI 兼容) ──
    "qwen3-max": ModelConfig(
        provider=LLMProvider.DASHSCOPE,
        model_name="qwen3-max",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
        max_tokens=4096,
        temperature=0.7,
        timeout=30,
        cost_per_1m_input=2.5,
        cost_per_1m_output=10.0,
    ),
    "qwen-plus": ModelConfig(
        provider=LLMProvider.DASHSCOPE,
        model_name="qwen-plus",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
        max_tokens=2048,
        temperature=0.7,
        timeout=15,
        cost_per_1m_input=0.8,
        cost_per_1m_output=2.0,
    ),
    "qwen-turbo": ModelConfig(
        provider=LLMProvider.DASHSCOPE,
        model_name="qwen-turbo",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
        max_tokens=1024,
        temperature=0.3,
        timeout=10,
        cost_per_1m_input=0.3,
        cost_per_1m_output=0.6,
    ),
    # ── 通义 Embedding ──
    "text-embedding-v3": ModelConfig(
        provider=LLMProvider.DASHSCOPE,
        model_name="text-embedding-v3",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
        cost_per_1m_input=0.7,
    ),
    # ── DeepSeek (备用) ──
    "deepseek-v3": ModelConfig(
        provider=LLMProvider.DEEPSEEK,
        model_name="deepseek-chat",
        base_url="https://api.deepseek.com/v1",
        api_key_env="DEEPSEEK_API_KEY",
        max_tokens=4096,
        temperature=0.7,
        timeout=30,
        cost_per_1m_input=2.0,
        cost_per_1m_output=8.0,
    ),
    # ── DeepSeek via 百炼 (同一平台调用) ──
    "deepseek-v3-bailian": ModelConfig(
        provider=LLMProvider.DASHSCOPE,
        model_name="deepseek-v3",
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key_env="DASHSCOPE_API_KEY",
        max_tokens=4096,
        temperature=0.7,
        timeout=30,
        cost_per_1m_input=2.0,
        cost_per_1m_output=8.0,
    ),
}


# ══════════════════════════════════════════════
# 响应数据结构
# ══════════════════════════════════════════════

@dataclass
class LLMResponse:
    """统一响应格式"""
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    cost_yuan: float = 0.0
    finish_reason: str = ""
    raw: dict = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


# ══════════════════════════════════════════════
# 同步客户端 (使用 httpx, 不依赖 openai SDK)
# ══════════════════════════════════════════════

class LLMClient:
    """
    统一 LLM 调用客户端

    用法:
        client = LLMClient()
        resp = client.chat("qwen-plus", messages=[{"role":"user","content":"你好"}])
        print(resp.content)
    """

    def __init__(self):
        self._api_keys: dict[str, str] = {}

    def _get_api_key(self, env_var: str) -> str:
        if env_var not in self._api_keys:
            key = os.environ.get(env_var, "")
            if not key:
                raise LLMAPIError(
                    model="N/A", status_code=0,
                    detail=f"API key environment variable '{env_var}' is not set",
                )
            self._api_keys[env_var] = key
        return self._api_keys[env_var]

    def chat(
        self,
        model_key: str,
        messages: list[dict],
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        extra_params: dict | None = None,
    ) -> LLMResponse:
        """
        同步聊天补全
        model_key: MODEL_REGISTRY 中的键名
        """
        import httpx

        config = MODEL_REGISTRY.get(model_key)
        if not config:
            raise ValueError(f"Unknown model: {model_key}. Available: {list(MODEL_REGISTRY.keys())}")

        api_key = self._get_api_key(config.api_key_env)

        # 构建消息列表
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        payload = {
            "model": config.model_name,
            "messages": full_messages,
            "max_tokens": max_tokens or config.max_tokens,
            "temperature": temperature if temperature is not None else config.temperature,
        }
        if extra_params:
            payload.update(extra_params)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        t0 = time.time()
        try:
            with httpx.Client(timeout=config.timeout) as http:
                resp = http.post(
                    f"{config.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.TimeoutException:
            logger.error(f"LLM timeout: {model_key} ({config.timeout}s)")
            raise LLMTimeoutError(model_key, config.timeout)
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM HTTP error: {model_key} {e.response.status_code}")
            raise LLMAPIError(model_key, e.response.status_code, str(e))
        except Exception as e:
            logger.error(f"LLM error: {model_key} {e}")
            raise LLMAPIError(model_key, 0, str(e))

        latency = int((time.time() - t0) * 1000)

        # 解析 OpenAI 兼容响应
        choice = data.get("choices", [{}])[0]
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        cost = (
            input_tokens / 1_000_000 * config.cost_per_1m_input
            + output_tokens / 1_000_000 * config.cost_per_1m_output
        )

        return LLMResponse(
            content=choice.get("message", {}).get("content", ""),
            model=config.model_name,
            provider=config.provider.value,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency,
            cost_yuan=round(cost, 6),
            finish_reason=choice.get("finish_reason", ""),
            raw=data,
        )

    def embed(
        self,
        texts: list[str],
        model_key: str = "text-embedding-v3",
    ) -> list[list[float]]:
        """批量文本向量化"""
        import httpx

        config = MODEL_REGISTRY.get(model_key)
        if not config:
            raise ValueError(f"Unknown embedding model: {model_key}")

        api_key = self._get_api_key(config.api_key_env)

        payload = {
            "model": config.model_name,
            "input": texts,
            "encoding_format": "float",
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=30) as http:
            resp = http.post(
                f"{config.base_url}/embeddings",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        embeddings = [item["embedding"] for item in data.get("data", [])]
        return embeddings


# ══════════════════════════════════════════════
# 异常类
# ══════════════════════════════════════════════

class LLMTimeoutError(Exception):
    def __init__(self, model: str, timeout: int):
        self.model = model
        self.timeout = timeout
        super().__init__(f"LLM timeout: {model} after {timeout}s")


class LLMAPIError(Exception):
    def __init__(self, model: str, status_code: int, detail: str):
        self.model = model
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"LLM API error: {model} [{status_code}] {detail}")

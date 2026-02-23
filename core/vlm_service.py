"""
VLM (Vision Language Model) 服务 — V5.2.0

策略: ollama_first (Ollama qwen2.5vl → Cloud VLM API fallback)
支持: ollama / cloud / ollama_first / disabled

用法:
    svc = VLMService()
    result = await svc.analyze_image(image_b64, prompt)
"""

import os
import httpx
from loguru import logger
from api.config import (
    OLLAMA_API_URL, OLLAMA_TIMEOUT,
    VLM_PROVIDER, VLM_OLLAMA_MODEL, VLM_CLOUD_API_KEY,
    VLM_CLOUD_BASE_URL, VLM_CLOUD_MODEL, VLM_TIMEOUT,
)


class VLMService:
    """视觉语言模型服务 — ollama_first + cloud fallback"""

    def __init__(self):
        self.provider = VLM_PROVIDER

    async def analyze_image(
        self,
        image_b64: str,
        prompt: str,
        temperature: float = 0.3,
    ) -> dict:
        """
        分析图片并返回文字结果

        Args:
            image_b64: Base64 编码的图片数据
            prompt: 分析指令
            temperature: 模型温度

        Returns: {"text": str, "provider": str}
        Raises: RuntimeError if all providers fail
        """
        if self.provider == "disabled":
            raise RuntimeError("VLM 服务已禁用")

        if self.provider == "ollama":
            return await self._analyze_ollama(image_b64, prompt, temperature)

        if self.provider == "cloud":
            return await self._analyze_cloud(image_b64, prompt, temperature)

        # ollama_first: try Ollama → fallback to Cloud
        try:
            return await self._analyze_ollama(image_b64, prompt, temperature)
        except Exception as e:
            logger.warning(f"Ollama VLM failed, falling back to cloud: {e}")

        # Cloud fallback
        if VLM_CLOUD_API_KEY:
            try:
                return await self._analyze_cloud(image_b64, prompt, temperature)
            except Exception as e:
                logger.error(f"Cloud VLM also failed: {e}")

        raise RuntimeError(
            "视觉识别失败: 所有提供者均不可用。"
            "请确保 Ollama 服务运行中或配置 VLM_CLOUD_API_KEY。"
        )

    async def _analyze_ollama(
        self, image_b64: str, prompt: str, temperature: float,
    ) -> dict:
        """Ollama VLM (qwen2.5vl) 分析"""
        url = f"{OLLAMA_API_URL}/api/chat"
        payload = {
            "model": VLM_OLLAMA_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_b64],
                }
            ],
            "stream": False,
            "options": {"temperature": temperature},
        }

        async with httpx.AsyncClient(timeout=VLM_TIMEOUT) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data.get("message", {}).get("content", "")

        logger.info(f"Ollama VLM: {len(image_b64)} b64chars → {len(text)} chars")
        return {"text": text, "provider": "ollama"}

    async def _analyze_cloud(
        self, image_b64: str, prompt: str, temperature: float,
    ) -> dict:
        """
        Cloud VLM API (OpenAI-compatible vision endpoint)
        Supports: GPT-4o, Qwen-VL-Plus, DeepSeek-VL, etc.
        """
        if not VLM_CLOUD_API_KEY:
            raise RuntimeError("VLM_CLOUD_API_KEY 未配置")

        url = f"{VLM_CLOUD_BASE_URL}/chat/completions"
        headers = {"Authorization": f"Bearer {VLM_CLOUD_API_KEY}"}

        payload = {
            "model": VLM_CLOUD_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}",
                            },
                        },
                    ],
                }
            ],
            "temperature": temperature,
            "max_tokens": 1024,
        }

        async with httpx.AsyncClient(timeout=VLM_TIMEOUT) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            text = (
                data.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
            )

        logger.info(f"Cloud VLM: {len(image_b64)} b64chars → {len(text)} chars")
        return {"text": text, "provider": "cloud"}

    def is_available(self) -> dict:
        """检查 VLM 服务可用性"""
        return {
            "provider": self.provider,
            "ollama_model": VLM_OLLAMA_MODEL,
            "ollama_url": OLLAMA_API_URL,
            "cloud_configured": bool(VLM_CLOUD_API_KEY),
            "status": "disabled" if self.provider == "disabled" else "ready",
        }

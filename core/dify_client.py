import json
import hashlib
import time
import httpx
from loguru import logger
from typing import AsyncGenerator, Dict, Any, Optional


class DifyClient:
    """
    Dify 客户端（优化版）

    优化点：
    1. 复用 httpx.AsyncClient，避免每次请求重建 TCP 连接
    2. 本地缓存：相同 trigger + 相近血糖区间的建议直接返回缓存
    3. 自动适配：先尝试 blocking（CHATFLOW 快），失败则降级 streaming（Agent）
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.dify.ai/v1",
        cache_ttl: int = 300,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        # 复用连接
        self._client: Optional[httpx.AsyncClient] = None

        # 本地缓存: key -> (timestamp, result)
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = cache_ttl

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(600.0, connect=10.0, read=300.0)
            )
        return self._client

    # ------------------------------------------------------------------
    # 缓存
    # ------------------------------------------------------------------

    def _cache_key(self, trigger_tags: str, glucose_value: float) -> str:
        """按 trigger 标签 + 血糖区间（取整）生成缓存 key"""
        bucket = round(glucose_value)  # 12.1 和 12.8 落入同一桶
        raw = f"{trigger_tags}|{bucket}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def _get_cached(self, key: str) -> Optional[Dict]:
        if key in self._cache:
            ts, result = self._cache[key]
            if time.time() - ts < self._cache_ttl:
                logger.info(f"命中缓存 (key={key[:8]}...)")
                return result
            del self._cache[key]
        return None

    def _set_cache(self, key: str, result: Dict):
        self._cache[key] = (time.time(), result)

    # ------------------------------------------------------------------
    # 主方法
    # ------------------------------------------------------------------

    async def generate_intervention(
        self,
        user_input: str,
        user_id: str,
        context_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """调用 Dify 获取干预建议，带缓存 + blocking/streaming 自动适配"""

        # 1. 查缓存
        tags_str = ",".join(sorted(context_data.get("trigger_tags", [])))
        glucose_val = float(context_data.get("glucose_value", 0))
        ck = self._cache_key(tags_str, glucose_val)
        cached = self._get_cached(ck)
        if cached:
            return cached

        # 2. 构造 payload
        str_inputs = {k: str(v) for k, v in context_data.items()}
        base_payload = {
            "inputs": str_inputs,
            "query": user_input,
            "conversation_id": "",
            "user": user_id,
        }

        # 3. 直接走 streaming（兼容 Agent 和 CHATFLOW，避免 blocking 超时浪费）
        result = await self._try_streaming(base_payload)

        # 5. 写缓存
        if result and result.get("answer"):
            self._set_cache(ck, result)

        return result

    # ------------------------------------------------------------------
    # Blocking 模式（CHATFLOW）
    # ------------------------------------------------------------------

    async def _try_blocking(self, base_payload: Dict) -> Optional[Dict]:
        payload = {**base_payload, "response_mode": "blocking"}
        client = await self._get_client()
        try:
            response = await client.post(
                f"{self.base_url}/chat-messages",
                json=payload,
                headers=self.headers,
            )
            if response.status_code == 400:
                body = response.json()
                if "not support blocking" in body.get("message", ""):
                    logger.info("Blocking 不支持，降级 streaming")
                    return None
            response.raise_for_status()
            data = response.json()
            return {
                "answer": data.get("answer", ""),
                "conversation_id": data.get("conversation_id"),
            }
        except httpx.HTTPStatusError:
            return None
        except Exception as e:
            logger.warning(f"Blocking 请求异常: {e}")
            return None

    # ------------------------------------------------------------------
    # Streaming 模式（Agent）
    # ------------------------------------------------------------------

    async def _try_streaming(self, base_payload: Dict) -> Dict[str, Any]:
        payload = {**base_payload, "response_mode": "streaming"}
        parts = []
        conversation_id = None
        client = await self._get_client()

        try:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat-messages",
                json=payload,
                headers=self.headers,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[len("data:"):].strip()
                    if not raw:
                        continue
                    try:
                        event_data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    event = event_data.get("event", "")
                    if event in ("agent_message", "message"):
                        answer = event_data.get("answer", "")
                        if answer:
                            parts.append(answer)
                    elif event in ("message_end", "agent_message_end"):
                        conversation_id = event_data.get("conversation_id")
                        break

        except Exception as e:
            logger.error(f"Dify API 调用失败: {e}")
            return {"answer": "系统繁忙，请稍后再试。"}

        return {
            "answer": "".join(parts) or "未获取到回复内容。",
            "conversation_id": conversation_id,
        }

    # ------------------------------------------------------------------
    # 流式生成器（供 SSE 端点使用）
    # ------------------------------------------------------------------

    async def stream_chat(
        self,
        user_input: str,
        user_id: str,
        context_data: Dict[str, Any],
    ) -> AsyncGenerator[str, None]:
        """逐 token 产出文本片段，供 FastAPI StreamingResponse 使用"""
        str_inputs = {k: str(v) for k, v in context_data.items()}
        payload = {
            "inputs": str_inputs,
            "query": user_input,
            "conversation_id": "",
            "user": user_id,
            "response_mode": "streaming",
        }
        client = await self._get_client()
        try:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat-messages",
                json=payload,
                headers=self.headers,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    raw = line[len("data:"):].strip()
                    if not raw:
                        continue
                    try:
                        event_data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue
                    event = event_data.get("event", "")
                    if event in ("agent_message", "message"):
                        chunk = event_data.get("answer", "")
                        if chunk:
                            yield chunk
                    elif event in ("message_end", "agent_message_end"):
                        break
        except Exception as e:
            logger.error(f"Dify 流式调用失败: {e}")
            yield "系统繁忙，请稍后再试。"

    # ------------------------------------------------------------------
    # 清理
    # ------------------------------------------------------------------

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

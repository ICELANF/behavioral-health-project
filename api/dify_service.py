# -*- coding: utf-8 -*-
"""
Dify 对话服务 - 对接 Dify 工作流编排平台

模式参照 llm_service.py 的 OllamaService
"""

import httpx
import json
import time
from typing import Optional, Dict, AsyncGenerator
from loguru import logger

from api.config import DIFY_API_URL, DIFY_API_KEY, DIFY_TIMEOUT, HEALTH_CACHE_TTL


class DifyChatService:
    """Dify 对话服务"""

    def __init__(
        self,
        api_url: str = DIFY_API_URL,
        api_key: str = DIFY_API_KEY,
        timeout: float = DIFY_TIMEOUT,
    ):
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        # 使用分离式超时: connect=10s, 读取超时=30s (每次读取，Dify ping 间隔约5s)
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=10.0, read=30.0)
        )

        # session_id -> dify conversation_id 映射
        self._conversation_map: Dict[str, str] = {}

        # 健康状态缓存
        self._health_cache: Optional[Dict] = None
        self._health_cache_ts: float = 0

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------
    # 健康检查
    # ------------------------------------------------------------------

    async def check_health(self) -> Dict:
        """
        检查 Dify 服务可用性 (GET /parameters)

        返回: {"status": "healthy"|"unhealthy", ...}
        结果缓存 HEALTH_CACHE_TTL 秒
        """
        now = time.time()
        if self._health_cache and (now - self._health_cache_ts) < HEALTH_CACHE_TTL:
            return self._health_cache

        try:
            response = await self.client.get(
                f"{self.api_url}/parameters",
                headers=self._headers,
            )
            if response.status_code == 200:
                data = response.json()
                result = {
                    "status": "healthy",
                    "app": data.get("user_input_form", []),
                    "opening_statement": data.get("opening_statement", ""),
                }
            else:
                result = {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                }
        except Exception as e:
            logger.error(f"Dify health check failed: {e}")
            result = {"status": "unhealthy", "error": str(e)}

        self._health_cache = result
        self._health_cache_ts = now
        return result

    def is_healthy_cached(self) -> bool:
        """快速判断缓存的健康状态"""
        if self._health_cache and (time.time() - self._health_cache_ts) < HEALTH_CACHE_TTL:
            return self._health_cache.get("status") == "healthy"
        return False

    # ------------------------------------------------------------------
    # conversation_id 映射
    # ------------------------------------------------------------------

    def get_conversation_id(self, session_id: str) -> Optional[str]:
        return self._conversation_map.get(session_id)

    def set_conversation_id(self, session_id: str, conversation_id: str):
        self._conversation_map[session_id] = conversation_id

    # ------------------------------------------------------------------
    # 阻塞式对话
    # ------------------------------------------------------------------

    async def chat(
        self,
        query: str,
        user: str,
        inputs: Optional[Dict] = None,
        session_id: Optional[str] = None,
    ) -> Dict:
        """
        POST /chat-messages — 收集完整响应

        Dify Agent Chat App 不支持 blocking 模式，因此使用 streaming
        内部收集所有 delta 后拼接为完整 answer 返回。

        返回: {"answer": str, "conversation_id": str}
        """
        parts = []
        conversation_id = None

        async for chunk in self.chat_stream(
            query=query,
            user=user,
            inputs=inputs,
            session_id=session_id,
        ):
            if chunk:  # 跳过 keepalive 空字符串
                parts.append(chunk)

        # chat_stream 内部已保存 conversation_id
        if session_id:
            conversation_id = self.get_conversation_id(session_id)

        return {
            "answer": "".join(parts),
            "conversation_id": conversation_id,
        }

    # ------------------------------------------------------------------
    # 流式对话
    # ------------------------------------------------------------------

    async def chat_stream(
        self,
        query: str,
        user: str,
        inputs: Optional[Dict] = None,
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        POST /chat-messages (streaming SSE)

        Yields: answer delta 文本片段
        """
        payload = {
            "inputs": inputs or {},
            "query": query,
            "response_mode": "streaming",
            "user": user,
        }

        if session_id:
            conv_id = self.get_conversation_id(session_id)
            if conv_id:
                payload["conversation_id"] = conv_id

        try:
            async with self.client.stream(
                "POST",
                f"{self.api_url}/chat-messages",
                json=payload,
                headers=self._headers,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue

                    # Dify Agent 思考期间发送 event: ping 保持连接
                    if line.strip() == "event: ping":
                        yield ""  # 空字符串作为 keepalive 信号
                        continue

                    if not line.startswith("data: "):
                        continue

                    raw = line[6:]  # strip "data: "
                    if not raw:
                        continue

                    try:
                        event_data = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    event = event_data.get("event")

                    if event in ("message", "agent_message"):
                        answer = event_data.get("answer", "")
                        if answer:
                            yield answer

                    elif event in ("message_end", "agent_message_end"):
                        # 保存 conversation_id
                        new_conv_id = event_data.get("conversation_id")
                        if session_id and new_conv_id:
                            self.set_conversation_id(session_id, new_conv_id)
                        return

        except Exception as e:
            logger.error(f"Dify stream chat failed: {e}")
            yield f"[错误] Dify 流式响应失败: {str(e)}"

    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()


# 全局实例
dify_service = DifyChatService()

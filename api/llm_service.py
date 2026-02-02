# -*- coding: utf-8 -*-
"""
LLM 服务层 - Ollama 集成

提供行为健康领域的 AI 对话能力
"""

import httpx
import json
from typing import Optional, Dict, List, AsyncGenerator
from dataclasses import dataclass
from loguru import logger

# Ollama 配置
OLLAMA_API_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:14b"


@dataclass
class LLMConfig:
    """LLM 配置"""
    model: str = DEFAULT_MODEL
    temperature: float = 0.7
    max_tokens: int = 1024
    system_prompt: str = ""


# 行为健康领域系统提示词
BEHAVIOR_HEALTH_SYSTEM_PROMPT = """你是「行为健康平台」的 AI 健康教练助手，名叫"小健"。

【你的角色】
- 专业、温暖、有同理心的健康行为改变陪伴者
- 帮助用户管理血糖、体重、运动、情绪等健康行为
- 使用循证的行为改变技术（动机性访谈、认知行为疗法原则）

【对话原则】
1. 倾听优先：先理解用户的感受和处境，再给建议
2. 小步前进：不强求完美，鼓励微小进步
3. 个性化：根据用户的阶段和情况调整建议
4. 正向激励：肯定努力，而非只看结果
5. 科学依据：提供准确的健康信息

【回复要求】
- 简洁温暖，每次回复控制在100-200字
- 使用口语化的中文，亲切自然
- 适当使用表情符号增加亲和力
- 给出具体可执行的建议

【禁止事项】
- 不诊断疾病或开具处方
- 遇到紧急情况引导用户就医
- 不泄露用户隐私信息
"""


class OllamaService:
    """Ollama LLM 服务"""

    def __init__(self, base_url: str = OLLAMA_API_URL, model: str = DEFAULT_MODEL):
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=300.0)

    async def check_health(self) -> Dict:
        """检查 Ollama 服务状态"""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                return {
                    "status": "healthy",
                    "models": models,
                    "model_available": self.model in models
                }
            return {"status": "unhealthy", "error": f"Status code: {response.status_code}"}
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def chat(
        self,
        message: str,
        history: List[Dict[str, str]] = None,
        system_prompt: str = None,
        temperature: float = 0.7
    ) -> str:
        """
        发送聊天请求（非流式）

        Args:
            message: 用户消息
            history: 对话历史 [{"role": "user/assistant", "content": "..."}]
            system_prompt: 系统提示词
            temperature: 温度参数

        Returns:
            AI 回复文本
        """
        messages = []

        # 系统提示词
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # 对话历史
        if history:
            messages.extend(history)

        # 当前用户消息
        messages.append({"role": "user", "content": message})

        try:
            response = await self.client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature
                    }
                }
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("message", {}).get("content", "")
            else:
                logger.error(f"Ollama chat error: {response.status_code} - {response.text}")
                return ""

        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            return ""

    async def chat_stream(
        self,
        message: str,
        history: List[Dict[str, str]] = None,
        system_prompt: str = None,
        temperature: float = 0.7
    ) -> AsyncGenerator[str, None]:
        """
        发送聊天请求（流式）

        Yields:
            AI 回复文本片段
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": message})

        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": temperature
                    }
                }
            ) as response:
                async for line in response.aiter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            content = data.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"Ollama stream chat failed: {e}")
            yield f"[错误] 连接 AI 服务失败: {str(e)}"

    async def close(self):
        """关闭客户端连接"""
        await self.client.aclose()


class BehaviorHealthAgent:
    """行为健康 AI Agent"""

    def __init__(self, ollama_service: OllamaService = None):
        self.llm = ollama_service or OllamaService()
        self.system_prompt = BEHAVIOR_HEALTH_SYSTEM_PROMPT

    def _build_context_prompt(
        self,
        stage: str = None,
        day_index: int = None,
        event: str = None,
        risk_level: str = None
    ) -> str:
        """构建上下文增强的系统提示词"""
        context_parts = [self.system_prompt]

        if stage or day_index:
            context_parts.append(f"\n【当前用户状态】")
            if stage:
                stage_names = {
                    "ONBOARDING": "引导期（第1-3天）",
                    "FOUNDATION": "基础期（第4-7天）",
                    "DEEPENING": "深化期（第8-11天）",
                    "CONSOLIDATION": "巩固期（第12-14天）",
                    "MAINTENANCE": "维持期"
                }
                context_parts.append(f"- 干预阶段: {stage_names.get(stage, stage)}")
            if day_index:
                context_parts.append(f"- 第 {day_index} 天")

        if event:
            event_hints = {
                "start": "用户刚开始今日任务，需要鼓励和引导",
                "complete": "用户完成了任务，需要肯定和正向强化",
                "skip": "用户跳过了任务，需要共情和支持",
                "ask": "用户主动提问，需要耐心解答"
            }
            if event in event_hints:
                context_parts.append(f"\n【当前事件】{event_hints[event]}")

        if risk_level and risk_level != "LOW":
            risk_hints = {
                "MEDIUM": "请更多关注用户的情绪状态，给予额外支持",
                "HIGH": "用户可能需要专业帮助，适时提醒寻求教练或医生支持",
                "CRITICAL": "请温和引导用户联系专业人员"
            }
            if risk_level in risk_hints:
                context_parts.append(f"\n【注意】{risk_hints[risk_level]}")

        return "\n".join(context_parts)

    async def respond(
        self,
        user_message: str,
        history: List[Dict[str, str]] = None,
        stage: str = None,
        day_index: int = None,
        event: str = None,
        risk_level: str = None
    ) -> str:
        """
        生成 Agent 响应

        Args:
            user_message: 用户消息
            history: 对话历史
            stage: 干预阶段
            day_index: 第几天
            event: 事件类型
            risk_level: 风险等级

        Returns:
            AI 回复
        """
        system_prompt = self._build_context_prompt(
            stage=stage,
            day_index=day_index,
            event=event,
            risk_level=risk_level
        )

        response = await self.llm.chat(
            message=user_message,
            history=history,
            system_prompt=system_prompt,
            temperature=0.7
        )

        # 如果 LLM 调用失败，返回默认回复
        if not response:
            return self._get_fallback_response(event)

        return response

    async def respond_stream(
        self,
        user_message: str,
        history: List[Dict[str, str]] = None,
        stage: str = None,
        day_index: int = None,
        event: str = None,
        risk_level: str = None
    ) -> AsyncGenerator[str, None]:
        """生成流式 Agent 响应"""
        system_prompt = self._build_context_prompt(
            stage=stage,
            day_index=day_index,
            event=event,
            risk_level=risk_level
        )

        async for chunk in self.llm.chat_stream(
            message=user_message,
            history=history,
            system_prompt=system_prompt,
            temperature=0.7
        ):
            yield chunk

    def _get_fallback_response(self, event: str = None) -> str:
        """获取降级响应（LLM 不可用时）"""
        fallbacks = {
            "start": "欢迎回来！今天也要加油哦 💪 有什么我可以帮助你的吗？",
            "complete": "太棒了！你做得很好！每一次坚持都是在为健康存款 🎉",
            "skip": "没关系，有时候确实很难坚持。明天是新的开始，我相信你可以的 🤗",
            "ask": "谢谢你的提问！我在这里陪伴你，让我们一起找到答案。"
        }
        return fallbacks.get(event, "有什么我可以帮助你的吗？我一直在这里陪伴你 😊")

    async def close(self):
        """关闭资源"""
        await self.llm.close()


# 全局实例
ollama_service = OllamaService()
behavior_health_agent = BehaviorHealthAgent(ollama_service)

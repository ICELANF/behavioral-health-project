"""
core.llm — LLM 调用抽象层

公开 API:
    LLMClient          同步 LLM 客户端
    LLMRouter          三级路由 + 故障降级
    CoachAgent         对话代理 (集成 RAG + 画像)
    create_coach_agent 便捷工厂
"""
from core.llm.client import LLMClient, LLMResponse, MODEL_REGISTRY
from core.llm.router import LLMRouter, TaskComplexity
from core.llm.coach_agent import CoachAgent, UserContext, create_coach_agent

__all__ = [
    "LLMClient", "LLMResponse", "MODEL_REGISTRY",
    "LLMRouter", "TaskComplexity",
    "CoachAgent", "UserContext", "create_coach_agent",
]

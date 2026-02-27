"""
Assistant Agent 基类

安全约束: 用户层Agent不提供个体化建议，仅科普/支持/转介。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAssistantAgent(ABC):
    """所有assistant层Agent的基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    @abstractmethod
    def domain(self) -> str:
        ...

    @abstractmethod
    async def run(self, message: str, **kwargs) -> Dict[str, Any]:
        """处理用户/教练输入，返回结构化响应"""
        ...

    async def safety_check(self, message: str) -> bool:
        """安全检查 — L1拦截"""
        # 基础关键词安全检查 (SafetyPipeline 由 MasterAgent 层统一调用)
        dangerous_keywords = ["自杀", "自残", "伤害自己"]
        return not any(kw in message for kw in dangerous_keywords)

    def _format_response(self, content: str, **metadata) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "domain": self.domain,
            "content": content,
            "layer": "assistant",
            **metadata,
        }

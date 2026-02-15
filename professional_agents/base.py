"""
Professional Agent 基类

安全约束: 教练层Agent输出必须经教练审核后才能触达用户。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseProfessionalAgent(ABC):
    """所有professional层Agent的基类"""

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
        # TODO: 接入SafetyPipeline
        dangerous_keywords = ["自杀", "自残", "伤害自己"]
        return not any(kw in message for kw in dangerous_keywords)

    def _format_response(self, content: str, **metadata) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "domain": self.domain,
            "content": content,
            "layer": "professional",
            **metadata,
        }

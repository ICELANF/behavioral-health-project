"""
GenericLLMAgent — 纯 LLM 动态 Agent
无硬编码规则逻辑, 完全依赖 system_prompt + LLM 生成建议。
用于通过 DB 模板动态创建的新 Agent。
"""
from __future__ import annotations
import logging
from .base import BaseAgent, AgentDomain, AgentInput, AgentResult, RiskLevel

logger = logging.getLogger(__name__)


class GenericLLMAgent(BaseAgent):
    """纯 LLM 动态 Agent — 无规则逻辑, 完全依赖 system_prompt"""

    def __init__(self, template: dict):
        self.domain = None
        domain_enum = template.get("domain_enum")
        if domain_enum:
            try:
                self.domain = AgentDomain(domain_enum)
            except ValueError:
                pass

        self._agent_id = template["agent_id"]
        self.display_name = template.get("display_name", self._agent_id)
        self.keywords = template.get("keywords", [])
        self.data_fields = template.get("data_fields", [])
        self.priority = template.get("priority", 5)
        self.base_weight = template.get("base_weight", 0.8)
        self.enable_llm = template.get("enable_llm", True)
        self._template_system_prompt = template.get("system_prompt", "")

    def process(self, inp: AgentInput) -> AgentResult:
        """构造基础 result, 然后通过 LLM 增强"""
        domain_value = self.domain.value if self.domain else self._agent_id

        # 基础 result: 无规则引擎, 仅提供上下文
        result = AgentResult(
            agent_domain=domain_value,
            confidence=0.6,
            risk_level=RiskLevel.LOW,
            findings=[],
            recommendations=[],
        )

        # 如果 LLM 不可用, 返回默认建议
        if not self.enable_llm or not self._template_system_prompt:
            result.recommendations = [f"请咨询{self.display_name}获取专业建议"]
            return result

        return self._enhance_with_llm(result, inp)

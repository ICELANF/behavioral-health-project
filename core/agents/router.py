"""
AgentRouter — 路由分发
来源: §9.3 路由优先级规则

优先级规则:
  1. 危机状态 → CrisisAgent (强制)
  2. 风险等级 → 对应专业Agent
  3. 意图关键词 → 匹配领域Agent
  4. 用户偏好 → preferences.focus
  5. 设备数据 → 有数据的领域Agent
  6. 领域关联 → 加入相关协同Agent
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from .base import AgentDomain, AgentInput, DOMAIN_CORRELATIONS

if TYPE_CHECKING:
    from .base import BaseAgent


class AgentRouter:
    """根据用户输入和画像, 路由到1-2个最相关的Agent"""

    def __init__(self, agents: dict[str, "BaseAgent"]):
        self.agents = agents  # domain_str -> agent instance

        # 尝试从模板缓存加载关联网络, 失败降级到硬编码
        self._correlations = DOMAIN_CORRELATIONS
        try:
            from core.agent_template_service import build_correlations_from_templates
            tpl_corr = build_correlations_from_templates()
            if tpl_corr:
                self._correlations = tpl_corr
        except Exception:
            pass

    def route(self, inp: AgentInput, max_agents: int = 2) -> list[str]:
        """
        返回应激活的agent domain列表 (按优先级排序)
        """
        scored: list[tuple[float, str]] = []

        for domain_str, agent in self.agents.items():
            score = 0.0

            # 规则1: 危机强制
            if domain_str == "crisis" and agent.matches_intent(inp.message):
                return ["crisis"]  # 立即返回, 不再路由其他

            # 规则2: 风险等级
            risk = inp.profile.get("risk_level", "low")
            if risk == "critical" and domain_str == "crisis":
                score += 100
            elif risk == "high" and domain_str in ("glucose", "stress", "mental"):
                score += 50

            # 规则3: 意图关键词
            if agent.matches_intent(inp.message):
                score += 30

            # 规则4: 用户偏好
            focus = inp.profile.get("preferences", {}).get("focus", "")
            if focus and focus == domain_str:
                score += 20

            # 规则5: 设备数据
            for field in getattr(agent, "data_fields", []):
                if field in inp.device_data or \
                   any(k.startswith(field) for k in inp.device_data):
                    score += 15

            if score > 0:
                scored.append((score, domain_str))

        scored.sort(key=lambda x: -x[0])
        primary = [d for _, d in scored[:max_agents]]

        # 规则6: 领域关联 — 补充协同Agent
        if len(primary) == 1:
            corr = self._correlations.get(primary[0], [])
            for c in corr:
                if c in self.agents and c not in primary:
                    # 仅在关联Agent也有关键词匹配时才加入
                    if self.agents[c].matches_intent(inp.message):
                        primary.append(c)
                        break

        return primary or ["behavior_rx"]  # fallback

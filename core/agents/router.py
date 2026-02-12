"""
AgentRouter — 路由分发
来源: §9.3 路由优先级规则

优先级规则:
  1. 危机状态 → CrisisAgent (强制)
  2. 风险等级 → 对应专业Agent
  3. 意图关键词 → 匹配领域Agent (专家自定义 > 平台预置)
  4. 用户偏好 → preferences.focus
  5. 设备数据 → 有数据的领域Agent
  6. 领域关联 → 加入相关协同Agent
"""
from __future__ import annotations
from typing import TYPE_CHECKING, Optional
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

    def route(self, inp: AgentInput, max_agents: int = 2,
              tenant_ctx: Optional[dict] = None) -> list[str]:
        """
        返回应激活的agent domain列表 (按优先级排序)

        tenant_ctx: 租户路由上下文 (来自 get_tenant_routing_context)
            - agent_keyword_overrides: {agent_id: {"keywords": [...], "boost": 1.5}}
            - correlations: 租户级关联覆盖
            - fallback_agent: 租户回退 Agent
            - enabled_agents: 租户启用的 Agent 列表
        """
        scored: list[tuple[float, str]] = []

        # 租户路由上下文
        kw_overrides = (tenant_ctx or {}).get("agent_keyword_overrides", {})
        tenant_corr = (tenant_ctx or {}).get("correlations")
        fallback = (tenant_ctx or {}).get("fallback_agent", "behavior_rx")
        enabled_set = set((tenant_ctx or {}).get("enabled_agents", []))

        # 合并关联: 租户优先 > 模板/硬编码
        correlations = dict(self._correlations)
        if tenant_corr:
            correlations.update(tenant_corr)

        for domain_str, agent in self.agents.items():
            # 如果有租户上下文且 Agent 不在启用列表中, 跳过 (crisis 始终保留)
            if enabled_set and domain_str != "crisis" and domain_str not in enabled_set:
                continue

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

            # 规则3a: 专家自定义关键词 (优先级更高)
            override = kw_overrides.get(domain_str)
            if override:
                boost = override.get("boost", 1.5)
                custom_kws = override.get("keywords", [])
                msg_lower = inp.message.lower()
                if any(kw.lower() in msg_lower for kw in custom_kws):
                    score += 30 * boost  # 带加权的关键词得分

            # 规则3b: 平台预置关键词
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
            corr = correlations.get(primary[0], [])
            for c in corr:
                if c in self.agents and c not in primary:
                    # 仅在关联Agent也有关键词匹配时才加入
                    if self.agents[c].matches_intent(inp.message):
                        primary.append(c)
                        break

        return primary or [fallback if fallback in self.agents else "behavior_rx"]

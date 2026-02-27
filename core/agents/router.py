"""
AgentRouter — 路由分发 (Registry 版)

变更:
  Before: __init__(agents: dict[str, BaseAgent]) — 接受硬编码 dict
  After:  __init__(registry: AgentRegistry) — 从 Registry 查询

路由优先级规则不变 (§9.3):
  1. 危机状态 → CrisisAgent (强制)
  2. 风险等级 → 对应专业Agent
  3. 意图关键词 → 匹配领域Agent (专家自定义 > 平台预置)
  4. 用户偏好 → preferences.focus
  5. 设备数据 → 有数据的领域Agent
  6. 领域关联 → 加入相关协同Agent
"""
from __future__ import annotations
import logging
from typing import TYPE_CHECKING, Optional

from .base import AgentInput, DOMAIN_CORRELATIONS
from .registry import AgentRegistry

if TYPE_CHECKING:
    from .base import BaseAgent

logger = logging.getLogger(__name__)


class AgentRouter:
    """根据用户输入和画像, 路由到 1-2 个最相关的 Agent"""

    def __init__(self, registry: AgentRegistry):
        self._registry = registry

        # 尝试从模板缓存加载关联网络, 失败降级到硬编码
        self._correlations = dict(DOMAIN_CORRELATIONS)
        try:
            from core.agent_template_service import build_correlations_from_templates
            tpl_corr = build_correlations_from_templates()
            if tpl_corr:
                self._correlations = tpl_corr
        except Exception:
            pass

    @property
    def agents(self) -> dict[str, "BaseAgent"]:
        """向后兼容: 暴露 agents dict (只读)"""
        return self._registry.list_agents()

    def route(self, inp: AgentInput, max_agents: int = 2,
              tenant_ctx: Optional[dict] = None) -> list[str]:
        """
        返回应激活的 agent domain 列表 (按优先级排序)

        逻辑与原版完全一致, 仅将 self.agents[...] 改为 self._registry.get_or_none(...)
        """
        scored: list[tuple[float, str]] = []

        # 租户路由上下文
        kw_overrides = (tenant_ctx or {}).get("agent_keyword_overrides", {})
        tenant_corr = (tenant_ctx or {}).get("correlations")
        fallback = (tenant_ctx or {}).get("fallback_agent", "behavior_rx")
        enabled_set = set((tenant_ctx or {}).get("enabled_agents", []))

        # ── XZB 行智诊疗: 检测专家绑定 ──
        xzb_expert_id = (tenant_ctx or {}).get("xzb_expert_id")
        if xzb_expert_id and self._registry.has("xzb_expert"):
            scored.append((80.0, "xzb_expert"))

        # 合并关联: 租户优先 > 模板/硬编码
        correlations = dict(self._correlations)
        if tenant_corr:
            correlations.update(tenant_corr)

        for domain, agent in self._registry:
            # 如果有租户上下文且 Agent 不在启用列表中, 跳过 (crisis 始终保留)
            if enabled_set and domain != "crisis" and domain not in enabled_set:
                continue

            score = 0.0

            # 规则1: 危机强制
            if domain == "crisis" and agent.matches_intent(inp.message):
                return ["crisis"]  # 立即返回

            # 规则2: 风险等级
            risk = inp.profile.get("risk_level", "low")
            if risk == "critical" and domain == "crisis":
                score += 100
            elif risk == "high" and domain in ("glucose", "stress", "mental"):
                score += 50

            # 规则3a: 专家自定义关键词
            override = kw_overrides.get(domain)
            if override:
                boost = override.get("boost", 1.5)
                custom_kws = override.get("keywords", [])
                msg_lower = inp.message.lower()
                if any(kw.lower() in msg_lower for kw in custom_kws):
                    score += 30 * boost

            # 规则3b: 平台预置关键词 (优先从 AgentMeta 获取, 降级到实例属性)
            meta = self._registry.get_meta(domain) if self._registry.has(domain) else None
            meta_keywords = meta.keywords if meta else ()
            instance_keywords = getattr(agent, "keywords", [])
            all_keywords = set(meta_keywords) | set(instance_keywords)

            msg_lower = inp.message.lower()
            if any(kw in msg_lower for kw in all_keywords):
                score += 30

            # 规则4: 用户偏好
            focus = inp.profile.get("preferences", {}).get("focus", "")
            if focus and focus == domain:
                score += 20

            # 规则5: 设备数据
            data_fields = meta.data_fields if meta else ()
            if not data_fields:
                data_fields = getattr(agent, "data_fields", [])
            for field in data_fields:
                if field in inp.device_data or \
                   any(k.startswith(field) for k in inp.device_data):
                    score += 15

            # I-09: 循证等级加分
            _tier_bonus = {"T1": 10, "T2": 7, "T3": 3, "T4": 0}
            agent_tier = meta.evidence_tier if meta else getattr(agent, "evidence_tier", "T3")
            score += _tier_bonus.get(agent_tier, 0)

            if score > 0:
                scored.append((score, domain))

        scored.sort(key=lambda x: -x[0])
        primary = [d for _, d in scored[:max_agents]]

        # 规则6: 领域关联 — 补充协同Agent
        if len(primary) == 1:
            corr = correlations.get(primary[0], [])
            for c in corr:
                if self._registry.has(c) and c not in primary:
                    corr_agent = self._registry.get(c)
                    if corr_agent.matches_intent(inp.message):
                        primary.append(c)
                        break

        fallback_domain = fallback if self._registry.has(fallback) else "behavior_rx"
        return primary or [fallback_domain]

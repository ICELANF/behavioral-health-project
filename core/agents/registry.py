"""
AgentRegistry — 唯一 Agent 注册表

设计原则:
  1. 单例: 整个应用只有一个 Registry
  2. 启动期注册: 所有 Agent 在 startup 阶段注册
  3. 冻结: 启动完成后 freeze(), 运行时不可篡改
  4. 强制: AgentRouter / Coordinator 只能从 Registry 获取 Agent
  5. 安全: CrisisAgent priority=0, 始终在位

使用:
    registry = AgentRegistry()
    registry.register(CrisisAgent(), meta)
    registry.freeze()

    agent = registry.get("crisis")        # 获取实例
    meta = registry.get_meta("crisis")    # 获取元数据
    domains = registry.list_domains()     # 列出所有域
"""
from __future__ import annotations
import logging
from typing import Any, Iterator

from .agent_meta import AgentMeta

logger = logging.getLogger(__name__)


class RegistryFrozenError(RuntimeError):
    """注册表已冻结, 不允许修改"""
    pass


class AgentNotRegisteredError(KeyError):
    """Agent 未注册"""
    pass


class AgentRegistry:
    """
    Agent 注册表 — 启动期注册, 冻结后只读

    不使用单例模式 (dependency injection 更可测试),
    但通常整个应用只创建一个实例, 通过 DI 传递。
    """

    def __init__(self):
        self._agents: dict[str, Any] = {}       # domain → Agent 实例
        self._meta: dict[str, AgentMeta] = {}    # domain → 元数据
        self._frozen: bool = False
        self._registration_order: list[str] = [] # 保持注册顺序

    # ── 注册 ──

    def register(self, agent: Any, meta: AgentMeta) -> None:
        """
        注册一个 Agent

        Args:
            agent: BaseAgent 实例
            meta:  AgentMeta 元数据 (meta.domain 作为注册 key)

        Raises:
            RegistryFrozenError: 冻结后调用
            ValueError:          domain 重复或 meta 无效
        """
        if self._frozen:
            raise RegistryFrozenError(
                f"注册表已冻结, 无法注册 '{meta.domain}'. "
                "所有 Agent 必须在 startup 阶段注册."
            )

        domain = meta.domain
        if not domain:
            raise ValueError("AgentMeta.domain 不能为空")

        if domain in self._agents:
            logger.warning(
                "Agent '%s' 已注册, 将被覆盖 (旧: %s, 新: %s)",
                domain, type(self._agents[domain]).__name__, type(agent).__name__,
            )
        else:
            self._registration_order.append(domain)

        self._agents[domain] = agent
        self._meta[domain] = meta
        logger.info(
            "Agent 注册: %s (%s) priority=%d tier=%s",
            domain, meta.display_name, meta.priority, meta.tier.value,
        )

    def register_batch(self, agents_with_meta: list[tuple[Any, AgentMeta]]) -> None:
        """批量注册"""
        for agent, meta in agents_with_meta:
            self.register(agent, meta)

    # ── 冻结 ──

    def freeze(self) -> None:
        """
        冻结注册表 — 此后 register() 将抛异常

        应在 FastAPI startup 完成所有注册后调用。
        """
        # 安全检查: CrisisAgent 必须存在
        if "crisis" not in self._agents:
            raise RuntimeError(
                "冻结失败: CrisisAgent 未注册! "
                "CrisisAgent 是安全硬约束, 必须始终存在."
            )

        self._frozen = True
        logger.info(
            "AgentRegistry 已冻结: %d 个 Agent 注册完成 — %s",
            len(self._agents), list(self._agents.keys()),
        )

    @property
    def is_frozen(self) -> bool:
        return self._frozen

    # ── 查询 ──

    def get(self, domain: str) -> Any:
        """获取 Agent 实例"""
        agent = self._agents.get(domain)
        if agent is None:
            raise AgentNotRegisteredError(
                f"Agent '{domain}' 未注册. 已注册: {list(self._agents.keys())}"
            )
        return agent

    def get_or_none(self, domain: str) -> Any | None:
        """获取 Agent 实例, 不存在返回 None"""
        return self._agents.get(domain)

    def get_meta(self, domain: str) -> AgentMeta:
        """获取 Agent 元数据"""
        meta = self._meta.get(domain)
        if meta is None:
            raise AgentNotRegisteredError(f"Agent '{domain}' 无元数据")
        return meta

    def list_domains(self) -> list[str]:
        """列出所有已注册的 domain (按注册顺序)"""
        return list(self._registration_order)

    def list_agents(self) -> dict[str, Any]:
        """返回 domain → Agent 实例的字典 (只读副本)"""
        return dict(self._agents)

    def list_meta(self) -> dict[str, AgentMeta]:
        """返回 domain → AgentMeta 字典 (只读副本)"""
        return dict(self._meta)

    def has(self, domain: str) -> bool:
        """检查 Agent 是否已注册"""
        return domain in self._agents

    def count(self) -> int:
        return len(self._agents)

    # ── 按条件查询 ──

    def get_by_tier(self, tier) -> dict[str, Any]:
        """按层级获取 Agent"""
        return {
            domain: agent
            for domain, agent in self._agents.items()
            if self._meta.get(domain) and self._meta[domain].tier == tier
        }

    def get_by_priority(self, max_priority: int = 3) -> list[tuple[str, Any]]:
        """获取优先级 ≤ max_priority 的 Agent (按优先级排序)"""
        result = []
        for domain, agent in self._agents.items():
            meta = self._meta.get(domain)
            if meta and meta.priority <= max_priority:
                result.append((domain, agent))
        result.sort(key=lambda x: self._meta[x[0]].priority)
        return result

    # ── 迭代 ──

    def __iter__(self) -> Iterator[tuple[str, Any]]:
        yield from self._agents.items()

    def __len__(self) -> int:
        return len(self._agents)

    def __contains__(self, domain: str) -> bool:
        return domain in self._agents

    # ── 诊断 ──

    def health_check(self) -> dict:
        """注册表健康检查 — 供 /health 端点调用"""
        return {
            "agent_count": len(self._agents),
            "frozen": self._frozen,
            "has_crisis": "crisis" in self._agents,
            "domains": self.list_domains(),
            "tier_counts": {
                tier.value: len(self.get_by_tier(tier))
                for tier in set(m.tier for m in self._meta.values())
            },
        }

    def __repr__(self) -> str:
        state = "frozen" if self._frozen else "open"
        return f"<AgentRegistry [{state}] {len(self._agents)} agents>"

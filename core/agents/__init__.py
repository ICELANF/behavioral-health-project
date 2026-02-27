"""
core.agents — Agent 子系统公开 API

用法:
    from core.agents import MasterAgent, AgentRegistry, create_registry

    registry = create_registry(db_session=db)
    agent = MasterAgent(registry=registry)
    result = agent.process(user_id=1, message="...")
"""
from .registry import AgentRegistry, RegistryFrozenError, AgentNotRegisteredError
from .agent_meta import AgentMeta, AgentTier
from .startup import create_registry, register_all_agents
from .master_agent import MasterAgent
from .base import BaseAgent, AgentInput, AgentResult, RiskLevel, AgentDomain, PolicyDecision

__all__ = [
    # Registry
    "AgentRegistry", "RegistryFrozenError", "AgentNotRegisteredError",
    "AgentMeta", "AgentTier",
    "create_registry", "register_all_agents",
    # Core
    "MasterAgent",
    "BaseAgent", "AgentInput", "AgentResult",
    "RiskLevel", "AgentDomain", "PolicyDecision",
]

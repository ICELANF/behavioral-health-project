# -*- coding: utf-8 -*-
"""
Agent 注册表

管理所有专家 Agent 的注册和查询
"""

from typing import Dict, Optional, List
from .base import ExpertAgent, AgentConfig


class AgentRegistry:
    """Agent 注册表 - 单例模式

    负责管理所有专家 Agent 的注册、查询和生命周期
    """

    _instance = None
    _agents: Dict[str, ExpertAgent] = {}
    _configs: Dict[str, AgentConfig] = {}

    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents = {}
            cls._instance._configs = {}
        return cls._instance

    def register(self, agent_id: str, agent: ExpertAgent, config: AgentConfig):
        """注册一个专家 Agent

        Args:
            agent_id: Agent 唯一标识符
            agent: ExpertAgent 实例
            config: AgentConfig 配置对象
        """
        self._agents[agent_id] = agent
        self._configs[agent_id] = config

    def unregister(self, agent_id: str) -> bool:
        """取消注册一个专家 Agent

        Args:
            agent_id: Agent 唯一标识符

        Returns:
            是否成功取消注册
        """
        if agent_id in self._agents:
            del self._agents[agent_id]
            del self._configs[agent_id]
            return True
        return False

    def get(self, agent_id: str) -> Optional[ExpertAgent]:
        """获取指定的专家 Agent

        Args:
            agent_id: Agent 唯一标识符

        Returns:
            ExpertAgent 实例，如果不存在则返回 None
        """
        return self._agents.get(agent_id)

    def get_config(self, agent_id: str) -> Optional[AgentConfig]:
        """获取指定 Agent 的配置

        Args:
            agent_id: Agent 唯一标识符

        Returns:
            AgentConfig 实例，如果不存在则返回 None
        """
        return self._configs.get(agent_id)

    def get_all(self) -> Dict[str, ExpertAgent]:
        """获取所有注册的 Agent

        Returns:
            所有 Agent 的字典副本
        """
        return self._agents.copy()

    def get_all_configs(self) -> Dict[str, AgentConfig]:
        """获取所有 Agent 配置

        Returns:
            所有配置的字典副本
        """
        return self._configs.copy()

    def list_agents(self) -> List[str]:
        """列出所有已注册的 Agent ID

        Returns:
            Agent ID 列表
        """
        return list(self._agents.keys())

    def list_by_priority(self) -> List[str]:
        """按优先级排序返回 Agent ID 列表

        Returns:
            按优先级排序的 Agent ID 列表
        """
        return sorted(
            self._configs.keys(),
            key=lambda x: self._configs[x].priority
        )

    def clear(self):
        """清空所有注册的 Agent"""
        self._agents.clear()
        self._configs.clear()

    def __len__(self) -> int:
        """返回已注册的 Agent 数量"""
        return len(self._agents)

    def __contains__(self, agent_id: str) -> bool:
        """检查 Agent 是否已注册"""
        return agent_id in self._agents

    def __iter__(self):
        """迭代所有 Agent ID"""
        return iter(self._agents)

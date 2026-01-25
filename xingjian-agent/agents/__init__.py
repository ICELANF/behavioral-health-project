# -*- coding: utf-8 -*-
"""
多专家 Agent 系统模块

包含:
- ExpertAgent: 专家 Agent 基类
- AgentRegistry: Agent 注册表
- AgentFactory: Agent 工厂
- IntentRouter: 意图路由器
- CollaborationProtocol: 协作协议
- AgentOrchestrator: 主协调器
"""

from .base import ExpertAgent, AgentConfig
from .registry import AgentRegistry
from .factory import AgentFactory
from .router import IntentRouter, RoutingResult
from .collaboration import CollaborationProtocol, ConsultationRequest, ConsultationResponse
from .orchestrator import AgentOrchestrator

__all__ = [
    'ExpertAgent',
    'AgentConfig',
    'AgentRegistry',
    'AgentFactory',
    'IntentRouter',
    'RoutingResult',
    'CollaborationProtocol',
    'ConsultationRequest',
    'ConsultationResponse',
    'AgentOrchestrator',
]

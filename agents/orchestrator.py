# -*- coding: utf-8 -*-
"""
Agent 协调器

多专家 Agent 系统的核心协调模块
负责初始化所有专家、路由用户查询、协调专家协作
"""

import os
import re
import yaml
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from .base import AgentConfig
from .registry import AgentRegistry
from .factory import AgentFactory
from .router import IntentRouter, RoutingResult
from .collaboration import (
    CollaborationProtocol,
    ConsultationRequest,
    ConsultationType,
    ConsultationResponse
)


def clean_surrogates(text: str) -> str:
    """清理文本中的代理字符"""
    return re.sub(r'[\ud800-\udfff]', '', text)


@dataclass
class OrchestratorResponse:
    """协调器响应"""

    final_response: str            # 最终综合响应
    primary_expert: str            # 主要处理专家名称
    primary_expert_id: str         # 主要处理专家 ID
    consulted_experts: List[str]   # 咨询过的专家名称列表
    routing_confidence: float      # 路由置信度
    routing_reasoning: str         # 路由原因


class AgentOrchestrator:
    """Agent 协调器

    多专家 Agent 系统的核心，负责：
    1. 初始化所有专家 Agent
    2. 路由用户查询到合适的专家
    3. 协调专家之间的咨询
    4. 综合多专家响应
    """

    def __init__(self, config_path: str = "config.yaml"):
        """初始化协调器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()

        # 初始化组件
        self.registry = AgentRegistry()
        self.factory = AgentFactory(config_path)
        self.router: Optional[IntentRouter] = None
        self.collaboration: Optional[CollaborationProtocol] = None

        # 初始化所有专家
        self._initialize_agents()

        # 初始化路由器和协作协议
        self._initialize_components()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _initialize_agents(self):
        """初始化所有专家 Agent"""
        experts_config = self.config.get("experts", {})
        paths_config = self.config.get("paths", {})

        if not experts_config:
            raise ValueError("配置文件中未找到专家配置")

        print(f"\n正在初始化专家 Agent...")

        for expert_id, expert_conf in experts_config.items():
            try:
                agent, agent_config = self.factory.create_agent_from_config_dict(
                    expert_id=expert_id,
                    expert_conf=expert_conf,
                    paths_config=paths_config
                )
                self.registry.register(expert_id, agent, agent_config)
                print(f"  [OK] {expert_conf.get('name', expert_id)}")
            except FileNotFoundError as e:
                print(f"  [X] {expert_conf.get('name', expert_id)}: {e}")
            except Exception as e:
                print(f"  [X] {expert_conf.get('name', expert_id)}: 初始化失败 - {e}")

        if len(self.registry) == 0:
            raise RuntimeError("没有成功初始化任何专家 Agent")

        print(f"\n成功初始化 {len(self.registry)} 个专家 Agent")

    def _initialize_components(self):
        """初始化路由器和协作协议"""
        self.router = IntentRouter(self.registry, self.config)
        self.collaboration = CollaborationProtocol(self.registry, self.config)

    def process_query(self, user_query: str) -> OrchestratorResponse:
        """处理用户查询

        Args:
            user_query: 用户输入的问题

        Returns:
            OrchestratorResponse 对象
        """
        # 清理输入
        user_query = clean_surrogates(user_query)

        # Step 1: 路由到合适的专家
        routing_result = self.router.route(user_query)

        # 获取主要专家
        primary_agent = self.registry.get(routing_result.primary_agent)
        primary_config = self.registry.get_config(routing_result.primary_agent)

        if not primary_agent or not primary_config:
            return OrchestratorResponse(
                final_response="抱歉，系统暂时无法处理您的问题，请稍后再试。",
                primary_expert="未知",
                primary_expert_id="unknown",
                consulted_experts=[],
                routing_confidence=0.0,
                routing_reasoning="无法找到合适的专家"
            )

        print(f"\n[{primary_config.name}] 正在分析您的问题...")

        # Step 2: 获取主要专家的回复
        try:
            primary_response = primary_agent.chat(user_query)
            primary_response_text = clean_surrogates(primary_response.response)
        except Exception as e:
            return OrchestratorResponse(
                final_response=f"处理您的问题时发生错误: {str(e)}",
                primary_expert=primary_config.name,
                primary_expert_id=routing_result.primary_agent,
                consulted_experts=[],
                routing_confidence=routing_result.confidence,
                routing_reasoning=routing_result.reasoning
            )

        # Step 3: 检查是否需要跨专业咨询
        consultation_responses: List[ConsultationResponse] = []
        orchestrator_config = self.config.get("orchestrator", {})

        if (orchestrator_config.get("enable_multi_expert", True) and
            routing_result.secondary_agents):

            max_consults = orchestrator_config.get("max_consultations", 2)

            for consultant_id in routing_result.secondary_agents[:max_consults]:
                consultant_config = self.registry.get_config(consultant_id)
                if not consultant_config:
                    continue

                print(f"[{consultant_config.name}] 正在提供专业补充意见...")

                request = ConsultationRequest(
                    requester_id=routing_result.primary_agent,
                    consultant_id=consultant_id,
                    user_query=user_query,
                    initial_analysis=primary_response_text,
                    consultation_type=ConsultationType.SUPPLEMENT
                )

                response = self.collaboration.request_consultation(request)
                if response.confidence > 0:
                    consultation_responses.append(response)

        # Step 4: 综合响应
        if consultation_responses:
            print(f"\n[协调员] 正在综合专家意见...")
            final_response = self.collaboration.synthesize_responses(
                user_query=user_query,
                primary_response=primary_response_text,
                primary_expert_name=primary_config.name,
                consultation_responses=consultation_responses
            )
        else:
            final_response = primary_response_text

        return OrchestratorResponse(
            final_response=clean_surrogates(final_response),
            primary_expert=primary_config.name,
            primary_expert_id=routing_result.primary_agent,
            consulted_experts=[r.consultant_name for r in consultation_responses],
            routing_confidence=routing_result.confidence,
            routing_reasoning=routing_result.reasoning
        )

    def chat(self, user_query: str) -> str:
        """简化的对话接口

        Args:
            user_query: 用户输入

        Returns:
            回复文本
        """
        result = self.process_query(user_query)
        return result.final_response

    def get_available_experts(self) -> List[Dict[str, str]]:
        """获取可用专家列表

        Returns:
            专家信息列表
        """
        experts = []
        for agent_id in self.registry.list_by_priority():
            config = self.registry.get_config(agent_id)
            if config:
                experts.append({
                    "id": agent_id,
                    "name": config.name,
                    "description": config.description
                })
        return experts

    def reset_all(self):
        """重置所有专家的对话历史"""
        for agent_id in self.registry:
            agent = self.registry.get(agent_id)
            if agent:
                agent.reset()

    def direct_chat(self, expert_id: str, message: str) -> str:
        """直接与指定专家对话（绕过路由）

        Args:
            expert_id: 专家 ID
            message: 用户消息

        Returns:
            专家回复
        """
        agent = self.registry.get(expert_id)
        if not agent:
            return f"未找到专家: {expert_id}"

        try:
            response = agent.chat(clean_surrogates(message))
            return clean_surrogates(response.response)
        except Exception as e:
            return f"与专家对话时发生错误: {str(e)}"

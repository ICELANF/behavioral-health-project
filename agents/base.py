# -*- coding: utf-8 -*-
"""
ExpertAgent 基类定义

定义专家 Agent 的基础结构和配置数据类
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from llama_index.core.chat_engine.types import BaseChatEngine


@dataclass
class AgentConfig:
    """Agent 配置数据类"""

    name: str                           # 显示名称 (如: "心理咨询师")
    id: str                             # 唯一标识符 (如: "mental_health")
    description: str                    # 简短描述，用于路由展示
    knowledge_path: str                 # Obsidian 知识库路径
    vectordb_path: str                  # 向量数据库路径
    system_prompt_path: str             # 系统提示词文件路径
    keywords: List[str] = field(default_factory=list)  # 意图匹配关键词
    can_consult: List[str] = field(default_factory=list)  # 可咨询的其他专家 ID
    priority: int = 99                  # 优先级 (数字越小优先级越高)

    def __post_init__(self):
        """验证配置"""
        if not self.name:
            raise ValueError("Agent name cannot be empty")
        if not self.id:
            raise ValueError("Agent id cannot be empty")


class ExpertAgent:
    """专家 Agent 基类

    封装 LlamaIndex ChatEngine，提供统一的对话接口
    """

    def __init__(
        self,
        agent_id: str,
        name: str,
        chat_engine: BaseChatEngine,
        config: AgentConfig
    ):
        """初始化专家 Agent

        Args:
            agent_id: Agent 唯一标识符
            name: Agent 显示名称
            chat_engine: LlamaIndex ChatEngine 实例
            config: Agent 配置对象
        """
        self.agent_id = agent_id
        self.name = name
        self.chat_engine = chat_engine
        self.config = config
        self._conversation_history: List[Dict[str, str]] = []

    def chat(self, message: str) -> Any:
        """发送消息并获取回复

        Args:
            message: 用户输入的消息

        Returns:
            ChatEngine 的响应对象
        """
        response = self.chat_engine.chat(message)

        # 记录对话历史
        self._conversation_history.append({
            "role": "user",
            "content": message
        })
        self._conversation_history.append({
            "role": "assistant",
            "content": response.response
        })

        return response

    def reset(self):
        """重置对话历史"""
        self.chat_engine.reset()
        self._conversation_history = []

    @property
    def history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self._conversation_history.copy()

    @property
    def keywords(self) -> List[str]:
        """获取关键词列表"""
        return self.config.keywords

    @property
    def can_consult(self) -> List[str]:
        """获取可咨询的专家列表"""
        return self.config.can_consult

    def __repr__(self) -> str:
        return f"ExpertAgent(id={self.agent_id}, name={self.name})"

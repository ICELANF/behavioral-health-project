# -*- coding: utf-8 -*-
"""
Agent 工厂

负责创建和初始化专家 Agent 实例
"""

import os
import re
import yaml
from typing import Dict, Any, Optional

from llama_index.core import StorageContext, load_index_from_storage, Settings, PromptTemplate
from llama_index.core.chat_engine.types import ChatMode
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.ollama import OllamaEmbedding

from .base import ExpertAgent, AgentConfig


def clean_surrogates(text: str) -> str:
    """清理文本中的代理字符

    Args:
        text: 输入文本

    Returns:
        清理后的文本
    """
    return re.sub(r'[\ud800-\udfff]', '', text)


class AgentFactory:
    """Agent 工厂

    负责从配置创建专家 Agent 实例
    """

    def __init__(self, config_path: str = "config.yaml"):
        """初始化工厂

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_global_settings()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _setup_global_settings(self):
        """初始化全局 LlamaIndex 设置"""
        model_config = self.config.get("model", {})

        Settings.llm = Ollama(
            model=model_config.get("llm", "qwen2.5:0.5b"),
            base_url=model_config.get("ollama_base_url", "http://localhost:11434"),
            temperature=model_config.get("temperature", 0.3),
            request_timeout=model_config.get("request_timeout", 600.0)
        )

        Settings.embed_model = OllamaEmbedding(
            model_name=model_config.get("embed", "mxbai-embed-large:latest"),
            base_url=model_config.get("ollama_base_url", "http://localhost:11434")
        )

    def create_agent(self, agent_config: AgentConfig) -> ExpertAgent:
        """从配置创建专家 Agent

        Args:
            agent_config: Agent 配置对象

        Returns:
            创建的 ExpertAgent 实例
        """
        # 加载系统提示词
        system_prompt = self._load_system_prompt(agent_config.system_prompt_path)

        # 加载向量索引
        index = self._load_vector_index(agent_config.vectordb_path)

        # 创建上下文提示模板
        context_template = self._create_context_template(system_prompt)

        # 创建聊天引擎
        chat_engine = index.as_chat_engine(
            chat_mode=ChatMode.CONTEXT,
            system_prompt=system_prompt,
            context_template=context_template,
            similarity_top_k=3
        )

        return ExpertAgent(
            agent_id=agent_config.id,
            name=agent_config.name,
            chat_engine=chat_engine,
            config=agent_config
        )

    def _load_system_prompt(self, prompt_path: str) -> str:
        """加载系统提示词

        Args:
            prompt_path: 提示词文件路径

        Returns:
            清理后的提示词内容
        """
        if not os.path.exists(prompt_path):
            raise FileNotFoundError(f"系统提示词文件不存在: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        return clean_surrogates(content)

    def _load_vector_index(self, vectordb_path: str):
        """加载向量索引

        Args:
            vectordb_path: 向量数据库路径

        Returns:
            LlamaIndex 索引对象
        """
        if not os.path.exists(vectordb_path):
            raise FileNotFoundError(f"向量数据库不存在: {vectordb_path}")

        storage = StorageContext.from_defaults(persist_dir=vectordb_path)
        return load_index_from_storage(storage)

    def _create_context_template(self, system_prompt: str) -> PromptTemplate:
        """创建上下文提示模板

        Args:
            system_prompt: 系统提示词

        Returns:
            PromptTemplate 对象
        """
        return PromptTemplate(
            "【重要指令】你必须完全使用中文回复，严禁使用任何英文单词。\n\n"
            "你现在的身份是：\n"
            "----------\n"
            f"{system_prompt}\n"
            "----------\n\n"
            "以下是参考的背景资料：\n"
            "{context_str}\n"
            "----------\n\n"
            "用户问题：{query_str}\n\n"
            "【回复要求】\n"
            "1. 必须100%使用中文，包括所有专业术语\n"
            "2. 禁止出现任何英文单词\n"
            "3. 遵循专业术语标准\n"
        )

    def create_agent_from_config_dict(
        self,
        expert_id: str,
        expert_conf: Dict[str, Any],
        paths_config: Dict[str, str]
    ) -> tuple[ExpertAgent, AgentConfig]:
        """从配置字典创建专家 Agent

        Args:
            expert_id: 专家 ID
            expert_conf: 专家配置字典
            paths_config: 路径配置字典

        Returns:
            (ExpertAgent, AgentConfig) 元组
        """
        # 构建完整路径
        knowledge_path = os.path.join(
            paths_config.get("obsidian_vault", ""),
            expert_conf.get("knowledge_folder", "")
        )
        vectordb_path = os.path.join(
            paths_config.get("vectordb_base", ""),
            expert_conf.get("vectordb_folder", "")
        )
        system_prompt_path = os.path.join(
            paths_config.get("prompts", ""),
            expert_conf.get("system_prompt", "")
        )

        # 创建配置对象
        agent_config = AgentConfig(
            name=expert_conf.get("name", ""),
            id=expert_id,
            description=expert_conf.get("description", ""),
            knowledge_path=knowledge_path,
            vectordb_path=vectordb_path,
            system_prompt_path=system_prompt_path,
            keywords=expert_conf.get("keywords", []),
            can_consult=expert_conf.get("can_consult", []),
            priority=expert_conf.get("priority", 99)
        )

        # 创建 Agent
        agent = self.create_agent(agent_config)

        return agent, agent_config
